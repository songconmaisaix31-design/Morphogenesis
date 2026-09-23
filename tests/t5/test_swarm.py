"""V-track decentralized swarm view: read-only projection + /api/swarm endpoint.

No test here writes swarm state, claims a task, changes a lease, budget hold,
audit or verification record, and none calls a model. The projection is
exercised with synthetic ``observe``-shaped views (pure function) and against a
real temporary SQLite/JSON state directory (real local read, no network).
"""

import json
import math
import sqlite3
import tempfile
import threading
import time
import unittest
import urllib.request
from pathlib import Path
from typing import Any

from http.server import ThreadingHTTPServer

from viz.adapter import empty_dashboard
from viz.server import DashboardHandler
from viz.swarm_adapter import (
    SWARM_SCHEMA,
    empty_swarm,
    load_swarm,
    project,
)


def _db(state: str = "ok", tables: dict[str, list[dict[str, Any]]] | None = None) -> dict[str, Any]:
    return {"state": state, "tables": tables or {}, "row_limit": 200}


def _records(state: str = "ok", records: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {"state": state, "records": records or [], "row_limit": 200}


def _view(sections: dict[str, Any], observed_at: float = 1000.0) -> dict[str, Any]:
    return {
        "observed_at": observed_at,
        "readonly": True,
        "health": "ok" if all(s.get("state") == "ok" for s in sections.values() if isinstance(s, dict)) else "partial",
        "sections": sections,
        "acceptance": {"provenance": "mock", "contract_local": "not_run",
                       "interface_live": "not_run", "task_live": "not_run"},
    }


def _task(task_id: str, status: str = "available", *, attempts: int = 0, owner: str | None = None,
          expiry: float | None = None, token: int = 0) -> dict[str, Any]:
    return {
        "swarm_id": "swarm", "task_id": task_id, "workspace": "/ws", "scope": "module_0",
        "module": "module_0", "capability": "repair", "signal": json.dumps({"kind": "error_pattern"}),
        "status": status, "acceptance": {}, "attempts": attempts, "token": token, "owner": owner,
        "expiry": expiry, "created_at": 900.0, "updated_at": 900.0, "derived_from": None,
        "result_id": None, "result": None, "effect_applied": 0,
    }


class ProjectionTests(unittest.TestCase):
    def test_lease_states_are_classified_without_mutation(self) -> None:
        tasks = [
            _task("leased", "claimed", owner="w1", expiry=2000.0, token=1, attempts=1),
            _task("expired", "claimed", owner="w1", expiry=900.0, token=1, attempts=1),
            _task("partial", "submitting", owner="w1", token=1, attempts=1),
            _task("completed", "completed", owner="w1", token=1, attempts=1),
            _task("failed", "failed", owner="w1", token=2, attempts=3),
            _task("handoff", "available", attempts=2, token=2),
            _task("available", "available", attempts=0),
        ]
        attempts = [
            {"swarm_id": "swarm", "task_id": "handoff", "token": 1, "worker_id": "w1",
             "started_at": 910.0, "finished_at": 920.0, "outcome": "expired", "evidence": None},
            {"swarm_id": "swarm", "task_id": "handoff", "token": 2, "worker_id": "w2",
             "started_at": 930.0, "finished_at": 940.0, "outcome": "released", "evidence": None},
        ]
        view = _view({"ledger": _db(tables={"tasks": tasks, "task_attempts": attempts, "dependencies": []})})
        result = project(view, now=1000.0)
        by_id = {task["task_id"]: task["lease_state"] for task in result["tasks"]}
        self.assertEqual("leased", by_id["leased"])
        self.assertEqual("expired", by_id["expired"])
        self.assertEqual("partial", by_id["partial"])
        self.assertEqual("completed", by_id["completed"])
        self.assertEqual("failed", by_id["failed"])
        self.assertEqual("handoff", by_id["handoff"])
        self.assertEqual("available", by_id["available"])

    def test_dependencies_are_read_not_inferred(self) -> None:
        deps = [
            {"swarm_id": "swarm", "task_id": "t1", "dependency_id": "t0"},
            {"swarm_id": "swarm", "task_id": "t1", "dependency_id": "t2"},
        ]
        view = _view({"ledger": _db(tables={"tasks": [_task("t1"), _task("t0")], "dependencies": deps})})
        result = project(view, now=1000.0)
        task = next(t for t in result["tasks"] if t["task_id"] == "t1")
        self.assertEqual(["t0", "t2"], task["dependencies"])

    def test_route_weights_decay_at_read_time(self) -> None:
        field = {
            "preference_config": [{"swarm_id": "swarm", "tau": 100.0, "alpha": 0.05}],
            "pipe_history": [
                {"swarm_id": "swarm", "worker_id": "w1", "pipe_key": "repair", "weight": 1.0, "samples": 4, "updated_at": 1000.0},
                {"swarm_id": "swarm", "worker_id": "w1", "pipe_key": "optimize", "weight": 1.0, "samples": 2, "updated_at": 900.0},
            ],
            "pheromones": [
                {"swarm_id": "swarm", "signal_id": "s1", "task_id": "t1", "concentration": 2.0,
                 "updated_at": 900.0, "multiplier": 2.0},
            ],
        }
        view = _view({"field": _db(tables=field)})
        result = project(view, now=1000.0)
        routes = {route["pipe_key"]: route for route in result["routes"]}
        self.assertAlmostEqual(1.0, routes["repair"]["decayed_weight"])
        self.assertAlmostEqual(math.exp(-1.0), routes["optimize"]["decayed_weight"])
        # pheromone uses tau / multiplier = 50.0; elapsed 100 -> exp(-2)
        self.assertEqual(1, len(result["signals"]))
        self.assertAlmostEqual(2.0 * math.exp(-2.0), result["signals"][0]["decayed_concentration"])

    def test_budget_reservations_map_to_reserved_settled_unknown(self) -> None:
        budget = {
            "swarm_budgets": [{"swarm_id": "swarm", "policy_json": {"admission_control": "enabled"},
                               "breaker": None, "started_at": 0.0}],
            "budget_reservations": [
                {"reservation_id": "r1", "swarm_id": "swarm", "worker_id": "w1", "task_id": "t1",
                 "body": "{}", "status": "pending", "created_at": 1.0, "settled_at": None, "tokens": None,
                 "estimate_usd": None, "reserved_usd": 2.0, "request_id": "t1:1", "usage_metering": "unknown",
                 "request_bound": "unbounded", "admission_control": "enabled", "cost": "unknown",
                 "settlement": None, "admitted_usd": None},
                {"reservation_id": "r2", "swarm_id": "swarm", "worker_id": "w1", "task_id": "t2",
                 "body": "{}", "status": "settled", "created_at": 2.0, "settled_at": 3.0, "tokens": 4,
                 "estimate_usd": 0.5, "reserved_usd": 0.5, "request_id": "t2:1", "usage_metering": "verified",
                 "request_bound": "verified", "admission_control": "enabled", "cost": "estimated",
                 "settlement": "[1,1,2]", "admitted_usd": 0.5},
                {"reservation_id": "r3", "swarm_id": "swarm", "worker_id": "w2", "task_id": "t3",
                 "body": "{}", "status": "uncertain", "created_at": 3.0, "settled_at": 4.0, "tokens": None,
                 "estimate_usd": None, "reserved_usd": 1.0, "request_id": "t3:1", "usage_metering": "unknown",
                 "request_bound": "unbounded", "admission_control": "enabled", "cost": "unknown",
                 "settlement": None, "admitted_usd": None},
            ],
        }
        view = _view({"budget": _db(tables=budget)})
        result = project(view, now=1000.0)
        states = {r["reservation_id"]: r["state"] for r in result["budget"]["reservations"]}
        self.assertEqual({"r1": "reserved", "r2": "settled", "r3": "unknown"}, states)
        totals = result["budget"]["totals"]
        self.assertEqual(1, totals["reserved"])
        self.assertEqual(1, totals["settled"])
        self.assertEqual(1, totals["unknown"])
        self.assertAlmostEqual(2.0, totals["reserved_usd"])
        self.assertAlmostEqual(0.5, totals["admitted_usd"])

    def test_adoption_chain_and_promotions_are_traceable_by_asset_id(self) -> None:
        adoption = {
            "asset_id": "sha256:aa", "candidate_asset_id": "sha256:bb", "result_id": "result-1",
            "adopted_at": 1234.0,
            "context": {"swarm_id": "swarm", "task_id": "t1", "worker_id": "w2", "fencing_token": 1,
                        "execution_id": "e1", "scope": "module_0"},
        }
        promotion = {"asset_id": "sha256:aa", "report_id": "report-1", "promoted_at": 1200.0,
                     "policy_version": "fixture-files-v1"}
        view = _view({"validation": _db(tables={
            "adoptions": [{"execution_id": "e1", "body": adoption}],
            "approvals": [{"asset_id": "sha256:aa", "report_id": "report-1", "body": promotion}],
        })})
        result = project(view, now=1000.0)
        self.assertEqual(1, len(result["assets"]))
        self.assertEqual("sha256:aa", result["assets"][0]["asset_id"])
        self.assertEqual("t1", result["assets"][0]["task_id"])
        self.assertEqual("w2", result["assets"][0]["worker_id"])
        self.assertEqual(1, len(result["promotions"]))
        self.assertEqual("sha256:aa", result["promotions"][0]["asset_id"])

    def test_workers_union_includes_owners_and_route_workers(self) -> None:
        view = _view({
            "workers": _records(records=[{"worker_id": "w1", "pid": 1, "state": "active"}]),
            "ledger": _db(tables={"tasks": [_task("t1", "completed", owner="w2")]}),
            "budget": _db(tables={"budget_reservations": [
                {"worker_id": "w3", "reservation_id": "r1", "status": "settled"}]}),
            "field": _db(tables={"pipe_history": [
                {"worker_id": "w4", "pipe_key": "repair", "weight": 0.5, "samples": 1, "updated_at": 1.0}]}),
        })
        result = project(view, now=1000.0)
        ids = {worker["worker_id"] for worker in result["workers"]}
        self.assertEqual({"w1", "w2", "w3", "w4"}, ids)

    def test_acceptance_never_promotes_a_live_claim(self) -> None:
        view = _view({"ledger": _db(tables={"tasks": [_task("t1", "completed", attempts=1)]})})
        view["acceptance"] = {"provenance": "live", "contract_local": "passed",
                              "interface_live": "passed", "task_live": "passed"}
        result = project(view, now=1000.0)
        self.assertEqual("not_run", result["acceptance"]["interface_live"])
        self.assertEqual("not_run", result["acceptance"]["task_live"])
        self.assertEqual("mock", result["acceptance"]["provenance"])
        self.assertEqual(SWARM_SCHEMA, result["schema"])
        json.dumps(result)

    def test_empty_swarm_is_degraded_not_claimed(self) -> None:
        view = empty_swarm()
        self.assertEqual("missing", view["health"])
        self.assertEqual("not_run", view["acceptance"]["task_live"])
        self.assertEqual([], view["workers"])
        self.assertIn("待发布", view["hub_status"])
        json.dumps(view)


class LoadSwarmTests(unittest.TestCase):
    """Real local SQLite read through the observer; no network, no writes."""

    def setUp(self) -> None:
        # ignore_cleanup_errors: Windows keeps a read-only SQLite mapping alive
        # briefly after the observer closes its connection; cleanup is deferred.
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _snapshot(self) -> dict[str, tuple[bytes, int]]:
        return {str(p.relative_to(self.root)): (p.read_bytes(), p.stat().st_mtime_ns)
                for p in self.root.rglob("*") if p.is_file()}

    def test_observing_missing_state_never_creates_it(self) -> None:
        state = self.root / "missing"
        view = load_swarm(state)
        self.assertEqual("partial", view["health"])
        self.assertEqual([], view["workers"])
        self.assertEqual([], view["tasks"])
        self.assertFalse(state.exists())

    def test_load_swarm_projects_real_sqlite_and_mutates_nothing(self) -> None:
        field = self.root / "field.sqlite3"
        with sqlite3.connect(field) as db:
            db.execute("CREATE TABLE preference_config (swarm_id TEXT, tau REAL, alpha REAL)")
            db.execute("INSERT INTO preference_config VALUES ('swarm', 100.0, 0.05)")
            db.execute("CREATE TABLE pipe_history (swarm_id TEXT, worker_id TEXT, pipe_key TEXT, "
                       "weight REAL, samples INTEGER, updated_at REAL)")
            db.execute("INSERT INTO pipe_history VALUES ('swarm', 'w1', 'repair', 1.0, 3, 1000.0)")
        tasks_db = self.root / "tasks.sqlite3"
        future = time.time() + 3600.0
        with sqlite3.connect(tasks_db) as db:
            db.execute("CREATE TABLE tasks (swarm_id TEXT, task_id TEXT, workspace TEXT, scope TEXT, module TEXT, "
                       "capability TEXT, signal TEXT, status TEXT, acceptance TEXT, attempts INTEGER, token INTEGER, "
                       "owner TEXT, expiry REAL, created_at REAL, updated_at REAL, derived_from TEXT, result_id TEXT, "
                       "result TEXT, effect_applied INTEGER)")
            db.execute("INSERT INTO tasks VALUES ('swarm', 't1', '/ws', 'module_0', 'module_0', 'repair', "
                       "'{\"kind\":\"error_pattern\"}', 'claimed', '{}', 1, 1, 'w1', ?, 900.0, 900.0, "
                       "NULL, NULL, NULL, 0)", (future,))
        before = self._snapshot()
        view = load_swarm(self.root)
        self.assertEqual(SWARM_SCHEMA, view["schema"])
        self.assertEqual(1, len(view["routes"]))
        self.assertEqual("repair", view["routes"][0]["pipe_key"])
        self.assertEqual(1, len(view["tasks"]))
        self.assertEqual("leased", view["tasks"][0]["lease_state"])
        self.assertEqual(self._snapshot(), before)


class SwarmRouteTests(unittest.TestCase):
    """Real local HTTP against the real handler; the swarm stays a local read."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        root = Path(self.temp_dir.name)
        self.state = root / "state"

        def handler(*args: Any, **kwargs: Any) -> DashboardHandler:
            return DashboardHandler(
                *args, directory=str(root), dashboard_loader=empty_dashboard,
                echarts_asset=root / "missing.js", evomap_service=None, **kwargs,
            )

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.temp_dir.cleanup()

    def _get(self, path: str, method: str = "GET", body: bytes | None = None) -> tuple[int, dict[str, Any] | None]:
        request = urllib.request.Request(self.base + path, data=body, method=method)
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as error:
            try:
                return error.code, json.loads(error.read())
            except ValueError:
                # send_error bodies (e.g. 405) are HTML, not the JSON contract.
                return error.code, None

    def test_swarm_route_returns_the_degraded_contract_without_state(self) -> None:
        status, body = self._get("/api/swarm")
        self.assertEqual(200, status)
        self.assertEqual(SWARM_SCHEMA, body["schema"])
        self.assertEqual("missing", body["health"])
        self.assertEqual("not_run", body["acceptance"]["task_live"])
        self.assertIn("待发布", body["hub_status"])

    def test_swarm_route_is_read_only_and_rejects_bodies_and_other_verbs(self) -> None:
        status, _ = self._get("/api/swarm", method="POST", body=b"{}")
        self.assertEqual(405, status)
        status, _ = self._get("/api/swarm", method="PUT", body=b"{}")
        self.assertEqual(405, status)

    def test_swarm_route_ignores_query_parameters(self) -> None:
        status, body = self._get("/api/swarm?secret=do-not-log")
        self.assertEqual(200, status)
        self.assertEqual(SWARM_SCHEMA, body["schema"])


if __name__ == "__main__":
    unittest.main()
