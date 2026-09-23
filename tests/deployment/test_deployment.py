from functools import partial
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
from threading import Thread
from unittest.mock import Mock

import httpx
import pytest

from deploy.package import FILES, allowed, package
from viz import server
from viz.adapter import load_dashboard
from viz.evomap_service import EvomapService

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("host", [None, "0.0.0.0"])
def test_cli_bind_default_and_explicit_host(monkeypatch, host):
    listener = Mock()
    factory = Mock(return_value=listener)
    monkeypatch.setattr(server, "ThreadingHTTPServer", factory)
    monkeypatch.setattr(server, "echarts_asset_path", lambda _: Path("unused"))
    monkeypatch.setattr(sys, "argv", ["viz.server", "--port", "7501"] + (["--host", host] if host else []))
    server.main()
    assert factory.call_args.args[0] == (host or "127.0.0.1", 7501)
    listener.serve_forever.assert_called_once()


@pytest.fixture
def backend(tmp_path):
    chart = tmp_path / "echarts.min.js"
    chart.write_text("/* isolated test asset */")
    upstream = []

    def hub(request):
        upstream.append(request)
        return httpx.Response(404, json={"error": "not_found"})

    service = EvomapService(transport=httpx.MockTransport(hub))
    handler = partial(
        server.DashboardHandler, directory=str(tmp_path),
        dashboard_loader=lambda: load_dashboard(ROOT / "demo/data/mock-run.json", ROOT),
        echarts_asset=chart, evomap_service=service,
    )
    listener = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=listener.serve_forever, daemon=True)
    thread.start()

    def request(method, path):
        client = HTTPConnection("127.0.0.1", listener.server_port, timeout=5)
        try:
            client.request(method, path)
            response = client.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            client.close()

    yield request, upstream
    listener.shutdown()
    listener.server_close()
    thread.join(timeout=5)


def test_real_http_mock_dashboard_and_head_have_same_headers(backend):
    request, upstream = backend
    status, headers, body = request("GET", "/api/dashboard?cache=1")
    assert status == 200
    data = json.loads(body)
    assert data["provenance"] == "mock"
    assert data["acceptance"]["task_live"] == "not_run"
    head_status, head_headers, head_body = request("HEAD", "/api/dashboard")
    assert head_status == 200 and head_body == b""
    assert head_headers["Content-Length"] == headers["Content-Length"]
    assert upstream == []


@pytest.mark.parametrize("path,error", [
    ("/api/evomap?limit=invalid", "invalid_query"),
    ("/api/evomap/asset?id=invalid", "invalid_asset_id"),
    ("/api/evomap?" + "&".join(f"x{i}=1" for i in range(9)), "too_many_query_fields"),
    ("/api/evomap/asset?" + "&".join(f"x{i}=1" for i in range(5)), "too_many_query_fields"),
])
def test_bad_public_api_queries_return_json_without_upstream(backend, path, error):
    request, upstream = backend
    status, _, body = request("GET", path)
    assert status == 400 and json.loads(body)["error"] == error
    head_status, _, head_body = request("HEAD", path)
    assert head_status == 400 and head_body == b""
    assert upstream == []


def test_echarts_head_matches_get(backend):
    request, _ = backend
    status, headers, body = request("GET", "/vendor/echarts.min.js?v=1")
    assert status == 200 and body
    status, head_headers, body = request("HEAD", "/vendor/echarts.min.js?v=1")
    assert status == 200 and body == b""
    assert head_headers["Content-Length"] == headers["Content-Length"]


def test_compose_renders_isolated_readonly_services(tmp_path):
    if not shutil.which("docker"):
        pytest.skip("Docker Compose CLI unavailable")
    env = dict(os.environ, MORPH_RELEASE="a" * 40, MORPH_REPLAY_FILE=str(tmp_path / "rehearsal.json"))
    base = ["docker", "compose", "-f", str(ROOT / "deploy/compose.yaml")]
    config = json.loads(subprocess.check_output(base + ["config", "--format", "json"], env=env))
    assert config["name"] == "morphogenesis"
    api, web = config["services"]["api"], config["services"]["web"]
    assert not api.get("ports") and not api.get("volumes")
    assert web["ports"] == [{"mode": "ingress", "host_ip": "127.0.0.1", "target": 8080, "published": "7799", "protocol": "tcp"}]
    for service in (api, web):
        assert service["read_only"] and service["restart"] == "unless-stopped"
        assert service["cap_drop"] == ["ALL"]
        assert "healthcheck" in service
        assert not service.get("environment")
    replay = json.loads(subprocess.check_output(base + ["-f", str(ROOT / "deploy/compose.replay.yaml"), "config", "--format", "json"], env=env))
    api = replay["services"]["api"]
    assert api["command"] == ["--rehearsal", "/data/rehearsal.json", "--replay"]
    mount = api["volumes"][0]
    assert mount["read_only"] and not mount["bind"]["create_host_path"]


def test_release_archive_contains_committed_allowlist_only(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    safe = FILES | {"viz/server.py", "viz/static/index.html", "viz/static/assets/finals-shell.js", "viz/static/assets/finals-shell.css", "viz/static/fonts/Jost-latin.woff2"}
    unsafe = {".env", ".env.production", "id_rsa", "viz/static/private.key", "viz/static/.env", "runtime_exports/events.jsonl", "deploy/workstation.json", "node_modules/private.txt"}
    for name in safe | unsafe:
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("committed")
    def git(*args):
        return subprocess.check_output(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", *args], cwd=repo)
    git("init", "-q")
    git("add", ".")
    git("commit", "-qm", "fixture")
    sha = git("rev-parse", "HEAD").decode().strip()
    (repo / "viz/server.py").write_text("dirty workstation content")
    output = tmp_path / "release.tar.gz"
    names = package(sha, output, root=repo)
    assert set(names) == safe
    with tarfile.open(output) as archive:
        assert archive.extractfile(f"{sha}/viz/server.py").read() == b"committed"
        assert not any(archive.getnames().count(f"{sha}/{name}") for name in unsafe)
    with pytest.raises(ValueError, match="Output exists"):
        package(sha, output, root=repo)
    with pytest.raises(ValueError, match="exact"):
        package("HEAD", tmp_path / "other.tar.gz", root=repo)


@pytest.mark.parametrize("name", [".git/config", ".env", "viz/static/.env", "viz/static/test.js.map", "deploy/id_rsa", "orchestration/__pycache__/module.py"])
def test_release_rejects_workstation_artifacts(name):
    assert not allowed(name)
