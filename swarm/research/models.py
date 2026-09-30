"""Trusted host configuration, never populated from MCP tool arguments."""
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

    def locality(self) -> Locality:
        return Locality(workspace=self.workspace, authorized_scopes=self.authorized_scopes)
