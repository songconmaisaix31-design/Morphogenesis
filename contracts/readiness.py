"""Readiness vocabulary: can this deployment actually work here, right now.

Readiness answers three independent questions and nothing else:

``machine``
    What host is this process running on, as observed locally.
``interface``
    Whether one declared integration surface (a public CLI, an MCP server)
    answers.  The surface must be declared by configuration; none is assumed.
``account``
    Whether an identity or credential that an integration needs is present.
    Presence only: values are never read into a report.

This is deliberately *not* the run-evidence model.  A probe never establishes
``contract_local`` / ``interface_live`` / ``task_live``, and ``not_run`` means
"no probe was wired", never "the external system passed".  A state other than
``not_run`` therefore requires a real observation, enforced below.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Literal, Self

from pydantic import Field, model_validator

from contracts.base import Contract

ReadinessSchema = Literal["morph.readiness/1"]
READINESS_SCHEMA: ReadinessSchema = "morph.readiness/1"

ProbeSubject = Literal["machine", "interface", "account"]
SUBJECTS: tuple[ProbeSubject, ...] = ("machine", "interface", "account")

ProbeState = Literal["not_run", "ok", "degraded", "blocked", "failed"]

#: Severity order used to fold several observations of one subject. ``not_run``
#: sits above ``ok`` so a probe that did not execute cannot be hidden by one
#: that did, and a subject with no result at all falls back to ``not_run``.
_SEVERITY: Mapping[ProbeState, int] = {
    "ok": 0, "not_run": 1, "degraded": 2, "blocked": 3, "failed": 4,
}

MAX_DETAIL = 200
MAX_PROBE_ID = 64
MAX_EVIDENCE_VALUE = 200


class ProbeResult(Contract):
    """One bounded observation by one named probe."""

    probe_id: str = Field(min_length=1, max_length=MAX_PROBE_ID)
    subject: ProbeSubject
    state: ProbeState = "not_run"
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


def dimension_states(results: Sequence[ProbeResult]) -> dict[ProbeSubject, ProbeState]:
    """Worst state per subject; every subject is present, uncovered as not_run."""
    observed: dict[ProbeSubject, ProbeState] = {}
    for result in results:
        current = observed.get(result.subject)
        if current is None or _SEVERITY[result.state] > _SEVERITY[current]:
            observed[result.subject] = result.state
    return {subject: observed.get(subject, "not_run") for subject in SUBJECTS}


def overall_state(dimensions: Mapping[ProbeSubject, ProbeState]) -> ProbeState:
    """One verdict that never overstates coverage.

    * nothing probed at all -> ``not_run``
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


class EnvironmentReport(Contract):
    """The three-dimension verdict plus the individual observations behind it.

    ``dimensions`` and ``overall`` are recomputed by the validator, so a report
    can never disagree with its own evidence.
    """

    schema_version: ReadinessSchema = READINESS_SCHEMA
    generated_at: float | None = None
    overall: ProbeState = "not_run"
    dimensions: dict[ProbeSubject, ProbeState]
    results: list[ProbeResult] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_aggregate(self) -> Self:
        expected = dimension_states(self.results)
        if dict(self.dimensions) != expected:
            raise ValueError("dimensions must be derived from results")
        if self.overall != overall_state(expected):
            raise ValueError("overall must be derived from dimensions")
        ids = [result.probe_id for result in self.results]
        if len(set(ids)) != len(ids):
            raise ValueError("probe_id must be unique within a report")
        return self
