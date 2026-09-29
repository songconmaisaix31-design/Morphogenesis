"""Explicit target publication, invoked only inside the task ledger submit fence."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import os
from pathlib import Path
import tempfile
import time

from local_assets.models import ApplicationReceipt, AssetSafetyError, Candidate, ValidationReport
from local_assets.paths import check_target, git, no_links, safe_join
from local_assets.promote import checked_report
from local_assets.snapshot import check_snapshot, scope_tree
from local_assets.store import LocalAssetStore


def _scope_bytes(target: Path, scope: str) -> dict[Path, bytes]:
    root = target if scope == "." else safe_join(target, scope)
    paths = root.rglob("*") if root.is_dir() else iter((root,))
    result: dict[Path, bytes] = {}
    size = 0
    for path in paths:
        if ".git" in path.relative_to(target).parts:
            continue
        no_links(path)
        if path.is_file():
            size += path.stat().st_size
            if len(result) >= 2000 or size > 16 * 1024 * 1024:
                raise AssetSafetyError("application_scope_limit")
            result[path] = path.read_bytes()
    return result


def _read(path: Path) -> bytes | None:
    no_links(path)
    if path.is_dir():
        raise AssetSafetyError("target_file_is_directory")
    return path.read_bytes() if path.is_file() else None


@dataclass(frozen=True)
class PreparedApplication:
    """Preparation is not authorization; apply needs B's live submit callback.

    Caller checks lease.scope covers scope. The callback is the exact assert_owned
    yielded by TaskLedger.submit, whose durable submitting intent blocks takeover
    after a crash. No Git, SDK, tests or separate ledger transactions occur here.
    """

    target: Path
    candidate: Candidate
    report: ValidationReport
    baseline_files: dict[Path, bytes]
    git_metadata: dict[Path, bytes | None]

    @property
    def scope(self) -> str:
        return str(self.target if self.candidate.scope == "." else self.target / self.candidate.scope)

    def apply(self, assert_owned: Callable[[], None]) -> ApplicationReceipt:
        assert_owned()
        no_links(self.target)
        if any(_read(path) != body for path, body in self.git_metadata.items()):
            raise AssetSafetyError("target_revision_changed")
        if _scope_bytes(self.target, self.candidate.scope) != self.baseline_files:
            raise AssetSafetyError("target_changed_after_preparation")
        written: list[tuple[Path, bytes | None]] = []
        try:
            for change in self.candidate.changes:
                assert_owned()
                if time.time() >= self.report.expires_at:
                    raise AssetSafetyError("stale_report")
                path = safe_join(self.target, change.path)
                before = change.before.encode("utf-8") if change.before is not None else None
                if _read(path) != before:
                    raise AssetSafetyError("target_preimage_changed_during_application")
                after = change.after.encode("utf-8") if change.after is not None else None
                self._replace(path, after)
                written.append((path, before))
            assert_owned()
            if time.time() >= self.report.expires_at:
                raise AssetSafetyError("stale_report")
        except BaseException:
            # B still holds BEGIN IMMEDIATE and submitting ownership during undo.
            # A hard process/OS crash leaves submitting, never automatic replay.
            for path, before in reversed(written):
                self._replace(path, before)
            raise
        return ApplicationReceipt(
            asset_id=self.report.asset_id, report_id=self.report.report_id,
            target=str(self.target), paths=tuple(c.path for c in self.candidate.changes),
            applied_at=time.time(), policy_version=self.report.policy_version,
        )

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


class AssetApplicator:
    def __init__(self, store: LocalAssetStore, target: Path | str, *, policy_version: str,
                 protected_paths: tuple[Path, ...] = ()) -> None:
        self.store = store
        self.target = Path(target).absolute()
        self.policy_version = policy_version
        self.protected_paths = protected_paths

    def prepare(self, asset_id: str, report_id: str | ValidationReport) -> PreparedApplication:
        candidate, report = checked_report(self.store, asset_id, report_id, self.policy_version)
        target = check_target(self.target, self.protected_paths)
        # Resolve metadata once outside B's transaction. Re-read these exact native
        # Git files in the callback so ref/branch/HEAD changes invalidate preparation.
        ref = git(target, "symbolic-ref", "HEAD").decode().strip()
        metadata_paths = [Path(git(target, "rev-parse", "--path-format=absolute", "--git-path", name)
                               .decode().strip()) for name in ("HEAD", ref, "packed-refs")]
        if (target / ".git").is_file():
            metadata_paths.append(target / ".git")
        metadata = {path: _read(path) for path in metadata_paths}
        files = _scope_bytes(target, candidate.scope)
        if git(target, "rev-parse", "HEAD").decode().strip() != (candidate.base_head or candidate.base_revision):
            raise AssetSafetyError("target_revision_changed")
        for change in candidate.changes:
            expected = change.before.encode("utf-8") if change.before is not None else None
            if _read(safe_join(target, change.path)) != expected:
                raise AssetSafetyError("target_preimage_mismatch")
        if candidate.base_head:
            check_snapshot(target, candidate, self.store.root / "snapshots")
        else:
            tree, _ = scope_tree(target, candidate.scope, self.store.root / "snapshots")
            if tree != git(target, "rev-parse", candidate.base_revision + "^{tree}").decode().strip():
                raise AssetSafetyError("snapshot_target_changed")
        if (_scope_bytes(target, candidate.scope) != files
                or any(_read(path) != body for path, body in metadata.items())):
            raise AssetSafetyError("target_changed_during_preparation")
        return PreparedApplication(target, candidate, report, files, metadata)
