from typing import Literal, Self

from pydantic import Field, model_validator

from contracts.base import Contract
from contracts.identity import AgentId, AttemptId
from contracts.provenance import Acceptance, Provenance

TaskStatus = Literal[
    "succeeded", "failed", "interrupted", "pending_review", "insufficient_evidence"
]


class Verification(Contract):
    passed: bool | None = None
    reviewer: AgentId | None = None
    evidence: list[str] = Field(default_factory=list)
    command: list[str] = Field(default_factory=list)
    exit_code: int | None = None
    summary: str = "Not verified"

    @model_validator(mode="after")
    def validate_pass(self) -> Self:
        if self.passed is True and (
            self.reviewer is None or not self.evidence or self.exit_code != 0
        ):
            raise ValueError("passed verification requires reviewer, evidence and exit_code=0")
        if self.passed is False and self.exit_code == 0:
            raise ValueError("failed verification cannot have exit_code=0")
        return self


class Usage(Contract):
    """None means unreported/unknown, distinct from a measured zero."""

    tokens: int | None = Field(default=None, ge=0)
    cost_usd: float | None = Field(default=None, ge=0)


class TaskResult(Contract):
    run_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    attempt: AttemptId
    status: TaskStatus
    verdict: Verification = Field(default_factory=Verification)
    artifact_uri: str | None = None
    provenance: Provenance = "live"
    original_run_uri: str | None = None
    acceptance: Acceptance = Field(default_factory=Acceptance)
    usage: Usage = Field(default_factory=Usage)

    @model_validator(mode="after")
    def validate_result(self) -> Self:
        if self.task_id != self.attempt.task_id:
            raise ValueError("TaskResult.task_id must match attempt.task_id")
        if self.acceptance.provenance != self.provenance:
            raise ValueError("result and acceptance provenance must match")
        if self.provenance == "replay" and not self.original_run_uri:
            raise ValueError("replay requires original_run_uri")
        if self.provenance == "replay" and self.original_run_uri != self.acceptance.original_run_uri:
            raise ValueError("result and acceptance original_run_uri must match")
        if self.verdict.passed is True and self.verdict.reviewer == self.attempt.agent:
            raise ValueError("executor cannot independently verify its own work")
        if self.status == "succeeded" and (
            self.verdict.passed is not True or not self.artifact_uri
        ):
            raise ValueError("succeeded requires independent passing verdict and artifact")
        if self.acceptance.task_live == "passed" and self.status != "succeeded":
            raise ValueError("task_live passed requires succeeded result")
        return self
