"""Formal research service: authorization, identity, and durable admission."""
from pathlib import Path

import pytest

from contracts.identity import AgentId
from swarm.models import RunLimits, Signal
from swarm.research.models import HostConfig
from swarm.research.records import ResearchBranch, ResearchEvent, ResearchProject
from swarm.research.service import ResearchService
from swarm.research.server import create_server
from swarm.task_ledger import RunLimitReached, TaskLedger


def service(root: Path, project="p1", limits=None):
    config = HostConfig(ledger_path=str(root / "ledger.db"), swarm_id="q-security",
                        workspace=str(root / "workspace"), worker_id="q",
                        agent=AgentId(role="builder", instance=0), authorized_scopes=("science",),
                        capabilities=("research",), assets_root=str(root / "assets"),
                        evidence_root=str(root / "evidence"), project_id=project,
                        authorization_ref="host-authority")
    ledger = TaskLedger(config.ledger_path, config.swarm_id, clock=lambda: 100.0, limits=limits)
    return ResearchService(config, ledger=ledger)


def seeded(root):
    s = service(root)
    s.create_project("p1", "trusted project")
    # Trusted fixture seeding of another project sharing the same ledger.
    s.knowledge.put_project(ResearchProject(project_id="p2", goal="other", created_at=100))
    s.knowledge.put_branch(ResearchBranch(branch_id="foreign", project_id="p2",
                                        title="other", goal="other", created_at=100))
    return s


@pytest.mark.parametrize("operation", ["read", "context", "branch", "note", "proposal", "create"])
def test_host_project_cannot_be_overridden(tmp_path, operation):
    s = seeded(tmp_path)
    calls = {
        "read": lambda: s.project("p2"),
        "context": lambda: s.research_context("p2"),
        "branch": lambda: s.create_branch("p2", "intruder", "x", "x"),
        "note": lambda: s.submit_note("p2", "hypothesis", "intrusion"),
        "proposal": lambda: s.propose_work("p2", "question", "g", "j", "e"),
        "create": lambda: s.create_project("p3", "intrusion"),
    }
    with pytest.raises((PermissionError, ValueError)):
        calls[operation]()
    assert s.ledger.snapshot() == []


def test_caller_cannot_replace_host_authorization(tmp_path):
    s = service(tmp_path)
    try:
        s.create_project("p1", "g", authorization_ref="caller-granted-admin")
    except (PermissionError, ValueError):
        return
    # Refusal and ignored extra input are both safe. Prove the durable authority
    # rather than requiring a particular error style from the owner.
    assert s.knowledge.project("p1").authorization_ref == s.config.authorization_ref
    assert service(tmp_path).project("p1")["authorization_ref"] == "host-authority"


@pytest.mark.parametrize("operation", ["parent", "note", "proposal"])
def test_cross_project_branch_rejected(tmp_path, operation):
    s = seeded(tmp_path)
    with pytest.raises((PermissionError, ValueError)):
        if operation == "parent":
            s.create_branch("p1", "child", "x", "x", parent_branch_id="foreign")
        elif operation == "note":
            s.submit_note("p1", "hypothesis", "x", branch_id="foreign")
        else:
            s.propose_work("p1", "question", "g", "j", "e", branch_id="foreign")
    assert s.ledger.snapshot() == []


@pytest.mark.parametrize("kwargs", [{"scope": "../private"}, {"required_capability": "admin"}])
def test_proposal_cannot_expand_scope_or_capability(tmp_path, kwargs):
    s = seeded(tmp_path)
    with pytest.raises(PermissionError):
        s.propose_work("p1", "question", "g", "j", "e", **kwargs)
    assert s.ledger.snapshot() == []


def test_out_of_scope_derived_source_rejected(tmp_path):
    s = seeded(tmp_path)
    s.ledger.enqueue(Signal(task_id="foreign-task", workspace=s.config.workspace,
                            scope="private", kind="opportunity", required_capability="research"))
    with pytest.raises((PermissionError, ValueError)):
        s.propose_work("p1", "question", "g", "j", "e", derived_from="foreign-task")
    assert len(s.ledger.snapshot()) == 1


@pytest.mark.parametrize("cut", ["after_put", "after_enqueue", "after_bind"])
def test_admission_recovery_after_each_durable_boundary(tmp_path, monkeypatch, cut):
    s = seeded(tmp_path)
    obj, name = {
        "after_put": (s.knowledge, "put_proposal"),
        "after_enqueue": (s.ledger, "enqueue"),
        "after_bind": (s.knowledge, "bind_proposal"),
    }[cut]
    original = getattr(obj, name)

    def interrupted(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError("Q deterministic crash after durable write")

    monkeypatch.setattr(obj, name, interrupted)
    with pytest.raises(RuntimeError, match="Q deterministic crash"):
        s.propose_work("p1", "question", "g", "j", "e")
    # Reopen stores to ensure recovery uses durable state rather than memory.
    reopened = service(tmp_path)
    result = reopened.propose_work("p1", "question", "g", "j", "e")
    assert result["status"] == "accepted"
    assert len(reopened.ledger.snapshot()) == 1
    assert reopened.ledger.get(result["task_id"]).signal.task_id == result["proposal_id"]
    assert reopened.propose_work("p1", "question", "g", "j", "e") == result


def test_same_branch_id_different_payload_rejected(tmp_path):
    s = seeded(tmp_path)
    s.create_branch("p1", "same", "original", "original")
    with pytest.raises((ValueError, PermissionError)):
        s.create_branch("p1", "same", "rewritten", "rewritten")
    assert s.knowledge.branch("same").goal == "original"


def test_same_event_id_different_payload_rejected(tmp_path):
    s = seeded(tmp_path)
    event = ResearchEvent(event_id="same", project_id="p1", actor=s.config.agent,
                          at=100, schema_version="research-v1", event_kind="note", payload={"value": 1})
    s.knowledge.record(event)
    with pytest.raises(ValueError):
        s.knowledge.record(event.model_copy(update={"payload": {"value": 2}}))
    assert [e.payload for e in s.knowledge.events("p1") if e.event_id == "same"] == [{"value": 1}]


def test_authorized_research_stays_unverified_and_claim_is_voluntary(tmp_path):
    s = seeded(tmp_path)
    s.create_branch("p1", "own", "authorized", "authorized")
    note = s.submit_note("p1", "hypothesis", "candidate idea", branch_id="own")
    assert note["review_state"] == "unverified"
    proposal = s.propose_work("p1", "question", "g", "j", "e", branch_id="own")
    assert s.ledger.get(proposal["task_id"]).owner is None
    lease = s.claim(proposal["task_id"])
    assert lease is not None
    assert s.ledger.get(proposal["task_id"]).owner == s.config.worker_id


@pytest.mark.parametrize("field", ["scope", "capability", "dependency"])
def test_exploration_cannot_bypass_ledger_claim_permissions(tmp_path, field):
    s = seeded(tmp_path)
    if field == "dependency":
        s.ledger.enqueue(Signal(task_id="unfinished", workspace=s.config.workspace,
                                scope="science", kind="opportunity", required_capability="research"))
    s.ledger.enqueue(Signal(task_id="forbidden", workspace=s.config.workspace,
                            scope="private" if field == "scope" else "science",
                            kind="opportunity", required_capability="admin" if field == "capability" else "research"),
                     dependencies=("unfinished",) if field == "dependency" else ())
    try:
        lease = s.claim("forbidden")
    except PermissionError:
        lease = None
    assert lease is None
    assert s.ledger.get("forbidden").owner is None


def test_branch_and_member_reopen_do_not_reset_task_envelope(tmp_path):
    limits = RunLimits(max_tasks=1)
    s = service(tmp_path, limits=limits)
    s.create_project("p1", "g")
    s.create_branch("p1", "b1", "first", "first")
    s.propose_work("p1", "question", "first", "j", "e", branch_id="b1")
    s.create_branch("p1", "b2", "second", "second")
    reopened = service(tmp_path, limits=limits)
    with pytest.raises(RunLimitReached):
        reopened.propose_work("p1", "question", "second", "j", "e", branch_id="b2")
    assert len(reopened.ledger.snapshot()) == 1


def test_note_link_to_private_task_rejected(tmp_path):
    s = seeded(tmp_path)
    s.ledger.enqueue(Signal(task_id="private", workspace=s.config.workspace,
                            scope="private", kind="opportunity", required_capability="research"))
    with pytest.raises((PermissionError, ValueError)):
        s.submit_note("p1", "hypothesis", "leak", task_id="private")


def test_official_mcp_tool_arguments_cannot_impersonate_host(tmp_path, deny_candidate_execution_and_network):
    from mcp.server.fastmcp.exceptions import ToolError

    s = seeded(tmp_path)
    s.ledger.enqueue(Signal(task_id="authorized", workspace=s.config.workspace, scope="science",
                            kind="opportunity", required_capability="research",
                            payload={"project_id": "p1"}))
    server = create_server(s)

    async def call():
        tools = await server.list_tools()
        lease_tool = next(t for t in tools if t.name == "lease_task")
        assert "worker_id" not in lease_tool.inputSchema.get("properties", {})
        try:
            await server.call_tool("lease_task", {"action": "claim", "task_id": "authorized",
                "worker_id": "impersonated", "scope": "private", "capabilities": ["admin"],
                "authorization_ref": "caller-granted"})
        except ToolError:
            await server.call_tool("lease_task", {"action": "claim", "task_id": "authorized"})

    deny_candidate_execution_and_network.run_until_complete(call())
    assert s.ledger.get("authorized").owner == s.config.worker_id
    assert s.config.authorized_scopes == ("science",)
    assert s.config.capabilities == ("research",)
    assert s.config.authorization_ref == "host-authority"


def test_official_mcp_cross_project_access_refused(tmp_path, deny_candidate_execution_and_network):
    from mcp.server.fastmcp.exceptions import ToolError

    s = seeded(tmp_path)
    server = create_server(s)
    with pytest.raises(ToolError):
        deny_candidate_execution_and_network.run_until_complete(
            server.call_tool("research_project", {"action": "read", "project_id": "p2"}))
