"""Compare installed Python/Node bridge bytes with an exact git archive, read-only."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path
import sys
import tomllib
import zipfile


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    site = Path(sys.prefix) / "Lib" / "site-packages"
    checked, missing, mismatches = [], [], []
    with zipfile.ZipFile(args.archive) as archive:
        project = tomllib.loads(archive.read("pyproject.toml").decode())
        packages = {item["include"] for item in project["tool"]["poetry"]["packages"]}
        lock = tomllib.loads(archive.read("poetry.lock").decode())
        for name in archive.namelist():
            if name.split("/")[0] not in packages or not name.endswith((".py", ".mjs")):
                continue
            installed = site / name
            if not installed.is_file():
                missing.append(name)
            elif installed.read_bytes() != archive.read(name):
                mismatches.append(name)
            checked.append(name)
    distribution = importlib.metadata.distribution("morphogenesis")
    direct = json.loads(distribution.read_text("direct_url.json") or "{}")
    locked = {p["name"].lower().replace("_", "-"): p["version"] for p in lock["package"]}
    drift = []
    installed_versions = {}
    for dist in importlib.metadata.distributions():
        name = dist.metadata["Name"].lower().replace("_", "-")
        installed_versions[name] = dist.version
        if name in locked and dist.version != locked[name]:
            drift.append({"name": name, "installed": dist.version, "lock": locked[name]})
    result = {"requested_source": args.source, "git_archive": str(args.archive.resolve()),
              "python": sys.executable, "cwd": str(Path.cwd()), "direct_url": direct,
              "version": distribution.version, "byte_scope": "all tracked product package .py and .mjs files",
              "checked": checked, "missing": missing, "mismatches": mismatches,
              "installed_versions": installed_versions, "lock_drift": drift,
              "passed": not missing and not mismatches and not drift and not direct.get("dir_info", {}).get("editable", False)}
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    print(json.dumps({"passed": result["passed"], "checked": len(checked), "missing": len(missing),
                      "mismatches": len(mismatches), "lock_drift": len(drift)}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
