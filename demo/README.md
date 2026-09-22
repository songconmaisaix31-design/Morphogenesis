# T5 五分钟本地演示

先确认 T0 的 `bootstrap` 和 T2 `orchestration.acceptance` 已合并。真实演示不制造任务、模型输出或事件：T2 的单次受预算限制入口调用 T0 固定样例，写出 `Envelope`、`TaskResult`、T3M `GeneView` 和 `UseRecord` sidecars，最后由本轨只读展示。

```powershell
.\demo\run-demo.ps1
```

打开 `http://127.0.0.1:7500`。可通过 `-Model`、`-MaxTokens`、`-MaxCostUsd` 与 `-TimeoutSeconds` 传入显式运行规格；该命令仅在 T2 返回成功且四个固定 sidecar 都存在时才预览，任何失败都停止，不会降级为 mock 或把未验证结果标为 `task_live`。

仅用于布局和图表检查的 fixture 必须显式选择：

```powershell
.\demo\run-demo.ps1 -Mock
```

它在页面上标识为 `mock`，`interface_live` 与 `task_live` 都是 `not_run`，不能作为运行验收。真实预览只接受受限 T2 证据根目录：`events.jsonl`（完整 `Envelope`）、`result.json`（完整 `TaskResult`）、`genes.json`（`GeneView[]`）和 `adoption.json`（当前 run 的 `UseRecord[]`）；每一项都按共享 Pydantic 模型重验。没有 `metrics.json` 的正式来源，当前/均值/历史最佳图保持空态，不作推断。
