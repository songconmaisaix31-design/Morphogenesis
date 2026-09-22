# 开发状态

八个功能轨及一个独立集成轨已交付核心原型。通过 Orca CLI 多开，按难度分配 Astra / Terra / Luna；领域返修仍由原 Worker 完成。主 Agent 只维护计划、状态、决策与验收，接收集成结果，不写业务代码。

- 主线：`codex/morphogenesis-mainline`，已接收集成候选 `b6bb49c3112a12f3c0bdcddbddbf2dde453be2e6`，最终状态/验收记录随主线提交推送。
- 初始仓库 `117fdde` 仅 LICENSE；用户 ZIP 原文在 `docs/source/`，保留 Apache-2.0。
- 功能：LangGraph 执行/独立复核/接续；反馈拓扑选路；经验正文注入、采用、衰减和本地归档；官方 GEP SDK/MCP 桥；受控本地 Hub 适配；ECharts 实际事件展示。
- 最终验证：149 tests、50 文件 strict、sdist/wheel 与 11 包安装检查、真实 Chromium 页面检查通过；Windows / Ubuntu CI 见 [验收矩阵](ACCEPTANCE.md)。
- 三次真实模型任务通过：正常/接续/复用，3 次 CLI / 43,166 tokens，费用未知。远端 Hub、动态供给、硬单次模型费用上限与正式现场演示仍有限制，不能宣称 G0–G5 整体通过。

## 分轨提交与身份

worktree 根目录 `C:/Users/DW/orca/workspaces/Morphogenesis/`；以下后缀同时是目录名和分支后缀，分支前缀为 `songconmaisaix31-design/`。所有精确领域提交已合入并推送，历史保留。

| 轨 | worktree / branch 后缀 | 实际模型 | 最终领域提交 |
|---|---|---|---|
| T0 地基 | morph-t0-foundation | gpt-6-astra（继承） | cdc8972ba0a711cb3b06bd36bdea516807430a8e |
| T1 协议桥 | morph-t1-adapters | gpt-6-astra（继承） | adca7f69183669f70135ead9e043aa5b70a8b876 |
| H Hub | morph-hub | gpt-6-astra / high | 07636c17f95a24dd0fbd37dbdf050cb6a26ca496 |
| P 供给 | morph-provision | gpt-5.6-luna / high | 1c4e5e9013ef08bbb50cbf20c11eb0119960c42e |
| T2 执行 | morph-t2-runtime | gpt-6-astra / xhigh | 33ed929d2065db8a00d46f679d27ba09d950d13a |
| T3T 拓扑 | morph-t3-topology | gpt-5.6-terra / high | a12d288a6505c1c098d85cbfd231a708e9b59342 |
| T3M 代谢 | morph-t3-metabolism | gpt-6-astra / high | 240aaf0f985ec3d374e07a25b3969650698d0aee |
| T5 展示 | morph-t5-viz | gpt-5.6-terra / high | 9ae01cf6428d04ed365ad778f4b3436d35d536ba |
| I 集成 | morph-integration | gpt-6-astra / high | b6bb49c3112a12f3c0bdcddbddbf2dde453be2e6 |

Orca Run：`run_3cac02602e7c`；协调 terminal：`term_263319ac-dfa1-4ff3-8463-7fe200fad470`。

| 轨 | Task | Dispatch |
|---|---|---|
| T0 | task_3bdb79633de5 | ctx_177ee63228f3 |
| T1 | task_b92657a452bc | ctx_c6e4d813fcc6 |
| T2 | task_c03f393208dd | ctx_0f54173a063d |
| T3T | task_9c35a6fd3bee | ctx_ed1ee9f3817e |
| T3M | task_beb94df50bac | ctx_31f926047197 |
| T5 | task_f37cacf4910a | ctx_101b31af0af0 |
| H | task_89da8e623a87 | ctx_a2be7a533175 |
| P | task_9ae1f6f71a6d | ctx_a408002966fe |
| I | task_c465399ce327 | ctx_90a1c3ad0fa9 |

P 最初 Task `task_509a8b88e115` / Dispatch `ctx_8e1f19911c90` 在原 terminal 立即续接返修，最终以表内 dispatch 结束。集成 terminal 为 `term_81b5bbf7-efd6-4285-8269-8e98919eb912`。

## 结束与资源处置

九个最终 Worker 均已发送 worker_done / succeeded。P、H、T2、T3T、T3M、T5、I 的 worker-release 均返回 released / closed_agent_terminal，输出归档 captured。T0 / T1 的 worker-release 返回 retained / external_terminal / processAction=none；这是 Orca 的外部 terminal 所有权限制，未绕过该限制强关。

T5 与集成 Worker 已逐一核对并清理自有预览进程；协调者复查 7500 / 7501 / 7502 / 7510 均无监听。浏览器截图及本地日志保留。

未重启 Orca 或操作其他项目进程；Git 分支、worktree、原始真实任务和本地验收产物保留。集成没有新增模型调用或外部 Hub 发布。详细命令、早期失败与修复及证据边界见 [集成报告](tracks/integration.md)。
