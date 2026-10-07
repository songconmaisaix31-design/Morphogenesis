"""Thin process/arrival driver for installed Worker.run; never routes or grades tasks.

Offline mode is an explicit mock HTTP control. Live mode uses the product's
DashScope HTTP child. Run from a private evidence cwd, with immutable new output.
"""
from __future__ import annotations

import argparse
from collections import Counter
import ctypes
from datetime import datetime, timezone
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
from typing import Any

from live_cases import BY_NAME, DEFECTS, PHASES, PROFILE_ORDER, PROFILES, PUBLIC_SPEC
from live_plan import MODEL, SYSTEMS, plan


def write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def append(path: Path, value: Any) -> None:
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, allow_nan=False) + "\n")


def provider_stop(state: Path) -> bool:
    for path in state.rglob("response.json"):
        try:
            response = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return True
        status = response.get("http_status")
        if response.get("uncertain") or isinstance(status, int) and status >= 400:
            return True
    return False


def unknown_effect(response: dict[str, Any]) -> bool:
    if response.get("error_kind") == "credential_unavailable":
        return False
    if response.get("classification") == "confirmed_rejection":
        return False
    return not response or bool(response.get("uncertain"))


def workers_quiescent(processes: list[tuple[subprocess.Popen[bytes], dict[str, Any]]], state: Path) -> bool:
    for process, fact in processes:
        if process.poll() is not None:
            continue
        spec = json.loads(Path(fact["spec"]).read_text(encoding="utf-8"))
        agent = spec["worker"]["agent"]
        status_path = state / "workers" / f"{agent['role']}-{agent['instance']}.json"
        try:
            status = json.loads(status_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False
        if (status.get("pid") != process.pid or status.get("state") not in ("idle", "exhausted", "stopped", "sleeping")
                or status.get("active_reservation") is not None or status.get("pending_finalization") is not None):
            return False
    return True


def identity() -> dict[str, Any]:
    # A restarted terminal may inherit the user's variable. Remove it from this
    # process without reading/logging its value; HTTP child reads User scope.
    if "DASHSCOPE_API_KEY" in os.environ:
        del os.environ["DASHSCOPE_API_KEY"]
    import swarm.worker_loop
    import swarm.code_executor
    import local_assets.validate
    modules = {m.__name__: str(Path(m.__file__ or "").resolve()) for m in
               (swarm.worker_loop, swarm.code_executor, local_assets.validate)}
    site = Path(sys.prefix).resolve() / "Lib" / "site-packages"
    if not all(Path(p).is_relative_to(site) for p in modules.values()):
        raise RuntimeError("product_import_must_be_installed")
    dist = importlib.metadata.distribution("morphogenesis")
    direct = json.loads(dist.read_text("direct_url.json") or "{}")
    if direct.get("dir_info", {}).get("editable"):
        raise RuntimeError("editable_product_forbidden")
    return {"modules": modules, "version": dist.version, "direct_url": direct,
            "python": sys.executable, "cwd": str(Path.cwd())}


def mock_executor(config: Any) -> Any:
    """Positive HTTP control only; this result is never counted as live science."""
    import httpx
    from live_cases import _source
    from swarm.code_executor import DashScopeCodeExecutor
    def respond(request: httpx.Request) -> httpx.Response:
        request_body = json.loads(request.content)
        context = json.loads(request_body["messages"][1]["content"])
        reply = {"changes": [{"path": context["path"], "before": context["source"], "after": _source()}],
                 "adopted_asset_ids": [x["asset_id"] for x in context["experience"]]}
        return httpx.Response(200, json={"id": "offline-fixture-only", "model": MODEL,
            "choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": json.dumps(reply)}}],
            "usage": {"prompt_tokens": 200, "completion_tokens": 300, "total_tokens": 500}})
    return DashScopeCodeExecutor(config, transport=httpx.MockTransport(respond), provenance="mock")


def child(spec_path: Path) -> int:
    from swarm.worker_loop import Worker, WorkerConfig
    from swarm.code_executor import DashScopeCodeConfig, DashScopeCodeExecutor
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    result_file = spec_path.with_suffix(".result.json")
    try:
        installed = identity()
        config = WorkerConfig.model_validate_json(json.dumps(spec["worker"]))
        settings = DashScopeCodeConfig.model_validate(spec["executor"])
        executor = mock_executor(settings) if spec["mode"] == "offline" else DashScopeCodeExecutor(settings)
        started = time.time()
        worker = Worker(config, executor)
        if spec.get("fault_stage"):
            from live_faults import install_hooks
            install_hooks(worker, executor, spec["fault_stage"], spec_path.with_suffix(".held.json"))
        status = worker.run()
        write(result_file, {"pid": os.getpid(), "started": started, "finished": time.time(),
                            "mode": spec["mode"], "identity": installed, "status": status})
        return 0
    except BaseException:
        write(result_file, {"pid": os.getpid(), "mode": spec["mode"], "exception": traceback.format_exc()})
        return 1


def creation_time(process: subprocess.Popen[bytes]) -> float | None:
    if sys.platform != "win32":
        return None
    from ctypes import wintypes
    times = [wintypes.FILETIME() for _ in range(4)]
    call = ctypes.windll.kernel32.GetProcessTimes
    call.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    call.restype = wintypes.BOOL
    if not call(int(getattr(process, "_handle")), *(ctypes.byref(t) for t in times)):
        raise ctypes.WinError()
    return ((times[0].dwHighDateTime << 32) | times[0].dwLowDateTime) / 10000000 - 11644473600


def start(spec_path: Path) -> tuple[subprocess.Popen[bytes], dict[str, Any]]:
    env = {k: v for k, v in os.environ.items() if k.upper() not in ("DASHSCOPE_API_KEY", "PYTHONPATH", "PYTHONHOME")}
    env.update({"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
                "PYTHONDONTWRITEBYTECODE": "1"})
    executable = sys.executable
    if sys.platform == "win32" and sys.prefix != sys.base_prefix:
        executable = str(getattr(sys, "_base_executable"))
        env["__PYVENV_LAUNCHER__"] = sys.executable
    command = [executable, str(Path(__file__).resolve()), "--child", str(spec_path)]
    with spec_path.with_suffix(".stdout.log").open("wb") as out, spec_path.with_suffix(".stderr.log").open("wb") as err:
        process = subprocess.Popen(command, env=env, cwd=spec_path.parent, stdout=out, stderr=err)
    fact = {"pid": process.pid, "create_time": creation_time(process), "command": command,
            "spec": str(spec_path), "started": time.time()}
    return process, fact


def budget(cap: int) -> Any:
    from swarm.models import BudgetPolicy, ModelPrices, RunLimits
    return BudgetPolicy(max_cost_usd=cap * 0.1 / 6, max_tokens=cap * (16384 + 2048),
        burn_rate_tokens=cap * (16384 + 2048), burn_window_seconds=1.0,
        unbounded_reservation_usd=0.1 / 6,
        limits=RunLimits(max_tasks=cap, max_attempts=cap, max_attempts_per_task=1,
                         max_derived_tasks=0, max_runtime_seconds=600.0),
        prices=ModelPrices(provider="dashscope", model=MODEL,
                           input_usd_per_million=0.8 / 6, output_usd_per_million=2.0 / 6))


def config_for(target: Path, state: Path, cell: dict[str, Any], worker_index: int, cap: int, workers: int) -> Any:
    from contracts.identity import AgentId
    from swarm.models import Locality
    from swarm.worker_loop import WorkerConfig
    successor = cell["system"] == "successor_claim_v01"
    legacy = cell["system"] == "legacy_cycle_v0"
    return WorkerConfig(state=state, target=target, swarm_id=cell["id"],
        agent=AgentId(role="builder", instance=worker_index),
        locality=Locality(workspace=str(target), authorized_scopes=(".",), modules=("clamp", "mean", "unique")),
        capabilities={"clamp": 1.0, "mean": 1.0, "unique": 1.0}, budget=budget(cap),
        energy=64 if cell["category"] == "dynamic" else cap // workers + (worker_index < cap % workers),
        energy_policy="cycle" if legacy else "claim", routing_strategy="v0.1" if successor else "v0",
        max_senses=128, max_idle=64 if cell["category"] == "dynamic" else 2,
        stop_when_local_terminal=cell["category"] != "dynamic",
        idle_seconds=15.0 if cell["category"] == "dynamic" else 0.1,
        sleep_seconds=0.1, lease_seconds=180.0, validation_seconds=20.0,
        seed=cell["seed"] * 1000 + worker_index, continue_on_rejection=True)


def setup(root: Path, cell: dict[str, Any], names: list[str], workers: int, mode: str) -> tuple[Path, Path, Any]:
    from local_assets.paths import git
    from swarm.code_executor import DashScopeCodeConfig, DashScopeCodeExecutor
    from swarm.worker_loop import Worker
    root.mkdir(parents=True, exist_ok=False)
    target, state = root / "target", root / "state"
    target.mkdir()
    for index, name in enumerate(names):
        folder = target / f"t{index:02d}"
        folder.mkdir()
        (folder / "sample.py").write_bytes(BY_NAME[name].source.encode("utf-8"))
    git(target, "init", "-b", "benchmark")
    git(target, "-c", "core.autocrlf=false", "add", ".")
    git(target, "-c", "user.name=MorphBench", "-c", "user.email=local@localhost", "commit", "-m", "buggy seeds")
    cap = int(cell.get("ledger_cap", len(names)))
    first_config = config_for(target, state, cell, 0, cap, workers)
    if cell.get("fault_stage") == "before_reserve":
        policy = first_config.budget.model_copy(update={"limits": first_config.budget.limits.model_copy(
            update={"max_attempts": 2, "max_attempts_per_task": 2})})
        first_config = first_config.model_copy(update={"budget": policy})
    # Initializes the existing stores only; parent never executes requests.
    executor = mock_executor(DashScopeCodeConfig()) if mode == "offline" else DashScopeCodeExecutor(DashScopeCodeConfig())
    worker = Worker(first_config, executor)
    return target, state, worker


def enqueue(worker: Any, name: str, index: int, phase: int, log: Path) -> None:
    from local_assets.models import SampleValidationPolicy
    from swarm.models import Signal
    path = f"t{index:02d}/sample.py"
    family = "clamp" if BY_NAME[name].family == "composite" else BY_NAME[name].family
    signal = Signal(task_id=f"t{index:02d}-{name}", signal_id=f"t{index:02d}-{name}",
        workspace=str(worker.target), scope=f"t{index:02d}", module=family,
        kind="error_pattern", required_capability=family,
        payload={"instruction": PUBLIC_SPEC, "output_path": path, "phase": str(phase)})
    policy = SampleValidationPolicy(version="sample-tests-v1", path=path)
    worker.ledger.enqueue(signal, acceptance={"validation_policy": policy.model_dump(mode="json")})
    worker.field.deposit(signal)
    append(log, {"event": "arrival", "time": time.time(), "phase": phase,
                 "task_id": signal.task_id, "defect": name})


def observe(root: Path, cell: dict[str, Any], worker: Any,
            processes: list[tuple[subprocess.Popen[bytes], dict[str, Any]]], started: float, mode: str) -> dict[str, Any]:
    records = worker.ledger.snapshot(limit=1000)
    responses = []
    for path in sorted(worker.state.rglob("response.json")):
        response = json.loads(path.read_text(encoding="utf-8"))
        request = json.loads(path.with_name("request.json").read_text(encoding="utf-8"))
        responses.append({"path": str(path), "task_id": request.get("attempt", {}).get("task_id"), **response})
    uncertain = any(unknown_effect(r) for r in responses)
    snapshot = worker.budget.snapshot().model_dump(mode="json")
    unreconciled = snapshot["uncertain_reservations"] > 0 or snapshot["pending_reservations"] > 0
    uncertain = uncertain or snapshot["pending_reservations"] > 0
    statuses = []
    for process, fact in processes:
        fact["exit_code"] = process.poll()
        path = Path(fact["spec"]).with_suffix(".result.json")
        statuses.append(json.loads(path.read_text()) if path.exists() else {"missing": str(path)})
    result = {"cell": cell, "mode": mode, "layer": "live_worker_trial_not_a_pass" if mode == "live" else "contract_mock_http",
              "started": started, "finished": time.time(), "elapsed_seconds": time.time() - started,
              "processes": [fact for _, fact in processes], "worker_results": statuses,
              "worker_status_snapshots": [json.loads(p.read_text(encoding="utf-8"))
                  for p in sorted((worker.state / "workers").glob("*.json"))],
              "ledger": [r.model_dump(mode="json") for r in records], "budget": snapshot,
              "ledger_audit": worker.ledger.audit(limit=10000),
              "status_counts": dict(Counter(r.status for r in records)),
              "solved": sum(r.status == "completed" and r.effect_applied for r in records),
              "expected_tasks": cell["request_cap"], "responses": responses,
              "local_request_intents": len(list(worker.state.rglob("request.json"))),
              "stop_paid": uncertain or unreconciled or any(isinstance(r.get("http_status"), int) and r["http_status"] >= 400 for r in responses)
              or any(fact.get("killed_at_deadline") for _, fact in processes),
              "unknown_effect": uncertain, "unreconciled_budget": unreconciled, "actual_bill_cny": None,
              "estimated_cost_cny": None if snapshot["estimated_cost_usd"] is None else snapshot["estimated_cost_usd"] * 6,
              "accounting_cny_per_usd": 6, "identity": identity()}
    write(root / "result.json", result)
    return result


def run_cell(root: Path, cell: dict[str, Any], mode: str) -> dict[str, Any]:
    from swarm.code_executor import DashScopeCodeConfig
    dynamic = cell["category"] == "dynamic"
    names = [name for phase in PHASES for name in phase] if dynamic else [c.name for c in DEFECTS]
    if "names" in cell:
        names = cell["names"]
    workers = 3 if cell["system"] in ("legacy_cycle_v0", "successor_claim_v01") else 1
    started = time.time()
    target, state, observer = setup(root, cell, names, workers, mode)
    write(root / "cell.json", cell)
    arrival_epoch = time.time()
    write(root / "arrival-clock.json", {"epoch": arrival_epoch, "wall_started": started})
    phases = [names[i:i + 4] for i in range(0, len(names), 4)] if dynamic else [names]
    processes = []
    offset = 0
    for phase, group in enumerate(phases):
        if phase:
            deadline = arrival_epoch + [0, 45, 90][phase]
            while time.time() < deadline:
                time.sleep(min(0.2, deadline - time.time()))
        for name in group:
            enqueue(observer, name, offset, phase, root / "events.jsonl")
            offset += 1
        if phase == 0:
            for index in range(workers):
                config = config_for(target, state, cell, index, len(names), workers)
                profiles = ({str(p): PROFILES[PROFILE_ORDER[p][index]] for p in range(3)}
                            if dynamic and workers == 3 else {})
                spec = root / f"worker-{index}.json"
                write(spec, {"worker": config.model_dump(mode="json"), "mode": mode,
                             "executor": DashScopeCodeConfig(phase_profiles=profiles).model_dump(mode="json")})
                processes.append(start(spec))
    while dynamic and any(process.poll() is None for process, _ in processes):
        records = observer.ledger.snapshot(limit=1000)
        pending = observer.budget.snapshot().pending_reservations
        # All arrivals are now visible. This is a quiescent benchmark stop, not
        # a crash-recovery result: no lease/HTTP request may still be active.
        if (len(records) == len(names) and pending == 0 and not observer.ledger.leases()
                and workers_quiescent(processes, state)
                and all(r.status in ("completed", "failed", "blocked") or r.attempts >= 1 for r in records)):
            for process, fact in processes:
                if process.poll() is None:
                    fact["stopped_after_all_attempts_quiescent"] = True
                    process.kill()
                    process.wait(timeout=15)
            break
        if time.time() - started >= 600:
            break
        time.sleep(0.2)
    for process, fact in processes:
        try:
            process.wait(timeout=max(1, 600 - (time.time() - started)))
        except subprocess.TimeoutExpired:
            # Stop only our own handle; no retry of an unknown in-flight request.
            process.kill()
            process.wait(timeout=15)
            fact["killed_at_deadline"] = True
    return observe(root, cell, observer, processes, started, mode)


def run_single(root: Path, cell: dict[str, Any], mode: str) -> dict[str, Any]:
    from contracts.identity import AgentId
    from swarm.code_executor import DashScopeCodeConfig
    dynamic = cell["category"] == "dynamic"
    names = [n for p in PHASES for n in p] if dynamic else [c.name for c in DEFECTS]
    started = time.time()
    target, state, observer = setup(root, cell, names, 1, mode)
    write(root / "cell.json", cell)
    arrival_epoch = time.time()
    write(root / "arrival-clock.json", {"epoch": arrival_epoch, "wall_started": started})
    processes: list[tuple[subprocess.Popen[bytes], dict[str, Any]]] = []
    phase, offset = 0, 0
    groups = [list(p) for p in PHASES] if dynamic else [names]
    current: subprocess.Popen[bytes] | None = None
    while time.time() - started < 600:
        if phase < len(groups) and time.time() >= arrival_epoch + (45 * phase if dynamic else 0):
            for name in groups[phase]:
                enqueue(observer, name, offset, phase, root / "events.jsonl")
                offset += 1
            phase += 1
        if current is not None and current.poll() is not None:
            state_budget = observer.budget.snapshot()
            if (current.returncode or state_budget.pending_reservations or state_budget.uncertain_reservations
                    or provider_stop(state)):
                break
            current = None
        records = observer.ledger.snapshot(limit=1000)
        ready = any(r.status == "available" and r.attempts < 1 for r in records)
        if current is None and ready and len(processes) < len(names):
            index = len(processes)
            config = config_for(target, state, cell, 0, len(names), 1).model_copy(update={
                "agent": AgentId(role="builder", instance=index), "energy": 1,
                "seed": cell["seed"] * 1000 + index, "stop_when_local_terminal": True})
            spec = root / f"worker-{index}.json"
            write(spec, {"worker": config.model_dump(mode="json"), "mode": mode,
                         "executor": DashScopeCodeConfig().model_dump(mode="json")})
            spawned = start(spec)
            processes.append(spawned)
            current = spawned[0]
        if current is None and phase == len(groups) and not ready:
            break
        if current is None and len(processes) >= len(names):
            break
        time.sleep(0.2)
    for process, fact in processes:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=15)
            fact["killed_at_deadline"] = True
    result = observe(root, cell, observer, processes, started, mode)
    result["single_mechanism"] = "one fresh Worker identity/process per acquired task; common task ledger, no declared reuse dependency"
    write(root / "result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--mode", choices=("offline", "live"), default="offline")
    parser.add_argument("--cell")
    args = parser.parse_args()
    if args.child:
        return child(args.child)
    if not args.out or not args.cell:
        parser.error("--out and --cell required")
    identity()
    cell = next((t for t in plan()["trials"] if t["id"] == args.cell), None)
    if cell is None or cell["category"] not in ("code", "dynamic"):
        parser.error("cell must be a registered code or dynamic trial")
    result = (run_single if cell["system"] == "single" else run_cell)(args.out.resolve(), cell, args.mode)
    print(json.dumps({"cell": args.cell, "mode": args.mode, "solved": result["solved"],
                      "expected": result["expected_tasks"], "stop_paid": result["stop_paid"]}))
    return 2 if result["stop_paid"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
