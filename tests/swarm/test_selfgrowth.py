"""Real process/file acceptance; executor usage remains explicitly fixture_mock."""

from __future__ import annotations

import importlib.abc
import json
import multiprocessing
import os
from pathlib import Path
import runpy
import socket
import sys
import time

from swarm.cli import demo_config, seed_demo


def _offline_worker(config_json, start, mode="normal"):
    # No central dispatcher can be imported. The existing gateway usage parser
    # remains reusable without executing its model adapter.
    class NoController(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path, target=None):
            if fullname in {"orchestration.runtime", "orchestration.rehearsal", "bootstrap.cli"}:
                raise AssertionError("controller disabled")
            return None
    sys.meta_path.insert(0, NoController())
    def deny(*args, **kwargs):
        raise AssertionError("network disabled in worker process")
    socket.socket.connect = deny
    socket.socket.connect_ex = deny
    socket.create_connection = deny
    socket.getaddrinfo = deny
    from swarm.worker_loop import ExecutionResult, FixtureExecutor, Worker, WorkerConfig
    from swarm.pheromone import PheromoneField
    from swarm.observer import observe
    # Any global view accidentally wired into runtime selection fails this test.
    PheromoneField.snapshot = deny
    import swarm.observer
    swarm.observer.observe = deny
    class HighUsage(FixtureExecutor):
        def execute(self, signal, attempt, repository, directory, **snapshot):
            return ExecutionResult(None, {"usage": {"prompt_tokens": 100000,
                                   "completion_tokens": 100000, "total_tokens": 200000}})
    config = WorkerConfig.model_validate_json(config_json)
    worker = Worker(config, HighUsage() if mode == "high" else None)
    start.wait(timeout=60)  # Start only: no signals/tasks/results cross this barrier.
    result = worker.run()
    (config.state / f"process-{config.agent.instance}.json").write_text(json.dumps({
        "pid": os.getpid(), "state": result["state"], "network": "blocked_python_socket",
        "controller": "blocked", "global_views": "blocked", "provenance": "mock"}), encoding="utf-8")


def _three_processes(target, state, *, mode="normal", cost=1.0):
    context = multiprocessing.get_context("spawn")
    start = context.Barrier(3)
    configs = [demo_config(target, state, i, cost) for i in range(3)]
    workers = [context.Process(target=_offline_worker, args=(config, start, mode)) for config in configs]
    try:
        for process in workers:
            process.start()
        deadline = time.monotonic() + 180
        for process in workers:
            process.join(timeout=max(0, deadline-time.monotonic()))
        assert [process.exitcode for process in workers] == [0, 0, 0]
    finally:
        for process in workers:
            if process.is_alive():
                process.terminate()
                process.join(5)
    return configs


def test_three_independent_workers_selfgrow_offline_and_restart(tmp_path: Path):
    target, state = seed_demo(tmp_path / "growth")
    configs = _three_processes(target, state)
    events = [json.loads(p.read_bytes()) for p in (state / "audit").rglob("*.json")]
    successes = [event for event in events if event["outcome"] == "promoted"]
    assert len(successes) == 6  # Six actual fixed functions exceeds the >=5 requirement.
    assert {event["worker_id"] for event in successes} == {"builder-0", "builder-1", "builder-2"}
    assert len({event["pid"] for event in successes}) == 3
    for event in successes:
        assert event["provenance"] == "mock" and event["usage_source"] == "fixture_mock"
        assert event["interface_live"] == event["task_live"] == "not_run"
        assert event["env_fingerprint"]["node_version"]
        assert event["env_fingerprint"]["arch"] and event["env_fingerprint"]["platform"]
        assert Path(event["execution_workspace"]).is_dir()
        assert Path(event["validation_workspace"]).is_dir()
        assert event["execution_workspace"] != event["validation_workspace"]
    for number in range(6):
        assert runpy.run_path(str(target / f"task_{number}.py"))["answer"]() == number
    from swarm.worker_loop import Worker, WorkerConfig
    from swarm.pheromone import PheromoneField
    from swarm.lease import LeaseManager
    from local_assets.store import LocalAssetStore
    field = PheromoneField(state / "field.sqlite3")
    assert all(signal.completed and signal.concentration > 1 for signal in field.snapshot())
    assert all(field.pipe_history(f"builder-{i}", "repair").samples == 2 for i in range(3))
    store = LocalAssetStore(state / "assets")
    assert len(store.promotions()) == len(store.reports()) == 6
    assert all(report.passed and report.commands[0].exit_code == 0 for report in store.reports())
    before = len(events)
    for config in configs:
        assert Worker(WorkerConfig.model_validate_json(config)).run()["state"] == "idle"
    assert len(list((state / "audit").rglob("*.json"))) == before
    assert LeaseManager(state / "leases").snapshot() == []


def test_fake_high_usage_breaker_sleeps_all_three_processes(tmp_path: Path):
    target, state = seed_demo(tmp_path / "breaker")
    _three_processes(target, state, mode="high", cost=0.001)
    statuses = [json.loads(p.read_bytes()) for p in (state / "workers").glob("*.json")]
    assert len(statuses) == 3 and all(row["state"] == "sleeping" for row in statuses)
    assert all(row["reason"] != "lease_metadata_busy" for row in statuses)
    assert all(row["provenance"] == "mock" for row in statuses)
    from swarm.budget import BudgetLedger
    from swarm.worker_loop import WorkerConfig
    config = WorkerConfig.model_validate_json(demo_config(target, state, 0, 0.001))
    ledger = BudgetLedger(state / "budget.sqlite3", config.account_id, config.budget)
    snapshot = ledger.snapshot()
    assert snapshot.sleeping and snapshot.actual_cost_usd is None
    assert snapshot.estimated_cost_usd >= 0.2
    audit = [json.loads(path.read_bytes()) for path in (state / "audit").rglob("*.json")]
    assert any(event["outcome"] == "budget_stopped" for event in audit)
    assert all("return -1" in p.read_text() for p in target.glob("task_*.py"))
