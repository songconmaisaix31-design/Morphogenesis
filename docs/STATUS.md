# 开发状态

- 主线分支：`codex/morphogenesis-mainline`。
- 基线：`117fdde`，仅 LICENSE，工作区原先干净。
- 用户开发包已导入，计划提交 `45ddbd1` 已推送；八轨候选已齐，唯一集成 Agent 已启动。
- Orca Run：`run_3cac02602e7c`；协调 terminal：`term_263319ac-dfa1-4ff3-8463-7fe200fad470`。
- T0：worktree `C:/Users/DW/orca/workspaces/Morphogenesis/morph-t0-foundation`，branch `songconmaisaix31-design/morph-t0-foundation`，Task `task_3bdb79633de5`，Dispatch `ctx_177ee63228f3`，Worker terminal `term_d2213de0-0e65-444f-898d-0846c2c41869`；已确认实际 working。
- 按用户最新要求改为八个功能轨；以下均已收到 ready 启动回执。
- T0 最新分发/README `cdc8972` 已推送；完整合并视图最终检查交集成 Agent。
- T2 `33ed929` 已推送，三次真实正常/接续/经验复用均通过，证据见 ACCEPTANCE。

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
| I | morph-integration | gpt-6-astra / high | task_c465399ce327 | ctx_90a1c3ad0fa9 |

集成 terminal：`term_81b5bbf7-efd6-4285-8269-8e98919eb912`；worktree 从主线 `02f42c2` 建立。集成只合并、验收和少量胶水，领域问题退回原轨。

## 当前分轨证据

以下为 Worker 报告且精确提交已推送；不替代最终集成验收。

| 轨 | 当前提交 | 证据 / 剩余工作 |
|---|---|---|
| T0 | cdc8972 | 32 tests、strict；11 包/资源的分发配置及安装验证通过 |
| T1 | adca7f6 | 17 桥测试、真实本地官方 SDK/MCP；待集成 |
| H | 07636c1 | 46 tests、strict；只允许本地 stub，远端未运行 |
| P | 1c4e5e9 | 6 tests、strict；重复 builder 身份已修复，Worker 完成并释放 |
| T3T | a12d288 | 10 tests、strict；成功率/闲置衰减已返修 |
| T3M | 240aaf0 | 13 本轨 tests + 31 T0 tests、strict；真实任务采用由 T2 验证 |
| T2 | 33ed929 | 16 tests、strict；三次真实任务通过，共 43,166 tokens，费用未知 |
| T5 | 46aa58e | 9 tests、strict、Node 语法通过；真实 API 接入完成，浏览器 helper 不可用，交集成补验 |

P 最初 Task `task_509a8b88e115` / Dispatch `ctx_8e1f19911c90` 完成后在原 terminal 立即续接上述返修任务。最终 `worker-release` 回执为 `released` / `closed_agent_terminal`，输出归档 captured。

最终集成验收尚未完成。G0–G5 不标记整体通过；各证据维度见 ACCEPTANCE，领域返修仍留在原 Worker。
