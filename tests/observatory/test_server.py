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


def test_wayfinder_passes_the_question_as_one_argv_without_a_shell(server: Any, monkeypatch: Any) -> None:
    """The question must never reach a shell: metacharacters stay in one argv slot."""
    calls: list[dict] = []

    class FakeCompleted:
        stdout = "answer"
        stderr = ""
        returncode = 0

    def fake_run(argv: Any, **kwargs: Any) -> Any:
        calls.append({"argv": argv, "kwargs": kwargs})
        return FakeCompleted()

    monkeypatch.setattr(server, "_dashscope_key", lambda: "fixture-key")
    monkeypatch.setattr(server.shutil, "which", lambda name: "C:/npm/pi.cmd" if name == "pi" else None)
    monkeypatch.setattr(server.subprocess, "run", fake_run)
    hostile = "状态如何 & echo injected"
    status, payload = server.run_wayfinder_ask(hostile, None)
    assert status == 200 and payload["answer"] == "answer"
    assert len(calls) == 1
    assert calls[0]["argv"] == ["C:/npm/pi.cmd", "-p", hostile]
    assert calls[0]["kwargs"].get("shell") is not True
    assert "shell" not in calls[0]["kwargs"]


def test_wayfinder_reports_a_missing_pi_without_running_anything(server: Any, monkeypatch: Any) -> None:
    def fail_run(argv: Any, **kwargs: Any) -> Any:  # pragma: no cover - must not be called
        raise AssertionError("pi must not be invoked when it is not installed")

    monkeypatch.setattr(server, "_dashscope_key", lambda: "fixture-key")
    monkeypatch.setattr(server.shutil, "which", lambda name: None)
    monkeypatch.setattr(server.subprocess, "run", fail_run)
    status, payload = server.run_wayfinder_ask("状态如何", None)
    assert status == 503 and payload["error"] == "pi_not_installed"


def test_service_unavailable_degrades_to_503(server: Any) -> None:
    from starlette.testclient import TestClient

    with TestClient(server.create_app(None, service_error="OBSERVATORY_HOST_CONFIG 未设置")) as client:
        for path in ("/api/research/package", "/api/research/snapshot", "/api/research/activity",
                     "/api/research/context", "/api/research/advisory", "/api/research/replay/T-1"):
            response = client.get(path)
            assert response.status_code == 503, path
            assert response.json()["error"] == "observatory_service_unavailable"
        assert client.get("/").status_code == 200  # static still served → frontend falls back to mock


def test_agent_environments_endpoint_shape(client: Any) -> None:
    """执行环境清单：真实探测结果的信封，字段缺失只允许是 None。"""
    resp = client.get("/api/compute/instances")
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "live-probe"
    assert isinstance(body["environments"], list)
    assert body["total"] == len(body["environments"])
    assert isinstance(body["counts"], dict)

    # 本机是唯一不依赖外部工具的来源，必须始终在场
    kinds = {env["kind"] for env in body["environments"]}
    assert "host" in kinds

    allowed = {"host", "container", "wsl", "k8s", "cloud-vm"}
    for env in body["environments"]:
        for key in ("id", "kind", "provider", "name", "status"):
            assert key in env, key
        assert env["kind"] in allowed
        # 拿不到真实值就必须是 None —— 这里挡住"用 0 填充"的回归
        assert env["cpu_cores"] is None or isinstance(env["cpu_cores"], int)
        assert env["memory_gib"] is None or isinstance(env["memory_gib"], (int, float))
        assert env["gpu_count"] is None or isinstance(env["gpu_count"], int)
        assert isinstance(env["runtimes"], list)


def test_agent_environments_read_only(client: Any) -> None:
    """写方法在环境端点上同样被拒（只读契约不能漏掉新路由）。"""
    assert client.post("/api/compute/instances").status_code == 405
    assert client.put("/api/compute/instances").status_code == 405
    assert client.delete("/api/compute/instances").status_code == 405


def test_local_gpu_endpoint_shape(client: Any) -> None:
    resp = client.get("/api/compute/local")
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"] == "local"
    assert isinstance(body["gpus"], list)
    assert body["count"] == len(body["gpus"])
    for gpu in body["gpus"]:
        assert gpu["name"]
        assert gpu["memory_total_mib"] is None or isinstance(gpu["memory_total_mib"], int)


def test_compute_providers_envelope(client: Any) -> None:
    """provider 槽位：状态必须是四态之一，未接入的不能带数据。"""
    body = client.get("/api/compute/providers").json()
    assert isinstance(body["providers"], list)
    allowed = {"ready", "no_gpu", "probe_failed", "cli_missing", "not_configured", "not_integrated"}
    for provider in body["providers"]:
        assert provider["status"] in allowed
        if not provider.get("integrated"):
            assert provider["status"] == "not_integrated"


def test_health_is_cheap_and_honest(client: Any) -> None:
    """探活端点必须极轻：不碰 SQLite、不起子进程，否则探活本身成为故障源。"""
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert isinstance(body["pid"], int)
    assert body["service_ready"] is True
    assert body["uptime_s"] >= 0
    routes = set(body["routes"])
    for route in ("/api/health", "/api/compute/instances", "/api/compute/local",
                  "/api/compute/providers", "/api/compute/aliyun",
                  "/api/agents/probe", "/api/research/package"):
        assert route in routes, route


def test_probe_can_be_disabled(monkeypatch: Any, client: Any) -> None:
    """OBSERVATORY_PROBE=0 时跳过外部探测，且如实标注而非返回空数据冒充。"""
    monkeypatch.setenv("OBSERVATORY_PROBE", "0")
    body = client.get("/api/compute/instances", params={"refresh": 1}).json()
    assert body["source"] == "probe-disabled"
    assert body["environments"] == []
    assert body["total"] == 0
    assert any("OBSERVATORY_PROBE" in note for note in body["notes"])


def test_probe_disabled_hides_from_health(monkeypatch: Any, client: Any) -> None:
    monkeypatch.setenv("OBSERVATORY_PROBE", "false")
    assert client.get("/api/health").json()["probe_enabled"] is False
