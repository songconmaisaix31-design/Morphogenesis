# V 固定彩排界面

基线 `791d3cf`；消费 R 提交 `652e319` 中的 `orchestration.rehearsal.read_rehearsal` 与 `RehearsalDocument`，未复制快照、调度或 Attempt 契约。`viz.adapter.load_rehearsal()` 只接受命名的 `rehearsal.json`，按请求重新验证；`--replay` 直接调用 R 的只读降级函数，不改写原始 TaskResult 或文件。

主屏在 1366×768 / 1920×1080 的四栏叙事中放置：题目、独立 checkpoint 的 0/3 至 3/3、实际 PipeState 拓扑（边粗细=权重，inactive=虚线，数值与前序数值并列）、下线原因与恢复选路。Gene 区只呈现 `GeneView` 中的采用次数、权重、tau 与归档状态；数据缺失时保留空态，旧 Gene/消息/指标仪表板入口和三态仍可用。

`demo/run-demo.ps1` 先启动回环只读页面，再以前台运行 R 的固定流程；真实模式必须显式 `-AuthorizeLive`，自动与控制台 Enter 手动两种模式均只授权 `repair`、`recovery` 两个新任务。`-Replay` 保持原证据路径且明确显示回放；`-Mock` 仅为旧仪表板布局检查，绝不表示真实通过。

本轨本地验证（锁定 `.venv`）：

```powershell
.venv\Scripts\python.exe -m unittest tests/t5/test_adapter.py -v
.venv\Scripts\mypy.exe --strict --follow-imports=skip --no-incremental --cache-dir tests/t5/.mypy_cache viz tests/t5/test_adapter.py
node --check viz/static/app.js
```

上述检查仅覆盖合同与界面代码。真实模型任务、三轮软件彩排和物理投影由 I / 现场操作员执行；浏览器空态核查不替代真实任务验收。

浏览器复核使用 Orca embedded browser：空态页面在 1707×909 视口无横向溢出，明确显示未加载且 `task_live=not_run`。另用 R 本地 fixture 生成的 `mock` 快照检查了 3/3 checkpoint、两条实际管道、下线原因、恢复选路、两条 Gene 和 ECharts 拓扑 canvas；三态为 `passed / not_run / not_run`，因此只证明 mock 界面接线，不能外推为现场通过。Windows 冷启动还确认页面约 3 秒内以 launcher 加监听子进程就绪；文件未出现时仍返回空态 `task_live=not_run`，失败清理只针对该次验证的父子进程。1366×768 / 1920×1080 的实际投影与三次真实运行仍由 I / 现场操作员执行。
