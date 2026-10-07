"""Run the frozen cells once, serially, stopping all new paid starts on uncertainty."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time
import traceback

from live_experience import run as experience
from live_faults import run as fault
from live_plan import plan
from live_run import identity, run_cell, run_single, write


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--mode", choices=("offline", "live"), default="offline")
    parser.add_argument("--product-source", required=True)
    parser.add_argument("--protocol-source", required=True)
    parser.add_argument("--window-message", required=True)
    args = parser.parse_args()
    root = args.out.resolve()
    root.mkdir(parents=True, exist_ok=False)
    frozen = plan()
    write(root / "arguments.json", {**vars(args), "out": str(root), "plan": frozen,
          "installed": identity(), "started": time.time(),
          "preflight": "NOT_RUN_no_separate_preflight_or_calibration", "unallocated_slots_used": 0})
    # Full-loop wall bound is finite: 24 cells * 600s, 3 reuse groups * 720s,
    # 4 fault cells * 510s. Actual elapsed is reported, never budget as usage.
    try:
        for cell in frozen["trials"]:
            if cell["category"] not in ("code", "dynamic"):
                continue
            print(json.dumps({"event": "cell_start", "cell": cell["id"], "at": time.time()}), flush=True)
            runner = run_single if cell["system"] == "single" else run_cell
            result = runner(root / cell["id"], cell, args.mode)
            print(json.dumps({"event": "cell_end", "cell": cell["id"], "solved": result["solved"],
                              "intents": result["local_request_intents"], "stop_paid": result["stop_paid"]}), flush=True)
            if result["stop_paid"]:
                write(root / "stopped.json", {"cell": cell["id"], "reason": "unknown_or_provider_rejection", "at": time.time()})
                return 2
        for seed in (0, 1, 2):
            print(json.dumps({"event": "experience_start", "seed": seed}), flush=True)
            result = experience(root / f"experience-s{seed}", seed, args.mode)
            if result["stop_paid"]:
                write(root / "stopped.json", {"cell": f"experience-s{seed}", "reason": "unknown_or_provider_rejection"})
                return 2
        for stage in ("before_reserve", "before_commit", "after_commit", "inflight"):
            print(json.dumps({"event": "fault_start", "stage": stage}), flush=True)
            result = fault(root / f"fault-{stage}", stage, args.mode)
            if result["stop_paid"] or not result["stage_reached"]:
                write(root / "stopped.json", {"cell": f"fault-{stage}", "reason":
                      "inflight_is_final_intentional_stop" if stage == "inflight" else "fault_incomplete_or_unknown"})
                return 0 if stage == "inflight" and result["stage_reached"] else 2
    except BaseException:
        write(root / "failure.json", {"exception": traceback.format_exc(), "at": time.time(),
                                     "remaining_cells": "NOT_RUN; no automatic continuation"})
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
