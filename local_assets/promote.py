"""Promotion under the runtime's scope lease; original candidate bytes only."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
import time

from local_assets.models import AssetSafetyError, LeaseGuard, PromotionReceipt, ValidationReport
from local_assets.paths import check_target, git, safe_join
from local_assets.store import LocalAssetStore
from local_assets.snapshot import check_snapshot
from local_assets.validate import fingerprint, inspect_candidate


class AssetPromoter:
    def __init__(self, store: LocalAssetStore, target: Path | str, *,
                 protected_paths: tuple[Path, ...] = ()) -> None:
        self.store = store
        self.target = Path(target).absolute()
        self.protected_paths = protected_paths

    def promote(self, asset_id: str, report_id: str | ValidationReport,
                lease_guard: LeaseGuard) -> PromotionReceipt:
        # Accepting a model is convenient, but it must equal persisted evidence.
        submitted = report_id if isinstance(report_id, ValidationReport) else None
        report = self.store.get_report(submitted.report_id if submitted else str(report_id))
        if submitted is not None and submitted != report:
            raise AssetSafetyError("tampered_report")
        candidate = self.store.fetch(asset_id)
        actual = inspect_candidate(candidate)
        if (report.asset_id != asset_id or report.candidate_json != candidate.model_dump_json()
                or report.attempt != candidate.attempt or report.base_revision != candidate.base_revision
                or (report.actual_files, report.actual_lines) != actual):
            raise AssetSafetyError("report_candidate_mismatch")
        if (not report.passed or report.reasons or not report.commands
                or any(r.exit_code != 0 or r.timed_out or r.output_limited for r in report.commands)):
            raise AssetSafetyError("report_not_passed")
        if not report.created_at <= time.time() < report.expires_at:
            raise AssetSafetyError("stale_report")
        with tempfile.TemporaryDirectory(prefix="swarm-promote-env-") as directory:
            if fingerprint(Path(directory)) != report.env_fingerprint:
                raise AssetSafetyError("environment_changed")
        target = check_target(self.target, self.protected_paths)
        scope = target if candidate.scope == "." else safe_join(target, candidate.scope)
        with lease_guard(str(scope)) as assert_owned:
            assert_owned()
            # Both lease state and consumed report are fenced while bytes change.
            with self.store.connection() as db:
                db.execute("BEGIN IMMEDIATE")
                if db.execute("SELECT 1 FROM promotions WHERE report_id=?", (report.report_id,)).fetchone():
                    raise AssetSafetyError("report_already_promoted")
                check_target(target, self.protected_paths)
                if git(target, "rev-parse", "HEAD").decode().strip() != (candidate.base_head or candidate.base_revision):
                    raise AssetSafetyError("target_revision_changed")
                check_snapshot(target, candidate, self.store.root / "snapshots")
                paths: list[tuple[Path, bytes | None, bytes | None]] = []
                for change in candidate.changes:
                    path = safe_join(target, change.path)
                    before = path.read_bytes() if path.is_file() else None
                    expected = change.before.encode("utf-8") if change.before is not None else None
                    if path.is_dir() or before != expected:
                        raise AssetSafetyError("target_preimage_mismatch")
                    after = change.after.encode("utf-8") if change.after is not None else None
                    paths.append((path, before, after))
                written: list[tuple[Path, bytes | None]] = []
                try:
                    for path, before, after in paths:
                        assert_owned()
                        if time.time() >= report.expires_at:
                            raise AssetSafetyError("stale_report")
                        # Recheck immediately before replacement, under lease.
                        safe_join(target, path.relative_to(target).as_posix())
                        if (path.read_bytes() if path.is_file() else None) != before:
                            raise AssetSafetyError("target_preimage_changed_during_promotion")
                        self._replace(path, after)
                        written.append((path, before))
                    assert_owned()
                    if time.time() >= report.expires_at:
                        raise AssetSafetyError("stale_report")
                    receipt = PromotionReceipt(
                        asset_id=asset_id, report_id=report.report_id, target=str(target),
                        paths=tuple(c.path for c in candidate.changes), promoted_at=time.time(),
                    )
                    db.execute("INSERT INTO promotions VALUES (?, ?, ?)",
                               (report.report_id, asset_id, receipt.model_dump_json()))
                    db.commit()
                except BaseException:
                    # The lease's atomic guard still excludes successor holders.
                    for path, before in reversed(written):
                        self._replace(path, before)
                    raise
        return receipt

    @staticmethod
    def _replace(path: Path, content: bytes | None) -> None:
        if content is None:
            path.unlink(missing_ok=True)
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(prefix=".swarm-", dir=path.parent)
        temporary = Path(temporary_name)
        try:
            with os.fdopen(fd, "wb") as output:
                output.write(content)
                output.flush()
                os.fsync(output.fileno())
            if path.exists():
                os.chmod(temporary, path.stat().st_mode)
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
