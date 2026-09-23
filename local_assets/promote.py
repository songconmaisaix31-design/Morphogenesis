"""Report-bound approval changes only the local asset index, never target files."""

from __future__ import annotations

import tempfile
from pathlib import Path
import time

from local_assets.models import AssetSafetyError, Candidate, PromotionReceipt, ValidationPolicy, ValidationReport
from local_assets.store import LocalAssetStore
from local_assets.validate import fingerprint, inspect_candidate


def checked_report(store: LocalAssetStore, asset_id: str, report_id: str | ValidationReport,
                   policy_version: str) -> tuple[Candidate, ValidationReport]:
    submitted = report_id if isinstance(report_id, ValidationReport) else None
    report = store.get_report(submitted.report_id if submitted else str(report_id))
    if submitted is not None and submitted != report:
        raise AssetSafetyError("tampered_report")
    candidate = store.fetch(asset_id)
    actual = inspect_candidate(candidate)
    if (report.asset_id != asset_id or report.candidate_json != candidate.model_dump_json()
            or report.attempt != candidate.attempt or report.base_revision != candidate.base_revision
            or (report.actual_files, report.actual_lines) != actual):
        raise AssetSafetyError("report_candidate_mismatch")
    if report.policy_version != policy_version or not report.policy_json:
        raise AssetSafetyError("validation_policy_mismatch")
    policy = ValidationPolicy.model_validate_json(report.policy_json)
    if policy.version != policy_version:
        raise AssetSafetyError("validation_policy_mismatch")
    if report.isolation != "non_arbitrary_literal_files":
        raise AssetSafetyError("unsafe_legacy_validation")
    if (not report.passed or report.reasons or len(report.commands) != 1
            or report.commands[0].argv != (policy.executor, policy.version)
            or any(r.exit_code != 0 or r.timed_out or r.output_limited for r in report.commands)):
        raise AssetSafetyError("report_not_passed")
    if not report.created_at <= time.time() < report.expires_at:
        raise AssetSafetyError("stale_report")
    with tempfile.TemporaryDirectory(prefix="swarm-approve-env-") as directory:
        if fingerprint(Path(directory)) != report.env_fingerprint:
            raise AssetSafetyError("environment_changed")
    return candidate, report


class AssetPromoter:
    def __init__(self, store: LocalAssetStore, *, policy_version: str) -> None:
        self.store = store
        self.policy_version = policy_version

    def promote(self, asset_id: str, report_id: str | ValidationReport) -> PromotionReceipt:
        _, report = checked_report(self.store, asset_id, report_id, self.policy_version)
        with self.store.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT body FROM approvals WHERE asset_id=?", (asset_id,)).fetchone()
            if row:
                receipt = PromotionReceipt.model_validate_json(row[0])
                if receipt.report_id != report.report_id:
                    raise AssetSafetyError("asset_already_approved")
                return receipt
            receipt = PromotionReceipt(asset_id=asset_id, report_id=report.report_id,
                                       promoted_at=time.time(), policy_version=report.policy_version)
            db.execute("INSERT INTO approvals VALUES (?, ?, ?)",
                       (asset_id, report.report_id, receipt.model_dump_json()))
        return receipt
