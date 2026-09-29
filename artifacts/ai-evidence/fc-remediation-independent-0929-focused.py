"""D's independent probes; reusable fixture setup only, no Owner test calls.

Run from an exact LF archive with PYTHONPATH pointing to that archive. Only
executor/network boundaries are mocked. Assertions are outside production catches.
Local fixture token counts are synthetic; no real billing or live claims.
"""
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import json
import os
from pathlib import Path
import subprocess
import sys
from threading import Event
from unittest.mock import Mock

import httpx
import pytest
import time_machine

from orchestration.provider_adapters.base import RequestContext
from orchestration.provider_adapters.dashscope import DashScopeAdapter
from orchestration.provider_adapters.evomap import EvoMapAdapter
from swarm.breaker import BreakerConfig
from swarm.cli import EvoMapRun, evomap_worker_config, seed_evomap
from swarm.evomap_executor import EvoMapConfig, EvoMapExecutor
from swarm.pheromone import PheromoneField
from swarm.task_ledger import TaskLedger
from swarm.worker_loop import FixtureExecutor, Worker, WorkerConfig
from tests.swarm.test_failure_chain_runtime import (
    _claim, _events, _executor, _facts, _failure, _reservations, _worker_config,
)

BREAK = BreakerConfig(window_seconds=600, aggregation_period_seconds=1,
    failure_threshold=2, min_samples=2, cooldown_seconds=4, probe_ttl_seconds=7)
NOW = 1800000300.0


def settings(tmp_path, *, prices=True, only_first=False, instance=0):
    cfg = _worker_config(tmp_path, prices=prices, max_cost=10)
    locality = cfg.locality.model_copy(update={
        "authorized_scopes": ("module_0", "module_1", "module_2"),
        "modules": ("module_0", "module_1", "module_2"),
        "dependency_of": ("fixture-0",) if only_first else (),
    })
    return cfg.model_copy(update={"locality": locality, "max_idle": 1,
        "agent": cfg.agent.model_copy(update={"instance": instance})})


def subject(cfg, *executors):
    return Worker(cfg, executors[0], candidates=executors, breaker_config=BREAK)


def process(worker, number=0):
    signal, lease = _claim(worker, f"fixture-{number}")
    return worker._process(signal, lease)


def child(cfg, mode="recover"):
    completed = subprocess.run([sys.executable, str(Path(__file__).resolve()), mode,
        cfg.model_dump_json()], cwd=Path.cwd(), capture_output=True, text=True, timeout=50)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    result = json.loads(completed.stdout)
    assert result["pid"] != os.getpid()
    assert Path(result["source"]).resolve().is_relative_to(Path.cwd().resolve())
    return result


@pytest.mark.parametrize("instance", [0, 11])
@pytest.mark.parametrize("handoff", [False, True])
def test_unknown_settled_effect_restart_and_handoff(tmp_path, instance, handoff):
    cfg = settings(tmp_path, only_first=True)
    boundary = _executor()
    worker = subject(cfg, boundary)
    destination = cfg.model_copy(update={"agent": cfg.agent.model_copy(update={"instance": instance})})
    moved = []
    def unknown(*args, **kwargs):
        if handoff:
            current, = worker.leases.snapshot()
            next_owner = destination.worker_id if instance else "recipient-D"
            moved.append(worker.leases.handoff(current, next_owner))
        return _failure("unknown_effect", known_usage=True, reason="read_timeout")
    boundary.execute.side_effect = unknown
    outcome = process(worker)
    rows = _reservations(worker)
    assert boundary.execute.call_count == 1 and outcome == "sleeping", _events(worker)
    assert not handoff or (len(moved) == 1 and moved[0].status == "handoff")
    assert rows[0]["status"] == "settled" and rows[0]["tokens"] == 2
    snapshot = worker.budget.snapshot()
    assert not snapshot.sleeping and snapshot.reserved_estimate_usd == 0
    assert snapshot.admission_charged_usd < cfg.budget.max_cost_usd / 10
    restarted = child(destination)
    assert restarted["calls"] == 0, restarted
    assert restarted["rows"] == rows and restarted["result_id"] is None
    assert restarted["budget_sleeping"] is False
    fresh = subject(destination, _executor())
    assert fresh.leases.acquire("fixture-0", fresh.worker_id, locality=cfg.locality) is None


def test_confirmed_rejection_success_and_lost_lease_controls(tmp_path):
    cfg = settings(tmp_path / "normal", only_first=True)
    reject, success = _executor(result=_failure(known_usage=True, reason="rate_limited")), _executor()
    worker = subject(cfg, reject, success)
    outcome = process(worker)
    assert outcome == "completed", _events(worker)
    assert [reject.execute.call_count, success.execute.call_count] == [1, 1]
    assert child(cfg)["calls"] == 0
    cfg = settings(tmp_path / "loss", only_first=True)
    boundary = _executor()
    worker = subject(cfg, boundary)
    old_bytes = (worker.target / "module_0/task_0.py").read_bytes()
    moved, results = [], []
    def lose(*args, **kwargs):
        result = FixtureExecutor().execute(*args, **kwargs)
        results.append(result)
        current, = worker.leases.snapshot()
        moved.append(worker.leases.handoff(current, "replacement-D"))
        return result
    boundary.execute.side_effect = lose
    outcome = process(worker)
    assert boundary.execute.call_count == 1 and results[0].candidate is not None
    assert moved[0].status == "handoff" and outcome == "failed", _events(worker)
    assert worker.ledger.get("fixture-0").result_id is None
    assert not worker.assets.promotions()
    assert (worker.target / "module_0/task_0.py").read_bytes() == old_bytes


def suspended(cfg):
    boundary = _executor(result=_failure(known_usage=True, reason="billing_arrearage"))
    worker = subject(cfg, boundary)
    assert process(worker) == "rejected", _events(worker)
    assert boundary.execute.call_count == 1
    worker.shared_breaker.observe(worker.fault_observation_store)
    assert worker.shared_breaker.view("local", "billing_arrearage").state == "suspended"
    return worker


@pytest.mark.parametrize("same_owner", [False, True])
def test_ttl_worker_boundary_fences_both_old_results(tmp_path, same_owner):
    with time_machine.travel(NOW, tick=False) as clock:
        cfg = settings(tmp_path)
        old = suspended(cfg)
        clock.shift(4)
        owner = cfg.worker_id if same_owner else "departed-D"
        slot = old.shared_breaker.try_claim_probe("local", "billing_arrearage", owner)
        clock.shift(6.99)
        competitor = subject(cfg.model_copy(update={"agent": cfg.agent.model_copy(update={"instance": 9})}), _executor())
        early = process(competitor, 2)
        assert competitor.executor.execute.call_count == 0 and early == "sleeping"
        assert old.shared_breaker.view("local", "billing_arrearage") == slot
        clock.shift(.01)
        contender = subject(cfg, _executor())
        captured = []
        def execute(*args, **kwargs):
            before = contender.shared_breaker.view("local", "billing_arrearage")
            a = old.shared_breaker.report_probe_success("local", "billing_arrearage", owner, probe_token=slot.probe_token)
            b = old.shared_breaker.report_probe_failure("local", "billing_arrearage", owner, probe_token=slot.probe_token)
            captured.append((before, a, b, contender.shared_breaker.view("local", "billing_arrearage")))
            return FixtureExecutor().execute(*args, **kwargs)
        contender.executor.execute.side_effect = execute
        result = process(contender, 2)
        assert contender.executor.execute.call_count == 1, _events(contender)
        assert result == "completed"
        before, a, b, after = captured[0]
        assert before == after and a is b is False
        assert before.probe_token == slot.probe_token + 1
        assert contender.shared_breaker.view("local", "billing_arrearage").state == "normal"


def test_ttl_two_workers_only_one_executor(tmp_path):
    with time_machine.travel(NOW, tick=False) as clock:
        cfg = settings(tmp_path)
        old = suspended(cfg)
        clock.shift(4)
        stale = old.shared_breaker.try_claim_probe("local", "billing_arrearage", "lost-D")
        clock.shift(7)
        release, entered = Event(), Event()
        def held(*args, **kwargs):
            entered.set()
            release.wait(20)
            return _failure(known_usage=True, reason="rate_limited")
        workers = [subject(cfg.model_copy(update={"agent": cfg.agent.model_copy(update={"instance": n})}),
                           _executor(effect=held)) for n in (4, 5)]
        with ThreadPoolExecutor(2) as pool:
            futures = [pool.submit(process, w, n) for w, n in zip(workers, (2, 4))]
            try:
                finished, _ = wait(futures, timeout=18, return_when=FIRST_COMPLETED)
                seen = entered.wait(1)
                counts = [w.executor.execute.call_count for w in workers]
                token = old.shared_breaker.view("local", "billing_arrearage").probe_token
            finally:
                release.set()
            outcomes = [f.result(timeout=25) for f in futures]
        assert finished and seen and sorted(counts) == [0, 1]
        assert sorted(w.executor.execute.call_count for w in workers) == [0, 1]
        assert sorted(outcomes) == ["rejected", "sleeping"]
        assert token == stale.probe_token + 1


def test_recovery_watermark_old_history_and_equal_time_new_faults(tmp_path):
    with time_machine.travel(NOW, tick=False) as clock:
        cfg = settings(tmp_path)
        bad = _executor(result=_failure(known_usage=True, reason="rate_limited"))
        origin = subject(cfg, bad)
        for n in (0, 1):
            assert process(origin, n) == "rejected", _events(origin)
        assert bad.execute.call_count == 2
        origin.shared_breaker.observe(origin.fault_observation_store)
        old_bytes = origin.fault_observation_store.path.read_bytes()
        peer = subject(cfg.model_copy(update={"agent": cfg.agent.model_copy(update={"instance": 8})}), _executor())
        peer.shared_breaker.observe(peer.fault_observation_store)
        stale_aggregate = peer.fault_observation_store.aggregate(now=NOW, window_seconds=600)
        clock.shift(4)
        recovered = subject(cfg, _executor())
        assert process(recovered, 2) == "completed", _events(recovered)
        assert recovered.executor.execute.call_count == 1
        observed_states = []
        for reader in (recovered, peer):
            reader.shared_breaker.observe(reader.fault_observation_store)
            reader.shared_breaker.apply_aggregates(stale_aggregate)
            observed_states.append(reader.shared_breaker.view("local", "rate_limited").state)
        restarted = child(cfg, "observe")
        assert recovered.fault_observation_store.path.read_bytes() == old_bytes
        fresh = _executor(result=_failure(known_usage=True, reason="rate_limited"))
        emitter = subject(cfg, fresh)
        outcomes = [process(emitter, n) for n in (3, 4)]
        assert fresh.execute.call_count == 2
        assert outcomes == ["rejected", "rejected"], _events(emitter)
        assert observed_states == ["normal", "normal"]
        assert restarted["breaker"] == "normal" and restarted["records"] == 2
        blocked = process(emitter, 5)
        assert fresh.execute.call_count == 2 and blocked == "sleeping", _events(emitter)
        records = _facts(emitter)
        assert len(records) == 4 and [r.occurred_at for r in records[2:]] == [NOW + 4] * 2
        assert emitter.fault_observation_store.path.read_bytes().startswith(old_bytes)


@pytest.mark.parametrize("allow", [False, True])
def test_current_reservation_cost_and_retained_hold(tmp_path, allow):
    cfg = settings(tmp_path / "missing", prices=False)
    cfg = cfg.model_copy(update={"budget": cfg.budget.model_copy(update={"allow_unknown_cost": allow})})
    e = _executor(result=_failure(known_usage=True, reason="rate_limited"))
    worker = subject(cfg, e)
    assert process(worker) == "rejected", _events(worker)
    assert e.execute.call_count == 1
    row, = _reservations(worker)
    fact, = _facts(worker)
    assert fact.cost_state == "unknown" and fact.request_id == row["request_id"]
    assert row["tokens"] == 2 and row["estimate_usd"] is row["admitted_usd"] is None
    assert row["cost"] == "unknown" and worker.budget.snapshot().reserved_estimate_usd == .2
    assert subject(cfg, _executor()).budget.snapshot().reserved_estimate_usd == .2
    cfg = settings(tmp_path / "mixed")
    unknown, settled = _executor(result=_failure(reason="rate_limited")), _executor(result=_failure(known_usage=True, reason="rate_limited"))
    worker = subject(cfg, unknown, settled)
    assert process(worker) == "rejected", _events(worker)
    assert [unknown.execute.call_count, settled.execute.call_count] == [1, 1]
    rows = _reservations(worker)
    facts = {f.request_id: f for f in _facts(worker)}
    assert worker.budget.snapshot().cost == "unknown"
    assert [facts[row["request_id"]].cost_state for row in rows] == ["unknown", "settled"]
    assert worker.budget.snapshot().reserved_estimate_usd == .2


@pytest.mark.parametrize("adapter,provider", [(DashScopeAdapter, "dashscope"), (EvoMapAdapter, "evomap")])
@pytest.mark.parametrize("status", [0, 400, 403, 429, 500, 503, 599])
@pytest.mark.parametrize("code,message", [("Arrearage", "账户欠费 balance account"), ("AllocationQuota.FreeTierOnly", "免费配额 exhausted quota")])
def test_adapter_status_priority(adapter, provider, status, code, message):
    body = json.dumps({"code": code, "message": message, "error": {"code": code, "message": message}})
    result = adapter.interpret(body, status, {}, RequestContext(provider=provider, model="D", endpoint="/chat/completions"))
    expected = "unknown_effect" if status == 0 or status >= 500 else "confirmed_rejection"
    assert result.classification.value == expected


def gateway(tmp_path, handler):
    run = EvoMapRun(directory=tmp_path / "demo", api=EvoMapConfig(credential_file=tmp_path / "mock-unused"),
        budget={"max_cost_usd": 10, "unbounded_reservation_usd": .2,
                "limits": {"max_tasks": 6, "max_attempts": 6, "max_attempts_per_task": 1,
                           "max_derived_tasks": 0, "max_runtime_seconds": 300}})
    seed_evomap(run)
    cfg = WorkerConfig.model_validate_json(evomap_worker_config(run, 0))
    cfg = cfg.model_copy(update={"state": tmp_path / "state", "budget": cfg.budget.model_copy(update={
        "burn_rate_tokens": 100000, "limits": cfg.budget.limits.model_copy(update={"max_attempts_per_task": 8})})})
    ledger = TaskLedger(cfg.state / "tasks.sqlite3", cfg.swarm_id, limits=cfg.budget.limits)
    field = PheromoneField(cfg.state / "field.sqlite3", ledger=ledger)
    # Read the canonical seeded location from the CLI's config.
    seeded_cfg = WorkerConfig.model_validate_json(evomap_worker_config(run, 0))
    seeded = TaskLedger(seeded_cfg.state / "tasks.sqlite3", cfg.swarm_id, limits=seeded_cfg.budget.limits)
    for task in seeded.snapshot():
        ledger.enqueue(task.signal, acceptance=task.acceptance)
        field.deposit(task.signal)
    calls = [Mock(side_effect=handler), Mock(side_effect=lambda request: httpx.Response(429, text="rate limit"))]
    executors = []
    for call in calls:
        real = EvoMapExecutor(run.api, transport=httpx.MockTransport(call), provenance="mock")
        wrapper = Mock(spec_set=EvoMapExecutor, wraps=real)
        for attr in ("provenance", "usage_source", "original_run_uri"):
            setattr(wrapper, attr, getattr(real, attr))
        executors.append(wrapper)
    return subject(cfg, *executors), executors, calls


@pytest.mark.parametrize("status", [400, 403, 429, 500, 503, 599])
def test_real_gateway_request_count(tmp_path, status):
    worker, executors, network = gateway(tmp_path, lambda request: httpx.Response(status,
        json={"error": {"code": "Arrearage", "message": "账户余额欠费 quota exceeded"}}))
    signal, lease = _claim(worker, "data-0")
    outcome = worker._process(signal, lease)
    expected = [1, 0] if status >= 500 else [1, 1]
    assert [x.execute.call_count for x in executors] == expected, _events(worker)
    assert [x.call_count for x in network] == expected
    assert outcome == ("sleeping" if status >= 500 else "rejected")
    assert all(r["tokens"] is None and r["cost"] == "unknown" for r in _reservations(worker))
    assert worker.budget.snapshot().reserved_estimate_usd == .2 * sum(expected)


def test_transport_unknown_precedes_rejection_body(tmp_path):
    class Partial(httpx.SyncByteStream):
        def __iter__(self):
            yield b'{"error":{"code":"Arrearage","message":"account balance"}}'
            raise httpx.ReadTimeout("D synthetic interruption")
    worker, executors, network = gateway(tmp_path, lambda request: httpx.Response(400, stream=Partial()))
    signal, lease = _claim(worker, "data-0")
    worker._process(signal, lease)
    assert [x.execute.call_count for x in executors] == [1, 0]
    assert [x.call_count for x in network] == [1, 0]
    fact, = _facts(worker)
    assert fact.failure_class == "unknown_effect" and fact.switched_to is None


if __name__ == "__main__":
    import swarm.worker_loop as source
    cfg = WorkerConfig.model_validate_json(sys.argv[2])
    boundary = _executor(result=_failure("unknown_effect", known_usage=True, reason="read_timeout"))
    worker = subject(cfg, boundary)
    output = {"pid": os.getpid(), "source": source.__file__}
    if sys.argv[1] == "recover":
        worker.run()
        output.update(calls=boundary.execute.call_count, rows=_reservations(worker),
            result_id=worker.ledger.get("fixture-0").result_id, budget_sleeping=worker.budget.snapshot().sleeping)
    else:
        worker.shared_breaker.observe(worker.fault_observation_store, now=NOW + 4)
        output.update(breaker=worker.shared_breaker.view("local", "rate_limited").state,
            records=len(_facts(worker)))
    print(json.dumps(output))
