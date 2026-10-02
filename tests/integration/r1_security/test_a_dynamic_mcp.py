"""Official MCP and actual generated service chain with fixed host output only.

Git/GEP plumbing are deterministic fixtures; all original domain and ledger
checks run. Host candidate execution, native processes and sockets stay denied.
"""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from mcp.server.fastmcp.exceptions import ToolError

from contracts.identity import AgentId
from local_assets.store import LocalAssetStore
from local_assets import apply as applying
from orchestration.experiments.trusted import TrustedCriteriaRecord, TrustedCriteriaRegistry
from swarm.models import BudgetPolicy, ExecutionBound, RunLimits
from swarm.research import dynamic, service as service_module
from swarm.research.models import HostConfig, ResearchEnvelope
from swarm.research.server import create_server
from swarm.research.service import ResearchService
from swarm.task_ledger import TaskLedger
from tests.integration.r1_security.test_b_generated_boundaries import CODE, plan, raw_output
from tests.integration.r1_security.test_b_mock_adoption import InertAssetBridge, git_plumbing_fixture


def fixture(root, monkeypatch, *, outcome="succeeded", refuted=False):
    import time

    monkeypatch.setattr(time, "time", lambda: 100.0)
    target = root / "workspace"
    (target / "science").mkdir(parents=True)
    (target / ".git/refs/heads").mkdir(parents=True)
    (target / ".git/HEAD").write_text("ref: refs/heads/fixture\n")
    (target / ".git/refs/heads/fixture").write_text("a" * 40 + "\n")
    plumbing = SimpleNamespace(target=target)
    git_plumbing_fixture(monkeypatch, plumbing)

    def git(workspace, *args):
        assert Path(workspace) == target
        if args == ("rev-parse", "HEAD"):
            return b"a" * 40
        assert args == ("ls-tree", "a" * 40, "--", "science/candidate.py")
        return b""

    def snapshot(workspace, scope, snapshots):
        assert Path(workspace) == target and scope == "science"
        assert not (target / "science/candidate.py").exists()
        return "a" * 40, "a" * 40

    def check_snapshot(workspace, candidate, snapshots):
        assert Path(workspace) == target
        assert candidate.base_head == candidate.base_revision == "a" * 40
        assert list((target / "science").iterdir()) == []
        assert all(change.before is None for change in candidate.changes)

    monkeypatch.setattr(dynamic, "git", git)
    monkeypatch.setattr(dynamic, "snapshot_revision", snapshot)
    monkeypatch.setattr(service_module, "snapshot_revision", snapshot)
    monkeypatch.setattr(applying, "check_snapshot", check_snapshot)
    p = plan()
    p = p.model_copy(update={"environment": p.environment.model_copy(update={
        "image": "fixture@sha256:" + "c" * 64, "image_digest": "sha256:" + "c" * 64})})
    criterion = TrustedCriteriaRecord(spec=p.evaluation, approved_by="criteria-owner", approved_at=90)
    registry = TrustedCriteriaRegistry(records=(criterion,))
    limits = RunLimits(max_tasks=30, max_attempts=30, max_runtime_seconds=600)
    output = json.loads(raw_output())
    if refuted:
        output["u"] = [0.0] * len(output["x"])
    config = HostConfig(ledger_path=str(root / "state/tasks.db"), swarm_id="q-dynamic-mcp", workspace=str(target),
        worker_id="author", agent=AgentId(role="builder", instance=0), authorized_scopes=("science",),
        capabilities=("research",), assets_root=str(root / "state/assets"), evidence_root=str(root / "evidence"),
        project_id="p1", authorization_ref=p.authorization_ref, research_provenance="mock",
        research_envelope=ResearchEnvelope(goal="Q fixed output fixture", limits=limits,
            actions=("read", "note", "branch", "propose", "choose", "claim", "review", "experiment", "apply")),
        research_budget_path=str(root / "state/budget.db"),
        research_budget_policy=BudgetPolicy(max_cost_usd=10, unbounded_reservation_usd=.1,
            allow_unknown_usage=True, allow_unknown_cost=True, limits=limits),
        research_execution_bound=ExecutionBound(provider="fixture", model="fixed-output", input_tokens=0, max_output_tokens=0),
        generated_experiments={"mode": "mock", "environment": p.environment.model_dump(mode="json"),
            "resources": p.backend.model_dump(mode="json"), "criteria": [criterion.model_dump(mode="json")],
            "fixture_workspace": str(root), "instance_id": "q-service-fixture", "fixture_outcome": outcome,
            "fixture_output": json.dumps(output)})
    bridge = InertAssetBridge()

    def member(worker="author", instance=0):
        selected = config.model_copy(update={"worker_id": worker,
            "agent": AgentId(role="builder" if worker == "author" else "reviewer", instance=instance)})
        assets = LocalAssetStore(config.assets_root, bridge=bridge, research_provenance="mock",
                                fixture_workspace=root, generated_criteria=registry)
        ledger = TaskLedger(config.ledger_path, config.swarm_id, limits=limits, clock=lambda: 100.0)
        return ResearchService(selected, store=assets, ledger=ledger)

    author = member()
    author.create_project("p1", "Q fixed output fixture")
    author.create_branch("p1", "b1", "bounded dynamic", "inspect fixed conditions")
    author.create_branch("p1", "other", "other legal branch", "future work")
    return SimpleNamespace(author=author, member=member, plan=p, target=target)


def call(loop, service, name, **arguments):
    returned = loop.run_until_complete(create_server(service).call_tool(name, arguments))
    assert isinstance(returned, tuple) and len(returned) == 2
    result = returned[1]
    assert isinstance(result, dict), "official tool returned no structured result"
    return result["result"] if set(result) == {"result"} else result


def claimed(loop, service, p, *, purpose="original", dependencies=()):
    proposal = call(loop, service, "propose_research_work", project_id="p1", kind="experiment",
        goal="Q " + purpose, justification="frozen host fixture", expected_contribution="bounded evidence",
        branch_id="b1", dependencies=list(dependencies))
    task = proposal["task_id"]
    assert call(loop, service, "choose_research_work", task_id=task, reason="fixture relevance")["selected"] == task
    lease = call(loop, service, "lease_task", action="claim", task_id=task, ttl_seconds=300)
    assert lease["worker_id"] == service.config.worker_id
    return task, lease["token"], p.model_copy(update={"task_id": task})


def prepared(loop, service, p, *, purpose="original", asset=None, dependencies=()):
    task, token, frozen = claimed(loop, service, p, purpose=purpose, dependencies=dependencies)
    args = dict(task_id=task, token=token, plan=frozen.model_dump(mode="json"), purpose=purpose,
                files={"candidate.py": CODE.decode()} if asset is None else None, asset_id=asset)
    admitted = call(loop, service, "prepare_candidate_experiment", **args)
    assert admitted["admitted"] and not admitted["execution_started"]
    assert admitted["provenance"] == "mock"
    assert call(loop, service, "prepare_candidate_experiment", **args) == admitted
    return task, token, admitted


def observed(loop, service, task, token, asset, purpose):
    run = call(loop, service, "research_experiment", action="run", task_id=task, token=token)
    report = call(loop, service, "verify_research", task_id=task, token=token, asset_id=asset,
                  run_id=run["run_id"], purpose=purpose)
    assert report["source_attempt"]["task_id"] == task and report["provenance"] == "mock"
    return run["run_id"], report


def original_and_review(f, loop, *, approve=False):
    author, p = f.author, f.plan
    task, token, admission = prepared(loop, author, p)
    asset = admission["asset_id"]
    run, original = observed(loop, author, task, token, asset, "original")
    completed = call(loop, author, "complete_research_task", task_id=task, token=token, asset_id=asset, run_id=run)
    assert not call(loop, author, "accept_result", result_id=completed["result_id"])["accepted"]
    reviewer = f.member("reviewer", 1)
    assert not call(loop, reviewer, "accept_result", result_id=completed["result_id"])["accepted"]
    review_task, review_token, review_admission = prepared(loop, reviewer, p,
        purpose="reproduction", asset=asset, dependencies=(task,))
    review_run, report = observed(loop, reviewer, review_task, review_token, asset, "reproduction")
    assert not call(loop, reviewer, "accept_result", result_id=completed["result_id"])["accepted"]
    if approve:
        call(loop, reviewer, "approve_candidate", task_id=review_task, token=review_token, asset_id=asset,
             report_id=review_admission["report"]["report_id"])
    call(loop, reviewer, "complete_research_task", task_id=review_task, token=review_token,
         asset_id=asset, run_id=review_run)
    assert call(loop, reviewer, "accept_result", result_id=completed["result_id"])["accepted"]
    return reviewer, task, review_task, asset, completed["result_id"], original


@pytest.mark.parametrize("refuted", [False, True])
def test_official_mcp_generated_original_review_credit_and_future_work(tmp_path, monkeypatch,
        deny_candidate_execution_and_network, refuted):
    loop = deny_candidate_execution_and_network
    f = fixture(tmp_path, monkeypatch, refuted=refuted)
    reviewer, task, review_task, asset, result_id, report = original_and_review(f, loop)
    assert report["scientific_verdict"] == ("failed" if refuted else "passed")
    advice = call(loop, reviewer, "research_advisory", project_id="p1")
    assert len(advice["contributions"]) == 1 and advice["contributions"][0]["provenance"] == "mock"
    row = next(r for r in advice["opportunities"]["opportunities"] if r["branch_id"] == "b1")
    assert row["refuted_by" if refuted else "supported_by"] == [result_id]
    assert row["eligible"] and row["share"] > 0
    if refuted:
        assert row["share"] < next(r["share"] for r in advice["opportunities"]["opportunities"] if r["branch_id"] == "other")
    assert not call(loop, reviewer, "accept_result", result_id=result_id)["accepted"]
    reopened = f.member("reviewer", 1)
    assert reopened.research_advisory()["contributions"] == advice["contributions"]
    assert reopened.budget.snapshot().tokens is None and reopened.budget.snapshot().actual_cost_usd is None
    assert reopened.store.adoptions() == []


def test_official_mcp_generated_inheritance_reaches_only_mock_original_adoption(tmp_path, monkeypatch,
        deny_candidate_execution_and_network):
    loop = deny_candidate_execution_and_network
    f = fixture(tmp_path, monkeypatch)
    reviewer, task, review_task, asset, result_id, report = original_and_review(f, loop, approve=True)
    consumer = f.member("consumer", 2)
    child_task, token, _ = prepared(loop, consumer, f.plan, purpose="inheritance", asset=asset,
                                   dependencies=(task, review_task))
    observed(loop, consumer, child_task, token, asset, "inheritance")
    consumed = call(loop, consumer, "inherit_experience", task_id=child_task, token=token, asset_id=asset,
        path_map={"science/candidate.py": "science/candidate.py"}, preimages={"science/candidate.py": None},
        base_revision=f.plan.candidate_revision)
    child = consumed["candidate_asset_id"]
    report = call(loop, consumer, "research_candidate", action="validate_files", task_id=child_task,
                  token=token, asset_id=child)
    call(loop, consumer, "approve_candidate", task_id=child_task, token=token, asset_id=child, report_id=report["report_id"])
    assert consumer.store.adoptions() == [] and not (f.target / "science/candidate.py").exists()
    receipt = call(loop, consumer, "apply_candidate", task_id=child_task, token=token, asset_id=child,
        report_id=report["report_id"], execution_id=consumed["context"]["execution_id"])
    assert receipt["adopted"] and receipt["adoption"]["provenance"] == "mock"
    assert consumer.ledger.get(child_task).status == "completed"
    assert (f.target / "science/candidate.py").read_bytes() == CODE
    assert f.member("consumer", 2).store.adoptions() == consumer.store.adoptions()


@pytest.mark.parametrize("attack", ["project", "branch", "authorization", "environment", "resources",
                                    "self_approved_evaluator", "data_ref", "stale_token"])
def test_tool_plan_cannot_override_generated_host_authority(tmp_path, monkeypatch,
        deny_candidate_execution_and_network, attack):
    loop = deny_candidate_execution_and_network
    f = fixture(tmp_path, monkeypatch)
    task, token, frozen = claimed(loop, f.author, f.plan)
    payload = frozen.model_dump(mode="json")
    if attack == "project":
        payload["project_id"] = "foreign"
    elif attack == "branch":
        payload["branch_id"] = "other"
    elif attack == "authorization":
        payload["authorization_ref"] = "caller-granted"
    elif attack == "environment":
        payload["environment"]["dependency_lock_sha256"] = "d" * 64
    elif attack == "resources":
        payload["backend"]["cpu"] = 2
    elif attack == "self_approved_evaluator":
        payload["evaluation"].update(max_abs_tolerance=.5, approved=True, approved_by="author")
    elif attack == "data_ref":
        payload["data_refs"] = ["unapproved-external-material"]
    else:
        token += 1
    with pytest.raises(ToolError):
        call(loop, f.author, "prepare_candidate_experiment", task_id=task, token=token,
             plan=payload, files={"candidate.py": CODE.decode()})
    assert "generated_plan" not in f.author.ledger.get(task).acceptance
    assert not [e for e in f.author.ledger.audit() if e["event"] == "execution_unconfirmed"]
    assert f.author.store.adoptions() == []


@pytest.mark.parametrize("outcome", ["failed", "timeout", "unknown"])
def test_formal_generated_failure_never_becomes_refutation_or_credit(tmp_path, monkeypatch,
        deny_candidate_execution_and_network, outcome):
    loop = deny_candidate_execution_and_network
    f = fixture(tmp_path, monkeypatch, outcome=outcome)
    task, token, admission = prepared(loop, f.author, f.plan)
    result = call(loop, f.author, "research_experiment", action="run", task_id=task, token=token)
    assert result["result"]["scientific_verdict"] == "not_evaluated"
    assert result["result"]["generated_assessment"]["hypothesis"] != "refuted"
    assert f.author.research_advisory()["contributions"] == [] and f.author.store.adoptions() == []
    if outcome == "unknown":
        for current in (f.author, f.member()):
            with pytest.raises(ToolError):
                call(loop, current, "research_experiment", action="run", task_id=task, token=token)
        events = [e for e in f.author.ledger.audit() if e["event"] == "execution_unconfirmed"]
        assert len(events) == 1, "unknown generated effect was automatically resent"


def test_same_frozen_task_different_plan_is_refused_without_second_execution(tmp_path, monkeypatch,
        deny_candidate_execution_and_network):
    loop = deny_candidate_execution_and_network
    f = fixture(tmp_path, monkeypatch)
    task, token, admitted = prepared(loop, f.author, f.plan)
    changed = dict(admitted["plan"], claim="a different scientific claim")
    with pytest.raises(ToolError):
        call(loop, f.author, "prepare_candidate_experiment", task_id=task, token=token,
             plan=changed, files={"candidate.py": CODE.decode()})
    assert f.author.ledger.get(task).acceptance["generated_plan"] == admitted["plan"]
    assert not [e for e in f.author.ledger.audit() if e["event"] == "execution_unconfirmed"]
