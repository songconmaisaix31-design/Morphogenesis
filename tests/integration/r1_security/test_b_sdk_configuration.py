"""Intercept trusted SDK configuration without any sandbox or candidate run."""
from types import SimpleNamespace

import pytest

from orchestration.experiments import sandbox_adapter as adapter
from orchestration.experiments.backend import UnsupportedCapability
from orchestration.experiments.security import SecurityRejection
from tests.integration.r1_security.test_b_generated_boundaries import context, plan


@pytest.mark.parametrize("control", ["image", "network"])
def test_sdk_configuration_matches_frozen_image_and_network(tmp_path, monkeypatch, control):
    calls = []

    def capture(image, **kwargs):
        calls.append((image, kwargs))
        return SimpleNamespace(id="fixture-only-no-sandbox")

    monkeypatch.setattr(adapter.SandboxSync, "create", capture)
    p = plan()
    p = p.model_copy(update={"environment": p.environment.model_copy(
        update={"image_digest": "sha256:" + "c" * 64})})
    backend = adapter.LocalCpuSandboxBackend(domain="127.0.0.1:65534")
    try:
        backend.create(p, context())
    except (UnsupportedCapability, SecurityRejection, PermissionError):
        assert not calls, "refusal followed a remote create"
        return
    assert len(calls) == 1
    image, options = calls[0]
    if control == "image":
        assert image == "fixture@sha256:" + "c" * 64, "SDK image omitted frozen repository/digest binding"
    else:
        policy = options.get("network_policy")
        assert policy is not None, "deny network declared but SDK create has no egress policy"
        payload = policy.model_dump(mode="json") if hasattr(policy, "model_dump") else policy
        assert payload.get("default_action") == "deny"


def test_unverified_process_limit_cannot_reach_sdk_creation(monkeypatch):
    calls = []

    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(id="fixture-only-no-sandbox")

    monkeypatch.setattr(adapter.SandboxSync, "create", capture)
    backend = adapter.LocalCpuSandboxBackend(domain="127.0.0.1:65534")
    try:
        backend.create(plan(), context())
    except (UnsupportedCapability, SecurityRejection, PermissionError):
        pass
    assert calls == [], "backend created without trusted process-limit/isolation instance verification"
