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

## notice 语义验收返修

从 clean `450c9cc1d2554b19436c00be4aaebc8a3c6d6e32` 接续，仅补上一轮遗漏的关键结论：[矩阵 notice 节](../agents/ORCA_PROTOCOL_MATRIX_1001.md#验收返修startup-notice-不是-fatal但必须精确兼容)。官方 caller 在 requested CodeModeOnly、host unavailable、service 首次发出时生成 WarningEvent，完全不看 direct11 exposure；exec 将它及 DeprecationNotice 映射 ErrorItem/Running，真正 Error notification 为顶层 error，turn.failed 另按 TurnStatus 发。wire 无 severity，不能泛化放行 item.error；官方 notice 不等于实际 disabled exec 执行失败。

薄 Handoff 先交 root `msg_ab4a19e90e87` / P `msg_0eb9b49dac5d` / I `msg_7a2fb95f17f5`，再按 root 仅 host notice 的批准收窄并补齐 caller 至 root `msg_5688452d4b43` / P `msg_516624f91c7d` / I `msg_c6355910c248`。P 去除 memory_tool alias但 memoriesfalse 保留；弃用通知虽然官方非fatal，**不列入批准兼容名单**。D只交源码语义，不修改产品实现或原checker，不冻结签署live。

验证：10个固定官方文件 HTTP200、11/11引用行界有效，caller Warning/无exposure判断、fatal映射及完整notice与原raw逐字节匹配检查exit0，原 :1–7顺序核对通过；仅两docs ownership、`git diff --check`通过，cached检查和完整commit、push、remote exact、clean在最终Handoff回传。只读原 case02 为0研究calls但已模型响应，outcome cancelled/unknown/null与原红全部保留；没有API/model/auth/sandbox/新UUID、host开启、HOME/catalog/provider改动。检索推测文件 `event_processor_with_json_output.rs` 返回404后按官方tree使用真实 `event_processor_with_jsonl_output.rs`，不伪造映射。真正模型接受/选择 direct11及完整三角色checker仍未在本诊断执行，后续科研/更多Agent放行顺序不变。

## Case03 metadata 有界只读诊断

基线 clean `8acb7d3f3c7a3dcea85c20c2494f74c1377cd437`，固定官方0.159 / `687a119` / Apache-2.0；[矩阵 case03 节](../agents/ORCA_PROTOCOL_MATRIX_1001.md#case03-metadata-网络与继承配置诊断) 收录真实installed继承路径、官方refresh/cache/deadline/fallback/tier来源和联通结果。首批给root `msg_875e67787ae8` / I `msg_33ab5f6fd401`；完整诊断与安全authGET方案给root `msg_c592f176ff07`（请转未来P Owner，旧P settled不复用）/ I `msg_e3e7087780d7`，installed与官方路由候选补充 `msg_3fcf9c17a378` / `msg_0ecc2ed0bc64`；收到I现有环境边界 `msg_02bceade7532`，未要求新科学case。

已确定metadata刷新deadline失败→metadata缺失→fallback/tier omit；未定位旧5秒timeout的底层网络/auth/server原因。早先当前缓存0.158/超300s/无slug和bundled无slug只是观测，不能补造03原cache/env快照；无凭据HTTP405本身也不是authenticated metadata恢复证明。root三条授权 `msg_7b6072e819f8/msg_883d378dd578/msg_96aabbb0c304` 已读取并ACK，明确允许官方正常cache/auth行为；本轮新增实际检查如下，保留此前第一失败和历史RED。

ORCA当前host选中managed id2a305740-3098-46da-a63f-2d9e42ae9d72，实际供给目录AppData/Roaming/orca/codex-accounts/<id>/home与default ~/.codex不同；CLI公开摘要在内存比较provider/workspace身份相等，两边top model/tier相同，无身份原值输出。这只证明当前身份关系，非03历史快照；既有selected-home无副作用解析来源已列矩阵。保持formal默认HOME、原model/tier/项目cwd，现装官方 `codex debug models` 于03:36:26.927Z执行，2.774s exit0、stderr空、10 models，目标gpt-6.1-sol `code_mode_only`/search=true/priority advertised；调用前cache0.158无目标，官方调用后0.159有目标。因此当前metadata刷新成功，无需换模型/删tier/放行fallback/开codehost。默认已成功，按root条件授权不额外proxy比较、不另发自制GET。实际结果薄交root `msg_a9c58e43b03c` / I `msg_0b6fb1c63506`，未来P由root转交。

验证：最终固定官方引用21/21行界、18文件HTTP200及此前5/5关键源码断言通过；只读归档/真实installed/安全键和network-free bundled检查通过，新增官方有界nonbundled检查如上。仅非秘密cache时间/版本与选定公共metadata写新private sibling `morph-agent-protocols-1001-state/metadata-diagnostic-2026-10-01T03-36-26-923Z/{cache-before,default}.json`；无凭据/header/整auth/env/catalog输出，无模型/沙箱/科学UUID，未改I状态。仅两docs入Git；diff/cached、commitpush、remoteexactclean结果在最终Handoff回传。I旧fullchecker exit1缺resume（证据06ee5e4）不重跑/改checker/阈值；case01/02/03 raw/outcomeunknown/null不回写，无研究calls不等于零远端模型效果。当前metadata可达不代签科研/live，旧timeout底层原因仍UNKNOWN。

检索限制如实保留：初始路径模式models_manager/model_provider_info未匹配新的dash包名；`login/src/default_client.rs`为404后按固定tree定位auth/default_client.rs；过宽03路径输出截断后只读精确顶层文件，未据截断推断缺文件。用户要求继续同Task实际检查，未提前结算/新派发；实际检查后root `msg_4d5819c9ed4d` 直接核对default.json并接受当前metadata PASS，明确不再检查/API及按原Owner两docs commit/push收口。没有产品业务修复依据；root另释放I唯一case04，D不辅助预热或参与科学/native，原完整三角色未通过前后续放行顺序不变。
