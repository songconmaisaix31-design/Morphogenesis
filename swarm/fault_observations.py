"""Immutable failure facts and run-scoped routing views, never reusable assets.

Pydantic v2 (MIT) handles validation/JSON; stdlib uuid supplies identifiers.
The existing swarm.task_ledger SQLite transaction helper serializes cooperating
writers through a sidecar holding a rebuildable deduplication index.
JSONL writes follow the local_assets fsync convention without importing assets.
All writers must use this store and preserve its sidecar while it is in use.
Reads are snapshots: a concurrent incomplete last line may be reported as invalid.
"""

from __future__ import annotations

import math
import os
from pathlib import Path
import sqlite3
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from swarm.task_ledger import connection

FailureClass = Literal[
    "confirmed_rejection", "unknown_effect", "budget_exhausted", "capability_mismatch"
]
CostState = Literal["settled", "unknown", "reserved"]


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True, allow_inf_nan=False)


class FaultObservation(_Model):
    """One request attempt; evidence_ref is FC-A's evidence_hash verbatim.

    attempt is zero-based, matching contracts.identity.AttemptId.attempt. Time is
    UTC Unix seconds. Missing switch, cost state and cooldown remain unknown.
    A replay may regenerate observation_id but must retain every other fact.
    """

    observation_id: str = Field(default_factory=lambda: uuid4().hex, min_length=1)
    run_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    attempt: int = Field(ge=0)
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    failure_class: FailureClass
    normalized_reason: str = Field(min_length=1)
    retry_after_seconds: float | None = Field(default=None, ge=0)
    switched_to: str | None = Field(default=None, min_length=1)
    cost_state: CostState | None = None
    occurred_at: float = Field(ge=0)
    evidence_ref: str | None = None

    @model_validator(mode="after")
    def finite_cooldown(self) -> FaultObservation:
        if self.retry_after_seconds is not None and not math.isfinite(
            self.occurred_at + self.retry_after_seconds
        ):
            raise ValueError("nonfinite cooldown deadline")
        return self


class FaultReadIssue(_Model):
    """Safe diagnostics: never includes raw lines or validation exception text."""

    line_number: int = Field(gt=0)
    reason: Literal["invalid_record", "duplicate_record", "conflicting_record"]


class FaultReadResult(_Model):
    records: tuple[FaultObservation, ...] = ()
    issues: tuple[FaultReadIssue, ...] = ()
    record_lines: tuple[int, ...] = ()


class FaultSample(_Model):
    """Routing inputs with their existing append-only file position."""

    sequence: int = Field(gt=0)
    occurred_at: float
    confirmed_rejection: bool
    retry_after_until: float | None = None


class FaultAggregate(_Model):
    """Failure counts only, not a failure rate or permission to retry.

    retry_after_until is the maximum observed absolute deadline, not a cooldown
    measured from the time of aggregation. None means no known hint. Consumers
    should inspect read().issues before treating incomplete evidence as healthy.
    """

    provider: str
    normalized_reason: str
    sample_count: int = Field(gt=0)
    confirmed_rejections: int = Field(ge=0)
    first_occurred_at: float
    last_occurred_at: float
    retry_after_until: float | None = None
    samples: tuple[FaultSample, ...] = ()

    def after_recovery(self, at: float, sequence: int | None) -> FaultAggregate | None:
        """Exclude the recovery snapshot and delayed pre-recovery events.

        File order disambiguates equal timestamps. Without a file checkpoint,
        only strictly later timestamps are known to be new evidence.
        """
        if not self.samples:
            return self if self.first_occurred_at > at else None
        samples = tuple(sample for sample in self.samples if (
            sample.occurred_at > at if sequence is None else
            sample.sequence > sequence and sample.occurred_at >= at
        ))
        return self.from_samples(self.provider, self.normalized_reason, samples) if samples else None

    @classmethod
    def from_samples(cls, provider: str, reason: str,
                     samples: tuple[FaultSample, ...]) -> FaultAggregate:
        deadlines = [sample.retry_after_until for sample in samples
                     if sample.retry_after_until is not None]
        return cls(
            provider=provider, normalized_reason=reason, sample_count=len(samples),
            confirmed_rejections=sum(sample.confirmed_rejection for sample in samples),
            first_occurred_at=min(sample.occurred_at for sample in samples),
            last_occurred_at=max(sample.occurred_at for sample in samples),
            retry_after_until=max(deadlines) if deadlines else None, samples=samples,
        )


class ObservationConflict(ValueError):
    """An existing request attempt or observation identity has different facts."""


def _same_facts(first: FaultObservation, second: FaultObservation) -> bool:
    return first.model_dump(exclude={"observation_id"}) == second.model_dump(
        exclude={"observation_id"}
    )


class FaultObservationStore:
    """Append-only JSONL; idempotence is (run_id, request_id, attempt).

    Each append checks a persistent index in a bounded SQLite write transaction.
    JSONL remains authoritative: its fsync precedes the index commit. A missing
    index or changed file signature triggers one rebuild before using the index,
    including after a crash between the JSONL write and the SQLite commit.
    Truncated/malformed lines are retained and skipped; a missing trailing newline
    is sealed before a new record. Valid records with conflicting identities are
    diagnosed and the first valid fact wins on read. Filesystem errors propagate.
    This is local cooperating-process storage, not a distributed filesystem lock.
    """

    def __init__(self, path: str | Path, run_id: str, *, timeout_seconds: float = 10) -> None:
        if not run_id.strip():
            raise ValueError("run_id required")
        if not math.isfinite(timeout_seconds) or not 0 <= timeout_seconds <= 60:
            raise ValueError("timeout_seconds must be in [0,60]")
        self.path = Path(path).resolve()
        self.run_id = run_id
        self.timeout_seconds = timeout_seconds
        self._lock_path = self.path.with_name(self.path.name + ".lock.sqlite3")

    def _read_all(self) -> FaultReadResult:
        records: dict[tuple[str, str, int], FaultObservation] = {}
        record_lines: list[int] = []
        identities: set[tuple[str, str]] = set()
        issues: list[FaultReadIssue] = []
        try:
            source = self.path.open("rb")
        except FileNotFoundError:
            return FaultReadResult()
        with source:
            for number, line in enumerate(source, start=1):
                try:
                    item = FaultObservation.model_validate_json(line)
                except ValidationError:
                    issues.append(FaultReadIssue(line_number=number, reason="invalid_record"))
                    continue
                key = (item.run_id, item.request_id, item.attempt)
                identity = (item.run_id, item.observation_id)
                existing = records.get(key)
                if existing is not None:
                    issues.append(FaultReadIssue(
                        line_number=number,
                        reason="duplicate_record" if _same_facts(existing, item) else "conflicting_record",
                    ))
                elif identity in identities:
                    issues.append(FaultReadIssue(line_number=number, reason="conflicting_record"))
                else:
                    records[key] = item
                    identities.add(identity)
                    record_lines.append(number)
        return FaultReadResult(records=tuple(records.values()), issues=tuple(issues),
                               record_lines=tuple(record_lines))

    def read(self) -> FaultReadResult:
        """Read without creating or repairing files; diagnostics cover the file."""
        result = self._read_all()
        return FaultReadResult(
            records=tuple(item for item in result.records if item.run_id == self.run_id),
            issues=result.issues,
            record_lines=tuple(line for item, line in zip(result.records, result.record_lines, strict=True)
                               if item.run_id == self.run_id),
        )

    def checkpoint(self) -> int:
        """Capture append order under the same bounded lock as writers.

        This is a position in the existing JSONL, not a second event log. The
        last partial line also counts: append seals it before adding new facts.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with connection(self._lock_path, write=True, timeout=self.timeout_seconds):
            try:
                with self.path.open("rb") as source:
                    return sum(1 for _ in source)
            except FileNotFoundError:
                return 0

    def _file_signature(self) -> str:
        try:
            stat = self.path.stat()
        except FileNotFoundError:
            return "missing"
        return str((stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns))

    @staticmethod
    def _index_record(db: sqlite3.Connection, item: FaultObservation) -> None:
        db.execute(
            "INSERT INTO fault_observation_index "
            "(run_id, request_id, attempt, observation_id, record) VALUES (?,?,?,?,?)",
            (item.run_id, item.request_id, str(item.attempt), item.observation_id,
             item.model_dump_json()),
        )

    def _save_index_signature(self, db: sqlite3.Connection) -> None:
        db.execute(
            "INSERT OR REPLACE INTO fault_observation_index_state VALUES (1,?)",
            (self._file_signature(),),
        )

    def _ensure_index(self, db: sqlite3.Connection) -> None:
        index_exists = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='fault_observation_index'"
        ).fetchone() is not None
        # TEXT preserves the model's unbounded nonnegative integer attempt IDs.
        db.execute(
            "CREATE TABLE IF NOT EXISTS fault_observation_index ("
            "run_id TEXT NOT NULL, request_id TEXT NOT NULL, attempt TEXT NOT NULL, "
            "observation_id TEXT NOT NULL, record TEXT NOT NULL, "
            "PRIMARY KEY(run_id,request_id,attempt), UNIQUE(run_id,observation_id))"
        )
        db.execute(
            "CREATE TABLE IF NOT EXISTS fault_observation_index_state ("
            "singleton INTEGER PRIMARY KEY CHECK(singleton=1), file_signature TEXT NOT NULL)"
        )
        state = db.execute(
            "SELECT file_signature FROM fault_observation_index_state WHERE singleton=1"
        ).fetchone()
        if index_exists and state is not None and state["file_signature"] == self._file_signature():
            return
        db.execute("DELETE FROM fault_observation_index")
        for item in self._read_all().records:
            self._index_record(db, item)
        # Recovered bytes may come from a failed fsync or an interrupted writer.
        # Make them durable before committing an index that includes them.
        try:
            # Windows fsync requires a writable handle, even without a write.
            source = self.path.open("r+b")
        except FileNotFoundError:
            pass
        else:
            with source:
                os.fsync(source.fileno())
        self._save_index_signature(db)

    def append(self, observation: FaultObservation) -> bool:
        """Return True for an fsynced append, False for replay; reject conflicts.

        Storage failure can leave a partial or complete final line; it is not a
        reason to repeat a remote request. A later local replay rebuilds a stale
        index from the file; SQLite cannot roll back already appended JSONL bytes.
        """
        observation = FaultObservation.model_validate(observation.model_dump())
        if observation.run_id != self.run_id:
            raise ValueError("observation run_id mismatch")
        payload = observation.model_dump_json().encode("utf-8") + b"\n"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with connection(self._lock_path, write=True, timeout=self.timeout_seconds) as db:
            self._ensure_index(db)
            key = (observation.run_id, observation.request_id, str(observation.attempt))
            existing = db.execute(
                "SELECT record FROM fault_observation_index WHERE run_id=? AND request_id=? AND attempt=?",
                key,
            ).fetchone()
            if existing is not None and not _same_facts(
                FaultObservation.model_validate_json(existing["record"]), observation
            ):
                raise ObservationConflict("request attempt already has different facts")
            if db.execute(
                "SELECT 1 FROM fault_observation_index WHERE run_id=? AND observation_id=? "
                "AND NOT (request_id=? AND attempt=?)",
                (observation.run_id, observation.observation_id, observation.request_id,
                 str(observation.attempt)),
            ).fetchone() is not None:
                raise ObservationConflict("observation_id already identifies another request attempt")
            if existing is not None:
                return False
            with self.path.open("a+b") as output:
                output.seek(0, os.SEEK_END)
                if output.tell():
                    output.seek(-1, os.SEEK_END)
                    if output.read(1) != b"\n":
                        output.write(b"\n")
                output.write(payload)
                output.flush()
                os.fsync(output.fileno())
            self._index_record(db, observation)
            self._save_index_signature(db)
        return True

    def aggregate(self, *, now: float, window_seconds: float) -> dict[tuple[str, str], FaultAggregate]:
        """Group unique failures in (now - window_seconds, now], for this run.

        Expired/future facts remain on disk. Thresholds, minimum sample counts,
        routing decisions and recovery probes belong to the consumer (FC-C).
        """
        if not math.isfinite(now) or now < 0:
            raise ValueError("now must be finite and nonnegative")
        if not math.isfinite(window_seconds) or window_seconds <= 0:
            raise ValueError("window_seconds must be finite and positive")
        groups: dict[tuple[str, str], list[FaultSample]] = {}
        snapshot = self.read()
        for item, sequence in zip(snapshot.records, snapshot.record_lines, strict=True):
            if now - window_seconds < item.occurred_at <= now:
                groups.setdefault((item.provider, item.normalized_reason), []).append(FaultSample(
                    sequence=sequence, occurred_at=item.occurred_at,
                    confirmed_rejection=item.failure_class == "confirmed_rejection",
                    retry_after_until=(item.occurred_at + item.retry_after_seconds
                                       if item.retry_after_seconds is not None else None),
                ))
        result: dict[tuple[str, str], FaultAggregate] = {}
        for key, items in sorted(groups.items()):
            result[key] = FaultAggregate.from_samples(key[0], key[1], tuple(items))
        return result
