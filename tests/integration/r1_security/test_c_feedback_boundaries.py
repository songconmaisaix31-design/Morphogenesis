"""Persisted research contributions require authoritative facts, not caller labels."""
import inspect
import json

import pytest

from contracts.identity import AgentId, AttemptId
from local_assets.models import Candidate, FileChange
from local_assets.research_models import ResearchClaim, ResearchObservation
from local_assets.store import LocalAssetStore
from swarm.models import Locality, Signal
from swarm.research.feedback import ResearchFeedbackStore, research_feedback
from swarm.research.policy import Branch, CorrectionEvent, ResearchPolicy, ThreeAxisResult
from swarm.task_ledger import TaskLedger


def store(root):
    ledger = TaskLedger(root / "ledger.db", "q-security", clock=lambda: 100.0)
    # C successor adds an assets-root binding; preserve coverage of both the
    # original first-RED API and the versioned repair API without importing helpers.
    kwargs = {"clock": lambda: 100.0}
    if "assets_root" in inspect.signature(ResearchFeedbackStore).parameters:
        kwargs["assets_root"] = root / "assets"
    if "reviewer" in inspect.signature(ResearchFeedbackStore).parameters:
        kwargs["reviewer"] = "nominated-reviewer"  # trusted host fixture identity
    return ResearchFeedbackStore(root / "feedback.db", ledger, **kwargs)


def accept(s, value, reviewer="invented-reviewer"):
    # Successor moves identity to host construction and removes caller reviewer.
    if "result_id" in inspect.signature(s.accept).parameters and isinstance(value, ThreeAxisResult):
        value = value.result_id
    if "reviewer" in inspect.signature(s.accept).parameters:
        return s.accept(value, reviewer=reviewer)
    return s.accept(value)


def forged(**updates):
    data = dict(result_id="invented", report_id="invented-report", task_id="missing-task",
                actor="attacker", source_ref="invented-source", provenance="live",
                execution="succeeded", hypothesis="supported", at=100)
    data.update(updates)
    return ThreeAxisResult(**data)


@pytest.mark.parametrize("hypothesis", ["supported", "refuted"])
def test_forged_result_and_reviewer_never_persist(tmp_path, hypothesis):
    s = store(tmp_path)
    try:
        decision = accept(s, forged(hypothesis=hypothesis))
    except (ValueError, PermissionError, KeyError):
        pass
    else:
        assert not decision.accepted, "caller result/reviewer granted scientific contribution"
    assert s.contributions() == []


def test_synchronize_does_not_import_caller_accepted_label(tmp_path):
    s = store(tmp_path)
    synchronize = getattr(s, "synchronize", None)
    if synchronize is not None:
        try:
            synchronize([forged(contribution="accepted")])
        except (ValueError, PermissionError, KeyError):
            pass
    assert s.contributions() == []


@pytest.mark.parametrize("execution", ["unknown", "failed", "cancelled", "running", "not_run"])
def test_unknown_and_crash_do_not_reward(tmp_path, execution):
    s = store(tmp_path)
    try:
        decision = accept(s, forged(execution=execution))
    except (ValueError, PermissionError, KeyError):
        pass
    else:
        assert not decision.accepted
    assert s.contributions() == []


def test_empty_ledger_has_no_scientific_feedback(tmp_path):
    s = store(tmp_path)
    assert research_feedback(s.ledger, tmp_path / "no-assets") == []


def test_corrections_append_and_keep_prior_event(tmp_path):
    s = store(tmp_path)
    first = CorrectionEvent(event_id="sleep", branch_id="b", kind="sleep", reason="review",
                            source_ref="evidence", actor="reviewer", at=100)
    second = first.model_copy(update={"event_id": "reopen", "kind": "reopen", "at": 101})
    s.record_correction(first)
    s.record_correction(second)
    assert s.corrections("b") == [first, second]
    assert store(tmp_path).corrections("b") == [first, second]


def test_exploration_does_not_authorize_out_of_scope_branch():
    plan = ResearchPolicy().opportunities([Branch(branch_id="private", status="proposed", authorized=False)])
    assert plan.opportunities[0].share == 0
    assert not plan.opportunities[0].eligible


def scientific_fixture(root, *, execution="succeeded", verdict="failed", effect="known", branch_id=None):
    """Host-only fixture writes through existing ledger/store contracts.

    This constructs a known, submitted counterexample chain and never runs an
    experiment. It is deterministic contract_local evidence, not live science.
    """
    s = store(root)
    assets = LocalAssetStore(root / "assets")
    locality = Locality(workspace=str(root / "workspace"), authorized_scopes=("science",))
    agent = AgentId(role="builder", instance=0)
    claim = ResearchClaim(plan_id="fixture-plan", criterion_version="v1",
                          conditions={"data": "fixture"}, sources=("fixture-source",))
    p = {"plan_id": claim.plan_id, "criteria": {"version": claim.criterion_version}}
    signal = Signal(task_id="refuted", workspace=locality.workspace, scope="science/refuted",
                    kind="opportunity", required_capability="research.author",
                    payload={"project_id": "p1", "branch_id": branch_id} if branch_id is not None else {})
    s.ledger.enqueue(signal, acceptance={"research_claim": claim.model_dump(mode="json"),
                                         "experiment_plan": p})
    candidate = Candidate(attempt=AttemptId(task_id="refuted", agent=agent, attempt=1),
                          base_revision="a" * 40, scope=signal.scope,
                          changes=(FileChange(path="science/refuted/r.txt", before=None, after="fixture"),),
                          declared_files=1, declared_lines=1, research=claim)
    asset = {"type": "Gene", "schema_version": "1.14.0", "id": "local_fixture", "category": "repair",
             "signals_match": ["local_candidate"], "strategy": [candidate.summary,
             "local_candidate_json:" + candidate.model_dump_json()],
             "constraints": {"max_files": 1, "forbidden_paths": [".git/**"]},
             "validation": ["local_assets.AssetValidator"], "asset_id": "fixture-asset"}
    with assets.connection() as db:
        db.execute("INSERT INTO assets VALUES (?,?)", ("fixture-asset", json.dumps(asset)))
    lease = s.ledger.claim("refuted", "author", locality=locality)
    assert lease is not None
    raw = {"execution_state": execution, "scientific_verdict": verdict, "effect_state": effect,
           "provenance": "mock"}
    s.ledger.begin_execution(lease, "fixture-run", max_executions=1)
    s.ledger.record_event("research_execution", {"run_id": "fixture-run", "worker_id": "author",
                                                 "token": lease.token, "result": raw}, task_id="refuted")
    s.ledger.confirm_execution(lease, "fixture-run")
    observation = ResearchObservation(report_id="fixture-report", asset_id="fixture-asset", task_id="refuted",
        worker_id="author", fencing_token=lease.token, run_id="fixture-run", sandbox_id=None,
        plan_id=claim.plan_id, criterion_version=claim.criterion_version, conditions=claim.conditions,
        plan_json=json.dumps(p), candidate_json=candidate.model_dump_json(), result_json=json.dumps(raw),
        provenance="mock", purpose="counterexample", execution_state=execution, scientific_verdict=verdict,
        created_at=100, source_swarm_id=s.ledger.swarm_id, source_fencing_token=lease.token,
        source_attempt=candidate.attempt)
    with assets.connection() as db:
        db.execute("INSERT INTO research_reports VALUES (?,?,?)",
                   (observation.report_id, "fixture-asset", observation.model_dump_json()))
    s.ledger.submit(lease, "fixture-result", {"asset_id": "fixture-asset", "run_id": "fixture-run",
        "stage": "evidence_submitted", "scientific_verdict": verdict, "execution_state": execution,
        "provenance": "mock"})
    facts = research_feedback(s.ledger, assets.root)
    return s, facts, locality


def trusted_refutation(root):
    s, facts, locality = scientific_fixture(root)
    assert len(facts) == 1 and facts[0].hypothesis == "refuted"
    return s, facts[0], locality


@pytest.mark.parametrize("known_actor", [False, True])
def test_nomination_of_unknown_or_unrelated_known_reviewer_cannot_accept(tmp_path, known_actor):
    s, fact, locality = trusted_refutation(tmp_path)
    if known_actor:
        s.ledger.enqueue(Signal(task_id="unrelated", workspace=locality.workspace, scope="science/elsewhere",
                                kind="opportunity", required_capability="research.author"))
        assert s.ledger.claim("unrelated", "nominated-reviewer", locality=locality) is not None
    # Knowing/claiming another task does not establish review of this result.
    value = fact.result_id if "result_id" in inspect.signature(s.accept).parameters else fact
    try:
        decision = accept(s, value, reviewer="nominated-reviewer")
    except (ValueError, PermissionError, KeyError):
        pass
    else:
        assert not decision.accepted, "nominated identity has no result-bound independent review"
    assert s.contributions() == []


def test_review_observation_without_ledger_execution_cannot_authorize(tmp_path):
    s, fact, locality = trusted_refutation(tmp_path)
    assets = LocalAssetStore(tmp_path / "assets")
    with assets.connection() as db:
        row = db.execute("SELECT body FROM research_reports WHERE report_id=?", ("fixture-report",)).fetchone()
        original = ResearchObservation.model_validate_json(row[0])
        # Caller-invented reviewer observation has no task, lease, run, or result.
        fake = original.model_copy(update={"report_id": "fake-review", "task_id": "missing-review-task",
            "worker_id": "nominated-reviewer", "run_id": "missing-review-run", "purpose": "reproduction"})
        db.execute("INSERT INTO research_reports VALUES (?,?,?)",
                   (fake.report_id, fake.asset_id, fake.model_dump_json()))
    value = fact.result_id if "result_id" in inspect.signature(s.accept).parameters else fact
    decision = accept(s, value, reviewer="nominated-reviewer")
    assert not decision.accepted, "unbound review report granted independent acceptance"
    assert s.contributions() == []


@pytest.mark.parametrize("execution,verdict,effect", [
    ("failed", "not_evaluated", "known"),
    ("timeout", "not_evaluated", "known"),
    ("unknown", "not_evaluated", "unknown"),
    ("succeeded", "failed", "unknown"),
])
def test_projection_unknown_crash_timeout_and_unknown_effect_earn_no_reward(tmp_path, execution, verdict, effect):
    s, facts, locality = scientific_fixture(tmp_path, execution=execution, verdict=verdict, effect=effect)
    assert facts == [], "non-scientific source ledger/store state produced scientific contribution"
    value = "fixture-result" if "result_id" in inspect.signature(s.accept).parameters else forged(execution="unknown")
    decision = accept(s, value)
    assert not decision.accepted
    assert s.contributions() == []


def independent_review(s, root, locality, *, execution="succeeded", verdict="failed", effect="known"):
    """A distinct review task with real local ledger claim/confirm/submit facts."""
    assets = LocalAssetStore(root / "assets")
    with assets.connection() as db:
        original = ResearchObservation.model_validate_json(db.execute(
            "SELECT body FROM research_reports WHERE report_id=?", ("fixture-report",)).fetchone()[0])
    source_task = s.ledger.get("refuted")
    s.ledger.enqueue(Signal(task_id="review-task", workspace=locality.workspace,
        scope=source_task.signal.scope, kind="opportunity", required_capability="research.counterexample",
        payload=source_task.signal.payload),
        acceptance=source_task.acceptance)
    lease = s.ledger.claim("review-task", "nominated-reviewer", locality=locality)
    assert lease is not None
    raw = {"execution_state": execution, "scientific_verdict": verdict,
           "effect_state": effect, "provenance": "mock"}
    s.ledger.begin_execution(lease, "review-run", max_executions=1)
    s.ledger.record_event("research_execution", {"run_id": "review-run", "worker_id": "nominated-reviewer",
        "token": lease.token, "result": raw}, task_id="review-task")
    s.ledger.confirm_execution(lease, "review-run")
    observation = original.model_copy(update={"report_id": "review-report", "task_id": "review-task",
        "worker_id": "nominated-reviewer", "fencing_token": lease.token, "run_id": "review-run",
        "execution_state": execution, "scientific_verdict": verdict, "result_json": json.dumps(raw),
        "source_fencing_token": lease.token,
        "source_attempt": AttemptId(task_id="review-task", agent=AgentId(role="reviewer", instance=1), attempt=1)})
    with assets.connection() as db:
        db.execute("INSERT INTO research_reports VALUES (?,?,?)",
                   (observation.report_id, observation.asset_id, observation.model_dump_json()))
    s.ledger.submit(lease, "review-result", {"asset_id": observation.asset_id, "run_id": "review-run",
        "stage": "evidence_submitted", "execution_state": execution,
        "scientific_verdict": verdict, "provenance": "mock"})


def test_trusted_independent_refutation_accepted_once_and_history_retained(tmp_path):
    s, fact, locality = trusted_refutation(tmp_path)
    independent_review(s, tmp_path, locality)
    projected = research_feedback(s.ledger, tmp_path / "assets")
    assert {f.task_id for f in projected} == {"refuted", "review-task"}
    value = fact.result_id if "result_id" in inspect.signature(s.accept).parameters else fact
    assert accept(s, value, reviewer="nominated-reviewer").accepted
    assert not accept(s, value, reviewer="nominated-reviewer").accepted
    original = s.contributions()
    assert len(original) == 1 and original[0].contribution == "accepted"
    assert store(tmp_path).contributions() == original
    if hasattr(s, "record_supersession"):
        from swarm.research.policy import SupersessionEvent

        s.record_supersession(SupersessionEvent(event_id="supersede", result_id=fact.result_id,
            reason="new evidence", source_ref="fixture-correction", actor="nominated-reviewer", at=101))
        assert s.contributions() == original
        assert s.effective_contributions()[0].contribution == "superseded"


@pytest.mark.parametrize("execution,verdict,effect", [
    ("failed", "not_evaluated", "known"),
    ("unknown", "not_evaluated", "unknown"),
    ("succeeded", "failed", "unknown"),
])
def test_crashed_or_unknown_review_cannot_authorize_original_contribution(tmp_path, execution, verdict, effect):
    s, fact, locality = trusted_refutation(tmp_path)
    independent_review(s, tmp_path, locality, execution=execution, verdict=verdict, effect=effect)
    value = fact.result_id if "result_id" in inspect.signature(s.accept).parameters else fact
    assert not accept(s, value, reviewer="nominated-reviewer").accepted
    assert s.contributions() == []
