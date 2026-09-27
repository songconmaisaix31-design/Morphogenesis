"""Bounded candidate-chain decisions and shared-breaker routing guards.

Data-only module: it holds no budget, lease or attempt authority and never
sends a request. The real FC-B/FC-C modules are consumed through structural
protocols, so the baseline runtime keeps working when they are absent, while a
composed tree gets the genuine shared store/breaker without copied code.

Red lines honored here:
- ``switched_to`` is decided by the caller only after the next candidate was
  actually admitted; this module never fabricates a switch.
- Probe outcomes are reported with the exact token the caller claimed.
- Budget-exhausted and capability-mismatch classifications are never treated
  as provider rejections; only ``confirmed_rejection`` may advance a chain.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

FailureClass = Literal[
    "confirmed_rejection", "unknown_effect", "budget_exhausted", "capability_mismatch"
]
CostState = Literal["settled", "unknown", "reserved"]

CONFIRMED_REJECTION = "confirmed_rejection"
UNKNOWN_EFFECT = "unknown_effect"
BUDGET_EXHAUSTED = "budget_exhausted"
CAPABILITY_MISMATCH = "capability_mismatch"

ChainAction = Literal[
    "switch",
    "stop_unknown_effect",
    "stop_budget_exhausted",
    "stop_capability_mismatch",
    "stop_local_failure",
    "exit_candidates_rejected",
]


class BreakerViewLike(Protocol):
    """Structural mirror of FC-C's BreakerView (field names verbatim)."""

    @property
    def provider(self) -> str: ...

    @property
    def reason(self) -> str: ...

    @property
    def state(self) -> str: ...

    @property
    def probe_token(self) -> int: ...


class SharedBreakerLike(Protocol):
    """Structural mirror of the FC-C methods the runtime consumes."""

    def views(self, *, limit: int = 1000) -> list[BreakerViewLike]: ...

    def eligible(self, provider: str, reason: str, *, worker_id: str | None = None,
                 now: float | None = None) -> bool: ...

    def try_claim_probe(self, provider: str, reason: str, worker_id: str, *,
                        now: float | None = None) -> BreakerViewLike | None: ...

    def report_probe_success(self, provider: str, reason: str, worker_id: str, *,
                             probe_token: int, now: float | None = None) -> bool: ...

    def report_probe_failure(self, provider: str, reason: str, worker_id: str, *,
                             probe_token: int, retry_after_until: float | None = None,
                             now: float | None = None) -> bool: ...

    def observe(self, store: Any, *, now: float | None = None) -> Any: ...


class FaultStoreLike(Protocol):
    """Structural mirror of the FC-B store methods the runtime consumes."""

    def append(self, observation: Any) -> bool: ...


@dataclass(frozen=True)
class ProbeClaim:
    """One probe slot this worker currently holds for (provider, reason)."""

    provider: str
    reason: str
    token: int


@dataclass(frozen=True)
class GuardResult:
    """Routing eligibility for one candidate provider.

    ``routable`` is True only when every known (provider, reason) breaker is
    either healthy or covered by one of our own probe claims. Blocked reasons
    name the facts that kept the provider from being routable.
    """

    routable: bool
    claims: tuple[ProbeClaim, ...] = ()
    blocked_reasons: tuple[str, ...] = ()


_ROUTABLE_STATES = ("insufficient_evidence", "normal")


def guard_provider(breaker: SharedBreakerLike, provider: str, worker_id: str, *,
                   now: float) -> GuardResult:
    """Evaluate one candidate provider against the shared breaker.

    Suspended breakers are probed exactly once per evaluation: the atomic
    ``try_claim_probe`` admits at most one worker network-wide. A breaker
    already in ``probing_recovery`` is routable only for its live slot owner,
    identified by worker id and fencing token.
    """
    claims: list[ProbeClaim] = []
    blocked: list[str] = []
    for view in breaker.views():
        if view.provider != provider:
            continue
        state = view.state
        if state in _ROUTABLE_STATES:
            continue
        if state == "suspended":
            claimed = breaker.try_claim_probe(provider, view.reason, worker_id, now=now)
            if claimed is None:
                blocked.append(view.reason)
            else:
                claims.append(ProbeClaim(provider, view.reason, claimed.probe_token))
            continue
        if state == "probing_recovery":
            if breaker.eligible(provider, view.reason, worker_id=worker_id, now=now):
                claims.append(ProbeClaim(provider, view.reason, view.probe_token))
            else:
                blocked.append(view.reason)
            continue
        blocked.append(view.reason)
    return GuardResult(routable=not blocked, claims=tuple(claims), blocked_reasons=tuple(blocked))


@dataclass(frozen=True)
class ChainDecision:
    """What the chain does after one classified request outcome."""

    action: ChainAction
    record_observation: bool


def decide(classification: str | None, has_later_candidate: bool) -> ChainDecision:
    """Map one failure classification to a chain action.

    Only ``confirmed_rejection`` may advance the chain, and only while a later
    candidate exists. ``None`` means a local (non-provider) failure, which is
    not recorded as a provider fault observation.
    """
    if classification == CONFIRMED_REJECTION:
        if has_later_candidate:
            return ChainDecision("switch", True)
        return ChainDecision("exit_candidates_rejected", True)
    if classification == UNKNOWN_EFFECT:
        return ChainDecision("stop_unknown_effect", True)
    if classification == BUDGET_EXHAUSTED:
        return ChainDecision("stop_budget_exhausted", True)
    if classification == CAPABILITY_MISMATCH:
        return ChainDecision("stop_capability_mismatch", True)
    return ChainDecision("stop_local_failure", False)


def candidate_identity(provider: str, model: str) -> str:
    """Stable identity string used for observation ``switched_to`` facts."""
    return f"{provider}:{model}"


class FailureObservationFact(BaseModel):
    """Data-only mirror of FC-B's FaultObservation (minus observation_id).

    The real FC-B store re-validates every field on append; replay idempotence
    is keyed by (run_id, request_id, attempt), which the runtime derives from
    the durable budget reservation identity.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    run_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    attempt: int = Field(ge=0)
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    failure_class: FailureClass
    normalized_reason: str = Field(min_length=1)
    retry_after_seconds: float | None = Field(default=None, ge=0)
    switched_to: str | None = Field(default=None, min_length=1)
    cost_state: CostState | None = None
    occurred_at: float = Field(ge=0)
    evidence_ref: str | None = None

    @model_validator(mode="after")
    def finite_cooldown(self) -> FailureObservationFact:
        if self.retry_after_seconds is not None and not math.isfinite(
            self.occurred_at + self.retry_after_seconds
        ):
            raise ValueError("nonfinite cooldown deadline")
        return self
