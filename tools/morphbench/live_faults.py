"""Owned real Worker kill probes; control hooks are explicitly contract-local.

Only the inflight arm watches the actual HTTP child's send-entry trace. It is
last in the paid matrix and is never recovered by sending another request.
"""
from __future__ import annotations

import argparse
import ctypes
import json
import os
from pathlib import Path
import subprocess
import sqlite3
import time
from typing import Any

from live_run import enqueue, identity, observe, setup, start, write


def install_hooks(worker: Any, executor: Any, stage: str, marker: Path) -> None:
    def hold() -> None:
        write(marker, {"pid": os.getpid(), "stage": stage, "at": time.time(),
                       "layer": "contract_control_at_real_worker_boundary"})
        time.sleep(180)
        raise RuntimeError("parent_did_not_kill_at_control_boundary")
    if stage == "before_reserve":
        bound = executor.bound
        def held_bound(signal: Any) -> Any:
            hold()
            return bound(signal)
        executor.bound = held_bound
    elif stage in ("before_commit", "after_commit"):
        submit = worker.leases.submit
        def held_submit(*args: Any, **kwargs: Any) -> Any:
            if stage == "before_commit":
                hold()
            result = submit(*args, **kwargs)
            hold()
            return result
        worker.leases.submit = held_submit
    elif stage == "inflight_offline_control":
        execute = executor.execute
        def held_execute(*args: Any, **kwargs: Any) -> Any:
            hold()
            return execute(*args, **kwargs)
        executor.execute = held_execute
    else:
        raise ValueError("unknown_fault_control")


def traces(state: Path) -> list[dict[str, Any]]:
    rows = []
    for path in state.rglob("http-trace.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                rows.append({"path": str(path), **json.loads(line)})
            except json.JSONDecodeError:
                # A currently-written final line is not a complete observation.
                continue
    return rows


def owned_http_handle(pid: int, worker_fact: dict[str, Any]) -> tuple[int | None, dict[str, Any]]:
    """Verify ancestry then retain an OS handle, so later cleanup cannot hit PID reuse."""
    if os.name != "nt":
        return None, {"status": "unsupported_platform", "pid": pid}
    from ctypes import wintypes
    script = (f"$taskProcCursor={pid}; $taskProcRows=@(); for($i=0;$i -lt 4;$i++){{ "
        "$taskProc=Get-CimInstance Win32_Process -Filter ('ProcessId='+$taskProcCursor); "
        "if(-not $taskProc){break}; $taskProcRows += [pscustomobject]@{pid=$taskProc.ProcessId; "
        "parent=$taskProc.ParentProcessId; created=$taskProc.CreationDate.ToUniversalTime().ToString('o')}; "
        "$taskProcCursor=$taskProc.ParentProcessId }; ConvertTo-Json -Compress -InputObject $taskProcRows")
    shell = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    probe = subprocess.run([str(shell), "-NoProfile", "-NonInteractive", "-Command", script],
                           capture_output=True, text=True, timeout=15, check=False)
    rows = json.loads(probe.stdout) if probe.returncode == 0 and probe.stdout.strip() else []
    if not rows or rows[0]["pid"] != pid or not any(r["pid"] == worker_fact["pid"] for r in rows[1:]):
        return None, {"status": "ancestry_not_verified", "pid": pid, "chain": rows}
    kernel = ctypes.windll.kernel32
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    handle = kernel.OpenProcess(0x1000 | 0x0001 | 0x00100000, False, pid)
    if not handle:
        return None, {"status": "already_exited_or_handle_unavailable", "pid": pid, "chain": rows}
    times = [wintypes.FILETIME() for _ in range(4)]
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    if not kernel.GetProcessTimes(handle, *(ctypes.byref(t) for t in times)):
        kernel.CloseHandle(wintypes.HANDLE(handle))
        raise ctypes.WinError()
    created = ((times[0].dwHighDateTime << 32) | times[0].dwLowDateTime) / 10000000 - 11644473600
    from datetime import datetime
    cim_created = datetime.fromisoformat(rows[0]["created"]).timestamp()
    if abs(created - cim_created) > 0.001 or created < worker_fact["create_time"]:
        kernel.CloseHandle(wintypes.HANDLE(handle))
        raise RuntimeError("http_child_creation_time_mismatch")
    return int(handle), {"status": "owned_descendant_handle", "pid": pid, "create_time": created, "chain": rows}


def finish_http(handle: int, fact: dict[str, Any]) -> None:
    from ctypes import wintypes
    kernel = ctypes.windll.kernel32
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    try:
        wait_result = kernel.WaitForSingleObject(handle, 75000)
        fact["wait_result"] = wait_result
        if wait_result == 258:
            fact["terminated_after_75_seconds"] = bool(kernel.TerminateProcess(handle, 1))
            kernel.WaitForSingleObject(handle, 15000)
        exit_code = wintypes.DWORD()
        kernel.GetExitCodeProcess(handle, ctypes.byref(exit_code))
        fact["exit_code"] = exit_code.value
    finally:
        kernel.CloseHandle(handle)


def run(root: Path, stage: str, mode: str) -> dict[str, Any]:
    from contracts.identity import AgentId
    from swarm.code_executor import DashScopeCodeConfig
    from swarm.models import Lease
    cell = {"id": f"fault-{stage}", "category": "code", "system": "single", "seed": 0,
            "request_cap": 1, "fault_stage": stage}
    target, state, worker = setup(root, cell, ["clamp-interval"], 1, mode)
    config = worker.config.model_copy(update={"lease_seconds": 2.0 if stage == "before_reserve" else 180.0, "energy": 1})
    enqueue(worker, "clamp-interval", 0, 0, root / "arrival.jsonl")
    settings = DashScopeCodeConfig()
    spec = root / "victim.json"
    value: dict[str, Any] = {"worker": config.model_dump(mode="json"), "executor": settings.model_dump(mode="json"), "mode": mode}
    if stage != "inflight":
        value["fault_stage"] = stage
    elif mode == "offline":
        value["fault_stage"] = "inflight_offline_control"
    write(spec, value)
    started = time.time()
    victim, owned = start(spec)
    processes = [(victim, owned)]
    marker = spec.with_suffix(".held.json")
    reached = False
    http_handle: int | None = None
    http_fact: dict[str, Any] | None = None
    selected_trace: list[dict[str, Any]] = []
    deadline = time.monotonic() + 150
    while victim.poll() is None and time.monotonic() < deadline:
        if stage == "inflight" and mode == "live":
            selected_trace = traces(state)
            entered = any(r["stage"] == "http_send_entered" for r in selected_trace)
            returned = any(r["stage"] in ("http_response_headers", "http_transport_returned") for r in selected_trace)
            if entered and not returned:
                pid = next(int(r["pid"]) for r in selected_trace if r["stage"] == "http_send_entered")
                http_handle, http_fact = owned_http_handle(pid, owned)
                selected_trace = traces(state)
                reached = http_handle is not None and not any(r["stage"] in
                    ("http_response_headers", "http_transport_returned") for r in selected_trace)
                break
        elif marker.exists():
            observed = json.loads(marker.read_text(encoding="utf-8"))
            if observed["pid"] != victim.pid:
                raise RuntimeError("owned_pid_does_not_match_control_marker")
            reached = True
            break
        time.sleep(0.01)
    old_leases = worker.ledger.leases()
    write(root / "pre-kill.json", {"reached": reached, "owned": owned,
          "leases": [lease.model_dump(mode="json") for lease in old_leases], "http_trace": selected_trace,
          "budget": worker.budget.snapshot().model_dump(mode="json")})
    if victim.poll() is None and not reached and time.monotonic() < deadline:
        try:
            victim.wait(timeout=max(1, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            pass
    if victim.poll() is None:
        victim.kill()
        victim.wait(timeout=15)
        owned["killed_at"] = time.time()
        owned["killed_at_requested_stage"] = reached
    if http_handle is not None and http_fact is not None:
        finish_http(http_handle, http_fact)
    requests_before_restart = len(list(state.rglob("request.json")))
    response_rows = [json.loads(path.read_text(encoding="utf-8")) for path in state.rglob("response.json")]
    with sqlite3.connect(f"file:{(state / 'budget.sqlite3').as_posix()}?mode=ro", uri=True) as database:
        settlements = [row[0] for row in database.execute(
            "SELECT status FROM budget_reservations WHERE swarm_id=?", (config.swarm_id,)).fetchall()]
    before_commit_known = (requests_before_restart == 1 and len(response_rows) == 1
        and response_rows[0].get("usage") is not None and not response_rows[0].get("uncertain")
        and settlements == ["settled"])
    stale_effects: list[str] = []
    stale_errors: list[str] = []
    if reached and stage == "before_reserve":
        expiry = max((lease.expires_at for lease in old_leases), default=time.time())
        time.sleep(max(0, expiry - time.time()) + 0.15)
        for old in old_leases:
            try:
                worker.ledger.submit(Lease.model_validate(old.model_dump()), "stale-probe", {},
                                     apply=lambda check: stale_effects.append("forbidden"))
            except Exception as error:
                stale_errors.append(type(error).__name__ + ":" + str(error))
    # after_commit resumes only durable accepted finalization on the same identity.
    # before_reserve gets a new identity and a second lease, with one request slot.
    if reached and stage in ("before_reserve", "before_commit", "after_commit") and (stage != "before_commit" or before_commit_known):
        successor = config.model_copy(update={"lease_seconds": 180.0})
        if stage == "before_reserve":
            successor = successor.model_copy(update={"agent": AgentId(role="builder", instance=8)})
        resumed = root / "successor.json"
        write(resumed, {"worker": successor.model_dump(mode="json"), "executor": settings.model_dump(mode="json"), "mode": mode})
        process, fact = start(resumed)
        processes.append((process, fact))
        try:
            process.wait(timeout=180)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=15)
            fact["deadline_kill"] = True
    final = observe(root, cell, worker, processes, started, mode)
    final.update({"stage": stage, "stage_reached": reached,
        "stale_submit_effects": stale_effects, "stale_errors": stale_errors,
        "trace_at_kill": selected_trace, "trace_after_kill": traces(state),
        "http_child": http_fact,
        "settlements_before_restart": settlements, "requests_before_restart": requests_before_restart,
        "before_commit_response_usage_known": before_commit_known if stage == "before_commit" else None,
        "request_replayed": False,
        "fault_layer": "contract_control" if stage != "inflight" or mode == "offline" else "real_http_send_entry_observed",
        "limitation": "HTTP send-entry is local transport entry, not proof of packet delivery/server receipt; all unknown effects stop."})
    if stage == "before_commit":
        resumed_result = root / "successor.result.json"
        resumed_status = json.loads(resumed_result.read_text()).get("status", {}) if resumed_result.exists() else {}
        final["before_commit_recovery"] = resumed_status
        final["safe_to_continue"] = (before_commit_known and final["local_request_intents"] == requests_before_restart
            and final["budget"]["pending_reservations"] == 0 and final["budget"]["uncertain_reservations"] == 0
            and resumed_status.get("state") == "needs_review" and final["solved"] == 0)
        final["stop_paid"] = final["stop_paid"] or not final["safe_to_continue"]
    if stage == "inflight":
        final["stop_paid"] = True
        final["unknown_effect"] = reached
    write(root / "result.json", final)
    return final


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--stage", choices=("before_reserve", "before_commit", "after_commit", "inflight"), required=True)
    parser.add_argument("--mode", choices=("offline", "live"), default="offline")
    args = parser.parse_args()
    identity()
    result = run(args.out, args.stage, args.mode)
    print(json.dumps({"stage": args.stage, "reached": result["stage_reached"],
                      "solved": result["solved"], "stop_paid": result["stop_paid"], "mode": args.mode}))
    raise SystemExit(0 if result["stage_reached"] else 1)
