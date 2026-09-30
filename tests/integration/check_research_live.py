"""Read an actual three-role archive; never launch, claim, approve or adopt.

Run explicitly after live operations, using the locked integration environment.
Failure leaves the original archive unchanged. Unknown effects cannot pass.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import json
import math
from pathlib import Path

from local_assets import LocalAssetStore
from local_assets.models import Candidate
from orchestration.experiments.executor import read_result
from orchestration.experiments.models import ExperimentContext, ExperimentPlan
from swarm.research.models import HostConfig
from swarm.task_ledger import TaskLedger


TOOLS = {
    "discover_tasks", "project_context", "lease_task", "search_evidence",
    "research_experiment", "research_candidate", "verify_research",
    "complete_research_task", "approve_candidate", "inherit_experience", "apply_candidate",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def events(root: Path, phase: str):
    return [json.loads(line)["event"] for line in
            (root / f"{phase}-native/native-bound.jsonl").read_text(encoding="utf-8").splitlines()]


def native_calls(root: Path, phase: str):
    calls = []
    for event in events(root, phase):
        raw = event["raw"]
        if not isinstance(raw, dict):
            continue
        if event.get("native_type") == "item.completed" and isinstance(raw.get("item"), dict):
            item = raw["item"]
            if item.get("type") == "mcp_tool_call":
                calls.append((item.get("tool"), item.get("arguments", {}), item))
        elif event["kind"] == "tool" and event["runtime"] == "claude":
            for block in raw.get("message", {}).get("content", []):
                if block.get("type") == "tool_use" and block.get("id") == event["tool_id"]:
                    calls.append((block["name"].removeprefix("mcp__morph_research__"), block["input"], block))
    return calls


def fraction_check(result):
    """Separate exact calculation from archived inputs, including every residual."""
    archive = Path(result.archive_path)
    lines = (archive / "inputs/NumAcc4.dat").read_text(encoding="ascii").splitlines()
    values = [Fraction(line.strip()) for line in lines[60:] if line.strip()]
    assert len(values) == 1001
    assert set(values) == {Fraction("10000000.1"), Fraction("10000000.2"), Fraction("10000000.3")}
    mean = sum(values, Fraction(0)) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    assert variance == Fraction("0.01")
    output = load(archive / "outputs/metrics.json")
    assert output["count"] == len(values)
    assert math.isfinite(output["mean"]) and math.isfinite(output["sample_variance"])
    assert abs(output["mean"] - float(mean)) <= result.plan.criteria.mean_absolute_tolerance
    assert abs(output["sample_variance"] - float(variance)) <= result.plan.criteria.variance_absolute_tolerance
    assert len(output["residuals"]) == len(values)
    assert all(math.isfinite(r) and abs(r - float(v - mean)) <= result.plan.criteria.residual_absolute_tolerance
               for v, r in zip(values, output["residuals"], strict=True))
    numbers = [float(value) for value in values]
    naive = (sum(v * v for v in numbers) - sum(numbers) ** 2 / len(numbers)) / (len(numbers) - 1)
    assert output["naive_variance"] == naive
    return {"count": len(values), "exact_mean": str(mean), "exact_variance": str(variance)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    args = parser.parse_args()
    root = args.state.resolve(strict=True)
    configs = {role: HostConfig.model_validate_json((root / f"{role}-host.json").read_bytes())
               for role in ("author", "replication", "inheritance")}
    assert len({c.worker_id for c in configs.values()}) == 3
    assert len({c.agent.model_dump_json() for c in configs.values()}) == 3
    assert len({c.swarm_id for c in configs.values()}) == 1
    assert all(not root.is_relative_to(Path(c.workspace).resolve()) for c in configs.values())
    config = configs["author"]
    assert Path(config.ledger_path).is_file() and Path(config.assets_root).is_dir()
    ledger = TaskLedger(config.ledger_path, config.swarm_id)
    store = LocalAssetStore(config.assets_root)
    tasks = {role: ledger.get(role) for role in configs}
    audit = ledger.audit(limit=10000)
    phases = ["interrupt", "resume", "replication", "inheritance"]
    if (root / "interrupt-recovery-observation.json").exists():
        phases.insert(1, "interrupt-recovery")
    observations = {phase: load(root / f"{phase}-observation.json") for phase in phases}
    interruption_phase = "interrupt-recovery" if "interrupt-recovery" in observations else "interrupt"
    interrupted = observations[interruption_phase]
    resumed = observations["resume"]
    assert interrupted["interruption_observed"] is True
    assert interrupted["outcome"]["exit_code"] not in (None, 0)
    assert interrupted["outcome"]["reason"] == "cancelled; usage and remote effect may be unknown"
    assert not any(a["event"] == "execution_unconfirmed" for a in load(root / f"{interruption_phase}-ledger-audit.json"))
    assert interrupted["old_attempt"] is not None
    assert interrupted["outcome"]["session_id"] == resumed["outcome"]["session_id"]
    if interruption_phase == "interrupt-recovery":
        denied = observations["interrupt"]
        assert denied["interruption_observed"] is False and denied["held_task"]["status"] == "available"
        assert denied["outcome"]["session_id"] == interrupted["outcome"]["session_id"]
        assert not any(a["event"] in {"claimed", "execution_unconfirmed"}
                       for a in load(root / "interrupt-ledger-audit.json"))
        assert "MCP tool call requires approval, but approval policy is never" in (root / "interrupt-native/native.jsonl").read_text(encoding="utf-8")
    uuids = {resumed["outcome"]["session_id"], observations["replication"]["outcome"]["session_id"],
             observations["inheritance"]["outcome"]["session_id"]}
    assert len(uuids) == 3 and None not in uuids
    assert observations["replication"]["outcome"]["runtime"] == "claude"
    assert resumed["outcome"]["runtime"] == observations["inheritance"]["outcome"]["runtime"] == "codex"
    for role in configs:
        phases = [o for o in observations.values() if o["role"] == role]
        assert sum(o["wall_seconds"] for o in phases) <= 900
        assert sum(o["outcome"]["observed_tool_calls"] for o in phases) <= 64
    for phase in observations:
        assert observations[phase]["outcome"]["provenance"] == "live"
        for event in events(root, phase):
            name = event.get("tool_name")
            if event["kind"] == "tool" and name:
                assert name.removeprefix("mcp__morph_research__") in TOOLS, name
        launch = load(root / f"{phase}-launch.json")
        binding = launch["plan"]["host_binding"]
        role = observations[phase]["role"]
        assert binding["agent"] == configs[role].agent.model_dump(mode="json")
        assert binding["worker_id"] == configs[role].worker_id
        assert binding["swarm_id"] == configs[role].swarm_id
        argv = launch["plan"]["argv"]
        if role == "replication":
            assert launch["request"]["permission_mode"] == "dontAsk"
            assert set(launch["request"]["allowed_tools"]) == {"mcp__morph_research__" + t for t in TOOLS}
            assert "--strict-mcp-config" in argv and argv[argv.index("--tools") + 1] == ""
        else:
            assert launch["request"]["sandbox"] == "read-only"
            assert 'default_permissions=":read-only"' in argv and 'approval_policy="never"' in argv
            if phase != "interrupt" or interruption_phase == "interrupt":
                assert 'mcp_servers.morph_research.default_tools_approval_mode="prompt"' in argv
                assert all(f'mcp_servers.morph_research.tools.{tool}.approval_mode="approve"' in argv for tool in TOOLS)
    for phase in ("resume", "replication", "inheritance"):
        assert observations[phase]["outcome"]["state"] == "completed"
        calls = native_calls(root, phase)
        assert any(name == "discover_tasks" for name, _, _ in calls)
        assert any(name == "lease_task" and a.get("action") == "claim" for name, a, _ in calls)
        assert any(name == "lease_task" and a.get("action") == "renew" for name, a, _ in calls)
        if phase == "inheritance":
            assert any(name == "search_evidence" for name, _, _ in calls)
        if phase == "resume":
            stale = interrupted["held_task"]["token"]
            renew_rejected = submit_rejected = False
            for name, arguments, item in calls:
                if name == "lease_task" and arguments.get("action") == "claim":
                    assert renew_rejected and submit_rejected, "claim preceded both genuine stale rejections"
                    break
                if name == "lease_task" and arguments.get("action") == "renew" and arguments.get("token") == stale:
                    assert "lease_expired_or_not_claimed" in json.dumps(item)
                    renew_rejected = True
                if name == "research_candidate" and arguments.get("action") == "submit" and arguments.get("token") == stale:
                    old_candidate = Candidate.model_validate(arguments["candidate"])
                    assert old_candidate.attempt.model_dump(mode="json") == interrupted["old_attempt"]
                    expected = Candidate.model_validate({**tasks["author"].signal.payload["candidate_template"],
                                                         "attempt": interrupted["old_attempt"]})
                    assert old_candidate == expected
                    assert "lease_expired_or_not_claimed" in json.dumps(item)
                    submit_rejected = True
            assert renew_rejected and submit_rejected
    assert tasks["author"].token > interrupted["held_task"]["token"]
    assert any(a["event"] == "claimed" and a["task_id"] == "author"
               and a["at"] > interrupted["held_task"]["expires_at"] for a in audit)
    assert all(t.status == "completed" and t.result_id and t.result for t in tasks.values())
    assert tasks["author"].effect_applied is False
    assert tasks["replication"].effect_applied is tasks["inheritance"].effect_applied is True
    source = tasks["author"].result["asset_id"]
    assert tasks["replication"].result["candidate_asset_id"] == source
    original = store.fetch_approved(source)
    assert original.attempt.agent == configs["author"].agent
    assert original.attempt.attempt == tasks["author"].attempts
    assert tasks["author"].result["approved"] is False
    run_summaries = []
    for role, task in tasks.items():
        began = [a for a in audit if a["task_id"] == role and a["event"] == "execution_unconfirmed"]
        executed = [a for a in audit if a["task_id"] == role and a["event"] == "research_execution"]
        assert len(began) == len(executed) == 1
        body = executed[0]["body"]
        if isinstance(body, str):
            body = json.loads(body)
        assert body["worker_id"] == configs[role].worker_id and body["token"] == task.token
        plan = ExperimentPlan.model_validate(task.acceptance["experiment_plan"])
        assert plan.role == role and plan.parameters == ("original",)
        context = ExperimentContext(run_id=body["run_id"], task_id=role, worker_id=configs[role].worker_id,
                                    fencing_token=task.token)
        result = read_result(configs[role].evidence_root, body["run_id"], expected_plan=plan, expected_context=context)
        assert result.provenance == "live" and result.execution_state == "succeeded"
        assert result.scientific.verdict == "passed" and result.remote_effect == "known"
        assert result.cleanup_state == "destroyed" and result.sandbox_id
        assert result.usage is None and result.cost_usd is None
        assert (Path(result.archive_path) / "inputs/experiment.py").read_bytes() == original.changes[0].after.encode()
        run_summaries.append({"role": role, "run_id": context.run_id, "sandbox_id": result.sandbox_id,
                              "archive": result.archive_path, "fraction": fraction_check(result)})
    assert len({r["run_id"] for r in run_summaries}) == len({r["sandbox_id"] for r in run_summaries}) == 3
    reports = store.research_reports(source)
    for role, purpose in (("author", "original"), ("replication", "reproduction"), ("inheritance", "inheritance")):
        matches = [r for r in reports if r.task_id == role and r.purpose == purpose]
        assert len(matches) == 1 and matches[0].provenance == "live"
        assert matches[0].scientific_verdict == "passed" and matches[0].fencing_token == tasks[role].token
    adoptions = store.adoptions()
    assert len(adoptions) == 1
    receipt = adoptions[0]
    child_task = tasks["inheritance"]
    execution = store.consumption(child_task.result["execution_id"])
    assert receipt.asset_id == execution.asset_id == source
    assert receipt.context == execution.context
    assert receipt.result_id == child_task.result_id
    assert receipt.context.task_id == "inheritance" and receipt.context.worker_id == configs["inheritance"].worker_id
    assert receipt.context.fencing_token == child_task.token and receipt.context.scope == "science"
    assert receipt.candidate_asset_id == execution.candidate_asset_id == child_task.result["candidate_asset_id"]
    assert child_task.result["consumed_asset_ids"] == [source]
    assert child_task.result["input_context"] == receipt.context.input_context
    child = store.fetch_approved(receipt.candidate_asset_id)
    assert child == execution.candidate and child.attempt.agent == configs["inheritance"].agent
    assert len(child.changes) == 1 and child.changes[0].path == "science/reused.py"
    assert child.changes[0].before is None and child.changes[0].after == original.changes[0].after
    target = Path(config.workspace)
    assert (target / "science/experiment.py").read_bytes() == original.changes[0].after.encode()
    assert (target / "science/reused.py").read_bytes() == child.changes[0].after.encode()
    print(json.dumps({"task_live": "passed", "sessions": sorted(uuids), "runs": run_summaries,
                      "source_asset": source, "adoption": receipt.model_dump(mode="json"),
                      "metabolism_UseRecord": "not generated; existing AdoptionReceipt is actual use evidence"}, indent=2))


if __name__ == "__main__":
    main()
