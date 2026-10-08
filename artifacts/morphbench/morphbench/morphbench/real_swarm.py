"""Real-engine adapter: drive MorphBench experiment allocation through
Morphogenesis 0.2.1's actual swarm modules.

WHAT IS REAL (imported from the 0.2.1 repository, executed, not reimplemented):
  * ``swarm.task_ledger.TaskLedger``  - enqueue / claim (fencing token) / submit.
    "Do not redo finished work" comes from the ledger's own eligibility rules,
    not from a Python ``set``.
  * ``swarm.pheromone.PheromoneField`` - deposit + exponential tau decay
    (``metabolism.decay.exponential_decay``) + materialisation per candidate.
  * ``swarm.router.Router``            - softmax weighted sampling over
    pheromone concentration x pipe history x urgency, plus ``reinforce``.
  * ``swarm.models`` (Signal / Locality / TaskRecord / RunLimits).

WHAT IS BENCHMARK-SIDE GLUE (our policy, explicitly labelled, not engine code):
  * how a config maps to a Signal (task id, capability, x/y coordinates);
  * how much pheromone an improving result deposits, neighbourhood radius+cap;
  * ``tau_seconds`` chosen so decay is observable inside a short run;
  * how "experience carries over" between rounds (copy the pheromone DB).

Read the resulting numbers as: *0.2.1's coordination substrate, driving a
synthetic ML hyper-parameter search.* Not as a BioML-Bench score.
"""
from __future__ import annotations

import math
import random
import shutil
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from swarm.models import Locality, RunLimits, Signal
from swarm.pheromone import PheromoneField
from swarm.router import Router
from swarm.task_ledger import TaskLedger

from .agents import EpisodeStats, _better, _init_best
from .local_tasks import LocalTask

# Benchmark knobs (NOT engine defaults).
TAU_SECONDS = 30.0          # 86400s default = no observable decay in a 2-min run
NEIGHBOURHOOD_RADIUS = 0.35
NEIGHBOURHOOD_CAP = 3       # bound sqlite cost: deposit to the k nearest only
EXPLORATION = 0.10
IMPROVE_DEPOSIT = 1.0
MISS_DEPOSIT = 0.05

FIELD_NAME = "pheromone.sqlite3"


def _family(cfg: Dict) -> str:
    """Model family -> Router capability ('pipe')."""
    return str(cfg.get("model", "hpo"))


def _coords(cfg: Dict, families: List[str]) -> Tuple[float, float]:
    """Config -> stigmergy coordinates: x = family, y = log-scaled magnitude."""
    fam = _family(cfg)
    x = (families.index(fam) + 1) / (len(families) + 1)
    nums = [v for _k, v in sorted(cfg.items())
            if isinstance(v, (int, float)) and not isinstance(v, bool)]
    y = 0.5
    if nums:
        y = min(1.0, math.log1p(abs(float(nums[0]))) / 10.0)
    return float(x), float(y)


def _payload(cfg: Dict) -> Dict[str, object]:
    return {k: (float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else str(v))
            for k, v in sorted(cfg.items())}


@dataclass
class RealEpisodeStats(EpisodeStats):
    units_to_target: Optional[int] = None


class SwarmEngine:
    """One real 0.2.1 ledger + pheromone field + router over a config space."""

    def __init__(self, task: LocalTask, seed: int = 0, tau_seconds: float = TAU_SECONDS,
                 root: Optional[Path] = None, swarm_id: Optional[str] = None,
                 reuse_field_from: Optional[Path] = None, persist: bool = False) -> None:
        self.task = task
        self.persist = persist
        self._tmp = root or Path(tempfile.mkdtemp(prefix="morphbench-swarm-"))
        self.root = self._tmp.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        sid = swarm_id or f"{task.task_id}-s{seed}"

        self.ledger = TaskLedger(
            self.root / "ledger.sqlite3", sid,
            limits=RunLimits(max_tasks=max(1000, len(task.config_space) + 10),
                             max_attempts=100000, max_attempts_per_task=10),
        )
        if reuse_field_from is not None and Path(reuse_field_from).is_file():
            # Carry the learned landscape (pheromone + pipe history) into a
            # fresh ledger: the policy transfers, the completed work does not.
            shutil.copy2(reuse_field_from, self.root / FIELD_NAME)
        self.field = PheromoneField(self.root / FIELD_NAME, ledger=self.ledger,
                                    tau_seconds=tau_seconds)
        self.router = Router(self.field, beta=1.0, rng=random.Random(seed),
                             exploration=EXPLORATION)
        # Locality needs a non-empty authorized scope: `_local_filter` emits
        # "(0)" (matches nothing) when the tuple is empty.
        self.locality = Locality(workspace=str(self.root), authorized_scopes=("cfg",))
        self.families = sorted({_family(c) for c in task.config_space})
        self.capabilities = {f: 1.0 for f in self.families}
        self.signals: Dict[str, Signal] = {}
        self.cfg_by_id: Dict[str, Dict] = {}
        self.done: set = set()
        self._enqueue_space()

    @property
    def field_path(self) -> Path:
        return self.root / FIELD_NAME

    def _enqueue_space(self) -> None:
        for i, cfg in enumerate(self.task.config_space):
            tid = f"cfg-{i}"
            x, y = _coords(cfg, self.families)
            signal = Signal(
                task_id=tid, workspace=str(self.root), scope=f"cfg/{tid}",
                kind="opportunity", payload=_payload(cfg),
                required_capability=_family(cfg), module="morphbench",
                concentration=1.0, urgency=1.0, x=x, y=y,
            )
            self.ledger.enqueue(signal)
            self.signals[tid] = signal
            self.cfg_by_id[tid] = cfg

    def _deposit(self, tid: str, delta: float) -> None:
        if delta > 0:
            self.field.deposit(self.signals[tid], delta)

    def _spread(self, tid: str, delta: float) -> None:
        """Stigmergic spread to the k nearest *untried* configs (bounded cost)."""
        if delta <= 0:
            return
        origin = self.signals[tid]
        ranked: List[Tuple[float, str]] = []
        for other_id, sig in self.signals.items():
            if other_id == tid or other_id in self.done:
                continue
            d = math.dist((origin.x, origin.y), (sig.x, sig.y))
            if d <= NEIGHBOURHOOD_RADIUS:
                ranked.append((d, other_id))
        ranked.sort()
        for d, other_id in ranked[:NEIGHBOURHOOD_CAP]:
            self._deposit(other_id, delta * (1.0 - d / NEIGHBOURHOOD_RADIUS))

    def close(self) -> None:
        if not self.persist and self.root.exists():
            shutil.rmtree(self.root, ignore_errors=True)


def run_real_swarm(task: LocalTask, budget: int, workers: int = 4, seed: int = 0,
                   kills: int = 0, tau_seconds: float = TAU_SECONDS,
                   target: Optional[float] = None,
                   reuse_field_from: Optional[Path] = None,
                   swarm_id: Optional[str] = None,
                   root: Optional[Path] = None,
                   persist: bool = False) -> RealEpisodeStats:
    """Allocate a fixed experiment budget through the real 0.2.1 swarm.

    A unit is "duplicate" when the stigmergic recommendation pointed at work the
    real ledger refused (already completed / still leased), or when the space is
    exhausted and a repeat is forced. The ledger is what prevents the waste, so
    the residual rate measures the coordinator's mis-steps.
    """
    rng = random.Random(seed)
    engine = SwarmEngine(task, seed=seed, tau_seconds=tau_seconds,
                         reuse_field_from=reuse_field_from, swarm_id=swarm_id,
                         root=root, persist=persist)
    tried = dup = improvements = 0
    best = _init_best(task)
    units_to_target: Optional[int] = None
    alive: List[str] = [f"w{i}" for i in range(workers)]
    try:
        for step in range(budget):
            if kills and step == budget // 2:
                for _ in range(kills):
                    if len(alive) > 1:
                        alive.pop(rng.randrange(len(alive)))
            if not alive:
                break
            worker = alive[step % len(alive)]
            chosen = engine.router.choose(worker, engine.locality, engine.capabilities)
            if chosen is None:
                # space exhausted -> forced repeat (a genuinely wasted unit)
                cfg = rng.choice(task.config_space)
                score = task.evaluate(cfg)
                tried += 1
                dup += 1
                if _better(score, best, task.higher_is_better):
                    best, improvements = score, improvements + 1
            else:
                lease = engine.ledger.claim(chosen.task_id, worker,
                                            locality=engine.locality, ttl_seconds=30)
                if lease is None:
                    # stale recommendation: the real ledger refused, unit wasted
                    tried += 1
                    dup += 1
                else:
                    cfg = engine.cfg_by_id[chosen.task_id]
                    score = float(task.evaluate(cfg))
                    engine.ledger.submit(lease, result_id=f"res-{tried}",
                                         result={"score": score})
                    tried += 1
                    improved = _better(score, best, task.higher_is_better)
                    if improved:
                        best, improvements = score, improvements + 1
                    delta = IMPROVE_DEPOSIT if improved else MISS_DEPOSIT
                    engine.done.add(chosen.task_id)
                    # No deposit on the task just completed: it is no longer a
                    # candidate, so its own concentration cannot steer anything.
                    # Only the neighbourhood of *untried* configs is marked.
                    engine._spread(chosen.task_id, delta)
                    engine.router.reinforce(worker, chosen, success=improved)
            if target is not None and units_to_target is None:
                if (task.higher_is_better and best >= target) or \
                   (not task.higher_is_better and best <= target):
                    units_to_target = tried
    finally:
        engine.close()
    return RealEpisodeStats("MorphSwarm", task.task_id, float(best), tried, dup,
                            improvements, completed=tried > 0,
                            units_to_target=units_to_target)


def run_real_central(task: LocalTask, budget: int, workers: int = 4, seed: int = 0,
                     kills: int = 0) -> EpisodeStats:
    """Central planner with a genuine single point of failure.

    Every experiment serialises through the planner. When the planner is killed
    the run stops immediately - executed, not asserted.
    """
    rng = random.Random(seed)
    seen: set = set()
    tried = dup = improvements = 0
    best = _init_best(task)
    planner_alive = True
    for step in range(budget):
        if kills and step == budget // 2:
            planner_alive = False  # central node dies -> nobody can re-plan
        if not planner_alive:
            break
        cfg = None
        for _attempt in range(20):
            cand = rng.choice(task.config_space)
            if tuple(sorted(cand.items())) not in seen:
                cfg = cand
                break
        if cfg is None:
            cfg = rng.choice(task.config_space)
        if tuple(sorted(cfg.items())) in seen:
            dup += 1
        seen.add(tuple(sorted(cfg.items())))
        tried += 1
        score = task.evaluate(cfg)
        if _better(score, best, task.higher_is_better):
            best, improvements = score, improvements + 1
    return EpisodeStats("CentralScheduler", task.task_id, float(best), tried, dup,
                        improvements, completed=planner_alive and tried > 0)


def run_no_coordination(task: LocalTask, budget: int, seed: int = 0) -> EpisodeStats:
    """SB-03 baseline: same number of fits, no ledger / field / router."""
    rng = random.Random(seed)
    tried = improvements = 0
    best = _init_best(task)
    for _ in range(budget):
        score = task.evaluate(rng.choice(task.config_space))
        tried += 1
        if _better(score, best, task.higher_is_better):
            best, improvements = score, improvements + 1
    return EpisodeStats("NoCoordination", task.task_id, float(best), tried, 0,
                        improvements, completed=tried > 0)


def measure_coordination_overhead(task: LocalTask, budget: int, seed: int = 0,
                                  workers: int = 4) -> Dict[str, float]:
    """SB-03 measured, not assumed: real swarm wall-clock vs no-coordination."""
    t0 = time.perf_counter()
    run_no_coordination(task, budget, seed=seed)
    base_wall = time.perf_counter() - t0

    t1 = time.perf_counter()
    run_real_swarm(task, budget, workers=workers, seed=seed)
    swarm_wall = time.perf_counter() - t1

    overhead = (swarm_wall - base_wall) / base_wall if base_wall > 0 else float("nan")
    return {"base_wall_seconds": round(base_wall, 4),
            "swarm_wall_seconds": round(swarm_wall, 4),
            "overhead_ratio": round(overhead, 4)}


def fault_tolerance_experiment(task: LocalTask, workers: int = 4, kills: int = 2,
                               budget: int = 20, seed: int = 0) -> Dict[str, float]:
    """SB-01: kill workers in the real engine; kill the planner in the central one."""
    swarm = run_real_swarm(task, budget, workers=workers, kills=kills, seed=seed)
    central = run_real_central(task, budget, workers=workers, kills=kills, seed=seed)
    return {
        "swarm_survival": 1.0 if swarm.completed else 0.0,
        "swarm_best_val": round(swarm.best_val, 6),
        "swarm_units_used": swarm.units_used,
        "central_survival": 1.0 if central.completed else 0.0,
        "central_best_val": round(central.best_val, 6),
        "central_units_used": central.units_used,
    }


def _shifted_task(task: LocalTask, seed: int) -> LocalTask:
    """Same search space, perturbed surface: remembered scores stop transferring,
    but which regions are promising still does."""
    rng = random.Random(seed)
    jitter = {i: rng.uniform(-1.0, 1.0) for i in range(len(task.config_space))}

    def evaluate(cfg):
        # Additive and symmetric in the metric's own units. A multiplicative
        # factor would silently invert meaning for negative metrics such as
        # BM-05's -val_bpb (factor < 1 makes a worse score look better).
        raw = float(task.evaluate(cfg))
        eps = 0.06 * abs(raw) if raw != 0.0 else 0.06
        return raw + jitter.get(_index_of(task.config_space, cfg), 0.0) * eps

    return LocalTask(f"{task.task_id}-shift", task.config_space, evaluate, evaluate,
                     task.higher_is_better)


def _index_of(space, cfg) -> int:
    key = tuple(sorted(cfg.items()))
    for i, c in enumerate(space):
        if tuple(sorted(c.items())) == key:
            return i
    return -1


def experience_reuse_experiment(task: LocalTask, workers: int = 4, budget: int = 24,
                                seed: int = 0) -> Dict[str, float]:
    """SB-02, rebuilt so it is not tautological.

    The shipped version asked "can a warm ledger re-reach a score it already
    remembers" - always 100%. Here:

      * round 2 runs on a *perturbed* instance of the same space, so remembered
        scores are worthless, but the learned landscape (pheromone + pipe
        history, copied from round 1) still transfers;
      * the target is the quality a **cold** full-budget run reaches on that same
        perturbed instance;
      * gain = fraction of the cold run's budget the warm run saves reaching it.
    """
    shifted = _shifted_task(task, seed + 7919)
    sid = f"reuse-{task.task_id}-s{seed}"

    # Reference quality: cold run on the perturbed instance, full budget.
    ref = run_real_swarm(shifted, budget, workers=workers, seed=seed,
                         swarm_id=f"{sid}-ref")
    target = ref.best_val

    # Round 1 on the ORIGINAL instance; its pheromone DB is what carries over.
    warm_root = Path(tempfile.mkdtemp(prefix="morphbench-warm-"))
    r1 = run_real_swarm(task, budget, workers=workers, seed=seed,
                        swarm_id=f"{sid}-r1", root=warm_root, persist=True)
    carried = warm_root / FIELD_NAME

    cold = run_real_swarm(shifted, budget, workers=workers, seed=seed, target=target,
                          swarm_id=f"{sid}-cold")
    warm = run_real_swarm(shifted, budget, workers=workers, seed=seed, target=target,
                          swarm_id=f"{sid}-warm", reuse_field_from=carried)
    shutil.rmtree(warm_root, ignore_errors=True)

    cold_units = cold.units_to_target if cold.units_to_target is not None else budget
    warm_units = warm.units_to_target if warm.units_to_target is not None else budget
    gain = (cold_units - warm_units) / cold_units if cold_units > 0 else 0.0
    return {
        "target": round(float(target), 6),
        "round1_units": r1.units_used,
        "cold_units_to_target": cold_units,
        "warm_units_to_target": warm_units,
        "reuse_gain": round(max(0.0, gain), 4),
        "note": "perturbed instance; cold vs warm field, same target",
    }
