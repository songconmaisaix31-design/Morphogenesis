"""Business identities only. AttemptId has no scheduler or lifecycle behavior."""

from typing import Literal

from pydantic import Field

from contracts.base import Contract

Role = Literal["planner", "builder", "reviewer", "aggregator"]


class AgentId(Contract):
    role: Role
    instance: int = Field(ge=0)


class AttemptId(Contract):
    task_id: str = Field(min_length=1)
    agent: AgentId
    attempt: int = Field(ge=0)
