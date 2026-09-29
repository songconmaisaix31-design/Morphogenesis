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


def require_completed(worker, result, *, renewals=None):
    if result["state"] != "exhausted" or result["completed"] != 1:
        # pytest truncates rewritten assertion dictionaries; print the complete
        # safe runtime record as the failure message, including phase and fence.
        pytest.fail("worker did not complete:\n" + json.dumps(
            {"status": result, "audit": events(worker.config), "renewals": renewals},
            indent=2, ensure_ascii=True), pytrace=False)


def test_atomic_status_sharing_conflict_is_locally_bounded(tmp_path, monkeypatch):
    import os
    from swarm.worker_loop import _write_json
    destination = tmp_path / "status.json"
    destination.write_text('{"old":true}')
    original = os.replace
    calls = []
    def shared(source, target):
        calls.append(target)
        if len(calls) == 1:
            assert json.loads(destination.read_bytes()) == {"old": True}
            raise PermissionError("fixture file sharing")
        return original(source, target)
    monkeypatch.setattr(os, "replace", shared)
    _write_json(destination, {"completed": 1})
    assert len(calls) == 2 and json.loads(destination.read_bytes()) == {"completed": 1}
    calls.clear()
    def denied(source, target):
        calls.append(target)
        raise PermissionError("persistent fixture sharing")
    monkeypatch.setattr(os, "replace", denied)
    with pytest.raises(PermissionError):
        _write_json(destination, {"completed": 2})
    assert len(calls) == 3 and json.loads(destination.read_bytes()) == {"completed": 1}
    assert not list(tmp_path.glob("*.tmp"))


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
    assert events(config)[0]["outcome"] == "explicit_unbounded_admission_required"


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
    result = worker.run()
    assert result["state"] == "stopped"
    assert result["failure"]["failure_stage"] == "validate"
    assert result["failure"]["validation_reasons"] == ["fixed_expectation_failed"]
    report = worker.assets.reports()[0]
    assert not report.passed and Path(report.worktree_path).exists()
    assert worker.assets.state(report.asset_id) == "quarantined"
    assert worker.budget.snapshot().tokens == 2
    assert events(config)[0]["outcome"] == "quarantined"
    assert not worker.assets.promotions()
    assert worker.ledger.get(report.attempt.task_id).status == "available"
    assert all("return -1" in path.read_text() for path in config.target.rglob("task_*.py"))


def test_continue_on_rejection_processes_followup_tasks(tmp_path):
    config = configured(tmp_path, energy=2, continue_on_rejection=True)
    worker = Worker(config, WrongAnswer())
    result = worker.run()
    assert result["state"] == "exhausted"
    assert [event["outcome"] for event in events(config)] == ["quarantined", "quarantined"]
    assert not worker.assets.promotions()
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


def test_renewal_keeps_slow_local_execution_owned(tmp_path, monkeypatch):
    from threading import Event
    renewed = Event()
    clock = [time.time()]
    renewals = []
    class Slow(FixtureExecutor):
        def execute(self, *args, **kwargs):
            # Exercise three real SQLite renewals across more than the initial
            # TTL. A controlled ledger clock avoids equating CI scheduler delay
            # with failure of the renewal protocol.
            for _ in range(3):
                renewed.clear()
                clock[0] += 0.2
                assert renewed.wait(5), "renewal thread did not persist its next expiry"
            return super().execute(*args, **kwargs)
    config = configured(tmp_path, energy=1, lease_seconds=0.25)
    worker = Worker(config, Slow())
    clock[0] = time.time()
    monkeypatch.setattr(worker.ledger, "now", lambda: clock[0])
    original = worker.leases.renew
    def record(lease, **kwargs):
        result = original(lease, **kwargs)
        if result is not None:
            renewals.append((lease.expires_at, result.expires_at))
            renewed.set()
        return result
    monkeypatch.setattr(worker.leases, "renew", record)
    outcome = worker.run()
    require_completed(worker, outcome, renewals=renewals)
    assert sum(after > before for before, after in renewals) >= 3
    assert len(worker.assets.promotions()) == 1
    assert worker.leases.snapshot() == []


def test_real_wall_clock_renewal_outlives_initial_ttl(tmp_path, monkeypatch):
    renewed = []
    class Slow(FixtureExecutor):
        def execute(self, *args, **kwargs):
            time.sleep(2.5)
            return super().execute(*args, **kwargs)
    config = configured(tmp_path, energy=1, lease_seconds=2)
    worker = Worker(config, Slow())
    original = worker.leases.renew
    def record(lease, **kwargs):
        result = original(lease, **kwargs)
        if result is not None:
            renewed.append((lease.expires_at, result.expires_at))
        return result
    monkeypatch.setattr(worker.leases, "renew", record)
    result = worker.run()
    require_completed(worker, result, renewals=renewed)
    assert result["completed"] == 1 and len(renewed) >= 2
    assert all(new > old for old, new in renewed)
    assert len(worker.assets.promotions()) == 1 and worker.leases.snapshot() == []


def test_slow_submission_status_keeps_lease_alive(tmp_path, monkeypatch):
    """Durable status IO is preparation and must retain background renewal."""
    config = configured(tmp_path, energy=1, lease_seconds=2)
    worker = Worker(config)
    original = worker._status
    writes = []
    def delayed(state, reason=""):
        if state == "submitting":
            writes.append(worker._pending["lease"]["expires_at"])
            time.sleep(2.5)  # Longer than TTL, using real clock/SQLite/fencing.
        return original(state, reason)
    monkeypatch.setattr(worker, "_status", delayed)
    result = worker.run()
    require_completed(worker, result)
    assert len(writes) == 1
    audit = events(config)[0]
    task = worker.ledger.get(audit["task_id"])
    assert audit["lease"]["expires_at"] == task.expires_at > writes[0]
    assert len(worker.assets.promotions()) == 1 and worker.leases.snapshot() == []


def test_expiry_after_handoff_still_rejects_submit(tmp_path, monkeypatch):
    config = configured(tmp_path, energy=1, lease_seconds=2)
    worker = Worker(config)
    original = worker.leases.submit
    def expired(lease, *args, **kwargs):
        assert worker.leases.is_valid(lease)
        time.sleep(2.5)  # No renewal once short publication has taken ownership.
        return original(lease, *args, **kwargs)
    monkeypatch.setattr(worker.leases, "submit", expired)
    result = worker.run()
    assert result["state"] == "stopped"
    failure = result["failure"]
    assert failure["failure_stage"] == "submit"
    assert failure["failure_reason"] == "lease_expired_changed_or_fenced"
    facts = failure["lease_diagnostics"]
    assert facts["owner_matches"] and facts["expiry_matches"] and not facts["effect_applied"]
    assert facts["observed_at"] > facts["lease_expires_at"]
    assert not worker.assets.promotions()
    assert not any(event["outcome"] == "promoted" for event in events(config))
    assert all("return -1" in path.read_text() for path in config.target.rglob("task_*.py"))


def test_final_handoff_never_revives_expired_or_replaced_holder(tmp_path, monkeypatch):
    from swarm.worker_loop import _Renewal
    config = configured(tmp_path)
    worker = Worker(config)
    signal = worker.field.sense(config.locality)[0]
    old = worker.leases.acquire(signal.task_id, worker.worker_id, ttl_seconds=2, locality=config.locality)
    clock = old.expires_at + 0.01
    monkeypatch.setattr(worker.ledger, "now", lambda: clock)
    with pytest.raises(AssetSafetyError, match="stale_lease"):
        _Renewal(worker.leases, old, 2).handoff()
    successor = worker.leases.acquire(signal.task_id, "builder-9", ttl_seconds=2, locality=config.locality)
    assert successor.token > old.token
    with pytest.raises(AssetSafetyError, match="stale_lease"):
        _Renewal(worker.leases, old, 2).handoff()
    assert worker.leases.is_valid(successor)


def test_crash_after_submit_recovers_final_expiry_from_authority(tmp_path, monkeypatch):
    config = configured(tmp_path, energy=1, lease_seconds=2)
    worker = Worker(config)
    def crash():
        # No finalizing/stopped status is written: retain the actual pre-handoff
        # durable preparation record, as after loss of the process.
        raise SystemExit("fixture crash before finalization")
    monkeypatch.setattr(worker, "_finalize", crash)
    with pytest.raises(SystemExit):
        worker.run()
    pending = json.loads(worker.status_path.read_bytes())["pending_finalization"]
    task = worker.ledger.get(pending["lease"]["task_id"])
    assert task.status == "completed" and task.effect_applied
    assert pending["lease"]["expires_at"] < task.expires_at
    resumed = Worker(config, Unbounded())
    require_completed(resumed, resumed.run())
    promoted = [event for event in events(config) if event["outcome"] == "promoted"]
    assert len(promoted) == 1 and promoted[0]["lease"]["expires_at"] == task.expires_at
    assert resumed.ledger.get(task.signal.task_id).attempts == 1
    assert not resumed.executor.called and resumed.budget.snapshot().tokens == 2


def test_failure_diagnostics_exclude_exception_text(tmp_path):
    class SecretFailure(FixtureExecutor):
        def execute(self, *args, **kwargs):
            raise RuntimeError("Bearer private-fixture-credential /private/provider/response")
    config = configured(tmp_path, energy=1)
    result = Worker(config, SecretFailure()).run()
    failure = result["failure"]
    assert failure["failure_stage"] == "execute" and failure["failure_kind"] == "RuntimeError"
    assert failure["failure_reason"] == "exception_details_withheld"
    evidence = json.dumps({"result": result, "audit": events(config)})
    assert "private-fixture-credential" not in evidence and "/private/provider" not in evidence


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
