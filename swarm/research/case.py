"""Seed the one public CPU case through existing ledger and asset contracts."""
from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
from uuid import uuid4

from pydantic import JsonValue

from contracts.identity import AgentId
from local_assets.models import FileExpectation, ValidationPolicy
from local_assets.paths import SWARM_SOURCE, FROZEN_MAINLINE, git, no_links
from local_assets.research_models import ResearchClaim
from local_assets.validate import static_syntax
from swarm.models import Signal
from swarm.research.models import HostConfig
from swarm.task_ledger import TaskLedger

PENDING = "# Research candidate pending; no scientific result asserted.\n"


def seed_case(project: Path, state: Path, *, python: Path, plan: dict[str, JsonValue], code: str,
              swarm_id: str, domain: str, api_key_env: str | None = None) -> dict[str, str]:
    """Trusted operator entry, not an MCP administration tool; never allocate/execute."""
    for path in (project, state, python):
        if not path.is_absolute():
            raise ValueError("case_paths_must_be_absolute")
        no_links(path)
    project, state = project.resolve(), state.resolve()
    if (project == state or project.is_relative_to(state) or state.is_relative_to(project)
            or any(project.is_relative_to(p.resolve()) or state.is_relative_to(p.resolve())
                   for p in (SWARM_SOURCE, FROZEN_MAINLINE))):
        raise ValueError("case_project_and_protected_state_must_be_separate")
    if project.exists() or state.exists():
        raise ValueError("case_paths_must_not_exist_no_overwrite")
    if not python.is_file():
        raise ValueError("python_executable_required")
    static_syntax("science/experiment.py", code)
    if plan.get("mode", "script") != "script":
        raise ValueError("public_case_requires_script_mode")
    plan_id = plan.get("plan_id")
    criteria = plan.get("criteria")
    data = plan.get("data")
    environment = plan.get("environment")
    if (not isinstance(plan_id, str) or not isinstance(criteria, dict) or not isinstance(data, dict)
            or not isinstance(environment, dict) or criteria.get("version") != "nist-numacc4-v1"):
        raise ValueError("official_public_case_plan_required")
    state.mkdir(parents=True)
    (project / "science").mkdir(parents=True)
    git(project, "init", "-b", "research-numacc4")
    (project / "science/experiment.py").write_bytes(PENDING.encode())
    git(project, "add", "science")
    git(project, "-c", "user.name=Morphogenesis Research", "-c", "user.email=research@example.invalid",
        "commit", "-m", "Seed public NIST research task without results")
    revision = git(project, "rev-parse", "HEAD").decode().strip()
    claim = ResearchClaim.model_validate({"plan_id": plan_id, "criterion_version": criteria["version"],
        "conditions": {"data_sha256": data.get("sha256"), "image": environment.get("image"),
                       "parameters": json.dumps(plan.get("parameters"), sort_keys=True),
                       "seed": str(plan.get("seed"))}, "sources": [data.get("source")]})
    ledger = TaskLedger(state / "tasks.sqlite3", swarm_id)
    paths: dict[str, str] = {"project": str(project), "state": str(state), "swarm_id": swarm_id,
                            "python": str(python), "base_revision": revision}
    for role, instance, dependencies in (("author", 0, ()), ("replication", 1, ("author",)),
                                         ("inheritance", 2, ("author", "replication"))):
        role_plan = {**plan, "role": role}
        destination = "science/reused.py" if role == "inheritance" else "science/experiment.py"
        policy = ValidationPolicy(version="nist-" + role + "-files-v1",
                                  expectations=(FileExpectation(path=destination, content=code),))
        instructions = (
            "Discover and actively claim the eligible task with lease_task(action=claim); renew it during work. "
            "Read project_context and dependency_results. Use only the pre-registered experiment and trusted verification. "
            "Unknown effects stop without replay; retrieved/injected/applied/adopted are separate stages. ")
        if role == "author":
            instructions += ("Execute the registered case, submit the candidate template using your returned canonical attempt_id, "
                             "verify_research purpose=original, then complete_research_task while still quarantined. Do not approve your own result.")
        elif role == "replication":
            instructions += ("Take author.result.asset_id from dependency_results, run in a fresh sandbox, verify purpose=reproduction, "
                             "validate_files and approve only if the trusted gates pass; apply the original candidate through apply_candidate. "
                             "This completes replication and makes inheritance eligible.")
        else:
            instructions += ("Use author.result.asset_id, run local revalidation and verify purpose=inheritance; inherit_experience with "
                             "path_map science/experiment.py -> science/reused.py and preimage null, using the task base_revision. "
                             "Validate_files and approve the returned child, then apply_candidate with its execution_id. "
                             "The existing AssetConsumer records actual adoption only after bytes and ledger effect agree.")
        payload: dict[str, JsonValue] = {"question": "Reproduce NIST NumAcc4 sample variance using CPython statistics.variance.",
            "instructions": instructions, "sources": list(claim.sources), "base_revision": revision,
            "destination": destination, "original_scope": "science", "candidate_code": code}
        if role == "author":
            payload["candidate_template"] = {"base_revision": revision, "scope": "science",
                "changes": [{"path": destination, "before": PENDING, "after": code}],
                "declared_files": 1, "declared_lines": len(PENDING.splitlines()) + len(code.splitlines()),
                "summary": "NIST NumAcc4 variance method; predeclared conditions only", "research": claim.model_dump(mode="json")}
        ledger.enqueue(Signal(task_id=role, workspace=str(project), scope="science", kind="opportunity",
                              required_capability="research." + role, module="research", payload=payload),
                       dependencies=dependencies, acceptance={"experiment_plan": role_plan,
                           "research_claim": claim.model_dump(mode="json"), "file_policy": policy.model_dump(mode="json")})
        backend = {"domain": domain}
        if api_key_env is not None:
            backend["api_key_env"] = api_key_env
        config = HostConfig(ledger_path=str(ledger.path), swarm_id=swarm_id, workspace=str(project), worker_id=role,
            agent=AgentId(role="reviewer" if role == "replication" else "builder", instance=instance),
            authorized_scopes=("science",), capabilities=("research." + role,), assets_root=str(state / "assets"),
            evidence_root=str(state / "experiments"), project_context=instructions, experiment_backend=backend)
        path = state / (role + "-host.json")
        path.write_text(config.model_dump_json(indent=2), encoding="utf-8")
        paths[role + "_config"] = str(path)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize a trusted public NumAcc4 research space; no model or sandbox calls")
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--case-directory", type=Path, required=True)
    parser.add_argument("--swarm-id", default=None)
    parser.add_argument("--domain", default="127.0.0.1:8097")
    parser.add_argument("--api-key-env")
    args = parser.parse_args()
    if not args.case_directory.is_absolute():
        parser.error("--case-directory must be absolute")
    no_links(args.case_directory)
    factory = importlib.import_module("orchestration.experiments.case")
    plan = factory.public_case(args.case_directory, role="author", order="original")
    code = Path(plan.code.local_path).read_bytes().decode("utf-8")
    paths = seed_case(args.project, args.state, python=args.python, plan=plan.model_dump(mode="json"), code=code,
                      swarm_id=args.swarm_id or uuid4().hex, domain=args.domain, api_key_env=args.api_key_env)
    print(json.dumps(paths, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
