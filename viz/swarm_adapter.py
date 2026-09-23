"""Read-only projection of the decentralized swarm state for the T5 dashboard.

This module reuses ``swarm.observer.observe`` (or the underlying
``read_database`` / ``read_records``) so every link check, WAL-safe hot read,
no-sidecar guarantee and limit already enforced by the observer holds here too.
It never writes swarm state, never claims/advances tasks, never changes a lease,
budget hold, audit record or verification report, and never calls a model.

The observer exposes raw tables; this adapter projects them into a bounded,
JSON-only ``SwarmView`` the static page renders. All numbers are read, never
invented: route weights are decayed at read time (``exp(-dt/tau)``, matching
``swarm/pheromone.py``), aggregate acceptance stays ``not_run``, and Hub status stays
"待发布" until a real Hub sandbox is configured.
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

from swarm.observer import observe

SWARM_SCHEMA = "morph.swarm.readonly/1"
DEFAULT_TAU_SECONDS = 86400.0

# Fixed truth, never derived from input or a model.
HUB_STATUS = "待发布（未配置 Hub 沙箱）"
BOUNDARIES = [
    "严格只读：不认领、不推进、不改租约/审计/验证。",
    "不调用任何模型；不伪造 task_live。",
    "费用未知时保留 unknown，不显示为零。",
    "Hub 状态待发布；本地批准不等于 Hub promoted。",
    "租约态直接映射持久化任务状态；claimed 按 TTL 分为 leased/expired。",
]

def _as_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return None


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _as_str(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _tables(view: dict[str, Any], section: str) -> dict[str, list[dict[str, Any]]]:
    """Return {table_name: [row_dict]} from one observer section, or {}."""
    sections = _as_dict(view.get("sections"))
    block = _as_dict(sections.get(section))
    raw = _as_dict(block.get("tables"))
    result: dict[str, list[dict[str, Any]]] = {}
    for name, rows in raw.items():
        result[str(name)] = [row for row in _as_list(rows) if isinstance(row, dict)]
    return result


def _records(view: dict[str, Any], section: str) -> list[dict[str, Any]]:
    """Return the JSON records list of one observer section, or []."""
    sections = _as_dict(view.get("sections"))
    block = _as_dict(sections.get(section))
    return [row for row in _as_list(block.get("records")) if isinstance(row, dict)]


def _signal_of(task: dict[str, Any]) -> dict[str, Any]:
    """Parse the persisted ``signal`` JSON text without inventing fields."""
    raw = task.get("signal")
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except ValueError:
            return {}
    return {}


def _lease_state(task: dict[str, Any], now: float) -> str:
    """Map the durable task status directly to a read-time lease state.

    ``lease_state`` is a projection of ``status``, never a re-derivation from
    attempt history. Only ``claimed`` is split into leased/expired by its TTL;
    every other durable status (partial/handoff/blocked/submitting/completed/
    failed/available) passes through unchanged, so the raw ``status`` field and
    ``lease_state`` can never contradict each other.
    """
    status = _as_str(task.get("status")) or "available"
    if status == "claimed":
        expiry = _as_float(task.get("expiry"))
        return "expired" if (expiry is not None and expiry <= now) else "leased"
    return status


def _as_bool(value: Any) -> bool:
    """SQLite stores ``effect_applied`` as INTEGER 0/1, not bool."""
    if isinstance(value, bool):
        return value
    return _as_int(value) == 1


def _workers(view: dict[str, Any]) -> list[dict[str, Any]]:
    """Union of worker status files, task owners, budget workers and route workers."""
    by_id: dict[str, dict[str, Any]] = {}
    for record in _records(view, "workers"):
        worker_id = _as_str(record.get("worker_id"))
        if not worker_id:
            continue
        by_id[worker_id] = {
            "worker_id": worker_id,
            "pid": _as_int(record.get("pid")),
            "state": _as_str(record.get("state")),
            "reason": _as_str(record.get("reason")),
            "remaining_energy": _as_int(record.get("remaining_energy")),
            "completed": _as_int(record.get("completed")),
            "updated_at": _as_float(record.get("updated_at")),
            "provenance": _as_str(record.get("provenance")),
            "usage_source": _as_str(record.get("usage_source")),
            "evidence_class": _as_str(record.get("evidence_class")),
        }
    for row in _tables(view, "ledger").get("tasks", []):
        owner = _as_str(row.get("owner"))
        if owner and owner not in by_id:
            by_id[owner] = {"worker_id": owner, "state": "unknown"}
    for row in _tables(view, "budget").get("budget_reservations", []):
        worker_id = _as_str(row.get("worker_id"))
        if worker_id and worker_id not in by_id:
            by_id[worker_id] = {"worker_id": worker_id, "state": "unknown"}
    for row in _tables(view, "field").get("pipe_history", []):
        worker_id = _as_str(row.get("worker_id"))
        if worker_id and worker_id not in by_id:
            by_id[worker_id] = {"worker_id": worker_id, "state": "unknown"}
    return sorted(by_id.values(), key=lambda item: item["worker_id"])


def _tasks(view: dict[str, Any], now: float) -> list[dict[str, Any]]:
    ledger = _tables(view, "ledger")
    attempts_by_task: dict[str, list[dict[str, Any]]] = {}
    for row in ledger.get("task_attempts", []):
        task_id = _as_str(row.get("task_id"))
        if not task_id:
            continue
        attempts_by_task.setdefault(task_id, []).append({
            "token": _as_int(row.get("token")),
            "worker_id": _as_str(row.get("worker_id")),
            "started_at": _as_float(row.get("started_at")),
            "finished_at": _as_float(row.get("finished_at")),
            "outcome": _as_str(row.get("outcome")),
        })
    deps_by_task: dict[str, list[str]] = {}
    for row in ledger.get("dependencies", []):
        task_id = _as_str(row.get("task_id"))
        dependency = _as_str(row.get("dependency_id"))
        if task_id and dependency:
            deps_by_task.setdefault(task_id, []).append(dependency)
    result: list[dict[str, Any]] = []
    for task in ledger.get("tasks", []):
        task_id = _as_str(task.get("task_id")) or ""
        signal = _signal_of(task)
        attempt_history = sorted(attempts_by_task.get(task_id, []), key=lambda a: _as_int(a.get("token")) or 0)
        deps = sorted(set(deps_by_task.get(task_id, [])))
        result.append({
            "task_id": task_id,
            "module": _as_str(task.get("module")),
            "capability": _as_str(task.get("capability")),
            "scope": _as_str(task.get("scope")),
            "workspace": _as_str(task.get("workspace")),
            "kind": _as_str(signal.get("kind")),
            "status": _as_str(task.get("status")),
            "lease_state": _lease_state(task, now),
            "attempts": _as_int(task.get("attempts")),
            "token": _as_int(task.get("token")),
            "owner": _as_str(task.get("owner")),
            "expires_at": _as_float(task.get("expiry")),
            "created_at": _as_float(task.get("created_at")),
            "updated_at": _as_float(task.get("updated_at")),
            "derived_from": _as_str(task.get("derived_from")),
            "result_id": _as_str(task.get("result_id")),
            "effect_applied": _as_bool(task.get("effect_applied")),
            "dependencies": deps,
            "attempt_history": attempt_history,
        })
    result.sort(key=lambda item: item["task_id"])
    return result


def _tau_of(view: dict[str, Any]) -> float:
    for row in _tables(view, "field").get("preference_config", []):
        tau = _as_float(row.get("tau"))
        if tau is not None and tau > 0:
            return tau
    return DEFAULT_TAU_SECONDS


def _routes(view: dict[str, Any], now: float, tau: float) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in _tables(view, "field").get("pipe_history", []):
        worker_id = _as_str(row.get("worker_id"))
        pipe_key = _as_str(row.get("pipe_key"))
        if not worker_id or not pipe_key:
            continue
        weight = _as_float(row.get("weight"))
        updated_at = _as_float(row.get("updated_at"))
        elapsed = max(0.0, now - updated_at) if updated_at is not None else None
        decayed = (weight * math.exp(-elapsed / tau)) if (weight is not None and elapsed is not None) else weight
        result.append({
            "worker_id": worker_id,
            "pipe_key": pipe_key,
            "weight": weight,
            "samples": _as_int(row.get("samples")),
            "updated_at": updated_at,
            "decayed_weight": decayed,
            "tau_seconds": tau,
        })
    result.sort(key=lambda item: (item["worker_id"], item["pipe_key"]))
    return result


def _signals(view: dict[str, Any], now: float, tau: float) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in _tables(view, "field").get("pheromones", []):
        signal_id = _as_str(row.get("signal_id"))
        task_id = _as_str(row.get("task_id"))
        if not signal_id:
            continue
        concentration = _as_float(row.get("concentration"))
        updated_at = _as_float(row.get("updated_at"))
        multiplier = _as_float(row.get("multiplier"))
        tau_effective = tau / (multiplier if (multiplier is not None and multiplier > 0) else 1.0)
        elapsed = max(0.0, now - updated_at) if updated_at is not None else None
        decayed = (concentration * math.exp(-elapsed / tau_effective)) if (concentration is not None and elapsed is not None) else concentration
        result.append({
            "signal_id": signal_id,
            "task_id": task_id,
            "concentration": concentration,
            "multiplier": multiplier,
            "updated_at": updated_at,
            "decayed_concentration": decayed,
            "tau_seconds": tau_effective,
        })
    result.sort(key=lambda item: item["signal_id"])
    return result


def _budget(view: dict[str, Any]) -> dict[str, Any]:
    tables = _tables(view, "budget")
    breaker = None
    admission_control = None
    for row in tables.get("swarm_budgets", []):
        breaker = _as_str(row.get("breaker"))
        policy = _as_dict(row.get("policy_json"))
        admission_control = _as_str(policy.get("admission_control"))
        allow_unknown_cost = policy.get("allow_unknown_cost") is True
        break
    else:
        allow_unknown_cost = False
    reservations: list[dict[str, Any]] = []
    for row in tables.get("budget_reservations", []):
        status = _as_str(row.get("status"))
        state = {"pending": "reserved", "settled": "settled", "uncertain": "unknown",
                 "unknown_cost_allowed": "unknown_cost_allowed"}.get(status or "", "unknown")
        reservations.append({
            "reservation_id": _as_str(row.get("reservation_id")),
            "worker_id": _as_str(row.get("worker_id")),
            "task_id": _as_str(row.get("task_id")),
            "request_id": _as_str(row.get("request_id")),
            "state": state,
            "reserved_usd": _as_float(row.get("reserved_usd")),
            "estimate_usd": _as_float(row.get("estimate_usd")),
            "admitted_usd": _as_float(row.get("admitted_usd")),
            "tokens": _as_int(row.get("tokens")),
            "usage_metering": _as_str(row.get("usage_metering")),
            "request_bound": _as_str(row.get("request_bound")),
            "cost": _as_str(row.get("cost")),
            "created_at": _as_float(row.get("created_at")),
            "settled_at": _as_float(row.get("settled_at")),
        })
    reservations.sort(key=lambda item: (item["created_at"] is None, item["created_at"], item["reservation_id"]))
    pending_hold = sum((r["reserved_usd"] or 0.0) for r in reservations if r["state"] == "reserved")
    unknown_hold = sum((r["reserved_usd"] or 0.0) for r in reservations if r["state"] == "unknown")
    admitted = sum((r["admitted_usd"] or 0.0) for r in reservations)
    return {
        "breaker": breaker,
        "admission_control": admission_control,
        "allow_unknown_cost": allow_unknown_cost,
        "reservations": reservations,
        "totals": {
            "pending_hold_usd": pending_hold,
            "unknown_hold_usd": unknown_hold,
            "allowed_unknown_cost_hold_usd": sum((r["reserved_usd"] or 0.0) for r in reservations if r["state"] == "unknown_cost_allowed"),
            "total_hold_usd": sum((r["reserved_usd"] or 0.0) for r in reservations if r["state"] != "settled"),
            "admitted_usd": admitted,
            "reserved": sum(1 for r in reservations if r["state"] == "reserved"),
            "settled": sum(1 for r in reservations if r["state"] == "settled"),
            "unknown": sum(1 for r in reservations if r["state"] == "unknown"),
            "unknown_cost_allowed": sum(1 for r in reservations if r["state"] == "unknown_cost_allowed"),
        },
    }


def _audit(view: dict[str, Any]) -> list[dict[str, Any]]:
    """Task lifecycle audit stream (SQL ``task_audit``) plus worker audit records."""
    ledger = _tables(view, "ledger")
    result: list[dict[str, Any]] = []
    for row in ledger.get("task_audit", []):
        result.append({
            "sequence": _as_int(row.get("sequence")),
            "task_id": _as_str(row.get("task_id")),
            "event": _as_str(row.get("event")),
            "at": _as_float(row.get("at")),
            "body": _as_dict(row.get("body")),
        })
    result.sort(key=lambda item: (item["sequence"] is None, item["sequence"] or 0), reverse=True)
    return result


def _worker_audit(view: dict[str, Any]) -> list[dict[str, Any]]:
    """Sanitized per-attempt worker audit facts (asset_id, usage class, provenance)."""
    result: list[dict[str, Any]] = []
    for record in _records(view, "audit"):
        worker_id = _as_str(record.get("worker_id"))
        task_id = _as_str(record.get("task_id"))
        if not worker_id and not task_id:
            continue
        result.append({
            "worker_id": worker_id,
            "task_id": task_id,
            "outcome": _as_str(record.get("outcome")),
            "asset_id": _as_str(record.get("asset_id")),
            "result_id": _as_str(record.get("result_id")),
            "consumed_asset_ids": [v for v in _as_list(record.get("consumed_asset_ids")) if isinstance(v, str)],
            "provenance": _as_str(record.get("provenance")),
            "evidence_class": _as_str(record.get("evidence_class")),
            "interface_live": _as_str(record.get("interface_live")),
            "task_live": _as_str(record.get("task_live")),
            "requested_model": _as_str(record.get("requested_model")),
            "returned_model": _as_str(record.get("returned_model")),
            "created_at": _as_float(record.get("created_at")),
        })
    result.sort(key=lambda item: (item["created_at"] is None, item["created_at"]))
    return result


def _adoption_chain(view: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Trace assets across producers and adopters, keyed by ``asset_id``.

    ``adoptions`` rows carry the full ``AdoptionReceipt``; ``approvals`` rows
    carry the promotion receipt proving a local approved state. No asset id is
    ever inferred from a payload.
    """
    validation = _tables(view, "validation")
    adoptions: list[dict[str, Any]] = []
    for row in validation.get("adoptions", []):
        body = _as_dict(row.get("body"))
        context = _as_dict(body.get("context"))
        adoptions.append({
            "execution_id": _as_str(row.get("execution_id")),
            "asset_id": _as_str(body.get("asset_id")),
            "candidate_asset_id": _as_str(body.get("candidate_asset_id")),
            "task_id": _as_str(context.get("task_id")),
            "worker_id": _as_str(context.get("worker_id")),
            "result_id": _as_str(body.get("result_id")),
            "adopted_at": _as_float(body.get("adopted_at")),
        })
    adoptions.sort(key=lambda item: (item["adopted_at"] is None, item["adopted_at"], item["asset_id"]))
    promotions: list[dict[str, Any]] = []
    for row in validation.get("approvals", []):
        body = _as_dict(row.get("body"))
        promotions.append({
            "asset_id": _as_str(row.get("asset_id")) or _as_str(body.get("asset_id")),
            "report_id": _as_str(row.get("report_id")) or _as_str(body.get("report_id")),
            "promoted_at": _as_float(body.get("promoted_at")),
            "policy_version": _as_str(body.get("policy_version")),
        })
    promotions.sort(key=lambda item: (item["promoted_at"] is None, item["promoted_at"], item["asset_id"]))
    return adoptions, promotions


def _acceptance(view: dict[str, Any]) -> dict[str, str]:
    """Classify explicit audit provenance without promoting global acceptance."""
    records = _worker_audit(view)
    provenances = {record["provenance"] for record in records if record.get("provenance") in {"live", "mock"}}
    provenance = next(iter(provenances)) if len(provenances) == 1 else "unverified"

    return {
        "provenance": provenance,
        "contract_local": "not_run",
        "interface_live": "not_run",
        "task_live": "not_run",
    }


def _source_sections(view: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for name, raw in _as_dict(view.get("sections")).items():
        section = _as_dict(raw)
        result[str(name)] = {
            "state": _as_str(section.get("state")) or "unavailable",
            "reason": _as_str(section.get("reason")),
            "row_limit": _as_int(section.get("row_limit")),
        }
    return result


def project(view: dict[str, Any], *, now: float | None = None, replay: bool = False) -> dict[str, Any]:
    """Project one ``observe`` result into a JSON-only SwarmView dict."""
    observed_at = _as_float(view.get("observed_at")) if now is None else now
    if observed_at is None:
        observed_at = time.time()
    health = _as_str(view.get("health")) or "partial"
    tau = _tau_of(view)
    adoptions, promotions = _adoption_chain(view)
    acceptance = _acceptance(view)
    if replay:
        acceptance = {**acceptance, "provenance": "replay", "interface_live": "not_run", "task_live": "not_run"}
    return {
        "schema": SWARM_SCHEMA,
        "observed_at": observed_at,
        "readonly": True,
        "health": health,
        "sources": _source_sections(view),
        "hub_status": HUB_STATUS,
        "acceptance": acceptance,
        "workers": _workers(view),
        "tasks": _tasks(view, observed_at),
        "routes": _routes(view, observed_at, tau),
        "signals": _signals(view, observed_at, tau),
        "budget": _budget(view),
        "audit": _audit(view),
        "worker_audit": _worker_audit(view),
        "assets": adoptions,
        "promotions": promotions,
        "boundaries": BOUNDARIES,
    }


def empty_swarm(note: str = "未配置蜂群状态目录；/api/swarm 保持空态。") -> dict[str, Any]:
    """A degraded but stable view when no swarm state directory is configured."""
    return {
        "schema": SWARM_SCHEMA,
        "observed_at": time.time(),
        "readonly": True,
        "health": "missing",
        "hub_status": HUB_STATUS,
        "acceptance": {"provenance": "unverified", "contract_local": "not_run",
                       "interface_live": "not_run", "task_live": "not_run"},
        "sources": {},
        "workers": [],
        "tasks": [],
        "routes": [],
        "signals": [],
        "budget": {"breaker": None, "admission_control": None, "reservations": [],
                   "totals": {"pending_hold_usd": 0.0, "unknown_hold_usd": 0.0,
                              "total_hold_usd": 0.0, "admitted_usd": 0.0,
                              "reserved": 0, "settled": 0, "unknown": 0}},
        "audit": [],
        "worker_audit": [],
        "assets": [],
        "promotions": [],
        "boundaries": BOUNDARIES,
        "notes": [note],
    }


def load_swarm(state: Path, *, limit: int = 200, replay: bool = False) -> dict[str, Any]:
    """Read the swarm state through the observer and project it for the page."""
    if not 1 <= limit <= 1000:
        raise ValueError("observer_limit_out_of_range")
    if not state.is_dir():
        return empty_swarm("已配置的蜂群状态目录不存在。")
    return project(observe(state, limit=limit), replay=replay)
