from __future__ import annotations

import json
import multiprocessing
from pathlib import Path
import time

import pytest

from contracts.identity import AgentId
from local_assets.models import AssetSafetyError, FileExpectation, ValidationPolicy
from swarm.cli import demo_config, seed_demo
from swarm.models import ExecutionBound, Signal
from swarm.task_ledger import LeaseLost, TaskLedger
from swarm.worker_loop import ExecutionResult, FixtureExecutor, Worker, WorkerConfig


def configured(tmp_path, **updates):
    target, state = seed_demo(tmp_path / "fixture")
    config = WorkerConfig.model_validate_json(demo_config(target, state, 0, 1.0))
    return config.model_copy(update=updates)


def events(config):
    return [json.loads(path.read_bytes()) for path in (config.state / "audit").rglob("*.json")]


class UnknownUsage(FixtureExecutor):
    def execute(self, signal, attempt, repository, directory, **snapshot):
        return ExecutionResult(None, {"secret": "must-not-enter-audit"})


class KnownFailure(FixtureExecutor):
    def execute(self, signal, attempt, repository, directory, **snapshot):
        return ExecutionResult(None, {"usage": {"prompt_tokens": 1, "completion_tokens": 0, "total_tokens": 1}})


class WrongAnswer(FixtureExecutor):
    def execute(self, signal, attempt, repository, directory, **snapshot):
        changes = [{**change, "after": "def answer():\n    return 999\n"} for change in signal.payload["changes"]]
        bad = signal.model_copy(update={"payload": {"changes": changes}})
        return super().execute(bad, attempt, repository, directory, **snapshot)


class Unbounded(FixtureExecutor):
    called = False
    def bound(self, signal):
        return ExecutionBound(provider="local", model="fixture", input_tokens=1,
                              max_output_tokens=1, provider_enforced=False)
    def execute(self, *args, **kwargs):
        self.called = True
        raise AssertionError("unbounded call reached")


def test_unknown_usage_persists_swarm_stop_and_never_logs_raw_response(tmp_path):
    config = configured(tmp_path)
    worker = Worker(config, UnknownUsage())
    assert worker.run()["state"] == "sleeping"
    assert worker.budget.snapshot().estimated_cost_usd is None
    assert events(config)[0]["usage"] is None
    assert "must-not-enter-audit" not in json.dumps(events(config))
    assert Worker(config).run()["state"] == "sleeping"
    assert len(events(config)) == 1
    assert worker.leases.snapshot() == []


def test_bound_prevents_executor_call(tmp_path):
    config = configured(tmp_path)
    executor = Unbounded()
    worker = Worker(config, executor)
    assert worker.run()["state"] == "sleeping"
    assert executor.called is False
    assert worker.budget.snapshot().pending_reservations == 0
    assert events(config)[0]["outcome"] == "provider_bound_not_enforced"


@pytest.mark.parametrize("outside", [True, False])
def test_reuse_preimage_scope_and_size_denied_before_read(tmp_path, monkeypatch, outside):
    config = configured(tmp_path)
    worker = Worker(config)
    destination = "module_1/task_2.py" if outside else "module_0/oversize.txt"
    forbidden = config.target / destination
    if not outside:
        forbidden.write_bytes(b"x" * (256 * 1024 + 1))
    reads = []
    read = Path.read_bytes
    def spy(path):
        if path == forbidden:
            reads.append(path)
        return read(path)
    monkeypatch.setattr(Path, "read_bytes", spy)
    with pytest.raises(AssetSafetyError, match="reuse_destination_outside_scope|reuse_preimage_limit"):
        worker._preimages({"module_0/task_0.py": destination}, "module_0")
    assert reads == []


def test_reservation_capacity_prevents_executor_call(tmp_path):
    config = configured(tmp_path)
    config = config.model_copy(update={"budget": config.budget.model_copy(update={"max_cost_usd": 0.000001})})
    worker = Worker(config)
    assert worker.run()["state"] == "sleeping"
    assert not (config.state / "execution").exists()
    assert events(config)[0]["outcome"] == "swarm_reservation_capacity"


def test_restart_recovers_committed_hold_without_status_json(tmp_path):
    config = configured(tmp_path)
    interrupted = Worker(config)
    signal = interrupted.field.sense(config.locality)[0]
    interrupted.budget.reserve(interrupted.worker_id, signal.task_id,
                               FixtureExecutor().bound(signal), request_id="crash-before-status")
    assert not interrupted.status_path.exists()
    resumed = Worker(config, Unbounded())
    assert resumed.run()["state"] == "sleeping"
    snapshot = resumed.budget.snapshot()
    assert snapshot.reason == "unknown_usage" and snapshot.uncertain_reservations == 1
    assert snapshot.pending_reservations == 0
    assert events(config) == []
    assert not (config.state / "execution").exists()


def test_known_final_credit_finishes_effect_before_next_admission_stops(tmp_path):
    config = configured(tmp_path)
    config = config.model_copy(update={"budget": config.budget.model_copy(update={"max_cost_usd": 0.000002})})
    worker = Worker(config)
    result = worker.run()
    assert result["state"] == "sleeping" and result["completed"] == 1
    assert worker.budget.snapshot().reason == "swarm_cost_estimate_exhausted"
    audit = events(config)
    assert len(audit) == 1 and audit[0]["outcome"] == "promoted"
    task = worker.ledger.get(audit[0]["task_id"])
    assert task.status == "completed" and task.effect_applied
    assert len(worker.assets.promotions()) == 1
    assert worker.leases.snapshot() == []


def test_failed_execution_settles_usage_keeps_task_and_negative_feedback(tmp_path):
    config = configured(tmp_path, energy=1)
    worker = Worker(config, KnownFailure())
    assert worker.run()["state"] == "stopped"
    snapshot = worker.budget.snapshot()
    assert snapshot.tokens == 1 and snapshot.pending_reservations == 0
    failed = [signal for signal in worker.field.snapshot() if signal.decay_multiplier > 1]
    assert len(failed) == 1 and not failed[0].completed and failed[0].concentration < 1
    assert worker.ledger.get(failed[0].task_id).status == "available"
    assert events(config)[0]["outcome"] == "execution_failed"


def test_failed_validation_retains_quarantine_and_accounts_usage(tmp_path):
    config = configured(tmp_path, energy=1)
    worker = Worker(config, WrongAnswer())
    assert worker.run()["state"] == "stopped"
    report = worker.assets.reports()[0]
    assert not report.passed and Path(report.worktree_path).exists()
    assert worker.assets.state(report.asset_id) == "quarantined"
    assert worker.budget.snapshot().tokens == 2
    assert events(config)[0]["outcome"] == "quarantined"
    assert not worker.assets.promotions()
    assert worker.ledger.get(report.attempt.task_id).status == "available"
    assert all("return -1" in path.read_text() for path in config.target.rglob("task_*.py"))


def test_expired_scope_lease_blocks_promotion_and_success_audit(tmp_path):
    config = configured(tmp_path, energy=1)
    worker = Worker(config)
    signal = worker.field.sense(config.locality)[0]
    lease = worker.leases.acquire(signal.task_id, worker.worker_id, ttl_seconds=0.01, locality=config.locality)
    assert lease is not None
    time.sleep(0.02)
    assert worker._process(signal, lease) == "failed"
    assert not worker.assets.promotions()
    assert events(config)[0]["outcome"] == "stale_lease"
    assert worker.budget.snapshot().pending_reservations == 0
    assert all("return -1" in path.read_text() for path in config.target.rglob("task_*.py"))


def test_runtime_refuses_own_repository_and_state_before_mutation(tmp_path):
    config = configured(tmp_path)
    source = Path(__file__).resolve().parents[2]
    with pytest.raises(AssetSafetyError):
        Worker(config.model_copy(update={"target": source}))
    with pytest.raises(AssetSafetyError):
        Worker(config.model_copy(update={"state": source / "forbidden-runtime-state"}))
    assert not (source / "forbidden-runtime-state").exists()


def _hold_running_worker(config_json):
    config = WorkerConfig.model_validate_json(config_json)
    class PauseBeforeReservation(FixtureExecutor):
        def bound(self, signal):
            (config.state / "held-task.json").write_text(json.dumps({"task_id": signal.task_id}), encoding="utf-8")
            time.sleep(90)
            return super().bound(signal)
    Worker(config, PauseBeforeReservation()).run()


def test_killed_actual_worker_ttl_successor_completes_and_old_submit_is_rejected(tmp_path):
    config = configured(tmp_path, lease_seconds=0.3)
    process = multiprocessing.get_context("spawn").Process(target=_hold_running_worker, args=(config.model_dump_json(),))
    process.start()
    marker = config.state / "held-task.json"
    try:
        deadline = time.monotonic() + 40
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert marker.exists() and process.is_alive()
        process.terminate()
        process.join(10)
        assert not process.is_alive()
        ledger = TaskLedger(config.state / "tasks.sqlite3", config.swarm_id)
        old = ledger.leases()[0]
        assert old.token == 1
        time.sleep(max(0, old.expires_at - time.time()) + 0.1)
        successor = Worker(config.model_copy(update={"agent": AgentId(role="builder", instance=8), "lease_seconds": 30}))
        assert successor.run()["state"] == "idle"
        task = ledger.get(old.task_id)
        assert task.status == "completed" and task.token == 2 and task.effect_applied
        writes = []
        with pytest.raises(LeaseLost):
            ledger.submit(old, "late-result", {"applied": True}, apply=lambda check: writes.append("forbidden"))
        assert writes == [] and not ledger.release(old)
        assert len(successor.assets.promotions()) == 2
    finally:
        if process.is_alive():
            process.terminate()
            process.join(10)


def test_resuming_interrupted_execution_preserves_hold_and_sleeps(tmp_path):
    config = configured(tmp_path)
    worker = Worker(config)
    signal = worker.field.sense(config.locality)[0]
    reservation = worker.budget.reserve(worker.worker_id, signal.task_id, FixtureExecutor().bound(signal))
    worker._active = reservation
    worker._status("executing")
    resumed = Worker(config)
    assert resumed.run()["state"] == "sleeping"
    assert resumed.budget.snapshot().uncertain_reservations == 1
    assert not (config.state / "execution").exists()


def enqueue(worker, *, task_id, scope, path, before, after, payload=None, dependencies=()):
    policy = ValidationPolicy(version="fixture-files-v1", expectations=(FileExpectation(path=path, content=after),))
    signal = Signal(task_id=task_id, signal_id=task_id, workspace=str(worker.target), scope=scope,
                    module=scope, kind="opportunity", required_capability="repair",
                    payload=payload or {"changes": [{"path": path, "before": before, "after": after}]})
    worker.ledger.enqueue(signal, dependencies=dependencies, acceptance={"validation_policy": policy.model_dump(mode="json")})
    worker.field.deposit(signal)
    return signal


def test_two_generations_preserve_head_index_and_unrelated_wip(tmp_path):
    from local_assets.paths import git
    config = configured(tmp_path, max_idle=1)
    unrelated = config.target / "module_2/task_5.py"
    unrelated.write_bytes(unrelated.read_bytes() + b"# unrelated staged work\n")
    git(config.target, "add", "module_2/task_5.py")
    untracked = config.target / "untracked.txt"
    untracked.write_bytes(b"preserve me\n")
    head = git(config.target, "rev-parse", "HEAD")
    index = (config.target / ".git/index").read_bytes()
    unrelated_bytes = unrelated.read_bytes()
    first = Worker(config)
    assert first.run()["state"] == "idle"
    path = config.target / "module_0/task_0.py"
    before = path.read_bytes().decode("utf-8")
    after = before.replace("return 0", "return 10")
    enqueue(first, task_id="generation-2", scope="module_0", path="module_0/task_0.py", before=before, after=after)
    second = Worker(config)
    assert second.run()["state"] == "idle"
    assert path.read_bytes() == after.encode("utf-8")
    assert len(second.assets.promotions()) == 3
    assert git(config.target, "rev-parse", "HEAD") == head
    assert (config.target / ".git/index").read_bytes() == index
    assert unrelated.read_bytes() == unrelated_bytes and untracked.read_bytes() == b"preserve me\n"


def test_renewal_keeps_slow_local_execution_owned(tmp_path):
    class Slow(FixtureExecutor):
        def execute(self, *args, **kwargs):
            time.sleep(0.6)
            return super().execute(*args, **kwargs)
    config = configured(tmp_path, energy=1, lease_seconds=0.25)
    worker = Worker(config, Slow())
    assert worker.run()["state"] == "exhausted"
    assert len(worker.assets.promotions()) == 1
    assert worker.leases.snapshot() == []


def test_restart_completed_before_approval_does_not_reexecute(tmp_path, monkeypatch):
    config = configured(tmp_path, energy=1)
    worker = Worker(config)
    original = worker._finalize
    def interruption():
        raise RuntimeError("simulated process loss after completed submit")
    monkeypatch.setattr(worker, "_finalize", interruption)
    assert worker.run()["state"] == "stopped"
    pending = worker._pending
    assert pending and worker.assets.state(pending["asset_id"]) == "quarantined"
    completed = worker.ledger.get(pending["lease"]["task_id"])
    assert completed.status == "completed" and completed.effect_applied
    resumed = Worker(config, Unbounded())
    assert resumed.run()["state"] == "exhausted"
    assert len(resumed.assets.promotions()) == 1
    assert resumed.budget.snapshot().tokens == 2
    assert resumed.ledger.get(completed.signal.task_id).attempts == 1
    assert not resumed.executor.called


def test_interrupted_feedback_is_visible_and_never_reinforced_twice(tmp_path, monkeypatch):
    config = configured(tmp_path, energy=1)
    worker = Worker(config)
    def interrupt(*args, **kwargs):
        raise RuntimeError("after positive field deposition")
    monkeypatch.setattr(worker.router, "reinforce", interrupt)
    assert worker.run()["state"] == "stopped"
    assert worker._pending["feedback_started"] and not worker._pending["feedback_complete"]
    values = {s.signal_id: s.concentration for s in worker.field.snapshot()}
    resumed = Worker(config)
    assert resumed.run()["state"] == "needs_review"
    assert resumed._pending is not None
    assert all(s.concentration <= values[s.signal_id] for s in resumed.field.snapshot())
    assert len(resumed.assets.promotions()) == 1 and resumed.budget.snapshot().tokens == 2


def test_approval_gap_waits_without_claim_or_reservation(tmp_path, monkeypatch):
    config = configured(tmp_path, energy=1, max_idle=1)
    producer = Worker(config)
    monkeypatch.setattr(producer, "_finalize", lambda: (_ for _ in ()).throw(RuntimeError("approval gap")))
    producer.run()
    source = producer.ledger.get(producer._pending["lease"]["task_id"])
    expected = producer.assets.fetch(source.result["candidate_asset_id"]).changes[0].after
    signal = enqueue(producer, task_id="reuse-gap", scope="module_0", path="module_0/copy.py",
                     before=None, after=expected, dependencies=(source.signal.task_id,),
                     payload={"reuse_task_id": source.signal.task_id,
                              "path_map": {source.signal.payload["changes"][0]["path"]: "module_0/copy.py"}})
    from swarm.models import Locality
    consumer_config = config.model_copy(update={"agent": AgentId(role="builder", instance=9),
        "locality": Locality(workspace=str(config.target), authorized_scopes=("module_0",),
                             dependency_of=(signal.task_id,))})
    consumer = Worker(consumer_config)
    before = consumer.budget.snapshot().tokens
    assert consumer.run()["state"] == "waiting"
    assert consumer.ledger.get(signal.task_id).attempts == 0
    assert consumer.budget.snapshot().tokens == before
