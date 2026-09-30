"""Side-channel FC 1.0.0 JSONL, never an execution or routing authority.

Schema: frozen H3 be4fb7a685e951c9e42d8dc0c7eeb900cb5518f1 fenced JSON.
Reuse jsonschema 4.26 (MIT, already locked via MCP), Pydantic 2 (MIT),
FaultObservationStore's bounded SQLite/fsync convention and existing path guards.
The packaged JSON is byte-identical to that fence; runtime never reads docs/Git.
"""
from __future__ import annotations

from functools import lru_cache
from importlib.resources import files
import json
import logging
import math
import os
from pathlib import Path
import re
from typing import Any, Literal

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, JsonValue, TypeAdapter

from contracts.provenance import Acceptance, Provenance
from local_assets.paths import FROZEN_MAINLINE, no_links
from orchestration.rehearsal_models import RehearsalSnapshot
from swarm.fault_observations import FaultObservation
from swarm.task_ledger import TaskLedger, connection

EventKind = Literal["task", "asset_call", "routing", "claim", "fault_observation", "rehearsal"]
_OBJECT = TypeAdapter(dict[str, JsonValue], config=ConfigDict(allow_inf_nan=False))
_LOG = logging.getLogger(__name__)
_SOURCE = Path(__file__).resolve().parents[1]
# Reject the entire projection rather than corrupting immutable nested facts.
_CREDENTIAL = re.compile(
    r"(?i)\bbearer\s+\S+|\bsk-[a-z0-9_-]+|"
    r"(?:api[_-]?key|access[_-]?token|authorization|password|secret)\s*[=:]\s*\S+|"
    r"https?://[^\s/]+:[^\s/]+@"
)


@lru_cache(maxsize=1)
def _validator() -> Any:
    schema = json.loads(files("orchestration").joinpath("fc_log_schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def validate_event(value: object) -> dict[str, JsonValue]:
    """Frozen structural contract plus original model/cross-field semantics."""
    data = _OBJECT.validate_python(value)
    _validator().validate(data)
    Acceptance(provenance=data["provenance"], original_run_uri=data["original_run_uri"])  # type: ignore[arg-type]
    for key in ("dag_node", "claim", "fault_observation", "rehearsal"):
        fact = data[key]
        if isinstance(fact, dict) and fact.get("task_id") != data["task_id"]:
            raise ValueError("fc_nested_task_mismatch")
    fault = data["fault_observation"]
    if fault is not None:
        if not isinstance(fault, dict) or "observation_id" not in fault:
            raise ValueError("fc_observation_identity_missing")
        observation = FaultObservation.model_validate(fault)
        if observation.run_id != data["run_id"]:
            raise ValueError("fc_nested_run_mismatch")
    snapshot = data["rehearsal"]
    if snapshot is not None:
        rehearsal = RehearsalSnapshot.model_validate(snapshot)
        if rehearsal.provenance != data["provenance"]:
            raise ValueError("fc_nested_provenance_mismatch")
        if rehearsal.acceptance.original_run_uri != data["original_run_uri"]:
            raise ValueError("fc_nested_origin_mismatch")
    route = data["routing"]
    if isinstance(route, dict):
        candidates = route["candidates"]
        assert isinstance(candidates, list)
        ids = [str(item["task_id"]) for item in candidates if isinstance(item, dict)]
        probabilities = [float(item["probability"]) for item in candidates if isinstance(item, dict)]  # type: ignore[arg-type]
        if len(set(ids)) != len(ids) or (route["selected"] is not None and route["selected"] not in ids):
            raise ValueError("fc_invalid_route_selection")
        if probabilities and not math.isclose(sum(probabilities), 1, abs_tol=1e-9):
            raise ValueError("fc_invalid_route_probabilities")
        if data["task_id"] != route["selected"]:
            raise ValueError("fc_route_task_mismatch")
    audit = data.get("issue_audit")
    if isinstance(audit, dict):
        issue_ids = audit["confirmed_issue_ids"]
        if not isinstance(issue_ids, list) or len(issue_ids) != data.get("audit_confirmed_issue_events"):
            raise ValueError("fc_audit_count_mismatch")
    payload = _OBJECT.dump_json(data).decode("utf-8")
    if _CREDENTIAL.search(payload):
        raise ValueError("fc_sensitive_projection_withheld")
    return data


class FCLogWriter:
    """A fixed destination per evidence class; append failures are observable only.

    emit returns False on failure and logs only a constant diagnostic. append is
    the strict variant for validation tools. Neither caller should use this return
    value to decide remote execution. No retry, completion index, or control state.
    sequence preserves a source ordinal when supplied, otherwise the JSONL line
    position; it is not a globally unique identity or a cross-source clock.
    """

    def __init__(self, root: str | Path, run_id: str, *, provenance: Provenance,
                 drill: bool = False, original_run_uri: str | None = None) -> None:
        self.root = Path(root).absolute()
        self.run_id, self.provenance = run_id, provenance
        self.drill, self.original_run_uri = drill, original_run_uri
        self.path = self.root / "fc-logs" / ("drill" if drill else "runtime") / provenance / "events.jsonl"
        self._cursor = 0
        # Measured local diagnostic count since construction, NOT issue_audit.
        self.failure_count = 0

    def _check_path(self) -> None:
        no_links(self.path)
        root = self.root.resolve()
        if any(root == protected.resolve() or root.is_relative_to(protected.resolve())
               for protected in (_SOURCE, FROZEN_MAINLINE)):
            raise ValueError("protected_runtime_state")

    def append(self, event: EventKind, *, task_id: str | None, at: float,
               sequence: int | None = None, duration_seconds: float | None = None,
               **facts: object) -> None:
        data: dict[str, object] = dict(
            schema_version="1.0.0", run_id=self.run_id, sequence=sequence if sequence is not None else 0,
            task_id=task_id, at=at, duration_seconds=duration_seconds, drill=self.drill,
            provenance=self.provenance, evidence_label={"mock": "SIMULATED", "live": "LIVE", "replay": "REPLAY"}[self.provenance],
            original_run_uri=self.original_run_uri, event=event, dag_node=None,
            asset_calls=[], routing=None, claim=None, fault_observation=None, rehearsal=None,
        )
        allowed = {"dag_node", "asset_calls", "routing", "claim", "fault_observation", "rehearsal",
                   "audit_confirmed_issue_events", "issue_audit"}
        if facts.keys() - allowed:
            raise ValueError("fc_unknown_fact")
        data.update({key: value.model_dump(mode="json") if isinstance(value, BaseModel) else value
                     for key, value in facts.items()})
        valid = validate_event(data)
        self._check_path()
        lock = self.path.with_name(self.path.name + ".lock.sqlite3")
        no_links(lock)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with connection(lock, write=True, timeout=0.05):
            self._check_path()
            with self.path.open("a+b") as stream:
                stream.seek(0)
                if sequence is None:
                    valid["sequence"] = sum(1 for _ in stream)
                stream.seek(0, os.SEEK_END)
                if stream.tell():
                    stream.seek(-1, os.SEEK_END)
                    if stream.read(1) != b"\n":
                        stream.write(b"\n")
                stream.write(_OBJECT.dump_json(valid) + b"\n")
                stream.flush()
                os.fsync(stream.fileno())

    def emit(self, event: EventKind, *, task_id: str | None, at: float,
             sequence: int | None = None, duration_seconds: float | None = None,
             **facts: object) -> bool:
        try:
            self.append(event, task_id=task_id, at=at, sequence=sequence,
                        duration_seconds=duration_seconds, **facts)
            return True
        except Exception:
            self.diagnostic()
            return False

    def diagnostic(self) -> None:
        self.failure_count += 1
        # Even a broken logging handler must not replace execution facts.
        try:
            _LOG.warning("fc_log_projection_failed")
        except Exception:
            pass

    def observe_ledger(self, ledger: TaskLedger, worker_id: str) -> None:
        """Read exact persisted routing/claim facts, outside authority transactions.

        The in-memory cursor only avoids duplicate reads during this process.
        Restarts may repeat source sequences; consumers must not sum snapshots.
        """
        try:
            with connection(ledger.path, timeout=0.05) as db:
                rows = db.execute(
                    "SELECT a.*, t.worker_id AS attempt_worker FROM task_audit a LEFT JOIN task_attempts t "
                    "ON t.swarm_id=a.swarm_id AND t.task_id=a.task_id AND t.token=json_extract(a.body,'$.token') "
                    "WHERE a.swarm_id=? AND a.sequence>? ORDER BY a.sequence",
                    (ledger.swarm_id, self._cursor),
                ).fetchall()
            for row in rows:
                self._cursor = row["sequence"]
                body = json.loads(row["body"])
                if row["event"] == "routing" and body["worker_id"] == worker_id:
                    candidates = [dict(signal, probability=probability) for signal, probability in
                                  zip(body["signals"], body["probabilities"], strict=True)]
                    self.emit("routing", task_id=body["selected"], at=row["at"], sequence=row["sequence"],
                              routing=dict(worker_id=worker_id, selected=body["selected"], candidates=candidates,
                                           filtered_task_ids=[item["task_id"] for item in body["filtered"]],
                                           beta=body["beta"], exploration=body["exploration"]))
                elif row["event"] in {"claimed", "released", "completed"} and row["attempt_worker"] == worker_id:
                    self.emit("claim", task_id=row["task_id"], at=row["at"], sequence=row["sequence"],
                              claim=dict(task_id=row["task_id"], worker_id=worker_id, token=body["token"],
                                         outcome="submitted" if row["event"] == "completed" else row["event"]))
        except Exception:
            self.diagnostic()
