"""The read-only panel serves readiness, and an unwired panel reports not_run."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from functools import partial
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from typing import Any

import pytest

from contracts.readiness import ProbeResult, ProbeSubject
from readiness.service import ReadinessService
from viz import server
from viz.adapter import empty_dashboard
from viz.evomap_service import EvomapService

Request = Callable[..., tuple[int, dict[str, str], bytes]]
Starter = Callable[[ReadinessService | None], Request]


class StubProbe:
    probe_id = "interface:stub"
    subject: ProbeSubject = "interface"

    def probe(self) -> ProbeResult:
        return ProbeResult(
            probe_id=self.probe_id, subject=self.subject, state="ok", observed=True,
            detail="stub", evidence={"code": "ok"},
        )


@pytest.fixture
def panel(tmp_path: Path) -> Iterator[Starter]:
    (tmp_path / "index.html").write_text("<html>read only</html>", encoding="utf-8")
    chart = tmp_path / "echarts.min.js"
    chart.write_text("/* isolated test asset */", encoding="utf-8")
    listeners: list[ThreadingHTTPServer] = []

    def start(service: ReadinessService | None = None) -> Request:
        extra: dict[str, Any] = {} if service is None else {"readiness_service": service}
        handler = partial(
            server.DashboardHandler,
            directory=str(tmp_path),
            dashboard_loader=empty_dashboard,
            echarts_asset=chart,
            evomap_service=EvomapService(store_path=None),
            **extra,
        )
        listener = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        listeners.append(listener)
        Thread(target=listener.serve_forever, daemon=True).start()

        def request(method: str, path: str, body: bytes | None = None) -> tuple[int, dict[str, str], bytes]:
            client = HTTPConnection("127.0.0.1", listener.server_port, timeout=10)
            try:
                client.request(method, path, body=body)
                response = client.getresponse()
                return response.status, dict(response.getheaders()), response.read()
            finally:
                client.close()

        return request

    try:
        yield start
    finally:
        for listener in listeners:
            listener.shutdown()


def test_a_wired_probe_is_served_and_partial_coverage_stays_degraded(panel: Starter) -> None:
    request = panel(ReadinessService((StubProbe(),)))
    status, headers, body = request("GET", "/api/readiness")
    assert status == 200
    assert headers["Content-Type"].startswith("application/json")
    payload = json.loads(body)
    assert payload["schema_version"] == "morph.readiness/1"
    assert set(payload["dimensions"]) == {"machine", "interface", "account"}
    assert payload["dimensions"]["interface"] == "ok"
    assert payload["dimensions"]["machine"] == "not_run"
    assert payload["overall"] == "degraded"
    assert [result["probe_id"] for result in payload["results"]] == ["interface:stub"]


def test_an_unconfigured_panel_reports_not_run_rather_than_a_verdict(panel: Starter) -> None:
    request = panel(None)
    status, _, body = request("GET", "/api/readiness")
    assert status == 200
    payload = json.loads(body)
    assert payload["overall"] == "not_run"
    assert payload["results"] == []
    assert set(payload["dimensions"].values()) == {"not_run"}


def test_readiness_is_read_only_and_bodyless(panel: Starter) -> None:
    request = panel(ReadinessService((StubProbe(),)))
    status, _, body = request("HEAD", "/api/readiness")
    assert (status, body) == (200, b"")
    assert request("POST", "/api/readiness")[0] == 405
    assert request("GET", "/api/readiness", b"body")[0] == 413
