"""Runtime closure tests: chain decisions, routing guard, and breaker wiring.

These exercise the real FC-A/B/C structural interfaces through the FC-R data
module and a real SharedBreaker. No remote requests are sent.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from swarm.breaker import BreakerConfig, SharedBreaker
from swarm.failure_chain import (
    CAPABILITY_MISMATCH,
    CONFIRMED_REJECTION,
    UNKNOWN_EFFECT,
    FailureObservationFact,
    candidate_identity,
    decide,
    guard_provider,
)
from swarm.fault_observations import FaultObservation, FaultObservationStore


def _config() -> BreakerConfig:
    return BreakerConfig(
        window_seconds=100.0,
        aggregation_period_seconds=10.0,
        failure_threshold=2,
        min_samples=1,
        cooldown_seconds=60.0,
        probe_ttl_seconds=30.0,
    )


def test_decide_all_branches():
    assert decide(CONFIRMED_REJECTION, True).action == "switch"
    assert decide(CONFIRMED_REJECTION, True).record_observation is True
    assert decide(CONFIRMED_REJECTION, False).action == "exit_candidates_rejected"
    assert decide(UNKNOWN_EFFECT, True).action == "stop_unknown_effect"
    assert decide("budget_exhausted", True).action == "stop_budget_exhausted"
    assert decide(CAPABILITY_MISMATCH, True).action == "stop_capability_mismatch"
    assert decide(None, True).action == "stop_local_failure"
    assert decide(None, True).record_observation is False


def test_candidate_identity():
    assert candidate_identity("evomap", "m1") == "evomap:m1"


def test_failure_observation_fact_validation():
    fact = FailureObservationFact(
        run_id="r", task_id="t", request_id="q", attempt=0,
        provider="evomap", model="m", failure_class=CONFIRMED_REJECTION,
        normalized_reason="billing_arrearage", occurred_at=1.0,
    )
    assert fact.switched_to is None
    assert fact.cost_state is None
    with pytest.raises(Exception):
        FailureObservationFact(
            run_id="r", task_id="t", request_id="q", attempt=-1,
            provider="evomap", model="m", failure_class=CONFIRMED_REJECTION,
            normalized_reason="x", occurred_at=1.0,
        )


def test_guard_provider_suspends_then_blocks(tmp_path: Path):
    store = FaultObservationStore(tmp_path / "faults.jsonl", "swarm")
    store.append(FaultObservation(
        run_id="swarm", task_id="t1", request_id="q1", attempt=0,
        provider="evomap", model="m", failure_class=CONFIRMED_REJECTION,
        normalized_reason="billing_arrearage", occurred_at=time.time(),
    ))
    breaker = SharedBreaker(tmp_path / "breaker.sqlite3", "swarm", _config())
    breaker.observe(store, now=time.time())
    assert breaker.view("evomap", "billing_arrearage").state == "suspended"
    guard = guard_provider(breaker, "evomap", "worker-1", now=time.time())
    assert guard.routable is False
    assert guard.blocked_reasons == ("billing_arrearage",)


def test_guard_provider_healthy_is_routable(tmp_path: Path):
    breaker = SharedBreaker(tmp_path / "breaker.sqlite3", "swarm", _config())
    guard = guard_provider(breaker, "evomap", "worker-1", now=time.time())
    assert guard.routable is True
    assert guard.claims == ()
