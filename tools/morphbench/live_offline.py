"""Check frozen negative controls with the installed independent product runner."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

from live_cases import DEFECTS, GENERATION_CASE, model_material
from live_plan import plan


def offline(root: Path) -> dict[str, Any]:
    import bootstrap.acceptance_runner as runner
    from orchestration.sample_policy import validate_sample

    root.mkdir(parents=True, exist_ok=False)
    runner_path = Path(runner.__file__).resolve()
    if not runner_path.is_relative_to(Path(sys.prefix).resolve()):
        raise RuntimeError("independent_runner_must_be_installed")
    rows = []
    env = {k: v for k, v in os.environ.items()
           if not any(word in k.upper() for word in ("KEY", "TOKEN", "SECRET", "CREDENTIAL"))}
    for case in (*DEFECTS, GENERATION_CASE):
        validate_sample(case.source)
        target = root / case.name
        target.mkdir()
        source = target / "sample.py"
        source.write_text(case.source, encoding="utf-8")
        completed = subprocess.run([sys.executable, "-I", "-S", str(runner_path), str(source)],
                                   env=env, cwd=target, capture_output=True, text=True, timeout=15)
        (target / "test.stdout").write_text(completed.stdout, encoding="utf-8")
        (target / "test.stderr").write_text(completed.stderr, encoding="utf-8")
        checkpoints = [line for line in completed.stdout.splitlines()
                       if line.startswith("MORPH_CHECKPOINTS=")]
        observation = json.loads(checkpoints[0].split("=", 1)[1]) if len(checkpoints) == 1 else None
        expected_failures = ("clamp", "mean", "unique") if case.family == "composite" else (case.family,)
        rows.append({"defect": case.name, "family": case.family, "exit_code": completed.returncode,
                     "checkpoints": observation,
                     "negative_control_detected": completed.returncode == 1 and observation is not None
                     and all(observation["checks"][family] is False for family in expected_failures),
                     "model_material": model_material(case.name)})
    result = {"kind": "offline_negative_controls", "layer": "installed_contract_control",
              "provider_requests": 0, "python": sys.executable, "runner": str(runner_path),
              "plan": plan(), "rows": rows,
              "passed": all(row["negative_control_detected"] for row in rows)}
    (root / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    report = offline(args.out)
    print(json.dumps({"passed": report["passed"], "negative_controls": len(report["rows"]),
                      "provider_requests": 0, "out": str(args.out)}))
    raise SystemExit(0 if report["passed"] else 1)
