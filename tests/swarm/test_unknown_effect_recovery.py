"""Unknown remote effects survive Worker/process replacement with settled costs.

Only the executor boundary is synthetic. Routing, leases, status loading and
SQLite storage are real; the spawned process runs a mock fixture, never live.
"""
from __future__ import annotations

import json
import multiprocessing
from dataclasses import replace

import pytest

from contracts.identity import AgentId
from swarm.worker_loop import FixtureExecutor, Worker, WorkerConfig
from tests.swarm.test_failure_chain_runtime import (
    _claim, _events, _executor, _facts, _failure, _reservations, _worker_config,
)


def _recovery_config(tmp_path):
    config = _worker_config(tmp_path, prices=True)
    return config.model_copy(update={
        "max_idle": 1,
        "locality": config.locality.model_copy(update={"dependency_of": ("fixture-0",)}),
    })


def _recover(config_json, output):
    config = WorkerConfig.model_validate_json(config_json)
    executor = _executor(result=_failure("unknown_effect", known_usage=True, reason="read_timeout"))
    worker = Worker(config, executor)
    status = worker.run()
    output.write_text(json.dumps({
        "status": status, "calls": executor.execute.call_count,
        "reservations": _reservations(worker),
        "task": worker.ledger.get("fixture-0").model_dump(mode="json"),
    }), encoding="utf-8")


@pytest.mark.parametrize("other_worker", [False, True], ids=["same-worker-restart", "other-worker-takeover"])
def test_settled_unknown_effect_never_resends_after_process_restart(tmp_path, other_worker):
    config = _recovery_config(tmp_path)
    executor = _executor(result=_failure("unknown_effect", known_usage=True, reason="read_timeout"))
    worker = Worker(config, executor)
    first = worker.run()
    assert first["state"] == "sleeping", _events(worker)
    assert executor.execute.call_count == 1
    before = _reservations(worker)
    assert len(before) == 1 and before[0]["status"] == "settled"
    assert before[0]["tokens"] == 2 and before[0]["cost"] == "estimated"
    budget = worker.budget.snapshot()
    assert budget.sleeping is False and budget.reserved_estimate_usd == 0
    assert budget.admission_charged_usd < config.budget.max_cost_usd
    fact, = _facts(worker)
    assert fact.failure_class == "unknown_effect" and fact.cost_state == "settled"

    recovered_config = config.model_copy(update={"agent": AgentId(role="builder", instance=1)}) if other_worker else config
    output = tmp_path / "recovered.json"
    process = multiprocessing.get_context("spawn").Process(
        target=_recover, args=(recovered_config.model_dump_json(), output))
    process.start()
    process.join(45)
    if process.is_alive():
        process.terminate()
        process.join(5)
    assert process.exitcode == 0
    recovered = json.loads(output.read_bytes())
    # Behavior first: the original bug really calls the external boundary again.
    assert recovered["calls"] == 0, recovered
    assert recovered["reservations"] == before
    assert recovered["task"]["status"] == "blocked"
    assert recovered["task"]["result_id"] is None
    assert recovered["task"]["attempts"] == 1
    restarted = Worker(recovered_config, _executor())
    assert restarted.router.choose(restarted.worker_id, config.locality, config.capabilities) is None
    assert restarted.leases.acquire("fixture-0", restarted.worker_id, locality=config.locality) is None
    assert restarted.budget.snapshot().sleeping is False


def test_confirmed_rejection_still_switches_and_success_stays_completed(tmp_path):
    config = _recovery_config(tmp_path)
    rejected = _executor(result=_failure(known_usage=True, reason="rate_limited"))
    success = _executor()
    worker = Worker(config, rejected, candidates=[rejected, success])
    signal, lease = _claim(worker)
    result = worker._process(signal, lease)
    assert result == "completed", _events(worker)
    assert rejected.execute.call_count == success.execute.call_count == 1
    assert worker.ledger.get(signal.task_id).status == "completed"
    assert all(row["status"] == "settled" for row in _reservations(worker))
    unused = _executor()
    restarted = Worker(config, unused)
    restarted.run()
    assert unused.execute.call_count == 0
    assert restarted.ledger.get(signal.task_id).status == "completed"


def test_unknown_effect_after_real_lease_handoff_cannot_be_sent_by_successor(tmp_path):
    config = _recovery_config(tmp_path)
    executor = _executor()
    worker = Worker(config, executor)
    signal, lease = _claim(worker)
    successor_config = config.model_copy(update={"agent": AgentId(role="builder", instance=2)})
    transfers = []

    def execute(*args, **kwargs):
        current = next(item for item in worker.leases.snapshot() if item.task_id == signal.task_id)
        transfers.append(worker.leases.handoff(current, successor_config.worker_id))
        return _failure("unknown_effect", known_usage=True, reason="read_timeout")

    executor.execute.side_effect = execute
    outcome = worker._process(signal, lease)
    assert outcome == "sleeping", _events(worker)
    assert executor.execute.call_count == len(transfers) == 1
    assert transfers[0].status == "handoff"
    before = _reservations(worker)
    assert before[0]["status"] == "settled" and worker.budget.snapshot().sleeping is False
    successor_executor = _executor(result=_failure("unknown_effect", known_usage=True, reason="read_timeout"))
    successor = Worker(successor_config, successor_executor)
    successor.run()
    assert successor_executor.execute.call_count == 0
    assert _reservations(successor) == before
    assert successor.leases.acquire(signal.task_id, successor.worker_id, locality=config.locality) is None
    assert successor.ledger.get(signal.task_id).result_id is None


def test_unknown_effect_candidate_is_not_published_or_retried(tmp_path):
    config = _recovery_config(tmp_path)
    fixture = FixtureExecutor()
    executor = _executor(effect=lambda *args, **kwargs: replace(
        fixture.execute(*args, **kwargs),
        metadata={"classification": "unknown_effect", "normalized_reason": "read_timeout"}))
    worker = Worker(config, executor)
    signal, lease = _claim(worker)
    outcome = worker._process(signal, lease)
    assert outcome == "sleeping", _events(worker)
    assert executor.execute.call_count == 1
    assert worker.ledger.get(signal.task_id).status == "blocked"
    assert worker.ledger.get(signal.task_id).result_id is None
    assert not worker.assets.promotions()
    assert worker.budget.snapshot().sleeping is False
    assert _reservations(worker)[0]["status"] == "settled"
    successor_executor = _executor()
    Worker(config, successor_executor).run()
    assert successor_executor.execute.call_count == 0
