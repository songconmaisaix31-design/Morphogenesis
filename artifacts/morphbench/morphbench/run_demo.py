#!/usr/bin/env python3
"""Run the MorphBench local suite and emit JSON + Markdown reports.

Usage:
    python run_demo.py --budget 24 --out ../outputs
"""
from __future__ import annotations

import argparse
import os

from morphbench.runner import run_suite, to_markdown
from morphbench.tasks import list_tasks


def main() -> None:
    ap = argparse.ArgumentParser(description="MorphBench local suite runner")
    ap.add_argument("--budget", type=int, default=24, help="experiments per task")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=str, default="outputs")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)

    print("Registered tasks:")
    for t in list_tasks():
        print(f"  [{t.tier:9s}] {t.id}  {t.name:42s} metric={t.metric}")

    report = run_suite(budget=args.budget, seed=args.seed)
    json_path = os.path.join(args.out, "morphbench_report.json")
    md_path = os.path.join(args.out, "morphbench_report.md")
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(report.to_json())
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(to_markdown(report))

    print("\n" + to_markdown(report))
    print(f"\nWrote:\n  {json_path}\n  {md_path}")


if __name__ == "__main__":
    main()
