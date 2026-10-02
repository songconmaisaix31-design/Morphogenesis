# Research Swarm Alpha R1 一页开发计划（2026-10-03）

事实源：`docs/source/Morphogenesis_Research_Swarm_Spec_v1.0_2026-10-02.md`。用户已授权开发、Orca 派发、测试、commit/push；旧包冲突条款以本 Spec 及本计划为准。旧冻结源码/报告和首失败原样保留。

基线：核心报告 `326fd8f633c7db72d4fab216a10a77b63aafe59d`（源码 `7062a632b8c625c05b35bdec4c36fce63a31c2a4`）；产品 `78370ad68dcc78d26b880854aedabac2e5ab797e`（完整受测源码 `a25aa40bb0f5259799641fee378d09ccc5887054`）。主线有 WIP，保持不动。

| 长期轨 | 单 Worker / Orca worktree / 分支后缀 | 独占 write_paths | FR / AT |
|---|---|---|---|
| A 共同研究与正式 MCP | OpenCode / morph-r1-research-1003 / 同名 | `swarm/research/**`（除 case.py、feedback*.py、policy*.py）；`tests/research/**`（除 test_generated*.py、test_research_policy*.py）；`docs/tracks/r1-research.md` | FR01-11,25-28；AT01-04,09,14-15 |
| B 动态候选、隔离、评价与继承 | OpenCode / morph-r1-experiments-1003 / 同名 | `orchestration/experiments/**`, `local_assets/**`, `swarm/research/case.py`, `tests/experiments/**`, `tests/local_assets/**`, `tests/research/test_generated*.py`, `docs/tracks/r1-experiments.md`, 核心 `pyproject.toml`/`poetry.lock`/`THIRD_PARTY_NOTICES.md`（依赖必要时） | FR15-20,26；AT05-07,12-15,17-18 |
| C 贡献与研究路线政策 | OpenCode / morph-r1-policy-1003 / 同名 | `swarm/router.py`, `swarm/pheromone.py`, `swarm/feedback.py`, `swarm/worker_loop.py`, `swarm/research/feedback*.py`, `swarm/research/policy*.py`, `tests/swarm/**`, `tests/research/test_research_policy*.py`, `docs/tracks/r1-policy.md` | FR12-14,24；AT08-11,14-15 |
| P 产品入口与三页 | OpenCode / research-r1-product-1003 / 同名，私库 | 私库全部产品源码/前端/测试/依赖锁/README/第三方说明和 `docs/tracks/r1-product.md`；排除治理文件与 Spec | FR01-05,09-11,20-28；AT01-02,04,09,14-18 |
| I 最后独立集成（轨道完成后派） | Codex / 核心 morph-r1-integration-1003；产品由独立安装验收使用 P 最终源码 | exact merge、`tests/integration/**`, `docs/tracks/r1-integration.md`，少量导入/配置/类型/路由胶水；领域问题退原 Worker | 全部 AT 的适用 L0/L1；L2 单列 |

主控只写治理：AGENTS、docs/PLAN、docs/R1_PLAN、docs/STATUS、docs/DECISIONS、docs/ACCEPTANCE、docs/source 指针及用户 Spec 存档；不写业务代码。每轨固定同一 Agent/worktree/branch，开发、测试、返修和文档持续由原所有者负责。跨轨发 Handoff，禁止修改他轨文件。采用普通精确 SHA merge，无 cherry-pick/force push。

顺序：并行 A(M1)、B(M2)、C(M3 契约/离线)、P(M4 输入与 UI) → A 接 B/C 新契约，原 Worker 测试 → 独立 I 合并核心并验证/安装/构建 → P 固定最终核心 SHA/锁并完成 HTTP/MCP/三页 → I 复核产品固定组合/历史保护/导出。M3 只接受可信评价事件；不把 LLM 意见或崩溃当反证。旧 v0/v0.1、两类固定案例、literal-files-v1 不改语义。

复用唯一 TaskLedger/lease/fencing/BudgetLedger/native/Executor/资产消费采用链；不新增调度器或完成证明。研究表仅描述语义，未知效果不重放，费用未知为 null。候选不在宿主执行；隔离能力未验证则拒绝执行。资源/数据/模型/费用 envelope 不随新 branch/run 重置。

本轮可执行：开发 Agent、确定性与安装/真实本机 HTTP/MCP/页面测试；模型科研调用、真实沙箱资源与隔离探针、论文外发、GPU/云后端、发布未获运行级授权，不执行。L2 所需研究题/容差/批准环境/账户/预算/数据外发仍需具体授权；建议默认不能变成已批准额度。

验收：每轨先交 FR→源码→契约→AT 映射、最小 API Handoff，再源码+适用测试+报告 commit/push 精确 SHA；保留首 RED、NOT_RUN、既有类型错误身份。I 验证最终核心/产品源码、wheel 安装、pytest、新增边界 strict、前端构建/两视窗真实 HTTP 页面、兼容案例/检查器、幂等与中断。AT07/L2/L3/人工观察未执行时明确列出，不宣称 R1 PASS。
