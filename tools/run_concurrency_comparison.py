from __future__ import annotations

import argparse
import asyncio
import csv
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import importlib
from importlib.metadata import version
import json
import multiprocessing
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any
from uuid import uuid4

from swarm.benchmark_model import ModelRequest, SharedRequestGate, StepFunBenchmarkExecutor, STEPFUN_MODEL, SYSTEM_PROMPT, validate_transport_configuration
from swarm.benchmark_runtime import run_tasks as morph_run_tasks
from tools.benchmark_protocol import FRAMEWORKS, load_examples, model_tasks, ordered_arms, score_records, summarize_http


def write_json(path: Path, value: Any) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, allow_nan=False, indent=2)
        stream.write("\n")


def load_adapters(directory: Path) -> dict[str, Any]:
    directory = directory.resolve(strict=True)
    expected = {"autogen-core": "0.7.5", "langgraph": "1.2.18"}
    for name, required in expected.items():
        if version(name) != required:
            raise ValueError("comparator_version_mismatch")
    sys.path.insert(0, str(directory))
    modules = {"autogen-core": importlib.import_module("autogen_adapter"),
               "langgraph": importlib.import_module("langgraph_adapter")}
    for module in modules.values():
        if module.__file__ is None or Path(module.__file__).resolve().parent != directory:
            raise ValueError("comparator_import_path_mismatch")
    return modules


def source_snapshot(adapters: Path) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    tracked = subprocess.check_output(["git", "ls-files", "-z", "*.py", "package.json", "package-lock.json", "poetry.lock"], cwd=root).decode().split("\0")
    additions = ("swarm/benchmark_model.py", "swarm/benchmark_runtime.py", "tools/benchmark_protocol.py",
                 "tools/run_concurrency_comparison.py", "tools/benchmark_requirements.lock.txt")
    sources = {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
               for name in sorted(set(tracked) | set(additions)) if name}
    comparator = {name: hashlib.sha256((adapters / name).read_bytes()).hexdigest()
                  for name in ("autogen_adapter.py", "langgraph_adapter.py", "comparator_contract.py")}
    return {"source_files_sha256": sources, "comparator_files_sha256": comparator,
            "packages": {name: version(name) for name in ("autogen-core", "langgraph", "httpx", "socksio", "pydantic", "sqlmodel")},
            "python": sys.version, "node": subprocess.check_output(["node", "--version"], text=True).strip()}


def prepare(output: Path, source: Path, adapters: Path, *, mode: str, seed: int, max_tokens: int, temperature: float) -> tuple[list[Any], dict[str, Any]]:
    examples, selection = load_examples(source, split="train" if mode == "development" else "test",
                                        count=4 if mode == "development" else 48)
    arms = ([{"framework": name, "concurrency": 2} for name in FRAMEWORKS]
            if mode == "development" else ordered_arms(seed))
    plan = {"schema": "morph.concurrency-comparison.v1", "mode": mode, "order_seed": seed,
            "repeats": 1, "arms": arms, "tasks_per_arm": len(examples),
            "maximum_requests": len(arms) * len(examples), "maximum_concurrent_owned_requests": 5,
            "model": STEPFUN_MODEL, "system_prompt": SYSTEM_PROMPT,
            "max_tokens": max_tokens, "temperature": temperature, "stream": False,
            "reasoning_settings": "provider default, identical across all arms; no reasoning_effort override",
            "automatic_retries": 0, "source_revision": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[1], text=True).strip(),
            "execution_snapshot": source_snapshot(adapters),
            "gold_access": "independent evaluator only; never worker ledger, prompt, executor or native framework",
            "claim_limit": "fixed independent batch throughput/accuracy; not collaborative or decentralized superiority"}
    output.mkdir(mode=0o700, parents=True, exist_ok=True)
    for name, body in (("selection.json", selection), ("plan.json", plan)):
        path = output / name
        if path.exists():
            if json.loads(path.read_text(encoding="utf-8")) != body:
                raise ValueError("frozen_benchmark_plan_changed")
        else:
            write_json(path, body)
    return examples, plan


def result_slots(tasks: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [{"task_id": task["id"], "status": "not_run", "text": None,
             "usage": None, "request_id": None, "evidence": {}} for task in tasks]


class RecordingExecutor:
    def __init__(self, executor: StepFunBenchmarkExecutor, tasks: list[dict[str, str]], directory: Path):
        self.executor, self.gate, self.directory = executor, executor.gate, directory
        self.indexes = {task["id"]: index for index, task in enumerate(tasks)}
        directory.mkdir(mode=0o700)

    async def generate(self, request: ModelRequest) -> Any:
        response = await self.executor.generate(request)
        # 只记录已通过公共边界脱敏的结果；框架取消不得抹去此前已完成调用。
        write_json(self.directory / f"task_{self.indexes[request.task_id]:03d}.json",
                   {"task_id": request.task_id, **asdict(response)})
        return response


def preserve_completed(rows: list[dict[str, Any]], tasks: list[dict[str, str]], directory: Path) -> list[dict[str, Any]]:
    by_task = {row.get("task_id"): row for row in rows}
    for index, task in enumerate(tasks):
        path = directory / f"task_{index:03d}.json"
        if path.is_file():
            stored = json.loads(path.read_text(encoding="utf-8"))
            if stored.get("task_id") != task["id"]:
                raise ValueError("recorded_response_identity_mismatch")
            by_task[task["id"]] = stored
    return [by_task.get(task["id"], result_slots([task])[0]) for task in tasks]


async def comparator_arm(module: Any, tasks: list[dict[str, str]], executor: RecordingExecutor,
                         options: dict[str, Any], events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], bool]:
    try:
        async with asyncio.timeout(1800):
            try:
                rows = await module.run_tasks(tasks, executor, request_factory=ModelRequest,
                                             event_sink=events.append, **options)
            except asyncio.CancelledError as canceled:
                # 在 timeout 转换异常之前取得框架已排空的真实完成记录。
                executor.gate.stop()
                return getattr(canceled, "results", result_slots(tasks)), True
        return rows, False
    except Exception as error:
        # 不输出第三方异常原文；保存已完成结果，不重试未知请求。
        executor.gate.stop()
        rows = getattr(error, "results", result_slots(tasks))
        if not isinstance(rows, list):
            rows = result_slots(tasks)
        return rows, True


def run(args: argparse.Namespace) -> int:
    os.umask(0o077)
    if not 1 <= args.max_tokens <= 4096 or not 0 <= args.temperature <= 2:
        raise ValueError("invalid_fixed_model_settings")
    # 在读取凭据/创建预算/发起网络请求前验证实际传输依赖（含现有代理配置）。
    validate_transport_configuration()
    examples, plan = prepare(args.output, args.source, args.adapters_dir, mode=args.mode, seed=args.seed,
                             max_tokens=args.max_tokens, temperature=args.temperature)
    if args.prepare_only:
        print(json.dumps({"status": "PREPARED", "output": str(args.output), "model_calls": 0,
                          "maximum_requests": plan["maximum_requests"]}))
        return 0
    if not args.credential_stdin or sys.stdin.isatty():
        raise ValueError("private_parent_stdin_required")
    if (args.output / "run-started.json").exists():
        raise ValueError("benchmark_directory_already_attempted_no_automatic_replay")
    modules = load_adapters(args.adapters_dir)
    tasks = model_tasks(examples)
    gate = SharedRequestGate.create(multiprocessing.get_context("spawn"), concurrency=5,
                                    max_requests=plan["maximum_requests"])
    # 只从所属匿名 stdin 读取一次；不从环境、文件或命令行取密钥。
    key = sys.stdin.buffer.readline(8194).decode("utf-8").rstrip("\r\n")
    if not key or len(key.encode("utf-8")) > 8192:
        raise ValueError("invalid_ephemeral_credential")
    run_id = "gsm8k-" + uuid4().hex
    started = time.monotonic_ns()
    write_json(args.output / "run-started.json", {"run_id": run_id, "started_at": datetime.now(timezone.utc).isoformat(),
               "started_monotonic_ns": started, "plan": plan, "replay_allowed": False})
    results: list[dict[str, Any]] = []
    executor: StepFunBenchmarkExecutor | None = None
    try:
        for ordinal, arm in enumerate(plan["arms"]):
            block_id = f"block-{ordinal:02d}"
            record: dict[str, Any] = {**arm, "ordinal": ordinal, "block_id": block_id, "status": "NOT_RUN",
                                      "requested_tasks": len(tasks), "records": result_slots(tasks)}
            results.append(record)
            if gate.stopped.is_set():
                continue
            gate = gate.for_concurrency(multiprocessing.get_context("spawn"), arm["concurrency"])
            if executor is not None:
                executor.close()
            executor = StepFunBenchmarkExecutor(key, gate)
            directory = args.output / block_id
            directory.mkdir(mode=0o700)
            events: list[dict[str, Any]] = []
            response_directory = directory / "model-results"
            arm_started = time.monotonic_ns()
            options = dict(run_id=run_id, block_id=block_id, seed=args.seed,
                           concurrency=arm["concurrency"], max_tokens=args.max_tokens, temperature=args.temperature)
            try:
                if arm["framework"] == "morphogenesis":
                    value = morph_run_tasks(tasks, credential=key, gate=gate, directory=directory / "native", **options)
                    rows = value["records"]
                    record["native_runtime"] = value["runtime"]
                    aborted = gate.stopped.is_set()
                else:
                    recording = RecordingExecutor(executor, tasks, response_directory)
                    rows, aborted = asyncio.run(comparator_arm(modules[arm["framework"]], tasks, recording, options, events))
                    rows = preserve_completed(rows, tasks, response_directory)
                record["records"] = rows
                model_complete = (not aborted and len(rows) == len(tasks)
                            and all(row.get("status") == "completed" for row in rows)
                            and {row.get("task_id") for row in rows} == {task["id"] for task in tasks})
                native = record.get("native_runtime")
                delivery_complete = (native is None or (
                    native["owned_workers_exited"] and not native["forced_termination_pids"] and not native["interrupted"]
                    and all(process["exit_code"] == 0 for process in native["processes"])
                    and all(row.get("native_task", {}).get("status") == "completed"
                            and row.get("native_task", {}).get("effect_applied") for row in rows)))
                record["model_inventory_complete"] = model_complete
                record["native_delivery_complete"] = delivery_complete
                complete = model_complete and delivery_complete
                if not complete:
                    gate.stop()
                record["status"] = "COMPLETED" if complete else "ABORTED"
            except BaseException:
                gate.stop()
                record["status"] = "ABORTED"
                record["safe_error"] = "runtime_or_evidence_failure"
                recovery_directory = (directory / "native" / "state" / "model-results"
                                      if arm["framework"] == "morphogenesis" else response_directory)
                if recovery_directory.is_dir():
                    record["records"] = preserve_completed(record["records"], tasks, recovery_directory)
                record["model_inventory_complete"] = False
                record["native_delivery_complete"] = False
            record["wall_seconds"] = (time.monotonic_ns() - arm_started) / 1e9
            score = score_records(examples, record["records"])
            record["evaluation"] = score
            record["completed_requests"] = sum(row.get("status") == "completed" for row in record["records"])
            record["primary_accuracy"] = score["accuracy"] if record["status"] == "COMPLETED" else None
            record["correct_per_minute"] = (score["correct"] * 60 / record["wall_seconds"]
                                             if record["status"] == "COMPLETED" else None)
            record["http"] = summarize_http(record["records"])
            if (record["http"]["peak_client_http_active"] is not None
                    and record["http"]["peak_client_http_active"] > arm["concurrency"]):
                gate.stop()
                record["status"] = "ABORTED"
                record["safe_error"] = "measured_http_concurrency_exceeded_arm_limit"
                record["primary_accuracy"] = record["correct_per_minute"] = None
            write_json(directory / "native-events.json", events)
            write_json(directory / "result.json", record)
            print(json.dumps({"block_id": block_id, "framework": arm["framework"],
                              "concurrency": arm["concurrency"], "status": record["status"],
                              "completed_requests": record["completed_requests"]}), flush=True)
    finally:
        if executor is not None:
            executor.close()
        key = ""
        report = {"schema": plan["schema"], "run_id": run_id,
                  "status": "COMPLETED" if len(results) == len(plan["arms"]) and all(r["status"] == "COMPLETED" for r in results) else "ABORTED",
                  "mode": args.mode, "arms": results, "gate": gate.snapshot(),
                  "wall_seconds": (time.monotonic_ns() - started) / 1e9,
                  "claim": "same-model fixed-task batch pilot; no demonstrated architecture or collaboration superiority",
                  "cost": None, "limitations": ["single exploratory repeat", "public benchmark contamination possible",
                      "network/provider queueing/cache/order effects", "HTTP-active overlap is not GPU concurrency"]}
        write_json(args.output / "report.json", report)
        with (args.output / "summary.csv").open("x", newline="", encoding="utf-8") as stream:
            fields = ["framework", "concurrency", "status", "requested_tasks", "completed_requests", "wall_seconds", "primary_accuracy", "correct_per_minute"]
            writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(results)
    return 0 if report["status"] == "COMPLETED" else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--adapters-dir", type=Path, required=True)
    parser.add_argument("--mode", choices=("development", "pilot"), default="pilot")
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--credential-stdin", action="store_true")
    parser.add_argument("--seed", type=int, default=20261030)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--temperature", type=float, default=0.0)
    args = parser.parse_args()
    try:
        return run(args)
    except Exception:
        print(json.dumps({"status": "FAILED", "error": "benchmark_preparation_or_execution_failed"}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
