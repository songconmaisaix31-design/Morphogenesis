"""Offline bridge probe against an explicit immutable C source export.

Run with the locked C Python interpreter and --c-source pointing to git archive.
It reuses C's mock backend; raw NumAcc4 calculations are real CPU work, but no
OpenSandbox/native/model live acceptance is claimed and research stays quarantine.
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.util
from pathlib import Path
import tempfile


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--c-source", required=True, type=Path)
    args = parser.parse_args()
    b_root = Path(__file__).resolve().parents[2]
    import sys
    sys.path.insert(0, str(b_root))
    import orchestration
    orchestration.__path__.append(str(args.c_source / "orchestration"))
    from orchestration.experiments.case import public_case
    from orchestration.experiments import ExperimentExecutor
    from contracts.identity import AgentId, AttemptId
    from local_assets.models import AssetSafetyError, Candidate, FileChange, FileExpectation, ValidationPolicy
    from local_assets.paths import git
    from local_assets.research_models import ResearchClaim
    from swarm.models import Signal
    from swarm.research.experiments import OfficialExperiments
    from swarm.research.models import HostConfig
    from swarm.research.service import ResearchService
    from swarm.research.case import seed_case
    spec = importlib.util.spec_from_file_location("c_contract_fixture", args.c_source / "tests/experiments/test_execution.py")
    assert spec is not None and spec.loader is not None
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    plan = public_case(args.c_source / "demo/research_case")
    body = Path(plan.code.local_path).read_bytes().decode("utf-8")
    with tempfile.TemporaryDirectory(prefix="morph-B-C-bridge-") as temporary:
        root = Path(temporary)
        target = root / "target"
        (target / "science").mkdir(parents=True)
        git(target, "init", "-b", "research-contract")
        (target / "science/experiment.py").write_bytes(b"answer = 1\n")
        git(target, "add", "science")
        git(target, "-c", "user.name=Contract Probe", "-c", "user.email=contract@example.invalid", "commit", "-m", "fixture")
        config = HostConfig(ledger_path=str(root / "ledger.sqlite3"), swarm_id="offline-bridge", workspace=str(target),
                            worker_id="author", agent=AgentId(role="builder", instance=0), authorized_scopes=("science",),
                            capabilities=("research",), assets_root=str(root / "assets"), evidence_root=str(root / "evidence"),
                            experiment_backend={"domain": "127.0.0.1:8097"})
        backend = OfficialExperiments(config)
        backend.executor = ExperimentExecutor(fixture.LocalContractBackend(root / "mock-work"))
        service = ResearchService(config, backend=backend)
        claim = ResearchClaim(plan_id=plan.plan_id, criterion_version=plan.criteria.version,
                              conditions={"data": "NIST NumAcc4", "python": "3.12", "order": "original"}, sources=(plan.data.source,))
        policy = ValidationPolicy(version="nist-script-files-v1", expectations=(FileExpectation(path="science/experiment.py", content=body),))
        acceptance = {"experiment_plan": plan.model_dump(mode="json"), "research_claim": claim.model_dump(mode="json"),
                      "file_policy": policy.model_dump(mode="json")}
        service.ledger.enqueue(Signal(task_id="author", workspace=str(target), scope="science", kind="opportunity",
                                      required_capability="research"), acceptance=acceptance)
        lease = service.claim("author")
        assert lease is not None
        candidate = Candidate(attempt=AttemptId.model_validate(lease["attempt_id"]),
                              base_revision=git(target, "rev-parse", "HEAD").decode().strip(), scope="science",
                              changes=(FileChange(path="science/experiment.py", before="answer = 1\n", after=body),),
                              declared_files=1, declared_lines=1 + len(body.splitlines()), research=claim)
        asset_id = service.publish("author", 1, candidate)
        executed = asyncio.run(service.execute("author", 1))
        assert executed["result"]["execution_state"] == "succeeded"
        assert executed["result"]["scientific_verdict"] == "passed"
        assert executed["result"]["provenance"] == "mock"
        report = service.observe("author", 1, asset_id, executed["run_id"], "original")
        assert report["scientific_verdict"] == "passed" and report["provenance"] == "mock"
        files = service.validate_files("author", 1, asset_id)
        assert files["passed"] is True, files["reasons"]
        try:
            service.approve("author", 1, asset_id, files["report_id"])
        except AssetSafetyError as error:
            assert str(error) == "independent_clean_reproduction_required"
        else:
            raise AssertionError("mock research was approved")
        done = service.complete_research("author", 1, asset_id, executed["run_id"])
        assert done["status"] == "completed" and not done["effect_applied"]
        assert service.store.state(asset_id) == "quarantined" and not service.store.adoptions()
        seeded = seed_case(root / "seed-project", root / "seed-state", python=Path(sys.executable),
                           plan=plan.model_dump(mode="json"), code=body, swarm_id="seeded-case",
                           domain="127.0.0.1:8097")
        author_config = HostConfig.model_validate_json(Path(seeded["author_config"]).read_bytes())
        replica_config = HostConfig.model_validate_json(Path(seeded["replication_config"]).read_bytes())
        author_backend = OfficialExperiments(author_config)
        author_backend.executor = ExperimentExecutor(fixture.LocalContractBackend(root / "seed-mock-work"))
        author = ResearchService(author_config, backend=author_backend)
        replica = ResearchService(replica_config)
        assert [t["signal"]["task_id"] for t in author.discover()] == ["author"]
        assert not replica.discover()
        lease = author.claim("author")
        template = author.context("author")["task"]["signal"]["payload"]["candidate_template"]
        candidate = Candidate.model_validate({**template, "attempt": lease["attempt_id"]})
        seeded_asset = author.publish("author", 1, candidate)
        executed = asyncio.run(author.execute("author", 1))
        author.observe("author", 1, seeded_asset, executed["run_id"], "original")
        author.complete_research("author", 1, seeded_asset, executed["run_id"])
        assert [t["signal"]["task_id"] for t in replica.discover()] == ["replication"]
        assert replica.context("replication")["dependency_results"][0]["result"]["asset_id"] == seeded_asset
        print("contract_local=passed; provenance=mock; C trusted raw NumAcc4 reader + B ledger/assets bridge; mock remains quarantined")


if __name__ == "__main__":
    main()
