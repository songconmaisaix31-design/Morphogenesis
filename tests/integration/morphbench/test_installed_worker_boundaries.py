"""Bounded real-process controls; fixed fixtures are not scientific results.

Run from outside a checkout with a noneditable 0.2.1 interpreter and the pinned
Node SDK available above its site-packages. Child processes import that same
installed package. MORPHBENCH_EVIDENCE_DIR retains raw observations on failure.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from contracts.identity import AgentId
from local_assets.models import AssetSafetyError
from swarm.cli import demo_config, seed_demo
from swarm.task_ledger import LeaseLost, TaskLedger
from swarm.worker_loop import FixtureExecutor, Worker, WorkerConfig
import swarm.worker_loop as runtime


class HeldExecutor(FixtureExecutor):
    def __init__(self, stage: str, marker: Path):
        self.stage, self.marker = stage, marker

    def hold(self, signal):
        self.marker.write_text(json.dumps({"pid": os.getpid(), "task_id": signal.task_id,
                                           "stage": self.stage, "time": time.time()}))
        time.sleep(120)
        raise RuntimeError("control hold timed out before parent kill")

    def bound(self, signal):
        if self.stage == "before_reservation":
            self.hold(signal)
        return super().bound(signal)

    def execute(self, signal, *args, **kwargs):
        if self.stage == "after_reservation":
            self.hold(signal)
        return super().execute(signal, *args, **kwargs)


def child(config_path: Path, stage: str):
    config = WorkerConfig.model_validate_json(config_path.read_bytes())
    marker = config_path.with_suffix(".held.json")
    executor = HeldExecutor(stage, marker) if stage != "normal" else FixtureExecutor()
    result = Worker(config, executor).run()
    config_path.with_suffix(".result.json").write_text(json.dumps(result, indent=2))


def start(config: WorkerConfig, stage: str, root: Path, name: str):
    path = root / f"{name}.json"
    path.write_text(config.model_dump_json())
    executable = sys.executable
    environment = os.environ.copy()
    if sys.platform == "win32" and sys.prefix != sys.base_prefix:
        # Same venv handling as CPython multiprocessing.popen_spawn_win32
        # (bpo-35797): retain the venv, bypass its redirector, own the real PID.
        executable = sys._base_executable
        environment["__PYVENV_LAUNCHER__"] = sys.executable
    with path.with_suffix(".stdout.log").open("wb") as out, path.with_suffix(".stderr.log").open("wb") as err:
        process = subprocess.Popen([executable, str(Path(__file__).resolve()),
                                    "--child", str(path), stage], stdout=out, stderr=err,
                                   env=environment)
    return process, path


def await_held(process, path):
    deadline = time.monotonic() + 60
    marker = path.with_suffix(".held.json")
    while not marker.exists() and process.poll() is None and time.monotonic() < deadline:
        time.sleep(0.05)
    assert marker.exists(), path.with_suffix(".stderr.log").read_text()
    value = json.loads(marker.read_text())
    assert value["pid"] == process.pid and process.poll() is None
    return value


@pytest.mark.parametrize("stage", ["before_reservation", "after_reservation"])
def test_two_actual_worker_kills_preserve_authority_and_unknown_usage(tmp_path, stage):
    evidence = {"stage": stage, "runtime_file": runtime.__file__,
                "evidence_class": "contract_local", "provenance": "mock",
                "task_live": "not_run", "processes": [], "held": [], "root": str(tmp_path)}
    all_processes = []
    try:
        target, state = seed_demo(tmp_path / "fixture")
        configs = [WorkerConfig.model_validate_json(demo_config(target, state, i, 1.0))
                   .model_copy(update={"energy": 2, "lease_seconds": 1.0}) for i in range(3)]
        held = [start(configs[i], stage, tmp_path, f"held-{i}") for i in range(2)]
        all_processes.extend(p for p, _ in held)
        for process, path in held:
            evidence["held"].append(await_held(process, path))
        ledger = TaskLedger(state / "tasks.sqlite3", configs[0].swarm_id)
        old = list(ledger.leases())
        assert len(old) == 2 and {item.token for item in old} == {1}
        evidence["leases_before_kill"] = [item.model_dump(mode="json") for item in old]
        for process, path in held:
            # Popen owns a Windows process handle; no PID-only lookup or tree kill.
            process.kill()
            process.wait(timeout=15)
            evidence["processes"].append({"pid": process.pid, "exit": process.returncode,
                                          "config": str(path), "killed": True})
        time.sleep(max(0, max(item.expires_at for item in old) - time.time()) + 0.15)
        evidence["completed_after_kill"] = sum(r.status == "completed" for r in ledger.snapshot())
        writes = []
        for lease in old:
            with pytest.raises(LeaseLost):
                ledger.submit(lease, "late-result", {"applied": True},
                              apply=lambda check: writes.append("forbidden"))
        assert writes == []
        evidence["stale_submit_side_effects"] = writes
        if stage == "before_reservation":
            # Two successors plus the unaffected locality run independently.
            successors = [config.model_copy(update={
                "agent": AgentId(role="builder", instance=i + 8), "lease_seconds": 30})
                for i, config in enumerate(configs)]
            runs = [start(config, "normal", tmp_path, f"successor-{i}")
                    for i, config in enumerate(successors)]
            all_processes.extend(p for p, _ in runs)
            evidence["successors"] = []
            for process, path in runs:
                process.wait(timeout=120)
                evidence["processes"].append({"pid": process.pid, "exit": process.returncode,
                                              "config": str(path), "killed": False})
                result = json.loads(path.with_suffix(".result.json").read_text())
                evidence["successors"].append(result)
                assert process.returncode == 0 and result["completed"] == 2
            records = ledger.snapshot()
            evidence["completed_final"] = sum(r.status == "completed" for r in records)
            assert len(records) == 6 and all(r.effect_applied for r in records)
            for lease in old:
                record = ledger.get(lease.task_id)
                assert record.token == 2 and record.status == "completed"
        else:
            # Same identities recover their own outstanding holds. No fabricated
            # settlement, release, reset, or forced retry of an unknown execution.
            evidence["recovery"] = [Worker(config).run() for config in configs[:2]]
            assert all(r["state"] == "sleeping" for r in evidence["recovery"])
            budget = Worker(configs[2]).budget.snapshot()
            evidence["budget"] = budget.model_dump(mode="json")
            evidence["completed_final"] = sum(r.status == "completed" for r in ledger.snapshot())
            assert budget.reason == "unknown_usage" and budget.uncertain_reservations == 2
            assert budget.estimated_cost_usd is None and budget.pending_reservations == 0
            assert evidence["completed_final"] == 0
            assert Worker(configs[2]).run()["state"] == "sleeping"
        evidence["result"] = "pass"
    finally:
        for process in all_processes:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=15)
        directory = Path(os.environ.get("MORPHBENCH_EVIDENCE_DIR", str(tmp_path)))
        directory.mkdir(parents=True, exist_ok=True)
        # Do not overwrite an earlier run; use distinct basetemp/evidence dirs.
        with (directory / f"two-kill-{stage}.json").open("x", encoding="utf-8") as stream:
            json.dump(evidence, stream, indent=2)


def test_installed_runtime_protects_its_actual_package_root(tmp_path):
    target, state = seed_demo(tmp_path / "fixture")
    config = WorkerConfig.model_validate_json(demo_config(target, state, 0, 1.0))
    package_root = Path(runtime.__file__).resolve().parents[1]
    with pytest.raises(AssetSafetyError):
        Worker(config.model_copy(update={"target": package_root}))
    forbidden = package_root / "morphbench-forbidden-runtime-state"
    assert not forbidden.exists()
    with pytest.raises(AssetSafetyError):
        Worker(config.model_copy(update={"state": forbidden}))
    assert not forbidden.exists()


if __name__ == "__main__" and sys.argv[1] == "--child":
    child(Path(sys.argv[2]), sys.argv[3])
