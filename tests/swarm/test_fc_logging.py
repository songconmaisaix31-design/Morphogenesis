"""Independent frozen-schema checks and real Worker entrypoint evidence (mock).

No live subprocess interception. Fixture executors are the existing local file
transformation; unknown usage/cost remains unknown in both source and projection.
"""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from functools import lru_cache
from importlib.resources import files
import json
from pathlib import Path
import sqlite3

from jsonschema import Draft202012Validator
import pytest

from orchestration.fc_logging import FCLogWriter, validate_event
from swarm.worker_loop import FixtureExecutor, Worker
from tests.swarm.test_failure_chain_runtime import (
    _claim, _executor, _facts, _failure, _reservations, _worker_config,
)
from tests.swarm.test_worker_runtime import enqueue

@lru_cache(maxsize=1)
def frozen_json():
    return files("orchestration").joinpath("fc_log_schema.json").read_bytes()


def read_events(path):
    records = [json.loads(line) for line in path.read_bytes().splitlines()]
    validator = Draft202012Validator(json.loads(frozen_json()))
    for record in records:
        validator.validate(record)
        validate_event(record)
    return records


def test_packaged_schema_exists_and_is_valid():
    packaged = files("orchestration").joinpath("fc_log_schema.json")
    assert packaged.is_file()
    source = packaged.read_bytes()
    assert source.strip()
    Draft202012Validator.check_schema(json.loads(source))


def task(writer, **facts):
    writer.append("task", task_id="t", at=123.5,
                  dag_node={"task_id": "t", "dependencies": [], "status": "available"}, **facts)


@pytest.mark.parametrize("audit", [{}, {"audit_confirmed_issue_events": None},
                                   {"audit_confirmed_issue_events": None, "issue_audit": None}])
def test_uncollected_audit_is_optional_nullable(tmp_path, audit):
    writer = FCLogWriter(tmp_path, "r", provenance="mock")
    task(writer, **audit)
    record, = read_events(writer.path)
    assert record.get("audit_confirmed_issue_events") is None
    assert record["duration_seconds"] is None


@pytest.mark.parametrize("mutation", [
    {"schema_version": "1.1.0"}, {"drill": True, "provenance": "live", "evidence_label": "LIVE"},
    {"provenance": "replay", "evidence_label": "REPLAY", "original_run_uri": None},
    {"audit_confirmed_issue_events": -1}, {"audit_confirmed_issue_events": 0},
    {"audit_confirmed_issue_events": 1}, {"event": "asset_call", "asset_calls": []},
    {"event": "fault_observation", "fault_observation": None},
    {"dag_node": {"task_id": "other", "dependencies": [], "status": "available"}},
])
def test_invalid_records_still_rejected(tmp_path, mutation):
    writer = FCLogWriter(tmp_path, "r", provenance="mock")
    task(writer)
    record, = read_events(writer.path)
    with pytest.raises(Exception):
        validate_event(record | mutation)


def test_audit_counts_require_matching_complete_evidence(tmp_path):
    writer = FCLogWriter(tmp_path, "r", provenance="mock")
    audit = dict(status="complete", protocol_id="review-1", scope="r/mock/t", reviewer="reviewer",
                 confirmed_issue_ids=[], evidence_refs=["file:///review.txt"])
    task(writer, audit_confirmed_issue_events=0, issue_audit=audit)
    record, = read_events(writer.path)
    validator = Draft202012Validator(json.loads(frozen_json()))
    for invalid in [record | {"issue_audit": audit | {"status": "partial"}},
                    record | {"audit_confirmed_issue_events": None},
                    record | {"issue_audit": audit | {"evidence_refs": []}}]:
        assert not validator.is_valid(invalid)
    with pytest.raises(ValueError, match="fc_audit_count_mismatch"):
        validate_event(record | {"audit_confirmed_issue_events": 2,
                                "issue_audit": audit | {"confirmed_issue_ids": ["issue-1"]}})


@pytest.mark.parametrize("number", [float("nan"), float("inf")])
def test_nonfinite_numbers_cannot_be_serialized_as_unknown(tmp_path, number):
    writer = FCLogWriter(tmp_path, "r", provenance="mock")
    with pytest.raises(Exception):
        writer.append("task", task_id="t", at=number,
                      dag_node={"task_id": "t", "dependencies": [], "status": "available"})
    assert not writer.path.exists()


def test_drill_live_replay_partition_and_origin(tmp_path):
    writers = [FCLogWriter(tmp_path, "r", provenance="mock", drill=True),
               FCLogWriter(tmp_path, "r", provenance="live"),
               FCLogWriter(tmp_path, "r", provenance="replay", original_run_uri="file:///original/run.json")]
    for writer in writers:
        task(writer)
    assert len({writer.path for writer in writers}) == 3
    assert read_events(writers[0].path)[0]["drill"] is True
    assert read_events(writers[1].path)[0]["evidence_label"] == "LIVE"
    assert read_events(writers[2].path)[0]["original_run_uri"] == "file:///original/run.json"
    with pytest.raises(Exception):
        task(FCLogWriter(tmp_path, "r", provenance="live", drill=True))


def test_writer_rejects_credentials_and_protected_or_linked_destinations(tmp_path, caplog):
    writer = FCLogWriter(tmp_path, "Bearer very-private", provenance="mock")
    assert writer.emit("task", task_id="t", at=1,
                       dag_node={"task_id": "t", "dependencies": [], "status": "available"}) is False
    assert "very-private" not in caplog.text
    assert "fc_log_projection_failed" in caplog.text
    assert not writer.path.exists()
    source = Path(__file__).resolve().parents[2]
    with pytest.raises(ValueError, match="protected_runtime_state"):
        task(FCLogWriter(source / ".runtime", "r", provenance="mock"))
    writer = FCLogWriter(tmp_path, "r", provenance="mock")
    writer.path.parent.mkdir(parents=True)
    private = tmp_path / "private"
    private.write_bytes(b"do not modify")
    writer.path.hardlink_to(private)
    with pytest.raises(Exception):
        task(writer)
    assert private.read_bytes() == b"do not modify"


def test_concurrent_append_and_partial_tail_preserve_facts(tmp_path):
    writer = FCLogWriter(tmp_path, "r", provenance="mock")
    writer.path.parent.mkdir(parents=True)
    writer.path.write_bytes(b'{"incomplete":')
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(lambda _: task(FCLogWriter(tmp_path, "r", provenance="mock")), range(6)))
    lines = writer.path.read_bytes().splitlines()
    assert lines[0] == b'{"incomplete":'
    assert len(lines) == 7
    records = [json.loads(line) for line in lines[1:]]
    assert [record["sequence"] for record in records] == list(range(1, 7))
    for record in records:
        validate_event(record)


def test_worker_run_projects_real_route_claim_assets_and_dag(tmp_path):
    config = _worker_config(tmp_path, prices=True)
    executor = _executor()
    worker = Worker(config, executor)
    worker.run()
    records = read_events(worker.fc_log.path)
    assert {record["event"] for record in records} >= {"routing", "claim", "asset_call", "task"}
    audit = {row["sequence"]: row for row in worker.ledger.audit(limit=10000)}
    routes = [record for record in records if record["event"] == "routing"]
    for record in routes:
        source = audit[record["sequence"]]
        assert record["at"] == source["at"]
        assert record["routing"]["selected"] == source["body"]["selected"]
        assert record["routing"]["candidates"] == [dict(signal, probability=probability) for signal, probability
            in zip(source["body"]["signals"], source["body"]["probabilities"], strict=True)]
    claims = [record for record in records if record["event"] == "claim"]
    assert {record["claim"]["outcome"] for record in claims} >= {"claimed", "submitted"}
    for record in claims:
        source = audit[record["sequence"]]
        assert record["at"] == source["at"] and record["claim"]["token"] == source["body"]["token"]
    assets = [call for record in records for call in record["asset_calls"]]
    assert {call["operation"] for call in assets} >= {"validate", "apply"}
    for call in assets:
        assert call["duration_seconds"] > 0
        assert call["outcome"] == "succeeded"
        worker.assets.fetch(call["asset_id"])
    tasks = [record for record in records if record["event"] == "task"]
    assert tasks and all(record["duration_seconds"] > 0 for record in tasks)
    for record in tasks:
        source = worker.ledger.get(record["task_id"])
        assert record["dag_node"]["dependencies"] == list(source.dependencies)
        assert record["dag_node"]["status"] == source.status == "completed"
    assert all(record["provenance"] == "mock" and record["evidence_label"] == "SIMULATED" for record in records)
    assert all("audit_confirmed_issue_events" not in record for record in records)


@pytest.mark.parametrize("known_usage", [False, True])
def test_process_fault_projection_preserves_all_fourteen_fields_and_hold(tmp_path, known_usage):
    config = _worker_config(tmp_path, prices=known_usage)
    first = _executor(result=_failure("unknown_effect", known_usage=known_usage))
    later = _executor()
    writer = FCLogWriter(tmp_path / "drill", config.swarm_id, provenance="mock", drill=True)
    worker = Worker(config, first, candidates=[first, later], fc_log=writer)
    signal, lease = _claim(worker)
    assert worker._process(signal, lease) == "sleeping"
    records = read_events(writer.path)
    fault, = [record for record in records if record["event"] == "fault_observation"]
    source, = _facts(worker)
    assert len(fault["fault_observation"]) == 14
    assert fault["fault_observation"] == source.model_dump(mode="json")
    assert fault["at"] == source.occurred_at and fault["duration_seconds"] is None
    assert source.cost_state == ("settled" if known_usage else "unknown")
    assert source.switched_to is None and later.execute.call_count == 0
    reservation, = _reservations(worker)
    assert reservation["tokens"] == (2 if known_usage else None)
    if not known_usage:
        assert reservation["status"] == "uncertain" and reservation["reserved_usd"] > 0
    assert all(record["drill"] and record["provenance"] == "mock" for record in records)
    assert not (writer.root / "fc-logs/runtime").exists()


def test_log_io_failure_cannot_repeat_send_or_replace_completed_fact(tmp_path, caplog):
    config = _worker_config(tmp_path, prices=True)
    executor = _executor()
    worker = Worker(config, executor)
    # Real filesystem failure, not a patched Worker/control path.
    (worker.state / "fc-logs").write_text("occupied")
    signal, lease = _claim(worker)
    assert worker._process(signal, lease) == "completed"
    assert executor.execute.call_count == 1
    assert worker.ledger.get(signal.task_id).status == "completed"
    reservation, = _reservations(worker)
    assert reservation["status"] == "settled" and reservation["tokens"] == 2
    assert worker.assets.promotions()
    assert "fc_log_projection_failed" in caplog.text


def test_real_asset_injection_and_adoption_are_distinct_calls(tmp_path):
    config = _worker_config(tmp_path, prices=True)
    worker = Worker(config)
    source_signal, source_lease = _claim(worker)
    assert worker._process(source_signal, source_lease) == "completed"
    source = worker.ledger.get(source_signal.task_id)
    asset = worker.assets.fetch(source.result["candidate_asset_id"])
    followup = enqueue(worker, task_id="actual-reuse", scope="module_0", path="module_0/copy.py",
                       before=None, after=asset.changes[0].after, dependencies=(source_signal.task_id,),
                       payload={"reuse_task_id": source_signal.task_id,
                                "path_map": {asset.changes[0].path: "module_0/copy.py"}})
    signal, lease = _claim(worker, followup.task_id)
    assert worker._process(signal, lease) == "completed"
    records = read_events(worker.fc_log.path)
    calls = [call for record in records if record["task_id"] == followup.task_id for call in record["asset_calls"]]
    assert [call["operation"] for call in calls] == ["inject", "validate", "apply", "adopt"]
    assert calls[0]["asset_id"] == calls[-1]["asset_id"] == source.result["candidate_asset_id"]
    assert all(call["outcome"] == "succeeded" for call in calls)
    record = next(record for record in records if record["event"] == "task" and record["task_id"] == followup.task_id)
    assert record["dag_node"]["dependencies"] == [source_signal.task_id]


@pytest.mark.parametrize("origin", ["file:///recorded-fixture/run.json", "https://example.org/original/run"])
def test_task_snapshot_preserves_last_admitted_candidate_source(tmp_path, origin):
    class ReplayFixture(FixtureExecutor):
        provenance = "replay"
        usage_source = "replay"
        original_run_uri = origin

        def execute(self, *args, **kwargs):
            return replace(super().execute(*args, **kwargs), provenance=self.provenance,
                           usage_source=self.usage_source, original_run_uri=self.original_run_uri)

    config = _worker_config(tmp_path, prices=True)
    first = _executor(result=_failure(known_usage=True))
    worker = Worker(config, first, candidates=[first, ReplayFixture()])
    signal, lease = _claim(worker)
    assert worker._process(signal, lease) == "completed"
    assert worker.ledger.get(signal.task_id).result["provenance"] == "replay"
    mock_records = read_events(worker.fc_log.path)
    replay_records = read_events(worker.fc_log.root / "fc-logs/runtime/replay/events.jsonl")
    assert any(record["event"] == "fault_observation" for record in mock_records)
    assert not any(record["event"] == "task" for record in mock_records)
    task_record, = [record for record in replay_records if record["event"] == "task"]
    assert task_record["provenance"] == "replay" and task_record["original_run_uri"] == origin
    assert all(record["provenance"] == "replay" and record["original_run_uri"] == origin for record in replay_records)
    assert worker.fc_log.failure_count == 0


def test_foreign_ledger_worker_claims_are_not_projected(tmp_path):
    config = _worker_config(tmp_path, prices=True)
    worker = Worker(config)
    signal, lease = _claim(worker)
    with sqlite3.connect(worker.ledger.path) as db:
        db.execute("UPDATE task_attempts SET worker_id='other' WHERE token=?", (lease.token,))
    worker.fc_log.observe_ledger(worker.ledger, worker.worker_id)
    assert not worker.fc_log.path.exists()


def test_append_real_sqlite_rejection_preserves_partial_tail(tmp_path, monkeypatch):
    import orchestration.fc_logging as fc

    writer = FCLogWriter(tmp_path, "lock", provenance="mock")
    writer.path.parent.mkdir(parents=True)
    original = b'{"incomplete":'
    writer.path.write_bytes(original)
    lock = writer.path.with_name(writer.path.name + ".lock.sqlite3")
    real_connection = fc.connection
    calls = []

    def recorded(path, **kwargs):
        calls.append(kwargs)
        return real_connection(path, **kwargs)

    monkeypatch.setattr(fc, "connection", recorded)
    with real_connection(lock, write=True):
        with pytest.raises(sqlite3.OperationalError, match="database is locked"):
            task(writer)
    assert calls == [{"write": True, "timeout": fc.APPEND_LOCK_TIMEOUT_SECONDS}]
    assert writer.path.read_bytes() == original


def test_append_rechecks_native_hardlink_after_preflight(tmp_path, monkeypatch):
    from contextlib import contextmanager

    from local_assets.models import AssetSafetyError
    import orchestration.fc_logging as fc

    writer = FCLogWriter(tmp_path, "recheck", provenance="mock")
    writer.path.parent.mkdir(parents=True)
    original = b'{"incomplete":'
    writer.path.write_bytes(original)
    linked = tmp_path / "linked"
    real_connection = fc.connection
    calls = []

    @contextmanager
    def changed(path, **kwargs):
        calls.append(kwargs)
        with real_connection(path, **kwargs) as db:
            linked.hardlink_to(writer.path)
            yield db

    monkeypatch.setattr(fc, "connection", changed)
    with pytest.raises(AssetSafetyError, match="hardlinked_path"):
        task(writer)
    assert calls == [{"write": True, "timeout": fc.APPEND_LOCK_TIMEOUT_SECONDS}]
    assert writer.path.read_bytes() == linked.read_bytes() == original


def test_contended_append_waits_for_real_sqlite_lock(tmp_path, monkeypatch):
    from contextlib import contextmanager
    from threading import Barrier, local
    import time

    import orchestration.fc_logging as fc

    # Warm schema validation separately; every contender then reaches real BEGIN.
    task(FCLogWriter(tmp_path / "warm", "warm", provenance="mock"))
    writers = [FCLogWriter(tmp_path, "r", provenance="mock") for _ in range(3)]
    path = writers[0].path
    path.parent.mkdir(parents=True)
    path.write_bytes(b'{"incomplete":')
    lock = path.with_name(path.name + ".lock.sqlite3")
    real_connection = fc.connection
    entered = Barrier(4)
    thread = local()

    @contextmanager
    def coordinated(path, **kwargs):
        if not getattr(thread, "entered", False):
            thread.entered = True
            entered.wait(timeout=5)
        with real_connection(path, **kwargs) as db:
            yield db

    def append_two(writer):
        task(writer)
        task(writer)

    monkeypatch.setattr(fc, "connection", coordinated)
    with ThreadPoolExecutor(max_workers=3) as pool:
        with real_connection(lock, write=True):
            futures = [pool.submit(append_two, writer) for writer in writers]
            entered.wait(timeout=5)
            time.sleep(0.2)
        for future in futures:
            future.result(timeout=5)

    lines = path.read_bytes().splitlines()
    assert lines[0] == b'{"incomplete":'
    assert len(lines) == 7
    records = [json.loads(line) for line in lines[1:]]
    assert [record["sequence"] for record in records] == list(range(1, 7))
    for record in records:
        validate_event(record)
    assert all(writer.failure_count == 0 for writer in writers)


def test_process_writers_share_real_sqlite_append_lock(tmp_path):
    import subprocess
    import sys
    import time

    from swarm.task_ledger import connection

    writer = FCLogWriter(tmp_path, "r", provenance="mock")
    writer.path.parent.mkdir(parents=True)
    writer.path.write_bytes(b'{"incomplete":')
    lock = writer.path.with_name(writer.path.name + ".lock.sqlite3")
    script = """
import os
from pathlib import Path
import sys
from orchestration.fc_logging import FCLogWriter
root = Path(sys.argv[1])
def append(writer):
    writer.append("task", task_id="t", at=123.5,
                  dag_node={"task_id": "t", "dependencies": [], "status": "available"})
append(FCLogWriter(root / str(os.getpid()), "warm", provenance="mock"))
writer = FCLogWriter(root, "r", provenance="mock")
print("READY", flush=True)
assert sys.stdin.readline().strip() == "GO"
for _ in range(3):
    append(writer)
print("DONE", writer.failure_count, flush=True)
"""
    processes = []
    pool = ThreadPoolExecutor(max_workers=2)
    try:
        for _ in range(2):
            processes.append(subprocess.Popen(
                [sys.executable, "-I", "-c", script, str(tmp_path)], shell=False,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            ))
        ready = [pool.submit(process.stdout.readline) for process in processes]
        for future in ready:
            assert future.result(timeout=30).strip() == "READY"
        with connection(lock, write=True):
            for process in processes:
                process.stdin.write("GO\n")
                process.stdin.flush()
            time.sleep(0.2)
        for process in processes:
            stdout, stderr = process.communicate(timeout=30)
            assert process.returncode == 0, stderr
            assert stdout.strip() == "DONE 0"
    finally:
        # Only children created by this test are owned; always reap them.
        for process in processes:
            if process.poll() is None:
                process.kill()
            process.communicate(timeout=5)
        pool.shutdown(wait=True)

    lines = writer.path.read_bytes().splitlines()
    assert lines[0] == b'{"incomplete":'
    assert len(lines) == 7
    records = [json.loads(line) for line in lines[1:]]
    assert [record["sequence"] for record in records] == list(range(1, 7))
    for record in records:
        validate_event(record)


def test_exhausted_append_lock_emits_failure_without_writing(tmp_path, caplog):
    import time

    import orchestration.fc_logging as fc

    writer = FCLogWriter(tmp_path, "r", provenance="mock")
    task(writer)
    before = writer.path.read_bytes()
    lock = writer.path.with_name(writer.path.name + ".lock.sqlite3")
    with fc.connection(lock, write=True):
        start = time.monotonic()
        assert writer.emit("task", task_id="t", at=123.5,
                           dag_node={"task_id": "t", "dependencies": [], "status": "available"}) is False
        elapsed = time.monotonic() - start
    assert 0.9 <= elapsed < 3
    assert writer.failure_count == 1
    assert writer.path.read_bytes() == before
    assert "fc_log_projection_failed" in caplog.text
    assert len(read_events(writer.path)) == 1


@pytest.mark.parametrize("strict", [True, False])
def test_postwrite_fsync_failure_is_not_retried(tmp_path, monkeypatch, strict):
    import orchestration.fc_logging as fc

    writer = FCLogWriter(tmp_path, "r", provenance="mock")
    task(writer)
    before = writer.path.read_bytes()
    fsync_calls = []

    def failed_fsync(fd):
        fsync_calls.append(fd)
        raise OSError("fixture fsync failure after write")

    monkeypatch.setattr(fc.os, "fsync", failed_fsync)
    if strict:
        with pytest.raises(OSError, match="fixture fsync failure after write"):
            task(writer)
        assert writer.failure_count == 0
    else:
        assert writer.emit("task", task_id="t", at=123.5,
                           dag_node={"task_id": "t", "dependencies": [], "status": "available"}) is False
        assert writer.failure_count == 1
    assert len(fsync_calls) == 1
    assert writer.path.read_bytes().startswith(before)
    # Visible bytes do not imply durable success; one call never repeats them.
    records = read_events(writer.path)
    assert len(records) == 2
    assert [record["sequence"] for record in records] == [0, 1]
