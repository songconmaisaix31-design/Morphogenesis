"""Unmodified installed-origin gate, protected factory and actual HTTP handlers.

The HTTP transport is in process under the socket deny fixture. No fake core
metadata, backend injection, native adapter or candidate process is used.
"""
import json
import os
import sqlite3
import sysconfig
from email.message import Message
from pathlib import Path
from types import SimpleNamespace

import pytest

if os.environ.get("R1_SECURITY_INSTALLED") != "1":
    pytest.skip("exact noneditable core/product pair not selected; factory NOT_RUN", allow_module_level=True)

import swarm
import morph_research
from contracts.identity import AgentId
from morph_research.config import installed_core
from morph_research.r1_config import ConfiguredResearch, ResearchConnection, ResearchMember
from morph_research.web.r1 import R1Spaces
from morph_research.web.server import Handler
from morph_research.web.spaces import ServeConfig
from tests.integration.r1_security.test_a_project_budget_boundaries import host

SPACE = "a" * 32


@pytest.fixture
def configured(tmp_path):
    core = host(tmp_path / "core")
    Path(core.workspace).mkdir(parents=True)
    materials = tmp_path / "materials"
    materials.mkdir()
    envelope = core.research_envelope.model_copy(update={"data_bounds": {"local_import_roots": json.dumps([str(materials)])}})
    core = core.model_copy(update={"research_envelope": envelope})
    members = []
    tokens = {}
    for index, worker in enumerate(("member-one", "member-two")):
        selected = core.model_copy(update={"worker_id": worker, "agent": AgentId(role="builder", instance=index)})
        path = tmp_path / (worker + "-host.json")
        path.write_text(selected.model_dump_json(), encoding="utf-8")
        token_path = tmp_path / (worker + ".key")
        tokens[worker] = "q-installed-fixture-" + worker + "-" + "x" * 48
        token_path.write_text(tokens[worker], encoding="ascii")
        members.append(ResearchMember(id=worker, host_config=path, http_token_file=token_path))
    connection = ResearchConnection(space_id=SPACE, name="Q configured research", ingress_member="member-one", members=tuple(members))
    config = ServeConfig(root=tmp_path / "product", case_directory=tmp_path / "cases",
        sandbox_domain="127.0.0.1:65534", allowed_import_dirs=(str(materials),), research_connections=(connection,))
    spaces = R1Spaces(config)
    connected = ConfiguredResearch(config, spaces)
    try:
        yield SimpleNamespace(config=config, connected=connected, spaces=spaces, materials=materials, hosts=members,
                              tokens=tokens)
    finally:
        spaces.close()


def handler(f, fields, loop, monkeypatch, authorization=None):
    from morph_research.web import server

    monkeypatch.setattr(server.asyncio, "run", loop.run_until_complete)
    request = object.__new__(Handler)
    request.server = SimpleNamespace(r1=f.spaces, spaces=SimpleNamespace(config=f.config),
        configured_research=f.connected, backend_for=f.connected.backend)
    request.form = lambda **kwargs: fields
    request.headers = Message()
    if authorization is not None:
        request.headers.add_header("Authorization", authorization)
    responses = []
    request.reply = lambda code, body: responses.append((code, body))
    return request, responses


def tool(f, loop, monkeypatch, member, name, **arguments):
    request, responses = handler(f, {"arguments": arguments}, loop, monkeypatch, "Bearer " + f.tokens[member])
    request.route_research(f"/api/research-spaces/{SPACE}/members/{member}/tools/{name}", True)
    assert len(responses) == 1 and responses[0][0] == 200
    body = responses[0][1]
    assert body["acceptance"] == "core_tool_response"
    result = body["result"][1]
    return result["result"] if set(result) == {"result"} else result


def test_exact_installed_factory_keeps_two_original_host_identities(configured):
    f = configured
    origin = installed_core()  # real product VCS-pin check, never mocked
    assert origin["core_sha"] == morph_research.CORE_SHA
    purelib = Path(sysconfig.get_paths()["purelib"]).resolve()
    assert Path(swarm.__file__).resolve().is_relative_to(purelib)
    assert Path(morph_research.__file__).resolve().is_relative_to(purelib)
    first = f.connected.backend(SPACE, "member-one").service
    second = f.connected.backend(SPACE, "member-two").service
    assert first.ledger.path == second.ledger.path
    assert first.config.project_id == second.config.project_id == "q-project"
    assert (first.config.worker_id, second.config.worker_id) == ("member-one", "member-two")
    assert first.store.root == second.store.root and first.budget.path == second.budget.path
    with pytest.raises(KeyError):
        f.connected.backend(SPACE, "caller-invented-member")
    assert first.ledger.snapshot() == [] and first.store.adoptions() == []


def test_actual_configured_handler_mcp_claim_and_stale_release(configured, monkeypatch, deny_candidate_execution_and_network):
    f, loop = configured, deny_candidate_execution_and_network
    proposal = tool(f, loop, monkeypatch, "member-two", "propose_research_work", project_id="q-project",
        kind="question", goal="Q bounded question", justification="fixture", expected_contribution="question")
    task = proposal["task_id"]
    lease = tool(f, loop, monkeypatch, "member-two", "lease_task", action="claim", task_id=task)
    service = f.connected.backend(SPACE, "member-two").service
    assert lease["worker_id"] == service.ledger.get(task).owner == "member-two"
    with pytest.raises(RuntimeError, match="core_tool_refused"):
        tool(f, loop, monkeypatch, "member-two", "lease_task", action="release", task_id=task, token=lease["token"] + 1)
    assert service.ledger.get(task).owner == "member-two"
    tool(f, loop, monkeypatch, "member-two", "lease_task", action="release", task_id=task, token=lease["token"])
    with pytest.raises(RuntimeError, match="core_tool_refused"):
        tool(f, loop, monkeypatch, "member-two", "research_project", action="read", project_id="foreign-project")
    assert service.store.adoptions() == []


def test_actual_source_handler_preserves_two_versions_and_links_correct_core_notes(configured, monkeypatch,
        deny_candidate_execution_and_network):
    f = configured
    material = f.materials / "inert.txt"
    material.write_text("Q source version one", encoding="utf-8")
    for version, text in (("v1", "Q source version one"), ("v2", "Q source version two")):
        material.write_text(text, encoding="utf-8")
        request, responses = handler(f, {"kind": "text", "identifier": str(material), "version": version},
                                     deny_candidate_execution_and_network, monkeypatch)
        request.route_research(f"/api/research-spaces/{SPACE}/sources", True)
        assert responses[0][0] == 201
    saved = f.spaces.store(SPACE).sources(SPACE)
    assert len(saved) == 2 and {source["version"] for source in saved} == {"v1", "v2"}
    service = f.connected.backend(SPACE).service
    notes = service.knowledge.notes("q-project")
    refs = {ref.source_id for note in notes for ref in note.source_refs}
    assert refs == {source["id"] for source in saved}
    assert all(note.review_state == "unverified" for note in notes)
    assert service.feedback_store.contributions() == []


def test_configured_restart_keeps_original_run_and_rebinding_refuses(configured):
    f = configured
    service = f.connected.backend(SPACE).service

    def started():
        with sqlite3.connect(service.ledger.path) as db:
            return db.execute("SELECT started_at FROM swarm_runs WHERE swarm_id=?", (service.config.swarm_id,)).fetchone()[0]

    first = started()
    reopened = ConfiguredResearch(f.config, f.spaces)
    assert started() == first
    assert reopened.backend(SPACE).project("q-project") == f.connected.backend(SPACE).project("q-project")
    path = f.hosts[0].host_config
    body = json.loads(path.read_text(encoding="utf-8"))
    body["swarm_id"] = "caller-new-run-reset"
    path.write_text(json.dumps(body), encoding="utf-8")
    with pytest.raises((PermissionError, ValueError)):
        ConfiguredResearch(f.config, f.spaces)
    assert started() == first and service.ledger.snapshot() == []
