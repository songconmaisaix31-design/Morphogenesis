"""Legacy narrowing retains original launch identity and actual MCP handlers."""
import json
import os
from pathlib import Path

import pytest

if not os.environ.get("R1_PRODUCT_SOURCE") and os.environ.get("R1_SECURITY_INSTALLED") != "1":
    pytest.skip("P source not selected; registered boundary NOT_RUN", allow_module_level=True)

from contracts.identity import AgentId
from mcp.server.fastmcp.exceptions import ToolError
from orchestration.native_agents import launch
from swarm.models import Signal
from swarm.research.models import HostConfig
from swarm.research.server import create_server
from swarm.research.service import ResearchService
from morph_research import permissions
from tests.integration.r1_security.test_a_project_budget_boundaries import host
from tests.integration.r1_security.test_p_provider_binding import safe_codex_metadata

LEGACY_TOOLS = {"discover_tasks", "project_context", "lease_task", "search_evidence", "research_experiment",
    "research_candidate", "verify_research", "complete_research_task", "approve_candidate",
    "inherit_experience", "apply_candidate"}
R1_TOOLS = {"research_project", "propose_research_work", "research_snapshot", "choose_research_work",
            "record_research_correction", "prepare_candidate_experiment"}


class NoExecutionBoundary:
    async def execute(self, *args, **kwargs):
        raise AssertionError("Q legacy boundary cannot execute an experiment")


def configured_host(root, *, r1=False):
    config = host(root) if r1 else HostConfig(ledger_path=str(root / "ledger.db"), swarm_id="q-legacy",
        workspace=str(root / "workspace"), worker_id="q-legacy-member", agent=AgentId(role="builder", instance=0),
        authorized_scopes=("science",), capabilities=("research",), assets_root=str(root / "assets"),
        evidence_root=str(root / "evidence"))
    Path(config.workspace).mkdir(parents=True, exist_ok=True)
    if not r1:
        assert config.project_id == ""  # The original valid default, never a model_copy(None) bypass.
    return config


def planned(config, path, runtime, mode):
    return permissions.plan_launch(config, path, "replication" if runtime == "claude" else "interrupt",
        "Q inert planning fixture", None, key_env="MORPH_RESEARCH_Q_FIXTURE", claude_auth="inherited-gateway",
        choice_only=mode == "choice", member_runtime=runtime if mode == "r1" else None,
        member_tools=tuple(sorted(R1_TOOLS | LEGACY_TOOLS)) if mode == "r1" else None)


@pytest.mark.parametrize("runtime", ["codex", "claude"])
@pytest.mark.parametrize("mode", ["registered", "choice", "r1"])
def test_original_host_binding_survives_product_mcp_module_selection(tmp_path, monkeypatch, runtime, mode):
    config = configured_host(tmp_path, r1=mode == "r1")
    path = tmp_path / "host.json"
    path.write_text(config.model_dump_json(), encoding="utf-8")
    safe_codex_metadata(tmp_path, monkeypatch)
    monkeypatch.setattr(launch, "resolve_executable", lambda spec: ("q-native-never-executed",))
    request, plan = planned(config, path, runtime, mode)
    module = {"registered": "morph_research.registered_mcp", "choice": "morph_research.choice_mcp",
              "r1": "swarm.research"}[mode]
    assert request.mcp.args == ("-m", module, "--config", str(path))
    original_request = request.model_copy(update={"mcp": request.mcp.model_copy(update={
        "args": ("-m", "swarm.research", "--config", str(path))})})
    original = launch.build_launch(original_request, claude_mcp_path=tmp_path / "original-mcp.json")
    assert original.host_binding is not None
    assert plan.host_binding == original.host_binding, "product module lost the original core HostBinding"
    if runtime == "claude":
        assert plan.mcp_config["mcpServers"]["morph_research"]["args"] == list(request.mcp.args)
    else:
        values = [value.split("=", 1)[1] for value in plan.argv
                  if value.startswith("mcp_servers.morph_research.args=")]
        assert len(values) == 1 and json.loads(values[0]) == list(request.mcp.args)


@pytest.mark.parametrize("runtime", ["codex", "claude"])
@pytest.mark.parametrize("mode", ["registered", "choice", "r1"])
@pytest.mark.parametrize("attack", ["relative_config", "foreign_workspace"])
def test_product_module_cannot_bypass_original_config_workspace_refusal(tmp_path, monkeypatch, runtime, mode, attack):
    config = configured_host(tmp_path, r1=mode == "r1")
    body = config.model_dump(mode="json")
    if attack == "foreign_workspace":
        body["workspace"] = str(tmp_path / "another-workspace")
    path = tmp_path / "host.json"
    path.write_text(json.dumps(body), encoding="utf-8")
    if attack == "relative_config":
        path = Path("q-relative-host.json")
    safe_codex_metadata(tmp_path, monkeypatch)
    monkeypatch.setattr(launch, "resolve_executable", lambda spec: ("q-native-never-executed",))
    with pytest.raises((PermissionError, ValueError)):
        planned(config, path, runtime, mode)


@pytest.mark.parametrize("choice_only", [False, True])
def test_valid_legacy_eleven_tools_keep_handlers_without_mutating_r1_surface(tmp_path, monkeypatch,
        deny_candidate_execution_and_network, choice_only):
    from morph_research import registered_mcp
    from morph_research.choice_mcp import ChoiceService

    loop = deny_candidate_execution_and_network
    monkeypatch.setattr(registered_mcp.asyncio, "run", loop.run_until_complete)
    config = configured_host(tmp_path / "legacy")
    service = ResearchService(config, backend=NoExecutionBoundary())
    # Original bounded choice requires two legal alternatives before discovery.
    for task_id in ("q-legacy-one", "q-legacy-two"):
        service.ledger.enqueue(Signal(task_id=task_id, workspace=config.workspace, scope="science",
                                      kind="opportunity", required_capability="research"))
    r1 = ResearchService(configured_host(tmp_path / "r1", r1=True), backend=NoExecutionBoundary())
    before = {tool.name: tool.model_dump() for tool in loop.run_until_complete(create_server(r1).list_tools())}
    assert R1_TOOLS | LEGACY_TOOLS <= before.keys()
    selected = ChoiceService(service) if choice_only else service
    server = registered_mcp.create_registered_server(selected)
    catalogue = {tool.name: tool.model_dump() for tool in loop.run_until_complete(server.list_tools())}
    assert set(catalogue) == LEGACY_TOOLS
    assert catalogue == {name: before[name] for name in LEGACY_TOOLS}
    result = loop.run_until_complete(server.call_tool("discover_tasks", {}))[1]
    rows = result["result"] if isinstance(result, dict) and set(result) == {"result"} else result
    assert {row["signal"]["task_id"] for row in rows} == {"q-legacy-one", "q-legacy-two"}
    with pytest.raises(ToolError, match="Unknown tool"):
        loop.run_until_complete(server.call_tool("propose_research_work", {
            "project_id": "q-project", "kind": "question", "goal": "Q forbidden dynamic call",
            "justification": "fixture", "expected_contribution": "question"}))
    if choice_only:
        with pytest.raises(ToolError, match="bounded_choice_disallows"):
            loop.run_until_complete(server.call_tool("search_evidence", {"query": "Q forbidden evidence search"}))
    after = {tool.name: tool.model_dump() for tool in loop.run_until_complete(create_server(r1).list_tools())}
    assert after == before
    assert len(service.ledger.snapshot()) == 2 and service.store.adoptions() == []
    assert r1.ledger.snapshot() == [] and r1.store.adoptions() == []


def test_r1_host_cannot_be_narrowed_into_legacy_authority(tmp_path):
    from morph_research.registered_mcp import create_registered_server

    service = ResearchService(configured_host(tmp_path, r1=True), backend=NoExecutionBoundary())
    with pytest.raises(PermissionError, match="registered_case_mcp_requires_legacy_host"):
        create_registered_server(service)
    assert service.ledger.snapshot() == [] and service.store.adoptions() == []
