"""Prepare registered research hosts and exercise their real MCP stdio interface.

This helper never launches a model, executes an experiment, or approves an asset.
Run from the Morphogenesis checkout: python -m demo.swa_research_bridge --help.
"""
from __future__ import annotations

import argparse
import asyncio
from contextlib import AsyncExitStack
import json
from pathlib import Path
import tempfile
from typing import Any
from uuid import uuid4

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult

from contracts.identity import AgentId
from local_assets.paths import no_links
from orchestration.experiments.case import get_case
from swarm.research.case import PENDING, seed_case
from swarm.research.models import HostConfig
from swarm.task_ledger import TaskLedger

REPOSITORY = Path(__file__).resolve().parents[1]
ROLES = ("author", "replication", "inheritance")


def _write(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def prepare(project: Path, state: Path, python: Path, *, swarm_id: str,
            domain: str = "127.0.0.1:8097", api_key_env: str | None = None) -> dict[str, str]:
    """Use the existing registered NIST case and emit fixed, absolute descriptors."""
    plan = get_case("nist-numacc4-v1").build_plan()
    paths = seed_case(project, state, python=python, plan=plan.model_dump(mode="json"),
                      code=Path(plan.code.local_path).read_bytes().decode("utf-8"),
                      swarm_id=swarm_id, domain=domain, api_key_env=api_key_env)
    state = Path(paths["state"])
    inputs = Path(paths["project"]) / "swa-inputs"
    inputs.mkdir()
    for role in ROLES:
        descriptor = state / (role + ".morph.json")
        _write(descriptor, {"python": paths["python"], "cwd": str(REPOSITORY),
                            "host_config": paths[role + "_config"]})
        paths[role + "_descriptor"] = str(descriptor)
        host = HostConfig.model_validate_json(Path(paths[role + "_config"]).read_bytes())
        spec = inputs / (role + ".task.json")
        _write(spec, {"goal": "Perform the eligible registered NIST research role: " + role,
                      "source_repo": paths["project"], "source_revision": paths["base_revision"],
                      "success_criteria": ["Use Morph tools to discover and claim eligible work",
                                           "Follow the role's trusted project_context; report actual tool outcomes"],
                      "max_workers": 1, "initial_workers": 1,
                      "context": {"references": [], "files": []}})
        prompt = inputs / (role + ".input.txt")
        prompt.write_text(
            "Use morph_list_tools {} to read the real Morph MCP tool schemas. Then use only "
            "morph_call_tool {name, arguments} for research operations. The host fixes your identity. "
            "Discover eligible tasks, choose one, voluntarily claim it, and read project_context. "
            "Use lease ttl_seconds=600 and renew before each evidence phase. Never invent IDs, "
            "scientific metrics, usage, approval, or adoption. Never execute candidate code in native "
            "tools. Each task permits at most one external experiment; stop on unknown effects and "
            "never retry that experiment. A dependency that is not completed is a reason to stop. "
            "Return the actual task/asset/run/report IDs and observed stage.\n\n"
            + host.project_context + "\n", encoding="utf-8")
        paths[role + "_spec"] = str(spec)
        paths[role + "_input"] = str(prompt)
    return paths


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _value(result: CallToolResult) -> Any:
    _require(not result.isError, "MCP call failed: " + str(result.content))
    value = result.structuredContent
    if value is not None:
        return value["result"] if set(value) == {"result"} else value
    texts = [item.text for item in result.content if item.type == "text"]
    _require(len(texts) == 1, "MCP response has no single JSON value")
    return json.loads(texts[0])


async def _check(paths: dict[str, str]) -> dict[str, object]:
    """Race two identity-bound official MCP clients; only local ledger effects."""
    state = Path(paths["state"])
    host = HostConfig.model_validate_json(Path(paths["author_config"]).read_bytes())
    peer = host.model_copy(update={"worker_id": "author-peer", "agent": AgentId(role="builder", instance=3)})
    peer_path = state / "author-peer-host.json"
    _write(peer_path, peer.model_dump(mode="json"))
    configs = [Path(paths["author_config"]), peer_path]
    worker_ids = [host.worker_id, peer.worker_id]
    ledger = TaskLedger(host.ledger_path, host.swarm_id)
    with (state / "selfcheck-stderr.log").open("x", encoding="utf-8") as stderr:
        async with AsyncExitStack() as stack:
            sessions = []
            for config in configs:
                parameters = StdioServerParameters(command=paths["python"],
                    args=["-m", "swarm.research", "--config", str(config)], cwd=REPOSITORY,
                    env={"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"})
                reader, writer = await stack.enter_async_context(stdio_client(parameters, errlog=stderr))
                session = await stack.enter_async_context(ClientSession(reader, writer))
                await session.initialize()
                sessions.append(session)
            tools = await sessions[0].list_tools()
            names = {tool.name for tool in tools.tools}
            _require({"discover_tasks", "lease_task", "project_context"} <= names, "required tools absent")
            for session in sessions:
                available = _value(await session.call_tool("discover_tasks", {"limit": 10}))
                _require([item["signal"]["task_id"] for item in available] == ["author"],
                         "discovery did not respect case dependencies and capabilities")
            claims = await asyncio.gather(*(session.call_tool("lease_task", {
                "action": "claim", "task_id": "author", "ttl_seconds": 60}) for session in sessions))
            values = [_value(result) for result in claims]
            winners = [index for index, value in enumerate(values) if isinstance(value, dict)]
            _require(len(winners) == 1, "competing claims did not produce exactly one winner")
            winner = winners[0]
            loser = 1 - winner
            token = values[winner]["token"]
            _require(ledger.get("author").owner == worker_ids[winner], "ledger owner differs from bound identity")
            renewed = _value(await sessions[winner].call_tool("lease_task", {
                "action": "renew", "task_id": "author", "token": token, "ttl_seconds": 60}))
            _require(renewed["token"] == token, "renew changed fencing token")
            _require(_value(await sessions[winner].call_tool("lease_task", {
                "action": "release", "task_id": "author", "token": token})) is True, "release failed")
            claimed_again = _value(await sessions[loser].call_tool("lease_task", {
                "action": "claim", "task_id": "author", "ttl_seconds": 60}))
            next_token = claimed_again["token"]
            _require(next_token > token, "new owner did not receive a higher fencing token")
            stale = await sessions[winner].call_tool("lease_task", {
                "action": "renew", "task_id": "author", "token": token, "ttl_seconds": 60})
            _require(stale.isError is True, "old holder was not rejected")
            _require(ledger.get("author").owner == worker_ids[loser], "stale call altered the current owner")
            _require(_value(await sessions[loser].call_tool("lease_task", {
                "action": "release", "task_id": "author", "token": next_token})) is True,
                "second owner could not release")
    snapshot = ledger.snapshot()
    _require(all(task.status == "available" and task.owner is None and task.result is None
                 for task in snapshot), "selfcheck left an owned or completed task")
    _require(not any(event["event"] == "research_execution" for event in ledger.audit()),
             "selfcheck unexpectedly executed research")
    _require((Path(paths["project"]) / "science/experiment.py").read_text(encoding="utf-8") == PENDING,
             "selfcheck changed the scientific candidate")
    return {"status": "passed", "validation": "contract_local", "transport": "official_mcp_stdio",
            "model_invoked": False, "experiment_invoked": False, "scientific_result": None,
            "tool_count": len(names), "workers": worker_ids, "winning_worker": worker_ids[winner],
            "first_token": token, "second_token": next_token, "old_token_rejected": True,
            "final_task_status": "available", "stdio_sessions_closed": True,
            "project": paths["project"], "state": paths["state"]}


def selfcheck(root: Path, python: Path) -> dict[str, object]:
    """Each invocation creates a new case; no reset or reuse of prior authority."""
    if not root.is_absolute():
        raise ValueError("selfcheck_root_must_be_absolute")
    no_links(root)
    root.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix="stdio-", dir=root))
    paths = prepare(run / "project", run / "state", python, swarm_id="stdio-" + uuid4().hex)
    result = asyncio.run(_check(paths))
    output = Path(paths["state"]) / "selfcheck-result.json"
    result["result_file"] = str(output)
    _write(output, result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    setup = commands.add_parser("prepare", help="Prepare a new NIST project and three fixed SWA descriptors")
    setup.add_argument("--project", type=Path, required=True)
    setup.add_argument("--state", type=Path, required=True)
    setup.add_argument("--python", type=Path, required=True)
    setup.add_argument("--swarm-id", default=None)
    setup.add_argument("--domain", default="127.0.0.1:8097")
    setup.add_argument("--api-key-env")
    check = commands.add_parser("selfcheck", help="Use two real stdio clients; no model or experiment")
    check.add_argument("--root", type=Path, required=True)
    check.add_argument("--python", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        result: object = prepare(args.project, args.state, args.python,
                                 swarm_id=args.swarm_id or uuid4().hex,
                                 domain=args.domain, api_key_env=args.api_key_env)
    else:
        result = selfcheck(args.root, args.python)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
