import json
from pathlib import Path
import sqlite3
import subprocess
import sys
from uuid import UUID

import pytest
from pydantic import ValidationError

from swarm.fault_observations import (
    FaultObservation,
    FaultObservationStore,
    ObservationConflict,
)


def observation(**updates):
    values = dict(
        run_id="run", task_id="task", request_id="request", attempt=0,
        provider="dashscope", model="qwen", failure_class="confirmed_rejection",
        normalized_reason="rate_limited", occurred_at=100.0, evidence_ref="a" * 64,
    )
    values.update(updates)
    return FaultObservation(**values)


def test_model_roundtrip_and_unknown_fields_stay_null():
    item = observation()
    assert UUID(item.observation_id).version == 4
    assert FaultObservation.model_validate_json(item.model_dump_json()) == item
    body = json.loads(item.model_dump_json())
    assert body["evidence_ref"] == "a" * 64
    for field in ("switched_to", "cost_state", "retry_after_seconds"):
        assert body[field] is None
    with pytest.raises(ValidationError):
        item.cost_state = "settled"


@pytest.mark.parametrize("updates", [
    {"attempt": -1}, {"attempt": True}, {"attempt": "1"},
    {"cost_state": 0}, {"switched_to": 0}, {"cost_state": "billed"},
    {"failure_class": "answer_wrong"}, {"retry_after_seconds": -1.0},
    {"retry_after_seconds": float("nan")}, {"occurred_at": float("inf")},
    {"occurred_at": -1.0}, {"occurred_at": 1e308, "retry_after_seconds": 1e308},
    {"raw_body": "must not persist"}, {"request_id": ""},
])
def test_invalid_observations_rejected(updates):
    with pytest.raises(ValidationError):
        observation(**updates)


@pytest.mark.parametrize("failure_class", [
    "confirmed_rejection", "unknown_effect", "budget_exhausted", "capability_mismatch",
])
@pytest.mark.parametrize("cost_state", [None, "settled", "unknown", "reserved"])
def test_failure_and_cost_facts_preserved(tmp_path, failure_class, cost_state):
    store = FaultObservationStore(tmp_path / "facts.jsonl", "run")
    item = observation(failure_class=failure_class, cost_state=cost_state)
    assert store.append(item)
    assert store.read().records == (item,)


def test_replay_restart_attempt_and_run_isolation(tmp_path):
    path = tmp_path / "facts.jsonl"
    store = FaultObservationStore(path, "run")
    first = observation()
    assert store.append(first)
    original = path.read_bytes()
    assert not store.append(first)
    assert not FaultObservationStore(path, "run").append(observation())
    assert path.read_bytes() == original
    second = observation(attempt=1)
    assert store.append(second)
    other = observation(run_id="other", observation_id=first.observation_id)
    assert FaultObservationStore(path, "other").append(other)
    assert store.read().records == (first, second)
    assert FaultObservationStore(path, "other").read().records == (other,)
    assert len(path.read_bytes().splitlines()) == 3
    with pytest.raises(ValueError, match="run_id mismatch"):
        store.append(other)


@pytest.mark.parametrize("updates", [
    {"cost_state": "settled"}, {"evidence_ref": "b" * 64},
    {"task_id": "another"}, {"provider": "evomap"}, {"occurred_at": 101.0},
])
def test_conflicting_replay_is_not_an_update(tmp_path, updates):
    store = FaultObservationStore(tmp_path / "facts.jsonl", "run")
    store.append(observation())
    original = store.path.read_bytes()
    with pytest.raises(ObservationConflict, match="different facts"):
        store.append(observation(**updates))
    assert store.path.read_bytes() == original


def test_reused_observation_id_rejected_and_copied_model_revalidated(tmp_path):
    store = FaultObservationStore(tmp_path / "facts.jsonl", "run")
    first = observation()
    store.append(first)
    with pytest.raises(ObservationConflict, match="observation_id"):
        store.append(observation(observation_id=first.observation_id, request_id="another"))
    with pytest.raises(ValidationError):
        store.append(first.model_copy(update={"attempt": -1}))
    assert store.read().records == (first,)


def test_append_uses_persistent_index_without_repeated_scans(tmp_path, monkeypatch):
    path = tmp_path / "facts.jsonl"
    first = observation(attempt=2**80)
    path.write_text(first.model_dump_json() + "\n", encoding="utf-8")
    scans = []
    original_read_all = FaultObservationStore._read_all

    def counted_scan(store):
        scans.append(store.path)
        return original_read_all(store)

    def forbidden_read(_):
        pytest.fail("append must not use read()")

    monkeypatch.setattr(FaultObservationStore, "_read_all", counted_scan)
    monkeypatch.setattr(FaultObservationStore, "read", forbidden_read)
    for index in range(40):
        # New instances must reuse the on-disk index, including other runs.
        run_id = "run" if index % 2 else "other"
        store = FaultObservationStore(path, run_id)
        item = observation(run_id=run_id, request_id=str(index))
        assert store.append(item)
        assert not store.append(observation(run_id=run_id, request_id=str(index)))
        with pytest.raises(ObservationConflict, match="different facts"):
            store.append(observation(run_id=run_id, request_id=str(index), cost_state="settled"))
        with pytest.raises(ObservationConflict, match="observation_id"):
            store.append(observation(run_id=run_id, observation_id=item.observation_id))
    assert not FaultObservationStore(path, "run").append(first)
    assert scans == [path]
    assert len(path.read_bytes().splitlines()) == 41


def test_replay_cannot_borrow_another_attempts_observation_id(tmp_path):
    store = FaultObservationStore(tmp_path / "facts.jsonl", "run")
    first, second = observation(), observation(request_id="second")
    assert store.append(first)
    assert store.append(second)
    with pytest.raises(ObservationConflict, match="observation_id"):
        store.append(observation(observation_id=second.observation_id))
    assert store.read().records == (first, second)


@pytest.mark.parametrize("missing", ["sidecar", "table", "state"])
def test_missing_index_is_rebuilt_from_all_runs(tmp_path, missing):
    path = tmp_path / "facts.jsonl"
    first = observation()
    other = observation(run_id="other", observation_id=first.observation_id)
    store = FaultObservationStore(path, "run")
    assert store.append(first)
    assert FaultObservationStore(path, "other").append(other)
    if missing == "sidecar":
        store._lock_path.unlink()
    else:
        with sqlite3.connect(store._lock_path) as db:
            if missing == "table":
                db.execute("DROP TABLE fault_observation_index")
            else:
                db.execute("DELETE FROM fault_observation_index_state")
    original = path.read_bytes()
    assert not FaultObservationStore(path, "run").append(observation())
    assert not FaultObservationStore(path, "other").append(other)
    with pytest.raises(ObservationConflict, match="different facts"):
        store.append(observation(cost_state="settled"))
    assert path.read_bytes() == original


@pytest.mark.parametrize("initialized", [False, True])
@pytest.mark.parametrize("crash_at", ["fsynced", "indexed"])
def test_process_crash_before_index_commit_recovers_without_duplicates(tmp_path, initialized, crash_at):
    path = tmp_path / "facts.jsonl"
    store = FaultObservationStore(path, "run")
    previous = observation(request_id="previous")
    if initialized:
        assert store.append(previous)
    item = observation()
    script = """
import os
import sys
from swarm.fault_observations import FaultObservation, FaultObservationStore
store = FaultObservationStore(sys.argv[1], 'run')
item = FaultObservation.model_validate_json(sys.stdin.read())
if sys.argv[2] == 'fsynced':
    original = os.fsync
    def crash(fd):
        original(fd)
        os._exit(23)
    os.fsync = crash
else:
    original = FaultObservationStore._save_index_signature
    def crash(self, db):
        original(self, db)
        if db.execute('SELECT 1 FROM fault_observation_index WHERE request_id=?',
                      (item.request_id,)).fetchone():
            os._exit(23)
    FaultObservationStore._save_index_signature = crash
store.append(item)
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(path), crash_at], input=item.model_dump_json(),
        capture_output=True, text=True, timeout=30, cwd=Path(__file__).resolve().parents[2],
    )
    assert result.returncode == 23, result.stderr
    original = path.read_bytes()
    restarted = FaultObservationStore(path, "run")
    assert not restarted.append(item)
    with pytest.raises(ObservationConflict, match="different facts"):
        restarted.append(observation(cost_state="settled"))
    with pytest.raises(ObservationConflict, match="observation_id"):
        restarted.append(observation(observation_id=item.observation_id, request_id="another"))
    assert path.read_bytes() == original
    following = observation(request_id="following")
    assert restarted.append(following)
    expected = (previous, item, following) if initialized else (item, following)
    assert restarted.read().records == expected
    assert restarted.read().issues == ()


def test_partial_tail_invalidates_existing_index_and_is_sealed(tmp_path):
    path = tmp_path / "facts.jsonl"
    store = FaultObservationStore(path, "run")
    first = observation()
    assert store.append(first)
    with path.open("ab") as output:
        output.write(b'{"interrupted":')
    original = path.read_bytes()
    following = observation(request_id="following")
    assert FaultObservationStore(path, "run").append(following)
    assert path.read_bytes().startswith(original + b"\n")
    assert store.read().records == (first, following)
    assert [(issue.line_number, issue.reason) for issue in store.read().issues] == [(2, "invalid_record")]


def test_read_and_aggregate_do_not_create_missing_files(tmp_path):
    path = tmp_path / "missing" / "facts.jsonl"
    store = FaultObservationStore(path, "run")
    assert store.read().records == ()
    assert store.aggregate(now=100.0, window_seconds=10.0) == {}
    assert not path.parent.exists()


def test_sliding_window_grouping_and_absolute_cooldown_preserve_facts(tmp_path):
    store = FaultObservationStore(tmp_path / "facts.jsonl", "run")
    items = [
        observation(request_id="boundary", occurred_at=90.0, retry_after_seconds=1000.0),
        observation(request_id="a", occurred_at=91.0, retry_after_seconds=30.0),
        observation(request_id="b", occurred_at=99.0, retry_after_seconds=2.0),
        observation(request_id="c", occurred_at=100.0, failure_class="unknown_effect"),
        observation(request_id="future", occurred_at=101.0),
        observation(request_id="other-provider", provider="evomap"),
        observation(request_id="other-reason", normalized_reason="arrearage"),
        observation(request_id="other-model", model="qwen-other"),
    ]
    for item in reversed(items):  # File order must not determine time boundaries.
        store.append(item)
    other = FaultObservationStore(store.path, "another-run")
    other.append(observation(run_id="another-run", retry_after_seconds=999.0))
    original = store.path.read_bytes()
    groups = store.aggregate(now=100.0, window_seconds=10.0)
    assert len(groups) == 3
    group = groups[("dashscope", "rate_limited")]
    assert group.sample_count == 4
    assert group.confirmed_rejections == 3
    assert group.first_occurred_at == 91.0 and group.last_occurred_at == 100.0
    assert group.retry_after_until == 121.0
    assert groups[("evomap", "rate_limited")].retry_after_until is None
    assert store.aggregate(now=1000.0, window_seconds=10.0) == {}
    assert store.path.read_bytes() == original
    assert len(store.read().records) == len(items)


def test_zero_retry_after_is_known_not_missing(tmp_path):
    store = FaultObservationStore(tmp_path / "facts.jsonl", "run")
    store.append(observation(retry_after_seconds=0.0))
    assert store.aggregate(now=100.0, window_seconds=1.0)[
        ("dashscope", "rate_limited")
    ].retry_after_until == 100.0


@pytest.mark.parametrize("now,window", [
    (-1.0, 1.0), (float("nan"), 1.0), (float("inf"), 1.0),
    (100.0, 0.0), (100.0, -1.0), (100.0, float("inf")),
])
def test_invalid_windows_rejected(tmp_path, now, window):
    with pytest.raises(ValueError):
        FaultObservationStore(tmp_path / "facts.jsonl", "run").aggregate(
            now=now, window_seconds=window
        )


def test_corrupt_lines_duplicates_and_partial_tail_are_retained(tmp_path):
    path = tmp_path / "facts.jsonl"
    first = observation()
    conflict = observation(cost_state="settled")
    duplicate = observation()
    identity_conflict = observation(observation_id=first.observation_id, request_id="other")
    original = (
        first.model_dump_json().encode() + b"\nnot json\n\xff\n{}\n\n"
        + duplicate.model_dump_json().encode() + b"\n"
        + conflict.model_dump_json().encode() + b"\n"
        + identity_conflict.model_dump_json().encode() + b'\n{"unfinished":'
    )
    path.write_bytes(original)
    store = FaultObservationStore(path, "run")
    read = store.read()
    assert read.records == (first,)
    assert [issue.line_number for issue in read.issues] == list(range(2, 10))
    assert [issue.reason for issue in read.issues][-4:] == [
        "duplicate_record", "conflicting_record", "conflicting_record", "invalid_record",
    ]
    assert path.read_bytes() == original
    second = observation(request_id="new")
    assert store.append(second)
    assert path.read_bytes().startswith(original + b"\n")
    assert store.read().records == (first, second)
    assert len(store.read().issues) == 8
    assert store.aggregate(now=100.0, window_seconds=5.0)[
        ("dashscope", "rate_limited")
    ].sample_count == 2
    assert not store.append(second)


def test_complete_record_without_newline_is_not_lost(tmp_path):
    path = tmp_path / "facts.jsonl"
    first = observation()
    path.write_bytes(first.model_dump_json().encode())
    store = FaultObservationStore(path, "run")
    assert not store.append(first)
    second = observation(request_id="new")
    assert store.append(second)
    assert store.read().records == (first, second)
    assert store.read().issues == ()


@pytest.mark.parametrize("initialized", [False, True])
def test_fsync_failure_does_not_cause_duplicate_local_replay(tmp_path, monkeypatch, initialized):
    store = FaultObservationStore(tmp_path / "facts.jsonl", "run")
    previous = observation(request_id="previous")
    if initialized:
        assert store.append(previous)
    item = observation()

    def fail(_):
        raise OSError("simulated persistence failure")

    with monkeypatch.context() as patch:
        patch.setattr("swarm.fault_observations.os.fsync", fail)
        with pytest.raises(OSError):
            store.append(item)
    assert not store.append(item)
    assert store.read().records == ((previous, item) if initialized else (item,))


def test_competing_processes_append_once_and_preserve_all_unique_records(tmp_path):
    path = tmp_path / "facts.jsonl"
    script = """
import sys
from swarm.fault_observations import FaultObservation, FaultObservationStore
item = FaultObservation.model_validate_json(sys.stdin.readline())
store = FaultObservationStore(sys.argv[1], 'run')
store.append(item)
for index in range(8):
    store.append(FaultObservation.model_validate({
        **item.model_dump(), 'observation_id': sys.argv[2] + '-' + str(index),
        'request_id': sys.argv[2] + '-' + str(index),
    }))
"""
    children = [subprocess.Popen(
        [sys.executable, "-c", script, str(path), str(index)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        cwd=Path(__file__).resolve().parents[2],
    ) for index in range(3)]
    try:
        for child in children:
            child.stdin.write(observation().model_dump_json() + "\n")
            child.stdin.flush()
        for child in children:
            _, error = child.communicate(timeout=30)
            assert child.returncode == 0, error
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=10)
    result = FaultObservationStore(path, "run").read()
    assert len(result.records) == 25
    assert len(path.read_bytes().splitlines()) == 25
    assert result.issues == ()


def test_busy_writer_fails_within_configured_timeout_without_appending(tmp_path):
    path = tmp_path / "facts.jsonl"
    store = FaultObservationStore(path, "run", timeout_seconds=0)
    with sqlite3.connect(str(path) + ".lock.sqlite3") as database:
        database.execute("BEGIN IMMEDIATE")
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            store.append(observation())
    assert not path.exists()
    assert store.append(observation())


def test_recovery_boundary_retains_history_and_filters_by_time_and_file_order(tmp_path):
    store = FaultObservationStore(tmp_path / "facts.jsonl", "run")
    store.append(observation(request_id="old", occurred_at=100.0))
    store.append(observation(request_id="future-old", occurred_at=102.0))
    # A corrupt line remains in the durable file and participates in file order.
    with store.path.open("ab") as handle:
        handle.write(b"invalid\n")
    checkpoint = store.checkpoint()
    before = store.path.read_bytes()
    store.append(observation(request_id="late-old", occurred_at=99.0))
    store.append(observation(request_id="new-equal", occurred_at=100.0))
    store.append(observation(request_id="new", occurred_at=101.0, retry_after_seconds=3.0))
    group = store.aggregate(now=102.0, window_seconds=10.0)[("dashscope", "rate_limited")]
    recovered = group.after_recovery(100.0, checkpoint)
    assert checkpoint == 3
    assert group.sample_count == 5
    assert recovered.sample_count == recovered.confirmed_rejections == 2
    assert (recovered.first_occurred_at, recovered.last_occurred_at) == (100.0, 101.0)
    assert recovered.retry_after_until == 104.0
    assert store.path.read_bytes().startswith(before)
    assert len(store.read().records) == 5 and len(store.read().issues) == 1
    assert group.after_recovery(102.0, store.checkpoint()) is None


def test_recovery_checkpoint_serializes_with_append_lock(tmp_path):
    store = FaultObservationStore(tmp_path / "facts.jsonl", "run", timeout_seconds=0)
    store.append(observation())
    with sqlite3.connect(str(store.path) + ".lock.sqlite3") as database:
        database.execute("BEGIN IMMEDIATE")
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            store.checkpoint()
    assert store.checkpoint() == 1
