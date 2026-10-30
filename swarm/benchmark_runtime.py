from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import asdict
import json
import math
import multiprocessing
from multiprocessing.connection import Connection
from multiprocessing.context import BaseContext
import os
from pathlib import Path
import re
import tempfile
from threading import Event, Thread
import time
from typing import Any, Literal, Protocol, cast

from pydantic import JsonValue

from contracts.identity import AgentId, AttemptId
from contracts.provenance import Provenance
from local_assets.models import (
    AssetSafetyError, BenchmarkOutputValidationPolicy, Candidate,
    ConsumptionExecution, FileChange,
)
from local_assets.paths import git, no_links, safe_join
from local_assets.validate import blast_radius
from swarm.benchmark_model import (
    ModelRequest, ModelResponse, SharedRequestGate, STEPFUN_MODEL, StepFunBenchmarkExecutor,
)
from swarm.budget import BudgetLedger
from swarm.models import BudgetPolicy, ExecutionBound, Locality, RunLimits, Signal
from swarm.pheromone import PheromoneField
from swarm.task_ledger import TaskLedger
from swarm.worker_loop import ExecutionResult, FixtureExecutor, Worker, WorkerConfig, check_state_path

_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]{1,160}")


class ModelLeaf(Protocol):
    provenance: Literal["live", "mock"]

    def generate_sync(self, request: ModelRequest) -> ModelResponse: ...

    def close(self) -> None: ...


ModelFactory = Callable[[str, SharedRequestGate, float], ModelLeaf]


def create_live_model(key: str, gate: SharedRequestGate, timeout_seconds: float) -> ModelLeaf:
    return StepFunBenchmarkExecutor(key, gate, timeout_seconds=timeout_seconds)


def _write_new(path: Path, value: Any) -> None:
    no_links(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open("x", encoding="utf-8") as stream:
        os.chmod(path, 0o600)
        json.dump(value, stream, ensure_ascii=False, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())


def validate_tasks(tasks: Sequence[dict[str, str]]) -> list[dict[str, str]]:
    if not 1 <= len(tasks) <= 48:
        raise ValueError("benchmark_requires_1_to_48_tasks")
    result: list[dict[str, str]] = []
    for task in tasks:
        if (not isinstance(task, dict) or set(task) != {"id", "prompt"}
                or not isinstance(task["id"], str) or _IDENTIFIER.fullmatch(task["id"]) is None
                or not isinstance(task["prompt"], str) or not task["prompt"]
                or len(task["prompt"].encode("utf-8")) > 48000):
            raise ValueError("benchmark_task_contract_invalid")
        result.append(dict(task))
    if len({task["id"] for task in result}) != len(result):
        raise ValueError("benchmark_task_ids_must_be_unique")
    return result


def budget_policy(task_count: int, runtime_seconds: float, max_tokens: int) -> BudgetPolicy:
    return BudgetPolicy(
        max_tokens=48000 + max_tokens,
        burn_rate_tokens=task_count * (48000 + max_tokens),
        max_cost_usd=float(task_count), unbounded_reservation_usd=1.0,
        # A completed response with absent metering still consumes its one finite
        # request reservation. Do not halt only this arm or fabricate zero usage.
        allow_unknown_cost=True, allow_unknown_usage=True,
        limits=RunLimits(max_tasks=task_count, max_attempts=task_count,
                         max_attempts_per_task=1, max_derived_tasks=0,
                         max_runtime_seconds=runtime_seconds),
    )


def seed_tasks(directory: Path, tasks: Sequence[dict[str, str]], *,
               run_id: str, policy: BudgetPolicy) -> tuple[Path, Path]:
    validated = validate_tasks(tasks)
    root = check_state_path(directory)
    if root.exists():
        raise ValueError("benchmark_directory_must_be_new")
    root.mkdir(parents=True, mode=0o700)
    target, state = root / "workspace", root / "state"
    target.mkdir(mode=0o700)
    state.mkdir(mode=0o700)
    git(target, "init", "-b", "benchmark-local")
    for index in range(len(validated)):
        scope_directory = target / f"task_{index:03d}"
        scope_directory.mkdir(mode=0o700)
        (scope_directory / "result.json").write_text("null\n", encoding="utf-8")
    git(target, "add", "--", ".")
    git(target, "-c", "user.name=Benchmark Local", "-c", "user.email=benchmark@localhost",
        "commit", "-m", "Seed fixed benchmark data outputs")
    ledger = TaskLedger(state / "tasks.sqlite3", run_id, limits=policy.limits)
    field = PheromoneField(state / "field.sqlite3", ledger=ledger)
    BudgetLedger(state / "budget.sqlite3", run_id, policy)
    for index, task in enumerate(validated):
        scope = f"task_{index:03d}"
        output_path = f"{scope}/result.json"
        signal = Signal(task_id=task["id"], signal_id=task["id"], workspace=str(target),
                        scope=scope, module=scope, kind="opportunity", required_capability="math",
                        payload={"prompt": task["prompt"], "output_path": output_path,
                                 "ordinal": index})
        acceptance = BenchmarkOutputValidationPolicy(path=output_path)
        ledger.enqueue(signal, acceptance={"validation_policy": acceptance.model_dump(mode="json")})
        field.deposit(signal)
    return target, state


class BenchmarkWorkerExecutor:
    original_run_uri: str | None = None

    def __init__(self, model: ModelLeaf, *, run_id: str, block_id: str,
                 seed: int, max_tokens: int, temperature: float, evidence: Path) -> None:
        self.model = model
        self.provenance: Provenance = model.provenance
        self.usage_source: Literal["fixture_mock", "provider_reported", "replay"] = (
            "provider_reported" if model.provenance == "live" else "fixture_mock")
        self.run_id, self.block_id, self.seed = run_id, block_id, seed
        self.max_tokens, self.temperature, self.evidence = max_tokens, temperature, evidence

    def check_paths(self, target: Path, state: Path) -> None:
        no_links(target)
        no_links(state)
        no_links(self.evidence)
        if self.evidence.resolve().is_relative_to(target.resolve()):
            raise AssetSafetyError("benchmark_evidence_inside_target")

    def bound(self, signal: Signal) -> ExecutionBound:
        prompt = signal.payload.get("prompt")
        if not isinstance(prompt, str) or len(prompt.encode("utf-8")) > 48000:
            raise AssetSafetyError("benchmark_prompt_invalid")
        return ExecutionBound(provider="stepfun-cn", model=STEPFUN_MODEL,
                              input_tokens=48000, max_output_tokens=self.max_tokens,
                              provider_enforced=False, request_bound="unbounded")

    def execute(self, signal: Signal, attempt: AttemptId, repository: Path, directory: Path, *,
                base_revision: str, base_head: str,
                experience: ConsumptionExecution | None = None) -> ExecutionResult:
        if experience is not None or set(signal.payload) != {"prompt", "output_path", "ordinal"}:
            raise AssetSafetyError("benchmark_has_no_adoption_or_extra_context")
        prompt, output_path, ordinal = (signal.payload[name] for name in ("prompt", "output_path", "ordinal"))
        if not isinstance(prompt, str) or not isinstance(output_path, str) or type(ordinal) is not int:
            raise AssetSafetyError("benchmark_payload_invalid")
        request = ModelRequest(run_id=self.run_id, framework="morphogenesis", block_id=self.block_id,
                               seed=self.seed, task_id=signal.task_id, prompt=prompt,
                               max_tokens=self.max_tokens, temperature=self.temperature)
        reply = self.model.generate_sync(request)
        record = {"task_id": signal.task_id, "worker_id": f"{attempt.agent.role}-{attempt.agent.instance}",
                  "pid": os.getpid(), "attempt": attempt.model_dump(mode="json"),
                  **asdict(reply)}
        # 原始模型输出先保存；后续文件验证失败不会从评分分母中移除这道题。
        evidence_path = self.evidence / f"task_{ordinal:03d}.json"
        _write_new(evidence_path, record)
        metadata = {"request_id": reply.request_id, "requested_model": STEPFUN_MODEL,
                    "returned_model": reply.evidence.get("returned_model"),
                    "http_status": reply.evidence.get("http_status"),
                    "task_kind": "benchmark_data_output", "evidence_uri": self.evidence.as_uri(),
                    "response_file": str(evidence_path), "actual_cost_usd": None,
                    "classification": "unknown_effect" if reply.status != "completed" else None,
                    "error_kind": reply.evidence.get("error_kind"),
                    "interface_live": "passed" if reply.status == "completed" and self.provenance == "live" else "not_run"}
        usage: JsonValue = {"usage": cast(JsonValue, reply.usage)} if reply.usage is not None else None
        candidate = None
        if reply.status == "completed":
            output = safe_join(repository, output_path)
            before = output.read_bytes().decode("utf-8")
            # 已知过滤终止没有正文时，存储空字符串；原始 None 和终止原因仍在评分证据中。
            after = json.dumps({"response": reply.text or ""}, ensure_ascii=False, allow_nan=False) + "\n"
            candidate = Candidate(attempt=attempt, base_revision=base_revision, base_head=base_head,
                                  changes=(FileChange(path=output_path, before=before, after=after),),
                                  declared_files=1, declared_lines=0, scope=signal.scope,
                                  summary="Bounded benchmark output; mathematical correctness is evaluated separately")
            files, lines = blast_radius(candidate)
            candidate = candidate.model_copy(update={"declared_files": files, "declared_lines": lines})
            FixtureExecutor.materialize(candidate, repository, directory)
        return ExecutionResult(candidate, usage, str(directory) if candidate else None,
                               self.provenance, self.usage_source, metadata=cast(dict[str, JsonValue], metadata),
                               uncertain=reply.status != "completed")


def _worker_entry(config_json: str, owner: Connection, gate: SharedRequestGate,
                  model_factory: ModelFactory, timeout_seconds: float, parameters: dict[str, Any]) -> None:
    model: ModelLeaf | None = None
    watcher_done = Event()
    config = WorkerConfig.model_validate_json(config_json)
    result_path = config.state / "processes" / f"worker-{config.agent.instance}.json"
    try:
        os.umask(0o077)
        temp = config.state / "temp" / f"worker-{config.agent.instance}"
        temp.mkdir(parents=True, mode=0o700)
        tempfile.tempdir = str(temp)
        for name in ("TMPDIR", "TMP", "TEMP"):
            os.environ[name] = str(temp)
        if not owner.poll(10):
            raise ValueError("benchmark_credential_frame_timeout")
        frame = bytearray(owner.recv_bytes(8192))
        try:
            model = model_factory(frame.decode("utf-8"), gate, timeout_seconds)
        finally:
            frame[:] = b"\0" * len(frame)

        def watch_owner() -> None:
            while not watcher_done.wait(0.05):
                try:
                    if owner.poll(0):
                        owner.recv_bytes(1)
                        gate.stop()
                        return
                except (EOFError, OSError):
                    gate.stop()
                    return

        watcher = Thread(target=watch_owner, name="benchmark-owner-watch", daemon=True)
        watcher.start()
        executor = BenchmarkWorkerExecutor(model, evidence=config.state / "model-results", **parameters)
        result = Worker(config, executor).run()
        _write_new(result_path, {"pid": os.getpid(), "worker_id": config.worker_id, "result": result})
    except BaseException as error:
        gate.stop()
        _write_new(result_path, {"pid": os.getpid(), "worker_id": config.worker_id,
                                 "failure": "benchmark_worker_failed",
                                 "error_type": type(error).__name__ if type(error).__name__ in {
                                     "ValueError", "EOFError", "OSError", "TimeoutError", "AssetSafetyError"
                                 } else "internal_error"})
        raise SystemExit(1) from None
    finally:
        watcher_done.set()
        owner.close()
        if model is not None:
            model.close()


def run_tasks(tasks: Sequence[dict[str, str]], *, credential: str, gate: SharedRequestGate,
              run_id: str, block_id: str, seed: int, concurrency: int, max_tokens: int,
              temperature: float, directory: Path, timeout_seconds: float = 120,
              runtime_seconds: float = 1800, model_factory: ModelFactory = create_live_model,
              context: BaseContext | None = None) -> dict[str, Any]:
    validated = validate_tasks(tasks)
    if (type(concurrency) is not int or not 1 <= concurrency <= gate.concurrency <= 5
            or not math.isfinite(runtime_seconds) or not 0 < runtime_seconds <= 1800
            or not 0 < timeout_seconds <= 180 or not isinstance(credential, str)
            or re.fullmatch(r"[A-Za-z0-9._~+/=-]{1,8192}", credential) is None):
        raise ValueError("invalid_benchmark_runtime_configuration")
    # 共用契约在任何文件写入、子进程或模型请求之前验证身份和参数。
    for task in validated:
        ModelRequest(run_id=run_id, framework="morphogenesis", block_id=block_id,
                     seed=seed, task_id=task["id"], prompt=task["prompt"],
                     max_tokens=max_tokens, temperature=temperature)
    policy = budget_policy(len(validated), runtime_seconds, max_tokens)
    started_ns = time.monotonic_ns()
    target, state = seed_tasks(directory, validated, run_id=run_id, policy=policy)
    scopes = tuple(f"task_{index:03d}" for index in range(len(validated)))
    ctx = cast(Any, context or multiprocessing.get_context("spawn"))
    processes: list[Any] = []
    owners: list[Connection] = []
    interrupted = False
    forced: list[int] = []
    parameters = {"run_id": run_id, "block_id": block_id, "seed": seed,
                  "max_tokens": max_tokens, "temperature": temperature}
    try:
        for number in range(concurrency):
            config = WorkerConfig(
                state=state, target=target, agent=AgentId(role="builder", instance=number),
                swarm_id=run_id, locality=Locality(workspace=str(target), authorized_scopes=scopes, modules=scopes),
                budget=policy, capabilities={"math": 1.0}, seed=seed + number,
                energy=len(validated), energy_policy="claim", max_senses=10000,
                max_idle=100, idle_seconds=0.01, sleep_seconds=0.01,
                lease_seconds=min(300.0, runtime_seconds), continue_on_rejection=True,
            )
            receiver, sender = ctx.Pipe(duplex=False)
            process = ctx.Process(target=_worker_entry, args=(config.model_dump_json(), receiver, gate,
                                  model_factory, timeout_seconds, parameters), name=f"morph-benchmark-{number}")
            try:
                process.start()
            except BaseException:
                receiver.close()
                sender.close()
                raise
            receiver.close()
            processes.append(process)
            owners.append(sender)
        for owner in owners:
            owner.send_bytes(credential.encode("utf-8"))
        deadline = started_ns / 1e9 + runtime_seconds
        for process in processes:
            process.join(max(0.0, deadline - time.monotonic()))
        if any(process.is_alive() for process in processes):
            interrupted = True
            gate.stop()
    except BaseException:
        interrupted = True
        gate.stop()
        raise
    finally:
        for owner in owners:
            owner.close()
        if interrupted or any(process.is_alive() for process in processes):
            gate.stop()
            drain_deadline = time.monotonic() + timeout_seconds + 20
            for process in processes:
                process.join(max(0.0, drain_deadline - time.monotonic()))
            for process in processes:
                if process.is_alive():
                    forced.append(process.pid)
                    process.terminate()
            for process in processes:
                process.join(10)
    ledger = TaskLedger(state / "tasks.sqlite3", run_id, limits=policy.limits)
    records: list[dict[str, Any]] = []
    for index, task in enumerate(validated):
        path = state / "model-results" / f"task_{index:03d}.json"
        record = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {
            "task_id": task["id"], "text": None, "usage": None, "status": "canceled",
            "request_id": None, "evidence": {"error_kind": "not_executed"},
        }
        fact = ledger.get(task["id"])
        record["native_task"] = {"status": fact.status, "attempts": fact.attempts,
                                 "result_id": fact.result_id, "owner": fact.owner,
                                 "effect_applied": fact.effect_applied, "scope": fact.signal.scope}
        records.append(record)
    native_processes = [{"pid": process.pid, "exit_code": process.exitcode,
                        "alive": process.is_alive()} for process in processes]
    runtime = {"framework": "morphogenesis", "directory": str(directory),
               "wall_seconds": (time.monotonic_ns() - started_ns) / 1e9,
               "processes": native_processes, "forced_termination_pids": forced,
               "owned_workers_exited": all(not process.is_alive() for process in processes),
               "descendant_cleanup_confirmed": None,
               "descendant_cleanup_scope": "synchronous native helpers are waited by their owner; no independent descendant inventory",
               "interrupted": interrupted, "gate": gate.snapshot(),
               "ledger": str(state / "tasks.sqlite3"), "budget": str(state / "budget.sqlite3"),
               "audit": str(state / "audit"),
               "mathematical_accuracy": "independent_evaluator_only",
               "local_allowance_is_not_provider_price": True}
    _write_new(state / "runtime-result.json", runtime)
    return {"records": records, "runtime": runtime}
