"""Native CLI data contracts; no task selection or dispatch lifecycle."""

from pathlib import Path
from typing import Literal, Self
from uuid import UUID

from pydantic import Field, model_validator

from contracts.base import Contract
from contracts.identity import AgentId, AttemptId
from contracts.provenance import Acceptance, Provenance
from contracts.results import Usage

RuntimeId = Literal["codex", "claude"]
Mode = Literal["headless", "interactive"]


class Capability(Contract):
    supported: bool | None = None
    validated: Literal["contract_local", "probe", "interface_live", "not_run"] = "not_run"
    detail: str


class RuntimeSpec(Contract):
    runtime: RuntimeId
    executable: str
    npm_package: str
    expected_version: str
    connection: Literal["native_cli"] = "native_cli"
    version_args: tuple[str, ...] = ("--version",)
    auth_args: tuple[str, ...]
    capabilities: dict[str, Capability]


class McpStdio(Contract):
    """Trusted host input, not values accepted from a model tool call."""

    command: str = Field(min_length=1)
    args: tuple[str, ...] = ()
    env: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def safe_command(self) -> Self:
        if Path(self.command).suffix.lower() in {".cmd", ".bat", ".ps1"}:
            raise ValueError("MCP command must be a native executable, not a shell shim")
        protected = {"HOME", "USERPROFILE", "CODEX_HOME", "CLAUDE_CONFIG_DIR"}
        if any(key.upper() in protected or key.upper().startswith("ORCA_") for key in self.env):
            raise ValueError("MCP environment cannot replace native auth homes or Orca authority")
        return self


class LaunchRequest(Contract):
    runtime: RuntimeId
    workspace: Path
    prompt: str = Field(min_length=1, max_length=131072)
    mode: Mode = "headless"
    session_id: str | None = None
    mcp: McpStdio | None = None
    model: str | None = None
    # Native permissions are inherited unless the trusted caller explicitly selects one.
    sandbox: Literal["read-only", "workspace-write"] | None = None
    permission_mode: Literal["manual", "dontAsk", "plan", "acceptEdits"] | None = None
    allowed_tools: tuple[str, ...] = ()
    max_budget_usd: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_request(self) -> Self:
        if not self.workspace.is_absolute() or not self.workspace.is_dir():
            raise ValueError("workspace must be an existing absolute directory")
        if self.session_id is not None:
            UUID(self.session_id)  # Exact native identity; never --last or an invented id.
        if self.runtime == "codex" and (
            self.permission_mode is not None or self.allowed_tools or self.max_budget_usd is not None
        ):
            raise ValueError("Claude-only permission/tool/budget option requested for Codex")
        if self.runtime == "claude" and self.sandbox is not None:
            raise ValueError("Codex-only sandbox requested for Claude")
        if self.mode == "interactive" and self.max_budget_usd is not None:
            raise ValueError("Claude budget flag is headless-only")
        return self


class HostBinding(Contract):
    """Existing ledger identity read from the trusted MCP host config."""

    agent: AgentId
    worker_id: str = Field(min_length=1)
    swarm_id: str = Field(min_length=1)
    config_path: Path


class LaunchPlan(Contract):
    runtime: RuntimeId
    mode: Mode
    argv: tuple[str, ...]
    workspace: Path
    stdin_text: str | None
    mcp_config: dict[str, object] | None = None
    session_id: str | None = None
    host_binding: HostBinding | None = None


class NativeEvent(Contract):
    runtime: RuntimeId
    kind: Literal["session", "turn", "tool", "tool_result", "message", "result", "error", "unknown"]
    native_type: str | None = None
    session_id: str | None = None
    tool_id: str | None = None
    tool_name: str | None = None
    reported_attempt: AttemptId | None = None
    terminal: Literal["completed", "failed"] | None = None
    usage: Usage = Field(default_factory=Usage)
    raw: object


class NativeOutcome(Contract):
    runtime: RuntimeId
    session_id: str | None = None
    exit_code: int | None = None
    state: Literal["completed", "failed", "unknown"] = "unknown"
    remote_effect: Literal["unknown"] = "unknown"
    usage: Usage = Field(default_factory=Usage)
    observed_tool_calls: int = 0
    reason: str | None = None
    provenance: Provenance
    acceptance: Acceptance


class ResearchBootstrap(Contract):
    space: str = Field(min_length=1)
    agent: AgentId
    objective: str = Field(min_length=1)
    tool_names: tuple[str, ...]
    rules: tuple[str, ...] = ()

    def prompt(self) -> str:
        return (
            f"Research space: {self.space}\nRole: {self.agent.role}; instance: {self.agent.instance}\n"
            f"Objective: {self.objective}\nResearch MCP tools: {', '.join(self.tool_names)}\n"
            "Discover eligible work using the shared research tools, then choose and claim work yourself. "
            "Respect the host-bound identity and scopes; renew your lease and stop on stale fencing. "
            "Read shared evidence and experience before acting; record actual experiments, conditions, "
            "negative results and independent reproduction. Only record adoption after actual use. "
            "Keep infrastructure failures separate from scientific negative results. Never replay an "
            "unknown external effect; unknown exit, usage and cost remain unknown. "
            "Use native tools and permissions; do not change authentication or kill attached sessions. "
            "Do not spawn additional research agents. This product does not use Orca.\n"
            + "\n".join(self.rules)
        )
