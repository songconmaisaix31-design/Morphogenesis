"""Official MCP Python client for the pinned GEP server, in isolated local mode."""

from __future__ import annotations

import json
import math
import os
import shutil
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import timedelta
from pathlib import Path
from typing import TypeVar

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent, Tool
from pydantic import JsonValue, TypeAdapter, ValidationError

from bridge_node.assets import BridgeError, NodeAssetBridge
from bridge_node.environment import child_environment

_T = TypeVar("_T")
_OBJECT = TypeAdapter(dict[str, JsonValue])
LOCAL_TOOLS = frozenset({
    "gep_recall", "gep_evolve", "gep_export", "gep_status", "gep_protocol_info",
    "gep_list_genes", "gep_install_gene", "gep_record_outcome",
})


class GepMcpSession:
    """A connected local session; timeouts end its usable lifetime, with no retry."""

    def __init__(
        self, session: ClientSession, workspace: Path, timeout_seconds: float,
    ) -> None:
        self._session = session
        self._workspace = workspace
        self._timeout = timeout_seconds
        self._usable = True

    async def _run(self, action: Callable[[], Awaitable[_T]]) -> _T:
        if not self._usable:
            raise BridgeError("mcp_session_closed")
        try:
            with anyio.fail_after(self._timeout):
                return await action()
        except TimeoutError:
            self._usable = False
            raise BridgeError("mcp_timeout") from None
        except Exception:
            self._usable = False
            raise BridgeError("mcp_transport_failed") from None

    async def list_tools(self) -> list[Tool]:
        result = await self._run(self._session.list_tools)
        return result.tools

    async def call_tool(
        self, name: str, arguments: dict[str, JsonValue] | None = None,
    ) -> dict[str, JsonValue]:
        if name not in LOCAL_TOOLS:
            raise BridgeError("mcp_tool_not_allowed")
        if not self._usable:
            raise BridgeError("mcp_session_closed")
        # JSON roundtrip takes an immutable-at-the-boundary copy and rejects NaN.
        try:
            args = _OBJECT.validate_json(json.dumps(arguments or {}, allow_nan=False))
        except (ValidationError, ValueError, TypeError):
            raise BridgeError("invalid_json_value") from None
        if name == "gep_install_gene":
            gene = args.get("gene")
            if not isinstance(gene, dict):
                raise BridgeError("invalid_gene")
            validation = await anyio.to_thread.run_sync(NodeAssetBridge().validate_asset, gene)
            if gene.get("type") != "Gene" or not validation.valid:
                raise BridgeError("invalid_gene")
        if name == "gep_export":
            # 1.7.0's path guard uses '/' even on Windows. Its stable fallback is
            # assets/export.gepx; expose that single destination on all platforms.
            destination = self._workspace / "assets" / "export.gepx"
            requested = args.get("outputPath", str(destination))
            if not isinstance(requested, str) or Path(requested).resolve() != destination:
                raise BridgeError("mcp_export_path_restricted")
            args["outputPath"] = str(destination)
        result = await self._run(lambda: self._session.call_tool(name, args))
        if result.isError:
            raise BridgeError("mcp_tool_failed")
        if len(result.content) != 1 or not isinstance(result.content[0], TextContent):
            raise BridgeError("mcp_invalid_response")
        try:
            payload = _OBJECT.validate_json(result.content[0].text)
        except ValidationError:
            raise BridgeError("mcp_invalid_response") from None
        if "error" in payload:
            raise BridgeError("mcp_tool_failed")
        return payload


class LocalGepMcpClient:
    """Owns an explicitly supplied workspace, never the user's GEP/home state.

    Uses stdio_client/ClientSession directly, including their process shutdown.
    Network tools are deliberately unavailable here: Hub publication has its own
    approval boundary. This is not a hostile-code sandbox.
    """

    def __init__(self, workspace: Path, *, timeout_seconds: float = 15.0) -> None:
        if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be finite and positive")
        self.workspace = workspace.resolve()
        self.timeout_seconds = timeout_seconds

    def _parameters(self) -> StdioServerParameters:
        executable = shutil.which("node")
        if executable is None:
            raise BridgeError("node_unavailable")
        package = Path(__file__).resolve().parent.parent / "node_modules" / "@evomap" / "gep-mcp-server"
        try:
            metadata = json.loads((package / "package.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raise BridgeError("mcp_server_unavailable") from None
        if metadata.get("version") != "1.7.0":
            raise BridgeError("mcp_version_mismatch")
        self.workspace.mkdir(parents=True, exist_ok=True)
        return StdioServerParameters(
            command=executable, args=[str(package / "src" / "index.js")],
            cwd=self.workspace, env=child_environment(self.workspace),
        )

    @asynccontextmanager
    async def connect(self) -> AsyncIterator[GepMcpSession]:
        parameters = self._parameters()
        adapter: GepMcpSession | None = None
        body_error: BaseException | None = None
        # Do not forward upstream stderr, which may echo submitted tool data.
        with open(os.devnull, "w", encoding="utf-8") as errlog:
            try:
                async with stdio_client(parameters, errlog=errlog) as (read, write):
                    async with ClientSession(
                        read, write,
                        read_timeout_seconds=timedelta(seconds=self.timeout_seconds + 1),
                    ) as session:
                        adapter = GepMcpSession(session, self.workspace, self.timeout_seconds)
                        initialized = await adapter._run(session.initialize)
                        if (
                            initialized.serverInfo.name != "gep-mcp-server"
                            or initialized.serverInfo.version != "1.7.0"
                        ):
                            raise BridgeError("mcp_version_mismatch")
                        try:
                            yield adapter
                        except BaseException as exc:
                            body_error = exc
                            raise
            except Exception as exc:
                # anyio task groups can wrap a caller or protocol exception. Keep
                # caller errors intact; never leak child-provided error content.
                if body_error is not None:
                    raise body_error from None
                if isinstance(exc, BridgeError):
                    raise
                if isinstance(exc, ExceptionGroup):
                    known, _ = exc.split(BridgeError)
                    if known is not None:
                        first: BaseException = known
                        while isinstance(first, BaseExceptionGroup):
                            first = first.exceptions[0]
                        raise first from None
                raise BridgeError("mcp_transport_failed") from None
            finally:
                if adapter is not None:
                    adapter._usable = False
