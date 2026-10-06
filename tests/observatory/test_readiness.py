"""Readiness contract, declared providers and the /api/readiness surface.

The point of these tests is the *honesty* rule: an undeclared dimension is
``not_run``, a state other than ``not_run`` must come from a real observation,
and the provider set is data rather than the machine this app was written on.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from swarm.observatory import (
    EXAMPLE_MANIFEST,
    CliProvider,
    CredentialFileProvider,
    CredentialProvider,
    EnvironmentReport,
    HostProvider,
    McpProvider,
    ProbeResult,
    ProviderConfigError,
    ProviderRegistry,
    build_registry,
    example_manifest_json,
    load_manifest,
)

SERVER_PATH = Path(__file__).resolve().parents[2] / "src" / "env-observatory" / "server.py"


def _load_server_module() -> Any:
    """Load server.py by path (its directory name is not importable as a package)."""
    spec = importlib.util.spec_from_file_location("env_observatory_server_readiness", SERVER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module", name="server")
def server_module() -> Any:
    return _load_server_module()


@pytest.fixture(name="client")
def client_fixture(server: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Any]:
    """A client whose provider set is nothing but the host provider."""
    from starlette.testclient import TestClient

    monkeypatch.delenv("OBSERVATORY_PROVIDERS", raising=False)
    monkeypatch.delenv("OBSERVATORY_PROBE", raising=False)
    with TestClient(server.create_app(None)) as client:
        yield client


# ---------------------------------------------------------------------------
# contract rules
# ---------------------------------------------------------------------------

def _observation(provider_id: str, subject: str, state: str) -> ProbeResult:
    return ProbeResult(provider_id=provider_id, subject=subject, state=state, observed=state != "not_run")


def test_not_run_cannot_claim_an_observation() -> None:
    with pytest.raises(ValueError):
        ProbeResult(provider_id="p", subject="machine", state="not_run", observed=True)


@pytest.mark.parametrize("state", ["ok", "degraded", "blocked", "failed"])
def test_any_other_state_requires_a_real_observation(state: str) -> None:
    with pytest.raises(ValueError):
        ProbeResult(provider_id="p", subject="machine", state=state, observed=False)


def _report(results: list[ProbeResult]) -> EnvironmentReport:
    from swarm.observatory.contracts import dimension_states, overall_state

    dimensions = dimension_states(results)
    return EnvironmentReport(overall=overall_state(dimensions), dimensions=dimensions, results=results)


def test_only_full_coverage_can_be_ok() -> None:
    partial = _report([_observation("h", "machine", "ok")])
    assert partial.overall == "degraded"
    assert partial.dimensions == {"machine": "ok", "interface": "not_run", "account": "not_run"}
    complete = _report([_observation(s, s, "ok") for s in ("machine", "interface", "account")])
    assert complete.overall == "ok"


def test_report_rejects_dimensions_that_disagree_with_the_evidence() -> None:
    with pytest.raises(ValueError):
        EnvironmentReport(
            overall="ok",
            dimensions={"machine": "ok", "interface": "ok", "account": "ok"},
            results=[_observation("h", "machine", "ok")],
        )


def test_report_rejects_a_duplicated_provider_id() -> None:
    with pytest.raises(ValueError):
        _report([_observation("h", "machine", "ok"), _observation("h", "interface", "ok")])


# ---------------------------------------------------------------------------
# registry rules
# ---------------------------------------------------------------------------

class ExplodingProvider:
    provider_id = "boom"
    subject = "interface"
    kind = "cli"
    label = "boom"

    def probe(self) -> ProbeResult:
        raise RuntimeError("boom")


class MismatchedProvider:
    provider_id = "declared"
    subject = "interface"
    kind = "cli"
    label = "declared"

    def probe(self) -> ProbeResult:
        return ProbeResult(provider_id="other", subject="interface", state="ok", observed=True)


def test_an_empty_registry_is_not_run_and_says_so() -> None:
    report = ProviderRegistry().report()
    assert report.overall == "not_run"
    assert report.results == []
    assert any("未声明任何 provider" in note for note in report.notes)


def test_a_provider_that_raises_closes_as_failed() -> None:
    report = ProviderRegistry((ExplodingProvider(),)).report()
    assert report.results[0].state == "failed"
    assert report.results[0].evidence["code"] == "provider_error"
    assert report.overall == "failed"


def test_a_provider_returning_another_identity_is_rejected() -> None:
    report = ProviderRegistry((MismatchedProvider(),)).report()
    assert report.results[0].evidence["code"] == "provider_contract_mismatch"


def test_duplicate_provider_ids_are_refused() -> None:
    with pytest.raises(ValueError):
        ProviderRegistry((HostProvider(), HostProvider()))


def test_probe_disabled_runs_nothing() -> None:
    registry = ProviderRegistry((HostProvider(),), probe_enabled=False)
    report = registry.report()
    assert [result.state for result in report.results] == ["not_run"]
    assert report.results[0].observed is False
    assert any("OBSERVATORY_PROBE" in note for note in report.notes)


def test_a_cache_window_keeps_one_report() -> None:
    counter = {"calls": 0}

    class CountingProvider:
        provider_id = "counter"
        subject = "machine"
        kind = "host"
        label = "counting"

        def probe(self) -> ProbeResult:
            counter["calls"] += 1
            return ProbeResult(provider_id="counter", subject="machine", state="ok", observed=True)

    clock = {"now": 0.0}
    registry = ProviderRegistry((CountingProvider(),), clock=lambda: clock["now"], cache_seconds=60)
    first = registry.report()
    assert registry.report() is first
    assert counter["calls"] == 1
    registry.invalidate()
    registry.report()
    assert counter["calls"] == 2


def test_the_default_deployment_declares_only_the_host() -> None:
    registry = build_registry(environ={})
    assert registry.provider_ids == ("host:self",)
    report = registry.report()
    assert report.dimensions["machine"] in {"ok", "degraded"}
    assert report.dimensions["interface"] == "not_run"
    assert report.dimensions["account"] == "not_run"


# ---------------------------------------------------------------------------
# providers
# ---------------------------------------------------------------------------

def test_host_provider_reports_facts_without_identity() -> None:
    result = HostProvider().probe()
    assert (result.state, result.observed) == ("ok", True)
    assert set(result.evidence) == {"os", "python", "cpus", "temp_writable"}
    assert not any(Path(value).is_absolute() for value in result.evidence.values())


def test_a_cli_provider_checks_presence_without_executing() -> None:
    present = CliProvider(provider_id="cli:self", command=sys.executable, execute=False).probe()
    assert (present.state, present.evidence["code"]) == ("ok", "present")
    absent = CliProvider(provider_id="cli:absent", command="observatory-absent-cli-xyz").probe()
    assert (absent.state, absent.evidence["code"]) == ("blocked", "command_missing")


def test_a_cli_provider_reports_only_a_version_shaped_line() -> None:
    probe = CliProvider(
        provider_id="cli:version", command=sys.executable,
        args=["-c", "print('aliyun 3.0.233')"], report_version_line=True,
    )
    assert probe.probe().evidence["output"] == "aliyun 3.0.233"
    secret = CliProvider(
        provider_id="cli:secret", command=sys.executable,
        args=["-c", "print('token=abcdefghijklmnop')"], report_version_line=True,
    )
    assert "output" not in secret.probe().evidence


def test_a_cli_provider_timeout_closes_as_failed() -> None:
    probe = CliProvider(
        provider_id="cli:slow", command=sys.executable,
        args=["-c", "import time; time.sleep(30)"], timeout_seconds=0.5,
    )
    result = probe.probe()
    assert (result.state, result.evidence["code"]) == ("failed", "timeout")


def test_credential_provider_reports_presence_only() -> None:
    secret = "super-secret-value"
    present = CredentialProvider(
        provider_id="account:key", names=["OBS_TEST_KEY"], lookup={"OBS_TEST_KEY": secret}
    ).probe()
    assert (present.state, present.evidence["present"]) == ("ok", "1/1")
    assert secret not in json.dumps(present.model_dump(mode="json"))
    missing = CredentialProvider(provider_id="account:key", names=["OBS_TEST_KEY"], lookup={}).probe()
    assert (missing.state, missing.evidence["missing"]) == ("blocked", "OBS_TEST_KEY")


def test_credential_file_provider_reports_key_presence_only(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"mode": "AK", "access_key_id": "AK-not-a-secret"}), encoding="utf-8")
    ok = CredentialFileProvider(provider_id="account:file", path=config, keys=["mode", "access_key_id"]).probe()
    assert ok.state == "ok"
    assert "AK-not-a-secret" not in json.dumps(ok.model_dump(mode="json"))

    partial = CredentialFileProvider(provider_id="account:file", path=config, keys=["mode", "absent"]).probe()
    assert (partial.state, partial.evidence["missing"]) == ("degraded", "absent")

    missing = CredentialFileProvider(provider_id="account:file", path=tmp_path / "nope.json", keys=[]).probe()
    assert (missing.state, missing.evidence["code"]) == ("blocked", "file_missing")


MCP_STUB = r'''
import json
import sys

TOOLS = [{"name": "search"}, {"name": "graph"}]


def send(payload):
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()


for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        message = json.loads(line)
    except ValueError:
        continue
    method = message.get("method")
    if method == "initialize":
        send({"jsonrpc": "2.0", "id": message["id"], "result": {
            "protocolVersion": "2025-06-18", "capabilities": {},
            "serverInfo": {"name": "research-mcp", "version": "0.3.0"}}})
    elif method == "tools/list":
        send({"jsonrpc": "2.0", "id": message["id"], "result": {"tools": TOOLS}})
'''


def test_mcp_provider_completes_a_bounded_handshake(tmp_path: Path) -> None:
    stub = tmp_path / "stub_mcp.py"
    stub.write_text(MCP_STUB, encoding="utf-8")
    ok = McpProvider(
        provider_id="mcp:research", command=sys.executable, args=[str(stub)],
        require_tools=["search"], timeout_seconds=20,
    ).probe()
    assert (ok.state, ok.evidence["server"], ok.evidence["tool_count"]) == ("ok", "research-mcp", "2")

    degraded = McpProvider(
        provider_id="mcp:research", command=sys.executable, args=[str(stub)],
        require_tools=["deploy"], timeout_seconds=20,
    ).probe()
    assert (degraded.state, degraded.evidence["missing_tools"]) == ("degraded", "deploy")


def test_mcp_provider_reports_a_missing_command_and_a_closed_session(tmp_path: Path) -> None:
    absent = McpProvider(provider_id="mcp:absent", command="observatory-absent-mcp-xyz").probe()
    assert (absent.state, absent.evidence["code"]) == ("blocked", "command_missing")
    silent = tmp_path / "silent.py"
    silent.write_text("raise SystemExit(0)\n", encoding="utf-8")
    closed = McpProvider(
        provider_id="mcp:silent", command=sys.executable, args=[str(silent)], timeout_seconds=20
    ).probe()
    assert (closed.state, closed.evidence["code"]) == ("failed", "mcp_closed")


# ---------------------------------------------------------------------------
# manifest
# ---------------------------------------------------------------------------

def _write_manifest(tmp_path: Path, document: dict[str, Any]) -> Path:
    path = tmp_path / "providers.json"
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    return path


def test_the_reference_manifest_is_itself_valid(tmp_path: Path) -> None:
    providers = load_manifest(_write_manifest(tmp_path, EXAMPLE_MANIFEST))
    ids = [provider.provider_id for provider in providers]
    assert ids[0] == "host:self"
    # wayfinder is sugar: its command and its credential become two real checks
    assert "wayfinder:local:cli" in ids and "wayfinder:local:key" in ids
    assert json.loads(example_manifest_json())["schema"] == "observatory.providers/1"


@pytest.mark.parametrize(
    "document",
    [
        {"schema": "observatory.providers/2", "providers": []},
        {"schema": "observatory.providers/1", "providers": []},
        {"schema": "observatory.providers/1", "providers": [{"kind": "shell", "provider_id": "p"}]},
        {"schema": "observatory.providers/1", "providers": [{"kind": "cli", "provider_id": "p", "command": "x", "shell": True}]},
        {"schema": "observatory.providers/1", "providers": [{"kind": "cli", "provider_id": "p"}]},
        {"schema": "observatory.providers/1", "providers": [
            {"kind": "host", "provider_id": "p"},
            {"kind": "host", "provider_id": "p"},
        ]},
        {"schema": "observatory.providers/1", "providers": [
            {"kind": "cli", "provider_id": "p", "command": "x", "timeout_seconds": "soon"},
        ]},
        {"schema": "observatory.providers/1", "providers": [
            {"kind": "cli", "provider_id": "p", "command": "x", "subject": "cluster"},
        ]},
    ],
)
def test_a_rejected_manifest_is_fail_closed(tmp_path: Path, document: dict[str, Any]) -> None:
    with pytest.raises(ProviderConfigError):
        load_manifest(_write_manifest(tmp_path, document))


def test_a_broken_manifest_yields_the_host_only_with_a_note(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("{", encoding="utf-8")
    registry = build_registry(environ={"OBSERVATORY_PROVIDERS": str(path)})
    assert registry.provider_ids == ("host:self",)
    assert any("未通过校验" in note for note in registry.report().notes)


# ---------------------------------------------------------------------------
# HTTP surface
# ---------------------------------------------------------------------------

def test_readiness_endpoint_is_contract_shaped(client: Any) -> None:
    body = client.get("/api/readiness").json()
    assert body["schema_version"] == "observatory.readiness/1"
    assert set(body["dimensions"]) == {"machine", "interface", "account"}
    assert [result["provider_id"] for result in body["results"]] == ["host:self"]
    assert body["overall"] == "degraded"
    assert any("not_run" in note for note in body["notes"])


def test_readiness_is_read_only(client: Any) -> None:
    for method in ("post", "put", "delete"):
        assert getattr(client, method)("/api/readiness").status_code == 405


def test_headers_and_probe_switch_apply_to_readiness(client: Any, monkeypatch: pytest.MonkeyPatch, server: Any) -> None:
    from starlette.testclient import TestClient

    monkeypatch.setenv("OBSERVATORY_PROBE", "0")
    with TestClient(server.create_app(None)) as off:
        body = off.get("/api/readiness").json()
    assert [result["state"] for result in body["results"]] == ["not_run"]
    assert any("OBSERVATORY_PROBE" in note for note in body["notes"])


def test_compute_providers_lists_only_declared_providers(client: Any) -> None:
    body = client.get("/api/compute/providers").json()
    ids = [provider["id"] for provider in body["providers"]]
    assert ids == ["host:self"]
    allowed = {"ready", "no_gpu", "probe_failed", "cli_missing", "not_configured", "not_integrated"}
    for provider in body["providers"]:
        assert provider["status"] in allowed
        assert provider["integrated"] is (provider["status"] != "not_integrated")
        assert provider["readiness"] in {"not_run", "ok", "degraded", "blocked", "failed"}
    # the old fixed vendor slots are gone: an undeclared provider is not invented
    assert not {"tencent", "aws", "azure"} & set(ids)


def test_a_declared_manifest_shows_up_in_both_surfaces(
    server: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from starlette.testclient import TestClient

    manifest = _write_manifest(tmp_path, {
        "schema": "observatory.providers/1",
        "providers": [
            {"kind": "cli", "provider_id": "cli:absent", "label": "缺席 CLI", "command": "observatory-absent-cli-xyz"},
            {"kind": "credential", "provider_id": "account:key", "label": "凭据", "names": ["OBSERVATORY_ABSENT_KEY"]},
        ],
    })
    monkeypatch.setenv("OBSERVATORY_PROVIDERS", str(manifest))
    with TestClient(server.create_app(None)) as client:
        readiness = client.get("/api/readiness").json()
        providers = client.get("/api/compute/providers").json()["providers"]

    assert [result["provider_id"] for result in readiness["results"]] == ["host:self", "cli:absent", "account:key"]
    assert readiness["dimensions"]["interface"] == "blocked"
    assert readiness["dimensions"]["account"] == "blocked"
    assert readiness["overall"] == "blocked"
    by_id = {provider["id"]: provider for provider in providers}
    assert by_id["cli:absent"]["status"] == "cli_missing"
    assert by_id["cli:absent"]["readiness"] == "blocked"
    assert by_id["account:key"]["status"] == "not_configured"
    assert by_id["host:self"]["integrated"] is True


def test_health_advertises_the_readiness_route(client: Any) -> None:
    routes = set(client.get("/api/health").json()["routes"])
    assert "/api/readiness" in routes
