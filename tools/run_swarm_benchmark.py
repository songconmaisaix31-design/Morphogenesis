"""Prepare and score the pinned GSM8K/BBH swarm benchmark without exposing gold answers.

Live execution is intentionally delegated to the generic EvoMap swarm entrypoint.  This
module owns the reproducible source selection, answer isolation, and conservative scoring.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import random
import re
import subprocess
import sys
from typing import Any, Iterable, Literal


GSM8K_REVISION = "3101c7d5072418e28b9008a6636bde82a006892c"
BBH_REVISION = "9ee07bd481feebf959a6b59d61ea57bdcf30964d"
GSM8K_REPOSITORY = "https://github.com/openai/grade-school-math.git"
BBH_REPOSITORY = "https://github.com/suzgunmirac/BIG-Bench-Hard.git"
DEFAULT_SEED = 20260924
BBH_TASKS = ("logical_deduction_three_objects", "multistep_arithmetic_two", "boolean_expressions")


@dataclass(frozen=True)
class BenchmarkExample:
    sample_id: str
    dataset: Literal["gsm8k", "bbh"]
    task: str
    question: str
    target: str


@dataclass(frozen=True)
class Score:
    status: Literal["correct", "incorrect", "malformed", "missing", "duplicate"]
    strict_json: bool
    normalized_correct: bool


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _require_revision(root: Path, revision: str) -> None:
    actual = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=True,
                            capture_output=True, text=True).stdout.strip()
    if actual != revision:
        raise ValueError("dataset_revision_mismatch")
    dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all"],
                           check=True, capture_output=True, text=True).stdout.strip()
    if dirty:
        raise ValueError("dataset_checkout_dirty")


def download_sources(directory: Path) -> tuple[Path, Path]:
    """Clone exact public revisions outside the repository; never print examples or answers."""
    directory.mkdir(parents=True, exist_ok=True)
    result: list[Path] = []
    for name, repository, revision in (("gsm8k", GSM8K_REPOSITORY, GSM8K_REVISION),
                                       ("bbh", BBH_REPOSITORY, BBH_REVISION)):
        target = directory / name
        if not target.exists():
            subprocess.run(["git", "clone", "--no-checkout", repository, str(target)], check=True)
        subprocess.run(["git", "-C", str(target), "checkout", "--detach", revision], check=True)
        _require_revision(target, revision)
        result.append(target)
    return result[0], result[1]


def _gsm_target(answer: str) -> str:
    match = re.search(r"####\s*([^\n]+)\s*$", answer)
    if match is None:
        raise ValueError("gsm8k_answer_without_official_marker")
    return match.group(1).strip()


def _load_gsm8k(root: Path) -> list[BenchmarkExample]:
    path = root / "grade_school_math" / "data" / "test.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    examples: list[BenchmarkExample] = []
    for index, row in enumerate(rows):
        question, answer = row.get("question"), row.get("answer")
        if not isinstance(question, str) or not isinstance(answer, str):
            raise ValueError("invalid_gsm8k_record")
        examples.append(BenchmarkExample(f"gsm8k:test:{index}", "gsm8k", "test", question, _gsm_target(answer)))
    return examples


def _load_bbh_task(root: Path, task: str) -> list[BenchmarkExample]:
    body = _read_json(root / "bbh" / f"{task}.json")
    rows = body.get("examples") if isinstance(body, dict) else None
    if not isinstance(rows, list):
        raise ValueError("invalid_bbh_task_file")
    examples: list[BenchmarkExample] = []
    for index, row in enumerate(rows):
        question, target = ((row.get("input"), row.get("target")) if isinstance(row, dict) else (None, None))
        if not isinstance(question, str) or not isinstance(target, str):
            raise ValueError("invalid_bbh_record")
        examples.append(BenchmarkExample(f"bbh:{task}:{index}", "bbh", task, question, target))
    return examples


def _choose(rows: list[BenchmarkExample], count: int, rng: random.Random) -> list[BenchmarkExample]:
    if len(rows) < count:
        raise ValueError("dataset_too_small_for_requested_stratum")
    indexes = list(range(len(rows)))
    rng.shuffle(indexes)
    return [rows[index] for index in indexes[:count]]


def select_examples(gsm8k_root: Path, bbh_root: Path, *, seed: int = DEFAULT_SEED,
                    gsm8k_count: int = 24, bbh_per_task: int = 8) -> list[BenchmarkExample]:
    """Select a fixed stratified subset. Gold stays in memory for acceptance seeding only."""
    _require_revision(gsm8k_root, GSM8K_REVISION)
    _require_revision(bbh_root, BBH_REVISION)
    rng = random.Random(seed)
    selected = _choose(_load_gsm8k(gsm8k_root), gsm8k_count, rng)
    for task in BBH_TASKS:
        selected.extend(_choose(_load_bbh_task(bbh_root, task), bbh_per_task, rng))
    rng.shuffle(selected)
    return selected


def select_extension(gsm8k_root: Path, bbh_root: Path, *, seed: int = DEFAULT_SEED) -> tuple[list[BenchmarkExample], list[BenchmarkExample]]:
    """Return 48 baseline rows and 48 disjoint additions with baseline IDs preserved."""
    baseline = select_examples(gsm8k_root, bbh_root, seed=seed)
    all_rows = _load_gsm8k(gsm8k_root)
    for task in BBH_TASKS:
        all_rows.extend(_load_bbh_task(bbh_root, task))
    used = {row.sample_id for row in baseline}
    additions = [row for row in all_rows if row.sample_id not in used]
    if len(additions) < 48:
        raise ValueError("dataset_too_small_for_extension")
    return baseline, _choose(additions, 48, random.Random(seed + 1))


def public_manifest(examples: Iterable[BenchmarkExample], *, seed: int) -> dict[str, Any]:
    """Public run metadata deliberately excludes targets and questions."""
    rows = list(examples)
    return {"protocol": "swarm-common-benchmark-v1", "seed": seed,
            "sources": {"gsm8k": {"revision": GSM8K_REVISION, "license": "MIT"},
                        "bbh": {"revision": BBH_REVISION, "license": "MIT"}},
            "sample_ids": [row.sample_id for row in rows], "count": len(rows)}


def benchmark_instruction(example: BenchmarkExample) -> str:
    return ("Solve the official benchmark question below. Return exactly one JSON object with string field answer "
            "and adopted_asset_ids set to an empty array. Do not use Markdown, explanation, or tools.\n\nQuestion:\n"
            + example.question)


def _gsm_number(value: str) -> Decimal | None:
    cleaned = value.strip().replace(",", "").replace("$", "")
    try:
        value = Decimal(cleaned)
        return value if value.is_finite() else None
    except InvalidOperation:
        return None


def normalized_correct(example: BenchmarkExample, answer: str) -> bool:
    if example.dataset == "gsm8k":
        actual, expected = _gsm_number(answer), _gsm_number(example.target)
        return actual is not None and expected is not None and actual == expected
    return answer.strip() == example.target.strip()


def score_response(example: BenchmarkExample, response: str | None, *, duplicate: bool = False) -> Score:
    if duplicate:
        return Score("duplicate", False, False)
    if response is None:
        return Score("missing", False, False)
    try:
        value = json.loads(response)
    except (TypeError, json.JSONDecodeError):
        return Score("malformed", False, False)
    strict_json = (isinstance(value, dict) and set(value) == {"answer", "adopted_asset_ids"}
                   and isinstance(value.get("answer"), str) and value.get("adopted_asset_ids") == [])
    if not strict_json:
        return Score("malformed", False, False)
    correct = normalized_correct(example, value["answer"])
    return Score("correct" if correct else "incorrect", True, correct)


def summarize(scores: Iterable[Score]) -> dict[str, int | float]:
    values = list(scores)
    totals = {status: sum(score.status == status for score in values)
              for status in ("correct", "incorrect", "malformed", "missing", "duplicate")}
    total = len(values)
    return {"requested": total, **totals, "accuracy": totals["correct"] / total if total else 0.0,
            "strict_json_rate": sum(score.strict_json for score in values) / total if total else 0.0}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, required=True, help="task-specific directory outside Git")
    parser.add_argument("--manifest", type=Path, required=True, help="public metadata destination; no answers")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--download", action="store_true", help="clone pinned public source revisions")
    args = parser.parse_args(argv)
    try:
        gsm, bbh = download_sources(args.sources) if args.download else (args.sources / "gsm8k", args.sources / "bbh")
        examples = select_examples(gsm, bbh, seed=args.seed)
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(public_manifest(examples, seed=args.seed), indent=2) + "\n", encoding="utf-8")
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError):
        print("benchmark_source_or_manifest_failed", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
