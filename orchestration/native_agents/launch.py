"""Typed native CLI argv. Tools, auth, and tool loop belong to the official CLI."""

import json
from pathlib import Path

from orchestration.native_agents.models import HostBinding, LaunchPlan, LaunchRequest
from orchestration.native_agents.registry import REGISTRY, resolve_executable


def build_launch(request: LaunchRequest, *, claude_mcp_path: Path | None = None) -> LaunchPlan:
    command = resolve_executable(REGISTRY[request.runtime])
    argv = list(command)
    headless = request.mode == "headless"
    config: dict[str, object] | None = None
    binding: HostBinding | None = None
    if request.mcp and request.mcp.args[:2] == ("-m", "swarm.research"):
        if len(request.mcp.args) != 4 or request.mcp.args[2] != "--config":
            raise ValueError("research MCP requires its exact trusted --config launch contract")
        config_path = Path(request.mcp.args[3])
        if not config_path.is_absolute():
            raise ValueError("research host config path must be absolute")
        host = json.loads(config_path.read_text(encoding="utf-8"))
        if Path(host["workspace"]).resolve() != request.workspace.resolve():
            raise ValueError("research MCP config workspace differs from native CLI workspace")
        binding = HostBinding(agent=host["agent"], worker_id=host["worker_id"],
                              swarm_id=host["swarm_id"], config_path=config_path)
    if request.runtime == "codex":
        # resume has a narrower flag surface than exec. Global overrides work in both.
        if request.sandbox:
            argv += ["-c", f"sandbox_mode={json.dumps(request.sandbox)}"]
        if request.mcp:
            for name, value in (("command", request.mcp.command), ("args", request.mcp.args)):
                argv += ["-c", f"mcp_servers.morph_research.{name}={json.dumps(value, ensure_ascii=False)}"]
            if request.mcp.env:
                values = ", ".join(f"{json.dumps(k)} = {json.dumps(v)}" for k, v in request.mcp.env.items())
                argv += ["-c", "mcp_servers.morph_research.env={" + values + "}"]
        if request.model:
            argv += ["--model", request.model]
        if headless:
            argv += ["exec"]
            if request.session_id:
                argv += ["resume", request.session_id]
            argv += ["--json", "--skip-git-repo-check", "-"]
        else:
            # Do not use or own the user's shared app-server daemon.
            argv += ["--no-daemon", "--cd", str(request.workspace)]
            if request.session_id:
                argv += ["resume", request.session_id]
            argv += ["--", request.prompt]
    else:
        if request.mcp:
            if claude_mcp_path is None or not claude_mcp_path.is_absolute():
                raise ValueError("Claude MCP requires an independent absolute config file path")
            config = {"mcpServers": {"morph_research": {"type": "stdio", "command": request.mcp.command,
                       "args": list(request.mcp.args), "env": request.mcp.env}}}
            argv += ["--mcp-config", str(claude_mcp_path)]
        if request.model:
            argv += ["--model", request.model]
        if request.permission_mode:
            argv += ["--permission-mode", request.permission_mode]
        if request.allowed_tools:
            argv += ["--allowedTools", ",".join(request.allowed_tools)]
        if request.session_id:
            argv += ["--resume", request.session_id]
        if headless:
            argv += ["--print", "--output-format", "stream-json", "--verbose"]
            if request.max_budget_usd:
                argv += ["--max-budget-usd", str(request.max_budget_usd)]
        else:
            argv += ["--", request.prompt]
    return LaunchPlan(runtime=request.runtime, mode=request.mode, argv=tuple(argv),
                      workspace=request.workspace, stdin_text=request.prompt if headless else None,
                      mcp_config=config, session_id=request.session_id, host_binding=binding)


def write_mcp_config(plan: LaunchPlan, path: Path) -> None:
    """Exclusive local file creation; never edit an existing user config."""
    if plan.mcp_config is None:
        return
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(plan.mcp_config, stream, ensure_ascii=False, indent=2)
