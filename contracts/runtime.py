from pathlib import PurePosixPath, PureWindowsPath
from typing import Literal, Self

from pydantic import Field, model_validator

from contracts.base import Contract
from contracts.identity import AgentId
from contracts.provenance import Provenance

StopReason = Literal["achieved", "budget_exhausted", "no_progress", "manual", "unknown_effect"]


class RunConfig(Contract):
    run_id: str = Field(min_length=1)
    workspace: str = Field(min_length=1)
    writable_paths: list[str] = Field(min_length=1)
    max_tokens: int = Field(default=20000, gt=0)
    max_cost_usd: float = Field(default=1.0, gt=0)
    max_retries: int = Field(default=1, ge=0)
    no_progress_limit: int = Field(default=2, ge=1)
    timeout_seconds: float = Field(default=120, gt=0)
    gene_budget: int = Field(default=3, ge=0)
    publication_approval_required: Literal[True] = True
    unknown_usage_policy: Literal["stop"] = "stop"

    @model_validator(mode="after")
    def validate_paths(self) -> Self:
        for path in self.writable_paths:
            posix, windows = PurePosixPath(path), PureWindowsPath(path)
            if not path or posix.is_absolute() or windows.drive or windows.root:
                raise ValueError("writable_paths must be relative to workspace")
            if ".." in posix.parts or ".." in windows.parts:
                raise ValueError("writable_paths cannot traverse parents")
        return self


class Provision(Contract):
    provision_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    source: Literal["fixed", "orca"] = "fixed"
    requested: int = Field(ge=1)
    members: list[AgentId] = Field(min_length=1)
    quota: int | None = Field(default=None, ge=0)
    provenance: Provenance = "live"
    external_ids: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_members(self) -> Self:
        if len(set(self.members)) != len(self.members):
            raise ValueError("provision members must be unique")
        if len(self.members) > self.requested:
            raise ValueError("provisioned members exceed requested count")
        if self.quota is not None and len(self.members) > self.quota:
            raise ValueError("provisioned members exceed declared quota")
        return self
