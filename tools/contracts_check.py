"""Run caller-to-implementation semantic checks, not signature reflection."""

from pathlib import Path
import subprocess
import sys


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    return subprocess.call(
        [sys.executable, "-m", "pytest", "tests/t0", "-q"], cwd=root
    )


if __name__ == "__main__":
    raise SystemExit(main())
