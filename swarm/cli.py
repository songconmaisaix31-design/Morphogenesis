"""Executable offline swarm mode. Each worker senses its own neighborhood."""

from __future__ import annotations

import argparse
import json
import multiprocessing
from pathlib import Path
import sys
import time

from pydantic import JsonValue


def fixture_policy(max_cost_usd: float) -> dict[str, JsonValue]:
    return {"max_cost_usd": max_cost_usd, "prices": {
        "provider": "local", "model": "fixture", "input_usd_per_million": 1,
        "output_usd_per_million": 1}}


def seed_demo(directory: Path) -> tuple[Path, Path]:
    """Seed environmental observations once, before any independent worker exists."""
    from local_assets.paths import git
    from local_assets.models import FileExpectation, ValidationPolicy
    from swarm.models import Signal
    from swarm.pheromone import PheromoneField
    from swarm.task_ledger import TaskLedger
    from swarm.worker_loop import check_state_path

    directory = check_state_path(directory)
    if directory.exists():
        raise ValueError("demo_directory_must_be_new")
    target, state = directory / "local-workspace", directory / "state"
    target.mkdir(parents=True)
    git(target, "init", "-b", "swarm-local-demo")
    for number in range(6):
        seed_path = target / f"module_{number // 2}" / f"task_{number}.py"
        seed_path.parent.mkdir(exist_ok=True)
        seed_path.write_bytes(b"def answer():\n    return -1\n")
    git(target, "add", "--", "module_0", "module_1", "module_2")
    git(target, "-c", "user.name=Local Swarm Fixture", "-c", "user.email=fixture@localhost",
        "commit", "-m", "Seed six broken local fixture functions")
    ledger = TaskLedger(state / "tasks.sqlite3", "local-fixture")
    field = PheromoneField(state / "field.sqlite3", ledger=ledger)
    for number in range(6):
        module = f"module_{number // 2}"
        path = f"{module}/task_{number}.py"
        before = (target / path).read_bytes().decode("utf-8")
        # The fixed acceptance is seeded independently of future candidate output.
        expected = f"def answer():\n    return {number}\n"
        policy = ValidationPolicy(version="fixture-files-v1", expectations=(
            FileExpectation(path=path, content=expected),))
        signal = Signal(task_id=f"fixture-{number}", signal_id=f"fixture-{number}",
                        workspace=str(target), scope=module, module=module, kind="error_pattern",
                        payload={"changes": [{"path": path, "before": before, "after": expected}]})
        ledger.enqueue(signal, acceptance={"validation_policy": policy.model_dump(mode="json")})
        field.deposit(signal)
    return target, state


def demo_config(target: Path, state: Path, instance: int, max_cost_usd: float) -> str:
    from contracts.identity import AgentId
    from swarm.models import BudgetPolicy, Locality
    from swarm.worker_loop import WorkerConfig

    return WorkerConfig(state=state, target=target, agent=AgentId(role="builder", instance=instance),
                        locality=Locality(workspace=str(target), authorized_scopes=(f"module_{instance}",),
                                          modules=(f"module_{instance}",)),
                        budget=BudgetPolicy.model_validate(fixture_policy(max_cost_usd)),
                        seed=instance).model_dump_json()


def process_worker(config_json: str) -> None:
    from swarm.worker_loop import Worker, WorkerConfig
    result = Worker(WorkerConfig.model_validate_json(config_json)).run()
    if result.get("state") in {"stopped", "needs_review"}:
        raise SystemExit(1)


def demo(directory: Path, *, max_cost_usd: float, resume: bool = False) -> dict[str, JsonValue]:
    from swarm.observer import observe, read_records
    from swarm.worker_loop import check_state_path

    directory = check_state_path(directory)
    target, state = ((directory / "local-workspace", directory / "state") if resume
                     else seed_demo(directory))
    context = multiprocessing.get_context("spawn")
    processes = [context.Process(target=process_worker,
                 args=(demo_config(target, state, i, max_cost_usd),)) for i in range(3)]
    try:
        for process in processes:
            process.start()
        deadline = time.monotonic() + 180
        for process in processes:
            process.join(timeout=max(0, deadline - time.monotonic()))
        codes: list[JsonValue] = [process.exitcode for process in processes]
        records = read_records(state / "audit", limit=1000).get("records")
        completed = sum(1 for row in records if isinstance(row, dict) and row.get("outcome") == "promoted") \
            if isinstance(records, list) else 0
        return {"process_exitcodes": codes, "state_directory": str(state), "view": observe(state),
                "completed_tasks": completed, "evidence_class": "contract_local", "provenance": "mock"}
    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    view = sub.add_parser("observe", help="read existing health/evidence without modifying it")
    view.add_argument("--state", type=Path, required=True)
    view.add_argument("--limit", type=int, default=200)
    seed = sub.add_parser("seed-demo", help="create six local fixture observations; starts no workers")
    seed.add_argument("--directory", type=Path, required=True)
    demonstration = sub.add_parser("demo", help="run three independent offline fixture processes")
    demonstration.add_argument("--directory", type=Path, required=True)
    demonstration.add_argument("--max-cost-usd", type=float, required=True)
    demonstration.add_argument("--resume", action="store_true")
    worker = sub.add_parser("worker", help="one local worker, suitable for independent terminals")
    worker.add_argument("--state", type=Path, required=True)
    worker.add_argument("--target", type=Path, required=True)
    worker.add_argument("--instance", type=int, required=True)
    worker.add_argument("--scope", action="append", required=True,
                        help="authorized backend path relative to target; repeat for multiple scopes")
    worker.add_argument("--module", action="append", default=[])
    worker.add_argument("--swarm-id", default="local-fixture")
    worker.add_argument("--max-cost-usd", type=float, required=True)
    worker.add_argument("--max-tokens", type=int, default=20000)
    worker.add_argument("--energy", type=int, default=20)
    worker.add_argument("--executor", choices=["fixture"], required=True)
    args = parser.parse_args(argv)
    try:
        result: JsonValue
        if args.command == "observe":
            from swarm.observer import observe
            result = observe(args.state, limit=args.limit)
        elif args.command == "seed-demo":
            target, state = seed_demo(args.directory)
            result = {"target": str(target), "state": str(state), "provenance": "mock"}
        elif args.command == "demo":
            result = demo(args.directory, max_cost_usd=args.max_cost_usd, resume=args.resume)
        else:
            from contracts.identity import AgentId
            from swarm.models import BudgetPolicy, Locality
            from swarm.worker_loop import Worker, WorkerConfig
            policy = fixture_policy(args.max_cost_usd)
            policy["max_tokens"] = args.max_tokens
            config = WorkerConfig(state=args.state, target=args.target,
                                  agent=AgentId(role="builder", instance=args.instance),
                                  locality=Locality(workspace=str(args.target.resolve()),
                                                    authorized_scopes=tuple(args.scope), modules=tuple(args.module)),
                                  budget=BudgetPolicy.model_validate(policy), energy=args.energy,
                                  swarm_id=args.swarm_id)
            result = Worker(config).run()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if isinstance(result, dict) and "process_exitcodes" in result:
            count = result.get("completed_tasks")
            return 0 if result["process_exitcodes"] == [0, 0, 0] and isinstance(count, int) and count >= 6 else 1
        if isinstance(result, dict) and result.get("state") in {"stopped", "needs_review"}:
            return 1
        return 0
    except (ValueError, OSError):
        # Fixed text prevents data/credentials from validation exceptions leaking.
        print("swarm_configuration_or_local_io_failed", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
