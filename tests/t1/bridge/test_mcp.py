from __future__ import annotations

import json
import sys
import tarfile
from pathlib import Path

import anyio
import pytest
from mcp import StdioServerParameters
from pydantic import JsonValue

from bridge_node import BridgeError, LocalGepMcpClient
from bridge_node.environment import child_environment
from bridge_node.mcp_client import LOCAL_TOOLS


def test_isolated_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ("EVOMAP_API_KEY", "EVOMAP_NODE_SECRET", "EVOMAP_NODE_ID", "NODE_OPTIONS"):
        monkeypatch.setenv(key, "sensitive-parent-value")
    env = child_environment(tmp_path)
    assert "sensitive-parent-value" not in env.values()
    assert env["EVOMAP_HUB_URL"] == "http://127.0.0.1:9"
    for key in ("HOME", "USERPROFILE", "GEP_ASSETS_DIR", "GEP_MEMORY_DIR", "CLAUDE_SKILLS_DIR"):
        assert Path(env[key]).is_relative_to(tmp_path)


def test_official_mcp_handshake_list_call_export_and_isolation(
    tmp_path: Path, gene: dict[str, JsonValue], monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Even a caller with real environment credentials must stay in local mode.
    for key in ("EVOMAP_API_KEY", "EVOMAP_NODE_SECRET", "EVOMAP_NODE_ID"):
        monkeypatch.setenv(key, "sensitive-parent-value")
    workspace = tmp_path / "one"

    async def scenario() -> None:
        async with LocalGepMcpClient(workspace).connect() as session:
            tools = await session.list_tools()
            assert LOCAL_TOOLS <= {tool.name for tool in tools}
            installed = await session.call_tool("gep_install_gene", {"gene": gene})
            assert installed["installed"] == gene["id"]
            evolved = await session.call_tool("gep_evolve", {"context": "error in fixture", "intent": "repair"})
            selected = evolved["selected_gene"]
            assert isinstance(selected, dict) and selected["id"] == gene["id"]
            recorded = await session.call_tool("gep_record_outcome", {
                "geneId": gene["id"], "signals": ["log_error"], "status": "success",
                "score": 0.5, "summary": "Synthetic local protocol test, not task evidence",
            })
            assert recorded["ok"] is True
            recalled = await session.call_tool("gep_recall", {"query": "error", "signals": ["log_error"]})
            matches = recalled["matches"]
            assert isinstance(matches, list) and len(matches) == 1
            exported = await session.call_tool("gep_export", {"agentName": "local-fixture"})
            assert exported["ok"] is True
            assert Path(str(exported["outputPath"])) == workspace / "assets" / "export.gepx"
            for prohibited in ("gep_publish_bundle", "gep_search_community", "gep_load_skill", "unknown"):
                with pytest.raises(BridgeError, match="mcp_tool_not_allowed"):
                    await session.call_tool(prohibited)
            with pytest.raises(BridgeError, match="mcp_export_path_restricted"):
                await session.call_tool("gep_export", {"outputPath": str(tmp_path / "escape.gepx")})
        with pytest.raises(BridgeError, match="mcp_session_closed"):
            await session.list_tools()
        # Runtime-owned memory persists only in the explicitly selected root.
        async with LocalGepMcpClient(workspace).connect() as reopened:
            assert (await reopened.call_tool("gep_list_genes"))["total"] == 1
        async with LocalGepMcpClient(tmp_path / "two").connect() as isolated:
            assert (await isolated.call_tool("gep_list_genes"))["total"] == 0

    anyio.run(scenario)
    with tarfile.open(workspace / "assets" / "export.gepx") as archive:
        genes_file = next(item for item in archive if item.name.endswith("genes/genes.json"))
        content = archive.extractfile(genes_file)
        assert content is not None
        assert str(gene["id"]) in json.dumps(json.load(content))
    assert not (tmp_path / "escape.gepx").exists()


def test_mcp_rejects_unvalidated_install_and_preserves_caller_errors(tmp_path: Path) -> None:
    async def scenario() -> None:
        with pytest.raises(ValueError, match="caller-error"):
            async with LocalGepMcpClient(tmp_path).connect() as session:
                with pytest.raises(BridgeError, match="invalid_gene"):
                    await session.call_tool("gep_install_gene", {"gene": {"type": "Gene", "id": "bad"}})
                raise ValueError("caller-error")

    anyio.run(scenario)


@pytest.mark.parametrize(
    ("source", "error"),
    [("import time; time.sleep(60)", "mcp_timeout"), ("import sys; sys.exit(3)", "mcp_transport_failed")],
)
def test_mcp_failed_initialization_has_no_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, source: str, error: str,
) -> None:
    client = LocalGepMcpClient(tmp_path, timeout_seconds=0.3 if error == "mcp_timeout" else 10)
    starts = 0

    def parameters() -> StdioServerParameters:
        nonlocal starts
        starts += 1
        return StdioServerParameters(command=sys.executable, args=["-c", source], cwd=tmp_path)

    monkeypatch.setattr(client, "_parameters", parameters)

    async def scenario() -> None:
        with pytest.raises(BridgeError, match=error):
            async with client.connect():
                pytest.fail("uninitialized MCP client was exposed")

    anyio.run(scenario)
    assert starts == 1
