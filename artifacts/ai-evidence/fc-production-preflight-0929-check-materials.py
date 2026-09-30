"""Offline negative controls for review tooling; never validates product behavior."""
import argparse
import copy
import json
import runpy
import subprocess
import sys
from pathlib import Path

import yaml  # existing poetry.lock dependency, used only to read native config dump

ROOT = Path(__file__).resolve().parents[2]
PREFIX = "review-0929-release-v41flash-"
GOV = "40577cb841e8d89c08e1336d7254c4ca7bb3984e"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--native-dir", required=True, type=Path)
    parser.add_argument("--controls-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.controls_dir.mkdir(parents=True, exist_ok=False)
    data = json.loads((args.input_dir / (PREFIX + "input.json")).read_text(encoding="utf-8"))
    sha = data["candidate"]
    coverage = args.input_dir / (PREFIX + "coverage.json")
    required = json.loads(coverage.read_text(encoding="utf-8"))["required"]
    source = subprocess.run(["git", "show", f"{sha}:swarm/breaker.py"], cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8").splitlines()
    start = next(i for i, line in enumerate(source, 1) if "TODO-HUMAN-REVIEW: complete four-state transition table." in line)
    fact = {"id": "control_fact", "dimension": "inv1", "type": "fact", "commit": sha,
            "file": f"swarm/breaker.py:{start}", "quote": source[start - 1], "content": "CONTROL ONLY: exact comment bytes", "verification": "NOT_RUN"}
    items = [fact] + [{"id": "control_" + row["id"], "dimension": row["id"], "type": "hypothesis", "severity": "info",
                      "content": "CONTROL ONLY: no review performed, coverage insufficient", "status": "待验证", "evidence": ["control_fact"],
                      "suggested_check": "Actual designated reviewer must assess final candidate"} for row in required]
    cases = []
    def run(name, value, expected):
        response = args.controls_dir / (name + ".json")
        output = args.controls_dir / (name + ".verification.json")
        if value is not None:
            response.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        command = [sys.executable, "-B", str(Path(__file__).with_name(PREFIX + "verify.py")), str(response),
                   "--candidate", sha, "--coverage", str(coverage), "--output", str(output)]
        result = subprocess.run(command, cwd=ROOT, capture_output=True)
        (args.controls_dir / (name + ".stdout.log")).write_bytes(result.stdout)
        (args.controls_dir / (name + ".stderr.log")).write_bytes(result.stderr)
        cases.append({"case": name, "expected_exit": expected, "actual_exit": result.returncode, "pass": result.returncode == expected})
        return json.loads(output.read_text(encoding="utf-8"))
    run("exact_positive_mechanical_only", items, 0)
    bad = copy.deepcopy(items); bad[0]["file"] = f"swarm/breaker.py:{start + 1}"
    run("wrong_start_line", bad, 1)
    bad = copy.deepcopy(items); bad[0]["quote"] = bad[0]["quote"].lstrip()
    run("changed_whitespace", bad, 1)
    bad = copy.deepcopy(items); bad[0]["commit"] = GOV
    run("governance_sha_substitution", bad, 1)
    run("missing_dimension", items[:-1], 1)
    run("duplicate_id", items + [fact], 1)
    bad = copy.deepcopy(items); bad[1]["evidence"] = ["nonexistent"]
    run("invalid_evidence", bad, 1)
    run("non_array_output", {"items": items}, 1)
    run("no_response", None, 2)
    legacy = json.loads(subprocess.run(["git", "show", f"{GOV}:artifacts/ai-evidence/review-0929-formal-v2-items.json"], cwd=ROOT, capture_output=True, check=True).stdout)
    old = run("legacy_response_unchanged", legacy, 1)
    quote_verify = runpy.run_path(str(Path(__file__).with_name(PREFIX + "verify.py")))["verify"]
    legacy_quotes = [{"id": item["id"], "quote_verification": quote_verify(item, sha, ROOT)} for item in legacy if item["type"] == "fact"]
    native = json.loads((args.native_dir / "native-prepare.json").read_text(encoding="utf-8-sig"))
    rows = yaml.load((args.native_dir / "composed.yml").read_text(encoding="utf-8-sig"), Loader=yaml.BaseLoader)
    by_id = {row["id"]: row for row in rows}
    checks = {
        "native_dump_exit_zero": native["dump_exit"] == 0,
        "full_task_bytes_equal": by_id["headless-runner"]["config"]["task"].encode("utf-8") == data["content"].encode("utf-8"),
        "runner_no_startup_dependency": by_id["headless-runner"]["inject"] == [],
        "all_disabled_plugins_retained": all(by_id[x].get("disabled") == "true" for x in native["disabled_plugins"]),
        "zero_retry": by_id["llm-deepseek"]["config"]["retryPolicy"] == {"mode": "normal", "maxRetries": "0"},
        "finite_output": by_id["llm-deepseek"]["config"]["maxTokens"] == str(native["max_output_tokens"]),
        "official_route": by_id["agent-default-model"]["config"] == {"provider": "deepseek-official", "model": "deepseek-flash"},
    }
    exit_code = int(not all(x["pass"] for x in cases) or not all(checks.values()))
    payload = {"candidate": sha, "preparation_control": True, "source_reference": GOV,
               "control_cases": cases, "native_configuration_checks": checks,
               "legacy_current_protocol_results": old["results"], "legacy_quote_only_results": legacy_quotes, "model_requests": 0,
               "scope": "offline review-tool controls/config composition, NOT FC-E or product acceptance", "exit_code": exit_code}
    with args.output.open("x", encoding="utf-8", newline="\n") as target:
        target.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(payload, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
