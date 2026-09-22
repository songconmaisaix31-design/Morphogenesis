from pathlib import Path

import pytest

from bootstrap.sample import prepare_workspace
from bootstrap.verify import SampleVerifier
from contracts import AgentId
from contracts.protocols import Verifier


def test_fixed_independent_acceptance_and_real_caller(tmp_path: Path) -> None:
    workspace = prepare_workspace(tmp_path / "executor")
    assert sorted(path.name for path in workspace.iterdir()) == ["TASK.md", "sample.py"]
    verifier: Verifier = SampleVerifier(tmp_path / "evidence")
    reviewer = AgentId(role="reviewer", instance=0)
    broken = verifier.verify(str(workspace), reviewer)
    assert broken.passed is False
    assert broken.exit_code == 1
    # A deterministic fixture repair validates evaluator semantics; not a model task run.
    source = (workspace / "sample.py").read_text(encoding="utf-8")
    fixed = source.replace("min(lower, max(upper, value))", "max(lower, min(upper, value))")
    fixed = fixed.replace("(len(values) + 1)", "len(values)")
    fixed = fixed.replace("sorted(set(items))", "list(dict.fromkeys(items))")
    (workspace / "sample.py").write_text(fixed, encoding="utf-8")
    # Candidate-supplied discovery hooks must not get loaded by the independent runner.
    (workspace / "conftest.py").write_text("raise RuntimeError('untrusted')", encoding="utf-8")
    passed = verifier.verify(str(workspace), reviewer)
    assert passed.passed is True
    assert passed.exit_code == 0
    assert passed.reviewer == reviewer
    reports = list((tmp_path / "evidence").glob("verification-*.txt"))
    assert len(reports) == 2
    assert any("Ran 3 tests" in report.read_text(encoding="utf-8") for report in reports)


def test_prepare_does_not_overwrite_and_verifier_is_external(tmp_path: Path) -> None:
    workspace = prepare_workspace(tmp_path / "executor")
    with pytest.raises(FileExistsError):
        prepare_workspace(workspace)
    with pytest.raises(ValueError, match="outside"):
        SampleVerifier(workspace / "evidence").verify(str(workspace), AgentId(role="reviewer", instance=0))


def test_verifier_timeout_is_unknown(tmp_path: Path) -> None:
    workspace = prepare_workspace(tmp_path / "executor")
    (workspace / "sample.py").write_text("while True: pass", encoding="utf-8")
    result = SampleVerifier(tmp_path / "evidence", timeout_seconds=0.1).verify(
        str(workspace), AgentId(role="reviewer", instance=0)
    )
    assert result.passed is None
    assert result.exit_code is None


def test_early_process_exit_is_not_acceptance(tmp_path: Path) -> None:
    workspace = prepare_workspace(tmp_path / "executor")
    (workspace / "sample.py").write_text("raise SystemExit(0)", encoding="utf-8")
    result = SampleVerifier(tmp_path / "evidence").verify(
        str(workspace), AgentId(role="reviewer", instance=0)
    )
    assert result.passed is None
