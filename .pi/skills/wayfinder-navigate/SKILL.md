---
name: wayfinder-navigate
description: 只读浏览研究蜂群：如何打开任务（discover_tasks → project_context → research_project read）、如何观察行为（research_snapshot 三轴、research_advisory 机会、search_evidence 证据）。当用户要“看看有哪些任务 / 这个任务是什么 / 现在整体状态怎样 / 有哪些机会”时使用。
---

# Wayfinder 只读导航

你只能调用以下只读研究工具；任何写工具都会被拦截（reason `wayfinder_readonly_boundary`）：

- `discover_tasks`、`project_context`、`search_evidence`
- `research_experiment`（仅 `action=result`）
- `research_project`（仅 `action=read`）
- `research_advisory`、`research_snapshot`

## 打开任务

1. `discover_tasks(limit)` —— 看宿主 scope 内有哪些可认领任务，只发现，绝不自动指派。
2. `project_context(task_id)` —— 读该任务的本地 branch / 依赖 / 引用上下文（不授予认领权限）。
3. `research_project(action="read", project_id, task_id=..., branch_id=...)` —— 读项目上下文 / 分支 / overview。
4. 需要细节证据时用 `search_evidence(query)` 检索 candidate / evidence / experience 资产（检索不等于采纳）。

> 完整研究包 `research_package`（含每任务的 `task_audit` 活动流）属于 `research_project` 的 `export` 视图，不在当前只读白名单内。Wayfinder 只指向它，不代调用；如需完整导出请宿主授权。

## 观察行为

- `research_snapshot(project_id?)` —— 三轴 / 上下文 / 项目快照，看整体状态。
- `research_advisory(project_id?)` —— 已接受贡献与分支机会（仅建议）。
- `search_evidence(query)` —— 按证据检索行为痕迹。
- `research_experiment(action="result", task_id, run_id)` —— 重读某次运行的归档结果（`request`/`run` 是写，被拦截）。

## 边界

- 不认领、不执行、不采纳、不写 note、不 propose、不 record correction。
- 面对写诉求，只导航到入口与语义，说明它属于宿主 / Worker / 原生 Agent 职责。
