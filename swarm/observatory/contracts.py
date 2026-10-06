"""Readiness contract: what this deployment can observe about itself.

The observatory has to answer three independent questions about *any* machine it
is deployed on, not about the machine it was developed on:

``machine``
    The host this process actually runs on: OS, Python, CPU, scratch space.
``interface``
    Whether one *declared* integration surface answers: a public CLI, an MCP
    server, or the local Wayfinder agent.
``account``
    Whether the identity or credential a declared surface needs is present.
    Presence only — values are never read into a report.

Vocabulary: ``not_run`` | ``ok`` | ``degraded`` | ``blocked`` | ``failed``.

``not_run`` means "nothing was declared here", never "it works".  Every other
state must come from a real observation, and the declared provider set is *data*
(a manifest), so a fresh deployment starts empty instead of inheriting this
machine's wiring.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Literal, Protocol, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

READINESS_SCHEMA: Literal["observatory.readiness/1"] = "observatory.readiness/1"

ProviderSubject = Literal["machine", "interface", "account"]
SUBJECTS: tuple[ProviderSubject, ...] = ("machine", "interface", "account")

ProviderState = Literal["not_run", "ok", "degraded", "blocked", "failed"]

ProviderKind = Literal["host", "cli", "mcp", "wayfinder", "credential"]

#: Severity used to fold several observations of one subject. ``not_run`` sits
#: above ``ok`` so a provider that did not execute cannot be hidden by one that
#: did; a subject with no observation at all falls back to ``not_run``.
_SEVERITY: Mapping[ProviderState, int] = {
    "ok": 0, "not_run": 1, "degraded": 2, "blocked": 3, "failed": 4,
}

MAX_DETAIL = 200
MAX_EVIDENCE_VALUE = 200


class _Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class ProbeResult(_Contract):
    """One bounded observation, from one declared provider."""

    provider_id: str = Field(min_length=1, max_length=64)
    subject: ProviderSubject
    state: ProviderState = "not_run"
    observed: bool = False
    detail: str = Field(default="", max_length=MAX_DETAIL)
    evidence: dict[str, str] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_observation(self) -> Self:
        for value in self.evidence.values():
            if len(value) > MAX_EVIDENCE_VALUE:
                raise ValueError("evidence values must stay short")
        if self.state == "not_run":
            if self.observed:
                raise ValueError("not_run cannot claim an observation")
            return self
        if not self.observed:
            raise ValueError("a state other than not_run requires a real observation")
        return self


def dimension_states(results: Sequence[ProbeResult]) -> dict[ProviderSubject, ProviderState]:
    """Worst state per subject; every subject is present, uncovered as not_run."""
    observed: dict[ProviderSubject, ProviderState] = {}
    for result in results:
        current = observed.get(result.subject)
        if current is None or _SEVERITY[result.state] > _SEVERITY[current]:
            observed[result.subject] = result.state
    return {subject: observed.get(subject, "not_run") for subject in SUBJECTS}


def overall_state(dimensions: Mapping[ProviderSubject, ProviderState]) -> ProviderState:
    """One verdict that never overstates coverage.

    * nothing observed at all -> ``not_run``
    * any ``failed`` -> ``failed``; else any ``blocked`` -> ``blocked``
    * any ``degraded`` or any uncovered subject -> ``degraded``
    * ``ok`` requires all three subjects covered and healthy
    """
    values = [dimensions[subject] for subject in SUBJECTS]
    if all(value == "not_run" for value in values):
        return "not_run"
    for state in ("failed", "blocked", "degraded"):
        if state in values:
            return state
    if "not_run" in values:
        return "degraded"
    return "ok"


class EnvironmentReport(_Contract):
    """The three-dimension verdict plus the observations behind it.

    ``dimensions`` and ``overall`` are recomputed by the validator, so a report
    can never disagree with its own evidence.
    """

    schema_version: str = READINESS_SCHEMA
    generated_at: float | None = None
    overall: ProviderState = "not_run"
    dimensions: dict[ProviderSubject, ProviderState]
    results: list[ProbeResult] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_aggregate(self) -> Self:
        expected = dimension_states(self.results)
        if dict(self.dimensions) != expected:
            raise ValueError("dimensions must be derived from results")
        if self.overall != overall_state(expected):
            raise ValueError("overall must be derived from dimensions")
        ids = [result.provider_id for result in self.results]
        if len(set(ids)) != len(ids):
            raise ValueError("provider_id must be unique within a report")
        return self


class Provider(Protocol):
    """One declared way to observe readiness.

    Intentionally transport-free: a provider may read the local machine, run a
    declared public CLI, speak MCP, or drive the local Wayfinder agent.  An empty
    provider set is a valid deployment state that must report ``not_run`` rather
    than a default verdict.
    """

    @property
    def provider_id(self) -> str: ...

    @property
    def subject(self) -> ProviderSubject: ...

    @property
    def kind(self) -> ProviderKind: ...

    @property
    def label(self) -> str: ...

    def probe(self) -> ProbeResult: ...
