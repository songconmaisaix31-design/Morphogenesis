"""Additional tests for B's successor host-owned authority API.

No real probe is run. Deterministic host fixture authority must be bound to its
exact reference; a different/missing caller reference cannot consume it.
"""
import pytest

trusted = pytest.importorskip("orchestration.experiments.trusted",
                             reason="successor authority API absent in historical source")
from orchestration.experiments.generated import IsolationCapability, IsolationReport
from orchestration.experiments.security import verify_isolation


@pytest.mark.parametrize("proof_ref", [None, "invented-probe"])
def test_registered_probe_cannot_authorize_different_or_missing_reference(proof_ref):
    capability = IsolationCapability(**{key: True for key in IsolationCapability.model_fields})
    record = trusted.IsolationProbeRecord(probe_id="host-probe", backend="fixture",
        declared=capability, verified=True, passed=True, evidence_ref="fixture-only-no-live-claim", probed_at=100)
    registry = trusted.TrustedProbeRegistry(records=(record,))
    report = IsolationReport(backend="fixture", declared=capability, verified=True,
                             probe="passed", proof_ref=proof_ref)
    with pytest.raises(ValueError):
        verify_isolation(report, registry)
