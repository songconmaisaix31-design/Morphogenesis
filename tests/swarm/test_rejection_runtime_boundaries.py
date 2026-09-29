"""Real HTTP adapter -> executor -> Worker -> durable ledger boundary checks.

Only httpx's explicit mock transport is substituted. Wrapping mocks count real
executor calls; no live subprocess is intercepted and no usage is fabricated.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from unittest.mock import Mock

import httpx
import pytest

from swarm.breaker import SharedBreaker
from swarm.cli import EvoMapRun, evomap_worker_config, seed_evomap
from swarm.evomap_executor import EvoMapConfig, EvoMapExecutor
from swarm.failure_chain import guard_provider
from swarm.fault_observations import FaultObservation, FaultObservationStore
from swarm.pheromone import PheromoneField
from swarm.task_ledger import TaskLedger
from swarm.worker_loop import Worker, WorkerConfig
from tests.orchestration.test_rejection_classification_boundaries import ERRORS, error_body
from tests.swarm.test_failure_chain_runtime import _claim, _config, _events, _facts, _reservations


def _gateway_worker(tmp_path, response_factory):
    config = EvoMapRun(
        directory=tmp_path / "data",
        api=EvoMapConfig(credential_file=tmp_path / "unused-mock-key"),
        budget={"max_cost_usd": 2, "unbounded_reservation_usd": 0.2,
                "limits": {"max_tasks": 6, "max_attempts": 6, "max_attempts_per_task": 1,
                           "max_derived_tasks": 0, "max_runtime_seconds": 300}},
    )
    seed_evomap(config)
    first_transport = Mock(side_effect=response_factory)
    later_transport = Mock(side_effect=lambda request: httpx.Response(429, json={"error": "rate limited"}))
    executors = []
    for handler in (first_transport, later_transport):
        real = EvoMapExecutor(config.api, transport=httpx.MockTransport(handler), provenance="mock")
        wrapped = Mock(spec_set=EvoMapExecutor, wraps=real)
        wrapped.provenance = real.provenance
        wrapped.usage_source = real.usage_source
        wrapped.original_run_uri = real.original_run_uri
        executors.append(wrapped)
    seeded = WorkerConfig.model_validate_json(evomap_worker_config(config, 0))
    # The EvoMap demo CLI deliberately permits one request. The production
    # Worker chain accepts immutable multi-attempt limits in a separate run.
    values = seeded.model_dump()
    values["state"] = tmp_path / "chain-state"
    values["budget"]["limits"]["max_attempts_per_task"] = 10
    worker_config = WorkerConfig.model_validate(values)
    ledger = TaskLedger(worker_config.state / "tasks.sqlite3", worker_config.swarm_id,
                        limits=worker_config.budget.limits)
    field = PheromoneField(worker_config.state / "field.sqlite3", ledger=ledger)
    for task in TaskLedger(seeded.state / "tasks.sqlite3", seeded.swarm_id).snapshot():
        ledger.enqueue(task.signal, acceptance=task.acceptance)
        field.deposit(task.signal)
    worker = Worker(worker_config, executors[0], candidates=executors, breaker_config=_config())
    return worker, executors, (first_transport, later_transport)


@pytest.mark.parametrize("status", [500, 502, 503, 504])
@pytest.mark.parametrize("code,message", ERRORS)
def test_gateway_server_error_stops_real_worker_chain(tmp_path, capsys, status, code, message):
    body = error_body("evomap", code, message).encode()
    worker, (first, later), transports = _gateway_worker(
        tmp_path, lambda request: httpx.Response(status, content=body, headers={"Retry-After": "17"}))
    signal, lease = _claim(worker, "data-0")
    outcome = worker._process(signal, lease)

    # Behavioral assertions are outside Worker._process's exception handler.
    assert later.execute.call_count == 0
    assert first.execute.call_count == transports[0].call_count == 1
    assert transports[1].call_count == later.bound.call_count == 0
    assert outcome == "sleeping", _events(worker)
    row, = _reservations(worker)
    assert row["status"] == "uncertain" and row["cost"] == "unknown"
    assert row["tokens"] is row["admitted_usd"] is row["estimate_usd"] is None
    assert row["reserved_usd"] == 0.2
    fact, = _facts(worker)
    assert fact.failure_class == "unknown_effect" and fact.normalized_reason == f"http_{status}"
    assert fact.switched_to is None and fact.cost_state == "unknown"
    assert fact.evidence_ref == hashlib.sha256(body).hexdigest()
    assert fact.retry_after_seconds == 17.0
    assert worker.ledger.get(signal.task_id).result_id is None
    assert not worker.assets.promotions()
    snapshot = worker.budget.snapshot()
    assert snapshot.reserved_estimate_usd == 0.2
    assert snapshot.tokens is snapshot.actual_cost_usd is snapshot.estimated_cost_usd is None
    event, = _events(worker)
    assert event["interface_live"] == event["task_live"] == "not_run"
    persisted = b"".join(path.read_bytes() for path in worker.state.rglob("*.json"))
    captured = capsys.readouterr()
    assert body not in persisted and message not in captured.out + captured.err
    assert b"fixture-only-not-a-real-key" not in persisted


@pytest.mark.parametrize("status,body", [
    (400, error_body("evomap", "Arrearage", "Account has outstanding balance")),
    (403, error_body("evomap", "AllocationQuota.FreeTierOnly", "免费配额已耗尽")),
    (429, '{"error":"too many requests"}'),
    (400, "bad request"),
])
def test_confirmed_rejection_still_admits_exactly_one_later_request(tmp_path, status, body):
    worker, executors, transports = _gateway_worker(
        tmp_path, lambda request: httpx.Response(status, text=body))
    signal, lease = _claim(worker, "data-0")
    outcome = worker._process(signal, lease)

    assert [executor.execute.call_count for executor in executors] == [1, 1]
    assert [transport.call_count for transport in transports] == [1, 1]
    assert outcome == "rejected", _events(worker)
    rows = _reservations(worker)
    assert len(rows) == 2 and {row["task_id"] for row in rows} == {signal.task_id}
    assert all(row["status"] == "uncertain" and row["tokens"] is None and row["cost"] == "unknown" for row in rows)
    assert worker.budget.snapshot().reserved_estimate_usd == 0.4
    first, final = _facts(worker)
    assert first.failure_class == final.failure_class == "confirmed_rejection"
    next_bound = json.loads(rows[1]["body"])["bound"]
    assert first.switched_to == f"{next_bound['provider']}:{next_bound['model']}"
    assert final.switched_to is None


class _InterruptedBody(httpx.SyncByteStream):
    def __iter__(self):
        yield error_body("evomap", "Arrearage", "账户欠费 account balance").encode()
        raise httpx.ReadTimeout("billing quota exceeded")


@pytest.mark.parametrize("fault", ["connect", "partial_400", "partial_503"])
def test_transport_unknown_overrides_even_received_rejection_body(tmp_path, fault):
    def handle(request):
        if fault == "connect":
            raise httpx.ConnectError("Arrearage account balance", request=request)
        return httpx.Response(400 if fault == "partial_400" else 503, stream=_InterruptedBody())

    worker, (first, later), transports = _gateway_worker(tmp_path, handle)
    signal, lease = _claim(worker, "data-0")
    outcome = worker._process(signal, lease)

    assert first.execute.call_count == transports[0].call_count == 1
    assert later.execute.call_count == transports[1].call_count == 0
    assert outcome == "sleeping", _events(worker)
    fact, = _facts(worker)
    assert fact.failure_class == "unknown_effect" and fact.switched_to is None
    row, = _reservations(worker)
    assert row["status"] == "uncertain" and row["tokens"] is None
    assert worker.budget.snapshot().reserved_estimate_usd == 0.2


@pytest.mark.parametrize("next_owner", ["old-owner", "new-owner"])
def test_guard_reclaims_expired_probe_with_fresh_fenced_token(tmp_path, next_owner):
    store = FaultObservationStore(tmp_path / "faults.jsonl", "probe-run")
    store.append(FaultObservation.model_validate({"run_id": "probe-run", "task_id": "task", "request_id": "request", "attempt": 0,
                  "provider": "evomap", "model": "fixture", "failure_class": "confirmed_rejection",
                  "normalized_reason": "billing_arrearage", "occurred_at": 1000.0}))
    path = tmp_path / "breaker.sqlite3"
    breaker = SharedBreaker(path, "probe-run", _config())
    breaker.observe(store, now=1000.0)
    old = breaker.try_claim_probe("evomap", "billing_arrearage", "old-owner", now=1300.0)
    assert old is not None
    live = guard_provider(breaker, "evomap", "old-owner", now=1329.0)
    assert live.routable and live.claims[0].token == old.probe_token
    assert not guard_provider(breaker, "evomap", "other", now=1329.0).routable

    recovered = guard_provider(SharedBreaker(path, "probe-run", _config()), "evomap", next_owner, now=1330.0)

    assert recovered.routable
    fresh, = recovered.claims
    assert fresh.token > old.probe_token
    assert breaker.view("evomap", "billing_arrearage").probe_token == fresh.token
    assert not breaker.report_probe_success("evomap", "billing_arrearage", "old-owner", probe_token=old.probe_token, now=1331.0)
    assert breaker.report_probe_success("evomap", "billing_arrearage", next_owner, probe_token=fresh.token, now=1331.0)


def test_guard_expired_probe_has_one_concurrent_winner(tmp_path):
    store = FaultObservationStore(tmp_path / "faults.jsonl", "probe-race")
    store.append(FaultObservation.model_validate({"run_id": "probe-race", "task_id": "task", "request_id": "request", "attempt": 0,
                  "provider": "evomap", "model": "fixture", "failure_class": "confirmed_rejection",
                  "normalized_reason": "billing_arrearage", "occurred_at": 1000.0}))
    path = tmp_path / "breaker.sqlite3"
    breaker = SharedBreaker(path, "probe-race", _config())
    breaker.observe(store, now=1000.0)
    old = breaker.try_claim_probe("evomap", "billing_arrearage", "old-owner", now=1300.0)
    assert old is not None
    peers = [SharedBreaker(path, "probe-race", _config()) for _ in range(2)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(guard_provider, peer, "evomap", f"worker-{i}", now=1330.0)
                   for i, peer in enumerate(peers)]
        results = [future.result() for future in futures]
    assert sum(result.routable for result in results) == 1
    winner, = [result for result in results if result.routable]
    assert winner.claims[0].token == old.probe_token + 1
