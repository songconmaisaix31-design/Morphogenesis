"""Claude gateway destination admission; every routing input is a Q fixture."""
import json
import os
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

if not os.environ.get("R1_PRODUCT_SOURCE") and os.environ.get("R1_SECURITY_INSTALLED") != "1":
    pytest.skip("P source not selected; Claude provider binding NOT_RUN", allow_module_level=True)

from contracts.provenance import Acceptance
from contracts.results import Usage
from orchestration.native_agents import launch
from orchestration.native_agents.events import parse_event
from orchestration.native_agents.models import NativeOutcome
from orchestration.native_agents.registry import ProbeResult
from morph_research import r1_native as native, r1_provider as provider
from morph_research.r1_config import ResearchConnection, ResearchMember
from tests.integration.r1_security.test_a_project_budget_boundaries import host

SPACE = "a" * 32
DESTINATION = "https://authorized.invalid/v1"


def configured(root, monkeypatch, loop, attack=None):
    core = host(root, allowance=.2)
    bound = core.research_execution_bound.model_copy(update={"provider": "authorized.invalid"})
    prices = core.research_budget_policy.prices.model_copy(update={"provider": "authorized.invalid"})
    grant = {"project_id": core.project_id, "member_id": core.worker_id, "runtime": "claude",
        "provider": bound.provider, "model": bound.model, "scopes": list(core.authorized_scopes),
        "data_categories": ["goal", "sources", "expert_opinions", "research_notes", "candidate_code", "raw_outputs"]}
    binding = {"runtime": "claude", "provider": bound.provider, "base_url": DESTINATION}
    bounds = {"native_egress": json.dumps([grant]), "native_provider_bindings": json.dumps([binding])}
    if attack == "missing_binding":
        bounds.pop("native_provider_bindings")
    core = core.model_copy(update={"research_execution_bound": bound,
        "research_budget_policy": core.research_budget_policy.model_copy(update={"prices": prices}),
        "research_envelope": core.research_envelope.model_copy(update={"data_bounds": bounds})})
    Path(core.workspace).mkdir()
    config_path = root / "host.json"
    config_path.write_text(core.model_dump_json(), encoding="utf-8")
    member = ResearchMember(id=core.worker_id, host_config=config_path, runtime="claude",
                             native_authorized=True, native_execution_bound=bound)
    connection = ResearchConnection(space_id=SPACE, name="Q inert Claude gateway", ingress_member=member.id,
                                    members=(member,))
    config = SimpleNamespace(research_connections=(connection,), sandbox_key_env="MORPH_RESEARCH_Q_FIXTURE",
        codex_auth="pending", claude_auth="inherited-gateway", claude_api_base_url=None, claude_model=None)
    settings = root / "settings.json"
    selected = {"ANTHROPIC_BASE_URL": "https://foreign.invalid/v1" if attack == "endpoint" else DESTINATION}
    if attack == "cloud_flag":
        selected["CLAUDE_CODE_USE_BEDROCK"] = "1"
    settings.write_text(json.dumps({"env": selected}), encoding="utf-8")
    managed = root / "managed-settings.json"
    if attack == "managed":
        managed.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(provider, "claude_settings_sources", lambda: (settings, [managed]))
    # Replace this module's routing-environment view, not os.environ or auth.
    monkeypatch.setattr(provider, "os", SimpleNamespace(environ={}, name=os.name))
    monkeypatch.setattr(launch, "resolve_executable", lambda spec: ("q-native-never-executed",))
    monkeypatch.setattr(native.asyncio, "run", loop.run_until_complete)
    if os.environ.get("R1_SECURITY_INSTALLED") != "1":
        monkeypatch.setattr(native, "installed_core", lambda: {"acceptance": "fixture_package_gate_not_validated"})
    calls = {"probe": [], "native": []}

    def probe(runtime):
        calls["probe"].append(runtime)
        return ProbeResult(runtime=runtime, command=("q-native-never-executed",), version="2.1.238",
            version_matches=True, authenticated=True, version_exit=0, auth_exit=0)

    def observe(plan, evidence, **kwargs):
        calls["native"].append(plan)
        event = {"type": "result", "subtype": "success", "is_error": False, "usage": {
            "input_tokens": 3, "output_tokens": 2, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}}
        for parsed in parse_event("claude", json.dumps(event)):
            kwargs["on_event"](parsed)
        return NativeOutcome(runtime="claude", provenance="mock", acceptance=Acceptance(provenance="mock"),
                             state="completed", usage=Usage(tokens=5))

    monkeypatch.setattr(native, "probe", probe)
    monkeypatch.setattr(native, "run_headless", observe)
    return config, member, calls


def test_claude_selected_gateway_and_frozen_launch_match_host_grant(tmp_path, monkeypatch,
        deny_candidate_execution_and_network):
    config, member, calls = configured(tmp_path, monkeypatch, deny_candidate_execution_and_network)
    result, code = native.run_member(config, SPACE, member.id, str(uuid4()))
    assert code == 0 and result["acceptance"] == "native_observation_only"
    assert len(calls["probe"]) == len(calls["native"]) == 1
    plan = calls["native"][0]
    settings = json.loads(plan.argv[plan.argv.index("--settings") + 1])
    assert settings["env"]["ANTHROPIC_BASE_URL"] == DESTINATION
    assert result["budget"]["tokens"] == 5 and result["budget"]["actual_cost_usd"] is None


@pytest.mark.parametrize("attack", ["endpoint", "cloud_flag", "managed", "missing_binding"])
def test_claude_unapproved_or_ambiguous_destination_refuses_before_effect(tmp_path, monkeypatch,
        deny_candidate_execution_and_network, attack):
    config, member, calls = configured(tmp_path, monkeypatch, deny_candidate_execution_and_network, attack)
    with pytest.raises((PermissionError, ValueError)):
        native.run_member(config, SPACE, member.id, str(uuid4()))
    assert calls == {"probe": [], "native": []}
    service = native.build_service(member)
    assert service.budget.snapshot().pending_reservations == 0
    assert service.budget.snapshot().uncertain_reservations == 0
    assert service.store.adoptions() == [] and service.feedback_store.contributions() == []
