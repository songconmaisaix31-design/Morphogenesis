"""Shared rehearsal presentation data; no scheduler or additional attempt system.

The fixed logical member pool loses a member BETWEEN tasks. This is not evidence
of recovery after killing an in-flight CLI process. Consumers import these types.
"""

from typing import Literal, Self

from pydantic import Field, model_validator

from contracts.base import Contract
from contracts.identity import AgentId, AttemptId
from contracts.protocols import PipeState
from contracts.provenance import Acceptance, Provenance
from contracts.results import TaskResult, Verification
from metabolism.models import GeneView, UseRecord

Stage = Literal[
    "task_ready", "repair_selected", "repair_reviewed", "gene_generated",
    "awaiting_offline", "member_offline", "recovery_ready", "recovery_selected",
    "recovery_reviewed", "gene_adopted", "decaying", "archived", "completed", "failed",
]
ExecutorKind = Literal["codex", "evomap"]


class Checkpoint(Contract):
    name: Literal["clamp", "mean", "unique"]
    passed: bool | None = None


class Checkpoints(Contract):
    checks: list[Checkpoint] = Field(min_length=3, max_length=3)
    passed_count: int = Field(ge=0, le=3)
    total: Literal[3] = 3
    ratio: float = Field(ge=0, le=1)
    verification: Verification
    provenance: Provenance

    @model_validator(mode="after")
    def true_count(self) -> Self:
        if {check.name for check in self.checks} != {"clamp", "mean", "unique"}:
            raise ValueError("exactly the three fixed checkpoints are required")
        if self.passed_count != sum(check.passed is True for check in self.checks):
            raise ValueError("count must come from checkpoint verdicts")
        if self.ratio != self.passed_count / self.total:
            raise ValueError("ratio must come from checkpoint verdicts")
        if self.passed_count == 3 and self.verification.passed is not True:
            raise ValueError("3/3 requires completed independent verification")
        return self


class MemberAvailability(Contract):
    agent: AgentId
    available: bool = True
    changed_at: float = Field(ge=0)
    reason: str = "fixed logical member"


class RoutingFact(Contract):
    task_id: str
    eligible_members: list[AgentId]
    selected_attempt: AttemptId | None = None
    removed_member: AgentId | None = None
    removed_at: float | None = None
    boundary: Literal["between_tasks"] = "between_tasks"

    @model_validator(mode="after")
    def eligible_selection(self) -> Self:
        if self.removed_member in self.eligible_members:
            raise ValueError("removed member cannot be eligible")
        if self.selected_attempt is not None and (
            self.selected_attempt.agent not in self.eligible_members
            or self.selected_attempt.task_id != self.task_id
        ):
            raise ValueError("selection must name an eligible member of this task")
        return self


class RehearsalSnapshot(Contract):
    executor: ExecutorKind = "codex"
    model: str | None = None
    sequence: int = Field(ge=0)
    stage: Stage
    at: float = Field(ge=0, description="Actual Unix wall-clock seconds")
    task_id: str
    task_description: str
    provenance: Provenance
    acceptance: Acceptance
    checkpoints: Checkpoints | None = None
    members: list[MemberAvailability]
    pipes: list[PipeState]
    routing: RoutingFact
    genes: list[GeneView] = Field(default_factory=list)
    adoptions: list[UseRecord] = Field(default_factory=list)
    results: list[TaskResult] = Field(default_factory=list)
    retrievable_gene_ids: list[str] = Field(default_factory=list)
    tau_seconds: float = Field(gt=0)
    archive_threshold: float = Field(gt=0, lt=1)
    max_model_calls: Literal[2] = 2
    model_calls_started: int = Field(ge=0, le=2)
    cost_usd: float | None = Field(default=None, ge=0)
    message: str = ""
    failure: str | None = None

    @model_validator(mode="after")
    def consistent_sources(self) -> Self:
        sources = [self.acceptance.provenance]
        if self.checkpoints:
            sources.append(self.checkpoints.provenance)
        sources.extend(item.provenance for item in self.genes)
        sources.extend(item.provenance for item in self.adoptions)
        sources.extend(item.provenance for item in self.results)
        if any(source != self.provenance for source in sources):
            raise ValueError("snapshot sources must have matching provenance")
        return self


class RehearsalDocument(Contract):
    schema_version: Literal[1] = 1
    rehearsal_id: str
    mode: Provenance
    original_run_uri: str | None = None
    current: RehearsalSnapshot
    history: list[RehearsalSnapshot] = Field(min_length=1)
    scope: Literal["fixed_pool_between_tasks"] = "fixed_pool_between_tasks"
    hub_status: Literal["pending_publish"] = "pending_publish"

    @model_validator(mode="after")
    def current_is_last(self) -> Self:
        if self.current != self.history[-1]:
            raise ValueError("current must be the last historical snapshot")
        if any(snapshot.provenance != self.mode for snapshot in self.history):
            raise ValueError("document and snapshot sources must agree")
        if self.mode == "replay" and not self.original_run_uri:
            raise ValueError("replay requires original_run_uri")
        return self
