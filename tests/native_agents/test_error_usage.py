"""Real owned subprocess/stdout/exit with an in-memory provider transport only.

All emitted provider data is declared mock. No official CLI, auth, or network call.
"""

import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest

from orchestration.native_agents.models import LaunchPlan
from orchestration.native_agents.process import run_headless


SESSION = "5c787eb6-602b-4e03-9fea-313af2b5c826"


def claude_result(tokens: int | None, cost: float | None, error: bool | None,
                  subtype: str = "success") -> dict[str, object]:
    return {"type": "result", "subtype": subtype, "is_error": error,
            "terminal_reason": "api_error" if error else "end_turn", "session_id": SESSION,
            "total_cost_usd": cost, "usage": {
                "input_tokens": tokens, "output_tokens": 2 if tokens else 0,
                "cache_creation_input_tokens": 4 if tokens else 0,
                "cache_read_input_tokens": 5 if tokens else 0}}


def mock_transport_plan(workspace: Path, results: list[dict[str, object]], *,
                        exit_code: int, requests: int = 1, hold: bool = False) -> LaunchPlan:
    # Count actual httpx calls in the native stand-in, and append one marker per
    # invocation so a second process cannot conceal adapter relaunch/retry.
    script = (
        "import json,pathlib,sys,time,httpx\n"
        "calls=0\n"
        "def transport(request):\n"
        "    global calls\n"
        "    calls+=1\n"
        "    return httpx.Response(401 if " + repr(requests == 10) + " else 200)\n"
        "with httpx.Client(transport=httpx.MockTransport(transport),trust_env=False) as client:\n"
        "    for attempt in range(" + repr(requests) + "):\n"
        "        response=client.post('https://provider.invalid/mock')\n"
        "        if response.status_code==401:\n"
        "            print(json.dumps({'type':'system','subtype':'api_retry',"
        "'attempt':attempt+1,'max_retries':10,'status':401,'error':'authentication_failed'}),flush=True)\n"
        "with pathlib.Path('invocations.jsonl').open('a',encoding='utf-8') as marker:\n"
        "    marker.write(json.dumps({'transport_calls':calls})+'\\n')\n"
        "for result in json.loads(" + repr(json.dumps(results)) + "):\n"
        "    print(json.dumps(result),flush=True)\n"
        + ("time.sleep(30)\n" if hold else "")
        + "sys.exit(" + repr(exit_code) + ")\n"
    )
    return LaunchPlan(runtime="claude", mode="headless", workspace=workspace,
                      argv=(sys.executable, "-u", "-c", script), stdin_text="declared mock")


@pytest.mark.parametrize(("tokens", "cost", "error", "subtype", "exit_code", "requests",
                          "expected_tokens", "expected_cost", "state"), [
    pytest.param(0, 0, True, "success", 1, 10, None, None, "failed", id="auth_retry_synthetic_zero"),
    pytest.param(0, 0, True, "success", 0, 1, None, None, "failed", id="is_error_over_success_and_exit_zero"),
    pytest.param(0, 0, False, "error_during_execution", 0, 1, None, None, "failed", id="error_subtype_over_false_flag"),
    pytest.param(0, 0, False, "success", 0, 1, 0, 0, "completed", id="successful_measured_zero"),
    pytest.param(3, 0.25, True, "success", 1, 1, 14, 0.25, "failed", id="failed_positive_report"),
    pytest.param(3, None, True, "success", 1, 1, 14, None, "failed", id="failed_tokens_only"),
    pytest.param(None, 0.25, True, "success", 1, 1, None, 0.25, "failed", id="failed_cost_only"),
    pytest.param(3, 0, True, "success", 1, 1, 14, None, "failed", id="positive_tokens_unknown_zero_cost"),
    pytest.param(0, 0.25, True, "success", 1, 1, None, 0.25, "failed", id="positive_cost_unknown_zero_tokens"),
    pytest.param(0, 0, False, "success", 1, 1, None, None, "failed", id="exit_failure_with_success_zero"),
    pytest.param(3, 0.25, False, "success", 1, 1, 14, 0.25, "failed", id="exit_failure_with_positive_report"),
    pytest.param(0, 0, None, "success", 0, 1, None, None, "unknown", id="unconfirmed_terminal_zero"),
])
def test_error_usage_through_real_process(tmp_path: Path, tokens: int | None, cost: float | None,
                                        error: bool | None, subtype: str, exit_code: int, requests: int,
                                        expected_tokens: int | None, expected_cost: float | None,
                                        state: str) -> None:
    raw_result = claude_result(tokens, cost, error, subtype)
    observed = []
    plan = mock_transport_plan(tmp_path, [raw_result], exit_code=exit_code, requests=requests)
    # Forward to the real Popen, including Windows' ownership barrier. This is a
    # transport spy, not a replacement for the process/normalizer under test.
    with patch("orchestration.native_agents.process.subprocess.Popen", wraps=subprocess.Popen) as launches:
        outcome = run_headless(plan, tmp_path / "out", timeout_seconds=5, max_tool_calls=5,
                               provenance="mock", on_event=observed.append)
    assert launches.call_count == 1
    assert outcome.exit_code == exit_code and outcome.state == state
    assert outcome.usage.tokens == expected_tokens and outcome.usage.cost_usd == expected_cost
    assert outcome.observed_tool_calls == 0 and outcome.remote_effect == "unknown"
    assert outcome.acceptance.interface_live == outcome.acceptance.task_live == "not_run"
    assert outcome.session_id == SESSION
    records = [json.loads(line) for line in (tmp_path / "out/native.jsonl").read_text().splitlines()]
    assert records[-1] == raw_result and observed[-1].raw == raw_result
    assert sum(record.get("subtype") == "api_retry" for record in records) == (10 if requests == 10 else 0)
    assert (tmp_path / "invocations.jsonl").read_text().splitlines() == [json.dumps({"transport_calls": requests})]
    # A successful event remains a measured zero even if the real exit later
    # contradicts it; only the failed invocation total must become unknown.
    event_tokens, event_cost = (0, 0) if error is False and subtype == "success" and tokens == 0 else (
        expected_tokens, expected_cost)
    assert observed[-1].usage.tokens == event_tokens and observed[-1].usage.cost_usd == event_cost


def test_failed_report_before_later_success_keeps_positive_partial_usage(tmp_path: Path) -> None:
    results = [claude_result(3, 0.25, True), claude_result(0, 0, False)]
    plan = mock_transport_plan(tmp_path, results, exit_code=0)
    with patch("orchestration.native_agents.process.subprocess.Popen", wraps=subprocess.Popen) as launches:
        outcome = run_headless(plan, tmp_path / "out", timeout_seconds=5, max_tool_calls=5, provenance="mock")
    assert launches.call_count == 1 and outcome.exit_code == 0 and outcome.state == "failed"
    assert outcome.usage.tokens == 14 and outcome.usage.cost_usd == 0.25
    assert [json.loads(line) for line in (tmp_path / "out/native.jsonl").read_text().splitlines()] == results
    assert (tmp_path / "invocations.jsonl").read_text().splitlines() == [json.dumps({"transport_calls": 1})]


def test_cancel_after_report_remains_unknown_and_keeps_raw_positive_usage(tmp_path: Path) -> None:
    results = [claude_result(3, 0.25, False)]
    plan = mock_transport_plan(tmp_path, results, exit_code=0, hold=True)
    observed = []
    with patch("orchestration.native_agents.process.subprocess.Popen", wraps=subprocess.Popen) as launches:
        outcome = run_headless(plan, tmp_path / "out", timeout_seconds=5, max_tool_calls=5,
                               provenance="mock", on_event=observed.append,
                               stop_requested=lambda: bool(observed))
    assert launches.call_count == 1 and outcome.exit_code is not None and outcome.state == "unknown"
    assert "cancelled" in outcome.reason and outcome.remote_effect == "unknown"
    assert outcome.usage.tokens is None and outcome.usage.cost_usd is None
    assert observed[-1].usage.tokens == 14 and observed[-1].usage.cost_usd == 0.25
    assert [json.loads(line) for line in (tmp_path / "out/native.jsonl").read_text().splitlines()] == results
    assert (tmp_path / "invocations.jsonl").read_text().splitlines() == [json.dumps({"transport_calls": 1})]
