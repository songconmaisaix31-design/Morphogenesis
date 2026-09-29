"""Strict original quote/start-line verifier adapted from 40577cb v41flash verifier.

Apache-2.0 repository reuse. No model invocation or semantic acceptance.
Exit 0 = mechanical only; 1 = INVALID; 2 = response absent. Never rewrites input.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path


def verify(item, sha, repo):
    if not isinstance(item, dict):
        return "INVALID"
    if item.get("type") == "hypothesis":
        return "NOT_RUN" if (item.get("status") == "待验证"
            and item.get("severity") in ("high", "medium", "low", "info")
            and isinstance(item.get("content"), str) and item["content"]
            and isinstance(item.get("suggested_check"), str) and item["suggested_check"]) else "INVALID"
    if item.get("type") != "fact" or item.get("commit") != sha or item.get("verification") != "NOT_RUN":
        return "INVALID"
    location, quote = item.get("file"), item.get("quote")
    if not isinstance(location, str) or not isinstance(quote, str) or not quote or "\r" in quote:
        return "INVALID"
    match = re.fullmatch(r"([^:\r\n]+):([1-9][0-9]*)", location)
    if not match:
        return "INVALID"
    path, start = match[1], int(match[2]) - 1
    if path.startswith(("/", "-")) or ".." in path.split("/") or "\\" in path:
        return "INVALID"
    result = subprocess.run(["git", "show", f"{sha}:{path}"], cwd=repo, capture_output=True)
    if result.returncode:
        return "INVALID"
    expected = quote.encode("utf-8").split(b"\n")
    return "PASS" if result.stdout.split(b"\n")[start:start + len(expected)] == expected else "INVALID"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("response", type=Path)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--coverage", type=Path, required=True)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.candidate):
        parser.error("Full candidate SHA required")
    coverage = json.loads(args.coverage.read_text(encoding="utf-8-sig"))
    if coverage["candidate"] != args.candidate:
        parser.error("Coverage/candidate mismatch")
    required = {x["id"] for x in coverage["required"]}
    payload = {"candidate": args.candidate, "scope": "original quote bytes/start lines and coverage presence only; NO semantic acceptance",
               "response_present": args.response.exists(), "results": [], "missing_dimensions": sorted(required)}
    exit_code = 2
    if args.response.exists():
        try:
            items = json.loads(args.response.read_text(encoding="utf-8-sig"))
            if not isinstance(items, list) or not items or len(items) > 100:
                raise ValueError("Response must be nonempty array of at most 100 items")
            seen = set()
            for i, item in enumerate(items):
                result = verify(item, args.candidate, args.repo)
                identifier = item.get("id") if isinstance(item, dict) else None
                if not isinstance(identifier, str) or not identifier or identifier in seen:
                    result = "INVALID"
                else:
                    seen.add(identifier)
                if not isinstance(item, dict) or not isinstance(item.get("dimension"), str) or item["dimension"] not in required:
                    result = "INVALID"
                payload["results"].append({"index": i, "id": identifier, "verification": result})
            facts = {item["id"] for item, result in zip(items, payload["results"]) if result["verification"] == "PASS"}
            dimensions, invalid_evidence = set(), []
            for item, result in zip(items, payload["results"]):
                if not isinstance(item, dict) or item.get("type") != "hypothesis":
                    continue
                evidence = item.get("evidence")
                valid = isinstance(evidence, list) and all(isinstance(x, str) and x in facts for x in evidence)
                if not valid:
                    invalid_evidence.append(item.get("id"))
                elif result["verification"] == "NOT_RUN":
                    dimensions.add(item["dimension"])
            payload["invalid_evidence_references"] = invalid_evidence
            payload["missing_dimensions"] = sorted(required - dimensions)
            exit_code = int(bool(payload["missing_dimensions"] or invalid_evidence or any(r["verification"] not in ("PASS", "NOT_RUN") for r in payload["results"])))
            payload["status"] = "MECHANICAL_ONLY" if exit_code == 0 else "REJECTED_MECHANICAL"
        except (ValueError, TypeError, KeyError) as error:
            payload["status"], payload["error"], exit_code = "INVALID_OUTPUT", str(error), 1
    else:
        payload["status"] = "NOT_RUN_NO_RESPONSE"
    payload["exit_code"] = exit_code
    with args.output.open("x", encoding="utf-8", newline="\n") as target:
        target.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": payload["status"], "exit_code": exit_code, "missing_dimensions": len(payload["missing_dimensions"])}))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
