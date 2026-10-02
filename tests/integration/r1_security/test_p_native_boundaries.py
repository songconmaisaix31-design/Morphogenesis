"""Native admission with original budget and inert adapter/event fixtures only."""
import json
import os
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

if not os.environ.get("R1_PRODUCT_SOURCE") and os.environ.get("R1_SECURITY_INSTALLED") != "1":
    pytest.skip("P source not selected; native admission NOT_RUN", allow_module_level=True)

from contracts.identity import AgentId
from contracts.provenance import Acceptance
from contracts.results import Usage
from orchestration.native_agents.events import parse_event
from orchestration.native_agents.models import NativeOutcome
from morph_research import r1_native as native
from morph_research.r1_config import ResearchConnection, ResearchMember
from tests.integration.r1_security.test_a_project_budget_boundaries import host, opened, InertExecutionBoundary

SPACE = "a" * 32


def configured(root, monkeypatch, *, authorized=True, bound=True, selected=True, grant_attack=None):
    core = host(root, allowance=.2)
    categories = ["goal", "sources", "expert_opinions", "research_notes", "candidate_code", "raw_outputs"]
    grants = [{"project_id": core.project_id, "member_id": member, "runtime": "codex",
        "provider": core.research_execution_bound.provider, "model": core.research_execution_bound.model,
        "scopes": list(core.authorized_scopes), "data_categories": categories}
        for member in ("member-one", "member-two")]
    if grant_attack == "missing":
        grants = []
    elif grant_attack in {"project_id", "member_id", "runtime", "provider", "model"}:
        grants[0][grant_attack] = "unapproved-destination"
    elif grant_attack == "scope":
        grants[0]["scopes"] = ["private"]
    elif grant_attack == "category":
        grants[0]["data_categories"] = ["goal"]
    bounds = {"native_egress": json.dumps(grants)}
    if grant_attack == "malformed":
        bounds["native_egress"] = "true"
    core = core.model_copy(update={"research_envelope": core.research_envelope.model_copy(update={"data_bounds": bounds})})
    service = opened(core, InertExecutionBoundary())
    service.create_project(core.project_id, core.research_envelope.goal)
    members = tuple(ResearchMember(id=worker, host_config=root / (worker + ".json"), runtime="codex",
        native_authorized=authorized, native_execution_bound=core.research_execution_bound if bound else None)
        for worker in ("member-one", "member-two"))
    for index, member in enumerate(members):
        configured_host = core.model_copy(update={"worker_id": member.id, "agent": AgentId(role="builder", instance=index)})
        member.host_config.write_text(configured_host.model_dump_json(), encoding="utf-8")
    connection = ResearchConnection(space_id=SPACE, name="Q mock native boundary", ingress_member="member-one", members=members)
    config = SimpleNamespace(research_connections=(connection,), codex_auth="inherited-selected" if selected else "pending",
                             claude_auth="pending")
    calls = {"probe": [], "native": []}

    def prepare(config, space_id, member_id, invocation, resume=None):
        member = next(value for value in members if value.id == member_id)
        s = opened(core.model_copy(update={"worker_id": member_id,
            "agent": AgentId(role="builder", instance=0 if member_id == "member-one" else 1)}), InertExecutionBoundary())
        directory = root / "evidence/native" / member_id / invocation
        return member, s, ("research_project", "choose_research_work"), directory, SimpleNamespace(
            model_dump=lambda **kwargs: {"provenance": "mock", "fixture_only": True}), SimpleNamespace()

    def probe(runtime):
        calls["probe"].append(runtime)
        return SimpleNamespace(version_matches=True, authenticated=True)

    def run(*args, **kwargs):
        calls["native"].append(True)
        return NativeOutcome(runtime="codex", provenance="mock", acceptance=Acceptance(provenance="mock"),
                             state="unknown", usage=Usage())

    monkeypatch.setattr(native, "prepare_member", prepare)  # planner tested separately on installed pair
    monkeypatch.setattr(native, "probe", probe)  # no CLI/auth probe
    monkeypatch.setattr(native, "run_headless", run)  # no native/model process
    monkeypatch.setattr(native, "write_mcp_config", lambda plan, path: Path(path).write_text('{"fixture_only":true}'))
    return config, service, calls


@pytest.mark.parametrize("missing", ["authorization", "budget_bound", "selected_auth"])
def test_native_authority_gaps_refuse_before_probe_or_launch(tmp_path, monkeypatch, missing):
    config, service, calls = configured(tmp_path, monkeypatch, authorized=missing != "authorization",
        bound=missing != "budget_bound", selected=missing != "selected_auth")
    with pytest.raises(PermissionError):
        native.run_member(config, SPACE, "member-one", str(uuid4()))
    assert calls == {"probe": [], "native": []}
    assert service.budget.snapshot().pending_reservations == 0


@pytest.mark.parametrize("attack", ["missing", "project_id", "member_id", "runtime", "provider", "model",
                                    "scope", "category", "malformed"])
def test_native_data_egress_requires_exact_host_project_destination_and_categories(tmp_path, monkeypatch, attack):
    config, service, calls = configured(tmp_path, monkeypatch, grant_attack=attack)
    with pytest.raises(PermissionError, match="data_egress_grant_required"):
        native.run_member(config, SPACE, "member-one", str(uuid4()))
    assert calls == {"probe": [], "native": []}
    assert service.budget.snapshot().pending_reservations == 0
    assert service.budget.snapshot().uncertain_reservations == 0


def test_native_observer_limits_cannot_claim_provider_hard_enforcement(tmp_path):
    core = host(tmp_path)
    bound = core.research_execution_bound.model_copy(update={"request_bound": "verified", "provider_enforced": True,
        "max_cost_usd": .1})
    with pytest.raises(ValueError):
        ResearchMember(id="member-one", host_config=tmp_path / "host.json", runtime="codex",
                       native_authorized=True, native_execution_bound=bound)


def test_native_pending_original_hold_blocks_same_member_replacement(tmp_path, monkeypatch):
    config, service, calls = configured(tmp_path, monkeypatch)
    service.budget.reserve("member-one", "native-member:member-one", service.config.research_execution_bound,
                           request_id="interrupted-before-launch")
    with pytest.raises(PermissionError):
        native.run_member(config, SPACE, "member-one", str(uuid4()))
    assert calls == {"probe": [], "native": []}
    assert service.budget.snapshot().pending_reservations == 1


@pytest.mark.parametrize("next_member", ["member-one", "member-two"])
def test_unknown_native_observation_preserves_unknown_and_blocks_new_invocation(tmp_path, monkeypatch, next_member):
    config, service, calls = configured(tmp_path, monkeypatch)
    result, code = native.run_member(config, SPACE, "member-one", str(uuid4()))
    assert code == 1 and result["acceptance"] == "native_observation_only"
    assert result["outcome"]["provenance"] == "mock"
    assert result["outcome"]["usage"] == {"tokens": None, "cost_usd": None}
    assert result["budget"]["uncertain_reservations"] == 1
    assert result["budget"]["tokens"] is None and result["budget"]["actual_cost_usd"] is None
    with pytest.raises(PermissionError):
        native.run_member(config, SPACE, next_member, str(uuid4()))
    assert len(calls["native"]) == len(calls["probe"]) == 1
    assert service.store.adoptions() == [] and service.feedback_store.contributions() == []


@pytest.mark.parametrize("reported", ["matching", "mismatched", "missing"])
def test_completed_native_observation_settles_only_exact_event_usage(tmp_path, monkeypatch, reported):
    config, service, calls = configured(tmp_path, monkeypatch)

    def completed(*args, **kwargs):
        calls["native"].append(True)
        if reported != "missing":
            event = {"type": "turn.completed", "usage": {"input_tokens": 3, "output_tokens": 2}}
            for parsed in parse_event("codex", json.dumps(event)):
                kwargs["on_event"](parsed)
        return NativeOutcome(runtime="codex", provenance="mock", acceptance=Acceptance(provenance="mock"),
            state="completed", usage=Usage(tokens=6 if reported == "mismatched" else 5))

    monkeypatch.setattr(native, "run_headless", completed)
    result, code = native.run_member(config, SPACE, "member-one", str(uuid4()))
    assert code == 0 and result["acceptance"] == "native_observation_only"
    assert len(calls["native"]) == len(calls["probe"]) == 1
    snapshot = service.budget.snapshot()
    assert snapshot.pending_reservations == 0
    assert snapshot.actual_cost_usd is None
    assert result["outcome"]["usage"]["cost_usd"] is None
    if reported == "matching":
        assert snapshot.tokens == result["budget"]["tokens"] == 5
        assert snapshot.uncertain_reservations == 0
        assert not snapshot.sleeping
    else:
        assert snapshot.tokens is None
        assert snapshot.uncertain_reservations == 1
    assert service.feedback_store.contributions() == [] and service.store.adoptions() == []


@pytest.mark.parametrize("kind", ["foreign_mcp", "host_command", "mismatched_usage"])
def test_member_observer_does_not_promote_forbidden_calls_or_invent_usage(tmp_path, monkeypatch, kind):
    _, service, calls = configured(tmp_path, monkeypatch)
    guard = native.MemberGuard(service, ("choose_research_work",))
    if kind == "mismatched_usage":
        event = {"type": "turn.completed", "usage": {"input_tokens": 3, "output_tokens": 2}}
    else:
        item = {"id": "q-fixture", "type": "mcp_tool_call", "server": "foreign",
                "tool": "choose_research_work", "arguments": {}} if kind == "foreign_mcp" else {
                "id": "q-fixture", "type": "command_execution", "command": "inert fixture text"}
        event = {"type": "item.started", "item": item}
    for parsed in parse_event("codex", json.dumps(event)):
        guard.on_event(parsed)
    if kind == "mismatched_usage":
        outcome = NativeOutcome(runtime="codex", provenance="mock", acceptance=Acceptance(provenance="mock"),
            state="completed", usage=Usage(tokens=6))
        assert guard.observed_usage(outcome) is None
    else:
        assert guard.stop and guard.forbidden
    assert service.feedback_store.contributions() == [] and service.store.adoptions() == []
    assert calls == {"probe": [], "native": []}
