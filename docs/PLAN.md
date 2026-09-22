# Morphogenesis 接手与核心闭环一页计划

## 目标与事实源

从仅含 LICENSE 的仓库实现开发包规定的核心原型：固定规模成员通过成熟执行 CLI 完成可验证的小仓库修复；LangGraph 串联分配、执行、独立复核、反馈、接续；拓扑权重影响下一次选路，经验有正文注入和采用记录；真实事件驱动可视化；官方 GEP SDK 校验资产，受控 Hub 发布缺配置时保留待发布。

`docs/source/` 原样保存 2026-09-22 用户开发包。优先级：用户当前指令 > 统一对齐 > AI 原生多轨 > 开发文档 v2 > 推理/方案/时间表。T4/EvoX 为可选扩展，当前不开发。原六轨合并为四条，T2 与 T5 同一所有者，避免运行事件与演示反复交接。

## 四条长期开发轨

| 轨 | 职责与 write_paths | 验收 |
|---|---|---|
| T0 地基 | `contracts/**`, `persistence/**`, `bootstrap/**`, `tools/**`, `tests/t0/**`, `.github/**`, `.gitignore`, `.env.example`, `pyproject.toml`, `poetry.lock`, `package.json`, `package-lock.json`, `README.md`, `THIRD_PARTY_NOTICES.md`, `docs/tracks/t0.md` | Pydantic 身份与消息语义、SQLModel 持久化调用、固定样例任务、可复现依赖锁、类型检查、构建 |
| T1 外部适配 | `hub_client/**`, `bridge_node/**`, `orca_provision/**`, `tests/t1/**`, `docs/tracks/t1.md` | 官方 SDK 跨语言真实校验；MCP 标准客户端；Hub 本地联调与批准/未知状态/重试边界；固定规模供给 |
| T2 执行与演示 | `orchestration/**`, `viz/**`, `demo/**`, `tests/t2/**`, `tests/t5/**`, `docs/tracks/t2.md` | 复用现有 CLI 执行；独立复核；LangGraph 恢复；预算和路径边界；真实事件展示；真实任务正常/接续/经验复用分别留证 |
| T3 核心机制 | `topology/**`, `metabolism/**`, `mocks/**`, `tests/t3/**`, `docs/tracks/t3.md` | 成功/失败改变选路；重复反馈不重复奖励；经验解析/注入/采用/衰减/归档同步检索；复用 Chroma 或 FAISS |

每轨使用 Orca 创建独立 worktree/branch，首次 dispatch 后在 `docs/STATUS.md` 记录实际身份。Worker 只改本轨，依赖/契约变更交 T0。主 Agent 所有权：本文件、`AGENTS.md`、`docs/source/**`、`docs/STATUS.md`、`docs/DECISIONS.md`、`docs/ACCEPTANCE.md`。集成 Agent 所有权：合并操作、`tests/integration/**`、少量跨轨接线胶水；领域修复退回原 Worker。

## 顺序与完成边界

1. 保存事实源与复用决策，commit + push；T0 先交付契约/锁/样例。
2. T1、T2、T3 从 T0 已提交基线并行；T0 持续负责依赖/契约 Handoff；所有轨自行测试并 commit + push。
3. 由一个集成 Agent 合并；运行全套适用测试、严格类型检查、构建、官方 SDK 校验和固定任务验证。必要返修仍由原所有者提交。
4. 主 Agent复核证据并更新验收矩阵，最终分支 push。G3/G4 需要的外部验收若缺凭据，明确未通过，不以本地测试替代。

## 假设与限制

- 固定样例选“修复含三个确定性 bug 的 Python 小模块”，验收测试固定且不由执行者修改。
- 首选已安装的 Codex CLI 作为现有执行入口；仅使用公开 CLI、隔离任务目录和其支持的沙箱，不依赖 ORCA 内部代码。若账号/配额/沙箱阻塞，保留精确错误并标 task_live 未验证，不换 mock。
- 开源复用以依赖调用为主，不复制整个项目；许可证由实际版本核实，原仓库 Apache-2.0 保留。
- Hub 沙箱地址/凭据和运行时 ORCA 供给契约缺失，按文档降级，不要求用户重复确认，不进行生产发布。
