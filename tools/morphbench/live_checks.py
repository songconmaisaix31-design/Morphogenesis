"""Serial representative offline gates; never run the whole paid matrix as mock."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

from live_plan import SYSTEMS
from live_run import identity, write


def run(root: Path, only: list[str] | None = None) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=False)
    tools = Path(__file__).resolve().parent
    commands: list[tuple[str, list[str], int]] = [
        ("negative", ["live_offline.py"], 60),
        *((f"code-s0-{system}", ["live_run.py", "--mode", "offline", "--cell", f"code-s0-{system}"], 630)
          for system in SYSTEMS),
        *((f"dynamic-s0-{system}", ["live_run.py", "--mode", "offline", "--cell", f"dynamic-s0-{system}"], 630)
          for system in ("legacy_cycle_v0", "successor_claim_v01")),
        ("experience-s0", ["live_experience.py", "--mode", "offline", "--seed", "0"], 750),
        *((f"fault-{stage}", ["live_faults.py", "--mode", "offline", "--stage", stage], 540)
          for stage in ("before_reserve", "before_commit", "after_commit", "inflight")),
    ]
    names = [name for name, _, _ in commands]
    if only and not set(only).issubset(names):
        raise ValueError("unknown offline check")
    omitted = [name for name in names if only and name not in only]
    commands = [command for command in commands if command[0] not in omitted]
    results = []
    write(root / "identity.json", identity())
    for name, parts, timeout in commands:
        command = [sys.executable, str(tools / parts[0]), *parts[1:], "--out", str(root / name)]
        print(json.dumps({"event": "offline_start", "name": name, "at": time.time()}), flush=True)
        started = time.time()
        with (root / (name + ".stdout.log")).open("wb") as out, (root / (name + ".stderr.log")).open("wb") as err:
            completed = subprocess.run(command, cwd=root, stdout=out, stderr=err, timeout=timeout, check=False)
        row = {"name": name, "command": command, "exit_code": completed.returncode, "seconds": time.time() - started}
        results.append(row)
        write(root / "commands.json", results)
        if completed.returncode != 0:
            raise RuntimeError(f"offline first failure: {name}; inspect original logs")
        result = json.loads((root / name / "result.json").read_text(encoding="utf-8"))
        if name == "negative":
            assert result["passed"] and len(result["rows"]) == 7
        elif name.startswith("code"):
            assert result["mode"] == "offline" and not result["stop_paid"]
            assert result["local_request_intents"] <= 6
            if "legacy_cycle" in name:
                assert 1 <= result["solved"] <= 6
                assert all(r["status"] in ("completed", "available") for r in result["ledger"])
                if result["solved"] < 6:
                    assert all(r.get("status", {}).get("remaining_energy") == 0 for r in result["worker_results"])
            else:
                assert result["solved"] == 6
        elif name.startswith("dynamic"):
            assert result["solved"] == 12 and result["local_request_intents"] == 12
            arrivals = [json.loads(line) for line in (root / name / "events.jsonl").read_text().splitlines()]
            assert [sum(a["phase"] == phase for a in arrivals) for phase in range(3)] == [4, 4, 4]
            epoch = json.loads((root / name / "arrival-clock.json").read_text())["epoch"]
            for phase, earliest in ((1, 45), (2, 90)):
                assert min(a["time"] for a in arrivals if a["phase"] == phase) - epoch >= earliest
        elif name == "experience-s0":
            assert len(result["arms"]) == 4 and len(result["adoptions"]) == 1
            assert len({r["target"] for r in result["arms"]}) == 4
            assert len({r["process"]["pid"] for r in result["arms"]}) == 4
            assert result["arms"][-1]["negative_control"]["refused"]
            assert result["solved"] == result["local_request_intents"] == 4
        elif name == "fault-before_reserve":
            assert result["stage_reached"] and result["solved"] == result["local_request_intents"] == 1
            assert result["stale_submit_effects"] == [] and result["stale_errors"]
        elif name == "fault-before_commit":
            assert result["stage_reached"] and result["solved"] == 0 and result["safe_to_continue"]
            assert result["local_request_intents"] == 1 and not result["stop_paid"]
        elif name == "fault-after_commit":
            assert result["stage_reached"] and result["solved"] == result["local_request_intents"] == 1
        else:
            assert result["stage_reached"] and result["stop_paid"] and result["solved"] == 0
            assert result["local_request_intents"] == 0
        print(json.dumps({"event": "offline_pass", "name": name, "seconds": row["seconds"]}), flush=True)
    report = {"passed": True, "provider_requests": 0, "commands": results, "omitted_checks": omitted,
              "not_covered": "other seeds, real HTTP credential/trace child, full 233-slot matrix; not task_live evidence"}
    write(root / "result.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--only", nargs="+", help="Run selected checks in a NEW evidence directory; omitted checks stay explicit.")
    args = parser.parse_args()
    run(args.out.resolve(), args.only)
