"""Actual service admission against the original project BudgetLedger.

The injected async boundary returns deterministic mock metadata only; it never
executes Python candidates, tools, providers or network operations.
"""
import pytest

from contracts.identity import AgentId
from swarm.budget import BudgetBlocked
from swarm.models import BudgetPolicy, ExecutionBound, ModelPrices, RunLimits, Signal
from swarm.research.models import HostConfig, ResearchEnvelope
from swarm.research.service import ResearchService
from swarm.task_ledger import TaskLedger


class InjectedCrash(BaseException):
    pass


class InertExecutionBoundary:
    def __init__(self, effect="known"):
        self.effect = effect
        self.calls = []

    async def execute(self, plan, run_id, lease):
        self.calls.append((lease.task_id, run_id, lease.worker_id))
        if self.effect == "crash":
            raise InjectedCrash("Q deterministic boundary interruption")
        return {"execution_state": "succeeded" if self.effect == "known" else "unknown",
            "effect_state": self.effect, "scientific_verdict": "not_evaluated", "provenance": "mock",
            # Original BudgetLedger accepts a provider response envelope, not
            # an invented monetary bill. This is fixture metering only.
            "usage": {"usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}
                     if self.effect == "known" else None}


def host(root, *, allowance=0.6):
    limits = RunLimits(max_tasks=10, max_attempts=10, max_attempts_per_task=3)
    envelope = ResearchEnvelope(goal="Q bounded fixture", limits=limits,
        actions=("read", "note", "branch", "propose", "choose", "claim", "review", "experiment"))
    return HostConfig(ledger_path=str(root / "ledger.db"), swarm_id="q-budget-run",
        workspace=str(root / "workspace"), worker_id="member-one",
        agent=AgentId(role="builder", instance=0), authorized_scopes=("science",), capabilities=("research",),
        assets_root=str(root / "assets"), evidence_root=str(root / "evidence"),
        project_id="q-project", authorization_ref="q-host-fixture-authorization", research_envelope=envelope,
        research_budget_path=str(root / "budget.db"),
        research_budget_policy=BudgetPolicy(max_cost_usd=1, unbounded_reservation_usd=allowance,
            prices=ModelPrices(provider="q-mock", model="fixture", input_usd_per_million=1,
                               output_usd_per_million=1), limits=limits),
        research_execution_bound=ExecutionBound(provider="q-mock", model="fixture",
            input_tokens=10, max_output_tokens=10))


def opened(config, boundary):
    ledger = TaskLedger(config.ledger_path, config.swarm_id,
                        limits=config.research_envelope.limits, clock=lambda: 100.0)
    return ResearchService(config, ledger=ledger, backend=boundary)


def task(s, name):
    s.create_branch(s.config.project_id, name, "Q branch " + name, "bounded fixture")
    s.ledger.enqueue(Signal(task_id=name, workspace=s.config.workspace, scope="science/" + name,
        kind="opportunity", required_capability="research",
        payload={"project_id": s.config.project_id, "branch_id": name}),
        acceptance={"experiment_plan": {"fixture_only": True}})


def execute(s, name, loop):
    claim = s.claim(name)
    assert claim is not None, "legal fixture task must be claimable"
    return loop.run_until_complete(s.execute(name, claim["token"]))


def test_known_mock_execution_consumes_one_project_allowance_across_new_member_task_branch(
        tmp_path, deny_candidate_execution_and_network):
    loop = deny_candidate_execution_and_network
    config = host(tmp_path)
    boundary = InertExecutionBoundary()
    s = opened(config, boundary)
    s.create_project(config.project_id, config.research_envelope.goal)
    task(s, "first")
    first = execute(s, "first", loop)
    assert first["result"]["provenance"] == "mock"
    assert len(boundary.calls) == 1
    assert s.budget.snapshot().admission_charged_usd == 0.6
    assert s.budget.snapshot().pending_reservations == 0
    reopened = opened(config.model_copy(update={"worker_id": "member-two",
        "agent": AgentId(role="builder", instance=1)}), boundary)
    task(reopened, "second")
    with pytest.raises((BudgetBlocked, PermissionError, ValueError)):
        execute(reopened, "second", loop)
    assert len(boundary.calls) == 1, "new task/branch/member reset the existing project allowance"
    assert reopened.budget.snapshot().admission_charged_usd == 0.6


@pytest.mark.parametrize("effect", ["unknown", "crash"])
def test_unknown_or_crash_retains_project_hold_and_blocks_new_execution(
        tmp_path, deny_candidate_execution_and_network, effect):
    loop = deny_candidate_execution_and_network
    config = host(tmp_path, allowance=0.2)
    boundary = InertExecutionBoundary(effect)
    s = opened(config, boundary)
    s.create_project(config.project_id, config.research_envelope.goal)
    task(s, "first")
    if effect == "crash":
        with pytest.raises(InjectedCrash):
            execute(s, "first", loop)
    else:
        execute(s, "first", loop)
    assert len(boundary.calls) == 1
    before = s.budget.snapshot()
    assert before.reserved_estimate_usd == 0.2
    assert before.tokens is None and before.estimated_cost_usd is None
    reopened = opened(config, boundary)
    with pytest.raises((BudgetBlocked, PermissionError, ValueError)):
        task(reopened, "second")
        execute(reopened, "second", loop)
    assert len(boundary.calls) == 1
    assert reopened.budget.snapshot().reserved_estimate_usd == 0.2


def test_interrupt_after_reserve_before_task_execution_cannot_resume_as_fresh_allowance(
        tmp_path, monkeypatch, deny_candidate_execution_and_network):
    loop = deny_candidate_execution_and_network
    config = host(tmp_path, allowance=0.2)
    boundary = InertExecutionBoundary()
    s = opened(config, boundary)
    s.create_project(config.project_id, config.research_envelope.goal)
    task(s, "first")

    def interrupted(*args, **kwargs):
        raise InjectedCrash("Q crash after durable reserve, before ledger begin")

    monkeypatch.setattr(s.ledger, "begin_execution", interrupted)
    with pytest.raises(InjectedCrash):
        execute(s, "first", loop)
    assert boundary.calls == []
    assert s.budget.snapshot().reserved_estimate_usd == 0.2
    reopened = opened(config.model_copy(update={"worker_id": "replacement-member"}), boundary)
    with pytest.raises((BudgetBlocked, PermissionError, ValueError)):
        task(reopened, "second")
        execute(reopened, "second", loop)
    assert boundary.calls == [], "unreconciled reservation was bypassed on restart"
    assert reopened.budget.snapshot().reserved_estimate_usd >= 0.2


@pytest.mark.parametrize("replacement", ["swarm", "budget_path"])
def test_project_binding_prevents_new_run_or_budget_database_reset(
        tmp_path, deny_candidate_execution_and_network, replacement):
    loop = deny_candidate_execution_and_network
    config = host(tmp_path)
    boundary = InertExecutionBoundary()
    s = opened(config, boundary)
    s.create_project(config.project_id, config.research_envelope.goal)
    task(s, "first")
    execute(s, "first", loop)
    update = {"swarm_id": "replacement-run"} if replacement == "swarm" else {
        "research_budget_path": str(tmp_path / "replacement-budget.db")}
    with pytest.raises((BudgetBlocked, PermissionError, ValueError)):
        reopened = opened(config.model_copy(update=update), boundary)
        reopened.create_project(config.project_id, config.research_envelope.goal)
        task(reopened, "second")
        execute(reopened, "second", loop)
    assert len(boundary.calls) == 1
    assert s.budget.snapshot().admission_charged_usd == 0.6
