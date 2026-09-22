# Morphogenesis 接手与核心闭环一页计划

## 已通过：EvoMap 网关第四轮与备选模型配置

结果（2026-09-22）：原 R `94b7081` 已推送并由原 I 合入 `7c0bb6a`，200 tests、53 文件 strict、构建/SDK/安装包及精确提交双平台 CI 通过。北京时间 16:12–16:13 第四轮完成：两个真实网关请求、两个任务各 3/3、手动下线后另一 builder 实际执行、Gene 采用与真实衰减归档通过，2,235 tokens / 费用未知。OpenCode 项目配置的 7 个备选代码模型解析/枚举通过，工具调用与其它模型实际开发仍 NOT_RUN。详细证据与边界见 [ACCEPTANCE](ACCEPTANCE.md)。下文保留本轮授权、所有权及原始范围。

用户已在本轮明确批准原 R/I 会话执行提交推送、集成复验及第四轮彩排。此前“待有限命令授权”的阻塞已解除；同一会话可按需执行本项目 Git 元数据写入/推送、Orca 通信和测试（含结束测试自身子进程）的受限外命令。保留全局默认值，不写永久允许规则，不影响其他项目或进程。R 沿原失败 Task 重试；I 沿原会话接收正式集成任务，原候选及报告草稿继续由原所有者完成。

新增要求：EvoMap API 纳入并行开发备选模型。本机已安装 OpenCode 1.18.31（MIT），复用其官方 OpenAI-compatible provider；I 额外独占 `opencode.evomap.json` 的项目级提供方配置胶水（只引用环境变量，无秘密、无新调度器），并在 `docs/tracks/rehearsal-integration.md` 记录接入命令、模型选择、隔离与实际验证边界。按任务难度给出建议分档，目录可见与开发工具调用兼容分别标注；不把图片模型当代码 Worker，不自动替换正在运行的 R/I 模型，不因列入备选而逐个付费调用。具体模型池在本计划及验收记录维护。

2026-09-22 用户明确要求切换执行器到已验证的 EvoMap Gateway，并跑第四轮完整真实软件彩排。基线 `5dd9e2c`；沿用原 R/I Agent、worktree、branch，保留两轨已有未提交返修草稿。主 Agent 只负责计划、状态、决策、验收及按集成交接运行已审阅的真实入口。

| 轨 | 固定所有者 / write_paths | 交付与验收 |
|---|---|---|
| R 网关执行 | 原 morph-rehearsal-runtime；`orchestration/**`, `tests/t2/**`, `docs/tracks/rehearsal-runtime.md`；`.runtime/**` 仅本地测试产物 | 复用现有 httpx 与 Executor/Proposal/Pydantic/样例白名单；一次受限 Chat Completions 请求产生提案，无工具循环、无自动重试或 CLI 伪造事件。显式 executor 选择，保留 Codex 兼容；测试凭据缺失、网络/HTTP/无效提案、usage、路径与采用一致性。完成既有时间竞态返修，commit+push |
| I 集成与第四轮 | 原 morph-rehearsal-integration；普通合并、`tests/integration/**`, `docs/tracks/rehearsal-integration.md`；允许仅在 `demo/run-demo.ps1` 添加执行器/网关参数透传及凭据不传给 viewer 的启动配置胶水，领域问题回 R/V | 接收 R 精确提交后合并；全套测试/strict/build；扩展既有审计与双尺寸浏览器观察器，真实网关第四轮手动下线，保留独立 TEMP 证据；commit+push |

第四轮限定两个新任务、最多两次模型 POST，模型 `evomap-gpt-5.6-luna`，Base URL `https://api.evomap.ai/v1`。每次发送有限输出上限与超时；未知效果不重试。两份全新坏样例各自必须从 0/3 到 3/3，第一位 builder 在两任务间下线，第二位真实执行并采用第一份 Gene，真实墙钟 τ=10 秒衰减归档且不可检索。复用当前 ECharts 页面；出现显示领域缺陷才交回原 V，不预先新开显示轨。

网关凭据只由协调者在运行时注入专用子进程环境，不进入 Worker prompt、Git、日志、页面数据或进程参数。不修改全局 CLI/账号/权限设置；受限环境测试优先使用本轨允许的私有 TEMP，不能完成的步骤如实保留错误。三轮旧证据只读；第四轮单列，物理投影、生产 Hub 发布和在途进程强杀仍不纳入本轮软件证据。

### 并行开发的 EvoMap 备选模型池

下表是初始任务分配建议，不是性能、价格或工具兼容性排名。每个候选仍须满足该轨的真实测试与验收；保持 1 Agent / 1 worktree / 1 branch / 互斥 write_paths。当前 R/I 延续原 Astra 会话，备用配置采用已安装的 OpenCode 1.18.31（MIT）及其官方 [OpenAI-compatible provider](https://opencode.ai/docs/providers/#custom-provider)，通过 [OPENCODE_CONFIG 与环境变量引用](https://opencode.ai/docs/config/) 显式启用，不修改全局账号。

| 任务难度/用途 | 备选模型 ID |
|---|---|
| 边界明确的小改动、测试或文档 | `evomap-gpt-5.6-luna`、`evomap-deepseek-v4-flash` |
| 常规模块开发与返修 | `evomap-glm-5.1`、`evomap-glm-5.2`、`evomap-gpt-5.6-terra`（网关目录额外提供） |
| 复杂契约、跨模块推理与审查 | `evomap-gpt-5.6-sol`、`evomap-gemini-3.1-pro-preview` |
| 图像素材，独立于代码 Worker | `evomap-gemini-2.5-flash-image`、`evomap-gemini-3-pro-image`、`evomap-gemini-3.1-flash-image` |

目前目录十项已核验；Luna 的非流式 Chat Completions 已有短文本 HTTP 200，第四轮另行验证修复链。OpenCode 配置解析/模型枚举、真实工具调用与各模型端到端开发验收分列，不把模型目录可见或固定修复 API 成功等同于所有模型可承担自主开发。只保留代码模型在备选配置，图片模型不进入编码任务派发；本轮不为加入备选逐个追加模型调用。

## 当前阶段：三次完整软件彩排已通过（2026-09-22）

收尾返修：候选 Windows CI 暴露测试以 `weight > 0.5` 假设快照耗时小于 69ms 的竞态，即使下一次 CI 偶然通过也需修复。恢复原 R 会话、原 worktree/branch，仅改 `tests/t2/test_rehearsal.py` 与本轨报告，按真实采样时间验证衰减语义；恢复原 I 会话做普通合并及适用检查，并纠正回放进程交接。协调者重建只读回放服务并维护验收记录；不新增演示模型调用，不改业务运行时。

用户新增验收：固定已知 bug 的小仓库，自动判定 checkpoint；完整呈现“出题 → 管道图变化 → 下线一位 Agent 并重新选路恢复 → Gene 池代谢”。至少三次软件全流程彩排；实际投影接线单独记录，不能用浏览器截图代替。

结果：主线已接收集成 `e83a8168a066a0c687a15a7d28c15739bab13ad6`。北京时间 13:23–13:30 完成 manual / auto / auto 三轮，每轮两次新任务均通过三个独立 checkpoint，实际成员切换、Gene 采用、墙钟衰减和归档均通过；合计 6 次 CLI / 87,133 tokens，费用未知。158 tests、52 文件 strict、构建/安装包检查通过；最终界面 `80220c5` 以明确 replay 的双尺寸实图和实际绘制边界复验。约 14:12 补测用户提供的 EvoMap Gateway 凭据，模型目录与 Luna 一次短文本生成均 HTTP 200，实际 15 tokens；尚未用该网关重跑演示，真实投影仍 NOT_RUN。详见 [本轮验收](ACCEPTANCE.md) 和 [集成报告](tracks/rehearsal-integration.md)。

基线 `44e2889`。最小并行拆分为两条开发轨加一条独立集成轨，每轨固定 Agent / worktree / branch；原有核心实现与锁不重写。优先复用现有 LangGraph、TopologyEngine、LocalMetabolism、固定独立验证器、ECharts。主 Agent 只维护本计划、状态、决策和验收并核对只读 API 测试。

| 轨 | 模型 | 互斥 write_paths | 交付 |
|---|---|---|---|
| R 运行彩排 | Astra xhigh | `orchestration/**`, `bootstrap/**`, `topology/**`, `tests/t2/**`, `tests/t0/test_bootstrap.py`, `tests/t3/topology/**`, `docs/tracks/rehearsal-runtime.md` | 最小有类型演示快照契约、逐项真实 checkpoint、成员下线/重新选路、真实经验产生/采用/墙钟衰减归档、可重复的固定流程 |
| V 演示界面 | Terra high | `viz/**`, `demo/**`, `tests/t5/**`, `docs/tracks/rehearsal-ui.md` | 消费 R 快照，分步管道/成员/通过率/Gene 池展示，手动与自动彩排入口，大屏布局/现场清单 |
| I 集成验收 | Astra high | 普通合并、`tests/integration/**`, `docs/tracks/rehearsal-integration.md`，少量导入配置胶水 | 锁环境测试/strict/build、真实完整彩排三次、浏览器截图、精确分支推送 |

运行边界：每次彩排最多两次明确的新模型任务（常规修复、移除成员后新任务恢复），三次合计六次；不重试未知执行。下线发生于两任务间，属于固定成员池的可用性/选路自愈；没有证据时不得声称杀死在途模型进程后自动恢复。Gene 使用真实任务经验与真实时间；演示衰减时间常数需在页面明确显示。API 凭据只通过受保护的进程环境使用，Base URL/用途未确认前不发送，不入 Git/日志/Worker prompt。真实投影设备未确认前为 NOT_RUN。

顺序：R 先交最小快照契约；V 同时完成布局后接该精确契约；各轨测试/返修/commit/push，统一集成做六次以内真实调用与三次浏览器全流程。旧阶段证据不计为本轮三次彩排。

实施结果（2026-09-22）：以下八个功能轨与独立集成轨已完成当前核心原型，主线接收集成提交 `b6bb49c`。G1/G2 与固定样例的三次真实任务通过，外部验收限制和完整命令见 [ACCEPTANCE](ACCEPTANCE.md)，各轨分支/SHA 与资源处置见 [STATUS](STATUS.md)。本计划保留原始范围，未因验收收尾扩展 T4 或远端生产发布。

## 目标与事实源

从仅含 LICENSE 的仓库实现开发包规定的核心原型：固定规模成员通过成熟执行 CLI 完成可验证的小仓库修复；LangGraph 串联分配、执行、独立复核、反馈、接续；拓扑权重影响下一次选路，经验有正文注入和采用记录；真实事件驱动可视化；官方 GEP SDK 校验资产，受控 Hub 发布缺配置时保留待发布。

`docs/source/` 原样保存 2026-09-22 用户开发包。优先级：用户当前指令 > 统一对齐 > AI 原生多轨 > 开发文档 v2 > 推理/方案/时间表。T4/EvoX 为可选扩展，当前不开发。用户最新指令要求按功能解耦、不限制为四轨，并按难度分级模型；据此拆为以下八个互斥功能轨，数量随实际依赖调整。

## 功能开发轨与模型分级

| 轨 / 模型档位 | 职责与 write_paths | 验收 |
|---|---|---|
| T0 地基 / Astra，已运行 | `contracts/**`, `persistence/**`, `bootstrap/**`, `tools/**`, `tests/t0/**`, `.github/**`, `.gitignore`, `.env.example`, `pyproject.toml`, `poetry.lock`, `package.json`, `package-lock.json`, `README.md`, `THIRD_PARTY_NOTICES.md`, `docs/tracks/t0.md` | 契约语义、SQLModel 持久化、固定样例、依赖锁、类型检查、构建 |
| T1 桥 / Astra，已运行 | `bridge_node/**`, `tests/t1/bridge/**`, `docs/tracks/t1.md` | 官方 SDK schema/hash；官方 MCP 客户端与真实本地工具调用 |
| H Hub / Astra high | `hub_client/**`, `tests/t1/hub/**`, `docs/tracks/hub.md` | A2A、本地联调、发布批准、未知状态不重试、生命周期 |
| P 供给 / Luna high | `orca_provision/**`, `tests/t1/provision/**`, `docs/tracks/provision.md` | 最小供给接口、固定规模 fallback、配额和身份；不臆造远端 API |
| T2 执行 / Astra xhigh | `orchestration/**`, `tests/t2/**`, `docs/tracks/t2.md` | Codex CLI、独立复核、LangGraph 接续、预算/路径、正常/接续/复用实测 |
| T3T 拓扑 / Terra high | `topology/**`, `tests/t3/topology/**`, `docs/tracks/topology.md` | 权重影响实例选择、幂等反馈、明确生边与裁剪规则 |
| T3M 代谢 / Astra high | `metabolism/**`, `mocks/**`, `tests/t3/metabolism/**`, `docs/tracks/metabolism.md` | 复用检索库；经验正文注入/采用/衰减/归档一致性 |
| T5 展示 / Terra high | `viz/**`, `demo/**`, `tests/t5/**`, `docs/tracks/t5.md` | ECharts Gene/消息双视图、真实事件来源、独立三态、可跑演示 |

每轨使用 Orca 创建独立 worktree/branch，首次 dispatch 后在 `docs/STATUS.md` 记录实际身份。Worker 只改本轨，依赖/契约变更交 T0。主 Agent 所有权：本文件、`AGENTS.md`、`docs/source/**`、`docs/STATUS.md`、`docs/DECISIONS.md`、`docs/ACCEPTANCE.md`。集成 Agent 所有权：合并操作、`tests/integration/**`、少量跨轨接线胶水；领域修复退回原 Worker。

## 顺序与完成边界

1. 保存事实源与复用决策，commit + push；T0 先交付契约/锁/样例。
2. 各轨先在互斥文件内进行不依赖契约的官方 API 核查和适配设计；收到 T0 精确提交后合并该基线，再对接公共契约，不自行猜测或复制契约。T0 持续负责依赖/契约 Handoff；各轨自行测试并 commit + push。
3. 由一个集成 Agent 合并；运行全套适用测试、严格类型检查、构建、官方 SDK 校验和固定任务验证。必要返修仍由原所有者提交。
4. 主 Agent复核证据并更新验收矩阵，最终分支 push。G3/G4 需要的外部验收若缺凭据，明确未通过，不以本地测试替代。

模型选择已从本机 Codex 模型目录核实；实际生效模型仍以 Orca 启动回执/运行状态为准。现有 Worker 保持会话，后续按档位显式启动；不为凑数量再拆强耦合文件，也不因扩大并行引入 T4 新范围。集成使用 Astra high，领域修复留给原 Worker。

## 假设与限制

- 固定样例选“修复含三个确定性 bug 的 Python 小模块”，验收测试固定且不由执行者修改。
- 首选已安装的 Codex CLI 作为现有执行入口；仅使用公开 CLI、隔离任务目录和其支持的沙箱，不依赖 ORCA 内部代码。若账号/配额/沙箱阻塞，保留精确错误并标 task_live 未验证，不换 mock。
- 开源复用以依赖调用为主，不复制整个项目；许可证由实际版本核实，原仓库 Apache-2.0 保留。
- Hub 沙箱地址/凭据和运行时 ORCA 供给契约缺失，按文档降级，不要求用户重复确认，不进行生产发布。
