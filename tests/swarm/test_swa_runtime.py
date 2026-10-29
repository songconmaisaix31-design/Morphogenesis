import json
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from swarm.models import Signal
from swarm.swa_runtime import _completion_summary, load_entries
from swarm.task_ledger import TaskLedger


def entries(root: Path):
    return [{"worker": {"state": str(root / "state"), "target": str(root / "target"),
            "swarm_id": "test-swa", "agent": {"role": "builder", "instance": instance},
            "locality": {"workspace": str(root / "target"), "authorized_scopes": ["data"]},
            "budget": {"max_cost_usd": 1.0}},
        "swa": {"executable": str(root / "swa"), "workdir": str(root / "staging"),
                "project": "approved-project", "endpoint": "http://127.0.0.1:8787",
                "agent": "opencode", "model": "provider/model"}} for instance in range(2)]


def test_load_distinct_workers_preserves_conservative_budget(tmp_path):
    path = tmp_path / "members.json"
    path.write_text(json.dumps(entries(tmp_path)))
    actual = load_entries(path)
    assert [entry.worker.worker_id for entry in actual] == ["builder-0", "builder-1"]
    assert all(not entry.worker.budget.allow_unknown_usage for entry in actual)
    assert all(entry.worker.budget.unbounded_reservation_usd is None for entry in actual)


@pytest.mark.parametrize("field,value", [
    ("state", "/different/state"), ("target", "/different/target"),
    ("swarm_id", "different"), ("budget", {"max_cost_usd": 2.0}),
    ("agent", {"role": "builder", "instance": 0}),
])
def test_rejects_conflicting_worker_configuration(tmp_path, field, value):
    payload = entries(tmp_path)
    payload[1]["worker"][field] = value
    path = tmp_path / "members.json"
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        load_entries(path)


def test_rejects_mixed_project_token_scope(tmp_path):
    payload = entries(tmp_path)
    payload[1]["swa"]["project"] = "another-project"
    path = tmp_path / "members.json"
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="share_swa_authority"):
        load_entries(path)


def test_help_needs_no_swa_or_model(tmp_path):
    result = subprocess.run([sys.executable, "-m", "swarm.swa_runtime", "--help"],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0
    assert "--config" in result.stdout


@pytest.mark.parametrize("statuses,worker_state,expected_code", [
    ([], "idle", 1),
    (["available"], "idle", 1),
    (["completed", "available"], "idle", 1),
    (["completed", "completed"], "idle", 0),
    (["completed"], "stopped", 1),
])
def test_completion_requires_finished_tasks_and_workers(tmp_path, statuses, worker_state, expected_code):
    path = tmp_path / "members.json"
    path.write_text(json.dumps(entries(tmp_path)))
    config = load_entries(path)[0].worker
    database = config.state / "tasks.sqlite3"
    ledger = TaskLedger(database, config.swarm_id)
    for index, status in enumerate(statuses):
        task_id = f"task-{index}"
        ledger.enqueue(Signal(task_id=task_id, signal_id=task_id, workspace=str(config.target),
                              scope="data", module="data", kind="opportunity", required_capability="json"))
        with sqlite3.connect(database) as db:
            db.execute("UPDATE tasks SET status=? WHERE task_id=?", (status, task_id))
    code, result = _completion_summary(config, [
        {"worker_id": config.worker_id, "state": worker_state, "exit_code": 0},
    ])
    assert code == expected_code
    assert result["status"] == ("completed" if expected_code == 0 else "incomplete")
    assert result["tasks"] == {"total": len(statuses), "completed": statuses.count("completed")}
