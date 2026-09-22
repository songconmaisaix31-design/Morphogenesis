# Morphogenesis 接手与核心闭环一页计划

## 当前阶段：三次完整软件彩排已通过（2026-09-22）

用户新增验收：固定已知 bug 的小仓库，自动判定 checkpoint；完整呈现“出题 → 管道图变化 → 下线一位 Agent 并重新选路恢复 → Gene 池代谢”。至少三次软件全流程彩排；实际投影接线单独记录，不能用浏览器截图代替。

结果：主线已接收集成 `e83a8168a066a0c687a15a7d28c15739bab13ad6`。北京时间 13:23–13:30 完成 manual / auto / auto 三轮，每轮两次新任务均通过三个独立 checkpoint，实际成员切换、Gene 采用、墙钟衰减和归档均通过；合计 6 次 CLI / 87,133 tokens，费用未知。158 tests、52 文件 strict、构建/安装包检查通过；最终界面 `80220c5` 以明确 replay 的双尺寸实图和实际绘制边界复验。API 新凭据因缺目的地未测试，真实投影仍 NOT_RUN。详见 [本轮验收](ACCEPTANCE.md) 和 [集成报告](tracks/rehearsal-integration.md)。

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
