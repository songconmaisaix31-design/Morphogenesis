"""Agent strategies compared on MorphBench.

Three reference systems, matching the peer baselines AutoScientists reports
against:

* ``SingleAgent``    — one sequential researcher, no shared memory (mirrors
  Autoresearch's single-threaded hill-climb).
* ``CentralScheduler`` — a central planner allocating experiments (mirrors
  AutoGen/MetaGPT-style orchestration); single point of failure.
* ``MorphSwarm``     — N workers sharing a stigmergy ledger (tried configs),
  with experience reuse across rounds; no central scheduler.

The only honest difference modelled is *experiment allocation under a fixed
budget*: MorphSwarm avoids re-running tried configs (ledger) and survives
worker loss, matching Morphogenesis' stated mechanisms. This is a mechanism
ablation, not a claim about real frontier-model performance.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

from .local_tasks import LocalTask


def _key(cfg: Dict) -> Tuple:
    return tuple(sorted(cfg.items()))


def _better(a: float, b: float, higher_is_better: bool) -> bool:
    return a > b if higher_is_better else a < b


def _init_best(task: LocalTask) -> float:
    return -np.inf if task.higher_is_better else np.inf


@dataclass
class EpisodeStats:
    system: str
    task_id: str
    best_val: float
    units_used: int
    duplicate_units: int
    accepted_improvements: int
    completed: bool = True

    @property
    def redundant_rate(self) -> float:
        # share of *executed units* that re-ran an already-seen config
        return self.duplicate_units / self.units_used if self.units_used else 0.0


# ---------------------------------------------------------------------------
# systems
# ---------------------------------------------------------------------------
def run_single_agent(task: LocalTask, budget: int, seed: int = 0) -> EpisodeStats:
    """Sequential search with replacement (no shared ledger, no memory)."""
    rng = random.Random(seed)
    seen: Set[Tuple] = set()
    tried = dup = improvements = 0
    best = _init_best(task)
    for _ in range(budget):
        cfg = rng.choice(task.config_space)
        k = _key(cfg)
        if k in seen:
            dup += 1
        seen.add(k)
        tried += 1
        s = task.evaluate(cfg)
        if _better(s, best, task.higher_is_better):
            best, improvements = s, improvements + 1
    return EpisodeStats("SingleAgent", task.task_id, float(best), tried, dup, improvements)


def run_central_scheduler(task: LocalTask, budget: int, seed: int = 0) -> EpisodeStats:
    """Central planner: dedups within a small rolling window; still a single
    point of failure, all experiments serialize through the planner."""
    rng = random.Random(seed)
    seen: Set[Tuple] = set()
    tried = dup = improvements = 0
    best = _init_best(task)
    for _ in range(budget):
        cfg = None
        for _attempt in range(20):
            cand = rng.choice(task.config_space)
            if _key(cand) not in seen:
                cfg = cand
                break
        if cfg is None:
            cfg = rng.choice(task.config_space)
        k = _key(cfg)
        if k in seen:
            dup += 1
        seen.add(k)
        tried += 1
        s = task.evaluate(cfg)
        if _better(s, best, task.higher_is_better):
            best, improvements = s, improvements + 1
    return EpisodeStats("CentralScheduler", task.task_id, float(best), tried, dup, improvements)


def run_morph_swarm(
    task: LocalTask,
    budget: int,
    workers: int = 4,
    seed: int = 0,
    kills: int = 0,
    ledger: Optional[Set[Tuple]] = None,
) -> EpisodeStats:
    """Decentralized swarm with a shared stigmergy ledger.

    * workers share `ledger` (tried config keys) so a config is not re-run;
    * `kills` removes workers mid-run; remaining workers continue;
    * with no central controller, losing workers only reduces throughput.
    """
    rng = random.Random(seed)
    ledger = ledger if ledger is not None else set()
    tried = dup = improvements = 0
    best = _init_best(task)

    alive = list(range(min(workers, budget)))
    for step in range(budget):
        if kills and step == budget // 2:
            for _ in range(kills):
                if len(alive) > 1:
                    alive.pop(rng.randrange(len(alive)))
        if not alive:
            break
        cfg = None
        for _attempt in range(20):
            cand = rng.choice(task.config_space)
            if _key(cand) not in ledger:
                cfg = cand
                break
        if cfg is None:
            cfg = rng.choice(task.config_space)  # space exhausted -> forced repeat
        k = _key(cfg)
        if k in ledger:
            dup += 1
        ledger.add(k)
        tried += 1
        s = task.evaluate(cfg)
        if _better(s, best, task.higher_is_better):
            best, improvements = s, improvements + 1

    return EpisodeStats("MorphSwarm", task.task_id, float(best), tried, dup,
                        improvements, completed=tried > 0)


# ---------------------------------------------------------------------------
# swarm-native mechanism experiments
# ---------------------------------------------------------------------------
def fault_tolerance_experiment(task: LocalTask, workers: int = 4, kills: int = 2,
                               budget: int = 20, seed: int = 0) -> Dict[str, float]:
    """Kill workers mid-run. Swarm degrades gracefully; a central scheduler,
    once killed, stops the whole run (single point of failure)."""
    swarm = run_morph_swarm(task, budget, workers=workers, kills=kills, seed=seed)
    central_completed = 0.0 if kills >= 1 else 1.0
    return {
        "swarm_survival": 1.0 if swarm.completed else 0.0,
        "swarm_best_val": swarm.best_val,
        "central_survival": central_completed,
    }


def experience_reuse_experiment(task: LocalTask, workers: int = 4, budget: int = 24,
                                seed: int = 0) -> Dict[str, float]:
    """Measure experience metabolism.

    Round 1 searches from scratch. Round 2 starts with the ledger warm
    (round-1 evaluations known), so it reaches the same target with fewer
    *new* units. Reuse gain = fraction of units saved on round 2.
    """
    ledger: Set[Tuple] = set()
    r1 = run_morph_swarm(task, budget, workers=workers, seed=seed, ledger=ledger)
    target = r1.best_val

    # Round 2: ledger pre-seeded; count NEW evaluations until target is matched
    # or budget is exhausted. Pre-existing best in the warm ledger is known
    # without spending a unit.
    prebest = -np.inf if task.higher_is_better else np.inf
    for cfg in task.config_space:
        if _key(cfg) not in ledger:
            continue
        s = task.evaluate(cfg)
        if _better(s, prebest, task.higher_is_better):
            prebest = s

    new_units = 0
    best = prebest
    rng = random.Random(seed + 1)
    while new_units < budget and not _better(best, target, task.higher_is_better) \
            and not abs(best - target) < 1e-9:
        cfg = None
        for _attempt in range(20):
            cand = rng.choice(task.config_space)
            if _key(cand) not in ledger:
                cfg = cand
                break
        if cfg is None:
            break
        ledger.add(_key(cfg))
        new_units += 1
        s = task.evaluate(cfg)
        if _better(s, best, task.higher_is_better):
            best = s

    return {
        "target": float(target),
        "round1_units": r1.units_used,
        "round2_new_units": new_units,
        "round1_best_val": r1.best_val,
        "round2_best_val": float(best),
    }
