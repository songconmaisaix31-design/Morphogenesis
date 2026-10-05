/**
 * WindFinder — 项目自带的只读导航 agent（框架 Pi）。
 *
 * default 导出工厂：
 *   1. 注入 WindFinder system prompt（读 prompt.ts）
 *   2. 注册只读边界守卫（guard.ts）
 *   3. 注册 CLI 入口清单工具（cli.ts）
 *   4. 注册 swarm.research MCP（config 路径来自 WINDFINDER_HOST_CONFIG，缺失仅告警不崩溃）
 */
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { registerCliTool } from "./cli";
import { registerGuard } from "./guard";
import { WINDFINDER_PROMPT } from "./prompt";
import { HOST_CONFIG_ENV, MCP_SERVER_NAME } from "./research";

const WINDFINDER_SECTION = "windfinder";

export default function (pi: ExtensionAPI) {
  pi.on("before_agent_start", (event) => {
    event.systemPromptOptions.sections[WINDFINDER_SECTION] = WINDFINDER_PROMPT;
  });

  registerGuard(pi);
  registerCliTool(pi);

  const hostConfig = process.env[HOST_CONFIG_ENV];
  if (!hostConfig) {
    console.warn(
      `[windfinder] 环境变量 ${HOST_CONFIG_ENV} 未设置，跳过 swarm.research MCP 注册（只读导航不可用，不崩溃）。`,
    );
    return;
  }

  pi.registerMcpServer(MCP_SERVER_NAME, {
    command: "python",
    args: ["-m", "swarm.research", "--config", hostConfig],
    exposure: "direct",
    description:
      "Morphogenesis 研究蜂群只读导航（写工具由 WindFinder 只读边界拦截，reason=windfinder_readonly_boundary）。",
  });
}
