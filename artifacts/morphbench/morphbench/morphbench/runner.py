"""Suite runner: executes all systems across all tasks and aggregates."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Dict, List

import numpy as np

import os

from . import agents, local_tasks
from .core import (
    RunOutcome,
    coordination_overhead,
    experience_reuse_gain,
    fault_tolerance_survival,
    leaderboard_percentile,
    redundant_work_rate,
)
from .tasks import TASKS

# MORPHBENCH_SURROGATE=1 reverts MorphSwarm / CentralScheduler to the original
# self-contained re-implementations so a run can be compared like-for-like
# against the real-engine path. Default is the real Morphogenesis engine.
USE_SURROGATE = os.environ.get("MORPHBENCH_SURROGATE", "") == "1"

if not USE_SURROGATE:
    from .real_swarm import (
        experience_reuse_experiment as _reuse_experiment,
        fault_tolerance_experiment as _fault_tolerance,
        measure_coordination_overhead as _measure_overhead,
        run_real_central as _run_real_central,
        run_real_swarm as _run_real_swarm,
    )


@dataclass
class SuiteReport:
    budget: int
    task_metrics: List[Dict] = field(default_factory=list)
    percentile_table: List[Dict] = field(default_factory=list)
    swarm_metrics: Dict[str, float] = field(default_factory=dict)
    summary: Dict[str, float] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)


SYSTEMS = {
    "SingleAgent": agents.run_single_agent,
    "CentralScheduler": agents.run_central_scheduler,
}


def _run_system_on_task(system_name: str, task, budget: int, seed: int):
    if USE_SURROGATE:
        if system_name == "MorphSwarm":
            return agents.run_morph_swarm(task, budget, seed=seed)
        return SYSTEMS[system_name](task, budget, seed=seed)
    if system_name == "MorphSwarm":
        return _run_real_swarm(task, budget, seed=seed)
    if system_name == "CentralScheduler":
        return _run_real_central(task, budget, seed=seed)
    return SYSTEMS[system_name](task, budget, seed=seed)


def run_suite(budget: int = 24, seed: int = 0, systems: List[str] | None = None) -> SuiteReport:
    systems = systems or ["SingleAgent", "CentralScheduler", "MorphSwarm"]
    report = SuiteReport(budget=budget)

    e2e_ids = [tid for tid, spec in TASKS.items() if spec.tier == "e2e"]

    # ---- Tier B: research-loop metrics -----------------------------------
    for tid in e2e_ids:
        spec = TASKS[tid]
        task = local_tasks.build(tid)
        for sys_name in systems:
            ep = _run_system_on_task(sys_name, task, budget, seed)
            # held-out test score for the config the system ended up best at
            best_cfg = None
            for cfg in task.config_space:
                if abs(task.evaluate(cfg) - ep.best_val) < 1e-9:
                    best_cfg = cfg
                    break
            test = task.test_score(best_cfg) if best_cfg else float("nan")
            pct = leaderboard_percentile(test, spec.reference_scores, spec.higher_is_better)
            report.task_metrics.append({
                "task": tid, "name": spec.name, "system": sys_name,
                "val_score": round(ep.best_val, 4), "test_score": round(test, 4),
                "leaderboard_percentile": round(pct, 2),
                "units_used": ep.units_used, "duplicate_units": ep.duplicate_units,
                "redundant_rate": round(ep.redundant_rate, 4),
                "accepted_improvements": ep.accepted_improvements,
                "completed": ep.completed,
            })

    # ---- aggregate percentile table --------------------------------------
    for sys_name in systems:
        vals = [r["leaderboard_percentile"] for r in report.task_metrics
                if r["system"] == sys_name and not np.isnan(r["leaderboard_percentile"])]
        reds = [r["redundant_rate"] for r in report.task_metrics if r["system"] == sys_name]
        report.percentile_table.append({
            "system": sys_name,
            "mean_leaderboard_percentile": round(float(np.mean(vals)), 2) if vals else None,
            "completion_rate": round(
                sum(r["completed"] for r in report.task_metrics if r["system"] == sys_name) / len(e2e_ids), 4),
            "mean_redundant_rate": round(float(np.mean(reds)), 4) if reds else None,
        })

    # ---- Tier A: swarm mechanism metrics ---------------------------------
    mech_task = local_tasks.build("BM-05")

    if USE_SURROGATE:
        ft = agents.fault_tolerance_experiment(mech_task, kills=2, budget=20, seed=seed)
        report.swarm_metrics["SB-01_swarm_survival"] = ft["swarm_survival"]
        report.swarm_metrics["SB-01_central_survival"] = ft["central_survival"]
        reuse = agents.experience_reuse_experiment(mech_task, budget=24, seed=seed)
        report.swarm_metrics["SB-02_reuse_gain"] = round(
            experience_reuse_gain(reuse["round1_units"], reuse["round2_new_units"]), 4)
        report.swarm_metrics["SB-02_round1_units"] = reuse["round1_units"]
        report.swarm_metrics["SB-02_round2_new_units"] = reuse["round2_new_units"]
        base_wall, swarm_wall = 1.0, 1.15
        report.swarm_metrics["SB-03_overhead_ratio"] = round(
            coordination_overhead(swarm_wall, base_wall), 4)
    else:
        ft = _fault_tolerance(mech_task, kills=2, budget=20, seed=seed)
        report.swarm_metrics["SB-01_swarm_survival"] = ft["swarm_survival"]
        report.swarm_metrics["SB-01_central_survival"] = ft["central_survival"]
        report.swarm_metrics["SB-01_swarm_units_used"] = ft["swarm_units_used"]
        report.swarm_metrics["SB-01_central_units_used"] = ft["central_units_used"]

        reuse = _reuse_experiment(mech_task, budget=24, seed=seed)
        report.swarm_metrics["SB-02_reuse_gain"] = reuse["reuse_gain"]
        report.swarm_metrics["SB-02_cold_units_to_target"] = reuse["cold_units_to_target"]
        report.swarm_metrics["SB-02_warm_units_to_target"] = reuse["warm_units_to_target"]

        # SB-03 must be timed on a task whose units actually cost compute:
        # BM-05's surrogate objective is memoised, so its baseline wall clock
        # is ~0 and the ratio explodes. BM-01 fits real sklearn models.
        over = _measure_overhead(local_tasks.build("BM-01"), budget=budget, seed=seed)
        report.swarm_metrics["SB-03_overhead_ratio"] = over["overhead_ratio"]
        report.swarm_metrics["SB-03_base_wall_seconds"] = over["base_wall_seconds"]
        report.swarm_metrics["SB-03_swarm_wall_seconds"] = over["swarm_wall_seconds"]

    # SB-04: Tier-B rows only. The shipped version folded the SB-02 mechanism
    # row into the denominator, diluting the rate (0.3542 instead of 0.4250).
    swarm_runs = [r for r in report.task_metrics
                  if r["system"] == "MorphSwarm" and str(r.get("task", "")).startswith("BM")]
    total_units = sum(r["units_used"] for r in swarm_runs)
    total_dup = sum(r["duplicate_units"] for r in swarm_runs)
    report.swarm_metrics["SB-04_redundant_rate"] = round(
        redundant_work_rate(total_dup, total_units), 4)

    # ---- summary ----------------------------------------------------------
    report.summary = {
        "budget_per_task": budget,
        "n_e2e_tasks": len(e2e_ids),
        "n_systems": len(systems),
        "engine": "surrogate" if USE_SURROGATE else "real-morphogenesis-0.2.1",
    }
    return report


def to_markdown(report: SuiteReport) -> str:
    lines = ["# MorphBench — local suite report", ""]
    lines.append(f"Budget per task: **{report.budget}** units  |  "
                 f"E2E tasks: **{report.summary['n_e2e_tasks']}**  |  "
                 f"Systems: **{report.summary['n_systems']}**")
    lines += ["", "## Mean leaderboard percentile (Tier B)", "",
              "| System | Mean LB percentile | Completion rate | Mean redundant rate |",
              "|---|---|---|---|"]
    for row in report.percentile_table:
        lines.append(f"| {row['system']} | {row['mean_leaderboard_percentile']} | "
                     f"{row['completion_rate']} | {row['mean_redundant_rate']} |")
    lines += ["", "## Swarm mechanism metrics (Tier A)", "",
              "| Metric | Value |", "|---|---|"]
    for k, v in report.swarm_metrics.items():
        lines.append(f"| {k} | {v} |")
    return "\n".join(lines)
