"""Causal controls for opt-in claim charging; no remote executor is involved."""

import pytest
from types import SimpleNamespace

from swarm.worker_loop import Worker
from tests.swarm.test_worker_runtime import configured, events, KnownFailure


@pytest.mark.parametrize("policy,expected", [("cycle", 0), ("claim", 1)])
def test_lost_claim_does_not_spend_claim_energy(tmp_path, monkeypatch, policy, expected):
    config = configured(tmp_path, energy=1, energy_policy=policy, max_senses=3)
    worker = Worker(config)
    original = worker.leases.acquire
    calls = 0

    def contend_once(*args, **kwargs):
        nonlocal calls
        calls += 1
        return None if calls == 1 else original(*args, **kwargs)

    monkeypatch.setattr(worker.leases, "acquire", contend_once)
    result = worker.run()
    assert result["completed"] == expected
    assert result["remaining_energy"] == 0
    assert result["senses"] == 1 + expected
    assert len(events(config)) == expected


def test_continuous_contention_stops_and_resume_keeps_sense_limit(tmp_path, monkeypatch):
    config = configured(tmp_path, energy=2, energy_policy="claim", max_senses=3)
    worker = Worker(config)
    monkeypatch.setattr(worker.leases, "acquire", lambda *a, **kw: None)
    result = worker.run()
    assert result["reason"] == "sense_limit"
    assert result["remaining_energy"] == 2
    assert result["senses"] == 3
    assert worker.budget.snapshot().pending_reservations == 0
    assert Worker(config).run()["reason"] == "sense_limit"
    assert events(config) == []


def test_claim_energy_charges_rejected_execution(tmp_path):
    config = configured(tmp_path, energy=1, energy_policy="claim", max_senses=3)
    result = Worker(config, KnownFailure()).run()
    assert result["remaining_energy"] == 0
    assert result["completed"] == 0
    assert len(events(config)) == 1


def test_restart_cannot_silently_change_policy(tmp_path):
    config = configured(tmp_path, energy=1)
    Worker(config).run()
    with pytest.raises(ValueError, match="worker_policy_changed"):
        Worker(config.model_copy(update={"energy_policy": "claim"})).run()


def test_worker_routes_with_selected_existing_policy(tmp_path):
    worker = Worker(configured(tmp_path, routing_strategy="v0.1"))
    assert worker.router.strategy_version == "v0.1"


@pytest.mark.parametrize("stop,reason,senses", [(True, "local_tasks_terminal", 1), (False, "no_local_signal", 2)])
def test_future_arrivals_opt_in_wait_is_still_idle_bounded(tmp_path, monkeypatch, stop, reason, senses):
    worker = Worker(configured(tmp_path, energy_policy="claim", max_senses=5, max_idle=2,
                               stop_when_local_terminal=stop))
    monkeypatch.setattr(worker.router, "choose", lambda *args: None)
    monkeypatch.setattr(worker.ledger, "candidates", lambda *a, **kw: [SimpleNamespace(status="completed")])
    monkeypatch.setattr(worker, "_backoff", lambda count: None)
    result = worker.run()
    assert result["reason"] == reason
    assert result["senses"] == senses
    assert result["remaining_energy"] == worker.config.energy
