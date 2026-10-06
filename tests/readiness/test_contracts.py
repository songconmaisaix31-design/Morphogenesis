"""Readiness contract rules: observations are required and coverage is never assumed."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from contracts.readiness import (
    READINESS_SCHEMA,
    SUBJECTS,
    EnvironmentReport,
    ProbeResult,
    ProbeState,
    ProbeSubject,
    dimension_states,
    overall_state,
)


def observation(probe_id: str, subject: ProbeSubject, state: ProbeState) -> ProbeResult:
    return ProbeResult(
        probe_id=probe_id,
        subject=subject,
        state=state,
        observed=state != "not_run",
    )


def build(results: list[ProbeResult]) -> EnvironmentReport:
    dimensions = dimension_states(results)
    return EnvironmentReport(
        generated_at=0.0,
        overall=overall_state(dimensions),
        dimensions=dimensions,
        results=results,
    )


def test_schema_version_is_the_single_served_identity() -> None:
    assert READINESS_SCHEMA == "morph.readiness/1"
    assert build([]).schema_version == READINESS_SCHEMA


def test_not_run_cannot_claim_an_observation() -> None:
    with pytest.raises(ValidationError):
        ProbeResult(probe_id="machine:host", subject="machine", state="not_run", observed=True)


@pytest.mark.parametrize("state", ["ok", "degraded", "blocked", "failed"])
def test_any_other_state_requires_a_real_observation(state: str) -> None:
    with pytest.raises(ValidationError):
        ProbeResult(probe_id="machine:host", subject="machine", state=state, observed=False)


def test_evidence_values_are_bounded() -> None:
    with pytest.raises(ValidationError):
        ProbeResult(
            probe_id="machine:host", subject="machine", state="ok", observed=True,
            evidence={"output": "x" * 201},
        )


def test_dimensions_cover_every_subject_even_when_nothing_was_probed() -> None:
    report = build([])
    assert report.dimensions == {subject: "not_run" for subject in SUBJECTS}
    assert report.overall == "not_run"


def test_one_healthy_subject_is_degraded_not_ok() -> None:
    report = build([observation("machine:host", "machine", "ok")])
    assert report.dimensions == {"machine": "ok", "interface": "not_run", "account": "not_run"}
    assert report.overall == "degraded"


def test_only_full_coverage_can_be_ok() -> None:
    results = [observation(f"p:{subject}", subject, "ok") for subject in SUBJECTS]
    assert build(results).overall == "ok"


@pytest.mark.parametrize(
    "states,expected",
    [
        (["ok", "degraded", "ok"], "degraded"),
        (["ok", "blocked", "degraded"], "blocked"),
        (["failed", "blocked", "ok"], "failed"),
        (["ok", "ok", "not_run"], "degraded"),
        (["not_run", "not_run", "not_run"], "not_run"),
    ],
)
def test_worst_state_decides_and_uncovered_subjects_degrade(states: list[str], expected: str) -> None:
    results = [
        observation(f"p:{subject}", subject, state)  # type: ignore[arg-type]
        for subject, state in zip(SUBJECTS, states)
    ]
    assert build(results).overall == expected


def test_report_rejects_dimensions_that_disagree_with_its_results() -> None:
    with pytest.raises(ValidationError):
        EnvironmentReport(
            overall="ok",
            dimensions={"machine": "ok", "interface": "ok", "account": "ok"},
            results=[observation("machine:host", "machine", "ok")],
        )


def test_report_rejects_a_duplicated_probe_id() -> None:
    with pytest.raises(ValidationError):
        build([
            observation("machine:host", "machine", "ok"),
            observation("machine:host", "interface", "ok"),
        ])
