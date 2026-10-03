"""SDK requests are intercepted; fixture probes never create a sandbox or run code."""

from dataclasses import replace
import os
import socket
import subprocess
from types import SimpleNamespace

import pytest

from orchestration.experiments import sandbox_adapter as adapter
from orchestration.experiments.generated import effective_environment
from orchestration.experiments.generated_executor import GeneratedExperimentExecutor
from orchestration.experiments.trusted import IsolationProbeRecord, TrustedProbeRegistry
from tests.experiments.generated_helpers import (
    GENERATED_CODE, IMAGE_DIGEST, MockGeneratedBackend, full_capability, make_context,
    make_poisson_plan, probe_record, verified_probe_registry,
)


@pytest.fixture(autouse=True)
def no_execution_or_network(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("fixture forbids processes and network")
    monkeypatch.setattr(subprocess, "Popen", denied)
    monkeypatch.setattr(os, "system", denied)
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket.socket, "connect_ex", denied)
    # This file isolates request/probe binding against a hypothetical supported
    # exporter. Current production support is False and separately tested in
    # test_at07_export; this fixture never proves live export/AT07 availability.
    monkeypatch.setattr(adapter, "ATOMIC_EXPORT_SCOPE_SUPPORTED", True)


def configured_backend(plan):
    settings = dict(domain="127.0.0.1:65534", instance_id="fixture-deployment-1",
                    runtime_profile="fixture-linux-pids16-v1", server_process_limit=16)
    configuration = adapter.LocalCpuSandboxBackend(**settings).configuration(plan)
    record = IsolationProbeRecord(probe_id="fixture-probe", backend="opensandbox",
        declared=full_capability(), image_digest=IMAGE_DIGEST, configuration=configuration,
        verified=True, passed=True, evidence_ref="inert-fixture-not-live-probe", probed_at=100)
    return adapter.LocalCpuSandboxBackend(**settings, probe=record), record


def test_supported_configuration_reaches_sdk_with_real_deny_and_repository_digest(monkeypatch):
    plan = make_poisson_plan()
    plan = plan.model_copy(update={"environment": plan.environment.model_copy(update={"image": "fixture:tag"})})
    backend, record = configured_backend(plan)
    calls = []
    def capture(image, **kwargs):
        calls.append((image, kwargs))
        return SimpleNamespace(id="inert-sdk-return")
    monkeypatch.setattr(adapter.SandboxSync, "create", capture)
    executor = GeneratedExperimentExecutor(backend, probe_registry=TrustedProbeRegistry((record,)))
    executor.admit(executor.prepare(plan, {"experiment.py": GENERATED_CODE.encode()}))
    session = backend.create(plan, make_context())
    assert session.id == "inert-sdk-return"
    assert len(calls) == 1  # Refusal is not a passing SDK-configuration test.
    image, options = calls[0]
    assert image == "fixture@" + IMAGE_DIGEST
    assert options["network_policy"].model_dump(mode="json")["default_action"] == "deny"
    assert options["resource"] == {"cpu": "1", "memory": "512Mi"}
    assert options["connection_config"].domain == "127.0.0.1:65534"
    assert options["connection_config"].protocol == "http"
    assert "volumes" not in options and "credential_proxy" not in options


@pytest.mark.parametrize("change", ["endpoint", "instance", "runtime", "network", "process", "image",
    "lock", "python", "sdk", "backend", "cpu", "memory", "duration", "lifetime", "export", "digest"])
def test_exact_probe_binding_rejects_changed_effective_configuration(monkeypatch, change):
    plan = make_poisson_plan()
    backend, record = configured_backend(plan)
    calls = []
    monkeypatch.setattr(adapter.SandboxSync, "create", lambda *a, **k: calls.append((a, k)))
    if change == "endpoint":
        backend._opensandbox.domain = "different-host:1"
    elif change == "instance":
        backend._instance_id = "different-instance"
    elif change == "runtime":
        backend._runtime_profile = "different-runtime"
    elif change == "network":
        backend._network_deny = False
    elif change == "process":
        backend._server_process_limit = 17
    elif change == "digest":
        record = record.model_copy(update={"image_digest": "sha256:" + "e" * 64})
        backend._probe = record
    else:
        fields = {"cpu": ("cpu", 2), "memory": ("memory_mib", 1024), "duration": ("command_seconds", 29),
                  "lifetime": ("lifetime_seconds", 179), "export": ("artifact_bytes", 1024)}
        if change in fields:
            key, value = fields[change]
            plan = plan.model_copy(update={"backend": plan.backend.model_copy(update={key: value})})
        else:
            edits = {"image": {"image": "other@sha256:" + "d" * 64, "image_digest": "sha256:" + "d" * 64},
                "lock": {"dependency_lock_sha256": "d" * 64}, "python": {"python_version": "3.13"},
                "sdk": {"sdk_version": "9.0.0"}, "backend": {"backend": "other"}}[change]
            plan = plan.model_copy(update={"environment": plan.environment.model_copy(update=edits)})
    with pytest.raises((ValueError, PermissionError)):
        backend.create(plan, make_context())
    assert calls == []


def test_prepare_admit_rechecks_backend_configuration(tmp_path):
    plan = make_poisson_plan()
    backend, record = configured_backend(plan)
    executor = GeneratedExperimentExecutor(backend, probe_registry=TrustedProbeRegistry((record,)))
    prepared = executor.prepare(plan, {"experiment.py": GENERATED_CODE.encode()})
    executor.admit(prepared)
    backend._opensandbox.protocol = "https"
    with pytest.raises(ValueError, match="prepared_configuration_changed"):
        executor.admit(prepared)


def test_prepared_code_cannot_bypass_static_or_manifest_checks(tmp_path):
    plan = make_poisson_plan()
    executor = GeneratedExperimentExecutor(MockGeneratedBackend(tmp_path), probe_registry=verified_probe_registry())
    prepared = executor.prepare(plan, {"experiment.py": GENERATED_CODE.encode()})
    forged = replace(prepared, files={"experiment.py": b"import os\n"})
    with pytest.raises(ValueError, match="manifest_digest_mismatch"):
        executor.admit(forged)


def test_probe_duplicate_and_dead_digest_are_checked():
    original = probe_record()
    TrustedProbeRegistry((original, original))
    with pytest.raises(ValueError, match="probe_id_conflict"):
        TrustedProbeRegistry((original, original.model_copy(update={"evidence_ref": "changed"})))


def test_missing_process_control_and_probe_cannot_create(monkeypatch):
    calls = []
    monkeypatch.setattr(adapter.SandboxSync, "create", lambda *a, **k: calls.append((a, k)))
    backend = adapter.LocalCpuSandboxBackend(instance_id="unverified", runtime_profile="unknown", server_process_limit=16)
    assert backend.isolation().declared.process_limit is False
    with pytest.raises(ValueError):
        backend.create(make_poisson_plan(), make_context())
    assert calls == []


def test_image_digest_conflict_is_not_silently_rewritten():
    environment = make_poisson_plan().environment.model_copy(update={"image_digest": "sha256:" + "d" * 64})
    with pytest.raises(ValueError, match="image_digest_mismatch"):
        effective_environment(environment)
