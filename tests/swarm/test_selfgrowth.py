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
        assert runpy.run_path(str(target / f"module_{number // 2}/task_{number}.py"))["answer"]() == number
    from swarm.worker_loop import Worker, WorkerConfig
    from swarm.pheromone import PheromoneField
    from swarm.lease import LeaseManager
    from swarm.task_ledger import TaskLedger
    from local_assets.store import LocalAssetStore
    ledger = TaskLedger(state / "tasks.sqlite3", "local-fixture")
    field = PheromoneField(state / "field.sqlite3", ledger=ledger)
    assert all(signal.completed and signal.concentration > 1 for signal in field.snapshot())
    assert all(field.pipe_history(f"builder-{i}", "repair").samples == 2 for i in range(3))
    store = LocalAssetStore(state / "assets")
    assert len(store.promotions()) == len(store.reports()) == 6
    assert all(report.passed and report.commands[0].exit_code == 0 for report in store.reports())
    before = len(events)
    for config in configs:
        assert Worker(WorkerConfig.model_validate_json(config)).run()["state"] == "idle"
    assert len(list((state / "audit").rglob("*.json"))) == before
    assert LeaseManager(ledger).snapshot() == []
    assert all(task.status == "completed" and task.effect_applied for task in ledger.snapshot())
    assert all(report.isolation == "non_arbitrary_literal_files" for report in store.reports())


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
    ledger = BudgetLedger(state / "budget.sqlite3", config.swarm_id, config.budget)
    snapshot = ledger.snapshot()
    assert snapshot.sleeping and snapshot.actual_cost_usd is None
    assert snapshot.estimated_cost_usd >= 0.2
    audit = [json.loads(path.read_bytes()) for path in (state / "audit").rglob("*.json")]
    assert any(event["outcome"] == "budget_stopped" for event in audit)
    assert all("return -1" in p.read_text() for p in target.rglob("task_*.py"))


def _one_process(config_json):
    context = multiprocessing.get_context("spawn")
    start = context.Barrier(1)  # Keep the POSIX semaphore alive until child join.
    process = context.Process(target=_offline_worker, args=(config_json, start))
    process.start()
    try:
        process.join(120)
        assert process.exitcode == 0
    finally:
        if process.is_alive():
            process.terminate()
            process.join(10)


def test_approved_content_adopted_by_different_worker_in_new_process(tmp_path):
    from contracts.identity import AgentId
    from local_assets.models import FileExpectation, ValidationPolicy
    from local_assets.store import LocalAssetStore
    from swarm.models import Signal
    from swarm.task_ledger import TaskLedger
    from swarm.pheromone import PheromoneField
    from swarm.worker_loop import WorkerConfig
    target, state = seed_demo(tmp_path / "reuse")
    first_json = demo_config(target, state, 0, 1.0)
    _one_process(first_json)
    ledger = TaskLedger(state / "tasks.sqlite3", "local-fixture")
    source = ledger.get("fixture-0")
    store = LocalAssetStore(state / "assets")
    source_id = source.result["candidate_asset_id"]
    original = store.fetch_approved(source_id)
    destination = "module_0/reused.py"
    after = original.changes[0].after
    policy = ValidationPolicy(version="fixture-files-v1", expectations=(FileExpectation(path=destination, content=after),))
    signal = Signal(task_id="reuse-next-session", signal_id="reuse-next-session", workspace=str(target),
                    scope="module_0", module="module_0", kind="opportunity", required_capability="repair",
                    payload={"reuse_task_id": "fixture-0", "path_map": {original.changes[0].path: destination}})
    # Environment seeding describes dependency and scope; it assigns no worker.
    ledger.enqueue(signal, dependencies=("fixture-0",), acceptance={"validation_policy": policy.model_dump(mode="json")})
    PheromoneField(state / "field.sqlite3", ledger=ledger).deposit(signal)
    config = WorkerConfig.model_validate_json(first_json).model_copy(update={"agent": AgentId(role="builder", instance=7)})
    _one_process(config.model_dump_json())
    task = ledger.get(signal.task_id)
    assert task.status == "completed" and task.owner == "builder-7" and task.effect_applied
    assert (target / destination).read_bytes() == after.encode("utf-8")
    assert runpy.run_path(str(target / destination))["answer"]() == 0
    adoption, = store.adoptions()
    assert adoption.asset_id == source_id and adoption.result_id == task.result_id
    assert adoption.context.worker_id == "builder-7" and adoption.context.task_id != original.attempt.task_id
    assert adoption.context.input_context == task.result["input_context"]
    assert store.consumption(adoption.context.execution_id).candidate_asset_id == task.result["candidate_asset_id"]
    events = [json.loads(p.read_bytes()) for p in (state / "audit").rglob("*.json")]
    assert len({row["pid"] for row in events if row["outcome"] == "promoted"}) == 2
    assert next(row for row in events if row["task_id"] == signal.task_id)["consumed_asset_ids"] == [source_id]


def test_reuse_verdict_distinguishes_transient_wait_from_failed_source(tmp_path):
    from swarm.models import Locality, Signal
    from swarm.worker_loop import Worker, WorkerConfig
    from swarm.cli import demo_config, seed_demo

    target, state = seed_demo(tmp_path / "verdict")
    worker = Worker(WorkerConfig.model_validate_json(demo_config(target, state, 0, 1.0)))
    ledger = worker.ledger
    locality = Locality(workspace=str(target), authorized_scopes=(".",))

    # Completed source whose asset is not yet approved -> transient wait.
    src = Signal(task_id="src-wait", workspace=str(target), scope="module_0",
                 kind="opportunity", required_capability="repair")
    ledger.enqueue(src)
    lease = ledger.claim("src-wait", "builder-0", locality=locality)
    assert lease is not None
    ledger.submit(lease, "r-src-wait", {"candidate_asset_id": "pending-approval"})
    reuse = Signal(task_id="reuse-wait", workspace=str(target), scope="module_0", kind="opportunity",
                   required_capability="repair",
                   payload={"reuse_task_id": "src-wait", "path_map": {"a.py": "b.py"}})
    ledger.enqueue(reuse, dependencies=("src-wait",))
    assert worker._reuse_verdict(reuse) == "wait"

    # A terminally failed source -> unsatisfiable (may be blocked).
    src2 = Signal(task_id="src-fail", workspace=str(target), scope="module_1",
                  kind="opportunity", required_capability="repair")
    ledger.enqueue(src2)
    for _ in range(3):  # Default max_attempts_per_task makes the third fail terminal.
        held = ledger.claim("src-fail", "builder-0", locality=locality)
        assert held is not None
        ledger.fail(held, {"error": "validation"})
    assert ledger.get("src-fail").status == "failed"
    reuse2 = Signal(task_id="reuse-fail", workspace=str(target), scope="module_1", kind="opportunity",
                    required_capability="repair",
                    payload={"reuse_task_id": "src-fail", "path_map": {"a.py": "b.py"}})
    ledger.enqueue(reuse2, dependencies=("src-fail",))
    assert worker._reuse_verdict(reuse2) == "unsatisfiable"
