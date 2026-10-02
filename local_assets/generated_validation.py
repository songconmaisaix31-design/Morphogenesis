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
import time
from uuid import uuid4

from contracts.identity import AttemptId
from local_assets.consume import AssetConsumer
from local_assets.generated_models import GeneratedApproval, GeneratedValidationReport
from local_assets.models import Candidate, FileChange
from local_assets.store import LocalAssetStore
from local_assets.validate import blast_radius
from orchestration.experiments.executor import digest
from orchestration.experiments.generated import GeneratedExperimentPlan, IsolationReport
from orchestration.experiments.security import SecurityRejection, static_checks, verify_isolation
from orchestration.experiments.trusted import TrustedProbeRegistry


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
                         report_ttl_seconds: float = 300) -> GeneratedValidationReport:
    """Admission gate: static security plus host-verified isolation; never byte-equality."""
    plan = GeneratedExperimentPlan.model_validate(plan.model_dump(mode="json"))
    _verify_manifest(plan, files)
    static = static_checks(plan, files)
    reasons = list(static.reasons)
    if not static.passed:
        reasons.append("static_security_failed")
    try:
        verify_isolation(isolation, probe_registry)
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
        summary=summary, required_capabilities=(), dependencies=plan.environment.dependencies)
    count, lines = blast_radius(candidate)
    return candidate.model_copy(update={"declared_files": count, "declared_lines": lines})


__all__ = ["GeneratedValidationReport", "GeneratedApproval", "AssetConsumer", "approve_generated",
           "generated_candidate", "generated_validation"]
