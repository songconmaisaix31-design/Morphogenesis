"""Offline policy behavior with the real ledger and preference store."""

import math
import random

import pytest

from swarm.models import Locality, RunLimits, Signal
from swarm.pheromone import PheromoneField
from swarm.router import Router
from swarm.task_ledger import TaskLedger


def setup(tmp_path):
    now = [100.0]
    ledger = TaskLedger(tmp_path / "tasks.db", "policy", clock=lambda: now[0],
                        limits=RunLimits(max_runtime_seconds=1e12))
    field = PheromoneField(tmp_path / "field.db", ledger=ledger, clock=lambda: now[0])
    locality = Locality(workspace=str(tmp_path), authorized_scopes=("allowed",))
    return ledger, field, locality, now


def deposit(field, root, task, capability, **kwargs):
    return field.deposit(Signal(task_id=task, workspace=str(root), scope=f"allowed/{task}",
                                kind="opportunity", required_capability=capability, **kwargs))


def test_recommendation_and_choose_share_seeded_policy_without_claim(tmp_path):
    ledger, field, locality, _ = setup(tmp_path)
    deposit(field, tmp_path, "a", "repair")
    deposit(field, tmp_path, "b", "research", payload={"problem": "offline second candidate"})
    first = Router(field, strategy_version="v0.1", rng=random.Random(17))
    second = Router(field, strategy_version="v0.1", rng=random.Random(17))
    matches = {"repair": 1.0, "research": 1.0}
    decision = first.recommend("worker", locality, matches)
    assert ledger.audit()[0]["sequence"] == decision["routing_sequence"]
    chosen = second.choose("worker", locality, matches)
    assert decision["strategy_version"] == "v0.1"
    assert decision["policy_version"] == "v0.1"
    assert decision["selected"] == chosen.task_id
    assert decision["probabilities"] == ledger.audit()[0]["body"]["probabilities"]
    assert decision["recommendation"]["task_id"] == chosen.task_id
    assert decision["query_limit"] == 100
    assert decision["window_order"] == ["created_at", "task_id"]
    assert [r.status for r in ledger.snapshot()] == ["available", "available"]
    assert [r.attempts for r in ledger.snapshot()] == [0, 0]


def test_success_failure_and_worker_identity_change_probabilities(tmp_path):
    _, field, locality, _ = setup(tmp_path)
    a = deposit(field, tmp_path, "a", "repair")
    deposit(field, tmp_path, "b", "research")
    router = Router(field, strategy_version="v0.1", beta=4)
    matches = {"repair": 1.0, "research": 1.0}
    before = router.recommend("worker", locality, matches)["probabilities"]
    history = router.reinforce("worker", a, success=True)
    after = router.recommend("worker", locality, matches)["probabilities"]
    assert history.weight == pytest.approx(.2625)
    assert after[0] > before[0] and after[1] < before[1]
    assert router.recommend("other", locality, matches)["probabilities"] == before
    router.reinforce("worker", a, success=False)
    failed = router.recommend("worker", locality, matches)["probabilities"]
    assert failed[0] < after[0] and failed[1] > after[1]


def test_operator_readonly_diagnostic_uses_shared_math_without_writing(tmp_path, monkeypatch):
    ledger, field, locality, _ = setup(tmp_path)
    deposit(field, tmp_path, "a", "repair")
    deposit(field, tmp_path, "b", "research")
    audit_before, records_before = ledger.audit(), ledger.snapshot()
    def forbidden_transaction():
        pytest.fail("read-only recommendation attempted a write transaction")
    with monkeypatch.context() as patch:
        patch.setattr(ledger, "transaction", forbidden_transaction)
        preview = Router(field, strategy_version="v0.1", rng=random.Random(17)).recommend(
            "worker", locality, {"repair": 1.0, "research": 1.0}, record_audit=False)
    assert preview["routing_sequence"] is None and preview["audited"] is False
    assert ledger.audit() == audit_before and ledger.snapshot() == records_before
    recorded = Router(field, strategy_version="v0.1", rng=random.Random(17)).recommend(
        "worker", locality, {"repair": 1.0, "research": 1.0})
    assert recorded["audited"] is True
    assert preview["selected"] == recorded["selected"]
    assert preview["probabilities"] == recorded["probabilities"]


@pytest.mark.parametrize("beta,concentration,urgency,match,elapsed", [
    (0, 0, 0, 1.0, 0),
    (1e6, 1e12, 1e6, 1.0, 0),
    (1e6, 0, 1e6, 1e-300, 1e9),
    (1, 1e12, 0, 1.0, 86400),
])
def test_extremes_remain_normalized_with_exploration_floor(
        tmp_path, beta, concentration, urgency, match, elapsed):
    _, field, locality, now = setup(tmp_path)
    deposit(field, tmp_path, "a", "repair", concentration=concentration, urgency=urgency)
    deposit(field, tmp_path, "b", "research", concentration=0, urgency=0)
    now[0] += elapsed
    decision = Router(field, strategy_version="v0.1", beta=beta).recommend(
        "worker", locality, {"repair": match, "research": 1.0})
    probabilities = decision["probabilities"]
    assert all(math.isfinite(p) and p >= .025 for p in probabilities)
    assert sum(probabilities) == pytest.approx(1)
    assert all(math.isfinite(s["score"]) and 0 <= s["score"] <= 44 * beta
               for s in decision["signals"])


def test_versioned_scale_retains_unit_scale_but_bounds_extreme_dominance(tmp_path):
    _, field, locality, _ = setup(tmp_path)
    deposit(field, tmp_path, "a", "repair", concentration=1e12, urgency=1e6)
    deposit(field, tmp_path, "b", "research")
    matches = {"repair": 1.0, "research": 1.0}
    old = Router(field).recommend("worker", locality, matches)
    new = Router(field, strategy_version="v0.1").recommend("worker", locality, matches)
    assert old["strategy_version"] == "v0"
    assert old["probabilities"][1] == pytest.approx(.025)
    assert new["probabilities"][1] > .30
    assert old["signals"][1]["score"] == new["signals"][1]["score"]


def test_scope_capability_dependency_and_unknown_effect_cannot_win(tmp_path):
    ledger, field, locality, now = setup(tmp_path)
    deposit(field, tmp_path, "legal", "repair")
    deposit(field, tmp_path, "incapable", "missing", concentration=1e12)
    field.deposit(Signal(task_id="outside", workspace=str(tmp_path), scope="private",
                         kind="opportunity", required_capability="repair", concentration=1e12))
    ledger.enqueue(Signal(task_id="dependent", workspace=str(tmp_path), scope="allowed/dependent",
                          kind="opportunity", required_capability="repair", concentration=1e12),
                   dependencies=("outside",))
    deposit(field, tmp_path, "unknown", "repair", concentration=1e12)
    lease = ledger.claim("unknown", "holder", locality=locality, ttl_seconds=1)
    ledger.begin_execution(lease, "unconfirmed-offline-request")
    now[0] += 2
    decision = Router(field, strategy_version="v0.1", beta=1e6).recommend(
        "worker", locality, {"repair": 1.0})
    assert [s["task_id"] for s in decision["signals"]] == ["legal"]
    assert decision["selected"] == "legal" and decision["probabilities"] == [1.0]
    assert ledger.get("unknown").status == "claimed"
    assert ledger.claim("unknown", "worker", locality=locality) is None


def test_window_excludes_late_high_score_even_from_exploration(tmp_path):
    ledger, field, locality, now = setup(tmp_path)
    for i in range(101):
        deposit(field, tmp_path, f"task-{i:03}", "repair", concentration=1e12 if i == 100 else 0)
        now[0] += 1
    decision = Router(field, strategy_version="v0.1", exploration=1).recommend(
        "worker", locality, {"repair": 1.0})
    assert len(decision["signals"]) == 100
    assert "task-100" not in {s["task_id"] for s in decision["signals"]}
    assert sum(decision["probabilities"]) == pytest.approx(1)
    assert ledger.get("task-100").attempts == 0


def test_empty_and_invalid_inputs_do_not_make_a_claim(tmp_path):
    ledger, field, locality, _ = setup(tmp_path)
    router = Router(field, strategy_version="v0.1")
    decision = router.recommend("worker", locality, {})
    assert decision["selected"] is None and decision["probabilities"] == []
    assert decision["recommendation"] is None
    for matches in ({"repair": float("nan")}, {"repair": True}, {"repair": -1.0}):
        with pytest.raises(ValueError):
            router.recommend("worker", locality, matches)
    for limit in (0, 101, True):
        with pytest.raises(ValueError):
            router.recommend("worker", locality, {}, limit=limit)
    with pytest.raises(ValueError):
        Router(field, strategy_version="unknown")
    assert ledger.snapshot() == []
