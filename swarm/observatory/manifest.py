"""Which providers exist is deployment data, not code.

A fresh observatory declares **nothing** beyond the host provider, so
``/api/compute/providers`` and ``/api/readiness`` describe a new machine honestly
(``not_run``) instead of inheriting the machine this app was written on.  Wiring
a surface means editing a manifest — Wayfinder, a public CLI or an MCP server —
not editing this package.

The reference manifest below shows every shape.  It deliberately keeps the argv
of third-party tools minimal: a command line must come from that tool's published
contract, never from a guess here.
"""
from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from swarm.observatory.contracts import Provider, ProviderState, ProviderSubject, SUBJECTS
from swarm.observatory.providers import (
    CliProvider,
    CredentialFileProvider,
    CredentialProvider,
    EnvMode,
    HostProvider,
    McpProvider,
)

MANIFEST_SCHEMA = "observatory.providers/1"
MAX_MANIFEST_BYTES = 256 * 1024

ENV_MANIFEST = "OBSERVATORY_PROVIDERS"
ENV_LOCAL = "OBSERVATORY_PROVIDERS_LOCAL"
ENV_DISABLE = "OBSERVATORY_PROVIDERS_DISABLE"
ENV_CACHE_SECONDS = "OBSERVATORY_PROVIDERS_CACHE"
ENV_BUDGET_SECONDS = "OBSERVATORY_PROVIDERS_BUDGET"

_FALSEY = frozenset({"0", "false", "no", "off"})

_ALLOWED_KEYS: dict[str, frozenset[str]] = {
    "host": frozenset({"kind", "provider_id", "label"}),
    "cli": frozenset({
        "kind", "provider_id", "label", "subject", "command", "args", "execute",
        "timeout_seconds", "nonzero_state", "env_mode", "report_version_line", "workspace_root",
    }),
    "mcp": frozenset({
        "kind", "provider_id", "label", "subject", "command", "args",
        "timeout_seconds", "env_mode", "require_tools", "workspace_root",
    }),
    "credential": frozenset({"kind", "provider_id", "label", "subject", "names"}),
    "credential_file": frozenset({"kind", "provider_id", "label", "subject", "path", "keys"}),
    "wayfinder": frozenset({
        "kind", "provider_id", "label", "command", "execute",
        "timeout_seconds", "credential_env", "credential_file",
    }),
}

EXAMPLE_MANIFEST: dict[str, Any] = {
    "schema": MANIFEST_SCHEMA,
    "notes": [
        "示例只演示接入形态；command/args 必须由运营者按目标工具已发布的契约填写。",
        "execute=false 只做存在性检查，适合 pi 这类不带参数会开交互会话的工具。",
        "wayfinder 是语法糖：展开为「Wayfinder 命令是否存在」+「其凭据是否存在」两条真实探测。",
        "aliyun 的凭证只在 ~/.aliyun/config.json 里检查字段是否存在，不读取其值。",
    ],
    "providers": [
        {"kind": "host", "provider_id": "host:self", "label": "本机"},
        {
            "kind": "cli", "provider_id": "cli:aliyun", "label": "阿里云 CLI",
            "command": "aliyun", "args": ["version"], "report_version_line": True,
            "timeout_seconds": 10,
        },
        {
            "kind": "credential_file", "provider_id": "account:aliyun",
            "label": "阿里云登录态", "path": "~/.aliyun/config.json",
            "keys": ["mode", "access_key_id"],
        },
        {
            "kind": "cli", "provider_id": "cli:docker", "label": "Docker",
            "command": "docker", "args": ["version", "--format", "{{.Server.Version}}"],
            "report_version_line": True, "nonzero_state": "blocked",
        },
        {
            "kind": "cli", "provider_id": "cli:kubectl", "label": "Kubernetes",
            "command": "kubectl", "args": ["config", "get-contexts", "-o", "name"],
            "execute": False,
        },
        {
            "kind": "wayfinder", "provider_id": "wayfinder:local", "label": "Wayfinder",
            "command": "pi", "execute": False,
            "credential_env": ["DASHSCOPE_API_KEY"],
            "credential_file": "~/.bailian/config.json",
        },
        {
            "kind": "mcp", "provider_id": "mcp:research", "label": "研究 MCP",
            "command": "node", "args": ["-e", "process.exit(0)"], "timeout_seconds": 10,
        },
    ],
}


class ProviderConfigError(ValueError):
    """A declared provider configuration is invalid; nothing is inferred from it."""


def load_manifest(path: Path, *, environ: Mapping[str, str] | None = None) -> tuple[Provider, ...]:
    """Read one bounded, strictly validated provider manifest."""
    candidate = Path(path)
    if candidate.is_symlink() or not candidate.is_file():
        raise ProviderConfigError("provider 清单必须是普通文件")
    if candidate.stat().st_size > MAX_MANIFEST_BYTES:
        raise ProviderConfigError("provider 清单超过 256 KiB 上限")
    try:
        document = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ProviderConfigError(f"provider 清单不是有效 JSON：{type(error).__name__}") from error
    if not isinstance(document, dict):
        raise ProviderConfigError("provider 清单必须是 JSON 对象")
    if document.get("schema") != MANIFEST_SCHEMA:
        raise ProviderConfigError(f"provider 清单 schema 必须为 {MANIFEST_SCHEMA}")
    specs = document.get("providers")
    if not isinstance(specs, list) or not specs:
        raise ProviderConfigError("provider 清单必须声明至少一个 provider")
    providers: list[Provider] = []
    for spec in specs:
        providers.extend(_build(spec, environ))
    ids = [provider.provider_id for provider in providers]
    if len(set(ids)) != len(ids):
        raise ProviderConfigError("provider_id 必须唯一")
    return tuple(providers)


def build_providers(
    *, environ: Mapping[str, str] | None = None, manifest: Path | None = None,
    local: bool | None = None, declared: bool = True,
) -> tuple[Provider, ...]:
    """Compose the declared provider set: host (optional) plus the manifest.

    ``declared=False`` skips the manifest entirely, which is how a rejected
    manifest degrades to "host only" instead of dropping every provider.
    """
    source: Mapping[str, str] = os.environ if environ is None else environ
    providers: list[Provider] = []
    include_local = local if local is not None else source.get(ENV_LOCAL, "1").strip().lower() not in _FALSEY
    if include_local:
        providers.append(HostProvider())
    declared_path = manifest if manifest is not None else _optional_path(source.get(ENV_MANIFEST))
    if declared and declared_path is not None:
        providers.extend(load_manifest(declared_path, environ=source))
    disabled = {entry.strip() for entry in source.get(ENV_DISABLE, "").split(",") if entry.strip()}
    return tuple(provider for provider in providers if provider.provider_id not in disabled)


def example_manifest_json() -> str:
    return json.dumps(EXAMPLE_MANIFEST, ensure_ascii=False, indent=2)


def _optional_path(value: str | None) -> Path | None:
    text = (value or "").strip()
    return Path(text) if text else None


def _build(spec: Any, environ: Mapping[str, str] | None) -> list[Provider]:
    if not isinstance(spec, dict):
        raise ProviderConfigError("每个 provider 声明必须是 JSON 对象")
    kind = spec.get("kind")
    if not isinstance(kind, str) or kind not in _ALLOWED_KEYS:
        raise ProviderConfigError("provider kind 必须是 host、cli、mcp、credential、credential_file 或 wayfinder")
    unknown = sorted(set(spec) - _ALLOWED_KEYS[kind])
    if unknown:
        raise ProviderConfigError(f"{kind} provider 含未知字段：{', '.join(unknown)}")
    provider_id = _text(spec, "provider_id")
    label = str(spec.get("label") or "")
    if kind == "host":
        return [HostProvider(provider_id=provider_id, label=label or "本机")]
    if kind == "cli":
        return [CliProvider(
            provider_id=provider_id,
            label=label,
            command=_text(spec, "command"),
            args=_texts(spec, "args"),
            subject=_subject(spec.get("subject", "interface")),
            execute=bool(spec.get("execute", True)),
            timeout_seconds=_float(spec, "timeout_seconds", 5.0),
            nonzero_state=_state(spec.get("nonzero_state", "failed")),
            env_mode=_env_mode(spec.get("env_mode", "isolated")),
            report_version_line=bool(spec.get("report_version_line", False)),
            workspace_root=_path(spec, "workspace_root"),
        )]
    if kind == "mcp":
        return [McpProvider(
            provider_id=provider_id,
            label=label,
            command=_text(spec, "command"),
            args=_texts(spec, "args"),
            subject=_subject(spec.get("subject", "interface")),
            timeout_seconds=_float(spec, "timeout_seconds", 15.0),
            env_mode=_env_mode(spec.get("env_mode", "isolated")),
            require_tools=_texts(spec, "require_tools"),
            workspace_root=_path(spec, "workspace_root"),
        )]
    if kind == "credential":
        return [CredentialProvider(
            provider_id=provider_id, label=label, subject=_subject(spec.get("subject", "account")),
            names=_texts(spec, "names"), lookup=environ,
        )]
    if kind == "credential_file":
        return [CredentialFileProvider(
            provider_id=provider_id, label=label, subject=_subject(spec.get("subject", "account")),
            path=Path(_text(spec, "path")), keys=_texts(spec, "keys"),
        )]
    return _build_wayfinder(provider_id, label, spec)


def _build_wayfinder(provider_id: str, label: str, spec: Mapping[str, Any]) -> list[Provider]:
    """Wayfinder is reached through its published entry points, so it expands to
    the two real checks it implies: the agent command and its credential."""
    command = _text(spec, "command")
    providers: list[Provider] = [CliProvider(
        provider_id=f"{provider_id}:cli",
        label=label or provider_id,
        kind="wayfinder",
        command=command,
        execute=bool(spec.get("execute", False)),
        timeout_seconds=_float(spec, "timeout_seconds", 5.0),
        nonzero_state="blocked",
    )]
    names = _texts(spec, "credential_env")
    if names:
        providers.append(CredentialProvider(
            provider_id=f"{provider_id}:key", label=f"{label or provider_id} 凭据", names=names,
        ))
    file_value = spec.get("credential_file")
    if file_value is not None:
        if not isinstance(file_value, str) or not file_value.strip():
            raise ProviderConfigError("字段 credential_file 必须是非空字符串路径")
        providers.append(CredentialFileProvider(
            provider_id=f"{provider_id}:login", label=f"{label or provider_id} 登录态",
            path=Path(file_value.strip()), keys=[],
        ))
    return providers


def _text(spec: Mapping[str, Any], key: str) -> str:
    value = spec.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ProviderConfigError(f"字段 {key} 必须是非空字符串")
    return value.strip()


def _texts(spec: Mapping[str, Any], key: str) -> list[str]:
    value = spec.get(key, [])
    if not isinstance(value, list) or any(not isinstance(entry, str) or not entry.strip() for entry in value):
        raise ProviderConfigError(f"字段 {key} 必须是字符串数组")
    return [entry.strip() for entry in value]


def _float(spec: Mapping[str, Any], key: str, default: float) -> float:
    value = spec.get(key, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProviderConfigError(f"字段 {key} 必须是数值")
    return float(value)


def _path(spec: Mapping[str, Any], key: str) -> Path | None:
    value = spec.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ProviderConfigError(f"字段 {key} 必须是非空字符串路径")
    return Path(value.strip())


def _subject(value: Any) -> ProviderSubject:
    if value not in SUBJECTS:
        raise ProviderConfigError("subject 必须是 machine、interface 或 account")
    return cast(ProviderSubject, value)


def _state(value: Any) -> ProviderState:
    if value not in ("ok", "degraded", "blocked", "failed"):
        raise ProviderConfigError("nonzero_state 必须是 ok、degraded、blocked 或 failed")
    return cast(ProviderState, value)


def _env_mode(value: Any) -> EnvMode:
    if value not in ("isolated", "inherit"):
        raise ProviderConfigError("env_mode 必须是 isolated 或 inherit")
    return cast(EnvMode, value)
