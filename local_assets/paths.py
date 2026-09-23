"""Fail-closed portable paths and read-only Git inspection."""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath
import re
import subprocess

from local_assets.models import AssetSafetyError

FROZEN_MAINLINE = Path("C:/Users/DW/orca/Morphogenesis")
SWARM_SOURCE = Path(__file__).resolve().parents[1]
PROTECTED_BRANCHES = frozenset({"main", "master", "codex/morphogenesis-mainline"})
PROTECTED_FILES = frozenset({"docs/acceptance.md", "docs/plan.md", "docs/status.md"})


def relative_path(value: str, *, allow_root: bool = False) -> str:
    if value == "." and allow_root:
        return value
    parts = value.split("/")
    if (not value or any(char in value for char in '\\:<>"|?*') or "\x00" in value
            or any(part in {"", ".", ".."} or part.endswith((".", " ")) for part in parts)
            or any(ord(char) < 32 for char in value)
            or PurePosixPath(value).is_absolute()):
        raise AssetSafetyError("unsafe_relative_path")
    for part in parts:
        if part.lower() == ".git" or re.fullmatch(
            r"(?i)(con|prn|aux|nul|com[0-9]|lpt[0-9])(?:\..*)?", part
        ):
            raise AssetSafetyError("reserved_path")
    lowered = value.lower()
    if (lowered in PROTECTED_FILES or lowered.startswith("docs/tracks/")
            or lowered.startswith("docs/source/") or lowered.startswith("docs/swarm_")):
        raise AssetSafetyError("protected_document")
    if (lowered.split("/")[0] in {"swarm", "local_assets", "tests", "bridge_node", "hub_client",
                                    "orchestration", "metabolism", "contracts", ".github"}
            or lowered in {"pyproject.toml", "poetry.lock", "package.json", "package-lock.json", "agents.md"}
            or PurePosixPath(lowered).name in {"executor.py", "worker_loop.py", "budget.py", "validate.py",
                                               "verifier.py", "verify.py"}
            or lowered.startswith("tools/")):
        raise AssetSafetyError("protected_execution_policy")
    return value


def no_links(path: Path) -> None:
    absolute = Path(os.path.abspath(path))
    for component in (*reversed(absolute.parents), absolute):
        if component.is_symlink() or component.is_junction():
            raise AssetSafetyError("symlink_or_junction")
        if component.exists() and component.is_file() and component.stat().st_nlink > 1:
            raise AssetSafetyError("hardlinked_path")


def safe_join(root: Path, value: str) -> Path:
    relative_path(value)
    path = root.joinpath(*value.split("/"))
    no_links(path)
    if not path.resolve().is_relative_to(root.resolve()):
        raise AssetSafetyError("path_escape")
    return path


def git(root: Path, *args: str, timeout: float = 15, input_data: bytes | None = None,
        index_file: Path | None = None) -> bytes:
    env = {key: value for key, value in os.environ.items()
           if not key.upper().startswith("GIT_")}
    env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_TERMINAL_PROMPT": "0"})
    if index_file is not None:
        env["GIT_INDEX_FILE"] = str(index_file.absolute())
    result = subprocess.run(
        ["git", "-c", "core.hooksPath=" + os.devnull, "-c", "core.autocrlf=false",
         "-c", "core.fsmonitor=false", "-C", str(root), *args],
        capture_output=True, timeout=timeout, check=False, shell=False, env=env, input=input_data,
    )
    if result.returncode:
        raise AssetSafetyError("git_operation_failed:" + args[0])
    return result.stdout


def check_target(root: Path, protected_paths: tuple[Path, ...] = ()) -> Path:
    no_links(root)
    root = root.resolve(strict=True)
    for protected in (FROZEN_MAINLINE, SWARM_SOURCE, *protected_paths):
        if root == protected.resolve() or root.is_relative_to(protected.resolve()):
            raise AssetSafetyError("protected_target")
    if Path(git(root, "rev-parse", "--show-toplevel").decode().strip()).resolve() != root:
        raise AssetSafetyError("target_must_be_worktree_root")
    branch = git(root, "symbolic-ref", "--short", "HEAD").decode().strip()
    if branch in PROTECTED_BRANCHES:
        raise AssetSafetyError("protected_branch")
    return root
