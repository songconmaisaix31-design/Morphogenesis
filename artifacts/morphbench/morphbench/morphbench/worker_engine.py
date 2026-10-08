"""Phase 0: run MorphBench on 0.2.1's REAL decentralized workers.

This replaces the central driver loop in ``real_swarm.run_real_swarm`` (which
did ``for step in range(budget): worker = alive[step % len(alive)]`` — a
scheduler, by any honest reading) with N independent ``swarm.worker_loop.Worker``
processes that forage the shared ``TaskLedger`` on their own.

What is real here:
  * ``swarm.worker_loop.Worker.run()`` — "Independent bounded forager"
  * ``swarm.budget.BudgetLedger``      — real budget admission + reservation
  * ``swarm.lease.LeaseManager``       — real lease acquire / renew / fence
  * ``swarm.task_ledger.TaskLedger``   — claim / submit / validation gating
  * ``swarm.router.Router`` + ``PheromoneField`` — stigmergic selection
  * validation of the execution product against an operator-seeded
    ``ValidationPolicy`` (immutable task facts, never candidate-supplied)

What is benchmark-side glue:
  * ``MorphBenchExecutor`` — the ``Executor`` protocol implementation that turns
    one Signal into one model fit. Its ``execute`` really fits the model.
  * seeding the expected score per config. The surrogate spaces are
    deterministic, so the acceptance fact can be precomputed; that makes the
    validation real instead of "accept anything".
"""
from __future__ import annotations

import json
import multiprocessing
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from contracts.identity import AgentId, AttemptId
from contracts.provenance import Provenance
from local_assets.models import Candidate, FileChange, FileExpectation, ValidationPolicy
from local_assets.paths import git, no_links, safe_join
from local_assets.validate import blast_radius, inspect_candidate
from swarm.models import BudgetPolicy, ExecutionBound, Locality, Signal
from swarm.pheromone import PheromoneField
from swarm.task_ledger import TaskLedger
from swarm.worker_loop import ExecutionResult, Worker, WorkerConfig

from . import local_tasks
from .real_swarm import _family, _payload

USAGE: dict = {"usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}
RESULT_PATH = "result.json"


def scoped_result_path(task_id: str) -> str:
    """Change path must sit inside the candidate scope, like seed_demo does
    (module_0/task_0.py within scope module_0)."""
    return f"cfg/{task_id}/result.json"


EXECUTOR_SPEC = "executor_spec.json"


def expected_content(index: int, cfg: Dict, score: float) -> str:
    return json.dumps({"index": index, "config": _payload(cfg), "score": round(float(score), 6)},
                      sort_keys=True, separators=(",", ":"))


class MorphBenchExecutor:
    """One Signal -> one real model fit -> one quarantined candidate file."""

    provenance: Provenance = "mock"
    usage_source = "fixture_mock"
    original_run_uri: str | None = None

    def __init__(self, task_id: str, space: List[Dict]) -> None:
        self.task_id = task_id
        self.space = space
        self._task = None

    @property
    def task(self):
        if self._task is None:
            self._task = local_tasks.build(self.task_id)
        return self._task

    def check_paths(self, target: Path, state: Path) -> None:
        return None

    def bound(self, signal: Signal) -> ExecutionBound:
        return ExecutionBound(
            provider="local", model="morphbench-cpu", input_tokens=1, max_output_tokens=1,
            provider_enforced=True, request_bound="verified", max_cost_usd=0.000002,
            bound_evidence="local CPU fixture: one model fit; no paid calls",
        )

    def execute(self, signal: Signal, attempt: AttemptId, repository: Path,
                directory: Path, *, base_revision: str, base_head: str,
                experience=None) -> ExecutionResult:
        index = int(signal.payload["index"])
        cfg = self.space[index]
        # The fit is real: the surrogate task is rebuilt and evaluated here.
        score = float(self.task.evaluate(cfg))
        content = expected_content(index, cfg, score)
        changes = (FileChange(path=scoped_result_path(signal.task_id), before=None, after=content),)
        candidate = Candidate(attempt=attempt, base_revision=base_revision, base_head=base_head,
                              changes=changes, declared_files=1, declared_lines=1,
                              scope=signal.scope)
        count, lines = blast_radius(candidate)
        candidate = candidate.model_copy(update={"declared_files": count, "declared_lines": lines})
        self.materialize(candidate, repository, directory)
        return ExecutionResult(candidate, USAGE, str(directory))

    @staticmethod
    def materialize(candidate: Candidate, repository: Path, directory: Path) -> None:
        inspect_candidate(candidate)
        tree = git(repository, "ls-tree", "-rz", candidate.base_revision)
        if any(item.startswith((b"120000 ", b"160000 ")) for item in tree.split(b"\0")):
            raise RuntimeError("baseline_links_or_submodules")
        no_links(directory)
        directory.parent.mkdir(parents=True, exist_ok=True)
        git(repository, "worktree", "add", "--detach", str(directory), candidate.base_revision)
        for change in candidate.changes:
            path = safe_join(directory, change.path)
            current = path.read_bytes() if path.is_file() else None
            expected = change.before.encode("utf-8") if change.before is not None else None
            if current != expected:
                raise RuntimeError("execution_preimage_mismatch")
            if change.after is None:
                path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(change.after.encode("utf-8"))


def seed_workspace(root: Path, task_id: str, swarm_id: str) -> Tuple[Path, Path]:
    """Seed a git workspace + ledger + field, one task per candidate config."""
    target, state = root / "workspace", root / "state"
    target.mkdir(parents=True, exist_ok=True)
    git(target, "init", "-b", "morphbench")
    (target / "README.md").write_text("# MorphBench task workspace\n", encoding="utf-8")
    git(target, "add", "--", "README.md")
    git(target, "-c", "user.name=MorphBench", "-c", "user.email=bench@localhost",
        "commit", "-m", "seed morphbench workspace")
    state.mkdir(parents=True, exist_ok=True)

    task = local_tasks.build(task_id)
    families = sorted({_family(c) for c in task.config_space})
    ledger = TaskLedger(state / "tasks.sqlite3", swarm_id)
    field = PheromoneField(state / "field.sqlite3", ledger=ledger)

    scores: Dict[str, float] = {}
    for i, cfg in enumerate(task.config_space):
        score = float(task.evaluate(cfg))
        scores[f"cfg-{i}"] = score
        policy = ValidationPolicy(
            version="morphbench-v1",
            expectations=(FileExpectation(path=scoped_result_path(f"cfg-{i}"),
                                          content=expected_content(i, cfg, score)),),
        )
        signal = Signal(
            task_id=f"cfg-{i}", workspace=str(target.resolve()), scope=f"cfg/cfg-{i}",
            kind="opportunity", payload={"index": i, "cfg": _payload(cfg)},
            required_capability=_family(cfg), module="morphbench",
            concentration=1.0, urgency=1.0,
        )
        ledger.enqueue(signal, acceptance={"validation_policy": policy.model_dump(mode="json")})
        field.deposit(signal)

    (state / EXECUTOR_SPEC).write_text(
        json.dumps({"task_id": task_id, "space": task.config_space, "scores": scores},
                   ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return target, state


def worker_config(target: Path, state: Path, instance: int, swarm_id: str,
                  capabilities: Dict[str, float], energy: int) -> str:
    return WorkerConfig(
        state=state, target=target, agent=AgentId(role="builder", instance=instance),
        locality=Locality(workspace=str(target.resolve()), authorized_scopes=("cfg",)),
        # Prices are keyed by (provider, model): without an entry matching the
        # ExecutionBound the reservation cost is unknown and the worker sleeps.
        budget=BudgetPolicy(max_tokens=20000, max_cost_usd=1.0,
                            burn_rate_tokens=20000, burn_window_seconds=60.0,
                            allow_unknown_usage=True,
                            prices={"provider": "local", "model": "morphbench-cpu",
                                    "input_usd_per_million": 1, "output_usd_per_million": 1}),
        swarm_id=swarm_id, capabilities=capabilities, energy=energy,
        seed=instance, max_idle=3, idle_seconds=0.05, sleep_seconds=0.05,
    ).model_dump_json()


def process_worker(config_json: str, state: str) -> None:
    spec = json.loads((Path(state) / EXECUTOR_SPEC).read_text(encoding="utf-8"))
    executor = MorphBenchExecutor(spec["task_id"], spec["space"])
    Worker(WorkerConfig.model_validate_json(config_json), executor).run()


def run_decentralized(task_id: str, workers: int = 3, energy: int = 8, seed: int = 0,
                      root: Optional[Path] = None, kills: int = 0,
                      kill_after_seconds: float = 3.0) -> Dict:
    """Run N independent Worker processes over one MorphBench task.

    No function here decides which worker acts next: each process runs
    ``Worker.run()`` and forages the shared ledger on its own.
    """
    import tempfile
    base = Path(root) if root else Path(tempfile.mkdtemp(prefix="morphbench-workers-"))
    swarm_id = f"{task_id}-w{workers}-s{seed}"
    target, state = seed_workspace(base, task_id, swarm_id)

    task = local_tasks.build(task_id)
    families = sorted({_family(c) for c in task.config_space})
    capabilities = {f: 1.0 for f in families}

    context = multiprocessing.get_context("spawn")
    configs = [worker_config(target, state, i, swarm_id, capabilities, energy)
               for i in range(workers)]
    procs = [context.Process(target=process_worker, args=(c, str(state))) for c in configs]
    started = time.perf_counter()
    for p in procs:
        p.start()
    if kills:
        time.sleep(kill_after_seconds)
        for p in procs[:kills]:
            if p.is_alive():
                p.kill()
    for p in procs:
        p.join()

    wall = time.perf_counter() - started
    ledger = TaskLedger(state / "tasks.sqlite3", swarm_id)
    records = ledger.snapshot(limit=1000)
    completed = [r for r in records if r.status == "completed"]
    # The Worker's stored `result` is the engine's own validation report, not our
    # score file. Validation already proved the produced file equals the seeded
    # expectation, so the seeded score is the value the worker actually produced.
    spec = json.loads((state / EXECUTOR_SPEC).read_text(encoding="utf-8"))
    scores: Dict[str, float] = spec.get("scores", {})
    best = None
    seen: List[float] = []
    for r in completed:
        if r.signal.task_id not in scores:
            continue
        score = float(scores[r.signal.task_id])
        seen.append(score)
        if best is None or (score > best if task.higher_is_better else score < best):
            best = score
    return {
        "task_id": task_id, "workers": workers, "energy": energy,
        "tasks_completed": len(completed), "tasks_total": len(records),
        "units_scored": len(seen),
        "best_val": best, "wall_seconds": round(wall, 3),
        "seconds_per_unit": round(wall / len(seen), 3) if seen else None,
        "kills": kills, "exit_codes": [p.exitcode for p in procs],
        "state": str(state),
    }
