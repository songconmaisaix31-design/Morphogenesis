"""Aggregation rules: empty is not healthy, and a failing probe never propagates."""

from __future__ import annotations

from typing import Any

import pytest

from contracts.readiness import ProbeResult, ProbeSubject
from readiness.service import BOUNDARIES, ReadinessService


class CountingProbe:
    probe_id = "interface:counter"
    subject: ProbeSubject = "interface"

    def __init__(self) -> None:
        self.calls = 0

    def probe(self) -> ProbeResult:
        self.calls += 1
        return ProbeResult(probe_id=self.probe_id, subject=self.subject, state="ok", observed=True)


class ExplodingProbe:
    probe_id = "account:explode"
    subject: ProbeSubject = "account"

    def probe(self) -> ProbeResult:
        raise RuntimeError("boom")


class MismatchedProbe:
    probe_id = "interface:declared"
    subject: ProbeSubject = "interface"

    def probe(self) -> ProbeResult:
        return ProbeResult(
            probe_id="interface:other", subject="interface", state="ok", observed=True
        )


class NotAResultProbe:
    probe_id = "interface:not-a-result"
    subject: ProbeSubject = "interface"

    def probe(self) -> Any:
        return "ok"


class FakeClock:
    def __init__(self, step: float = 0.0) -> None:
        self.now = 0.0
        self.step = step

    def __call__(self) -> float:
        current = self.now
        self.now += self.step
        return current


def test_the_empty_probe_set_is_not_run_and_says_so() -> None:
    report = ReadinessService().report()
    assert report.overall == "not_run"
    assert report.results == []
    assert set(report.dimensions.values()) == {"not_run"}
    assert any("未声明任何探针" in note for note in report.notes)
    assert set(BOUNDARIES).issubset(set(report.notes))


def test_each_probe_runs_once_per_report() -> None:
    probe = CountingProbe()
    service = ReadinessService((probe,))
    service.report()
    service.report()
    assert probe.calls == 2


def test_a_cache_window_keeps_one_report_and_invalidate_clears_it() -> None:
    probe = CountingProbe()
    service = ReadinessService((probe,), clock=FakeClock(), cache_seconds=10)
    first = service.report()
    assert service.report() is first
    assert probe.calls == 1
    service.invalidate()
    assert service.report() is not first
    assert probe.calls == 2


def test_a_budget_stops_further_probes_without_inventing_results() -> None:
    first, second = CountingProbe(), CountingProbe()
    second.probe_id = "interface:counter-2"
    service = ReadinessService((first, second), clock=FakeClock(step=5.0), budget_seconds=1.0)
    report = service.report()
    assert first.calls == 0 and second.calls == 0
    assert [result.state for result in report.results] == ["not_run", "not_run"]
    assert all(result.observed is False for result in report.results)
    assert any("总预算耗尽" in note for note in report.notes)


def test_a_raising_probe_closes_as_failed() -> None:
    report = ReadinessService((ExplodingProbe(),)).report()
    result = report.results[0]
    assert (result.state, result.observed) == ("failed", True)
    assert result.evidence["code"] == "probe_error"
    assert result.evidence["exception"] == "RuntimeError"
    assert report.overall == "failed"


def test_a_probe_returning_another_identity_is_rejected() -> None:
    result = ReadinessService((MismatchedProbe(),)).report().results[0]
    assert (result.state, result.evidence["code"]) == ("failed", "probe_contract_mismatch")


def test_a_probe_returning_a_non_contract_value_is_rejected() -> None:
    result = ReadinessService((NotAResultProbe(),)).report().results[0]
    assert (result.state, result.evidence["code"]) == ("failed", "probe_result_invalid")


def test_duplicate_probe_identities_are_refused() -> None:
    with pytest.raises(ValueError):
        ReadinessService((CountingProbe(), CountingProbe()))


@pytest.mark.parametrize("kwargs", [{"cache_seconds": -1}, {"budget_seconds": 0}])
def test_invalid_limits_are_refused(kwargs: dict[str, float]) -> None:
    with pytest.raises(ValueError):
        ReadinessService((), **kwargs)


def test_declared_notes_are_preserved_ahead_of_the_boundaries() -> None:
    report = ReadinessService((), notes=["接入清单未通过校验"]).report()
    assert report.notes[0] == "接入清单未通过校验"
    assert set(BOUNDARIES).issubset(set(report.notes))
