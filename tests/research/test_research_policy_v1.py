"""Three-axis contribution and research-route policy (research-v1) boundaries.

These tests exercise the pure policy engine and the approved-fact projection
without invoking the Node GEP bridge or any executor. The projection is built
exclusively from immutable ledger/asset facts, so a valid refutation earns a
contribution while a crash, timeout, auth error or unknown effect earns none.
"""
import json
import sqlite3
from pathlib import Path

import pytest

from contracts.identity import AgentId
from swarm.models import Signal
from swarm.research.models import HostConfig
from swarm.research.service import ResearchService
from swarm.research.policy import (
    Branch,
    ContributionDecision,
    CorrectionEvent,
    ResearchPolicy,
    RouteOpportunityPlan,
    ThreeAxisResult,
)
from swarm.research.feedback import ResearchFeedbackStore, research_feedback
from swarm.router import Router


def make_result(result_id="r1", source_ref="https://example.invalid/paper", *,
                actor="author-0", execution="succeeded", hypothesis="refuted",
                contribution="proposed", at=1.0, report_id=None, task_id="t1") -> ThreeAxisResult:
    return ThreeAxisResult(
        result_id=result_id, report_id=report_id or (result_id + "-report"), task_id=task_id,
        actor=actor, source_ref=source_ref, provenance="mock", execution=execution,
        hypothesis=hypothesis, contribution=contribution, at=at,
    )


def make_branch(branch_id="b1", status="proposed", *, authorized=True, supported=(),
                refuted=(), conditions=None) -> Branch:
    return Branch(branch_id=branch_id, status=status, authorized=authorized,
                  supported_by=supported, refuted_by=refuted,
                  conditions=conditions or {"seed": "0"})


# ---------------------------------------------------------------------------
# Three-axis model and contribution acceptance
# ---------------------------------------------------------------------------

def test_valid_refutation_is_an_independently_accepted_contribution():
    policy = ResearchPolicy()
    result = make_result(execution="succeeded", hypothesis="refuted")
    decision = policy.accept(result, reviewer="reviewer-1", seen=set())
    assert decision.accepted is True and decision.state == "accepted"
    assert decision.reasons == ("independent_evidence_accepted",)


def test_crash_timeout_and_unknown_effect_earn_no_scientific_reward():
    policy = ResearchPolicy()
    for execution, hypothesis in (("failed", "not_evaluated"), ("unknown", "not_evaluated"),
                                  ("cancelled", "not_evaluated")):
        result = make_result(execution=execution, hypothesis=hypothesis)
        decision = policy.accept(result, reviewer="reviewer-1", seen=set())
        assert decision.accepted is False and decision.state == "rejected"
        assert decision.reasons == ("execution_not_succeeded",)


def test_self_approval_by_the_same_actor_is_rejected():
    policy = ResearchPolicy()
    result = make_result(actor="author-0", execution="succeeded", hypothesis="supported")
    decision = policy.accept(result, reviewer="author-0", seen=set())
    assert decision.accepted is False and decision.reasons == ("self_approval_rejected",)


def test_duplicate_result_and_duplicate_source_are_not_counted_again():
    policy = ResearchPolicy()
    seen: set[str] = set()
    first = make_result(result_id="r1", source_ref="https://example.invalid/paper")
    assert policy.accept(first, reviewer="reviewer-1", seen=seen).accepted is True
    # Same completed result, a different reviewer: not a second contribution.
    duplicate_result = make_result(result_id="r1", source_ref="https://example.invalid/paper")
    assert policy.accept(duplicate_result, reviewer="reviewer-2", seen=seen).reasons == ("duplicate_contribution",)
    # Different result, same source paper/origin: not an independent source.
    same_paper = make_result(result_id="r2", source_ref="https://example.invalid/paper")
    assert policy.accept(same_paper, reviewer="reviewer-3", seen=seen).reasons == ("duplicate_contribution",)
    # A genuinely distinct source is accepted regardless of agent brand.
    other_paper = make_result(result_id="r3", source_ref="https://example.invalid/other-paper", actor="other-brand-0")
    assert policy.accept(other_paper, reviewer="reviewer-1", seen=seen).accepted is True


# ---------------------------------------------------------------------------
# Route opportunities: bounded, explainable, excludes dormant/refuted/archived/scope
# ---------------------------------------------------------------------------

def test_route_opportunities_are_bounded_and_total_share_is_fixed():
    policy = ResearchPolicy(exploration_fraction=0.20)
    branches = [make_branch("legal-a", "proposed"), make_branch("legal-b", "exploring"),
                make_branch("dormant", "dormant"), make_branch("refuted", "refuted"),
                make_branch("archived", "archived"), make_branch("out-of-scope", "proposed", authorized=False)]
    plan = policy.opportunities(branches)
    assert isinstance(plan, RouteOpportunityPlan) and plan.version == "research-v1"
    assert plan.total_share == 1.0
    eligible = [op for op in plan.opportunities if op.eligible]
    assert {op.branch_id for op in eligible} == {"legal-a", "legal-b"}
    assert sum(op.share for op in eligible) == pytest.approx(1.0, abs=1e-9)
    by_id = {op.branch_id: op for op in plan.opportunities}
    for excluded, reason in (("dormant", "dormant"), ("refuted", "refuted_under_conditions"),
                             ("archived", "archived"), ("out-of-scope", "out_of_scope")):
        op = by_id[excluded]
        assert op.eligible is False and op.share == 0.0 and reason in op.reasons


def test_exploration_floor_is_bounded_and_configurable():
    for fraction in (0.0, 0.20, 0.50):
        policy = ResearchPolicy(exploration_fraction=fraction)
        branches = [make_branch("a", "proposed", supported=("s1",)),
                    make_branch("b", "proposed", refuted=("r1",))]
        plan = policy.opportunities(branches)
        shares = [op.share for op in plan.opportunities]
        assert sum(shares) == pytest.approx(1.0, abs=1e-9)
        floor = fraction / 2
        assert all(share >= floor - 1e-9 for share in shares)


def test_trusted_refutation_lowers_future_opportunity_for_the_same_conditions():
    policy = ResearchPolicy(exploration_fraction=0.0)
    stable = make_branch("a", "supported", supported=("s1",))
    before = policy.opportunities([stable, make_branch("b", "supported", supported=("s1",))])
    after = policy.opportunities([stable, make_branch("b", "supported", supported=("s1",), refuted=("r1",))])
    before_b = next(op for op in before.opportunities if op.branch_id == "b")
    after_b = next(op for op in after.opportunities if op.branch_id == "b")
    assert after_b.share < before_b.share
    assert after_b.factors["refute_count"] == 1.0


def test_invalid_exploration_fraction_is_rejected():
    with pytest.raises(ValueError, match="exploration_fraction"):
        ResearchPolicy(exploration_fraction=1.5)
    with pytest.raises(ValueError, match="exploration_fraction"):
        ResearchPolicy(exploration_fraction=float("nan"))


# ---------------------------------------------------------------------------
# Sleep / downgrade / reopen corrections preserve history and never erase refutation
# ---------------------------------------------------------------------------

def test_sleep_downgrade_and_reopen_are_explicit_reasoned_transitions():
    policy = ResearchPolicy()
    branch = make_branch("b", "supported", supported=("s1",))
    slept = policy.apply_correction(branch, CorrectionEvent(
        event_id="e1", branch_id="b", kind="sleep", reason="budget_reallocated",
        source_ref="https://example.invalid/decision", actor="operator", at=2.0))
    assert slept.status == "dormant"
    reopened = policy.apply_correction(slept, CorrectionEvent(
        event_id="e2", branch_id="b", kind="reopen", reason="new_grant",
        source_ref="https://example.invalid/decision2", actor="operator", at=3.0))
    assert reopened.status == "proposed"
    downgraded = policy.apply_correction(make_branch("b", "supported"), CorrectionEvent(
        event_id="e3", branch_id="b", kind="downgrade", reason="weak_evidence",
        source_ref="https://example.invalid/review", actor="reviewer", at=4.0))
    assert downgraded.status == "disputed"


def test_refuted_branch_requires_a_new_condition_branch_and_preserves_the_refutation():
    policy = ResearchPolicy()
    refuted = make_branch("b", "refuted", refuted=("r1",))
    with pytest.raises(ValueError, match="refuted_requires_new_branch"):
        policy.apply_correction(refuted, CorrectionEvent(
            event_id="e1", branch_id="b", kind="reopen", reason="condition changed",
            source_ref="https://example.invalid/note", actor="operator", at=2.0))
    reopened = policy.new_condition_branch(refuted, "b2", {"seed": "1"})
    assert reopened.parent_id == "b" and reopened.status == "proposed"
    assert refuted.status == "refuted" and refuted.refuted_by == ("r1",)


# ---------------------------------------------------------------------------
# Thin snapshot interface for A/P
# ---------------------------------------------------------------------------

def test_snapshot_reports_three_axes_and_advisory_only():
    policy = ResearchPolicy()
    results = [make_result(result_id="r1", execution="succeeded", hypothesis="refuted", contribution="accepted"),
               make_result(result_id="r2", execution="succeeded", hypothesis="supported", contribution="proposed")]
    snapshot = policy.snapshot(results, [make_branch("b", "supported")])
    assert snapshot["policy_version"] == "research-v1"
    assert snapshot["advisory_only"] is True
    assert snapshot["three_axis"]["hypothesis"]["refuted"] == 1
    assert snapshot["three_axis"]["hypothesis"]["supported"] == 1
    assert snapshot["opportunities"]["version"] == "research-v1"


# ---------------------------------------------------------------------------
# Approved-fact projection (no Node bridge, no executor)
# ---------------------------------------------------------------------------

def service_at(root, capability="research.author"):
    config = HostConfig(ledger_path=str(root / "ledger.sqlite3"), swarm_id="research-v1-fixture",
                        workspace=str(root / "project"), worker_id="worker",
                        agent=AgentId(role="builder", instance=0), authorized_scopes=("science",),
                        capabilities=(capability,), assets_root=str(root / "assets"),
                        evidence_root=str(root / "evidence"))
    return ResearchService(config)


def insert_asset(store, asset_id, candidate):
    body = {"type": "Gene", "schema_version": "1.14.0", "id": "local_" + asset_id, "category": "repair",
            "signals_match": ["local_candidate"], "strategy": [candidate.summary,
            "local_candidate_json:" + candidate.model_dump_json()],
            "constraints": {"max_files": candidate.declared_files, "forbidden_paths": [".git/**"]},
            "validation": ["local_assets.AssetValidator"], "asset_id": asset_id}
    with store.connection() as db:
        db.execute("INSERT INTO assets VALUES (?,?)", (asset_id, json.dumps(body)))


def submit_scientific(service, task_id, *, verdict="passed", execution="succeeded",
                      effect="known", purpose="original"):
    from contracts.identity import AttemptId
    from local_assets.models import Candidate, FileChange
    from local_assets.research_models import ResearchClaim, ResearchObservation
    claim = ResearchClaim(plan_id="plan-" + task_id, criterion_version="cv1",
                          conditions={"input": "fixture"}, sources=("https://example.invalid/paper",))
    plan = {"plan_id": claim.plan_id, "criteria": {"version": claim.criterion_version}}
    signal = Signal(task_id=task_id, workspace=service.config.workspace, scope="science/" + task_id,
                    kind="opportunity", required_capability="research.author")
    service.ledger.enqueue(signal, acceptance={"research_claim": claim.model_dump(mode="json"),
                                               "experiment_plan": plan})
    candidate = Candidate(attempt=AttemptId(task_id=task_id, agent=service.config.agent, attempt=1),
                          base_revision="a" * 40, scope=signal.scope,
                          changes=(FileChange(path="science/" + task_id + "/r.txt", before=None, after="fixture"),),
                          declared_files=1, declared_lines=1, research=claim)
    asset_id = "asset-" + task_id
    insert_asset(service.store, asset_id, candidate)
    lease = service.ledger.claim(task_id, "worker", locality=service.locality)
    assert lease is not None
    run_id = task_id + "-run"
    result = {"execution_state": execution, "scientific_verdict": verdict, "effect_state": effect, "provenance": "mock"}
    service.ledger.begin_execution(lease, run_id, max_executions=1)
    service.ledger.record_event("research_execution", {"run_id": run_id, "worker_id": "worker",
                                                       "token": 1, "result": result}, task_id=task_id)
    service.ledger.confirm_execution(lease, run_id)
    observation = ResearchObservation(report_id=task_id + "-report", asset_id=asset_id, task_id=task_id,
                                      worker_id="worker", fencing_token=1, run_id=run_id, sandbox_id=None,
                                      plan_id=claim.plan_id, criterion_version=claim.criterion_version,
                                      conditions=claim.conditions, plan_json=json.dumps(plan),
                                      candidate_json=candidate.model_dump_json(), result_json=json.dumps(result),
                                      provenance="mock", purpose=purpose, execution_state=execution,
                                      scientific_verdict=verdict, created_at=service.ledger.now(),
                                      source_swarm_id=service.config.swarm_id, source_fencing_token=1,
                                      source_attempt=candidate.attempt)
    with service.store.connection() as db:
        db.execute("INSERT INTO research_reports VALUES (?,?,?)",
                   (observation.report_id, asset_id, observation.model_dump_json()))
    service.ledger.submit(lease, task_id + "-result", {"asset_id": asset_id, "run_id": run_id,
                                                       "stage": "evidence_submitted",
                                                       "scientific_verdict": verdict, "execution_state": execution,
                                                       "provenance": "mock"})
    return service


def test_projection_separates_supported_refuted_and_non_scientific(tmp_path):
    service = service_at(tmp_path)
    submit_scientific(service, "supported", verdict="passed")
    submit_scientific(service, "refuted", verdict="failed", purpose="counterexample")
    submit_scientific(service, "crash", verdict="not_evaluated", execution="failed", effect="known")
    submit_scientific(service, "unknown", verdict="failed", execution="succeeded", effect="unknown")
    results = research_feedback(service.ledger, service.store.root)
    by_task = {r.task_id: r for r in results}
    assert set(by_task) == {"supported", "refuted"}
    assert by_task["supported"].hypothesis == "supported"
    assert by_task["refuted"].hypothesis == "refuted"
    assert by_task["refuted"].execution == "succeeded"
    assert all(r.contribution == "proposed" for r in results)
    # crash/unknown produce no scientific three-axis entry.
    assert "crash" not in by_task and "unknown" not in by_task


def test_store_is_idempotent_and_deduplicates_by_result_and_source(tmp_path):
    service = service_at(tmp_path)
    submit_scientific(service, "refuted", verdict="failed", purpose="counterexample")
    results = research_feedback(service.ledger, service.store.root)
    assert len(results) == 1
    store = ResearchFeedbackStore(tmp_path / "policy.sqlite3", service.ledger)
    refuted = results[0]
    decision = store.accept(refuted, reviewer="reviewer-1")
    assert decision.accepted is True
    # Repeated rebuild from the same accepted facts must not double-count.
    accepted = refuted.model_copy(update={"contribution": "accepted"})
    store.synchronize([accepted, accepted])
    assert len(store.contributions()) == 1
    # Same result re-submitted by another reviewer is a duplicate.
    again = store.accept(refuted, reviewer="reviewer-2")
    assert again.accepted is False and again.reasons == ("duplicate_contribution",)
    # Self-approval is rejected and never persisted.
    self_approved = store.accept(refuted, reviewer=refuted.actor)
    assert self_approved.accepted is False and self_approved.reasons == ("self_approval_rejected",)
    assert len(store.contributions()) == 1
    snapshot = store.snapshot()
    assert snapshot["policy_version"] == "research-v1" and snapshot["advisory_only"] is True
    assert snapshot["three_axis"]["contribution"]["accepted"] == 1


def test_correction_events_are_append_only_and_replayed(tmp_path):
    service = service_at(tmp_path)
    store = ResearchFeedbackStore(tmp_path / "policy.sqlite3", service.ledger)
    events = [
        CorrectionEvent(event_id="e1", branch_id="b", kind="sleep", reason="budget",
                        source_ref="https://example.invalid/d1", actor="operator", at=1.0),
        CorrectionEvent(event_id="e2", branch_id="b", kind="reopen", reason="new_grant",
                        source_ref="https://example.invalid/d2", actor="operator", at=2.0),
    ]
    for event in events:
        store.record_correction(event)
    assert [e.kind for e in store.corrections()] == ["sleep", "reopen"]
    assert [e.kind for e in store.corrections(branch_id="b")] == ["sleep", "reopen"]
    assert store.corrections(branch_id="other") == []
    with pytest.raises(ValueError, match="already_recorded"):
        store.record_correction(events[0])


def test_projection_read_failure_is_not_swallowed(tmp_path):
    service = service_at(tmp_path)
    submit_scientific(service, "supported", verdict="passed")
    # A corrupt source archive must fail loudly, never return an empty projection.
    broken = tmp_path / "broken-assets"
    broken.mkdir()
    (broken / "assets.sqlite3").write_bytes(b"not a sqlite database")
    with pytest.raises(sqlite3.Error):
        research_feedback(service.ledger, broken)


def test_router_v0_and_v01_remain_unchanged_by_the_research_v1_policy(tmp_path):
    service = service_at(tmp_path)
    # research-v1 is a separate advisory layer, not a Router strategy version.
    with pytest.raises(ValueError, match="strategy_version"):
        Router(service.field, strategy_version="research-v1")  # type: ignore[arg-type]
    assert ResearchPolicy.version == "research-v1"
