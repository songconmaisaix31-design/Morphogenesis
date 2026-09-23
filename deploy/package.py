"""Create a standard git archive of one reviewed SHA, using a file allowlist."""

from __future__ import annotations

import argparse
from pathlib import Path, PurePosixPath
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PYTHON_PACKAGES = {
    "contracts", "persistence", "bootstrap", "bridge_node", "hub_client",
    "orca_provision", "orchestration", "topology", "metabolism", "mocks", "viz",
}
FILES = {
    "pyproject.toml", "poetry.lock", "package.json", "package-lock.json",
    "README.md", "LICENSE", "THIRD_PARTY_NOTICES.md", "demo/data/mock-run.json",
    "deploy/Dockerfile", "deploy/Dockerfile.dockerignore", "deploy/compose.yaml",
    "deploy/compose.replay.yaml", "deploy/nginx.conf", "deploy/proxy.conf",
    "deploy/healthcheck.py", "deploy/package.py", "deploy/smoke.py", "deploy/README.md",
}
STATIC_SUFFIXES = {".html", ".js", ".css", ".woff2", ".txt", ".md"}


def allowed(name: str) -> bool:
    path = PurePosixPath(name)
    if any(part.startswith(".") or part == "__pycache__" for part in path.parts):
        return False
    if name in FILES:
        return True
    if name.startswith("viz/static/"):
        return path.suffix in STATIC_SUFFIXES
    return len(path.parts) == 2 and path.parts[0] in PYTHON_PACKAGES and path.suffix == ".py"


def package(sha: str, output: Path, *, root: Path = ROOT) -> list[str]:
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("Use an exact 40-character reviewed commit SHA")
    subprocess.run(["git", "cat-file", "-e", f"{sha}^{{commit}}"], cwd=root, check=True)
    records = subprocess.check_output(["git", "ls-tree", "-rz", sha], cwd=root).split(b"\0")
    names = []
    for record in filter(None, records):
        metadata, raw_name = record.split(b"\t", 1)
        name = raw_name.decode("utf-8")
        if allowed(name):
            if metadata.split()[0] not in {b"100644", b"100755"}:
                raise ValueError(f"Refusing non-regular release file: {name}")
            names.append(name)
    required = FILES | {"viz/server.py", "viz/static/index.html", "viz/static/assets/finals-shell.js", "viz/static/assets/finals-shell.css"}
    if required - set(names):
        raise ValueError(f"Incomplete release: {sorted(required - set(names))}")
    if output.exists():
        raise ValueError("Output exists; choose a new archive path")
    # git archive reads committed blobs; dirty files, symlinks and untracked secrets
    # never enter the bundle. No custom manifest or digest format is introduced.
    subprocess.run([
        "git", "archive", "--format=tar.gz", f"--prefix={sha}/",
        f"--output={output.resolve()}", sha, "--", *names,
    ], cwd=root, check=True)
    return names


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sha")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    files = package(args.sha, args.output)
    print(f"Packaged {len(files)} committed files from {args.sha} into {args.output}")
