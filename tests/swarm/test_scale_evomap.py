"""Scale topology is deterministic and remains bounded to the approved shapes."""

import subprocess

import pytest

from swarm.cli import EvoMapRun, evomap_worker_config, seed_evomap
from swarm.evomap_executor import EvoMapConfig
from swarm.models import BudgetPolicy
from swarm.worker_loop import WorkerConfig


def _config(tmp_path, workers, tasks):
    tmp_path.mkdir(parents=True, exist_ok=True)
    key = tmp_path / "private-key.txt"
    key.write_text("fixture-only-not-a-real-key")
    return EvoMapRun(
        directory=tmp_path / f"run-{workers}-{tasks}", workers=workers, tasks=tasks,
        api=EvoMapConfig(credential_file=key),
        budget=BudgetPolicy(max_cost_usd=1, unbounded_reservation_usd=0.02,
            limits={"max_tasks": tasks, "max_attempts": tasks,
                    "max_attempts_per_task": 1, "max_derived_tasks": 0,
                    "max_runtime_seconds": 300}),
    )


def test_approved_scale_shapes_seed_exact_task_counts(tmp_path):
    for workers, tasks in ((3, 6), (8, 48), (16, 96)):
        config = _config(tmp_path, workers, tasks)
        _, state = seed_evomap(config)
        from swarm.task_ledger import TaskLedger
        ledger = TaskLedger(state / "tasks.sqlite3", config.swarm_id, limits=config.budget.limits)
        records = ledger.snapshot(limit=tasks)
        assert len(records) == tasks
        assert records[-1].signal.payload["reuse_task_id"] == "data-0"
        assert records[-1].dependencies == ("data-0",)
        tracked = {path.replace("\\", "/") for path in subprocess.check_output(
            ["git", "ls-files"], cwd=config.directory / "local-workspace", text=True).splitlines()}
        assert {f"module_{index}/result_{index}.json" for index in range(workers)} <= tracked
        memberships: dict[str, int] = {}
        for instance in range(workers):
            worker = WorkerConfig.model_validate_json(evomap_worker_config(config, instance))
            for scope in worker.locality.authorized_scopes:
                memberships[scope] = memberships.get(scope, 0) + 1
            for record in records:
                if record.signal.scope in worker.locality.authorized_scopes:
                    assert record.signal.required_capability in worker.capabilities
        assert all(memberships[f"module_{index}"] >= 2 for index in range(workers))


def test_scale_rejects_unapproved_shape(tmp_path):
    with pytest.raises(ValueError, match="scale"):
        _config(tmp_path, 4, 8)


def test_worker_models_are_fixed_by_worker_and_validate_length(tmp_path):
    models = ("evomap-deepseek-v4-flash", "evomap-gemini-3.1-pro-preview", "evomap-glm-5.1")
    config = _config(tmp_path, 3, 6).model_copy(update={"worker_models": models})
    config = EvoMapRun.model_validate(config.model_dump())
    assert config.worker_models == models
    with pytest.raises(ValueError, match="worker_models"):
        EvoMapRun.model_validate({**config.model_dump(), "worker_models": models[:2]})


def test_capability_override_and_effective_model_price_binding(tmp_path):
    tags = ("gsm8k_math", "bbh_boolean")
    config = _config(tmp_path, 3, 6).model_copy(update={"capability_names": tags})
    config = EvoMapRun.model_validate(config.model_dump())
    for instance in range(3):
        worker = WorkerConfig.model_validate_json(evomap_worker_config(config, instance))
        assert worker.capabilities == {"gsm8k_math": 1.0, "bbh_boolean": 1.0}
    with pytest.raises(ValueError, match="capability_names"):
        EvoMapRun.model_validate({**config.model_dump(), "capability_names": ["gsm8k_math"] * 2})
    priced = _config(tmp_path / "priced", 3, 6).model_copy(update={"budget": BudgetPolicy(
        max_cost_usd=1, unbounded_reservation_usd=0.02,
        prices={"provider": "evomap", "model": "evomap-gpt-5.6-sol",
                "input_usd_per_million": 1, "output_usd_per_million": 1},
        limits={"max_tasks": 6, "max_attempts": 6, "max_attempts_per_task": 1,
                "max_derived_tasks": 0, "max_runtime_seconds": 300})})
    with pytest.raises(ValueError, match="matching_prices"):
        EvoMapRun.model_validate({**priced.model_dump(), "worker_models": ["evomap-gpt-5.6-terra"] * 3})
