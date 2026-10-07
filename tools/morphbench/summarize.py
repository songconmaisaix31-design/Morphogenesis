"""Summarize local fixed-budget trials; never map synthetic scores to a leaderboard."""
from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path
import random
import statistics


def estimate(values: list[float]) -> dict:
    return {"n": len(values), "mean": statistics.mean(values) if values else None,
            "se": statistics.stdev(values) / math.sqrt(len(values)) if len(values) > 1 else None}


def paired(left: dict[int, float], right: dict[int, float], draws: int = 10000) -> dict:
    seeds = sorted(left.keys() & right.keys())
    differences = [left[s] - right[s] for s in seeds]
    if not differences:
        return {"seeds": [], **estimate([]), "ci95": None, "sign_flip_p": None}
    rng = random.Random(20261007)
    samples = sorted(statistics.mean(rng.choices(differences, k=len(differences))) for _ in range(draws))
    def quantile(fraction):
        index = (len(samples) - 1) * fraction
        lo, hi = math.floor(index), math.ceil(index)
        return samples[lo] + (samples[hi] - samples[lo]) * (index - lo)
    observed = abs(statistics.mean(differences))
    permutations = [abs(statistics.mean(d * sign for d, sign in zip(differences, signs)))
                    for signs in itertools.product((-1, 1), repeat=len(differences))]
    p_value = sum(value >= observed - 1e-14 for value in permutations) / len(permutations)
    return {"seeds": seeds, "differences": differences, **estimate(differences),
            "ci95": [quantile(0.025), quantile(0.975)], "sign_flip_p": p_value,
            "bootstrap_draws": draws, "bootstrap_seed": 20261007}


def bh_adjust(p_values: list[float]) -> list[float]:
    ordered = sorted(range(len(p_values)), key=lambda i: p_values[i])
    adjusted = [1.0] * len(p_values)
    running = 1.0
    for rank in range(len(ordered), 0, -1):
        index = ordered[rank - 1]
        running = min(running, p_values[index] * len(ordered) / rank)
        adjusted[index] = running
    return adjusted


def summarize(root: Path) -> dict:
    rows = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(root.glob("BM-*/result.json"))]
    argument_file = root / "arguments.json"
    arguments = json.loads(argument_file.read_text(encoding="utf-8")) if argument_file.exists() else {
        "tasks": [f"BM-0{i}" for i in range(1, 6)], "seeds": list(range(5)),
        "systems": ["SingleAgent", "CentralScheduler", "MorphSwarm"]}
    expected = list(itertools.product(arguments["tasks"], arguments["seeds"], arguments["systems"]))
    observed = {(r["task"], r["seed"], r["system"]) for r in rows}
    if len(observed) != len(rows):
        raise ValueError("duplicate task/seed/system result")
    missing = [{"task": task, "seed": seed, "system": system,
                "status": "FAIL_no_result" if (root / f"{task}-s{seed}-{system}" / "failure.json").exists() else "NOT_RUN"}
               for task, seed, system in expected if (task, seed, system) not in observed]
    groups, contrasts, allowance_contrasts = [], [], []
    for task in sorted({row["task"] for row in rows}):
        for system in ("SingleAgent", "CentralScheduler", "MorphSwarm"):
            group = [r for r in rows if r["task"] == task and r["system"] == system]
            good = [r for r in group if r["status"] == "PASS_local_trial"]
            groups.append({"task": task, "system": system, "trials": len(group), "complete_trials": len(good),
                           "test_score": estimate([r["test_score"] for r in good if r["test_score"] is not None]),
                           "observed_test_score_including_partial": estimate([r["test_score"] for r in group if r["test_score"] is not None]),
                           "search_wall_seconds": estimate([r["search_wall_seconds"] for r in group]),
                           "evaluations_finished": sum(r["evaluations_finished"] for r in group),
                           "duplicate_evaluations": sum(r["duplicate_evaluations"] for r in group),
                           "setup_evaluations": sum(r["setup_evaluations"] for r in group),
                           "test_evaluations": sum(r["test_evaluations"] for r in group)})
        for baseline in ("SingleAgent", "CentralScheduler"):
            def scores(system, complete_only=True):
                selected = [r for r in rows if r["task"] == task and r["system"] == system
                            and (not complete_only or r["status"] == "PASS_local_trial") and r["test_score"] is not None]
                if len({r["seed"] for r in selected}) != len(selected):
                    raise ValueError("duplicate seed in a task/system")
                return {r["seed"]: r["test_score"] for r in selected}
            contrasts.append({"task": task, "contrast": f"MorphSwarm minus {baseline}",
                              **paired(scores("MorphSwarm"), scores(baseline))})
            allowance_contrasts.append({"task": task, "contrast": f"MorphSwarm minus {baseline}",
                **paired(scores("MorphSwarm", False), scores(baseline, False)),
                "interpretation": "fixed search allowance; includes partial trials; not equal executed evaluations"})
    tested = [row for row in contrasts if row["sign_flip_p"] is not None]
    for row, q in zip(tested, bh_adjust([r["sign_flip_p"] for r in tested])):
        row["bh_q"] = q
    return {"groups": groups, "paired_contrasts": contrasts,
            "fixed_allowance_paired_contrasts": allowance_contrasts, "trials": rows,
            "coverage": {"expected": len(expected), "observed": len(rows), "missing_count": len(missing),
                         "missing": missing, "complete_budget_trials": sum(r["status"] == "PASS_local_trial" for r in rows)},
            "final_evaluation": "BM-01..04 held-out synthetic test; BM-05 same mathematical objective, no independent test set",
            "bootstrap_unit": "paired allocation seed; fixed synthetic data and fixed model seeds",
            "interpretation": "exploratory; complete-only comparisons can have selection bias; fixed-allowance contrasts retain observable partial endpoints; neither measures population/dataset uncertainty",
            "sequential_testing": "NOT_RUN; no sequential stopping rule preregistered",
            "fdr_family": "10 two-sided exact sign-flip contrasts; Benjamini-Hochberg exploratory adjustment",
            "official_leaderboard": "NOT_RUN; synthetic proxies and no official calibration",
            "actual_cost_usd": None}


def markdown(report: dict) -> str:
    coverage = report["coverage"]
    lines = ["# Local synthetic MorphBench results", "", "Complete-budget trials only; all first failures and partial trials remain in JSON.", "",
             f"Coverage: expected {coverage['expected']}, observed {coverage['observed']}, missing {coverage['missing_count']}; complete budget {coverage['complete_budget_trials']}.", "",
             report["final_evaluation"], "",
             "| Task | System | Complete / observed | Final evaluation mean | SE | Search evaluations | Duplicates | Prefit | Final evaluation calls |",
             "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for r in report["groups"]:
        score = r["test_score"]
        lines.append(f"| {r['task']} | {r['system']} | {r['complete_trials']}/{r['trials']} | {score['mean']} | {score['se']} | {r['evaluations_finished']} | {r['duplicate_evaluations']} | {r['setup_evaluations']} | {r['test_evaluations']} |")
    lines += ["", "Paired differences (higher is better, including the negative mathematical BM-05 objective):", "",
              "| Task | Contrast | n | Mean difference | 95% paired bootstrap CI | Exploratory BH q |", "|---|---|---:|---:|---|---:|"]
    for r in report["paired_contrasts"]:
        lines.append(f"| {r['task']} | {r['contrast']} | {r['n']} | {r['mean']} | {r['ci95']} | {r.get('bh_q')} |")
    lines += ["", "Fixed-allowance contrasts including observable partial trials (descriptive; execution counts may differ):", "",
              "| Task | Contrast | n | Mean difference | 95% paired bootstrap CI |", "|---|---|---:|---:|---|"]
    for r in report["fixed_allowance_paired_contrasts"]:
        lines.append(f"| {r['task']} | {r['contrast']} | {r['n']} | {r['mean']} | {r['ci95']} |")
    lines += ["", report["interpretation"], "", report["bootstrap_unit"], "", report["official_leaderboard"], ""]
    if coverage["missing"]:
        lines += ["Missing combinations:", "", "| Task | Seed | System | Status |", "|---|---:|---|---|"]
        lines += [f"| {r['task']} | {r['seed']} | {r['system']} | {r['status']} |" for r in coverage["missing"]]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = summarize(args.input)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "summary.json").write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    (args.output / "summary.md").write_text(markdown(report), encoding="utf-8")
    print(json.dumps({"trials": len(report["trials"]), "groups": len(report["groups"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
