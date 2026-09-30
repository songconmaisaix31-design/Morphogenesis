"""One explicit native invocation, bounded observation, ownership-safe cleanup.

No retry, task dispatch, process-name killing, global hooks, or credentials store.
"""

from collections.abc import Callable
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import BinaryIO, Literal

from contracts.provenance import Acceptance, Provenance
from contracts.results import Usage
from orchestration.native_agents.events import parse_event
from orchestration.native_agents.models import LaunchPlan, NativeEvent, NativeOutcome, RuntimeId
from orchestration.native_agents.registry import REGISTRY, child_environment, resolve_executable
from orchestration.native_agents.windows_job import WindowsJob


class AttachedSession:
    """Metadata only. No PID attachment or ability to terminate the external owner."""

    def __init__(self, runtime: RuntimeId, session_id: str) -> None:
        self.runtime = runtime
        self.session_id = session_id

    def cancel(self) -> bool:
        return False


class OwnedProcess:
    """Ownership derives solely from our Popen object, never names or persisted PIDs.

    POSIX children use a private process group. Windows uses an unnamed Job Object
    containing this newly launched process and descendants; no taskkill /T.
    """

    def __init__(self, process: subprocess.Popen[bytes]) -> None:
        self._process = process
        self._job: WindowsJob | None = None
        if os.name == "nt" and process.poll() is None:
            try:
                self._job = WindowsJob()
                self._job.assign(process.pid)
            except OSError:
                process.terminate()
                process.wait(timeout=3)
                if self._job:
                    self._job.close()
                raise

    def cancel(self) -> bool:
        process = self._process
        if process.poll() is not None:
            if self._job:
                self._job.close()
            return False
        if os.name == "nt":
            if self._job:
                self._job.terminate()
            else:
                process.terminate()
        else:
            getattr(os, "killpg")(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                process.kill()
            else:
                getattr(os, "killpg")(process.pid, getattr(signal, "SIGKILL"))
            process.wait(timeout=3)
        if self._job:
            self._job.close()
        return True

    def poll(self) -> int | None:
        return self._process.poll()


def launch_interactive(plan: LaunchPlan) -> OwnedProcess:
    """Caller must already have a real terminal; no screen-text readiness claims."""
    if plan.mode != "interactive":
        raise ValueError("interactive launch requires an interactive plan")
    _require_native_command(plan)
    return _spawn_owned(plan, None, None, None)


def _spawn_owned(plan: LaunchPlan, stdin: BinaryIO | None,
                 stdout: BinaryIO | None, stderr: BinaryIO | None) -> OwnedProcess:
    if os.name != "nt":
        return OwnedProcess(subprocess.Popen(plan.argv, cwd=plan.workspace, env=child_environment(),
                                             stdin=stdin, stdout=stdout, stderr=stderr,
                                             shell=False, start_new_session=True))
    # Python waits for one startup message. Assign Job ownership BEFORE the native
    # CLI (or any MCP/tool child) can execute, instead of racing CLI initialization.
    barrier = Path(__file__).with_name("_windows_exec.py")
    process = subprocess.Popen([sys.executable, str(barrier)], cwd=plan.workspace,
                               env=child_environment(), stdin=subprocess.PIPE,
                               stdout=stdout, stderr=stderr, shell=False)
    owner = OwnedProcess(process)
    try:
        assert process.stdin is not None
        payload = {"argv": plan.argv, "stdin_path": str(stdin.name) if stdin else None,
                   "launch_error_path": str(Path(str(stdin.name)).with_name("launch-error.txt")) if stdin else None}
        process.stdin.write((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
        process.stdin.close()
    except BaseException:
        owner.cancel()
        raise
    return owner


def _require_native_command(plan: LaunchPlan) -> None:
    command = resolve_executable(REGISTRY[plan.runtime])
    if plan.argv[:len(command)] != command:
        raise ValueError("live invocation must use the discovered official CLI; test commands require mock")


def run_headless(plan: LaunchPlan, evidence_dir: Path, *, timeout_seconds: float,
                 max_tool_calls: int, provenance: Provenance = "live",
                 stop_requested: Callable[[], bool] | None = None,
                 on_event: Callable[[NativeEvent], None] | None = None) -> NativeOutcome:
    """Persist raw CLI output and observe one native tool loop; never relaunch.

    Limits are observer limits, not hard token/dollar ceilings. Cancellation never
    establishes absence of remote effects, and CLI completion never grants task_live.
    """
    if plan.mode != "headless" or plan.stdin_text is None:
        raise ValueError("headless launch requires stdin text")
    if timeout_seconds <= 0 or max_tool_calls <= 0:
        raise ValueError("positive invocation limits are required")
    if provenance == "replay":
        raise ValueError("replay is observation only; this function starts a process")
    if provenance == "live":
        _require_native_command(plan)
    if stop_requested and stop_requested():
        return NativeOutcome(runtime=plan.runtime, provenance=provenance,
                             acceptance=Acceptance(provenance=provenance), reason="stopped before launch")
    evidence_dir.mkdir(parents=True, exist_ok=False)
    output = evidence_dir / "native.jsonl"
    session_id = plan.session_id
    terminal: str | None = None
    terminal_usage: list[Usage] = []
    tool_ids: set[str] = set()
    anonymous_tools = 0
    reason: str | None = None
    exit_code: int | None = None
    owner: OwnedProcess | None = None
    offset = 0
    pending = b""

    def consume(data: bytes, *, final: bool = False) -> None:
        nonlocal pending, session_id, terminal, anonymous_tools, reason
        pending += data
        lines = pending.split(b"\n")
        pending = lines.pop()
        if final and pending:
            lines.append(pending)
            pending = b""
        for line in lines:
            if not line.strip():
                continue
            for event in parse_event(plan.runtime, line.decode("utf-8", errors="replace")):
                if event.session_id:
                    session_id = event.session_id
                    if plan.session_id and event.session_id != plan.session_id:
                        reason = "native resume reported a different session; no automatic continuation"
                if event.kind in {"tool", "tool_result"}:
                    if event.tool_id:
                        tool_ids.add(event.tool_id)
                    else:
                        anonymous_tools += 1  # Conservatively bound unidentifiable calls.
                if event.terminal:
                    terminal = "failed" if "failed" in {terminal, event.terminal} else event.terminal
                    terminal_usage.append(event.usage)
                if plan.host_binding:
                    identity_matches = None
                    if event.reported_attempt:
                        identity_matches = event.reported_attempt.agent == plan.host_binding.agent
                        if not identity_matches:
                            reason = "MCP reported attempt differs from host-bound AgentId; stop without replay"
                    record = {"host_binding": plan.host_binding.model_dump(mode="json"),
                              "native_session_id": session_id, "provenance": provenance,
                              "reported_attempt_matches_host": identity_matches,
                              "event": event.model_dump(mode="json")}
                    # An ordinary evidence log; the existing ledger remains authoritative.
                    with (evidence_dir / "native-bound.jsonl").open("a", encoding="utf-8", newline="\n") as trace:
                        trace.write(json.dumps(record, ensure_ascii=False) + "\n")
                        trace.flush()
                        os.fsync(trace.fileno())
                if on_event:
                    on_event(event)

    try:
        with output.open("wb") as stdout, (evidence_dir / "stderr.txt").open("wb") as stderr:
            # File stdin avoids pipe deadlock on a large prompt, preserves exact UTF-8,
            # and EOF signals one native turn. No fabricated structured event input.
            with (evidence_dir / "prompt.txt").open("w+b") as stdin:
                stdin.write(plan.stdin_text.encode("utf-8"))
                stdin.seek(0)
                stdin.flush()
                owner = _spawn_owned(plan, stdin, stdout, stderr)
                started = time.monotonic()
                while True:
                    with output.open("rb") as reader:
                        reader.seek(offset)
                        data = reader.read()
                        offset = reader.tell()
                    consume(data)
                    exit_code = owner.poll()
                    if exit_code is not None:
                        break
                    if stop_requested and stop_requested():
                        reason = "cancelled; usage and remote effect may be unknown"
                    elif time.monotonic() - started >= timeout_seconds:
                        reason = "timeout; usage and remote effect may be unknown"
                    elif len(tool_ids) + anonymous_tools >= max_tool_calls:
                        reason = "tool observation limit reached; remote effect remains unknown"
                    if reason:
                        owner.cancel()
                        exit_code = owner.poll()
                        break
                    time.sleep(0.05)
        with output.open("rb") as reader:
            reader.seek(offset)
            consume(reader.read(), final=True)
        launch_error = evidence_dir / "launch-error.txt"
        if launch_error.exists():
            reason = "native launch failure: " + launch_error.read_text(encoding="utf-8")
            exit_code = None  # The barrier exited, but the native CLI never started.
    except KeyboardInterrupt:
        reason = "interrupted; usage and remote effect may be unknown"
    except (OSError, subprocess.SubprocessError) as exc:
        reason = f"launch/observation failure: {type(exc).__name__}"
    finally:
        if owner is not None:
            owner.cancel()
    known_tokens = [item.tokens for item in terminal_usage]
    known_costs = [item.cost_usd for item in terminal_usage]
    tokens = sum(value for value in known_tokens if value is not None) if known_tokens and all(
        value is not None for value in known_tokens) else None
    cost = sum(value for value in known_costs if value is not None) if known_costs and all(
        value is not None for value in known_costs) else None
    # Cancellation or observation failure can hide additional consumption after a reported turn.
    usage = Usage(tokens=tokens, cost_usd=cost) if reason is None else Usage()
    state: Literal["completed", "failed", "unknown"] = "unknown"
    if reason is None and exit_code is not None:
        if exit_code != 0 or terminal == "failed":
            state = "failed"
        elif terminal == "completed":
            state = "completed"
    # A real failed exit can contradict a successful zero-valued result event.
    # Preserve positive reports; failure zeros cannot establish absent billing.
    if state == "failed":
        usage = Usage(tokens=None if usage.tokens == 0 else usage.tokens,
                      cost_usd=None if usage.cost_usd == 0 else usage.cost_usd)
    return NativeOutcome(runtime=plan.runtime, session_id=session_id, exit_code=exit_code,
                         state=state, usage=usage, observed_tool_calls=len(tool_ids) + anonymous_tools,
                         reason=reason, provenance=provenance,
                         acceptance=Acceptance(provenance=provenance))
