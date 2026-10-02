"""An explicitly mock fixture uses the original file/ledger/adoption chain."""

import os
import json
import socket
import subprocess

import pytest

from contracts.identity import AgentId, AttemptId
from local_assets.apply import AssetApplicator
from local_assets.consume import AssetConsumer
from local_assets.generated_validation import (
    approve_generated, generated_candidate, generated_validation, record_generated_observation,
)
from local_assets.models import ConsumptionContext
from local_assets.paths import git
from local_assets.research import require_reproduced
from local_assets.store import LocalAssetStore
from orchestration.experiments.generated_executor import GeneratedExperimentExecutor
from swarm.models import Locality, Signal
from swarm.task_ledger import TaskLedger
from tests.experiments.generated_helpers import (
    GENERATED_CODE, MockGeneratedBackend, approved_criteria_registry, make_context, make_poisson_plan,
    mock_isolation, poisson_reference_output, verified_probe_registry,
)
from tests.local_assets.test_generated_validation import ATTEMPT, FakeBridge


@pytest.fixture(autouse=True)
def only_trusted_git_processes(monkeypatch):
    original = subprocess.Popen
    def process(argv, *args, **kwargs):
        if not isinstance(argv, list) or not argv or argv[0] != "git":
            raise AssertionError("fixture only permits trusted Git; never candidate processes")
        return original(argv, *args, **kwargs)
    def denied(*args, **kwargs):
        raise AssertionError("fixture forbids network and shell")
    monkeypatch.setattr(subprocess, "Popen", process)
    monkeypatch.setattr(os, "system", denied)
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket.socket, "connect_ex", denied)


def setup(tmp_path, *, mode="mock"):
    target = tmp_path / "project"
    target.mkdir()
    (target / "science").mkdir()
    (target / "science" / "README.txt").write_text("inert fixture\n")
    git(target, "init", "-b", "fixture")
    git(target, "add", "science")
    git(target, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-m", "fixture")
    revision = git(target, "rev-parse", "HEAD").decode().strip()
    plan = make_poisson_plan().model_copy(update={"candidate_revision": revision})
    registry = approved_criteria_registry(plan.evaluation, approved_by="reviewer-1")
    store = LocalAssetStore(tmp_path / "state" / "assets", bridge=FakeBridge(), research_provenance=mode,
                            fixture_workspace=tmp_path if mode == "mock" else None, generated_criteria=registry)
    files = {"experiment.py": GENERATED_CODE.encode()}
    asset = store.publish(generated_candidate(plan, files, attempt=ATTEMPT, scope="science", summary="fixture"))
    plan = plan.model_copy(update={"candidate_asset_id": asset})
    return target, store, plan, registry, files


def observe(tmp_path, store, plan, registry, *, task, worker, purpose, attempt):
    plan = plan.model_copy(update={"task_id": task})
    context = make_context(task_id=task, run_id="run-" + task).model_copy(update={"worker_id": worker})
    executor = GeneratedExperimentExecutor(MockGeneratedBackend(tmp_path / task, output=poisson_reference_output(100)),
        probe_registry=verified_probe_registry(), criteria_registry=registry)
    executor.execute(plan, context, {"experiment.py": GENERATED_CODE.encode()}, tmp_path / "archive")
    return record_generated_observation(store, plan.candidate_asset_id, archive_root=tmp_path / "archive",
        plan=plan, context=context, purpose=purpose, criteria_registry=registry, assert_owned=lambda: None,
        source_swarm_id="fixture", source_attempt=attempt, source_fencing_token=context.fencing_token)


def original_and_review(tmp_path, store, plan, registry):
    observe(tmp_path, store, plan, registry, task=ATTEMPT.task_id, worker="author", purpose="original", attempt=ATTEMPT)
    review = AttemptId(task_id="review", agent=AgentId(role="reviewer", instance=1), attempt=1)
    observe(tmp_path, store, plan, registry, task="review", worker="reviewer", purpose="reproduction", attempt=review)


def prepare_consumption(tmp_path):
    target, store, plan, registry, files = setup(tmp_path)
    original_and_review(tmp_path, store, plan, registry)
    require_reproduced(store, plan.candidate_asset_id)
    source_report = generated_validation(store, plan.candidate_asset_id, plan, files,
        mock_isolation(), probe_registry=verified_probe_registry())
    approve_generated(store, source_report, lambda: None)
    ledger = TaskLedger(store.root / "tasks.sqlite3", "fixture")
    ledger.enqueue(Signal(task_id="reuse", workspace=str(target), scope="science", kind="opportunity"))
    lease = ledger.claim("reuse", "consumer", ttl_seconds=300,
                         locality=Locality(workspace=str(target), authorized_scopes=("science",)))
    assert lease is not None
    context = ConsumptionContext(swarm_id=lease.swarm_id, task_id=lease.task_id, worker_id=lease.worker_id,
        fencing_token=lease.token, execution_id="fixture-consumption", scope="science", input_context="mock fixture only")
    consumer = AssetConsumer(store)
    injected = consumer.inject(plan.candidate_asset_id, context)
    attempt = AttemptId(task_id="reuse", agent=AgentId(role="builder", instance=2), attempt=1)
    execution = consumer.execute(injected, attempt=attempt, base_revision=plan.candidate_revision,
        path_map={"science/experiment.py": "science/experiment.py"}, preimages={"science/experiment.py": None})
    assert execution.provenance == "mock"
    assert execution.candidate.changes[0].after.encode() == files["experiment.py"]
    assert not (target / "science" / "experiment.py").exists() and not store.adoptions()
    child_plan = plan.model_copy(update={"task_id": "reuse", "candidate_asset_id": execution.candidate_asset_id})
    child_report = generated_validation(store, execution.candidate_asset_id, child_plan, files,
        mock_isolation(), probe_registry=verified_probe_registry())
    approve_generated(store, child_report, lambda: None)
    with pytest.raises(ValueError, match="local_revalidation_required"):
        store.fetch_approved(execution.candidate_asset_id)
    observe(tmp_path, store, plan, registry, task="reuse", worker="consumer", purpose="inheritance", attempt=attempt)
    prepared = AssetApplicator(store, target, policy_version="generated-isolation-v1").prepare(
        execution.candidate_asset_id, child_report)
    result = dict(candidate_asset_id=execution.candidate_asset_id, consumed_asset_ids=[plan.candidate_asset_id],
                  input_context=context.input_context, execution_id=context.execution_id, applied=True)
    return target, store, plan, consumer, ledger, lease, context, prepared, result


def test_mock_generated_byte_consumption_real_fenced_apply_and_adoption(tmp_path):
    target, store, plan, consumer, ledger, lease, context, prepared, result = prepare_consumption(tmp_path)
    with pytest.raises(ValueError, match="completed_fenced_execution"):
        consumer.record_adoption(context.execution_id, "reuse-result", ledger)
    ledger.submit(lease, "reuse-result", result, apply=prepared.apply)
    assert (target / "science" / "experiment.py").read_bytes() == GENERATED_CODE.encode()
    receipt = consumer.record_adoption(context.execution_id, "reuse-result", ledger)
    assert receipt.provenance == "mock" and receipt.asset_id == plan.candidate_asset_id
    assert consumer.record_adoption(context.execution_id, "reuse-result", ledger) == receipt
    reopened = LocalAssetStore(store.root, bridge=FakeBridge(), research_provenance="mock", fixture_workspace=tmp_path)
    assert reopened.adoptions() == [receipt]
    with pytest.raises(ValueError, match="provenance_conflict"):
        LocalAssetStore(store.root, bridge=FakeBridge())
    with pytest.raises(ValueError, match="generated_criteria_registry_required"):
        reopened.fetch_approved(plan.candidate_asset_id)


def test_default_live_mode_refuses_mock_science_and_mode_switch(tmp_path):
    _, store, plan, registry, _ = setup(tmp_path, mode="live")
    original_and_review(tmp_path, store, plan, registry)
    with pytest.raises(ValueError, match="independent_clean_reproduction_required"):
        require_reproduced(store, plan.candidate_asset_id)
    with pytest.raises(ValueError, match="provenance_conflict"):
        LocalAssetStore(store.root, bridge=FakeBridge(), research_provenance="mock", fixture_workspace=tmp_path)


def test_mock_store_is_bound_to_one_fixture_workspace(tmp_path):
    _, store, _, _, _ = setup(tmp_path)
    with pytest.raises(ValueError, match="provenance_conflict"):
        LocalAssetStore(store.root, bridge=FakeBridge(), research_provenance="mock", fixture_workspace=tmp_path.parent)
    with pytest.raises(ValueError, match="outside_fixture_workspace"):
        store.check_fixture_target(tmp_path.parent)
    with pytest.raises(ValueError, match="isolated_fixture_workspace"):
        LocalAssetStore(tmp_path / "unscoped", bridge=FakeBridge(), research_provenance="mock")


def test_mock_and_live_observations_cannot_form_reproduction_pair(tmp_path):
    _, store, plan, registry, _ = setup(tmp_path)
    original = observe(tmp_path, store, plan, registry, task=ATTEMPT.task_id, worker="author",
                       purpose="original", attempt=ATTEMPT)
    # Synthetic row is an attack fixture, not a claim of live execution.
    forged = original.model_copy(update={"report_id": "forged-live", "provenance": "live",
        "purpose": "reproduction", "worker_id": "other", "run_id": "other", "sandbox_id": "other"})
    store._record_research(forged)
    with pytest.raises(ValueError, match="independent_clean_reproduction_required"):
        require_reproduced(store, plan.candidate_asset_id)


@pytest.mark.parametrize("changed", ["output", "evaluation"])
def test_cached_pass_cannot_survive_original_archive_tampering(tmp_path, changed):
    _, store, plan, registry, files = setup(tmp_path)
    original_and_review(tmp_path, store, plan, registry)
    report = generated_validation(store, plan.candidate_asset_id, plan, files,
        mock_isolation(), probe_registry=verified_probe_registry())
    approve_generated(store, report, lambda: None)
    store.fetch_approved(plan.candidate_asset_id)
    archive = tmp_path / "archive" / ("run-" + ATTEMPT.task_id)
    if changed == "output":
        (archive / "outputs" / "output.json").write_bytes(b"{}")
    else:
        result = json.loads((archive / "result.json").read_bytes())
        result["plan"]["evaluation"]["max_abs_tolerance"] = 1.0
        (archive / "result.json").write_text(json.dumps(result))
        (archive / "plan.json").write_text(json.dumps(result["plan"]))
    with pytest.raises(ValueError):
        store.fetch_approved(plan.candidate_asset_id)


@pytest.mark.parametrize("moment", ["before", "after"])
def test_prepared_application_rechecks_original_evidence_and_rolls_back(tmp_path, monkeypatch, moment):
    target, store, _, _, ledger, lease, _, prepared, result = prepare_consumption(tmp_path)
    output = tmp_path / "archive" / ("run-" + ATTEMPT.task_id) / "outputs" / "output.json"
    if moment == "before":
        output.write_bytes(b"{}")
    else:
        replace = prepared._replace
        def replace_then_change_archive(path, content):
            replace(path, content)
            if content is not None:
                output.write_bytes(b"{}")
        monkeypatch.setattr(type(prepared), "_replace", staticmethod(replace_then_change_archive))
    with pytest.raises(ValueError):
        ledger.submit(lease, "reuse-result", result, apply=prepared.apply)
    assert not (target / "science" / "experiment.py").exists()
    assert not store.adoptions()
