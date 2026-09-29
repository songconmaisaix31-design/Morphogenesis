# FC 生产接线与发布前置一页计划 · 2026-09-29

本页登记最新用户授权及主控本轮 Dispatch，优先于历史两轨/五轨状态；不覆盖历史失败。共同代码起点 `c552250c0d07f5f70f09eb0a5ab3c322195e34ec`（C552）；本页不是候选验收或发布签字。主控只调度、收取状态、验收，不写业务代码；领域返修归原 Owner，阶段完成普通 commit + push，禁止 force push。

| 轨道 / Owner | 固定 worktree / branch / Dispatch | 独占 write_paths | 本阶段验收 / 接续 |
|---|---|---|---|
| A / codex 生产接线 | `morph-fc-log-wiring-0929` / 同名 / `ctx_06977a19eff5` | `orchestration/fc_logging.py`；可选纯冻结导出 `orchestration/fc_log_schema.json`；`orchestration/rehearsal.py`；`swarm/worker_loop.py`；`tests/swarm/test_fc_logging.py`；`tests/t2/test_rehearsal.py`；`docs/tracks/fc-log-wiring-0929.md` | 按 H3 冻结契约接线，行为/语义和适用测试，交付精确 SHA；接口请求经 Handoff |
| B / codex 故障演练 | `morph-fault-drill-0929` / `feat/fault-drill` / `ctx_fb4be01a9a4c` | **仅** `demo/fault_drill.py`、`tests/swarm/test_fault_drill.py` | 正常→拒绝→切换→B 读取 A 并避让→新 probe token→恢复六阶段；SIMULATED/mock；同 Owner 返修；历史 Qwen 认证失败不冒充本轮成果 |
| C / codex 发布前置、正式 FC-E 与 live 预检 | `morph-fc-release-preflight-0929` / 同名 / `ctx_6b976c62b96d` | 本页；`docs/FC_RELEASE_PREFLIGHT_0929.md` **只追加**；`artifacts/ai-evidence/fc-production-preflight-0929*`；`artifacts/ai-evidence/review-0929-release-v41flash-*`；临时/原始日志仅 OS TEMP 或 ignored `.runtime/fc-production-0929/` | 本阶段交付可运行 prepare/逐字 verifier、H1 最小待签清单、native dsh/真实入口预检；**模型和 Hub 请求为零**；材料完成即结算，正式调用须主控另交最终候选 SHA |
| I / 后续集成 Agent | A/B 完成后由主控指定单一 worktree / branch / Dispatch | 仅合并精确提交与必要少量导入/配置/类型/路由胶水；领域问题退原 Owner | 共同最终候选合入 H3+A+B 和必要材料，focused/full/strict/build/SDK/distribution；同 SHA 独立语义 mutation、Schema、六阶段与入口验收；正式 FC-E 与 H1 锁齐后才合入 `decentralized-swarm`，逐轮三连 smoke、tag、live |

三个当前轨道写权互斥，不为并行重构目录、不新增调度/预算/Attempt/Manifest/哈希系统、不派子 Agent；T0 锁和依赖文件只读。已有锁包可在本树环境安装，缺新依赖先上报。C 不改 TASKS、旧评审、Schema、产品/测试、AGENTS/SWARM、桌面或 H1 签字槽。

H3 最新事实为 `decentralized-swarm@be4fb7a685e951c9e42d8dc0c7eeb900cb5518f1`（parent `73798cd6f05210f2bd9b1eebfd6f9f0dd6e842db`）：David 于 2026-09-29 正式冻结 Schema 1.0.0，单文档提交，原 12/12 + 9 controls；这些是已有证据，不是 C 重跑。H3 不替代 H1：C552 breaker 三处 TODO 和预算 A/B、breaker 六点人签须逐项核实，不能从“签字目前h1”推定签名已齐。

FC-E 指定 **原生 dsh + DeepSeek V4.1 Flash**；只读复用治理 `40577cb841e8d89c08e1336d7254c4ca7bb3984e` 工具/旧失败，不把治理 HEAD 当共同代码。保留 fact 原 `file:line` 与逐字源码，不匹配整条 INVALID；hypothesis 待验证。覆盖五不变量、16 转移、五修复、六类假绿。最终 SHA 未到前不评旧 C552；后续授权一轮 invocation ≤10分钟、retry=0、有限输出、关闭非必要 tools/title/compaction，非 exactly-one-HTTP 限额，未知效果不重试。

live 目标/凭据入口/模型价格与跨三轮预算由主控收取，未答不视为批准；`run-demo.ps1` 的 repair/recovery 样例不替代真实课题。auto 三轮逐轮验收、失败即停，unknown 成本保留且不盲目续发；MaxCostUsd 不是上游硬账单上限。manual 若确有需求由人按 Enter。T9 样例/消息待后续，benchmark `POLL_MS` 风险及不在候选的 WIP 原样保留。

门禁红两轮、五不变量疑似违反、越写权立即上报；Owner 自测、独立验收、FC-E、人签、contract_local/interface_live/task_live 分列。最新证据、真实退出码、具体缺项见 [本轮追加预检](FC_RELEASE_PREFLIGHT_0929.md#9-本轮生产前置追加事实2026-09-29)。
