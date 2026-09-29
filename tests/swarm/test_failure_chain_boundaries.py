"""Failure-chain invariants through Worker._process, never direct settlement."""
from __future__ import annotations

import json

import pytest

from swarm.worker_loop import FixtureExecutor
from tests.swarm.test_failure_chain_runtime import (
    _assert_calls, _claim, _events, _executor, _facts, _failure, _reservations,
    _worker, _worker_config,
)


@pytest.mark.parametrize("known_usage", [False, True])
def test_unknown_effect_stops_chain_and_preserves_real_usage_state(tmp_path, known_usage):
    config = _worker_config(tmp_path, prices=known_usage)
    first = _executor(result=_failure("unknown_effect", known_usage=known_usage, reason="read_timeout"))
    later = _executor()
    worker = _worker(config, [first, later])
    signal, lease = _claim(worker)

    outcome = worker._process(signal, lease)

    assert outcome == "sleeping", _events(worker)
    _assert_calls(first, signal, lease)
    _assert_calls(later, signal, lease, expected=0)
    assert later.bound.call_count == 0
    row, = _reservations(worker)
    assert row["status"] == ("settled" if known_usage else "uncertain")
    assert row["tokens"] == (2 if known_usage else None)
    assert row["reserved_usd"] == 0.2
    fact, = _facts(worker)
    assert fact.failure_class == "unknown_effect" and fact.switched_to is None
    assert fact.cost_state == ("settled" if known_usage else "unknown")
    assert worker.ledger.get(signal.task_id).result_id is None
    assert not worker.assets.promotions()
    if not known_usage:
        snapshot = worker.budget.snapshot()
        assert snapshot.tokens is snapshot.estimated_cost_usd is snapshot.actual_cost_usd is None
        assert snapshot.reserved_estimate_usd == 0.2 and snapshot.reason == "unknown_usage"
        restarted = _worker(config, [first, later])
        restart_outcome = restarted.run()
        assert restart_outcome["state"] == "sleeping"
        assert first.execute.call_count == 1 and later.execute.call_count == 0
        assert _reservations(restarted) == [row]


def test_known_usage_unknown_cost_blocks_next_candidate_and_restart(tmp_path):
    config = _worker_config(tmp_path)  # Valid tokens without model prices leave cost unknown.
    first = _executor("alpha", result=_failure(known_usage=True))
    later = _executor("beta")
    worker = _worker(config, [first, later])
    signal, lease = _claim(worker)

    outcome = worker._process(signal, lease)

    assert outcome == "sleeping", _events(worker)
    _assert_calls(first, signal, lease)
    _assert_calls(later, signal, lease, expected=0)
    row, = _reservations(worker)
    assert row["status"] == "uncertain" and row["tokens"] == 2
    assert row["usage_metering"] == "verified" and row["cost"] == "unknown"
    assert row["estimate_usd"] is row["admitted_usd"] is None
    snapshot = worker.budget.snapshot()
    assert snapshot.reason == "unknown_cost" and snapshot.reserved_estimate_usd == 0.2
    assert snapshot.tokens == 2 and snapshot.actual_cost_usd is snapshot.estimated_cost_usd is None
    fact, = _facts(worker)
    assert fact.switched_to is None  # Considered fallback is not an admitted request.
    event, = _events(worker)
    assert event["outcome"] == "unknown_cost"
    restarted = _worker(config, [first, later])
    restart_outcome = restarted.run()
    assert restart_outcome["state"] == "sleeping"
    assert first.execute.call_count == 1 and later.execute.call_count == 0
    assert _reservations(restarted) == [row]


@pytest.mark.parametrize("known_usage", [False, True])
@pytest.mark.parametrize("gate", ["capacity", "task_attempts", "run_attempts"])
def test_chain_cumulative_budget_and_attempts_limit_actual_sends(tmp_path, known_usage, gate):
    config = _worker_config(
        tmp_path, prices=known_usage, max_cost=0.5 if gate == "capacity" else 2.0,
        per_task=2 if gate == "task_attempts" else 10,
        max_attempts=2 if gate == "run_attempts" else 20,
    )
    # Cross-provider unknown holds; same priced model for the known-usage control.
    providers = ["local"] * 3 if known_usage else ["alpha", "beta", "gamma"]
    candidates = [_executor(provider, result=_failure(known_usage=known_usage)) for provider in providers]
    worker = _worker(config, candidates)
    signal, lease = _claim(worker)
    before_each_send = []

    def rejected(*args, **kwargs):
        before_each_send.append(_reservations(worker))
        return _failure(known_usage=known_usage)

    for executor in candidates:
        executor.execute.side_effect = rejected
    outcome = worker._process(signal, lease)

    assert outcome == "sleeping", _events(worker)
    assert [executor.execute.call_count for executor in candidates] == [1, 1, 0]
    for executor in candidates[:2]:
        _assert_calls(executor, signal, lease)
    assert [len(rows) for rows in before_each_send] == [1, 2]
    assert all(rows[-1]["status"] == "pending" for rows in before_each_send)
    rows = _reservations(worker)
    assert len(rows) == sum(executor.execute.call_count for executor in candidates) == 2
    assert [row["request_id"] for row in rows] == [f"fixture-0:{lease.token}:{index}" for index in range(2)]
    assert {row["task_id"] for row in rows} == {signal.task_id}
    assert [json.loads(row["body"])["bound"]["provider"] for row in rows] == providers[:2]
    snapshot = worker.budget.snapshot()
    assert snapshot.reserved_estimate_usd == pytest.approx(0 if known_usage else 0.4)
    assert snapshot.admission_charged_usd == pytest.approx(0.4 if known_usage else 0)
    assert snapshot.reserved_estimate_usd + snapshot.admission_charged_usd == pytest.approx(0.4)
    assert [row["tokens"] for row in rows] == ([2, 2] if known_usage else [None, None])
    if not known_usage:
        assert snapshot.tokens is snapshot.estimated_cost_usd is None
        assert all(row["admitted_usd"] is None and row["status"] == "uncertain" for row in rows)
    event, = _events(worker)
    assert event["outcome"] == {"capacity": "swarm_reservation_capacity",
                                 "task_attempts": "max_attempts_per_task",
                                 "run_attempts": "max_attempts"}[gate]
    facts = _facts(worker)
    assert [fact.switched_to for fact in facts] == [f"{providers[1]}:fixture", None]


@pytest.mark.parametrize("candidate_count", [1, 2, 4])
def test_rejected_candidates_exit_after_one_pass(tmp_path, candidate_count):
    config = _worker_config(tmp_path)
    candidates = [_executor(f"provider-{index}", result=_failure()) for index in range(candidate_count)]
    worker = _worker(config, candidates)
    signal, lease = _claim(worker)

    outcome = worker._process(signal, lease)

    assert outcome == "rejected", _events(worker)
    for executor in candidates:
        _assert_calls(executor, signal, lease)
        assert executor.bound.call_count == 1
    rows = _reservations(worker)
    assert len(rows) == candidate_count
    assert [row["request_id"] for row in rows] == [f"fixture-0:{lease.token}:{i}" for i in range(candidate_count)]
    facts = _facts(worker)
    assert len(facts) == candidate_count and facts[-1].switched_to is None
    assert [fact.attempt for fact in facts] == list(range(candidate_count))
    event, = _events(worker)
    assert event["outcome"] == "all_candidates_rejected"
    assert worker.ledger.get(signal.task_id).result_id is None


def test_lost_lease_after_successful_execution_prevents_submission(tmp_path):
    config = _worker_config(tmp_path, prices=True)
    first, later = _executor(), _executor()
    worker = _worker(config, [first, later])
    signal, lease = _claim(worker)
    original = (worker.target / "module_0/task_0.py").read_bytes()
    results, handoffs = [], []
    fixture = FixtureExecutor()

    def lose_lease(*args, **kwargs):
        result = fixture.execute(*args, **kwargs)
        results.append(result)
        # Real lease handoff, without replacing keeper, submit, validation or ledger.
        # Snapshot/fixture work may span a real renewal; use its current expiry.
        current = next(item for item in worker.leases.snapshot() if item.task_id == signal.task_id)
        handoffs.append(worker.leases.handoff(current, "replacement-worker"))
        return result

    first.execute.side_effect = lose_lease
    outcome = worker._process(signal, lease)

    assert outcome == "failed", _events(worker)
    assert len(results) == len(handoffs) == 1 and results[0].candidate is not None
    _assert_calls(first, signal, lease)
    _assert_calls(later, signal, lease, expected=0)
    task = worker.ledger.get(signal.task_id)
    assert task.status == "handoff" and not task.effect_applied
    assert task.result_id is task.result is None
    assert not worker.assets.promotions()
    assert (worker.target / "module_0/task_0.py").read_bytes() == original
    row, = _reservations(worker)
    assert row["status"] == "settled" and row["tokens"] == 2
    event, = _events(worker)
    assert event["outcome"] == "stale_lease"
    assert event["execution"]["failure_reason"] == "stale_lease"


@pytest.mark.parametrize("classification,outcome", [
    ("capability_mismatch", "rejected"), ("budget_exhausted", "sleeping"),
])
def test_non_rejection_classification_never_switches(tmp_path, classification, outcome):
    config = _worker_config(tmp_path, prices=True)
    first = _executor(result=_failure(classification, known_usage=True, reason=classification))
    later = _executor()
    worker = _worker(config, [first, later])
    signal, lease = _claim(worker)

    actual = worker._process(signal, lease)

    assert actual == outcome, _events(worker)
    _assert_calls(first, signal, lease)
    _assert_calls(later, signal, lease, expected=0)
    assert len(_reservations(worker)) == 1
    fact, = _facts(worker)
    assert fact.failure_class == classification and fact.switched_to is None
