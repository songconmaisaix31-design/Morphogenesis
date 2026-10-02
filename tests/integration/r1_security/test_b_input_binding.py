"""Manifest and asset binding; only inert bytes and prepare/validate run."""
import hashlib

import pytest

from local_assets.generated_validation import generated_validation
from orchestration.experiments.generated import GeneratedFile, IsolationCapability, IsolationReport
from orchestration.experiments.generated_executor import GeneratedExperimentExecutor
from orchestration.experiments.trusted import IsolationProbeRecord, TrustedProbeRegistry
from tests.integration.r1_security.test_b_generated_boundaries import CODE, NoRunBackend, plan
from tests.integration.r1_security.test_b_successor_authority import candidate_store


def manifest(name, body):
    return GeneratedFile(name=name, sha256=hashlib.sha256(body).hexdigest(),
                         size_bytes=len(body), source="q-inert-fixture")


@pytest.mark.parametrize("attack", ["code_overlap", "runner_name", "duplicate_data", "total_size"])
def test_data_cannot_replace_code_runner_or_escape_manifest_limits(attack):
    name = "candidate.py" if attack == "code_overlap" else "data.json"
    if attack == "runner_name":
        name = "parameters.json"
    body = b"# inert substitution, never executed\n" if attack == "code_overlap" else b"{}"
    if attack == "total_size":
        body = b" " * 1024
    entries = (manifest(name, body),)
    if attack == "duplicate_data":
        entries = entries + entries
    p = plan(data=entries)
    if attack == "total_size":
        p = p.model_copy(update={"backend": p.backend.model_copy(update={"artifact_bytes": 1024})})
    backend = NoRunBackend()
    try:
        prepared = GeneratedExperimentExecutor(backend).prepare(p, {"candidate.py": CODE}, {name: body})
    except ValueError:
        return
    assert not prepared.static.passed, "unsafe data passed preparation before the independent isolation gate"
    assert backend.create_calls == 0


def test_disjoint_bound_inert_data_retains_static_admission():
    body = b"{}"
    p = plan(data=(manifest("data.json", body),))
    backend = NoRunBackend()
    prepared = GeneratedExperimentExecutor(backend).prepare(p, {"candidate.py": CODE}, {"data.json": body})
    assert prepared.static.passed
    assert prepared.files == {"candidate.py": CODE}
    assert prepared.data == {"data.json": body}
    assert backend.create_calls == 0


def host_fixture_probe():
    # Deterministic host authority for a fixture backend, never a live probe.
    capability = IsolationCapability(**{key: True for key in IsolationCapability.model_fields})
    record = IsolationProbeRecord(probe_id="asset-binding-fixture", backend="fixture", declared=capability,
        verified=True, passed=True, evidence_ref="q-contract-local-only", probed_at=100)
    report = IsolationReport(backend="fixture", declared=capability, proof_ref=record.probe_id)
    return report, TrustedProbeRegistry(records=(record,))


@pytest.mark.parametrize("changed", ["asset_id", "revision", "persisted_bytes"])
def test_generated_validation_binds_the_actual_persisted_candidate(tmp_path, changed):
    store = candidate_store(tmp_path)
    isolation, registry = host_fixture_probe()
    p = plan()
    files = {"candidate.py": CODE}
    positive = generated_validation(store, "candidate", p, files, isolation, probe_registry=registry)
    assert positive.passed, "valid persisted candidate control must reach the same validation boundary"
    if changed == "asset_id":
        p = p.model_copy(update={"candidate_asset_id": "different-asset"})
    elif changed == "revision":
        p = p.model_copy(update={"candidate_revision": "b" * 40})
    else:
        files = {"candidate.py": CODE + b"# different inert asset\n"}
        p = p.model_copy(update={"files": (manifest("candidate.py", files["candidate.py"]),)})
    try:
        report = generated_validation(store, "candidate", p, files, isolation, probe_registry=registry)
    except (ValueError, PermissionError):
        return
    assert not report.passed, "validation certified a different asset identity/revision/byte payload"
    assert store.state("candidate") == "quarantined"
