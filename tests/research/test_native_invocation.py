"""Host-only invocation binding retains the original cumulative budget authority."""
import asyncio
import time
from uuid import uuid4

import pytest

from swarm.budget import BudgetBlocked
from swarm.models import BudgetPolicy, ExecutionBound, ModelPrices
from swarm.research.models import ResearchEnvelope
from swarm.research.server import create_server
from swarm.research.service import ResearchService
from swarm.task_ledger import RunLimitReached, TaskLedger
from tests.research.test_research_v1 import make_service


def setup(tmp_path):
    base = make_service(tmp_path).config
    clock = [time.time() + 1]
    bound = ExecutionBound(provider="fixture", model="inert", input_tokens=100, max_output_tokens=100)
    envelope = ResearchEnvelope(goal="goal",
        actions=("read", "note", "branch", "propose", "choose", "claim", "review", "experiment", "apply"))
    cfg = base.model_copy(update={"authorization_ref": "local-test", "research_envelope": envelope,
        "research_execution_bound": bound, "research_budget_path": str(tmp_path / "budget.sqlite3"),
        "research_budget_policy": BudgetPolicy(max_cost_usd=1, unbounded_reservation_usd=.1,
            allow_unknown_usage=True, prices=ModelPrices(provider="fixture", model="inert",
                input_usd_per_million=1, output_usd_per_million=1))})
    ledger = TaskLedger(cfg.ledger_path, cfg.swarm_id, clock=lambda: clock[0])
    s = ResearchService(cfg, ledger=ledger)
    s.create_project("p1", "goal")
    return s, bound, clock


def attach(s, binding):
    return ResearchService(s.config.model_copy(update={"native_invocation": binding}), ledger=s.ledger)


def test_formal_mcp_claim_accepts_only_own_active_native_hold(tmp_path):
    s, bound, _ = setup(tmp_path)
    task = s.propose_work("p1", "question", "g", "j", "e")["task_id"]
    binding = s.admit_native_invocation(str(uuid4()), bound, ttl_seconds=60)
    assert binding.reservation == s.budget.pending(s.config.worker_id)[0]
    with pytest.raises(BudgetBlocked, match="pending"):
        s.claim(task)
    attached = attach(s, binding)
    assert attached._host_binding() == s._host_binding()
    async def run():
        server = create_server(attached)
        names = [tool.name for tool in await server.list_tools()]
        assert "admit_native_invocation" not in names
        _, claimed = await server.call_tool("lease_task", {"action": "claim", "task_id": task})
        assert claimed["result"]["worker_id"] == s.config.worker_id
    asyncio.run(run())
    assert s.budget.snapshot().pending_reservations == 1


@pytest.mark.parametrize("closed", ["settled", "uncertain", "expired"])
def test_closed_or_expired_binding_cannot_replay_read_or_mutations(tmp_path, closed):
    s, bound, clock = setup(tmp_path)
    binding = s.admit_native_invocation(str(uuid4()), bound, ttl_seconds=60)
    attached = attach(s, binding)
    if closed == "settled":
        s.budget.settle(binding.reservation, {"usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}})
    elif closed == "uncertain":
        s.budget.mark_uncertain(binding.reservation)
    else:
        clock[0] += 60
    for action in (lambda: attached.create_project("p1", "goal"),
                   lambda: attached.research_context(),
                   lambda: attached.submit_note("p1", "expert_opinion", "replay"),
                   lambda: attached.propose_work("p1", "question", "replay", "j", "e"),
                   lambda: attached.choose()):
        with pytest.raises((PermissionError, BudgetBlocked), match="native|unknown"):
            action()


def test_native_admission_rechecks_original_unknown_effect_before_reserving(tmp_path):
    s, bound, _ = setup(tmp_path)
    task = s.propose_work("p1", "question", "g", "j", "e")["task_id"]
    lease = s.ledger.claim(task, s.config.worker_id, locality=s.locality)
    s.ledger.begin_execution(lease, "unknown-execution")
    with pytest.raises(BudgetBlocked, match="unknown_effect"):
        s.admit_native_invocation(str(uuid4()), bound, ttl_seconds=60)
    assert s.budget.snapshot().pending_reservations == 0


def test_native_binding_never_excuses_other_pending_or_unknown_usage(tmp_path):
    s, bound, _ = setup(tmp_path)
    binding = s.admit_native_invocation(str(uuid4()), bound, ttl_seconds=60)
    attached = attach(s, binding)
    task = s.propose_work("p1", "question", "g", "j", "e")["task_id"]
    other = s.budget.reserve("other-member", "another-task", bound, request_id="another-request")
    with pytest.raises(BudgetBlocked, match="pending"):
        attached.claim(task)
    s.budget.mark_uncertain(other)
    assert s.budget.snapshot().sleeping is False  # Unknown-usage allowance does not grant a native retry.
    with pytest.raises(BudgetBlocked, match="unknown"):
        attached.claim(task)


@pytest.mark.parametrize("field", ["worker_id", "project_id", "request_id", "provider", "model"])
def test_native_binding_rejects_mismatched_host_and_original_record(tmp_path, field):
    s, bound, _ = setup(tmp_path)
    binding = s.admit_native_invocation(str(uuid4()), bound, ttl_seconds=60)
    updates = {"native_invocation": binding}
    if field in {"worker_id", "project_id"}:
        updates[field] = "foreign"
    elif field == "request_id":
        updates["native_invocation"] = binding.model_copy(update={
            "reservation": binding.reservation.model_copy(update={"request_id": "native:foreign"})})
    else:
        updates["native_invocation"] = binding.model_copy(update={"reservation": binding.reservation.model_copy(
            update={"bound": bound.model_copy(update={field: "foreign"})})})
    with pytest.raises((PermissionError, BudgetBlocked, ValueError)):
        ResearchService(s.config.model_copy(update=updates), ledger=s.ledger).research_context()


def test_native_admission_keeps_bound_budget_and_request_identity(tmp_path):
    s, bound, _ = setup(tmp_path)
    with pytest.raises((PermissionError, BudgetBlocked), match="bound"):
        s.admit_native_invocation(str(uuid4()), bound.model_copy(update={"input_tokens": 1}), ttl_seconds=60)
    invocation = str(uuid4())
    binding = s.admit_native_invocation(invocation, bound, ttl_seconds=60)
    s.budget.settle(binding.reservation, {"usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}})
    assert s.budget.snapshot().admission_charged_usd == .1
    with pytest.raises(BudgetBlocked, match="reserved_no_retry"):
        s.admit_native_invocation(invocation, bound, ttl_seconds=60)
    second = s.admit_native_invocation(str(uuid4()), bound, ttl_seconds=60)
    assert second.reservation.reservation_id != binding.reservation.reservation_id
    assert s.budget.snapshot().admission_charged_usd == .1


def test_native_admission_requires_operator_experiment_authorization(tmp_path):
    s, bound, _ = setup(tmp_path)
    # Remove the operator's "experiment" authorization from the host envelope.
    no_experiment = s.config.model_copy(update={"research_envelope": s.config.research_envelope.model_copy(
        update={"actions": tuple(a for a in s.config.research_envelope.actions if a != "experiment")})})
    unapproved = ResearchService(no_experiment, ledger=s.ledger)
    with pytest.raises(PermissionError, match="action_outside_research_envelope"):
        unapproved.admit_native_invocation(str(uuid4()), bound, ttl_seconds=60)


def test_native_admission_requires_execution_bound(tmp_path):
    s, bound, _ = setup(tmp_path)
    no_bound = s.config.model_copy(update={"research_execution_bound": None})
    with pytest.raises(ValueError, match="research_budget_requires_complete_host_binding"):
        ResearchService(no_bound, ledger=s.ledger)


def test_native_admission_cannot_reset_original_runtime_or_attempt_limits(tmp_path):
    s, bound, clock = setup(tmp_path)
    for _ in range(s.budget.policy.limits.max_attempts_per_task):
        binding = s.admit_native_invocation(str(uuid4()), bound, ttl_seconds=60)
        s.budget.settle(binding.reservation, {"usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}})
    with pytest.raises(BudgetBlocked, match="max_attempts_per_task"):
        s.admit_native_invocation(str(uuid4()), bound, ttl_seconds=60)
    clock[0] += s.ledger.limits.max_runtime_seconds
    with pytest.raises((BudgetBlocked, RunLimitReached), match="run_runtime_limit|expired"):
        s.admit_native_invocation(str(uuid4()), bound, ttl_seconds=60)
