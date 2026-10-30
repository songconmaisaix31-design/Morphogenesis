import asyncio
import json
from types import SimpleNamespace

from tools.run_concurrency_comparison import comparator_arm, preserve_completed, result_slots


def test_recover_native_and_comparator_completed_rows_after_owner_cancel(tmp_path):
    tasks = [{"id": "fixture:0", "prompt": "fixed"}, {"id": "fixture:1", "prompt": "fixed"}]
    for relative in ("model-results", "native/state/model-results"):
        directory = tmp_path / relative
        directory.mkdir(parents=True)
        stored = {"task_id": "fixture:0", "status": "completed", "text": "#### 7", "usage": None,
                  "request_id": None, "evidence": {"provenance": "mock"}}
        (directory / "task_000.json").write_text(json.dumps(stored))
        rows = preserve_completed(result_slots(tasks), tasks, directory)
        assert rows[0] == stored
        assert rows[1]["status"] == "not_run"


def test_cancel_retains_framework_rows_and_stops_shared_gate():
    tasks = [{"id": "fixture:0", "prompt": "fixed"}]
    rows = [{"task_id": "fixture:0", "status": "completed", "text": "#### 7"}]
    stopped = []

    async def run_tasks(*args, **kwargs):
        error = asyncio.CancelledError()
        error.results = rows
        raise error

    result, aborted = asyncio.run(comparator_arm(SimpleNamespace(run_tasks=run_tasks), tasks,
        SimpleNamespace(gate=SimpleNamespace(stop=lambda: stopped.append(True))), {}, []))
    assert aborted and result == rows and stopped == [True]
