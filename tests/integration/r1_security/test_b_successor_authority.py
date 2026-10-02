"""Additional tests for B's successor host-owned authority API.

No real probe is run. Deterministic host fixture authority must be bound to its
exact reference; a different/missing caller reference cannot consume it.
"""
import pytest
import json
from types import SimpleNamespace

trusted = pytest.importorskip("orchestration.experiments.trusted",
                             reason="successor authority API absent in historical source")
from orchestration.experiments.generated import IsolationCapability, IsolationReport
from orchestration.experiments.security import verify_isolation
from tests.integration.r1_security.test_b_generated_boundaries import CODE, isolation, plan
from contracts.identity import AgentId, AttemptId
from local_assets.generated_validation import generated_candidate, generated_validation
from local_assets.store import LocalAssetStore


def candidate_store(root, *, p=None):
    candidate = generated_candidate(p if p is not None else plan(), {"candidate.py": CODE},
        attempt=AttemptId(task_id="t1", agent=AgentId(role="builder", instance=0), attempt=1),
        scope="science", summary="inert fixture")
    body = {"type": "Gene", "schema_version": "1.14.0", "id": "local_candidate", "category": "repair",
        "signals_match": ["local_candidate"], "strategy": [candidate.summary,
        "local_candidate_json:" + candidate.model_dump_json()],
        "constraints": {"max_files": 1, "forbidden_paths": [".git/**"]},
        "validation": ["local_assets.AssetValidator"], "asset_id": "candidate"}
    class InertFixtureBridge:
        # Only this exact trusted fixture is admitted. Production SDK validation
        # uses Node; Q forbids all child processes and does not test that bridge.
        def validate_asset(self, asset):
            return SimpleNamespace(valid=asset == body)

    store = LocalAssetStore(root / "assets", bridge=InertFixtureBridge())
    with store.connection() as db:
        db.execute("INSERT INTO assets VALUES (?,?)", ("candidate", json.dumps(body)))
    return store


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


def test_forged_passed_report_cannot_approve_recorded_failure(tmp_path):
    store = candidate_store(tmp_path)
    report = generated_validation(store, "candidate", plan(), {"candidate.py": CODE}, isolation())
    assert not report.passed
    forged = report.model_copy(update={"passed": True, "reasons": ()})
    try:
        store.approve_generated(forged, proof_ref="caller-invented-authority")
    except (ValueError, PermissionError):
        pass
    assert store.state("candidate") == "quarantined", "forged passed boolean bypassed stored failure and fencing"
    assert not store.generated_report(report.report_id).passed


def test_generated_validation_rejects_manifest_byte_substitution(tmp_path):
    store = candidate_store(tmp_path)
    capability = IsolationCapability(**{key: True for key in IsolationCapability.model_fields})
    record = trusted.IsolationProbeRecord(probe_id="host-probe", backend="fixture", declared=capability,
        verified=True, passed=True, evidence_ref="fixture-only", probed_at=100)
    registry = trusted.TrustedProbeRegistry(records=(record,))
    report = IsolationReport(backend="fixture", declared=capability, verified=True,
                             probe="passed", proof_ref="host-probe")
    try:
        result = generated_validation(store, "candidate", plan(), {"candidate.py": CODE + b"# changed\n"},
                                       report, probe_registry=registry)
    except (ValueError, PermissionError):
        return
    assert not result.passed, "validation admitted bytes outside the frozen manifest"
