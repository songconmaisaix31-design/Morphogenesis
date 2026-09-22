"""Strict checking of every present package in the declared root layout."""

from pathlib import Path
import subprocess
import sys

PACKAGES = (
    "contracts", "persistence", "bootstrap", "tools", "hub_client", "bridge_node",
    "orca_provision", "orchestration", "topology", "metabolism", "mocks", "viz", "demo",
)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    present = [name for name in PACKAGES if root.joinpath(name).is_dir()
               and any(root.joinpath(name).rglob("*.py"))]
    return subprocess.call([sys.executable, "-m", "mypy", "--strict", *present], cwd=root)


if __name__ == "__main__":
    raise SystemExit(main())
