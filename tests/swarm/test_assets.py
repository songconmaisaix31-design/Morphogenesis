from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import sqlite3
import subprocess
import sys
import threading
import time

import pytest

from contracts.identity import AgentId, AttemptId
from local_assets import (
    AssetPromoter, AssetSafetyError, AssetValidator, Candidate, FileChange,
    LocalAssetStore, ValidationReport, blast_radius,
    snapshot_revision,
)
from local_assets.paths import check_target, git, safe_join


@dataclass
class Fixture:
    repository: Path
    store: LocalAssetStore
    candidate: Candidate


@pytest.fixture
def local(tmp_path: Path) -> Fixture:
    repository = tmp_path / "repository"
    repository.mkdir()
    git(repository, "init", "-b", "local-target")
    (repository / "example.py").write_bytes(b"answer = 1\n")
    (repository / "other.txt").write_bytes(b"preserve\n")
    git(repository, "add", "example.py", "other.txt")
    git(repository, "-c", "user.name=Local Test", "-c", "user.email=local@example.invalid",
        "commit", "-m", "local fixture")
    candidate = Candidate(
        attempt=AttemptId(task_id="repair", agent=AgentId(role="builder", instance=0), attempt=0),
        base_revision=git(repository, "rev-parse", "HEAD").decode().strip(),
        changes=(FileChange(path="example.py", before="answer = 1\n", after="answer = 2\n"),),
        declared_files=1, declared_lines=2,
    )
    return Fixture(repository, LocalAssetStore(tmp_path / "store"), candidate)


def validator(local: Fixture, *commands: tuple[str, ...], **kwargs: float) -> AssetValidator:
    return AssetValidator(
        local.store, local.repository,
        commands=commands or ((sys.executable, "-B", "-c", "import example; assert example.answer == 2"),),
        **kwargs,
    )


@contextmanager
def guard(scope: str) -> Iterator[Callable[[], None]]:
    assert Path(scope).is_absolute()
    yield lambda: None


def passed(local: Fixture) -> tuple[str, ValidationReport]:
    asset_id = local.store.publish(local.candidate)
    report = validator(local).validate(asset_id)
    assert report.passed, report.reasons
    return asset_id, report


def test_official_address_persistence_actual_worktree_and_promotion(local: Fixture) -> None:
    asset_id, report = passed(local)
    assert local.store.bridge.verify_asset_id(local.store.fetch_asset(asset_id))
    assert local.store.bridge.compute_asset_id(local.store.fetch_asset(asset_id)) == asset_id
    assert local.store.publish(local.candidate) == asset_id
    assert LocalAssetStore(local.store.root).fetch(asset_id) == local.candidate
    assert local.store.state(asset_id) == "quarantined"
    assert report.worktree_path and Path(report.worktree_path).resolve() != local.repository
    assert (Path(report.worktree_path) / "example.py").read_bytes() == b"answer = 2\n"
    assert (local.repository / "example.py").read_bytes() == b"answer = 1\n"
    assert report.env_fingerprint.node_version.startswith("v")
    assert report.env_fingerprint.arch and report.env_fingerprint.platform
    assert local.store.get_report(report.report_id) == report
    receipt = AssetPromoter(local.store, local.repository).promote(asset_id, report.report_id, guard)
    assert receipt.paths == ("example.py",)
    assert (local.repository / "example.py").read_bytes() == b"answer = 2\n"
    assert (local.repository / "other.txt").read_bytes() == b"preserve\n"
    assert local.store.state(asset_id) == "promoted"
    bundle = local.store.promoted_assets()
    assert [asset["type"] for asset in bundle] == ["Gene", "Capsule"]
    assert bundle[0]["asset_id"] == bundle[1]["gene"] == asset_id
    assert all(local.store.bridge.validate_asset(asset).valid for asset in bundle)
    with pytest.raises(AssetSafetyError, match="report_already_promoted"):
        AssetPromoter(local.store, local.repository).promote(asset_id, report.report_id, guard)


@pytest.mark.parametrize(("body", "reason"), [
    ("answer = (\n", "python_syntax"),
    ("import subprocess\n", "dangerous_import"),
    ("import socket as harmless\n", "dangerous_import"),
    ("eval('danger')\n", "dangerous_pattern"),
    ("import os\nos.remove('x')\n", "dangerous_pattern"),
])
def test_static_failure_quarantines_without_running(local: Fixture, body: str, reason: str) -> None:
    changed = local.candidate.model_copy(update={
        "changes": (FileChange(path="example.py", before="answer = 1\n", after=body),),
        "declared_lines": 1 + len(body.splitlines()),
    })
    asset_id = local.store.publish(changed)
    report = validator(local).validate(asset_id)
    assert not report.passed and reason in report.reasons
    assert report.commands == () and report.worktree_path is None
    assert local.store.state(asset_id) == "quarantined"
    assert local.store.promoted_assets() == []
    with pytest.raises(AssetSafetyError):
        AssetPromoter(local.store, local.repository).promote(asset_id, report.report_id, guard)


@pytest.mark.parametrize("path", [
    "../escape.py", "/escape.py", "C:/escape.py", "sub/../../escape.py",
    "sub\\escape.py", ".git/config", "CON.py", "case./file.py", "file.py:stream",
    "docs/ACCEPTANCE.md", "docs/tracks/ownership.md", "docs/source/frozen.md",
])
def test_unsafe_paths_remain_quarantined(local: Fixture, path: str) -> None:
    candidate = local.candidate.model_copy(update={
        "changes": (FileChange(path=path, before=None, after="answer = 2\n"),), "declared_lines": 1,
    })
    asset_id = local.store.publish(candidate)
    report = validator(local).validate(asset_id)
    assert not report.passed and report.worktree_path is None
    assert local.store.state(asset_id) == "quarantined"


@pytest.mark.parametrize("update,reason", [
    ({"declared_files": 2}, "blast_radius_mismatch"),
    ({"declared_lines": 1}, "blast_radius_mismatch"),
    ({"scope": "sub"}, "scope_mismatch"),
])
def test_declaration_mismatch(local: Fixture, update: dict[str, object], reason: str) -> None:
    asset_id = local.store.publish(local.candidate.model_copy(update=update))
    report = validator(local).validate(asset_id)
    assert not report.passed and reason in report.reasons


@pytest.mark.parametrize("script,reason", [
    ("raise SystemExit(4)", "validation_command_failed"),
    ("import time; time.sleep(20)", "validation_command_failed"),
    ("print('x' * 200000)", "validation_command_failed"),
    ("from pathlib import Path; Path('other.txt').write_text('tamper')", "validation_mutated_worktree"),
])
def test_bounded_commands_and_mutating_validator(local: Fixture, script: str, reason: str) -> None:
    asset_id = local.store.publish(local.candidate)
    report = validator(local, (sys.executable, "-B", "-c", script), timeout_seconds=5).validate(asset_id)
    assert not report.passed and reason in report.reasons
    assert local.store.state(asset_id) == "quarantined"
    assert (local.repository / "other.txt").read_bytes() == b"preserve\n"
    assert report.worktree_path and Path(report.worktree_path).is_dir()


def test_stale_tampered_substituted_and_changed_target(local: Fixture) -> None:
    asset_id, report = passed(local)
    promoter = AssetPromoter(local.store, local.repository)
    with pytest.raises(AssetSafetyError, match="tampered_report"):
        promoter.promote(asset_id, report.model_copy(update={"expires_at": report.expires_at + 9}), guard)
    other = local.candidate.model_copy(update={"summary": "A different candidate"})
    other_id = local.store.publish(other)
    with pytest.raises(AssetSafetyError, match="report_candidate_mismatch"):
        promoter.promote(other_id, report.report_id, guard)
    (local.repository / "example.py").write_bytes(b"answer = 99\n")
    with pytest.raises(AssetSafetyError, match="target_preimage_mismatch"):
        promoter.promote(asset_id, report.report_id, guard)
    assert local.store.state(asset_id) == "quarantined"


def test_report_expiry_and_immutable_evidence(local: Fixture) -> None:
    asset_id = local.store.publish(local.candidate)
    report = validator(local, report_ttl_seconds=0.01).validate(asset_id)
    time.sleep(0.02)
    with pytest.raises(AssetSafetyError, match="stale_report"):
        AssetPromoter(local.store, local.repository).promote(asset_id, report.report_id, guard)
    with local.store.connection() as db:
        with pytest.raises(sqlite3.IntegrityError, match="immutable_local_evidence"):
            db.execute("UPDATE reports SET body='{}'")
        with pytest.raises(sqlite3.IntegrityError, match="immutable_local_evidence"):
            db.execute("DELETE FROM assets")


def test_protected_target_and_branch(local: Fixture) -> None:
    asset_id, report = passed(local)
    with pytest.raises(AssetSafetyError, match="protected_target"):
        AssetPromoter(local.store, local.repository, protected_paths=(local.repository,)).promote(
            asset_id, report.report_id, guard)
    git(local.repository, "branch", "-m", "codex/morphogenesis-mainline")
    with pytest.raises(AssetSafetyError, match="protected_branch"):
        AssetPromoter(local.store, local.repository).promote(asset_id, report.report_id, guard)


def test_hardlink_path_is_denied(local: Fixture, tmp_path: Path) -> None:
    source = tmp_path / "outside.txt"
    source.write_text("outside", encoding="utf-8")
    (local.repository / "linked.txt").hardlink_to(source)
    with pytest.raises(AssetSafetyError, match="hardlinked_path"):
        safe_join(local.repository, "linked.txt")


def test_alias_link_is_denied(local: Fixture, tmp_path: Path) -> None:
    alias = tmp_path / "alias"
    try:
        alias.symlink_to(local.repository, target_is_directory=True)
    except OSError:
        if sys.platform != "win32":
            raise
        completed = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(alias), str(local.repository)], capture_output=True,
        )
        assert completed.returncode == 0
    with pytest.raises(AssetSafetyError, match="symlink_or_junction"):
        check_target(alias)


def test_lease_loss_rolls_back_while_fenced(local: Fixture) -> None:
    asset_id, report = passed(local)
    calls = 0

    @contextmanager
    def lost(scope: str) -> Iterator[Callable[[], None]]:
        def assert_owned() -> None:
            nonlocal calls
            calls += 1
            if calls == 3:
                raise AssetSafetyError("lease_expired")
        yield assert_owned

    with pytest.raises(AssetSafetyError, match="lease_expired"):
        AssetPromoter(local.store, local.repository).promote(asset_id, report.report_id, lost)
    assert (local.repository / "example.py").read_bytes() == b"answer = 1\n"
    assert local.store.state(asset_id) == "quarantined"


def test_same_report_concurrent_promotion_is_consumed_once(local: Fixture) -> None:
    asset_id, report = passed(local)
    lock = threading.Lock()
    outcomes: list[str] = []

    @contextmanager
    def locked(scope: str) -> Iterator[Callable[[], None]]:
        with lock:
            yield lambda: None

    def run() -> None:
        try:
            AssetPromoter(local.store, local.repository).promote(asset_id, report.report_id, locked)
            outcomes.append("ok")
        except AssetSafetyError as error:
            outcomes.append(str(error))

    threads = [threading.Thread(target=run) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
        assert not thread.is_alive()
    assert sorted(outcomes) == ["ok", "report_already_promoted"]
    assert len(local.store.promotions()) == 1


def test_radius_add_remove_and_byte_newline_change(local: Fixture) -> None:
    candidate = local.candidate.model_copy(update={"changes": (
        FileChange(path="a.txt", before=None, after="new\n"),
        FileChange(path="b.txt", before="old\n", after=None),
        FileChange(path="c.txt", before="same\r\n", after="same\n"),
    )})
    assert blast_radius(candidate) == (3, 4)


def test_only_validator_can_issue_passing_report(local: Fixture) -> None:
    asset_id, report = passed(local)
    with pytest.raises(AssetSafetyError, match="passing_report_requires_validator"):
        local.store.report(report.model_copy(update={"report_id": "forged-new-id"}))
    assert local.store.state(asset_id) == "quarantined"


def test_tampered_database_asset_fails_sdk_verification(local: Fixture) -> None:
    import json

    asset_id = local.store.publish(local.candidate)
    # Model an OS-owner edit that bypassed append-only triggers. Address checking
    # still catches substituted candidate bytes; database owner is not a sandbox.
    with local.store.connection() as db:
        db.execute("DROP TRIGGER assets_UPDATE")
        body = json.loads(db.execute("SELECT body FROM assets WHERE asset_id=?", (asset_id,)).fetchone()[0])
        body["strategy"][1] = body["strategy"][1].replace("answer = 2", "answer = 99")
        db.execute("UPDATE assets SET body=? WHERE asset_id=?", (json.dumps(body), asset_id))
    with pytest.raises(AssetSafetyError, match="tampered_asset"):
        local.store.fetch(asset_id)


def test_real_lease_guard_rejects_old_holder_after_reclaim(local: Fixture, tmp_path: Path) -> None:
    from swarm.lease import LeaseLost, LeaseManager, canonical_scope

    asset_id, report = passed(local)
    now = [10.0]
    manager = LeaseManager(tmp_path / "leases", clock=lambda: now[0])
    old = manager.acquire(local.repository, "old", ttl_seconds=1)
    assert old is not None
    now[0] = 12
    successor = manager.acquire(local.repository, "new", ttl_seconds=10)
    assert successor is not None

    @contextmanager
    def old_guard(scope: str) -> Iterator[Callable[[], None]]:
        assert canonical_scope(scope) == old.scope
        with manager.guard(old) as owned:
            yield owned

    with pytest.raises(LeaseLost):
        AssetPromoter(local.store, local.repository).promote(asset_id, report.report_id, old_guard)
    assert not manager.release(old)
    assert manager.is_valid(successor)
    assert (local.repository / "example.py").read_bytes() == b"answer = 1\n"


def test_native_worktree_create_and_delete_exact_bytes(local: Fixture) -> None:
    candidate = local.candidate.model_copy(update={
        "changes": (FileChange(path="new.txt", before=None, after="new\r\n"),
                    FileChange(path="other.txt", before="preserve\n", after=None)),
        "declared_files": 2, "declared_lines": 2,
    })
    asset_id = local.store.publish(candidate)
    command = (sys.executable, "-B", "-c",
               "from pathlib import Path; assert Path('new.txt').read_bytes() == b'new\\r\\n'; assert not Path('other.txt').exists()")
    report = validator(local, command).validate(asset_id)
    assert report.passed, report.reasons
    AssetPromoter(local.store, local.repository).promote(asset_id, report.report_id, guard)
    assert (local.repository / "new.txt").read_bytes() == b"new\r\n"
    assert not (local.repository / "other.txt").exists()


@pytest.mark.parametrize("body,passed_check", [("const value = 2;\n", True), ("const = ;\n", False)])
def test_javascript_node_syntax_in_real_worktree(local: Fixture, body: str, passed_check: bool) -> None:
    candidate = local.candidate.model_copy(update={
        "changes": (FileChange(path="new.js", before=None, after=body),), "declared_lines": 1,
    })
    asset_id = local.store.publish(candidate)
    report = validator(local, (sys.executable, "-B", "-c", "pass")).validate(asset_id)
    assert report.passed is passed_check
    if not passed_check:
        assert report.reasons == ("javascript_syntax",)


def test_fixed_frozen_mainline_is_denied_without_writes() -> None:
    from local_assets.paths import FROZEN_MAINLINE

    with pytest.raises(AssetSafetyError, match="protected_target"):
        LocalAssetStore(FROZEN_MAINLINE / ".runtime" / "must-not-create")
    if FROZEN_MAINLINE.exists():
        with pytest.raises(AssetSafetyError, match="protected_target"):
            check_target(FROZEN_MAINLINE)


def test_two_generations_same_file_snapshot_preserves_other_wip_and_index(local: Fixture) -> None:
    (local.repository / "other.txt").write_bytes(b"unrelated staged WIP\n")
    git(local.repository, "add", "other.txt")
    (local.repository / "untracked.txt").write_bytes(b"untracked WIP\n")
    index = (local.repository / ".git" / "index").read_bytes()
    head = git(local.repository, "rev-parse", "HEAD")
    for before, after in ((1, 2), (2, 3)):
        revision, base_head = snapshot_revision(local.repository, "example.py", local.store.root / "snapshots")
        candidate = local.candidate.model_copy(update={
            "base_revision": revision, "base_head": base_head, "scope": "example.py",
            "changes": (FileChange(path="example.py", before=f"answer = {before}\n", after=f"answer = {after}\n"),),
        })
        asset_id = local.store.publish(candidate)
        report = validator(local, (sys.executable, "-B", "-c",
                                  f"import example; assert example.answer == {after}")).validate(asset_id)
        assert report.passed, report.reasons
        AssetPromoter(local.store, local.repository).promote(asset_id, report.report_id, guard)
        assert (local.repository / "example.py").read_bytes() == f"answer = {after}\n".encode()
        assert git(local.repository, "rev-parse", "HEAD") == head
        assert (local.repository / ".git" / "index").read_bytes() == index
        assert (local.repository / "other.txt").read_bytes() == b"unrelated staged WIP\n"
        assert (local.repository / "untracked.txt").read_bytes() == b"untracked WIP\n"
        assert git(local.repository, "show", revision + ":other.txt") == b"preserve\n"
    assert len(local.store.promotions()) == 2


def test_snapshot_stale_scope_dependency_rejected(local: Fixture) -> None:
    revision, base_head = snapshot_revision(local.repository, ".", local.store.root / "snapshots")
    candidate = local.candidate.model_copy(update={"base_revision": revision, "base_head": base_head})
    asset_id = local.store.publish(candidate)
    report = validator(local).validate(asset_id)
    assert report.passed, report.reasons
    (local.repository / "other.txt").write_bytes(b"changed after validation\n")
    with pytest.raises(AssetSafetyError, match="snapshot_target_changed"):
        AssetPromoter(local.store, local.repository).promote(asset_id, report.report_id, guard)
    assert (local.repository / "example.py").read_bytes() == b"answer = 1\n"
