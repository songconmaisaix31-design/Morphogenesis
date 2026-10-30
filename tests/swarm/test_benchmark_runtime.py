from __future__ import annotations

import json
import multiprocessing
from pathlib import Path
import sqlite3

import httpx
import pytest

from swarm.benchmark_model import SharedRequestGate, StepFunBenchmarkExecutor
from swarm.benchmark_runtime import budget_policy, run_tasks, seed_tasks, validate_tasks


def mock_model_factory(key, gate, timeout):
    def handle(request):
        payload = json.loads(request.content)
        assert payload["messages"][1]["content"].startswith("Synthetic question ")
        assert "gold" not in payload["messages"][1]["content"].lower()
        return httpx.Response(200, json={
            "id": "mock-request", "model": "step-3.5-flash",
            "choices": [{"message": {"content": "Synthetic reasoning.\n#### 999"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18},
        })
    return StepFunBenchmarkExecutor(key, gate, timeout_seconds=timeout,
                                    transport=httpx.MockTransport(handle), provenance="mock")


def rejection_factory(key, gate, timeout):
    return StepFunBenchmarkExecutor(key, gate, timeout_seconds=timeout,
        transport=httpx.MockTransport(lambda request: httpx.Response(429, json={"error": "rate limited"})),
        provenance="mock")


def filtered_factory(key, gate, timeout):
    return StepFunBenchmarkExecutor(key, gate, timeout_seconds=timeout,
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json={
            "id": "mock-filtered", "model": "step-3.5-flash",
            "choices": [{"message": {"content": None}, "finish_reason": "content_filter"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 0, "total_tokens": 10},
        })), provenance="mock")


def missing_usage_factory(key, gate, timeout):
    return StepFunBenchmarkExecutor(key, gate, timeout_seconds=timeout,
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json={
            "id": "mock-no-metering", "model": "step-3.5-flash",
            "choices": [{"message": {"content": "#### 999"}, "finish_reason": "stop"}],
        })), provenance="mock")


def tasks(count=4):
    return [{"id": f"synthetic-{index}", "prompt": f"Synthetic question {index}: add one and one."}
            for index in range(count)]


def test_task_contract_rejects_gold_duplicate_and_unbounded_inventory():
    with pytest.raises(ValueError, match="contract"):
        validate_tasks([{"id": "x", "prompt": "q", "gold": "2"}])
    with pytest.raises(ValueError, match="unique"):
        validate_tasks([{"id": "x", "prompt": "q"}] * 2)
    with pytest.raises(ValueError, match="48"):
        validate_tasks(tasks(49))


def test_seeding_uses_fixed_independent_scopes_and_no_gold(tmp_path):
    target, state = seed_tasks(tmp_path / "fresh", tasks(), run_id="seed-fixture",
                               policy=budget_policy(4, 60, 128))
    with sqlite3.connect(state / "tasks.sqlite3") as db:
        rows = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        assert rows
        dump = "\n".join(db.iterdump())
    assert "gold" not in dump
    assert "bounded-json-answer-v1" in dump
    assert "expectations" not in dump
    assert sorted(path.name for path in target.glob("task_*")) == [f"task_{i:03d}" for i in range(4)]


@pytest.mark.parametrize("concurrency", [1, 2])
def test_real_worker_processes_and_sqlite_accept_wrong_but_safe_output(tmp_path, concurrency):
    context = multiprocessing.get_context("spawn")
    gate = SharedRequestGate.create(context, concurrency=concurrency, max_requests=4)
    result = run_tasks(tasks(), credential="not-a-real-key-fixture", gate=gate,
        run_id=f"runtime-fixture-{concurrency}", block_id="block-0", seed=7,
        concurrency=concurrency, max_tokens=128, temperature=0.0,
        directory=tmp_path / f"c{concurrency}", runtime_seconds=90,
        timeout_seconds=2, model_factory=mock_model_factory, context=context)
    assert result["runtime"]["owned_workers_exited"]
    assert not result["runtime"]["forced_termination_pids"]
    assert len(result["runtime"]["processes"]) == concurrency
    assert all(p["exit_code"] == 0 for p in result["runtime"]["processes"])
    assert [record["task_id"] for record in result["records"]] == [task["id"] for task in tasks()]
    for record in result["records"]:
        assert record["text"] == "Synthetic reasoning.\n#### 999"
        assert record["evidence"]["provenance"] == "mock"
        assert record["native_task"]["status"] == "completed", record
        assert record["native_task"]["attempts"] == 1
        assert record["native_task"]["effect_applied"]
    assert gate.snapshot()["reserved_requests"] == 4
    with sqlite3.connect(result["runtime"]["budget"]) as db:
        assert db.execute("SELECT COUNT(*),COUNT(DISTINCT task_id) FROM budget_reservations").fetchone() == (4, 4)
    files = list((tmp_path / f"c{concurrency}").rglob("*"))
    assert not any(b"not-a-real-key-fixture" in path.read_bytes()
                   for path in files if path.is_file())


def test_shared_fatal_rejection_stops_future_calls_and_keeps_all_tasks(tmp_path):
    context = multiprocessing.get_context("spawn")
    gate = SharedRequestGate.create(context, concurrency=1, max_requests=4)
    result = run_tasks(tasks(), credential="not-a-real-key-fixture", gate=gate,
        run_id="fatal-fixture", block_id="block-0", seed=7,
        concurrency=1, max_tokens=128, temperature=0.0,
        directory=tmp_path / "fatal", runtime_seconds=30,
        timeout_seconds=2, model_factory=rejection_factory, context=context)
    assert len(result["records"]) == 4
    assert gate.snapshot()["reserved_requests"] == 1
    assert gate.snapshot()["stopped"]
    assert sum(row["status"] == "fatal" for row in result["records"]) == 1
    assert result["runtime"]["owned_workers_exited"]
    assert not result["runtime"]["forced_termination_pids"]


def test_known_filtered_terminal_preserves_raw_none_and_continues(tmp_path):
    context = multiprocessing.get_context("spawn")
    gate = SharedRequestGate.create(context, concurrency=5, max_requests=2)
    result = run_tasks(tasks(2), credential="not-a-real-key-fixture", gate=gate,
        run_id="filter-fixture", block_id="block-0", seed=7,
        concurrency=1, max_tokens=128, temperature=0.0,
        directory=tmp_path / "filtered", runtime_seconds=30,
        timeout_seconds=2, model_factory=filtered_factory, context=context)
    assert gate.snapshot()["reserved_requests"] == 2
    assert not gate.snapshot()["stopped"]
    assert all(row["text"] is None and row["evidence"]["model_outcome"] == "filtered"
               and row["native_task"]["status"] == "completed" for row in result["records"])


def test_completed_missing_usage_retains_unknown_metering_and_continues(tmp_path):
    context = multiprocessing.get_context("spawn")
    gate = SharedRequestGate.create(context, concurrency=5, max_requests=2)
    result = run_tasks(tasks(2), credential="not-a-real-key-fixture", gate=gate,
        run_id="missing-metering-fixture", block_id="block-0", seed=7,
        concurrency=1, max_tokens=128, temperature=0.0,
        directory=tmp_path / "missing-metering", runtime_seconds=30,
        timeout_seconds=2, model_factory=missing_usage_factory, context=context)
    assert gate.snapshot()["reserved_requests"] == 2
    assert not gate.snapshot()["stopped"]
    assert result["runtime"]["owned_workers_exited"]
    assert all(row["usage"] is None and row["evidence"]["usage_metering"] == "unknown"
               and row["native_task"]["status"] == "completed" for row in result["records"])


def test_key_and_configuration_not_validated_after_side_effects(tmp_path):
    context = multiprocessing.get_context("spawn")
    gate = SharedRequestGate.create(context, concurrency=1, max_requests=4)
    with pytest.raises(ValueError):
        run_tasks(tasks(), credential="", gate=gate, run_id="x", block_id="b", seed=0,
                  concurrency=1, max_tokens=128, temperature=0.0, directory=tmp_path / "not-created")
    assert not (tmp_path / "not-created").exists()
