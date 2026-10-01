"""Offline policy behavior with the real ledger and preference store."""

import math
import random
import sqlite3
import json

import pytest

from orchestration.fc_logging import FCLogWriter, validate_event
from swarm.models import Locality, RunLimits, Signal
from swarm.pheromone import PheromoneField
from swarm.router import Router
from swarm.task_ledger import TaskLedger


def setup(tmp_path, **field_options):
    now = [100.0]
    ledger = TaskLedger(tmp_path / "tasks.db", "policy", clock=lambda: now[0],
                        limits=RunLimits(max_runtime_seconds=1e12))
    field = PheromoneField(tmp_path / "field.db", ledger=ledger, clock=lambda: now[0], **field_options)
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


@pytest.mark.parametrize("success", [False, True])
def test_expired_history_returns_to_prior_without_rewriting_old_rows(tmp_path, success):
    _, field, locality, now = setup(tmp_path)
    a = deposit(field, tmp_path, "a", "repair")
    deposit(field, tmp_path, "b", "research")
    router = Router(field, strategy_version="v0.1")
    router.reinforce("worker", a, success=success)
    with sqlite3.connect(field.path) as db:
        stored = db.execute("SELECT weight,samples,updated_at FROM pipe_history").fetchall()
    now[0] += 100 * field.tau_seconds
    decision = router.recommend("worker", locality, {"repair": 1.0, "research": 1.0})
    assert [s["w_history"] for s in decision["signals"]] == pytest.approx([.25, .25])
    assert decision["history_prior"] == .25
    # Explicit legacy view of the same stored row still tends to zero.
    old = Router(field).recommend("worker", locality, {"repair": 1.0, "research": 1.0})
    assert old["history_prior"] is None
    assert old["signals"][0]["w_history"] < 1e-40
    with sqlite3.connect(field.path) as db:
        assert db.execute("SELECT weight,samples,updated_at FROM pipe_history").fetchall() == stored
    # New feedback must read with the same prior used to score, not a zero-
    # centered history which would make a late success weaker than no history.
    late_success = router.reinforce("worker", a, success=True)
    assert late_success.weight == pytest.approx(.2625) and late_success.samples == 2


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


@pytest.mark.parametrize("success", [False, True])
def test_history_endpoints_and_tiny_aging_constant_keep_probability_finite(tmp_path, success):
    _, field, locality, now = setup(tmp_path, alpha=1.0)
    a = deposit(field, tmp_path, "a", "repair", concentration=1e12, urgency=1e6)
    deposit(field, tmp_path, "b", "research", concentration=0)
    router = Router(field, strategy_version="v0.1", beta=1e6, aging_seconds=1e-300)
    history = router.reinforce("worker", a, success=success, speedup=1.0, token_saving=1.0)
    assert history.weight == float(success)
    now[0] += 1
    decision = router.recommend("worker", locality, {"repair": 1.0, "research": 1.0})
    assert all(s["age_weight"] == 11 for s in decision["signals"])
    assert all(math.isfinite(p) and p >= .025 for p in decision["probabilities"])
    assert sum(decision["probabilities"]) == pytest.approx(1)


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


def test_suggestion_cannot_reserve_a_task_or_override_a_later_lease(tmp_path):
    ledger, field, locality, _ = setup(tmp_path)
    deposit(field, tmp_path, "a", "repair")
    deposit(field, tmp_path, "b", "research")
    decision = Router(field, strategy_version="v0.1", rng=random.Random(17)).recommend(
        "worker", locality, {"repair": 1.0, "research": 1.0})
    selected = decision["selected"]
    competing = ledger.claim(selected, "other", locality=locality)
    assert competing is not None
    assert ledger.claim(selected, "worker", locality=locality) is None
    next_decision = Router(field, strategy_version="v0.1").recommend(
        "worker", locality, {"repair": 1.0, "research": 1.0})
    assert next_decision["selected"] != selected
    assert ledger.is_valid(competing)


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


@pytest.mark.parametrize("version", ["v0", "v0.1"])
def test_real_routing_projection_retains_frozen_fc_schema(tmp_path, caplog, version):
    ledger, field, locality, _ = setup(tmp_path)
    deposit(field, tmp_path, "a", "repair")
    deposit(field, tmp_path, "b", "research")
    decision = Router(field, strategy_version=version, rng=random.Random(17)).recommend(
        "worker", locality, {"repair": 1.0, "research": 1.0})
    source = ledger.audit()[0]
    writer = FCLogWriter(tmp_path / "projection", ledger.swarm_id, provenance="mock")
    writer.observe_ledger(ledger, "worker")
    assert writer.path.exists(), caplog.text
    events = [validate_event(json.loads(line)) for line in writer.path.read_bytes().splitlines()]
    routing, = [event for event in events if event["event"] == "routing"]
    assert routing["sequence"] == decision["routing_sequence"]
    assert routing["routing"]["candidates"] == [dict(signal, probability=p) for signal, p in
        zip(source["body"]["signals"], source["body"]["probabilities"], strict=True)]
    assert source["body"]["policy_candidates"] == decision["signals"]
    assert "fc_log_projection_failed" not in caplog.text
