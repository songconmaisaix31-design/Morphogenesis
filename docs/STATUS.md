# 开发状态

## 本轮结果：三次完整软件彩排已通过

收尾复核：主线 `c1542b2` 的 Windows/Ubuntu CI 35691937011 均 success，但较早候选 `e83a816` 的 Windows CI 35691719303 暴露 `tests/t2/test_rehearsal.py:81` 的时间竞态；后续偶然通过不消除该问题。原 R/I 会话通过 Orca terminal 内 `codex resume --last` 恢复到原 worktree/branch，任务分别为 `task_78d3e30ecafd / ctx_76c264a284f2`、`task_0abdacc8d0ba / ctx_44c3b8728ee5`。恢复时 CLI 使用受限沙箱，Orca 通信与共享 Git 元数据访问需确认；当前仅授权范围内准备返修，未将新修改宣称为已验证或推送。

2026-09-22 用户新增固定演示全链和至少三次完整彩排，旧三次单任务证据不计入本轮。主线已接收并验收集成 `e83a8168a066a0c687a15a7d28c15739bab13ad6`。北京时间 13:23–13:30 顺序完成 manual / auto / auto，共 6 次真实 CLI / 87,133 tokens，费用未知。每轮两个新任务 3/3、下线改道、Gene 生成/采用/墙钟衰减/归档全部通过。Orca Run `run_2cdbc98915f7`，协调 terminal 沿用原身份。

| 轨 | worktree / branch 后缀 | 实际模型 | Task / Dispatch | terminal |
|---|---|---|---|---|
| R | morph-rehearsal-runtime | gpt-6-astra / xhigh | task_3ca8b0ded0ae / ctx_bee3929001e7 | term_1fa7a0dc-6e17-4c96-9835-0428cf455e07 |
| V | morph-rehearsal-viz | gpt-5.6-terra / high | task_d91042ca5a85 / ctx_e028b3a23be7 | term_ffa1e302-b8ed-43c0-bae6-fcc662233d0c |
| I | morph-rehearsal-integration | gpt-6-astra / high | task_6bf332fa1437 / ctx_0887e4fb6588 | term_1eee9d49-ded9-441b-b7c8-406b5692b797 |

R/V worktree 从 `791d3cf` 建立；最终领域提交为 R `652e3199d626f60b414b70ee523b5f9703d1e539`、V `80220c5481e64fa197a679a7ec2ea466b6306af6`，集成 I 从 `501c491` 建立，最终为 `e83a8168a066a0c687a15a7d28c15739bab13ad6`。全部 commit + push，三个模型均经 effective 回执确认。主 Agent 只合入候选和维护治理文档，所有显示/类型返修都由原 V 完成。

158 tests、全包 strict 52 文件、SDK、构建与安装后资源检查通过；三轮实时双视口截图和最终 UI 明确 replay 的实际绘制边界检查通过。最终显示修复没有重复模型调用或替换旧 live 图片，证据边界见 [本轮集成报告](tracks/rehearsal-integration.md)。用户补充模型提供方与清单后，约 14:12 完成 EvoMap Gateway `https://api.evomap.ai/v1` 的鉴权和 Luna 一次真实短文本测试：均 HTTP 200，返回 OK / 15 tokens / 4813 ms。模型目录共十项，含额外的 Terra；完整 ID 与证据边界见 ACCEPTANCE。凭据未进入代码、命令参数、验收记录或 Worker prompt；尚未改演示执行器，物理投影接线仍 NOT_RUN。

第一轮 R、V、I 均已 worker_done / succeeded；三个 worker-release 均返回 released / closed_agent_terminal，transcript captured。三个无任务启动 PowerShell 已单独核对关闭。集成自有 7520–7524 服务和临时页面已清理，独立浏览器均正常关闭。原 7525 服务实际随 I 的 release 退出，原先“独立隐藏进程可保留”的判断已被否定。协调者已重新启动 [7525 只读回放](http://127.0.0.1:7525/)，核验 launcher 65808 → listener 57100，HTTP 200、mode/provenance=replay、current.stage=completed、task_live=not_run；日志位于 `%TEMP%/morph-replay-coordinator-983d9f27fa08480a9c1836c25c9dbb64/`。这不是新 live，也不承诺跨 Orca/系统退出常驻；端口空闲后按报告中的 replay 命令重启。原始 TEMP 证据、分支和 worktree 保留。

## 已完成的核心原型基线

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
