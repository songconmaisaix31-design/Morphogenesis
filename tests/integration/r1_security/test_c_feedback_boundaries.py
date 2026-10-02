"""Persisted research contributions require authoritative facts, not caller labels."""
import pytest

from swarm.research.feedback import ResearchFeedbackStore, research_feedback
from swarm.research.policy import Branch, CorrectionEvent, ResearchPolicy, ThreeAxisResult
from swarm.task_ledger import TaskLedger


def store(root):
    ledger = TaskLedger(root / "ledger.db", "q-security", clock=lambda: 100.0)
    return ResearchFeedbackStore(root / "feedback.db", ledger, clock=lambda: 100.0)


def forged(**updates):
    data = dict(result_id="invented", report_id="invented-report", task_id="missing-task",
                actor="attacker", source_ref="invented-source", provenance="live",
                execution="succeeded", hypothesis="supported", at=100)
    data.update(updates)
    return ThreeAxisResult(**data)


@pytest.mark.parametrize("hypothesis", ["supported", "refuted"])
def test_forged_result_and_reviewer_never_persist(tmp_path, hypothesis):
    s = store(tmp_path)
    try:
        decision = s.accept(forged(hypothesis=hypothesis), reviewer="invented-reviewer")
    except (ValueError, PermissionError, KeyError):
        pass
    else:
        assert not decision.accepted, "caller result/reviewer granted scientific contribution"
    assert s.contributions() == []


def test_synchronize_does_not_import_caller_accepted_label(tmp_path):
    s = store(tmp_path)
    try:
        s.synchronize([forged(contribution="accepted")])
    except (ValueError, PermissionError, KeyError):
        pass
    assert s.contributions() == []


@pytest.mark.parametrize("execution", ["unknown", "failed", "cancelled", "running", "not_run"])
def test_unknown_and_crash_do_not_reward(tmp_path, execution):
    s = store(tmp_path)
    try:
        decision = s.accept(forged(execution=execution), reviewer="reviewer")
    except (ValueError, PermissionError, KeyError):
        pass
    else:
        assert not decision.accepted
    assert s.contributions() == []


def test_empty_ledger_has_no_scientific_feedback(tmp_path):
    s = store(tmp_path)
    assert research_feedback(s.ledger, tmp_path / "no-assets") == []


def test_corrections_append_and_keep_prior_event(tmp_path):
    s = store(tmp_path)
    first = CorrectionEvent(event_id="sleep", branch_id="b", kind="sleep", reason="review",
                            source_ref="evidence", actor="reviewer", at=100)
    second = first.model_copy(update={"event_id": "reopen", "kind": "reopen", "at": 101})
    s.record_correction(first)
    s.record_correction(second)
    assert s.corrections("b") == [first, second]
    assert store(tmp_path).corrections("b") == [first, second]


def test_exploration_does_not_authorize_out_of_scope_branch():
    plan = ResearchPolicy().opportunities([Branch(branch_id="private", status="proposed", authorized=False)])
    assert plan.opportunities[0].share == 0
    assert not plan.opportunities[0].eligible
