"""Installed mock adapter is usable without importing test-only backends."""

import os
import socket
import subprocess

import pytest

from orchestration.experiments.fixture import GeneratedFixtureBackend
from orchestration.experiments.generated_executor import GeneratedExperimentExecutor, read_generated_result
from orchestration.experiments.sandbox_adapter import LocalCpuSandboxBackend
from tests.experiments.generated_helpers import (
    GENERATED_CODE, approved_criteria_registry, make_context, make_poisson_plan, poisson_reference_output,
)


@pytest.fixture(autouse=True)
def no_process_or_network(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("installed fixture may not launch a process or access network")
    monkeypatch.setattr(subprocess, "Popen", denied)
    monkeypatch.setattr(os, "system", denied)
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket.socket, "connect_ex", denied)


@pytest.mark.parametrize("outcome,state,hypothesis", [
    ("succeeded", "succeeded", "supported"), ("failed", "failed", "not_evaluated"),
    ("timeout", "timeout", "not_evaluated"), ("unknown", "unknown", "not_evaluated"),
])
def test_installed_fixture_fixed_output_and_failure_states(tmp_path, outcome, state, hypothesis):
    plan = make_poisson_plan()
    backend = GeneratedFixtureBackend(environment=plan.environment, resources=plan.backend,
        output=poisson_reference_output(100), instance_id="fixture-1", outcome=outcome)
    executor = GeneratedExperimentExecutor(backend, probe_registry=backend.probe_registry,
        criteria_registry=approved_criteria_registry(plan.evaluation))
    result = executor.execute(plan, make_context(), {"experiment.py": GENERATED_CODE.encode()}, tmp_path)
    assert result.provenance == "mock" and result.execution_state == state
    assert result.assessment.hypothesis == hypothesis
    assert result.cleanup_state == "destroyed"
    loaded = read_generated_result(tmp_path, make_context().run_id, expected_plan=plan)
    assert loaded.provenance == "mock" and loaded.execution_state == state
    if outcome == "unknown":
        assert loaded.remote_effect == "unknown"
        with pytest.raises(FileExistsError):
            executor.execute(plan, make_context(), {"experiment.py": GENERATED_CODE.encode()}, tmp_path)


def test_fixture_host_configuration_cannot_follow_changed_plan(tmp_path):
    plan = make_poisson_plan()
    backend = GeneratedFixtureBackend(environment=plan.environment, resources=plan.backend,
                                     output=None, instance_id="fixture-1")
    altered = plan.model_copy(update={"backend": plan.backend.model_copy(update={"memory_mib": 1024})})
    executor = GeneratedExperimentExecutor(backend, probe_registry=backend.probe_registry)
    with pytest.raises(ValueError, match="configuration_mismatch"):
        executor.admit(executor.prepare(altered, {"experiment.py": GENERATED_CODE.encode()}))


def test_fixture_record_never_authorizes_real_adapter():
    plan = make_poisson_plan()
    fixture = GeneratedFixtureBackend(environment=plan.environment, resources=plan.backend,
                                     output=None, instance_id="fixture-1")
    real = LocalCpuSandboxBackend(probe=fixture._probe, instance_id="fixture-1",
                                 runtime_profile="fixed-output-fixture-v1", server_process_limit=16)
    assert not real.isolation().declared.process_limit
    with pytest.raises(ValueError):
        real.create(plan, make_context())
