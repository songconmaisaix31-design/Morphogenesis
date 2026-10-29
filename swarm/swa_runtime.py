"""Launch independent Morphogenesis workers with an explicitly configured SWA executor."""
from __future__ import annotations

import argparse
import json
import multiprocessing
from multiprocessing.connection import Connection
from multiprocessing.process import BaseProcess
import os
from pathlib import Path
import sqlite3

from pydantic import BaseModel, ConfigDict, JsonValue, TypeAdapter

from local_assets.paths import no_links
from swarm.cli import _limit_blas_threads
from swarm.swa_executor import SwaConfig, SwaExecutor
from swarm.worker_loop import Worker, WorkerConfig

_INPUT_ERRORS = {"at_least_one_worker_required", "worker_paths_must_be_absolute",
                 "workers_must_share_swarm_state_target_and_budget", "locality_target_mismatch",
                 "duplicate_worker_identity", "workers_must_share_swa_authority",
                 "config_path_must_be_absolute", "bounded_config_file_required", "swa_project_token_required"}


class WorkerEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    worker: WorkerConfig
    swa: SwaConfig


def validate_entries(entries: list[WorkerEntry]) -> list[WorkerEntry]:
    if not entries:
        raise ValueError("at_least_one_worker_required")
    first = entries[0]
    identities: set[str] = set()
    for entry in entries:
        config = entry.worker
        if not config.target.is_absolute() or not config.state.is_absolute():
            raise ValueError("worker_paths_must_be_absolute")
        if (config.state.resolve() != first.worker.state.resolve()
                or config.target.resolve() != first.worker.target.resolve()
                or config.swarm_id != first.worker.swarm_id or config.budget != first.worker.budget):
            raise ValueError("workers_must_share_swarm_state_target_and_budget")
        if Path(config.locality.workspace).resolve() != config.target.resolve():
            raise ValueError("locality_target_mismatch")
        if config.worker_id in identities:
            raise ValueError("duplicate_worker_identity")
        identities.add(config.worker_id)
        # One inherited token belongs to one SWA project and endpoint.
        if entry.swa.project != first.swa.project or entry.swa.endpoint != first.swa.endpoint:
            raise ValueError("workers_must_share_swa_authority")
    return entries


def load_entries(path: Path) -> list[WorkerEntry]:
    if not path.is_absolute():
        raise ValueError("config_path_must_be_absolute")
    no_links(path)
    if not path.is_file() or path.stat().st_size > 1024 * 1024:
        raise ValueError("bounded_config_file_required")
    return validate_entries(TypeAdapter(list[WorkerEntry]).validate_json(path.read_bytes()))


def _member(payload: str, sender: Connection) -> None:
    entry = WorkerEntry.model_validate_json(payload)
    try:
        result = Worker(entry.worker, SwaExecutor(entry.swa)).run()
        sender.send({key: result.get(key) for key in ("worker_id", "state", "reason", "completed")})
    except Exception as error:
        sender.send({"worker_id": entry.worker.worker_id, "state": "error", "error_kind": type(error).__name__})
        raise SystemExit(1) from None
    finally:
        sender.close()


def run_workers(entries: list[WorkerEntry]) -> tuple[int, dict[str, JsonValue]]:
    validate_entries(entries)
    if not os.environ.get("SWA_PROJECT_TOKEN"):
        raise ValueError("swa_project_token_required")
    for entry in entries:
        SwaExecutor(entry.swa).check_paths(entry.worker.target, entry.worker.state)
    _limit_blas_threads()
    context = multiprocessing.get_context("spawn")
    children: list[tuple[BaseProcess, Connection]] = []
    rows: list[JsonValue] = []
    try:
        for entry in entries:
            receiver, sender = context.Pipe(duplex=False)
            process = context.Process(target=_member, args=(entry.model_dump_json(), sender))
            process.start()
            sender.close()
            children.append((process, receiver))
        for entry, (child_process, receiver) in zip(entries, children, strict=True):
            child_process.join()
            try:
                value = receiver.recv() if receiver.poll() else None
            except EOFError:
                value = None
            row: dict[str, JsonValue] = (TypeAdapter(dict[str, JsonValue]).validate_python(value)
                if value is not None else {"worker_id": entry.worker.worker_id, "state": "unknown"})
            row["exit_code"] = child_process.exitcode
            rows.append(row)
    except KeyboardInterrupt:
        return 130, {"status": "interrupted", "workers": rows, "external_effect": "unknown"}
    finally:
        for child_process, receiver in children:
            if child_process.is_alive():
                child_process.terminate()
                child_process.join()
            receiver.close()
    return _completion_summary(entries[0].worker, rows)


def _completion_summary(config: WorkerConfig, rows: list[JsonValue]) -> tuple[int, dict[str, JsonValue]]:
    database = config.state / "tasks.sqlite3"
    no_links(database)
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as db:
        total, completed = db.execute(
            "SELECT COUNT(*), COALESCE(SUM(status='completed'),0) FROM tasks WHERE swarm_id=?",
            (config.swarm_id,),
        ).fetchone()
    process_ok = all(isinstance(row, dict) and row.get("exit_code") == 0
                     and row.get("state") in {"idle", "exhausted"} for row in rows)
    complete = process_ok and total > 0 and completed == total
    return (0 if complete else 1), {"status": "completed" if complete else "incomplete", "workers": rows,
                                    "tasks": {"total": total, "completed": completed}}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run independently choosing Morphogenesis workers through SWA")
    parser.add_argument("--config", required=True, type=Path, help="Absolute JSON file containing Worker/SWA entries")
    args = parser.parse_args()
    try:
        code, result = run_workers(load_entries(args.config))
    except Exception as error:
        code, result = 1, {"status": "error", "error_kind": type(error).__name__}
        if type(error) is ValueError and str(error) in _INPUT_ERRORS:
            result["reason"] = str(error)
    print(json.dumps(result, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
