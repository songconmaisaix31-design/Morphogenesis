from enum import Enum
from typing import Literal, Self

from pydantic import Field, JsonValue, model_validator

from contracts.base import Contract
from contracts.identity import AgentId, AttemptId
from contracts.provenance import Provenance


class MsgType(str, Enum):
    INTENT = "intent"
    RESULT = "result"
    SIGNAL = "signal"


class Envelope(Contract):
    run_id: str = Field(min_length=1)
    msg_id: str = Field(min_length=1)
    msg_type: MsgType
    sender: AgentId
    receiver: AgentId | Literal["broadcast"]
    task_id: str = Field(min_length=1)
    attempt: AttemptId
    artifact_uri: str | None = None
    seq: int = Field(ge=0)
    handled: bool = False
    provenance: Provenance = "live"
    original_run_uri: str | None = None
    ts: float = Field(ge=0)
    payload: dict[str, JsonValue] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_lineage(self) -> Self:
        if self.task_id != self.attempt.task_id:
            raise ValueError("Envelope.task_id must match attempt.task_id")
        if self.provenance == "replay" and not self.original_run_uri:
            raise ValueError("replay requires original_run_uri")
        return self
