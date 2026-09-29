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
    AssetPromoter, AssetApplicator, AssetSafetyError, AssetValidator, Candidate, FileChange,
    FileExpectation, ValidationPolicy,
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
        commands=commands,
        policy=ValidationPolicy(version="test-v1", expectations=(FileExpectation(path="example.py", content="answer = 2\n"),)),
        **kwargs,
    )


@contextmanager
def guard(scope: str) -> Iterator[Callable[[], None]]:
    assert Path(scope).is_absolute()
    yield lambda: None


def prepare(local: Fixture, asset_id: str, report: ValidationReport):
    return AssetApplicator(local.store, local.repository, policy_version="test-v1").prepare(asset_id, report)


def apply(local: Fixture, asset_id: str, report: ValidationReport, lease_guard=guard):
    prepared = prepare(local, asset_id, report)
    with lease_guard(prepared.scope) as assert_owned:
        return prepared.apply(assert_owned)


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
    receipt = AssetPromoter(local.store, policy_version="test-v1").promote(asset_id, report.report_id)
    assert receipt.paths == () and receipt.target == ""
    assert (local.repository / "example.py").read_bytes() == b"answer = 1\n"
    apply(local, asset_id, report)
    assert (local.repository / "example.py").read_bytes() == b"answer = 2\n"
    assert (local.repository / "other.txt").read_bytes() == b"preserve\n"
    assert local.store.state(asset_id) == "approved"
    bundle = local.store.promoted_assets()
    assert [asset["type"] for asset in bundle] == ["Gene", "Capsule"]
    assert bundle[0]["asset_id"] == bundle[1]["gene"] == asset_id
    assert all(local.store.bridge.validate_asset(asset).valid for asset in bundle)
    assert AssetPromoter(local.store, policy_version="test-v1").promote(asset_id, report.report_id) == receipt


@pytest.mark.parametrize(("body", "reason"), [
    ("answer = (\n", "python_syntax"),
    ("return 2\n", "python_syntax"),
    ("def function(arg, arg): pass\n", "python_syntax"),
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
        AssetPromoter(local.store, policy_version="test-v1").promote(asset_id, report.report_id)


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


@pytest.mark.parametrize("script", [
    "raise SystemExit(4)", "import time; time.sleep(20)", "print('x' * 200000)",
    "from pathlib import Path; Path('other.txt').write_text('tamper')",
])
def test_arbitrary_commands_fail_closed(local: Fixture, script: str) -> None:
    asset_id = local.store.publish(local.candidate)
    report = validator(local, (sys.executable, "-B", "-c", script), timeout_seconds=5).validate(asset_id)
    assert not report.passed and report.reasons == ("arbitrary_execution_isolation_unavailable",)
    assert report.worktree_path is None and report.commands == ()
    assert local.store.state(asset_id) == "quarantined"
    assert (local.repository / "other.txt").read_bytes() == b"preserve\n"


def test_stale_tampered_substituted_and_changed_target(local: Fixture) -> None:
    asset_id, report = passed(local)
    promoter = AssetPromoter(local.store, policy_version="test-v1")
    with pytest.raises(AssetSafetyError, match="tampered_report"):
        promoter.promote(asset_id, report.model_copy(update={"expires_at": report.expires_at + 9}))
    other = local.candidate.model_copy(update={"summary": "A different candidate"})
    other_id = local.store.publish(other)
    with pytest.raises(AssetSafetyError, match="report_candidate_mismatch"):
        promoter.promote(other_id, report.report_id)
    (local.repository / "example.py").write_bytes(b"answer = 99\n")
    with pytest.raises(AssetSafetyError, match="target_preimage_mismatch"):
        apply(local, asset_id, report)
    assert local.store.state(asset_id) == "quarantined"


def test_report_expiry_and_immutable_evidence(local: Fixture) -> None:
    asset_id = local.store.publish(local.candidate)
    report = validator(local, report_ttl_seconds=0.01).validate(asset_id)
    time.sleep(0.02)
    with pytest.raises(AssetSafetyError, match="stale_report"):
        AssetPromoter(local.store, policy_version="test-v1").promote(asset_id, report.report_id)
    with local.store.connection() as db:
        with pytest.raises(sqlite3.IntegrityError, match="immutable_local_evidence"):
            db.execute("UPDATE reports SET body='{}'")
        with pytest.raises(sqlite3.IntegrityError, match="immutable_local_evidence"):
            db.execute("DELETE FROM assets")


def test_protected_target_and_branch(local: Fixture) -> None:
    asset_id, report = passed(local)
    with pytest.raises(AssetSafetyError, match="protected_target"):
        AssetApplicator(local.store, local.repository, policy_version="test-v1", protected_paths=(local.repository,)).prepare(
            asset_id, report.report_id)
    git(local.repository, "branch", "-m", "codex/morphogenesis-mainline")
    with pytest.raises(AssetSafetyError, match="protected_branch"):
        prepare(local, asset_id, report)


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
        apply(local, asset_id, report, lost)
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
            AssetPromoter(local.store, policy_version="test-v1").promote(asset_id, report.report_id)
            outcomes.append("ok")
        except AssetSafetyError as error:
            outcomes.append(str(error))

    threads = [threading.Thread(target=run) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
        assert not thread.is_alive()
    assert outcomes == ["ok", "ok"]
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


def test_native_worktree_create_and_delete_exact_bytes(local: Fixture) -> None:
    candidate = local.candidate.model_copy(update={
        "changes": (FileChange(path="new.txt", before=None, after="new\r\n"),
                    FileChange(path="other.txt", before="preserve\n", after=None)),
        "declared_files": 2, "declared_lines": 2,
    })
    asset_id = local.store.publish(candidate)
    command = (sys.executable, "-B", "-c",
               "from pathlib import Path; assert Path('new.txt').read_bytes() == b'new\\r\\n'; assert not Path('other.txt').exists()")
    report = AssetValidator(local.store, local.repository, policy=ValidationPolicy(
        version="test-v1", expectations=(FileExpectation(path="new.txt", content="new\r\n"),
                                        FileExpectation(path="other.txt", content=None)))).validate(asset_id)
    assert report.passed, report.reasons
    apply(local, asset_id, report)
    assert (local.repository / "new.txt").read_bytes() == b"new\r\n"
    assert not (local.repository / "other.txt").exists()


@pytest.mark.parametrize("body,passed_check", [("const value = 2;\n", True), ("const = ;\n", False)])
def test_javascript_node_syntax_in_real_worktree(local: Fixture, body: str, passed_check: bool) -> None:
    candidate = local.candidate.model_copy(update={
        "changes": (FileChange(path="new.js", before=None, after=body),), "declared_lines": 1,
    })
    asset_id = local.store.publish(candidate)
    report = AssetValidator(local.store, local.repository, policy=ValidationPolicy(
        version="test-v1", expectations=(FileExpectation(path="new.js", content=body),))).validate(asset_id)
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
        report = AssetValidator(local.store, local.repository, policy=ValidationPolicy(
            version="test-v1", expectations=(FileExpectation(path="example.py", content=f"answer = {after}\n"),))).validate(asset_id)
        assert report.passed, report.reasons
        apply(local, asset_id, report)
        AssetPromoter(local.store, policy_version="test-v1").promote(asset_id, report.report_id)
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
        prepare(local, asset_id, report)
    assert (local.repository / "example.py").read_bytes() == b"answer = 1\n"


def test_fixed_policy_is_independent_and_version_bound(local: Fixture) -> None:
    asset_id, report = passed(local)
    with pytest.raises(AssetSafetyError, match="validation_policy_mismatch"):
        AssetPromoter(local.store, policy_version="test-v2").promote(asset_id, report.report_id)
    wrong = ValidationPolicy(version="test-v1", expectations=(FileExpectation(path="example.py", content="answer = 99\n"),))
    rejected = AssetValidator(local.store, local.repository, policy=wrong).validate(asset_id)
    assert rejected.reasons == ("fixed_expectation_failed",)
    assert rejected.policy_json == wrong.model_dump_json()
    missing = AssetValidator(local.store, local.repository).validate(asset_id)
    assert missing.reasons == ("fixed_validation_policy_required",)


@pytest.mark.parametrize("path", ["tests/test_candidate.py", "swarm/budget.py", "local_assets/validate.py",
                                  "verifier.py", "src/executor.py", "docs/SWARM_TASK.md"])
def test_candidate_cannot_modify_fixed_verifier_or_runtime(local: Fixture, path: str) -> None:
    candidate = local.candidate.model_copy(update={
        "changes": (FileChange(path=path, before=None, after="pass\n"),), "declared_lines": 1,
    })
    asset_id = local.store.publish(candidate)
    report = validator(local).validate(asset_id)
    assert not report.passed and report.worktree_path is None
    assert report.reasons[0] in {"protected_execution_policy", "protected_document"}


def test_candidate_python_is_inert_and_host_commands_never_start(local: Fixture, tmp_path: Path,
                                                                 monkeypatch: pytest.MonkeyPatch) -> None:
    marker = tmp_path / "outside-marker"
    # This is valid syntax but the literal executor does not evaluate/import it.
    body = f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n"
    candidate = local.candidate.model_copy(update={
        "changes": (FileChange(path="example.py", before="answer = 1\n", after=body),), "declared_lines": 3,
    })
    asset_id = local.store.publish(candidate)
    report = AssetValidator(local.store, local.repository, policy=ValidationPolicy(
        version="inert-data-v1", expectations=(FileExpectation(path="example.py", content=body),))).validate(asset_id)
    assert report.passed and report.isolation == "non_arbitrary_literal_files"
    assert not marker.exists()
    called: list[object] = []
    original = subprocess.Popen

    def observe(*args, **kwargs):
        called.append(args[0])
        return original(*args, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", observe)
    commands = (
        (sys.executable, "-c", "import socket; socket.create_connection(('127.0.0.1',9))"),
        (sys.executable, "-c", "import os; print(os.environ['ASSET_TEST_SECRET'])"),
        (sys.executable, "-c", f"from pathlib import Path; Path({str(marker)!r}).write_text('escape')"),
    )
    monkeypatch.setenv("ASSET_TEST_SECRET", "synthetic-secret-never-read")
    for command in commands:
        denied = validator(local, command).validate(asset_id)
        assert denied.reasons == ("arbitrary_execution_isolation_unavailable",)
        assert denied.commands == () and not marker.exists()
    assert not any(isinstance(argv, (list, tuple)) and argv and argv[0] == sys.executable for argv in called)
    assert all("synthetic-secret-never-read" not in r.model_dump_json() for r in local.store.reports())


def test_prepared_baseline_and_own_swarm_tree_are_protected(local: Fixture) -> None:
    from local_assets.paths import SWARM_SOURCE

    asset_id, report = passed(local)
    ready = prepare(local, asset_id, report)
    (local.repository / "other.txt").write_bytes(b"changed after prepare\n")
    with pytest.raises(AssetSafetyError, match="target_changed_after_preparation"):
        ready.apply(lambda: None)
    assert (local.repository / "example.py").read_bytes() == b"answer = 1\n"
    with pytest.raises(AssetSafetyError, match="protected_target"):
        AssetApplicator(local.store, SWARM_SOURCE, policy_version="test-v1").prepare(asset_id, report)


def task_lease(local: Fixture, *, task_id: str = "repair", scope: str = ".", clock=time.time):
    from swarm.models import Locality, Signal
    from swarm.task_ledger import TaskLedger

    ledger = TaskLedger(local.store.root / "tasks.sqlite3", "asset-test", clock=clock)
    ledger.enqueue(Signal(task_id=task_id, workspace=str(local.repository), scope=scope, kind="opportunity"))
    locality = Locality(workspace=str(local.repository), authorized_scopes=(".",))
    lease = ledger.claim(task_id, "consumer", ttl_seconds=300, locality=locality)
    assert lease is not None
    return ledger, lease, locality


def test_real_sqlite_submit_rejects_stale_before_target_write(local: Fixture) -> None:
    from swarm.task_ledger import LeaseLost

    asset_id, report = passed(local)
    ready = prepare(local, asset_id, report)
    now = [100.0]
    ledger, old, locality = task_lease(local, clock=lambda: now[0])
    now[0] = 401.0
    successor = ledger.claim("repair", "successor", ttl_seconds=30, locality=locality)
    assert successor is not None and successor.token == old.token + 1
    writes: list[str] = []

    def effect(owned):
        writes.append(ready.apply(owned).asset_id)

    ledger.submit(successor, "successor-result", {"asset_id": asset_id}, apply=effect)
    with pytest.raises(LeaseLost):
        ledger.submit(old, "old-result", {"asset_id": asset_id}, apply=effect)
    assert writes == [asset_id]
    assert (local.repository / "example.py").read_bytes() == b"answer = 2\n"
    assert local.store.state(asset_id) == "quarantined"
    assert not ledger.release(old)


def test_approved_fetch_applicability_injection_actual_execution_and_adoption(local: Fixture) -> None:
    from local_assets import AssetConsumer, ConsumptionContext

    local.candidate = local.candidate.model_copy(update={"required_capabilities": ("literal",), "dependencies": ("setup",)})
    asset_id, report = passed(local)
    consumer = AssetConsumer(local.store)
    ledger, lease, _ = task_lease(local, task_id="reuse")
    context = ConsumptionContext(swarm_id=lease.swarm_id, task_id="reuse", worker_id=lease.worker_id, fencing_token=lease.token,
                                 execution_id="member-b-execution", scope=".", capabilities=("literal",),
                                 completed_dependencies=("setup",), input_context="new member task: create next.py")
    with pytest.raises(AssetSafetyError, match="asset_not_approved"):
        consumer.inject(asset_id, context)
    AssetPromoter(local.store, policy_version="test-v1").promote(asset_id, report)
    for update, reason in [({"capabilities": ()}, "capabilities"), ({"completed_dependencies": ()}, "dependencies")]:
        with pytest.raises(AssetSafetyError, match=reason):
            consumer.inject(asset_id, context.model_copy(update=update))
    injected = consumer.inject(asset_id, context)
    assert local.store.adoptions() == []
    with pytest.raises(AssetSafetyError, match="execution_not_consumed"):
        consumer.record_adoption(context.execution_id, "reuse-result", ledger)
    attempt = AttemptId(task_id="reuse", agent=AgentId(role="builder", instance=1), attempt=0)
    with pytest.raises(AssetSafetyError, match="unsafe_relative_path"):
        consumer.execute(injected, attempt=attempt, base_revision=local.candidate.base_revision,
                         path_map={"example.py": "../escape.py"}, preimages={"../escape.py": None})
    execution = consumer.execute(injected, attempt=attempt, base_revision=local.candidate.base_revision,
                                 path_map={"example.py": "next.py"}, preimages={"next.py": None})
    assert execution.candidate.changes[0].after == "answer = 2\n"
    assert local.store.adoptions() == [] and not (local.repository / "next.py").exists()
    policy = ValidationPolicy(version="reuse-v1", expectations=(FileExpectation(path="next.py", content="answer = 2\n"),))
    derived_report = AssetValidator(local.store, local.repository, policy=policy).validate(execution.candidate_asset_id)
    assert derived_report.passed, derived_report.reasons
    prepared = AssetApplicator(local.store, local.repository, policy_version=policy.version).prepare(
        execution.candidate_asset_id, derived_report)
    result = {"candidate_asset_id": execution.candidate_asset_id, "consumed_asset_ids": [asset_id],
              "input_context": context.input_context, "execution_id": context.execution_id, "applied": True}

    def apply_result(owned):
        prepared.apply(owned)

    # A source-only approval or injection never proves this task completed.
    with pytest.raises(AssetSafetyError, match="asset_not_approved"):
        consumer.record_adoption(context.execution_id, "reuse-result", ledger)
    # Index approval is independent. Even an approved output plus fabricated
    # result metadata or a no-op effect callback cannot create an adoption.
    AssetPromoter(local.store, policy_version=policy.version).promote(execution.candidate_asset_id, derived_report)
    from swarm.task_ledger import TaskLedger
    from swarm.models import Locality

    for effect, reason in [(None, "completed_fenced_execution"), (lambda owned: owned(), "target_effect_missing")]:
        fake = TaskLedger(local.store.root / (reason + ".sqlite3"), lease.swarm_id)
        fake.enqueue(ledger.get("reuse").signal)
        fake_lease = fake.claim("reuse", lease.worker_id, ttl_seconds=300,
                                locality=Locality(workspace=str(local.repository), authorized_scopes=(".",)))
        assert fake_lease is not None
        fake.submit(fake_lease, "reuse-result", result, apply=effect)
        with pytest.raises(AssetSafetyError, match=reason):
            consumer.record_adoption(context.execution_id, "reuse-result", fake)
        assert local.store.adoptions() == []
    completed = ledger.submit(lease, "reuse-result", result, apply=apply_result)
    assert completed.status == "completed"
    AssetPromoter(local.store, policy_version=policy.version).promote(execution.candidate_asset_id, derived_report)
    receipt = consumer.record_adoption(context.execution_id, "reuse-result", ledger)
    assert receipt.asset_id == asset_id and receipt.context == context
    assert (local.repository / "next.py").read_bytes() == b"answer = 2\n"
    assert len(local.store.adoptions()) == 1
    assert consumer.record_adoption(context.execution_id, "reuse-result", ledger) == receipt
    with pytest.raises(AssetSafetyError, match="completed_fenced_execution"):
        consumer.record_adoption(context.execution_id, "wrong-result", ledger)
    from types import SimpleNamespace

    for update in ({"swarm_id": "wrong-swarm"}, {"owner": "stale-owner"}, {"token": lease.token + 1},
                   {"result": {**result, "input_context": "substituted"}},
                   {"result": {**result, "execution_id": "substituted"}},
                   {"result": {**result, "consumed_asset_ids": ["sha256:wrong"]}}):
        replaced = completed.model_copy(update=update)
        with pytest.raises(AssetSafetyError, match="adoption_"):
            consumer.record_adoption(context.execution_id, "reuse-result", SimpleNamespace(get=lambda task: replaced))
    (local.repository / "next.py").write_bytes(b"later task output\n")
    assert consumer.record_adoption(context.execution_id, "reuse-result", ledger) == receipt
    assert len(local.store.adoptions()) == 1


def test_approved_asset_scope_must_cover_consumer_scope(local: Fixture) -> None:
    from local_assets import AssetConsumer, ConsumptionContext

    local.candidate = local.candidate.model_copy(update={"scope": "example.py"})
    asset_id, report = passed(local)
    AssetPromoter(local.store, policy_version="test-v1").promote(asset_id, report)
    context = ConsumptionContext(swarm_id="test", task_id="new-task", worker_id="builder-1", fencing_token=1,
                                 execution_id="new-execution", scope=".", input_context="wider scope")
    with pytest.raises(AssetSafetyError, match="scope_inapplicable"):
        AssetConsumer(local.store).inject(asset_id, context)


def _crash_during_publication(root: str, target: str, asset_id: str, report_id: str, lease_json: str) -> None:
    import os
    from local_assets import PreparedApplication
    from swarm.models import Lease
    from swarm.task_ledger import TaskLedger

    store = LocalAssetStore(root)
    ready = AssetApplicator(store, target, policy_version="crash-v1").prepare(asset_id, report_id)
    ledger = TaskLedger(store.root / "tasks.sqlite3", "asset-test")
    replace = PreparedApplication._replace

    def die(path: Path, content: bytes | None) -> None:
        replace(path, content)
        os._exit(71)

    PreparedApplication._replace = staticmethod(die)

    def effect(owned):
        ready.apply(owned)

    ledger.submit(Lease.model_validate_json(lease_json), "crashed-result", {"asset_id": asset_id}, apply=effect)


def test_process_crash_leaves_partial_patch_quarantined_and_scope_blocked(local: Fixture) -> None:
    import multiprocessing

    candidate = local.candidate.model_copy(update={
        "changes": (*local.candidate.changes, FileChange(path="new.txt", before=None, after="new\n")),
        "declared_files": 2, "declared_lines": 3,
    })
    asset_id = local.store.publish(candidate)
    policy = ValidationPolicy(version="crash-v1", expectations=(
        FileExpectation(path="example.py", content="answer = 2\n"), FileExpectation(path="new.txt", content="new\n")))
    report = AssetValidator(local.store, local.repository, policy=policy).validate(asset_id)
    assert report.passed
    ledger, lease, locality = task_lease(local)
    child = multiprocessing.get_context("spawn").Process(target=_crash_during_publication, args=(
        str(local.store.root), str(local.repository), asset_id, report.report_id, lease.model_dump_json()))
    child.start()
    child.join(40)
    if child.is_alive():
        child.terminate()
        child.join(10)
        pytest.fail("owned publication test child timed out")
    assert child.exitcode == 71
    assert (local.repository / "example.py").read_bytes() == b"answer = 2\n"
    assert not (local.repository / "new.txt").exists()
    assert ledger.get("repair").status == "submitting"
    assert ledger.claim("repair", "successor", locality=locality) is None
    assert local.store.state(asset_id) == "quarantined" and local.store.adoptions() == []
