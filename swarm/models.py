"""Shared swarm data contracts. Attempt identity remains contracts.identity.AttemptId."""

from __future__ import annotations

from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, JsonValue

SignalKind = Literal["error_pattern", "timeout_storm", "retry_flood", "opportunity"]
TaskKind = Literal["repair", "optimize", "innovation"]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True, allow_inf_nan=False)


class Locality(Model):
    workspace: str = Field(min_length=1)
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
    scope: str
    worker_id: str
    token: str
    expires_at: float


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


class ExecutionBound(Model):
    provider: str
    model: str
    input_tokens: int = Field(ge=0, strict=True)
    max_output_tokens: int = Field(ge=0, strict=True)
    provider_enforced: bool = False


class Reservation(Model):
    reservation_id: str
    account_id: str
    worker_id: str
    task_id: str
    bound: ExecutionBound
    reserved_estimate_usd: float
    created_at: float


class BudgetSnapshot(Model):
    account_id: str
    sleeping: bool
    reason: str | None = None
    sleep_seconds: float = 0.0
    tokens: int | None
    estimated_cost_usd: float | None
    actual_cost_usd: float | None = None
    reserved_estimate_usd: float
    uncertain_reservations: int
    pending_reservations: int
