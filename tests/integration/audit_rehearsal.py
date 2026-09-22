"""Read-only acceptance audit of one completed real rehearsal; never invokes a model."""
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from orchestration.rehearsal import read_rehearsal


def audit(root: Path) -> dict[str, object]:
    originals = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in root.rglob('*') if p.is_file()}
    document = read_rehearsal(root / 'rehearsal.json')
    final = document.current
    assert document.mode == 'live' and final.stage == 'completed'
    assert final.model_calls_started == 2 and final.cost_usd is None
    assert final.acceptance.task_live == 'passed'
    first, second = final.results
    assert first.attempt.agent != second.attempt.agent
    assert first.task_id != second.task_id
    assert final.routing.selected_attempt == second.attempt
    assert final.routing.removed_member == first.attempt.agent
    assert final.routing.eligible_members == [second.attempt.agent]
    assert not next(m.available for m in final.members if m.agent == first.attempt.agent)
    assert not next(p.active for p in final.pipes if p.dst == first.attempt.agent)
    assert document.history[0].checkpoints.passed_count == 0
    assert final.checkpoints.passed_count == 3
    assert all(check.passed is True for check in final.checkpoints.checks)
    assert next(p.weight for p in document.history[0].pipes if p.dst == first.attempt.agent) == 1
    assert any(any(p.dst == first.attempt.agent and p.weight == 1.9 for p in s.pipes) for s in document.history)
    assert len(final.genes) == 2 and len(final.adoptions) == 1
    first_gene = next(g for g in final.genes if g.source_attempt == first.attempt)
    assert first_gene.use_count == 1 and first_gene.injected_count == 1
    assert final.adoptions[0].attempt == second.attempt and final.adoptions[0].ref == first_gene.ref
    assert not final.retrievable_gene_ids
    decay_points = 0
    for snapshot in document.history:
        for gene in snapshot.genes:
            if gene.archived_at is None:
                anchor = gene.last_used_at if gene.last_used_at is not None else gene.created_at
                assert math.isclose(gene.weight, math.exp(-(gene.evaluated_at-anchor)/10), rel_tol=1e-9)
                assert abs(gene.evaluated_at-snapshot.at) < 0.001
                decay_points += 1
    for gene in final.genes:
        assert gene.archived_at is not None and gene.weight < final.archive_threshold
        anchor = gene.last_used_at if gene.last_used_at is not None else gene.created_at
        assert gene.archived_at-anchor >= 10*math.log(1/final.archive_threshold)
    calls = []
    external_checks = []
    for directory, expected in [('initial-review', False), ('repair/review', True), ('recovery/initial-review', False), ('recovery/review', True)]:
        reports = list((root/directory).glob('verification-*.json'))
        assert len(reports) == 1
        report = json.loads(reports[0].read_text())
        assert report['checks'] == dict.fromkeys(('clamp','mean','unique'), expected)
        assert report['exit_code'] == (0 if expected else 1)
        assert report['command'][1:3] == ['-I', '-S']
        assert Path(report['command'][3]).name == 'acceptance_runner.py'
        external_checks.append({'directory':directory,'checks':report['checks'],'exit_code':report['exit_code']})
    for name, result in zip(('repair', 'recovery'), final.results):
        cli = root / name / 'cli'
        events = [json.loads(line) for line in (cli/'codex.jsonl').read_text().splitlines() if line.strip()]
        turns = [event for event in events if event.get('type') == 'turn.completed']
        assert len(turns) == 1
        assert sum(e.get('type') == 'turn.started' for e in events) == 1
        usage = turns[0]['usage']
        assert usage['input_tokens']+usage['output_tokens'] == result.usage.tokens
        assert result.status == 'succeeded' and result.verdict.passed is True
        argv = json.loads((cli/'command.json').read_text())
        assert argv[argv.index('--model')+1] == 'gpt-5.6-luna'
        calls.append({'task':name,'agent':result.attempt.agent.model_dump(), 'cli_calls':1,'turns':1,'usage':usage,'tokens':result.usage.tokens,'cost_usd':result.usage.cost_usd})
    # SQLite immutable read avoids creating/changing WAL/SHM on the live evidence.
    connection=sqlite3.connect((root/'metadata.db').as_uri()+'?mode=ro&immutable=1',uri=True)
    tables=[row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    gene_table=next(table for table in tables if table=='genes')
    assert connection.execute(f'SELECT count(*) FROM "{gene_table}"').fetchone()[0] == 0
    connection.close()
    replay = read_rehearsal(root/'rehearsal.json', replay=True)
    assert replay.mode == 'replay'
    assert all(s.provenance == 'replay' and s.acceptance.task_live == 'not_run' for s in replay.history)
    assert originals == {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in root.rglob('*') if p.is_file()}
    return {'root':str(root),'stage':final.stage,'start':datetime.fromtimestamp(document.history[0].at,timezone.utc).isoformat(),'end':datetime.fromtimestamp(final.at,timezone.utc).isoformat(),'calls':calls,'external_checks':external_checks,'decay_points_checked':decay_points,'archive_cached_bodies':0,'replay_original_files_unchanged':len(originals)}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root',type=Path)
    args=parser.parse_args()
    print(json.dumps(audit(args.root.resolve()),indent=2))
