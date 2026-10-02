"""research-v1 wiring: three-axis advisory, acceptance, lifecycle, discovery enrichment."""
from __future__ import annotations

from pathlib import Path

import pytest

from contracts.identity import AgentId
from swarm.research.models import HostConfig
from swarm.research.service import ResearchService
from swarm.task_ledger import TaskLedger


def make_service(tmp_path: Path, project_id: str = "p1") -> ResearchService:
    config = HostConfig(ledger_path=str(tmp_path / "ledger.sqlite3"), swarm_id="research-v1",
                        workspace=str(tmp_path / "project"), worker_id="reviewer-a",
                        agent=AgentId(role="reviewer", instance=0), authorized_scopes=("science",),
                        capabilities=("research", "review"), assets_root=str(tmp_path / "assets"),
                        evidence_root=str(tmp_path / "evidence"), project_id=project_id)
    ledger = TaskLedger(config.ledger_path, config.swarm_id)
    return ResearchService(config, ledger=ledger)


def test_accept_unknown_result_is_rejected_not_crash(tmp_path: Path) -> None:
    s = make_service(tmp_path)
    s.create_project("p1", "goal")
    decision = s.accept_result("forged-result-id")
    assert decision["accepted"] is False
    assert decision["state"] == "rejected"
    assert decision["reasons"] == ["untrusted_result"]


def test_advisory_and_snapshot_are_advisory_only_and_consume_branches(tmp_path: Path) -> None:
    s = make_service(tmp_path)
    s.create_project("p1", "goal")
    s.create_branch("p1", "b1", "soft boundary", "explore soft BC")
    advisory = s.research_advisory("p1")
    assert advisory["advisory_only"] is True
    assert advisory["claim_requires_recheck"] is True
    assert advisory["policy_version"] == "research-v1"
    assert advisory["contributions"] == []
    opportunities = advisory["opportunities"]["opportunities"]
    assert any(op["branch_id"] == "b1" for op in opportunities)
    snapshot = s.research_snapshot("p1")
    assert snapshot["policy_version"] == "research-v1"
    assert snapshot["three_axis"] == {"execution": {}, "hypothesis": {}, "contribution": {}}
    assert snapshot["branches"][0]["branch_id"] == "b1"


def test_correction_and_supersession_append_without_deleting(tmp_path: Path) -> None:
    s = make_service(tmp_path)
    s.create_project("p1", "goal")
    s.create_branch("p1", "b1", "branch", "explore")
    note = s.submit_note("p1", "expert_opinion", "consider pausing")
    correction = s.record_correction("b1", "sleep", "low value", note["note_id"])
    assert correction["kind"] == "sleep"
    assert correction["actor"] == "reviewer-a"
    with pytest.raises(PermissionError, match="contribution_outside"):
        s.record_supersession("result-1", "superseded", note["note_id"], superseded_by="result-2")
    snapshot = s.research_snapshot("p1")
    assert snapshot["corrections"][0]["kind"] == "sleep"
    assert snapshot["supersessions"] == []
    assert snapshot["contributions"] == []
    assert snapshot["branches"][0]["status"] == "dormant"
    assert s.knowledge.branch("b1").status == "proposed"


def test_sleep_reopen_and_claim_recheck_preserve_history(tmp_path: Path) -> None:
    s = make_service(tmp_path)
    s.create_project("p1", "goal")
    s.create_branch("p1", "b1", "branch", "explore")
    task = s.propose_work("p1", "question", "g", "j", "e", branch_id="b1")["task_id"]
    note = s.submit_note("p1", "expert_opinion", "pause to inspect assumptions")
    assert s.choose(task, reason="inspect this branch")["selected"] == task
    first = s.record_correction("b1", "sleep", "assumptions need review", note["note_id"])
    assert s.record_correction("b1", "sleep", "assumptions need review", note["note_id"]) == first
    assert s.discover() == []
    with pytest.raises(PermissionError, match="branch_not_active"):
        s.claim(task)
    s.record_correction("b1", "reopen", "review completed", note["note_id"])
    lease = s.claim(task)
    assert lease["research_selection"]["actual_task_id"] == task
    assert len(s.research_snapshot()["corrections"]) == 2
    assert s.knowledge.branch("b1").status == "proposed"


def test_shared_ledger_projects_cannot_read_choose_claim_or_correct_each_other(tmp_path: Path) -> None:
    a = make_service(tmp_path)
    a.create_project("p1", "goal")
    a.create_branch("p1", "b1", "one", "first")
    b = make_service(tmp_path, "p2")
    b.create_project("p2", "private goal")
    b.create_branch("p2", "private-branch", "private", "private")
    private = b.propose_work("p2", "question", "PRIVATE_SENTINEL", "j", "e", branch_id="private-branch")
    a.propose_work("p1", "question", "public", "j", "e", branch_id="b1")
    assert "PRIVATE_SENTINEL" not in str(a.discover())
    with pytest.raises(PermissionError, match="host_project"):
        a.context(private["task_id"])
    with pytest.raises(PermissionError, match="host_project"):
        a.claim(private["task_id"])
    with pytest.raises(PermissionError, match="legal_opportunity"):
        a.choose(private["task_id"])
    with pytest.raises(ValueError, match="belong_to_project"):
        a.record_correction("private-branch", "sleep", "r", "s")
    assert b.feedback_store.corrections() == []


def test_envelope_is_host_approved_and_cannot_reset_with_new_run(tmp_path: Path) -> None:
    from swarm.research.models import ResearchEnvelope
    from swarm.models import BudgetPolicy, ExecutionBound, RunLimits
    limits = RunLimits(max_attempts=3)
    initial = make_service(tmp_path)
    config = initial.config.model_copy(update={
        "authorization_ref": "approved-a", "research_envelope": ResearchEnvelope(
            goal="approved goal", allowed_domains=("math",), data_bounds={"data": "local-only"}, limits=limits),
        "research_budget_path": str(tmp_path / "budget.sqlite3"),
        "research_budget_policy": BudgetPolicy(max_cost_usd=1.0, unbounded_reservation_usd=0.2, limits=limits),
        "research_execution_bound": ExecutionBound(provider="mock", model="fixture", input_tokens=0, max_output_tokens=0)})
    # A distinct original ledger is initialized with the host limits, not an old
    # ledger silently reconfigured to those limits.
    config = config.model_copy(update={"ledger_path": str(tmp_path / "approved-ledger.sqlite3")})
    a = ResearchService(config)
    with pytest.raises(PermissionError, match="host_envelope"):
        a.create_project("p1", "approved goal", data_bounds={"data": "external"})
    project = a.create_project("p1", "approved goal")
    assert project["data_bounds"] == {"data": "local-only"}
    assert a.create_project("p1", "approved goal") == project
    a.budget.reserve("reviewer-a", "task", config.research_execution_bound, request_id="request")
    again = ResearchService(config)
    assert again.budget.snapshot().pending_reservations == 1
    from swarm.budget import BudgetBlocked
    with pytest.raises(BudgetBlocked, match="pending_request_requires_reconciliation"):
        again._budget_ready()
    changed = ResearchService(config.model_copy(update={"swarm_id": "replacement-run"}))
    with pytest.raises(PermissionError, match="host_envelope_changed"):
        changed.project()
    assert changed.budget.snapshot().pending_reservations == 1


def test_discover_enriches_research_v1_alongside_legacy_v01(tmp_path: Path) -> None:
    s = make_service(tmp_path)
    s.create_project("p1", "goal")
    s.create_branch("p1", "b1", "t", "g")
    proposal = s.propose_work("p1", "question", "g", "j", "e", branch_id="b1")
    discovered = s.discover()
    assert discovered[0]["signal"]["task_id"] == proposal["task_id"]
    assert discovered[0]["policy_recommendation"]["policy_version"] == "v0.1"
    assert discovered[0]["research_v1"]["policy_version"] == "research-v1"
    assert discovered[0]["research_v1"]["advisory_only"] is True


def test_reviewer_is_host_bound_not_caller_supplied(tmp_path: Path) -> None:
    import asyncio

    from swarm.research.server import create_server
    s = make_service(tmp_path)
    s.create_project("p1", "goal")
    server = create_server(s)
    tools = asyncio.run(server.list_tools())
    accept = next(t for t in tools if t.name == "accept_result")
    assert "reviewer" not in accept.inputSchema.get("properties", {})
    assert "worker_id" not in accept.inputSchema.get("properties", {})
    assert set(accept.inputSchema.get("properties", {})) == {"result_id"}


def test_accept_result_mcp_rejects_unknown_id(tmp_path: Path) -> None:
    import asyncio

    from swarm.research.server import create_server
    s = make_service(tmp_path)
    s.create_project("p1", "goal")
    server = create_server(s)

    async def run() -> None:
        _, decision = await server.call_tool("accept_result", {"result_id": "forged"})
        assert decision["accepted"] is False
        assert decision["reasons"] == ["untrusted_result"]

    asyncio.run(run())
