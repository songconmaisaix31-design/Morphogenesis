"""Run the declared providers and aggregate one verdict that never overstates coverage.

``ProviderRegistry(())`` is a valid deployment: every dimension reports
``not_run``.  That is a state to display, never a licence to invent a verdict —
which is exactly why the observatory ships with no fixed provider list.
"""
from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from typing import Any

from swarm.observatory.contracts import (
    EnvironmentReport,
    ProbeResult,
    Provider,
    dimension_states,
    overall_state,
)

#: Fixed boundaries shipped with every report, so a consumer cannot mistake
#: readiness for run evidence.
BOUNDARIES: tuple[str, ...] = (
    "readiness 不是运行证据：不建立 contract_local / interface_live / task_live 任何一档。",
    "not_run 表示该维度未声明或未执行探测，不表示外部系统可用。",
    "每个 provider 每次报告最多执行一次，不做重试；provider 自身异常按失败关闭。",
    "证据只含净化后的短标记与布尔事实，不含子进程原始输出、凭据值或主机名。",
    "provider 集合来自清单（OBSERVATORY_PROVIDERS），不是代码里的固定列表。",
)


class ProviderRegistry:
    """Hold declared providers, run each at most once per report, aggregate honestly."""

    def __init__(
        self,
        providers: Sequence[Provider] = (),
        *,
        clock: Callable[[], float] = time.time,
        cache_seconds: float = 0.0,
        budget_seconds: float | None = None,
        probe_enabled: bool = True,
        notes: Sequence[str] = (),
    ) -> None:
        if cache_seconds < 0:
            raise ValueError("cache_seconds must not be negative")
        if budget_seconds is not None and budget_seconds <= 0:
            raise ValueError("budget_seconds must be positive when set")
        self.cache_seconds = float(cache_seconds)
        self.budget_seconds = budget_seconds
        self.probe_enabled = probe_enabled
        self._clock = clock
        self._notes = tuple(notes)
        self._providers = tuple(providers)
        ids = [provider.provider_id for provider in self._providers]
        if len(set(ids)) != len(ids):
            raise ValueError("provider_id must be unique across the declared providers")
        self._cached: EnvironmentReport | None = None
        self._cached_at = 0.0

    @property
    def provider_ids(self) -> tuple[str, ...]:
        return tuple(provider.provider_id for provider in self._providers)

    def invalidate(self) -> None:
        self._cached = None

    def declared(self) -> list[dict[str, Any]]:
        """One entry per declared provider: identity, kind and its measured state."""
        by_id = {result.provider_id: result for result in self._results()}
        entries: list[dict[str, Any]] = []
        for provider in self._providers:
            result = by_id.get(provider.provider_id)
            entries.append({
                "id": provider.provider_id,
                "label": provider.label,
                "kind": provider.kind,
                "subject": provider.subject,
                "state": result.state if result is not None else "not_run",
                "observed": bool(result.observed) if result is not None else False,
                "detail": result.detail if result is not None else "",
                "evidence": dict(result.evidence) if result is not None else {},
            })
        return entries

    def report(self) -> EnvironmentReport:
        now = self._clock()
        if self._cached is not None and now - self._cached_at < self.cache_seconds:
            return self._cached
        report = self._build(now)
        self._cached = report
        self._cached_at = now
        return report

    def _results(self) -> list[ProbeResult]:
        return list(self.report().results)

    def _build(self, started: float) -> EnvironmentReport:
        notes = list(self._notes) + list(BOUNDARIES)
        if not self.probe_enabled:
            notes.append("OBSERVATORY_PROBE 已关闭：未执行任何 provider，全部维度保持未探测。")
            results = [_unobserved(provider) for provider in self._providers]
        else:
            results = []
            truncated = False
            for provider in self._providers:
                if self.budget_seconds is not None and self._clock() - started > self.budget_seconds:
                    truncated = True
                    results.append(_unobserved(provider, "总预算耗尽，未执行该 provider"))
                    continue
                results.append(self._run(provider))
            if truncated:
                notes.append("总预算耗尽：其余 provider 保持未探测，不推断其结果。")
        if not self._providers:
            notes.append("当前部署未声明任何 provider：三个维度均为未探测。")
        dimensions = dimension_states(results)
        return EnvironmentReport(
            generated_at=started,
            overall=overall_state(dimensions),
            dimensions=dimensions,
            results=results,
            notes=notes,
        )

    def _run(self, provider: Provider) -> ProbeResult:
        try:
            result = provider.probe()
        except Exception as error:  # noqa: BLE001 - provider failures close the result
            return _failed(provider, "provider_error", "provider 实现异常，已按失败关闭", type(error).__name__)
        if not isinstance(result, ProbeResult):
            return _failed(provider, "provider_result_invalid", "provider 返回了非契约结果")
        if result.provider_id != provider.provider_id or result.subject != provider.subject:
            return _failed(provider, "provider_contract_mismatch", "provider 返回的身份与声明不一致")
        return result


def _unobserved(provider: Provider, detail: str = "未执行探测") -> ProbeResult:
    return ProbeResult(provider_id=provider.provider_id, subject=provider.subject, state="not_run", detail=detail)


def _failed(provider: Provider, code: str, detail: str, cause: str | None = None) -> ProbeResult:
    evidence = {"code": code}
    if cause is not None:
        evidence["exception"] = cause
    return ProbeResult(
        provider_id=provider.provider_id,
        subject=provider.subject,
        state="failed",
        observed=True,
        detail=detail,
        evidence=evidence,
    )


def build_registry(*, environ: Any = None, manifest: Any = None, probe_enabled: bool = True,
                   cache_seconds: float | None = None, budget_seconds: float | None = None,
                   clock: Callable[[], float] = time.time) -> ProviderRegistry:
    """Compose the deployed registry from the environment and the manifest.

    A rejected manifest yields an **empty** registry plus a note: nothing is
    guessed from a config file that did not validate.
    """
    import os

    from swarm.observatory.manifest import (
        ENV_BUDGET_SECONDS,
        ENV_CACHE_SECONDS,
        ProviderConfigError,
        build_providers,
    )

    source = os.environ if environ is None else environ
    notes: list[str] = []
    try:
        providers = build_providers(environ=source, manifest=manifest)
    except ProviderConfigError as error:
        # A rejected manifest drops only the providers it declared: the host
        # provider is configuration-free and stays.
        providers = build_providers(environ=source, manifest=None, declared=False)
        notes.append(f"provider 清单未通过校验，只保留本机 provider：{error}")
    cache = _number(source, ENV_CACHE_SECONDS, 60.0, notes) if cache_seconds is None else cache_seconds
    budget = _number(source, ENV_BUDGET_SECONDS, 45.0, notes) if budget_seconds is None else budget_seconds
    return ProviderRegistry(
        providers,
        clock=clock,
        cache_seconds=cache,
        budget_seconds=budget if budget > 0 else None,
        probe_enabled=probe_enabled,
        notes=notes,
    )


def _number(source: Any, name: str, default: float, notes: list[str]) -> float:
    raw = str(source.get(name) or "").strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        notes.append(f"{name} 不是数值，已使用默认值 {default}")
        return default
    if value < 0:
        notes.append(f"{name} 为负数，已忽略")
        return default
    return value
