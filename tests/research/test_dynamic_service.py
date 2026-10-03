"""Actual formal service chain with fixed output bytes; no candidate execution."""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import socket
import subprocess

import pytest
from pydantic import ValidationError

from contracts.identity import AgentId
from local_assets.models import AssetSafetyError
from local_assets.snapshot import git
from local_assets.store import LocalAssetStore
from orchestration.experiments.generated import IsolationCapability
from orchestration.experiments.trusted import (
    IsolationProbeRecord, TrustedCriteriaRecord, TrustedCriteriaRegistry,
)
from swarm.budget import BudgetBlocked
from swarm.models import BudgetPolicy, ExecutionBound, RunLimits
from swarm.research.models import HostConfig, ResearchEnvelope
from swarm.research.dynamic import GeneratedHostSettings
from swarm.research.server import create_server
from swarm.research.service import ResearchService
from tests.experiments.generated_helpers import (
    GENERATED_CODE, make_poisson_plan, poisson_reference_output, poisson_wrong_output,
)
from tests.local_assets.test_generated_validation import FakeBridge


@pytest.fixture(autouse=True)
def no_candidate_process_or_network(monkeypatch):
    original = subprocess.Popen
    # Windows creates an internal loopback socket pair for the trusted event
    # loop. Construct it before denying all candidate/network connections.
    runner = asyncio.Runner()
    runner.get_loop()
    monkeypatch.setattr(asyncio, "run", runner.run)

    def process(argv, *args, **kwargs):
        if not isinstance(argv, list) or not argv or argv[0] != "git":
            raise AssertionError("only trusted Git is permitted in service fixture")
        return original(argv, *args, **kwargs)

    def denied(*args, **kwargs):
        raise AssertionError("candidate process/network forbidden")

    monkeypatch.setattr(subprocess, "Popen", process)
    monkeypatch.setattr(os, "system", denied)
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket.socket, "connect_ex", denied)
    yield
    runner.close()


def setup(tmp_path, *, outcome="succeeded", refuted=False):
    workspace = tmp_path / "project"
    workspace.mkdir()
    (workspace / "science").mkdir()
    (workspace / "science" / "README.txt").write_text("inert isolated fixture\n")
    git(workspace, "init", "-b", "fixture")
    git(workspace, "add", "science")
    git(workspace, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-m", "fixture")
    revision = git(workspace, "rev-parse", "HEAD").decode().strip()
    plan = make_poisson_plan().model_copy(update={"candidate_revision": revision})
    limits = RunLimits(max_tasks=30, max_attempts=30, max_runtime_seconds=600)
    config = HostConfig(ledger_path=str(tmp_path / "state" / "tasks.sqlite3"), swarm_id="generated-service",
        workspace=str(workspace), worker_id="author", agent=AgentId(role="builder", instance=1),
        authorized_scopes=("science",), capabilities=("research",), assets_root=str(tmp_path / "state" / "assets"),
        evidence_root=str(tmp_path / "archive"), project_id=plan.project_id, authorization_ref=plan.authorization_ref,
        research_provenance="mock", research_envelope=ResearchEnvelope(goal="approved fixture goal", limits=limits,
            data_bounds={"data": "local fixture only"},
            actions=("read", "note", "branch", "propose", "choose", "claim", "review", "experiment", "apply")),
        research_budget_path=str(tmp_path / "state" / "budget.sqlite3"),
        research_budget_policy=BudgetPolicy(max_cost_usd=10, unbounded_reservation_usd=0.1,
            allow_unknown_usage=True, allow_unknown_cost=True, limits=limits),
        research_execution_bound=ExecutionBound(provider="fixture", model="fixed-output", input_tokens=0, max_output_tokens=0),
        generated_experiments={"mode": "mock", "environment": plan.environment.model_dump(mode="json"),
            "resources": plan.backend.model_dump(mode="json"), "criteria": [TrustedCriteriaRecord(
                spec=plan.evaluation, approved_by="evaluation-owner", approved_at=1_000_000).model_dump(mode="json")],
            "fixture_workspace": str(tmp_path), "instance_id": "service-fixture", "fixture_outcome": outcome,
            "fixture_output": (poisson_wrong_output(100) if refuted else poisson_reference_output(100)).decode()})
    s = member(config)
    s.create_project(plan.project_id, "approved fixture goal")
    s.create_branch(plan.project_id, plan.branch_id, "generated branch", "inspect dynamic Python")
    s.create_branch(plan.project_id, "alternative", "another branch", "keep exploration legal")
    return s, plan


def member(config, worker=None, instance=1):
    if worker is not None:
        config = config.model_copy(update={"worker_id": worker, "agent": AgentId(role="reviewer", instance=instance)})
    store = LocalAssetStore(config.assets_root, bridge=FakeBridge(), research_provenance="mock",
                            fixture_workspace=config.generated_experiments["fixture_workspace"],
                            generated_criteria=TrustedCriteriaRegistry(tuple(TrustedCriteriaRecord.model_validate(r)
                                for r in config.generated_experiments["criteria"])))
    # No executor injection: exercises the installed host-selected fixture backend.
    return ResearchService(config, store=store)


def prepare(s, plan, *, purpose="original", asset_id=None, dependencies=()):
    proposal = s.propose_work(plan.project_id, "experiment", "work " + purpose, "inspect frozen conditions", "evidence",
                              branch_id=plan.branch_id, dependencies=dependencies)
    task = proposal["task_id"]
    assert s.choose(task, reason="review this proposal")["selected"] == task
    lease = s.claim(task, ttl_seconds=300)
    assert lease is not None
    token = lease["token"]
    plan = plan.model_copy(update={"task_id": task})
    prepared = s.prepare_candidate_experiment(task, token, plan.model_dump(mode="json"),
        {"experiment.py": GENERATED_CODE} if asset_id is None else None, asset_id=asset_id, purpose=purpose)
    assert prepared["admitted"] and not prepared["execution_started"]
    assert prepared["provenance"] == "mock"
    assert s.prepare_candidate_experiment(task, token, plan.model_dump(mode="json"),
        {"experiment.py": GENERATED_CODE} if asset_id is None else None, asset_id=asset_id, purpose=purpose) == prepared
    return task, token, prepared


def execute_observe(s, task, token, asset, purpose):
    admitted = s.admit_candidate_experiment(task, token)
    assert admitted["admitted"] and not admitted["execution_started"]
    execution = asyncio.run(s.execute(task, token))
    run = execution["run_id"]
    report = s.observe(task, token, asset, run, purpose)
    assert report["source_attempt"]["task_id"] == task
    assert report["provenance"] == "mock"
    return run, report


def test_original_artifact_reader_is_bounded_task_bound_and_rechecks_mutation(tmp_path):
    s, plan = setup(tmp_path)
    task, token, prepared = prepare(s, plan)
    run, _ = execute_observe(s, task, token, prepared["asset_id"], "original")
    output = s.artifact(task, run, "outputs/output.json")
    assert output["archive_status"] == "verified" and output["provenance"] == "mock"
    assert not output["truncated"] and len(json.loads(output["content"])["x"]) == 101
    with pytest.raises(AssetSafetyError, match="inline_limit"):
        s.artifact(task, run, "outputs/output.json", max_bytes=1)
    with pytest.raises(AssetSafetyError, match="not_in_original_archive"):
        s.artifact(task, run, "../host.json")
    with pytest.raises(AssetSafetyError, match="unknown_task_run"):
        s.artifact(task, "unknown-run", "outputs/output.json")
    raw = Path(s.config.evidence_root, run, "outputs", "output.json")
    raw.write_bytes(b'{}')
    with pytest.raises(ValueError):
        s.artifact(task, run, "outputs/output.json")


@pytest.mark.parametrize("refuted", [False, True])
def test_dynamic_service_accepts_only_independent_original_chain_and_changes_opportunities(tmp_path, refuted):
    author, plan = setup(tmp_path, refuted=refuted)
    task, token, prepared = prepare(author, plan)
    asset = prepared["asset_id"]
    run, report = execute_observe(author, task, token, asset, "original")
    assert report["execution_state"] == "succeeded"
    assert report["scientific_verdict"] == ("failed" if refuted else "passed")
    completed = author.complete_research(task, token, asset, run)
    assert author.accept_result(completed["result_id"])["accepted"] is False
    reviewer = member(author.config, "reviewer", 2)
    assert reviewer.accept_result(completed["result_id"])["accepted"] is False
    review_task, review_token, _ = prepare(reviewer, plan, purpose="reproduction", asset_id=asset, dependencies=(task,))
    review_run, _ = execute_observe(reviewer, review_task, review_token, asset, "reproduction")
    assert reviewer.accept_result(completed["result_id"])["accepted"] is False
    reviewer.complete_research(review_task, review_token, asset, review_run)
    assert reviewer.accept_result(completed["result_id"])["accepted"] is True
    advice = reviewer.research_advisory()
    contribution = advice["contributions"][0]
    assert contribution["reviewer"] == "reviewer" and contribution["provenance"] == "mock"
    assert contribution["hypothesis"] == ("refuted" if refuted else "supported")
    result_id = completed["result_id"]
    opportunity = next(x for x in advice["opportunities"]["opportunities"] if x["branch_id"] == plan.branch_id)
    assert opportunity["refuted_by" if refuted else "supported_by"] == [result_id]
    assert opportunity["share"] < .5 if refuted else opportunity["share"] > .5
    follow = reviewer.propose_work(plan.project_id, "question", "follow up", "j", "e", branch_id=plan.branch_id)
    discovered = reviewer.discover()
    assert next(x for x in discovered if x["signal"]["task_id"] == follow["task_id"])["research_opportunity"] == opportunity
    choice = reviewer.choose(follow["task_id"], reason="follow evidence")
    lease = reviewer.claim(follow["task_id"], ttl_seconds=300)
    assert choice["selected"] == lease["research_selection"]["actual_task_id"]
    assert result_id in str(lease["research_selection"])
    assert reviewer.research_context()["research_v1"]["effective_contributions"] == advice["contributions"]
    assert reviewer.budget.snapshot().tokens is None
    assert reviewer.budget.snapshot().actual_cost_usd is None
    assert not author.store.adoptions()


def test_dynamic_service_original_inheritance_apply_receipt_is_explicitly_mock(tmp_path):
    author, plan = setup(tmp_path)
    task, token, prepared = prepare(author, plan)
    asset = prepared["asset_id"]
    run, _ = execute_observe(author, task, token, asset, "original")
    author.complete_research(task, token, asset, run)
    reviewer = member(author.config, "reviewer", 2)
    review_task, review_token, review_prepared = prepare(reviewer, plan, purpose="reproduction", asset_id=asset, dependencies=(task,))
    review_run, _ = execute_observe(reviewer, review_task, review_token, asset, "reproduction")
    reviewer.approve(review_task, review_token, asset, review_prepared["report"]["report_id"])
    reviewer.complete_research(review_task, review_token, asset, review_run)
    consumer = member(author.config, "consumer", 3)
    child_task, child_token, _ = prepare(consumer, plan, purpose="inheritance", asset_id=asset, dependencies=(task, review_task))
    execute_observe(consumer, child_task, child_token, asset, "inheritance")
    consumed = consumer.inherit(child_task, child_token, asset,
        {"science/experiment.py": "science/experiment.py"}, {"science/experiment.py": None}, plan.candidate_revision)
    child = consumed["candidate_asset_id"]
    validated = consumer.validate_files(child_task, child_token, child)
    consumer.approve(child_task, child_token, child, validated["report_id"])
    assert not consumer.store.adoptions()
    receipt = consumer.apply(child_task, child_token, child, validated["report_id"], consumed["context"]["execution_id"])
    assert receipt["adopted"] and receipt["adoption"]["provenance"] == "mock"
    assert consumer.ledger.get(child_task).status == "completed"
    assert Path(consumer.config.workspace, "science", "experiment.py").read_text() == GENERATED_CODE
    assert member(author.config, "late", 4).store.adoptions() == consumer.store.adoptions()
    package = consumer.research_package()
    assert package["adoption_receipts"] == [receipt["adoption"]]
    assert len(package["executions"]) == 3
    assert all(e["archive_status"] == "verified" for e in package["executions"])
    assert all(e["verified_result"]["provenance"] == "mock" for e in package["executions"])
    assert not package["completion_claim"] and not package["tasks_truncated"]
    assert len(consumer.research_package(limit=1)["tasks"]) == 1
    assert consumer.research_package(limit=1)["tasks_truncated"]
    # A later independently versioned candidate may edit the applied bytes.
    # Its native snapshot preserves the old worktree; the code is not executed.
    next_task = consumer.propose_work(plan.project_id, "experiment", "version two", "refine code", "new evidence",
                                     branch_id=plan.branch_id, dependencies=(child_task,))["task_id"]
    next_lease = consumer.claim(next_task, ttl_seconds=300)
    changed_code = GENERATED_CODE + "\n# independent candidate version two\n"
    next_plan = make_poisson_plan(code=changed_code.encode()).model_copy(update={
        "task_id": next_task, "candidate_revision": plan.candidate_revision})
    next_prepared = consumer.prepare_candidate_experiment(next_task, next_lease["token"], next_plan.model_dump(mode="json"),
                                                         {"experiment.py": changed_code})
    next_candidate = consumer.store.fetch(next_prepared["asset_id"])
    assert next_candidate.changes[0].before == GENERATED_CODE
    assert next_candidate.changes[0].after == changed_code
    assert next_candidate.base_head == plan.candidate_revision
    assert next_candidate.base_revision != next_candidate.base_head
    assert consumer.store.fetch(asset).changes[0].after == GENERATED_CODE
    assert Path(consumer.config.workspace, "science", "experiment.py").read_text() == GENERATED_CODE


@pytest.mark.parametrize("outcome", ["failed", "timeout", "unknown"])
def test_dynamic_service_failure_is_not_refutation_and_unknown_is_not_retried(tmp_path, outcome):
    s, plan = setup(tmp_path, outcome=outcome)
    task, token, prepared = prepare(s, plan)
    result = asyncio.run(s.execute(task, token))
    assert result["result"]["scientific_verdict"] == "not_evaluated"
    assert result["result"]["generated_assessment"]["hypothesis"] != "refuted"
    assert s.research_advisory()["contributions"] == []
    if outcome == "unknown":
        with pytest.raises(BudgetBlocked):
            asyncio.run(s.execute(task, token))
        reopened = member(s.config)
        with pytest.raises(BudgetBlocked):
            reopened._budget_ready()
        assert reopened.feedback_store.trusted() == []


def test_dynamic_mcp_preparation_rejects_self_declared_approval_and_environment(tmp_path):
    s, plan = setup(tmp_path)
    task = s.propose_work(plan.project_id, "experiment", "bad", "j", "e", branch_id=plan.branch_id)["task_id"]
    s.claim(task, ttl_seconds=300)
    bad = plan.model_copy(update={"task_id": task, "evaluation": plan.evaluation.model_copy(update={
        "max_abs_tolerance": .5, "approved": True, "approved_by": "caller"})})
    server = create_server(s)

    async def run():
        with pytest.raises(Exception, match="frozen_evaluation"):
            await server.call_tool("prepare_candidate_experiment", {"task_id": task, "token": 1,
                "plan": bad.model_dump(mode="json"), "files": {"experiment.py": GENERATED_CODE}})
        tools = await server.list_tools()
        assert len(tools) == 23
        for tool in tools:
            assert "fixture_output" not in tool.inputSchema.get("properties", {})
            assert "reviewer" not in tool.inputSchema.get("properties", {})

    asyncio.run(run())
    with pytest.raises(PermissionError, match="environment_outside"):
        s.prepare_candidate_experiment(task, 1, plan.model_copy(update={"task_id": task,
            "backend": plan.backend.model_copy(update={"cpu": 2})}).model_dump(mode="json"), {"experiment.py": GENERATED_CODE})
    assert not [e for e in s.ledger.audit() if e["event"] == "execution_unconfirmed"]


def docker_export_fixture():
    # Deterministic configuration only; this is not an observed Engine identity.
    return {"endpoint": "npipe:////./pipe/dockerDesktopLinuxEngine",
            "daemon_id": "fixture-only-engine", "engine_version": "29.5.3"}


def live_probe_fixture():
    # A real isolation record is never verified here; this only supplies a
    # non-empty probes tuple so the live host settings construct. Admission
    # still fails closed because the probe is unverified and not passed.
    return IsolationProbeRecord(probe_id="fixture-live-probe", backend="opensandbox",
        declared=IsolationCapability(no_host_write=True, no_credentials=True, no_host_control=True,
            no_privilege=True, export_bounded=True, network_deny=True, cpu_limit=True,
            memory_limit=True, process_limit=True, time_limit=True, self_owned_cleanup=True),
        verified=False, passed=False, evidence_ref="fixture-unverified", probed_at=0).model_dump(mode="json")


@pytest.mark.parametrize("configured", [False, True])
def test_host_docker_export_roundtrip_factory_and_no_implicit_admission(tmp_path, monkeypatch, configured):
    s, plan = setup(tmp_path)
    settings = {key: value for key, value in s.config.generated_experiments.items()
                if not key.startswith("fixture_")}
    settings.update(mode="live", runtime_profile="fixture-only-profile", server_process_limit=16,
                    probes=[live_probe_fixture()])
    if configured:
        settings["docker_export"] = docker_export_fixture()
    # Neither an unapproved remote endpoint nor a context can supply this field.
    monkeypatch.setenv("DOCKER_HOST", "tcp://unapproved.invalid:2375")
    monkeypatch.setenv("DOCKER_CONTEXT", "unapproved-context")
    config = HostConfig.model_validate_json(s.config.model_copy(update={
        "generated_experiments": settings, "research_provenance": "live",
        "assets_root": str(tmp_path / "config-only-live-assets")}).model_dump_json())
    trusted = GeneratedHostSettings.model_validate(config.generated_experiments)
    store = LocalAssetStore(config.assets_root, bridge=FakeBridge(), research_provenance="live",
                            generated_criteria=s.generated.criteria)
    service = ResearchService(config, store=store)
    backend = service.generated.executor.backend
    actual = backend.configuration(plan)
    assert actual.docker_export == trusted.docker_export
    assert (actual.docker_export is not None) is configured
    if configured:
        assert actual.docker_export.daemon_id == "fixture-only-engine"
        assert actual.docker_export.api_version == "1.52"
        assert actual.docker_export.request_timeout_seconds == 10
    isolation = backend.isolation()
    assert not isolation.verified and isolation.probe == "not_run"
    assert not service.generated.probes.is_verified(isolation)
    assert not [e for e in service.ledger.audit() if e["event"] == "execution_unconfirmed"]


def test_host_live_mode_rejects_empty_probes(tmp_path):
    s, plan = setup(tmp_path)
    settings = {key: value for key, value in s.config.generated_experiments.items()
                if not key.startswith("fixture_")}
    settings.update(mode="live", runtime_profile="fixture-only-profile", server_process_limit=16)
    with pytest.raises(ValidationError, match="live_mode_requires_verified_probes"):
        GeneratedHostSettings.model_validate(settings)


def test_host_generated_settings_require_non_empty_criteria(tmp_path):
    s, plan = setup(tmp_path)
    settings = {key: value for key, value in s.config.generated_experiments.items()
                if not key.startswith("fixture_")}
    settings["criteria"] = []
    with pytest.raises(ValidationError, match="criteria"):
        GeneratedHostSettings.model_validate(settings)


@pytest.mark.parametrize("changed", [
    {"endpoint": "tcp://localhost:2375"}, {"engine_version": "unknown"},
    {"daemon_id": ""}, {"api_version": "1.51"}, {"request_timeout_seconds": 11},
])
def test_host_docker_export_invalid_configuration_rejected(tmp_path, changed):
    s, _ = setup(tmp_path)
    export = docker_export_fixture() | changed
    config = s.config.model_copy(update={"generated_experiments": {
        **s.config.generated_experiments, "docker_export": export}})
    with pytest.raises(ValidationError):
        member(config)


def test_host_docker_export_cannot_rebind_existing_project(tmp_path):
    s, plan = setup(tmp_path)
    config = s.config.model_copy(update={"generated_experiments": {
        **s.config.generated_experiments, "docker_export": docker_export_fixture()}})
    changed = member(config)
    with pytest.raises(ValueError, match="^project_identity_cannot_change$"):
        changed.create_project(plan.project_id, "approved fixture goal")
    with pytest.raises(PermissionError, match="^project_host_envelope_changed$"):
        changed.research_context(plan.project_id)
    assert s.generated.settings.docker_export is None
    assert s.research_context(plan.project_id)["project"]["project_id"] == plan.project_id


def test_mcp_candidate_cannot_supply_docker_export(tmp_path):
    s, plan = setup(tmp_path)
    task = s.propose_work(plan.project_id, "experiment", "bad control", "j", "e",
                          branch_id=plan.branch_id)["task_id"]
    lease = s.claim(task, ttl_seconds=300)
    supplied = plan.model_copy(update={"task_id": task}).model_dump(mode="json")
    supplied["docker_export"] = docker_export_fixture()
    server = create_server(s)

    async def run():
        tools = await server.list_tools()
        for tool in tools:
            assert "docker_export" not in tool.inputSchema.get("properties", {})
        with pytest.raises(Exception, match="docker_export"):
            await server.call_tool("prepare_candidate_experiment", {
                "task_id": task, "token": lease["token"], "plan": supplied,
                "files": {"experiment.py": GENERATED_CODE}})

    asyncio.run(run())
    assert s.generated.settings.docker_export is None
    assert not s.ledger.get(task).acceptance.get("generated_plan")
    assert not [e for e in s.ledger.audit() if e["event"] == "execution_unconfirmed"]
