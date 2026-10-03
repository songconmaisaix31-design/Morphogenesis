"""Original native request/observation scope, with no native launch or auth read.

Source mode substitutes only package admission and the native launch planner.
Installed mode keeps installed_core unchanged. Core service, protected HostConfig,
official tool catalogue and original budget/resume records remain actual.
"""
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from uuid import uuid4

import pytest

if not os.environ.get("R1_PRODUCT_SOURCE") and os.environ.get("R1_SECURITY_INSTALLED") != "1":
    pytest.skip("P source not selected; resume admission NOT_RUN", allow_module_level=True)

from contracts.provenance import Acceptance
from contracts.results import Usage
from orchestration.native_agents.models import HostBinding, LaunchPlan, LaunchRequest, McpStdio, NativeOutcome
from morph_research import r1_native as native
from morph_research.config import exclusive_json
from morph_research.r1_config import ResearchConnection, ResearchMember
from tests.integration.r1_security.test_a_project_budget_boundaries import host
from tests.integration.r1_security.test_p_provider_binding import PROVIDER_BINDING, safe_codex_metadata

SPACE = "a" * 32


@pytest.fixture
def recorded(tmp_path, monkeypatch, deny_candidate_execution_and_network):
    core = host(tmp_path)
    grant = {"project_id": core.project_id, "member_id": core.worker_id, "runtime": "codex",
        "provider": core.research_execution_bound.provider, "model": core.research_execution_bound.model,
        "scopes": list(core.authorized_scopes), "data_categories": ["goal", "sources", "expert_opinions",
                                                                  "research_notes", "candidate_code", "raw_outputs"]}
    core = core.model_copy(update={"research_envelope": core.research_envelope.model_copy(update={
        "data_bounds": {"native_egress": json.dumps([grant]),
                        "native_provider_bindings": json.dumps([PROVIDER_BINDING])}})})
    safe_codex_metadata(tmp_path, monkeypatch)
    Path(core.workspace).mkdir()
    path = tmp_path / "member-host.json"
    path.write_text(core.model_dump_json(), encoding="utf-8")
    member = ResearchMember(id=core.worker_id, host_config=path, runtime="codex",
        native_authorized=True, native_execution_bound=core.research_execution_bound)
    connection = ResearchConnection(space_id=SPACE, name="Q inert native record", ingress_member=member.id,
                                    members=(member,))
    config = SimpleNamespace(research_connections=(connection,), sandbox_key_env="MORPH_RESEARCH_Q_FIXTURE",
        codex_auth="inherited-selected", claude_auth="pending", claude_api_base_url=None, claude_model=None)
    calls = []

    def planner(selected, config_path, invocation, prompt, resume, **kwargs):
        calls.append(resume)
        request = LaunchRequest(runtime=kwargs["member_runtime"], workspace=Path(selected.workspace),
            model=kwargs["member_model"], prompt=prompt, session_id=resume, sandbox="read-only",
            mcp=McpStdio(command=sys.executable, args=("-m", "swarm.research", "--config", str(config_path))))
        plan = LaunchPlan(runtime=request.runtime, mode=request.mode,
            argv=("q-inert-never-executed", "-c", 'sandbox_mode="read-only"', "exec"),
            workspace=request.workspace, stdin_text=request.prompt, session_id=resume,
            host_binding=HostBinding(agent=selected.agent, worker_id=selected.worker_id,
                swarm_id=selected.swarm_id, config_path=config_path))
        return request, plan

    if os.environ.get("R1_SECURITY_INSTALLED") != "1":
        monkeypatch.setattr(native, "installed_core", lambda: {"acceptance": "fixture_package_gate_not_validated"})
    monkeypatch.setattr(native, "plan_launch", planner)  # no native config/auth/binary access
    monkeypatch.setattr(native.asyncio, "run", deny_candidate_execution_and_network.run_until_complete)
    invocation, session = str(uuid4()), str(uuid4())
    _, service, _, directory, request, _ = native.prepare_member(config, SPACE, member.id, invocation)
    reservation = service.budget.reserve(member.id, "native-member:" + member.id,
        member.native_execution_bound, request_id="native:" + invocation)
    budget = service.budget.settle(reservation, {"usage": {"prompt_tokens": 3, "completion_tokens": 2,
                                                          "total_tokens": 5}})
    assert budget.tokens == 5 and budget.uncertain_reservations == 0
    outcome = NativeOutcome(runtime="codex", session_id=session, state="completed", provenance="mock",
        acceptance=Acceptance(provenance="mock"), usage=Usage(tokens=5))
    directory.mkdir(parents=True)
    exclusive_json(directory / "request.json", {"request": request.model_dump(mode="json"),
                                                "provider_binding": dict(PROVIDER_BINDING),
                                                "reservation": reservation.model_dump(mode="json")})
    exclusive_json(directory / "observation.json", {"member_id": member.id, "project_id": core.project_id,
        "outcome": outcome.model_dump(mode="json"), "forbidden": False, "budget": budget.model_dump(mode="json"),
        "acceptance": "native_observation_only"})
    calls.clear()
    return SimpleNamespace(config=config, member=member, service=service, directory=directory,
                           session=session, calls=calls, workspace=Path(core.workspace))


def test_same_project_member_native_record_can_prepare_resume_without_launch(recorded):
    f = recorded
    _, service, _, directory, request, plan = native.prepare_member(f.config, SPACE, f.member.id,
                                                                   str(uuid4()), f.session)
    assert request.session_id == plan.session_id == f.session
    assert f.calls == [f.session]
    assert not directory.exists()
    assert request.workspace == f.workspace and request.model == f.member.native_execution_bound.model
    assert service.ledger.snapshot() == [] and service.store.adoptions() == []
    assert service.budget.snapshot().tokens == 5


@pytest.mark.parametrize("field", ["project", "member", "outcome_runtime", "request_runtime", "model",
                                   "workspace", "reservation_member", "missing_request",
                                   "binding_provider", "binding_endpoint", "binding_runtime", "missing_binding"])
def test_resume_rejects_foreign_or_missing_original_record_before_planning(recorded, field):
    f = recorded
    path = f.directory / ("observation.json" if field in {"project", "member", "outcome_runtime"}
                          else "request.json")
    if field == "missing_request":
        path.unlink()  # This test owns this exact inert fixture, not repository evidence.
    else:
        body = json.loads(path.read_text(encoding="utf-8"))
        if field == "project":
            body["project_id"] = "foreign-project"
        elif field == "member":
            body["member_id"] = "foreign-member"
        elif field == "outcome_runtime":
            body["outcome"]["runtime"] = "claude"
        elif field == "request_runtime":
            body["request"]["runtime"] = "claude"
        elif field == "model":
            body["request"]["model"] = "foreign-model"
        elif field == "workspace":
            other = f.workspace.parent / "other-workspace"
            other.mkdir()
            body["request"]["workspace"] = str(other)
        elif field == "reservation_member":
            body["reservation"]["worker_id"] = "foreign-member"
        elif field == "binding_provider":
            body["provider_binding"]["provider"] = "foreign"
        elif field == "binding_endpoint":
            body["provider_binding"]["base_url"] = "https://foreign.invalid/v1"
        elif field == "binding_runtime":
            body["provider_binding"]["runtime"] = "claude"
        elif field == "missing_binding":
            del body["provider_binding"]
        path.write_text(json.dumps(body), encoding="utf-8")
    with pytest.raises((PermissionError, ValueError, FileNotFoundError)):
        native.prepare_member(f.config, SPACE, f.member.id, str(uuid4()), f.session)
    assert f.calls == [], "foreign resume record reached native planning"
    assert f.service.ledger.snapshot() == [] and f.service.store.adoptions() == []
    assert f.service.budget.snapshot().tokens == 5
