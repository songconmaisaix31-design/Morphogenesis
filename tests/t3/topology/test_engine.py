from typing import Any

import pytest
from pydantic import ValidationError

from contracts.identity import AgentId, AttemptId
from contracts.messages import Envelope, MsgType
from topology import Connection, TopologyEngine, TopologyPolicy


PLANNER = AgentId(role="planner", instance=0)
BUILDER_A = AgentId(role="builder", instance=0)
BUILDER_B = AgentId(role="builder", instance=1)
REVIEWER = AgentId(role="reviewer", instance=0)


def attempt(agent: AgentId, number: int = 0) -> AttemptId:
    return AttemptId(task_id="task-1", agent=agent, attempt=number)


def feedback(msg_id: str, target: AgentId, reporter: AgentId = REVIEWER) -> Envelope:
    return Envelope(
        run_id="run-1",
        msg_id=msg_id,
        msg_type=MsgType.RESULT,
        sender=reporter,
        receiver=PLANNER,
        task_id="task-1",
        attempt=attempt(target),
        seq=0,
        ts=1.0,
    )


def engine() -> TopologyEngine:
    return TopologyEngine(
        PLANNER,
        [
            Connection(src=PLANNER, dst=BUILDER_A, weight=1.0),
            Connection(src=PLANNER, dst=BUILDER_B, weight=0.9),
        ],
        TopologyPolicy(decay_lambda=0, reinforcement=1.0),
    )


def test_failure_updates_real_selection_and_attempt_duplicate_is_ignored() -> None:
    topology = engine()
    targets = [BUILDER_A, BUILDER_B]

    assert topology.select([REVIEWER]) is None
    assert topology.select(targets) == BUILDER_A
    topology.record(attempt(BUILDER_A), success=False)
    assert topology.select(targets) == BUILDER_B
    before_duplicate = topology.snapshot()

    topology.record(attempt(BUILDER_A), success=False)
    assert topology.snapshot() == before_duplicate


def test_success_feedback_changes_selection_and_deduplicates_msg_and_attempt() -> None:
    topology = engine()
    targets = [BUILDER_A, BUILDER_B]
    first = feedback("result-1", BUILDER_B)

    assert topology.select(targets) == BUILDER_A
    assert topology.record_feedback(
        first, True, route_source=PLANNER, route_target=BUILDER_B
    )
    assert topology.select(targets) == BUILDER_B
    after_first = topology.snapshot()

    assert not topology.record_feedback(
        first, True, route_source=PLANNER, route_target=BUILDER_B
    )
    assert not topology.record_feedback(
        feedback("result-2", BUILDER_B), True, route_source=PLANNER, route_target=BUILDER_B
    )
    assert topology.snapshot() == after_first


def test_feedback_reporter_is_not_conflated_with_routed_target() -> None:
    topology = engine()

    assert topology.record_feedback(
        feedback("review-1", BUILDER_A, reporter=REVIEWER),
        True,
        route_source=PLANNER,
        route_target=BUILDER_A,
    )
    with pytest.raises(ValueError, match="route_target"):
        topology.record_feedback(
            feedback("review-2", BUILDER_A),
            True,
            route_source=PLANNER,
            route_target=REVIEWER,
        )


def test_required_review_link_is_never_pruned_and_minimum_preserves_a_link() -> None:
    reviewer_link = Connection(src=PLANNER, dst=REVIEWER, weight=0.0, required=True)
    optional_link = Connection(src=PLANNER, dst=BUILDER_A, weight=0.0)
    topology = TopologyEngine(
        PLANNER,
        [reviewer_link, optional_link],
        TopologyPolicy(prune_threshold=0.1, low_activity_window=2, min_active_outgoing=1),
    )

    topology.advance_idle_window()
    topology.advance_idle_window()
    assert topology.prune() == [optional_link]
    active = {pipe.dst for pipe in topology.snapshot() if pipe.active}
    assert active == {REVIEWER}


def test_candidates_are_explicit_and_feedback_never_creates_a_connection() -> None:
    topology = engine()
    candidates = topology.candidate_connections([BUILDER_A, REVIEWER])

    assert candidates == [Connection(src=PLANNER, dst=REVIEWER, weight=0.1)]
    with pytest.raises(ValueError, match="no configured connection"):
        topology.record(attempt(REVIEWER), success=True)
    topology.add_connection(candidates[0])
    assert topology.select([REVIEWER]) == REVIEWER


@pytest.mark.parametrize(
    "kwargs",
    [
        {"decay_lambda": float("nan")},
        {"reinforcement": float("nan")},
        {"quality": -1.0},
        {"prune_threshold": -0.1},
    ],
)
def test_policy_rejects_nan_and_negative_parameters(kwargs: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        TopologyPolicy(**kwargs)


def test_connection_rejects_negative_weight_and_self_loop() -> None:
    with pytest.raises(ValidationError):
        Connection(src=PLANNER, dst=BUILDER_A, weight=-0.1)
    with pytest.raises(ValidationError, match="distinct"):
        Connection(src=PLANNER, dst=PLANNER)
