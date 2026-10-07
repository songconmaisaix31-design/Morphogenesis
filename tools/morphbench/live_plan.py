"""Emit the reviewable live matrix and conservative financial plan, without IO to APIs."""
from __future__ import annotations

import argparse
from decimal import Decimal
import json
from pathlib import Path
from typing import Any

from live_cases import DEFECTS, PHASES, PROFILE_ORDER, PROFILES

SYSTEMS = ("single", "central_serial", "legacy_cycle_v0", "successor_claim_v01")
SEEDS = (0, 1, 2)
MODEL = "qwen-plus-2025-12-01"
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


def plan() -> dict[str, Any]:
    trials: list[dict[str, Any]] = []
    for category in ("code", "dynamic"):
        for seed in SEEDS:
            # Counterbalance order without consulting results.
            order = SYSTEMS[seed:] + SYSTEMS[:seed]
            for system in order:
                trials.append({"id": f"{category}-s{seed}-{system}", "category": category,
                               "seed": seed, "system": system,
                               "request_cap": 6 if category == "code" else 12})
    for seed in SEEDS:
        trials.append({"id": f"experience-source-s{seed}", "category": "experience_source",
                       "seed": seed, "request_cap": 1})
        for arm in ("none", "correct", "wrong"):
            trials.append({"id": f"experience-s{seed}-{arm}", "category": "experience_transfer",
                           "seed": seed, "arm": arm, "request_cap": 1})
    for stage in ("before_reserve", "before_commit", "after_commit", "inflight"):
        trials.append({"id": f"fault-{stage}", "category": "fault", "stage": stage,
                       "request_cap": 1})
    trials.append({"id": "preflight", "category": "preflight", "request_cap": 1})
    cap = sum(t["request_cap"] for t in trials)
    input_bound, output_bound = 16384, 2048
    unit_estimate = (Decimal(input_bound) * Decimal("0.8") +
                     Decimal(output_bound) * Decimal("2")) / Decimal(1000000)
    return {
        "protocol": "morphbench-live-1007-v2", "status": "FROZEN_PROTOCOL_REQUIRES_EXPLICIT_WINDOW",
        "model": MODEL, "base_url": BASE_URL, "enable_thinking": False,
        "temperature": 0.2, "provider_seed": 1234, "allocation_seeds": list(SEEDS),
        "max_input_bytes": 12000, "max_output_tokens": 1536,
        "reserve_input_tokens": input_bound, "reserve_output_tokens": output_bound,
        "prices": {"currency": "CNY", "input_per_million": "0.8", "output_per_million": "2",
                   "checked_date": "2026-10-08",
                   "source": "https://help.aliyun.com/zh/model-studio/qwen-plus"},
        "request_cap": cap, "unallocated_request_slots": 7, "absolute_request_cap": 240,
        "user_request_ceiling": 256, "user_currency_ceiling": "30",
        "per_request_admission_cny": "0.1", "total_admission_cny": "24",
        "accounting_cny_per_usd": "6", "conversion_is_market_fx": False,
        "planned_token_estimate_upper_cny": str(unit_estimate * cap),
        "actual_bill_cny": None, "pricing_is_estimate": True,
        "systems": list(SYSTEMS), "code_defects": [c.name for c in DEFECTS],
        "dynamic_arrival_seconds": [0, 45, 90], "dynamic_phases": PHASES,
        "profiles": PROFILES, "profile_order": PROFILE_ORDER,
        "trials": trials,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    body = json.dumps(plan(), ensure_ascii=False, indent=2) + "\n"
    if args.out:
        with args.out.open("x", encoding="utf-8") as stream:
            stream.write(body)
    else:
        print(body, end="")
