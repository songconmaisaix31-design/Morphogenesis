"""Identity materialization around the shared T0 supply record."""

from pydantic import Field, model_validator

from contracts.base import Contract
from contracts.identity import AgentId, AttemptId, Role
from contracts.runtime import Provision


class IdentityBinding(Contract):
    """One internal Role -> AgentId -> AttemptId mapping."""

    role: Role
    agent_id: AgentId
    attempt_id: AttemptId

    @model_validator(mode="after")
    def validate_chain(self) -> "IdentityBinding":
        if self.agent_id.role != self.role:
            raise ValueError("binding role must match agent_id.role")
        if self.attempt_id.agent != self.agent_id:
            raise ValueError("attempt_id.agent must match agent_id")
        return self


class ProvisionedSwarm(Contract):
    """A provision record plus locally materialized identity mappings."""

    provision: Provision
    bindings: list[IdentityBinding] = Field(min_length=1)
    external_ids: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_members(self) -> "ProvisionedSwarm":
        expected = set(self.provision.members)
        actual = {binding.agent_id for binding in self.bindings}
        if actual != expected:
            raise ValueError("identity bindings must cover exactly the provision members")
        return self
