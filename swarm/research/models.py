"""Trusted host configuration, never populated from MCP tool arguments."""
from pathlib import Path

from pydantic import Field
from contracts.base import Contract
from contracts.identity import AgentId
from swarm.models import Locality


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

    def knowledge_path(self) -> Path:
        if self.research_knowledge_path is not None:
            path = Path(self.research_knowledge_path)
            if not path.is_absolute():
                raise ValueError("research_knowledge_path_must_be_absolute")
            return path
        return Path(self.ledger_path).resolve().with_name("research-knowledge.sqlite3")

    def locality(self) -> Locality:
        return Locality(workspace=self.workspace, authorized_scopes=self.authorized_scopes)
