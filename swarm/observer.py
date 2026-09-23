"""Bounded, strictly read-only health snapshots; never a worker decision input."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import time

from pydantic import JsonValue, TypeAdapter

from local_assets.paths import no_links

_JSON: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)
_TABLES = frozenset({"signals", "pipes", "accounts", "reservations", "assets", "reports", "promotions"})


def _stamp(path: Path) -> tuple[int, int] | None:
    if not path.exists():
        return None
    stat = path.stat()
    return stat.st_size, stat.st_mtime_ns


def read_database(path: Path, *, limit: int = 200) -> dict[str, JsonValue]:
    """Never create SQLite sidecars, recover a journal, checkpoint, or refresh.

    immutable=1 avoids even shared-memory creation. A hot journal/WAL means this
    view is unavailable, not silently stale. Concurrent changes discard the
    snapshot; callers may explicitly observe again later.
    """
    if not 1 <= limit <= 1000:
        raise ValueError("observer_limit_out_of_range")
    result: dict[str, JsonValue] = {"state": "missing", "tables": {}}
    try:
        no_links(path)
        if not path.is_file():
            return result
        related = [path, Path(str(path) + "-wal"), Path(str(path) + "-journal")]
        for entry in related:
            no_links(entry)
        before = [_stamp(entry) for entry in related]
        if any(stamp is not None and stamp[0] > 0 for stamp in before[1:]):
            return {"state": "busy", "reason": "uncheckpointed_or_active_writer", "tables": {}}
        db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro&immutable=1", uri=True, timeout=0)
        try:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA query_only=ON")
            tables: dict[str, JsonValue] = {}
            names = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            for name in sorted(names & _TABLES):
                rows: list[JsonValue] = []
                for row in db.execute(f'SELECT * FROM "{name}" LIMIT ?', (limit,)):
                    value: dict[str, JsonValue] = {}
                    for key in row.keys():
                        cell = row[key]
                        if key in {"body", "policy_json", "payload"} and isinstance(cell, str):
                            try:
                                cell = _JSON.validate_json(cell)
                            except ValueError:
                                cell = "invalid_json"
                        value[key] = _JSON.validate_python(cell)
                    rows.append(value)
                tables[name] = rows
        finally:
            db.close()
        if before != [_stamp(entry) for entry in related]:
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
        "field": read_database(state / "field.sqlite3", limit=limit),
        "budget": read_database(state / "budget.sqlite3", limit=limit),
        "validation": read_database(state / "assets" / "assets.sqlite3", limit=limit),
        "leases": read_records(state / "leases", limit=limit),
        "audit": read_records(state / "audit", limit=limit),
        "workers": read_records(state / "workers", limit=limit),
    }
    return {"observed_at": time.time(), "readonly": True,
            "health": "ok" if all(item["state"] == "ok" for item in sections.values()) else "partial",
            "sections": _JSON.validate_python(sections),
            "acceptance": {"provenance": "mock", "contract_local": "not_run",
                           "interface_live": "not_run", "task_live": "not_run"}}


def render(state: Path, *, limit: int = 200) -> str:
    return json.dumps(observe(state, limit=limit), ensure_ascii=False, indent=2)
