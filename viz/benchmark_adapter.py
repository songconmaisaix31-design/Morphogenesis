"""Read-only projection of persisted benchmark results for the dashboard.

The benchmark runner already emits a bounded, aggregate-only JSON (no questions,
gold answers, per-request evidence URIs or credentials). This adapter only reads
that file and re-emits it under a fixed read-only schema; it never recomputes
scores, never loads datasets or gold answers, and never calls a model.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

BENCHMARK_SCHEMA = "morph.benchmark.readonly/1"
MAX_BYTES = 2_000_000


def empty_benchmark(note: str = "未配置 benchmark 结果文件；/api/benchmark 保持空态。") -> dict[str, Any]:
    return {
        "schema": BENCHMARK_SCHEMA,
        "readonly": True,
        "observed_at": time.time(),
        "conditions": [],
        "notes": [note],
    }


def load_benchmark(path: Path) -> dict[str, Any]:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
            return empty_benchmark("benchmark 结果文件不可用。")
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return empty_benchmark("benchmark 结果文件格式无效。")
        conditions = raw.get("conditions")
        if not isinstance(conditions, list):
            return empty_benchmark("benchmark 结果文件缺少 conditions。")
        return {
            "schema": BENCHMARK_SCHEMA,
            "readonly": True,
            "observed_at": time.time(),
            "generated_at": raw.get("generated_at"),
            "protocol": raw.get("protocol"),
            "note": raw.get("note"),
            "conditions": [condition for condition in conditions if isinstance(condition, dict)],
        }
    except (OSError, ValueError):
        return empty_benchmark("benchmark 结果文件读取失败。")
