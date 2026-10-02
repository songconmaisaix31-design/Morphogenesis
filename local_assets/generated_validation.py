"""Admission, apply and consume entrypoints for generated candidates.

The generated candidate is admitted by ``generated_validation`` (static security
gates plus a *verified* isolation report), then reused through the existing
asset chain: ``AssetApplicator`` (prepare/apply) and ``AssetConsumer``
(execute/record_adoption -> ``AdoptionReceipt``). No second ledger, scheduler or
completion-proof system is introduced.
"""

from __future__ import annotations

import time
from uuid import uuid4

from local_assets.consume import AssetConsumer
from local_assets.generated_models import GeneratedValidationReport
from local_assets.models import Candidate, FileChange
from local_assets.store import LocalAssetStore
from local_assets.validate import blast_radius
from orchestration.experiments.generated import GeneratedExperimentPlan, IsolationReport
from orchestration.experiments.security import static_checks
from contracts.identity import AttemptId


def generated_validation(store: LocalAssetStore, asset_id: str, plan: GeneratedExperimentPlan,
                         files: dict[str, bytes], isolation: IsolationReport, *,
                         report_ttl_seconds: float = 300) -> GeneratedValidationReport:
    """Admission gate: static security plus verified isolation; never byte-equality."""
    plan = GeneratedExperimentPlan.model_validate(plan.model_dump(mode="json"))
    static = static_checks(plan, files)
    reasons = list(static.reasons)
    if not static.passed:
        reasons.append("static_security_failed")
    if not isolation.admitted:
        reasons.append("isolation_capability_unverified")
    now = time.time()
    report = GeneratedValidationReport(
        report_id=uuid4().hex, asset_id=asset_id, plan_json=plan.model_dump_json(),
        passed=not reasons, reasons=tuple(reasons), static=static, isolation=isolation,
        created_at=now, expires_at=now + report_ttl_seconds)
    store._record_generated_report(report)
    return report


def approve_generated(store: LocalAssetStore, report: GeneratedValidationReport) -> None:
    """Mark a passing generated admission durable; downstream reuse requires this."""
    store.approve_generated(report)


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


__all__ = ["GeneratedValidationReport", "AssetConsumer", "approve_generated", "generated_candidate",
           "generated_validation"]
