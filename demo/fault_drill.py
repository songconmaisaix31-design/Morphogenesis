"""Six-stage, offline FC drill through the real Worker and persistent stores.

Only executor responses are simulated. FixtureExecutor supplies its existing file
transformation; the real in-process EvoMap mock transport classifies the rejection.
No live request child is launched. All usage/cost remain unobserved (None).
The isolated, bounded mock policy allows unknown usage and retains every hold.
"""
from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from dataclasses import replace
import json
from pathlib import Path
import sqlite3
import tempfile
import time
from typing import Any, cast
from unittest.mock import Mock
from uuid import uuid4

import httpx
from pydantic import JsonValue

from orchestration.fc_logging import FCLogWriter, validate_event
from swarm.breaker import BreakerConfig, SharedBreaker
from swarm.cli import demo_config, seed_demo
from swarm.evomap_executor import _request
from swarm.failure_chain import SharedBreakerLike, guard_provider
from swarm.fault_observations import FaultObservationStore, FaultReadResult
from swarm.models import BudgetPolicy, ExecutionBound, RunLimits, Signal
from swarm.pheromone import PheromoneField
from swarm.task_ledger import TaskLedger
from swarm.worker_loop import ExecutionResult, Executor, FixtureExecutor, Worker, WorkerConfig, check_state_path


SCENARIO = "confirmed-rejection-peer-avoidance"
LABELS: dict[str, JsonValue] = {"drill": True, "provenance": "mock", "evidence_label": "SIMULATED"}


def require(condition: object, detail: object) -> None:
    """Checks run outside Worker exception handlers and executor callbacks."""
    if not condition:
        raise AssertionError(detail)


def breaker_config() -> BreakerConfig:
    return BreakerConfig(window_seconds=600.0, aggregation_period_seconds=1.0,
                         failure_threshold=2, min_samples=2, cooldown_seconds=30.0,
                         probe_ttl_seconds=60.0)


def prepare(directory: Path, *, policy: BudgetPolicy | None = None) -> WorkerConfig:
    directory = check_state_path(Path(directory))
    if not directory.is_relative_to(Path(tempfile.gettempdir()).resolve()):
        raise ValueError("drill_directory_must_be_under_os_temp")
    if directory.exists():
        raise ValueError("drill_directory_must_be_new")
    directory.mkdir(parents=True)
    target, seeded = seed_demo(directory / "source-target")
    config = WorkerConfig.model_validate_json(demo_config(target, seeded, 0, 2.0))
    policy = policy or BudgetPolicy(max_cost_usd=2.0, unbounded_reservation_usd=0.2,
                          allow_unknown_usage=True,
                          limits=RunLimits(max_tasks=6, max_attempts=8,
                                           max_attempts_per_task=2, max_derived_tasks=0))
    config = config.model_copy(update={
        "swarm_id": "fault-drill-" + uuid4().hex, "state": directory / "state",
        "budget": policy, "lease_seconds": 60.0,
        "locality": config.locality.model_copy(update={
            "authorized_scopes": ("module_0", "module_1", "module_2"),
            "modules": ("module_0", "module_1", "module_2"),
        }),
    })
    ledger = TaskLedger(config.state / "tasks.sqlite3", config.swarm_id, limits=policy.limits)
    field = PheromoneField(config.state / "field.sqlite3", ledger=ledger)
    for task in TaskLedger(seeded / "tasks.sqlite3", "local-fixture").snapshot():
        ledger.enqueue(task.signal, acceptance=task.acceptance)
        field.deposit(task.signal)
    return config


def rejection() -> ExecutionResult:
    # Reuse production classification AND evidence hashing, in its explicit
    # in-process mock mode. A literal offline key is never a real credential.
    transport = httpx.MockTransport(lambda request: httpx.Response(
        400, json={"error": {"code": "Arrearage", "message": "SIMULATED"}},
        headers={"x-request-id": "SIMULATED-rejection"}))
    reply = _request({"model": "fixture", "messages": []}, "offline-drill-key", 1.0,
                     transport=transport, provenance="mock")
    return ExecutionResult(None, None, uncertain=True, metadata={
        "classification": reply.classification, "normalized_reason": reply.normalized_reason,
        "retry_after_seconds": reply.retry_after_seconds, "evidence_hash": reply.evidence_hash,
        **LABELS,
    })


def executor(provider: str, *, reject_tasks: tuple[str, ...] = (),
             before_execute: Callable[[], object] | None = None) -> Mock:
    fixture = FixtureExecutor()
    boundary = Mock(spec_set=FixtureExecutor, wraps=fixture)
    boundary.provenance = "mock"
    boundary.usage_source = "fixture_mock"
    boundary.original_run_uri = None
    boundary.bound.return_value = ExecutionBound(
        provider=provider, model="fixture", input_tokens=1, max_output_tokens=1,
        provider_enforced=False, request_bound="unbounded")

    def execute(signal: Signal, *args: Any, **kwargs: Any) -> ExecutionResult:
        if before_execute is not None:
            before_execute()
        if signal.task_id in reject_tasks:
            return rejection()
        # Synthetic fixture tokens are not provider observations.
        return replace(fixture.execute(signal, *args, **kwargs), usage=None)

    boundary.execute.side_effect = execute
    return boundary


def make_worker(config: WorkerConfig, candidates: Sequence[Executor], instance: int = 0, *,
                fc_log: FCLogWriter | None = None) -> Worker:
    config = config.model_copy(update={"agent": config.agent.model_copy(update={"instance": instance})})
    writer = fc_log or FCLogWriter(config.state.parent, config.swarm_id, provenance="mock", drill=True)
    return Worker(config, candidates[0], candidates=candidates, breaker_config=breaker_config(), fc_log=writer)


def reservations(worker: Worker) -> list[dict[str, Any]]:
    with sqlite3.connect(worker.budget.path) as db:
        db.row_factory = sqlite3.Row
        return [dict(row) for row in db.execute(
            "SELECT * FROM budget_reservations WHERE swarm_id=? ORDER BY created_at,rowid",
            (worker.config.swarm_id,))]


def process(worker: Worker, task_id: str) -> dict[str, Any]:
    signal = worker.ledger.get(task_id).signal
    lease = worker.leases.acquire(task_id, worker.worker_id, ttl_seconds=60.0,
                                  locality=worker.config.locality)
    if lease is None:
        raise AssertionError("task lease unavailable")
    outcome = worker._process(signal, lease)
    return {"worker_id": worker.worker_id, "task_id": task_id, "outcome": outcome,
            "lease": lease.model_dump(mode="json"),
            "task": worker.ledger.get(task_id).model_dump(mode="json"),
            "reservations": reservations(worker),
            "budget": worker.budget.snapshot().model_dump(mode="json")}


class ReadTraceStore(FaultObservationStore):
    """Passive read instrumentation: return the untouched real store snapshot."""

    def __init__(self, path: Path, run_id: str) -> None:
        super().__init__(path, run_id)
        self.reads: list[dict[str, Any]] = []

    def read(self) -> FaultReadResult:
        snapshot = super().read()
        self.reads.append(snapshot.model_dump(mode="json"))
        return snapshot


def peer_sequence(config: WorkerConfig, *, fc_log: FCLogWriter | None = None
                  ) -> tuple[Worker, Worker, dict[str, Any]]:
    """Stages 1-4; no precomputed aggregates or direct state writes."""
    primary = executor("alpha", reject_tasks=("fixture-1",))
    backup = executor("beta")
    writer = fc_log or FCLogWriter(config.state.parent, config.swarm_id, provenance="mock", drill=True)
    worker_a = make_worker(config, [primary, backup], fc_log=writer)
    baseline = process(worker_a, "fixture-0")
    baseline["calls"] = {"alpha": primary.execute.call_count, "beta": backup.execute.call_count}
    require(baseline["outcome"] == "completed", baseline)
    require(baseline["calls"] == {"alpha": 1, "beta": 0}, baseline)

    switched = process(worker_a, "fixture-1")
    switched["calls"] = {"alpha": primary.execute.call_count - 1, "beta": backup.execute.call_count}
    require(switched["outcome"] == "completed", switched)
    require(switched["calls"] == {"alpha": 1, "beta": 1}, switched)
    snapshot = cast(FaultObservationStore, worker_a.fault_observation_store).read()
    require(not snapshot.issues and len(snapshot.records) == 1, snapshot)
    fact = snapshot.records[0]
    require(fact.failure_class == "confirmed_rejection" and fact.switched_to == "beta:fixture", fact)
    require(fact.cost_state == "unknown" and bool(fact.evidence_ref), fact)
    fault = {**fact.model_dump(mode="json"), "append_sequence": snapshot.record_lines[0]}

    blocked, alternate = executor("alpha"), executor("beta")
    worker_b = make_worker(config, [blocked, alternate], instance=1, fc_log=writer)
    trace = ReadTraceStore(cast(FaultObservationStore, worker_b.fault_observation_store).path, config.swarm_id)
    worker_b.fault_observation_store = trace
    breaker = cast(SharedBreaker, worker_b.shared_breaker)
    before = breaker.view("alpha", "billing_arrearage")
    avoided = process(worker_b, "fixture-2")
    # Behavior first: a broken aggregate transition must change executor calls.
    avoided["calls"] = {"alpha": blocked.execute.call_count, "beta": alternate.execute.call_count}
    require(avoided["calls"] == {"alpha": 0, "beta": 1}, avoided)
    require(avoided["outcome"] == "completed", avoided)
    after = breaker.view("alpha", "billing_arrearage")
    require(before.state == "insufficient_evidence" and after.state == "suspended", (before, after))
    require(any(fact.model_dump(mode="json") in read["records"] for read in trace.reads), trace.reads)
    require(writer.failure_count == 0, "FC log projection failed")
    avoided.update(shared_store=str(trace.path), reads=list(trace.reads),
                   breaker_before=before.model_dump(mode="json"), breaker_after=after.model_dump(mode="json"))
    return worker_a, worker_b, {"normal": baseline, "rejection": fault,
                               "controlled_switch": switched, "peer_avoidance": avoided}


def wait_until(deadline: float) -> None:
    time.sleep(max(0.0, deadline - time.time()))


def recover(config: WorkerConfig, worker_a: Worker, worker_b: Worker, *,
            wait: Callable[[float], None] = wait_until,
            fc_log: FCLogWriter | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    store = cast(FaultObservationStore, worker_a.fault_observation_store)
    breaker = cast(SharedBreaker, worker_a.shared_breaker)
    old_bytes = store.path.read_bytes()
    view = breaker.view("alpha", "billing_arrearage")
    before_guard = guard_provider(cast(SharedBreakerLike, breaker), "alpha", worker_a.worker_id, now=time.time())
    require(not before_guard.routable and not before_guard.claims, before_guard)
    if view.cooldown_until is None:
        raise AssertionError(view)
    wait(view.cooldown_until)
    captured: list[dict[str, Any]] = []
    primary = executor("alpha", before_execute=lambda: captured.append(
        breaker.view("alpha", "billing_arrearage").model_dump(mode="json")))
    backup = executor("beta")
    # Same real Worker A, changing only its explicitly injected executor boundary.
    worker_a.executor = primary
    worker_a._candidates = (primary, backup)
    recovered = process(worker_a, "fixture-3")
    require(primary.execute.call_count == 1 and backup.execute.call_count == 0, recovered)
    require(recovered["outcome"] == "completed" and len(captured) == 1, recovered)
    probe = captured[0]
    require(probe["state"] == "probing_recovery" and probe["probe_owner"] == worker_a.worker_id, probe)
    require(probe["probe_token"] > view.probe_token, probe)
    require(probe["probe_expires_at"] > probe["updated_at"], probe)
    observers: dict[str, Any] = {}
    for name, subject in (("same_worker", worker_a), ("other_worker", worker_b),
                          ("restart", make_worker(config, [executor("alpha")], instance=2, fc_log=fc_log))):
        reader = cast(SharedBreaker, subject.shared_breaker)
        reader.observe(cast(FaultObservationStore, subject.fault_observation_store), now=time.time())
        current = reader.view("alpha", "billing_arrearage")
        require(current.state == "normal" and current.recovery_sequence == store.checkpoint(), current)
        observers[name] = current.model_dump(mode="json")
    require(store.path.read_bytes() == old_bytes, "recovery altered historical observations")
    recovered.update(calls={"alpha": primary.execute.call_count, "beta": backup.execute.call_count},
                     observers=observers, breaker_audit=breaker.audit(),
                     history_preserved=True)
    return {"before_cooldown_routable": before_guard.routable, "probe": probe}, recovered


def run_drill(directory: Path, *, wait: Callable[[float], None] = wait_until) -> dict[str, Any]:
    config = prepare(directory)
    writer = FCLogWriter(directory, config.swarm_id, provenance="mock", drill=True)
    worker_a, worker_b, stages = peer_sequence(config, fc_log=writer)
    stages["cooldown_probe"], stages["recovery"] = recover(config, worker_a, worker_b, wait=wait, fc_log=writer)
    rows = reservations(worker_a)
    require(len(rows) == 5 and all(row["reserved_usd"] == 0.2 for row in rows), rows)
    require(all(row["tokens"] is None and row["cost"] == "unknown" and row["status"] == "uncertain"
                for row in rows), rows)
    require(worker_a.budget.snapshot().reserved_estimate_usd == 1.0, rows)
    require(writer.failure_count == 0, "FC log projection failed")
    records = [validate_event(json.loads(line)) for line in writer.path.read_text(encoding="utf-8").splitlines()]
    require(records, "FC log is empty")
    for record in records:
        require(all(record[key] == value for key, value in LABELS.items()), record)
        require(record["run_id"] == config.swarm_id and record["schema_version"] == "1.0.0", record)
        require(record.get("audit_confirmed_issue_events") is None and record.get("issue_audit") is None, record)
    logged_facts = [record["fault_observation"] for record in records if record["event"] == "fault_observation"]
    actual_facts = [fact.model_dump(mode="json") for fact in
                    cast(FaultObservationStore, worker_a.fault_observation_store).read().records]
    require(logged_facts == actual_facts, "FC log missing or duplicating the actual failure fact")
    expected_tasks = {f"fixture-{number}" for number in range(4)}
    for event in ("claim", "task", "asset_call"):
        require(expected_tasks <= {record["task_id"] for record in records if record["event"] == event},
                f"FC log missing {event} identity")
    result = {**LABELS, "run_id": config.swarm_id, "scenario": SCENARIO,
              "mock_budget_policy": config.budget.model_dump(mode="json"),
              "fc_log_path": str(writer.path), "fc_log_records": len(records),
              "writer_failure_count": writer.failure_count,
              "contract_local": "passed", "interface_live": "not_run", "task_live": "not_run",
              "usage": None, "cost_usd": None, "stages": stages}
    Path(directory, "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--scenario", choices=[SCENARIO], default=SCENARIO)
    args = parser.parse_args(argv)
    result = run_drill(args.directory)
    print(json.dumps({**LABELS, "run_id": result["run_id"], "stages": list(result["stages"]),
                      "result": str(args.directory / "result.json")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
