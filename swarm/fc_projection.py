"""Bounded FC side-channel inspection/rebuild; no execution or learning imports.

Only trusted existing FC logs and original ledger routes/claims are projected.
Missing asset/fault/rehearsal facts cannot be invented from a task status.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import cast

from pydantic import JsonValue

from local_assets.paths import no_links
from orchestration.fc_logging import (
    EventKind, FCLogWriter, ledger_projection_fact, ledger_projection_rows, validate_event,
)
from swarm.task_ledger import TaskLedger, connection

MAX_PROJECTION_BYTES = 8 * 1024 * 1024
_FACTS = ("dag_node", "asset_calls", "routing", "claim", "fault_observation", "rehearsal",
          "audit_confirmed_issue_events", "issue_audit")


@dataclass(frozen=True)
class ProjectionRead:
    state: str
    records: list[dict[str, JsonValue]]
    reasons: tuple[str, ...] = ()


def _stamp(path: Path) -> tuple[int, int, int]:
    metadata = path.stat()
    return metadata.st_ino, metadata.st_size, metadata.st_mtime_ns


def read_projection(path: Path, *, limit: int = 1000) -> ProjectionRead:
    """Read a bounded stable snapshot; invalid bytes remain untouched and visible."""
    if not 1 <= limit <= 10000:
        raise ValueError("fc_projection_limit_out_of_range")
    try:
        no_links(path)
        if not path.exists():
            return ProjectionRead("missing", [])
        before = _stamp(path)
        with path.open("rb") as stream:
            payload = stream.read(MAX_PROJECTION_BYTES + 1)
        no_links(path)
        if before != _stamp(path):
            return ProjectionRead("incomplete", [], ("changed_during_observation",))
        if len(payload) > MAX_PROJECTION_BYTES:
            return ProjectionRead("incomplete", [], ("byte_limit",))
        records: list[dict[str, JsonValue]] = []
        reasons: list[str] = []
        lines = payload.splitlines(keepends=True)
        if len(lines) > limit:
            reasons.append("record_limit")
        for line in lines[:limit]:
            if not line.endswith(b"\n"):
                reasons.append("partial_line")
                continue
            try:
                from json import loads

                records.append(validate_event(loads(line)))
            except Exception:
                # Exception text and malformed/untrusted bytes are never diagnostics.
                reasons.append("invalid_record")
        return ProjectionRead("incomplete" if reasons else "available", records,
                              tuple(dict.fromkeys(reasons)))
    except Exception:
        return ProjectionRead("incomplete", [], ("read_failed",))


def rebuild_projection(sources: tuple[Path, ...], destination: FCLogWriter,
                       ledger: TaskLedger, worker_id: str, *, limit: int = 1000) -> dict[str, JsonValue]:
    """Explicit one-shot fresh output, never repair in place or retry a write.

    Available means only supplied parseable FC facts plus this worker's persisted
    routing/claim window. It is not a certificate of complete execution evidence.
    Partial input stays incomplete even if the new JSONL is syntactically valid.
    """
    if not 1 <= limit <= 10000 or not worker_id.strip():
        raise ValueError("fc_projection_invalid_rebuild_request")
    if destination.run_id != ledger.swarm_id:
        raise ValueError("fc_projection_run_mismatch")
    destination._check_path()
    if destination.path.exists() or any(path.resolve() == destination.path.resolve() for path in sources):
        raise ValueError("fc_projection_requires_new_destination")
    records: list[dict[str, JsonValue]] = []
    reasons: list[str] = []
    for path in sources:
        view = read_projection(path, limit=limit)
        if view.state != "available":
            reasons.extend(view.reasons or ("missing_source",))
        for record in view.records:
            if (record["run_id"], record["provenance"], record["drill"], record["original_run_uri"]) != (
                    destination.run_id, destination.provenance, destination.drill, destination.original_run_uri):
                raise ValueError("fc_projection_source_mismatch")
            records.append(record)
            if len(records) > limit:
                return {"state": "incomplete", "scope": "fc_sidechannel", "reasons": ["record_limit"],
                        "written": 0}
    try:
        rows, truncated = ledger_projection_rows(ledger, limit=limit)
        if truncated:
            reasons.append("ledger_window_incomplete")
        # Match original audit ordinals, not a new identity/hash/completion index.
        for row in rows:
            fact = ledger_projection_fact(row, worker_id)
            if fact is None:
                continue
            event, task_id, facts = fact
            matches = [record for record in records
                       if record["event"] == event and record["sequence"] == row["sequence"]]
            if matches:
                if any(record["task_id"] != task_id or record["at"] != row["at"]
                       or any(record[key] != value for key, value in facts.items()) for record in matches):
                    reasons.append("ledger_fact_mismatch")
                continue
            records.append(dict(
                schema_version="1.0.0", run_id=destination.run_id, sequence=row["sequence"], task_id=task_id,
                at=row["at"], duration_seconds=None, drill=destination.drill, provenance=destination.provenance,
                evidence_label={"mock": "SIMULATED", "live": "LIVE", "replay": "REPLAY"}[destination.provenance],
                original_run_uri=destination.original_run_uri, event=event, dag_node=None, asset_calls=[],
                routing=None, claim=None, fault_observation=None, rehearsal=None,
            ) | cast(dict[str, JsonValue], facts))
        if len(records) > limit:
            return {"state": "incomplete", "scope": "fc_sidechannel", "reasons": ["record_limit"], "written": 0}
        for record in records:
            validate_event(record)
    except Exception:
        return {"state": "incomplete", "scope": "fc_sidechannel", "reasons": ["ledger_read_failed"], "written": 0}

    written = 0
    try:
        destination.path.parent.mkdir(parents=True, exist_ok=True)
        lock = destination.path.with_name(destination.path.name + ".lock.sqlite3")
        no_links(lock)
        with connection(lock, write=True, timeout=1.0):
            destination._check_path()
            with destination.path.open("xb"):
                pass  # Atomically refuse an existing/concurrently reserved destination.
        for record in records:
            facts = {key: record[key] for key in _FACTS if key in record}
            destination.append(cast(EventKind, record["event"]), task_id=cast(str | None, record["task_id"]),
                               at=cast(float, record["at"]), sequence=cast(int, record["sequence"]),
                               duration_seconds=cast(float | None, record["duration_seconds"]), **facts)
            written += 1
        final = read_projection(destination.path, limit=limit)
        if final.state != "available" or final.records != records:
            reasons.append("output_changed_or_incomplete")
    except Exception:
        destination.diagnostic()
        reasons.append("write_failed")
    return {"state": "incomplete" if reasons else "available", "scope": "fc_sidechannel",
            "coverage": "supplied_fc_facts_and_worker_ledger_routes_claims", "written": written,
            "reasons": list(dict.fromkeys(reasons))}
