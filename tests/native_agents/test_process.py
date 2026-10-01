"""Real subprocesses emitting declared mock data; no provider/model calls."""

import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

from orchestration.native_agents.models import HostBinding, LaunchPlan
from contracts.identity import AgentId
from orchestration.native_agents.process import AttachedSession, OwnedProcess, run_headless


def fake_plan(tmp_path: Path, script: str, runtime: str = "codex", session_id: str | None = None) -> LaunchPlan:
    return LaunchPlan(runtime=runtime, mode="headless", argv=(sys.executable, "-u", "-c", script),
                      workspace=tmp_path, stdin_text="discover and claim", session_id=session_id)


@pytest.mark.parametrize(("script", "expected", "exit_code"), [
    ("pass", "unknown", 0),
    ('print(\'{"type":"future.event"}\')', "unknown", 0),
    ("import sys;sys.exit(3)", "failed", 3),
    ('print(\'{"type":"turn.failed","error":{"message":"no"}}\')', "failed", 0),
])
def test_exit_without_terminal_does_not_pass(tmp_path: Path, script: str, expected: str, exit_code: int) -> None:
    result = run_headless(fake_plan(tmp_path, script), tmp_path / "out", timeout_seconds=5,
                          max_tool_calls=3, provenance="mock")
    assert result.state == expected and result.exit_code == exit_code
    assert result.usage.tokens is None and result.usage.cost_usd is None
    assert result.remote_effect == "unknown"
    assert result.acceptance.interface_live == "not_run" and result.acceptance.task_live == "not_run"


def test_later_turn_completed_does_not_erase_original_fatal_error(tmp_path: Path) -> None:
    script = ('print(\'{"type":"error","message":"fatal failure"}\');'
              'print(\'{"type":"turn.completed","usage":{"input_tokens":0,"output_tokens":0}}\')')
    result = run_headless(fake_plan(tmp_path, script), tmp_path / "out", timeout_seconds=5,
                          max_tool_calls=5, provenance="mock")
    assert result.state == "failed"
    assert "fatal failure" in (tmp_path / "out/native.jsonl").read_text()


def test_raw_stream_tool_dedup_and_measured_usage(tmp_path: Path) -> None:
    events = [{"type": "thread.started", "thread_id": "4b30d7cc-bb1d-4ffc-a3bd-813d9c2523ad"},
              {"type": "item.started", "item": {"id": "tool1", "type": "mcp_tool_call", "tool": "discover"}},
              {"type": "item.completed", "item": {"id": "tool1", "type": "mcp_tool_call", "tool": "discover"}},
              {"type": "future.event", "value": None},
              {"type": "turn.completed", "usage": {"input_tokens": 2, "output_tokens": 3}}]
    text = "\n".join(json.dumps(event) for event in events)
    script = "import sys;assert sys.stdin.read()=='discover and claim';print(" + repr(text) + ")"
    observed = []
    result = run_headless(fake_plan(tmp_path, script), tmp_path / "out", timeout_seconds=5,
                          max_tool_calls=5, provenance="mock", on_event=observed.append)
    assert result.state == "completed" and result.observed_tool_calls == 1
    assert result.session_id == events[0]["thread_id"] and result.usage.tokens == 5
    assert result.usage.cost_usd is None and result.remote_effect == "unknown"
    assert observed[3].kind == "unknown"
    assert (tmp_path / "out/native.jsonl").read_text().strip() == text
    assert result.acceptance.task_live == "not_run"


def test_tool_limit_cancels_once_without_replay(tmp_path: Path) -> None:
    script = ('import time,pathlib;pathlib.Path("invocations").write_text("once");'
              'print(\'{"type":"item.started","item":{"id":"tool1","type":"command_execution"}}\',flush=True);time.sleep(30)')
    result = run_headless(fake_plan(tmp_path, script), tmp_path / "out", timeout_seconds=5,
                          max_tool_calls=1, provenance="mock")
    assert result.state == "unknown" and "limit" in result.reason
    assert result.exit_code is not None
    assert result.usage.tokens is None and result.remote_effect == "unknown"
    assert (tmp_path / "invocations").read_text() == "once"


def test_timeout_preserves_failure_and_does_not_retry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Deterministic observer clock: the real process emits its failure before the
    # 0.2-second threshold is crossed. A separate test covers real wall-clock timeout.
    emitted = False

    def on_event(event: object) -> None:
        nonlocal emitted
        emitted = True

    monkeypatch.setattr("orchestration.native_agents.process.time", SimpleNamespace(
        monotonic=lambda: 0.21 if emitted else 0.0, sleep=time.sleep))
    script = 'import time;print(\'{"type":"error","message":"original failure"}\',flush=True);time.sleep(30)'
    result = run_headless(fake_plan(tmp_path, script), tmp_path / "out", timeout_seconds=0.2,
                          max_tool_calls=5, provenance="mock", on_event=on_event)
    assert result.state == "unknown" and "timeout" in result.reason
    assert "original failure" in (tmp_path / "out/native.jsonl").read_text()
    with pytest.raises(FileExistsError):
        run_headless(fake_plan(tmp_path, script), tmp_path / "out", timeout_seconds=0.2,
                     max_tool_calls=5, provenance="mock")


def test_actual_wall_timeout_is_bounded(tmp_path: Path) -> None:
    started = time.monotonic()
    result = run_headless(fake_plan(tmp_path, "import time;time.sleep(30)"), tmp_path / "out",
                          timeout_seconds=0.2, max_tool_calls=5, provenance="mock")
    assert time.monotonic() - started < 4
    assert result.state == "unknown" and "timeout" in result.reason


def test_attached_cancel_never_touches_external_process(tmp_path: Path) -> None:
    external = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(30)"])
    try:
        attached = AttachedSession("codex", "external-native-id")
        assert attached.cancel() is False
        assert external.poll() is None
        result = run_headless(fake_plan(tmp_path, "import time;time.sleep(30)"), tmp_path / "out",
                              timeout_seconds=0.2, max_tool_calls=5, provenance="mock")
        assert result.state == "unknown"
        assert external.poll() is None
    finally:
        external.terminate()
        external.wait(timeout=5)


def test_prelaunch_stop_creates_no_invocation(tmp_path: Path) -> None:
    result = run_headless(fake_plan(tmp_path, "raise Exception('must not run')"), tmp_path / "out",
                          timeout_seconds=5, max_tool_calls=5, provenance="mock", stop_requested=lambda: True)
    assert result.exit_code is None and result.state == "unknown"
    assert not (tmp_path / "out").exists()


def test_resume_mismatch_remains_unknown(tmp_path: Path) -> None:
    requested = "4b30d7cc-bb1d-4ffc-a3bd-813d9c2523ad"
    observed = "8e37ea7c-47d9-4946-8826-f0a545169fa6"
    script = 'print(' + repr(json.dumps({"type": "thread.started", "thread_id": observed})) + ')'
    result = run_headless(fake_plan(tmp_path, script, session_id=requested), tmp_path / "out",
                          timeout_seconds=5, max_tool_calls=5, provenance="mock")
    assert result.state == "unknown" and result.session_id == observed
    assert "different session" in result.reason


def test_unknown_launch_exit_and_mock_cannot_be_live(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Installed CLI discovery is external to this contract. Keep the real live
    # guard, with a deterministic official prefix distinct from either fake argv.
    official_command = (str(tmp_path / "official-codex.exe"),)
    monkeypatch.setattr("orchestration.native_agents.process.resolve_executable", lambda spec: official_command)
    bad = fake_plan(tmp_path, "pass").model_copy(update={"argv": (str(tmp_path / "missing.exe"),)})
    result = run_headless(bad, tmp_path / "out", timeout_seconds=5, max_tool_calls=5, provenance="mock")
    assert result.exit_code is None and result.state == "unknown"
    with pytest.raises(ValueError, match="official CLI"):
        run_headless(fake_plan(tmp_path, "pass"), tmp_path / "live", timeout_seconds=5, max_tool_calls=5)
    assert not (tmp_path / "live").exists()


@pytest.mark.parametrize("instance", [0, 1])
def test_persistent_native_host_attempt_trace(tmp_path: Path, instance: int) -> None:
    attempt = {"task_id": "science-1", "agent": {"role": "builder", "instance": instance}, "attempt": 2}
    raw = {"type": "item.completed", "item": {"id": "t1", "type": "mcp_tool_call", "server": "morph_research", "tool": "lease_task",
           "arguments": {"action": "claim", "task_id": "science-1"},
           "result": {"structured_content": {"attempt_id": attempt}}}}
    script = "print(" + repr(json.dumps(raw)) + ")"
    binding = HostBinding(agent=AgentId(role="builder", instance=0), worker_id="native-author",
                          swarm_id="research-demo", config_path=tmp_path / "host.json")
    plan = fake_plan(tmp_path, script).model_copy(update={"host_binding": binding})
    result = run_headless(plan, tmp_path / "out", timeout_seconds=5, max_tool_calls=5, provenance="mock")
    trace = json.loads((tmp_path / "out/native-bound.jsonl").read_text())
    assert trace["host_binding"]["agent"] == {"role": "builder", "instance": 0}
    assert trace["event"]["reported_attempt"] == attempt and trace["event"]["raw"] == raw
    assert trace["reported_attempt_matches_host"] is (instance == 0)
    assert trace["provenance"] == "mock" and result.state == "unknown"
    if instance == 1:
        assert "host-bound AgentId" in result.reason


@pytest.mark.skipif(os.name != "nt", reason="Windows Job Object API")
def test_owned_windows_job_terminates_descendant_and_preserves_external(tmp_path: Path) -> None:
    marker = tmp_path / "descendant.txt"
    child_script = 'import pathlib,time;time.sleep(1);pathlib.Path(' + repr(str(marker)) + ').write_text("leaked")'
    parent_script = 'import sys,subprocess,time;subprocess.Popen([sys.executable,"-c",' + repr(child_script) + ']);time.sleep(30)'
    # Parent receives code only after it is in our Job Object, avoiding startup races in this test.
    parent = subprocess.Popen([sys.executable, "-c", "import sys;exec(sys.stdin.read())"], stdin=subprocess.PIPE)
    owner = OwnedProcess(parent)
    external = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(30)"])
    try:
        parent.stdin.write(parent_script.encode())
        parent.stdin.close()
        time.sleep(0.15)
        assert owner.cancel() is True
        assert owner.cancel() is False
        time.sleep(1.2)
        assert not marker.exists()
        assert external.poll() is None
    finally:
        owner.cancel()
        external.terminate()
        external.wait(timeout=5)


@pytest.mark.skipif(os.name != "nt", reason="real Windows venv launcher and Job Objects")
def test_windows_venv_barrier_owns_actual_interpreter_before_native_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import _winapi
    from orchestration.native_agents import process as native
    from orchestration.native_agents.windows_job import WindowsJob

    assert sys.prefix != sys.base_prefix  # Run from the private installed venv.
    ready = tmp_path / "barrier-ready"
    # Instrument only the startup resource: publish the real interpreter PID
    # before the unchanged stdin barrier. Job assignment waits for this signal,
    # forcing the launcher/interpreter race instead of relying on timing luck.
    original = Path(native.__file__).with_name("_windows_exec.py").read_text()
    (tmp_path / "_windows_exec.py").write_text(
        "import os,pathlib\npathlib.Path(" + repr(str(ready)) + ").write_text(str(os.getpid()))\n" + original,
        encoding="utf-8",
    )
    monkeypatch.setattr(native, "__file__", str(tmp_path / "process.py"))
    assign = WindowsJob.assign
    assigned: list[int] = []

    def assign_after_interpreter_ready(job: WindowsJob, pid: int) -> None:
        deadline = time.monotonic() + 3
        while not ready.exists():
            assert time.monotonic() < deadline
            time.sleep(0.01)
        assigned.append(pid)
        assign(job, pid)

    monkeypatch.setattr(WindowsJob, "assign", assign_after_interpreter_ready)
    native_pid = tmp_path / "native-pid"
    script = ("import os,pathlib,time;pathlib.Path(" + repr(str(native_pid)) + ").write_text(str(os.getpid()));"
              "print('{\"type\":\"item.started\",\"item\":{\"id\":\"one\",\"type\":\"command_execution\"}}',flush=True);"
              "time.sleep(30)")
    # The native stand-in is real Python, with no venv redirector of its own.
    plan = fake_plan(tmp_path, script).model_copy(update={
        "argv": (sys._base_executable, "-u", "-c", script),
    })
    cleanup = WindowsJob()
    handle = None

    def observe(event: object) -> None:
        nonlocal handle
        if handle is None:
            pid = int(native_pid.read_text())
            handle = _winapi.OpenProcess(0x00100000 | 0x0001, False, pid)
            assign(cleanup, pid)  # Own only this test's child, including on RED.

    external = subprocess.Popen([sys._base_executable, "-c", "import time;time.sleep(30)"])
    try:
        result = run_headless(plan, tmp_path / "out", timeout_seconds=5,
                              max_tool_calls=1, provenance="mock", on_event=observe)
        assert handle is not None
        assert _winapi.WaitForSingleObject(handle, 500) == 0
        assert assigned == [int(ready.read_text())]
        assert result.state == "unknown" and result.exit_code is not None
        assert result.usage.tokens is None and result.remote_effect == "unknown"
        assert AttachedSession("codex", "external").cancel() is False
        assert external.poll() is None
    finally:
        cleanup.terminate()
        cleanup.close()
        if handle is not None:
            _winapi.WaitForSingleObject(handle, 3000)
            _winapi.CloseHandle(handle)
        external.terminate()
        external.wait(timeout=3)


@pytest.mark.skipif(os.name != "nt", reason="real Windows Job Object and inherited descriptors")
def test_windows_cancel_after_parent_exit_cleans_descendant_and_stdio(tmp_path: Path) -> None:
    child = "import time;print('child ready',flush=True);time.sleep(30)"
    script = "import subprocess;subprocess.Popen([" + repr(sys._base_executable) + ",'-u','-c'," + repr(child) + "])"
    parent = subprocess.Popen([sys._base_executable, "-u", "-c", "import sys;exec(sys.stdin.read())"],
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    owner = OwnedProcess(parent)
    external = subprocess.Popen([sys._base_executable, "-c", "import time;time.sleep(30)"])
    try:
        assert parent.stdin is not None and parent.stdout is not None
        parent.stdin.write(script.encode())
        parent.stdin.close()
        parent.stdin = None
        assert parent.stdout.readline() == b"child ready\r\n"
        assert parent.wait(timeout=3) == 0
        with pytest.raises(subprocess.TimeoutExpired):
            parent.communicate(timeout=0.05)
        started = time.monotonic()
        assert owner.cancel() is True
        assert time.monotonic() - started < 4
        parent.communicate(timeout=0.5)
        assert owner.cancel() is False
        assert AttachedSession("codex", "external").cancel() is False
        assert external.poll() is None
    finally:
        owner.cancel()
        for stream in (parent.stdout, parent.stderr):
            if stream is not None:
                stream.close()
        external.terminate()
        external.wait(timeout=3)


@pytest.mark.skipif(os.name != "nt", reason="real Windows owned descendant after native exit")
def test_windows_headless_parent_exit_keeps_descendant_cleanup_unknown(tmp_path: Path) -> None:
    import _winapi
    from orchestration.native_agents.windows_job import WindowsJob

    child_pid = tmp_path / "child-pid"
    child = "import time;time.sleep(30)"
    script = (
        "import pathlib,subprocess\n"
        "p=subprocess.Popen([" + repr(sys._base_executable) + ",'-c'," + repr(child) + "])\n"
        "pathlib.Path(" + repr(str(child_pid)) + ").write_text(str(p.pid))\n"
        "print('{\"type\":\"turn.completed\",\"usage\":{\"input_tokens\":0,\"output_tokens\":0}}',flush=True)\n"
    )
    cleanup = WindowsJob()
    handle = None

    def observe(event: object) -> None:
        nonlocal handle
        pid = int(child_pid.read_text())
        handle = _winapi.OpenProcess(0x00100000 | 0x0001, False, pid)
        cleanup.assign(pid)  # A finally-only safety net for this exact test child.

    try:
        result = run_headless(fake_plan(tmp_path, script), tmp_path / "out", timeout_seconds=5,
                              max_tool_calls=5, provenance="mock", on_event=observe)
        assert handle is not None and _winapi.WaitForSingleObject(handle, 500) == 0
        assert result.exit_code == 0 and result.state == "unknown"
        assert "descendants" in (result.reason or "")
        assert result.usage.tokens is None and result.usage.cost_usd is None
        assert result.remote_effect == "unknown" and result.acceptance.task_live == "not_run"
        assert json.loads((tmp_path / "out/native.jsonl").read_text())["usage"]["input_tokens"] == 0
    finally:
        cleanup.terminate()
        cleanup.close()
        if handle is not None:
            _winapi.WaitForSingleObject(handle, 3000)
            _winapi.CloseHandle(handle)
