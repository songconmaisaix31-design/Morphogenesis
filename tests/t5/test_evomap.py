"""E-track EvoMap read-only loop: mock-transport fetch paths, real local SQLite.

Live boundary: no test here contacts the real Hub. The one real live probe is
documented in docs/tracks/frontend-evomap.md. Remote behaviour is exercised
through httpx.MockTransport (mock scope); the local pool is tested against a
real temporary SQLite file (real local read, no network).
"""

import json
import sqlite3
import tempfile
import threading
import unittest
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx

from contracts.resolution import Gene, GeneRef
from http.server import ThreadingHTTPServer
from viz.adapter import DashboardInputError, empty_dashboard
from viz.evomap_models import CATEGORIES_PATH, EVOMAP_SCHEMA, SEARCH_PATH
from viz.evomap_service import EvomapQueryError, EvomapService, read_local_pool
from viz.server import DashboardHandler, degraded_loader


ASSET = {
    "kind": "asset",
    "asset_id": "sha256:24a8523720f948142ebd2808b45b2f606efa9c06a332d6f8b5d0ab2eecf19429",
    "asset_type": "Gene",
    "local_id": "gene_test_nfs-mount-repair_1779701226996",
    "url": "https://evomap.ai/asset/sha256:24a85",
    "status": "promoted",
    "author": "node_113a726159f1555e",
    "model_name": "gemini-2.5-flash",
    "short_title": "Automated NFS Mount Repair Pipeline",
    "nl_summary": "This gene automatically fixes NFS mount errors.",
    "gdi_score": 34.65,
    "view_count": 7,
    "has_strategy": True,
    "validation_status": "noop",
    "validation_credible": False,
    "similarity": 0.9269,
    "payload": {"type": "Gene", "id": "gene_test", "category": "repair"},
    "verification": {"attested": False},
    "some_unobserved_future_field": "dropped",
}


def _hub_payload(assets: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    items = [ASSET] if assets is None else assets
    return {
        "assets": items,
        "count": len(items),
        "search_status": "ok",
        "provider": "hub-test",
        "derived_queries": ["repair"],
    }


def _categories_payload() -> dict[str, Any]:
    return {
        "by_type": [
            {"type": "Gene", "count": 2509437},
            {"type": "Capsule", "count": 2505905},
            {"type": "EvolutionEvent", "count": 2094531, "unobserved": "dropped"},
        ],
        "by_gene_category": [
            {"category": "optimize", "count": 376082},
            {"category": "repair", "count": 342783},
        ],
    }


def _hub_handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == CATEGORIES_PATH:
        return httpx.Response(200, json=_categories_payload())
    return httpx.Response(200, json=_hub_payload())


def _service(handler: Callable[[httpx.Request], httpx.Response], **kwargs: Any) -> EvomapService:
    requests: list[httpx.Request] = []

    def recording(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return handler(request)

    service = EvomapService(transport=httpx.MockTransport(recording), **kwargs)
    service._test_requests = requests  # type: ignore[attr-defined]
    return service


class EvomapServiceTests(unittest.TestCase):
    def test_success_projects_only_observed_fields_and_sends_no_credentials(self) -> None:
        service = _service(
            _hub_handler,
            environ={"MORPH_EVOMAP_API_KEY": "secret-test-key"},
        )
        report = service.report(None, None, None)
        search = report.community_search
        self.assertEqual("live", search.state)
        self.assertEqual(1, search.count)
        asset = search.assets[0]
        self.assertEqual(ASSET["asset_id"], asset["asset_id"])
        self.assertEqual("Automated NFS Mount Repair Pipeline", asset["short_title"])
        self.assertEqual({"type": "Gene", "id": "gene_test", "category": "repair"}, asset["payload"])
        self.assertNotIn("some_unobserved_future_field", asset)
        request = service._test_requests[0]  # type: ignore[attr-defined]
        self.assertNotIn("authorization", request.headers)
        self.assertEqual("https", request.url.scheme)
        self.assertEqual("evomap.ai", request.url.host)
        self.assertEqual("/a2a/assets/semantic-search", request.url.path)
        self.assertEqual("repair", request.url.params["q"])
        # Presence is reported as a boolean; the key value never leaves the env.
        self.assertTrue(report.hub["api_key_configured"])
        self.assertNotIn("secret-test-key", json.dumps(report.as_dict()))

    def test_missing_key_is_reported_as_unconfigured_without_blocking_search(self) -> None:
        service = _service(_hub_handler, environ={})
        report = service.report("timeout", "Gene", "3")
        self.assertFalse(report.hub["api_key_configured"])
        self.assertEqual("live", report.community_search.state)
        params = service._test_requests[0].url.params  # type: ignore[attr-defined]
        self.assertEqual("timeout", params["q"])
        self.assertEqual("Gene", params["type"])
        self.assertEqual("3", params["limit"])

    def test_second_call_within_ttl_serves_cache_without_a_new_request(self) -> None:
        service = _service(_hub_handler)
        first = service.report(None, None, None)
        second = service.report(None, None, None)
        self.assertEqual("live", first.community_search.state)
        self.assertEqual("cache", second.community_search.state)
        self.assertEqual("live", first.community_categories.state)
        self.assertEqual("cache", second.community_categories.state)
        self.assertEqual(2, len(service._test_requests))  # type: ignore[attr-defined]
        self.assertIsNotNone(second.community_search.cache_age_seconds)

    def test_distinct_queries_are_cached_independently(self) -> None:
        service = _service(_hub_handler)
        service.report("alpha", None, None)
        service.report("beta", None, None)
        # Two search fetches plus one shared categories fetch (cached the second time).
        self.assertEqual(3, len(service._test_requests))  # type: ignore[attr-defined]

    def test_timeout_maps_to_fixed_error_code_with_single_attempt(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectTimeout("simulated", request=request)

        service = _service(handler)
        report = service.report(None, None, None)
        search = report.community_search
        self.assertEqual("error", search.state)
        self.assertEqual("timeout", search.error)
        self.assertEqual([], search.assets)
        self.assertEqual("error", report.community_categories.state)
        self.assertEqual("timeout", report.community_categories.error)
        # One attempt per block, never a retry.
        self.assertEqual(2, len(service._test_requests))  # type: ignore[attr-defined]

    def test_http_rejection_is_not_retried_and_status_is_coded(self) -> None:
        service = _service(lambda request: httpx.Response(429, text="slow down"))
        report = service.report(None, None, None)
        self.assertEqual("error", report.community_search.state)
        self.assertEqual("http_429", report.community_search.error)
        self.assertEqual("http_429", report.community_categories.error)
        self.assertEqual(2, len(service._test_requests))  # type: ignore[attr-defined]

    def test_malformed_body_is_rejected(self) -> None:
        service = _service(lambda request: httpx.Response(200, content=b"not json"))
        report = service.report(None, None, None)
        self.assertEqual("malformed_response", report.community_search.error)

    def test_oversized_body_is_rejected(self) -> None:
        service = _service(lambda request: httpx.Response(200, content=b"x" * (1024 * 1024 + 1)))
        report = service.report(None, None, None)
        self.assertEqual("response_too_large", report.community_search.error)

    def test_failure_after_success_serves_stale_cache_with_error(self) -> None:
        responses = [httpx.Response(200, json=_hub_payload()), httpx.Response(503, text="down")]

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == CATEGORIES_PATH:
                return httpx.Response(200, json=_categories_payload())
            return responses.pop(0)

        service = _service(handler, cache_ttl_seconds=0.01)
        import time

        self.assertEqual("live", service.report(None, None, None).community_search.state)
        time.sleep(0.02)
        report = service.report(None, None, None)
        search = report.community_search
        self.assertEqual("stale_cache", search.state)
        self.assertEqual("http_503", search.error)
        self.assertEqual(1, search.count)
        self.assertEqual("live", report.community_categories.state)

    def test_invalid_query_parameters_raise_before_any_request(self) -> None:
        service = _service(_hub_handler)
        for args in [("", None, None), ("x" * 501, None, None), (None, "Mutation", None), (None, None, "0"), (None, None, "51"), (None, None, "abc")]:
            with self.assertRaises(EvomapQueryError):
                service.report(*args)
        self.assertEqual(0, len(service._test_requests))  # type: ignore[attr-defined]

    def test_report_contract_shape(self) -> None:
        service = _service(_hub_handler)
        data = service.report(None, None, None).as_dict()
        self.assertEqual(EVOMAP_SCHEMA, data["schema"])
        self.assertEqual(
            {"base_url", "endpoint", "categories_endpoint", "auth", "api_key_configured"},
            set(data["hub"]),
        )
        self.assertIn("community_search", data)
        self.assertIn("community_categories", data)
        self.assertIn("local_pool", data)
        self.assertTrue(data["boundaries"])
        json.dumps(data)  # The whole contract must stay JSON-serializable.


class CommunityCategoriesTests(unittest.TestCase):
    def test_live_counts_are_projected_with_strict_validation(self) -> None:
        service = _service(_hub_handler)
        report = service.report(None, None, None)
        categories = report.community_categories
        self.assertEqual("live", categories.state)
        self.assertIsNone(categories.error)
        self.assertEqual(
            [
                {"type": "Gene", "count": 2509437},
                {"type": "Capsule", "count": 2505905},
                {"type": "EvolutionEvent", "count": 2094531},
            ],
            categories.by_type,
        )
        self.assertEqual(
            [{"category": "optimize", "count": 376082}, {"category": "repair", "count": 342783}],
            categories.by_gene_category,
        )
        request = [r for r in service._test_requests if r.url.path == CATEGORIES_PATH][0]  # type: ignore[attr-defined]
        self.assertNotIn("authorization", request.headers)
        self.assertEqual("evomap.ai", request.url.host)
        self.assertEqual(b"", request.read())

    def test_malformed_counts_fail_closed_without_touching_search(self) -> None:
        for bad in [
            {},
            {"by_type": [{"type": "Gene", "count": "many"}], "by_gene_category": []},
            {"by_type": [], "by_gene_category": [{"category": "repair", "count": True}]},
            {"by_type": [{"type": "", "count": 1}], "by_gene_category": []},
            {"by_type": [{"type": "Gene", "count": -1}], "by_gene_category": []},
        ]:
            def handler(request: httpx.Request) -> httpx.Response:
                if request.url.path == CATEGORIES_PATH:
                    return httpx.Response(200, json=bad)
                return httpx.Response(200, json=_hub_payload())

            service = _service(handler)
            report = service.report(None, None, None)
            self.assertEqual("error", report.community_categories.state, bad)
            self.assertEqual("malformed_response", report.community_categories.error, bad)
            self.assertEqual([], report.community_categories.by_type)
            self.assertEqual("live", report.community_search.state)

    def test_categories_failure_serves_stale_cache_then_recovers(self) -> None:
        responses = [httpx.Response(200, json=_categories_payload()), httpx.Response(503, text="down")]

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == CATEGORIES_PATH:
                return responses.pop(0)
            return httpx.Response(200, json=_hub_payload())

        service = _service(handler, cache_ttl_seconds=0.01)
        import time

        self.assertEqual("live", service.report(None, None, None).community_categories.state)
        time.sleep(0.02)
        stale = service.report(None, None, None).community_categories
        self.assertEqual("stale_cache", stale.state)
        self.assertEqual("http_503", stale.error)
        self.assertEqual(3, len(stale.by_type))


class CacheAgeClockTests(unittest.TestCase):
    """Controlled-clock regression for cache_age_seconds metadata.

    report() reads the clock before the GET while _fetch() stamps fetched_at
    after it, so a slow Hub used to produce a negative live age. The contract
    (docs/tracks/frontend-evomap.md) is: live => cache_age_seconds is null;
    cache/stale_cache => a nonnegative, accurate age.
    """

    @staticmethod
    def _clock(start: float = 1000.0) -> tuple[list[float], Callable[[], float]]:
        state = [start]
        return state, lambda: state[0]

    def test_live_age_is_null_even_when_the_clock_advances_during_fetch(self) -> None:
        state, clock = self._clock()

        def handler(request: httpx.Request) -> httpx.Response:
            state[0] += 30.0  # slow Hub: fetched_at lands after report()'s now
            return _hub_handler(request)

        service = _service(handler, clock=clock)
        report = service.report(None, None, None)
        self.assertEqual("live", report.community_search.state)
        self.assertIsNone(report.community_search.cache_age_seconds)
        self.assertEqual("live", report.community_categories.state)
        self.assertIsNone(report.community_categories.cache_age_seconds)

    def test_cache_age_is_nonnegative_and_accurate_for_both_blocks(self) -> None:
        state, clock = self._clock()

        def handler(request: httpx.Request) -> httpx.Response:
            state[0] += 5.0  # fetched_at lands a little after report()'s now
            return _hub_handler(request)

        service = _service(handler, clock=clock)
        service.report(None, None, None)
        state[0] += 40.0  # still within the default TTL
        report = service.report(None, None, None)
        for block in (report.community_search, report.community_categories):
            self.assertEqual("cache", block.state)
            fetched_at = block.fetched_at
            age = block.cache_age_seconds
            if fetched_at is None or age is None:
                self.fail("cache block must carry fetched_at and cache_age_seconds")
            self.assertGreaterEqual(age, 0.0)
            self.assertAlmostEqual(state[0] - fetched_at, age)

    def test_stale_cache_age_is_nonnegative_and_accurate_for_both_blocks(self) -> None:
        state, clock = self._clock()
        first_call = {SEARCH_PATH: True, CATEGORIES_PATH: True}

        def handler(request: httpx.Request) -> httpx.Response:
            path = request.url.path
            if first_call.get(path, False):
                first_call[path] = False
                return _hub_handler(request)
            return httpx.Response(503, text="down")

        service = _service(handler, clock=clock, cache_ttl_seconds=10.0)
        service.report(None, None, None)
        state[0] += 40.0  # past the TTL; the refetch fails and serves stale
        report = service.report(None, None, None)
        for block in (report.community_search, report.community_categories):
            self.assertEqual("stale_cache", block.state)
            self.assertEqual("http_503", block.error)
            fetched_at = block.fetched_at
            age = block.cache_age_seconds
            if fetched_at is None or age is None:
                self.fail("stale block must carry fetched_at and cache_age_seconds")
            self.assertGreaterEqual(age, 0.0)
            self.assertAlmostEqual(state[0] - fetched_at, age)


class DegradedLoaderTests(unittest.TestCase):
    """Regression: the degraded dashboard loader must outlive its except block.

    Python clears the exception variable when an except block exits, so a
    lambda closing over it raised NameError and /api/dashboard answered 500
    instead of the documented degraded empty dashboard.
    """

    def test_loader_survives_the_except_block(self) -> None:
        try:
            raise DashboardInputError("未找到锁定的本地 ECharts；先运行 npm ci")
        except DashboardInputError as error:
            load_data = degraded_loader(error)
        data = load_data()
        self.assertEqual(["输入未加载：未找到锁定的本地 ECharts；先运行 npm ci"], data.notes)
        self.assertEqual("live", data.provenance)
        self.assertEqual(
            {"contract_local": "not_run", "interface_live": "not_run", "task_live": "not_run"},
            data.acceptance,
        )
        self.assertEqual([], data.events)

    def test_dashboard_route_returns_degraded_payload_not_500(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        try:
            raise DashboardInputError("输入文件不存在")
        except DashboardInputError as error:
            load_data = degraded_loader(error)

        def handler(*args: Any, **kwargs: Any) -> DashboardHandler:
            return DashboardHandler(
                *args, directory=str(root), dashboard_loader=load_data,
                echarts_asset=root / "missing-echarts.js",
                evomap_service=EvomapService(store_path=None), **kwargs,
            )

        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)

        base = f"http://127.0.0.1:{server.server_address[1]}"
        try:
            with urllib.request.urlopen(base + "/api/dashboard", timeout=10) as response:
                status, body = response.status, json.loads(response.read())
        except urllib.error.HTTPError as error:
            self.fail(f"expected degraded 200, got {error.code}: {error.read()!r}")
        self.assertEqual(200, status)
        self.assertEqual(["输入未加载：输入文件不存在"], body["notes"])
        self.assertEqual("live", body["provenance"])
        self.assertEqual("not_run", body["acceptance"]["contract_local"])


class LocalPoolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _gene(self, gene_id: str, version: int = 1) -> str:
        return Gene(
            ref=GeneRef(gene_id=gene_id, version=version, asset_id=f"sha256:{gene_id}"),
            signals_match=["repair"], strategy=["inspect", "fix"],
            avoid=["guess"], verification=["run tests"], provenance="live",
        ).model_dump_json()

    def _make_store(self) -> Path:
        db = self.root / "metadata.db"
        connection = sqlite3.connect(db)
        connection.execute("CREATE TABLE genes (gene_id TEXT, version INTEGER, body TEXT, PRIMARY KEY (gene_id, version))")
        connection.execute(
            "CREATE TABLE metabolism_gene_state (gene_id TEXT, version INTEGER, ref_json TEXT,"
            " provenance TEXT, original_run_uri TEXT, source_attempt_json TEXT, created_at REAL,"
            " anchor_at REAL, evaluated_at REAL, tau_seconds REAL, weight REAL, use_count INTEGER,"
            " archived_at REAL, PRIMARY KEY (gene_id, version))"
        )
        connection.execute("INSERT INTO genes VALUES (?, ?, ?)", ("g-active", 1, self._gene("g-active")))
        connection.execute("INSERT INTO genes VALUES (?, ?, ?)", ("g-broken", 1, "{not a gene"))
        connection.execute(
            "INSERT INTO metabolism_gene_state (gene_id, version, ref_json, provenance,"
            " original_run_uri, source_attempt_json, created_at, anchor_at, evaluated_at,"
            " tau_seconds, weight, use_count, archived_at) VALUES (?, ?, '{}', 'live', NULL, NULL,"
            " 1, 1, 1, 10, 0.5, 3, NULL)",
            ("g-active", 1),
        )
        connection.execute(
            "INSERT INTO metabolism_gene_state (gene_id, version, ref_json, provenance,"
            " original_run_uri, source_attempt_json, created_at, anchor_at, evaluated_at,"
            " tau_seconds, weight, use_count, archived_at) VALUES (?, ?, '{}', 'live', NULL, NULL,"
            " 1, 1, 1, 10, 0.01, 0, 2)",
            ("g-archived", 1),
        )
        connection.commit()
        connection.close()
        return db

    def test_real_sqlite_store_projects_valid_genes_and_notes_exclusions(self) -> None:
        pool = read_local_pool(self._make_store())
        self.assertEqual("ok", pool.state)
        self.assertEqual("sqlite:metadata.db", pool.source)
        self.assertEqual(1, len(pool.genes))
        gene = pool.genes[0]
        self.assertEqual("g-active", gene["gene_id"])
        self.assertEqual(["inspect", "fix"], gene["strategy"])
        self.assertEqual(0.5, gene["weight"])
        self.assertEqual(3, gene["use_count"])
        self.assertTrue(any("未通过共享契约" in note for note in pool.notes))
        self.assertTrue(any("已归档" in note for note in pool.notes))
        self.assertNotIn("g-archived", {g["gene_id"] for g in pool.genes})

    def test_missing_store_is_an_explicit_error_not_an_empty_pool(self) -> None:
        pool = read_local_pool(self.root / "absent.db")
        self.assertEqual("error", pool.state)
        self.assertEqual("store_missing", pool.error)

    def test_unreadable_store_is_an_explicit_error(self) -> None:
        garbage = self.root / "garbage.db"
        garbage.write_bytes(b"this is not sqlite at all")
        pool = read_local_pool(garbage)
        self.assertEqual("error", pool.state)
        self.assertEqual("store_unreadable", pool.error)

    def test_unconfigured_pool_is_closed_not_empty(self) -> None:
        service = EvomapService(transport=httpx.MockTransport(_hub_handler))
        pool = service.report(None, None, None).local_pool
        self.assertEqual("unconfigured", pool.state)


class EvomapRouteTests(unittest.TestCase):
    """Real local HTTP against the real handler; the Hub stays a mock transport."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.service = _service(_hub_handler)

        def handler(*args: Any, **kwargs: Any) -> DashboardHandler:
            return DashboardHandler(
                *args, directory=str(root), dashboard_loader=empty_dashboard,
                echarts_asset=root / "missing.js", evomap_service=self.service, **kwargs,
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

    def _get(self, path: str) -> tuple[int, dict[str, Any]]:
        try:
            with urllib.request.urlopen(self.base + path, timeout=10) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read())

    def test_evomap_route_returns_the_documented_contract(self) -> None:
        status, body = self._get("/api/evomap")
        self.assertEqual(200, status)
        self.assertEqual(EVOMAP_SCHEMA, body["schema"])
        self.assertEqual("live", body["community_search"]["state"])
        self.assertEqual("live", body["community_categories"]["state"])
        self.assertEqual("unconfigured", body["local_pool"]["state"])

    def test_query_parameters_are_forwarded_and_validated(self) -> None:
        status, body = self._get("/api/evomap?q=nfs&type=Gene&limit=5")
        self.assertEqual(200, status)
        self.assertEqual({"q": "nfs", "limit": 5, "type": "Gene"}, body["community_search"]["query"])
        status, body = self._get("/api/evomap?type=Mutation")
        self.assertEqual(400, status)
        self.assertEqual("invalid_query", body["error"])

    def test_dashboard_route_still_serves(self) -> None:
        status, body = self._get("/api/dashboard")
        self.assertEqual(200, status)
        self.assertIn("provenance", body)


if __name__ == "__main__":
    unittest.main()
