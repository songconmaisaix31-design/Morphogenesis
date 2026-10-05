/**
 * WindFinder 只读边界守卫。
 *
 * 通过 `pi.on("tool_call")` 拦截所有工具调用：只放行 research MCP 的
 * READONLY_TOOLS，其余研究 MCP 工具（propose_research_work、accept_result、
 * lease_task、research_experiment(action=request/run/artifact)、
 * research_project(action=create/export)、apply_candidate、
 * record_research_correction 等）一律返回 { block: true, reason }。
 *
 * 非研究 MCP 工具（内置工具、WindFinder 自身工具、其它 MCP）不受影响。
 */
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { BLOCK_REASON, MCP_TOOL_PREFIX, READONLY_TOOLS } from "./research";

function readAction(input: unknown): string | undefined {
  if (input === null || typeof input !== "object") return undefined;
  const value = (input as Record<string, unknown>).action;
  return typeof value === "string" ? value : undefined;
}

function isResearchTool(toolName: string): boolean {
  return toolName.startsWith(MCP_TOOL_PREFIX);
}

function bareToolName(toolName: string): string {
  return toolName.slice(MCP_TOOL_PREFIX.length);
}

export function registerGuard(pi: ExtensionAPI): void {
  pi.on("tool_call", (event) => {
    if (!isResearchTool(event.toolName)) {
      return undefined;
    }

    const name = bareToolName(event.toolName);
    const entry = READONLY_TOOLS.find((item) => item.name === name);
    if (!entry) {
      return { block: true, reason: BLOCK_REASON };
    }

    if (entry.actions) {
      const action = readAction(event.input);
      if (!action || !entry.actions.includes(action)) {
        return { block: true, reason: BLOCK_REASON };
      }
    }

    return undefined;
  });
}
