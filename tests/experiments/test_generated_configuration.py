"""SDK requests are intercepted; fixture probes never create a sandbox or run code."""

from dataclasses import replace
import os
import socket
import subprocess
from types import SimpleNamespace

import pytest

from orchestration.experiments import sandbox_adapter as adapter
from orchestration.experiments.generated import DockerExportConfiguration, effective_environment
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


def configured_backend(plan, *, frozen_export=True, api_version="1.52"):
    settings = dict(domain="127.0.0.1:65534", instance_id="fixture-deployment-1",
                    runtime_profile="fixture-linux-pids16-v1", server_process_limit=16)
    if frozen_export:
        settings["docker_export"] = DockerExportConfiguration(endpoint="npipe:////./pipe/dockerDesktopLinuxEngine",
            daemon_id="inert-daemon-1", engine_version="29.5.3", api_version=api_version)
    configuration = adapter.LocalCpuSandboxBackend(**settings).configuration(plan)
    record = IsolationProbeRecord(probe_id="fixture-probe", backend="opensandbox",
        declared=full_capability(), image_digest=IMAGE_DIGEST, configuration=configuration,
        verified=True, passed=True, evidence_ref="inert-fixture-not-live-probe", probed_at=100)
    return adapter.LocalCpuSandboxBackend(**settings, probe=record), record


@pytest.mark.parametrize("api_version", ["1.52", "1.54"])
def test_supported_configuration_reaches_sdk_with_real_deny_and_repository_digest(monkeypatch, api_version):
    plan = make_poisson_plan()
    plan = plan.model_copy(update={"environment": plan.environment.model_copy(update={"image": "fixture:tag"})})
    backend, record = configured_backend(plan, api_version=api_version)
    calls = []
    def capture(image, **kwargs):
        calls.append((image, kwargs))
        return SimpleNamespace(id="inert-sdk-return")
    monkeypatch.setattr(adapter.SandboxSync, "create", capture)
    preflight = []
    def control(config):
        assert config.docker_export == backend._docker_export
        return SimpleNamespace(preflight=lambda: preflight.append(config), close=lambda: None)
    monkeypatch.setattr(adapter, "FrozenDockerExport", control)
    executor = GeneratedExperimentExecutor(backend, probe_registry=TrustedProbeRegistry((record,)))
    executor.admit(executor.prepare(plan, {"experiment.py": GENERATED_CODE.encode()}))
    session = backend.create(plan, make_context())
    assert session.id == "inert-sdk-return"
    assert len(calls) == 1  # Refusal is not a passing SDK-configuration test.
    assert len(preflight) == 1
    assert preflight[0].docker_export.api_version == api_version
    image, options = calls[0]
    assert image == "fixture@" + IMAGE_DIGEST
    assert options["network_policy"].model_dump(mode="json")["default_action"] == "deny"
    assert options["resource"] == {"cpu": "1", "memory": "512Mi"}
    assert options["connection_config"].domain == "127.0.0.1:65534"
    assert options["connection_config"].protocol == "http"
    assert "volumes" not in options and "credential_proxy" not in options


@pytest.mark.parametrize("change", ["endpoint", "instance", "runtime", "network", "process", "image",
    "lock", "python", "sdk", "backend", "cpu", "memory", "duration", "lifetime", "export", "digest",
    "docker_endpoint", "docker_daemon", "docker_version", "docker_api"])
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
    elif change.startswith("docker_"):
        key, value = {"docker_endpoint": ("endpoint", "unix:///var/run/docker.sock"),
            "docker_daemon": ("daemon_id", "other-daemon"), "docker_version": ("engine_version", "29.5.4"),
            "docker_api": ("api_version", "1.54")}[change]
        backend._docker_export = backend._docker_export.model_copy(update={key: value})
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


def test_export_api_schema_keeps_legacy_default_and_explicit_closed_set():
    values = dict(endpoint="npipe:////./pipe/dockerDesktopLinuxEngine", daemon_id="inert-daemon-1", engine_version="29.5.3")
    assert DockerExportConfiguration(**values).api_version == "1.52"
    assert DockerExportConfiguration(**values, api_version="1.54").api_version == "1.54"
    schema = DockerExportConfiguration.model_json_schema()["properties"]["api_version"]
    assert schema["default"] == "1.52" and schema["enum"] == ["1.52", "1.54"]


@pytest.mark.parametrize("api_version", ["1.20", "1.53", "1.55", "auto", "", 1.54])
def test_unapproved_export_api_is_rejected(api_version):
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        DockerExportConfiguration(endpoint="npipe:////./pipe/dockerDesktopLinuxEngine",
            daemon_id="inert-daemon-1", engine_version="29.5.3", api_version=api_version)


def test_probe_with_154_cannot_admit_legacy_152_or_changed_record(monkeypatch):
    plan = make_poisson_plan()
    backend, record = configured_backend(plan, api_version="1.54")
    changed = record.configuration.model_copy(update={"docker_export": DockerExportConfiguration(
        **{**record.configuration.docker_export.model_dump(), "api_version": "1.52"})})
    with pytest.raises(ValueError, match="probe_id_conflict"):
        TrustedProbeRegistry((record, record.model_copy(update={"configuration": changed})))
    backend._docker_export = changed.docker_export
    calls = []
    monkeypatch.setattr(adapter.SandboxSync, "create", lambda *a, **k: calls.append((a, k)))
    with pytest.raises((ValueError, PermissionError)):
        backend.create(plan, make_context())
    assert calls == []
