"""Three-axis contribution and research-route policy (research-v1) boundaries.

These tests exercise the pure policy engine and the approved-fact projection
without invoking the Node GEP bridge or any executor. The projection is built
exclusively from immutable ledger/asset facts, so a valid refutation earns a
contribution while a crash, timeout, auth error or unknown effect earns none.
The durable store acceptance re-derives results from trusted facts, binds the
reviewer to a trusted independent review of the exact candidate, and rejects
forged, replayed, self-approved, unreviewed or cross-project results.
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
    CorrectionEvent,
    ResearchPolicy,
    RouteOpportunityPlan,
    SupersessionEvent,
    ThreeAxisResult,
)
from swarm.research.feedback import ResearchFeedbackStore, research_feedback
from swarm.router import Router


def make_result(result_id="r1", source_ref="https://example.invalid/paper", *,
                actor="author-0", execution="succeeded", hypothesis="refuted",
                contribution="proposed", at=1.0, report_id=None, task_id="t1",
                provenance="mock") -> ThreeAxisResult:
    return ThreeAxisResult(
        result_id=result_id, report_id=report_id or (result_id + "-report"), task_id=task_id,
        actor=actor, source_ref=source_ref, provenance=provenance, execution=execution,
        hypothesis=hypothesis, contribution=contribution, at=at,
    )


def make_branch(branch_id="b1", status="proposed", *, authorized=True, supported=(),
                refuted=(), conditions=None, applicability=1.0, goal_relevance=1.0,
                risk=0.0, known_cost=None) -> Branch:
    return Branch(branch_id=branch_id, status=status, authorized=authorized,
                  supported_by=supported, refuted_by=refuted,
                  conditions=conditions or {"seed": "0"}, applicability=applicability,
                  goal_relevance=goal_relevance, risk=risk, known_cost=known_cost)


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
    duplicate_result = make_result(result_id="r1", source_ref="https://example.invalid/paper")
    assert policy.accept(duplicate_result, reviewer="reviewer-2", seen=seen).reasons == ("duplicate_contribution",)
    same_paper = make_result(result_id="r2", source_ref="https://example.invalid/paper")
    assert policy.accept(same_paper, reviewer="reviewer-3", seen=seen).reasons == ("duplicate_contribution",)
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


def test_opportunity_carries_spec_factors_and_unknown_cost_reason():
    policy = ResearchPolicy(exploration_fraction=0.20)
    plan = policy.opportunities([make_branch("a", "proposed", applicability=0.8,
                                             goal_relevance=0.9, risk=0.1, known_cost=None)])
    op = plan.opportunities[0]
    assert op.eligible is True
    assert op.factors["applicability"] == 0.8
    assert op.factors["goal_relevance"] == 0.9
    assert op.factors["risk"] == 0.1
    assert "insufficient_evidence" in op.reasons
    assert "unknown_cost" in op.reasons and op.known_cost is None
    plan2 = policy.opportunities([make_branch("a", "proposed", known_cost=1.5)])
    assert plan2.opportunities[0].known_cost == 1.5
    assert "unknown_cost" not in plan2.opportunities[0].reasons


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

def service_at(root, capability="research.author", swarm_id="research-v1-fixture"):
    config = HostConfig(ledger_path=str(root / "ledger.sqlite3"), swarm_id=swarm_id,
                        workspace=str(root / "project"), worker_id="author",
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


def make_claim_plan(plan_id="plan"):
    from local_assets.research_models import ResearchClaim
    claim = ResearchClaim(plan_id=plan_id, criterion_version="cv1",
                          conditions={"input": "fixture"}, sources=("https://example.invalid/paper",))
    plan = {"plan_id": plan_id, "criteria": {"version": claim.criterion_version}}
    return claim, plan


def make_candidate(agent, task_id, claim):
    from contracts.identity import AttemptId
    from local_assets.models import Candidate, FileChange
    return Candidate(attempt=AttemptId(task_id=task_id, agent=agent, attempt=1),
                     base_revision="a" * 40, scope="science",
                     changes=(FileChange(path="science/r.txt", before=None, after="fixture"),),
                     declared_files=1, declared_lines=1, research=claim)


def submit_observation(service, task_id, worker, *, asset_id, candidate, claim, plan, purpose,
                       verdict="passed", execution="succeeded", effect="known", provenance="mock"):
    from contracts.identity import AttemptId
    from local_assets.research_models import ResearchObservation
    signal = Signal(task_id=task_id, workspace=service.config.workspace, scope="science",
                    kind="opportunity", required_capability="research.author")
    service.ledger.enqueue(signal, acceptance={"research_claim": claim.model_dump(mode="json"),
                                               "experiment_plan": plan})
    lease = service.ledger.claim(task_id, worker, locality=service.locality)
    assert lease is not None
    run_id = task_id + "-run"
    result = {"execution_state": execution, "scientific_verdict": verdict, "effect_state": effect,
              "provenance": provenance}
    service.ledger.begin_execution(lease, run_id, max_executions=1)
    service.ledger.record_event("research_execution", {"run_id": run_id, "worker_id": worker,
                                                       "token": lease.token, "result": result}, task_id=task_id)
    service.ledger.confirm_execution(lease, run_id)
    observation = ResearchObservation(report_id=task_id + "-report", asset_id=asset_id, task_id=task_id,
        worker_id=worker, fencing_token=lease.token, run_id=run_id, sandbox_id=None,
        plan_id=claim.plan_id, criterion_version=claim.criterion_version, conditions=claim.conditions,
        plan_json=json.dumps(plan), candidate_json=candidate.model_dump_json(), result_json=json.dumps(result),
        provenance=provenance, purpose=purpose, execution_state=execution, scientific_verdict=verdict,
        created_at=service.ledger.now(), source_swarm_id=service.config.swarm_id,
        source_fencing_token=lease.token, source_attempt=AttemptId(task_id=task_id, agent=service.config.agent, attempt=1))
    with service.store.connection() as db:
        db.execute("INSERT INTO research_reports VALUES (?,?,?)",
                   (observation.report_id, asset_id, observation.model_dump_json()))
    service.ledger.submit(lease, task_id + "-result", {"asset_id": asset_id, "run_id": run_id,
                                                       "stage": "evidence_submitted",
                                                       "scientific_verdict": verdict, "execution_state": execution,
                                                       "provenance": provenance})
    return service


def submit_scientific(service, task_id, *, verdict="passed", execution="succeeded",
                      effect="known", purpose="original", provenance="mock"):
    claim, plan = make_claim_plan("plan-" + task_id)
    candidate = make_candidate(service.config.agent, task_id, claim)
    asset_id = "asset-" + task_id
    insert_asset(service.store, asset_id, candidate)
    return submit_observation(service, task_id, "author", asset_id=asset_id, candidate=candidate,
                              claim=claim, plan=plan, purpose=purpose, verdict=verdict,
                              execution=execution, effect=effect, provenance=provenance)


def submit_review(service, source_task_id, reviewer, *, purpose="reproduction", verdict="passed"):
    """A trusted independent review: the reviewer runs a distinct completed task
    that reproduces/counters the source candidate on the same asset."""
    claim, plan = make_claim_plan("plan-" + source_task_id)
    candidate = make_candidate(service.config.agent, source_task_id, claim)
    review_task_id = source_task_id + "-review-" + reviewer
    return submit_observation(service, review_task_id, reviewer, asset_id="asset-" + source_task_id,
                              candidate=candidate, claim=claim, plan=plan, purpose=purpose, verdict=verdict)


def store_for(root, service, reviewer):
    return ResearchFeedbackStore(root / "policy.sqlite3", service.ledger, service.store.root,
                                 reviewer=reviewer)


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
    assert "crash" not in by_task and "unknown" not in by_task


def test_legacy_failed_original_is_not_a_refutation(tmp_path):
    service = service_at(tmp_path)
    submit_scientific(service, "failed-original", verdict="failed", purpose="original")
    results = research_feedback(service.ledger, service.store.root)
    assert results == []


def test_store_accept_binds_to_trusted_fact_and_records_reviewer(tmp_path):
    service = service_at(tmp_path)
    submit_scientific(service, "supported", verdict="passed")
    submit_review(service, "supported", "reviewer-1", purpose="reproduction", verdict="passed")
    store = store_for(tmp_path, service, "reviewer-1")
    decision = store.accept("supported-result")
    assert decision.accepted is True
    contributions = store.contributions()
    assert len(contributions) == 1
    persisted = contributions[0]
    # Identity is re-derived from the trusted fact, never from caller input.
    assert persisted.actor == "author" and persisted.task_id == "supported"
    assert persisted.reviewer == "reviewer-1" and persisted.contribution == "accepted"
    assert persisted.source_ref == "https://example.invalid/paper"
    assert persisted.asset_id == "asset-supported"


def test_advisory_opportunities_reference_contributions(tmp_path):
    service = service_at(tmp_path)
    submit_scientific(service, "supported", verdict="passed")
    submit_review(service, "supported", "reviewer-1", purpose="reproduction", verdict="passed")
    store = store_for(tmp_path, service, "reviewer-1")
    assert store.accept("supported-result").accepted is True
    branch = Branch(branch_id="b", status="supported", supported_by=("supported-result",))
    advisory = store.advisory([branch])
    assert advisory["advisory_only"] is True and advisory["claim_requires_recheck"] is True
    assert advisory["policy_version"] == "research-v1"
    # The opportunity references the real accepted contribution, not a bare score.
    opportunity = advisory["opportunities"]["opportunities"][0]
    assert opportunity["supported_by"] == ["supported-result"]
    assert [c["result_id"] for c in advisory["contributions"]] == ["supported-result"]
    assert advisory["contributions"][0]["contribution"] == "accepted"


def test_route_opportunity_carries_contribution_references():
    policy = ResearchPolicy(exploration_fraction=0.0)
    plan = policy.opportunities([make_branch("b", "supported", supported=("r1",), refuted=("r2",))])
    op = plan.opportunities[0]
    assert op.supported_by == ("r1",) and op.refuted_by == ("r2",)


def test_store_accept_rejects_forged_replay_self_cross_project_and_unreviewed(tmp_path):
    service = service_at(tmp_path)
    submit_scientific(service, "supported", verdict="passed")
    submit_review(service, "supported", "reviewer-1", purpose="reproduction", verdict="passed")
    store = store_for(tmp_path, service, "reviewer-1")
    # Forged result id: no such trusted result.
    assert store.accept("does-not-exist").reasons == ("untrusted_result",)
    # A replayed provenance cannot establish a new acceptance.
    submit_scientific(service, "replayed", verdict="passed", provenance="replay")
    assert store.accept("replayed-result").reasons == ("replay_not_acceptable",)
    # Cross-project: a result from a different swarm is not in this store's trusted facts.
    other = service_at(tmp_path / "other", swarm_id="other-swarm")
    submit_scientific(other, "foreign", verdict="failed", purpose="counterexample")
    assert store.accept("foreign-result").reasons == ("untrusted_result",)
    # A reviewer with no trusted independent review of this candidate is not admitted.
    store2 = store_for(tmp_path, service, "unreviewed-actor")
    assert store2.accept("supported-result").reasons == ("reviewer_not_admitted",)
    assert store2.contributions() == []


def test_known_actor_that_claimed_but_did_not_review_is_rejected(tmp_path):
    service = service_at(tmp_path)
    submit_scientific(service, "supported", verdict="passed")
    # Make "known-actor" a real task-claimer, but it never reviewed this result.
    service.ledger.enqueue(Signal(task_id="claim-known", workspace=service.config.workspace,
                                  scope="science/claim-known", kind="opportunity",
                                  required_capability="research.author"))
    assert service.ledger.claim("claim-known", "known-actor", locality=service.locality) is not None
    store = store_for(tmp_path, service, "known-actor")
    assert store.accept("supported-result").reasons == ("reviewer_not_admitted",)
    assert store.contributions() == []


def test_review_observation_without_ledger_execution_cannot_authorize(tmp_path):
    service = service_at(tmp_path)
    submit_scientific(service, "supported", verdict="passed")
    # A caller-invented review observation with no task/lease/run/result must not authorize.
    from local_assets.research_models import ResearchObservation
    with service.store.connection() as db:
        row = db.execute("SELECT body FROM research_reports WHERE report_id=?", ("supported-report",)).fetchone()
        original = ResearchObservation.model_validate_json(row[0])
        fake = original.model_copy(update={"report_id": "fake-review", "task_id": "missing-review-task",
                                           "worker_id": "reviewer-1", "run_id": "missing-review-run",
                                           "purpose": "reproduction"})
        db.execute("INSERT INTO research_reports VALUES (?,?,?)",
                   (fake.report_id, fake.asset_id, fake.model_dump_json()))
    store = store_for(tmp_path, service, "reviewer-1")
    assert store.accept("supported-result").reasons == ("reviewer_not_admitted",)
    assert store.contributions() == []


def test_store_accept_is_idempotent_and_deduplicates(tmp_path):
    service = service_at(tmp_path)
    submit_scientific(service, "supported", verdict="passed")
    submit_review(service, "supported", "reviewer-1", purpose="reproduction", verdict="passed")
    submit_review(service, "supported", "reviewer-2", purpose="reproduction", verdict="passed")
    store = store_for(tmp_path, service, "reviewer-1")
    assert store.accept("supported-result").accepted is True
    store2 = store_for(tmp_path, service, "reviewer-2")
    again = store2.accept("supported-result")
    assert again.accepted is False
    assert len(store.contributions()) == 1
    snapshot = store.snapshot()
    assert snapshot["policy_version"] == "research-v1" and snapshot["advisory_only"] is True
    assert snapshot["three_axis"]["contribution"]["accepted"] == 1


def test_supersession_is_append_only_and_never_deletes_the_original(tmp_path):
    service = service_at(tmp_path)
    submit_scientific(service, "supported", verdict="passed")
    submit_review(service, "supported", "reviewer-1", purpose="reproduction", verdict="passed")
    store = store_for(tmp_path, service, "reviewer-1")
    assert store.accept("supported-result").accepted is True
    store.record_supersession(SupersessionEvent(
        event_id="s1", result_id="supported-result", reason="superseded_by_reanalysis",
        source_ref="https://example.invalid/new", actor="reviewer-2", at=2.0))
    # Original record is preserved; the effective view marks it superseded.
    assert [c.contribution for c in store.contributions()] == ["accepted"]
    assert [c.contribution for c in store.effective_contributions()] == ["superseded"]
    assert store.snapshot()["three_axis"]["contribution"]["superseded"] == 1
    assert store.snapshot()["three_axis"]["contribution"].get("accepted", 0) == 0
    with pytest.raises(ValueError, match="already_recorded"):
        store.record_supersession(SupersessionEvent(
            event_id="s1", result_id="supported-result", reason="dup",
            source_ref="https://example.invalid/dup", actor="reviewer-3", at=3.0))


def test_correction_events_are_append_only_and_replayed(tmp_path):
    service = service_at(tmp_path)
    store = store_for(tmp_path, service, "reviewer-1")
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


def test_fresh_rebuild_writes_to_a_new_destination_and_never_mutates_source(tmp_path):
    service = service_at(tmp_path)
    submit_scientific(service, "supported", verdict="passed")
    submit_review(service, "supported", "reviewer-1", purpose="reproduction", verdict="passed")
    source = store_for(tmp_path, service, "reviewer-1")
    assert source.accept("supported-result").accepted is True
    before = source.snapshot()
    # A fresh rebuild is a new store at a new path; the source store is untouched.
    rebuilt = ResearchFeedbackStore(tmp_path / "rebuilt.sqlite3", service.ledger, service.store.root,
                                    reviewer="reviewer-1")
    assert rebuilt.accept("supported-result").accepted is True
    assert source.snapshot() == before
    assert len(source.contributions()) == 1 and len(rebuilt.contributions()) == 1


def test_projection_read_failure_is_not_swallowed(tmp_path):
    service = service_at(tmp_path)
    submit_scientific(service, "supported", verdict="passed")
    broken = tmp_path / "broken-assets"
    broken.mkdir()
    (broken / "assets.sqlite3").write_bytes(b"not a sqlite database")
    with pytest.raises(sqlite3.Error):
        research_feedback(service.ledger, broken)


def test_router_v0_and_v01_remain_unchanged_by_the_research_v1_policy(tmp_path):
    service = service_at(tmp_path)
    with pytest.raises(ValueError, match="strategy_version"):
        Router(service.field, strategy_version="research-v1")  # type: ignore[arg-type]
    assert ResearchPolicy.version == "research-v1"
