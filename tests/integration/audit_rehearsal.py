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


def gateway_receipt(task_root: Path, result: dict, model: str, experience: list[dict], *, provenance: str = 'live') -> dict:
    """Verify HTTP evidence against identity, applied source and actual Gene input."""
    assert not (task_root / 'cli').exists(), 'gateway evidence must not masquerade as CLI turns'
    evidence = task_root / 'gateway'
    request = json.loads((evidence / 'request.json').read_text(encoding='utf-8'))
    response = json.loads((evidence / 'response.json').read_text(encoding='utf-8'))
    proposal = json.loads((evidence / 'proposal.json').read_text(encoding='utf-8'))
    config = json.loads((task_root / 'config.json').read_text(encoding='utf-8'))
    assert request['executor'] == 'evomap' and request['provenance'] == provenance
    assert request['method'] == 'POST' and request['url'] == 'https://api.evomap.ai/v1/chat/completions'
    assert request['max_requests'] == 1
    assert request['run_id'] == result['run_id'] == config['run_id']
    assert request['attempt'] == result['attempt']
    payload = request['request']
    assert payload['model'] == model and payload['stream'] is False
    assert len(payload['messages']) == 2
    assert [m['role'] for m in payload['messages']] == ['system', 'user']
    supplied = json.loads(payload['messages'][1]['content'])
    assert supplied['experience'] == experience, 'actual injected Gene content differs'
    assert supplied['TASK'] == (Path(config['workspace']) / 'TASK.md').read_text(encoding='utf-8')
    assert response['http_status'] == 200 and response['error_kind'] is None
    assert response['cost_usd'] is None
    assert response['finished_at'] >= request['started_at']
    assert 0 <= response['elapsed_seconds'] <= config['timeout_seconds']
    body = response['body']
    assert isinstance(body['model'], str) and body['model'], 'missing returned model'
    usage = body['usage']
    assert all(type(usage[k]) is int and usage[k] >= 0 for k in ('prompt_tokens', 'completion_tokens', 'total_tokens'))
    assert usage['prompt_tokens'] + usage['completion_tokens'] == usage['total_tokens'] == result['usage']['tokens']
    assert usage['total_tokens'] <= config['max_tokens']
    assert usage['completion_tokens'] <= payload['max_tokens']
    assert len(body['choices']) == 1
    choice = body['choices'][0]
    assert choice['finish_reason'] == 'stop' and choice['message']['role'] == 'assistant'
    assert not any(choice['message'].get(k) for k in ('refusal', 'tool_calls', 'function_call'))
    assert json.loads(choice['message']['content']) == proposal
    assert proposal['content'] == (Path(config['workspace']) / 'sample.py').read_text(encoding='utf-8')
    assert proposal['adopted_gene_ids'] == [gene['ref']['gene_id'] for gene in experience]
    return {'http_requests': 1, 'http_status': 200, 'requested_model': model, 'returned_model': body['model'],
            'started_at': request['started_at'], 'finished_at': response['finished_at'],
            'elapsed_seconds': response['elapsed_seconds'], 'usage': usage,
            'injected_gene_ids': [gene['ref']['gene_id'] for gene in experience],
            'adopted_gene_ids': proposal['adopted_gene_ids']}


def audit(root: Path) -> dict[str, object]:
    originals = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in root.rglob('*') if p.is_file()}
    document = read_rehearsal(root / 'rehearsal.json')
    final = document.current
    executor = getattr(final, 'executor', 'codex')
    model = getattr(final, 'model', None) or 'gpt-5.6-luna'
    assert document.mode == 'live' and final.stage == 'completed'
    assert final.model_calls_started == 2 and final.cost_usd is None
    assert final.acceptance.task_live == 'passed'
    first, second = final.results
    assert first.attempt.agent.role == second.attempt.agent.role == 'builder'
    assert first.attempt.agent.instance == 0 and second.attempt.agent.instance == 1
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
                assert gene.tau_seconds == 10
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
        assert result.status == 'succeeded' and result.verdict.passed is True
        assert result.usage.cost_usd is None
        assert json.loads((root/name/'result.json').read_text(encoding='utf-8')) == result.model_dump(mode='json')
        if executor == 'evomap':
            experience = [] if name == 'repair' else [json.loads((root/'repair/gene.json').read_text(encoding='utf-8'))]
            if experience:
                assert experience[0]['source_attempt'] == first.attempt.model_dump(mode='json')
                assert experience[0]['ref'] == first_gene.ref.model_dump(mode='json')
                first_proposal = json.loads((root/'repair/gateway/proposal.json').read_text(encoding='utf-8'))
                assert any(first_proposal['content'] in strategy for strategy in experience[0]['strategy'])
            receipt = gateway_receipt(root/name, result.model_dump(mode='json'), model, experience)
            calls.append({'task':name,'agent':result.attempt.agent.model_dump(),'tokens':result.usage.tokens,'cost_usd':None,**receipt})
            continue
        assert executor == 'codex'
        cli = root / name / 'cli'
        events = [json.loads(line) for line in (cli/'codex.jsonl').read_text().splitlines() if line.strip()]
        turns = [event for event in events if event.get('type') == 'turn.completed']
        assert len(turns) == 1
        assert sum(e.get('type') == 'turn.started' for e in events) == 1
        usage = turns[0]['usage']
        assert usage['input_tokens']+usage['output_tokens'] == result.usage.tokens
        assert result.status == 'succeeded' and result.verdict.passed is True
        argv = json.loads((cli/'command.json').read_text())
        assert argv[argv.index('--model')+1] == model
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
    return {'root':str(root),'executor':executor,'model':model,'stage':final.stage,'start':datetime.fromtimestamp(document.history[0].at,timezone.utc).isoformat(),'end':datetime.fromtimestamp(final.at,timezone.utc).isoformat(),'calls':calls,'external_checks':external_checks,'decay_points_checked':decay_points,'archive_cached_bodies':0,'replay_original_files_unchanged':len(originals)}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root',type=Path)
    args=parser.parse_args()
    print(json.dumps(audit(args.root.resolve()),indent=2))
