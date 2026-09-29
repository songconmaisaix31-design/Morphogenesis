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


## 2026-09-30 G 当前执行状态（覆盖上文阶段状态，保留原文）

以上 4373 bytes 逐字导入 [C 的精确计划](https://github.com/songconmaisaix31-design/Morphogenesis/blob/1d7753957a982f1f67f29ffa02e8f064d4f67a41/docs/FC_PRODUCTION_PLAN_0929.md)；其中相对预检链接在 C 树解析，治理树请用 [C 的精确预检](https://github.com/songconmaisaix31-design/Morphogenesis/blob/1d7753957a982f1f67f29ffa02e8f064d4f67a41/docs/FC_RELEASE_PREFLIGHT_0929.md#L87)。未合入 A/B/C 源码历史，本治理树不是产品共同候选。

A `cb0902395d4e1fa89390c67c1cdfb6cec1607b72`、B `cbec0b31fc1e27bfee1b83bd84e1f34097c19a19`、C `1d7753957a982f1f67f29ffa02e8f064d4f67a41` 已交付/release；H3 `be4fb7a685e951c9e42d8dc0c7eeb900cb5518f1` 已正式冻结 1.0.0。I 固定 `morph-fc-production-integration-0929`，task `task_ee23e2bde40a` / 当前 Dispatch `ctx_af144abe21c7`，正在基于 be4 合精确 A+B+C；共同 SHA 与独立原门禁仍待回执。前次 Orca 重启 failed/terminal_missing 保留，不算产品门禁失败或通过。

G / codex 固定本树同名分支，task `task_a41bf1f2df89` / `ctx_94e98c11eb94`；写权仅 TASKS 本轮追加、本文、FC_RELEASE_PLAN 当前状态追加、新 fc-production-status 索引，以及收到后原字节 fc-production-integration-0929* 报告；桌面唯一 0929 Markdown 只追加。先提交 checkpoint，收到 I 报告后核 raw/实际 Git 身份再最终提交；不写业务代码、不自评、不代签、不合公共主线/tag。

用户已授权多 Agent 生产接线、合并/tag/三连/live；不是重新索取这些授权。执行仍须共同候选适用门禁、合格 FC-E 与 H1 三锁齐备；当前不可发布，G 不动公共主线/tag、不代签。主控已异步收取缺项，“继续任务”没有补齐本人结论、认证、live 目标/预算或 auto 路径选择。现有单任务 `orchestration.acceptance` 固定 Codex 样例，无 EvoMap/真实课题入口，exit0 可能仍 pending_review；不能冒充完整 live。未审计的计数不填0，未知实际 usage/费用保留 null/unknown。T9 GUI mock/队友消息、benchmark POLL_MS 及候选外 WIP 本轮未做。

门禁分层及逐任务 SHA 见 [一页证据索引](../artifacts/ai-evidence/fc-production-status-0929.md) 与 [TASKS 本轮区](../TASKS.md)。


## 2026-09-30 I正式交付后最终状态（G）

主控已验收并release I（msg_367334489d47）。共同代码固定 `morph-fc-production-integration-0929@8c76af727cf8a669c0b22b65586c2a0a70577e72`；H3+A+B+C精确普通合并，没有领域胶水或测后文档提交。G治理checkpoint为e862e4ca08f1331246596db47f3abcdaa96e0ee7，本页所属新治理提交不是受测代码。

I同SHA六门禁新执行：focused452/2warnings/837.19s、full899/2warnings/600.17s、strict89、新sdist+wheel、SDK1.14.0、独立安装分发13包+Node，均exit0；47独立P0、Schema原12/扩展24/controls13、12mutation红1恢复0，源码/安装包六阶段各21合法mock行，5 unknown holds保留。首轮focused6fail/full1fail、两次依赖下载-1、离线准备exit2及配置读码exit1等全部保留；Owner自验没有换标签成I实跑。

最终SHA离线FC-E包748088 bytes/40维、native dump七检查已备，模型请求0、正式review NOT_RUN。H3 是 David / 2026-09-29 / Schema 1.0.0 已冻结事实，不能推导 H1；最终 `8c76af727cf8a669c0b22b65586c2a0a70577e72` 的 breaker TODO 仍在202/592/672，H1本人预算A/B、breaker六点结论、姓名/时间/署名及完整受审SHA仍缺，历史73e64/C552签字槽不冒充最终签字。正式FC-E固定原生dsh / DeepSeek-V41-Flash，标准profile/认证缺失，**review NOT_RUN / FC-E OPEN**；离线40维要求与config检查不等于模型覆盖或无高危，实际返回模型/usage/cost=null。用户已授权合并/tag/三连/live，但尚缺H1、合格FC-E及live目标/实际模型/安全配置入口/累计预算和入口选择；主控已收取，G不新增审批流程或代签。

auto入口在 `orchestration/rehearsal.py:306–310` tokens已知/cost未知时仍返回并在346行执行recovery，auto live保持BLOCKED，未获路径选择前不启动。现有单任务orchestration.acceptance固定Codex样例，无EvoMap/真实课题入口，exit0仍可能pending_review；不能替代真实三连。unknown holds不释放、未知usage/费用不伪0，未审计计数不填0；日志是尽力旁路，崩溃/IO可能缺行，序号不等于请求数或审计问题数。公共主线合并、tag、正式FC-E调用、live三连、真实课题/现场/浏览器验收均NOT_RUN，interface_live/task_live未通过；T9 GUI mock/队友消息、benchmark POLL_MS及候选外WIP本轮未做。

G已原字节接收I正式报告并同步TASKS/桌面；写权不扩大，不写产品、测试、Schema、TODO或人签槽，不动公共主线/tag。主线仍 `be4fb7a685e951c9e42d8dc0c7eeb900cb5518f1`，新demo-build tag未创建；第一代root的既有WIP按I报告保留，不称全仓clean。入口：[一页状态](../artifacts/ai-evidence/fc-production-status-0929.md)、[I原字节正式报告](../artifacts/ai-evidence/fc-production-integration-0929-report.md)。
