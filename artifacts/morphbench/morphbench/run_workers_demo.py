#!/usr/bin/env python3
"""Smoke-drive the real decentralized workers on one MorphBench task."""
from __future__ import annotations

import argparse
import json
import sys


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default="BM-05")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--energy", type=int, default=4)
    ap.add_argument("--kills", type=int, default=0)
    args = ap.parse_args()

    from morphbench.worker_engine import run_decentralized
    out = run_decentralized(args.task, workers=args.workers, energy=args.energy,
                            seed=0, kills=args.kills)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
