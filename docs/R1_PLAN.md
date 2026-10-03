# Research Swarm Alpha R1 一页开发计划（2026-10-03）

## 用户模型选择与当前并行顺序（13:00）

用户指定 Codex 使用 GPT-6.1 Sol，OpenCode 使用 DeepSeek V4 Pro。主控已通过原终端官方模型菜单逐一确认 A/B/C/P/F/Q/I 为 `GPT-6.1-Sol max`，保留各原会话、Task、worktree、branch 和既有 max 推理档；当前无活跃 OpenCode，后续如复用则显式指定用户模型，不为此增加品牌或新开发轨。模型切换不是科研运行授权。原 Task 在安全边界暂时返回输入态，A/B 已在同 Task 接续；P 等人工 AOCI receipt 时保持闲置。

F 当前阶段已验收结算。B 新 SOURCE `5769005b09f1b756c94fdad0649a6b74690c0ca9` 已固定，A 接其受信配置并完成核心 AOCI，Q 可由原 Owner 独立复核该固定导出实现及三个受影响原测试。P 的受保护索引输入冻结；无实际人类 TTY receipt 前不执行 transition apply。重安装/测试仍串行；I 等领域最终交付后再唯一集成。

冻结导出的当前实现按每个文件执行原 OpenSandbox pause、Docker 只读 HEAD/GET、原 OpenSandbox resume；不能把早期“最终导出保持暂停至销毁”的提议当实现事实。固定上游 runtime volume 实际为 RW，仅允许 sandbox main/egress 这对自有容器独占且两者冻结，不能再描述为只读挂载。导出目录与其祖先/子路径不得有挂载。实际 Engine/隔离仍待单独 AT07。

## 12:24 导出工程决策（真实运行权限不变）

经 B 原 Owner 的官方源码/API 有界调查，继续在原 B 轨离线实现最小修复：复用 OpenSandbox 官方整容器 pause、受信 Docker Engine stat/archive 和原 session/finalize_session；不新增 executor 或运行权威。当前 fail-closed/Range 修正先独立提交保留失败，后继实现仍由 B 负责原适配器、边界测试、必要官方 Docker SDK 依赖/锁及授权包。Windows npipe 使用成熟官方 transport，不自研协议；真实 Engine/API 版本仍未知，须以后 AT07 核对。

冻结期间验收批准目录路径、所有祖先/leaf 无符号链接、无共享写入挂载、普通文件、字节/时间限额；tar 的链接/特殊类型/额外成员拒绝且不提取到宿主。Engine PathStat 不提供 nlink，不能宣称排除了全部 inode 别名；这一未承诺条件不额外升级为本轮收口门，宿主凭据/控制面及原始数据的隔离要求保持。任何暂停、恢复、流读取或 owned 清理效果未知均走原 unknown 边界，不自动重发。

若后继需要 HostConfig/factory 受信控制面注入，由 A 原 Owner 在原源码路径接线，并在稳定接口后完成核心 AOCI；B 只 Handoff。Q 原 Owner 在 B 后继固定后独立复核受影响边界，保留旧默认能力导致的首失败，不用假能力 fixture 宣称生产可执行。活跃槽位先由 P/F 完成阶段释放，I 仍待最终领域交付。以上仅工程实现决定，不授权启动 Docker/WSL、创建沙箱、执行 AT07 或研究候选。

## 2026-10-03 MVP 追加：AOCI 开发上下文与节点终端

用户追加继续 Orca/Codex YOLO 并行，接入 https://github.com/aoci-spec/aoci-code/ 以减少重复源码检索，前端参考 Codex GUI，拓扑节点右键打开其会话终端和上下文。本节扩展下节收口范围；原三项行为、一次最终完整离线回归、单独授权 AT-07、通过后一次 L2 的顺序继续生效，不扩大到 L3、多用户、跨宿主或更多运行品牌/语言。

| 长期 Owner | 原 worktree / branch 后缀 | 追加 write_paths 与交付 |
|---|---|---|
| A / 原 Codex | morph-r1-research-1003 | 先交完当前 FR04/native binding SOURCE/REPORT，再接核心开发 AOCI：aoci.txt、aoci.meta.txt、aoci.code.txt、.aoci 中官方可提交配置/索引基线、.gitignore 的 AOCI 区块、.gitattributes 的官方 AOCI LF 规则、docs/development/aoci.md；项目 .codex/config.toml 仅本机忽略。原源码归属不变。 |
| B / 原 Codex | morph-r1-experiments-1003 | 保持 AT-07 离线检查包、必要适配器边界修补及原 write_paths，不承担 UI/AOCI。 |
| P / 原 Codex | research-r1-product-1003 | 先交跨片段正式入口候选；后继复用原产品 native/process/session 记录提供节点会话/上下文 API，完成产品仓库 AOCI 同类文件（含官方 .gitattributes LF 规则）与安装说明。排除 F 路径和治理。 |
| F / 原 Codex | research-r1-ui-1003 | 原 frontend/**、web/static/**、tests/ui/**、r1-ui 报告：Codex GUI 参考布局、研究/成员拓扑、右键菜单、对应会话终端与上下文；键盘和窄屏可用。HTTP 契约与 P Handoff。 |

C 正证据已交付验收，留原 Worker 返修；不再加新业务轨。I 待 A/B/P/F 领域和配置交付后普通 exact merge，固定最终核心/产品组合，最后一次完整产品离线回归与适用 installed 页面观察。最多同时 3 个 Worker 加主控；测试/构建资源冲突时排队，其余开发/阅读并行，不重复跑已绿且未受改动影响的门。

AOCI 使用官方固定发布二进制和官方 MCP，不复制索引器/调度器/证明系统，不作为科研运行依赖。当前核实可用发布为 v0.1.0-rc17（预发布，FSL-1.1-MIT）；实际接入记录精确二进制/版本/许可与验证等级。配置限定每个仓库/worktree，机器绝对路径的 host 配置、运行 ledger/drafts、凭据不入库，不改全局 HOME/auth/provider。官方索引条目基于已读当前源文件；范围、未完成条目和 stale 状态如实报告，不用空索引或模板批量冒充认知完成。一次建立后按任务相关源文件增量核对；不得为“节省”预设或虚构 token 数，实际未提供用量则未知。AGENTS.md 仍由主控维护，官方 init 需要的标记区块由 Owner 提供精确 Handoff 后主控落地，不覆盖现有规则；新 MCP 未在旧会话加载时明确区分配置完成和实际连接。

前端保留现有 React/TDesign 及真实事实投影，参考 Codex 的项目/线程侧栏、中心工作区与终端检查区。用户已明确：查看对应 Agent 会话的实时输出和上下文，先只读。节点必须按原 project/member/task/invocation/session 身份关联，不能从相同作者或同时出现推造边，不能用静态演示代替已连接终端。不存在/歧义/归档/未知状态按真实原因展示；打开、切换和刷新只读取，不发命令、不发起科研、不重放请求或重置预算。不得以新 UI 将 mock/L0/L1 标成真实 L2。



## 2026-10-03 用户追加收口：三项行为、一次最终离线回归、独立 AT-07、一次 L2

本节为当前执行范围，覆盖下方历史阶段中的运行顺序与收口口径。原 Spec 文件 SHA256 AB73F60E26AF1BC1B44CA5DA9B94B2CFDDA91A5D4ACB25683B9386462DCFB165；本轮用户最新指令优先。起点为核心 SOURCE 2c63bc7c9e49edff28e26f5930a22d0415fadd65 / REPORT 08b31b39c075571ffd247e2b591d657ce09b6b34，产品 SOURCE 9e2718789cb67f8b829207e17dac4d95a88e59c9 / REPORT a7f657d18fae33fc2a4df92b5fcb60dcd7839c5d。

| 阶段/Owner | 固定 worktree / branch 后缀 | 本轮独占写入与交付 |
|---|---|---|
| A / 原 Codex | morph-r1-research-1003 | 沿用 A 的 swarm/research 非 B/C 文件、tests/research 非 B/C 文件和 r1-research 报告；核查 FR-04 相关性选择实际调用位置。私库已有能力只交调用/测试证据；缺口最小修正。 |
| C / 原 Codex | morph-r1-policy-1003 | 沿用 C policy/feedback/router/pheromone/worker_loop 与原测试/报告；针对正证据影响后续机会与选择的前后差异补测试并修正。不得新增复杂评分框架。 |
| P / 原 Codex | research-r1-product-1003 | 沿用 P 产品后端/CLI/后端测试/锁/报告，排除 F UI 与治理；明确正式 envelope 下跨片段接续路径、累计预算和共享知识；已实现则补证，最终精确 pin。 |
| I / 原 Codex，前三轨交付后 | morph-r1-integration-1003 | 普通精确合并、最终 SOURCE 固定、独立 COPY 安装，一次完整产品离线回归，原 installed 输入观察、适用核心/边界/构建；领域问题退原 Owner。 |

F UI 及 Q 边界现有文件归属保留，只有发现需修改其文件的具体缺陷时才唤醒原 Worker。C 完成后复用 B 原隔离 Owner（morph-r1-experiments-1003），在最终冻结前准备 AT-07 可审查检查包与必要最小工具/配置：沿用 orchestration/experiments/**、tests/experiments/**、docs/tracks/r1-experiments.md，并独占本轮 deploy/opensandbox/**、docs/experiments/** 中隔离探针相关文件；不改 SDK/后端种类，不接管 A/C/P。此阶段仅准备和离线验证，不启动 Docker/真实服务，不创建真实沙箱或运行候选；具体授权仍在固定组合离线验收后请求，探针通过后才进入 L2。主控只写计划/状态/决策/验收，保留根工作树 docs/SWARM_SOL_PLAN.md 原 WIP。Orca 继续原 Run run_d5306f2e4993，已结算任务使用新子 Task/Dispatch，不复用旧生命周期身份。

验收要求：
- 正证据必须证明接受前/后的合法路线机会或选择发生可解释变化，证据引用进入实际选择/认领记录；重复证据、未经独立接受、越权/不适用仍不得增益。旧 v0/v0.1 语义保留。
- 接续必须通过正式入口与原 envelope/预算账本；新片段保存共同知识、累计额度、原未知效果屏障，不能通过新 run 重置。区分原会话 resume 与新有界片段，不新增第二套执行/调度状态。
- 上下文必须给出正式调用链和针对性测试：权限、分支、依赖、能力、引用相关性及来源回链；禁止把全项目列表截断冒充相关性选择。无必要不重复实现私库模块。
- 最终产品回归在单一固定核心/产品 SOURCE 组合进行，完整首次结果原样保留；补齐两视窗相关 installed 输入观察。只记录性能实际值，不以未经承诺的最优值或额外优化作为退出条件。

真实运行顺序：工程修正/补证 → 最终组合离线验收 → 准备具体 AT-07 后单独请求用户授权 → 仅无害探针检验真实隔离 → 通过后按明确目标/材料/账户/环境/预算/数据范围执行一次 L2。AT-07 未通过前，生成候选不得进入真实执行环境。L2 给问题与材料，不给完整候选代码；保留非预置分支、代码版本、实验、独立复核、证据驱动后续行动和至少一次实际使用，允许不支持改进。人工理解观察可结合真实页面。L3、大规模效率对照、多用户、跨宿主、更多学科/Agent 品牌/计算语言、完整 RSI 不在本轮。

旧首 RED、UNKNOWN、NOT_RUN 和原十项产品类型债保留。C 系统 Python 误装清理此前被自动审批 blocked by policy 拒绝，本轮不重试或绕过；人工处理仍见原报告。

07:16 交付状态：五条开发轨、独立Q及唯一I已完成本轮实现与适用本地工程验收；最终核心SOURCE2c63bc7和产品SOURCE9e27187固定，精确双平台CI、独立COPY安装、适用类型、完整产品/边界/UI与实际四页面结果见R1_ACCEPTANCE。P原Owner四项新增类型返修已交付；原十项类型债保留。I仅后继文档REPORT待最后push，领域源码不再变化。AT07真实隔离及L2等仍NOT_RUN，全R1退出条件未达成，main/tag/部署未执行。

06:43 当前阶段：五条领域轨和独立Q已交付，唯一I已在独立工作树以Codex YOLO实际启动（task_8f2c3d496f12 / ctx_7ab9bc21276f）。核心SOURCE2c63bc7、产品SOURCEc9fcc6e已push；原P仅最终pin与短安装复验，I负责全新独立安装/完整适用回归/实际页面，领域问题仍退原Owner。最终结果与完整SHA见R1_STATUS/R1_ACCEPTANCE，AT07/L2等未执行项不转为PASS。

事实源：`docs/source/Morphogenesis_Research_Swarm_Spec_v1.0_2026-10-02.md`。用户已授权开发、Orca 派发、测试、commit/push；旧包冲突条款以本 Spec 及本计划为准。旧冻结源码/报告和首失败原样保留。

02:06 接续决策：用户再次要求继续多 Agent。原 A/B/C/P provider 会话故障及 Orca 重启后，六条轨均恢复为 Codex YOLO 会话，保持原 Task、worktree、branch、独占路径与原 WIP；下表 OpenCode 是初始派发记录，当前地址与恢复依据以 `R1_STATUS.md` 为准。主控仍不写业务代码，Q 独立验收，最后单一 I 集成。

基线：核心报告 `326fd8f633c7db72d4fab216a10a77b63aafe59d`（源码 `7062a632b8c625c05b35bdec4c36fce63a31c2a4`）；产品 `78370ad68dcc78d26b880854aedabac2e5ab797e`（完整受测源码 `a25aa40bb0f5259799641fee378d09ccc5887054`）。主线有 WIP，保持不动。

| 长期轨 | 单 Worker / Orca worktree / 分支后缀 | 独占 write_paths | FR / AT |
|---|---|---|---|
| A 共同研究与正式 MCP | OpenCode / morph-r1-research-1003 / 同名 | `swarm/research/**`（除 case.py、feedback*.py、policy*.py）；`tests/research/**`（除 test_generated*.py、test_research_policy*.py）；`docs/tracks/r1-research.md` | FR01-11；AT01-04,09,14-15 |
| B 动态候选、隔离、评价与继承 | OpenCode / morph-r1-experiments-1003 / 同名 | `orchestration/experiments/**`, `local_assets/**`, `swarm/research/case.py`, `tests/experiments/**`, `tests/local_assets/**`, `tests/research/test_generated*.py`, `docs/tracks/r1-experiments.md`, 核心 `pyproject.toml`/`poetry.lock`/`THIRD_PARTY_NOTICES.md`（依赖必要时） | FR15-20；AT05-07,12-15,17-18 |
| C 贡献与研究路线政策 | OpenCode / morph-r1-policy-1003 / 同名 | `swarm/router.py`, `swarm/pheromone.py`, `swarm/feedback.py`, `swarm/worker_loop.py`, `swarm/research/feedback*.py`, `swarm/research/policy*.py`, `tests/swarm/**`, `tests/research/test_research_policy*.py`, `docs/tracks/r1-policy.md` | FR12-14,24；AT08-11,14-15 |
| P 产品后端与正式入口 | OpenCode / research-r1-product-1003 / 同名，私库 | 后端源码/CLI/后端测试/pyproject/uv.lock/README/第三方说明和 `docs/tracks/r1-product.md`；排除 F 的 UI 路径、治理文件与 Spec | FR01-05,09-11,20-24；AT01-02,04,09,14-18 |
| I 最后独立集成（轨道完成后派） | Codex / 核心 morph-r1-integration-1003；产品由独立安装验收使用 P/F 最终源码 | exact merge、`tests/integration/**` 排除 Q 的 `r1_security/**`、`docs/tracks/r1-integration.md`，少量导入/配置/类型/路由胶水；领域问题退原 Worker | 全部 AT 的适用 L0/L1；L2 单列 |

主控只写治理：AGENTS、docs/PLAN、docs/R1_PLAN、docs/STATUS、docs/R1_STATUS、docs/DECISIONS、docs/ACCEPTANCE、docs/source 指针及用户 Spec 存档；不写业务代码。每轨固定同一 Agent/worktree/branch，开发、测试、返修和文档持续由原所有者负责。跨轨发 Handoff，禁止修改他轨文件。采用普通精确 SHA merge，无 cherry-pick/force push。

顺序：并行 A(M1)、B(M2)、C(M3)、P(M4 后端)、F(M4 UI)，Q 独立验收 → A 普通 exact merge B/C 最终接口并在自身 service/MCP 接线 → P/F 在真实可用候选核心上完成产品与安装/HTTP/UI，Q 验证组合及独立负例 → I 精确合并与适用回归 → P 同原 Owner 必要时最终 repin/lock，F 同原 Owner 处理 UI 返修 → I 复核固定组合/历史保护/导出。候选验证不能冒充最终组合通过；集成 Agent 不补领域功能。M3 只接受可信评价事件；不把 LLM 意见或崩溃当反证。旧 v0/v0.1、两类固定案例、literal-files-v1 不改语义。

复用唯一 TaskLedger/lease/fencing/BudgetLedger/native/Executor/资产消费采用链；不新增调度器或完成证明。研究表仅描述语义，未知效果不重放，费用未知为 null。候选不在宿主执行；隔离能力未验证则拒绝执行。资源/数据/模型/费用 envelope 不随新 branch/run 重置。

本轮可执行：开发 Agent、确定性与安装/真实本机 HTTP/MCP/页面测试；模型科研调用、真实沙箱资源与隔离探针、论文外发、GPU/云后端、发布未获运行级授权，不执行。L2 所需研究题/容差/批准环境/账户/预算/数据外发仍需具体授权；建议默认不能变成已批准额度。

验收：每轨先交 FR→源码→契约→AT 映射、最小 API Handoff，再源码+适用测试+报告 commit/push 精确 SHA；保留首 RED、NOT_RUN、既有类型错误身份。I 验证最终核心/产品源码、wheel 安装、pytest、新增边界 strict、前端构建/两视窗真实 HTTP 页面、兼容案例/检查器、幂等与中断。AT07/L2/L3/人工观察未执行时明确列出，不宣称 R1 PASS。
## 用户追加并行指令（2026-10-03）

用户要求“多开几条codex并行去耦合开发路线，直接开yolo模式”。本条覆盖初始四轨规模及P前端所有权；既有A/B/C/P保持原Owner，不接管其领域源码。

当前为五条互斥开发轨 A/B/C/P/F；Q 是独立验收，不是第六条业务实现轨。P 的既有 UI WIP 已保留为 `44353e35bc745b7542625b85376791b5ac68aa4f` 交 F；F 负责普通 merge 的 UI 冲突，不覆盖自己的工作。

- F / Codex YOLO / 私库 `research-r1-ui-1003` / 同名分支：独占 `frontend/**`, `src/morph_research/web/static/**`, `tests/ui/**`, `docs/tracks/r1-ui.md`（含前端package-lock）。P从现在排除以上路径，只负责产品后端/CLI/正式入口/uv.lock/pyproject及后端测试。F先只读，收到P无WIP交接后写入；HTTP契约通过Handoff，核心机制仍由原Owner负责。
- Q / Codex YOLO / 核心 `morph-r1-boundaries-1003` / 同名分支：独占新增 `tests/integration/r1_security/**`, `docs/tracks/r1-boundaries.md`；黑盒独立验证A/B/C正式边界、跨项目/注入/伪造批准/未知/中断/额度不重置/宿主不执行。Q不能修改领域实现或原测试阈值，缺陷发原Owner修复。本轮不做真实沙箱探针或模型科研。

新Codex进程用本次argv `codex --no-daemon --dangerously-bypass-approvals-and-sandbox`，不改全局配置；NO-DAEMON用于避开Codex0.160新共享daemon与Orca识别问题。若仍无法识别保留真实失败，不能用OpenCode冒充Codex。YOLO是研发进程执行权限，不赋予收费科学运行/资料外发/新云计算或沙箱授权。最终I仍待领域轨完成后派，合并所有者精确提交和独立安装验收。
