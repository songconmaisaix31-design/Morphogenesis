"""Independent contract-local proof of restart after cross-member adoption."""

import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

from contracts.identity import AgentId
from local_assets.models import FileExpectation, ValidationPolicy
from local_assets.paths import git
from swarm.cli import fixture_policy
from swarm.models import BudgetPolicy, Locality, Signal
from swarm.pheromone import PheromoneField
from swarm.task_ledger import TaskLedger
from swarm.worker_loop import WorkerConfig


def _rows(path: Path, table: str):
    with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as db:
        db.execute("PRAGMA query_only=ON")
        return db.execute(f'SELECT * FROM "{table}" ORDER BY rowid').fetchall()


def _process(config: WorkerConfig, *, resume=False):
    script = """
import json, os, sys
from local_assets.apply import PreparedApplication
from local_assets.consume import AssetConsumer
from local_assets.promote import AssetPromoter
from swarm.worker_loop import FixtureExecutor, Worker, WorkerConfig
if sys.argv[2] == 'resume':
    def forbidden(*args, **kwargs):
        raise AssertionError('completed adoption must not execute, apply, approve or adopt again')
    FixtureExecutor.bound = forbidden
    FixtureExecutor.execute = forbidden
    PreparedApplication.apply = forbidden
    AssetPromoter.promote = forbidden
    AssetConsumer.record_adoption = forbidden
result = Worker(WorkerConfig.model_validate_json(sys.argv[1])).run()
print(json.dumps({'pid': os.getpid(), 'result': result}))
"""
    result = subprocess.run(
        [sys.executable, "-c", script, config.model_dump_json(), "resume" if resume else "initial"],
        capture_output=True, text=True, timeout=90,
        env={**os.environ, "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1",
             "MKL_NUM_THREADS": "1", "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert result.returncode == 0, result.stderr
    receipt = json.loads(result.stdout)
    assert receipt["result"]["state"] == "idle", receipt
    return receipt


def test_completed_cross_member_adoption_restart_has_no_repeated_effect(tmp_path):
    # Explicit literal data fixture; no algorithm/model or candidate code executes.
    target, state = tmp_path / "target", tmp_path / "state"
    (target / "data").mkdir(parents=True)
    (target / "data/source.txt").write_bytes(b"old\n")
    git(target, "init", "-b", "integration-literal-fixture")
    git(target, "add", "--", "data/source.txt")
    git(target, "-c", "user.name=Integration Fixture", "-c", "user.email=fixture@localhost",
        "commit", "-m", "Seed independent literal fixture")
    head, index = git(target, "rev-parse", "HEAD"), (target / ".git/index").read_bytes()
    ledger = TaskLedger(state / "tasks.sqlite3", "integration-restart")
    field = PheromoneField(state / "field.sqlite3", ledger=ledger)
    for name, module, path, payload, dependencies in (
        ("source", "producer", "data/source.txt",
         {"changes": [{"path": "data/source.txt", "before": "old\n", "after": "stable data\n"}]}, ()),
        ("consumer", "consumer", "data/copy.txt",
         {"reuse_task_id": "source", "path_map": {"data/source.txt": "data/copy.txt"}}, ("source",)),
    ):
        signal = Signal(task_id=name, signal_id=name, workspace=str(target), scope="data", module=module,
                        kind="opportunity", required_capability="repair", payload=payload)
        policy = ValidationPolicy(version="independent-literal-v1", expectations=(
            FileExpectation(path=path, content="stable data\n"),))
        ledger.enqueue(signal, dependencies=dependencies,
                       acceptance={"validation_policy": policy.model_dump(mode="json")})
        field.deposit(signal)
    configs = [WorkerConfig(
        state=state, target=target, swarm_id="integration-restart", agent=AgentId(role="builder", instance=i),
        locality=Locality(workspace=str(target), authorized_scopes=("data",), modules=(module,)),
        budget=BudgetPolicy.model_validate(fixture_policy(0.01)), capabilities={"repair": 1},
        energy=5, max_idle=1,
    ) for i, module in enumerate(("producer", "consumer"))]
    receipts = [_process(config) for config in configs]
    assert receipts[0]["pid"] != receipts[1]["pid"]
    assert [receipt["result"]["completed"] for receipt in receipts] == [1, 1]
    source, consumer = ledger.get("source"), ledger.get("consumer")
    assert source.owner != consumer.owner and source.effect_applied and consumer.effect_applied
    assert consumer.result["consumed_asset_ids"] == [source.result["candidate_asset_id"]]
    adoptions = _rows(state / "assets/assets.sqlite3", "adoptions")
    assert len(adoptions) == 1
    adoption = json.loads(adoptions[0][1])
    assert adoption["result_id"] == consumer.result_id
    assert adoption["context"]["input_context"] == consumer.result["input_context"]
    assert adoption["context"]["execution_id"] == consumer.result["execution_id"]
    databases = {state / "tasks.sqlite3": ("tasks", "task_attempts", "dependencies"),
                 state / "budget.sqlite3": ("budget_reservations",),
                 state / "assets/assets.sqlite3": ("assets", "reports", "approvals", "consumptions", "adoptions")}
    before = {str(path) + ":" + table: _rows(path, table)
              for path, tables in databases.items() for table in tables}
    audits = {str(path): path.read_bytes() for path in (state / "audit").rglob("*.json")}
    receipts.append(_process(configs[1], resume=True))
    assert receipts[-1]["result"]["completed"] == 1
    after = {str(path) + ":" + table: _rows(path, table)
             for path, tables in databases.items() for table in tables}
    assert after == before
    assert {str(path): path.read_bytes() for path in (state / "audit").rglob("*.json")} == audits
    assert (target / "data/copy.txt").read_bytes() == (target / "data/source.txt").read_bytes() == b"stable data\n"
    assert git(target, "rev-parse", "HEAD") == head and (target / ".git/index").read_bytes() == index
    (tmp_path / "restart-evidence.json").write_text(json.dumps({
        "evidence_class": "contract_local", "processes": receipts, "adoption": adoption,
        "unchanged_business_rows": before, "interface_live": "not_run", "task_live": "not_run",
    }, indent=2), encoding="utf-8")
