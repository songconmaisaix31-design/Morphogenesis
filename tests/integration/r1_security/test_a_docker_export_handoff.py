"""Affected A configuration wiring only, with original service/store/MCP checks."""
import pytest
from mcp.server.fastmcp.exceptions import ToolError

from contracts.identity import AgentId
from local_assets.store import LocalAssetStore
from orchestration.experiments.trusted import TrustedCriteriaRecord, TrustedCriteriaRegistry
from swarm.models import BudgetPolicy, ExecutionBound, RunLimits
from swarm.research.dynamic import GeneratedHostSettings
from swarm.research.models import HostConfig, ResearchEnvelope
from swarm.research.server import create_server
from swarm.research.service import ResearchService
from tests.integration.r1_security.docker_export_fixture import SERVER, docker_settings
from tests.integration.r1_security.test_a_dynamic_mcp import fixture, claimed
from tests.integration.r1_security.test_b_configured_sdk_boundary import configured, capture_create
from tests.integration.r1_security.test_b_generated_boundaries import CODE
from tests.integration.r1_security.test_b_mock_adoption import InertAssetBridge


def configured_service(root, *, export=True):
    p, probe, _ = configured()
    workspace = root / "workspace"
    (workspace / "science").mkdir(parents=True)
    criterion = TrustedCriteriaRecord(spec=p.evaluation, approved_by="q-criteria-owner", approved_at=90)
    limits = RunLimits(max_tasks=10, max_attempts=10, max_runtime_seconds=600)
    # Live mode must declare the host probe it claims (L2 follow-up invariant
    # ``live_mode_requires_verified_probes``). The declared probe was recorded
    # for another runtime profile ("q-probed-fixed-policy" against this host's
    # "q-config-only"), so it cannot verify this backend: isolation stays
    # unverified and execution stays refused, which is what these tests prove.
    settings = dict(mode="live", environment=p.environment.model_dump(mode="json"),
        resources=p.backend.model_dump(mode="json"), criteria=[criterion.model_dump(mode="json")],
        probes=[probe.model_dump(mode="json")],
        instance_id=SERVER, runtime_profile="q-config-only", server_process_limit=p.backend.process_limit,
        domain="127.0.0.1:65534")
    if export:
        settings["docker_export"] = docker_settings().model_dump(mode="json")
    config = HostConfig(ledger_path=str(root / "state/tasks.db"), swarm_id="q-config-only", workspace=str(workspace),
        worker_id="q", agent=AgentId(role="builder", instance=0), authorized_scopes=("science",),
        capabilities=("research",), assets_root=str(root / "state/assets"), evidence_root=str(root / "evidence"),
        project_id="p1", authorization_ref=p.authorization_ref, research_provenance="live",
        research_envelope=ResearchEnvelope(goal="Q configuration only", limits=limits,
            actions=("read", "branch", "experiment")), research_budget_path=str(root / "state/budget.db"),
        research_budget_policy=BudgetPolicy(max_cost_usd=10, unbounded_reservation_usd=.1, limits=limits),
        research_execution_bound=ExecutionBound(provider="fixture", model="fixed-output", input_tokens=0, max_output_tokens=0),
        generated_experiments=settings)
    store = LocalAssetStore(config.assets_root, bridge=InertAssetBridge(), research_provenance="live",
        generated_criteria=TrustedCriteriaRegistry((criterion,)))
    return p, ResearchService(config, store=store)


@pytest.mark.parametrize("explicit", [False, True])
def test_original_factory_preserves_closed_host_field_but_unverified_isolation_cannot_execute(
        monkeypatch, tmp_path, explicit):
    monkeypatch.setenv("DOCKER_HOST", "tcp://unapproved.invalid:2375")
    monkeypatch.setenv("DOCKER_CONTEXT", "unapproved-context")
    p, service = configured_service(tmp_path, export=explicit)
    selected = GeneratedHostSettings.model_validate(service.config.generated_experiments)
    backend = service.generated.executor.backend
    assert backend.configuration(p).docker_export == selected.docker_export
    assert (selected.docker_export is not None) == explicit
    assert not backend.isolation().verified
    calls = capture_create(monkeypatch)
    prepared = service.generated.executor.prepare(p, {"candidate.py": CODE})
    assert prepared.static.passed
    with pytest.raises((ValueError, PermissionError)):
        service.generated.executor.admit(prepared)
    assert calls == []
    assert not [event for event in service.ledger.audit() if event["event"] == "execution_unconfirmed"]


@pytest.mark.parametrize("change", ["disable", "daemon"])
def test_frozen_project_cannot_rebind_docker_export_and_original_facts_remain(monkeypatch, tmp_path, change):
    p, service = configured_service(tmp_path)
    service.create_project(p.project_id, "Q configuration only")
    original = service.research_context(p.project_id)
    events = service.ledger.audit()
    value = None if change == "disable" else {**docker_settings().model_dump(mode="json"), "daemon_id": "another-daemon"}
    changed = service.config.model_copy(update={"generated_experiments": {
        **service.config.generated_experiments, "docker_export": value}})
    reopened = ResearchService(changed, store=service.store)
    with pytest.raises(PermissionError):
        reopened.research_context(p.project_id)
    with pytest.raises(ValueError):
        reopened.create_project(p.project_id, "Q configuration only")
    assert service.research_context(p.project_id) == original
    assert service.ledger.audit() == events


def test_official_mcp_rejects_candidate_control_field_before_persisting_plan(
        monkeypatch, tmp_path, deny_candidate_execution_and_network):
    loop = deny_candidate_execution_and_network
    prepared_fixture = fixture(tmp_path, monkeypatch)
    service = prepared_fixture.author
    task, token, p = claimed(loop, service, prepared_fixture.plan)
    server = create_server(service)
    tools = loop.run_until_complete(server.list_tools())
    for tool in tools:
        assert "docker_export" not in tool.inputSchema.get("properties", {})
    payload = p.model_dump(mode="json")
    payload["docker_export"] = docker_settings().model_dump(mode="json")
    with pytest.raises(ToolError):
        loop.run_until_complete(server.call_tool("prepare_candidate_experiment", {
            "task_id": task, "token": token, "plan": payload, "files": {"candidate.py": CODE.decode()}}))
    assert service.generated.settings.docker_export is None
    assert not service.ledger.get(task).acceptance.get("generated_plan")
    assert not [event for event in service.ledger.audit() if event["event"] == "execution_unconfirmed"]
