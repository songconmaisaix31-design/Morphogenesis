"""Availability tests for the env-observatory FastAPI service.

These lock in the read-only contract and the live wiring between the 255KB
single-file frontend and ``swarm/research/service.py``:

- package / snapshot / advisory / context return the contract shape (§2/§6/§7/§9)
- replay slices the package by task_id with the frontend's §10 semantics
- activity returns a task_audit increment that ``subscribeActivity`` can poll
- non GET/HEAD (except the Wayfinder POST) → 405, GET/HEAD with body → 413
- every response carries nosniff / DENY / no-referrer
- without a bound service (no HostConfig) the API degrades to 503 while static
  files keep serving, so the frontend falls back to its inline mock
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any, Iterator

import pytest

from contracts.identity import AgentId
from swarm.research.models import HostConfig
from swarm.research.service import ResearchService

PROJECT = "p1"
SERVER_PATH = Path(__file__).resolve().parents[2] / "src" / "env-observatory" / "server.py"


def _load_server_module() -> Any:
    """Load server.py by path (its directory name is not importable as a package)."""
    spec = importlib.util.spec_from_file_location("env_observatory_server", SERVER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module", name="server")
def server_module() -> Any:
    return _load_server_module()


@pytest.fixture(name="service")
def service_fixture(tmp_path: Path) -> ResearchService:
    config = HostConfig(ledger_path=str(tmp_path / "ledger.sqlite3"), swarm_id="swarm-obs",
                        workspace=str(tmp_path / "project"), worker_id="w-01",
                        agent=AgentId(role="builder", instance=0), authorized_scopes=("science",),
                        capabilities=("research", "review"), assets_root=str(tmp_path / "assets"),
                        evidence_root=str(tmp_path / "evidence"), project_id=PROJECT)
    service = ResearchService(config)
    service.create_project(PROJECT, "边界处理与采样策略的可验证数值方法", allowed_domains=("numerical_pde",))
    service.create_branch(PROJECT, "b-soft", "软边界方法", "探索软边界的数值处理")
    service.create_branch(PROJECT, "b-hard", "硬边界方法", "探索硬边界的数值验证")
    service.propose_work(PROJECT, "question", "文献调研：边界处理方法", "缺少既有处理方式",
                         "调研结论", branch_id="b-soft", required_capability="research")
    service.submit_note(PROJECT, "expert_opinion", "倾向软边界方法 A", branch_id="b-soft", signer="Dr. Y")
    return service


@pytest.fixture(name="client")
def client_fixture(server: Any, service: ResearchService) -> Iterator[Any]:
    from starlette.testclient import TestClient

    with TestClient(server.create_app(service)) as client:
        yield client


def test_package_returns_contract_shape(client: Any) -> None:
    body = client.get("/api/research/package").json()
    assert body["schema_version"] == "research-package/v1"
    assert body["project_id"] == PROJECT
    assert body["tasks"] and body["task_audit"]
    assert "research_v1" in body["context"]
    assert body["evidence_boundary"] == "per_record_provenance"
    assert body["completion_claim"] is False
    task = body["tasks"][0]
    assert "task_id" in task["signal"] and "goal" in task["signal"]["payload"]


def test_snapshot_returns_opportunities_and_branches(client: Any) -> None:
    body = client.get("/api/research/snapshot").json()
    assert body["policy_version"] == "research-v1"
    assert body["advisory_only"] is True
    assert [b["branch_id"] for b in body["branches"]] == ["b-soft", "b-hard"]
    assert body["opportunities"]["opportunities"]


def test_advisory_and_context_endpoints(client: Any) -> None:
    assert client.get("/api/research/advisory").json()["project_id"] == PROJECT
    context = client.get("/api/research/context").json()
    assert context["selection"]["mode"] == "overview"
    assert any(n["kind"] == "expert_opinion" for n in context["notes"])


def test_replay_slices_package_by_task(client: Any) -> None:
    task_id = client.get("/api/research/package").json()["tasks"][0]["signal"]["task_id"]
    replay = client.get(f"/api/research/replay/{task_id}").json()
    assert replay["task_id"] == task_id
    assert replay["task"]["signal"]["task_id"] == task_id
    assert all(e["task_id"] == task_id for e in replay["audit"])
    assert replay["audit"] == sorted(replay["audit"], key=lambda e: e["sequence"])
    for key in ("executions", "observations", "adoption_receipts"):
        assert isinstance(replay[key], list)
    assert client.get("/api/research/replay/").status_code == 404  # empty id is not a route


def test_activity_returns_increment_only(client: Any) -> None:
    latest = client.get("/api/research/activity").json()
    assert latest["events"]
    after = client.get(f"/api/research/activity?since_seq={latest['latest_seq']}").json()
    assert after["events"] == []
    assert client.get("/api/research/activity?since_seq=-1").status_code == 400


def test_read_only_method_policy(client: Any) -> None:
    assert client.post("/api/research/package").status_code == 405
    assert client.delete("/api/research/snapshot").status_code == 405
    assert client.patch("/api/research/package").status_code == 405
    assert client.put("/").status_code == 405
    assert client.request("GET", "/api/research/package", content=b"hello").status_code == 413


def test_security_headers_on_every_response(client: Any) -> None:
    headers = client.get("/api/research/package").headers
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert headers["referrer-policy"] == "no-referrer"
    assert headers["cache-control"] == "no-store"


def test_static_serving_and_allowlist(client: Any) -> None:
    root = client.get("/")
    assert root.status_code == 200
    assert "text/html" in root.headers["content-type"]
    assert "/api/research/" in root.text  # live data-layer wiring is present
    assert client.get("/seed.py").status_code == 404
    assert client.get("/../pyproject.toml").status_code == 404


def test_wayfinder_validates_without_invoking_pi(client: Any) -> None:
    assert client.post("/api/wayfinder/ask", json={}).json()["error"] == "missing_question"
    assert client.post("/api/wayfinder/ask", json={"question": "x" * 2500}).json()["error"] == "question_too_long"


def test_service_unavailable_degrades_to_503(server: Any) -> None:
    from starlette.testclient import TestClient

    with TestClient(server.create_app(None, service_error="OBSERVATORY_HOST_CONFIG 未设置")) as client:
        for path in ("/api/research/package", "/api/research/snapshot", "/api/research/activity",
                     "/api/research/context", "/api/research/advisory", "/api/research/replay/T-1"):
            response = client.get(path)
            assert response.status_code == 503, path
            assert response.json()["error"] == "observatory_service_unavailable"
        assert client.get("/").status_code == 200  # static still served → frontend falls back to mock
