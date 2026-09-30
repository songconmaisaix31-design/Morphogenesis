"""Owner SIMULATED acceptance: real Worker, shared facts, budgets and fencing.

Only executor boundaries and the documented time-machine clock seam are used.
Assertions live outside Worker callbacks. Formal live acceptance is NOT_RUN.
"""
import json
from importlib.resources import files
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

import pytest
import time_machine
from jsonschema import Draft202012Validator

from orchestration.fc_logging import validate_event
from demo.fault_drill import (
    LABELS, executor, make_worker, peer_sequence, prepare, process, reservations, run_drill,
)
from swarm.models import BudgetPolicy, RunLimits


@pytest.fixture(scope="module")
def completed(tmp_path_factory):
    directory = tmp_path_factory.mktemp("completed-parent") / "drill"
    with time_machine.travel(1800000000.0, tick=False) as clock:
        result = run_drill(directory, wait=lambda deadline: clock.shift(deadline - time.time()))
    return directory, result


def test_stigmergy_avoidance(tmp_path):
    """B consumes A's actual shared fact; broken suspension changes real calls."""
    with time_machine.travel(1800000000.0, tick=False):
        config = prepare(tmp_path / "peer")
        worker_a, worker_b, stages = peer_sequence(config)
    fact = stages["rejection"]
    peer = stages["peer_avoidance"]
    assert worker_a.worker_id != worker_b.worker_id
    assert peer["calls"] == {"alpha": 0, "beta": 1}
    assert Path(peer["shared_store"]) == worker_a.fault_observation_store.path
    consumed = [record for read in peer["reads"] for record in read["records"]]
    assert any(all(record[key] == fact[key] for key in (
        "observation_id", "request_id", "task_id", "attempt", "evidence_ref")) for record in consumed)
    assert any(fact["append_sequence"] in read["record_lines"] for read in peer["reads"])
    assert peer["breaker_before"]["state"] == "insufficient_evidence"
    assert peer["breaker_after"]["state"] == "suspended"
    rows = [row for row in peer["reservations"] if row["task_id"] == peer["task_id"]]
    assert len(rows) == 1 and rows[0]["request_id"].endswith(":1")
    assert json.loads(rows[0]["body"])["bound"]["provider"] == "beta"
    assert rows[0]["worker_id"] == worker_b.worker_id
    assert peer["task"]["effect_applied"] and peer["task"]["result_id"]


def test_six_stages_preserve_unknown_holds_and_attempts(completed):
    directory, result = completed
    assert {key: result[key] for key in LABELS} == LABELS
    assert result["interface_live"] == result["task_live"] == "not_run"
    assert result["usage"] is result["cost_usd"] is None
    stages = result["stages"]
    assert list(stages) == ["normal", "rejection", "controlled_switch", "peer_avoidance",
                            "cooldown_probe", "recovery"]
    assert stages["normal"]["calls"] == {"alpha": 1, "beta": 0}
    switched = stages["controlled_switch"]
    assert switched["calls"] == {"alpha": 1, "beta": 1}
    chain = [row for row in switched["reservations"] if row["task_id"] == switched["task_id"]]
    assert len(chain) == 2
    assert [row["request_id"] for row in chain] == ["fixture-1:1:0", "fixture-1:1:1"]
    assert chain[0]["request_id"] == stages["rejection"]["request_id"]
    assert stages["rejection"]["attempt"] == 0
    assert stages["rejection"]["normalized_reason"] == "billing_arrearage"
    assert stages["rejection"]["cost_state"] == "unknown"
    rows = stages["recovery"]["reservations"]
    assert len(rows) == 5 and len({row["request_id"] for row in rows}) == 5
    assert all(row["status"] == "uncertain" and row["reserved_usd"] == 0.2 for row in rows)
    assert all(row["tokens"] is row["estimate_usd"] is row["admitted_usd"] is None for row in rows)
    assert stages["recovery"]["budget"]["reserved_estimate_usd"] == 1.0
    assert json.loads((directory / "result.json").read_text()) == result


def test_cooldown_probe_and_recovery_watermark(completed):
    _, result = completed
    stages = result["stages"]
    assert stages["cooldown_probe"]["before_cooldown_routable"] is False
    probe = stages["cooldown_probe"]["probe"]
    assert probe["state"] == "probing_recovery" and probe["probe_token"] == 1
    assert probe["probe_owner"] == stages["normal"]["worker_id"]
    assert probe["updated_at"] >= stages["peer_avoidance"]["breaker_after"]["cooldown_until"]
    assert probe["probe_expires_at"] > probe["updated_at"]
    recovery = stages["recovery"]
    assert recovery["calls"] == {"alpha": 1, "beta": 0}
    assert recovery["history_preserved"] is True
    assert set(recovery["observers"]) == {"same_worker", "other_worker", "restart"}
    for view in recovery["observers"].values():
        assert view["state"] == "normal" and view["recovered_at"] is not None
        assert view["recovery_sequence"] == stages["rejection"]["append_sequence"]
    assert {row["event"] for row in recovery["breaker_audit"]} >= {"aggregate", "probe_claimed", "probe_success"}


def test_all_unified_log_rows_match_frozen_schema_and_actual_facts(completed):
    directory, result = completed
    # Resource validity is separate from the SHA-scoped H3 equality evidence
    # archived in docs/tracks/fc-stable-drill-0930.md.
    schema = json.loads(files("orchestration").joinpath("fc_log_schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    path = Path(result["fc_log_path"])
    assert path == directory / "fc-logs/drill/mock/events.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert rows and len(rows) == result["fc_log_records"]
    assert result["writer_failure_count"] == 0
    for row in rows:
        validator.validate(row)
        validate_event(row)
        assert {key: row[key] for key in LABELS} == LABELS
        assert row["run_id"] == result["run_id"]
        assert row.get("audit_confirmed_issue_events") is row.get("issue_audit") is None
    fact, = [row["fault_observation"] for row in rows if row["event"] == "fault_observation"]
    expected = {key: value for key, value in result["stages"]["rejection"].items() if key != "append_sequence"}
    assert fact == expected
    claimed = [row for row in rows if row["event"] == "claim" and row["task_id"] == "fixture-2"]
    assert claimed
    peer = result["stages"]["peer_avoidance"]
    assert {row["claim"]["outcome"] for row in claimed} >= {"claimed", "submitted"}
    assert all(row["claim"]["worker_id"] == peer["worker_id"] and
               row["claim"]["token"] == peer["lease"]["token"] for row in claimed)
    assert not (directory / "fc-logs/live").exists()


def test_unknown_effect_default_policy_stops_without_releasing_hold(tmp_path):
    config = prepare(tmp_path / "unknown")
    config = config.model_copy(update={"budget": config.budget.model_copy(update={"allow_unknown_usage": False})})
    first = executor("alpha", reject_tasks=("fixture-0",), rejection_status=503)
    second = executor("beta")
    worker = make_worker(config, [first, second])
    outcome = process(worker, "fixture-0")
    assert outcome["outcome"] == "sleeping"
    assert len(first.calls) == 1 and len(second.calls) == 0
    row, = reservations(worker)
    assert row["status"] == "uncertain" and row["reserved_usd"] == 0.2
    assert row["tokens"] is None and row["cost"] == "unknown"
    assert worker.budget.snapshot().reason == "unknown_usage"
    fact, = worker.fault_observation_store.read().records
    assert fact.failure_class == "unknown_effect" and fact.switched_to is None
    assert fact.cost_state == "unknown" and fact.evidence_ref
    restarted = make_worker(config, [first, second])
    assert restarted.run()["state"] == "sleeping"
    assert len(first.calls) == 1 and len(second.calls) == 0
    assert reservations(restarted) == [row]


def test_all_suspended_exits_without_send_or_new_hold(tmp_path):
    with time_machine.travel(1800000000.0, tick=False):
        config = prepare(tmp_path / "blocked")
        worker_a, _, _ = peer_sequence(config)
        blocked = executor("alpha")
        contender = make_worker(config, [blocked], instance=2)
        before = reservations(worker_a)
        outcome = process(contender, "fixture-3")
    assert outcome["outcome"] == "sleeping"
    assert len(blocked.bound_calls) == 1 and len(blocked.calls) == 0
    assert reservations(contender) == before
    assert not outcome["task"]["effect_applied"] and outcome["task"]["result_id"] is None


def test_mock_policy_still_enforces_budget_capacity(tmp_path):
    config = prepare(tmp_path / "capacity")
    config = config.model_copy(update={"budget": config.budget.model_copy(update={"max_cost_usd": 0.2})})
    first, second = executor("alpha", reject_tasks=("fixture-0",)), executor("beta")
    worker = make_worker(config, [first, second])
    outcome = process(worker, "fixture-0")
    assert outcome["outcome"] == "sleeping"
    assert len(first.calls) == 1 and len(second.calls) == 0
    row, = reservations(worker)
    assert row["reserved_usd"] == 0.2 and row["status"] == "uncertain"
    assert worker.budget.snapshot().reserved_estimate_usd == 0.2


def test_mock_policy_still_enforces_attempt_limit(tmp_path):
    policy = BudgetPolicy(max_cost_usd=2.0, unbounded_reservation_usd=0.2,
                          allow_unknown_usage=True, limits=RunLimits(max_attempts=1))
    config = prepare(tmp_path / "attempts", policy=policy)
    first, second = executor("alpha", reject_tasks=("fixture-0",)), executor("beta")
    worker = make_worker(config, [first, second])
    outcome = process(worker, "fixture-0")
    assert outcome["outcome"] == "sleeping"
    assert len(first.calls) == 1 and len(second.calls) == 0
    row, = reservations(worker)
    assert row["status"] == "uncertain" and row["reserved_usd"] == 0.2
    assert row["request_id"] == "fixture-0:1:0"


def test_worker_calls_explicit_executor_and_persists_its_unbounded_contract(tmp_path):
    config = prepare(tmp_path / "contract")
    first = executor("alpha", reject_tasks=("fixture-0",))
    second = executor("beta")
    worker = make_worker(config, [first, second])
    result = process(worker, "fixture-0")
    assert result["outcome"] == "completed"
    assert len(first.calls) == len(second.calls) == 1
    rows = reservations(worker)
    assert len(rows) == 2
    for adapter, row in zip((first, second), rows, strict=True):
        call, = adapter.calls
        signal, = adapter.bound_calls
        assert call.signal == signal == worker.ledger.get("fixture-0").signal
        assert call.attempt.task_id == signal.task_id
        assert call.attempt.agent == config.agent and call.attempt.attempt == 0
        assert call.repository == config.target
        assert call.directory.is_relative_to(config.state / "execution")
        assert call.base_revision and call.base_head and call.experience is None
        bound = json.loads(row["body"])["bound"]
        assert (bound["provider"], bound["model"]) == (adapter.provider, "fixture")
        assert bound["request_bound"] == "unbounded" and bound["provider_enforced"] is False
        assert bound["max_cost_usd"] is bound["bound_evidence"] is None
        assert row["worker_id"] == worker.worker_id
        assert row["reserved_usd"] == 0.2 and row["tokens"] is None
    fact, = worker.fault_observation_store.read().records
    assert fact.failure_class == "confirmed_rejection" and fact.switched_to == "beta:fixture"
    assert fact.normalized_reason == "billing_arrearage" and fact.cost_state == "unknown"


@pytest.mark.parametrize("policy_update", [
    {"unbounded_reservation_usd": None}, {"max_tokens": 1},
])
def test_explicit_bound_cannot_bypass_real_budget_admission(tmp_path, policy_update):
    config = prepare(tmp_path / "no-admission")
    config = config.model_copy(update={"budget": config.budget.model_copy(update=policy_update)})
    first, second = executor("alpha"), executor("beta")
    worker = make_worker(config, [first, second])
    result = process(worker, "fixture-0")
    assert result["outcome"] == "sleeping"
    assert len(first.bound_calls) == 1 and second.bound_calls == []
    assert first.calls == second.calls == []
    assert reservations(worker) == []
    assert not result["task"]["effect_applied"] and result["task"]["result_id"] is None


def test_fixture_input_limit_survives_explicit_bound_before_reservation(tmp_path):
    config = prepare(tmp_path / "invalid-input")
    adapter = executor("alpha")
    worker = make_worker(config, [adapter])
    signal = worker.ledger.get("fixture-0").signal
    lease = worker.leases.acquire(signal.task_id, worker.worker_id, ttl_seconds=60,
                                  locality=config.locality)
    assert lease is not None
    invalid = signal.model_copy(update={"payload": {"changes": []}})
    assert worker._process(invalid, lease) == "failed"
    assert len(adapter.bound_calls) == 1 and adapter.calls == []
    assert reservations(worker) == []
    assert not worker.ledger.get(signal.task_id).effect_applied


def test_unknown_effect_stops_even_when_unknown_usage_is_allowed(tmp_path):
    config = prepare(tmp_path / "unknown-allowed")
    first = executor("alpha", reject_tasks=("fixture-0",), rejection_status=503)
    second = executor("beta")
    worker = make_worker(config, [first, second])
    result = process(worker, "fixture-0")
    assert result["outcome"] == "sleeping" and result["task"]["status"] == "blocked"
    assert len(first.calls) == 1 and second.calls == []
    row, = reservations(worker)
    assert row["status"] == "uncertain" and row["reserved_usd"] == 0.2
    assert row["tokens"] is row["estimate_usd"] is row["admitted_usd"] is None
    restarted = make_worker(config, [first, second], instance=1)
    assert restarted.leases.acquire("fixture-0", restarted.worker_id, ttl_seconds=60,
                                    locality=config.locality) is None
    assert reservations(restarted) == [row] and len(first.calls) == 1


def test_stale_token_is_fenced_before_executor_bound_and_admission(tmp_path):
    config = prepare(tmp_path / "stale-token")
    adapter = executor("alpha")
    worker = make_worker(config, [adapter])
    signal = worker.ledger.get("fixture-0").signal
    old = worker.leases.acquire(signal.task_id, worker.worker_id, ttl_seconds=60,
                                locality=config.locality)
    assert old is not None and worker.leases.release(old)
    current = worker.leases.acquire(signal.task_id, "peer", ttl_seconds=60,
                                    locality=config.locality)
    assert current is not None and current.token > old.token
    assert worker._process(signal, old) == "failed"
    assert adapter.bound_calls == adapter.calls == [] and reservations(worker) == []
    assert worker.leases.is_valid(current)
    record = worker.ledger.get(signal.task_id)
    assert record.owner == "peer" and record.token == current.token and not record.effect_applied


def test_expired_execution_lease_keeps_hold_and_cannot_apply_or_retry(tmp_path):
    with time_machine.travel(1800000000.0, tick=False) as clock:
        config = prepare(tmp_path / "expired-send")
        first = executor("alpha", before_execute=lambda: clock.shift(60.0))
        second = executor("beta")
        worker = make_worker(config, [first, second])
        before = (config.target / "module_0" / "task_0.py").read_bytes()
        result = process(worker, "fixture-0")
        assert result["outcome"] == "failed" and result["task"]["status"] != "completed"
        assert len(first.calls) == 1 and second.calls == []
        assert not result["task"]["effect_applied"] and result["task"]["result_id"] is None
        assert (config.target / "module_0" / "task_0.py").read_bytes() == before
        row, = reservations(worker)
        assert row["status"] == "uncertain" and row["reserved_usd"] == 0.2
        assert row["tokens"] is None and row["cost"] == "unknown"
        with sqlite3.connect(worker.ledger.path) as db:
            request_id, = db.execute("SELECT unconfirmed_request_id FROM tasks WHERE swarm_id=? AND task_id=?",
                                     (config.swarm_id, "fixture-0")).fetchone()
        assert request_id == row["request_id"]
        restarted = make_worker(config, [first, second], instance=1)
        assert restarted.leases.acquire("fixture-0", restarted.worker_id, ttl_seconds=60,
                                        locality=config.locality) is None
        assert len(first.calls) == 1 and reservations(restarted) == [row]


def test_cli_refuses_existing_directory_without_mutation(tmp_path):
    marker = tmp_path / "keep.txt"
    marker.write_text("preserve")
    result = subprocess.run([sys.executable, "-B", "-m", "demo.fault_drill", "--directory", str(tmp_path)],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode != 0
    assert "drill_directory_must_be_new" in result.stderr
    assert marker.read_text() == "preserve"
    assert not (tmp_path / "result.json").exists()
