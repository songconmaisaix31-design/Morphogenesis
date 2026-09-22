"""Installed-wheel import/resource smoke check, separate from editable source imports."""

import argparse
import importlib
from importlib.resources import files
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

PACKAGES = (
    "contracts", "persistence", "bootstrap", "bridge_node", "hub_client", "orca_provision",
    "orchestration", "topology", "metabolism", "mocks", "viz",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-dir", type=Path, required=True)
    parser.add_argument("--check-node", action="store_true")
    args = parser.parse_args()
    target = args.site_dir.resolve()
    if not target.is_dir():
        parser.error("site-dir must be an installed wheel target")
    source = Path(__file__).resolve().parents[1]
    sys.path[:] = [str(target)] + [entry for entry in sys.path if Path(entry).resolve() != source]
    for name in PACKAGES:
        module = importlib.import_module(name)
        if module.__file__ is None or not Path(module.__file__).resolve().is_relative_to(target):
            raise AssertionError(f"{name} did not import from installed wheel target")
    resources = {
        "bootstrap": ["fixtures/sample.py.txt", "fixtures/TASK.md.txt", "acceptance_runner.py"],
        "bridge_node": ["asset_bridge.mjs"],
        "viz": ["static/index.html", "static/app.js", "static/style.css"],
    }
    for package, names in resources.items():
        for name in names:
            if not files(package).joinpath(name).read_bytes():
                raise AssertionError(f"missing or empty resource: {package}/{name}")
    for name in ("demo/README.md", "demo/run-demo.ps1", "demo/data/mock-run.json", "THIRD_PARTY_NOTICES.md"):
        if not target.joinpath(name).is_file():
            raise AssertionError(f"missing wheel data: {name}")
    from bootstrap.sample import prepare_workspace
    from bootstrap.verify import SampleVerifier
    from contracts.identity import AgentId

    with TemporaryDirectory(prefix="wheel-sample-") as directory:
        root = Path(directory)
        workspace = prepare_workspace(root / "executor")
        result = SampleVerifier(root / "evidence").verify(
            str(workspace), AgentId(role="reviewer", instance=0)
        )
        if result.passed is not False or result.exit_code != 1:
            raise AssertionError("installed evaluator did not reject the broken exercise")
    if args.check_node:
        bridge_module = importlib.import_module("bridge_node")
        if bridge_module.NodeAssetBridge().canonicalize({"b": 2, "a": 1}) != '{"a":1,"b":2}':
            raise AssertionError("installed Node bridge check failed")
    print(json.dumps({"scope": "contract_local", "packages_from_wheel": len(PACKAGES),
                      "resources_present": True, "installed_verifier": "passed",
                      "node_dependency_check": bool(args.check_node)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
