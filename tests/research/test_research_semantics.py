"""Research-semantics (M1) boundaries: sourced notes, branches, proposals, layering, idempotency."""
from __future__ import annotations

from pathlib import Path

import pytest

from contracts.identity import AgentId
from swarm.models import RunLimits, Signal
from swarm.research.models import HostConfig
from swarm.research.records import ResearchNote, SourceRef, WorkProposal
from swarm.research.service import ResearchService
from swarm.task_ledger import RunLimitReached, TaskLedger


def make_service(tmp_path: Path, worker: str = "native-a", instance: int = 0,
                 limits: RunLimits | None = None) -> ResearchService:
    config = HostConfig(ledger_path=str(tmp_path / "ledger.sqlite3"), swarm_id="research-semantics",
                        workspace=str(tmp_path / "project"), worker_id=worker,
                        agent=AgentId(role="builder", instance=instance), authorized_scopes=("science",),
                        capabilities=("research", "review"), assets_root=str(tmp_path / "assets"),
                        evidence_root=str(tmp_path / "evidence"))
    ledger = TaskLedger(config.ledger_path, config.swarm_id, limits=limits)
    return ResearchService(config, ledger=ledger)


def seed_project(service: ResearchService, project_id: str = "p1") -> None:
    service.create_project(project_id, "solve a Poisson PDE and compare solvers",
                           allowed_domains=("numerical_pde",), data_bounds={"data": "synthetic-only"})


def source(kind: str = "pdf", identifier: str = "https://example.invalid/paper.pdf",
           location: str = "p. 4, eq. (2)", retrieval: str = "present", version: str | None = None,
           license: str | None = None) -> SourceRef:
    return SourceRef(source_id=identifier + "#" + (location or ""), kind=kind, identifier=identifier,
                     version=version, license=license, retrieval=retrieval, location=location,
                     excerpt="the claimed excerpt")


def test_sourced_note_preserves_location_version_license_and_retrieval(tmp_path: Path) -> None:
    s = make_service(tmp_path)
    seed_project(s)
    ref = source(version="v3", license="CC-BY-4.0", retrieval="parse_failed", location="p. 9")
    note = s.submit_note("p1", "supporting_evidence", "method M appears applicable", source_refs=(ref,))
    assert note["review_state"] == "unverified"
    assert note["source_refs"][0]["version"] == "v3"
    assert note["source_refs"][0]["license"] == "CC-BY-4.0"
    assert note["source_refs"][0]["location"] == "p. 9"
    assert note["source_refs"][0]["retrieval"] == "parse_failed"
    ctx = s.research_context("p1")
    assert ctx["notes_unverified"][0]["note_id"] == note["note_id"]
    assert ctx["notes_verified"] == []


def test_evidence_note_requires_source_reference(tmp_path: Path) -> None:
    s = make_service(tmp_path)
    seed_project(s)
    for kind in ("observation", "supporting_evidence", "opposing_evidence"):
        with pytest.raises(ValueError, match="evidence_note_requires_source_reference"):
            s.submit_note("p1", kind, "no source here")


def test_expert_opinion_is_never_a_verified_fact(tmp_path: Path) -> None:
    s = make_service(tmp_path)
    seed_project(s)
    note = s.submit_note("p1", "expert_opinion", "Dr. X favors boundary method A",
                         signer="Dr. X", source_refs=(source(location="personal note"),))
    assert note["review_state"] == "unverified"
    assert note["signer"] == "Dr. X"
    with pytest.raises(ValueError, match="expert_opinion_is_never_verified_fact"):
        ResearchNote(note_id="x", project_id="p1", kind="expert_opinion", actor=s.config.agent,
                     signer="Dr. X", text="opinion", review_state="verified", created_at=0)
    ctx = s.research_context("p1")
    assert any(n["kind"] == "expert_opinion" for n in ctx["notes_unverified"])
    assert ctx["notes_verified"] == []


def test_hypothesis_note_registers_structured_hypothesis(tmp_path: Path) -> None:
    s = make_service(tmp_path)
    seed_project(s)
    note = s.submit_note("p1", "hypothesis", "PINN with soft boundary is more accurate",
                         source_refs=(source(kind="link"),))
    ctx = s.research_context("p1")
    assert any(h["hypothesis_id"] == note["note_id"] and h["claim"] == note["text"]
               for h in ctx["hypotheses"])


def test_propose_work_admits_task_inside_host_authorization(tmp_path: Path) -> None:
    s = make_service(tmp_path)
    seed_project(s)
    proposal = s.propose_work("p1", "experiment", "benchmark soft vs hard boundary",
                              "no member compared them", "a measured comparison",
                              source_refs=(source(kind="link"),))
    assert proposal["status"] == "accepted"
    assert proposal["task_id"] == proposal["proposal_id"]
    task = s.ledger.get(proposal["task_id"])
    assert task.signal.kind == "opportunity"
    assert task.signal.required_capability == "research"
    assert task.signal.scope == "science"
    assert task.acceptance["research_proposal_id"] == proposal["proposal_id"]
    assert task.owner is None
    assert [t["signal"]["task_id"] for t in s.discover()] == [proposal["task_id"]]


def test_propose_work_rejects_out_of_scope_and_unavailable_capability(tmp_path: Path) -> None:
    s = make_service(tmp_path)
    seed_project(s)
    with pytest.raises(PermissionError, match="scope_outside"):
        s.propose_work("p1", "question", "g", "j", "e", scope="private")
    with pytest.raises(PermissionError, match="capability_outside"):
        s.propose_work("p1", "question", "g", "j", "e", required_capability="admin")
    assert s.ledger.snapshot() == []


def test_proposal_and_note_are_idempotent_and_recovery_does_not_duplicate(tmp_path: Path) -> None:
    s = make_service(tmp_path)
    seed_project(s)
    first = s.propose_work("p1", "question", "g", "j", "e")
    second = s.propose_work("p1", "question", "g", "j", "e")
    assert first["proposal_id"] == second["proposal_id"]
    assert first["task_id"] == second["task_id"]
    assert [t.signal.task_id for t in s.ledger.snapshot()] == [first["task_id"]]
    note_a = s.submit_note("p1", "observation", "same observation", source_refs=(source(),))
    note_b = s.submit_note("p1", "observation", "same observation", source_refs=(source(),))
    assert note_a["note_id"] == note_b["note_id"]
    assert len(s.research_context("p1")["notes_unverified"]) == 1


def test_interrupted_admission_recovers_without_duplicate_task(tmp_path: Path) -> None:
    s = make_service(tmp_path)
    seed_project(s)
    # Simulate a crash after the knowledge write but before the ledger enqueue.
    s.knowledge.put_proposal(WorkProposal(
        proposal_id="seeded-prop", project_id="p1", kind="question", goal="g", justification="j",
        expected_contribution="e", scope="science", required_capability="research", dependencies=(),
        source_refs=(), actor=s.config.agent, status="proposed", created_at=s.ledger.now()))
    result = s.propose_work("p1", "question", "g", "j", "e")
    assert result["proposal_id"] == "seeded-prop"
    assert result["task_id"] == "seeded-prop"
    assert result["status"] == "accepted"
    assert [t.signal.task_id for t in s.ledger.snapshot()] == ["seeded-prop"]


def test_new_member_reads_shared_memory_for_continuation(tmp_path: Path) -> None:
    root = tmp_path
    a = make_service(root, worker="native-a", instance=0)
    seed_project(a)
    a.create_branch("p1", "b1", "soft boundary", "explore soft BC handling")
    a.submit_note("p1", "observation", "shared finding", branch_id="b1", source_refs=(source(),))
    a.propose_work("p1", "experiment", "verify soft BC", "based on shared finding", "a check", branch_id="b1")
    # A different member binds the same project and continues without re-pasting context.
    b = make_service(root, worker="native-b", instance=1)
    ctx = b.research_context("p1")
    assert ctx["project"]["project_id"] == "p1"
    assert [br["branch_id"] for br in ctx["branches"]] == ["b1"]
    assert any(n["text"] == "shared finding" for n in ctx["notes_unverified"])
    assert len(ctx["proposals"]) == 1


def test_derived_proposal_respects_derived_quota(tmp_path: Path) -> None:
    s = make_service(tmp_path, limits=RunLimits(max_derived_tasks=0))
    seed_project(s)
    s.ledger.enqueue(Signal(task_id="parent", workspace=s.config.workspace, scope="science",
                            kind="opportunity", required_capability="research", module="research"))
    with pytest.raises(RunLimitReached, match="max_derived_tasks"):
        s.propose_work("p1", "alternative_route", "g", "j", "e", derived_from="parent")


def test_discover_and_context_carry_task_linked_research_notes(tmp_path: Path) -> None:
    s = make_service(tmp_path)
    seed_project(s)
    proposal = s.propose_work("p1", "question", "g", "j", "e")
    task_id = proposal["task_id"]
    s.submit_note("p1", "observation", "note on this task", task_id=task_id, source_refs=(source(),))
    assert s.context(task_id)["research"]["notes"][0]["text"] == "note on this task"
    discovered = s.discover()
    assert discovered[0]["research"]["notes"][0]["task_id"] == task_id


def test_project_identity_is_immutable_and_persists_across_branches(tmp_path: Path) -> None:
    s = make_service(tmp_path)
    seed_project(s)
    s.create_branch("p1", "b1", "t", "g")
    s.create_branch("p1", "b2", "t2", "g2")
    with pytest.raises(ValueError, match="project_identity_cannot_change"):
        s.create_project("p1", "a different goal")
    # Branch creation never resets project-level knowledge.
    ctx = s.research_context("p1")
    assert {b["branch_id"] for b in ctx["branches"]} == {"b1", "b2"}
    assert ctx["project"]["goal"] == "solve a Poisson PDE and compare solvers"


def test_new_mcp_tools_round_trip_without_identity_grant(tmp_path: Path) -> None:
    import asyncio

    from swarm.research.server import create_server
    s = make_service(tmp_path)
    server = create_server(s)

    async def run() -> None:
        await server.call_tool("research_project", {"action": "create", "project_id": "p1",
                                                    "goal": "compare solvers"})
        _, note = await server.call_tool("submit_research_note", {
            "project_id": "p1", "kind": "expert_opinion", "text": "Dr. Y doubts A",
            "signer": "Dr. Y",
            "source_refs": [{"source_id": "s1", "kind": "text", "identifier": "memorandum",
                             "retrieval": "present", "location": "line 2"}]})
        assert note["review_state"] == "unverified"
        _, proposal = await server.call_tool("propose_research_work", {
            "project_id": "p1", "kind": "question", "goal": "g", "justification": "j",
            "expected_contribution": "e"})
        assert proposal["status"] == "accepted"
        assert s.ledger.get(proposal["task_id"]).owner is None

    asyncio.run(run())
