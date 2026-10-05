---
name: windfinder-task-flow
description: 解释研究蜂群的任务编排流程（propose→enqueue→claim→execute→review→adopt）与开启新任务的方式（propose_research_work 语义与宿主授权）。只解释、只导航，绝不代执行。当用户问“任务是怎么流转的 / 怎么开新任务 / 谁来认领和采纳”时使用。
---

# WindFinder 任务编排流程（只解释，不执行）

WindFinder 只读，不参与任何一步的真实执行。以下流程用于向用户解释“任务如何流转”，并导航到对应入口。

## 六阶段流程

1. **propose（提议）** —— `propose_research_work` 提议新工作；只有宿主授权范围内才会被准入单一账本。WindFinder 只解释其语义，不代调用。
2. **enqueue（准入）** —— 宿主把提议准入账本，成为可发现任务。
3. **claim（认领）** —— `lease_task(action="claim")` 由绑定身份主动认领租约；`choose_research_work` 仅选择机会，认领仍需 lease 复核。
4. **execute（执行）** —— 隔离执行冻结计划（`research_experiment(action="run")`、`research_candidate` 等），候选代码绝不宿主执行。
5. **review（复核）** —— 独立复现与静态校验（`verify_research`、`approve_candidate`）。
6. **adopt（采纳）** —— `apply_candidate` 经账本围栏写入真实采纳。

以上 1–6 全部是写操作，WindFinder 一律只导航，不执行。

## 开启新任务

- 新任务来自 `propose_research_work`（携带 kind / goal / justification / expected_contribution / scope 等），**准入需要宿主授权**，不是 Agent 自己说了算。
- WindFinder 用 `discover_tasks` 查看 scope 内已存在任务，用 `research_advisory` 看分支机会，但不能提出或准入任何任务。

## 边界

- 不 propose、不 enqueue、不 claim、不 execute、不 review、不 adopt。
- 用户要“开新任务 / 认领 / 执行”时，导航说明：这是宿主 / Worker / 原生 Agent 的职责，需要宿主授权。
