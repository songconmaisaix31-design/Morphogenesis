"""A dependency-free, read-only local server for the T5 dashboard."""

from __future__ import annotations

import argparse
import json
import socket
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from socketserver import BaseServer
from typing import Any

from viz.adapter import DashboardInputError, empty_dashboard, load_dashboard, load_runtime_export


def echarts_asset_path(project_root: Path) -> Path:
    """Return the one lockfile-installed local ECharts asset T5 may serve."""
    asset = project_root / "node_modules" / "echarts" / "dist" / "echarts.min.js"
    if not asset.is_file() or asset.is_symlink():
        raise DashboardInputError("未找到锁定的本地 ECharts；先运行 npm ci")
    return asset


class DashboardHandler(SimpleHTTPRequestHandler):
    dashboard: dict[str, object]

    def __init__(
        self,
        request: socket.socket | tuple[bytes, socket.socket],
        client_address: tuple[str, int],
        server: BaseServer,
        *,
        directory: str,
        dashboard: dict[str, object],
        echarts_asset: Path,
        **kwargs: Any,
    ) -> None:
        self.dashboard = dashboard
        self.echarts_asset = echarts_asset
        super().__init__(request, client_address, server, directory=directory, **kwargs)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/api/dashboard":
            body = json.dumps(self.dashboard, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
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

    def log_message(self, format: str, *args: object) -> None:
        # Keep demo output concise; request data never enters a shell or HTML.
        print("dashboard:", format % args)


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the Morphogenesis T5 dashboard locally.")
    parser.add_argument("--port", type=int, default=7500)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--input", type=Path, help="Allowlisted mock document or Envelope JSONL")
    source.add_argument("--t2-root", type=Path, help="T2 named evidence root with fixed sidecars")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")

    root = Path(__file__).resolve().parent.parent
    try:
        data = load_runtime_export(args.t2_root, root) if args.t2_root else load_dashboard(args.input, root) if args.input else empty_dashboard()
        asset = echarts_asset_path(root)
    except DashboardInputError as error:
        data = empty_dashboard(f"输入未加载：{error}")
        asset = root / "viz" / "static" / "missing-echarts.js"
    handler = partial(DashboardHandler, directory=str(root / "viz" / "static"), dashboard=data.as_dict(), echarts_asset=asset)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"Morphogenesis T5 dashboard: http://127.0.0.1:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
