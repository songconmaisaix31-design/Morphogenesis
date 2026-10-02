"""Actual generated archive -> report -> ledger -> contribution -> opportunity.

The original executor writes archives using B's inert mock backend. Candidate
source is never run on the host, no network or live science is involved.
"""
from __future__ import annotations

import json
import socket
import subprocess
from pathlib import Path

import pytest

from contracts.identity import AgentId, AttemptId
from local_assets.generated_validation import generated_candidate, record_generated_observation
from local_assets.models import AssetSafetyError
from local_assets.store import LocalAssetStore
from orchestration.experiments.generated import GeneratedContext
from orchestration.experiments.generated_executor import GeneratedExperimentExecutor
from orchestration.experiments.trusted import TrustedCriteriaRecord, TrustedCriteriaRegistry
from swarm.feedback import ReadonlyLedger, trusted_facts
from swarm.models import Locality, Signal
from swarm.research.feedback import ResearchFeedbackStore, research_feedback
from swarm.research.policy import Branch, SupersessionEvent
from swarm.task_ledger import TaskLedger, connection
from tests.experiments.generated_helpers import (
    GENERATED_CODE, MockGeneratedBackend, make_poisson_plan, mock_isolation,
    poisson_reference_output, poisson_wrong_output, verified_probe_registry,
)
from tests.local_assets.test_generated_validation import FakeBridge


@pytest.fixture(autouse=True)
def forbid_host_execution_and_network(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("generated feedback tests forbid host child processes and network")
    monkeypatch.setattr(subprocess, "Popen", denied)
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket.socket, "connect_ex", denied)


class DistinctMockBackend(MockGeneratedBackend):
    def create(self, plan, context):
        session = super().create(plan, context)
        session.id = context.run_id + "-sandbox"
        return session


class GeneratedFixture:
    def __init__(self, root: Path):
        self.root = root
        self.ledger = TaskLedger(root / "ledger.sqlite3", "generated-policy")
        self.assets = LocalAssetStore(root / "assets", bridge=FakeBridge())
        self.locality = Locality(workspace=str(root / "workspace"), authorized_scopes=("science",))
        self.plan = make_poisson_plan(n_intervals=4)
        self.criteria = TrustedCriteriaRegistry((TrustedCriteriaRecord(
            spec=self.plan.evaluation, approved_by="criteria-reviewer", approved_at=1.0),))
        self.feedback = ResearchFeedbackStore(root / "feedback.sqlite3", self.ledger, self.assets.root,
            reviewer="independent-reviewer", generated_criteria=self.criteria,
            project_id=self.plan.project_id, archive_root=root / "archives")
        self.plans = {}
        self.reports = {}

    def run(self, task_id, *, source=None, output=None, branch_id=None, worker=None,
            purpose=None, timeout=False, exit_code=0, frozen_criteria=True):
        original = source or task_id
        worker = worker or ("independent-reviewer" if source else "candidate-author")
        plan = (self.plans[source] if source else self.plan).model_copy(update={
            "task_id": task_id,
            "branch_id": branch_id or original + "-branch"})
        scope = "science/" + original
        attempt = AttemptId(task_id=task_id, agent=AgentId(role="reviewer" if source else "builder", instance=0),
                            attempt=1)
        if not source:
            candidate = generated_candidate(plan, {"experiment.py": GENERATED_CODE.encode()},
                attempt=attempt, scope=scope, summary="Inert generated policy fixture")
            plan = plan.model_copy(update={"candidate_asset_id": self.assets.publish(candidate)})
        self.plans[task_id] = plan
        self.ledger.enqueue(Signal(task_id=task_id, workspace=self.locality.workspace, scope=scope,
            kind="opportunity", required_capability="research.generated",
            payload={"project_id": plan.project_id, "branch_id": plan.branch_id}),
            acceptance={"generated_plan": plan.model_dump(mode="json")})
        lease = self.ledger.claim(task_id, worker, locality=self.locality)
        assert lease is not None
        assert self.ledger.get(task_id).attempts == attempt.attempt
        context = GeneratedContext(run_id=task_id + "-run", task_id=task_id, worker_id=worker,
            fencing_token=lease.token, author="candidate-author", reviewer="criteria-reviewer")
        backend = DistinctMockBackend(self.root / "mock" / task_id,
            output=output if output is not None else poisson_reference_output(4),
            timeout=timeout, entry_exit_code=exit_code, isolation=mock_isolation(plan=plan))
        executor = GeneratedExperimentExecutor(backend, probe_registry=verified_probe_registry(plan=plan),
                                               criteria_registry=self.criteria if frozen_criteria else None)
        self.ledger.begin_execution(lease, context.run_id, max_executions=1)
        result = executor.execute(plan, context, {"experiment.py": GENERATED_CODE.encode()}, self.root / "archives")
        assert result.provenance == "mock"
        with self.ledger.fenced(lease) as owned:
            report = record_generated_observation(self.assets, plan.candidate_asset_id,
                archive_root=self.root / "archives", plan=plan, context=context,
                purpose=purpose or ("reproduction" if source else "original"), criteria_registry=self.criteria,
                assert_owned=owned, source_swarm_id=self.ledger.swarm_id,
                source_attempt=attempt, source_fencing_token=lease.token)
        self.reports[task_id] = report
        self.ledger.record_event("research_execution", {"run_id": context.run_id, "worker_id": worker,
            "token": lease.token, "result": json.loads(report.result_json)}, task_id=task_id)
        self.ledger.confirm_execution(lease, context.run_id)
        self.ledger.submit(lease, task_id + "-result", {
            "stage": "evidence_submitted", "asset_id": report.asset_id, "run_id": report.run_id,
            "report_id": report.report_id, "execution_state": report.execution_state,
            "scientific_verdict": report.scientific_verdict, "provenance": report.provenance})
        return result


def test_generated_supported_refuted_and_inconclusive_reach_real_trusted_store(tmp_path):
    f = GeneratedFixture(tmp_path)
    f.run("support")
    f.run("support-review", source="support")
    f.run("refute", output=poisson_wrong_output(4))
    f.run("refute-review", source="refute", output=poisson_wrong_output(4), purpose="counterexample")
    f.run("uncertain", output=b'{"candidate_self_score": 1}')
    facts = {fact.task_id: fact for fact in f.feedback.trusted()}
    assert facts["support"].hypothesis == "supported"
    assert facts["refute"].hypothesis == "refuted"
    assert facts["uncertain"].hypothesis == "inconclusive"
    assert all(fact.contribution == "proposed" and fact.provenance == "mock" for fact in facts.values())
    assert trusted_facts(f.ledger, f.assets.root) == []  # no generated -> v0.1 promotion
    branches = [Branch(branch_id="support-branch", status="exploring"),
                Branch(branch_id="refute-branch", status="exploring")]
    before = f.feedback.advisory(branches)
    assert f.feedback.accept("support-result").accepted
    assert f.feedback.accept("refute-result").accepted
    assert not f.feedback.accept("uncertain-result").accepted
    assert not f.feedback.accept("support-result").accepted
    accepted = f.feedback.contributions()
    assert {fact.hypothesis for fact in accepted} == {"supported", "refuted"}
    assert {fact.review_report_id for fact in accepted} == {
        f.reports["support-review"].report_id, f.reports["refute-review"].report_id}
    after = f.feedback.advisory(branches)  # same input; store resolves accepted source refs
    next_opportunities = after["opportunities"]["opportunities"]
    assert next_opportunities[0]["supported_by"] == ["support-result"]
    assert next_opportunities[1]["refuted_by"] == ["refute-result"]
    assert next_opportunities[1]["share"] < before["opportunities"]["opportunities"][1]["share"]
    assert sum(op["share"] for op in next_opportunities) == pytest.approx(1)
    assert f.feedback.snapshot()["results"]


@pytest.mark.parametrize("fault", ["timeout", "crash", "unknown_effect", "unconfirmed", "missing_audit",
    "audit_worker", "audit_token", "audit_output", "completion_token", "wrong_asset", "source_attempt",
    "wrong_project", "wrong_branch", "missing_criteria", "late_criteria"])
def test_generated_invalid_original_never_enters_accepted_store(tmp_path, fault):
    f = GeneratedFixture(tmp_path)
    f.run("source", timeout=fault == "timeout", exit_code=1 if fault == "crash" else 0)
    report = f.reports["source"]
    with connection(f.ledger.path, write=True) as db:
        if fault == "unconfirmed":
            db.execute("UPDATE tasks SET unconfirmed_request_id='source-run' WHERE task_id='source'")
        elif fault == "missing_audit":
            db.execute("DELETE FROM task_audit WHERE event='research_execution'")
        elif fault.startswith("audit_"):
            row = db.execute("SELECT sequence,body FROM task_audit WHERE event='research_execution'").fetchone()
            body = json.loads(row[1])
            if fault == "audit_worker":
                body["worker_id"] = "forged"
            elif fault == "audit_token":
                body["token"] += 1
            else:
                body["result"]["experiment_result"]["assessment"]["hypothesis"] = "refuted"
            db.execute("UPDATE task_audit SET body=? WHERE sequence=?", (json.dumps(body), row[0]))
        elif fault == "completion_token":
            row = db.execute("SELECT sequence,body FROM task_audit WHERE event='completed'").fetchone()
            body = json.loads(row[1]); body["token"] += 1
            db.execute("UPDATE task_audit SET body=? WHERE sequence=?", (json.dumps(body), row[0]))
        elif fault in {"wrong_project", "wrong_branch"}:
            row = db.execute("SELECT signal FROM tasks WHERE task_id='source'").fetchone()
            signal = json.loads(row[0])
            signal["payload"]["project_id" if fault == "wrong_project" else "branch_id"] = "foreign"
            db.execute("UPDATE tasks SET signal=? WHERE task_id='source'", (json.dumps(signal),))
    if fault in {"unknown_effect", "wrong_asset", "source_attempt"}:
        updates = {}
        if fault == "wrong_asset":
            updates["asset_id"] = "foreign"
        elif fault == "source_attempt":
            updates["source_attempt"] = report.source_attempt.model_copy(update={"task_id": "foreign"})
        else:
            payload = json.loads(report.result_json); payload["effect_state"] = "unknown"
            updates["result_json"] = json.dumps(payload)
        with f.assets.connection() as db:
            db.execute("DROP TRIGGER research_reports_UPDATE")  # simulate offline archive tampering
            db.execute("UPDATE research_reports SET body=? WHERE report_id=?",
                (report.model_copy(update=updates).model_dump_json(), report.report_id))
    if fault == "missing_criteria":
        f.feedback.generated_criteria = None
    elif fault == "late_criteria":
        f.feedback.generated_criteria = TrustedCriteriaRegistry((TrustedCriteriaRecord(
            spec=f.plan.evaluation, approved_by="criteria-reviewer", approved_at=f.ledger.now() + 10),))
    assert not f.feedback.accept("source-result").accepted
    assert f.feedback.contributions() == []


@pytest.mark.parametrize("review", ["missing", "self", "disagrees", "timeout", "same_sandbox", "replay"])
def test_generated_review_is_independent_concordant_and_confirmed(tmp_path, review):
    f = GeneratedFixture(tmp_path)
    f.run("source")
    if review != "missing":
        f.run("review", source="source", worker="candidate-author" if review == "self" else None,
              output=poisson_wrong_output(4) if review == "disagrees" else None,
              timeout=review == "timeout")
    if review in {"same_sandbox", "replay"}:
        report = f.reports["review"]
        updates = {"sandbox_id": f.reports["source"].sandbox_id} if review == "same_sandbox" else {"provenance": "replay"}
        with f.assets.connection() as db:
            db.execute("DROP TRIGGER research_reports_UPDATE")  # simulate offline archive tampering
            db.execute("UPDATE research_reports SET body=? WHERE report_id=?",
                (report.model_copy(update=updates).model_dump_json(), report.report_id))
    try:
        decision = f.feedback.accept("source-result")
    except (ValueError, AssetSafetyError):
        pass
    else:
        assert not decision.accepted
    assert f.feedback.contributions() == []


def test_generated_raw_bytes_are_checked_on_accept_and_every_advisory(tmp_path):
    f = GeneratedFixture(tmp_path)
    f.run("source"); f.run("review", source="source")
    assert f.feedback.accept("source-result").accepted
    output = tmp_path / "archives" / "source-run" / "outputs" / "output.json"
    output.write_bytes(poisson_wrong_output(4))
    with pytest.raises((ValueError, AssetSafetyError)):
        f.feedback.advisory([Branch(branch_id="source-branch", status="exploring", supported_by=("source-result",))])
    assert len(f.feedback.contributions()) == 1  # history is preserved, invalid advice is not returned


def test_generated_advisory_drops_fake_duplicate_cross_branch_and_superseded_refs(tmp_path):
    f = GeneratedFixture(tmp_path)
    f.run("source"); f.run("review", source="source")
    assert f.feedback.accept("source-result").accepted
    branches = [Branch(branch_id="source-branch", status="exploring",
        supported_by=("source-result", "source-result", "invented"), refuted_by=("source-result",)),
        Branch(branch_id="foreign", status="exploring", supported_by=("source-result",))]
    advice = f.feedback.advisory(branches)["opportunities"]["opportunities"]
    assert advice[0]["supported_by"] == ["source-result"] and advice[0]["refuted_by"] == []
    assert advice[1]["supported_by"] == []
    f.feedback.record_supersession(SupersessionEvent(event_id="supersede", result_id="source-result",
        reason="additional evidence", source_ref="review", actor="independent-reviewer", at=f.ledger.now()))
    assert f.feedback.advisory(branches)["opportunities"]["opportunities"][0]["supported_by"] == []
    assert f.feedback.contributions()[0].contribution == "accepted"


def test_generated_readonly_rebuild_reuses_sources_without_reward_refresh(tmp_path):
    f = GeneratedFixture(tmp_path)
    f.run("source"); f.run("review", source="source")
    assert f.feedback.accept("source-result").accepted
    tracked = [f.ledger.path, f.assets.root / "assets.sqlite3", *(tmp_path / "archives").rglob("*.json")]
    before = {str(p): (p.read_bytes(), p.stat().st_mtime_ns) for p in tracked}
    readonly = ReadonlyLedger(f.ledger.path, f.ledger.swarm_id)
    for _ in range(2):
        facts = research_feedback(readonly, f.assets.root, generated_criteria=f.criteria,
                                  project_id=f.plan.project_id, archive_root=tmp_path / "archives")
        assert {r.task_id for r in facts} == {"source", "review"}
    rebuilt = ResearchFeedbackStore(tmp_path / "rebuilt.sqlite3", readonly, f.assets.root,
        reviewer="independent-reviewer", generated_criteria=f.criteria, project_id=f.plan.project_id)
    assert rebuilt.accept("source-result").accepted
    assert rebuilt.contributions() == f.feedback.contributions()
    assert before == {str(p): (p.read_bytes(), p.stat().st_mtime_ns) for p in tracked}


def test_generated_self_declared_final_trusted_cannot_replace_raw_evaluation(tmp_path):
    f = GeneratedFixture(tmp_path)
    f.run("source", output=b'{"candidate_self_score": 1}')
    f.run("review", source="source")
    report = f.reports["source"]
    envelope = json.loads(report.result_json)
    envelope["scientific_verdict"] = "passed"
    for key in ("generated_assessment",):
        envelope[key].update(hypothesis="supported", mode="final", trusted=True, contribution="accepted")
    envelope["experiment_result"]["assessment"].update(
        hypothesis="supported", mode="final", trusted=True, contribution="accepted")
    forged = report.model_copy(update={"scientific_verdict": "passed", "result_json": json.dumps(envelope)})
    # Even mutually consistent caller claims in report + audit + completion must
    # meet the independent archive reader's computation on original raw bytes.
    with f.assets.connection() as db:
        db.execute("DROP TRIGGER research_reports_UPDATE")
        db.execute("UPDATE research_reports SET body=? WHERE report_id=?",
                   (forged.model_dump_json(), report.report_id))
    with connection(f.ledger.path, write=True) as db:
        row = db.execute("SELECT sequence,body FROM task_audit WHERE task_id='source' AND event='research_execution'").fetchone()
        body = json.loads(row[1]); body["result"] = envelope
        db.execute("UPDATE task_audit SET body=? WHERE sequence=?", (json.dumps(body), row[0]))
        submitted = f.ledger.get("source").result.copy()
        submitted["scientific_verdict"] = "passed"
        db.execute("UPDATE tasks SET result=? WHERE task_id='source'", (json.dumps(submitted),))
    with pytest.raises(AssetSafetyError, match="generated_observation_result_mismatch"):
        f.feedback.accept("source-result")
    assert not f.feedback.contributions()


def test_generated_duplicate_raw_source_does_not_reward_a_new_identity(tmp_path):
    f = GeneratedFixture(tmp_path)
    f.run("source"); f.run("review", source="source")
    f.run("copy"); f.run("copy-review", source="copy")
    assert f.feedback.accept("source-result").accepted
    decision = f.feedback.accept("copy-result")
    assert not decision.accepted and decision.reasons == ("duplicate_contribution",)
    assert len(f.feedback.contributions()) == 1


def test_generated_approval_cannot_be_granted_retroactively_or_block_other_facts(tmp_path):
    f = GeneratedFixture(tmp_path)
    f.run("unapproved", frozen_criteria=False)
    f.run("source"); f.run("review", source="source")
    assert not f.feedback.accept("unapproved-result").accepted
    assert {fact.task_id for fact in f.feedback.trusted()} == {"source", "review"}
    assert f.feedback.accept("source-result").accepted


@pytest.mark.parametrize("limit", ["scope", "workspace", "reviewer_module", "origin_module"])
def test_generated_host_locality_filters_results_and_independent_review(tmp_path, limit):
    f = GeneratedFixture(tmp_path)
    f.run("source"); f.run("review", source="source")
    assert f.feedback.accept("source-result").accepted
    permitted = ResearchFeedbackStore(f.feedback.path, f.ledger, f.assets.root,
        reviewer="independent-reviewer", generated_criteria=f.criteria,
        project_id=f.plan.project_id, locality=f.locality)
    assert permitted.advisory([Branch(branch_id="source-branch", status="exploring")])[
        "branches"][0]["supported_by"] == ["source-result"]
    if limit == "scope":
        locality = f.locality.model_copy(update={"authorized_scopes": ("foreign",)})
    elif limit == "workspace":
        locality = f.locality.model_copy(update={"workspace": str(tmp_path / "foreign")})
    else:
        with connection(f.ledger.path, write=True) as db:
            db.execute("UPDATE tasks SET module='foreign' WHERE task_id=?",
                       ("review" if limit == "reviewer_module" else "source",))
        locality = f.locality.model_copy(update={"modules": ("",)})
    limited = ResearchFeedbackStore(tmp_path / "limited.sqlite3", f.ledger, f.assets.root,
        reviewer="independent-reviewer", generated_criteria=f.criteria,
        project_id=f.plan.project_id, locality=locality)
    assert not limited.accept("source-result").accepted
    if limit == "origin_module":
        assert limited.trusted() == []  # a local review cannot launder an excluded origin
    # Reopen the historical accepted store under this host's authority. Keeping
    # history cannot let a foreign fact or excluded reviewer influence advice.
    existing = ResearchFeedbackStore(f.feedback.path, f.ledger, f.assets.root,
        reviewer="independent-reviewer", generated_criteria=f.criteria,
        project_id=f.plan.project_id, locality=locality)
    advice = existing.advisory([Branch(branch_id="source-branch", status="exploring")])
    assert not advice["contributions"]
    assert advice["opportunities"]["opportunities"][0]["supported_by"] == []
    assert advice["branches"][0]["supported_by"] == []
