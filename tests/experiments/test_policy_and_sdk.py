"""Reject weakened scientific policy and unsafe attached-session operations."""

from pathlib import Path
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from orchestration.experiments import ExperimentCriteria, ExperimentEnvironment, ExperimentInput, ExperimentResources
from orchestration.experiments.backend import OpenSandboxBackend, OpenSandboxSession
from orchestration.experiments.case import public_case
from orchestration.experiments.models import ExperimentContext, ExperimentPlan


@pytest.mark.parametrize("fields", [
    {"variance_absolute_tolerance": 0.1}, {"observations": 10},
    {"version": "cmd:echo_passed"}, {"sample_variance": 1},
])
def test_fixed_scientific_criteria_cannot_be_relaxed(fields):
    with pytest.raises(ValidationError):
        ExperimentCriteria(**fields)


@pytest.mark.parametrize("path", ["../secret", "/absolute", "C:/secret", "a\\b", "a/../b", "a//b"])
def test_input_file_names_cannot_escape_archive_or_sandbox(path):
    with pytest.raises(ValidationError):
        ExperimentInput(local_path="irrelevant", name=path, sha256="0" * 64, source="contract")


def test_image_and_resource_bounds_are_predeclared():
    for image in ("python", "python:latest", "python:3.12 bad"):
        with pytest.raises(ValidationError):
            ExperimentEnvironment(image=image)
    with pytest.raises(ValidationError):
        ExperimentResources(cpu=3)
    with pytest.raises(ValidationError):
        ExperimentResources(command_seconds=180, lifetime_seconds=180)


def test_unknown_effect_network_operations_have_no_transport_retry():
    config = OpenSandboxBackend().connection()
    assert config.retry_policy.max_retries == 0
    assert config.disable_metrics is True
    assert config.debug is False


def test_attached_session_is_read_only_and_close_does_not_kill():
    sandbox = Mock(id="attached")
    attached = OpenSandboxSession(sandbox, owned=False)
    for operation in (
        lambda: attached.destroy(), lambda: attached.cancel("unowned-command"),
        lambda: attached.renew(30), lambda: attached.upload("/tmp/x", b"x"),
        lambda: attached.run(["echo", "x"], 1, "/tmp"),
        lambda: attached.start(["echo", "x"], 1, "/tmp"), lambda: attached.run_code("1+1"),
    ):
        with pytest.raises(PermissionError):
            operation()
    attached.close()
    sandbox.kill.assert_not_called()
    sandbox.close.assert_called_once()
    sandbox.commands.run.assert_not_called()


def test_owned_command_id_required_for_cancellation():
    sandbox = Mock(id="owned")
    session = OpenSandboxSession(sandbox, owned=True)
    with pytest.raises(PermissionError):
        session.cancel("other-command")
    sandbox.commands.interrupt.assert_not_called()
    session.command_ids.add("our-command")
    session.cancel("our-command")
    sandbox.commands.interrupt.assert_called_once_with("our-command")


def test_plan_roundtrip_preserves_missing_zero_and_unknown_semantics():
    root = Path(__file__).resolve().parents[2] / "demo/research_case"
    plan = public_case(root)
    assert ExperimentPlan.model_validate_json(plan.model_dump_json()) == plan
    assert plan.seed == 0 and plan.persistent_volume is None
    with pytest.raises(ValidationError):
        ExperimentContext(run_id="../other", task_id="x", worker_id="x", fencing_token=1)
