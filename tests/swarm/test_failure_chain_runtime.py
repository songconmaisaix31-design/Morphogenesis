"""Real Worker chain regressions; mocks replace only the Executor boundary.

The existing local fixture's two synthetic tokens are not remote billing evidence.
Unobserved usage stays None; assertions run outside Worker exception handlers.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from swarm.breaker import BreakerConfig, SharedBreaker
from swarm.cli import demo_config, seed_demo
from swarm.failure_chain import (
    CAPABILITY_MISMATCH, CONFIRMED_REJECTION, UNKNOWN_EFFECT,
    FailureObservationFact, candidate_identity, decide,
)
from swarm.fault_observations import FaultObservation, FaultObservationStore
from swarm.models import BudgetPolicy, ExecutionBound, RunLimits
from swarm.pheromone import PheromoneField
from swarm.task_ledger import TaskLedger
from swarm.worker_loop import ExecutionResult, FixtureExecutor, Worker, WorkerConfig


# Helpers are shared only by these two owned files, without production test hooks.
FIXTURE_USAGE = {"usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}


def _config() -> BreakerConfig:
    return BreakerConfig(
        window_seconds=600.0, aggregation_period_seconds=10.0,
        failure_threshold=2, min_samples=1, cooldown_seconds=300.0,
        probe_ttl_seconds=30.0,
    )


def _worker_config(tmp_path: Path, *, prices=False, max_cost=2.0,
                   max_attempts=20, per_task=10) -> WorkerConfig:
    target, state = seed_demo(tmp_path / "fixture")
    config = WorkerConfig.model_validate_json(demo_config(target, state, 0, max_cost))
    policy = BudgetPolicy(
        max_cost_usd=max_cost, unbounded_reservation_usd=0.2,
        prices=({"provider": "local", "model": "fixture", "input_usd_per_million": 1.0,
                 "output_usd_per_million": 1.0} if prices else None),
        limits=RunLimits(max_attempts=max_attempts, max_attempts_per_task=per_task),
    )
    # seed_demo persists default run limits. Seed a separate run with this test's
    # immutable limits; do not change the limits of an already-created run.
    config = config.model_copy(update={
        "state": tmp_path / "chain-state", "budget": policy,
        "lease_seconds": 60.0, "sleep_seconds": 0.001,
    })
    ledger = TaskLedger(config.state / "tasks.sqlite3", config.swarm_id, limits=policy.limits)
    field = PheromoneField(config.state / "field.sqlite3", ledger=ledger)
    for task in TaskLedger(state / "tasks.sqlite3", config.swarm_id).snapshot():
        ledger.enqueue(task.signal, acceptance=task.acceptance)
        field.deposit(task.signal)
    return config


def _failure(classification=CONFIRMED_REJECTION, *, known_usage=False,
             reason="billing_arrearage") -> ExecutionResult:
    return ExecutionResult(
        None, FIXTURE_USAGE if known_usage else None, uncertain=not known_usage,
        metadata={"classification": classification, "normalized_reason": reason},
    )


def _executor(provider="local", *, result=None, effect=None) -> Mock:
    """Successful output uses the existing FixtureExecutor and its real file edits."""
    fixture = FixtureExecutor()
    executor = Mock(spec_set=FixtureExecutor, wraps=fixture)
    executor.provenance = fixture.provenance
    executor.usage_source = fixture.usage_source
    executor.original_run_uri = fixture.original_run_uri
    executor.bound.return_value = ExecutionBound(
        provider=provider, model="fixture", input_tokens=1, max_output_tokens=1,
        provider_enforced=False, request_bound="unbounded",
    )
    if effect is not None:
        executor.execute.side_effect = effect
    elif result is not None:
        executor.execute.return_value = result
    return executor


def _worker(config, candidates):
    return Worker(config, candidates[0], candidates=candidates, breaker_config=_config())


def _claim(worker, task_id="fixture-0"):
    signal = worker.ledger.get(task_id).signal
    lease = worker.leases.acquire(task_id, worker.worker_id, ttl_seconds=60.0,
                                  locality=worker.config.locality)
    assert lease is not None
    return signal, lease


def _reservations(worker):
    # Fresh connection reads durable authority, not a mock or cached snapshot.
    with sqlite3.connect(worker.budget.path) as db:
        db.row_factory = sqlite3.Row
        return [dict(row) for row in db.execute(
            "SELECT * FROM budget_reservations WHERE swarm_id=? ORDER BY created_at,rowid",
            (worker.config.swarm_id,),
        )]


def _events(worker):
    return [json.loads(path.read_bytes()) for path in (worker.state / "audit").rglob("*.json")]


def _facts(worker):
    read = FaultObservationStore(worker.state / "fault_observations.jsonl", worker.config.swarm_id).read()
    assert read.issues == ()
    return read.records


def _assert_calls(executor, signal, lease, expected=1):
    assert executor.execute.call_count == expected
    if expected:
        args, kwargs = executor.execute.call_args
        assert args[0] == signal
        assert args[1].task_id == signal.task_id
        assert args[1].attempt == lease.token - 1
        assert Path(args[2]) == Path(signal.workspace)
        assert kwargs["base_revision"] and kwargs["base_head"]


def test_decide_all_branches():
    assert decide(CONFIRMED_REJECTION, True).action == "switch"
    assert decide(CONFIRMED_REJECTION, True).record_observation is True
    assert decide(CONFIRMED_REJECTION, False).action == "exit_candidates_rejected"
    assert decide(UNKNOWN_EFFECT, True).action == "stop_unknown_effect"
    assert decide("budget_exhausted", True).action == "stop_budget_exhausted"
    assert decide(CAPABILITY_MISMATCH, True).action == "stop_capability_mismatch"
    assert decide(None, True).action == "stop_local_failure"
    assert decide(None, True).record_observation is False


def test_failure_observation_fact_validation():
    fact = FailureObservationFact(
        run_id="r", task_id="t", request_id="q", attempt=0,
        provider="evomap", model="m", failure_class=CONFIRMED_REJECTION,
        normalized_reason="billing_arrearage", occurred_at=1.0,
    )
    assert fact.switched_to is fact.cost_state is None
    assert candidate_identity("evomap", "m") == "evomap:m"
    with pytest.raises(ValidationError):
        FailureObservationFact(**{**fact.model_dump(), "attempt": -1})


def test_confirmed_rejection_switches_provider_and_submits_success(tmp_path):
    config = _worker_config(tmp_path)
    first = _executor("alpha", result=_failure())
    second = _executor("beta")
    worker = _worker(config, [first, second])
    assert isinstance(worker.fault_observation_store, FaultObservationStore)
    assert isinstance(worker.shared_breaker, SharedBreaker)
    append = Mock(wraps=worker.fault_observation_store.append)
    worker.fault_observation_store.append = append
    signal, lease = _claim(worker)
    admitted_before_send = []
    fixture = FixtureExecutor()

    def execute(*args, **kwargs):
        admitted_before_send.append(_reservations(worker))
        return fixture.execute(*args, **kwargs)

    second.execute.side_effect = execute
    outcome = worker._process(signal, lease)

    assert outcome == "completed", _events(worker)
    _assert_calls(first, signal, lease)
    _assert_calls(second, signal, lease)
    assert len(admitted_before_send) == 1
    assert [row["status"] for row in admitted_before_send[0]] == ["uncertain", "pending"]
    rows = _reservations(worker)
    assert [row["request_id"] for row in rows] == [f"fixture-0:{lease.token}:0", f"fixture-0:{lease.token}:1"]
    assert {row["task_id"] for row in rows} == {signal.task_id}
    assert rows[0]["tokens"] is None and rows[1]["tokens"] == 2
    assert all(row["cost"] == "unknown" and row["admitted_usd"] is None for row in rows)
    snapshot = worker.budget.snapshot()
    assert snapshot.reserved_estimate_usd == pytest.approx(0.4)
    assert snapshot.admission_charged_usd == 0
    assert snapshot.actual_cost_usd is snapshot.estimated_cost_usd is None
    fact, = _facts(worker)
    append.assert_called_once()
    submitted, = append.call_args.args
    assert isinstance(submitted, FaultObservation)
    assert submitted == fact  # Includes the one persisted observation_id.
    logged = [json.loads(line) for line in worker.fc_log.path.read_text().splitlines()]
    logged_fact, = [row["fault_observation"] for row in logged if row["event"] == "fault_observation"]
    assert logged_fact["observation_id"] == fact.observation_id
    assert (fact.provider, fact.switched_to, fact.cost_state) == ("alpha", "beta:fixture", "unknown")
    assert fact.request_id == rows[0]["request_id"] and fact.attempt == 0
    task = worker.ledger.get(signal.task_id)
    assert task.status == "completed" and task.effect_applied and task.result_id
    assert (worker.target / "module_0/task_0.py").read_text() == "def answer():\n    return 0\n"
    event, = _events(worker)
    assert event["outcome"] == "promoted" and event["provenance"] == "mock"
    assert event["interface_live"] == event["task_live"] == "not_run"


def test_worker_observation_suspends_provider_and_routes_later_candidate(tmp_path):
    """Mutation target: real Worker failure drives observe -> transition -> routing."""
    config = _worker_config(tmp_path)
    rejected = _executor("alpha", result=_failure())
    first_worker = _worker(config, [rejected])
    signal, lease = _claim(first_worker)
    first_outcome = first_worker._process(signal, lease)
    assert first_outcome == "rejected", _events(first_worker)
    _assert_calls(rejected, signal, lease)
    fact, = _facts(first_worker)
    assert fact.provider == "alpha" and fact.failure_class == CONFIRMED_REJECTION

    blocked = _executor("alpha", result=_failure())
    fallback = _executor("beta", result=_failure(reason="rate_limited"))
    next_worker = _worker(config, [blocked, fallback])
    next_signal, next_lease = _claim(next_worker, "fixture-1")
    outcome = next_worker._process(next_signal, next_lease)

    assert outcome == "rejected", _events(next_worker)
    # Check behavior first: mutation must change an actual executor invocation.
    _assert_calls(blocked, next_signal, next_lease, expected=0)
    _assert_calls(fallback, next_signal, next_lease)
    assert blocked.bound.call_count == fallback.bound.call_count == 1
    rows = _reservations(next_worker)
    assert len(rows) == 2
    assert rows[-1]["request_id"] == f"fixture-1:{next_lease.token}:1"
    assert json.loads(rows[-1]["body"])["bound"]["provider"] == "beta"
    breaker = SharedBreaker(config.state / "breaker.sqlite3", config.swarm_id, _config())
    assert breaker.view("alpha", "billing_arrearage").state == "suspended"
    assert any(row["event"] == "aggregate" and row["from_state"] == "insufficient_evidence"
               and row["to_state"] == "suspended" for row in breaker.audit())


def test_all_suspended_candidates_exit_without_reservation_or_send(tmp_path):
    config = _worker_config(tmp_path)
    initial = [_executor(provider, result=_failure()) for provider in ("alpha", "beta")]
    worker = _worker(config, initial)
    signal, lease = _claim(worker)
    outcome = worker._process(signal, lease)
    assert outcome == "rejected", _events(worker)
    for executor in initial:
        _assert_calls(executor, signal, lease)

    candidates = [_executor(provider, result=_failure()) for provider in ("alpha", "beta")]
    other = _worker(config, candidates)
    next_signal, next_lease = _claim(other, "fixture-1")
    before = _reservations(other)
    outcome = other._process(next_signal, next_lease)

    assert outcome == "sleeping", _events(other)
    for executor in candidates:
        _assert_calls(executor, next_signal, next_lease, expected=0)
        assert executor.bound.call_count == 1  # One bounded pass, no wraparound.
    assert _reservations(other) == before
    assert len(_facts(other)) == 2
    event, = [row for row in _events(other) if row["task_id"] == "fixture-1"]
    assert event["outcome"] == "all_candidates_suspended"
    assert other.ledger.get("fixture-1").result_id is None
