"""Fake subprocess tests establish contract_local only, never live acceptance."""

from pathlib import Path
import sys
import time

import pytest

from contracts.identity import AgentId, AttemptId
from contracts.runtime import RunConfig
from orchestration.codex import CodexExecutor, read_usage, task_workspace
from orchestration.sample_policy import validate_sample

FIXED = '''def clamp(value: float, lower: float, upper: float) -> float:
    if lower > upper:
        raise ValueError("bad interval")
    return min(upper, max(lower, value))

def mean(values: list[float]) -> float:
    if not values:
        raise ValueError("empty")
    return sum(values) / len(values)

def unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))
'''


def prepared(tmp_path: Path) -> tuple[RunConfig, AttemptId]:
    workspace = tmp_path / "task"
    workspace.mkdir()
    (workspace / "sample.py").write_text("broken = True\n")
    (workspace / "TASK.md").write_text("Set broken to False.")
    return (RunConfig(run_id="fake-run", workspace=str(workspace), writable_paths=["sample.py"]),
            AttemptId(task_id="repair", agent=AgentId(role="builder", instance=0), attempt=0))


def fake_cli(tmp_path: Path, *, content: str = FIXED, path: str = "sample.py",
             adopted: list[str] | None = None, sleep: bool = False) -> list[str]:
    script = tmp_path / "fake_cli.py"
    proposal = {"path": path, "content": content, "summary": "fake only", "adopted_gene_ids": adopted or []}
    script.write_text(
        "import json,sys,time\nfrom pathlib import Path\n"
        "prompt=sys.stdin.read()\n"
        + ("time.sleep(20)\n" if sleep else "")
        + "args=sys.argv[1:]\n"
        + "assert args[args.index('--sandbox')+1] == 'read-only'\n"
        + "assert '--dangerously-bypass-approvals-and-sandbox' not in args\n"
        + f"proposal={proposal!r}\n"
        + "Path(args[args.index('--output-last-message')+1]).write_text(json.dumps(proposal))\n"
        + "print(json.dumps({'type':'turn.completed','usage':{'input_tokens':10,'cached_input_tokens':5,'output_tokens':3}}))\n",
        encoding="utf-8")
    return [sys.executable, str(script)]


def test_fake_proposal_only_writes_allowed_artifact(tmp_path: Path) -> None:
    config, attempt = prepared(tmp_path)
    task = Path(config.workspace) / "TASK.md"
    before = task.read_bytes()
    executor = CodexExecutor(tmp_path / "evidence", model="fake", command=fake_cli(tmp_path), provenance="mock")
    result = executor.execute(attempt, config, [])
    assert result.status == "pending_review"
    assert result.provenance == "mock"
    assert result.acceptance.interface_live == "not_run"
    assert result.acceptance.task_live == "not_run"
    assert result.usage.tokens == 13
    assert result.usage.cost_usd is None
    assert task.read_bytes() == before
    assert (Path(config.workspace) / "sample.py").read_text() == FIXED
    with pytest.raises(FileExistsError):
        executor.execute(attempt, config, [])


@pytest.mark.parametrize("path,adopted", [("../test.py", []), ("sample.py", ["not-injected"])])
def test_invalid_proposal_does_not_modify_task(tmp_path: Path, path: str, adopted: list[str]) -> None:
    config, attempt = prepared(tmp_path)
    executor = CodexExecutor(tmp_path / "evidence", model="fake",
                             command=fake_cli(tmp_path, path=path, adopted=adopted), provenance="mock")
    result = executor.execute(attempt, config, [])
    assert result.status == "insufficient_evidence"
    assert (Path(config.workspace) / "sample.py").read_text() == "broken = True\n"


def test_unmeasured_usage_is_unknown(tmp_path: Path) -> None:
    events = tmp_path / "events.jsonl"
    events.write_text('{"type":"thread.started"}\n')
    assert read_usage(events).tokens is None
    assert read_usage(events).cost_usd is None


def test_token_limit_rejects_application(tmp_path: Path) -> None:
    config, attempt = prepared(tmp_path)
    config = RunConfig.model_validate({**config.model_dump(), "max_tokens": 12})
    executor = CodexExecutor(tmp_path / "evidence", model="fake", command=fake_cli(tmp_path), provenance="mock")
    result = executor.execute(attempt, config, [])
    assert result.status == "insufficient_evidence"
    assert "budget exhausted" in result.verdict.summary
    assert (Path(config.workspace) / "sample.py").read_text() == "broken = True\n"


def test_no_progress_stops_subprocess_without_retry(tmp_path: Path) -> None:
    config, attempt = prepared(tmp_path)
    executor = CodexExecutor(tmp_path / "evidence", model="fake", command=fake_cli(tmp_path, sleep=True),
                             provenance="mock", no_progress_seconds=0.3)
    result = executor.execute(attempt, config, [])
    assert result.status == "insufficient_evidence"
    assert "no progress" in result.verdict.summary
    assert result.usage.tokens is None


def test_stop_before_launch_has_no_evidence_or_side_effect(tmp_path: Path) -> None:
    config, attempt = prepared(tmp_path)
    executor = CodexExecutor(tmp_path / "evidence", model="fake", command=fake_cli(tmp_path),
                             provenance="mock", stop_requested=lambda: True)
    assert "manual stop" in executor.execute(attempt, config, []).verdict.summary
    assert not (tmp_path / "evidence").exists()


def test_extra_files_and_hardlinks_are_rejected(tmp_path: Path) -> None:
    config, _ = prepared(tmp_path)
    workspace = Path(config.workspace)
    (workspace / "secret.txt").write_text("not permitted")
    with pytest.raises(ValueError, match="only"):
        task_workspace(config)
    (workspace / "secret.txt").unlink()
    (tmp_path / "alias.py").hardlink_to(workspace / "sample.py")
    with pytest.raises(ValueError, match="ordinary private"):
        task_workspace(config)


def test_custom_cli_cannot_claim_live(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="mock provenance"):
        CodexExecutor(tmp_path / "evidence", model="fake", command=[sys.executable])


def test_proposal_cannot_execute_io_in_verifier(tmp_path: Path) -> None:
    config, attempt = prepared(tmp_path)
    executor = CodexExecutor(tmp_path / "evidence", model="fake",
                             command=fake_cli(tmp_path, content="import os\n" + FIXED), provenance="mock")
    assert executor.execute(attempt, config, []).status == "insufficient_evidence"
    assert (Path(config.workspace) / "sample.py").read_text() == "broken = True\n"
    with pytest.raises(ValueError, match="capability"):
        validate_sample(FIXED.replace("return list(dict.fromkeys(items))", "min = open\n    return min('outside', 'w')"))


def test_timeout_and_manual_stop_during_invocation(tmp_path: Path) -> None:
    config, attempt = prepared(tmp_path)
    config = RunConfig.model_validate({**config.model_dump(), "timeout_seconds": 0.3})
    command = fake_cli(tmp_path, sleep=True)
    executor = CodexExecutor(tmp_path / "timeout", model="fake", command=command, provenance="mock")
    assert "timeout" in executor.execute(attempt, config, []).verdict.summary
    started = time.monotonic()
    executor = CodexExecutor(tmp_path / "manual", model="fake", command=command, provenance="mock",
                             stop_requested=lambda: time.monotonic() - started > 0.1)
    assert "manual stop" in executor.execute(attempt, config, []).verdict.summary
