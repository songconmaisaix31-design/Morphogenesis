"""Observation cost state is the current durable reservation, not run totals."""
import pytest

from swarm.worker_loop import Worker
from tests.swarm.test_failure_chain_runtime import (
    _claim, _events, _executor, _facts, _failure, _reservations, _worker_config,
)


@pytest.mark.parametrize("allow_unknown_cost", [False, True])
def test_known_usage_without_prices_observes_unknown_and_keeps_hold(tmp_path, allow_unknown_cost):
    config = _worker_config(tmp_path)
    config = config.model_copy(update={"budget": config.budget.model_copy(
        update={"allow_unknown_cost": allow_unknown_cost})})
    executor = _executor(result=_failure(known_usage=True, reason="rate_limited"))
    worker = Worker(config, executor)
    signal, lease = _claim(worker)
    outcome = worker._process(signal, lease)
    assert outcome == "rejected", _events(worker)
    assert executor.execute.call_count == 1
    row, = _reservations(worker)
    assert row["usage_metering"] == "verified" and row["tokens"] == 2
    assert row["cost"] == "unknown" and row["estimate_usd"] is None
    assert row["status"] == ("unknown_cost_allowed" if allow_unknown_cost else "uncertain")
    assert row["reserved_usd"] == 0.2 and row["admitted_usd"] is None
    fact, = _facts(worker)
    assert fact.request_id == row["request_id"] and fact.cost_state == "unknown"
    restarted = Worker(config, _executor())
    assert restarted.budget.snapshot().reserved_estimate_usd == 0.2
    assert _reservations(restarted) == [row]


def test_prior_unknown_hold_does_not_mislabel_current_settled_reservation(tmp_path):
    config = _worker_config(tmp_path, prices=True)
    first = _executor(result=_failure(reason="rate_limited"))
    current = _executor(result=_failure(known_usage=True, reason="rate_limited"))
    worker = Worker(config, first, candidates=[first, current])
    signal, lease = _claim(worker)
    outcome = worker._process(signal, lease)
    assert outcome == "rejected", _events(worker)
    assert first.execute.call_count == current.execute.call_count == 1
    previous_row, current_row = _reservations(worker)
    assert previous_row["status"] == "uncertain" and previous_row["cost"] == "unknown"
    assert previous_row["tokens"] is None and previous_row["reserved_usd"] == 0.2
    assert current_row["status"] == "settled" and current_row["cost"] == "estimated"
    assert current_row["tokens"] == 2 and current_row["estimate_usd"] > 0
    snapshot = worker.budget.snapshot()
    assert snapshot.cost == "unknown" and snapshot.reserved_estimate_usd == 0.2
    facts = {fact.request_id: fact for fact in _facts(worker)}
    assert facts[previous_row["request_id"]].cost_state == "unknown"
    assert facts[current_row["request_id"]].cost_state == "settled"
