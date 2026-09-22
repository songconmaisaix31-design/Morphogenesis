# Morphogenesis 多 Agent 开发包 · 统一版（README）

> 生成时点：2026/09/22（Day 2）。本包为**收敛后的唯一权威版本集合**，已做过全文档一致性对齐与矛盾消解。

## 权威顺序（冲突时以左为准）
1. **统一对齐与矛盾消解说明** ← 最高裁定
2. AI 原生多 Agent 多轨开发说明
3. 开发文档 v2
4. 深度思考
5. 作战方案 v2
6. 时间安排表
7. 开发文档 v1（**已归档，禁止据此开工**）

## 本包文件

| 文件 | 定位 | 状态 |
|---|---|---|
| `Morphogenesis_统一对齐与矛盾消解.md` | 收敛与裁定、矛盾清查表 | ★ 现行·最高 |
| `Morphogenesis_AI原生多Agent多轨开发说明.md` | 交 AI 开工的作业规范（六轨 + 十维隔离） | 现行 |
| `Morphogenesis_开发文档_v2.md` | 工程细节 | 现行 |
| `Morphogenesis_深度思考.md` | 设计推理 | 现行 |
| `Morphogenesis_作战方案_v2.md` | 战略与事实 | 现行 |
| `Morphogenesis_时间安排表.md` | 节奏（已对齐术语/门禁） | 现行 |
| `Morphogenesis_开发文档_v1.md` | 历史 | **已归档** |

## 关键决策（本包已统一）
- **ORCA 定位**：**代码不依赖 ORCA**（独立原型）；**运行时可用 ORCA 无限量批发 Agent**（"兵源"非"地基"）。
- **供给无上限 ≠ 支出无上限**：规模放开，但受运行规格（总预算/最大重试/停止条件）约束，登记 `Provision`。
- **身份三层**：Role / AgentId / AttemptId，缺一不可。
- **统一消息封装** Envelope；**目录命名唯一**（`orchestration/` 等）。
- **mock 不验收**：`provenance` 标记 + 三态分离（`contract_local / interface_live / task_live`）。
- **门禁统一 G0–G5**。

## 隔离十维（全队强制）
文件系统（git worktree）/ 契约 / 进程 / 端口 / 数据存储 / 消息事件 / mock / 凭据 / 产物 / 调度。

## 仍待确认（不阻塞开工）
1. EvoMap Hub 沙箱地址/凭据 → 未确认前只用本地隔离 stub；
2. ORCA 批发接口地址/凭据/配额 → 未确认前降级为固定规模蜂群。
