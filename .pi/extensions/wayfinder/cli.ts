/**
 * Wayfinder CLI 入口清单工具。
 *
 * 注册 `list_cli_entries`：返回项目 CLI 入口清单（用途 + 是否可执行）。
 * 可执行仅限安全只读命令（git status/log/diff、ls、查看日志）；
 * 模型调用 / 部署 / 安装 / bootstrap / 编排类入口一律标记「仅导航不执行」。
 */
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";

export interface CliEntry {
  /** 命令 / 入口名。 */
  entry: string;
  /** 用途。 */
  purpose: string;
  /** 是否可由 Wayfinder 执行（仅限安全只读命令）。 */
  executable: boolean;
  /** 补充说明（只读可执行 / 仅导航不执行原因）。 */
  note: string;
}

const CLI_ENTRIES: readonly CliEntry[] = [
  {
    entry: "python -m swarm.research --config <ABS>",
    purpose: "研究 MCP stdio（由 Wayfinder 注册为 MCP server）",
    executable: false,
    note: "仅导航不执行：写工具被只读边界拦截，只经 MCP 调用只读工具",
  },
  {
    entry: "morphogenesis",
    purpose: "bootstrap / swarm 编排入口",
    executable: false,
    note: "仅导航不执行：写入账本、租约、候选",
  },
  {
    entry: "morphogenesis-swarm",
    purpose: "swarm 编排入口",
    executable: false,
    note: "仅导航不执行：写入账本、租约、候选",
  },
  {
    entry: "bl",
    purpose: "阿里云百炼模型 CLI",
    executable: false,
    note: "仅导航不执行：模型调用与外部副作用",
  },
  {
    entry: "pi",
    purpose: "Pi agent 框架（Wayfinder 自身宿主）",
    executable: false,
    note: "仅导航不执行：自身即 Pi",
  },
  {
    entry: "kimi",
    purpose: "kimi agent 模型调用入口",
    executable: false,
    note: "仅导航不执行：模型调用入口",
  },
];

const READONLY_EXECUTABLE_COMMANDS: readonly CliEntry[] = [
  { entry: "git status", purpose: "查看工作区状态", executable: true, note: "只读可执行" },
  { entry: "git log [--oneline]", purpose: "查看提交历史", executable: true, note: "只读可执行" },
  { entry: "git diff", purpose: "查看未提交差异", executable: true, note: "只读可执行" },
  { entry: "ls / Get-ChildItem", purpose: "列出目录内容", executable: true, note: "只读可执行" },
  {
    entry: "Get-Content <log> -Tail 200 / tail -n 200 <log>",
    purpose: "查看日志尾部",
    executable: true,
    note: "只读可执行",
  },
];

function renderEntry(entry: CliEntry): string {
  const mark = entry.executable ? "可执行（只读）" : "仅导航，不执行";
  return `- ${entry.entry} — ${entry.purpose} — ${mark}（${entry.note}）`;
}

function renderCliEntries(): string {
  const navigate = CLI_ENTRIES.map(renderEntry).join("\n");
  const readonly = READONLY_EXECUTABLE_COMMANDS.map(renderEntry).join("\n");
  return [
    "# 项目 CLI 入口与白名单",
    "",
    "## 仅导航，不执行",
    navigate,
    "",
    "## 只读可执行白名单（仅限安全只读命令）",
    readonly,
    "",
    "模型调用 / 部署 / 安装 / bootstrap / 编排类入口：Wayfinder 只说明用途与用法，不代执行。",
    "需要真正执行写操作时，请宿主授权对应的 Worker / 原生 Agent。",
  ].join("\n");
}

export function registerCliTool(pi: ExtensionAPI): void {
  pi.registerTool({
    name: "list_cli_entries",
    label: "Wayfinder CLI 入口清单",
    description:
      "返回项目 CLI 入口清单（python -m swarm.research / morphogenesis / morphogenesis-swarm / bl / pi / kimi）" +
      "及其用途与是否可执行。可执行仅限安全只读命令（git status/log/diff、ls、查看日志）；" +
      "模型调用 / 部署 / 安装 / bootstrap / 编排类入口标记为「仅导航不执行」。",
    parameters: Type.Object({}),
    annotations: { readOnlyHint: true },
    async execute() {
      return {
        content: [{ type: "text", text: renderCliEntries() }],
        details: {
          cli_entries: CLI_ENTRIES,
          readonly_executable: READONLY_EXECUTABLE_COMMANDS,
        },
      };
    },
  });
}
