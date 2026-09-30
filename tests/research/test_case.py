from pathlib import Path
import sys
import subprocess

import pytest

from swarm.research.case import seed_case, PENDING
from swarm.research.models import HostConfig
from swarm.research.service import ResearchService
from swarm.task_ledger import TaskLedger


def plan():
    return {"plan_id": "nist-numacc4-original-v1", "mode": "script", "criteria": {"version": "nist-numacc4-v1"},
            "data": {"sha256": "1" * 64, "source": "https://www.itl.nist.gov/div898/strd/univ/data/NumAcc4.dat"},
            "environment": {"image": "python:3.12.13-slim"}, "parameters": ["original"], "seed": 0}


def test_operator_seeds_discoverable_dependency_chain_without_claim_result_or_approval(tmp_path: Path):
    paths = seed_case(tmp_path / "project", tmp_path / "state", python=Path(sys.executable), plan=plan(),
                      code="answer = 2\n", swarm_id="public-case", domain="127.0.0.1:8097", api_key_env="CASE_API_KEY")
    assert Path(paths["python"]) == Path(sys.executable)
    # Real locked interpreter, including Poetry's Linux venv symlink in CI.
    # A resolved base executable may pass is_file yet lose both prefix and MCP.
    selected_prefix = subprocess.check_output(
        [paths["python"], "-c", "import sys, mcp; print(sys.prefix)"], text=True, timeout=15).strip()
    assert selected_prefix == sys.prefix
    configs = [HostConfig.model_validate_json(Path(paths[r + "_config"]).read_bytes()) for r in ("author", "replication", "inheritance")]
    for config in configs:
        assert config.worker_id in {"author", "replication", "inheritance"}
        assert config.experiment_backend["api_key_env"] == "CASE_API_KEY"
        assert "secret" not in config.model_dump_json()
    ledger = TaskLedger(configs[0].ledger_path, "public-case")
    assert len(ledger.snapshot()) == 3
    assert all(t.status == "available" and t.owner is None and t.result is None for t in ledger.snapshot())
    service = ResearchService(configs[0])
    assert [t["signal"]["task_id"] for t in service.discover()] == ["author"]
    assert service.store.adoptions() == []
    assert (tmp_path / "project/science/experiment.py").read_bytes() == PENDING.encode()
    assert not (tmp_path / "project/science/reused.py").exists()
    assert ledger.get("replication").dependencies == ("author",)
    assert ledger.get("inheritance").dependencies == ("author", "replication")
    assert service.context("author")["dependency_results"] == []
    replica = ResearchService(configs[1])
    assert replica.discover() == []
    with pytest.raises(PermissionError, match="capability"):
        replica.claim("author")
    assert replica.context("replication")["dependency_results"][0]["task_id"] == "author"


def test_operator_seed_never_overwrites_or_puts_authority_under_agent_project(tmp_path: Path):
    arguments = dict(python=Path(sys.executable), plan=plan(), code="answer = 2\n", swarm_id="public-case", domain="127.0.0.1:8097")
    with pytest.raises(ValueError, match="must_be_separate"):
        seed_case(tmp_path / "project", tmp_path / "project/state", **arguments)
    existing = tmp_path / "project"
    existing.mkdir()
    (existing / "preserve.txt").write_bytes(b"WIP")
    with pytest.raises(ValueError, match="must_not_exist"):
        seed_case(existing, tmp_path / "state", **arguments)
    assert (existing / "preserve.txt").read_bytes() == b"WIP"
