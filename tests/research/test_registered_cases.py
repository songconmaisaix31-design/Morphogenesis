"""Both registered cases use the real ledger/file bridge, with honest mock science."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
import sys

import pytest

from local_assets.models import AssetSafetyError, Candidate
from orchestration.experiments.case import get_case
from orchestration.experiments.executor import ExperimentExecutor, digest
from swarm.research.case import PENDING, main, seed_case
from swarm.research.experiments import OfficialExperiments
from swarm.research.models import HostConfig
from swarm.research.service import ResearchService
from swarm.task_ledger import LeaseLost, TaskConflict
from tests.experiments.test_execution import LocalContractBackend


IDS = ("nist-numacc4-v1", "synthetic-linear-regression-v1")


@pytest.mark.parametrize("case_id", IDS)
def test_registered_seed_same_claim_execution_and_file_gates(tmp_path: Path, case_id: str) -> None:
    definition = get_case(case_id)
    plan = definition.build_plan()
    code = Path(plan.code.local_path).read_bytes().decode("utf-8")
    paths = seed_case(tmp_path / "project", tmp_path / "state", python=Path(sys.executable),
                      plan=plan.model_dump(mode="json"), code=code, swarm_id=case_id, domain="127.0.0.1:8097")
    services = {}
    backends = {}
    for role in ("author", "replication", "inheritance"):
        config = HostConfig.model_validate_json(Path(paths[role + "_config"]).read_bytes())
        bridge = OfficialExperiments(config)
        backend = LocalContractBackend(tmp_path / (role + "-mock"))
        bridge.executor = ExperimentExecutor(backend)
        service = ResearchService(config, backend=bridge)
        services[role], backends[role] = service, backend
        task = service.ledger.get(role)
        assert task.owner is None and task.result is None
        assert task.signal.scope == "science"
        assert task.signal.required_capability == "research." + role
        assert task.signal.payload["question"] == definition.problem
        assert task.acceptance["experiment_plan"] == {**plan.model_dump(mode="json"), "role": role}
        policy = task.acceptance["file_policy"]
        assert policy["version"] == definition.file_policy_prefix + "-" + role + "-files-v1"
        destination = "science/reused.py" if role == "inheritance" else "science/experiment.py"
        assert policy["expectations"] == [{"path": destination, "content": code}]
    author, peer, third = (services[r] for r in ("author", "replication", "inheritance"))
    assert peer.config.worker_id != author.config.worker_id and peer.config.agent != author.config.agent
    assert peer.discover() == third.discover() == []
    lease = author.claim("author")
    assert lease is not None
    token = lease["token"]
    author.renew("author", token)
    template = author.context("author")["task"]["signal"]["payload"]["candidate_template"]
    assert template["summary"] == definition.template_summary
    assert template["changes"] == [{"path": "science/experiment.py", "before": PENDING, "after": code}]
    candidate = Candidate.model_validate({**template, "attempt": lease["attempt_id"]})
    asset = author.publish("author", token, candidate)
    executed = asyncio.run(author.execute("author", token))
    assert executed["result"]["provenance"] == "mock"
    assert executed["result"]["scientific_verdict"] == "passed"
    assert executed["result"]["usage"] is executed["result"]["cost_usd"] is None
    original = author.observe("author", token, asset, executed["run_id"], "original")
    assert original["criterion_version"] == case_id and original["provenance"] == "mock"
    files = author.validate_files("author", token, asset)
    assert files["passed"], files["reasons"]
    author.complete_research("author", token, asset, executed["run_id"])
    assert backends["author"].create_calls == 1
    assert [t["signal"]["task_id"] for t in peer.discover()] == ["replication"]
    assert peer.context("replication")["dependency_results"][0]["result"]["asset_id"] == asset
    peer_lease = peer.claim("replication")
    assert peer_lease is not None
    peer_token = peer_lease["token"]
    peer.renew("replication", peer_token)
    reproduced = asyncio.run(peer.execute("replication", peer_token))
    report = peer.observe("replication", peer_token, asset, reproduced["run_id"], "reproduction")
    assert report["worker_id"] != original["worker_id"] and report["run_id"] != original["run_id"]
    assert report["provenance"] == "mock" and report["scientific_verdict"] == "passed"
    files = peer.validate_files("replication", peer_token, asset)
    assert files["passed"], files["reasons"]
    with pytest.raises(AssetSafetyError, match="independent_clean_reproduction_required"):
        peer.approve("replication", peer_token, asset, files["report_id"])
    with pytest.raises(AssetSafetyError, match="asset_not_approved"):
        peer.apply("replication", peer_token, asset, files["report_id"])
    with pytest.raises(TaskConflict, match="host_experiment_limit"):
        asyncio.run(peer.execute("replication", peer_token))
    assert backends["replication"].create_calls == 1
    assert peer.store.state(asset) == "quarantined"
    assert peer.store.adoptions() == [] and third.discover() == []
    assert third.claim("inheritance") is None
    with pytest.raises(LeaseLost):
        third.inherit("inheritance", 1, asset, {"science/experiment.py": "science/reused.py"},
                      {"science/reused.py": None}, paths["base_revision"])
    assert backends["inheritance"].create_calls == 0
    assert (tmp_path / "project/science/experiment.py").read_bytes() == PENDING.encode()
    assert not (tmp_path / "project/science/reused.py").exists()


@pytest.mark.parametrize("fault", ["unknown", "claim", "criteria", "code", "data", "candidate"])
def test_invalid_registered_seed_never_creates_project_or_authority(tmp_path: Path, fault: str) -> None:
    plan = get_case(IDS[1]).build_plan().model_dump(mode="json")
    code = Path(plan["code"]["local_path"]).read_bytes().decode("utf-8")
    if fault == "unknown":
        plan["criteria"]["version"] = "agent-provided-validator"
    elif fault == "claim":
        plan["claim"] = "Different scientific claim"
    elif fault == "criteria":
        plan["criteria"]["sse_absolute_tolerance"] = 1
    elif fault in {"code", "data"}:
        path = tmp_path / ("wrong.py" if fault == "code" else "wrong.csv")
        raw = b"answer = 1\n" if fault == "code" else b"unregistered input\n"
        path.write_bytes(raw)
        plan[fault].update(local_path=str(path), sha256=digest(raw))
    else:
        code += "\n# not the executed candidate\n"
    with pytest.raises(ValueError):
        seed_case(tmp_path / "project", tmp_path / "state", python=Path(sys.executable),
                  plan=plan, code=code, swarm_id="rejected", domain="127.0.0.1:8097")
    assert not (tmp_path / "project").exists() and not (tmp_path / "state").exists()


def test_operator_cli_selects_installed_second_case_without_directory(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["research-case", "--case-id", IDS[1], "--project", str(tmp_path / "project"),
                                     "--state", str(tmp_path / "state"), "--python", sys.executable])
    main()
    paths = json.loads(capsys.readouterr().out)
    config = HostConfig.model_validate_json(Path(paths["author_config"]).read_bytes())
    service = ResearchService(config)
    task = service.ledger.get("author")
    assert task.acceptance["experiment_plan"]["criteria"]["version"] == IDS[1]
    assert service.store.adoptions() == [] and task.owner is None
