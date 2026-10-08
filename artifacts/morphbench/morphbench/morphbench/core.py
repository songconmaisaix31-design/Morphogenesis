"""Core types and metric utilities for MorphBench."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

import numpy as np


# ---------------------------------------------------------------------------
# Data contracts
# ---------------------------------------------------------------------------
@dataclass
class TaskSpec:
    """Metadata describing one benchmark task.

    `reference_scores` anchors a raw score to a *leaderboard percentile* the
    same way BioML-Bench reports "mean leaderboard percentile": we anchor on
    human / public-submission quantiles supplied per task.
    """

    id: str
    name: str
    tier: str                       # "swarm" | "e2e" | "open" | "replication"
    domain: str
    metric: str
    higher_is_better: bool
    peer_source: str                # which peer benchmark/product this mirrors
    reference_scores: Dict[str, float] = field(default_factory=dict)
    budget: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass
class RunOutcome:
    """One system's result on one task."""

    task_id: str
    system: str
    score: float
    extra: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Leaderboard-percentile mapping
# ---------------------------------------------------------------------------
_DEFAULT_ANCHORS = {
    "p10": 0.10,
    "p25": 0.25,
    "median": 0.50,
    "p75": 0.75,
    "p90": 0.90,
    "sota": 0.98,
}


def leaderboard_percentile(
    score: float,
    reference_scores: Dict[str, float],
    higher_is_better: bool = True,
) -> float:
    """Map a raw metric to a percentile in [0, 100] against a reference set.

    The reference set uses quantile anchors (p10/p25/median/p75/p90/sota and
    optionally p0/min/p100/max). Values are interpolated linearly between
    anchors and clipped to the observed [0, 100] band. This mirrors the
    "leaderboard percentile relative to public human submissions" metric that
    AutoScientists reports on BioML-Bench.
    """
    if not reference_scores:
        return float("nan")

    anchors: list[tuple[float, float]] = []
    for key, pct in _DEFAULT_ANCHORS.items():
        if key in reference_scores:
            anchors.append((float(reference_scores[key]), pct * 100.0))
    if not anchors:
        return float("nan")

    anchors.sort(key=lambda t: t[0])
    xs = np.array([a[0] for a in anchors], dtype=float)
    ps = np.array([a[1] for a in anchors], dtype=float)

    if not higher_is_better:
        xs = -xs
        score = -score

    pct = float(np.interp(score, xs, ps))
    return max(0.0, min(100.0, pct))


# ---------------------------------------------------------------------------
# Swarm-native mechanism metrics
# ---------------------------------------------------------------------------
def experience_reuse_gain(round1_cost: float, round2_cost: float) -> float:
    """Fraction of cost saved on the 2nd exposure to the same task.

    Mirrors Morphogenesis' 'experience metabolism' claim: a swarm that reuses
    validated experience should reach the same target with less compute.
    """
    if round1_cost <= 0:
        return 0.0
    return max(0.0, (round1_cost - round2_cost) / round1_cost)


def fault_tolerance_survival(completed: int, total: int) -> float:
    """Passive-degradation survival rate under worker loss."""
    if total <= 0:
        return 0.0
    return completed / total


def coordination_overhead(system_wallclock: float, baseline_wallclock: float) -> float:
    """Extra wall-clock attributed to coordination, relative to a baseline."""
    if baseline_wallclock <= 0:
        return 0.0
    return (system_wallclock - baseline_wallclock) / baseline_wallclock


def redundant_work_rate(duplicate_units: int, total_units: int) -> float:
    """Share of executed units that duplicated already-available work."""
    if total_units <= 0:
        return 0.0
    return duplicate_units / total_units


def tokens_per_improvement(total_tokens: float, accepted_improvements: int) -> float:
    """LLM-token cost per accepted improvement (efficiency of the search)."""
    if accepted_improvements <= 0:
        return float("inf")
    return total_tokens / accepted_improvements
