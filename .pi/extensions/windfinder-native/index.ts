import { spawnSync } from "node:child_process";
import { Type } from "typebox";
import { defineTool, type ExtensionAPI } from "@earendil-works/pi-coding-agent";

type Runtime = "codex" | "claude";
type Mode = "headless" | "interactive";

interface CmdResult {
  code: number | null;
  stdout: string;
  stderr: string;
  error: string | null;
}

interface AgentStatus {
  installed: boolean;
  version: string | null;
  authenticated: boolean | null;
  reason: string | null;
}

interface ProbeDetails {
  codex: AgentStatus;
  claude: AgentStatus;
}

interface LaunchDetails {
  runtime: Runtime;
  mode: Mode;
  launched: false;
  argv: string[];
  stdin_text: string | null;
  workspace: string;
  mcp_config_path: string | null;
  preconditions: string[];
}

function childEnvironment(): NodeJS.ProcessEnv {
  const env: NodeJS.ProcessEnv = {};
  for (const [key, value] of Object.entries(process.env)) {
    if (value === undefined || key.toUpperCase().startsWith("ORCA_")) continue;
    env[key] = value;
  }
  return env;
}

function runCommand(command: string, args: string[]): CmdResult {
  try {
    const result = spawnSync(command, args, {
      shell: process.platform === "win32",
      encoding: "utf8",
      timeout: 15_000,
      windowsHide: true,
      env: childEnvironment(),
    });
    if (result.error) {
      return { code: null, stdout: "", stderr: "", error: result.error.code ?? result.error.name };
    }
    return {
      code: result.status,
      stdout: typeof result.stdout === "string" ? result.stdout : "",
      stderr: typeof result.stderr === "string" ? result.stderr : "",
      error: null,
    };
  } catch (err) {
    return { code: null, stdout: "", stderr: "", error: err instanceof Error ? err.name : "unknown" };
  }
}

function parseVersion(text: string): string | null {
  const match = text.match(/(?:^|\s)(\d+\.\d+\.\d+(?:[-+][^\s]+)?)(?:\s|$)/);
  return match ? match[1] : null;
}

function parseCodexAuth(result: CmdResult): boolean | null {
  const text = result.stdout + result.stderr;
  if (result.code === 0 && text.includes("Logged in using")) return true;
  if (text.includes("Not logged in")) return false;
  return null;
}

function parseClaudeAuth(result: CmdResult): boolean | null {
  if (result.code !== 0 && result.code !== 1) return null;
  try {
    const value = JSON.parse(result.stdout).loggedIn;
    return typeof value === "boolean" ? value : null;
  } catch {
    return null;
  }
}

function probeAgent(runtime: Runtime): AgentStatus {
  const authArgs = runtime === "codex" ? ["login", "status"] : ["auth", "status"];
  const versionResult = runCommand(runtime, ["--version"]);
  if (versionResult.code !== 0) {
    return { installed: false, version: null, authenticated: null, reason: versionResult.error ?? "not installed" };
  }
  const version = parseVersion(`${versionResult.stdout}\n${versionResult.stderr}`);
  const authResult = runCommand(runtime, authArgs);
  const authenticated = runtime === "codex" ? parseCodexAuth(authResult) : parseClaudeAuth(authResult);
  return {
    installed: true,
    version,
    authenticated,
    reason: version ? null : "version not recognized",
  };
}

const ProbeParams = Type.Object({
  runtime: Type.Optional(Type.Union([Type.Literal("codex"), Type.Literal("claude")])),
});

const probeTool = defineTool({
  name: "probe_native_agents",
  label: "Probe native agents",
  description:
    "Probe the local codex (@openai/codex) and claude (@anthropic-ai/claude-code) CLIs: installed, version, and authentication status. Read-only; runs only --version and login/auth status checks and never launches a session.",
  parameters: ProbeParams,
  annotations: { readOnlyHint: true, destructiveHint: false, openWorldHint: false },

  async execute(_toolCallId, params, _signal, _onUpdate) {
    const runtimes: Runtime[] = params.runtime ? [params.runtime] : ["codex", "claude"];
    const details: ProbeDetails = {
      codex: { installed: false, version: null, authenticated: null, reason: "not probed" },
      claude: { installed: false, version: null, authenticated: null, reason: "not probed" },
    };
    for (const runtime of runtimes) {
      details[runtime] = probeAgent(runtime);
    }
    const lines: string[] = [];
    for (const name of ["codex", "claude"] as const) {
      const status = details[name];
      if (status.reason === "not probed") {
        lines.push(`${name}: not probed`);
        continue;
      }
      const version = status.version ? ` v${status.version}` : "";
      const auth =
        status.authenticated === null
          ? "auth unknown"
          : status.authenticated
            ? "authenticated"
            : "not authenticated";
      const reason = status.reason ? ` (${status.reason})` : "";
      lines.push(`${name}: ${status.installed ? `installed${version}, ${auth}` : "not installed"}${reason}`);
    }
    return {
      content: [{ type: "text", text: lines.join("\n") }],
      details,
    };
  },
});

const LaunchParams = Type.Object({
  runtime: Type.Union([Type.Literal("codex"), Type.Literal("claude")]),
  mode: Type.Union([Type.Literal("headless"), Type.Literal("interactive")]),
  prompt: Type.Optional(
    Type.String({
      description: "One text prompt; passed via stdin in headless mode, or after `--` in interactive mode",
    }),
  ),
});

function buildLaunchExample(
  runtime: Runtime,
  mode: Mode,
  prompt?: string,
): Omit<LaunchDetails, "runtime" | "mode" | "launched"> {
  if (runtime === "codex") {
    if (mode === "headless") {
      return {
        argv: ["codex", "exec", "--json", "--skip-git-repo-check", "-"],
        stdin_text: prompt ?? null,
        workspace: "<workspace>",
        mcp_config_path: null,
        preconditions: [
          "workspace: absolute existing directory provided by the host (used as current working directory)",
          "mcp --config: host-provided research MCP, injected as -c mcp_servers.morph_research.command=... and -c mcp_servers.morph_research.args=[...]",
        ],
      };
    }
    return {
      argv: ["codex", "--no-daemon", "--cd", "<workspace>", "--", prompt ?? ""],
      stdin_text: null,
      workspace: "<workspace>",
      mcp_config_path: null,
      preconditions: ["workspace: absolute existing directory provided by the host (replaces <workspace>)"],
    };
  }
  if (mode === "headless") {
    return {
      argv: ["claude", "--print", "--output-format", "stream-json", "--verbose"],
      stdin_text: prompt ?? null,
      workspace: "<workspace>",
      mcp_config_path: "<mcp-config.json>",
      preconditions: [
        "workspace: absolute existing directory provided by the host (used as current working directory)",
        "mcp --config: host-provided independent absolute config file path (--mcp-config <mcp-config.json>)",
      ],
    };
  }
  return {
    argv: ["claude", "--", prompt ?? ""],
    stdin_text: null,
    workspace: "<workspace>",
    mcp_config_path: "<mcp-config.json>",
    preconditions: [
      "workspace: absolute existing directory provided by the host (used as current working directory)",
      "mcp --config: host-provided independent absolute config file path (--mcp-config <mcp-config.json>)",
    ],
  };
}

const launchTool = defineTool({
  name: "native_agent_launch",
  label: "Native agent launch",
  description:
    "Return an example launch argv for a native codex or claude agent plus its preconditions. The workspace and mcp --config are supplied by the host. Does not start any process.",
  parameters: LaunchParams,
  annotations: { readOnlyHint: true, destructiveHint: false, openWorldHint: false },

  async execute(_toolCallId, params, _signal, _onUpdate) {
    const example = buildLaunchExample(params.runtime, params.mode, params.prompt);
    const details: LaunchDetails = { runtime: params.runtime, mode: params.mode, launched: false, ...example };
    const preconditions = details.preconditions.map((line) => `- ${line}`).join("\n");
    return {
      content: [
        {
          type: "text",
          text: `${params.runtime} ${params.mode} example argv (not launched):\n  ${details.argv.join(" ")}\nPreconditions:\n${preconditions}`,
        },
      ],
      details,
    };
  },
});

export default function (pi: ExtensionAPI) {
  pi.registerTool(probeTool);
  pi.registerTool(launchTool);
}
