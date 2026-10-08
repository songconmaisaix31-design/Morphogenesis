# MorphBench

**A peer-aligned benchmark suite for Morphogenesis — the same benchmark layer that
AutoScientist / AutoScientists / The AI Scientist report on, extended with
swarm-native mechanism metrics.**

MorphBench is a self-contained, CPU-only evaluation harness. It contains two things:

1. **`PEER_INVENTORY`** (`morphbench/tasks.py`) — the exact benchmark portfolio peer
   products report on, so Morphogenesis can be placed on the *same leaderboards*:
   - Harvard **AutoScientists** → BioML-Bench (24 tasks), ProteinGym (217 assays),
     GPT-training-optimization (nanochat).
   - Sakana **The AI Scientist v2** → ICLR-workshop blind review score.
   - NUS **MLR-Bench** → 201 tasks + MLR-Judge 9-dim rubric.
   - OSU **ScienceAgentBench** → 102 tasks, VER/SR/CBS metrics.
   - OpenAI **MLE-bench** / **PaperBench**, METR **RE-Bench**.
   - Adaption **AutoScientist** → internal vertical win-rate.
   - EvoMap **AutoResearch** → ideation/validation efficiency.

2. **A runnable surrogate suite** that produces real, verifiable numbers offline,
   with three reference systems compared under a matched experiment budget:
   - `SingleAgent` — sequential, no shared memory (mirrors Autoresearch hill-climb).
   - `CentralScheduler` — central planner (mirrors AutoGen/MetaGPT orchestration).
   - `MorphSwarm` — N workers + stigmergy ledger + experience reuse (Morphogenesis).

## Task portfolio

| Tier | ID | Task | Metric | Peer source |
|---|---|---|---|---|
| B | BM-01 | Protein fitness regression | Spearman ρ | ProteinGym / BioML-Bench |
| B | BM-02 | Drug-discovery ADMET classification | AUROC | TDC / Polaris / BioML-Bench |
| B | BM-03 | Single-cell cell-type annotation | Accuracy | Open Problems / BioML-Bench |
| B | BM-04 | Biomedical image classification | Accuracy | Kaggle / BioML-Bench |
| B | BM-05 | GPT training HPO | −val bits-per-byte | Autoresearch nanochat |
| A | SB-01 | Fault tolerance under worker loss | Survival rate | AutoScientists robustness |
| A | SB-02 | Experience-metabolism reuse gain | Cost saved (round 2) | Morphogenesis (novel) |
| A | SB-03 | Coordination-overhead ratio | Overhead (lower better) | central-scheduler baseline |
| A | SB-04 | Redundant-work rate | Duplicate share (lower better) | stigmergy coordination |

Every Tier-B raw score is mapped to a **leaderboard percentile** against
per-task anchors (`median/p75/p90/sota`), mirroring AutoScientists' headline
"mean leaderboard percentile" metric.

## Run

```bash
python -m pip install -r requirements.txt
cd morphbench && python ../run_demo.py --budget 24 --out ../outputs
```

Outputs `outputs/morphbench_report.json` and `outputs/morphbench_report.md`.

## Scope & honesty notes

- The Tier-B tasks are **CPU-only surrogates** (synthetic data + sklearn), not the
  real BioML-Bench/ProteinGym datasets. They validate the *harness and metrics*,
  not frontier capability. To publish real numbers, swap `local_tasks.py`
  builders for the official task loaders (Kaggle/TDC/Open Problems/ProteinGym APIs).
- The only mechanism difference modelled between systems is **experiment
  allocation under a fixed budget** (a stigmergy ledger avoids re-runs; worker
  loss degrades gracefully). This is a mechanism ablation, not a performance claim.
- `judge.py` provides a deterministic offline rubric judge (MLR-Judge-style) and
  execution verdicts (ScienceAgentBench VER/SR); plug in an LLM judge via
  `llm_call` for production scoring.
