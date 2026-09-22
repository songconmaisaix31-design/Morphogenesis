# T5 五分钟本地演示

先确认 T0 的 `bootstrap` 和 T2 的 runtime/export 入口都已合并。真实演示不制造任务、模型输出或事件：T0 准备固定样例，T2 运行后把 `Envelope` JSONL 写入 `runtime_exports/events.jsonl`，最后由本轨只读展示。

```powershell
$env:MORPHOGENESIS_T2_DEMO_COMMAND = '<T2 owner documented command that runs and exports JSONL>'
.\demo\run-demo.ps1
```

打开 `http://127.0.0.1:7500`。该命令只有在 T2 命令成功且导出文件存在时才预览；任何失败都停止，不会降级为 mock 或把未验证结果标为 `task_live`。

仅用于布局和图表检查的 fixture 必须显式选择：

```powershell
.\demo\run-demo.ps1 -Mock
```

它在页面上标识为 `mock`，`interface_live` 与 `task_live` 都是 `not_run`，不能作为运行验收。T2 当前承诺的接口是 `orchestration.events.export_events(store, run_id, destination)` 生成 JSONL `Envelope`；这个格式只支持消息流，未导出的 Gene 正文和历史指标保持空态，不作推断。
