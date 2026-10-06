"""Concrete providers: host facts, declared CLIs, declared MCP servers, credentials.

Every adapter here is written so that a *fresh* deployment observes only what it
can really see:

* :class:`HostProvider` needs no configuration and reports only host facts.
* :class:`CliProvider` runs a command line the manifest declared verbatim.  It
  never invents a flag, and ``execute=False`` limits it to a presence check.
* :class:`McpProvider` speaks the published stdio transport: one ``initialize``,
  the ``initialized`` notification and one ``tools/list``.  It calls no tool and
  never retries.
* :class:`CredentialProvider` / :class:`CredentialFileProvider` report presence
  only; values are never read into a report.
"""
from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import threading
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, Any, Literal

from swarm.observatory.contracts import ProbeResult, ProviderKind, ProviderState, ProviderSubject

EnvMode = Literal["isolated", "inherit"]
SCRATCH_PREFIX = "observatory-probe-"
MAX_OUTPUT_MESSAGE = 512 * 1024
MAX_MCP_LINES = 200
MCP_PROTOCOL_VERSION = "2025-06-18"

#: A short, punctuation-restricted identifier: names, versions, exit statuses.
SAFE_TOKEN = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9 ._+()/:-]{0,63}\Z")
#: Only a version-shaped line may be echoed: ``<name> [v]X.Y[.Z...]``.  A bare
#: secret printed to stdout has no version tail, so it can never qualify.
VERSION_LINE = re.compile(r"\A[A-Za-z][A-Za-z0-9 ._+()-]{0,31} ?v?\d+(?:[.+-][0-9A-Za-z]+){1,4}\Z")

#: Preserve only OS process discovery essentials for isolated probes.
_KEEP_ENV = {"path", "systemroot", "windir", "comspec", "pathext", "pathext"}


def safe_token(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text if SAFE_TOKEN.match(text) else None


def first_version_line(*chunks: bytes) -> str | None:
    """Return the first version-shaped line, or None. Never returns raw output."""
    for chunk in chunks:
        for raw in chunk.splitlines():
            line = raw.decode("utf-8", "replace").strip()
            if not line:
                continue
            matched = VERSION_LINE.match(line)
            if matched is not None:
                return matched.group(0)
    return None


@dataclass(frozen=True)
class LaunchPlan:
    cwd: str | None
    env: dict[str, str]
    scratch: Path | None = None

    def cleanup(self) -> None:
        if self.scratch is not None:
            shutil.rmtree(self.scratch, ignore_errors=True)


def plan_launch(mode: EnvMode, workspace_root: Path | None = None) -> LaunchPlan:
    """isolated => scratch HOME/TEMP and no ambient credentials; inherit => as the operator."""
    if mode == "inherit":
        root = workspace_root.resolve() if workspace_root is not None else None
        return LaunchPlan(cwd=None if root is None else str(root), env=dict(os.environ))
    if workspace_root is not None:
        root = workspace_root.resolve()
        root.mkdir(parents=True, exist_ok=True)
        return LaunchPlan(cwd=str(root), env=_isolated_env(root))
    scratch = Path(tempfile.mkdtemp(prefix=SCRATCH_PREFIX))
    return LaunchPlan(cwd=str(scratch), env=_isolated_env(scratch), scratch=scratch)


def _isolated_env(root: Path) -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if key.lower() in _KEEP_ENV}
    home = root / "home"
    temp = root / "tmp"
    for directory in (home, temp):
        directory.mkdir(parents=True, exist_ok=True)
    env.update({
        "HOME": str(home), "USERPROFILE": str(home),
        "HOMEDRIVE": home.drive, "HOMEPATH": str(home)[len(home.drive):],
        "TEMP": str(temp), "TMP": str(temp), "TMPDIR": str(temp),
        # Explicit empties so an SDK cannot pick up the operator's credentials.
        "NODE_OPTIONS": "", "DASHSCOPE_API_KEY": "",
        "ALIBABACLOUD_ACCESS_KEY_ID": "", "ALIBABACLOUD_ACCESS_KEY_SECRET": "",
    })
    return env


# ---------------------------------------------------------------------------
# machine
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class HostProvider:
    """Host facts.  The only provider that needs no declaration."""

    provider_id: str = "host:self"
    label: str = "本机"
    kind: ProviderKind = "host"
    subject: ProviderSubject = "machine"

    def probe(self) -> ProbeResult:
        cpus = os.cpu_count() or 0
        writable = _temp_writable()
        import platform

        evidence = {
            "os": platform.system() or "unknown",
            "python": platform.python_version() or "unknown",
            "cpus": str(cpus),
            "temp_writable": "true" if writable else "false",
        }
        healthy = writable and cpus > 0
        return ProbeResult(
            provider_id=self.provider_id,
            subject=self.subject,
            state="ok" if healthy else "degraded",
            observed=True,
            detail=f"{evidence['os']} / Python {evidence['python']} / {cpus} CPU",
            evidence=evidence,
            notes=["只报告进程实际观测到的宿主事实；不含主机名、用户名与路径。"],
        )


def _temp_writable() -> bool:
    try:
        return os.access(tempfile.gettempdir(), os.W_OK)
    except OSError:
        return False


# ---------------------------------------------------------------------------
# interface: declared public CLI
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CliProvider:
    """A declared command line, executed at most once per report.

    ``execute=False`` turns it into a pure presence check, which is the right
    mode for interactive tools (running them without arguments would open a
    session instead of answering a question).
    """

    provider_id: str
    command: str
    args: Sequence[str] = ()
    label: str = ""
    kind: ProviderKind = "cli"
    subject: ProviderSubject = "interface"
    execute: bool = True
    timeout_seconds: float = 5.0
    nonzero_state: ProviderState = "failed"
    env_mode: EnvMode = "isolated"
    report_version_line: bool = False
    workspace_root: Path | None = None

    def __post_init__(self) -> None:
        if not self.provider_id:
            raise ValueError("provider_id must not be empty")
        if not self.command or "\x00" in self.command:
            raise ValueError("command must be a non-empty executable name or path")
        if any("\x00" in arg for arg in self.args):
            raise ValueError("arguments must not contain NUL")
        if not math.isfinite(self.timeout_seconds) or self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be finite and positive")
        if self.nonzero_state == "not_run":
            raise ValueError("nonzero_state must describe an observation")

    @property
    def display_label(self) -> str:
        return self.label or self.provider_id

    def probe(self) -> ProbeResult:
        executable = shutil.which(self.command)
        if executable is None:
            return self._result("blocked", f"未找到声明的 CLI：{self.command}", {"code": "command_missing"})
        if not self.execute:
            return self._result("ok", f"已找到 {self.command}", {"code": "present", "command": self.command})
        plan = plan_launch(self.env_mode, self.workspace_root)
        try:
            completed = subprocess.run(
                [executable, *self.args],
                cwd=plan.cwd,
                env=plan.env,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return self._result("failed", "探测命令超时，未重试", {"code": "timeout"})
        except OSError:
            return self._result("failed", "无法启动探测命令", {"code": "spawn_failed"})
        finally:
            plan.cleanup()

        state: ProviderState = "ok" if completed.returncode == 0 else self.nonzero_state
        evidence = {
            "code": "exit_ok" if completed.returncode == 0 else "exit_nonzero",
            "exit_code": str(completed.returncode),
        }
        detail = f"{self.command} 退出码 {completed.returncode}"
        if self.report_version_line:
            line = first_version_line(completed.stdout, completed.stderr)
            if line is not None:
                evidence["output"] = line
                if completed.returncode == 0:
                    detail = f"{self.command} {line}"
        return self._result(state, detail, evidence)

    def _result(self, state: ProviderState, detail: str, evidence: dict[str, str]) -> ProbeResult:
        return ProbeResult(
            provider_id=self.provider_id,
            subject=self.subject,
            state=state,
            observed=True,
            detail=detail,
            evidence=evidence,
            notes=[f"环境模式：{self.env_mode}；每次报告最多执行一次。"],
        )


# ---------------------------------------------------------------------------
# interface: declared MCP server
# ---------------------------------------------------------------------------

class McpHandshakeError(Exception):
    """A bounded, coded failure; the message never includes child text."""

    def __init__(self, code: str, detail: str, cause: str | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail
        self.cause = cause


@dataclass(frozen=True)
class McpProvider:
    """One bounded stdio MCP handshake against a declared, agent-facing server."""

    provider_id: str
    command: str
    args: Sequence[str] = ()
    label: str = ""
    kind: ProviderKind = "mcp"
    subject: ProviderSubject = "interface"
    timeout_seconds: float = 15.0
    env_mode: EnvMode = "isolated"
    require_tools: Sequence[str] = ()
    workspace_root: Path | None = None

    def __post_init__(self) -> None:
        if not self.provider_id:
            raise ValueError("provider_id must not be empty")
        if not self.command or "\x00" in self.command:
            raise ValueError("command must be a non-empty executable name or path")
        if any("\x00" in arg for arg in self.args):
            raise ValueError("arguments must not contain NUL")
        if not math.isfinite(self.timeout_seconds) or self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be finite and positive")
        if any(not name.strip() for name in self.require_tools):
            raise ValueError("require_tools entries must not be blank")

    @property
    def display_label(self) -> str:
        return self.label or self.provider_id

    def probe(self) -> ProbeResult:
        executable = shutil.which(self.command)
        if executable is None:
            return self._result("blocked", f"未找到 MCP 服务端命令：{self.command}", {"code": "command_missing"})
        plan = plan_launch(self.env_mode, self.workspace_root)
        holder: dict[str, Any] = {}
        process: subprocess.Popen[bytes] | None = None
        try:
            try:
                process = subprocess.Popen(
                    [executable, *self.args],
                    cwd=plan.cwd,
                    env=plan.env,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                )
            except OSError:
                return self._result("failed", "无法启动 MCP 服务端进程", {"code": "spawn_failed"})
            worker = threading.Thread(target=self._handshake_into, args=(process, holder), daemon=True)
            worker.start()
            worker.join(self.timeout_seconds)
            if worker.is_alive():
                return self._result("failed", "MCP 握手超时，未重试", {"code": "timeout"})
        finally:
            _terminate(process)
            plan.cleanup()

        error = holder.get("error")
        if isinstance(error, McpHandshakeError):
            evidence = {"code": error.code}
            if error.cause is not None:
                evidence["exception"] = error.cause
            return self._result("failed", error.detail, evidence)
        value = holder.get("value")
        if not isinstance(value, tuple):
            return self._result("failed", "MCP 握手未返回结果", {"code": "mcp_transport_failed"})
        name, version, tools = value
        evidence = {"code": "ok", "server": name, "version": version, "tool_count": str(len(tools))}
        missing = [required for required in self.require_tools if required not in tools]
        if missing:
            evidence["code"] = "tools_missing"
            evidence["missing_tools"] = ",".join(missing)
            return self._result("degraded", f"MCP 已连接但缺少必需工具：{', '.join(missing)}", evidence)
        return self._result("ok", f"MCP 已连接：{name} {version} · {len(tools)} 个工具", evidence)

    def _handshake_into(self, process: subprocess.Popen[bytes], holder: dict[str, Any]) -> None:
        try:
            holder["value"] = self._handshake(process)
        except McpHandshakeError as error:
            holder["error"] = error
        except Exception as error:  # noqa: BLE001 - never propagate into the request handler
            holder["error"] = McpHandshakeError("mcp_transport_failed", "MCP 会话异常结束", type(error).__name__)

    def _handshake(self, process: subprocess.Popen[bytes]) -> tuple[str, str, list[str]]:
        stdin, stdout = process.stdin, process.stdout
        if stdin is None or stdout is None:
            raise McpHandshakeError("mcp_transport_failed", "无法建立 MCP 管道")
        _send(stdin, {
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "observatory-readiness", "version": "1"},
            },
        })
        initialized = _read_result(stdout, 1)
        protocol = initialized.get("protocolVersion")
        info = initialized.get("serverInfo")
        if not isinstance(protocol, str) or not protocol:
            raise McpHandshakeError("mcp_malformed", "MCP 握手缺少 protocolVersion")
        if not isinstance(info, dict):
            raise McpHandshakeError("mcp_malformed", "MCP 握手缺少 serverInfo")
        raw_name = info.get("name")
        if not isinstance(raw_name, str) or not raw_name:
            raise McpHandshakeError("mcp_malformed", "MCP 握手缺少 serverInfo.name")
        name = safe_token(raw_name) or "unnamed-server"
        version = safe_token(info.get("version")) or "unknown"
        _send(stdin, {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        _send(stdin, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        listed = _read_result(stdout, 2)
        raw_tools = listed.get("tools")
        if not isinstance(raw_tools, list):
            raise McpHandshakeError("mcp_malformed", "tools/list 响应缺少 tools 数组")
        tools = [entry["name"] for entry in raw_tools
                 if isinstance(entry, dict) and isinstance(entry.get("name"), str)]
        return name, version, tools

    def _result(self, state: ProviderState, detail: str, evidence: dict[str, str]) -> ProbeResult:
        return ProbeResult(
            provider_id=self.provider_id,
            subject=self.subject,
            state=state,
            observed=True,
            detail=detail,
            evidence=evidence,
            notes=[
                "只做 initialize 与 tools/list；不调用任何工具，不重试。",
                f"环境模式：{self.env_mode}；协议版本：{MCP_PROTOCOL_VERSION}。",
            ],
        )


def _send(stream: IO[bytes], payload: dict[str, Any]) -> None:
    stream.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8") + b"\n")
    stream.flush()


def _read_result(stream: IO[bytes], request_id: int) -> dict[str, Any]:
    for _ in range(MAX_MCP_LINES):
        line = stream.readline()
        if not line:
            raise McpHandshakeError("mcp_closed", "MCP 服务端提前关闭了会话")
        if len(line) > MAX_OUTPUT_MESSAGE:
            raise McpHandshakeError("mcp_oversized", "MCP 消息超过大小上限")
        try:
            payload = json.loads(line)
        except ValueError:
            continue  # tolerate non-JSON progress lines a server may log to stdout
        if not isinstance(payload, dict) or payload.get("id") != request_id:
            continue
        if "error" in payload:
            raise McpHandshakeError("mcp_error_response", "MCP 返回了错误响应")
        result = payload.get("result")
        if not isinstance(result, dict):
            raise McpHandshakeError("mcp_malformed", "MCP 响应缺少 result 对象")
        return result
    raise McpHandshakeError("mcp_no_response", "在行数上限内未取得匹配响应")


def _terminate(process: subprocess.Popen[bytes] | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.kill()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        return


# ---------------------------------------------------------------------------
# account
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CredentialProvider:
    """Report whether each declared environment variable is set."""

    provider_id: str
    names: Sequence[str]
    label: str = ""
    kind: ProviderKind = "credential"
    subject: ProviderSubject = "account"
    lookup: Mapping[str, str] | None = None

    def __post_init__(self) -> None:
        if not self.provider_id:
            raise ValueError("provider_id must not be empty")
        if not self.names or any(not name.strip() for name in self.names):
            raise ValueError("names must declare at least one non-empty variable")

    @property
    def display_label(self) -> str:
        return self.label or self.provider_id

    def probe(self) -> ProbeResult:
        source: Mapping[str, str] = self.lookup if self.lookup is not None else os.environ
        missing = [name for name in self.names if not (source.get(name) or "").strip()]
        evidence = {
            "code": "configured" if not missing else "missing",
            "present": f"{len(self.names) - len(missing)}/{len(self.names)}",
        }
        if missing:
            evidence["missing"] = ",".join(missing)
        return ProbeResult(
            provider_id=self.provider_id,
            subject=self.subject,
            state="ok" if not missing else "blocked",
            observed=True,
            detail="凭据已注入进程环境" if not missing else f"缺少环境变量：{', '.join(missing)}",
            evidence=evidence,
            notes=["只报告环境变量是否存在；不读取、不记录、不回显其值。"],
        )


@dataclass(frozen=True)
class CredentialFileProvider:
    """Report whether a declared credential file carries the declared keys.

    Some CLIs keep their login state in a JSON file (``~/.aliyun/config.json``,
    ``~/.bailian/config.json``).  Only key presence becomes evidence: the file is
    parsed in memory, and no value is ever copied into the report.
    """

    provider_id: str
    path: Path
    keys: Sequence[str] = ()
    label: str = ""
    kind: ProviderKind = "credential"
    subject: ProviderSubject = "account"
    max_bytes: int = 256 * 1024

    def __post_init__(self) -> None:
        if not self.provider_id:
            raise ValueError("provider_id must not be empty")
        if any(not key.strip() for key in self.keys):
            raise ValueError("keys entries must not be blank")

    @property
    def display_label(self) -> str:
        return self.label or self.provider_id

    def probe(self) -> ProbeResult:
        target = self.path.expanduser()
        if target.is_symlink() or not target.is_file():
            return self._result("blocked", f"未找到凭据文件：{target.name}", {"code": "file_missing"})
        try:
            if target.stat().st_size > self.max_bytes:
                return self._result("degraded", "凭据文件超过大小上限，未解析", {"code": "file_too_large"})
            document = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return self._result("blocked", "凭据文件不可解析", {"code": "file_unreadable"})
        present = _present_keys(document, self.keys)
        if not self.keys:
            state: ProviderState = "ok"
            detail = f"凭据文件存在（{target.name}）"
        elif len(present) == len(self.keys):
            state = "ok"
            detail = f"凭据文件含声明字段（{target.name}）"
        elif present:
            state = "degraded"
            detail = "凭据文件只含部分声明字段"
        else:
            state = "blocked"
            detail = "凭据文件缺少声明字段"
        evidence = {"code": "file_read", "present": f"{len(present)}/{len(self.keys)}"}
        if len(present) != len(self.keys):
            evidence["missing"] = ",".join(key for key in self.keys if key not in present)
        return self._result(state, detail, evidence)

    def _result(self, state: ProviderState, detail: str, evidence: dict[str, str]) -> ProbeResult:
        return ProbeResult(
            provider_id=self.provider_id,
            subject=self.subject,
            state=state,
            observed=True,
            detail=detail,
            evidence=evidence,
            notes=["只报告凭据文件是否存在声明字段；不读取、不记录、不回显其值。"],
        )


def _present_keys(document: Any, keys: Sequence[str]) -> list[str]:
    """Presence-only walk of a credential file; never returns a value."""
    def has(candidate: Any, key: str) -> bool:
        if isinstance(candidate, dict):
            value = candidate.get(key)
            return bool(value) if not isinstance(value, (dict, list)) else True
        if isinstance(candidate, list):
            return any(has(entry, key) for entry in candidate)
        return False

    return [key for key in keys if has(document, key)]
