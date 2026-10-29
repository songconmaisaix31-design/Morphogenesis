"""Real local preparation and SDK stdio checks, without SWA/model/sandbox calls."""
import json
from pathlib import Path
import subprocess
import sys

from demo.swa_research_bridge import prepare, REPOSITORY, ROLES
from swarm.research.case import PENDING
from swarm.research.models import HostConfig
from swarm.task_ledger import TaskLedger


def test_prepare_uses_registered_case_and_preserves_host_authority(tmp_path: Path) -> None:
    paths = prepare(tmp_path / "project", tmp_path / "state", Path(sys.executable),
                    swarm_id="swa-preparation", api_key_env="MORPH_TEST_KEY")
    for role in ROLES:
        descriptor = json.loads(Path(paths[role + "_descriptor"]).read_text())
        assert descriptor == {"python": sys.executable, "cwd": str(REPOSITORY),
                              "host_config": paths[role + "_config"]}
        assert all(Path(value).is_absolute() for value in descriptor.values())
        host = HostConfig.model_validate_json(Path(descriptor["host_config"]).read_bytes())
        assert host.worker_id == role
        assert host.experiment_backend["api_key_env"] == "MORPH_TEST_KEY"
        assert host.native_invocation is None and host.research_budget_policy is None
        assert not Path(host.ledger_path).is_relative_to(Path(paths["project"]))
        spec = json.loads(Path(paths[role + "_spec"]).read_text())
        assert Path(paths[role + "_spec"]).parent == Path(paths["project"]) / "swa-inputs"
        assert Path(paths[role + "_input"]).parent == Path(paths["project"]) / "swa-inputs"
        assert spec["source_revision"] == paths["base_revision"]
        assert spec["max_workers"] == spec["initial_workers"] == 1
        prompt = Path(paths[role + "_input"]).read_text()
        assert "morph_list_tools" in prompt and "morph_call_tool" in prompt
    ledger = TaskLedger(Path(paths["state"]) / "tasks.sqlite3", "swa-preparation")
    assert all(task.status == "available" and task.owner is None and task.result is None
               for task in ledger.snapshot())
    assert {event["event"] for event in ledger.audit()} == {"created"}
    assert (Path(paths["project"]) / "science/experiment.py").read_text() == PENDING


def test_cli_real_stdio_competition_and_fencing_exits_cleanly(tmp_path: Path) -> None:
    process = subprocess.run([sys.executable, "-m", "demo.swa_research_bridge", "selfcheck",
        "--root", str(tmp_path), "--python", sys.executable], cwd=REPOSITORY,
        capture_output=True, text=True, timeout=90, check=False)
    assert process.returncode == 0, process.stderr
    result = json.loads(process.stdout)
    assert result["status"] == "passed" and result["validation"] == "contract_local"
    assert result["transport"] == "official_mcp_stdio"
    assert result["model_invoked"] is result["experiment_invoked"] is False
    assert result["scientific_result"] is None
    assert result["first_token"] < result["second_token"]
    assert result["old_token_rejected"] and result["stdio_sessions_closed"]
    assert json.loads(Path(result["result_file"]).read_text()) == result
    host = HostConfig.model_validate_json((Path(result["state"]) / "author-host.json").read_bytes())
    ledger = TaskLedger(host.ledger_path, host.swarm_id)
    claimed = [event["body"] for event in ledger.audit() if event["event"] == "claimed"]
    assert len(claimed) == 2
    assert {event["worker_id"] for event in claimed} == {"author", "author-peer"}
    assert all(task.status == "available" and task.owner is None and task.result is None
               for task in ledger.snapshot())
