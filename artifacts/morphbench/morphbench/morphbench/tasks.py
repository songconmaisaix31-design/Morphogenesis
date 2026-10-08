"""Benchmark task registry.

Two layers live here:

1. The **peer-aligned inventory** (`PEER_INVENTORY`) enumerates the exact
   benchmark portfolio that peer products report on (BioML-Bench, ProteinGym,
   GPT-training-optimization, MLR-Bench, ScienceAgentBench, MLE-bench,
   PaperBench, RE-Bench). It is metadata-only and drives the mapping document.

2. The **locally runnable suite** (`TASKS`) implements a CPU-only surrogate of
   that portfolio so the harness produces real, verifiable numbers offline.
   Each runnable task also carries `reference_scores` anchors so a raw score
   maps to a leaderboard percentile.
"""
from __future__ import annotations

from typing import Dict, List

from .core import TaskSpec

# ---------------------------------------------------------------------------
# 1. Peer-aligned inventory (mirrors what each peer product reports on)
# ---------------------------------------------------------------------------
PEER_INVENTORY: List[Dict[str, str]] = [
    {"peer": "Harvard AutoScientists", "benchmark": "BioML-Bench",
     "scope": "24 tasks: imaging 4 / drug discovery 9 / protein engineering 6 / single-cell 5",
     "metric": "mean leaderboard percentile; medal rate; completion rate",
     "reported": "74.40% (vs Autoresearch 66.07%); drug discovery 64.52%"},
    {"peer": "Harvard AutoScientists", "benchmark": "ProteinGym",
     "scope": "217 substitution assays",
     "metric": "Spearman rho (rank accuracy)",
     "reported": "ACE2-Spike +12.5% rho; all-217 +6.5% rho"},
    {"peer": "Harvard AutoScientists / EvoMap AutoResearch", "benchmark": "GPT training optimization (nanochat)",
     "scope": "single 5-min GPT training run per experiment (H100)",
     "metric": "val bits-per-byte (lower better); experiments-to-target",
     "reported": "1.9x faster to target; 7 vs 0 accepted improvements from champion"},
    {"peer": "Sakana AI (The AI Scientist v2)", "benchmark": "ICLR workshop blind review",
     "scope": "end-to-end paper generation",
     "metric": "double-blind review score (ICLR scale)",
     "reported": "6.33 avg (6/7/6) > human acceptance line"},
    {"peer": "NUS et al.", "benchmark": "MLR-Bench",
     "scope": "201 open-ended ML research tasks (NeurIPS/ICLR/ICML workshops)",
     "metric": "MLR-Judge 9-dim rubric (Consistency/Novelty/Clarity/Feasibility/"
               "Completeness/Soundness/Insightfulness/Significance/Overall)",
     "reported": "coding agents fabricated results in ~80% of cases"},
    {"peer": "OSU et al.", "benchmark": "ScienceAgentBench",
     "scope": "102 data-driven scientific tasks",
     "metric": "Valid Execution Rate (VER) / Success Rate (SR) / CodeBERTScore (CBS)",
     "reported": "best agent ~32.1% SR"},
    {"peer": "OpenAI", "benchmark": "MLE-bench",
     "scope": "75 Kaggle competitions, 24h Docker sandbox",
     "metric": "medal rate (>=bronze placement)",
     "reported": "O1-preview 16.9% medal rate"},
    {"peer": "OpenAI", "benchmark": "PaperBench",
     "scope": "20 ICML papers replication",
     "metric": "rubric-based replication score",
     "reported": "best agent ~21% replication"},
    {"peer": "METR", "benchmark": "RE-Bench",
     "scope": "7 ML tasks vs human experts, 8h budget",
     "metric": "score ratio vs human expert",
     "reported": "agents below human at 2h, ahead at 32h"},
    {"peer": "Adaption (AutoScientist)", "benchmark": "in-house vertical win-rate",
     "scope": "8 verticals x 5k-100k samples, auto fine-tuning",
     "metric": "win rate vs human-configured fine-tuning",
     "reported": "48% -> 64% (up to ~2x in company claims)"},
    {"peer": "EvoMap (AutoResearch)", "benchmark": "idea-generation efficiency",
     "scope": "weekly 8xL20 ideation->validation loop",
     "metric": "# ideas generated / # validated",
     "reported": "2584 ideas / 14 validated per week"},
]


# ---------------------------------------------------------------------------
# 2. Locally runnable surrogate suite
# ---------------------------------------------------------------------------
def _mk(task_id, name, tier, domain, metric, higher, peer, ref, budget, desc):
    return TaskSpec(
        id=task_id, name=name, tier=tier, domain=domain, metric=metric,
        higher_is_better=higher, peer_source=peer, reference_scores=ref,
        budget=budget, description=desc,
    )


TASKS: Dict[str, TaskSpec] = {
    # --- Tier B: end-to-end scientific ML (surrogate of BioML-Bench) --------
    "BM-01": _mk(
        "BM-01", "Protein fitness regression", "e2e", "protein_engineering",
        "spearman_rho", True, "ProteinGym / BioML-Bench protein engineering",
        {"median": 0.45, "p75": 0.60, "p90": 0.72, "sota": 0.85},
        {"max_units": 40, "unit": "model_fit"}, "Predict protein fitness (rank).",
    ),
    "BM-02": _mk(
        "BM-02", "Drug-discovery ADMET classification", "e2e", "drug_discovery",
        "auroc", True, "TDC / Polaris / BioML-Bench drug discovery",
        {"median": 0.72, "p75": 0.82, "p90": 0.88, "sota": 0.94},
        {"max_units": 40, "unit": "model_fit"}, "Binary ADMET/toxicity prediction.",
    ),
    "BM-03": _mk(
        "BM-03", "Single-cell cell-type annotation", "e2e", "single_cell_omics",
        "accuracy", True, "Open Problems / BioML-Bench single-cell",
        {"median": 0.70, "p75": 0.82, "p90": 0.90, "sota": 0.96},
        {"max_units": 40, "unit": "model_fit"}, "Classify cell types from expression.",
    ),
    "BM-04": _mk(
        "BM-04", "Biomedical image classification", "e2e", "biomedical_imaging",
        "accuracy", True, "Kaggle / BioML-Bench imaging",
        {"median": 0.75, "p75": 0.85, "p90": 0.92, "sota": 0.97},
        {"max_units": 40, "unit": "model_fit"}, "Classify synthetic bio-images.",
    ),
    # --- Tier B: model-training optimization (surrogate of nanochat) -------
    "BM-05": _mk(
        "BM-05", "GPT training hyper-parameter optimization", "e2e", "model_training",
        "neg_val_bpb", True, "Autoresearch nanochat GPT training optimization",
        {"median": -0.98, "p75": -0.965, "p90": -0.955, "sota": -0.945},
        {"max_units": 40, "unit": "training_run"}, "Minimize validation bits-per-byte.",
    ),
    # --- Tier A: swarm-native mechanism metrics ----------------------------
    "SB-01": _mk(
        "SB-01", "Fault tolerance under worker loss", "swarm", "mechanism",
        "survival_rate", True, "AutoScientists robustness analysis",
        {"median": 0.70, "p75": 0.90, "p90": 0.98, "sota": 1.0},
        {"kills": 2}, "Complete the task after killing k workers mid-run.",
    ),
    "SB-02": _mk(
        "SB-02", "Experience-metabolism reuse gain", "swarm", "mechanism",
        "reuse_gain", True, "Morphogenesis experience metabolism (novel)",
        {"median": 0.15, "p75": 0.30, "p90": 0.45, "sota": 0.60},
        {"rounds": 2}, "Cost saved on 2nd exposure to a solved task.",
    ),
    "SB-03": _mk(
        "SB-03", "Coordination-overhead ratio", "swarm", "mechanism",
        "overhead_ratio", False, "central-scheduler baseline (AutoGen-style)",
        {"median": 0.30, "p75": 0.18, "p90": 0.10, "sota": 0.05},
        {}, "Wall-clock overhead vs a no-coordination baseline (lower better).",
    ),
    "SB-04": _mk(
        "SB-04", "Redundant-work rate", "swarm", "mechanism",
        "redundant_rate", False, "stigmergy coordination (Morphogenesis)",
        {"median": 0.25, "p75": 0.12, "p90": 0.06, "sota": 0.02},
        {}, "Share of duplicated experiment units (lower better).",
    ),
}

REGISTRY = list(TASKS.values())


def list_tasks(tier: str | None = None) -> List[TaskSpec]:
    if tier is None:
        return list(TASKS.values())
    return [t for t in TASKS.values() if t.tier == tier]


def get_task(task_id: str) -> TaskSpec:
    return TASKS[task_id]
