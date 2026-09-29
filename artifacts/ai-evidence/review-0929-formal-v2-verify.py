"""Mechanical v2 quote comparison only; never validates an inference or a review."""
import argparse
import json
import re
import subprocess
from pathlib import Path


def verify(item):
    if item.get("type") == "hypothesis":
        return "NOT_RUN" if item.get("status") == "待验证" else "INVALID"
    if item.get("type") != "fact":
        return "INVALID"
    sha, location, quote = (item.get(k) for k in ("commit", "file", "quote"))
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
        return "INVALID"
    if not isinstance(location, str) or not isinstance(quote, str):
        return "INVALID"
    match = re.fullmatch(r"([^:\r\n]+):([1-9][0-9]*)", location)
    if not match or not quote or "\r" in quote:
        return "INVALID"
    path, start = match[1], int(match[2]) - 1
    if path.startswith(("/", "-")) or ".." in path.split("/"):
        return "INVALID"
    commit = subprocess.run(["git", "cat-file", "-t", sha], capture_output=True)
    if commit.returncode or commit.stdout.strip() != b"commit":
        return "NOT_FOUND"
    blob = subprocess.run(["git", "show", f"{sha}:{path}"], capture_output=True)
    if blob.returncode:
        return "NOT_FOUND"
    try:
        lines = blob.stdout.decode("utf-8").splitlines()
    except UnicodeDecodeError:
        return "INVALID"
    expected = quote.split("\n")
    if start + len(expected) > len(lines):
        return "NOT_FOUND"
    return "PASS" if lines[start:start + len(expected)] == expected else "INVALID"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("items", type=Path, help="JSON array; fact or hypothesis only")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    items = json.loads(args.items.read_text(encoding="utf-8-sig"))
    if not isinstance(items, list) or not items:
        raise ValueError("A nonempty JSON item array is required; absence is not PASS")
    results = []
    for index, item in enumerate(items):
        result = verify(item) if isinstance(item, dict) else "INVALID"
        results.append({"index": index, "verification": result})
    payload = {"scope": "quote equality only; inference not verified", "results": results}
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))
    return int(any(r["verification"] not in ("PASS", "NOT_RUN") for r in results))


if __name__ == "__main__":
    raise SystemExit(main())
