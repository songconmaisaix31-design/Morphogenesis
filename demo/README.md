# 固定彩排入口

先在本工作树安装锁定环境：

```powershell
$env:POETRY_VIRTUALENVS_IN_PROJECT='true'
uv tool run poetry install --no-interaction
npm ci --ignore-scripts --no-audit --no-fund
```

真实彩排需由 I / 已授权操作员明确发起；脚本只传递两项不同的新任务授权，失败、未知或中断不会重试：

```powershell
# 自动：成员在两项任务之间按固定顺序下线
.\demo\run-demo.ps1 -AuthorizeLive -Mode auto

# 手动：页面先启动；控制台出现提示时按 Enter 确认成员下线
.\demo\run-demo.ps1 -AuthorizeLive -Mode manual
```

每轮最多两项新任务（`repair`、`recovery`），三轮总预算由 I 跨根累计；脚本不发送密钥，也不调用未授权的第三项任务。页面只绑定 `127.0.0.1`，读取该轮 `rehearsal.json`，首次快照尚未写出时显示等待而非通过。
页面展示层自 2026-09-23 起为决赛深色黏菌黄设计：紧凑页头、checkpoint/本轮 tokens/活跃 Gene 三大数字、中央真实权重拓扑、四态 Gene 台账与真实阶段事件流；外壳适配自 Tencent tdesign-react-starter（MIT）。端口、数据源与拓扑语义不变，详见 `docs/tracks/frontend-stack.md`。
真实模式会打印本次页面 launcher / listener PID 及 TEMP stdout/stderr 日志目录；展示结束前先核对命令行，再仅关闭这两个已打印的进程。

已有真实历史的失败备用展示必须显式回放。该模式直接读取原证据，并把页面标为“回放视图”；不改原文件、不调用模型：

```powershell
.\demo\run-demo.ps1 -Replay "$env:TEMP\morph-rehearsal-<id>\rehearsal.json"
```

仅检查旧仪表板布局可用 `-Mock`，页面会标为 mock，真实接口和真实任务均为 `not_run`：

```powershell
.\demo\run-demo.ps1 -Mock
```

投影彩排清单：打开 `http://127.0.0.1:7500`；确认浏览器缩放 100%、系统分辨率为 1366×768 或 1920×1080；选择实际投影屏并确认无遮挡；观察同屏的 checkpoint、管道图与下线/恢复卡片。物理连屏、选屏和最终分辨率只能由现场操作员完成，未接入投影设备时均为 NOT_RUN。

2026-09-22 17:30–18:00 的现场顺序、专属端口和人工确认条件见 [`docs/tracks/onsite-viz.md`](../docs/tracks/onsite-viz.md)：协调者管理的 7526 只读回放必须先展示；新的 EvoMap 手动彩排只能使用独立的 7527，且只在真实 `awaiting_offline` 已同时出现在页面和该次运行控制台后由现场操作员按一次 Enter。不要用截图、定时器或 mock/replay 代替该确认，也不要停止或重启 7526。
