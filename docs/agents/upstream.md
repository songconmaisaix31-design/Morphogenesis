# 固定来源与复用边界

核验日期 2026-09-30。上游固定 [stablyai/orca commit 85f8d6b5f507df795cd3cef1cdea08124cf801ee](https://github.com/stablyai/orca/tree/85f8d6b5f507df795cd3cef1cdea08124cf801ee)，不是浮动 HEAD。[LICENSE](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/LICENSE) 为 MIT，Copyright (c) 2026 Lovecast Inc.，完整许可保存在 `orchestration/native_agents/ORCA_LICENSE.txt`。

已实际读取以下 `src/shared/` 文件及有关测试；每个链接固定在同一 SHA。

| 源码 | 核验结论及本轨使用 |
|---|---|
| [tui-agent-config.ts](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/shared/tui-agent-config.ts)、[types](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/shared/tui-agent-config-types.ts) | Claude/Codex 使用 argv 注入；探测名、启动名、预期进程、提示运输能力是不同字段。只保留两种原生 CLI，未移植 Orca 提前写 trust、盲重试 Enter、Agent Teams wrapper。 |
| [launch-command](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/shared/tui-agent-launch-command.ts)、[startup-shell](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/shared/tui-agent-startup-shell.ts) | 上游处理 posix、PowerShell、cmd 三种 shell、option terminator 和 session option 冲突。本轨直接 `subprocess` typed argv / `shell=False`；Windows npm 按 package.json bin 解析，绕过 .cmd/.ps1，不移植 shell 命令字符串。WSL 在其 Linux 宿主独立发现 CLI，不从 Windows 自动启动/接管 WSL。 |
| [agent-command-plan](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/shared/agent-command-plan.ts) | 上游将命令分成 binary/prefixArgs/env。本轨只接受 typed argv，不开放含 shell 语法的自定义命令串。 |
| [agent-headless-command](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/shared/agent-headless-command.ts)、[print-mode-headless-command](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/shared/print-mode-headless-command.ts) | Claude `-p/--print`、json/stream-json 与交互不同；`--` 后是提示文本。独立纯模块连原文件复制到 tests/native_agents/upstream，并用 Node 内置 TS stripping 实际执行；Python 行为移植与原模块逐 case 对比。 |
| [process-recognition](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/shared/agent-process-recognition.ts) | basename/.exe/.cmd/.ps1 和 codex-aarch64-ap 规则作窄行为移植；generic node/powershell 不证明 agent 身份。识别结果不授予取消权限；完全未移植全机进程扫描。 |
| [resume-launch-command](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/shared/agent-resume-launch-command.ts)、[agent-session-resume](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/shared/agent-session-resume.ts) | Claude 只保留一个 authoritative `--resume ID`，Codex `resume ID`；provider session 与 pane/工作树身份分开，warm attach 不应重启。原生 CLI 支持 exact UUID，本轨拒绝 --last、自动恢复、伪造 session。无桌面睡眠/恢复数据库。 |
| [hook-types](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/shared/agent-hook-types.ts) | hook installed/partial/error/skipped、协议版本和 live Session 生命周期是独立事实。本轨使用 CLI stdout JSONL，无 managed hook 安装，无全局 hook/auth 写入，也不把配置存在视为 installed。 |

测试阅读包括 `tui-agent-config.test.ts`、`tui-agent-prompt-transport.test.ts`、`agent-process-recognition.test.ts`、`agent-resume-launch-command.test.ts`、`tui-agent-startup-shell.test.ts`、`agent-session-resume.test.ts`。移植 case 明确列在 tests/native_agents/test_contracts.py；上游完整 Vitest suite **NOT_RUN**。原配置、启动和识别模块涉及多个相邻 shared 模块及桌面会话约定，不把整个图搬进 Python 产品。

实际 [package.json](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/package.json) 声明 Electron 43.7.5、node-pty ^1.1.0、Vitest ^4.1.11、Zustand ^5.0.14，并有 Electron/native-runtime 预检查与桌面恢复 E2E。产品不引入这些依赖；只复用上述行为与独立原模块作测试 oracle。

原生运行时独立保留其许可：当地 `@openai/codex` 0.159.0 为 Apache-2.0，npm bin 是 bin/codex.js；`@anthropic-ai/claude-code` 2.1.238 的 package.json 许可字段为 SEE LICENSE IN README.md，当地 bin 是 bin/claude.exe，不能按 Orca MIT 重许可 Claude。两者只被调用，不复制实现。

事件核对：[Codex rust-v0.159.0 exec_events.rs](https://github.com/openai/codex/blob/rust-v0.159.0/codex-rs/exec/src/exec_events.rs)、[官方非交互说明](https://developers.openai.com/codex/noninteractive)、[Claude 官方 headless](https://code.claude.com/docs/en/headless)。Schema 来源不是实际模型日志；本轨所有事件 fixture 均为 mock/contract_local，真正原生事件/MCP/模型链由最终 I 在统一候选验证。
