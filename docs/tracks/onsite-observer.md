# O 轨：现场操作员 Enter 观察器

基线：`9e4b43281b2b29a2ae946405bb0aa7ec7eee2def`。分支：`songconmaisaix31-design/morph-onsite-observer`。独占修改范围为 `tests/integration/**`、本报告；未修改 demo、viz、运行时、计划、状态或验收文件。

## 交付

`observe_rehearsal.cjs` 增加 `--operator-enter`，只允许与 `manual` 同用。参数解析和模块导入无浏览器加载、进程启动、模型调用或文件写入。未指定新参数时继续使用原 2.3 秒自动 Enter；`auto`、模型默认选择、双视口审计与旧 `manual-enter.json` 格式保持。

新模式先检查当前 stdin 是支持 raw mode 的 TTY，管道或重定向在启动真实 demo 前失败。两个既有浏览器视口（1366×768、1920×1080）都记录“等待下线确认”、来源 live，且序号与新 runtime root 下真实 `rehearsal.json` 的 live / awaiting_offline 相同时，才提示操作员并等待一次 Enter。输入前后的文件阶段和序号都要通过门禁；不读取凭据、不转发或记录任意终端文字。

人工输入窗口默认 120 秒，可用 `--operator-timeout-seconds 1..480` 调整，实际等待不超过观察器原有 480 秒总截止时间的剩余值。提示前已进入 Node 缓冲区的内容会丢弃；操作员应看到提示后再按一次 Enter，不应预输入或粘贴多行。

## 现场入口（本轨未执行）

由获授权操作员在普通交互终端运行以下入口；端口必须独立且空闲，目录每次全新。环境沿用现有锁环境、`MORPH_PLAYWRIGHT` / `MORPH_CHROMIUM` 与协调者受保护的子进程环境注入，不把密钥写进命令或页面。

```powershell
node tests/integration/observe_rehearsal.cjs manual 7530 "$env:TEMP/morph-onsite-operator-new" --executor evomap --model evomap-gpt-5.6-luna --operator-enter --operator-timeout-seconds 120
```

此入口会启动真实 demo；命令不是只读回放，也不是本地测试。不要对 7526 使用该入口。操作员看到终端提示、完成现场讲解后按 Enter；Ctrl+C / Escape 取消，Ctrl+D / Ctrl+Z 作为 EOF 处理。

## 证据与失败边界

- 原截图、双视口 JSON、demo stdout/stderr 与 `summary.json` 继续保留；新目录检查仍拒绝覆盖已有证据。
- 新模式 `manual-enter.json` 记录 `source: operator`、stage、sequence、`armedAt`、实际收到 Enter 的 `at`、写入回执 `forwardedAt`，以及 waiting / received / forwarded / failed 状态；失败时记录 `failedAt` 与明确原因，不记录键入正文。
- `summary.json` 仅在新模式增加 `confirmation: operator` 与 `operatorTimeoutMs`。新模式失败产生非零退出；超时、EOF、取消、阶段变更都不会发送换行，收尾关闭 demo stdin，使运行时现有 `input()` 按 EOF 停止并保留证据，不启动新 demo、不补发模型请求。
- 输入转发错误只尝试一次，结果未知不重试；`at` 证明收到操作员 Enter，`forwardedAt` 只证明管道写入回调成功，成员实际下线与后续任务结果仍由原运行证据和审计确认。
- 收尾摘要可能在 demo 退出前写入，因此 `exitCode` 可为 null；不能把它解释为运行时已终止。只读 viewer 生命周期维持原脚本策略，不自动杀死未知进程。已有在途模型调用不强杀、不重试。

## 验证

Node `v24.16.0`，以下命令通过（31 tests）：

```powershell
node --test tests/integration/test_browser_options.cjs tests/integration/test_operator_enter.cjs tests/integration/test_observer_control.cjs
```

覆盖纯参数解析、默认模型、实际子进程环境去除密钥哨兵、非 TTY 启动前失败、双视口/序号/来源/文件阶段门禁、无自动输入、一次确认和时间戳、超时、EOF、取消、任意文字不落日志、转发未知不重试。通过 VM 执行实际观察器主流程、用本地假 browser/child 边界复验人工成功、默认自动成功及四种失败收尾：只启动一次、换行次数、stdin 关闭、浏览器关闭、证据保留、凭据隔离。

`node --check` 检查本轨全部新增/修改 CJS，通过；`git diff --check` 通过。测试只使用本地合成终端/快照/浏览器/子进程夹具，不发 HTTP 模型请求，不启动实际 PowerShell demo。

## 真实剩余限制

本轨没有真实付费模型调用，没有操作或修改 7526 回放及第四轮证据，没有实接投影和真实人工终端彩排；这些均为 NOT_RUN，31 项本地测试不能升级为现场验收。工作树没有 `.venv`，本次只运行适用 Node 测试和语法检查；Python 全套测试、strict、构建由独立集成轨复验。操作员的物理投影见证与后续新真跑仍须分别记录。
