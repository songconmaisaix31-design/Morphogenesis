"""Persisted advisory evidence must resolve to accepted, applicable source facts."""
import pytest

from swarm.research.policy import Branch, SupersessionEvent
from tests.integration.r1_security.test_c_feedback_boundaries import (
    accept, independent_review, scientific_fixture, store,
)


def opportunity(advisory, branch_id):
    return next(row for row in advisory["opportunities"]["opportunities"] if row["branch_id"] == branch_id)


@pytest.mark.parametrize("axis", ["supported_by", "refuted_by"])
def test_invented_advisory_reference_cannot_become_evidence(tmp_path, axis):
    s = store(tmp_path)
    branch = Branch(branch_id="source-branch", status="exploring", **{axis: ("invented-result",)})
    try:
        result = s.advisory([branch, Branch(branch_id="other", status="exploring")])
    except (ValueError, PermissionError):
        assert s.contributions() == []
        return
    row = opportunity(result, "source-branch")
    assert "invented-result" not in row[axis], "unresolved caller reference presented as trusted evidence"
    assert row["share"] == opportunity(result, "other")["share"]
    assert s.contributions() == []


def accepted_refutation(root):
    s, facts, locality = scientific_fixture(root, branch_id="source-branch")
    assert len(facts) == 1
    independent_review(s, root, locality)
    assert accept(s, facts[0]).accepted
    return s, facts[0]


def test_valid_persisted_refutation_changes_opportunity_with_original_result(tmp_path):
    s, fact = accepted_refutation(tmp_path)
    result = s.advisory([
        Branch(branch_id="source-branch", status="exploring", refuted_by=(fact.result_id,)),
        Branch(branch_id="other", status="exploring"),
    ])
    row = opportunity(result, "source-branch")
    assert row["refuted_by"] == [fact.result_id]
    assert row["factors"]["refute_count"] == 1
    assert 0 < row["share"] < opportunity(result, "other")["share"]
    assert len(s.contributions()) == 1
    assert s.contributions()[0].contribution == "accepted"


@pytest.mark.parametrize("attack", ["foreign_branch", "wrong_axis", "duplicate", "superseded"])
def test_real_result_cannot_be_relabelled_recounted_or_rewarded_after_supersession(tmp_path, attack):
    s, fact = accepted_refutation(tmp_path)
    original = s.contributions()
    branch_id = "other" if attack == "foreign_branch" else "source-branch"
    axis = "supported_by" if attack == "wrong_axis" else "refuted_by"
    refs = (fact.result_id, fact.result_id) if attack == "duplicate" else (fact.result_id,)
    if attack == "superseded":
        s.record_supersession(SupersessionEvent(event_id="correct", result_id=fact.result_id,
            reason="new bounded evidence", source_ref="fixture-correction", actor="nominated-reviewer", at=101))
    try:
        result = s.advisory([Branch(branch_id=branch_id, status="exploring", **{axis: refs})])
    except (ValueError, PermissionError):
        assert s.contributions() == original
        return
    row = opportunity(result, branch_id)
    if attack == "duplicate":
        assert row["refuted_by"] == [fact.result_id]
        assert row["factors"]["refute_count"] == 1, "one source result was counted more than once"
    else:
        assert fact.result_id not in row[axis], "result was used outside its axis/branch/effective lifetime"
    assert s.contributions() == original, "advice rewrote original accepted history"
