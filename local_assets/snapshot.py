"""Native Git scoped snapshots without modifying refs, user index or worktree."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile

from local_assets.models import AssetSafetyError, Candidate
from local_assets.paths import check_target, git, no_links, relative_path, safe_join


def scope_tree(repository: Path, scope: str, scratch_directory: Path) -> tuple[str, str]:
    """Capture only the leased scope's delta on HEAD in an alternate index.

    Caller holds the runtime scope lease. No git add/commit/ref update occurs;
    immutable native blobs/trees are the entire snapshot mechanism.
    """
    repository = check_target(repository)
    scope = relative_path(scope, allow_root=True)
    no_links(scratch_directory)
    scratch_directory.mkdir(parents=True, exist_ok=True)
    head = git(repository, "rev-parse", "HEAD").decode().strip()
    pathspec = ":(literal)" + ("" if scope == "." else scope)
    changed = git(repository, "diff", "--name-only", "-z", head, "--", pathspec)
    untracked = git(repository, "ls-files", "--others", "--exclude-standard", "-z", "--", pathspec)
    paths = sorted({name.decode("utf-8") for name in (changed + untracked).split(b"\0") if name})
    if len(paths) > 2000:
        raise AssetSafetyError("snapshot_file_limit")
    entries = git(repository, "ls-tree", "-rz", head, "--", pathspec)
    modes: dict[str, str] = {}
    for entry in entries.split(b"\0"):
        if entry:
            header, raw_name = entry.split(b"\t", 1)
            modes[raw_name.decode("utf-8")] = header.split()[0].decode()
    observed: dict[Path, bytes | None] = {}
    total = 0
    with tempfile.TemporaryDirectory(prefix="scope-index-", dir=scratch_directory) as temporary:
        index = Path(temporary) / "index"
        git(repository, "read-tree", head, index_file=index)
        updates: list[bytes] = []
        for name in paths:
            path = safe_join(repository, name)
            if path.is_dir():
                raise AssetSafetyError("snapshot_directory_or_submodule")
            body = path.read_bytes() if path.is_file() else None
            observed[path] = body
            if body is None:
                updates.append(("0 " + "0" * len(head) + "\t" + name).encode() + b"\0")
                continue
            total += len(body)
            if total > 64 * 1024 * 1024:
                raise AssetSafetyError("snapshot_byte_limit")
            mode = modes.get(name, "100755" if os.name != "nt" and path.stat().st_mode & 0o111 else "100644")
            if mode not in {"100644", "100755"}:
                raise AssetSafetyError("snapshot_links_or_submodules")
            blob = git(repository, "hash-object", "-w", "--stdin", input_data=body).decode().strip()
            updates.append((mode + " " + blob + "\t" + name).encode() + b"\0")
        if updates:
            git(repository, "update-index", "-z", "--index-info", input_data=b"".join(updates), index_file=index)
        tree = git(repository, "write-tree", index_file=index).decode().strip()
    if git(repository, "rev-parse", "HEAD").decode().strip() != head:
        raise AssetSafetyError("snapshot_head_changed")
    if (git(repository, "diff", "--name-only", "-z", head, "--", pathspec) != changed
            or git(repository, "ls-files", "--others", "--exclude-standard", "-z", "--", pathspec) != untracked):
        raise AssetSafetyError("snapshot_paths_changed")
    for path, expected in observed.items():
        no_links(path)
        if (path.read_bytes() if path.is_file() else None) != expected:
            raise AssetSafetyError("snapshot_bytes_changed")
    return tree, head


def snapshot_revision(repository: Path | str, scope: str,
                      scratch_directory: Path | str) -> tuple[str, str]:
    """Return (unreferenced snapshot commit, anchored target HEAD)."""
    repository = Path(repository)
    tree, head = scope_tree(repository, scope, Path(scratch_directory))
    commit = git(
        repository, "-c", "user.name=Local Swarm", "-c", "user.email=local-swarm@example.invalid",
        "commit-tree", tree, "-p", head, "-m", "Local scoped validation snapshot; no branch update",
    ).decode().strip()
    return commit, head


def check_snapshot(repository: Path, candidate: Candidate, scratch_directory: Path) -> None:
    """Reconstruct scoped tree under lease, preventing stale snapshot promotion."""
    if candidate.base_head is None:
        return
    parent = git(repository, "rev-parse", candidate.base_revision + "^").decode().strip()
    if parent != candidate.base_head:
        raise AssetSafetyError("snapshot_parent_mismatch")
    tree, head = scope_tree(repository, candidate.scope, scratch_directory)
    baseline_tree = git(repository, "rev-parse", candidate.base_revision + "^{tree}").decode().strip()
    if head != candidate.base_head or tree != baseline_tree:
        raise AssetSafetyError("snapshot_target_changed")
