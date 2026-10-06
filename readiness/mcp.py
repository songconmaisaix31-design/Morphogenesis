"""One bounded MCP handshake against a declared, agent-facing server.

The probe speaks the published stdio transport directly: newline-delimited
JSON-RPC 2.0, an ``initialize`` request, the ``notifications/initialized``
notification and a single ``tools/list``.  It never calls a tool, never retries
and never forwards the child's stderr, so a readiness check cannot mutate
anything or leak child text into a report.

Running the handshake in a worker thread keeps the probe synchronous (the
read-only panel is synchronous) while still bounding a blocked pipe read: on
timeout the child process is killed, which releases the read.
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import threading
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any

from contracts.readiness import ProbeResult, ProbeState, ProbeSubject
from readiness.launch import EnvMode, plan_launch
from readiness.sanitize import safe_token

PROTOCOL_VERSION = "2025-06-18"
CLIENT_INFO: dict[str, str] = {"name": "morphogenesis-readiness", "version": "1"}
MAX_MESSAGE_BYTES = 512 * 1024
MAX_LINES = 200
INITIALIZE_ID = 1
TOOLS_LIST_ID = 2


class McpHandshakeError(Exception):
    """A bounded, coded failure; the message never includes child text."""

    def __init__(self, code: str, detail: str, cause: str | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail
        self.cause = cause


@dataclass(frozen=True)
class AgentMcpProbe:
    """Connect to one MCP server, verify it answers, then close it."""

    probe_id: str
    command: str
    args: Sequence[str] = ()
    subject: ProbeSubject = "interface"
    timeout_seconds: float = 15.0
    env_mode: EnvMode = "isolated"
    require_tools: Sequence[str] = ()
    workspace_root: Path | None = None

    def __post_init__(self) -> None:
        if not self.probe_id:
            raise ValueError("probe_id must not be empty")
        if not self.command or "\x00" in self.command:
            raise ValueError("command must be a non-empty executable name or path")
        if any("\x00" in arg for arg in self.args):
            raise ValueError("arguments must not contain NUL")
        if not math.isfinite(self.timeout_seconds) or self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be finite and positive")
        if any(not name.strip() for name in self.require_tools):
            raise ValueError("require_tools entries must not be blank")

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
        evidence = {
            "code": "ok",
            "server": name,
            "version": version,
            "tool_count": str(len(tools)),
        }
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
        except Exception as error:  # never propagate into the request handler
            holder["error"] = McpHandshakeError(
                "mcp_transport_failed", "MCP 会话异常结束", type(error).__name__
            )

    def _handshake(self, process: subprocess.Popen[bytes]) -> tuple[str, str, list[str]]:
        stdin = process.stdin
        stdout = process.stdout
        if stdin is None or stdout is None:
            raise McpHandshakeError("mcp_transport_failed", "无法建立 MCP 管道")
        _send(stdin, {
            "jsonrpc": "2.0",
            "id": INITIALIZE_ID,
            "method": "initialize",
            "params": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": CLIENT_INFO,
            },
        })
        initialized = _read_result(stdout, INITIALIZE_ID)
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
        _send(stdin, {"jsonrpc": "2.0", "id": TOOLS_LIST_ID, "method": "tools/list", "params": {}})
        listed = _read_result(stdout, TOOLS_LIST_ID)
        raw_tools = listed.get("tools")
        if not isinstance(raw_tools, list):
            raise McpHandshakeError("mcp_malformed", "tools/list 响应缺少 tools 数组")
        tools = [
            entry["name"] for entry in raw_tools
            if isinstance(entry, dict) and isinstance(entry.get("name"), str)
        ]
        return name, version, tools

    def _result(self, state: ProbeState, detail: str, evidence: dict[str, str]) -> ProbeResult:
        return ProbeResult(
            probe_id=self.probe_id,
            subject=self.subject,
            state=state,
            observed=True,
            detail=detail,
            evidence=evidence,
            notes=[
                "只做 initialize 与 tools/list；不调用任何工具，不重试。",
                f"环境模式：{self.env_mode}；协议版本：{PROTOCOL_VERSION}。",
            ],
        )


def _send(stream: IO[bytes], payload: dict[str, Any]) -> None:
    stream.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8") + b"\n")
    stream.flush()


def _read_result(stream: IO[bytes], request_id: int) -> dict[str, Any]:
    for _ in range(MAX_LINES):
        line = stream.readline()
        if not line:
            raise McpHandshakeError("mcp_closed", "MCP 服务端提前关闭了会话")
        if len(line) > MAX_MESSAGE_BYTES:
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
