"""Exercise the real checker entry point in isolated Python; no live state."""
from pathlib import Path
import subprocess
import sys


def test_registered_case_checker_help_with_isolated_python(tmp_path: Path) -> None:
    checker = Path(__file__).with_name("check_research_case_live.py").resolve()
    result = subprocess.run(
        [sys.executable, "-I", "-B", str(checker), "--help"],
        cwd=tmp_path, capture_output=True, text=True, timeout=30, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "--state" in result.stdout
