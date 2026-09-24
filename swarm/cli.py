"""Executable offline swarm mode. Each worker senses its own neighborhood."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import multiprocessing
from pathlib import Path
import re
import sys
import time

from pydantic import BaseModel, ConfigDict, JsonValue, TypeAdapter, model_validator
from typing import Self

from swarm.models import BudgetPolicy
from swarm.evomap_executor import EvoMapConfig, EvoMapTextModel


class EvoMapRun(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    directory: Path
    swarm_id: str = "evomap-data-v02"
    api: EvoMapConfig
    budget: BudgetPolicy
    workers: int = 3
    tasks: int = 6
    worker_models: tuple[EvoMapTextModel, ...] = ()
    capability_names: tuple[str, ...] = ()
    continue_on_rejection: bool = False

    @model_validator(mode="after")
    def bounded_experiment(self) -> Self:
        limits = self.budget.limits
        if (self.workers, self.tasks) not in {(3, 6), (8, 48), (16, 96)}:
            raise ValueError("evomap_scale_must_be_3x6_8x48_or_16x96")
        if self.worker_models and len(self.worker_models) != self.workers:
            raise ValueError("worker_models_must_match_worker_count")
        if (len(self.capability_names) > 16 or len(set(self.capability_names)) != len(self.capability_names)
                or any(not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", name) for name in self.capability_names)):
            raise ValueError("capability_names_must_be_unique_bounded_identifiers")
        if (limits.max_tasks != self.tasks or limits.max_attempts != self.tasks or limits.max_attempts_per_task != 1
                or limits.max_derived_tasks != 0 or limits.max_runtime_seconds > 900):
            raise ValueError("evomap_requires_one_attempt_per_task_no_derivation_max900s")
        if (self.budget.admission_control != "enabled" or self.budget.unbounded_reservation_usd is None
                or self.api.max_input_bytes + self.api.max_output_tokens > self.budget.max_tokens):
            raise ValueError("evomap_requires_explicit_unbounded_admission")
        effective_models = set(self.worker_models or (self.api.model,))
        if self.budget.prices is not None and (self.budget.prices.provider != "evomap"
                or effective_models != {self.budget.prices.model}):
            raise ValueError("evomap_matching_prices_required")
        return self


def seed_evomap(config: EvoMapRun) -> tuple[Path, Path]:
    """Deterministic diverse data tasks; oracles live only in acceptance records."""
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
    import heapq
    tasks: list[tuple[str, str, str, JsonValue, JsonValue]] = []
    for number in range(config.tasks):
        module_number = number % config.workers
        values = [((number + 3) * factor) % 29 - 14 for factor in (7, 2, 11, 5, 7, 3)]
        words = [f"item-{(number + offset * offset) % 7}" for offset in range(7)]
        operation = number % 5
        task: tuple[str, JsonValue, JsonValue]
        if operation == 0:
            task = ("Sort the integer input in ascending order, preserving duplicates.",
                    TypeAdapter(JsonValue).validate_python(values),
                    TypeAdapter(JsonValue).validate_python(sorted(values)))
        elif operation == 1:
            task = ("Remove repeated strings, preserving their first-occurrence order.",
                    TypeAdapter(JsonValue).validate_python(words),
                    TypeAdapter(JsonValue).validate_python(list(dict.fromkeys(words))))
        elif operation == 2:
            task = (
                "Return the three smallest integers in ascending order, preserving duplicates.",
                TypeAdapter(JsonValue).validate_python(values),
                TypeAdapter(JsonValue).validate_python(heapq.nsmallest(3, values)))
        elif operation == 3:
            task = ("Return the sum of the integer input as a JSON integer.",
                    TypeAdapter(JsonValue).validate_python(values), sum(values))
        else:
            task = ("Return an object mapping each string to its occurrence count.",
                    TypeAdapter(JsonValue).validate_python(words),
                    TypeAdapter(JsonValue).validate_python(dict(Counter(words))))
        instruction: str = task[0]
        incoming: JsonValue = task[1]
        expected: JsonValue = task[2]
        tasks.append((f"module_{module_number}", f"module_{module_number}", instruction, incoming, expected))
    # The final task must use data-0's exact result, so its independent model
    # response can prove approved cross-member reuse rather than mere injection.
    source_values = [((0 + 3) * factor) % 29 - 14 for factor in (7, 2, 11, 5, 7, 3)]
    tasks[-1] = ("module_0", "reuse", "Sort the integer input in ascending order, preserving duplicates. "
                  "Use the supplied approved result when applicable.",
                  TypeAdapter(JsonValue).validate_python(source_values),
                  TypeAdapter(JsonValue).validate_python(sorted(source_values)))
    for number, (scope, _, _, _, _) in enumerate(tasks):
        initial_path = target / scope / f"result_{number}.json"
        initial_path.parent.mkdir(exist_ok=True)
        initial_path.write_text("null\n", encoding="utf-8", newline="\n")
    git(target, "add", "--", *(f"module_{number}" for number in range(config.workers)))
    git(target, "-c", "user.name=Local Swarm Data", "-c", "user.email=data@localhost",
        "commit", "-m", "Seed bounded JSON algorithm inputs")
    ledger = TaskLedger(state / "tasks.sqlite3", config.swarm_id, limits=config.budget.limits)
    field = PheromoneField(state / "field.sqlite3", ledger=ledger)
    for number, (scope, module, instruction, incoming, expected) in enumerate(tasks):
        path = f"{scope}/result_{number}.json"
        payload: dict[str, JsonValue] = {"instruction": instruction, "input": incoming, "output_path": path}
        dependencies: tuple[str, ...] = ()
        if number == config.tasks - 1:
            dependencies = ("data-0",)
            payload.update({"reuse_task_id": "data-0", "path_map": {"module_0/result_0.json": path}})
        policy = ValidationPolicy(version="bounded-json-oracle-v1", expectations=(
            FileExpectation(path=path, content=canonical_answer(expected)),))
        capability = ("data_sort", "data_dedup", "data_topk", "data_sum", "data_count")[number % 5]
        if number == config.tasks - 1:
            capability = "data_sort"
        signal = Signal(task_id=f"data-{number}", signal_id=f"data-{number}", workspace=str(target),
                        scope=scope, module=module, kind="opportunity",
                        required_capability=capability, payload=payload)
        ledger.enqueue(signal, dependencies=dependencies, acceptance={"validation_policy": policy.model_dump(mode="json")})
        field.deposit(signal)
    return target, state


def evomap_worker_config(config: EvoMapRun, instance: int) -> str:
    from contracts.identity import AgentId
    from swarm.models import Locality
    from swarm.worker_loop import WorkerConfig
    target = (config.directory / "local-workspace").resolve()
    previous = (instance - 1) % config.workers
    scopes: tuple[str, ...] = (f"module_{instance}", f"module_{previous}")
    modules: tuple[str, ...] = (f"module_{instance}", f"module_{previous}")
    if instance == config.workers - 1:
        scopes = (*scopes, "module_0")
        modules = (*modules, "reuse")
    authorized_modules = {int(scope.removeprefix("module_")) for scope in scopes}
    if config.capability_names:
        capabilities = {name: 1.0 for name in config.capability_names}
    else:
        # Every worker can execute the operation classes present in either authorized module.
        capabilities = {("data_sort", "data_dedup", "data_topk", "data_sum", "data_count")[task % 5]: 1.0
                        for task in range(config.tasks)
                        if task % config.workers in authorized_modules}
        if instance == config.workers - 1:
            capabilities["data_sort"] = 1.0
    return WorkerConfig(state=config.directory / "state", target=target,
                        agent=AgentId(role="builder", instance=instance), swarm_id=config.swarm_id,
                        locality=Locality(workspace=str(target),
                            authorized_scopes=scopes, modules=modules),
                        budget=config.budget, capabilities=capabilities, seed=instance, max_idle=100, energy=150,
                        lease_seconds=min(300, config.budget.limits.max_runtime_seconds),
                        continue_on_rejection=config.continue_on_rejection).model_dump_json()


def _evomap_process(config_json: str, worker_json: str, instance: int) -> None:
    from swarm.evomap_executor import EvoMapExecutor
    from swarm.worker_loop import Worker, WorkerConfig
    config = EvoMapRun.model_validate_json(config_json)
    model = config.worker_models[instance] if config.worker_models else config.api.model
    executor = EvoMapExecutor(config.api.model_copy(update={"model": model}))
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
               args=(config.model_dump_json(), evomap_worker_config(config, i), i)) for i in range(config.workers)]
    try:
        for process in workers:
            process.start()
        deadline = time.monotonic() + config.budget.limits.max_runtime_seconds + 10
        for process in workers:
            process.join(max(0, deadline - time.monotonic()))
        events = read_records(state / "audit", limit=1000).get("records")
        rows = [row for row in events if isinstance(row, dict)] if isinstance(events, list) else []
        view = observe(state)
        summary = evomap_acceptance(rows, view, expected_workers=config.workers, expected_tasks=config.tasks)
        return {"process_exitcodes": [process.exitcode for process in workers], **summary,
                "state_directory": str(state), "provenance": "live", "evidence_class": "interface_live",
                "task_scope": "bounded_json_data_only", "max_requests": config.tasks,
                "configured_workers": config.workers, "configured_tasks": config.tasks, "view": view}
    finally:
        for process in workers:
            if process.is_alive():
                process.terminate()
                process.join(5)


def evomap_acceptance(rows: list[dict[str, JsonValue]], view: dict[str, JsonValue], *,
                      expected_workers: int = 3, expected_tasks: int = 6) -> dict[str, JsonValue]:
    accepted = [row for row in rows if row.get("provenance") == "live" and row.get("outcome") == "promoted"
                and row.get("task_live") == "passed"]
    participants: dict[str, JsonValue] = {}
    for row in accepted:
        worker = row.get("worker_id")
        if isinstance(worker, str):
            previous = participants.get(worker, 0)
            participants[worker] = previous + 1 if isinstance(previous, int) else 1
    pids = {row["pid"] for row in accepted if isinstance(row.get("pid"), int)}
    tasks = {str(row["task_id"]) for row in accepted if isinstance(row.get("task_id"), str)}
    sections = view.get("sections")
    validation = sections.get("validation") if isinstance(sections, dict) else None
    tables = validation.get("tables") if isinstance(validation, dict) else None
    adoptions = tables.get("adoptions") if isinstance(tables, dict) else None
    cross_member = 0
    lineage: list[JsonValue] = []
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
                lineage.append({"asset_id": body.get("asset_id"), "source_task": source.get("task_id"),
                                "source_worker": source.get("worker_id"), "target_task": target.get("task_id"),
                                "target_worker": target.get("worker_id")})
    interface = any(row.get("provenance") == "live" and row.get("interface_live") == "passed" for row in rows)
    latencies: list[float] = []
    request_usage: dict[str, int | None] = {}
    for row in rows:
        execution = row.get("execution")
        latency = execution.get("elapsed_seconds") if isinstance(execution, dict) else None
        if isinstance(latency, (int, float)) and not isinstance(latency, bool):
            latencies.append(float(latency))
        request_id = execution.get("request_id") if isinstance(execution, dict) else None
        usage = row.get("usage")
        if isinstance(request_id, str) and request_id not in request_usage:
            tokens = usage.get("total_tokens") if isinstance(usage, dict) else None
            request_usage[request_id] = (tokens if isinstance(tokens, int)
                                         and not isinstance(tokens, bool) else None) if isinstance(usage, dict) else None
    known_tokens = [tokens for tokens in request_usage.values() if tokens is not None]
    budget = sections.get("budget") if isinstance(sections, dict) else None
    budget_tables = budget.get("tables") if isinstance(budget, dict) else None
    reservations = budget_tables.get("budget_reservations") if isinstance(budget_tables, dict) else None
    reservation_rows = [row for row in reservations if isinstance(row, dict)] if isinstance(reservations, list) else []
    durable_tokens: list[int] = []
    for reservation_row in reservation_rows:
        durable_token = reservation_row.get("tokens")
        if isinstance(durable_token, int) and not isinstance(durable_token, bool):
            durable_tokens.append(durable_token)
    unknown_reservations = sum(row.get("usage_metering") != "verified" for row in reservation_rows)
    token_summary: dict[str, JsonValue] = {"audited_requests": len(request_usage),
        "known_requests": len(durable_tokens) if reservation_rows else len(known_tokens),
        "unknown_reservations": unknown_reservations,
        "known_total": sum(durable_tokens) if reservation_rows else sum(known_tokens),
        "total": (None if unknown_reservations else sum(durable_tokens)) if reservation_rows
                 else (None if any(tokens is None for tokens in request_usage.values()) else sum(known_tokens))}
    passed = (len(tasks) == expected_tasks and len(pids) == expected_workers
              and len(participants) == expected_workers and cross_member > 0)
    completed_task_ids = TypeAdapter(list[JsonValue]).validate_python(sorted(tasks))
    result: dict[str, JsonValue] = {"completed_tasks": len(tasks), "participation": participants, "independent_pids": len(pids),
            "unique_completed_tasks": completed_task_ids, "cross_member_adoptions": cross_member,
            "adoption_lineage": lineage, "latency_seconds": {"count": len(latencies),
                "total": sum(latencies), "minimum": min(latencies) if latencies else None,
                "maximum": max(latencies) if latencies else None},
            "tokens": token_summary,
            "stop_reasons": dict(Counter(str(row.get("outcome")) for row in rows)),
            "cost": {"estimated_usd": None, "billed_usd": None, "status": "unknown"},
            "interface_live": "passed" if interface else "not_run",
            "task_live": "passed" if passed else "blocked" if rows else "not_run"}
    return result


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
            workers_value = result.get("configured_workers", 3)
            tasks_value = result.get("configured_tasks", 6)
            expected_workers = workers_value if isinstance(workers_value, int) else 3
            expected_tasks = tasks_value if isinstance(tasks_value, int) else 6
            return 0 if (result["process_exitcodes"] == [0] * expected_workers and count == expected_tasks
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
