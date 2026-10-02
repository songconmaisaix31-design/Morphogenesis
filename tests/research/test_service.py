from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from contracts.identity import AgentId
from swarm.models import Signal
from swarm.research.models import HostConfig
from swarm.research.service import ResearchService
from swarm.task_ledger import LeaseLost, TaskConflict, TaskLedger


def make_service(tmp_path: Path, worker: str = "native-a", instance: int = 0,
                 clock: list[float] | None = None) -> ResearchService:
    config = HostConfig(ledger_path=str(tmp_path / "ledger.sqlite3"), swarm_id="research",
                        workspace=str(tmp_path / "project"), worker_id=worker,
                        agent=AgentId(role="builder", instance=instance), authorized_scopes=("science",),
                        capabilities=("research",), assets_root=str(tmp_path / "assets"),
                        evidence_root=str(tmp_path / "evidence"))
    ledger = TaskLedger(config.ledger_path, config.swarm_id, clock=(lambda: clock[0]) if clock else __import__("time").time)
    return ResearchService(config, ledger=ledger)


def enqueue(service: ResearchService, task_id: str = "original", scope: str = "science",
            capability: str = "research") -> None:
    service.ledger.enqueue(Signal(task_id=task_id, workspace=service.config.workspace, scope=scope,
                                 kind="opportunity", required_capability=capability,
                                 payload={"paper": "https://www.itl.nist.gov/div898/strd/univ/data/NumAcc4.dat"}),
                           acceptance={"experiment_plan": {"plan_id": "nist-numacc4-v1"}})


def test_active_discovery_scope_and_capabilities_are_host_bound(tmp_path: Path) -> None:
    s = make_service(tmp_path)
    enqueue(s)
    enqueue(s, "forbidden", "private")
    enqueue(s, "unqualified", capability="admin")
    assert [t["signal"]["task_id"] for t in s.discover()] == ["original"]
    assert s.ledger.get("original").owner is None
    for task in ("forbidden", "unqualified"):
        with pytest.raises(PermissionError):
            s.claim(task)
    with pytest.raises(PermissionError):
        s.context("forbidden")
    assert s.context("unqualified")["task"]["signal"]["task_id"] == "unqualified"
    assert s.context("original")["worker_id"] == "native-a"


def test_real_ledger_stale_holder_cannot_renew_release_handoff_or_execute(tmp_path: Path) -> None:
    now = [100.0]
    a = make_service(tmp_path, clock=now)
    b = make_service(tmp_path, "native-b", 1, now)
    enqueue(a)
    held = a.claim("original", ttl_seconds=1)
    assert held is not None
    now[0] = 102.0
    second = b.claim("original", ttl_seconds=10)
    assert second and second["token"] == 2
    for operation in (lambda: a.renew("original", 1), lambda: a.release("original", 1),
                      lambda: a.handoff("original", 1, "native-b"),
                      lambda: asyncio.run(a.execute("original", 1))):
        with pytest.raises(LeaseLost):
            operation()
    assert b.ledger.get("original").owner == "native-b"


def test_renewal_durable_and_handoff_does_not_assign(tmp_path: Path) -> None:
    s = make_service(tmp_path)
    enqueue(s)
    assert s.claim("original")
    s.renew("original", 1)
    assert any(e["event"] == "renewed" and e["body"]["token"] == 1 for e in s.ledger.audit())
    s.handoff("original", 1, "native-b", {"notes": "preserved"})
    assert s.ledger.get("original").owner is None
    assert s.ledger.get("original").result == {"notes": "preserved"}


class Backend:
    def __init__(self, service: ResearchService, state: str = "unknown", crash: bool = False) -> None:
        self.service, self.state, self.crash, self.calls = service, state, crash, 0

    async def execute(self, plan, run_id, lease):
        self.calls += 1
        # A real independent SQLite writer succeeds during the external call.
        TaskLedger(self.service.ledger.path, "research").record_event("external_no_lock", {})
        if self.crash:
            raise TimeoutError("original external failure")
        return {"execution_state": self.state, "effect_state": "unknown" if self.state == "unknown" else "confirmed",
                "exit_code": None if self.state == "unknown" else 0, "usage": None, "cost": None}

    def read(self, run_id):
        return {}

    def evaluate(self, run_id, plan, lease):
        return {}


@pytest.mark.parametrize("crash", [False, True])
def test_unknown_never_replayed_or_promoted_and_call_has_no_sqlite_lock(tmp_path: Path, crash: bool) -> None:
    s = make_service(tmp_path)
    enqueue(s)
    assert s.claim("original")
    backend = Backend(s, crash=crash)
    s.backend = backend
    if crash:
        with pytest.raises(TimeoutError, match="original external failure"):
            asyncio.run(s.execute("original", 1))
    else:
        result = asyncio.run(s.execute("original", 1))
        assert result["result"]["exit_code"] is None
    with pytest.raises(TaskConflict, match="unconfirmed"):
        asyncio.run(s.execute("original", 1))
    with pytest.raises(TaskConflict, match="unconfirmed"):
        s.ledger.assert_execution_confirmed(s._lease("original", 1))
    assert backend.calls == 1
    assert s.release("original", 1)
    assert s.ledger.get("original").status == "blocked"
    assert s.discover() == []


def test_mcp_tools_have_no_identity_database_or_metric_write_parameters(tmp_path: Path) -> None:
    from swarm.research.server import create_server
    server = create_server(make_service(tmp_path))
    tools = asyncio.run(server.list_tools())
    for tool in tools:
        assert not {"worker_id", "agent", "ledger_path", "passed", "approved", "metric"} & tool.inputSchema.get("properties", {}).keys()
    assert len(tools) == 21
    assert {t.name for t in tools} >= {"discover_tasks", "lease_task", "research_experiment", "verify_research", "inherit_experience"}


def test_consolidated_tools_reject_cross_action_arguments_and_stale_holder(tmp_path: Path) -> None:
    from swarm.research.server import create_server
    from mcp.server.fastmcp.exceptions import ToolError
    s = make_service(tmp_path)
    enqueue(s)
    server = create_server(s)
    async def run():
        with pytest.raises(ToolError, match="claim_accepts_only"):
            await server.call_tool("lease_task", {"action": "claim", "task_id": "original", "token": 100})
        await server.call_tool("lease_task", {"action": "claim", "task_id": "original"})
        assert s.ledger.get("original").owner == "native-a"
        with pytest.raises(ToolError, match="current_fencing_token_required"):
            await server.call_tool("lease_task", {"action": "renew", "task_id": "original"})
        with pytest.raises(ToolError, match="request_or_run"):
            await server.call_tool("research_experiment", {"action": "run", "task_id": "original", "token": 1, "run_id": "replay"})
        with pytest.raises(ToolError, match="validate_files_requires"):
            await server.call_tool("research_candidate", {"action": "validate_files", "task_id": "original", "token": 1})
    asyncio.run(run())


@pytest.mark.parametrize("effect", [None, "unexpected"])
def test_missing_or_unrecognised_effect_is_unconfirmed_not_retryable(tmp_path: Path, effect) -> None:
    s = make_service(tmp_path)
    enqueue(s)
    assert s.claim("original")
    backend = Backend(s, state="succeeded")
    original = backend.execute
    async def incomplete(plan, run_id, lease):
        result = await original(plan, run_id, lease)
        if effect is None:
            del result["effect_state"]
        else:
            result["effect_state"] = effect
        return result
    backend.execute = incomplete
    s.backend = backend
    asyncio.run(s.execute("original", 1))
    with pytest.raises(TaskConflict, match="unconfirmed"):
        asyncio.run(s.execute("original", 1))
    assert backend.calls == 1
    assert s.release("original", 1)
    assert s.ledger.get("original").status == "blocked"


def test_confirmed_experiment_is_bounded_by_host_without_extra_call(tmp_path: Path) -> None:
    s = make_service(tmp_path)
    enqueue(s)
    assert s.claim("original")
    backend = Backend(s, state="succeeded")
    s.backend = backend
    asyncio.run(s.execute("original", 1))
    with pytest.raises(TaskConflict, match="host_experiment_limit"):
        asyncio.run(s.execute("original", 1))
    assert backend.calls == 1


def test_blocking_candidate_validation_does_not_block_real_lease_renewal(tmp_path: Path, monkeypatch) -> None:
    import threading
    from swarm.research.server import create_server
    service = make_service(tmp_path)
    enqueue(service)
    assert service.claim("original")
    entered, release = threading.Event(), threading.Event()

    def blocking_validation(task_id, token, asset_id):
        service._lease(task_id, token)
        entered.set()
        release.wait(timeout=1)
        service._lease(task_id, token)
        return {"fixture_finished": True}

    monkeypatch.setattr(service, "validate_files", blocking_validation)
    server = create_server(service)

    async def run():
        validation = asyncio.create_task(server.call_tool("research_candidate", {
            "action": "validate_files", "task_id": "original", "token": 1, "asset_id": "owned-fixture"}))
        try:
            assert await asyncio.to_thread(entered.wait, 2)
            assert not validation.done(), "sync validation occupied the MCP event loop"
            await server.call_tool("lease_task", {"action": "renew", "task_id": "original", "token": 1})
            assert any(e["event"] == "renewed" and e["body"]["token"] == 1 for e in service.ledger.audit())
            assert not release.is_set()
        finally:
            release.set()
            await validation

    asyncio.run(run())
