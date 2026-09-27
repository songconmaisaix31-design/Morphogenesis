"""Immutable failure facts and run-scoped routing views, never reusable assets.

Pydantic v2 (MIT) handles validation/JSON; stdlib uuid supplies identifiers.
The existing swarm.task_ledger SQLite transaction helper serializes cooperating
writers through a sidecar, without a second copy/index of the observation facts.
JSONL writes follow the local_assets fsync convention without importing assets.
All writers must use this store and preserve its sidecar while it is in use.
Reads are snapshots: a concurrent incomplete last line may be reported as invalid.
"""

from __future__ import annotations

import math
import os
from pathlib import Path
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


class ObservationConflict(ValueError):
    """An existing request attempt or observation identity has different facts."""


def _same_facts(first: FaultObservation, second: FaultObservation) -> bool:
    return first.model_dump(exclude={"observation_id"}) == second.model_dump(
        exclude={"observation_id"}
    )


class FaultObservationStore:
    """Append-only JSONL; idempotence is (run_id, request_id, attempt).

    Each append scans the file while holding a bounded SQLite write transaction.
    There is no persistent deduplication cache to become inconsistent on a crash.
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
        return FaultReadResult(records=tuple(records.values()), issues=tuple(issues))

    def read(self) -> FaultReadResult:
        """Read without creating or repairing files; diagnostics cover the file."""
        result = self._read_all()
        return FaultReadResult(
            records=tuple(item for item in result.records if item.run_id == self.run_id),
            issues=result.issues,
        )

    def append(self, observation: FaultObservation) -> bool:
        """Return True for an fsynced append, False for replay; reject conflicts.

        Storage failure can leave a partial or complete final line; it is not a
        reason to repeat a remote request. A later local replay rescans the file.
        """
        observation = FaultObservation.model_validate(observation.model_dump())
        if observation.run_id != self.run_id:
            raise ValueError("observation run_id mismatch")
        payload = observation.model_dump_json().encode("utf-8") + b"\n"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with connection(self._lock_path, write=True, timeout=self.timeout_seconds):
            records = self.read().records
            for existing in records:
                same_key = (existing.request_id, existing.attempt) == (
                    observation.request_id, observation.attempt
                )
                if same_key and not _same_facts(existing, observation):
                    raise ObservationConflict("request attempt already has different facts")
                if existing.observation_id == observation.observation_id and not same_key:
                    raise ObservationConflict("observation_id already identifies another request attempt")
            if any((item.request_id, item.attempt) == (observation.request_id, observation.attempt)
                   for item in records):
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
        groups: dict[tuple[str, str], list[FaultObservation]] = {}
        for item in self.read().records:
            if now - window_seconds < item.occurred_at <= now:
                groups.setdefault((item.provider, item.normalized_reason), []).append(item)
        result: dict[tuple[str, str], FaultAggregate] = {}
        for key, items in sorted(groups.items()):
            deadlines = [item.occurred_at + item.retry_after_seconds for item in items
                         if item.retry_after_seconds is not None]
            result[key] = FaultAggregate(
                provider=key[0], normalized_reason=key[1], sample_count=len(items),
                confirmed_rejections=sum(item.failure_class == "confirmed_rejection" for item in items),
                first_occurred_at=min(item.occurred_at for item in items),
                last_occurred_at=max(item.occurred_at for item in items),
                retry_after_until=max(deadlines) if deadlines else None,
            )
        return result
