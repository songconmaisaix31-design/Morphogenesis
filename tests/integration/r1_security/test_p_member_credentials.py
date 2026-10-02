"""Real handler/configured authenticator and HostConfig/MCP member identities.

The configured object's validated connection/backend maps are supplied directly
for archive tests; its full protected constructor is covered by installed tests.
All keys here are Q-created inert fixture values, never real user credentials.
"""
from email.message import Message
import json
import os
from types import SimpleNamespace

import pytest

if not os.environ.get("R1_PRODUCT_SOURCE") and os.environ.get("R1_SECURITY_INSTALLED") != "1":
    pytest.skip("P source not selected; member credentials NOT_RUN", allow_module_level=True)

from contracts.identity import AgentId
from morph_research.backend import ServiceBackend
from morph_research.r1 import ResearchGoal
from morph_research.r1_config import ConfiguredResearch, ResearchConnection, ResearchMember
from morph_research.web.r1 import R1Spaces
from morph_research.web import server
from swarm.research.service import ResearchService
from swarm.task_ledger import TaskLedger
from tests.integration.r1_security.test_a_host_boundaries import seeded

SPACE = "a" * 32


@pytest.mark.parametrize("credential", ["missing", "wrong", "other_member", "duplicate", "correct"])
def test_url_member_cannot_become_reviewer_without_its_host_credential(tmp_path, monkeypatch,
        deny_candidate_execution_and_network, credential):
    author = seeded(tmp_path / "core")
    reviewer_config = author.config.model_copy(update={"worker_id": "reviewer",
        "agent": AgentId(role="reviewer", instance=1)})
    reviewer = ResearchService(reviewer_config, ledger=TaskLedger(reviewer_config.ledger_path,
        reviewer_config.swarm_id, clock=lambda: 100.0))
    keys = {"q": "q-author-fixture-" + "a" * 48, "reviewer": "q-review-fixture-" + "b" * 48}
    members = []
    for service in (author, reviewer):
        identity = service.config.worker_id
        host_path, key_path = tmp_path / (identity + ".json"), tmp_path / (identity + ".key")
        host_path.write_text(service.config.model_dump_json(), encoding="utf-8")
        key_path.write_text(keys[identity], encoding="ascii")
        options = {"http_token_file": key_path} if "http_token_file" in ResearchMember.model_fields else {}
        members.append(ResearchMember(id=identity, host_config=host_path, **options))
    connection = ResearchConnection(space_id=SPACE, name="Q member identity", ingress_member="q", members=tuple(members))
    configured = object.__new__(ConfiguredResearch)
    configured.connections = {SPACE: connection}
    configured.backends = {SPACE: {"q": ServiceBackend(author), "reviewer": ServiceBackend(reviewer)}}
    config = SimpleNamespace(root=tmp_path / "product", allowed_import_dirs=(), allowed_material_domains=())
    spaces = R1Spaces(config)
    spaces.create(SPACE, "Q", ResearchGoal(objective="member identity"), None)
    spaces.store(SPACE).bind_project(SPACE, "p1", author.config.authorization_ref)
    lookups = []

    def backend_for(space, member=None):
        lookups.append(member)
        return configured.backend(space, member)

    request = object.__new__(server.Handler)
    request.server = SimpleNamespace(r1=spaces, configured_research=configured,
        backend_for=backend_for, spaces=SimpleNamespace(config=config))
    request.headers = Message()
    if credential != "missing":
        value = keys["q"] if credential == "other_member" else keys["reviewer"] if credential in {"correct", "duplicate"} else "q-invalid-fixture"
        request.headers.add_header("Authorization", "Bearer " + value)
        if credential == "duplicate":
            request.headers.add_header("Authorization", "Bearer " + keys["q"])
    request.form = lambda **kwargs: {"arguments": {"project_id": "p1", "kind": "hypothesis",
        "text": "Q nonempty protected reviewer tool"}}
    responses = []
    request.reply = lambda status, result: responses.append((status, result))
    monkeypatch.setattr(server.asyncio, "run", deny_candidate_execution_and_network.run_until_complete)
    try:
        try:
            request.route_research(f"/api/research-spaces/{SPACE}/members/reviewer/tools/submit_research_note", True)
        except PermissionError:
            assert credential != "correct", "valid host member credential lost its nonempty positive path"
        if credential != "correct":
            assert lookups == [], "untrusted URL/key selected the reviewer backend"
            assert reviewer.knowledge.notes("p1") == []
            assert responses == []
        else:
            assert lookups == ["reviewer"] and responses[0][0] == 200
            notes = reviewer.knowledge.notes("p1")
            assert len(notes) == 1 and notes[0].actor == reviewer.config.agent
            assert notes[0].review_state == "unverified"
            exported = reviewer.research_package("p1")
            visible = json.dumps({"response": responses, "export": exported,
                                  "members": configured.members(SPACE)}, default=str)
            assert all(key not in visible for key in keys.values())
    finally:
        spaces.close()
