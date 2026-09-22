"""A dependency-free, read-only local server for the T5 dashboard."""

from __future__ import annotations

import argparse
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from viz.adapter import DashboardInputError, empty_dashboard, load_dashboard


class DashboardHandler(SimpleHTTPRequestHandler):
    dashboard: dict[str, object]

    def __init__(self, *args: object, directory: str, dashboard: dict[str, object], **kwargs: object) -> None:
        self.dashboard = dashboard
        super().__init__(*args, directory=directory, **kwargs)

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
        super().do_GET()

    def log_message(self, format: str, *args: object) -> None:
        # Keep demo output concise; request data never enters a shell or HTML.
        print("dashboard:", format % args)


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the Morphogenesis T5 dashboard locally.")
    parser.add_argument("--port", type=int, default=7500)
    parser.add_argument("--input", type=Path, help="Allowlisted local .json or .jsonl export")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")

    root = Path(__file__).resolve().parent.parent
    try:
        data = load_dashboard(args.input, root) if args.input else empty_dashboard()
    except DashboardInputError as error:
        data = empty_dashboard(f"输入未加载：{error}")
    handler = partial(DashboardHandler, directory=str(root / "viz" / "static"), dashboard=data.as_dict())
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"Morphogenesis T5 dashboard: http://127.0.0.1:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
