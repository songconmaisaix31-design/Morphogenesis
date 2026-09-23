from __future__ import annotations

import json
import multiprocessing
import os
from pathlib import Path
import time

import pytest

from swarm.cli import demo_config, seed_demo
from swarm.worker_loop import ExecutionResult, FixtureExecutor, Worker, WorkerConfig
from swarm.models import ExecutionBound


def configured(tmp_path, **updates):
    target, state = seed_demo(tmp_path / "fixture")
    config = WorkerConfig.model_validate_json(demo_config(target, state, 0, 1.0))
    return config.model_copy(update=updates)


class UnknownUsage(FixtureExecutor):
    def execute(self, signal, attempt, repository, directory, **snapshot):
        return ExecutionResult(None, {"secret": "must-not-enter-audit"})


class KnownFailure(FixtureExecutor):
    def execute(self, signal, attempt, repository, directory, **snapshot):
        return ExecutionResult(None, {"usage": {"prompt_tokens": 1, "completion_tokens": 0, "total_tokens": 1}})


class Unbounded(FixtureExecutor):
    called = False
    def bound(self, signal):
        return ExecutionBound(provider="local", model="fixture", input_tokens=1,
                              max_output_tokens=1, provider_enforced=False)
    def execute(self, *args, **kwargs):
        self.called = True
        raise AssertionError("unbounded call reached")


def events(config):
    return [json.loads(path.read_bytes()) for path in (config.state / "audit").rglob("*.json")]


def test_unknown_usage_persists_account_stop_and_never_logs_raw_response(tmp_path):
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


def test_reservation_capacity_prevents_executor_call(tmp_path):
    config = configured(tmp_path)
    config = config.model_copy(update={"budget": config.budget.model_copy(update={"max_cost_usd": 0.000001})})
    worker = Worker(config)
    assert worker.run()["state"] == "sleeping"
    assert not (config.state / "execution").exists()
    assert events(config)[0]["outcome"] == "account_reservation_capacity"


def test_failed_execution_usage_is_settled_and_negative_feedback_written(tmp_path):
    config = configured(tmp_path, energy=1)
    worker = Worker(config, KnownFailure())
    assert worker.run()["state"] == "exhausted"
    snapshot = worker.budget.snapshot()
    assert snapshot.tokens == 1 and snapshot.pending_reservations == 0
    retired = [signal for signal in worker.field.snapshot() if signal.completed]
    assert len(retired) == 1 and retired[0].concentration < 1 and retired[0].decay_multiplier > 1
    assert events(config)[0]["outcome"] == "execution_failed"


def test_failed_validation_retains_quarantine_and_accounts_usage(tmp_path):
    import sys
    config = configured(tmp_path, energy=1, commands=((sys.executable, "-B", "-c", "raise SystemExit(1)"),))
    worker = Worker(config)
    worker.run()
    report = worker.assets.reports()[0]
    assert not report.passed and Path(report.worktree_path).exists()
    assert worker.assets.state(report.asset_id) == "quarantined"
    assert worker.budget.snapshot().tokens == 2
    assert events(config)[0]["outcome"] == "quarantined"
    assert not worker.assets.promotions()


def test_expired_scope_lease_blocks_promotion_and_success_audit(tmp_path):
    config = configured(tmp_path, energy=1)
    worker = Worker(config)
    signal = worker.field.sense(config.locality)[0]
    lease = worker.leases.acquire(str(config.target / signal.scope), worker.worker_id, ttl_seconds=0.01)
    assert lease is not None
    time.sleep(0.02)
    assert worker._process(signal, lease) == "failed"
    assert not worker.assets.promotions()
    assert events(config)[0]["outcome"] == "stale_lease"
    assert all("return -1" in path.read_text() for path in config.target.glob("task_*.py"))


def test_runtime_refuses_own_repository_and_state_before_mutation(tmp_path):
    from local_assets.models import AssetSafetyError
    config = configured(tmp_path)
    source = Path(__file__).resolve().parents[2]
    with pytest.raises(AssetSafetyError):
        Worker(config.model_copy(update={"target": source}))
    with pytest.raises(AssetSafetyError):
        Worker(config.model_copy(update={"state": source / "forbidden-runtime-state"}))
    assert not (source / "forbidden-runtime-state").exists()


def _crash_after_lease(directory, scope):
    from swarm.lease import LeaseManager
    lease = LeaseManager(directory).acquire(scope, "crashed-worker", ttl_seconds=0.1)
    (Path(directory) / "crashed.json").write_text(lease.model_dump_json(), encoding="utf-8")
    os._exit(7)


def test_process_crash_ttl_recovery_and_stale_holder_cannot_release(tmp_path):
    from swarm.lease import LeaseManager
    from swarm.models import Lease
    directory = tmp_path / "leases"
    scope = str(tmp_path / "target" / "module.py")
    process = multiprocessing.get_context("spawn").Process(target=_crash_after_lease, args=(directory, scope))
    process.start()
    process.join(60)
    assert process.exitcode == 7
    old = Lease.model_validate_json((directory / "crashed.json").read_bytes())
    time.sleep(0.15)
    manager = LeaseManager(directory)
    new = manager.acquire(scope, "successor")
    assert new is not None and new.token != old.token
    assert not manager.release(old) and manager.is_valid(new)
    assert manager.release(new)


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


def test_two_generations_same_file_preserve_head_index_and_unrelated_wip(tmp_path):
    from local_assets.paths import git
    from swarm.models import Signal
    config = configured(tmp_path, max_idle=1)
    config = config.model_copy(update={"locality": config.locality.model_copy(update={"radius": 0})})
    unrelated = config.target / "task_5.py"
    unrelated.write_bytes(unrelated.read_bytes() + b"# unrelated staged work\n")
    git(config.target, "add", "task_5.py")
    untracked = config.target / "untracked.txt"
    untracked.write_bytes(b"preserve me\n")
    head = git(config.target, "rev-parse", "HEAD")
    index = (config.target / ".git" / "index").read_bytes()
    unrelated_bytes = unrelated.read_bytes()
    first = Worker(config)
    assert first.run()["state"] == "idle"
    assert len(first.assets.promotions()) == 1
    path = config.target / "task_0.py"
    before = path.read_bytes().decode("utf-8")
    assert "return 0" in before
    after = before.replace("return 0", "return 10").replace("answer() == 0", "answer() == 10")
    first.field.deposit(Signal(task_id="generation-2", signal_id="generation-2",
                              workspace=str(config.target), scope="task_0.py", kind="opportunity",
                              required_capability="repair", payload={"changes": [{"path": "task_0.py",
                              "before": before, "after": after}]}))
    second = Worker(config)
    assert second.run()["state"] == "idle"
    assert path.read_bytes() == after.encode("utf-8")
    assert len(second.assets.promotions()) == 2
    assert len([event for event in events(config) if event["outcome"] == "promoted"]) == 2
    assert all(second.assets.fetch(event["asset_id"]).base_head == head.decode().strip()
               for event in events(config))
    assert git(config.target, "rev-parse", "HEAD") == head
    assert (config.target / ".git" / "index").read_bytes() == index
    assert unrelated.read_bytes() == unrelated_bytes and untracked.read_bytes() == b"preserve me\n"
