"""Admission, apply and consume entrypoints for generated candidates.

The generated candidate is admitted by ``generated_validation`` (static security
gates plus a *host-owned* isolation proof), then reused through the existing
asset chain: ``AssetApplicator`` (prepare/apply) and ``AssetConsumer``
(execute/record_adoption -> ``AdoptionReceipt``). Approval is fence-guarded and
bound to the original chain, never an arbitrary caller authority. No second
ledger, scheduler or completion-proof system is introduced.
"""

from __future__ import annotations

from collections.abc import Callable
import json
from pathlib import Path
import time
from typing import Literal
from uuid import uuid4

from contracts.identity import AttemptId
from local_assets.consume import AssetConsumer
from local_assets.generated_models import GeneratedApproval, GeneratedValidationReport
from local_assets.models import AssetSafetyError, Candidate, FileChange
from local_assets.paths import no_links
from local_assets.research_models import ResearchClaim, ResearchObservation
from local_assets.store import LocalAssetStore
from local_assets.validate import blast_radius, inspect_candidate
from orchestration.experiments.executor import digest
from orchestration.experiments.generated import GeneratedContext, GeneratedExperimentPlan, GeneratedResult, IsolationReport
from orchestration.experiments.generated_executor import read_generated_result
from orchestration.experiments.security import SecurityRejection, static_checks, verify_isolation
from orchestration.experiments.trusted import TrustedCriteriaRegistry, TrustedProbeRegistry, finalize_assessment


def generated_conditions(plan: GeneratedExperimentPlan) -> dict[str, str]:
    """Scientific condition identity, independent of task/run/asset publication IDs."""
    fields = plan.model_dump(mode="json")
    keys = ("schema_version", "files", "entrypoint", "data", "data_refs", "environment", "parameters",
            "seeds", "evaluation", "backend", "output_schema", "claim", "hypothesis")
    fields["evaluation"] = plan.evaluation.model_copy(update={"approved": False, "approved_by": None}).model_dump(mode="json")
    return {key: json.dumps(fields[key], sort_keys=True, separators=(",", ":")) for key in keys}


def _check_candidate(candidate: Candidate, asset_id: str, plan: GeneratedExperimentPlan,
                     files: dict[str, bytes]) -> None:
    inspect_candidate(candidate)
    if asset_id != plan.candidate_asset_id or candidate.base_revision != plan.candidate_revision:
        raise AssetSafetyError("generated_candidate_identity_mismatch")
    expected = {(name if candidate.scope == "." else candidate.scope + "/" + name): body
                for name, body in files.items()}
    actual = {change.path: change.after.encode("utf-8") if change.after is not None else None
              for change in candidate.changes}
    if actual != expected or len(actual) != len(candidate.changes):
        raise AssetSafetyError("generated_candidate_bytes_mismatch")
    if candidate.research != ResearchClaim(plan_id=plan.plan_id, criterion_version=plan.evaluation.version,
            conditions=generated_conditions(plan), sources=tuple(source.ref for source in plan.sources)):
        raise AssetSafetyError("generated_candidate_conditions_mismatch")


def _bound_candidate(store: LocalAssetStore, asset_id: str, plan: GeneratedExperimentPlan,
                     files: dict[str, bytes]) -> Candidate:
    candidate = store.fetch(asset_id)
    _check_candidate(candidate, asset_id, plan, files)
    return candidate


def _verify_manifest(plan: GeneratedExperimentPlan, files: dict[str, bytes]) -> None:
    manifest = {file.name: file for file in plan.files}
    for name, body in files.items():
        entry = manifest.get(name)
        if entry is None or digest(body) != entry.sha256 or len(body) != entry.size_bytes:
            raise ValueError("manifest_digest_mismatch")
    if set(files) != set(manifest):
        raise ValueError("manifest_count_mismatch")


def generated_validation(store: LocalAssetStore, asset_id: str, plan: GeneratedExperimentPlan,
                         files: dict[str, bytes], isolation: IsolationReport, *,
                         probe_registry: TrustedProbeRegistry | None = None,
                         data: dict[str, bytes] | None = None,
                         report_ttl_seconds: float = 300) -> GeneratedValidationReport:
    """Admission gate: static security plus host-verified isolation; never byte-equality."""
    plan = GeneratedExperimentPlan.model_validate(plan.model_dump(mode="json"))
    _verify_manifest(plan, files)
    _bound_candidate(store, asset_id, plan, files)
    data = data or {}
    entries = {entry.name: entry for entry in plan.data}
    if set(data) != set(entries) or any(digest(body) != entries[name].sha256
            or len(body) != entries[name].size_bytes for name, body in data.items()):
        raise AssetSafetyError("data_manifest_digest_mismatch")
    static = static_checks(plan, files, data)
    reasons = list(static.reasons)
    if not static.passed:
        reasons.append("static_security_failed")
    try:
        verify_isolation(isolation, probe_registry, plan)
    except SecurityRejection as error:
        reasons.append(str(error))
    now = time.time()
    report = GeneratedValidationReport(
        report_id=uuid4().hex, asset_id=asset_id, plan_json=plan.model_dump_json(),
        passed=not reasons, reasons=tuple(reasons), static=static, isolation=isolation,
        created_at=now, expires_at=now + report_ttl_seconds)
    store._record_generated_report(report)
    return report


def approve_generated(store: LocalAssetStore, report: GeneratedValidationReport,
                      assert_owned: Callable[[], None] | None = None, *,
                      proof_ref: str | None = None) -> None:
    """Fence-guarded approval; downstream reuse requires the original approval authority."""
    store.approve_generated(report, assert_owned, proof_ref=proof_ref)


def checked_generated_report(store: LocalAssetStore, asset_id: str,
        report_id: str | GeneratedValidationReport, policy_version: str) -> tuple[Candidate, GeneratedValidationReport]:
    submitted = report_id if isinstance(report_id, GeneratedValidationReport) else None
    report = store.generated_report(submitted.report_id if submitted else str(report_id))
    if submitted is not None and submitted != report:
        raise AssetSafetyError("tampered_generated_report")
    if report.asset_id != asset_id or report.policy_version != policy_version:
        raise AssetSafetyError("generated_report_candidate_mismatch")
    if not report.passed or report.reasons:
        raise AssetSafetyError("generated_report_not_passed")
    if not report.created_at <= time.time() < report.expires_at:
        raise AssetSafetyError("stale_report")
    plan = GeneratedExperimentPlan.model_validate_json(report.plan_json)
    candidate = store.fetch(asset_id)
    prefix = "" if candidate.scope == "." else candidate.scope + "/"
    files = {change.path.removeprefix(prefix): change.after.encode("utf-8")
             for change in candidate.changes if change.after is not None}
    _verify_manifest(plan, files)
    _check_candidate(candidate, asset_id, plan, files)
    return candidate, report


def generated_result_payload(result: GeneratedResult, *,
                             criteria_registry: TrustedCriteriaRegistry | None) -> dict[str, object]:
    """Host projection for the existing research_execution audit/result envelope.

    Call only with a result freshly returned by the trusted archive reader.
    Approval recorded after execution began cannot retroactively finalize it.
    """
    approval = criteria_registry.approval(result.plan.evaluation) if criteria_registry else None
    if (approval is None or result.started_at is None or approval.approved_at > result.started_at
            or approval.approved_by == result.context.author
            or approval.model_dump_json() != result.criteria_approval_json):
        approval = None
    assessment = finalize_assessment(result.assessment, spec=result.plan.evaluation,
        registry=criteria_registry if approval else None,
        execution_state=result.execution_state, remote_effect=result.remote_effect)
    verdict = "not_evaluated"
    if assessment.trusted and assessment.mode == "final":
        verdict = {"supported": "passed", "refuted": "failed"}.get(assessment.hypothesis, "not_evaluated")
    return {"schema_version": "generated-experiment/v1", "effect_state": result.remote_effect,
            "execution_state": result.execution_state, "scientific_verdict": verdict,
            "provenance": result.provenance, "sandbox_id": result.sandbox_id,
            "experiment_result": result.model_dump(mode="json"),
            "generated_assessment": assessment.model_dump(mode="json"),
            "criteria_approval": approval.model_dump(mode="json") if approval else None,
            "usage": None, "cost_usd": None}


def record_generated_observation(store: LocalAssetStore, asset_id: str, *, archive_root: Path | str,
        plan: GeneratedExperimentPlan, context: GeneratedContext,
        purpose: Literal["original", "reproduction", "inheritance", "counterexample"],
        criteria_registry: TrustedCriteriaRegistry | None, assert_owned: Callable[[], None],
        source_swarm_id: str, source_attempt: AttemptId, source_fencing_token: int) -> ResearchObservation:
    """Append a host-read scientific observation to the original asset report table.

    The service corroborates this record with its original TaskLedger execution,
    audit and completion facts. This function neither completes a task nor grants
    contribution/adoption, and never consumes static approval as scientific proof.
    """
    assert_owned()
    result = read_generated_result(archive_root, context.run_id, expected_plan=plan, expected_context=context)
    if store.research_provenance == "mock" and result.provenance != "mock":
        raise AssetSafetyError("mock_fixture_cannot_import_live_result")
    candidate = store.fetch(asset_id)
    files = {entry.name: (Path(result.archive_path) / "inputs" / entry.name).read_bytes() for entry in plan.files}
    _verify_manifest(plan, files)
    _bound_candidate(store, asset_id, plan, files)
    if (plan.task_id != context.task_id or source_attempt.task_id != context.task_id
            or source_fencing_token != context.fencing_token
            or (purpose == "original" and source_attempt != candidate.attempt)
            or (purpose == "original" and context.task_id != candidate.attempt.task_id)
            or (purpose != "original" and context.task_id == candidate.attempt.task_id)):
        raise AssetSafetyError("generated_observation_lineage_mismatch")
    payload = generated_result_payload(result, criteria_registry=criteria_registry)
    report = ResearchObservation.model_validate(dict(
        report_id=uuid4().hex, asset_id=asset_id, task_id=context.task_id, worker_id=context.worker_id,
        fencing_token=context.fencing_token, run_id=context.run_id, sandbox_id=result.sandbox_id,
        plan_id=plan.plan_id, criterion_version=plan.evaluation.version, conditions=generated_conditions(plan),
        plan_json=plan.model_dump_json(), candidate_json=candidate.model_dump_json(),
        result_json=json.dumps(payload, sort_keys=True, separators=(",", ":")), provenance=result.provenance,
        purpose=purpose, execution_state=result.execution_state, scientific_verdict=payload["scientific_verdict"],
        reasons=result.reasons, created_at=time.time(), source_swarm_id=source_swarm_id,
        source_attempt=source_attempt, source_fencing_token=source_fencing_token))
    with store.connection() as db:
        db.execute("BEGIN IMMEDIATE")
        assert_owned()
        rows = db.execute("SELECT body FROM research_reports WHERE asset_id=? "
            "AND json_extract(body,'$.run_id')=? AND json_extract(body,'$.purpose')=?",
            (asset_id, context.run_id, purpose)).fetchall()
        if rows:
            existing = ResearchObservation.model_validate_json(rows[0][0])
            if len(rows) != 1 or existing.model_copy(update={"report_id": report.report_id,
                    "created_at": report.created_at}) != report:
                raise AssetSafetyError("generated_observation_conflict")
            assert_owned()
            return existing
        db.execute("INSERT INTO research_reports VALUES (?,?,?)", (report.report_id, asset_id, report.model_dump_json()))
        assert_owned()
    return report


def read_generated_observation(report: ResearchObservation, *,
                               criteria_registry: TrustedCriteriaRegistry) -> GeneratedResult:
    """Pure verification of an original persisted observation and its raw archive."""
    payload = json.loads(report.result_json)
    saved = GeneratedResult.model_validate(payload["experiment_result"])
    no_links(Path(saved.archive_path))
    plan = GeneratedExperimentPlan.model_validate_json(report.plan_json)
    context = saved.context
    if (report.run_id != context.run_id or report.task_id != context.task_id
            or plan.task_id != context.task_id or report.worker_id != context.worker_id
            or report.fencing_token != context.fencing_token or report.sandbox_id != saved.sandbox_id
            or report.provenance != saved.provenance or report.execution_state != saved.execution_state
            or report.plan_id != plan.plan_id or report.criterion_version != plan.evaluation.version
            or report.conditions != generated_conditions(plan)):
        raise AssetSafetyError("generated_observation_binding_mismatch")
    result = read_generated_result(Path(saved.archive_path).parent, context.run_id,
                                   expected_plan=plan, expected_context=context)
    candidate = Candidate.model_validate_json(report.candidate_json)
    files = {entry.name: (Path(result.archive_path) / "inputs" / entry.name).read_bytes() for entry in plan.files}
    _check_candidate(candidate, report.asset_id, plan, files)
    if (report.source_attempt is None or report.source_attempt.task_id != context.task_id
            or not report.source_swarm_id or report.source_fencing_token != context.fencing_token
            or (report.purpose == "original" and report.source_attempt != candidate.attempt)
            or (report.purpose != "original" and context.task_id == candidate.attempt.task_id)):
        raise AssetSafetyError("generated_observation_lineage_mismatch")
    recomputed = generated_result_payload(result, criteria_registry=criteria_registry)
    if payload != recomputed or report.scientific_verdict != recomputed["scientific_verdict"]:
        raise AssetSafetyError("generated_observation_result_mismatch")
    return result


def generated_candidate(plan: GeneratedExperimentPlan, files: dict[str, bytes], *, attempt: AttemptId,
                        scope: str, summary: str) -> Candidate:
    """Build a literal Candidate payload from generated code files for the asset chain.

    Only the addressed files supply ``after`` bytes; there is no eval, import or
    template interpolation. The candidate stays quarantined until approved.
    """
    changes = tuple(
        FileChange(path=(f"{scope}/{name}" if scope != "." else name), before=None,
                   after=body.decode("utf-8"))
        for name, body in sorted(files.items())
    )
    candidate = Candidate(
        attempt=attempt, base_revision=plan.candidate_revision, base_head=None,
        scope=scope, changes=changes, declared_files=len(changes), declared_lines=0,
        summary=summary, required_capabilities=(), dependencies=(),
        research=ResearchClaim(plan_id=plan.plan_id, criterion_version=plan.evaluation.version,
            conditions=generated_conditions(plan), sources=tuple(source.ref for source in plan.sources)))
    count, lines = blast_radius(candidate)
    return candidate.model_copy(update={"declared_files": count, "declared_lines": lines})


__all__ = ["GeneratedValidationReport", "GeneratedApproval", "AssetConsumer", "approve_generated",
           "generated_candidate", "generated_validation", "generated_conditions", "generated_result_payload",
           "record_generated_observation", "read_generated_observation"]
