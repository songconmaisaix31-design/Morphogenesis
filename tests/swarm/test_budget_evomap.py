"""Real SQLite admission counterexamples; response data is synthetic, no HTTP."""

import sqlite3
from pathlib import Path

import pytest

from swarm.budget import BudgetBlocked, BudgetLedger
from swarm.models import BudgetPolicy, ExecutionBound, RunLimits


def unbounded() -> ExecutionBound:
    return ExecutionBound(provider="evomap", model="evomap-gpt-5.6-luna",
                          input_tokens=100, max_output_tokens=20,
                          request_bound="unbounded", provider_enforced=False)


def policy() -> BudgetPolicy:
    # .20 is an operator's admission allocation; it is NOT EvoMap pricing.
    return BudgetPolicy(max_cost_usd=1.0, prices=None, unbounded_reservation_usd=.20,
                        limits=RunLimits(max_attempts=6, max_attempts_per_task=1))


def usage(prompt: int = 10, completion: int = 5) -> dict[str, object]:
    return {"usage": {"prompt_tokens": prompt, "completion_tokens": completion,
                      "total_tokens": prompt + completion}}


@pytest.mark.parametrize("claimed_enforcement", [False, True])
def test_unbounded_requires_operator_opt_in_not_a_provider_boolean(tmp_path: Path, claimed_enforcement: bool) -> None:
    ledger = BudgetLedger(tmp_path / "budget.db", "run", BudgetPolicy(max_cost_usd=1))
    request = unbounded().model_copy(update={"provider_enforced": claimed_enforcement})
    with pytest.raises(BudgetBlocked, match="explicit_unbounded_admission_required"):
        ledger.reserve("w", "task", request)
    assert ledger.snapshot().pending_reservations == 0


@pytest.mark.parametrize("invalid", [0, -1, float("nan"), float("inf"), True])
def test_operator_allowance_is_positive_finite_and_never_disables_admission(invalid: object) -> None:
    with pytest.raises(ValueError):
        BudgetPolicy(max_cost_usd=1, unbounded_reservation_usd=invalid)


def test_allowance_cannot_be_enabled_with_admission_disabled() -> None:
    with pytest.raises(ValueError, match="enabled admission"):
        BudgetPolicy(max_cost_usd=1, unbounded_reservation_usd=.2, admission_control="disabled")


def test_known_tokens_without_prices_keep_unknown_cost_hold_and_stop_next_call(tmp_path: Path) -> None:
    ledger = BudgetLedger(tmp_path / "budget.db", "run", policy())
    reservation = ledger.reserve("w", "task", unbounded(), request_id="task:1")
    assert reservation.bound.provider_enforced is False
    assert reservation.request_bound == "unbounded"
    assert reservation.reserved_estimate_usd == .2
    state = ledger.settle(reservation, usage())
    assert state.usage_metering == "verified" and state.tokens == 15
    assert state.cost == "unknown" and state.estimated_cost_usd is None and state.actual_cost_usd is None
    assert state.reserved_estimate_usd == .2 and state.admission_charged_usd == 0
    assert state.reason == "unknown_cost" and state.sleeping and state.uncertain_reservations == 1
    with sqlite3.connect(ledger.path) as db:
        assert db.execute("SELECT usage_metering,cost,tokens,estimate_usd,status,reserved_usd FROM budget_reservations").fetchone() == (
            "verified", "unknown", 15, None, "uncertain", .2)
    restarted = BudgetLedger(ledger.path, "run", policy())
    assert restarted.snapshot() == state
    assert restarted.settle(reservation, usage()).reserved_estimate_usd == .2
    with pytest.raises(BudgetBlocked, match="unknown_cost"):
        restarted.reserve("different-worker", "next-task", unbounded())
    with pytest.raises(ValueError, match="conflicting usage"):
        restarted.settle(reservation, usage(0, 0))
    with pytest.raises(ValueError, match="policy"):
        BudgetLedger(ledger.path, "run", policy().model_copy(update={"unbounded_reservation_usd": .1}))


@pytest.mark.parametrize("response", [None, {}, {"usage": {"prompt_tokens": "10", "completion_tokens": 5, "total_tokens": 15}}])
def test_missing_or_invalid_usage_does_not_become_known_zero(tmp_path: Path, response: object) -> None:
    ledger = BudgetLedger(tmp_path / "budget.db", "run", policy())
    reservation = ledger.reserve("w", "task", unbounded())
    state = ledger.settle(reservation, response)
    assert state.reason == "unknown_usage" and state.usage_metering == "unknown"
    assert state.tokens is None and state.cost == "unknown"
    assert state.reserved_estimate_usd == .2 and state.estimated_cost_usd is None
    assert ledger.settle(reservation, usage()).tokens is None  # Unknown is not overwritten on replay.


def test_actual_local_token_limit_exceedance_is_not_masked_by_unknown_cost(tmp_path: Path) -> None:
    ledger = BudgetLedger(tmp_path / "budget.db", "run", policy())
    reservation = ledger.reserve("w", "task", unbounded())
    state = ledger.settle(reservation, usage(101, 20))
    assert state.reason == "request_token_limit_exceeded"
    assert state.tokens == 121 and state.cost == "unknown" and state.reserved_estimate_usd == .2
    assert BudgetLedger(ledger.path, "run", policy()).snapshot().reason == "request_token_limit_exceeded"


def test_unknown_usage_outranks_other_inflight_unknown_cost(tmp_path: Path) -> None:
    ledger = BudgetLedger(tmp_path / "budget.db", "run", policy())
    first = ledger.reserve("one", "one", unbounded())
    second = ledger.reserve("two", "two", unbounded())
    assert ledger.settle(first, usage()).reason == "unknown_cost"
    final = ledger.settle(second, None)
    assert final.reason == "unknown_usage" and final.tokens is None
    assert final.reserved_estimate_usd == .4
