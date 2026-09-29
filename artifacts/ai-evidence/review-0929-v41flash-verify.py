"""Strict quote and coverage validation. No model calls or semantic approval."""
import argparse
import json
import re
import subprocess
from pathlib import Path

SHA = "c552250c0d07f5f70f09eb0a5ab3c322195e34ec"
ROOT = Path(__file__).resolve().parents[2]


def verify(item):
    if not isinstance(item, dict):
        return "INVALID"
    if item.get("type") == "hypothesis":
        return "NOT_RUN" if item.get("status") == "待验证" else "INVALID"
    if item.get("type") != "fact" or item.get("commit") != SHA:
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
    result = subprocess.run(["git", "show", f"{SHA}:{path}"], cwd=ROOT, capture_output=True)
    if result.returncode:
        return "NOT_FOUND"
    # Compare original blob bytes with UTF-8 bytes of the decoded quote. No trim,
    # whitespace normalization, line-number repair or Unicode normalization.
    raw_quote = quote.encode("utf-8")
    lines = result.stdout.split(b"\n")
    expected = raw_quote.split(b"\n")
    return "PASS" if lines[start:start + len(expected)] == expected else "INVALID"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("response", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    coverage = json.loads((Path(__file__).with_name("review-0929-v41flash-coverage.json")).read_text(encoding="utf-8"))
    payload = {"candidate": SHA, "scope": "quote bytes/start lines and coverage presence only; no semantic acceptance",
               "response_present": args.response.exists(), "results": [], "missing_dimensions": [r["id"] for r in coverage["required"]]}
    exit_code = 2
    if args.response.exists():
        try:
            items = json.loads(args.response.read_text(encoding="utf-8-sig"))
            if not isinstance(items, list) or not items or len(items) > 100:
                raise ValueError("Response must be a nonempty array with at most 100 items")
            seen = set()
            for i, item in enumerate(items):
                result = verify(item)
                identifier = item.get("id") if isinstance(item, dict) else None
                if not isinstance(identifier, str) or not identifier or identifier in seen:
                    result = "INVALID"
                seen.add(identifier)
                payload["results"].append({"index": i, "id": identifier, "verification": result})
            facts = {item.get("id") for item, result in zip(items, payload["results"]) if result["verification"] == "PASS"}
            invalid_evidence = [item.get("id") for item in items if isinstance(item, dict) and item.get("type") == "hypothesis"
                                and (not isinstance(item.get("evidence"), list) or any(x not in facts for x in item.get("evidence", [])))]
            payload["invalid_evidence_references"] = invalid_evidence
            dimensions = {item.get("dimension") for item in items if isinstance(item, dict) and item.get("type") == "hypothesis" and item.get("status") == "待验证"}
            payload["missing_dimensions"] = [r["id"] for r in coverage["required"] if r["id"] not in dimensions]
            exit_code = int(bool(payload["missing_dimensions"] or invalid_evidence or any(r["verification"] not in ("PASS", "NOT_RUN") for r in payload["results"])))
            payload["status"] = "MECHANICAL_ONLY" if exit_code == 0 else "REJECTED_MECHANICAL"
        except (ValueError, TypeError, KeyError) as error:
            payload["status"] = "INVALID_OUTPUT"
            payload["error"] = str(error)
            exit_code = 1
    else:
        payload["status"] = "NOT_RUN_NO_RESPONSE"
    payload["exit_code"] = exit_code
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "exit_code": exit_code, "results": payload["results"], "missing_dimensions": len(payload["missing_dimensions"])}))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
