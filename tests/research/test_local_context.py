"""FR-04 selection through the original service and official MCP, offline only."""
import asyncio
import json
import sys
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from swarm.models import Signal
from swarm.research.server import create_server
from swarm.research.service import ResearchService
from tests.research.test_research_semantics import source
from tests.research.test_research_v1 import make_service


def task(s, name, branch, *, capability="research", scope="science", dependencies=()):
    s.ledger.enqueue(Signal(task_id=name, workspace=s.config.workspace, scope=scope,
        kind="opportunity", module="research", required_capability=capability,
        payload={"project_id": "p1", "branch_id": branch}), dependencies=dependencies)


def scene(tmp_path):
    s = make_service(tmp_path)
    s.create_project("p1", "compare finite difference methods", data_bounds={"data": "synthetic"})
    for b in ("focus", "dependency", "citation", "unrelated"):
        s.create_branch("p1", b, b, "inspect " + b)
    task(s, "dependency-task", "dependency", capability="analyst")
    lease = s.ledger.claim("dependency-task", "analyst", locality=s.locality)
    assert lease is not None
    s.ledger.submit(lease, "dependency-result-id", {"answer": "dependency-result"})
    task(s, "focus-task", "focus", dependencies=("dependency-task",))
    task(s, "other-task", "unrelated")
    cited = s.submit_note("p1", "dispute", "cited disagreement", branch_id="citation",
                          applicability={"mesh": "coarse only"}, source_refs=(source(version="v3"),))
    s.submit_note("p1", "observation", "focus evidence", branch_id="focus", task_id="focus-task",
                  references=(cited["note_id"],), source_refs=(source(location="p. 2"),))
    s.submit_note("p1", "observation", "dependency evidence", task_id="dependency-task",
                  branch_id="dependency", source_refs=(source(location="p. 3"),))
    s.submit_note("p1", "expert_opinion", "UNRELATED-NOTE", branch_id="unrelated")
    s.submit_note("p1", "expert_opinion", "UNCITED-NEIGHBOUR", branch_id="citation")
    return s, cited


def test_task_context_selects_branch_dependencies_and_explicit_references(tmp_path):
    s, cited = scene(tmp_path)
    before = [t.model_dump() for t in s.ledger.snapshot()]
    ctx = s.context("focus-task")
    local = ctx["research"]
    texts = {n["text"] for n in local["notes"]}
    assert {"focus evidence", "dependency evidence", "cited disagreement"} <= texts
    assert "UNRELATED-NOTE" not in json.dumps(ctx)
    assert "UNCITED-NEIGHBOUR" not in json.dumps(ctx)
    assert ctx["dependency_results"][0]["result"] == {"answer": "dependency-result"}
    note = next(n for n in local["notes"] if n["note_id"] == cited["note_id"])
    assert note["applicability"] == {"mesh": "coarse only"}
    assert note["source_refs"][0]["version"] == "v3"
    assert note["review_state"] == "unverified"
    assert local["selection"]["task_id"] == "focus-task"
    assert local["selection"]["claim_requires_recheck"] is True
    assert before == [t.model_dump() for t in s.ledger.snapshot()]
    with pytest.raises(PermissionError, match="capability"):
        s.claim("dependency-task")


def test_reference_walk_filters_permission_before_following_edges(tmp_path):
    s, _ = scene(tmp_path)
    task(s, "hidden-task", "focus", scope="private")
    broad = ResearchService(s.config.model_copy(update={"authorized_scopes": ("science", "private")}))
    bridge = broad.submit_note("p1", "hypothesis", "HIDDEN-CLAIM", task_id="hidden-task",
        branch_id="focus", references=("other-task",))
    s.submit_note("p1", "dispute", "review unavailable source", task_id="focus-task",
                  references=(bridge["note_id"], "hidden-task"))
    local = s.context("focus-task")["research"]
    assert "HIDDEN-CLAIM" not in json.dumps(local)
    assert "UNRELATED-NOTE" not in json.dumps(local)
    assert not any(h["hypothesis_id"] == bridge["note_id"] for h in local["hypotheses"])
    assert local["selection"]["unresolved_references"] is True
    with pytest.raises(PermissionError):
        s.research_context(task_id="hidden-task", overview=True)


def test_default_member_context_uses_capability_without_claim_or_full_broadcast(tmp_path):
    s = make_service(tmp_path)
    s.create_project("p1", "goal")
    for branch in ("analyst", "research"):
        s.create_branch("p1", branch, branch, branch)
        task(s, branch, branch, capability=branch)
        s.submit_note("p1", "expert_opinion", branch + "-only", task_id=branch, branch_id=branch)
        s.submit_note("p1", "hypothesis", branch + "-hypothesis", task_id=branch, branch_id=branch)
    ctx = s.research_context()
    assert "research-only" in json.dumps(ctx)
    assert "analyst-only" not in json.dumps(ctx)
    assert "analyst-hypothesis" not in json.dumps(ctx)
    assert ctx["selection"]["reason"] == "eligible_task"
    assert s.ledger.get("research").owner is None
    assert s.ledger.get("research").attempts == 0


def test_result_reference_reaches_original_read_only_ledger_result(tmp_path):
    s, _ = scene(tmp_path)
    task(s, "independent-focus", "focus")
    s.submit_note("p1", "dispute", "check recorded dependency result", task_id="independent-focus",
                  references=("dependency-result-id",))
    ctx = s.context("independent-focus")["research"]
    result = next(t for t in ctx["tasks"] if t["task_id"] == "dependency-task")
    assert result["result_id"] == "dependency-result-id"
    assert result["result"] == {"answer": "dependency-result"}
    assert result["status"] == "completed"
    assert result["required_capability"] == "analyst"


def test_new_member_without_tasks_has_goal_shared_background_and_branch_catalogue(tmp_path):
    s = make_service(tmp_path)
    s.create_project("p1", "goal")
    s.create_branch("p1", "b", "open question", "unsolved")
    s.submit_note("p1", "hypothesis", "shared open question")
    s.submit_note("p1", "expert_opinion", "branch detail", branch_id="b")
    ctx = s.research_context()
    assert ctx["project"]["goal"] == "goal"
    assert ctx["branches"][0]["goal"] == "unsolved"
    assert "shared open question" in json.dumps(ctx)
    assert "branch detail" not in json.dumps(ctx)
    assert ctx["selection"]["reason"] == "shared_background"
    assert "branch detail" in json.dumps(s.research_context(overview=True))
    assert "branch detail" in json.dumps(s.research_package())


def test_limit_applies_after_relevance_and_reports_incomplete_context(tmp_path):
    s, _ = scene(tmp_path)
    for i in range(5):
        s.submit_note("p1", "dispute", "focus-" + str(i), branch_id="focus")
        s.submit_note("p1", "dispute", "unrelated-" + str(i), branch_id="unrelated")
    ctx = s.research_context(task_id="focus-task", limit=2)
    assert len(ctx["notes_unverified"]) == 2 and ctx["notes_unverified_truncated"]
    assert len(ctx["events"]) == 2 and ctx["events_truncated"]
    assert all(e["branch_id"] != "unrelated" for e in ctx["events"])
    with pytest.raises((ValueError, PermissionError)):
        s.research_context(task_id="focus-task", branch_id="unrelated")
    with pytest.raises(PermissionError):
        s.research_context("other-project", overview=True)


def test_official_mcp_context_and_focus_use_same_selection(tmp_path):
    s, _ = scene(tmp_path)
    server = create_server(s)
    async def run():
        _, task_ctx = await server.call_tool("project_context", {"task_id": "focus-task"})
        _, project_ctx = await server.call_tool("research_project", {
            "action": "read", "project_id": "p1", "task_id": "focus-task"})
        assert task_ctx["research"]["notes_unverified"] == project_ctx["notes_unverified"]
        assert "cited disagreement" in json.dumps(task_ctx)
        assert "UNRELATED-NOTE" not in json.dumps(task_ctx)
        _, overview = await server.call_tool("research_project", {
            "action": "read", "project_id": "p1", "overview": True})
        assert "UNRELATED-NOTE" in json.dumps(overview)
    asyncio.run(run())


def test_official_stdio_member_local_context(tmp_path: Path):
    s, _ = scene(tmp_path)
    config = tmp_path / "context-host.json"
    config.write_text(s.config.model_dump_json(), encoding="utf-8")
    async def run():
        params = StdioServerParameters(command=sys.executable,
            args=["-I", "-m", "swarm.research", "--config", str(config)],
            env={"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"})
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                response = await session.call_tool("project_context", {"task_id": "focus-task", "limit": 50})
                assert not response.isError
                body = response.structuredContent
                assert "cited disagreement" in json.dumps(body)
                assert "UNRELATED-NOTE" not in json.dumps(body)
                assert body["research"]["selection"]["claim_requires_recheck"] is True
    asyncio.run(run())
