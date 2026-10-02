"""Admission, apply and consume entrypoints for generated candidates (offline)."""

import hashlib
import json
from pathlib import Path

import pytest

from contracts.identity import AgentId, AttemptId
from local_assets.generated_validation import approve_generated, generated_candidate, generated_validation
from local_assets.store import LocalAssetStore
from tests.experiments.generated_helpers import (
    GENERATED_CODE, make_poisson_plan, mock_isolation, verified_probe_registry,
)

ATTEMPT = AttemptId(task_id="gen-task-1", agent=AgentId(role="builder", instance=0), attempt=1)


class FakeBridge:
    def compute_asset_id(self, asset):
        return hashlib.sha256(json.dumps(asset, sort_keys=True).encode()).hexdigest()

    def validate_asset(self, asset):
        from bridge_node.assets import AssetValidation
        return AssetValidation(valid=True, schema_valid=True, asset_id_valid=True,
                               schema_version="1.14.0", errors=[])

    def canonicalize(self, asset):
        return json.dumps(asset, sort_keys=True)


def _store(tmp_path: Path) -> LocalAssetStore:
    return LocalAssetStore(tmp_path / "store", bridge=FakeBridge())


def test_generated_validation_passes_with_host_verified_isolation(tmp_path):
    store = _store(tmp_path)
    plan = make_poisson_plan()
    candidate = generated_candidate(plan, {"experiment.py": GENERATED_CODE.encode()},
                                    attempt=ATTEMPT, scope="science", summary="poisson fd")
    asset_id = store.publish(candidate)
    report = generated_validation(store, asset_id, plan, {"experiment.py": GENERATED_CODE.encode()},
                                  mock_isolation(), probe_registry=verified_probe_registry())
    assert report.passed and report.static.passed
    approve_generated(store, report)
    assert store.state(asset_id) == "approved"
    assert store.fetch_approved(asset_id) == candidate


def test_generated_validation_fails_closed_without_host_probe(tmp_path):
    store = _store(tmp_path)
    plan = make_poisson_plan()
    candidate = generated_candidate(plan, {"experiment.py": GENERATED_CODE.encode()},
                                    attempt=ATTEMPT, scope="science", summary="poisson fd")
    asset_id = store.publish(candidate)
    report = generated_validation(store, asset_id, plan, {"experiment.py": GENERATED_CODE.encode()},
                                  mock_isolation(), probe_registry=None)
    assert not report.passed
    assert "isolation_capability_unverified" in report.reasons
    assert store.state(asset_id) == "quarantined"


def test_generated_validation_rejects_dangerous_code(tmp_path):
    store = _store(tmp_path)
    dangerous = "import os\n" + GENERATED_CODE
    plan = make_poisson_plan(code=dangerous.encode())
    candidate = generated_candidate(plan, {"experiment.py": dangerous.encode()},
                                    attempt=ATTEMPT, scope="science", summary="dangerous")
    asset_id = store.publish(candidate)
    report = generated_validation(store, asset_id, plan, {"experiment.py": dangerous.encode()},
                                  mock_isolation(), probe_registry=verified_probe_registry())
    assert not report.passed and not report.static.passed
    assert any("danger" in reason for reason in report.static.reasons)


def test_approval_requires_ownership_fence(tmp_path):
    store = _store(tmp_path)
    plan = make_poisson_plan()
    candidate = generated_candidate(plan, {"experiment.py": GENERATED_CODE.encode()},
                                    attempt=ATTEMPT, scope="science", summary="poisson fd")
    asset_id = store.publish(candidate)
    report = generated_validation(store, asset_id, plan, {"experiment.py": GENERATED_CODE.encode()},
                                  mock_isolation(), probe_registry=verified_probe_registry())

    def reject():
        raise AssertionError("ownership fence not held")

    with pytest.raises(AssertionError):
        approve_generated(store, report, reject)
    assert store.state(asset_id) == "quarantined"


def test_generated_candidate_builds_consistent_candidate():
    plan = make_poisson_plan()
    candidate = generated_candidate(plan, {"experiment.py": GENERATED_CODE.encode()},
                                    attempt=ATTEMPT, scope="science", summary="poisson fd")
    assert candidate.declared_files == 1
    assert candidate.changes[0].path == "science/experiment.py"
    assert candidate.changes[0].after == GENERATED_CODE
    from local_assets.validate import inspect_candidate
    inspect_candidate(candidate)
