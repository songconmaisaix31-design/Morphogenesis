# D ORCA 全 Agent 接口轨（1001）

本阶段仅接口盘点交付；同Owner后续续接实现。worktree `C:/Users/DW/orca/workspaces/Morphogenesis/morph-agent-protocols-1001`，branch `songconmaisaix31-design/morph-agent-protocols-1001`，基线 `c45888f64c1cec60e5f9df45677b6547c4527cac`，授权写入仅本报告和 [接口矩阵](../agents/ORCA_PROTOCOL_MATRIX_1001.md)。

## 完成

- 已读 AGENTS、docs/PLAN、事实源目录说明及主控 `morph-research-plan-1001/docs/RESEARCH_NEXT_PLAN_1001.md`；遵守当前只读源码研究、文档、commit/push阶段边界。
- 小Handoff `msg_9757ab2e4cb7` 先交核心 LaunchRequest/build_launch/run_headless/interactive/AttachedSession/MCP 复用清单；未先实现41种不存在的核心适配。
- 固定 ORCA 85f8d6：43族 TUI、20族 resume、13族 headless文本preset、独立headless模式识别、19族managed installer/24种hook来源；结构化创建只Claude/Codex，transcript解析另OpenClaude/Grok/OMP。矩阵逐族给launch、输入、headless、resume、events、permissions及usage位置，完整共同边界覆盖SDK/stdio/MCP/attach/cancel/streams/token-cost/error/auth/file scope，不支持/未知显式保留。
- 给P的映射精确到基线核心 Python 文件行：复用既有数据模型、官方CLI argv、FastMCP、host绑定、事件/原始证据、unknown用量与效果、owned/attached进程边界；产品权限/角色参数归P，进程修复归A。
- 收到主控 `msg_a1cdc669aaa7` 的urgent exact11问题后，只读固定Codex 0.159.0官方源与原checker，通过 `msg_e5d6b19309d3` 回传主控转P：server工具白名单/实际调用集合与完整模型目录exact11不同，当前公开CLI/TS SDK无全目录白名单证据；Rust嵌入ToolPolicy是不同入口，不能冒称现有Python能力。
- 审阅B公开薄Handoff `docs/tracks/research-space-1001.md`（读取时B HEAD `a060564dee6d7fa790b64583fd76301e95eadb54`），确认正式入口/三角色原checker/旧红保留的交接边界；未共写B/P文件。

## 本轮验证

| 命令 / 检查 | 结果 |
|---|---|
| `git rev-parse HEAD`、`git status --short --branch`（开工） | exact c45888；clean，分支匹配 |
| `orca skills get orca-cli`、`orca --version`、`orca status --json` | 指南已读；1.4.212 / ready，只读发现 |
| `Invoke-RestMethod https://api.github.com/repos/stablyai/orca/git/trees/85f8d6b5f507df795cd3cef1cdea08124cf801ee?recursive=1` + 对22个已有ORCA文件逐一 `git hash-object --no-filters -- <path>` 比较官方blob | tree SHA精确；22/22匹配，无字节差异 |
| `git diff --no-index -- <A/.reference/LICENSE> orchestration/native_agents/ORCA_LICENSE.txt` | exit0；许可相同，Git既有LF/CRLF提示保留 |
| 只读官方固定raw源码 / 本机 npm package.json / `node --version` | ORCA源码1.4.214、Claude JS SDK依赖0.3.251；本机Codex0.159.0/Claude2.1.238/Node24.16.0；未认证/调用/安装 |
| `node --input-type=module -` 标准库只读覆盖/引用检查；Git基线diff检查 | 43/43注册条目和C引用块匹配；20 resume/19 managed hook；73处headless/events/permissions官方范围及族名匹配；ToolPolicy行界有效；只有两授权文档变更，native/research/原checker diff为空；两个检查exit0 |
| `git diff --check`、`git diff --cached --check`、commit/push/`git ls-remote`/clean | exit0；盘点提交 `5a7b945eda2d3ceca816aa7b88871dfd95e756ea` 已push，ls-remote精确相同，status --porcelain空；相对c458只两授权文档。此收口记录另作文档提交，其完整SHA/remote/clean由最终Handoff回传 |

源码检索的真实失败保留：D worktree的`.reference`和A的`.runtime`不存在；`C:/Users/DW/orca/Agent-Graph`无可解析HEAD，不把它当指定上游；web页面抓取cache miss后改读固定官方raw/tree；推测的`claude-agent-sdk-connection.ts`、`codex-structured-turns.ts`为404，后按官方tree找到stream-json/cancellation真实文件；大JSON输出截断/HTTP错误混入stdout分别导致解析失败，随后缩小到必要schema/源码行并按真实tree定位。以上均未修改上游/业务/账号，也不是模型调用或工程门禁失败。

## 真实限制与未执行

没有新增Agent接入、生产启动/解析代码、依赖/全局配置修改、登录/模型/Hub/沙箱/live调用。未运行native probe（含auth步骤）、上游Electron/Vitest、全量pytest/build或完整科研checker；本轮文档验证不能替代这些门禁。

41族核心运行时尚未实现；19种installer/24种hook只是源码能力，未证明本机已安装。Agent提供方许可、真实auth、SDK/stdio/MCP/file-scope未知项需后续官方证据/授权实测，不能猜统一接口；成本未知保持null。公开Codex完整模型目录exact11要求尚未满足支持证据，原checker字节/断言保持，不自行改验收定义。

实现放行必须按主控原序：A进程清理与P正式安装入口 → 冻结三角色原完整checker真实通过 → NIST抽离与第二类任务通过 → 本D同Owner获新增native路径后实现。Claude认证身份由用户/主控决定，旧401/过期案例/第三NOT_RUN保留；EvoMap后置。无需主控阅读transcript或搬入ORCA桌面。

## 接续只读诊断（case02，非 live 验收）

本次从 clean `8530b1bb8df1c8f5272ff19e8b731c6eea62289a` 接续。固定 Codex rust-v0.159.0 官方 commit `687a119f0fcaace47e1f1abcc77cec6c813fd6da` / Apache-2.0；仅这两文档可写。官方 fail-closed/router、模型 metadata 优先级、DirectModelOnly 完整暴露链和最小候选详见 [矩阵 case02 节](../agents/ORCA_PROTOCOL_MATRIX_1001.md#case02-只读诊断code-mode-与直接-mcp-候选)。

- 小 Handoff `msg_e4734973e5e9` 先给根主控；完整固定来源与 effect/checker 限制分别给 P `msg_2c0fda02b176`、I `msg_5fc700aee148`、root `msg_c2a9577e6fc2`。P 独占 guard/error 分类及产品权限返修；D 不共写、不新增运行时。
- 根因解释：模型的 CodeModeOnly 可覆盖 feature=false，host=false 继续 fail closed；当前 model/cache 的选择性读取支持这一路径，但不是 case02 实际请求 metadata 的证明。服务器 omit deferred/code_mode 可把原11变为 DirectModelOnly，无需开启 host；provider/真实模型接受或选择仍 NOT_RUN。全目录 exact11 未满足，原实际调用11/权限/完整 checker 均不改。
- 实际 case02 已有模型响应；0研究工具、未认领/实验不等于无模型外部效果。原 raw/error、cancelled、unknown/null 与完整 checker RED 保留；当前诊断不能代签科研通过。metadata 实际调用名没有 raw 证据，保持 unknown。

| 本次验证 | 结果 |
|---|---|
| `git rev-parse HEAD` / `git status --porcelain` 开工、只读官方 GitHub commit tree/raw | clean 8530b1b；tree exact 687a119、非截断；只读文件行判断链已引用，不运行官方 mock 测试 |
| Node 标准库 Git blob SHA1 比较既有 P 官方 copy | `codex-repair-source/codex-rs_config_src_mcp_types.rs` = `4b627edc7769cdbe3c20e8903bb06234b9f6f8b5`；`codex-rs_core_src_config_mod.rs` = `571fc2d81b51d77f34084f28b296ebd1931b31e2`；2/2 与官方固定 tree 匹配 |
| 只读 forensics / 原 checker / 本机顶层 model 与该条 cache 字段 | 仅打印非秘密选定字段；bound error 项为 unknown/null；checker 原断言保留；未读取 auth、dump provider/全模型配置，未做模型请求 |
| `git diff --check` / Node 标准库 ownership、源码引用范围及关键判断链检查 | exit0；仅两授权文档；固定13个官方文件 HTTP200、20/20引用行界有效、3/3关键判断锚点匹配；无产品/核心/锁/原 checker 变更 |
| commit+push / `git ls-remote` / clean | 本次提交完整 SHA、remote exact 和 clean 收口结果在最终 Handoff 回传 |

本次检索的真实限制保留：P 官方副本为扁平文件而非完整 clone，初始目录模式检索无匹配；大范围源码输出截断后收缩为必要行；推测的 `tools/src/registry.rs`、`codex-mcp/src/mcp.rs` 返回404，按真实源码转用 tool_executor.rs/tools.rs。未据失败伪造接口，没有落盘新的官方源副本、修改全局配置或安装依赖。所有 modelrequest/auth/API/sandbox/session/烟测/live 诊断 NOT_RUN；NIST抽离、第二类任务及更多Agent仍须原三角色完整 checker 通过后再放行，EvoMap后置。
