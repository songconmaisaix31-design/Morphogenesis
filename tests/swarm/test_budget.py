"""M6 gate: real SQLite/process races; all usage/executors remain local fakes."""

import os
from pathlib import Path
import subprocess
import sys

import pytest

from swarm.budget import BudgetBlocked, BudgetLedger
from swarm.models import BudgetPolicy, ExecutionBound, ModelPrices


def policy(**updates: object) -> BudgetPolicy:
    data: dict[str, object] = dict(max_cost_usd=1.0, prices=ModelPrices(
        provider="fake", model="measured", input_usd_per_million=1,
        output_usd_per_million=2))
    data.update(updates)
    return BudgetPolicy.model_validate(data)


def bound(input_tokens: int = 10, output: int = 20) -> ExecutionBound:
    return ExecutionBound(provider="fake", model="measured", input_tokens=input_tokens,
                          max_output_tokens=output, provider_enforced=True)


def usage(prompt: int = 10, completion: int = 20) -> dict[str, object]:
    return {"usage": {"prompt_tokens": prompt, "completion_tokens": completion,
                      "total_tokens": prompt + completion}}


def test_default_bound_preflight_prices_enforcement_and_failure_measurement(tmp_path: Path) -> None:
    p = policy()
    assert p.max_tokens == 20000
    ledger = BudgetLedger(tmp_path / "budget.db", "account", p)
    with pytest.raises(BudgetBlocked, match="task_token_bound"):
        ledger.reserve("a", "too_large", bound(20000, 1))
    unbounded = ledger.reserve("a", "unbounded", bound().model_copy(update={"provider_enforced": False}))
    assert unbounded.request_bound == "unbounded"
    ledger.settle(unbounded, usage(0, 0))
    with pytest.raises(BudgetBlocked, match="matching_model_prices"):
        ledger.reserve("a", "wrong_model", bound().model_copy(update={"model": "other"}))
    no_prices = BudgetLedger(tmp_path / "unknown.db", "account", BudgetPolicy(max_cost_usd=1))
    with pytest.raises(BudgetBlocked):
        no_prices.reserve("a", "missing_prices", bound())
    reservation = ledger.reserve("a", "failed_task", bound())
    response = usage()
    response["error"] = "executor failed after consumption"
    state = ledger.settle(reservation, response)
    assert state.tokens == 30
    assert state.estimated_cost_usd == pytest.approx(0.00005)
    assert state.actual_cost_usd is None
    assert ledger.settle(reservation, usage()).tokens == 30
    with pytest.raises(BudgetBlocked, match="no_retry"):
        ledger.reserve("a", "failed_task", bound())


@pytest.mark.parametrize("bad", [-1, True, float("nan"), "1"])
def test_model_copy_cannot_bypass_preflight_validation(tmp_path: Path, bad: object) -> None:
    ledger = BudgetLedger(tmp_path / "budget.db", "account", policy())
    with pytest.raises(ValueError):
        ledger.reserve("w", "bad", bound().model_copy(update={"input_tokens": bad}))
    assert ledger.snapshot().pending_reservations == 0


def test_policy_and_reservation_are_revalidated(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        BudgetLedger(tmp_path / "budget.db", "a", policy().model_copy(update={"max_cost_usd": -1}))
    ledger = BudgetLedger(tmp_path / "budget.db", "a", policy())
    r = ledger.reserve("w", "t", bound())
    with pytest.raises(ValueError):
        ledger.settle(r.model_copy(update={"bound": r.bound.model_copy(update={"input_tokens": -1})}), usage())
    assert ledger.snapshot().pending_reservations == 1


@pytest.mark.parametrize("bad", [None, {}, {"usage": {}},
    {"usage": {"prompt_tokens": True, "completion_tokens": 1, "total_tokens": 2}},
    {"usage": {"prompt_tokens": "1", "completion_tokens": 1, "total_tokens": 2}},
    {"usage": {"prompt_tokens": -1, "completion_tokens": 1, "total_tokens": 0}},
    {"usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 7}},
    {"usage": {"prompt_tokens": 2**64, "completion_tokens": 1, "total_tokens": 2**64+1}},
])
def test_unknown_usage_persists_reservation_breaker_and_no_retry(tmp_path: Path, bad: object) -> None:
    ledger = BudgetLedger(tmp_path / "budget.db", "account", policy())
    reservation = ledger.reserve("a", "uncertain", bound())
    assert ledger.snapshot().tokens is None  # In-flight is also unknown, never zero.
    state = ledger.settle(reservation, bad)
    assert state.sleeping and state.uncertain_reservations == 1
    assert state.tokens is None and state.estimated_cost_usd is None and state.actual_cost_usd is None
    assert state.reserved_estimate_usd == reservation.reserved_estimate_usd
    restarted = BudgetLedger(tmp_path / "budget.db", "account", policy())
    for worker in ("a", "b", "c"):
        assert restarted.snapshot(worker).sleeping
        with pytest.raises(BudgetBlocked):
            restarted.reserve(worker, "next" + worker, bound())
    assert restarted.settle(reservation, usage()).uncertain_reservations == 1


def test_burn_rate_is_per_worker_and_persists(tmp_path: Path) -> None:
    now = [100.0]
    p = policy(burn_rate_tokens=30)
    ledger = BudgetLedger(tmp_path / "budget.db", "account", p, clock=lambda: now[0])
    r = ledger.reserve("a", "a1", bound())
    assert ledger.snapshot("a").sleeping
    assert not ledger.snapshot("b").sleeping
    ledger.settle(r, usage())
    restarted = BudgetLedger(tmp_path / "budget.db", "account", p, clock=lambda: now[0])
    with pytest.raises(BudgetBlocked, match="burn_rate"):
        restarted.reserve("a", "a2", bound())
    assert not restarted.snapshot("b").sleeping
    now[0] += 60
    assert not restarted.snapshot("a").sleeping
    restarted.reserve("a", "a2", bound())


def test_measured_high_consumption_trips_durable_shared_breaker(tmp_path: Path) -> None:
    p = policy(max_cost_usd=0.0001)
    ledger = BudgetLedger(tmp_path / "budget.db", "account", p)
    r = ledger.reserve("a", "high_fake", bound())
    state = ledger.settle(r, usage(200, 400))
    assert state.reason == "provider_bound_violated"  # Also exhausted; violation must take priority.
    assert state.tokens == 600 and state.estimated_cost_usd == pytest.approx(0.001)
    for worker in ("a", "b", "c"):
        peer = BudgetLedger(tmp_path / "budget.db", "account", p)
        assert peer.snapshot(worker).sleeping
        with pytest.raises(BudgetBlocked):
            peer.reserve(worker, worker, bound())


def test_bound_violation_stops_even_below_cost_cap(tmp_path: Path) -> None:
    ledger = BudgetLedger(tmp_path / "budget.db", "account", policy())
    r = ledger.reserve("a", "bad_provider", bound())
    assert ledger.settle(r, usage(11, 20)).reason == "provider_bound_violated"


def test_restart_cannot_reset_policy_or_uncertain_pending_task(tmp_path: Path) -> None:
    path = tmp_path / "budget.db"
    ledger = BudgetLedger(path, "account", policy(max_cost_usd=0.00005))
    r = ledger.reserve("crashed", "task", bound())
    restarted = BudgetLedger(path, "account", policy(max_cost_usd=0.00005))
    assert restarted.snapshot().pending_reservations == 1
    with pytest.raises(BudgetBlocked, match="no_retry"):
        restarted.reserve("replacement", "task", bound())
    with pytest.raises(BudgetBlocked, match="capacity"):
        restarted.reserve("replacement", "other", bound())
    with pytest.raises(ValueError, match="policy"):
        BudgetLedger(path, "account", policy(max_cost_usd=2))
    assert restarted.mark_uncertain(r).sleeping


def test_atomic_reservation_across_processes(tmp_path: Path) -> None:
    path = tmp_path / "budget.db"
    p = policy(max_cost_usd=0.0001)
    BudgetLedger(path, "account", p)
    script = '''
import sys
from swarm.budget import BudgetLedger, BudgetBlocked
from swarm.models import BudgetPolicy, ExecutionBound
ledger=BudgetLedger(sys.argv[1], 'account', BudgetPolicy.model_validate_json(sys.argv[2]))
try:
    r=ledger.reserve(sys.argv[3], sys.argv[3], ExecutionBound(provider='fake',model='measured',input_tokens=100,max_output_tokens=0,provider_enforced=True))
    print(r.model_dump_json())
except BudgetBlocked:
    print('blocked')
'''
    children = [subprocess.Popen([sys.executable, "-c", script, str(path), p.model_dump_json(), str(i)],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=os.environ.copy())
                for i in range(6)]
    results = [child.communicate(timeout=60) for child in children]
    assert all(child.returncode == 0 for child in children), results
    assert sum(out.strip() != "blocked" for out, _ in results) == 1
    state = BudgetLedger(path, "account", p).snapshot()
    assert state.reserved_estimate_usd == pytest.approx(0.0001)
    assert state.pending_reservations == 1
    assert all(not err for _, err in results)


def test_concurrent_settlement_charges_once(tmp_path: Path) -> None:
    p = policy()
    ledger = BudgetLedger(tmp_path / "budget.db", "account", p)
    r = ledger.reserve("w", "t", bound())
    script = '''
import sys
from swarm.budget import BudgetLedger
from swarm.models import BudgetPolicy, Reservation
ledger=BudgetLedger(sys.argv[1], 'account', BudgetPolicy.model_validate_json(sys.argv[2]))
ledger.settle(Reservation.model_validate_json(sys.argv[3]), {'usage':{'prompt_tokens':10,'completion_tokens':20,'total_tokens':30}})
'''
    children = [subprocess.Popen([sys.executable, "-c", script, str(ledger.path), p.model_dump_json(), r.model_dump_json()],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(4)]
    results = [child.communicate(timeout=60) for child in children]
    assert all(child.returncode == 0 for child in children), results
    assert ledger.snapshot().tokens == 30
    assert ledger.snapshot().estimated_cost_usd == pytest.approx(0.00005)


def test_explicit_budget_evidence_labels_and_no_boolean_cost_proof(tmp_path):
    import sqlite3
    ledger=BudgetLedger(tmp_path/'budget.db','swarm',policy())
    r=ledger.reserve('A','a',bound())
    assert r.request_bound=='unbounded' and r.usage_metering=='unknown'
    before=ledger.snapshot()
    assert before.cost=='unknown' and before.admission_control=='enabled'
    after=ledger.settle(r,usage())
    assert after.usage_metering=='verified' and after.cost=='estimated'
    assert after.request_bound=='unbounded' and after.actual_cost_usd is None
    with sqlite3.connect(ledger.path) as db:
        assert db.execute('PRAGMA journal_mode').fetchone()[0]=='wal'
        assert db.execute('SELECT usage_metering,request_bound,admission_control,cost FROM budget_reservations').fetchone()==('verified','unbounded','enabled','estimated')
    with pytest.raises(ValueError,match='executor evidence'):
        ledger.reserve('A','b',bound().model_copy(update={'request_bound':'verified'}))


def test_verified_cost_bound_is_retained_conservatively_without_bill(tmp_path):
    ledger=BudgetLedger(tmp_path/'budget.db','swarm',policy(max_cost_usd=.001))
    verified=bound().model_copy(update={'request_bound':'verified','max_cost_usd':.001,'bound_evidence':'local contractual cap fixture'})
    r=ledger.reserve('A','a',verified)
    assert r.reserved_estimate_usd==.001
    ledger.settle(r,usage())
    with pytest.raises(BudgetBlocked,match='capacity'):
        ledger.reserve('B','b',bound())
    assert ledger.snapshot().estimated_cost_usd==pytest.approx(.00005)
    assert ledger.snapshot().actual_cost_usd is None


def test_request_generation_known_settled_retry_and_unknown_no_retry(tmp_path):
    ledger=BudgetLedger(tmp_path/'budget.db','swarm',policy())
    r=ledger.reserve('A','task',bound(),request_id='task:1')
    with pytest.raises(BudgetBlocked,match='no_retry'):
        ledger.reserve('B','task',bound(),request_id='task:2')
    ledger.settle(r,usage())
    r2=ledger.reserve('B','task',bound(),request_id='task:2')
    with pytest.raises(ValueError,match='conflicting'):
        ledger.settle(r,usage(9,20))
    ledger.mark_uncertain(r2)
    assert ledger.snapshot().reserved_estimate_usd==r2.reserved_estimate_usd
    with pytest.raises(BudgetBlocked,match='unknown'):
        ledger.reserve('C','different',bound(),request_id='different:1')


def test_budget_run_limits_persist_and_swarm_isolation(tmp_path):
    from swarm.models import RunLimits
    now=[100.]
    p=policy(limits=RunLimits(max_tasks=1,max_attempts=2,max_attempts_per_task=2,max_runtime_seconds=10))
    ledger=BudgetLedger(tmp_path/'budget.db','one',p,clock=lambda:now[0])
    r=ledger.reserve('A','a',bound(),request_id='a:1')
    ledger.settle(r,usage())
    with pytest.raises(BudgetBlocked,match='max_tasks'):
        ledger.reserve('A','b',bound())
    r2=ledger.reserve('A','a',bound(),request_id='a:2')
    ledger.settle(r2,usage())
    with pytest.raises(BudgetBlocked,match='max_attempts'):
        ledger.reserve('A','a',bound(),request_id='a:3')
    peer=BudgetLedger(ledger.path,'two',p,clock=lambda:now[0])
    assert peer.snapshot().tokens==0
    now[0]=110
    with pytest.raises(BudgetBlocked,match='runtime'):
        peer.reserve('A','a',bound())


def test_disabled_admission_is_visible_not_a_cap_claim(tmp_path):
    ledger=BudgetLedger(tmp_path/'budget.db','run',policy(max_cost_usd=.000001,admission_control='disabled'))
    r=ledger.reserve('A','a',bound())
    assert r.admission_control=='disabled'
    assert ledger.snapshot().admission_control=='disabled'


def test_unbounded_low_usage_never_frees_allowance_across_restart(tmp_path):
    p=policy(max_cost_usd=.00005)
    ledger=BudgetLedger(tmp_path/'budget.db','run',p)
    r=ledger.reserve('A','a',bound())
    state=ledger.settle(r,usage(0,0))
    assert state.estimated_cost_usd==0
    assert state.actual_cost_usd is None and state.cost=='estimated'
    assert state.request_bound=='unbounded' and state.unreconciled_reservations==1
    assert state.admission_charged_usd==r.reserved_estimate_usd
    restarted=BudgetLedger(ledger.path,'run',p)
    assert restarted.snapshot().admission_charged_usd==r.reserved_estimate_usd
    with pytest.raises(BudgetBlocked,match='capacity'):
        restarted.reserve('B','next',bound(1,0))


def test_late_bound_violation_overrides_existing_admission_exhaustion(tmp_path):
    ledger=BudgetLedger(tmp_path/'budget.db','run',policy(max_cost_usd=.0001))
    final=ledger.reserve('A','final',bound(100,0))
    pending=ledger.reserve('B','zero',bound(0,0))
    assert ledger.settle(final,usage(100,0)).reason=='swarm_cost_estimate_exhausted'
    violated=ledger.settle(pending,usage(1,0))
    assert violated.reason=='provider_bound_violated'
    assert BudgetLedger(ledger.path,'run',ledger.policy).snapshot().reason=='provider_bound_violated'


def test_pending_accessor_recovers_reserve_status_gap_without_creating_authority(tmp_path):
    p=policy()
    ledger=BudgetLedger(tmp_path/'budget.db','run',p)
    one=ledger.reserve('crashed','a',bound(),request_id='a:1')
    ledger.reserve('live','b',bound())
    other=BudgetLedger(ledger.path,'other',p)
    other.reserve('crashed','other-task',bound())
    # No worker JSON was written. The durable reservation still identifies recovery.
    restarted=BudgetLedger(ledger.path,'run',p)
    assert restarted.pending('crashed')==[one]
    assert restarted.pending('missing')==[]
    assert restarted.snapshot().pending_reservations==2  # Lookup never mutates.
    with pytest.raises(ValueError):
        restarted.pending('crashed',limit=1001)
    restarted.mark_uncertain(restarted.pending('crashed',limit=1)[0])
    assert restarted.pending('crashed')==[]
    assert restarted.snapshot().reason=='unknown_usage'
    with pytest.raises(BudgetBlocked,match='unknown_usage'):
        restarted.reserve('replacement','c',bound())


def test_unknown_usage_overrides_prior_exhaustion_and_later_violation(tmp_path):
    ledger=BudgetLedger(tmp_path/'budget.db','run',policy(max_cost_usd=.0001))
    final=ledger.reserve('A','final',bound(100,0))
    unknown=ledger.reserve('B','unknown',bound(0,0))
    violated=ledger.reserve('C','violated',bound(0,0))
    assert ledger.settle(final,usage(100,0)).reason=='swarm_cost_estimate_exhausted'
    assert ledger.mark_uncertain(unknown).reason=='unknown_usage'
    assert ledger.settle(violated,usage(1,0)).reason=='unknown_usage'
    assert ledger.snapshot().uncertain_reservations==1
