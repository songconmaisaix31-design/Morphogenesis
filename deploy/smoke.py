"""Bounded HTTP acceptance for a running proxy; no model or task calls."""

import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
from urllib.error import HTTPError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from viz.adapter import validate_dashboard_snapshot


class Assets(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.paths: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        value = values.get("src") if tag == "script" else values.get("href") if tag == "link" else None
        if value:
            if tag == "link" and values.get("rel") == "icon" and value == "data:,":
                return  # The reviewed UI intentionally has an empty inline favicon.
            assert not urlsplit(value).netloc and not urlsplit(value).scheme, value
            self.paths.append(value)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url")
    parser.add_argument("--with-fonts", action="store_true", help="Require merged F font assets")
    parser.add_argument("--evomap-live", action="store_true", help="One public read-only search; no retries")
    parser.add_argument("--direct", action="store_true", help="Python viewer without nginx rate limits")
    args = parser.parse_args()
    base = args.base_url.rstrip("/") + "/"
    assert urlsplit(base).scheme in {"http", "https"}
    checks: list[dict[str, object]] = []

    def request(path: str, status: int | set[int] = 200, method: str = "GET", data: bytes | None = None) -> bytes:
        try:
            response = urlopen(Request(urljoin(base, path), method=method, data=data), timeout=65)
        except HTTPError as error:
            response = error
        with response:
            body = response.read()
            expected = status if isinstance(status, set) else {status}
            assert response.status in expected, (path, method, response.status, status)
            assert response.headers.get("X-Content-Type-Options") == "nosniff"
            if method == "HEAD":
                assert not body
            checks.append({"method": method, "path": path, "status": response.status})
            return body

    assets = Assets()
    assets.feed(request("/").decode())
    for path in assets.paths:
        assert request(path), path
        request(path, method="HEAD")
    if args.with_fonts:
        for path in ("/fonts/Jost-latin.woff2", "/fonts/InterVariable.woff2"):
            assert request(path).startswith(b"wOF2")
    dashboard = json.loads(request("/api/dashboard"))
    validate_dashboard_snapshot(dashboard)
    request("/api/dashboard", method="HEAD")
    # These prove both API routes reach Python validation without upstream calls.
    assert json.loads(request("/api/evomap?limit=invalid", 400))["error"] == "invalid_query"
    assert json.loads(request("/api/evomap/asset?id=invalid", 400))["error"] == "invalid_asset_id"
    for path in ("/.env", "/.git/config", "/assets/", "/fonts/", "/licenses/", "/api/tasks", "/api/evomap/asset/extra", "/server.py", "/vendor/"):
        request(path, 404)
    for method in ("POST", "PUT", "DELETE", "OPTIONS", "TRACE"):
        request("/api/dashboard", 405, method)
    request("/api/dashboard", 413, data=b"body")
    if args.evomap_live:
        report = json.loads(request("/api/evomap?q=repair&limit=1"))
        # HTTP 200 alone is not upstream success; preserve the full report.
        print(json.dumps({"evomap_report": report}, ensure_ascii=True))
    # Exercise the shared EvoMap rate limit without ever querying the Hub.
    if not args.direct:
        for _ in range(6):
            request("/api/evomap/asset?id=invalid", {400, 429})
        assert any(check["status"] == 429 for check in checks)
    print(json.dumps({"checks": checks, "provenance": dashboard["provenance"], "acceptance": dashboard["acceptance"]}, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
