"""Local validation inputs and observations; GEP wire schemas stay in the SDK."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Literal, Protocol

from pydantic import Field

from contracts.base import Contract
from contracts.identity import AttemptId


class FileChange(Contract):
    path: str
    before: str | None
    after: str | None


class Candidate(Contract):
    attempt: AttemptId
    base_revision: str = Field(pattern=r"^[a-f0-9]{40,64}$")
    base_head: str | None = Field(default=None, pattern=r"^[a-f0-9]{40,64}$")
    changes: tuple[FileChange, ...] = Field(min_length=1, max_length=64)
    declared_files: int = Field(ge=1, le=64)
    declared_lines: int = Field(ge=0, le=100000)
    scope: str = "."
    summary: str = "Local quarantined candidate; validation pending"


class EnvironmentFingerprint(Contract):
    node_version: str
    arch: str
    platform: str
    python_version: str


class CommandResult(Contract):
    argv: tuple[str, ...]
    exit_code: int | None
    timed_out: bool = False
    output_limited: bool = False


class ValidationReport(Contract):
    report_id: str
    asset_id: str
    attempt: AttemptId
    base_revision: str
    candidate_json: str
    passed: bool
    reasons: tuple[str, ...]
    actual_files: int
    actual_lines: int
    env_fingerprint: EnvironmentFingerprint
    commands: tuple[CommandResult, ...] = ()
    worktree_path: str | None = None
    created_at: float
    expires_at: float
    isolation: Literal["git_worktree_not_os_sandbox"] = "git_worktree_not_os_sandbox"


class PromotionReceipt(Contract):
    asset_id: str
    report_id: str
    target: str
    paths: tuple[str, ...]
    promoted_at: float


class LeaseGuard(Protocol):
    """Runtime holds its atomic lease lock and checks ownership until exit.

    The supplied scope is the absolute target scope. The yielded callable must
    raise when TTL/ownership is invalid; a boolean-only check is insufficient.
    """

    def __call__(self, scope: str) -> AbstractContextManager[Callable[[], None]]: ...


class AssetSafetyError(ValueError):
    """A local candidate remains quarantined when this exception is raised."""
