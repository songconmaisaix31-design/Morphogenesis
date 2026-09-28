# FC 后继开发一页计划 — 2026-09-28

总控 codex/master-control；当前用户任务书优先。事实基线为集成树 `73e64cc70116ac658d85591d082c0684a4952c99`，评审范围 `348cf8d42719402a7a5fcc09595e5040f96fa5be..73e64cc70116ac658d85591d082c0684a4952c99`。本日接续原 Orca Run `run_e46ee274f7c9`，当前总控终端 `term_f20e387c-dcb7-4bd1-97d7-bf6a5b446b9f`，generation 3。

## 三条互斥轨道

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
