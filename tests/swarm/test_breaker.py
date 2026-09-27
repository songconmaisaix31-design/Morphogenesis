"""FC-C breaker tests: real state machine, real SQLite, real process races.

Nothing here mocks the breaker's own decision core, storage or probe race.
FC-B's swarm/fault_observations.py is not present in this worktree before the
integration merge, so a fixture-data double stands in for its store interface
(no reimplementation of B's logic); the end-to-end test runs against the real
FC-B store whenever it is importable.

Time is controlled exclusively through the injected clock callable (the same
seam swarm.task_ledger uses), which also drives the TTLCache window timer.
"""

import multiprocessing
import sys
import time
from pathlib import Path

import pytest
from pydantic import ValidationError

from swarm.breaker import (
    BreakerConfig,
    SharedBreaker,
    TransitionParams,
    cooldown_deadline,
    transition,
)

try:  # pragma: no cover - depends on merge state of the FC-B branch
    from swarm.fault_observations import FaultObservation, FaultObservationStore

    FC_B_AVAILABLE = True
except ImportError:  # pragma: no cover
    FC_B_AVAILABLE = False

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------- helpers


class Clock:
    def __init__(self, start: float = 1000.0) -> None:
        self.t = start

    def __call__(self) -> float:
        return self.t


def cfg(**overrides) -> BreakerConfig:
    base = dict(
        window_seconds=60.0,
        aggregation_period_seconds=30.0,
        failure_threshold=5,
        min_samples=5,
        cooldown_seconds=300.0,
        probe_ttl_seconds=60.0,
    )
    base.update(overrides)
    return BreakerConfig(**base)


def params(**overrides) -> TransitionParams:
    base = dict(now=1000.0, reason="rate_limited", config=cfg())
    base.update(overrides)
    return TransitionParams(**base)


class AggregateDouble:
    """Field-for-field stand-in for FC-B's FaultAggregate (fixture data only)."""

    def __init__(self, provider="bailian", reason="rate_limited", sample_count=1,
                 confirmed_rejections=0, retry_after_until=None,
                 first_occurred_at=900.0, last_occurred_at=999.0):
        self.provider = provider
        self.normalized_reason = reason
        self.sample_count = sample_count
        self.confirmed_rejections = confirmed_rejections
        self.first_occurred_at = first_occurred_at
        self.last_occurred_at = last_occurred_at
        self.retry_after_until = retry_after_until


class IssueDouble:
    def __init__(self, line_number, reason):
        self.line_number = line_number
        self.reason = reason


class ReadDouble:
    def __init__(self, issues=()):
        self.issues = tuple(issues)


class StoreDouble:
    """Stands in for FC-B's store pre-merge: canned read()/aggregate() results."""

    def __init__(self, aggregates=(), issues=()):
        self.aggregates = {(a.provider, a.normalized_reason): a for a in aggregates}
        self.issues = tuple(issues)
        self.aggregate_calls = []

    def read(self):
        return ReadDouble(self.issues)

    def aggregate(self, *, now, window_seconds):
        self.aggregate_calls.append((now, window_seconds))
        return dict(self.aggregates)


def make(tmp_path, clock=None, swarm_id="swarm", name="breaker.sqlite3", **config_overrides):
    clock = clock if clock is not None else Clock()
    breaker = SharedBreaker(tmp_path / name, swarm_id, cfg(**config_overrides), clock=clock)
    return breaker, clock


def suspend(breaker, clock, *, provider="bailian", reason="rate_limited",
            retry_after_until=None, sample_count=5, confirmed_rejections=0):
    report = breaker.apply_aggregates(
        {(provider, reason): AggregateDouble(provider, reason, sample_count,
                                             confirmed_rejections, retry_after_until)},
        now=clock(),
    )
    assert [c.to_state for c in report.changes] == ["suspended"]
    return report


def one_aggregate(provider="bailian", reason="rate_limited", **kw):
    return {(provider, reason): AggregateDouble(provider, reason, **kw)}


# ---------------------------------------------------------------- pure transition()


def test_insufficient_evidence_waits_for_min_samples():
    state, actions = transition("insufficient_evidence", "aggregate", params(sample_count=4))
    assert (state, actions) == ("insufficient_evidence", ())
    state, actions = transition(
        "insufficient_evidence", "aggregate",
        params(sample_count=5, config=cfg(failure_threshold=10)))
    assert (state, actions) == ("normal", ("persist_state",))


def test_threshold_and_min_samples_both_gate_suspension():
    # threshold above min_samples: min_samples alone must not suspend
    assert transition("normal", "aggregate",
                      params(sample_count=5, config=cfg(failure_threshold=10)))[0] == "normal"
    state, actions = transition("normal", "aggregate",
                                params(sample_count=10, config=cfg(failure_threshold=10)))
    assert (state, actions) == ("suspended", ("persist_state", "set_cooldown"))
    # min_samples above threshold: threshold alone must not suspend
    state, _ = transition("normal", "aggregate",
                          params(sample_count=5, config=cfg(failure_threshold=3, min_samples=8)))
    assert state == "normal"
    state, _ = transition("normal", "aggregate",
                          params(sample_count=8, config=cfg(failure_threshold=3, min_samples=8)))
    assert state == "suspended"


def test_confirmed_arrearage_suspends_directly_bypassing_sample_floors():
    state, actions = transition("insufficient_evidence", "aggregate",
                                params(reason="arrearage", sample_count=1, confirmed_rejections=1))
    assert (state, actions) == ("suspended", ("persist_state", "set_cooldown"))
    # FC-A's current normalized vocabulary: billing_arrearage is canonical too
    state, actions = transition(
        "insufficient_evidence", "aggregate",
        params(reason="billing_arrearage", sample_count=1, confirmed_rejections=1))
    assert (state, actions) == ("suspended", ("persist_state", "set_cooldown"))
    state, _ = transition("normal", "aggregate",
                          params(reason="arrearage", sample_count=1, confirmed_rejections=1))
    assert state == "suspended"
    # unconfirmed rejection of the same reason respects the sample floors
    state, _ = transition("normal", "aggregate",
                          params(reason="arrearage", sample_count=1, confirmed_rejections=0))
    assert state == "normal"
    # injected set, not a hardcoded string: custom reason works the same
    state, _ = transition(
        "normal", "aggregate",
        params(reason="quota_free_tier", sample_count=1, confirmed_rejections=1,
               config=cfg(direct_suspend_reasons=frozenset({"quota_free_tier"}))))
    assert state == "suspended"


def test_suspended_aggregate_only_extends_on_strictly_later_hint():
    later = params(sample_count=99, confirmed_rejections=99, cooldown_until=2000.0,
                   retry_after_until=3000.0)
    state, actions = transition("suspended", "aggregate", later)
    assert (state, actions) == ("suspended", ("persist_state", "set_cooldown"))
    # stale in-window evidence must not keep pushing the deadline forward
    for kw in ({"retry_after_until": 1500.0}, {"retry_after_until": None},
               {"retry_after_until": 2000.0}):
        state, actions = transition("suspended", "aggregate",
                                    params(sample_count=99, cooldown_until=2000.0, **kw))
        assert (state, actions) == ("suspended", ())
    # first hint when none was persisted yet
    state, actions = transition("suspended", "aggregate",
                                params(cooldown_until=2000.0, retry_after_until=2500.0))
    assert actions == ("persist_state", "set_cooldown")


def test_aggregate_never_moves_probing_recovery():
    state, actions = transition(
        "probing_recovery", "aggregate",
        params(sample_count=100, confirmed_rejections=100, reason="arrearage"))
    assert (state, actions) == ("probing_recovery", ())


def test_cooldown_expired_boundary_and_reclaim():
    before = params(cooldown_until=1000.0, now=999.999)
    assert transition("suspended", "cooldown_expired", before) == ("suspended", ())
    at = params(cooldown_until=1000.0, now=1000.0)
    assert transition("suspended", "cooldown_expired", at) == (
        "probing_recovery", ("persist_state", "claim_probe_slot"))
    # no fabricated deadline: suspended without a persisted cooldown never opens
    assert transition("suspended", "cooldown_expired", params()) == ("suspended", ())
    # dead probe owner: slot reopens only at/after its persisted TTL
    alive = params(probe_owner="A", probe_expires_at=1060.0, now=1059.999)
    assert transition("probing_recovery", "cooldown_expired", alive) == ("probing_recovery", ())
    dead = params(probe_owner="A", probe_expires_at=1060.0, now=1060.0)
    assert transition("probing_recovery", "cooldown_expired", dead) == (
        "probing_recovery", ("persist_state", "claim_probe_slot"))
    # healthy states ignore the event entirely
    for state in ("insufficient_evidence", "normal"):
        assert transition(state, "cooldown_expired", params(cooldown_until=0.0)) == (state, ())


def test_probe_outcomes_require_live_owner():
    live = dict(probe_owner="A", probe_expires_at=1100.0, worker_id="A", now=1000.0)
    assert transition("probing_recovery", "probe_success", params(**live)) == (
        "normal", ("persist_state", "release_probe_slot", "reset_window"))
    assert transition("probing_recovery", "probe_failure", params(**live))[0] == "suspended"
    # not the owner
    assert transition("probing_recovery", "probe_success",
                      params(**{**live, "worker_id": "B"})) == ("probing_recovery", ())
    assert transition("probing_recovery", "probe_success",
                      params(**{**live, "worker_id": None})) == ("probing_recovery", ())
    # owner returned after its slot expired: report is fenced out
    stale = {**live, "probe_expires_at": 1000.0, "now": 1000.0}
    assert transition("probing_recovery", "probe_success", params(**stale)) == (
        "probing_recovery", ())
    # outcomes in other states do nothing
    for state in ("insufficient_evidence", "normal", "suspended"):
        assert transition(state, "probe_success", params(**live)) == (state, ())
        assert transition(state, "probe_failure", params(**live)) == (state, ())


def test_unknown_events_and_states_are_rejected_not_ignored():
    # answer correctness is not a breaker event: there is no way to spell it
    with pytest.raises(ValueError, match="unknown breaker event"):
        transition("normal", "model_wrong_answer", params())
    with pytest.raises(ValueError, match="unknown breaker event"):
        transition("normal", "", params())
    with pytest.raises(ValueError, match="unknown breaker state"):
        transition("half_open", "aggregate", params())


def test_transition_is_pure_and_repeatable():
    args = ("normal", "aggregate", params(sample_count=9))
    first = transition(*args)
    second = transition(*args)
    assert first == second == ("suspended", ("persist_state", "set_cooldown"))


def test_cooldown_deadline_honors_hint_and_never_fabricates_zero():
    hinted = params(retry_after_until=4321.0)
    assert cooldown_deadline(hinted) == 4321.0
    unknown = params(now=1000.0, config=cfg(cooldown_seconds=300.0))
    assert cooldown_deadline(unknown) == 1300.0
    assert cooldown_deadline(unknown) > unknown.now  # never "retry immediately"
    with pytest.raises(ValidationError):
        cfg(cooldown_seconds=0)
    with pytest.raises(ValidationError):
        cfg(cooldown_seconds=-1.0)
    with pytest.raises(ValidationError):
        params(now=float("nan"))
    with pytest.raises(ValidationError):
        params(retry_after_until=float("inf"))


# ---------------------------------------------------------------- config


def test_config_defaults_and_window_pitfall_guard():
    assert cfg().min_samples == 5
    with pytest.raises(ValidationError, match="aggregation_period_seconds"):
        cfg(window_seconds=10.0, aggregation_period_seconds=30.0)
    with pytest.raises(ValidationError):
        cfg(failure_threshold=0)
    with pytest.raises(ValidationError):
        cfg(min_samples=0)
    with pytest.raises(ValidationError):
        cfg(probe_ttl_seconds=0.0)


# ---------------------------------------------------------------- durable store


def test_fresh_breaker_is_insufficient_and_eligible(tmp_path):
    breaker, clock = make(tmp_path)
    view = breaker.view("bailian", "rate_limited")
    assert view.state == "insufficient_evidence" and view.updated_at is None
    assert breaker.eligible("bailian", "rate_limited", now=clock()) is True
    assert breaker.try_claim_probe("bailian", "rate_limited", "A", now=clock()) is None


def test_evidence_accumulation_suspends_with_configured_cooldown(tmp_path):
    breaker, clock = make(tmp_path, failure_threshold=5, min_samples=5, cooldown_seconds=300.0)
    report = breaker.apply_aggregates(one_aggregate(sample_count=4), now=clock())
    assert report.changes == () and report.evidence_complete
    assert breaker.view("bailian", "rate_limited").state == "insufficient_evidence"
    report = breaker.apply_aggregates(one_aggregate(sample_count=5), now=clock())
    assert [c.to_state for c in report.changes] == ["suspended"]
    view = breaker.view("bailian", "rate_limited")
    assert view.state == "suspended"
    assert view.cooldown_until == clock.t + 300.0  # unknown hint -> injected cooldown
    assert view.sample_count == 5
    assert breaker.eligible("bailian", "rate_limited", worker_id="A", now=clock()) is False
    audit = breaker.audit()
    assert audit[0]["event"] == "aggregate" and audit[0]["to_state"] == "suspended"


def test_single_confirmed_billing_arrearage_sample_suspends_immediately(tmp_path):
    breaker, clock = make(tmp_path, failure_threshold=5, min_samples=5)
    report = breaker.apply_aggregates(
        one_aggregate(reason="billing_arrearage", sample_count=1, confirmed_rejections=1),
        now=clock())
    assert [c.to_state for c in report.changes] == ["suspended"]
    view = breaker.view("bailian", "billing_arrearage")
    assert view.state == "suspended" and view.sample_count == 1
    assert view.cooldown_until == clock.t + 300.0  # no hint -> injected cooldown, not 0
    assert breaker.eligible("bailian", "billing_arrearage", now=clock()) is False


def test_observe_uses_fc_b_window_and_surfaces_read_issues(tmp_path):
    breaker, clock = make(tmp_path, window_seconds=90.0)
    store = StoreDouble(
        aggregates=[AggregateDouble(sample_count=1, confirmed_rejections=1, reason="arrearage")],
        issues=[IssueDouble(3, "invalid_record"), IssueDouble(7, "conflicting_record")],
    )
    report = breaker.observe(store, now=clock())
    assert store.aggregate_calls == [(clock.t, 90.0)]
    assert report.evidence_complete is False
    assert report.issues == ((3, "invalid_record"), (7, "conflicting_record"))
    # incomplete evidence still suspends on confirmed arrearage, and is reported
    assert [c.to_state for c in report.changes] == ["suspended"]
    # ... but it is never read as health: a clean empty cycle with issues keeps state
    store.aggregates.clear()
    report = breaker.observe(store, now=clock())
    assert report.evidence_complete is False
    assert breaker.view("bailian", "arrearage").state == "suspended"


def test_retry_after_hint_sets_probe_time_verbatim(tmp_path):
    breaker, clock = make(tmp_path)
    suspend(breaker, clock, retry_after_until=5000.0)
    assert breaker.view("bailian", "rate_limited").cooldown_until == 5000.0
    clock.t = 4999.999
    assert breaker.try_claim_probe("bailian", "rate_limited", "A", now=clock()) is None
    clock.t = 5000.0
    view = breaker.try_claim_probe("bailian", "rate_limited", "A", now=clock())
    assert view is not None and view.state == "probing_recovery"


def test_probe_lifecycle_claim_success_reset(tmp_path):
    breaker, clock = make(tmp_path, cooldown_seconds=300.0, probe_ttl_seconds=60.0)
    suspend(breaker, clock, sample_count=7)
    clock.t += 300.0
    winner = breaker.try_claim_probe("bailian", "rate_limited", "A", now=clock())
    assert winner is not None
    assert winner.state == "probing_recovery" and winner.probe_owner == "A"
    assert winner.probe_token == 1 and winner.probe_expires_at == clock.t + 60.0
    # the slot is taken: everyone else (and anonymous) stays ineligible
    assert breaker.try_claim_probe("bailian", "rate_limited", "B", now=clock()) is None
    assert breaker.eligible("bailian", "rate_limited", worker_id="A", now=clock()) is True
    assert breaker.eligible("bailian", "rate_limited", worker_id="B", now=clock()) is False
    assert breaker.eligible("bailian", "rate_limited", now=clock()) is False
    # non-owner cannot report outcomes
    assert breaker.report_probe_success("bailian", "rate_limited", "B",
                                        probe_token=winner.probe_token, now=clock()) is False
    assert breaker.view("bailian", "rate_limited").state == "probing_recovery"
    assert breaker.report_probe_success("bailian", "rate_limited", "A",
                                        probe_token=winner.probe_token, now=clock()) is True
    view = breaker.view("bailian", "rate_limited")
    assert view.state == "normal" and view.probe_owner is None
    assert view.cooldown_until is None and view.sample_count == 0
    assert breaker.eligible("bailian", "rate_limited", now=clock()) is True
    # a second success report is a stale no-op
    assert breaker.report_probe_success("bailian", "rate_limited", "A",
                                        probe_token=winner.probe_token, now=clock()) is False


def test_probe_failure_resuspends_with_hint_or_configured_cooldown(tmp_path):
    breaker, clock = make(tmp_path, cooldown_seconds=300.0, probe_ttl_seconds=60.0)
    suspend(breaker, clock)
    clock.t += 300.0
    claim = breaker.try_claim_probe("bailian", "rate_limited", "A", now=clock())
    assert claim is not None and claim.probe_token == 1
    hinted = 9999.0
    assert breaker.report_probe_failure("bailian", "rate_limited", "A",
                                        probe_token=claim.probe_token,
                                        retry_after_until=hinted, now=clock()) is True
    view = breaker.view("bailian", "rate_limited")
    assert view.state == "suspended" and view.cooldown_until == hinted
    assert view.retry_after_until == hinted and view.probe_owner is None
    # unknown outcome cooldown: injected cooldown, never zero-length
    clock.t = hinted
    claim = breaker.try_claim_probe("bailian", "rate_limited", "B", now=clock())
    assert claim is not None and claim.probe_token == 2
    assert breaker.report_probe_failure("bailian", "rate_limited", "B",
                                        probe_token=claim.probe_token, now=clock()) is True
    view = breaker.view("bailian", "rate_limited")
    assert view.cooldown_until == clock.t + 300.0 and view.retry_after_until is None


def test_expired_probe_owner_is_fenced_out(tmp_path):
    breaker, clock = make(tmp_path, probe_ttl_seconds=60.0)
    suspend(breaker, clock, retry_after_until=900.0)
    clock.t = 1000.0
    first = breaker.try_claim_probe("bailian", "rate_limited", "A", now=clock())
    assert first is not None and first.probe_token == 1
    clock.t = 1060.0  # A vanished mid-probe; TTL lapsed
    reclaim = breaker.try_claim_probe("bailian", "rate_limited", "B", now=clock())
    assert reclaim is not None and reclaim.probe_owner == "B" and reclaim.probe_token == 2
    # A resurfaces with its stale token 1: fenced by owner+token, state stays B's probe
    assert breaker.report_probe_success("bailian", "rate_limited", "A",
                                        probe_token=first.probe_token, now=clock()) is False
    assert breaker.report_probe_failure("bailian", "rate_limited", "A",
                                        probe_token=first.probe_token, now=clock()) is False
    view = breaker.view("bailian", "rate_limited")
    assert view.state == "probing_recovery" and view.probe_owner == "B"
    assert breaker.report_probe_success("bailian", "rate_limited", "B",
                                        probe_token=reclaim.probe_token, now=clock()) is True
    assert breaker.view("bailian", "rate_limited").state == "normal"


def test_same_owner_stale_probe_result_is_fenced_by_token(tmp_path):
    # mandatory repair scenario: one worker reclaims its own expired probe slot,
    # so a late outcome from the first attempt must not mutate the live slot.
    breaker, clock = make(tmp_path, probe_ttl_seconds=60.0)
    suspend(breaker, clock, retry_after_until=900.0)
    clock.t = 1000.0
    first = breaker.try_claim_probe("bailian", "rate_limited", "A", now=clock())
    assert first is not None and first.probe_token == 1
    clock.t = 1060.0  # A's own TTL lapsed; A reclaims and the token advances
    second = breaker.try_claim_probe("bailian", "rate_limited", "A", now=clock())
    assert second is not None and second.probe_token == 2 and second.probe_owner == "A"
    # the late first-attempt outcome (token 1) must not mutate state either way
    assert breaker.report_probe_success("bailian", "rate_limited", "A",
                                        probe_token=first.probe_token, now=clock()) is False
    view = breaker.view("bailian", "rate_limited")
    assert view.state == "probing_recovery" and view.probe_owner == "A"
    assert view.probe_token == 2 and view.probe_expires_at == clock.t + 60.0
    assert breaker.report_probe_failure("bailian", "rate_limited", "A",
                                        probe_token=first.probe_token, now=clock()) is False
    assert breaker.view("bailian", "rate_limited").state == "probing_recovery"
    # only the current token (2) succeeds
    assert breaker.report_probe_success("bailian", "rate_limited", "A",
                                        probe_token=second.probe_token, now=clock()) is True
    view = breaker.view("bailian", "rate_limited")
    assert view.state == "normal" and view.probe_token == 2  # token history stays fenced
    # a fabricated token never matches anything
    with pytest.raises(ValueError, match="probe_token"):
        breaker.report_probe_success("bailian", "rate_limited", "A", probe_token=0, now=clock())


def test_state_survives_reopen_with_deadlines_intact(tmp_path):
    clock = Clock()
    breaker, _ = make(tmp_path, clock=clock)
    suspend(breaker, clock, retry_after_until=5000.0)
    del breaker
    reopened, _ = make(tmp_path, clock=clock)  # "restart": fresh instance, same file
    view = reopened.view("bailian", "rate_limited")
    assert view.state == "suspended" and view.cooldown_until == 5000.0
    assert reopened.eligible("bailian", "rate_limited", worker_id="A", now=clock()) is False
    clock.t = 4999.0
    assert reopened.try_claim_probe("bailian", "rate_limited", "A", now=clock()) is None
    clock.t = 5000.0
    assert reopened.try_claim_probe("bailian", "rate_limited", "A", now=clock()) is not None
    events = [entry["event"] for entry in reversed(reopened.audit())]
    assert events == ["aggregate", "probe_claimed"]
    import sqlite3
    with sqlite3.connect(reopened.path) as db:
        assert db.execute("PRAGMA journal_mode").fetchone()[0] == "wal"


def test_swarm_ids_are_isolated_in_one_file(tmp_path):
    clock = Clock()
    left, _ = make(tmp_path, clock=clock, swarm_id="left")
    right, _ = make(tmp_path, clock=clock, swarm_id="right", name="breaker.sqlite3")
    suspend(left, clock)
    assert left.view("bailian", "rate_limited").state == "suspended"
    assert right.view("bailian", "rate_limited").state == "insufficient_evidence"
    assert right.eligible("bailian", "rate_limited", now=clock()) is True


# ---------------------------------------------------------------- window (TTLCache)


def test_window_boundary_is_exactly_window_seconds(tmp_path):
    clock = Clock(start=0.0)
    breaker, _ = make(tmp_path, clock=clock, window_seconds=60.0)
    breaker.apply_aggregates(one_aggregate(sample_count=3), now=clock())
    key = ("bailian", "rate_limited")
    assert breaker.windowed_evidence() == {key: 3}
    clock.t = 59.999
    assert breaker.windowed_evidence() == {key: 3}
    clock.t = 60.0  # cachetools expires at exactly timestamp+ttl
    assert breaker.windowed_evidence() == {}


def test_cached_evidence_bridges_aggregation_gaps_but_probe_success_resets(tmp_path):
    clock = Clock()
    breaker, _ = make(tmp_path, clock=clock, failure_threshold=5, cooldown_seconds=300.0,
                      probe_ttl_seconds=60.0)
    suspend(breaker, clock, sample_count=5)
    key = ("bailian", "rate_limited")
    # gap cycles with no fresh aggregate: the window cache keeps the evidence
    clock.t += 30.0
    report = breaker.apply_aggregates({}, now=clock())
    assert report.changes == () and breaker.windowed_evidence() == {key: 5}
    assert breaker.view("bailian", "rate_limited").state == "suspended"
    # recover: probe wins and succeeds, which must clear the cached evidence...
    clock.t += 270.0
    claim = breaker.try_claim_probe("bailian", "rate_limited", "A", now=clock())
    assert claim is not None
    assert breaker.report_probe_success("bailian", "rate_limited", "A",
                                        probe_token=claim.probe_token, now=clock()) is True
    assert breaker.windowed_evidence() == {}
    # ... otherwise this empty cycle would immediately re-suspend from stale cache
    report = breaker.apply_aggregates({}, now=clock())
    assert report.changes == ()
    assert breaker.view("bailian", "rate_limited").state == "normal"
    assert breaker.eligible("bailian", "rate_limited", now=clock()) is True


# ---------------------------------------------------------------- invariants


def test_module_never_touches_budget_lease_or_worker_internals():
    source = (REPO_ROOT / "swarm" / "breaker.py").read_text(encoding="utf-8")
    for forbidden in ("swarm.budget", "swarm.lease", "swarm.worker_loop", "swarm.pheromone",
                      "from swarm import", "task_ledger.TaskLedger"):
        assert forbidden not in source
    # reuse is limited to the shared transaction helper and clock validation
    assert "from swarm.task_ledger import connection, enable_wal, now_checked" in source


def test_eligibility_queries_do_not_mutate_state(tmp_path):
    breaker, clock = make(tmp_path)
    suspend(breaker, clock)
    before = breaker.view("bailian", "rate_limited")
    for _ in range(3):
        assert breaker.eligible("bailian", "rate_limited", worker_id="A", now=clock()) is False
        assert breaker.try_claim_probe("bailian", "rate_limited", "A", now=clock.t - 1) is None
    assert breaker.view("bailian", "rate_limited") == before


# ---------------------------------------------------------------- real processes


def _race_child(root, path, config_json, worker_id, barrier, out):
    sys.path.insert(0, str(root))
    from swarm.breaker import BreakerConfig, SharedBreaker

    breaker = SharedBreaker(path, "swarm", BreakerConfig.model_validate_json(config_json))
    barrier.wait(timeout=120)
    won = breaker.try_claim_probe("bailian", "rate_limited", worker_id) is not None
    out.put((worker_id, won))


def test_multiprocess_half_open_race_yields_exactly_one_probe(tmp_path):
    sys.path.insert(0, str(Path(__file__).resolve().parent))  # spawn children import this module
    path = tmp_path / "breaker.sqlite3"
    breaker = SharedBreaker(path, "swarm", cfg(), clock=time.time)
    # suspend with a server hint that has already elapsed in real time
    report = breaker.apply_aggregates(
        one_aggregate(sample_count=5, retry_after_until=time.time() - 1.0), now=time.time())
    assert [c.to_state for c in report.changes] == ["suspended"]

    context = multiprocessing.get_context("spawn")
    barrier = context.Barrier(4)
    out = context.Queue()
    workers = [f"w{i}" for i in range(4)]
    processes = [
        context.Process(target=_race_child,
                        args=(REPO_ROOT, str(path), cfg().model_dump_json(), worker, barrier, out))
        for worker in workers
    ]
    for process in processes:
        process.start()
    results = [out.get(timeout=120) for _ in workers]
    for process in processes:
        process.join(timeout=120)
        assert process.exitcode == 0
    winners = [worker for worker, won in results if won]
    assert len(winners) == 1
    view = breaker.view("bailian", "rate_limited")
    assert view.state == "probing_recovery" and view.probe_token == 1
    assert view.probe_owner == winners[0]
    assert breaker.eligible("bailian", "rate_limited", worker_id=winners[0]) is True
    losers = [worker for worker in workers if worker != winners[0]]
    assert all(breaker.eligible("bailian", "rate_limited", worker_id=w) is False for w in losers)


# ---------------------------------------------------------------- real FC-B end-to-end


@pytest.mark.skipif(not FC_B_AVAILABLE,
                    reason="FC-B fault_observations merges into this tree at integration")
def test_end_to_end_with_real_fc_b_store(tmp_path):
    clock = Clock()
    breaker, _ = make(tmp_path, clock=clock, failure_threshold=3, min_samples=3)
    store = FaultObservationStore(tmp_path / "faults.jsonl", "run-1")
    # single real canonical FC-A fact through the real FC-B store: immediate suspend
    assert store.append(FaultObservation(
        run_id="run-1", task_id="t1", request_id="r0", attempt=0,
        provider="bailian", model="qwen-max", failure_class="confirmed_rejection",
        normalized_reason="billing_arrearage", retry_after_seconds=120.0,
        occurred_at=clock.t - 10.0, evidence_ref="hash0",
    )) is True
    report = breaker.observe(store, now=clock())
    assert report.evidence_complete and report.issues == ()
    view = breaker.view("bailian", "billing_arrearage")
    assert view.state == "suspended" and view.sample_count == 1
    # real FC-B hint semantics: max(occurred_at + retry_after_seconds)
    assert view.cooldown_until == pytest.approx(clock.t + 110.0)
    # corrupt one line: issues surface and decisions never pretend health
    with (tmp_path / "faults.jsonl").open("a", encoding="utf-8") as handle:
        handle.write("{not json}\n")
    report = breaker.observe(store, now=clock())
    assert report.evidence_complete is False
    assert (2, "invalid_record") in report.issues
