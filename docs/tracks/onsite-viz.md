# V 现场投影操作清单（17:30–18:00）

基线：`9e4b432 plan parallel onsite rehearsal tracks`。本清单只组织现有 `demo/run-demo.ps1`、固定彩排页面和已有网关入口；不新增调度、Attempt、证明或模型调用。时间是操作顺序的建议，任何未完成阶段都不得用跳过、重跑或模拟来赶时间。

## 现场角色与硬边界

- **协调者**持有 7526 的生命周期和网关专用子进程环境；V 不停止、重启或改写 7526，也不读取、显示或记录密钥。
- **现场操作员**负责投影连接、全屏、浏览器缩放和一次人工 Enter；物理屏幕的可见性只能由其现场见证，软件截图不是投影验收。
- **7526**只用于既有第四轮证据的降级回放；**7527**只用于本次独立的、明确授权的 EvoMap 手动真跑。两者不得混用同一端口或把回放称为本次 live。
- 本次新真跑的额度是 `repair` 和 `recovery` 两项任务各一次；失败、超时、中断、HTTP/执行结果未知或端口冲突时保留现状、记录错误并停止本次真跑，**不重试**、不换模型、不另开根伪装成功。

## 17:30–17:35：投影与 7526 回放预检

1. 接上实际投影，选择正确的扩展/复制屏；将浏览器缩放设为 100%，操作系统分辨率确认在 1366×768 或 1920×1080。打开后用浏览器全屏（通常为 F11），现场操作员确认没有遮挡、裁切或错误屏幕。
2. 在**不改变 7526 进程**的 PowerShell 执行以下只读检查：

   ```powershell
   $replay = Invoke-WebRequest -UseBasicParsing http://127.0.0.1:7526/api/dashboard -TimeoutSec 10
   $replayData = $replay.Content | ConvertFrom-Json
   "HTTP=$($replay.StatusCode); provenance=$($replayData.provenance); task_live=$($replayData.acceptance.task_live); interface_live=$($replayData.acceptance.interface_live)"
   ```

   通过条件是 `HTTP=200; provenance=replay; task_live=not_run; interface_live=not_run`。本轨在编写本清单时实际得到这一结果；若结果不同、连接失败或页面并非协调者指定的回放，停止在此处并报告协调者，绝不自行重启服务。
3. 打开 `http://127.0.0.1:7526/` 并全屏展示。口径固定为：“这是既有第四轮的只读回放，来源为 replay，不代表新的现场模型调用或本次物理投影已经验收。”

## 17:35–17:42：先展示已知回放

按页面叙事展示题目/checkpoint、管道权重、`成员下线 → 重新选路` 和 Gene 区。页面中的 `replay` 徽标及 `not_run` 的 live 状态必须保持可见或可被操作员复查；它们是边界提示，不是故障。

现场操作员在真实投影屏上确认以下事项，并口头/现场记录结果：全屏已开启、缩放为 100%、目标投影屏正确、首屏 Gene 区可见、无明显裁切或遮挡。这里的确认只证明物理展示；不能从浏览器截图、HTTP 或本地回放外推为真实模型运行。

## 17:42–17:45：7527 单次真跑门槛

7526 继续原样显示，另开一个 PowerShell 窗口供 7527 使用。先执行：

```powershell
Get-NetTCPConnection -State Listen -LocalPort 7527 -ErrorAction SilentlyContinue
if (-not $env:MORPH_EVOMAP_API_KEY) { throw '缺少由协调者注入的 EvoMap 专用子进程环境；不启动真跑。' }
```

第一条必须无输出；有监听者时不得终止未知进程，也不得占用 7526，报告端口冲突并只保留回放展示。第二条只检查环境是否已由协调者安全注入，绝不输出变量值、写入文件或加入命令参数。

得到协调者的本次授权且上述门槛通过后，在仓库根目录仅执行一次：

```powershell
.\demo\run-demo.ps1 -AuthorizeLive -Mode manual -Port 7527 -Executor evomap -Model evomap-gpt-5.6-luna -TimeoutSeconds 180 -TauSeconds 10 -StageDelay 2
```

该命令会创建新的 TEMP 证据根并在 7527 启动本次页面；它只授权两个命名任务。不要在另一窗口复制执行相同命令，也不要以 `-Mock`、`-Replay`、`auto` 或额外模型调用替代它。

## 17:45–17:55：真实 `awaiting_offline` 的人工确认

1. 打开 `http://127.0.0.1:7527/`，按与回放相同的投影/全屏要求在实际屏幕展示。首次快照未生成时，“等待”不是通过；继续等待本次前台命令的实际阶段推进。
2. **不要按时间或页面预测 Enter。** 仅当以下三项同时成立时，现场操作员才可在运行该命令的同一个控制台按**一次** Enter：

   ```powershell
   $live = (Invoke-WebRequest -UseBasicParsing http://127.0.0.1:7527/api/dashboard -TimeoutSec 10).Content | ConvertFrom-Json
   "provenance=$($live.provenance); stage=$($live.rehearsal.current.stage)"
   ```

   - 命令输出为 `provenance=live; stage=awaiting_offline`；
   - 7527 页面明确显示“等待下线确认”；
   - 该次前台运行控制台显示 `Press Enter to remove the winning logical builder before the NEW recovery task:`。

   此 Enter 只移除两项任务之间的获胜**逻辑** builder。它不是强杀在途模型进程；不得宣称或演示“在途 Agent 被杀后恢复”。不满足任一条件、控制台已退出或出现错误时，不输入 Enter，保留日志/根并报告。
3. Enter 后先确认页面推进为“成员已下线”，原获胜成员管道为 inactive，再展示恢复任务由另一 builder 选路和执行。只有本次终态为 `completed`，且 7527 API 仍报告 `provenance=live`、页面的 task-live 状态为 `passed` 时，才可描述为“一次新的软件真跑完成”。任一失败/未知状态都只报告该状态，不重新执行。

## 17:55–18:00：收尾与记录

保留 7527 的终态页面供现场观看；记录实际开始/结束时间、7526 HTTP/provenance、7527 端口门槛、是否三条件满足后按了一次 Enter、最终 stage/验收状态和投影见证结论。`run-demo.ps1` 会打印该次 viewer launcher/listener PID 与日志目录；如需在展示结束后关闭，只能先逐一核验这些**本次打印的** PID 命令行属于 `m viz.server --port 7527`，再由其所有者关闭，绝不按端口或进程名广泛终止。

若 7527 没有完成，7526 回放仍可继续作为明确标注的备用展示，但必须声明新真跑未完成。Hub 发布、物理投影（除现场人员本次见证）、动态 ORCA 供给、T4、OpenCode 工具/流式能力以及在途进程强杀恢复都不在本清单的验收范围内。

## 本轨本地核验（非物理投影）

- 只读 `GET http://127.0.0.1:7526/api/dashboard`：HTTP 200，`provenance=replay`，`task_live=not_run`，`interface_live=not_run`；未操作该服务。
- `uv tool run poetry run python -B -m pytest -q tests/t5 --basetemp <私有 TEMP>`：**11 passed**。
- 设置现有 Playwright/Chromium 路径后，`node tests/integration/check_rehearsal_layout.cjs http://127.0.0.1:7526 <私有 TEMP>`：1366×768 与 1920×1080 的 replay 页面均通过；3 个管道标签、3 个节点，无裁切、重叠或横向溢出，Gene 区位于首屏。

最后一项是对本地浏览器渲染的只读检查，不是投影连接或现场物理可见性的证据。本轨没有执行 EvoMap 请求、没有生成付费模型调用、没有停止/重启 7526，也没有修改运行时或集成观察器。
