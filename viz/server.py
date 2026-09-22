"""A dependency-free, read-only local server for the T5 dashboard."""

from __future__ import annotations

import argparse
import json
import socket
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from socketserver import BaseServer
from typing import Any, Callable
from urllib.parse import parse_qs, urlsplit

from viz.adapter import DashboardData, DashboardInputError, empty_dashboard, load_dashboard, load_rehearsal, load_runtime_export
from viz.evomap_service import EvomapQueryError, EvomapService, dumps_report


def echarts_asset_path(project_root: Path) -> Path:
    """Return the one lockfile-installed local ECharts asset T5 may serve."""
    asset = project_root / "node_modules" / "echarts" / "dist" / "echarts.min.js"
    if not asset.is_file() or asset.is_symlink():
        raise DashboardInputError("未找到锁定的本地 ECharts；先运行 npm ci")
    return asset


def rehearsal_loader(path: Path, *, replay: bool = False) -> DashboardData:
    """Keep the page available before R writes its first atomic stage snapshot."""
    try:
        return load_rehearsal(path, replay=replay)
    except DashboardInputError as error:
        return empty_dashboard(f"彩排快照尚未可读：{error}")


def degraded_loader(error: DashboardInputError) -> Callable[[], DashboardData]:
    """Bind the reason now: Python clears the except-block variable afterwards."""
    reason = f"输入未加载：{error}"
    return lambda: empty_dashboard(reason)


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(
        self,
        request: socket.socket | tuple[bytes, socket.socket],
        client_address: tuple[str, int],
        server: BaseServer,
        *,
        directory: str,
        dashboard_loader: Callable[[], DashboardData],
        echarts_asset: Path,
        evomap_service: EvomapService,
        **kwargs: Any,
    ) -> None:
        self.dashboard_loader = dashboard_loader
        self.echarts_asset = echarts_asset
        self.evomap_service = evomap_service
        super().__init__(request, client_address, server, directory=directory, **kwargs)

    def _json_response(self, status: int, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        route = urlsplit(self.path)
        if route.path == "/api/evomap":
            params = parse_qs(route.query, keep_blank_values=False, max_num_fields=8)
            self._serve_evomap(params)
            return
        if self.path == "/api/dashboard":
            # Re-read the one named rehearsal.json on each request so the local
            # page follows R's real stage snapshots. Browser input never reaches
            # this loader and no request path is interpreted as a filesystem path.
            body = json.dumps(self.dashboard_loader().as_dict(), ensure_ascii=False).encode("utf-8")
            self._json_response(200, body)
            return
        if self.path == "/vendor/echarts.min.js":
            body = self.echarts_asset.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/javascript; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "public, max-age=3600")
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def _serve_evomap(self, params: dict[str, list[str]]) -> None:
        def first(name: str) -> str | None:
            values = params.get(name)
            return values[0] if values else None

        try:
            report = self.evomap_service.report(first("q"), first("type"), first("limit"))
        except EvomapQueryError as error:
            body = json.dumps(
                {"schema": "morph.evomap.readonly/1", "error": "invalid_query", "detail": str(error)},
                ensure_ascii=False,
            ).encode("utf-8")
            self._json_response(400, body)
            return
        self._json_response(200, dumps_report(report))

    def log_message(self, format: str, *args: object) -> None:
        # Keep demo output concise; request data never enters a shell or HTML.
        print("dashboard:", format % args)


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the Morphogenesis T5 dashboard locally.")
    parser.add_argument("--port", type=int, default=7500)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--input", type=Path, help="Allowlisted mock document or Envelope JSONL")
    source.add_argument("--t2-root", type=Path, help="T2 named evidence root with fixed sidecars")
    source.add_argument("--rehearsal", type=Path, help="R's explicit fixed-rehearsal rehearsal.json")
    parser.add_argument("--replay", action="store_true", help="Read the named rehearsal evidence as a downgraded replay")
    parser.add_argument("--evomap-store", type=Path, help="Read-only local Gene pool from the runtime SQLite store (e.g. metadata.db)")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    if args.replay and not args.rehearsal:
        parser.error("--replay requires --rehearsal")

    root = Path(__file__).resolve().parent.parent
    load_data: Callable[[], DashboardData]
    try:
        if args.rehearsal:
            load_data = lambda: rehearsal_loader(args.rehearsal, replay=args.replay)
        elif args.t2_root:
            load_data = lambda: load_runtime_export(args.t2_root, root)
        elif args.input:
            load_data = lambda: load_dashboard(args.input, root)
        else:
            load_data = empty_dashboard
        if not args.rehearsal:
            load_data()
        asset = echarts_asset_path(root)
    except DashboardInputError as error:
        load_data = degraded_loader(error)
        asset = root / "viz" / "static" / "missing-echarts.js"
    handler = partial(
        DashboardHandler, directory=str(root / "viz" / "static"),
        dashboard_loader=load_data, echarts_asset=asset,
        evomap_service=EvomapService(store_path=args.evomap_store),
    )
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"Morphogenesis T5 dashboard: http://127.0.0.1:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
