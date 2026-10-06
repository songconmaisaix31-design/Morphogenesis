"""Which probes exist is deployment data, not code.

The product ships a valid *empty* posture for interfaces and accounts: unless a
deployment declares CLI, MCP or credential probes, those dimensions report
``not_run``.  Adding an integration therefore means writing a manifest — not
editing this package — which is what keeps the app useful off this one machine.

The reference manifest below shows the three supported shapes (public CLI,
agent-facing MCP server, credential presence).  It deliberately uses placeholder
values: command lines must come from the target tool's published contract, never
from a guess here.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, cast

from contracts.protocols import ReadinessProbe
from contracts.readiness import SUBJECTS, ProbeState, ProbeSubject
from readiness.cli import PublicCliProbe
from readiness.credential import CredentialProbe
from readiness.launch import EnvMode
from readiness.local import LocalMachineProbe
from readiness.mcp import AgentMcpProbe
from readiness.service import ReadinessService

MANIFEST_SCHEMA = "morph.readiness.manifest/1"
MAX_MANIFEST_BYTES = 256 * 1024

ENV_MANIFEST = "MORPH_READINESS_MANIFEST"
ENV_LOCAL = "MORPH_READINESS_LOCAL"
ENV_DISABLE = "MORPH_READINESS_DISABLE"
ENV_CACHE_SECONDS = "MORPH_READINESS_CACHE_SECONDS"
ENV_BUDGET_SECONDS = "MORPH_READINESS_BUDGET_SECONDS"

_FALSEY = frozenset({"0", "false", "no", "off"})

_ALLOWED_KEYS: dict[str, frozenset[str]] = {
    "cli": frozenset({
        "kind", "probe_id", "subject", "command", "args", "timeout_seconds",
        "nonzero_state", "env_mode", "report_version_line", "workspace_root",
    }),
    "mcp": frozenset({
        "kind", "probe_id", "subject", "command", "args", "timeout_seconds",
        "env_mode", "require_tools", "workspace_root",
    }),
    "credential": frozenset({"kind", "probe_id", "subject", "names"}),
}

EXAMPLE_MANIFEST: dict[str, Any] = {
    "schema": MANIFEST_SCHEMA,
    "notes": [
        "示例只演示三种接入形态；command/args 必须由运营者按目标工具已发布的契约填写。",
        "env_mode=inherit 只在探针需要读取运营者自身登录状态时使用，默认 isolated。",
        "Wayfinder 类平台按其已发布的 CLI 与 MCP 入口接入，本清单不臆造子命令。",
    ],
    "probes": [
        {
            "kind": "cli",
            "probe_id": "interface:wayfinder-cli",
            "subject": "interface",
            "command": "wf",
            "args": ["--version"],
            "report_version_line": True,
        },
        {
            "kind": "mcp",
            "probe_id": "interface:wayfinder-mcp",
            "subject": "interface",
            "command": "wayfinder",
            "args": ["mcp", "knowledge"],
            "require_tools": [],
            "timeout_seconds": 20,
        },
        {
            "kind": "cli",
            "probe_id": "account:wayfinder",
            "subject": "account",
            "command": "wf",
            "args": ["login", "status"],
            "nonzero_state": "blocked",
            "env_mode": "inherit",
            "report_version_line": True,
        },
        {
            "kind": "credential",
            "probe_id": "account:evomap",
            "subject": "account",
            "names": ["EVOMAP_API_KEY"],
        },
    ],
}


class ReadinessConfigError(ValueError):
    """A declared probe configuration is invalid; nothing is inferred from it."""


def load_manifest(path: Path, *, environ: Mapping[str, str] | None = None) -> tuple[ReadinessProbe, ...]:
    """Read one bounded, strictly validated probe manifest.

    ``environ`` is the mapping credential probes ask about; deployments pass the
    live process environment, tests pass an explicit one.
    """
    candidate = Path(path)
    if candidate.is_symlink() or not candidate.is_file():
        raise ReadinessConfigError("接入清单必须是普通文件")
    if candidate.stat().st_size > MAX_MANIFEST_BYTES:
        raise ReadinessConfigError("接入清单超过 256 KiB 上限")
    try:
        document = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ReadinessConfigError(f"接入清单不是有效 JSON：{type(error).__name__}") from error
    if not isinstance(document, dict):
        raise ReadinessConfigError("接入清单必须是 JSON 对象")
    if document.get("schema") != MANIFEST_SCHEMA:
        raise ReadinessConfigError(f"接入清单 schema 必须为 {MANIFEST_SCHEMA}")
    specs = document.get("probes")
    if not isinstance(specs, list) or not specs:
        raise ReadinessConfigError("接入清单必须声明至少一个探针")
    probes = tuple(_build_probe(spec, environ) for spec in specs)
    ids = [probe.probe_id for probe in probes]
    if len(set(ids)) != len(ids):
        raise ReadinessConfigError("接入清单中的 probe_id 必须唯一")
    return probes


def build_service(
    *,
    environ: Mapping[str, str] | None = None,
    manifest: Path | None = None,
    local: bool | None = None,
    clock: Callable[[], float] = time.time,
    cache_seconds: float | None = None,
    budget_seconds: float | None = None,
) -> ReadinessService:
    """Compose the deployed probe set from environment and manifest."""
    source: Mapping[str, str] = os.environ if environ is None else environ
    probes: list[ReadinessProbe] = []
    include_local = local if local is not None else source.get(ENV_LOCAL, "1").strip().lower() not in _FALSEY
    if include_local:
        probes.append(LocalMachineProbe())
    declared = manifest if manifest is not None else _optional_path(source.get(ENV_MANIFEST))
    if declared is not None:
        probes.extend(load_manifest(declared, environ=source))
    disabled = {entry.strip() for entry in source.get(ENV_DISABLE, "").split(",") if entry.strip()}
    probes = [probe for probe in probes if probe.probe_id not in disabled]
    cache = cache_seconds if cache_seconds is not None else _number(source, ENV_CACHE_SECONDS, 60.0)
    budget = budget_seconds if budget_seconds is not None else _number(source, ENV_BUDGET_SECONDS, 45.0)
    return ReadinessService(probes, clock=clock, cache_seconds=cache, budget_seconds=budget)


def example_manifest_json() -> str:
    return json.dumps(EXAMPLE_MANIFEST, ensure_ascii=False, indent=2)


def _optional_path(value: str | None) -> Path | None:
    text = (value or "").strip()
    return Path(text) if text else None


def _number(source: Mapping[str, str], name: str, default: float) -> float:
    raw = (source.get(name) or "").strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError as error:
        raise ReadinessConfigError(f"{name} 必须是数值") from error
    if value < 0:
        raise ReadinessConfigError(f"{name} 不能为负数")
    return value


def _build_probe(spec: Any, environ: Mapping[str, str] | None = None) -> ReadinessProbe:
    if not isinstance(spec, dict):
        raise ReadinessConfigError("每个探针声明必须是 JSON 对象")
    kind = spec.get("kind")
    if not isinstance(kind, str) or kind not in _ALLOWED_KEYS:
        raise ReadinessConfigError("探针 kind 必须是 cli、mcp 或 credential")
    unknown = sorted(set(spec) - _ALLOWED_KEYS[kind])
    if unknown:
        raise ReadinessConfigError(f"{kind} 探针含未知字段：{', '.join(unknown)}")
    probe_id = _text(spec, "probe_id")
    subject = _subject(spec.get("subject", "interface"))
    if kind == "cli":
        return PublicCliProbe(
            probe_id=probe_id,
            command=_text(spec, "command"),
            args=_texts(spec, "args"),
            subject=subject,
            timeout_seconds=_float(spec, "timeout_seconds", 5.0),
            nonzero_state=_state(spec.get("nonzero_state", "failed")),
            env_mode=_env_mode(spec.get("env_mode", "isolated")),
            report_version_line=bool(spec.get("report_version_line", False)),
            workspace_root=_path(spec, "workspace_root"),
        )
    if kind == "mcp":
        return AgentMcpProbe(
            probe_id=probe_id,
            command=_text(spec, "command"),
            args=_texts(spec, "args"),
            subject=subject,
            timeout_seconds=_float(spec, "timeout_seconds", 15.0),
            env_mode=_env_mode(spec.get("env_mode", "isolated")),
            require_tools=_texts(spec, "require_tools"),
            workspace_root=_path(spec, "workspace_root"),
        )
    return CredentialProbe(probe_id=probe_id, names=_texts(spec, "names"), subject=subject, lookup=environ)


def _text(spec: Mapping[str, Any], key: str) -> str:
    value = spec.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ReadinessConfigError(f"字段 {key} 必须是非空字符串")
    return value.strip()


def _texts(spec: Mapping[str, Any], key: str) -> list[str]:
    value = spec.get(key, [])
    if not isinstance(value, list) or any(not isinstance(entry, str) or not entry.strip() for entry in value):
        raise ReadinessConfigError(f"字段 {key} 必须是字符串数组")
    return [entry.strip() for entry in value]


def _float(spec: Mapping[str, Any], key: str, default: float) -> float:
    value = spec.get(key, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ReadinessConfigError(f"字段 {key} 必须是数值")
    return float(value)


def _path(spec: Mapping[str, Any], key: str) -> Path | None:
    value = spec.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ReadinessConfigError(f"字段 {key} 必须是非空字符串路径")
    return Path(value.strip())


def _subject(value: Any) -> ProbeSubject:
    if value not in SUBJECTS:
        raise ReadinessConfigError("subject 必须是 machine、interface 或 account")
    return cast(ProbeSubject, value)


def _state(value: Any) -> ProbeState:
    if value not in ("ok", "degraded", "blocked", "failed"):
        raise ReadinessConfigError("nonzero_state 必须是 ok、degraded、blocked 或 failed")
    return cast(ProbeState, value)


def _env_mode(value: Any) -> EnvMode:
    if value not in ("isolated", "inherit"):
        raise ReadinessConfigError("env_mode 必须是 isolated 或 inherit")
    return cast(EnvMode, value)
