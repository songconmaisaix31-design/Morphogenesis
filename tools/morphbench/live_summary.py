"""Describe fixed-denominator results, known usage and missing/unknown evidence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from live_plan import SEEDS, SYSTEMS, plan
from summarize import estimate, paired


def accounting(root: Path) -> dict[str, Any]:
    requests = sorted(root.rglob("request.json"))
    rows = []
    for path in requests:
        request = json.loads(path.read_text(encoding="utf-8"))
        response_path = path.with_name("response.json")
        response = json.loads(response_path.read_text(encoding="utf-8")) if response_path.exists() else {}
        usage = response.get("usage")
        trace = path.with_name("http-trace.jsonl")
        trace_rows = [json.loads(line) for line in trace.read_text().splitlines()] if trace.exists() else []
        rows.append({"request_evidence": str(path), "local_request_id": request.get("request_id"),
            "provider_request_id": response.get("request_id"), "returned_model": response.get("returned_model"),
            "task_id": request.get("attempt", {}).get("task_id"),
            "requested_model": request.get("request", {}).get("model"),
            "provenance": request.get("provenance"), "usage": usage,
            "cached_input_tokens": response.get("cached_input_tokens"),
            "elapsed_seconds": response.get("elapsed_seconds"), "http_status": response.get("http_status"),
            "classification": response.get("classification"), "error_kind": response.get("error_kind"),
            "unknown_effect": not response or response.get("uncertain", False),
            "http_send_entry_observed": any(t.get("stage") == "http_send_entered" for t in trace_rows),
            "estimated_cost_cny": None if usage is None else
                (usage["prompt_tokens"] * 0.8 + usage["completion_tokens"] * 2) / 1000000,
            "actual_bill_cny": None})
    complete = all(r["usage"] is not None for r in rows)
    inputs = sum(r["usage"]["prompt_tokens"] for r in rows if r["usage"] is not None)
    outputs = sum(r["usage"]["completion_tokens"] for r in rows if r["usage"] is not None)
    known_cost = sum(r["estimated_cost_cny"] for r in rows if r["estimated_cost_cny"] is not None)
    return {"local_request_intents": len(rows), "live_http_send_entries": sum(r["http_send_entry_observed"] for r in rows),
            "usage_complete": complete, "known_input_tokens": inputs, "known_output_tokens": outputs,
            "input_tokens": inputs if complete else None, "output_tokens": outputs if complete else None,
            "known_estimated_cost_cny": known_cost, "estimated_cost_cny": known_cost if complete else None,
            "actual_bill_cny": None, "currency": "CNY", "accounting_cny_per_usd": 6,
            "cache_discount_applied": False, "price_source": plan()["prices"], "rows": rows}


def dynamic_metrics(result: dict[str, Any], folder: Path) -> dict[str, Any]:
    path = folder / "events.jsonl"
    arrivals = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    by_id = {r["signal"]["task_id"]: r for r in result.get("ledger", [])}
    audit = result.get("ledger_audit", [])
    phase_rows = []
    for phase in range(3):
        tasks = [a for a in arrivals if a["phase"] == phase]
        records = [by_id[t["task_id"]] for t in tasks if t["task_id"] in by_id]
        solved = [r for r in records if r["status"] == "completed" and r["effect_applied"]]
        # Do not call service latency adaptation; no success-derived winner is fed back.
        claims = [a for a in audit if a.get("event") == "claimed" and a.get("task_id") in {t["task_id"] for t in tasks}]
        delays = [a["at"] - t["time"] for t in tasks for a in claims if a["task_id"] == t["task_id"]]
        phase_rows.append({"phase": phase, "arrived": len(tasks), "expected": 4, "solved": len(solved),
                           "first_service_seconds": min(delays) if delays else None,
                           "unsolved": len(tasks) - len(solved),
                           "end_backlog": sum(r["status"] not in ("completed", "failed", "blocked") for r in records),
                           "worker_outcomes": [{"task_id": r["signal"]["task_id"], "worker": r["owner"],
                               "family": r["signal"]["module"],
                               "success": r["status"] == "completed" and r["effect_applied"]} for r in records]})
    return {"phases": phase_rows, "adaptation_delay": None,
            "adaptation_status": "NOT_IDENTIFIED_no_preregistered_evidence_of_reversed_best_worker",
            "capability_reversal_is_config_intervention_only": True}


def summarize(root: Path) -> dict[str, Any]:
    cells = []
    for cell in plan()["trials"]:
        if cell["category"] not in ("code", "dynamic"):
            continue
        path = root / cell["id"] / "result.json"
        result = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
        responses = result.get("responses", []) if result else []
        all_usage = result is not None and len(responses) == result["local_request_intents"] and all(r.get("usage") for r in responses)
        known_tokens = sum(r["usage"]["total_tokens"] for r in responses if r.get("usage"))
        solved = result["solved"] if result else 0
        cells.append({"cell": cell, "status": "OBSERVED" if result is not None else "NOT_RUN",
            "solved": result["solved"] if result else 0,
            "fixed_denominator": cell["request_cap"],
            "planned_completion_rate": (result["solved"] if result else 0) / cell["request_cap"],
            "observed_intents": result["local_request_intents"] if result else 0,
            "known_tokens": known_tokens, "usage_complete": all_usage,
            "tokens_per_solved": known_tokens / solved if solved and all_usage else None,
            "seconds_per_solved": result["elapsed_seconds"] / solved if solved and result is not None else None,
            "elapsed_seconds": result["elapsed_seconds"] if result else None,
            "dynamic": dynamic_metrics(result, path.parent) if result and cell["category"] == "dynamic" else None})
    groups, contrasts = [], []
    for category in ("code", "dynamic"):
        for system in SYSTEMS:
            group = [r for r in cells if r["cell"]["category"] == category and r["cell"]["system"] == system]
            observed = [r for r in group if r["status"] == "OBSERVED"]
            groups.append({"category": category, "system": system, "planned_seed_count": len(SEEDS),
                "observed_seed_count": len(observed),
                "planned_completion_rate": estimate([r["planned_completion_rate"] for r in group]),
                "observed_cell_completion_rate": estimate([r["planned_completion_rate"] for r in observed]),
                "elapsed_seconds": estimate([r["elapsed_seconds"] for r in observed])})
        def rates(system: str) -> dict[int, float]:
            return {r["cell"]["seed"]: r["planned_completion_rate"] for r in cells
                    if r["cell"]["category"] == category and r["cell"]["system"] == system and r["status"] == "OBSERVED"}
        contrasts.append({"category": category, "comparison": "successor_claim_v01-minus-legacy_cycle_v0",
                          **paired(rates("successor_claim_v01"), rates("legacy_cycle_v0"))})
    money = accounting(root)
    return {"cells": cells, "groups": groups, "paired_contrasts": contrasts, "accounting": money,
            "missing_cells": [r["cell"]["id"] for r in cells if r["status"] == "NOT_RUN"],
            "missing_cells_are_not_model_failure_scores": True,
            "note": "Planned completion includes unexecuted denominator; observed-cell scores/paired CI exclude whole unrun cells and disclose n."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = summarize(args.root)
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    print(json.dumps({"missing_cells": len(report["missing_cells"]),
                      "intents": report["accounting"]["local_request_intents"],
                      "actual_bill_cny": None}))
