"""Measure an operator-supplied local suite against an installed Morphogenesis.

The suite is intentionally not vendored: its redistribution license is unknown.
This observer reuses its tasks/executor and the installed product's Worker.run.
It is a benchmark driver, not a task scheduler. See README.md for interpretation.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import importlib.metadata
import json
import multiprocessing
import os
from pathlib import Path
import sys
import time
import traceback

SOURCE = "50396909c3fbaa510e755b8e2361e05d84afdfaa"


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")


def event(path: Path, value) -> None:
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, allow_nan=False) + "\n")
        stream.flush()


def read_events(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def configure(suite: str) -> None:
    # Set before NumPy/sklearn imports, also inherited by spawned workers.
    for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[name] = "1"
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(Path(suite).resolve()))


def installed_identity() -> dict:
    import swarm.worker_loop
    import local_assets.validate
    modules = {module.__name__: str(Path(module.__file__).resolve())
               for module in (swarm.worker_loop, local_assets.validate)}
    installed_root = Path(sys.prefix).resolve() / "Lib" / "site-packages"
    if not all(Path(p).is_relative_to(installed_root) for p in modules.values()):
        raise RuntimeError(f"product_import_not_from_installed_environment: {modules}")
    dist = importlib.metadata.distribution("morphogenesis")
    direct = json.loads(dist.read_text("direct_url.json") or "{}")
    if dist.version != "0.2.1" or direct.get("dir_info", {}).get("editable", False):
        raise RuntimeError("expected_noneditable_morphogenesis_0.2.1")
    return {"python": sys.version, "executable": sys.executable, "cwd": str(Path.cwd()),
            "product_version": dist.version, "direct_url": direct, "modules": modules,
            "requested_source": SOURCE, "source_byte_verification": "independent Q evidence required"}


def split_energy(budget: int, workers: int) -> list[int]:
    if not 1 <= workers <= budget:
        raise ValueError("require 1 <= workers <= budget")
    return [budget // workers + (i < budget % workers) for i in range(workers)]


def measured_task(task, log: Path, phase: str):
    from morphbench.local_tasks import LocalTask
    def evaluate(cfg):
        index = task.config_space.index(cfg)
        event(log, {"event": "evaluation_started", "phase": phase, "index": index})
        started = time.perf_counter()
        score = float(task.evaluate(cfg))
        event(log, {"event": "evaluation_finished", "phase": phase, "index": index,
                    "score": score, "seconds": time.perf_counter() - started})
        return score
    return LocalTask(task.task_id, task.config_space, evaluate, task.test_score, task.higher_is_better)


def worker_process(suite: str, config_json: str, state: str, log: str, result_file: str) -> None:
    configure(suite)
    from morphbench.worker_engine import MorphBenchExecutor, EXECUTOR_SPEC
    from swarm.worker_loop import Worker, WorkerConfig
    from morphbench import local_tasks
    spec = json.loads((Path(state) / EXECUTOR_SPEC).read_text(encoding="utf-8"))
    executor = MorphBenchExecutor(spec["task_id"], spec["space"])
    executor._task = measured_task(local_tasks.build(spec["task_id"]), Path(log), "search")
    try:
        identity = installed_identity()
        status = Worker(WorkerConfig.model_validate_json(config_json), executor).run()
        write_json(Path(result_file), {"identity": identity, "status": status})
    except BaseException:
        write_json(Path(result_file), {"exception": traceback.format_exc()})
        raise


def run_workers(task_id: str, seed: int, budget: int, workers: int, root: Path, suite: str) -> dict:
    from morphbench import worker_engine as engine
    from swarm.models import RunLimits
    from swarm.task_ledger import TaskLedger
    from swarm.worker_loop import WorkerConfig
    energies = split_energy(budget, workers)
    sid = f"{task_id}-s{seed}"
    limits = RunLimits(max_attempts=budget)
    original_build, original_ledger = engine.local_tasks.build, engine.TaskLedger
    setup_start = time.perf_counter()
    try:
        engine.local_tasks.build = lambda tid: measured_task(original_build(tid), root / "setup.jsonl", "acceptance_prefit")
        engine.TaskLedger = lambda path, swarm_id: TaskLedger(path, swarm_id, limits=limits)
        target, state = engine.seed_workspace(root, task_id, sid)
    finally:
        engine.local_tasks.build, engine.TaskLedger = original_build, original_ledger
    setup_seconds = time.perf_counter() - setup_start
    task = original_build(task_id)
    capabilities = {engine._family(cfg): 1.0 for cfg in task.config_space}
    configs = []
    for i, energy in enumerate(energies):
        data = json.loads(engine.worker_config(target, state, i, sid, capabilities, energy))
        data["seed"] = seed * 1000 + i
        data["budget"]["limits"] = limits.model_dump(mode="json")
        config = WorkerConfig.model_validate_json(json.dumps(data))
        configs.append(config.model_dump_json())
        write_json(root / f"worker-{i}-config.json", config.model_dump(mode="json"))
    context = multiprocessing.get_context("spawn")
    processes = [context.Process(target=worker_process, args=(suite, config, str(state),
                 str(root / f"worker-{i}.jsonl"), str(root / f"worker-{i}-result.json")))
                 for i, config in enumerate(configs)]
    start = time.perf_counter()
    for process in processes:
        process.start()
    timed_out = []
    for i, process in enumerate(processes):
        process.join(max(0.0, 600 - (time.perf_counter() - start)))
        if process.is_alive():
            timed_out.append(i)
            process.kill()
            process.join()
    wall = time.perf_counter() - start
    records = TaskLedger(state / "tasks.sqlite3", sid, limits=limits).snapshot(limit=1000)
    write_json(root / "ledger-snapshot.json", [r.model_dump(mode="json") for r in records])
    events = [row for i in range(workers) for row in read_events(root / f"worker-{i}.jsonl")]
    completed = [r for r in records if r.status == "completed"]
    # Read the actual applied score files, not the precomputed oracle scores.
    candidates = []
    for record in completed:
        file = target / engine.scoped_result_path(record.signal.task_id)
        candidates.append(json.loads(file.read_text(encoding="utf-8")))
    best = max(candidates, key=lambda row: row["score"], default=None)
    finished = [e for e in events if e["event"] == "evaluation_finished"]
    for candidate in candidates:
        if not any(e["index"] == candidate["index"] and round(e["score"], 6) == candidate["score"] for e in finished):
            raise RuntimeError("completed_candidate_not_bound_to_observed_evaluation")
    statuses = [json.loads((root / f"worker-{i}-result.json").read_text(encoding="utf-8"))
                if (root / f"worker-{i}-result.json").exists() else {"status": "missing"} for i in range(workers)]
    return {"events": events, "best": best, "search_wall_seconds": wall, "setup_seconds": setup_seconds,
            "setup_evaluations": sum(e["event"] == "evaluation_finished" for e in read_events(root / "setup.jsonl")),
            "tasks_completed": len(completed), "task_status_counts": dict(Counter(r.status for r in records)),
            "ledger_attempts": sum(r.attempts for r in records), "worker_energies": energies,
            "worker_seeds": [seed * 1000 + i for i in range(workers)], "timed_out_workers": timed_out,
            "exit_codes": [p.exitcode for p in processes], "worker_results": statuses,
            "layer": "installed_Worker.run_with_fixture_mock_executor_usage"}


def run_baseline(task_id: str, system: str, seed: int, budget: int, root: Path) -> dict:
    from morphbench import agents, local_tasks, real_swarm
    task = measured_task(local_tasks.build(task_id), root / "search.jsonl", "search")
    function = agents.run_single_agent if system == "SingleAgent" else real_swarm.run_real_central
    start = time.perf_counter()
    function(task, budget, seed=seed)
    wall = time.perf_counter() - start
    events = read_events(root / "search.jsonl")
    finished = [e for e in events if e["event"] == "evaluation_finished"]
    return {"events": events, "best": max(finished, key=lambda e: e["score"], default=None),
            "search_wall_seconds": wall, "setup_seconds": 0.0, "setup_evaluations": 0,
            "tasks_completed": len(finished), "layer": "local_serial_allocation_baseline"}


def run_trial(args, task_id: str, seed: int, system: str, root: Path) -> dict:
    from morphbench import local_tasks
    root.mkdir(parents=True, exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    start = time.perf_counter()
    if system == "MorphSwarm":
        result = run_workers(task_id, seed, args.budget, args.workers, root, args.suite)
    else:
        result = run_baseline(task_id, system, seed, args.budget, root)
    events = result.pop("events")
    finished = [e for e in events if e["event"] == "evaluation_finished"]
    executed = sum(e["event"] == "evaluation_started" for e in events)
    best = result.pop("best")
    test_score, test_seconds = None, 0.0
    if best is not None:
        task = local_tasks.build(task_id)
        test_start = time.perf_counter()
        test_score = float(task.test_score(task.config_space[best["index"]]))
        test_seconds = time.perf_counter() - test_start
    duplicate = len(finished) - len({e["index"] for e in finished})
    result.update({"task": task_id, "seed": seed, "system": system, "budget": args.budget,
                   "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(),
                   "elapsed_seconds": time.perf_counter() - start, "executions_started": executed,
                   "evaluations_finished": len(finished), "duplicate_evaluations": duplicate,
                   "redundant_rate": duplicate / len(finished) if finished else None,
                   "best_index": best["index"] if best else None, "best_val": best["score"] if best else None,
                   "test_score": test_score, "test_evaluations": int(best is not None), "test_seconds": test_seconds,
                   "search_indices": [e["index"] for e in finished], "search_evaluation_seconds": sum(e["seconds"] for e in finished),
                   "total_evaluation_calls": result["setup_evaluations"] + executed + int(best is not None),
                   "measurement_window": args.measurement_window, "actual_cost_usd": None,
                   "usage_source": "fixture_mock" if system == "MorphSwarm" else "no_provider_usage",
                   "data": "fixed_synthetic_data" if task_id != "BM-05" else "cached_mathematical_objective_no_training",
                   "official_leaderboard_score": None})
    if executed > args.budget:
        result["status"] = "FAIL_budget_exceeded"
    elif result.get("timed_out_workers") or any(code != 0 for code in result.get("exit_codes", [])):
        result["status"] = "FAIL_worker_process"
    elif result["tasks_completed"] != args.budget or len(finished) != args.budget:
        result["status"] = "INCOMPLETE_budget_not_completed"
    else:
        result["status"] = "PASS_local_trial"
    write_json(root / "result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tasks", nargs="+", default=[f"BM-0{i}" for i in range(1, 6)])
    parser.add_argument("--seeds", nargs="+", type=int, default=list(range(5)))
    parser.add_argument("--systems", nargs="+", choices=["SingleAgent", "CentralScheduler", "MorphSwarm"],
                        default=["SingleAgent", "CentralScheduler", "MorphSwarm"])
    parser.add_argument("--budget", type=int, default=8)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--measurement-window", default="uncontrolled_descriptive_only")
    args = parser.parse_args()
    configure(args.suite)
    args.output.mkdir(parents=True, exist_ok=False)
    write_json(args.output / "environment.json", installed_identity())
    write_json(args.output / "arguments.json", {**vars(args), "output": str(args.output)})
    failed = False
    for task in args.tasks:
        for seed in args.seeds:
            # Alternate system order to reduce the fixed-order timing bias.
            systems = args.systems if seed % 2 == 0 else list(reversed(args.systems))
            for system in systems:
                trial = args.output / f"{task}-s{seed}-{system}"
                try:
                    result = run_trial(args, task, seed, system, trial)
                except Exception:
                    trial.mkdir(parents=True, exist_ok=True)
                    write_json(trial / "failure.json", {"exception": traceback.format_exc()})
                    traceback.print_exc()
                    return 1  # Preserve first failure; never automatically retry an unknown execution.
                print(json.dumps({key: result[key] for key in ("task", "seed", "system", "status", "test_score", "elapsed_seconds", "total_evaluation_calls")}), flush=True)
                failed |= result["status"] != "PASS_local_trial"
    return int(failed)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    raise SystemExit(main())
