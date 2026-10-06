"""Probe behaviour: real observations, declared command lines, sanitized evidence."""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from contracts.readiness import ProbeResult
from readiness.cli import PublicCliProbe
from readiness.credential import CredentialProbe
from readiness.local import LocalMachineProbe
from readiness.mcp import AgentMcpProbe

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
            "serverInfo": {"name": "wayfinder-mcp", "version": "0.4.1"}}})
    elif method == "tools/list":
        send({"jsonrpc": "2.0", "id": message["id"], "result": {"tools": TOOLS}})
'''

MCP_SILENT_STUB = "raise SystemExit(0)\n"

MCP_BAD_VERSION_STUB = r'''
import json
import sys

for line in sys.stdin:
    message = json.loads(line)
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": message["id"], "result": {
        "capabilities": {}, "serverInfo": {"name": "wayfinder-mcp"}}}) + "\n")
    sys.stdout.flush()
'''


def write_stub(directory: Path, name: str, source: str) -> str:
    path = directory / name
    path.write_text(source, encoding="utf-8")
    return str(path)


def test_local_machine_probe_reports_host_facts_without_identity() -> None:
    result = LocalMachineProbe().probe()
    assert isinstance(result, ProbeResult)
    assert (result.probe_id, result.subject) == ("machine:host", "machine")
    assert result.state in {"ok", "degraded"}
    assert result.observed is True
    assert set(result.evidence) == {"os", "python", "cpus", "temp_writable"}
    assert result.evidence["temp_writable"] in {"true", "false"}
    assert not any(Path(value).is_absolute() for value in result.evidence.values())


def test_credential_probe_reports_presence_only() -> None:
    secret = "super-secret-value"
    probe = CredentialProbe(
        probe_id="account:hub", names=["MORPH_TEST_TOKEN"], lookup={"MORPH_TEST_TOKEN": secret}
    )
    result = probe.probe()
    assert (result.state, result.observed) == ("ok", True)
    assert secret not in str(result.model_dump(mode="json"))

    missing = CredentialProbe(
        probe_id="account:hub", names=["MORPH_TEST_TOKEN", "MORPH_TEST_OTHER"], lookup={}
    ).probe()
    assert missing.state == "blocked"
    assert missing.evidence["missing"] == "MORPH_TEST_TOKEN,MORPH_TEST_OTHER"


def test_credential_probe_requires_a_declared_name() -> None:
    with pytest.raises(ValueError):
        CredentialProbe(probe_id="account:hub", names=[])


def test_cli_probe_reports_a_missing_command_as_blocked() -> None:
    result = PublicCliProbe(probe_id="interface:absent", command="morph-absent-cli-xyz").probe()
    assert (result.state, result.observed) == ("blocked", True)
    assert result.evidence["code"] == "command_missing"


def test_cli_probe_reports_a_sanitized_version_line() -> None:
    probe = PublicCliProbe(
        probe_id="interface:python",
        command=sys.executable,
        args=["-c", "print('codex-cli 1.2.3')"],
        report_version_line=True,
    )
    result = probe.probe()
    assert result.state == "ok"
    assert result.evidence["output"] == "codex-cli 1.2.3"


def test_cli_probe_drops_unvetted_output() -> None:
    probe = PublicCliProbe(
        probe_id="interface:python",
        command=sys.executable,
        args=["-c", "print('token=abcdefghijklmnop')"],
        report_version_line=True,
    )
    result = probe.probe()
    assert result.state == "ok"
    assert "output" not in result.evidence


def test_cli_probe_maps_nonzero_exit_according_to_its_declaration() -> None:
    failing = PublicCliProbe(
        probe_id="interface:failing",
        command=sys.executable,
        args=["-c", "raise SystemExit(3)"],
    )
    assert failing.probe().state == "failed"

    not_logged_in = PublicCliProbe(
        probe_id="account:failing",
        subject="account",
        command=sys.executable,
        args=["-c", "raise SystemExit(1)"],
        nonzero_state="blocked",
    )
    result = not_logged_in.probe()
    assert result.state == "blocked"
    assert result.evidence["exit_code"] == "1"


def test_cli_probe_timeout_is_closed_as_failed() -> None:
    probe = PublicCliProbe(
        probe_id="interface:slow",
        command=sys.executable,
        args=["-c", "import time; time.sleep(30)"],
        timeout_seconds=0.5,
    )
    result = probe.probe()
    assert (result.state, result.evidence["code"]) == ("failed", "timeout")


def test_isolated_mode_hides_ambient_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MORPH_TEST_AMBIENT", "present")
    script = "import os, sys; sys.exit(0 if not os.environ.get('MORPH_TEST_AMBIENT') else 3)"

    isolated = PublicCliProbe(
        probe_id="interface:isolated", command=sys.executable, args=["-c", script]
    )
    assert isolated.probe().state == "ok"

    inherited = PublicCliProbe(
        probe_id="account:inherited", subject="account", command=sys.executable,
        args=["-c", script], env_mode="inherit", nonzero_state="blocked",
    )
    result = inherited.probe()
    assert result.evidence.get("exit_code") == "3"
    assert result.state == "blocked"


def test_mcp_probe_completes_a_bounded_handshake(tmp_path: Path) -> None:
    stub = write_stub(tmp_path, "stub_mcp.py", MCP_STUB)
    result = AgentMcpProbe(
        probe_id="interface:wayfinder-mcp",
        command=sys.executable,
        args=[stub],
        require_tools=["search"],
        timeout_seconds=20,
    ).probe()
    assert (result.state, result.observed) == ("ok", True)
    assert result.evidence["server"] == "wayfinder-mcp"
    assert result.evidence["tool_count"] == "2"


def test_mcp_probe_degrades_when_a_required_tool_is_absent(tmp_path: Path) -> None:
    stub = write_stub(tmp_path, "stub_mcp.py", MCP_STUB)
    result = AgentMcpProbe(
        probe_id="interface:wayfinder-mcp",
        command=sys.executable,
        args=[stub],
        require_tools=["deploy"],
        timeout_seconds=20,
    ).probe()
    assert result.state == "degraded"
    assert result.evidence["missing_tools"] == "deploy"


def test_mcp_probe_reports_a_closed_session_and_a_malformed_handshake(tmp_path: Path) -> None:
    silent = write_stub(tmp_path, "silent.py", MCP_SILENT_STUB)
    closed = AgentMcpProbe(
        probe_id="interface:silent", command=sys.executable, args=[silent], timeout_seconds=20
    ).probe()
    assert (closed.state, closed.evidence["code"]) == ("failed", "mcp_closed")

    malformed = write_stub(tmp_path, "bad.py", MCP_BAD_VERSION_STUB)
    incomplete = AgentMcpProbe(
        probe_id="interface:malformed", command=sys.executable, args=[malformed], timeout_seconds=20
    ).probe()
    assert (incomplete.state, incomplete.evidence["code"]) == ("failed", "mcp_malformed")


def test_mcp_probe_reports_a_missing_command_as_blocked() -> None:
    result = AgentMcpProbe(probe_id="interface:absent", command="morph-absent-mcp-xyz").probe()
    assert (result.state, result.evidence["code"]) == ("blocked", "command_missing")


def test_mcp_probe_timeout_is_bounded(tmp_path: Path) -> None:
    slow = write_stub(tmp_path, "slow.py", "import time\ntime.sleep(30)\n")
    result = AgentMcpProbe(
        probe_id="interface:slow", command=sys.executable, args=[slow], timeout_seconds=0.5
    ).probe()
    assert (result.state, result.evidence["code"]) == ("failed", "timeout")


@pytest.mark.parametrize(
    "factory",
    [
        lambda: PublicCliProbe(probe_id="p", command="", args=[]),
        lambda: PublicCliProbe(probe_id="p", command="wf", args=["a\x00b"]),
        lambda: PublicCliProbe(probe_id="p", command="wf", timeout_seconds=0),
        lambda: PublicCliProbe(probe_id="p", command="wf", nonzero_state="not_run"),
        lambda: AgentMcpProbe(probe_id="p", command="wf", timeout_seconds=-1),
        lambda: AgentMcpProbe(probe_id="p", command="wf", require_tools=[""]),
    ],
)
def test_declared_command_lines_are_validated(factory: Callable[[], object]) -> None:
    with pytest.raises(ValueError):
        factory()
