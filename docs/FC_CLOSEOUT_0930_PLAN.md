# FC 收口与受限 FC 入口打通 · 2026-09-30 一页计划

接手自原主控 `term_a6558643`。目标按用户指令收敛 FC 轮：修复 CI 历史依赖、打通预算一致且结果可判定的受限 FC 入口、固定新 SHA 后完成 DSH 与 H1、主线合并（`decentralized-swarm`）、三态验收与 `demo-build` Tag；性能优化先做全历史扫描，架构优化先切稳定接口，不推倒现有内核。

## 已核实的锚点

- 合并目标 `decentralized-swarm@be4fb7a`（H3 Schema 1.0.0 已冻结）。
- 完整 FC 代码顶点 `morph-fc-production-integration-0929@8c76af7`：包含 H3 冻结、C552 A/B、`fc_logging.py`/`fc_log_schema.json`、六阶段 `fault_drill.py`、cost_state 修复（`f2be388`）。`3d8bb85`/`318dd4f`/`4c3dc46`/`c552250`/`be4fb7a` 均为其祖先；`morph-closeout-integration-0929` 也已完全包含在内。
- `morph-readonly-app-0929@621f588`（C）与 FC 自 `605cf48` 分叉、前端冲突，本轮不强合前端，单独保留候选。
- **CI 红根因**：`tests/swarm/test_fc_logging.py` 用 `git show be4fb7a:docs/FC_LOG_SCHEMA_DRAFT_0928.md` 取冻结 fence，浅克隆（fetch-depth:1）下退出 128，双平台 pytest 全红。
- **全历史扫描**：`swarm/fault_observations.py` `append()` 每次 `read()` 全文件重扫（O(n²)），且持 SQLite 写事务。

## 轨道与独占写权

| 轨 | 基线 / 分支 | 独占 write_paths | 交付 |
|---|---|---|---|
| A 收口修复 | `morph-fc-production-integration-0929@8c76af7` → 新分支 | `tests/swarm/test_fc_logging.py`、`orchestration/fc_log_schema.json`、`swarm/fault_observations.py`、`tests/swarm/test_fault_observations.py` | 去 `git show` 历史依赖；append 去全历史扫描；focused/full/strict 绿 |
| I 独立集成 | A 精确 SHA → 候选 | 精确 no-ff 合并、必要胶水、`tests/integration/**` | focused/full/strict/build/SDK/分发 + 双平台 CI 绿，产「新固定 SHA」 |
| 主控 | `decentralized-swarm` 治理 | `docs/PLAN.md`/`STATUS.md`/`DECISIONS.md`/`ACCEPTANCE.md` 及本轮计划 | DSH 有界评审、H1 材料、主线合并、三态验收、Tag、perf/arch 验收 |

## 顺序与门禁

1. A 修复 → commit + push，双平台 CI 绿。
2. I 精确合并 A → 新固定 SHA，全量门禁绿。
3. 新 SHA 上 DSH 一次有界 `dsh --profile headless` 评审（`DEEPSEEK_API_KEY` 由用户提供，retry=0、有限输出）；H1 材料按新 SHA 重生成，用户亲签。
4. H1+DSH 齐后合入 `decentralized-swarm`（ff-only，漂移则 merge-tree 复核）。
5. 三态验收：`contract_local` 绿 / `interface_live` not_run / `task_live` not_run，如实记录。
6. `demo-build` 注解 tag → push → `ls-remote` 核 object+peeled commit，不覆盖。
7. Phase 2：架构优化切稳定接口（打包 schema、provider_adapters/base、breaker.transition、FaultObservationStore 稳定 API），不重写内核。

## 明确边界

不新增调度器/Attempt/Manifest/哈希系统；锁文件 T0/队长代理；DSH 一次调用、H1 用户亲签、三态无 live，均不伪造；每阶段 commit+push，禁 force push；第一代 `codex/morphogenesis-mainline` 及其未提交 `docs/SWARM_SOL_PLAN.md` 全程只读保留。

## 派发与验收记录

见下表随执行更新（Run / Task / Dispatch / 最终 SHA / 验证结果）。
