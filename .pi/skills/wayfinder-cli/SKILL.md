---
name: wayfinder-cli
description: 项目 CLI 入口清单与白名单：每个入口的用途、用法，以及它属于“只读可执行”还是“仅导航，不执行”。当用户问“有哪些命令 / 怎么跑 / 这个命令能执行吗 / CLI 入口是什么”时使用。
---

# Wayfinder CLI 入口与白名单

调用 `list_cli_entries` 工具可获取机器可读清单；下面是说明。

## 只读可执行白名单（可执行，仅限安全只读）

| 命令 | 用途 |
| --- | --- |
| `git status` | 查看工作区状态 |
| `git log [--oneline]` | 查看提交历史 |
| `git diff` | 查看未提交差异 |
| `ls` / `Get-ChildItem` | 列出目录内容 |
| `Get-Content <log> -Tail 200` / `tail -n 200 <log>` | 查看日志尾部 |

这些命令只读、不改变任何状态，Wayfinder 可以执行。

## 仅导航，不执行

| 入口 | 用途 | 为什么只导航 |
| --- | --- | --- |
| `python -m swarm.research --config <ABS>` | 研究 MCP stdio（作为 MCP server 注册） | 写工具被只读边界拦截；只经 MCP 调用只读工具 |
| `morphogenesis` / `morphogenesis-swarm` | bootstrap / swarm 编排 | 写入账本、租约、候选 |
| `bl` | 阿里云百炼模型 CLI | 模型调用与外部副作用 |
| `pi` | Pi agent 框架 | 自身即 Pi |
| `kimi` | kimi agent | 模型调用入口 |

## 用法要点

- `swarm.research` 由 Wayfinder 注册为 MCP server，配置绝对路径来自 `WAYFINDER_HOST_CONFIG`；缺失时注册失败但不崩溃。
- 模型调用 / 部署 / 安装 / bootstrap / 编排类入口：Wayfinder 只说明用途与用法，不代执行。
- 需要真正执行写操作时，请宿主授权对应的 Worker / 原生 Agent。
