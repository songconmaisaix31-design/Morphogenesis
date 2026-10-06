"""Aggregate declared probes into one verdict that never overstates coverage."""

from __future__ import annotations

import time
from collections.abc import Callable, Sequence

from contracts.protocols import ReadinessProbe
from contracts.readiness import (
    EnvironmentReport,
    ProbeResult,
    dimension_states,
    overall_state,
)

#: Fixed boundaries shipped with every report, so a consumer cannot mistake a
#: readiness verdict for run evidence.
BOUNDARIES: tuple[str, ...] = (
    "readiness 不是运行证据：不建立 contract_local / interface_live / task_live 任何一档。",
    "not_run 表示该维度未接入探测，不表示外部系统通过。",
    "每个探针每次报告最多执行一次，不做重试；探针自身异常按失败关闭。",
    "证据只含净化后的短标记与布尔事实，不含子进程原始输出、凭据值或主机名。",
)


class ReadinessService:
    """Run the declared probes, in order, at most once each.

    ``probes=()`` is a valid deployment: every dimension reports ``not_run``.
    That is a state to display, never a licence to invent a default verdict.
    """

    def __init__(
        self,
        probes: Sequence[ReadinessProbe] = (),
        *,
        clock: Callable[[], float] = time.time,
        cache_seconds: float = 0.0,
        budget_seconds: float | None = None,
        notes: Sequence[str] = (),
    ) -> None:
        if cache_seconds < 0:
            raise ValueError("cache_seconds must not be negative")
        if budget_seconds is not None and budget_seconds <= 0:
            raise ValueError("budget_seconds must be positive when set")
        self.cache_seconds = float(cache_seconds)
        self.budget_seconds = budget_seconds
        self._clock = clock
        self._notes = tuple(notes)
        self._probes = tuple(probes)
        ids = [probe.probe_id for probe in self._probes]
        if len(set(ids)) != len(ids):
            raise ValueError("probe_id must be unique across the declared probes")
        self._cached: EnvironmentReport | None = None
        self._cached_at: float = 0.0

    @property
    def probe_ids(self) -> tuple[str, ...]:
        return tuple(probe.probe_id for probe in self._probes)

    def invalidate(self) -> None:
        self._cached = None

    def report(self) -> EnvironmentReport:
        now = self._clock()
        if self._cached is not None and now - self._cached_at < self.cache_seconds:
            return self._cached
        report = self._build(now)
        self._cached = report
        self._cached_at = now
        return report

    def _build(self, started: float) -> EnvironmentReport:
        results: list[ProbeResult] = []
        notes = list(self._notes) + list(BOUNDARIES)
        truncated = False
        for probe in self._probes:
            if self.budget_seconds is not None and self._clock() - started > self.budget_seconds:
                truncated = True
                results.append(_unobserved(probe, "总预算耗尽，未执行该探针"))
                continue
            results.append(self._run(probe))
        if truncated:
            notes.append("总预算耗尽：其余探针保持未探测，不推断其结果。")
        if not self._probes:
            notes.append("当前部署未声明任何探针：三个维度均为未探测。")
        dimensions = dimension_states(results)
        return EnvironmentReport(
            generated_at=started,
            overall=overall_state(dimensions),
            dimensions=dimensions,
            results=results,
            notes=notes,
        )

    def _run(self, probe: ReadinessProbe) -> ProbeResult:
        try:
            result = probe.probe()
        except Exception as error:  # probe failures close the result, never propagate
            return _failed(probe, "probe_error", "探针实现异常，已按失败关闭", type(error).__name__)
        if not isinstance(result, ProbeResult):
            return _failed(probe, "probe_result_invalid", "探针返回了非契约结果")
        if result.probe_id != probe.probe_id or result.subject != probe.subject:
            return _failed(probe, "probe_contract_mismatch", "探针返回的身份与声明不一致")
        return result


def _unobserved(probe: ReadinessProbe, detail: str) -> ProbeResult:
    return ProbeResult(probe_id=probe.probe_id, subject=probe.subject, state="not_run", detail=detail)


def _failed(probe: ReadinessProbe, code: str, detail: str, cause: str | None = None) -> ProbeResult:
    evidence = {"code": code}
    if cause is not None:
        evidence["exception"] = cause
    return ProbeResult(
        probe_id=probe.probe_id,
        subject=probe.subject,
        state="failed",
        observed=True,
        detail=detail,
        evidence=evidence,
    )
