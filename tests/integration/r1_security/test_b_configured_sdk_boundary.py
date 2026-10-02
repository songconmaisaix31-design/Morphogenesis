"""Supported SDK request positive plus exact host-configuration substitutions.

The only SDK create is a capture returning an inert ID. No network, sandbox,
candidate or probe runs; the record is deterministic contract_local authority.
"""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from orchestration.experiments import sandbox_adapter as adapter
from orchestration.experiments.generated import IsolationCapability, IsolationConfiguration
from orchestration.experiments.generated_executor import GeneratedExperimentExecutor
from orchestration.experiments.trusted import IsolationProbeRecord, TrustedProbeRegistry
from tests.integration.r1_security.test_b_generated_boundaries import CODE, context, plan


def configured():
    p = plan()
    p = p.model_copy(update={"environment": p.environment.model_copy(update={
        "image": "fixture@sha256:" + "c" * 64, "image_digest": "sha256:" + "c" * 64})})
    config = IsolationConfiguration(endpoint="http://127.0.0.1:65534", instance_id="q-inert-instance",
        runtime_profile="q-probed-fixed-policy", environment=p.environment, resources=p.backend,
        network_deny=True, server_process_limit=p.backend.process_limit, use_server_proxy=True)
    probe = IsolationProbeRecord(probe_id="q-configured-fixture", backend="opensandbox",
        declared=IsolationCapability(**{key: True for key in IsolationCapability.model_fields}),
        configuration=config, image_digest=p.environment.image_digest,
        verified=True, passed=True, evidence_ref="q-fixture-only-not-live", probed_at=100)
    options = dict(domain="127.0.0.1:65534", protocol="http", network_deny=True,
        probe=probe, instance_id=config.instance_id, runtime_profile=config.runtime_profile,
        server_process_limit=config.server_process_limit)
    return p, probe, options


def capture_create(monkeypatch):
    calls = []

    def create(image, **kwargs):
        calls.append((image, kwargs))
        return SimpleNamespace(id="q-captured-request-no-sandbox")

    monkeypatch.setattr(adapter.SandboxSync, "create", create)
    return calls


def test_fully_bound_host_configuration_reaches_correct_sdk_request(monkeypatch):
    calls = capture_create(monkeypatch)
    p, probe, options = configured()
    backend = adapter.LocalCpuSandboxBackend(**options)
    executor = GeneratedExperimentExecutor(backend, probe_registry=TrustedProbeRegistry(records=(probe,)))
    prepared = executor.prepare(p, {"candidate.py": CODE})
    executor.admit(prepared)
    session = backend.create(p, context())
    assert session.id == "q-captured-request-no-sandbox"
    assert len(calls) == 1, "valid host configuration must reach the real adapter's SDK request boundary"
    image, request = calls[0]
    assert image == p.environment.image
    assert request["resource"] == {"cpu": str(p.backend.cpu), "memory": f"{p.backend.memory_mib}Mi"}
    policy = request["network_policy"].model_dump(mode="json")
    assert policy["default_action"] == "deny"
    assert request["timeout"].total_seconds() == p.backend.lifetime_seconds
    assert request["metadata"]["morph-task"] == p.task_id
    assert request["metadata"]["morph-fence"] == str(context().fencing_token)


@pytest.mark.parametrize("field", [
    "image", "dependency_lock", "cpu", "memory_mib", "process_limit", "command_seconds",
    "lifetime_seconds", "endpoint", "network", "instance", "runtime", "server_process_limit",
])
def test_verified_probe_cannot_be_reused_for_changed_effective_request(monkeypatch, field):
    calls = capture_create(monkeypatch)
    p, probe, options = configured()
    if field == "image":
        p = p.model_copy(update={"environment": p.environment.model_copy(update={
            "image": "fixture@sha256:" + "d" * 64, "image_digest": "sha256:" + "d" * 64})})
    elif field == "dependency_lock":
        p = p.model_copy(update={"environment": p.environment.model_copy(
            update={"dependency_lock_sha256": "d" * 64})})
    elif field in {"cpu", "memory_mib", "process_limit", "command_seconds", "lifetime_seconds"}:
        p = p.model_copy(update={"backend": p.backend.model_copy(update={field: getattr(p.backend, field) * 2})})
    else:
        changes = {"endpoint": ("domain", "127.0.0.1:65533"), "network": ("network_deny", False),
            "instance": ("instance_id", "different-instance"), "runtime": ("runtime_profile", "different-runtime"),
            "server_process_limit": ("server_process_limit", 32)}
        key, value = changes[field]
        options[key] = value
    backend = adapter.LocalCpuSandboxBackend(**options)
    with pytest.raises((ValueError, PermissionError)):
        backend.create(p, context())
    assert calls == [], "changed host configuration reached SDK create"


@pytest.mark.parametrize("change", ["input_bytes", "configuration"])
def test_preparation_mutation_is_rechecked_before_admission(change):
    p, probe, options = configured()
    backend = adapter.LocalCpuSandboxBackend(**options)
    executor = GeneratedExperimentExecutor(backend, probe_registry=TrustedProbeRegistry(records=(probe,)))
    prepared = executor.prepare(p, {"candidate.py": CODE})
    executor.admit(prepared)
    if change == "input_bytes":
        prepared.files["candidate.py"] = CODE + b"# replacement never executed\n"
    else:
        prepared = replace(prepared, plan=p.model_copy(update={
            "backend": p.backend.model_copy(update={"cpu": 2})}))
    with pytest.raises((ValueError, PermissionError)):
        executor.admit(prepared)
