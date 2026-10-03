"""A probe reference must not admit a different actual configuration.

Only executor.prepare/admit run. The fixture create method always raises and
is never called; these are host configuration diagnostics, not a live probe.
"""
import pytest

from orchestration.experiments.generated import IsolationCapability, IsolationReport
from orchestration.experiments.generated_executor import GeneratedExperimentExecutor
from orchestration.experiments.trusted import IsolationProbeRecord, TrustedProbeRegistry
from tests.integration.r1_security.test_b_generated_boundaries import CODE, plan


def probe():
    values = dict(probe_id="configured-host-probe", backend="fixture",
        declared=IsolationCapability(**{key: True for key in IsolationCapability.model_fields}),
        verified=True, passed=True, evidence_ref="fixture-only-no-live-probe", probed_at=100)
    if "image_digest" in IsolationProbeRecord.model_fields:
        values["image_digest"] = "sha256:" + "c" * 64
    return IsolationProbeRecord(**values)


def test_conflicting_duplicate_probe_id_is_not_silently_replaced():
    original = probe()
    changed = original.model_copy(update={"evidence_ref": "different-fixture", "passed": False})
    with pytest.raises(ValueError):
        TrustedProbeRegistry(records=(original, changed))


def test_exact_probe_record_repeat_remains_constructible():
    original = probe()
    assert TrustedProbeRegistry(records=(original, original)) is not None


@pytest.mark.parametrize("changed", ["image", "cpu", "memory", "process", "endpoint", "network"])
def test_same_probe_reference_cannot_admit_changed_configuration(tmp_path, changed):
    original = probe()
    p = plan()
    p = p.model_copy(update={"environment": p.environment.model_copy(update={
        "image": "fixture@sha256:" + "c" * 64, "image_digest": "sha256:" + "c" * 64})})
    if changed == "image":
        p = p.model_copy(update={"environment": p.environment.model_copy(update={
            "image": "fixture@sha256:" + "d" * 64, "image_digest": "sha256:" + "d" * 64})})
    fields = {"cpu": "cpu", "memory": "memory_mib", "process": "process_limit"}
    if changed in fields:
        field = fields[changed]
        p = p.model_copy(update={"backend": p.backend.model_copy(update={field: getattr(p.backend, field) * 2})})

    class InertBackend:
        provenance = "mock"
        capabilities = frozenset({"script", "cpu", "memory", "duration"})
        domain = "different-host:1" if changed == "endpoint" else "configured-host:1"
        protocol = "http"
        network_deny = changed != "network"

        def isolation(self):
            # Caller-visible capability booleans/ref remain unchanged. Admission
            # must bind the host configuration, not trust those claims alone.
            return IsolationReport(backend="fixture", declared=original.declared,
                verified=True, probe="passed", proof_ref=original.probe_id)

        def create(self, *args, **kwargs):
            raise AssertionError("Q never creates a candidate sandbox")

    executor = GeneratedExperimentExecutor(InertBackend(), probe_registry=TrustedProbeRegistry(records=(original,)))
    preparation = executor.prepare(p, {"candidate.py": CODE})
    with pytest.raises((ValueError, PermissionError)):
        executor.admit(preparation)
