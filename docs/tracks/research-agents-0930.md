# A 原生 Agent 接入轨 · Owner 报告

基线 ef77af603577d4539d8dbdf780e1536a369b0d12，计划提交 6ba12b24781318383454d2e7fb0b132e897b8a8d；Owner 分支 songconmaisaix31-design/morph-research-agents-0930。仅写 orchestration/native_agents/**、tests/native_agents/**、docs/agents/** 与本报告，未改旧 sample executor、公共依赖/锁或其它轨道，未创建 Agent/Run。

实现：两种官方 native_cli 注册、实际 npm bin 发现、只读 auth/version、typed argv 交互/headless/resume/MCP、bootstrap 主动发现认领提示、未知事件/usage/exit 语义、原生 raw JSONL、绑定既有 AgentId/AttemptId 的持久证据接口、own/attached 取消隔离。Windows 使用官方 Job Object + 启动屏障，POSIX 私有进程组；没有派单或自动恢复/重试。

来源：stablyai/orca 固定 85f8d6b5f507df795cd3cef1cdea08124cf801ee，MIT Copyright 2026 Lovecast Inc.，许可已保留；已核对指定 shared 文件、真实依赖和有关测试，窄行为适配与独立原模块运行见 docs/agents/upstream.md。Codex 0.159.0 Apache-2.0 和 Claude 2.1.238 自身许可独立，未复制 CLI 实现，无 SDK 结论。

当前本地证据：

- `python -m orchestration.native_agents probe`：Codex 0.159.0 / Claude 2.1.238，两者 version/auth exit=0、authenticated=true、精确版本相符。只读前置，不是模型/MCP interface_live。
- 新建/恢复、交互/headless 共 8 个原生 argv 的 `--help` 解析：全部 exit=0，未发送模型请求。
- `python -m pytest tests/native_agents -q --basetemp=tests/native_agents/.runtime/pytest-stage1 --tb=short`：73 passed；真实 subprocess / Windows Job Object / 外部附着进程保留 / unknown / canonical binding fixture 契约均覆盖，provider 数据为 mock。
- `python -m mypy --strict orchestration/native_agents`：10 source files，通过。
- `git diff --no-index docs/agents/.reference/src/shared/print-mode-headless-command.ts tests/native_agents/upstream/print-mode-headless-command.ts`：exit=0；pytest 实际用 Node 24.16.0 内置 TS stripping 跑 unchanged 上游纯模块，与 Python port 比较。上游全套 Vitest/Electron测试 NOT_RUN。
- 旧 Codex 兼容检查与构建复验正在收口；首次失败见下表，不据此宣称所有门禁已过。

历史失败保留，不覆盖：

| 首次/阶段命令 | 原结果 | 有界诊断和处理 |
|---|---|---|
| 错猜 `node .../@anthropic-ai/claude-code/cli.js` version/auth | MODULE_NOT_FOUND | 实读当地 npm shim/package.json：2.1.238 bin 为 bin/claude.exe，解析使用真实 bin map，未安装/升级/切换账号 |
| 初次新目录 strict | 11 errors | 修正 object narrowing、Literal 和跨平台类型；未降 strict |
| native pytest-first，指定未存在 .runtime 父目录 | 38 passed / 26 setup errors，WinError 3 | 新建本轨测试输出父目录；未改断言 |
| native pytest-second | 58 passed / 6 failed | `orca` 子串断言误把合法工作区父目录当依赖；保留失败，改为实际 executable/argv 语义检查，未增加 Orca 产品依赖 |
| native pytest-third，新增启动屏障 | 62 passed / 2 failed | native 未启动却误用屏障 exit，修复独立 launch-error 日志使 exit 保持 None；保留 0.2 秒 timeout 阈值，错误留存测试用确定 observer clock 等待真实 subprocess 发出错误，另加真实 wall timeout 检查 |
| native binding strict | 1 object-not-indexable error | 使用窄化的 dict payload 修复；未加 ignore |
| 系统 Python `-m build --no-isolation` | No module named build | 复用原项目已有 .venv 作构建检查，不动公共依赖/锁 |
| 旧 tests/t2/test_codex.py，源码树 --basetemp | 2 passed / 9 failed：既有 executor 要求 OS temp | 原门禁、断言和旧代码保持不变；默认 OS temp 复验单列 |

首次 readiness timeout 为开发终端历史：已 skip 升级提示，用户只读 cwd/SHA/branch 探针通过后沿同 Task retry；这不是产品门禁。

接口 Handoff：B 提供官方 FastMCP stdio `python -m swarm.research --config ABS_TRUSTED_JSON`，host 身份权限不由工具参数决定。A 不合并 B 分支；canonical claim 回包新 attempt_id 随 B 最终 SHA 交付，旧阶段29446a0只有 Lease，A 不凭空补身份。native-bound 只是可追溯报告，不替代 B authoritative ledger / fencing / 科研判据。

限制与未执行：真实原生模型、MCP工具连接、真实 claim/实验/复现/adoption、原生持久 session 恢复与交互 TUI 均 NOT_RUN，由最终 I 在统一候选按最多3会话运行；Linux/WSL实际进程组及原生环境尚 NOT_RUN。无硬 token/cost 封顶，observer工具限制不能撤回已发出请求，费用/远端效果 unknown不重试；附着会话无 stdin 接管，后台脱离进程组资源无清理保证。Hub/生产部署/tag/公共主线合并未执行。
