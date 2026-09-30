"""Explicit host observations using A's native loop and B's existing ledger.

Each invocation requires an explicit phase. This does not select tasks, execute
experiments, approve assets, write the ledger, or retry a failed invocation.
"""
import argparse
import json
import os
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
    parser.add_argument("--phase", choices=("interrupt", "resume", "replication", "inheritance"), required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--key-file", type=Path, required=True)
    args = parser.parse_args()
    root = args.state.resolve(strict=True)
    role = "author" if args.phase in {"interrupt", "resume"} else args.phase
    runtime = "claude" if role == "replication" else "codex"
    config_path = root / (role + "-host.json")
    config = HostConfig.model_validate_json(config_path.read_bytes())
    ledger = TaskLedger(config.ledger_path, config.swarm_id)
    observation = root / (args.phase + "-observation.json")
    evidence = root / (args.phase + "-native")
    if observation.exists() or evidence.exists():
        raise RuntimeError("an invocation is never replayed")
    previous = []
    for phase in ("interrupt", "resume", "replication", "inheritance"):
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
    if args.phase == "interrupt":
        rules += [
            "INTERRUPTION PHASE: discover eligible work, choose author, read context, claim with ttl_seconds=60, then renew with ttl_seconds=30.",
            "DO NOT request/run any experiment, publish/submit candidate, verify, approve, apply, release or complete. Experiment execution is forbidden until an explicit resumed turn.",
            "After renewal, keep reading project_context until the host interrupts your owned process; do not end naturally.",
        ]
    elif args.phase == "resume":
        old = json.loads((root / "interrupt-observation.json").read_text(encoding="utf-8"))
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
    mcp_path = root / (args.phase + "-mcp.json")
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
        }
        overrides.update({f"mcp_servers.{name}.enabled": False for name in existing.get("mcp_servers", {}) if name != "morph_research"})
        prefix = []
        for key, value in overrides.items():
            prefix += ["-c", key + "=" + json.dumps(value)]
        command_length = len(measured.command)
        plan = plan.model_copy(update={"argv": plan.argv[:command_length] + tuple(prefix) + plan.argv[command_length:]})
    else:
        plan = plan.model_copy(update={"argv": plan.argv + ("--strict-mcp-config", "--tools", "", "--disable-slash-commands")})
        write_mcp_config(plan, mcp_path)
    write(root / (args.phase + "-launch.json"), {"request": request.model_dump(mode="json"), "plan": plan.model_dump(mode="json"), "probe": measured.model_dump(mode="json")})
    stop = False
    native_renew_observed = False
    crossed_experiment = False
    reported_old_attempt = None
    def on_event(event):
        nonlocal stop, native_renew_observed, crossed_experiment, reported_old_attempt
        if args.phase != "interrupt":
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
        "old_attempt": reported_old_attempt,
        "interruption_observed": args.phase == "interrupt" and native_renew_observed and not crossed_experiment
            and reported_old_attempt is not None
            and outcome.reason == "cancelled; usage and remote effect may be unknown" and outcome.exit_code is not None
            and outcome.exit_code != 0 and not any(r["event"] == "execution_unconfirmed" for r in audit)}
    write(observation, record)
    print(json.dumps({"phase": args.phase, "role": role, "wall_seconds": wall,
        "native": outcome.model_dump(mode="json"), "task_status": task.status,
        "actual_interruption": record["interruption_observed"]}))
    if args.phase == "interrupt":
        return 0 if record["interruption_observed"] else 1
    return 0 if outcome.state == "completed" and task.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
