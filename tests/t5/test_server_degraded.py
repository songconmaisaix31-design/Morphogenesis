"""Regression: the degraded dashboard loader must outlive its except block.

Python clears the exception variable when an except block exits, so a lambda
closing over it raised NameError and /api/dashboard answered 500 instead of
the documented degraded empty dashboard. These tests pin the degraded
response for the two entry failures (missing locked ECharts, invalid input).
"""

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

from viz.adapter import DashboardInputError
from viz.evomap_service import EvomapService
from viz.server import DashboardHandler, degraded_loader


class DegradedLoaderTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
