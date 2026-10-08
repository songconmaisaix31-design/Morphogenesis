"""Local SB observations, with adapter-only boundaries and signed/censored reuse."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from importlib import import_module
import json
from pathlib import Path
import time
from typing import Any

from run_local import configure, installed_identity, measured_task, read_events, write_json
from summarize import estimate


def run(args: argparse.Namespace) -> dict[str, Any]:
    local_tasks, real_swarm = (import_module("morphbench." + name) for name in ("local_tasks", "real_swarm"))
    output = args.output
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "environment.json", installed_identity())
    report: dict[str, Any] = {"SB-01": [], "SB-02": [], "SB-03": [], "SB-04": [],
              "measurement_window": args.measurement_window}
    for seed in range(5):
        task = local_tasks.build("BM-05")
        root = output / f"s{seed}"
        root.mkdir()
        def adapter(label: str, current_task: Any, **kwargs: Any) -> Any:
            log = root / f"{label}.jsonl"
            observed = measured_task(current_task, log, label)
            stats = real_swarm.run_real_swarm(observed, args.budget, seed=seed,
                         root=root / label, persist=True, **kwargs)
            write_json(root / f"{label}.json", asdict(stats))
            return stats
        # This deliberately reproduces only the suite's adapter experiment.
        # It cannot establish real process loss; Q owns the separate kill evidence.
        alive = adapter("sb01-alive-list", task, workers=4, kills=2)
        central = real_swarm.run_real_central(measured_task(task, root / "sb01-central.jsonl", "sb01-central"),
                                             args.budget, seed=seed, kills=2)
        report["SB-01"].append({"seed": seed, "layer": "contract_local_adapter_only",
            "swarm_units": alive.units_used, "central_units": central.units_used,
            "swarm_completed_flag": alive.completed, "central_completed_flag": central.completed,
            "real_process_kills": 0, "real_fault_survival": None,
            "limitation": "alive-list removal / planner boolean; independent Q evidence required"})
        shifted = real_swarm._shifted_task(task, seed + 7919)
        ref = adapter("sb02-reference", shifted)
        train = adapter("sb02-train", task)
        cold = adapter("sb02-cold", shifted, target=ref.best_val)
        warm = adapter("sb02-warm", shifted, target=ref.best_val,
                       reuse_field_from=root / "sb02-train" / real_swarm.FIELD_NAME)
        cold_units, warm_units = cold.units_to_target, warm.units_to_target
        gain = (cold_units - warm_units) / cold_units if cold_units and warm_units is not None else None
        report["SB-02"].append({"seed": seed, "layer": "contract_local_adapter_field_transfer",
            "target": ref.best_val, "cold_units_to_target": cold_units, "warm_units_to_target": warm_units,
            "cold_censored": cold_units is None, "warm_censored": warm_units is None,
            "signed_gain": gain, "actual_evaluations": ref.units_used + train.units_used + cold.units_used + warm.units_used,
            "limitation": "fixed additive perturbed objective; same-data target selected by cold reference; no Worker research metabolism"})
        # Replay exactly the config sequence this Worker actually evaluated.
        # Ratio includes process/Git/SDK/validation overhead and concurrency.
        trial_path = args.matrix / f"BM-01-s{seed}-MorphSwarm" / "result.json"
        if trial_path.exists():
            trial = json.loads(trial_path.read_text(encoding="utf-8"))
            base_task = measured_task(local_tasks.build("BM-01"), root / "sb03-baseline.jsonl", "same_config_replay")
            started = time.perf_counter()
            for index in trial["search_indices"]:
                base_task.evaluate(base_task.config_space[index])
            baseline_seconds = time.perf_counter() - started
            report["SB-03"].append({"seed": seed, "layer": "installed_Worker_observed_pipeline_wall",
                "worker_search_wall_seconds": trial["search_wall_seconds"], "sequential_same_config_seconds": baseline_seconds,
                "relative_pipeline_wall_increment": trial["search_wall_seconds"] / baseline_seconds - 1,
                "additional_baseline_evaluations": len(trial["search_indices"]),
                "worker_trial_status": trial["status"], "worker_measurement_window": trial["measurement_window"],
                "limitation": "not isolated coordination cost; spawn + Git + SDK + validation, parallel work, no acceptance prefit in numerator"})
    rows = [json.loads(path.read_text(encoding="utf-8")) for path in args.matrix.glob("BM-*/result.json")]
    for system in ("SingleAgent", "CentralScheduler", "MorphSwarm"):
        group = [r for r in rows if r["system"] == system]
        units = sum(r["evaluations_finished"] for r in group)
        duplicates = sum(r["duplicate_evaluations"] for r in group)
        report["SB-04"].append({"system": system, "executed_evaluations": units,
            "duplicate_evaluations": duplicates, "rate": duplicates / units if units else None,
            "definition": "repeat config within task/seed search; setup and held-out refits separately charged"})
    report["SB-02_signed_gain_summary_uncensored_only"] = estimate([r["signed_gain"] for r in report["SB-02"] if r["signed_gain"] is not None])
    report["SB-03_wall_increment_summary"] = estimate([r["relative_pipeline_wall_increment"] for r in report["SB-03"]])
    report["actual_evaluation_calls"] = sum(len([e for e in read_events(p) if e["event"] == "evaluation_started"])
                                            for p in output.glob("s*/*.jsonl"))
    write_json(output / "mechanisms.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", required=True)
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--budget", type=int, default=8)
    parser.add_argument("--measurement-window", default="uncontrolled_descriptive_only")
    args = parser.parse_args()
    configure(args.suite)
    report = run(args)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
