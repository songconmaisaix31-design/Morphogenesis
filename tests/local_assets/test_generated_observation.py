"""Original asset/report persistence with inert mock outputs, never live science."""

import json
import os
import socket
import subprocess

import pytest

from contracts.identity import AgentId, AttemptId
from local_assets.generated_validation import (
    generated_candidate, generated_conditions, read_generated_observation, record_generated_observation,
)
from orchestration.experiments.generated_executor import GeneratedExperimentExecutor
from orchestration.experiments.trusted import TrustedCriteriaRecord, TrustedCriteriaRegistry
from tests.experiments.generated_helpers import (
    GENERATED_CODE, MockGeneratedBackend, approved_criteria_registry, make_context, make_poisson_plan,
    poisson_reference_output, poisson_wrong_output, verified_probe_registry,
)
from tests.local_assets.test_generated_validation import ATTEMPT, _store


@pytest.fixture(autouse=True)
def no_execution_or_network(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("fixture forbids processes and network")
    monkeypatch.setattr(subprocess, "Popen", denied)
    monkeypatch.setattr(os, "system", denied)
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket.socket, "connect_ex", denied)


def setup(tmp_path, *, refuted=False, entry_exit_code=0, frozen=True):
    store = _store(tmp_path)
    plan = make_poisson_plan()
    candidate = generated_candidate(plan, {"experiment.py": GENERATED_CODE.encode()},
                                    attempt=ATTEMPT, scope="science", summary="inert fixture")
    asset_id = store.publish(candidate)
    plan = plan.model_copy(update={"candidate_asset_id": asset_id})
    context = make_context()
    registry = approved_criteria_registry(plan.evaluation, approved_by=context.reviewer)
    backend = MockGeneratedBackend(tmp_path / "work", entry_exit_code=entry_exit_code,
        output=poisson_wrong_output(100) if refuted else poisson_reference_output(100))
    executor = GeneratedExperimentExecutor(backend, probe_registry=verified_probe_registry(),
                                          criteria_registry=registry if frozen else None)
    executor.execute(plan, context, {"experiment.py": GENERATED_CODE.encode()}, tmp_path / "archive")
    kwargs = dict(archive_root=tmp_path / "archive", plan=plan, context=context, purpose="original",
        criteria_registry=registry, assert_owned=lambda: None, source_swarm_id="fixture-swarm",
        source_attempt=ATTEMPT, source_fencing_token=1)
    return store, asset_id, registry, kwargs


@pytest.mark.parametrize("refuted", [False, True])
def test_original_result_is_persisted_and_purely_reread(tmp_path, refuted):
    store, asset, registry, kwargs = setup(tmp_path, refuted=refuted)
    report = record_generated_observation(store, asset, **kwargs)
    assert store.research_reports(asset) == [report]
    assert record_generated_observation(store, asset, **kwargs) == report
    payload = json.loads(report.result_json)
    assert report.scientific_verdict == ("failed" if refuted else "passed")
    assert payload["generated_assessment"]["mode"] == "final"
    assert payload["generated_assessment"]["contribution"] == "proposed"
    assert report.provenance == "mock" and payload["provenance"] == "mock"
    result = read_generated_observation(report, criteria_registry=registry)
    assert result.assessment.hypothesis == ("refuted" if refuted else "supported")
    assert result.provenance == "mock"
    assert store.state(asset) == "quarantined" and not store.adoptions()


def test_approval_after_execution_cannot_finalize_old_output(tmp_path):
    store, asset, registry, kwargs = setup(tmp_path, frozen=False)
    report = record_generated_observation(store, asset, **kwargs)
    assert report.scientific_verdict == "not_evaluated"
    assert json.loads(report.result_json)["criteria_approval"] is None
    assert read_generated_observation(report, criteria_registry=registry).assessment.mode == "diagnostic"


def test_failed_execution_never_becomes_refutation(tmp_path):
    store, asset, registry, kwargs = setup(tmp_path, entry_exit_code=2, refuted=True)
    report = record_generated_observation(store, asset, **kwargs)
    assert report.execution_state == "failed" and report.scientific_verdict == "not_evaluated"
    result = read_generated_observation(report, criteria_registry=registry)
    assert result.assessment.hypothesis == "not_evaluated"


def test_stale_fence_rolls_back_observation(tmp_path):
    store, asset, _, kwargs = setup(tmp_path)
    calls = []
    def ownership():
        calls.append(1)
        if len(calls) == 3:
            raise PermissionError("expired fence")
    with pytest.raises(PermissionError):
        record_generated_observation(store, asset, **dict(kwargs, assert_owned=ownership))
    assert not store.research_reports(asset)


@pytest.mark.parametrize("field", ["generated_assessment", "criteria_approval", "candidate", "plan", "source_attempt"])
def test_forged_persisted_scientific_fields_are_rejected(tmp_path, field):
    store, asset, registry, kwargs = setup(tmp_path)
    report = record_generated_observation(store, asset, **kwargs)
    if field in {"generated_assessment", "criteria_approval"}:
        body = json.loads(report.result_json)
        if field == "generated_assessment":
            body[field]["hypothesis"] = "refuted"
        else:
            body[field]["approved_by"] = "invented"
        report = report.model_copy(update={"result_json": json.dumps(body)})
    elif field == "candidate":
        candidate = json.loads(report.candidate_json)
        candidate["changes"][0]["after"] = "# replaced\n"
        report = report.model_copy(update={"candidate_json": json.dumps(candidate)})
    elif field == "plan":
        report = report.model_copy(update={"plan_json": kwargs["plan"].model_copy(update={"authorization_ref": "other"}).model_dump_json()})
    else:
        report = report.model_copy(update={"source_attempt": ATTEMPT.model_copy(update={"task_id": "other"})})
    with pytest.raises(ValueError):
        read_generated_observation(report, criteria_registry=registry)


def test_reproduction_uses_current_execution_attempt_and_original_candidate(tmp_path):
    store, asset, registry, kwargs = setup(tmp_path)
    record_generated_observation(store, asset, **kwargs)
    plan = kwargs["plan"].model_copy(update={"task_id": "reproduction"})
    context = make_context(task_id="reproduction", run_id="new-run").model_copy(update={"worker_id": "peer"})
    executor = GeneratedExperimentExecutor(MockGeneratedBackend(tmp_path / "peer", output=poisson_reference_output(100)),
        probe_registry=verified_probe_registry(), criteria_registry=registry)
    executor.execute(plan, context, {"experiment.py": GENERATED_CODE.encode()}, tmp_path / "archive")
    attempt = AttemptId(task_id="reproduction", agent=AgentId(role="reviewer", instance=1), attempt=1)
    report = record_generated_observation(store, asset, **dict(kwargs, plan=plan, context=context,
        purpose="reproduction", source_attempt=attempt))
    assert report.source_attempt == attempt
    assert report.conditions == generated_conditions(kwargs["plan"])
    assert read_generated_observation(report, criteria_registry=registry).context == context


def test_changed_host_approval_does_not_validate_saved_science(tmp_path):
    store, asset, registry, kwargs = setup(tmp_path)
    report = record_generated_observation(store, asset, **kwargs)
    changed = TrustedCriteriaRegistry((TrustedCriteriaRecord(spec=kwargs["plan"].evaluation,
        approved_by="different-reviewer", approved_at=1),))
    with pytest.raises(ValueError, match="result_mismatch"):
        read_generated_observation(report, criteria_registry=changed)
