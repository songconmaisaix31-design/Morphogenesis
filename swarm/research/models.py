"""Trusted host configuration, never populated from MCP tool arguments."""
from pathlib import Path
from typing import Literal

from pydantic import Field, JsonValue, model_validator
from contracts.base import Contract
from contracts.identity import AgentId
from swarm.models import BudgetPolicy, ExecutionBound, Locality, RunLimits


class ResearchEnvelope(Contract):
    """Operator-approved research scope, never an MCP argument or a spending grant."""

    goal: str = Field(min_length=1)
    allowed_domains: tuple[str, ...] = ()
    data_bounds: dict[str, str] = Field(default_factory=dict)
    actions: tuple[Literal["read", "note", "branch", "propose", "choose", "claim", "review", "experiment", "apply"], ...] = (
        "read", "note", "branch", "propose", "choose", "claim", "review")
    limits: RunLimits = Field(default_factory=RunLimits)


class HostConfig(Contract):
    ledger_path: str
    swarm_id: str = Field(min_length=1)
    workspace: str
    worker_id: str = Field(min_length=1)
    agent: AgentId
    authorized_scopes: tuple[str, ...] = Field(min_length=1)
    capabilities: tuple[str, ...] = Field(min_length=1)
    assets_root: str
    evidence_root: str
    project_context: str = ""
    experiment_backend: dict[str, str] = Field(default_factory=dict)
    max_experiments_per_task: int = Field(default=1, ge=1, le=10, strict=True)
    # Research-plane authorization references. These are host-supplied and are
    # never accepted from MCP tool arguments; project knowledge is persistent
    # across branches/runs and is not reset by creating a new branch or run.
    project_id: str = ""
    authorization_ref: str | None = None
    research_knowledge_path: str | None = None
    research_envelope: ResearchEnvelope | None = None
    research_provenance: Literal["contract_local", "mock", "live"] = "contract_local"
    research_budget_path: str | None = None
    research_budget_policy: BudgetPolicy | None = None
    research_execution_bound: ExecutionBound | None = None
    # Validated by the closed GeneratedHostSettings contract on service creation.
    # Keeping the import lazy preserves SDK-free non-execution member tools.
    generated_experiments: dict[str, JsonValue] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _project_binding(self) -> "HostConfig":
        if self.project_id and not self.project_id.strip():
            raise ValueError("project_id_must_be_a_non_empty_identifier")
        if self.research_envelope is not None and (not self.project_id or not self.authorization_ref):
            raise ValueError("research_envelope_requires_host_project_and_authorization")
        budget_values = (self.research_budget_path, self.research_budget_policy, self.research_execution_bound)
        if any(value is not None for value in budget_values):
            if not all(value is not None for value in budget_values) or self.research_envelope is None:
                raise ValueError("research_budget_requires_complete_host_binding")
            if self.research_budget_path is None or not Path(self.research_budget_path).is_absolute():
                raise ValueError("research_budget_path_must_be_absolute")
            if self.research_budget_policy is not None and self.research_budget_policy.limits != self.research_envelope.limits:
                raise ValueError("research_budget_and_ledger_limits_must_match")
        if self.generated_experiments and (self.research_envelope is None or self.research_budget_policy is None):
            raise ValueError("generated_experiments_require_host_envelope_and_budget")
        return self

    def knowledge_path(self) -> Path:
        if self.research_knowledge_path is not None:
            path = Path(self.research_knowledge_path)
            if not path.is_absolute():
                raise ValueError("research_knowledge_path_must_be_absolute")
            return path
        return Path(self.ledger_path).resolve().with_name("research-knowledge.sqlite3")

    def locality(self) -> Locality:
        return Locality(workspace=self.workspace, authorized_scopes=self.authorized_scopes)
