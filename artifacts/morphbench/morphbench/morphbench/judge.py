"""Rubric-based judging for open-ended research outputs (Tier C).

Mirrors the two judge families used by peers:

* **MLR-Bench / MLR-Judge** — a 9-dimension review rubric over research
  proposal / paper text.
* **ScienceAgentBench** — execution-grounded verdicts (Valid Execution Rate,
  Success Rate).

Both are deterministic offline here so the harness runs without a network.
An LLM judge can be plugged in through `llm_call` (optional).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

RUBRIC_DIMS: List[str] = [
    "Consistency", "Novelty", "Clarity", "Feasibility", "Completeness",
    "Soundness", "Insightfulness", "Significance", "Overall",
]

_METHOD_WORDS = ("method", "approach", "framework", "algorithm", "model", "training", "loss", "objective")
_EXPERIMENT_WORDS = ("experiment", "baseline", "ablation", "evaluation", "benchmark", "dataset", "validation")
_EVIDENCE_MARKERS = ("table", "figure", "results show", "we report", "accuracy", "score", "%", "rho", "auroc")


@dataclass
class JudgeResult:
    scores: Dict[str, float]
    overall: float
    rationale: str = ""

    def as_dict(self) -> Dict[str, float]:
        return {**self.scores, "Overall": self.overall}


def _clamp(x: float, lo: float = 1.0, hi: float = 10.0) -> float:
    return max(lo, min(hi, x))


def heuristic_judge(
    text: str,
    evidence: Optional[Dict[str, float]] = None,
    llm_call: Optional[Callable[[str], Dict[str, float]]] = None,
) -> JudgeResult:
    """Score a research text on the MLR-Judge rubric.

    Deterministic heuristic fallback; if `llm_call` is provided it is used
    instead (the returned dict is normalized onto the rubric).
    """
    if llm_call is not None:
        raw = llm_call(text)
        scores = {d: _clamp(float(raw.get(d, 5.0))) for d in RUBRIC_DIMS}
        overall = _clamp(float(raw.get("Overall", sum(scores.values()) / len(scores))))
        return JudgeResult(scores, overall, rationale="llm_judge")

    low = text.lower()
    n_words = max(1, len(low.split()))
    has_method = any(w in low for w in _METHOD_WORDS)
    has_exp = any(w in low for w in _EXPERIMENT_WORDS)
    has_evidence = any(w in low for w in _EVIDENCE_MARKERS)
    n_numbers = sum(ch.isdigit() for ch in low)

    length_signal = min(1.0, n_words / 400.0)
    scores = {
        "Consistency": _clamp(4 + 4 * length_signal),
        "Novelty": _clamp(3 + 3 * (has_method and has_exp) + 2 * length_signal),
        "Clarity": _clamp(5 + 3 * length_signal),
        "Feasibility": _clamp(4 + 3 * has_method + 2 * has_exp),
        "Completeness": _clamp(3 + 3 * has_exp + 2 * has_evidence + 2 * length_signal),
        "Soundness": _clamp(3 + 3 * has_evidence + 2 * has_exp + min(2.0, n_numbers / 20.0)),
        "Insightfulness": _clamp(3 + 3 * has_method + 2 * has_exp),
        "Significance": _clamp(4 + 2 * has_exp + 2 * length_signal),
    }
    if evidence:
        for k, v in evidence.items():
            if k in scores:
                scores[k] = _clamp(0.5 * scores[k] + 0.5 * v)
    overall = _clamp(sum(scores.values()) / len(scores))
    return JudgeResult(scores, overall, rationale="heuristic")


# ---------------------------------------------------------------------------
# Execution-grounded verdicts (ScienceAgentBench: VER / SR / CBS)
# ---------------------------------------------------------------------------
@dataclass
class ExecVerdict:
    valid_execution: int      # VER: ran without error + saved output
    success: int              # SR: output meets task criteria
    codebert_score: float = 0.0  # CBS proxy in [0,1]


def execution_verdict(ran_ok: bool, output_saved: bool, meets_criteria: bool,
                      code_similarity: float = 0.0) -> ExecVerdict:
    ver = 1 if (ran_ok and output_saved) else 0
    sr = 1 if (ver and meets_criteria) else 0
    return ExecVerdict(ver, sr, float(max(0.0, min(1.0, code_similarity))))
