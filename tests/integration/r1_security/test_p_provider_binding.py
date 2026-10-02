"""Real R1 planner/admission over credential-free selected-provider fixtures.

The only native configuration path is created here. The original planner and
HostConfig/core factory run; binary resolution, version/auth probe and native
execution are inert boundaries. No real auth/provider file is inspected.
"""
import json
import os
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

if not os.environ.get("R1_PRODUCT_SOURCE") and os.environ.get("R1_SECURITY_INSTALLED") != "1":
    pytest.skip("P source not selected; selected provider binding NOT_RUN", allow_module_level=True)

from contracts.provenance import Acceptance
from contracts.results import Usage
from orchestration.native_agents import launch
from orchestration.native_agents.events import parse_event
from orchestration.native_agents.models import NativeOutcome
from orchestration.native_agents.registry import ProbeResult
from morph_research import permissions, r1_native as native
from morph_research.r1_config import ResearchConnection, ResearchMember
from tests.integration.r1_security.test_a_project_budget_boundaries import host

SPACE = "a" * 32


def configured(root, selected_provider, monkeypatch, loop):
    core = host(root, allowance=.2)
    grant = {"project_id": core.project_id, "member_id": core.worker_id, "runtime": "codex",
        "provider": core.research_execution_bound.provider, "model": core.research_execution_bound.model,
        "scopes": list(core.authorized_scopes), "data_categories": ["goal", "sources", "expert_opinions",
                                                                  "research_notes", "candidate_code", "raw_outputs"]}
    core = core.model_copy(update={"research_envelope": core.research_envelope.model_copy(update={
        "data_bounds": {"native_egress": json.dumps([grant])}})})
    Path(core.workspace).mkdir()
    path = root / "member-host.json"
    path.write_text(core.model_dump_json(), encoding="utf-8")
    member = ResearchMember(id=core.worker_id, host_config=path, runtime="codex",
        native_authorized=True, native_execution_bound=core.research_execution_bound)
    connection = ResearchConnection(space_id=SPACE, name="Q selected-provider fixture", ingress_member=member.id,
                                    members=(member,))
    config = SimpleNamespace(research_connections=(connection,), sandbox_key_env="MORPH_RESEARCH_Q_FIXTURE",
        codex_auth="inherited-selected", claude_auth="pending", claude_api_base_url=None, claude_model=None)
    selected = root / "native-metadata.toml"
    selected.write_text('model_provider = ' + json.dumps(selected_provider) + '\nmodel = "fixture"\n'
        '[model_providers.q-mock]\nname = "Q mock"\nbase_url = "https://authorized.invalid/v1"\n'
        'wire_api = "responses"\n[model_providers.foreign]\nname = "Q unauthorized fixture"\n'
        'base_url = "https://foreign.invalid/v1"\nwire_api = "responses"\n', encoding="utf-8")
    calls = {"probe": [], "native": []}
    if os.environ.get("R1_SECURITY_INSTALLED") != "1":
        monkeypatch.setattr(native, "installed_core", lambda: {"acceptance": "fixture_package_gate_not_validated"})
    monkeypatch.setattr(permissions, "codex_config_sources", lambda workspace: [selected])
    monkeypatch.setattr(launch, "resolve_executable", lambda spec: ("q-native-never-executed",))
    monkeypatch.setattr(native.asyncio, "run", loop.run_until_complete)

    def probe(runtime):
        calls["probe"].append(runtime)
        return ProbeResult(runtime=runtime, command=("q-native-never-executed",), version="codex-cli 0.159.0",
            version_matches=True, authenticated=True, version_exit=0, auth_exit=0)

    def observe(plan, evidence, **kwargs):
        calls["native"].append(plan)
        for event in parse_event("codex", json.dumps({"type": "turn.completed",
                "usage": {"input_tokens": 3, "output_tokens": 2}})):
            kwargs["on_event"](event)
        return NativeOutcome(runtime="codex", provenance="mock", acceptance=Acceptance(provenance="mock"),
                             state="completed", usage=Usage(tokens=5))

    monkeypatch.setattr(native, "probe", probe)
    monkeypatch.setattr(native, "run_headless", observe)
    return config, member, calls


def test_actual_selected_provider_matches_host_grant_positive(tmp_path, monkeypatch, deny_candidate_execution_and_network):
    config, member, calls = configured(tmp_path, "q-mock", monkeypatch, deny_candidate_execution_and_network)
    result, code = native.run_member(config, SPACE, member.id, str(uuid4()))
    assert code == 0 and result["acceptance"] == "native_observation_only"
    assert len(calls["native"]) == len(calls["probe"]) == 1
    plan = calls["native"][0]
    assert plan.host_binding.worker_id == member.id
    assert plan.argv[plan.argv.index("--model") + 1] == "fixture"
    assert result["budget"]["tokens"] == 5 and result["budget"]["actual_cost_usd"] is None


def test_changed_selected_provider_cannot_reuse_previous_host_data_grant(tmp_path, monkeypatch,
                                                                       deny_candidate_execution_and_network):
    config, member, calls = configured(tmp_path, "foreign", monkeypatch, deny_candidate_execution_and_network)
    with pytest.raises((PermissionError, ValueError)):
        native.run_member(config, SPACE, member.id, str(uuid4()))
    assert calls == {"probe": [], "native": []}
    service = native.build_service(member)
    assert service.budget.snapshot().pending_reservations == 0
    assert service.budget.snapshot().uncertain_reservations == 0
    assert service.ledger.snapshot() == [] and service.store.adoptions() == []
