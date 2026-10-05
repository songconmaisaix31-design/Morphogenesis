/**
 * WindFinder research 只读白名单与常量。
 *
 * READONLY_TOOLS 是研究 MCP 的只读工具白名单；带 `actions` 的条目表示仅当
 * 该工具的 `action` 参数落在白名单值内时才视为只读。其余全部视为写工具，
 * 由 guard.ts 统一拦截（reason=windfinder_readonly_boundary）。
 */

/** 注册到 Pi 的 MCP server 名（仅允许 `[A-Za-z0-9_-]`，不能含 `.`）。 */
export const MCP_SERVER_NAME = "swarm_research";

/** Pi 生成的 MCP 工具名前缀：`mcp__<server>__<tool>`。 */
export const MCP_TOOL_PREFIX = "mcp__swarm_research__";

/** 只读边界拦截原因（guard 与 prompt 保持一致）。 */
export const BLOCK_REASON = "windfinder_readonly_boundary";

/** 环境变量：宿主研究配置的绝对路径（缺失时只告警、不崩溃）。 */
export const HOST_CONFIG_ENV = "WINDFINDER_HOST_CONFIG";

export interface ReadonlyToolEntry {
  /** 研究 MCP 的裸工具名（去掉 `mcp__swarm_research__` 前缀）。 */
  name: string;
  /** 仅当设置时，工具 `action` 参数必须落在这些值内才放行。 */
  actions?: readonly string[];
}

/** 只读白名单（7 项）。 */
export const READONLY_TOOLS: readonly ReadonlyToolEntry[] = [
  { name: "discover_tasks" },
  { name: "project_context" },
  { name: "search_evidence" },
  { name: "research_experiment", actions: ["result"] },
  { name: "research_project", actions: ["read"] },
  { name: "research_advisory" },
  { name: "research_snapshot" },
];

/** 由白名单推导出的裸工具名集合（不含 action 约束，仅用于快速判定）。 */
export const READONLY_TOOL_NAMES: ReadonlySet<string> = new Set(
  READONLY_TOOLS.map((entry) => entry.name),
);
