"""Formal research-v1 mutation and advice retain HostConfig authority."""
import pytest

from tests.integration.r1_security.test_a_host_boundaries import seeded, service


def opportunities(snapshot):
    return {row["branch_id"]: row for row in snapshot["opportunities"]["opportunities"]}


def test_foreign_branch_correction_cannot_mutate_feedback_history(tmp_path):
    s = seeded(tmp_path)
    before = s.feedback_store.corrections()
    with pytest.raises((ValueError, PermissionError, KeyError)):
        s.record_correction("foreign", "sleep", "caller request", "unverified-opinion")
    assert s.feedback_store.corrections() == before


def test_unresolved_result_supersession_cannot_create_authority(tmp_path):
    s = seeded(tmp_path)
    before = s.feedback_store.supersessions()
    with pytest.raises((ValueError, PermissionError, KeyError)):
        s.record_supersession("missing-result", "caller request", "unverified-opinion")
    assert s.feedback_store.supersessions() == before


@pytest.mark.parametrize("method", ["research_snapshot", "research_advisory"])
def test_research_feedback_projection_cannot_read_foreign_project(tmp_path, method):
    s = seeded(tmp_path)
    with pytest.raises((ValueError, PermissionError)):
        getattr(s, method)("p2")


def test_legal_sleep_and_reopen_change_future_advice_without_deleting_history(tmp_path):
    s = seeded(tmp_path)
    s.create_branch("p1", "local", "legal local work", "bounded research")
    before = opportunities(s.research_advisory("p1"))["local"]
    assert before["eligible"] and before["share"] > 0
    s.record_correction("local", "sleep", "bounded pause", "fixture-note")
    slept = opportunities(s.research_advisory("p1"))["local"]
    assert not slept["eligible"] and slept["share"] == 0, "persisted sleep failed to stop future opportunity"
    s = service(tmp_path)
    reopened_snapshot = opportunities(s.research_snapshot("p1"))["local"]
    assert not reopened_snapshot["eligible"] and reopened_snapshot["share"] == 0
    s.record_correction("local", "reopen", "conditions reviewed", "fixture-followup")
    after = opportunities(s.research_advisory("p1"))["local"]
    assert after["eligible"] and after["share"] > 0
    assert [event.kind for event in s.feedback_store.corrections("local")] == ["sleep", "reopen"]
    assert s.ledger.snapshot() == [], "a lifecycle correction created or claimed execution work"
