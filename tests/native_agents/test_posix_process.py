"""Real private POSIX groups, inherited descriptors, and unrelated processes."""

import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest

from orchestration.native_agents.models import LaunchPlan
from orchestration.native_agents.process import AttachedSession, OwnedProcess, run_headless


pytestmark = pytest.mark.skipif(os.name != "posix", reason="real POSIX process groups required")


def parent_script(tmp_path: Path, *, exit_parent: bool) -> str:
    # TERM is deliberately ignored by the owned child. Readiness is published
    # only after the handler is installed; stdout and stderr remain inherited.
    child = (
        "import pathlib,signal,time\n"
        "signal.signal(signal.SIGTERM,signal.SIG_IGN)\n"
        "pathlib.Path('ready').write_text('ready')\n"
        "print('child ready',flush=True)\n"
        "counter=0\n"
        "while True:\n"
        "    counter+=1\n"
        "    pathlib.Path('heartbeat').write_text(str(counter))\n"
        "    time.sleep(0.02)\n"
    )
    return (
        "import pathlib,subprocess,sys,time\n"
        "subprocess.Popen([sys.executable,'-u','-c'," + repr(child) + "],stdin=subprocess.DEVNULL)\n"
        "deadline=time.monotonic()+2\n"
        "while not pathlib.Path('ready').exists():\n"
        "    assert time.monotonic()<deadline\n"
        "    time.sleep(0.01)\n"
        + ("print('{\"type\":\"turn.completed\",\"usage\":{\"input_tokens\":0,\"output_tokens\":0}}',flush=True)\n"
           if exit_parent else "time.sleep(30)\n")
    )


def stop_test_group(parent: subprocess.Popen[bytes]) -> None:
    # Always clean the test's own private group, including on the original RED.
    try:
        os.killpg(parent.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    parent.wait(timeout=3)
    for stream in (parent.stdin, parent.stdout, parent.stderr):
        if stream is not None:
            stream.close()


@pytest.mark.parametrize("exit_parent", [True, False], ids=["parent_already_exited", "parent_exits_on_term"])
def test_cancel_cleans_owned_group_even_when_parent_wait_finishes(tmp_path: Path, exit_parent: bool) -> None:
    parent = subprocess.Popen([sys.executable, "-u", "-c", "import sys;exec(sys.stdin.read())"],
                              cwd=tmp_path, start_new_session=True, stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    external = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(30)"], start_new_session=True)
    owner = OwnedProcess(parent)
    attached = AttachedSession("codex", "unrelated-native-session")
    try:
        assert parent.stdin is not None and parent.stdout is not None
        parent.stdin.write(parent_script(tmp_path, exit_parent=exit_parent).encode())
        parent.stdin.close()
        parent.stdin = None
        assert parent.stdout.readline() == b"child ready\n"
        if exit_parent:
            assert parent.wait(timeout=3) == 0
            # The root is reaped, but its child still holds both pipes open.
            with pytest.raises(subprocess.TimeoutExpired):
                parent.communicate(timeout=0.05)
        started = time.monotonic()
        assert owner.cancel() is True
        assert time.monotonic() - started < 4
        parent.communicate(timeout=0.5)  # Both inherited descriptors must reach EOF.
        assert owner.cancel() is False
        assert attached.cancel() is False and external.poll() is None
    finally:
        stop_test_group(parent)
        external.terminate()
        external.wait(timeout=3)


@pytest.mark.parametrize("exit_parent", [True, False], ids=["natural_exit_with_owned_child", "timeout_with_owned_child"])
def test_headless_cleans_group_and_keeps_usage_unknown(tmp_path: Path, exit_parent: bool) -> None:
    external = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(30)"], start_new_session=True)
    spawned: list[subprocess.Popen[bytes]] = []
    # Forward the external launch boundary; cleanup on RED uses only this Popen's
    # explicitly requested private group, without replacing any guard or signal.
    from unittest.mock import patch
    real_popen = subprocess.Popen

    def launch(*args: object, **kwargs: object) -> subprocess.Popen[bytes]:
        process = real_popen(*args, **kwargs)
        spawned.append(process)
        return process

    plan = LaunchPlan(runtime="codex", mode="headless", workspace=tmp_path,
                      argv=(sys.executable, "-u", "-c", parent_script(tmp_path, exit_parent=exit_parent)),
                      stdin_text="declared mock")
    try:
        started = time.monotonic()
        with patch("orchestration.native_agents.process.subprocess.Popen", side_effect=launch):
            outcome = run_headless(plan, tmp_path / "out", timeout_seconds=0.2, max_tool_calls=5, provenance="mock")
        assert time.monotonic() - started < 4
        assert len(spawned) == 1 and (tmp_path / "ready").exists()
        before = (tmp_path / "heartbeat").read_text()
        time.sleep(0.1)
        assert (tmp_path / "heartbeat").read_text() == before
        assert outcome.state == "unknown" and outcome.exit_code is not None
        assert outcome.usage.tokens is None and outcome.usage.cost_usd is None
        assert outcome.remote_effect == "unknown" and outcome.acceptance.task_live == "not_run"
        assert "descendants" in (outcome.reason or "") if exit_parent else "timeout" in (outcome.reason or "")
        assert AttachedSession("codex", "unrelated-native-session").cancel() is False
        assert external.poll() is None
    finally:
        for parent in spawned:
            stop_test_group(parent)
        external.terminate()
        external.wait(timeout=3)


def test_nonprivate_owned_root_does_not_signal_callers_group() -> None:
    # Same group as pytest: group signalling here would kill this test and the
    # unrelated process. Ownership of a root alone must not imply group ownership.
    parent = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(30)"])
    external = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(30)"])
    try:
        assert OwnedProcess(parent).cancel() is True
        assert external.poll() is None
    finally:
        for process in (parent, external):
            if process.poll() is None:
                process.kill()
            process.wait(timeout=3)
