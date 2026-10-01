"""Real side-channel IO/ledger recovery boundaries; no model or science calls."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

import pytest

import orchestration.fc_logging as fc
from orchestration.rehearsal_models import RehearsalSnapshot
from swarm.fc_projection import read_projection, rebuild_projection
from swarm.worker_loop import Worker
from tests.swarm.test_failure_chain_runtime import _claim, _executor, _failure, _worker_config


def routed(tmp_path):
    worker = Worker(_worker_config(tmp_path, prices=True))
    worker.router.choose(worker.worker_id, worker.config.locality, worker.config.capabilities)
    _claim(worker)
    return worker


def writer_for(worker, directory):
    return fc.FCLogWriter(directory, worker.config.swarm_id, provenance="mock")


def test_failed_ledger_append_stops_before_cursor_and_explicit_rebuild_is_readonly(tmp_path):
    worker = routed(tmp_path)
    writer = worker.fc_log
    failed_sequence = next(row["sequence"] for row in worker.ledger.audit(limit=10000)
                           if row["event"] == "routing")
    writer.path.parent.mkdir(parents=True)
    lock = writer.path.with_name(writer.path.name + ".lock.sqlite3")
    # Actual lock exhaustion, not an emit stub. No authoritative task retry.
    with fc.connection(lock, write=True):
        writer.observe_ledger(worker.ledger, worker.worker_id)
    state = writer.projection_status()
    assert state["state"] == "incomplete" and state["ledger_cursor"] < failed_sequence
    assert state["failure_count"] == 1
    writer.observe_ledger(worker.ledger, worker.worker_id)
    assert not writer.path.exists() and writer.failure_count == 1
    before = worker.ledger.audit(limit=10000)
    destination = writer_for(worker, tmp_path / "reconstructed")
    result = rebuild_projection((), destination, worker.ledger, worker.worker_id)
    assert result["state"] == "available"
    records = read_projection(destination.path).records
    assert {record["event"] for record in records} == {"routing", "claim"}
    assert [record["sequence"] for record in records] == sorted(record["sequence"] for record in records)
    assert worker.ledger.audit(limit=10000) == before
    assert writer.projection_status()["state"] == "incomplete"  # Never relabel the failed original.
    with pytest.raises(ValueError, match="new_destination"):
        rebuild_projection((), destination, worker.ledger, worker.worker_id)


def test_fsync_unknown_write_is_not_implicitly_repeated(tmp_path, monkeypatch):
    worker = routed(tmp_path)
    failed_sequence = next(row["sequence"] for row in worker.ledger.audit(limit=10000)
                           if row["event"] == "routing")
    calls = []

    def failed(fd):
        calls.append(fd)
        raise OSError("private exception text must not enter status")

    monkeypatch.setattr(fc.os, "fsync", failed)
    worker.fc_log.observe_ledger(worker.ledger, worker.worker_id)
    before = worker.fc_log.path.read_bytes()
    worker.fc_log.observe_ledger(worker.ledger, worker.worker_id)
    assert len(calls) == 1 and worker.fc_log.path.read_bytes() == before
    state = worker.fc_log.projection_status()
    assert state["state"] == "incomplete" and state["ledger_cursor"] < failed_sequence
    assert "private exception" not in json.dumps(state)


def test_concurrent_observers_do_not_duplicate_source_ordinals(tmp_path):
    worker = routed(tmp_path)
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(lambda _: worker.fc_log.observe_ledger(worker.ledger, worker.worker_id), range(3)))
    view = read_projection(worker.fc_log.path)
    assert view.state == "available"
    sequences = [record["sequence"] for record in view.records]
    assert len(sequences) == len(set(sequences)) == 2
    assert worker.fc_log.projection_status()["failure_count"] == 0


def test_missing_ledger_read_is_incomplete_and_does_not_create_a_ledger(tmp_path):
    worker = routed(tmp_path)
    worker.ledger.path.rename(tmp_path / "retained-ledger.sqlite3")
    worker.fc_log.observe_ledger(worker.ledger, worker.worker_id)
    assert not worker.ledger.path.exists()
    assert worker.fc_log.projection_status()["state"] == "incomplete"
    assert worker.fc_log.failure_count == 1


def test_partial_source_is_retained_and_bounded_rebuild_never_calls_executor(tmp_path):
    worker = routed(tmp_path)
    worker.fc_log.path.parent.mkdir(parents=True)
    worker.fc_log.path.write_bytes(b'{"partial":')
    worker.fc_log.observe_ledger(worker.ledger, worker.worker_id)
    original = worker.fc_log.path.read_bytes()
    view = read_projection(worker.fc_log.path)
    assert view.state == "incomplete" and "invalid_record" in view.reasons
    assert len(view.records) == 2 and original.startswith(b'{"partial":\n')
    before = worker.ledger.audit(limit=10000)
    recovered = writer_for(worker, tmp_path / "new-projection")
    result = rebuild_projection((worker.fc_log.path,), recovered, worker.ledger, worker.worker_id)
    assert result["state"] == "incomplete" and result["reasons"] == ["invalid_record"]
    assert read_projection(recovered.path).records == view.records
    assert worker.fc_log.path.read_bytes() == original and worker.ledger.audit(limit=10000) == before
    assert read_projection(worker.fc_log.path, limit=1).state == "incomplete"


def test_changed_snapshot_and_unreadable_file_are_incomplete(tmp_path, monkeypatch):
    worker = routed(tmp_path)
    worker.fc_log.observe_ledger(worker.ledger, worker.worker_id)
    import swarm.fc_projection as projection

    real_stamp = projection._stamp
    count = 0

    def changed(path):
        nonlocal count
        count += 1
        stamp = real_stamp(path)
        return stamp if count == 1 else (stamp[0], stamp[1] + 1, stamp[2])

    monkeypatch.setattr(projection, "_stamp", changed)
    view = read_projection(worker.fc_log.path)
    assert view.records == [] and view.reasons == ("changed_during_observation",)
    assert read_projection(tmp_path).reasons == ("read_failed",)


def test_all_six_existing_fact_kinds_survive_rebuild_without_reexecuting(tmp_path):
    first, later = _executor(result=_failure(known_usage=True)), _executor()
    worker = Worker(_worker_config(tmp_path, prices=True), first, candidates=[first, later])
    worker.router.choose(worker.worker_id, worker.config.locality, worker.config.capabilities)
    signal, lease = _claim(worker)
    assert worker._process(signal, lease) == "completed"
    # Existing presentation contract, explicitly mock; no completion evidence is manufactured.
    snapshot = RehearsalSnapshot(
        sequence=0, stage="task_ready", at=123.5, task_id=signal.task_id, task_description="fixture",
        provenance="mock", acceptance={"provenance": "mock"}, members=[], pipes=[],
        routing={"task_id": signal.task_id, "eligible_members": []}, tau_seconds=86400,
        archive_threshold=0.1, model_calls_started=0,
    )
    worker.fc_log.append("rehearsal", task_id=signal.task_id, at=123.5, rehearsal=snapshot)
    before = read_projection(worker.fc_log.path).records
    assert {record["event"] for record in before} == {
        "task", "asset_call", "routing", "claim", "fault_observation", "rehearsal"}
    calls = (first.execute.call_count, later.execute.call_count)
    ledger = worker.ledger.audit(limit=10000)
    destination = writer_for(worker, tmp_path / "six-facts")
    result = rebuild_projection((worker.fc_log.path,), destination, worker.ledger, worker.worker_id)
    after = read_projection(destination.path).records
    assert result["state"] == "available" and after == before
    assert (first.execute.call_count, later.execute.call_count) == calls == (1, 1)
    assert worker.ledger.audit(limit=10000) == ledger


def test_rebuild_write_failure_and_source_mismatch_never_become_success(tmp_path, monkeypatch):
    worker = routed(tmp_path)
    worker.fc_log.observe_ledger(worker.ledger, worker.worker_id)
    destination = writer_for(worker, tmp_path / "denied-output")
    with pytest.raises(ValueError, match="source_mismatch"):
        rebuild_projection((worker.fc_log.path,), fc.FCLogWriter(
            tmp_path / "wrong", worker.config.swarm_id, provenance="live"), worker.ledger, worker.worker_id)
    calls = []

    def denied(fd):
        calls.append(fd)
        raise OSError("credential-shaped api_key=private must not enter summary")

    monkeypatch.setattr(fc.os, "fsync", denied)
    result = rebuild_projection((worker.fc_log.path,), destination, worker.ledger, worker.worker_id)
    assert result["state"] == "incomplete" and result["reasons"] == ["write_failed"]
    assert len(calls) == 1 and result["written"] == 0
    assert "private" not in json.dumps(result)
