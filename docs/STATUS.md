# 开发状态

- 主线分支：`codex/morphogenesis-mainline`。
- 基线：`117fdde`，仅 LICENSE，工作区原先干净。
- 用户开发包已导入，计划提交 `45ddbd1` 已推送；当前进入 T0 基础契约阶段。
- Orca Run：`run_3cac02602e7c`；协调 terminal：`term_263319ac-dfa1-4ff3-8463-7fe200fad470`。
- T0：worktree `C:/Users/DW/orca/workspaces/Morphogenesis/morph-t0-foundation`，branch `songconmaisaix31-design/morph-t0-foundation`，Task `task_3bdb79633de5`，Dispatch `ctx_177ee63228f3`，Worker terminal `term_d2213de0-0e65-444f-898d-0846c2c41869`；已确认实际 working。
- 按用户最新要求改为八个功能轨；以下均已收到 ready 启动回执。
- T0 初版契约 `d0f5ac9bd75b8b8f1bc12d0d22b625d549833a71` 已推送，测试/类型/构建待完成，未冻结。
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
| P | morph-provision | gpt-5.6-luna / high | task_509a8b88e115 | ctx_8e1f19911c90 |

验收尚未完成，G0–G5 均不标记通过。各轨 merge_ready 后派发独立集成 Agent，领域返修留在原 Worker。
