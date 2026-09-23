"""Conservative static checks then bounded commands in a retained Git worktree."""

from __future__ import annotations

import ast
import difflib
import json
import math
import os
from pathlib import Path
import platform
import re
import signal
import subprocess
import tempfile
import time
from uuid import uuid4

from bridge_node.environment import child_environment
from local_assets.models import (
    AssetSafetyError, Candidate, CommandResult, EnvironmentFingerprint, ValidationReport,
)
from local_assets.paths import git, no_links, relative_path, safe_join
from local_assets.store import LocalAssetStore


def blast_radius(candidate: Candidate) -> tuple[int, int]:
    """Count changed files and added+removed logical lines, including replacements."""
    count = lines = 0
    for change in candidate.changes:
        if change.before == change.after:
            continue
        count += 1
        before = (change.before or "").splitlines(keepends=True)
        after = (change.after or "").splitlines(keepends=True)
        for kind, i, j, k, l in difflib.SequenceMatcher(None, before, after, autojunk=False).get_opcodes():
            if kind != "equal":
                lines += (j - i) + (l - k)
    return count, lines


def inspect_candidate(candidate: Candidate) -> tuple[int, int]:
    scope = relative_path(candidate.scope, allow_root=True)
    paths: set[str] = set()
    for change in candidate.changes:
        path = relative_path(change.path)
        lowered = path.casefold()
        if lowered in paths or any(lowered.startswith(p + "/") or p.startswith(lowered + "/") for p in paths):
            raise AssetSafetyError("duplicate_or_overlapping_paths")
        paths.add(lowered)
        if scope != "." and path != scope and not path.startswith(scope + "/"):
            raise AssetSafetyError("scope_mismatch")
        if change.before == change.after:
            raise AssetSafetyError("unchanged_file")
        for body in (change.before, change.after):
            if body is not None and ("\x00" in body or len(body.encode("utf-8")) > 256 * 1024):
                raise AssetSafetyError("unsupported_binary_or_large_file")
        if change.after is not None:
            static_syntax(path, change.after)
    actual = blast_radius(candidate)
    if actual != (candidate.declared_files, candidate.declared_lines):
        raise AssetSafetyError("blast_radius_mismatch")
    return actual


_DANGEROUS = re.compile(
    r"\b(?:eval|exec|compile|__import__)\s*\(|\b(?:system|popen|unlink|rmtree|remove|"
    r"rmdir|chmod|chown|kill|spawn|execSync|execFile|fork)\s*\(|"
    r"child_process|node:fs|node:net|node:http|\bfetch\s*\(|"
    r"\b(?:curl|wget)\b|rm\s+-[rf]|Remove-Item|Invoke-Expression", re.IGNORECASE,
)
_DANGEROUS_IMPORTS = frozenset({
    "subprocess", "socket", "ctypes", "multiprocessing", "requests", "httpx",
    "urllib", "http", "ftplib", "shutil", "importlib", "pickle", "marshal", "os",
})


def static_syntax(path: str, body: str) -> None:
    if _DANGEROUS.search(body):
        raise AssetSafetyError("dangerous_pattern")
    suffix = Path(path).suffix.lower()
    if suffix == ".py":
        try:
            tree = ast.parse(body, filename=path)
            # Parsing alone accepts e.g. module-level return/break and duplicate
            # parameters. Compile validates those contexts without executing.
            compile(tree, path, "exec")
        except (SyntaxError, ValueError):
            raise AssetSafetyError("python_syntax") from None
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [(node.module or "").split(".")[0]]
            if any(name in _DANGEROUS_IMPORTS for name in names):
                raise AssetSafetyError("dangerous_import")
    elif suffix == ".json":
        try:
            json.loads(body)
        except ValueError:
            raise AssetSafetyError("json_syntax") from None
    elif suffix not in {".js", ".mjs", ".cjs", ".txt", ".md"}:
        raise AssetSafetyError("unsupported_static_language")


def fingerprint(workspace: Path) -> EnvironmentFingerprint:
    result = subprocess.run(
        ["node", "-p", "JSON.stringify({node_version:process.version,arch:process.arch,platform:process.platform})"],
        capture_output=True, timeout=10, check=True, shell=False,
        env=child_environment(workspace),
    )
    data = json.loads(result.stdout)
    return EnvironmentFingerprint(
        node_version=data["node_version"], arch=data["arch"], platform=data["platform"],
        python_version=platform.python_version(),
    )


def _stop(process: subprocess.Popen[bytes]) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                       capture_output=True, timeout=10, check=False)
    else:
        try:
            getattr(os, "killpg")(process.pid, getattr(signal, "SIGKILL"))
        except ProcessLookupError:
            pass
    if process.poll() is None:
        process.kill()
    process.wait(timeout=10)


def run_bounded(argv: tuple[str, ...], cwd: Path, env: dict[str, str], *,
                timeout: float, output_limit: int) -> CommandResult:
    with tempfile.TemporaryFile() as output:
        process = subprocess.Popen(
            argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
            stdout=output, stderr=output, shell=False,
            start_new_session=os.name != "nt",
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
        )
        deadline = time.monotonic() + timeout
        timed_out = limited = False
        try:
            while process.poll() is None:
                timed_out = time.monotonic() >= deadline
                limited = os.fstat(output.fileno()).st_size > output_limit
                if timed_out or limited:
                    _stop(process)
                    break
                time.sleep(0.02)
            limited = limited or os.fstat(output.fileno()).st_size > output_limit
        finally:
            if process.poll() is None:
                _stop(process)
        return CommandResult(argv=argv, exit_code=process.returncode,
                             timed_out=timed_out, output_limited=limited)


class AssetValidator:
    def __init__(self, store: LocalAssetStore, repository: Path | str, *,
                 commands: tuple[tuple[str, ...], ...], timeout_seconds: float = 30,
                 report_ttl_seconds: float = 300, output_limit: int = 128 * 1024) -> None:
        if (not commands or len(commands) > 16 or any(not argv or not argv[0] for argv in commands)
                or not 0 < timeout_seconds <= 300 or not math.isfinite(timeout_seconds)
                or not 0 < report_ttl_seconds <= 86400 or not math.isfinite(report_ttl_seconds)
                or not 1024 <= output_limit <= 1024 * 1024):
            raise ValueError("bounded_nonempty_validation_required")
        self.store = store
        self.repository = Path(repository).resolve()
        self.commands = commands
        self.timeout_seconds = timeout_seconds
        self.report_ttl_seconds = report_ttl_seconds
        self.output_limit = output_limit

    def validate(self, asset_id: str) -> ValidationReport:
        candidate = self.store.fetch(asset_id)
        report_id = uuid4().hex
        reasons: list[str] = []
        results: list[CommandResult] = []
        worktree: Path | None = None
        actual_files, actual_lines = blast_radius(candidate)
        with tempfile.TemporaryDirectory(prefix="swarm-validation-env-") as temporary:
            environment_root = Path(temporary)
            fp = fingerprint(environment_root)
            env = child_environment(environment_root)
            env.update({"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
                        "PYTHONDONTWRITEBYTECODE": "1"})
            try:
                inspect_candidate(candidate)
                no_links(self.repository)
                # Reject checkout-time links and submodules before materialization.
                tree = git(self.repository, "ls-tree", "-rz", candidate.base_revision)
                if any(record.startswith((b"120000 ", b"160000 ")) for record in tree.split(b"\0")):
                    raise AssetSafetyError("baseline_links_or_submodules")
                worktree = self.store.root / "worktrees" / report_id
                no_links(worktree)
                worktree.parent.mkdir(exist_ok=True)
                git(self.repository, "worktree", "add", "--detach", str(worktree), candidate.base_revision)
                git_marker = (worktree / ".git").read_bytes()
                deadline = time.monotonic() + self.timeout_seconds
                for change in candidate.changes:
                    path = safe_join(worktree, change.path)
                    before = path.read_bytes() if path.is_file() else None
                    expected = change.before.encode("utf-8") if change.before is not None else None
                    if path.is_dir() or before != expected:
                        raise AssetSafetyError("baseline_preimage_mismatch")
                    if change.after is None:
                        path.unlink()
                    else:
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_bytes(change.after.encode("utf-8"))
                        if path.suffix.lower() in {".js", ".mjs", ".cjs"}:
                            remaining = deadline - time.monotonic()
                            if remaining <= 0:
                                raise AssetSafetyError("validation_timeout")
                            result = run_bounded(("node", "--check", str(path)), worktree, env,
                                                 timeout=remaining, output_limit=self.output_limit)
                            results.append(result)
                            if result.exit_code != 0 or result.timed_out or result.output_limited:
                                raise AssetSafetyError("javascript_syntax")
                before_tree = self._snapshot(worktree)
                for command in self.commands:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise AssetSafetyError("validation_timeout")
                    result = run_bounded(command, worktree, env, timeout=remaining, output_limit=self.output_limit)
                    results.append(result)
                    if result.exit_code != 0 or result.timed_out or result.output_limited:
                        raise AssetSafetyError("validation_command_failed")
                if (worktree / ".git").read_bytes() != git_marker or self._snapshot(worktree) != before_tree:
                    raise AssetSafetyError("validation_mutated_worktree")
            except (AssetSafetyError, OSError, subprocess.SubprocessError) as error:
                reasons.append(str(error) if isinstance(error, AssetSafetyError) else type(error).__name__)
        now = time.time()
        report = ValidationReport(
            report_id=report_id, asset_id=asset_id, attempt=candidate.attempt,
            base_revision=candidate.base_revision, candidate_json=candidate.model_dump_json(),
            passed=not reasons, reasons=tuple(reasons), actual_files=actual_files, actual_lines=actual_lines,
            env_fingerprint=fp, commands=tuple(results),
            worktree_path=str(worktree) if worktree is not None else None,
            created_at=now, expires_at=now + self.report_ttl_seconds,
        )
        self.store._record_validation(report)
        return report

    @staticmethod
    def _snapshot(root: Path) -> dict[str, bytes]:
        files: dict[str, bytes] = {}
        total = 0
        for path in root.rglob("*"):
            no_links(path)
            if path.is_file() and path.name != ".git":
                total += path.stat().st_size
                if len(files) >= 20000 or total > 64 * 1024 * 1024:
                    raise AssetSafetyError("validation_tree_limit")
                files[path.relative_to(root).as_posix()] = path.read_bytes()
        return files
