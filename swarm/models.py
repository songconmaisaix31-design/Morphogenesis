"""Shared swarm data contracts. Attempt identity remains contracts.identity.AttemptId."""

from __future__ import annotations

from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

SignalKind = Literal["error_pattern", "timeout_storm", "retry_flood", "opportunity"]
TaskKind = Literal["repair", "optimize", "innovation"]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True, allow_inf_nan=False)


class Locality(Model):
    workspace: str = Field(min_length=1)
    authorized_scopes: tuple[str, ...] = Field(default=(), max_length=64)
    modules: tuple[str, ...] = Field(default=(), max_length=64)
    dependency_of: tuple[str, ...] = Field(default=(), max_length=64)
    # Compatibility display metadata only, never authorization or locality.
    x: float = 0.0
    y: float = 0.0
    radius: float = Field(default=1.0, ge=0)


class Signal(Model):
    signal_id: str = Field(default_factory=lambda: uuid4().hex)
    task_id: str = Field(min_length=1)
    workspace: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    kind: SignalKind
    payload: dict[str, JsonValue] = Field(default_factory=dict)
    x: float = 0.0
    y: float = 0.0
    concentration: float = Field(default=1.0, ge=0, le=1e12)
    urgency: float = Field(default=1.0, ge=0, le=1e6)
    required_capability: str = ""
    module: str = ""
    updated_at: float = Field(default=0.0, ge=0)
    decay_multiplier: float = Field(default=1.0, ge=1, le=1e6)
    completed: bool = False

    @property
    def task_kind(self) -> TaskKind:
        if self.kind == "error_pattern":
            return "repair"
        if self.kind == "opportunity":
            return "innovation"
        return "optimize"


class PipeHistory(Model):
    worker_id: str
    pipe_key: str
    weight: float = Field(default=0.25, ge=0, le=1)
    samples: int = Field(default=0, ge=0)


class Lease(Model):
    task_id: str
    swarm_id: str
    scope: str
    worker_id: str
    token: int = Field(gt=0, strict=True)
    expires_at: float


class RunLimits(Model):
    max_tasks: int = Field(default=1000, gt=0, le=100000, strict=True)
    max_attempts: int = Field(default=10000, gt=0, le=1000000, strict=True)
    max_attempts_per_task: int = Field(default=3, gt=0, le=100, strict=True)
    max_derived_tasks: int = Field(default=100, ge=0, le=100000, strict=True)
    max_runtime_seconds: float = Field(default=3600.0, gt=0)


class TaskRecord(Model):
    swarm_id: str
    signal: Signal
    status: Literal["available", "claimed", "submitting", "partial", "handoff", "completed", "failed", "blocked"]
    dependencies: tuple[str, ...] = ()
    acceptance: dict[str, JsonValue] = Field(default_factory=dict)
    attempts: int = 0
    condition_fail_count: int = Field(default=0, ge=0)
    token: int = 0
    owner: str | None = None
    expires_at: float | None = None
    created_at: float
    updated_at: float
    derived_from: str | None = None
    result_id: str | None = None
    result: dict[str, JsonValue] | None = None
    effect_applied: bool = False


class ModelPrices(Model):
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    input_usd_per_million: float = Field(ge=0)
    output_usd_per_million: float = Field(ge=0)


class BudgetPolicy(Model):
    max_tokens: int = Field(default=20000, gt=0, strict=True)
    max_cost_usd: float = Field(gt=0)
    burn_rate_tokens: int = Field(default=20000, gt=0, strict=True)
    burn_window_seconds: float = Field(default=60.0, gt=0)
    prices: ModelPrices | None = None
    limits: RunLimits = Field(default_factory=RunLimits)
    admission_control: Literal["enabled", "disabled"] = "enabled"
    # Operator allowance, never a provider price or a contractual request ceiling.
    unbounded_reservation_usd: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def unbounded_requires_admission(self) -> BudgetPolicy:
        if self.unbounded_reservation_usd is not None and self.admission_control != "enabled":
            raise ValueError("unbounded allowance requires enabled admission control")
        return self


class ExecutionBound(Model):
    provider: str
    model: str
    input_tokens: int = Field(ge=0, strict=True)
    max_output_tokens: int = Field(ge=0, strict=True)
    provider_enforced: bool = False
    request_bound: Literal["verified", "unbounded"] = "unbounded"
    max_cost_usd: float | None = Field(default=None, ge=0)
    bound_evidence: str | None = None

    @model_validator(mode="after")
    def credible_bound(self) -> ExecutionBound:
        if self.request_bound == "verified" and (
            not self.provider_enforced or self.max_cost_usd is None or
            not self.bound_evidence or not self.bound_evidence.strip()
        ):
            raise ValueError("verified request bound requires contractual cost and executor evidence")
        return self


class Reservation(Model):
    reservation_id: str
    request_id: str
    swarm_id: str
    worker_id: str
    task_id: str
    bound: ExecutionBound
    reserved_estimate_usd: float
    created_at: float
    usage_metering: Literal["verified", "unknown"] = "unknown"
    request_bound: Literal["verified", "unbounded"] = "unbounded"
    admission_control: Literal["enabled", "disabled"] = "enabled"
    cost: Literal["estimated", "billed", "unknown"] = "unknown"


class BudgetSnapshot(Model):
    swarm_id: str
    sleeping: bool
    reason: str | None = None
    sleep_seconds: float = 0.0
    tokens: int | None
    estimated_cost_usd: float | None
    actual_cost_usd: float | None = None
    reserved_estimate_usd: float
    uncertain_reservations: int
    pending_reservations: int
    usage_metering: Literal["verified", "unknown"] = "unknown"
    request_bound: Literal["verified", "unbounded"] = "unbounded"
    admission_control: Literal["enabled", "disabled"] = "enabled"
    cost: Literal["estimated", "billed", "unknown"] = "unknown"
    admission_charged_usd: float = 0.0
    unreconciled_reservations: int = 0
