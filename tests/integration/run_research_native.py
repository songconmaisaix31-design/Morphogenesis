"""Explicit host observations using A's native loop and B's existing ledger.

Each invocation requires an explicit phase. This does not select tasks, execute
experiments, approve assets, write the ledger, or retry a failed invocation.
"""
import argparse
import json
import os
import sqlite3
from pathlib import Path
import sys
import time
import tomllib

from orchestration.native_agents import (
    LaunchRequest, McpStdio, ResearchBootstrap, build_launch, probe,
    run_headless, write_mcp_config,
)
from swarm.research.models import HostConfig
from swarm.task_ledger import TaskLedger
from orchestration.experiments.executor import read_result
from orchestration.experiments.models import ExperimentContext, ExperimentPlan

TOOLS = (
    "discover_tasks", "project_context", "lease_task", "search_evidence",
    "research_experiment", "research_candidate", "verify_research",
    "complete_research_task", "approve_candidate", "inherit_experience", "apply_candidate",
)


def write(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("interrupt", "interrupt-recovery", "resume", "local-completion", "replication", "inheritance"), required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--key-file", type=Path, required=True)
    parser.add_argument("--inspect-only", action="store_true", help="Probe and persist actual launch bindings without a model invocation")
    args = parser.parse_args()
    root = args.state.resolve(strict=True)
    interrupting = args.phase in {"interrupt", "interrupt-recovery"}
    role = "author" if interrupting or args.phase in {"resume", "local-completion"} else args.phase
    runtime = "claude" if role == "replication" else "codex"
    config_path = root / (role + "-host.json")
    config = HostConfig.model_validate_json(config_path.read_bytes())
    ledger = TaskLedger(config.ledger_path, config.swarm_id)
    observation = root / (args.phase + "-observation.json")
    evidence = root / (args.phase + "-native")
    if observation.exists() or evidence.exists():
        raise RuntimeError("an invocation is never replayed")
    previous = []
    for phase in ("interrupt", "interrupt-recovery", "resume", "local-completion", "replication", "inheritance"):
        path = root / (phase + "-observation.json")
        if path.exists():
            record = json.loads(path.read_text(encoding="utf-8"))
            if record["role"] == role:
                previous.append(record)
    wall_remaining = 895 - sum(r["wall_seconds"] for r in previous)
    tools_remaining = 64 - sum(r["outcome"]["observed_tool_calls"] for r in previous)
    if wall_remaining <= 0 or tools_remaining <= 0:
        raise RuntimeError("declared identity observation window exhausted")
    session = None
    known_execution = None
    source_asset = None
    if args.phase == "interrupt-recovery":
        denied = json.loads((root / "interrupt-observation.json").read_text(encoding="utf-8"))
        denied_raw = (root / "interrupt-native/native.jsonl").read_text(encoding="utf-8")
        denied_audit = json.loads((root / "interrupt-ledger-audit.json").read_text(encoding="utf-8"))
        if (denied["held_task"]["status"] != "available" or denied["interruption_observed"]
                or ledger.get("author").status != "available"
                or any(r["event"] in {"claimed", "execution_unconfirmed"} for r in denied_audit)
                or "MCP tool call requires approval, but approval policy is never" not in denied_raw):
            raise RuntimeError("explicit permission recovery requires original denial and no prior claim/experiment")
        session = denied["outcome"]["session_id"]
        if not session:
            raise RuntimeError("permission recovery requires the original observed UUID")
    if args.phase == "local-completion":
        prior = json.loads((root / "resume-observation.json").read_text(encoding="utf-8"))
        if prior["held_task"]["status"] == "completed" or prior["outcome"]["state"] != "completed":
            raise RuntimeError("explicit local completion requires the settled incomplete prior turn")
        session = prior["outcome"]["session_id"]
        first = json.loads((root / "interrupt-observation.json").read_text(encoding="utf-8"))
        if not session or session != first["outcome"]["session_id"]:
            raise RuntimeError("local completion must retain the original UUID")
        historical = json.loads((root / "resume-ledger-audit.json").read_text(encoding="utf-8"))
        executions = [r["body"] for r in historical if r["task_id"] == "author" and r["event"] == "research_execution"]
        if len(executions) != 1:
            raise RuntimeError("local completion requires exactly one actual historical execution")
        known_execution = executions[0]
        task = ledger.get("author")
        context = ExperimentContext(run_id=known_execution["run_id"], task_id="author",
            worker_id=known_execution["worker_id"], fencing_token=known_execution["token"])
        actual = read_result(config.evidence_root, context.run_id,
            expected_plan=ExperimentPlan.model_validate(task.acceptance["experiment_plan"]), expected_context=context)
        with sqlite3.connect(Path(config.ledger_path).resolve().as_uri() + "?mode=ro", uri=True) as database:
            pending = database.execute("SELECT unconfirmed_request_id FROM tasks WHERE swarm_id=? AND task_id=?",
                                       (config.swarm_id, "author")).fetchone()
        if (context.worker_id != config.worker_id or actual.provenance != "live"
                or actual.execution_state != "succeeded" or actual.scientific.verdict != "passed"
                or actual.remote_effect != "known" or actual.cleanup_state != "destroyed"
                or pending is None or pending[0] is not None):
            raise RuntimeError("local completion refuses unknown, changed or other-worker experiments")
        native = [json.loads(line) for line in (root / "resume-native/native.jsonl").read_text(encoding="utf-8").splitlines()]
        published = [e["item"] for e in native if e.get("type") == "item.completed"
            and e.get("item", {}).get("tool") == "research_candidate"
            and e["item"].get("status") == "completed" and e["item"]["arguments"].get("action") == "submit"
            and e["item"]["arguments"].get("token") == context.fencing_token]
        if len(published) != 1:
            raise RuntimeError("local completion requires the original actual published candidate")
        source_asset = published[0]["result"]["structured_content"]["result"]
        if not isinstance(source_asset, str) or not source_asset.startswith("sha256:"):
            raise RuntimeError("original candidate return is not an actual asset address")
    rules = [
        "Use only the eleven morph_research MCP tools. Never use shell, file writes, browser, subagents, or other MCP servers.",
        "Never write host config, authoritative SQLite, approved files or raw archives directly. Only trusted MCP can mutate them.",
        "Read actual tool metadata; all identities/scopes/plans come from host configuration and project_context.",
        "Actively discover your eligible task, read context/dependency_results, claim it yourself, then renew before any experiment. The host never assigns or claims for you.",
        "Every task has at most ONE external experiment, including unknown. Never retry an experiment.",
        "Use lease ttl_seconds=600 for normal work and renew proactively before the experiment and each evidence phase.",
        "Three roles use original data order. Complete the role's exact project_context instructions; stop on unknown effects.",
        "When submitting use candidate_template literally, adding canonical attempt_id as Candidate.attempt.",
        "Candidate.research, base_revision, changes and summary come from project_context, never invented IDs or results.",
        "For inherit_experience use base_revision from task payload, path_map science/experiment.py to science/reused.py, preimages science/reused.py null.",
    ]
    if interrupting:
        rules += [
            "INTERRUPTION PHASE: discover eligible work, choose author, read context, claim with ttl_seconds=60, then renew with ttl_seconds=30.",
            "DO NOT request/run any experiment, publish/submit candidate, verify, approve, apply, release or complete. Experiment execution is forbidden until an explicit resumed turn.",
            "After renewal, keep reading project_context until the host interrupts your owned process; do not end naturally.",
        ]
    elif args.phase == "resume":
        interruption_phase = "interrupt-recovery" if (root / "interrupt-recovery-observation.json").exists() else "interrupt"
        old = json.loads((root / (interruption_phase + "-observation.json")).read_text(encoding="utf-8"))
        session = old["outcome"]["session_id"]
        if not session or not old.get("interruption_observed"):
            raise RuntimeError("resume requires an observed actual interruption")
        lease = old["held_task"]
        if time.time() <= lease["expires_at"]:
            raise RuntimeError("real lease TTL has not expired")
        rules += [
            "This is the explicitly resumed original session after real TTL expiry. The old owned process exited; no external experiment occurred.",
            f"BEFORE claiming again, call lease_task(action=renew, task_id=author, token={lease['token']}); it MUST reject the stale holder.",
            "Then read project_context and call research_candidate(action=submit) with a structurally valid old candidate_template and this old canonical Candidate.attempt: "
            + json.dumps(old["old_attempt"])
            + f". Use task_id=author and OLD token={lease['token']}. This legal public submit MUST also reject stale fencing.",
            "Do not fix or bypass these expected stale rejections. After BOTH rejections, actively discover/claim author again, obtaining higher token and current canonical attempt_id.",
            "Continue the author workflow with the CURRENT token/attempt only: request, ONE run, submit original candidate, verify purpose original, complete evidence while quarantined.",
        ]
    elif args.phase == "local-completion":
        rules += [
            "EXPLICIT LOCAL COMPLETION ONLY: the previous optional file check has a FAILED TimeoutExpired report; preserve it. The external scientific experiment is already known succeeded and destroyed.",
            "Actively discover and reclaim author with a fresh current token, then renew. This is the original final claim budget, not a new task or run.",
            f"Use ONLY original candidate {source_asset} and existing run {known_execution['run_id']}; its immutable execution token is {known_execution['token']}, while your newly claimed token fences CURRENT verification/report/completion writes.",
            "Do not publish a new candidate, validate_files, request/run an experiment, approve, apply, release or change identity. No new experiment, sandbox, candidate or fabricated result is permitted.",
            "Read current context, verify_research purpose=original against that existing candidate/run using your CURRENT token, renew, then complete_research_task for the same original candidate/run while quarantined.",
            "If trusted known-result continuation rejects the original execution context, stop and report; never bypass its fence or change archived context. No automatic retry.",
        ]
    elif args.phase == "inheritance":
        rules += [
            "Actively search_evidence for the original NIST NumAcc4 experience and inspect the returned original asset; retrieval alone is not adoption.",
            "Use the source asset from actual dependency_results, execute ONE fresh local validation, verify purpose=inheritance, then inherit_experience with the exact scope path_map/base_revision.",
            "Validate and approve the returned child candidate, then apply_candidate with its actual execution_id; require the actual returned AdoptionReceipt, not a self-declared use record.",
        ]
    request = LaunchRequest(
        runtime=runtime, workspace=Path(config.workspace), session_id=session,
        prompt=ResearchBootstrap(space=config.swarm_id, agent=config.agent,
            objective="Finish the host-bound public NIST NumAcc4 research role with actual trusted evidence.",
            tool_names=TOOLS, rules=tuple(rules)).prompt(),
        mcp=McpStdio(command=sys.executable, args=("-m", "swarm.research", "--config", str(config_path))),
        sandbox="read-only" if runtime == "codex" else None,
        permission_mode="dontAsk" if runtime == "claude" else None,
        allowed_tools=tuple("mcp__morph_research__" + t for t in TOOLS) if runtime == "claude" else (),
    )
    measured = probe(runtime)
    if measured.version_matches is not True or measured.authenticated is not True:
        write(root / (args.phase + "-probe.json"), measured.model_dump(mode="json"))
        raise RuntimeError("official runtime version/auth precondition failed")
    prefix_name = args.phase + ("-inspection" if args.inspect_only else "")
    mcp_path = root / (prefix_name + "-mcp.json")
    plan = build_launch(request, claude_mcp_path=mcp_path)
    if runtime == "codex":
        native_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
        native_config = native_home / "config.toml"
        existing = tomllib.loads(native_config.read_text(encoding="utf-8")) if native_config.exists() else {}
        overrides = {
            "default_permissions": ":read-only", "approval_policy": "never",
            "features.shell_tool": False, "features.multi_agent": False,
            "features.multi_agent_v2": False, "agents.enabled": False,
            "features.apps": False, "features.plugins": False, "features.hooks": False,
            "features.browser_use": False, "features.computer_use": False,
            "web_search": "disabled", "mcp_servers.morph_research.required": True,
            "mcp_servers.morph_research.env_vars": [config.experiment_backend["api_key_env"]],
            "mcp_servers.morph_research.enabled_tools": list(TOOLS),
            "mcp_servers.morph_research.default_tools_approval_mode": "prompt",
        }
        # Official per-tool policy for this already-authorized trusted MCP only.
        # Enabled-tools is visibility; it is not an approval grant by itself.
        overrides.update({f"mcp_servers.morph_research.tools.{tool}.approval_mode": "approve" for tool in TOOLS})
        overrides.update({f"mcp_servers.{name}.enabled": False for name in existing.get("mcp_servers", {}) if name != "morph_research"})
        prefix = []
        for key, value in overrides.items():
            prefix += ["-c", key + "=" + json.dumps(value)]
        command_length = len(measured.command)
        plan = plan.model_copy(update={"argv": plan.argv[:command_length] + tuple(prefix) + plan.argv[command_length:]})
    else:
        plan = plan.model_copy(update={"argv": plan.argv + ("--strict-mcp-config", "--tools", "", "--disable-slash-commands")})
        write_mcp_config(plan, mcp_path)
    write(root / (prefix_name + "-launch.json"), {"request": request.model_dump(mode="json"), "plan": plan.model_dump(mode="json"), "probe": measured.model_dump(mode="json"),
        "known_execution": known_execution, "source_asset": source_asset})
    if args.inspect_only:
        print(json.dumps({"inspect_only": True, "session_id": plan.session_id,
                          "wall_remaining": wall_remaining, "tools_remaining": tools_remaining,
                          "launch_path": str(root / (prefix_name + "-launch.json"))}))
        return 0
    stop = False
    native_renew_observed = False
    crossed_experiment = False
    reported_old_attempt = None
    forbidden_local_action = False
    def on_event(event):
        nonlocal stop, native_renew_observed, crossed_experiment, reported_old_attempt, forbidden_local_action
        if args.phase == "local-completion" and event.kind == "tool":
            raw_item = event.raw.get("item", {}) if isinstance(event.raw, dict) else {}
            action = raw_item.get("arguments", {}).get("action")
            if (event.tool_name in {"research_candidate", "approve_candidate", "apply_candidate", "inherit_experience"}
                    or event.tool_name == "research_experiment" and action != "result"):
                forbidden_local_action = True
                stop = True
        if not interrupting:
            return
        if event.reported_attempt is not None:
            reported_old_attempt = event.reported_attempt.model_dump(mode="json")
        if event.tool_name == "research_experiment":
            crossed_experiment = True
            stop = True
        if event.kind == "tool_result" and event.tool_name == "lease_task":
            audit = ledger.audit(limit=100)
            if any(r["event"] == "execution_unconfirmed" for r in audit):
                crossed_experiment = True
                stop = True
            if any(r["event"] == "renewed" and r["task_id"] == "author" for r in audit):
                native_renew_observed = True
                stop = True
    key_name = config.experiment_backend["api_key_env"]
    if key_name in os.environ:
        raise RuntimeError("operator must own its private key environment variable")
    os.environ[key_name] = args.key_file.read_text(encoding="utf-8").strip()
    started = time.monotonic()
    try:
        outcome = run_headless(plan, evidence, timeout_seconds=wall_remaining,
            max_tool_calls=tools_remaining, stop_requested=lambda: stop, on_event=on_event)
    finally:
        os.environ.pop(key_name, None)
    wall = time.monotonic() - started
    task = ledger.get(role)
    audit = ledger.audit(limit=10000)
    write(root / (args.phase + "-ledger-audit.json"), audit)
    record = {"phase": args.phase, "role": role, "wall_seconds": wall,
        "outcome": outcome.model_dump(mode="json"), "held_task": task.model_dump(mode="json"),
        "old_attempt": reported_old_attempt, "forbidden_local_action": forbidden_local_action,
        "interruption_observed": interrupting and native_renew_observed and not crossed_experiment
            and reported_old_attempt is not None
            and outcome.reason == "cancelled; usage and remote effect may be unknown" and outcome.exit_code is not None
            and outcome.exit_code != 0 and not any(r["event"] == "execution_unconfirmed" for r in audit)}
    write(observation, record)
    print(json.dumps({"phase": args.phase, "role": role, "wall_seconds": wall,
        "native": outcome.model_dump(mode="json"), "task_status": task.status,
        "actual_interruption": record["interruption_observed"]}))
    if interrupting:
        return 0 if record["interruption_observed"] else 1
    return 0 if outcome.state == "completed" and task.status == "completed" and not forbidden_local_action else 1


if __name__ == "__main__":
    raise SystemExit(main())
