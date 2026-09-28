# FC 后继开发一页计划 — 2026-09-28

## 2026-09-28 最新状态更新（当前有效）

权属已更新：主控只派发验收，治理文档由 Worker 独占；最新有效状态置顶，旧 10:56/11:00 状态
已被晚间授权替代。原文晚间误称 H4 在 morph-fc-docs-0928，现按已记录实际
morph-h4-docs-0928 修正。H4 真实 SHA 2957b40 已 rootff/push；T6 条件授权无需再问但
三锁缺口不能绕过。

T3 当前状态：22:11 第二次 mutation 删 breaker 转移仍绿（原生明确 The test still passes），
主控已按两轮失败协议停工；保存点 2d9d4304cfc0e1a3d4bfaeccb6ec5688aef60366 已
git push fix/fcd-interface-alignment；该提交实际缺 Swarm-Agent trailer（多行 shell 被截断），
不能改写公开历史。breaker 字节/ git diff 恢复为空。ctx_86b253aba968 已在 native 回 shell 后
abandon，task_1821ef01c94e blocked。门禁不通过、拒收不合并；22:40 裁撤规则保留但尚未到时
不能写已经触发。

FC-E 当前状态：修订稿 78c07459e14b4817c83c608c68978a07b68b5f9f 已由作者推送，
自行撤回 token high 推断；主控仍拒收，假绿清单继续声称 call_count/覆盖充分，
引用行号不匹配指定 73 源码；静态无高危意见不能据此补锁。
报告路径：morph-fc-e/artifacts/ai-evidence/review-0928-integration-qwen-fallback.md；
初稿 SHA：2180e0223fac39c5213c4a04474a8082e291bf7c；
修订稿 SHA：78c07459e14b4817c83c608c68978a07b68b5f9f；
拒收原因：high 声称 token 竞态无具体失败交错、假绿评价错误、同源标签不够、
commit 缺 Swarm-Agent trailer、引用行号不匹配指定 73 源码。
两提交均缺 Swarm-Agent trailer，不允许重写已推历史。人类已被问是否授权一次仅证据校正的返修；
未答复。ctx_925755d7dd00 原生已回 shell 后 abandon，task_fbbababc2840 blocked，
禁止重启它或代做评审。

Budget A/B 和 H1 人工结论、签字仍未收到；不签字、不替换生产 TODO、不代得出人类结论。
H3 Schema draft.2 待拍板。T6 merge/tag/smoke 全部 NOT_RUN。

| 轨道 | Worktree / Branch | 独占写权 | 今晚验收 |
|---|---|---|---|
| T3 / qwen-code | morph-fc-integration-0927 / fix/fcd-interface-alignment | tests/swarm/**、tests/fixtures/fault_injection/** | Worker._process 真实入口、assert 在 try 外、executor mock call_count；mutation 语义红并按字节恢复；全量+strict；commit+push |
| H4 / qwen-code | morph-h4-docs-0928 / songconmaisaix31-design/morph-h4-docs-0928 | README.md | 中文错误原文只在第一代主线 README:31，故从 f3feb7f 隔离新文档任务；τ=86400、动态指数衰减、半衰期约16.6h；只文档；commit+push |
| E 降级 / 独立 qwen-code 新会话 | morph-fc-e / fc/review-only | artifacts/ai-evidence/review-0928-integration-qwen-fallback.md | 精确 348cf8d..73e64cc；五不变量、转移表、假绿；标明同源降级；有行号、严重度、复现/验证边界；commit+push |

22:40 若 T3 未完成，保持 fix 分支不进入今晚冻结候选，登记 demo-build.1 首个 bump；
它不再单独阻塞生产基线，但不得用此规则忽略生产高危、预算人工结论、breaker 人工签字
或最新冻结候选的其他门禁。T6 条件满足后按本次用户授权执行，无需重复索要合并/tag许可。
①预算 A/B 结论与④breaker签字属于人类专属；AI只备材料，不代签或冒充人类复核。
T9 今晚不产生；T10 明日 acceptance 后、彩排前完成；benchmark 的独立轮询常量修复
登记明日，不纳入今晚基线。T8 新增审计确认事件计数，随 H3 一起批准，不自动冻结。

总控 codex/master-control；当前用户任务书优先。事实基线为集成树 `73e64cc70116ac658d85591d082c0684a4952c99`，评审范围 `348cf8d42719402a7a5fcc09595e5040f96fa5be..73e64cc70116ac658d85591d082c0684a4952c99`。本日接续原 Orca Run `run_e46ee274f7c9`，当前总控终端 `term_f20e387c-dcb7-4bd1-97d7-bf6a5b446b9f`，generation 3。

## 三条互斥轨道（上午历史计划，已被上方当前有效状态替代）

| 轨 / Owner | Worktree / Branch | write_paths | 本日任务与验收 |
|---|---|---|---|
| 文档 / qwen-code | `morph-fc-docs-0928` / `songconmaisaix31-design/morph-fc-docs-0928` | `artifacts/ai-evidence/fcr-hallucination-case-0928.md`；H4 后才授权精确两处文档 | 先 T2 单页事实案例；T1 等 H4；T7 只读分析交总控登记 TASKS，不直接写台账 |
| 测试 / qwen-code（接续 FC-D） | 原 `morph-fc-integration-0927` / 新 `fix/fcd-interface-alignment` | `tests/swarm/**`, `tests/fixtures/fault_injection/**` | T3 对齐真实接口；本地全量、strict、单行 mutation 变红并恢复；生产缺陷立即停手上报 |
| 异构评审 / deepseek-r1 | 原 `morph-fc-e` / `fc/review-only` | `artifacts/ai-evidence/review-0928-integration.md` | FC-E 精确集成 diff；五不变量逐条、有证据的风险和假绿测试；11:00 前报告 |

总控独占 `TASKS.md`、本计划、`docs/FC_HUMAN_REVIEW_0928.md`、`docs/FC_LOG_SCHEMA_DRAFT_0928.md`，负责 T4/T5/T8/T11 材料和验收。不改业务代码。临时派发材料仅入 Git 忽略的 `.runtime/fc-0928/`。所有阶段 Conventional Commit + `Swarm-Agent: codex/master-control` 或 Worker 真实物种 trailer，最终 push。

## 顺序与人类门禁

T2/T3/FC-E 即时并行；T1 等明确 H4。T5 10:30 前准备矩阵、fencing 摘录、六点清单和 FC-E 意见槽。H1 11:00–11:30 人类复核；H2 12:15 提醒、12:30 人类报名。T7/T8 下午准备；H3 16:00–17:30 人类 Schema 决策。T9 只在冻结后生成 mock 和消息草稿，队长发送。T10 为 B 类演练代码，先准备方案与写权，未获队长确认不实施；与 T3 测试写权串行交接。T11 睡前只检查状态与准备命令。

T6 三锁：最新完整门禁绿、FC-E 无高危、人类 breaker 签字；此外执行 merge/tag 前要有 B 类队长授权。任一缺失则不合回 decentralized-swarm、不打 demo-build、不宣称冻结。当前 TODO-HUMAN-REVIEW 标记保留，不代签。

## 接手证据与停止规则

根工作树 `codex/morphogenesis-mainline@f3feb7f` 有既有 `docs/SWARM_SOL_PLAN.md` WIP，只读保留。施工基座 `decentralized-swarm@ee5d606` clean、ahead 2；集成树 `73e64cc` clean。FC-E 原报告文件不存在，原 dsh 已回 shell；此前报告未达标。FC-D 现有 14 项含占位 subprocess 测试和吞异常路径；698 全绿是昨夜记录，非今日验收。

五不变量、AGENTS.md、docs/SWARM_*.md、锁文件只读。已知旧缺陷在授权 T3 范围内修测试；新生产缺陷、接口幻觉、疑似不变量违反、FC-E 高危、门禁红两轮以上、写权越界一律停止相关工作，按“现象/证据/建议/队长决策”上报。contract_local/interface_live/task_live 分列；SIMULATED/drill 日志不混入 live；未知 usage/cost 不填 0、不自动重试。
