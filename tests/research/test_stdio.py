"""A real official SDK subprocess exchange; no native/model/sandbox live claim."""
import asyncio
from pathlib import Path
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from tests.research.test_service import enqueue, make_service


def test_official_stdio_discovery_claim_and_bound_identity(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    enqueue(service)
    config = tmp_path / "host.json"
    config.write_text(service.config.model_dump_json(), encoding="utf-8")

    async def run() -> None:
        params = StdioServerParameters(command=sys.executable, args=["-m", "swarm.research", "--config", str(config)])
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                listed = await session.list_tools()
                assert "discover_tasks" in [t.name for t in listed.tools]
                result = await session.call_tool("discover_tasks", {"limit": 10})
                assert not result.isError
                claimed = await session.call_tool("lease_task", {"action": "claim", "task_id": "original", "worker_id": "impersonated"})
                # SDK may reject unknown fields or ignore them; neither can change identity.
                if claimed.isError:
                    claimed = await session.call_tool("lease_task", {"action": "claim", "task_id": "original"})
                assert not claimed.isError
                assert service.ledger.get("original").owner == "native-a"
                renewed = await session.call_tool("lease_task", {"action": "renew", "task_id": "original", "token": 1})
                assert not renewed.isError
                bad = await session.call_tool("lease_task", {"action": "renew", "task_id": "original", "token": 2})
                assert bad.isError
    asyncio.run(run())
