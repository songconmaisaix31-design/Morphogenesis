"""Real ledger/store/file gates with explicit mock observations; never live proof."""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from contracts.identity import AgentId, AttemptId
from local_assets.models import AssetSafetyError, Candidate, FileChange, FileExpectation, ValidationPolicy
from local_assets.paths import git
from local_assets.research import require_inheritance, require_reproduced
from local_assets.research_models import ResearchClaim
from swarm.models import Signal
from swarm.research.models import HostConfig
from swarm.research.service import ResearchService
from swarm.task_ledger import LeaseLost

BODY = "import statistics\n\ndef variance(values):\n    return statistics.variance(values)\n"


class MockEvidence:
    def __init__(self, state="succeeded", verdict="passed", reasons=()) -> None:
        self.state, self.verdict, self.reasons = state, verdict, list(reasons)
        self.runs = {}

    async def execute(self, plan, run_id, lease):
        result = {"execution_state": self.state, "scientific_verdict": self.verdict,
                  "effect_state": "unknown" if self.state == "unknown" else "known",
                  "sandbox_id": "mock-" + run_id, "provenance": "mock", "reasons": self.reasons,
                  "code_text": BODY}
        self.runs[run_id] = result
        return result

    def read(self, run_id):
        return self.runs[run_id]

    def evaluate(self, run_id, plan, lease):
        return self.read(run_id)


def setup(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    (target / "science").mkdir()
    (target / "science" / "experiment.py").write_bytes(b"answer = 1\n")
    git(target, "init", "-b", "research-target")
    git(target, "add", "science")
    git(target, "-c", "user.name=Research Test", "-c", "user.email=research@example.invalid", "commit", "-m", "fixture")
    config = HostConfig(ledger_path=str(tmp_path / "tasks.sqlite3"), swarm_id="science", workspace=str(target),
                        worker_id="author", agent=AgentId(role="builder", instance=0), authorized_scopes=("science",),
                        capabilities=("research",), assets_root=str(tmp_path / "assets"), evidence_root=str(tmp_path / "evidence"))
    service = ResearchService(config, backend=MockEvidence())
    claim = ResearchClaim(plan_id="numacc", criterion_version="nist-numacc4-v1",
                          conditions={"data": "NIST NumAcc4", "python": "3.12"}, sources=("https://www.itl.nist.gov/div898/strd/univ/data/NumAcc4.dat",))
    policy = ValidationPolicy(version="science-files-v1", expectations=(FileExpectation(path="science/experiment.py", content=BODY),))
    acceptance = {"experiment_plan": {"plan_id": "numacc", "role": "author", "criteria": {"version": "nist-numacc4-v1"}},
                  "research_claim": claim.model_dump(mode="json"), "file_policy": policy.model_dump(mode="json")}
    service.ledger.enqueue(Signal(task_id="original", workspace=str(target), scope="science", kind="opportunity",
                                  required_capability="research"), acceptance=acceptance)
    assert service.claim("original")
    candidate = Candidate(attempt=AttemptId(task_id="original", agent=config.agent, attempt=1),
                          base_revision=git(target, "rev-parse", "HEAD").decode().strip(), scope="science",
                          changes=(FileChange(path="science/experiment.py", before="answer = 1\n", after=BODY),),
                          declared_files=1, declared_lines=5, research=claim)
    asset = service.publish("original", 1, candidate)
    return service, asset, acceptance


def observe(service, asset, task="original", purpose="original"):
    executed = asyncio.run(service.execute(task, 1))
    run_id = executed["run_id"]
    return service.observe(task, 1, asset, run_id, purpose), run_id


def test_author_can_finish_quarantined_then_peer_claims_and_mock_never_approves(tmp_path: Path) -> None:
    author, asset, acceptance = setup(tmp_path)
    observation, run_id = observe(author, asset)
    assert observation["provenance"] == "mock"
    report = author.validate_files("original", 1, asset)
    assert report["passed"] is True, report["reasons"]
    with pytest.raises(AssetSafetyError, match="independent_clean"):
        author.approve("original", 1, asset, report["report_id"])
    done = author.complete_research("original", 1, asset, run_id)
    assert done["status"] == "completed" and done["effect_applied"] is False
    assert author.store.state(asset) == "quarantined"
    peer = ResearchService(author.config.model_copy(update={"worker_id": "replicator", "agent": AgentId(role="reviewer", instance=1)}),
                           backend=MockEvidence())
    acceptance["experiment_plan"]["role"] = "replication"
    peer.ledger.enqueue(Signal(task_id="reproduction", workspace=peer.config.workspace, scope="science", kind="opportunity",
                               required_capability="research"), dependencies=("original",), acceptance=acceptance)
    assert peer.claim("reproduction")
    observe(peer, asset, "reproduction", "reproduction")
    with pytest.raises(AssetSafetyError, match="independent_clean"):
        peer.approve("reproduction", 1, asset, report["report_id"])
    assert peer.store.state(asset) == "quarantined"
    assert peer.store.adoptions() == []


@pytest.mark.parametrize(("state", "verdict", "reasons"), [
    ("succeeded", "failed", ("variance_accuracy_failed",)),
    ("missing_artifact", "not_evaluated", ("missing_durable_evidence",)),
    ("unknown", "not_evaluated", ("unknown_remote_effect",)),
    ("failed", "not_evaluated", ("infrastructure_failure",)),
])
def test_failedcriterion_missingartifact_unknown_and_infrastructure_kept_distinct(tmp_path: Path, state, verdict, reasons) -> None:
    service, asset, _ = setup(tmp_path)
    service.backend = MockEvidence(state, verdict, reasons)
    report, _ = observe(service, asset)
    assert (report["execution_state"], report["scientific_verdict"], tuple(report["reasons"])) == (state, verdict, reasons)
    with pytest.raises(AssetSafetyError):
        require_reproduced(service.store, asset)
    assert service.store.state(asset) == "quarantined"
    assert service.store.adoptions() == []


def test_stale_submit_validation_and_conditions_rejected(tmp_path: Path) -> None:
    service, asset, acceptance = setup(tmp_path)
    report, run_id = observe(service, asset)
    assert service.release("original", 1)
    assert service.claim("original")
    with pytest.raises(LeaseLost):
        service.observe("original", 1, asset, run_id, "original")
    with pytest.raises(LeaseLost):
        service.validate_files("original", 1, asset)
    acceptance["research_claim"]["conditions"] = {"data": "other"}
    service.ledger.enqueue(Signal(task_id="other", workspace=service.config.workspace, scope="science/other", kind="opportunity",
                                 required_capability="research"), acceptance=acceptance)
    with pytest.raises(AssetSafetyError, match="research_condition_mismatch"):
        require_inheritance(service.store, asset, "other", "author", 1, {"data": "other"})


def test_passing_reference_cannot_certify_unexecuted_candidate_code(tmp_path: Path) -> None:
    service, asset, _ = setup(tmp_path)
    executed = asyncio.run(service.execute("original", 1))
    service.backend.runs[executed["run_id"]]["code_text"] = "answer = 999\n"
    with pytest.raises(AssetSafetyError, match="executed_code_mismatch"):
        service.observe("original", 1, asset, executed["run_id"], "original")
    assert service.store.research_reports(asset) == []


def test_missing_durable_artifact_reader_failure_is_retained(tmp_path: Path) -> None:
    service, asset, _ = setup(tmp_path)
    executed = asyncio.run(service.execute("original", 1))
    def missing(run_id, plan, lease):
        raise FileNotFoundError("raw artifact missing")
    service.backend.evaluate = missing
    report = service.observe("original", 1, asset, executed["run_id"], "original")
    assert report["execution_state"] == "missing_artifact"
    assert report["scientific_verdict"] == "not_evaluated"
    assert "raw artifact missing" in report["reasons"][0]
    assert len(service.store.research_reports(asset)) == 1


def test_counterexample_preserved_and_prevents_research_reuse(tmp_path: Path) -> None:
    service, asset, _ = setup(tmp_path)
    service.backend = MockEvidence("succeeded", "failed", ("variance_accuracy_failed",))
    observe(service, asset, purpose="counterexample")
    with pytest.raises(AssetSafetyError, match="invalidated_by_counterexample"):
        require_reproduced(service.store, asset)
    assert len(service.store.research_reports(asset)) == 1


@pytest.mark.parametrize("effect", [None, "unknown", "unrecognized"])
@pytest.mark.parametrize("purpose", ["original", "reproduction", "inheritance"])
def test_successful_science_with_unknown_effect_never_qualifies(tmp_path: Path, effect, purpose) -> None:
    service, asset, _ = setup(tmp_path)
    executed = asyncio.run(service.execute("original", 1))
    raw = service.backend.runs[executed["run_id"]]
    if effect is None:
        raw.pop("effect_state")
    else:
        raw["effect_state"] = effect
    report = service.observe("original", 1, asset, executed["run_id"], purpose)
    assert report["scientific_verdict"] == "passed" and report["provenance"] == "mock"
    with pytest.raises(AssetSafetyError, match="report_effect_unknown"):
        require_reproduced(service.store, asset)
    assert service.store.state(asset) == "quarantined" and not service.store.adoptions()


@pytest.mark.parametrize("field", ["plan_id", "criteria"])
def test_registered_plan_identity_cannot_be_relabelled_by_claim(tmp_path: Path, field) -> None:
    service, asset, _ = setup(tmp_path)
    executed = asyncio.run(service.execute("original", 1))
    from swarm.task_ledger import connection
    import json
    with connection(service.ledger.path, write=True) as db:
        row = db.execute("SELECT acceptance FROM tasks WHERE task_id='original'").fetchone()
        acceptance = json.loads(row[0])
        acceptance["experiment_plan"][field] = "different" if field == "plan_id" else {"version": "different"}
        db.execute("UPDATE tasks SET acceptance=? WHERE task_id='original'", (json.dumps(acceptance),))
    with pytest.raises(AssetSafetyError, match="plan_claim_mismatch"):
        service.observe("original", 1, asset, executed["run_id"], "original")
    assert not service.store.research_reports(asset)
