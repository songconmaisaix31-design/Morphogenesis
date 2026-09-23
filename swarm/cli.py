"""Executable offline swarm mode. Each worker senses its own neighborhood."""

from __future__ import annotations

import argparse
import json
import multiprocessing
from pathlib import Path
import sys
import time

from pydantic import BaseModel, ConfigDict, JsonValue, TypeAdapter, model_validator
from typing import Self

from swarm.models import BudgetPolicy
from swarm.evomap_executor import EvoMapConfig


class EvoMapRun(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    directory: Path
    swarm_id: str = "evomap-data-v02"
    api: EvoMapConfig
    budget: BudgetPolicy

    @model_validator(mode="after")
    def bounded_experiment(self) -> Self:
        limits = self.budget.limits
        if (limits.max_tasks != 6 or limits.max_attempts != 6 or limits.max_attempts_per_task != 1
                or limits.max_derived_tasks != 0 or limits.max_runtime_seconds > 900):
            raise ValueError("evomap_requires_six_single_attempt_tasks_no_derivation_max900s")
        if (self.budget.admission_control != "enabled" or self.budget.unbounded_reservation_usd is None
                or self.api.max_input_bytes + self.api.max_output_tokens > self.budget.max_tokens):
            raise ValueError("evomap_requires_explicit_unbounded_admission")
        if self.budget.prices is not None and (
            self.budget.prices.provider != "evomap" or self.budget.prices.model != self.api.model
        ):
            raise ValueError("evomap_matching_prices_required")
        return self


def seed_evomap(config: EvoMapRun) -> tuple[Path, Path]:
    """Six data algorithms; oracles live only in immutable acceptance records."""
    from collections import Counter
    from local_assets.models import FileExpectation, ValidationPolicy
    from local_assets.paths import git
    from swarm.evomap_executor import canonical_answer
    from swarm.models import Signal
    from swarm.pheromone import PheromoneField
    from swarm.task_ledger import TaskLedger
    from swarm.worker_loop import check_state_path

    directory = check_state_path(config.directory)
    if directory.exists():
        raise ValueError("experiment_directory_must_be_new")
    target, state = directory / "local-workspace", directory / "state"
    target.mkdir(parents=True)
    git(target, "init", "-b", "swarm-local-data")
    values = [9, -2, 5, 9, 0, 3]
    words = ["pear", "apple", "pear", "fig", "apple"]
    # The third task uses a mature standard-library heap operation.
    import heapq
    tasks = TypeAdapter(list[tuple[str, str, str, JsonValue, JsonValue]]).validate_python([
        ("module_0", "module_0", "Sort the integer input in ascending order, preserving duplicates.", values, sorted(values)),
        ("module_1", "module_1", "Remove repeated strings, preserving their first-occurrence order.", words, list(dict.fromkeys(words))),
        ("module_2", "module_2", "Return the three smallest integers in ascending order, preserving duplicates.", values, heapq.nsmallest(3, values)),
        ("module_0", "module_0", "Return the sum of the integer input as a JSON integer.", values, sum(values)),
        ("module_1", "module_1", "Return an object mapping each string to its occurrence count.", words, dict(Counter(words))),
        ("module_0", "reuse", "Sort the integer input in ascending order, preserving duplicates. Use the supplied approved result when applicable.", values, sorted(values)),
    ])
    for number, (scope, _, _, _, _) in enumerate(tasks):
        initial_path = target / scope / f"result_{number}.json"
        initial_path.parent.mkdir(exist_ok=True)
        initial_path.write_text("null\n", encoding="utf-8", newline="\n")
    git(target, "add", "--", "module_0", "module_1", "module_2")
    git(target, "-c", "user.name=Local Swarm Data", "-c", "user.email=data@localhost",
        "commit", "-m", "Seed bounded JSON algorithm inputs")
    ledger = TaskLedger(state / "tasks.sqlite3", config.swarm_id, limits=config.budget.limits)
    field = PheromoneField(state / "field.sqlite3", ledger=ledger)
    for number, (scope, module, instruction, incoming, expected) in enumerate(tasks):
        path = f"{scope}/result_{number}.json"
        payload: dict[str, JsonValue] = {"instruction": instruction, "input": incoming, "output_path": path}
        dependencies: tuple[str, ...] = ()
        if number == 5:
            dependencies = ("data-0",)
            payload.update({"reuse_task_id": "data-0", "path_map": {"module_0/result_0.json": path}})
        policy = ValidationPolicy(version="bounded-json-oracle-v1", expectations=(
            FileExpectation(path=path, content=canonical_answer(expected)),))
        signal = Signal(task_id=f"data-{number}", signal_id=f"data-{number}", workspace=str(target),
                        scope=scope, module=module, kind="opportunity", required_capability="data", payload=payload)
        ledger.enqueue(signal, dependencies=dependencies, acceptance={"validation_policy": policy.model_dump(mode="json")})
        field.deposit(signal)
    return target, state


def evomap_worker_config(config: EvoMapRun, instance: int) -> str:
    from contracts.identity import AgentId
    from swarm.models import Locality
    from swarm.worker_loop import WorkerConfig
    target = (config.directory / "local-workspace").resolve()
    return WorkerConfig(state=config.directory / "state", target=target,
                        agent=AgentId(role="builder", instance=instance), swarm_id=config.swarm_id,
                        locality=Locality(workspace=str(target),
                            authorized_scopes=("module_2", "module_0") if instance == 2 else (f"module_{instance}",),
                            modules=("module_2", "reuse") if instance == 2 else (f"module_{instance}",)),
                        budget=config.budget, capabilities={"data": 1.0}, seed=instance, max_idle=100, energy=150,
                        lease_seconds=min(300, config.budget.limits.max_runtime_seconds)).model_dump_json()


def _evomap_process(config_json: str, worker_json: str) -> None:
    from swarm.evomap_executor import EvoMapExecutor
    from swarm.worker_loop import Worker, WorkerConfig
    config = EvoMapRun.model_validate_json(config_json)
    executor = EvoMapExecutor(config.api)
    result = Worker(WorkerConfig.model_validate_json(worker_json), executor).run()
    if result.get("state") in {"stopped", "needs_review"}:
        raise SystemExit(1)


def evomap_experiment(config: EvoMapRun, *, resume: bool = False) -> dict[str, JsonValue]:
    from swarm.evomap_executor import EvoMapExecutor
    from swarm.observer import observe, read_records
    from swarm.worker_loop import check_state_path
    # Check environment and the explicitly named path, never read its contents.
    executor = EvoMapExecutor(config.api)
    executor.check_paths(config.directory / "local-workspace", config.directory)
    from local_assets.paths import no_links
    no_links(config.api.credential_file)
    if not config.api.credential_file.is_file():
        raise ValueError("credential_file_unavailable")
    directory = check_state_path(config.directory)
    _, state = (directory / "local-workspace", directory / "state") if resume else seed_evomap(config)
    context = multiprocessing.get_context("spawn")
    workers = [context.Process(target=_evomap_process,
               args=(config.model_dump_json(), evomap_worker_config(config, i))) for i in range(3)]
    try:
        for process in workers:
            process.start()
        deadline = time.monotonic() + config.budget.limits.max_runtime_seconds + 10
        for process in workers:
            process.join(max(0, deadline - time.monotonic()))
        events = read_records(state / "audit", limit=1000).get("records")
        rows = [row for row in events if isinstance(row, dict)] if isinstance(events, list) else []
        view = observe(state)
        summary = evomap_acceptance(rows, view)
        return {"process_exitcodes": [process.exitcode for process in workers], **summary,
                "state_directory": str(state), "provenance": "live", "evidence_class": "interface_live",
                "task_scope": "bounded_json_data_only", "max_requests": 6, "view": view}
    finally:
        for process in workers:
            if process.is_alive():
                process.terminate()
                process.join(5)


def evomap_acceptance(rows: list[dict[str, JsonValue]], view: dict[str, JsonValue]) -> dict[str, JsonValue]:
    accepted = [row for row in rows if row.get("provenance") == "live" and row.get("outcome") == "promoted"
                and row.get("task_live") == "passed"]
    participants: dict[str, JsonValue] = {}
    for row in accepted:
        worker = row.get("worker_id")
        if isinstance(worker, str):
            previous = participants.get(worker, 0)
            participants[worker] = previous + 1 if isinstance(previous, int) else 1
    pids = {row["pid"] for row in accepted if isinstance(row.get("pid"), int)}
    tasks = {row["task_id"] for row in accepted if isinstance(row.get("task_id"), str)}
    sections = view.get("sections")
    validation = sections.get("validation") if isinstance(sections, dict) else None
    tables = validation.get("tables") if isinstance(validation, dict) else None
    adoptions = tables.get("adoptions") if isinstance(tables, dict) else None
    cross_member = 0
    if isinstance(adoptions, list):
        for adoption_row in adoptions:
            body = adoption_row.get("body") if isinstance(adoption_row, dict) else None
            if not isinstance(body, dict):
                continue
            context = body.get("context")
            if not isinstance(context, dict):
                continue
            source = next((r for r in accepted if r.get("asset_id") == body.get("asset_id")), None)
            target = next((r for r in accepted if r.get("result_id") == body.get("result_id")
                           and r.get("task_id") == context.get("task_id")
                           and r.get("worker_id") == context.get("worker_id")
                           and r.get("consumed_asset_ids") == [body.get("asset_id")]), None)
            if source and target and source.get("worker_id") != target.get("worker_id"):
                cross_member += 1
    interface = any(row.get("provenance") == "live" and row.get("interface_live") == "passed" for row in rows)
    passed = len(tasks) >= 5 and len(pids) == 3 and len(participants) == 3 and cross_member > 0
    return {"completed_tasks": len(tasks), "participation": participants, "independent_pids": len(pids),
            "cross_member_adoptions": cross_member, "interface_live": "passed" if interface else "not_run",
            "task_live": "passed" if passed else "blocked" if rows else "not_run"}


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
    api = sub.add_parser("evomap", help="three independent EvoMap workers; explicit data-task configuration")
    api.add_argument("--config", type=Path, required=True, help="JSON configuration; credentials are file paths only")
    api.add_argument("--resume", action="store_true", help="resume the same durable run without retrying prior requests")
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
        elif args.command == "evomap":
            result = evomap_experiment(EvoMapRun.model_validate_json(args.config.read_bytes()), resume=args.resume)
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
            return 0 if (result["process_exitcodes"] == [0, 0, 0] and isinstance(count, int) and count >= 6
                         and result.get("task_live", "passed") == "passed") else 1
        if isinstance(result, dict) and result.get("state") in {"stopped", "needs_review"}:
            return 1
        return 0
    except (ValueError, OSError):
        # Fixed text prevents data/credentials from validation exceptions leaking.
        print("swarm_configuration_or_local_io_failed", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
