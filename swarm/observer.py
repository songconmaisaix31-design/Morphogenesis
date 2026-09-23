"""Bounded, strictly read-only health snapshots; never a worker decision input."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import time

from pydantic import JsonValue, TypeAdapter

from local_assets.paths import no_links

_JSON: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)
_TABLES = frozenset({
    "signals", "pipes", "accounts", "reservations", "assets", "reports", "promotions",
    "tasks", "dependencies", "attempts", "leases", "audit", "runs", "routing_audit",
    "applications", "adoptions", "injections", "approvals", "consumptions", "asset_states", "mirror_states",
    "swarm_runs", "task_evidence", "task_attempts", "task_audit", "swarm_budgets",
    "budget_reservations", "preference_config", "pheromones", "pipe_history",
})


def _stamp(path: Path) -> tuple[int, int] | None:
    if not path.exists():
        return None
    stat = path.stat()
    return stat.st_size, stat.st_mtime_ns


def read_database(path: Path, *, limit: int = 200) -> dict[str, JsonValue]:
    """Never create SQLite sidecars, recover a journal, checkpoint, or refresh.

    Existing hot WAL is read with mode=ro and query_only. SQLite may update SHM
    reader marks/locks; no business data, schema, expiry or checkpoint is changed.
    Without sidecars immutable=1 prevents their creation. Incomplete WAL pairs or
    recovery journals are unavailable. A changed payload discards the snapshot.
    """
    if not 1 <= limit <= 1000:
        raise ValueError("observer_limit_out_of_range")
    result: dict[str, JsonValue] = {"state": "missing", "tables": {}}
    try:
        no_links(path)
        if not path.is_file():
            return result
        related = [path, Path(str(path) + "-wal"), Path(str(path) + "-journal"), Path(str(path) + "-shm")]
        for entry in related:
            no_links(entry)
        before = [_stamp(entry) for entry in related]
        hot_wal = before[1] is not None and before[1][0] > 0
        if ((before[2] is not None and before[2][0] > 0) or (hot_wal and before[3] is None)):
            return {"state": "busy", "reason": "uncheckpointed_or_active_writer", "tables": {}}
        uri = path.resolve().as_uri() + ("?mode=ro" if hot_wal else "?mode=ro&immutable=1")
        db = sqlite3.connect(uri, uri=True, timeout=0)
        try:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA query_only=ON")
            db.execute("BEGIN")
            tables: dict[str, JsonValue] = {}
            names = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            for name in sorted(names & _TABLES):
                rows: list[JsonValue] = []
                for row in db.execute(f'SELECT * FROM "{name}" LIMIT ?', (limit,)):
                    value: dict[str, JsonValue] = {}
                    for key in row.keys():
                        cell = row[key]
                        if (key in {"body", "payload", "result", "acceptance"} or key.endswith("_json")) and isinstance(cell, str):
                            try:
                                cell = _JSON.validate_json(cell)
                            except ValueError:
                                cell = "invalid_json"
                        value[key] = _JSON.validate_python(cell)
                    rows.append(value)
                tables[name] = rows
        finally:
            db.close()
        if before[:3] != [_stamp(entry) for entry in related[:3]]:
            return {"state": "busy", "reason": "changed_during_observation", "tables": {}}
        return {"state": "ok", "tables": tables, "row_limit": limit}
    except (OSError, ValueError, sqlite3.Error):
        return {"state": "unavailable", "reason": "readonly_snapshot_failed", "tables": {}}


def read_records(root: Path, *, limit: int = 200) -> dict[str, JsonValue]:
    """Read existing JSON evidence only; no directory creation or lease expiry."""
    if not 1 <= limit <= 1000:
        raise ValueError("observer_limit_out_of_range")
    try:
        no_links(root)
        if not root.is_dir():
            return {"state": "missing", "records": []}
        records: list[JsonValue] = []
        for path in root.rglob("*.json"):
            if len(records) >= limit:
                break
            no_links(path)
            if path.stat().st_size > 2_000_000:
                records.append({"state": "oversize_record"})
                continue
            try:
                records.append(_JSON.validate_json(path.read_bytes()))
            except (OSError, ValueError):
                records.append({"state": "incomplete_record"})
        return {"state": "ok", "records": records, "row_limit": limit}
    except (OSError, ValueError):
        return {"state": "unavailable", "records": []}


def observe(state: Path, *, limit: int = 200) -> dict[str, JsonValue]:
    """The observer imports no field, router, budget, lease, or worker object."""
    sections = {
        "ledger": read_database(state / "tasks.sqlite3", limit=limit),
        "field": read_database(state / "field.sqlite3", limit=limit),
        "budget": read_database(state / "budget.sqlite3", limit=limit),
        "validation": read_database(state / "assets" / "assets.sqlite3", limit=limit),
        "leases": read_database(state / "tasks.sqlite3", limit=limit),
        "audit": read_records(state / "audit", limit=limit),
        "workers": read_records(state / "workers", limit=limit),
        "mirror": read_mirror(state / "mirror", limit=limit),
    }
    return {"observed_at": time.time(), "readonly": True,
            "health": "ok" if all(item["state"] == "ok" for item in sections.values()) else "partial",
            "sections": _JSON.validate_python(sections),
            "acceptance": {"provenance": "mock", "contract_local": "not_run",
                           "interface_live": "not_run", "task_live": "not_run"}}


def render(state: Path, *, limit: int = 200) -> str:
    return json.dumps(observe(state, limit=limit), ensure_ascii=False, indent=2)


def read_mirror(directory: Path, *, limit: int = 200) -> dict[str, JsonValue]:
    """Project adapter receipts into four states without changing source evidence.

    Confirmed is transport acknowledgment, never a claim of Hub promotion.
    Payload/credentials and untrusted exception strings are excluded from this view.
    """
    view = read_records(directory, limit=limit)
    source = view.get("records")
    records: list[JsonValue] = []
    if isinstance(source, list):
        for row in source:
            if not isinstance(row, dict):
                continue
            adapter_state = row.get("state")
            state = ("confirmed" if adapter_state in {"received", "candidate", "promoted"}
                     else adapter_state if adapter_state in {"pending", "unknown", "rejected"}
                     else "unknown")
            records.append({"state": state, "adapter_state": adapter_state,
                            "provenance": row.get("provenance"), "source": row.get("source"),
                            "hub_promoted": adapter_state == "promoted",
                            "acceptance": row.get("acceptance")})
    return {"state": view["state"], "records": records, "row_limit": limit}
