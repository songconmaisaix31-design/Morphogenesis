# Morphogenesis 接手与核心闭环一页计划

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
