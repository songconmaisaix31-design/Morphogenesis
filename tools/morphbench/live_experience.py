"""Fresh-process and fresh-target experience control using existing asset stores."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
import time
from typing import Any

from live_cases import BY_NAME, PUBLIC_SPEC
from live_run import budget, config_for, enqueue, identity, mock_executor, observe, setup, start, write


def new_target(root: Path, defect: str) -> Path:
    from local_assets.paths import git
    target = root / "target"
    (target / "t00").mkdir(parents=True, exist_ok=False)
    (target / "t00" / "sample.py").write_bytes(BY_NAME[defect].source.encode())
    git(target, "init", "-b", "transfer")
    git(target, "-c", "core.autocrlf=false", "add", ".")
    git(target, "-c", "user.name=MorphBench", "-c", "user.email=local@localhost", "commit", "-m", "transfer seed")
    return target


def wrong_control(worker: Any, task_id: str) -> dict[str, Any]:
    from contracts.identity import AttemptId
    from local_assets.models import AssetSafetyError, ConsumptionContext, FileChange, SampleValidationPolicy
    from local_assets.paths import git
    from local_assets.validate import AssetValidator
    from swarm.code_patch import SamplePatch, candidate_from_patch
    target = worker.target
    path = "t00/sample.py"
    head = git(target, "rev-parse", "HEAD").decode().strip()
    policy = SampleValidationPolicy(version="sample-tests-v1", path=path)
    candidate = candidate_from_patch(SamplePatch(changes=(FileChange(path=path,
        before=(target / path).read_bytes().decode(), after=BY_NAME["unique-order"].source),)),
        policy, attempt=AttemptId(task_id=task_id, agent=worker.config.agent, attempt=0),
        scope="t00", base_revision=head, base_head=head)
    asset = worker.assets.publish(candidate)
    report = AssetValidator(worker.assets, target, policy=policy, timeout_seconds=20).validate(asset)
    context = ConsumptionContext(swarm_id=worker.config.swarm_id, task_id=task_id,
        worker_id=worker.worker_id, fencing_token=1, execution_id=task_id + "-rejected-probe",
        scope="t00", capabilities=("clamp", "mean", "unique"), input_context="safe negative control")
    refused = False
    reason = None
    try:
        worker.consumer.inject(asset, context)
    except AssetSafetyError as error:
        refused, reason = True, str(error)
    return {"asset_id": asset, "validation": report.model_dump(mode="json"),
            "refused": refused, "reason": reason,
            "provenance": "local_operator_negative_control", "model_generated": False,
            "injected_to_model": False, "adoption": None}


def run(root: Path, seed: int, mode: str) -> dict[str, Any]:
    from contracts.identity import AgentId
    from local_assets.models import SampleValidationPolicy
    from swarm.code_executor import DashScopeCodeConfig, DashScopeCodeExecutor
    from swarm.models import Locality, Signal
    from swarm.worker_loop import Worker
    root.mkdir(parents=True, exist_ok=False)
    cell = {"id": f"experience-s{seed}", "category": "code", "system": "single", "seed": seed,
            "request_cap": 4, "ledger_cap": 4}
    target, state, source = setup(root / "generation", cell, ["generation-composite"], 1, mode)
    # Composite generation remains a supported repair capability, not a fourth
    # routing family inferred from its file name.
    enqueue(source, "generation-composite", 0, 0, root / "arrivals.jsonl")
    settings = DashScopeCodeConfig()
    rows = []
    processes = []
    started = time.time()
    for index, arm in enumerate(("source", "none", "correct", "wrong")):
        folder = root / arm
        folder.mkdir()
        if arm != "source":
            target = new_target(folder, "mean-empty")
        config = config_for(target, state, cell, 0, 4, 1).model_copy(update={
            "agent": AgentId(role="builder", instance=seed * 10 + index), "energy": 1,
            "locality": Locality(workspace=str(target), authorized_scopes=(".",), modules=("clamp", "mean", "unique")),
            "budget": budget(4)})
        executor = mock_executor(settings) if mode == "offline" else DashScopeCodeExecutor(settings)
        worker = Worker(config, executor)
        task_id = "t00-generation-composite" if arm == "source" else f"transfer-{arm}"
        negative = wrong_control(worker, task_id) if arm == "wrong" else None
        if negative is not None and (not negative["refused"] or negative["validation"]["passed"]):
            raise RuntimeError("negative_asset_must_be_rejected_without_bypassing_review")
        if arm != "source":
            payload: dict[str, Any] = {"instruction": PUBLIC_SPEC, "output_path": "t00/sample.py", "phase": "0"}
            dependencies: tuple[str, ...] = ()
            if arm == "correct":
                payload.update({"reuse_task_id": "t00-generation-composite", "path_map": {"t00/sample.py": "t00/sample.py"}})
                dependencies = ("t00-generation-composite",)
            signal = Signal(task_id=task_id, signal_id=task_id, workspace=str(target), scope="t00",
                module="mean", kind="error_pattern", required_capability="mean", payload=payload)
            worker.ledger.enqueue(signal, dependencies=dependencies,
                acceptance={"validation_policy": SampleValidationPolicy(version="sample-tests-v1", path="t00/sample.py").model_dump(mode="json")})
            worker.field.deposit(signal)
        spec = folder / "worker.json"
        write(spec, {"worker": config.model_dump(mode="json"), "executor": settings.model_dump(mode="json"), "mode": mode})
        process, fact = start(spec)
        processes.append((process, fact))
        try:
            process.wait(timeout=180)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=15)
        record = worker.ledger.get(task_id)
        row = {"arm": arm, "target": str(target), "state": str(state), "process": fact,
               "record": record.model_dump(mode="json"), "negative_control": negative}
        rows.append(row)
        write(folder / "observation.json", row)
        snapshot = worker.budget.snapshot()
        if snapshot.pending_reservations or snapshot.uncertain_reservations:
            break
    final = observe(root, cell, source, processes, started, mode)
    # Read actual program receipts. Never synthesize success/adoption from model text.
    with source.assets.connection() as database:
        final["adoptions"] = [dict(r) for r in database.execute("SELECT * FROM adoptions").fetchall()]
        final["consumptions"] = [dict(r) for r in database.execute("SELECT * FROM consumptions").fetchall()]
    final.update({"arms": rows, "generation_defect": "generation-composite", "transfer_defect": "mean-empty",
                  "session_definition": "fresh process + worker identity + target; shared same-swarm source ledger/assets, no DB copy"})
    write(root / "result.json", final)
    return final


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, choices=range(3), required=True)
    parser.add_argument("--mode", choices=("offline", "live"), default="offline")
    args = parser.parse_args()
    identity()
    result = run(args.out, args.seed, args.mode)
    print(json.dumps({"arms": len(result["arms"]), "stop_paid": result["stop_paid"],
                      "adoptions": len(result["adoptions"]), "mode": args.mode}))
    raise SystemExit(2 if result["stop_paid"] else 0)
