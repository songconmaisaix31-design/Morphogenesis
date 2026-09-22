# 开发状态

- 主线分支：`codex/morphogenesis-mainline`。
- 基线：`117fdde`，仅 LICENSE，工作区原先干净。
- 用户开发包已导入，计划提交 `45ddbd1` 已推送；八轨开发已运行，当前收拢真实闭环与集成候选。
- Orca Run：`run_3cac02602e7c`；协调 terminal：`term_263319ac-dfa1-4ff3-8463-7fe200fad470`。
- T0：worktree `C:/Users/DW/orca/workspaces/Morphogenesis/morph-t0-foundation`，branch `songconmaisaix31-design/morph-t0-foundation`，Task `task_3bdb79633de5`，Dispatch `ctx_177ee63228f3`，Worker terminal `term_d2213de0-0e65-444f-898d-0846c2c41869`；已确认实际 working。
- 按用户最新要求改为八个功能轨；以下均已收到 ready 启动回执。
- T0 最新契约与基础实现 `bdcb001` 已推送，32 项测试通过；最终全包分发与集成验证待完成。
- T2 事件导出 `53fa942` 已推送，运行入口尚在开发，非 task_live。

所有 worktree 根目录：`C:/Users/DW/orca/workspaces/Morphogenesis/`，分支前缀：`songconmaisaix31-design/`。下表名称同时是目录名与分支后缀。

| 轨 | worktree / branch 后缀 | 模型（实际生效） | Task | Dispatch |
|---|---|---|---|---|
| T0 | morph-t0-foundation | gpt-6-astra（继承） | task_3bdb79633de5 | ctx_177ee63228f3 |
| T1 | morph-t1-adapters | gpt-6-astra（继承） | task_b92657a452bc | ctx_c6e4d813fcc6 |
| T2 | morph-t2-runtime | gpt-6-astra / xhigh | task_c03f393208dd | ctx_0f54173a063d |
| T3T | morph-t3-topology | gpt-5.6-terra / high | task_9c35a6fd3bee | ctx_ed1ee9f3817e |
| T3M | morph-t3-metabolism | gpt-6-astra / high | task_beb94df50bac | ctx_31f926047197 |
| T5 | morph-t5-viz | gpt-5.6-terra / high | task_f37cacf4910a | ctx_101b31af0af0 |
| H | morph-hub | gpt-6-astra / high | task_89da8e623a87 | ctx_a2be7a533175 |
| P | morph-provision | gpt-5.6-luna / high | task_9ae1f6f71a6d | ctx_a408002966fe |

## 当前分轨证据

以下为 Worker 报告且精确提交已推送；不替代最终集成验收。

| 轨 | 当前提交 | 证据 / 剩余工作 |
|---|---|---|
| T0 | bdcb001 | 32 tests、strict、基础包构建；完整分发配置收尾 |
| T1 | adca7f6 | 17 桥测试、真实本地官方 SDK/MCP；待集成 |
| H | 07636c1 | 46 tests、strict；只允许本地 stub，远端未运行 |
| P | 1c4e5e9 | 6 tests、strict；重复 builder 身份已修复，Worker 完成并释放 |
| T3T | a12d288 | 10 tests、strict；成功率/闲置衰减已返修 |
| T3M | 240aaf0 | 13 本轨 tests + 31 T0 tests、strict；真实任务采用由 T2 验证 |
| T2 | 53fa942 | 已有事件导出；执行/接续/真实复用仍在开发验证 |
| T5 | bde0ab4 | 初版 6 tests；本地 ECharts、真实经验/结果导出及演示入口收尾 |

P 最初 Task `task_509a8b88e115` / Dispatch `ctx_8e1f19911c90` 完成后在原 terminal 立即续接上述返修任务。最终 `worker-release` 回执为 `released` / `closed_agent_terminal`，输出归档 captured。

验收尚未完成，G0–G5 均不标记通过。各轨 merge_ready 后派发独立集成 Agent，领域返修留在原 Worker。
