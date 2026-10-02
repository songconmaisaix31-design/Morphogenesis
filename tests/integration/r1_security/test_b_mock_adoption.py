"""Original generated inheritance and fenced apply, using inert fixed output.

The installed fixture backend runs in memory. Only GEP and Git plumbing are
deterministic fixture boundaries; validation, consumption, prepare, file apply,
TaskLedger and AdoptionReceipt are the original implementation. No child process.
"""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from contracts.identity import AgentId, AttemptId
from local_assets import apply as applying, paths
from local_assets.consume import AssetConsumer
from local_assets.generated_validation import (
    approve_generated, generated_candidate, generated_result_payload,
    generated_validation, record_generated_observation,
)
from local_assets.models import ConsumptionContext
from local_assets.research import require_reproduced
from local_assets.store import LocalAssetStore
from orchestration.experiments.fixture import GeneratedFixtureBackend
from orchestration.experiments.generated import GeneratedContext
from orchestration.experiments.generated_executor import GeneratedExperimentExecutor
from orchestration.experiments.trusted import TrustedCriteriaRecord, TrustedCriteriaRegistry
from swarm.models import Locality, Signal
from swarm.task_ledger import TaskLedger
from tests.integration.r1_security.test_b_generated_boundaries import CODE, plan, raw_output


class InertAssetBridge:
    """Store exact emitted fixture Genes, never launch the production Node bridge."""
    def __init__(self):
        self.bodies = {}

    def compute_asset_id(self, asset):
        for identity, original in self.bodies.items():
            if {k: v for k, v in original.items() if k != "asset_id"} == asset:
                return identity
        identity = "candidate" if not self.bodies else "child-" + str(len(self.bodies))
        self.bodies[identity] = dict(asset, asset_id=identity)
        return identity

    def validate_asset(self, asset):
        return SimpleNamespace(valid=asset == self.bodies.get(asset.get("asset_id")))

    @staticmethod
    def canonicalize(asset):
        return json.dumps(asset, sort_keys=True)


def setup(root, monkeypatch, *, mode="mock", review=True, review_outcome="succeeded"):
    import time

    monkeypatch.setattr(time, "time", lambda: 100.0)
    target = root / "workspace"
    (target / "science").mkdir(parents=True)
    metadata = target / ".git"
    (metadata / "refs/heads").mkdir(parents=True)
    (metadata / "HEAD").write_text("ref: refs/heads/fixture\n")
    (metadata / "refs/heads/fixture").write_text("a" * 40 + "\n")
    bridge = InertAssetBridge()
    assets = LocalAssetStore(root / "assets", bridge=bridge, research_provenance=mode,
                             fixture_workspace=root if mode == "mock" else None)
    p = plan()
    p = p.model_copy(update={"environment": p.environment.model_copy(update={
        "image": "fixture@sha256:" + "c" * 64, "image_digest": "sha256:" + "c" * 64})})
    original = AttemptId(task_id="t1", agent=AgentId(role="builder", instance=0), attempt=1)
    assert assets.publish(generated_candidate(p, {"candidate.py": CODE}, attempt=original,
        scope="science", summary="Q inert fixture")) == "candidate"
    ledger = TaskLedger(root / "ledger.db", "q-mock-adoption", clock=lambda: 100.0)
    locality = Locality(workspace=str(target), authorized_scopes=("science",))
    criterion = TrustedCriteriaRecord(spec=p.evaluation, approved_by="criteria-reviewer", approved_at=90)
    registry = TrustedCriteriaRegistry(records=(criterion,))
    backend = GeneratedFixtureBackend(environment=p.environment, resources=p.backend,
                                     output=raw_output(), instance_id="q-fixed-output")
    current_lease = [None]

    def claim(task, actor, frozen=None):
        ledger.enqueue(Signal(task_id=task, workspace=str(target), scope="science", kind="opportunity",
            payload={"project_id": "p1", "branch_id": "b1"}),
            acceptance={"generated_plan": frozen.model_dump(mode="json")} if frozen else {})
        lease = ledger.claim(task, actor, locality=locality, ttl_seconds=300)
        assert lease is not None
        current_lease[0] = lease
        return lease

    def observe(task, actor, purpose, *, lease=None, outcome="succeeded", submit=True):
        frozen = p.model_copy(update={"task_id": task})
        lease = lease or claim(task, actor, frozen)
        context = GeneratedContext(run_id="run-" + task, task_id=task, worker_id=actor,
            fencing_token=lease.token, author="author", reviewer="criteria-reviewer")
        selected = backend if outcome == "succeeded" else GeneratedFixtureBackend(
            environment=p.environment, resources=p.backend, output=raw_output(),
            instance_id="q-fixed-output", outcome=outcome)
        ledger.begin_execution(lease, context.run_id)
        result = GeneratedExperimentExecutor(selected, probe_registry=selected.probe_registry,
            criteria_registry=registry).execute(frozen, context, {"candidate.py": CODE}, root / "evidence")
        envelope = generated_result_payload(result, criteria_registry=registry)
        ledger.record_event("research_execution", {"run_id": context.run_id, "worker_id": actor,
            "token": lease.token, "result": envelope}, task_id=task)
        if result.remote_effect == "known":
            ledger.confirm_execution(lease, context.run_id)
        attempt = original if task == "t1" else AttemptId(task_id=task,
            agent=AgentId(role="reviewer" if purpose == "reproduction" else "builder", instance=1), attempt=1)

        def owned():
            assert ledger.is_valid(lease), "lost original TaskLedger fixture lease"

        report = record_generated_observation(assets, "candidate", archive_root=root / "evidence",
            plan=frozen, context=context, purpose=purpose, criteria_registry=registry,
            assert_owned=owned, source_swarm_id=ledger.swarm_id, source_attempt=attempt,
            source_fencing_token=lease.token)
        if submit and result.remote_effect == "known":
            ledger.submit(lease, "result-" + task, {"stage": "evidence_submitted", "asset_id": "candidate",
                "report_id": report.report_id, "run_id": context.run_id,
                "execution_state": report.execution_state, "scientific_verdict": report.scientific_verdict,
                "provenance": "mock"})
        return report

    approval_lease = claim("approval", "reviewer")

    def owned():
        assert ledger.is_valid(current_lease[0])

    report = generated_validation(assets, "candidate", p, {"candidate.py": CODE}, backend.isolation(),
                                  probe_registry=backend.probe_registry)
    assert report.passed
    approve_generated(assets, report, owned)
    assert ledger.release(approval_lease)
    observe("t1", "author", "original")
    if review:
        observe("review", "reviewer", "reproduction", outcome=review_outcome)
    return SimpleNamespace(root=root, target=target, assets=assets, bridge=bridge, p=p, backend=backend,
        ledger=ledger, locality=locality, observe=observe, claim=claim, owned=owned, report=report)


def git_plumbing_fixture(monkeypatch, fixture):
    """Only model exact read-only Git queries; unexpected Git use fails."""
    target = fixture.target
    tree = "b" * 40

    def git(root, *args, **kwargs):
        assert Path(root).resolve() == target.resolve()
        replies = {("rev-parse", "--show-toplevel"): str(target),
            ("symbolic-ref", "--short", "HEAD"): "fixture",
            ("symbolic-ref", "HEAD"): "refs/heads/fixture",
            ("rev-parse", "HEAD"): "a" * 40,
            ("rev-parse", "a" * 40 + "^{tree}"): tree}
        if args[:4] == ("rev-parse", "--path-format=absolute", "--git-path", "HEAD"):
            return str(target / ".git/HEAD").encode()
        if len(args) == 4 and args[:3] == ("rev-parse", "--path-format=absolute", "--git-path"):
            assert args[3] in {"refs/heads/fixture", "packed-refs"}
            return str(target / ".git" / args[3]).encode()
        assert args in replies, args
        return replies[args].encode()

    monkeypatch.setattr(paths, "git", git)
    monkeypatch.setattr(applying, "git", git)

    def scope_tree(root, scope, snapshots):
        assert root == target and scope == "science"
        assert list((root / scope).iterdir()) == []
        return tree, {}

    monkeypatch.setattr(applying, "scope_tree", scope_tree)


def consumption(fixture):
    f = fixture
    lease = f.claim("reuse", "consumer")
    context = ConsumptionContext(swarm_id=lease.swarm_id, task_id=lease.task_id, worker_id=lease.worker_id,
        fencing_token=lease.token, execution_id="q-consumption", scope="science", input_context="Q mock only")
    consumer = AssetConsumer(f.assets)
    injected = consumer.inject("candidate", context)
    attempt = AttemptId(task_id="reuse", agent=AgentId(role="builder", instance=1), attempt=1)
    execution = consumer.execute(injected, attempt=attempt, base_revision=f.p.candidate_revision,
        path_map={"science/candidate.py": "science/candidate.py"}, preimages={"science/candidate.py": None})
    return lease, context, consumer, execution


def test_installed_fixture_actual_original_consumption_fenced_apply_and_mock_receipt(tmp_path, monkeypatch):
    f = setup(tmp_path, monkeypatch)
    assert not f.backend.isolation().verified and f.backend.isolation().probe == "not_run"
    require_reproduced(f.assets, "candidate")
    lease, context, consumer, execution = consumption(f)
    assert execution.provenance == "mock" and not f.assets.adoptions()
    assert not (f.target / "science/candidate.py").exists()
    child = f.p.model_copy(update={"task_id": "reuse", "candidate_asset_id": execution.candidate_asset_id})
    validation = generated_validation(f.assets, execution.candidate_asset_id, child, {"candidate.py": CODE},
        f.backend.isolation(), probe_registry=f.backend.probe_registry)
    assert validation.passed
    approve_generated(f.assets, validation, f.owned)
    with pytest.raises(ValueError, match="local_revalidation_required"):
        f.assets.fetch_approved(execution.candidate_asset_id)
    f.observe("reuse", "consumer", "inheritance", lease=lease, submit=False)
    git_plumbing_fixture(monkeypatch, f)
    prepared = applying.AssetApplicator(f.assets, f.target, policy_version="generated-isolation-v1").prepare(
        execution.candidate_asset_id, validation)
    with pytest.raises(ValueError, match="completed_fenced_execution"):
        consumer.record_adoption(context.execution_id, "result-reuse", f.ledger)
    result = {"candidate_asset_id": execution.candidate_asset_id, "consumed_asset_ids": ["candidate"],
        "input_context": context.input_context, "execution_id": context.execution_id, "applied": True}
    f.ledger.submit(lease, "result-reuse", result, apply=prepared.apply)
    assert (f.target / "science/candidate.py").read_bytes() == CODE
    receipt = consumer.record_adoption(context.execution_id, "result-reuse", f.ledger)
    assert receipt.provenance == "mock" and receipt.asset_id == "candidate"
    assert consumer.record_adoption(context.execution_id, "result-reuse", f.ledger) == receipt
    reopened = LocalAssetStore(f.assets.root, bridge=f.bridge, research_provenance="mock", fixture_workspace=tmp_path)
    assert reopened.adoptions() == [receipt]


@pytest.mark.parametrize("mode", ["live", "mock"])
def test_persisted_mode_cannot_change_on_reopen(tmp_path, monkeypatch, mode):
    f = setup(tmp_path, monkeypatch, mode=mode)
    other = "live" if mode == "mock" else "mock"
    with pytest.raises(ValueError, match="provenance_conflict"):
        LocalAssetStore(f.assets.root, bridge=f.bridge, research_provenance=other,
                        fixture_workspace=tmp_path if other == "mock" else None)
    if mode == "live":
        with pytest.raises(ValueError, match="independent_clean_reproduction_required"):
            f.assets.fetch_approved("candidate")


def test_mock_root_is_persisted_and_cannot_escape_target(tmp_path, monkeypatch):
    f = setup(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="provenance_conflict"):
        LocalAssetStore(f.assets.root, bridge=f.bridge, research_provenance="mock", fixture_workspace=tmp_path.parent)
    with pytest.raises(ValueError, match="outside_fixture_workspace"):
        f.assets.check_fixture_target(tmp_path.parent)
    with pytest.raises(ValueError, match="isolated_fixture_workspace"):
        LocalAssetStore(tmp_path / "unbound", bridge=f.bridge, research_provenance="mock")


@pytest.mark.parametrize("outcome", ["failed", "timeout", "unknown"])
def test_failed_timeout_or_unknown_review_never_allows_inheritance(tmp_path, monkeypatch, outcome):
    f = setup(tmp_path, monkeypatch, review_outcome=outcome)
    with pytest.raises(ValueError):
        f.assets.fetch_approved("candidate")
    assert f.assets.adoptions() == []
    assert not (f.target / "science/candidate.py").exists()


def test_mixed_mock_live_cached_rows_do_not_form_independent_review(tmp_path, monkeypatch):
    f = setup(tmp_path, monkeypatch, review=False)
    original = f.assets.research_reports("candidate")[0]
    forged = original.model_copy(update={"report_id": "q-forged-live", "provenance": "live",
        "purpose": "reproduction", "worker_id": "other", "run_id": "other", "sandbox_id": "other"})
    f.assets._record_research(forged)  # attacker fixture; not live evidence
    with pytest.raises(ValueError, match="independent_clean_reproduction_required"):
        consumption(f)
    assert not f.assets.adoptions()


@pytest.mark.parametrize("changed", ["output", "evaluation", "environment"])
def test_original_archive_integrity_rechecked_before_inheritance(tmp_path, monkeypatch, changed):
    f = setup(tmp_path, monkeypatch)
    assert f.assets.fetch_approved("candidate").research is not None
    archive = tmp_path / "evidence/run-t1"
    if changed == "output":
        (archive / "outputs/output.json").write_bytes(b'{"score":1,"approved":true}')
    else:
        path = archive / "plan.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        if changed == "evaluation":
            payload["evaluation"]["max_abs_tolerance"] = 1.0
        else:
            payload["environment"]["dependency_lock_sha256"] = "d" * 64
        path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError):
        consumption(f)
    assert not f.assets.adoptions()


def test_mock_isolation_identity_cannot_admit_real_sdk_adapter(tmp_path, monkeypatch):
    from orchestration.experiments.sandbox_adapter import LocalCpuSandboxBackend
    from tests.integration.r1_security.test_b_generated_boundaries import context

    f = setup(tmp_path, monkeypatch)
    real = LocalCpuSandboxBackend(domain="127.0.0.1:65534", probe=f.backend._probe,
        instance_id="q-fixed-output",
        runtime_profile="fixed-output-fixture-v1", server_process_limit=f.p.backend.process_limit)
    with pytest.raises(ValueError):
        real.create(f.p, context())
