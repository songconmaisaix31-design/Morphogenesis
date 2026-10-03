"""FR-12/13, AT-10 through the original service, ledger and generated archives.

Only the existing inert mock executor is used; candidate processes and network
are denied by the shared service fixture. No policy result or acceptance is mocked.
"""
from __future__ import annotations

import json
import asyncio

import pytest

from swarm.budget import BudgetBlocked
from swarm.research.policy import Branch, ResearchPolicy
from swarm.task_ledger import connection
from tests.research.test_dynamic_service import (
    execute_observe, member, no_candidate_process_or_network, prepare, setup,
)
from tests.research.test_research_policy_generated import GeneratedFixture


def reviewed_result(tmp_path, *, refuted=False):
    author, plan = setup(tmp_path, refuted=refuted)
    task, token, prepared = prepare(author, plan)
    asset = prepared["asset_id"]
    run, _ = execute_observe(author, task, token, asset, "original")
    original = author.complete_research(task, token, asset, run)
    reviewer = member(author.config, "reviewer", 2)
    review_task, review_token, _ = prepare(
        reviewer, plan, purpose="reproduction", asset_id=asset, dependencies=(task,))
    review_run, _ = execute_observe(reviewer, review_task, review_token, asset, "reproduction")
    review = reviewer.complete_research(review_task, review_token, asset, review_run)
    return author, reviewer, plan, original["result_id"], review["result_id"]


def opportunities(service):
    return {op["branch_id"]: op for op in service.research_advisory()["opportunities"]["opportunities"]}


def test_accepted_support_changes_discover_choose_claim_and_preserves_envelope(tmp_path):
    author, reviewer, plan, result_id, _ = reviewed_result(tmp_path)
    reviewer.create_branch(plan.project_id, "third", "third route", "legal exploration")
    followups = {}
    for branch in ("alternative", "third", plan.branch_id):
        followups[branch] = reviewer.propose_work(
            plan.project_id, "question", "next " + branch, "test the next implication",
            "new evidence", branch_id=branch)["task_id"]
    # All three branches start equal. Source and independent review exist, but
    # neither an unaccepted result nor the author's approval earns preference.
    before = opportunities(reviewer)
    assert all(op["share"] == pytest.approx(1 / 3) for op in before.values())
    assert all(op["supported_by"] == [] for op in before.values())
    assert not author.accept_result(result_id)["accepted"]
    assert opportunities(reviewer) == before
    before_order = [row["signal"]["task_id"] for row in reviewer.discover()]
    assert before_order == list(followups.values())
    reviewer.router.rng.seed(4)
    before_choice = reviewer.choose(reason="same seeded draw before accepted evidence")
    assert before_choice["selected"] == followups["alternative"]
    budget_before = reviewer.budget.snapshot()
    policy_before = reviewer.budget.policy
    envelope_before = reviewer.config.research_envelope

    assert reviewer.accept_result(result_id)["accepted"]
    after = opportunities(reviewer)
    supported = after[plan.branch_id]
    assert supported["share"] > before[plan.branch_id]["share"]
    assert supported["share"] == pytest.approx(.8 * (2 / 3) / (2 / 3 + .5 + .5) + .2 / 3)
    assert before[plan.branch_id]["factors"]["evidence"] == .5
    assert supported["factors"]["evidence"] == pytest.approx(2 / 3)
    assert supported["factors"]["support_count"] == 1
    assert supported["supported_by"] == [result_id]
    assert sum(op["share"] for op in after.values()) == pytest.approx(1)
    assert all(op["share"] >= .2 / 3 for op in after.values())
    discovered = reviewer.discover()
    assert discovered[0]["signal"]["task_id"] == followups[plan.branch_id]
    assert discovered[0]["research_opportunity"] == supported
    reviewer.router.rng.seed(4)
    after_choice = reviewer.choose(reason="same seeded draw after accepted evidence")
    assert after_choice["selected"] == followups[plan.branch_id]
    assert not after_choice["overridden"]
    lease = reviewer.claim(after_choice["selected"], ttl_seconds=300)
    selection = lease["research_selection"]
    assert selection["choice"] == after_choice
    assert selection["opportunity"] == supported
    assert selection["result_references"] == [result_id]
    assert selection["claim_authority"] == "TaskLedger"
    assert selection["token"] == lease["token"]
    assert reviewer.ledger.get(after_choice["selected"]).owner == "reviewer"
    with connection(reviewer.ledger.path) as db:
        rows = db.execute("SELECT event,body FROM task_audit WHERE task_id=? AND "
                          "event IN ('research_choice','research_selection') ORDER BY sequence",
                          (after_choice["selected"],)).fetchall()
    assert [(row["event"], json.loads(row["body"])) for row in rows] == [
        ("research_choice", after_choice), ("research_selection", selection)]
    assert reviewer.config.research_envelope == envelope_before
    assert reviewer.budget.policy == policy_before
    assert reviewer.budget.snapshot() == budget_before
    assert reviewer.budget.snapshot().tokens is None
    assert reviewer.budget.snapshot().actual_cost_usd is None
    # Repeated approval cannot inflate the fixed opportunity pool.
    assert reviewer.accept_result(result_id)["reasons"] == ["duplicate_contribution"]
    assert opportunities(reviewer) == after
    assert len(reviewer.feedback_store.contributions()) == 1
    assert not reviewer.store.adoptions()


def test_accepted_refutation_reduces_route_but_preserves_positive_contribution(tmp_path):
    _, reviewer, plan, result_id, _ = reviewed_result(tmp_path, refuted=True)
    before = opportunities(reviewer)
    assert reviewer.accept_result(result_id)["accepted"]
    after = opportunities(reviewer)
    assert after[plan.branch_id]["share"] < before[plan.branch_id]["share"]
    assert after[plan.branch_id]["factors"]["evidence"] == pytest.approx(1 / 3)
    assert after[plan.branch_id]["refuted_by"] == [result_id]
    contribution = reviewer.research_advisory()["contributions"][0]
    assert (contribution["execution"], contribution["hypothesis"], contribution["contribution"]) == (
        "succeeded", "refuted", "accepted")
    assert sum(op["share"] for op in after.values()) == pytest.approx(1)


def test_same_raw_source_under_new_task_cannot_inflate_opportunities(tmp_path):
    fixture = GeneratedFixture(tmp_path)
    fixture.run("source")
    fixture.run("review", source="source")
    fixture.run("copy", branch_id="source-branch")
    fixture.run("copy-review", source="copy", branch_id="source-branch")
    branches = [Branch(branch_id="source-branch", status="exploring"),
                Branch(branch_id="alternative", status="exploring")]
    before = fixture.feedback.advisory(branches)
    assert fixture.feedback.accept("source-result").accepted
    after = fixture.feedback.advisory(branches)
    assert after["opportunities"]["opportunities"][0]["share"] > before["opportunities"]["opportunities"][0]["share"]
    assert fixture.feedback.accept("copy-result").reasons == ("duplicate_contribution",)
    assert fixture.feedback.accept("source-result").reasons == ("duplicate_contribution",)
    assert fixture.feedback.advisory(branches) == after
    assert len(fixture.feedback.contributions()) == 1


@pytest.mark.parametrize("restriction", [
    {"conditions": {"different": "condition"}}, {"authorized": False}, {"applicability": 0},
])
def test_trusted_support_does_not_reward_other_conditions_or_unauthorized_branch(tmp_path, restriction):
    fixture = GeneratedFixture(tmp_path)
    fixture.run("source")
    fixture.run("review", source="source")
    restricted = Branch(branch_id="source-branch", status="exploring", **restriction)
    branches = [restricted, Branch(branch_id="alternative", status="exploring")]
    before = fixture.feedback.advisory(branches)
    assert fixture.feedback.accept("source-result").accepted
    after = fixture.feedback.advisory(branches)
    old, new = before["opportunities"]["opportunities"][0], after["opportunities"]["opportunities"][0]
    assert new["share"] == old["share"]
    if restricted.conditions:
        assert new["supported_by"] == []
    else:
        assert not new["eligible"] and new["share"] == 0


def test_inapplicable_route_has_no_exploration_or_evidence_reward():
    for references in ((), ("already-accepted",)):
        plan = ResearchPolicy().opportunities([
            Branch(branch_id="inapplicable", status="exploring", applicability=0, supported_by=references),
            Branch(branch_id="legal", status="exploring")])
        excluded, legal = plan.opportunities
        assert not excluded.eligible and excluded.share == 0
        assert "inapplicable" in excluded.reasons
        assert legal.share == plan.total_share == 1


def test_host_without_review_authority_cannot_change_opportunities(tmp_path):
    _, reviewer, _, result_id, _ = reviewed_result(tmp_path)
    before = opportunities(reviewer)
    envelope = reviewer.config.research_envelope.model_copy(update={
        "actions": tuple(action for action in reviewer.config.research_envelope.actions if action != "review")})
    restricted = member(reviewer.config.model_copy(update={"research_envelope": envelope}))
    with pytest.raises(PermissionError):
        restricted.accept_result(result_id)
    assert opportunities(reviewer) == before
    assert reviewer.feedback_store.contributions() == []


@pytest.mark.parametrize("outcome", ["failed", "timeout", "unknown"])
def test_failed_timeout_unknown_execution_never_rewards_scientific_route(tmp_path, outcome):
    author, plan = setup(tmp_path, outcome=outcome)
    task, token, _ = prepare(author, plan)
    before = opportunities(author)
    execution = asyncio.run(author.execute(task, token))
    assert execution["result"]["scientific_verdict"] == "not_evaluated"
    assert execution["result"]["generated_assessment"]["hypothesis"] != "refuted"
    reviewer = member(author.config, "reviewer", 2)
    assert not reviewer.accept_result("untrusted-execution-result")["accepted"]
    assert opportunities(reviewer) == before
    assert reviewer.research_advisory()["contributions"] == []
    if outcome == "unknown":
        with pytest.raises(BudgetBlocked):
            asyncio.run(author.execute(task, token))
