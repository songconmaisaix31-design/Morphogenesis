import math
import sqlite3
import json

import pytest

from swarm.pheromone import PheromoneField
from swarm.task_ledger import TaskLedger
from swarm.feedback import trusted_facts, policy_diagnostics


def completed_fixture(root):
    from swarm.cli import seed_demo, demo_config
    from swarm.worker_loop import Worker, WorkerConfig
    target, state = seed_demo(root / "fixture")
    config = WorkerConfig.model_validate_json(demo_config(target, state, 0, 1.0)).model_copy(update={"energy": 1})
    worker = Worker(config)
    result = worker.run()
    assert result["state"] == "exhausted" and result["completed"] == 1, result
    return worker


def test_real_validated_result_read_rebuild_and_pair_crash_do_not_double_learn(tmp_path):
    worker = completed_fixture(tmp_path)
    facts = trusted_facts(worker.ledger, worker.assets.root)
    assert len(facts) == 1 and facts[0].kind == "validated_completion"
    assert facts == trusted_facts(worker.ledger, worker.assets.root)
    original = worker.field.pipe_history(worker.worker_id, "repair", prior=0.25)
    assert original.samples == 1
    task = worker.ledger.get(facts[0].task_id)
    with pytest.raises(RuntimeError, match="crash"):
        with worker.field.trusted_pair(facts[0]):
            worker.field.feedback(task.signal.signal_id, success=True)
            raise RuntimeError("crash before history and commit")
    assert worker.field.pipe_history(worker.worker_id, "repair", prior=0.25).samples == 1
    with worker.field.trusted_pair(facts[0]):
        worker.field.feedback(task.signal.signal_id, success=True)
        worker.router.reinforce(worker.worker_id, task.signal, success=True)
    assert worker.field.pipe_history(worker.worker_id, "repair", prior=0.25).samples == 1
    worker.field.synchronize(facts + facts)
    rebuilt = PheromoneField(tmp_path / "rebuilt.sqlite3", ledger=worker.ledger,
                              clock=lambda: facts[0].at + 86400 * 100)
    rebuilt.synchronize(facts)
    assert rebuilt.pipe_history(worker.worker_id, "repair", prior=0.25).weight == pytest.approx(0.25)
    with sqlite3.connect(rebuilt.path) as db:
        assert db.execute("SELECT samples,updated_at FROM learned_history").fetchone() == (1, facts[0].at)
    # Same completed authority cannot be relabelled as a second scientific reward.
    with pytest.raises(ValueError, match="kind"):
        rebuilt.synchronize(facts + [facts[0].model_copy(update={"kind": "scientific_result"})])
    assert rebuilt.pipe_history(worker.worker_id, "repair", prior=0.25).samples == 1


def test_two_legal_candidates_probabilities_change_and_readonly_recovery_never_executes(tmp_path, monkeypatch):
    from contracts.identity import AgentId
    from swarm.models import Signal
    from swarm.research.models import HostConfig
    from swarm.worker_loop import FixtureExecutor
    worker = completed_fixture(tmp_path)
    facts = trusted_facts(worker.ledger, worker.assets.root)
    host = HostConfig(ledger_path=str(worker.ledger.path), swarm_id=worker.ledger.swarm_id,
                      workspace=str(worker.target), worker_id=worker.worker_id,
                      agent=AgentId(role="builder", instance=0), authorized_scopes=("future",),
                      capabilities=("repair", "other"), assets_root=str(worker.assets.root),
                      evidence_root=str(worker.state / "evidence"))
    for name, capability in (("future-a", "repair"), ("future-b", "other")):
        worker.ledger.enqueue(Signal(task_id=name, workspace=str(worker.target), scope="future/" + name,
                                    required_capability=capability, kind="opportunity"))
    def forbidden(*args, **kwargs):
        raise AssertionError("diagnostics/rebuild must not call Executor")
    monkeypatch.setattr(FixtureExecutor, "execute", forbidden)
    monkeypatch.setattr(FixtureExecutor, "bound", forbidden)
    snapshot = {p: p.read_bytes() for p in worker.state.rglob("*") if p.is_file()}
    diagnostic = policy_diagnostics(host)
    probabilities = diagnostic["policy"]["probabilities"]
    assert len(probabilities) == 2 and probabilities[0] > probabilities[1]
    assert len(diagnostic["feedback"]) == 1
    assert snapshot == {p: p.read_bytes() for p in worker.state.rglob("*") if p.is_file()}
    rebuilt = policy_diagnostics(host, rebuild_to=tmp_path / "operator-derived.sqlite3")
    assert rebuilt["policy"]["probabilities"] == pytest.approx(probabilities, abs=1e-5)
    assert snapshot == {p: p.read_bytes() for p in worker.state.rglob("*") if p.is_file()}
    # Corrupted/wrong result identity cannot reuse the passing report as a reward.
    task = worker.ledger.get(facts[0].task_id)
    result = dict(task.result)
    result["candidate_asset_id"] = "wrong-asset"
    with sqlite3.connect(worker.ledger.path) as db:
        db.execute("UPDATE tasks SET result=? WHERE task_id=?", (json.dumps(result), task.signal.task_id))
    db.close()
    rejected = policy_diagnostics(host)
    assert rejected["feedback"] == []
    assert rejected["policy"]["probabilities"][0] == pytest.approx(rejected["policy"]["probabilities"][1], abs=1e-5)


def test_explicit_history_prior_keeps_old_default_and_original_anchor(tmp_path):
    clock = [1000.0]
    ledger = TaskLedger(tmp_path / "ledger.sqlite3", "policy", clock=lambda: clock[0])
    field = PheromoneField(tmp_path / "field.sqlite3", ledger=ledger,
                           tau_seconds=100, alpha=0.5, clock=lambda: clock[0])
    first = field.reinforce("worker", "pipe", 1.0, prior=0.25)
    assert first.weight == 0.625
    clock[0] += 100
    assert field.pipe_history("worker", "pipe").weight == pytest.approx(0.625 / math.e)
    assert field.pipe_history("worker", "pipe", prior=0.25).weight == pytest.approx(0.25 + 0.375 / math.e)
    with sqlite3.connect(field.path) as db:
        assert db.execute("SELECT updated_at,samples FROM pipe_history").fetchone() == (1000.0, 1)
    second = field.reinforce("worker", "pipe", 0, prior=0.25)
    assert second.weight == pytest.approx((0.25 + 0.375 / math.e) / 2)
    assert second.samples == 2
    with pytest.raises(ValueError, match="prior"):
        field.pipe_history("worker", "pipe", prior=float("nan"))
