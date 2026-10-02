"""Generated three axes from original ledger/report/archive joins, never execution.

All candidate bytes are inert. Q creates deterministic mock output artifacts and
uses B's real observation writer/reader plus C's real persisted projection.
"""
import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from contracts.identity import AgentId, AttemptId
from local_assets import generated_validation as reporting
from orchestration.experiments.generated import GeneratedContext, GeneratedResult
from orchestration.experiments.generated_executor import read_generated_result
from orchestration.experiments.models import ExperimentArtifact
from orchestration.experiments.trusted import TrustedCriteriaRecord, TrustedCriteriaRegistry
from swarm.models import Locality, Signal
from swarm.research.feedback import ResearchFeedbackStore
from swarm.research.policy import Branch
from swarm.task_ledger import TaskLedger
from tests.integration.r1_security.test_b_generated_boundaries import CODE, isolation, plan, raw_output
from tests.integration.r1_security.test_b_successor_authority import candidate_store
from tests.integration.r1_security.test_c_advisory_binding import opportunity


def persisted_chain(root, monkeypatch, *, hypothesis="supported", review_state="succeeded",
                    review_effect="known", review_actor="reviewer", reuse_sandbox=False,
                    include_review=True, approval_at=90, review_workspace=None):
    monkeypatch.setattr(reporting.time, "time", lambda: 100.0)
    p = plan()
    assets = candidate_store(root, p=p)
    ledger = TaskLedger(root / "ledger.db", "q-generated", clock=lambda: 100.0)
    locality = Locality(workspace=str(root / "workspace"), authorized_scopes=("science",))
    criterion = TrustedCriteriaRecord(spec=p.evaluation, approved_by="criteria-reviewer", approved_at=approval_at)
    registry = TrustedCriteriaRegistry(records=(criterion,))
    archive_root = root / "evidence"
    reports = []

    def append(task_id, actor, *, state="succeeded", effect="known", purpose="original"):
        frozen = p.model_copy(update={"task_id": task_id})
        execution_locality = locality if purpose == "original" or review_workspace is None else Locality(
            workspace=str(review_workspace), authorized_scopes=("science",))
        ledger.enqueue(Signal(task_id=task_id, workspace=execution_locality.workspace, scope="science",
            kind="opportunity", required_capability="research",
            payload={"project_id": p.project_id, "branch_id": p.branch_id}),
            acceptance={"generated_plan": frozen.model_dump(mode="json")})
        lease = ledger.claim(task_id, actor, locality=execution_locality)
        assert lease is not None
        run_id = "run-" + task_id
        ledger.begin_execution(lease, run_id)
        ctx = GeneratedContext(run_id=run_id, task_id=task_id, worker_id=actor, fencing_token=lease.token,
                               author="author", reviewer=criterion.approved_by)
        directory = archive_root / run_id
        (directory / "inputs").mkdir(parents=True)
        (directory / "outputs").mkdir()
        raw = raw_output()
        if hypothesis == "refuted":
            payload = json.loads(raw)
            payload["u"] = [0.0] * len(payload["x"])
            raw = json.dumps(payload).encode()
        bodies = {"inputs/candidate.py": CODE, "outputs/output.json": raw}
        artifacts = []
        for name, body in bodies.items():
            (directory / name).write_bytes(body)
            artifacts.append(ExperimentArtifact(name=name, archive_path=name,
                sha256=hashlib.sha256(body).hexdigest(), size_bytes=len(body)))
        result = GeneratedResult(plan=frozen, context=ctx, archive_path=str(directory), provenance="mock",
            isolation=isolation(), execution_state=state, remote_effect=effect, cleanup_state="destroyed",
            sandbox_id="fixture-sandbox-t1" if reuse_sandbox else "fixture-sandbox-" + task_id,
            exit_code=0 if state == "succeeded" else 1, artifacts=tuple(artifacts),
            started_at=100, criteria_approval_json=criterion.model_dump_json())
        (directory / "plan.json").write_text(frozen.model_dump_json(), encoding="utf-8")
        (directory / "result.json").write_text(result.model_dump_json(), encoding="utf-8")
        verified = read_generated_result(archive_root, run_id, expected_plan=frozen, expected_context=ctx)
        envelope = reporting.generated_result_payload(verified, criteria_registry=registry)
        ledger.record_event("research_execution", {"run_id": run_id, "worker_id": actor,
                            "token": lease.token, "result": envelope}, task_id=task_id)
        # These are explicitly constructed contract_local facts, not claims of
        # remote success. The effect field remains unknown in negative fixtures.
        ledger.confirm_execution(lease, run_id)
        attempt = AttemptId(task_id=task_id, agent=AgentId(role="builder", instance=0)
            if purpose == "original" else AgentId(role="reviewer", instance=1), attempt=1)

        def assert_owned():
            assert ledger.is_valid(lease), "lost fixture lease"

        report = reporting.record_generated_observation(assets, "candidate", archive_root=archive_root,
            plan=frozen, context=ctx, purpose=purpose, criteria_registry=registry,
            assert_owned=assert_owned,
            source_swarm_id=ledger.swarm_id, source_attempt=attempt, source_fencing_token=lease.token)
        ledger.submit(lease, "result-" + task_id, {"stage": "evidence_submitted", "asset_id": "candidate",
            "report_id": report.report_id, "run_id": run_id, "execution_state": report.execution_state,
            "scientific_verdict": report.scientific_verdict, "provenance": "mock"})
        reports.append(report)

    append("t1", "author")
    if include_review:
        append("review", review_actor, state=review_state, effect=review_effect, purpose="reproduction")
    feedback = ResearchFeedbackStore(root / "feedback.db", ledger, assets.root, reviewer="reviewer",
        clock=lambda: 100.0, generated_criteria=registry, project_id=p.project_id, archive_root=archive_root)
    return feedback, reports, assets, registry


@pytest.mark.parametrize("hypothesis", ["supported", "refuted"])
def test_generated_original_and_distinct_review_drive_persisted_contribution_and_advice(
        tmp_path, monkeypatch, hypothesis):
    s, reports, assets, registry = persisted_chain(tmp_path, monkeypatch, hypothesis=hypothesis)
    facts = s.trusted()
    assert {fact.task_id for fact in facts} == {"t1", "review"}
    assert {fact.hypothesis for fact in facts} == {hypothesis}
    assert s.accept("result-t1").accepted
    assert not s.accept("result-t1").accepted
    original = s.contributions()
    assert len(original) == 1 and original[0].contribution == "accepted"
    axis = "supported_by" if hypothesis == "supported" else "refuted_by"
    advice = s.advisory([Branch(branch_id="b1", status="exploring", **{axis: ("result-t1",)}),
                         Branch(branch_id="other", status="exploring")])
    row = opportunity(advice, "b1")
    assert row[axis] == ["result-t1"]
    if hypothesis == "refuted":
        assert 0 < row["share"] < opportunity(advice, "other")["share"]
    reopened = ResearchFeedbackStore(s.path, s.ledger, assets.root, reviewer="reviewer",
        clock=lambda: 100.0, generated_criteria=registry, project_id="p1", archive_root=tmp_path / "evidence")
    assert reopened.contributions() == original
    assert len(reopened.trusted()) == 2


@pytest.mark.parametrize("attack", ["crashed_review", "unknown_review", "unknown_effect", "same_actor",
                                    "same_sandbox", "missing_review", "late_criteria"])
def test_generated_review_requires_real_independent_known_execution_lineage(tmp_path, monkeypatch, attack):
    changes = {
        "crashed_review": {"review_state": "failed"},
        "unknown_review": {"review_state": "unknown", "review_effect": "unknown"},
        "unknown_effect": {"review_effect": "unknown"},
        "same_actor": {"review_actor": "author"},
        "same_sandbox": {"reuse_sandbox": True},
        "missing_review": {"include_review": False},
        "late_criteria": {"approval_at": 101},
    }[attack]
    s, reports, assets, registry = persisted_chain(tmp_path, monkeypatch, **changes)
    try:
        decision = s.accept("result-t1")
    except (ValueError, PermissionError):
        pass
    else:
        assert not decision.accepted, "invalid independent generated review granted a contribution"
    assert s.contributions() == []


@pytest.mark.parametrize("boundary", ["same_host", "foreign_scope", "foreign_workspace", "foreign_review"])
def test_generated_trust_and_historical_credit_remain_within_original_host_locality(tmp_path, monkeypatch, boundary):
    s, reports, assets, registry = persisted_chain(tmp_path, monkeypatch,
        review_workspace=tmp_path / "other-workspace" if boundary == "foreign_review" else None)
    if boundary != "foreign_review":
        assert s.accept("result-t1").accepted, "nonempty trusted contribution control required"
    host = Locality(workspace=str(tmp_path / ("other-workspace" if boundary == "foreign_workspace" else "workspace")),
        authorized_scopes=("private",) if boundary == "foreign_scope" else ("science",))
    scoped = ResearchFeedbackStore(s.path, s.ledger, assets.root, reviewer="reviewer", clock=lambda: 100.0,
        generated_criteria=registry, project_id="p1", archive_root=tmp_path / "evidence", locality=host)
    if boundary == "same_host":
        assert len(scoped.trusted()) == 2 and len(scoped.contributions()) == 1
    else:
        assert scoped.contributions() == [], "host-excluded historical credit leaked into current projection"
        if boundary == "foreign_review":
            try:
                decision = scoped.accept("result-t1")
            except (ValueError, PermissionError):
                pass
            else:
                assert not decision.accepted, "a review in another workspace granted contribution"
        else:
            assert scoped.trusted() == []


@pytest.mark.parametrize("changed", ["raw_output", "frozen_evaluation", "report_reviewer"])
def test_generated_persisted_claims_cannot_replace_original_archive_or_host_approval(tmp_path, monkeypatch, changed):
    s, reports, assets, registry = persisted_chain(tmp_path, monkeypatch)
    assert len(s.trusted()) == 2, "positive trust chain must exist before substitution"
    report = reports[0]
    directory = Path(json.loads(report.result_json)["experiment_result"]["archive_path"])
    if changed == "raw_output":
        (directory / "outputs/output.json").write_bytes(b'{"score": 1, "approved": true}')
    elif changed == "frozen_evaluation":
        frozen = json.loads((directory / "plan.json").read_text(encoding="utf-8"))
        frozen["evaluation"]["max_abs_tolerance"] = 1.0
        (directory / "plan.json").write_text(json.dumps(frozen), encoding="utf-8")
    else:
        body = json.loads(report.result_json)
        body["experiment_result"]["context"]["reviewer"] = "caller-invented-reviewer"
        forged = report.model_copy(update={"result_json": json.dumps(body)})
        with assets.connection() as db:
            with pytest.raises(sqlite3.IntegrityError, match="immutable_local_evidence"):
                db.execute("UPDATE research_reports SET body=? WHERE report_id=?",
                           (forged.model_dump_json(), report.report_id))
            original = db.execute("SELECT body FROM research_reports WHERE report_id=?",
                                  (report.report_id,)).fetchone()[0]
        assert original == report.model_dump_json()
        assert len(s.trusted()) == 2
        assert s.contributions() == []
        return
    try:
        decision = s.accept("result-t1")
    except (ValueError, PermissionError):
        pass
    else:
        assert not decision.accepted, "modified persisted metadata was treated as original trusted science"
    assert s.contributions() == []
