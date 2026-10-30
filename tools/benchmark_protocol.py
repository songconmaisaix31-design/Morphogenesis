from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import random
import re
from typing import Any

from swarm.benchmark_model import ANSWER_FORMAT_INSTRUCTION
from tools.run_swarm_benchmark import GSM8K_REVISION, _require_revision


FRAMEWORKS = ("morphogenesis", "autogen-core", "langgraph")
CONCURRENCIES = (1, 2, 3, 4, 5)
SELECTION_PREFIX = "morph-gsm8k-v1\n"
# 官方 dataset.py 的首个答案标记和字符串比较规则；不加入数值容差。
ANSWER_PATTERN = re.compile(r"#### (\-?[0-9\.\,]+)")


@dataclass(frozen=True)
class Example:
    sample_id: str
    line_index: int
    question: str
    target: str

    @property
    def prompt(self) -> str:
        return "Solve this mathematics problem. " + ANSWER_FORMAT_INSTRUCTION + "\n\n" + self.question


def extract_answer(text: str) -> str | None:
    match = ANSWER_PATTERN.search(text)
    return match.group(1).replace(",", "") if match else None


def load_examples(source: Path, *, split: str = "test", count: int = 48) -> tuple[list[Example], dict[str, Any]]:
    _require_revision(source, GSM8K_REVISION)
    if split not in {"test", "train"} or count != (48 if split == "test" else 4):
        raise ValueError("fixed_test48_or_development_train4_required")
    data = source / "grade_school_math" / "data" / f"{split}.jsonl"
    raw = data.read_bytes()
    examples: list[Example] = []
    for index, line in enumerate(raw.splitlines()):
        row = json.loads(line)
        if not isinstance(row, dict) or not isinstance(row.get("question"), str) or not isinstance(row.get("answer"), str):
            raise ValueError("invalid_official_gsm8k_record")
        target = extract_answer(row["answer"])
        if target is None:
            raise ValueError("official_gsm8k_gold_marker_missing")
        examples.append(Example(f"gsm8k:{split}:{index}", index, row["question"], target))
    prefix = SELECTION_PREFIX if split == "test" else "morph-gsm8k-development-v1\n"
    examples.sort(key=lambda item: (hashlib.sha256((prefix + item.question).encode("utf-8")).hexdigest(), item.line_index))
    selected = examples[:count]
    if len(selected) != count:
        raise ValueError("insufficient_official_examples")
    manifest = {
        "schema": "morph.gsm8k-comparison-selection.v1", "dataset": "GSM8K", "split": split,
        "source_repository": "https://github.com/openai/grade-school-math.git",
        "source_revision": GSM8K_REVISION, "license": "MIT", "source_file_sha256": hashlib.sha256(raw).hexdigest(),
        "selection": "ascending SHA256(prefix + question), original zero-based row index tie-break",
        "selection_prefix": prefix, "count": count,
        "samples": [{"sample_id": item.sample_id, "line_index": item.line_index,
                     "question_sha256": hashlib.sha256(item.question.encode("utf-8")).hexdigest(),
                     "prompt_sha256": hashlib.sha256(item.prompt.encode("utf-8")).hexdigest()} for item in selected],
    }
    return selected, manifest


def model_tasks(examples: list[Example]) -> list[dict[str, str]]:
    # 这是唯一进入 Worker/其他框架的任务表示，不含参考答案。
    return [{"id": item.sample_id, "prompt": item.prompt} for item in examples]


def ordered_arms(seed: int) -> list[dict[str, Any]]:
    arms = [{"framework": framework, "concurrency": concurrency}
            for framework in FRAMEWORKS for concurrency in CONCURRENCIES]
    random.Random(seed).shuffle(arms)
    return arms


def score_records(examples: list[Example], records: list[dict[str, Any]]) -> dict[str, Any]:
    by_id: dict[str, list[dict[str, Any]]] = {}
    requested = {item.sample_id for item in examples}
    for record in records:
        task_id = record.get("task_id")
        if isinstance(task_id, str):
            by_id.setdefault(task_id, []).append(record)
    scores: list[dict[str, Any]] = []
    for item in examples:
        rows = by_id.get(item.sample_id, [])
        text = rows[0].get("text") if len(rows) == 1 else None
        evidence = rows[0].get("evidence", {}) if len(rows) == 1 else {}
        outcome = evidence.get("model_outcome") if isinstance(evidence, dict) else None
        if len(rows) > 1:
            state = "duplicate"
        elif len(rows) == 1 and rows[0].get("status") not in {None, "completed"}:
            state = "missing"
        elif outcome in {"truncated", "filtered"}:
            state = "incorrect"
        elif len(rows) == 1 and rows[0].get("status") == "completed" and not isinstance(text, str):
            state = "malformed"
        elif not isinstance(text, str):
            state = "missing"
        elif extract_answer(text) is None:
            state = "malformed"
        else:
            state = "correct" if extract_answer(text) == item.target else "incorrect"
        scores.append({"task_id": item.sample_id, "status": state,
                       "single_marker": isinstance(text, str) and len(ANSWER_PATTERN.findall(text)) == 1,
                       "model_outcome": outcome})
    counts = {state: sum(row["status"] == state for row in scores)
              for state in ("correct", "incorrect", "malformed", "missing", "duplicate")}
    return {"requested": len(examples), **counts, "accuracy": counts["correct"] / len(examples),
            "single_marker_rate": sum(row["single_marker"] for row in scores) / len(examples),
            "unexpected_task_ids": sorted(set(by_id) - requested), "per_task": scores,
            "scoring": "official first #### regex match, remove commas, exact string equality; truncated/filtered outputs fail protocol; all requested denominator"}


def summarize_http(records: list[dict[str, Any]]) -> dict[str, Any]:
    events: list[tuple[int, int]] = []
    clocks: set[str] = set()
    usage_rows: list[dict[str, int] | None] = []
    seen: set[tuple[str, int]] = set()
    for record in records:
        evidence = record.get("evidence", {})
        if not isinstance(evidence, dict):
            continue
        clock = evidence.get("clock")
        ordinal = evidence.get("request_ordinal")
        if not isinstance(clock, dict) or not isinstance(clock.get("id"), str) or type(ordinal) is not int:
            continue
        identity = (clock["id"], ordinal)
        if identity in seen:
            continue
        seen.add(identity)
        clocks.add(json.dumps(clock, sort_keys=True))
        start, end = evidence.get("http_entered_at_ns"), evidence.get("http_returned_at_ns")
        if type(start) is int and type(end) is int and start < end:
            events.extend(((start, 1), (end, -1)))
        usage = record.get("usage")
        usage_rows.append(usage if isinstance(usage, dict) else None)
    active = peak = 0
    if len(clocks) == 1:
        for _, delta in sorted(events, key=lambda item: (item[0], item[1])):
            active += delta
            peak = max(peak, active)
    totals = [row.get("total_tokens") if isinstance(row, dict) else None for row in usage_rows]
    known = [value for value in totals if type(value) is int]
    return {"deduplicated_requests": len(seen), "clock_consistent": len(clocks) == 1,
            "peak_client_http_active": peak if len(clocks) == 1 else None,
            "tokens_known_subtotal": sum(known),
            "tokens_total": sum(known) if len(known) == len(totals) and totals else None,
            "unknown_usage_requests": len(totals) - len(known), "billed_cost": None,
            "scope": "client-observed HTTP active intervals; not streaming/GPU concurrency"}
