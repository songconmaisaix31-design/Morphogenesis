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

## 执行记录

- 治理提交 `37e7a6a` 已 push 到 `decentralized-swarm`（本计划）。
- Orca Run `run_5b66cce8b4b8`，协调终端 `term_0ffa0ad8-e93a-4385-b585-406317e51d44`。
- A 轨 Task `task_6c89f26607bb`：`worker-start --agent codex` 两次在 `agent_readiness`/`terminal_readying` 未完成（Orca 无法把已启动的 codex TUI 识别为受管 agent，与既往 `agent_unconfigured` 同类）。已 `worker-release` 首个失败 dispatch `ctx_66c1d6028d2c`、`worker-abandon` 卡住的 `ctx_b42ea51d24a3`，保留 codex 终端 `term_89e6fed4-f946-4660-9439-d259c2a3065b`，通过 `terminal send`（accepted / turn_started）直接投递任务书。记 unsupervised，验收以 git 提交 + 双平台 CI 为准，不以 worker_done 冒充。
- A 工作树 `morph-fc-closeout-fix-0930`，基线 `8c76af7`，分支 `songconmaisaix31-design/morph-fc-closeout-fix-0930`，codex 有效模型 GPT-6-Astra xhigh（终端回显）。codex 账户周额度告警（剩约 2%），已记录为运行风险，不自动换模型/充值。
- A 交付（自验回执）：CI 修复 `f0add30`（`test_fc_logging.py` 改读打包 `orchestration/fc_log_schema.json`，去 `git show be4fb7a`；聚焦 27 passed，`grep 'git show'` 无残留）；性能修复 `db283ea`（`fault_observations.py` 崩溃可恢复持久索引，append 不再全文件重扫；聚焦 101 passed）。strict 89 文件 exit 0，全量 **910 passed / 2 warnings / exit 0（619.88s）**，边界检查（仅 3 授权文件、冻结 Schema blob 不变、双 trailer、clean）通过。已 push，远端 `db283eaa1f1d71d36e7b8a3520aafbce5becf1dd`。
- **A 验收通过**：主控独立核对 diff 恰为 3 文件、`orchestration/fc_log_schema.json` 字节不变；CI run `36615184218` **双平台 success**（Ubuntu 6m / Windows ~29m，pytest 910 全绿 + build/SDK/分发）。**新固定 SHA = `db283eaa1f1d71d36e7b8a3520aafbce5becf1dd`**（受限 FC 入口已打通：CI 绿 + 六阶段 drill + 五不变量 + cost_state 一致 + 结果可判定）。
- **H1 人工签字归档**：David 2026.9.30 12:31 有条件接收（场景 A/B 结论「两者都不是/证据不足」+ breaker 六点 + 材料修正），见 `docs/FC_HUMAN_REVIEW_0930.md`。
- **DSH 评审归档**：一次真实 `dsh --profile headless`（deepseek-flash）62s，推理流实质评审了 inv1–5/repair1–5/fencing/budget_ab/false_green1–6/limitations；但 exit 1、输出预算耗尽，未产出结构化 fact/hypothesis 且 16 矩阵未覆盖。按用户确认以推理流为评审实质归档，如实标注「非合格正式评审」，见 `artifacts/ai-evidence/review-0930-dsh-report.md`。
- **主线合并**：`git merge --no-ff db283ea` → `86ade3d`（父 `86b1830` 治理 + `db283ea` 代码），`merge-tree` 无冲突，合并后 `swarm/orchestration/tests` 及共享文档/配置与 db283ea 字节一致，治理文件保留。已 push。
- **三态验收**：`contract_local` = **passed**（合并 SHA 代码与 db283ea 字节一致，CI run `36670085486` 双平台 success：pytest 910 + strict + build/SDK/分发）；`interface_live` = **not_run**（无 live 网关请求，fault_drill 为 mock/SIMULATED）；`task_live` = **not_run**（本轮无真实模型任务执行）。
- **Tag**：`git tag -a demo-build 86ade3d` → push；`ls-remote` 核 `refs/tags/demo-build = 77becf85`（peeled `86ade3d`），远端无既有同名 tag，未覆盖。
- **Phase 2（架构切稳定接口）未启动**：本轮未开展，作为后续项保留；perf（全历史扫描）已在本轮轨道 A 内完成。

## Phase 2 接续计划（2026-09-30，保留以上历史记录）

基线固定为 `7cc64e3eb0031a6b06b9482e95707de17dfe0885`。本轮使用 Codex `gpt-6.1-sol`，总控只分配、协调返修和验收；每轨一个 Agent、一个 worktree、一个分支。

| 轨 | Worktree / Branch | 独占 write_paths | 验收责任 |
|---|---|---|---|
| R | `morph-fc-stable-runtime-0930` / `songconmaisaix31-design/morph-fc-stable-runtime-0930` | `swarm/worker_loop.py`、`swarm/failure_chain.py`、`tests/swarm/test_failure_chain_boundaries.py`、`tests/swarm/test_failure_chain_runtime.py`、`docs/tracks/fc-stable-runtime-0930.md` | 现有运行时明确类型与模块边界；预算、租约、熔断行为保持；Owner focused/strict |
| D | `morph-fc-stable-drill-0930` / `songconmaisaix31-design/morph-fc-stable-drill-0930` | `demo/fault_drill.py`、`tests/swarm/test_fault_drill.py`、`docs/tracks/fc-stable-drill-0930.md`、本计划的 Phase 2 追加记录 | 显式离线 Executor 契约、真实 Worker 准入与六阶段模拟行为；独立归档旧候选与 H3 Schema 一致性；Owner focused/strict/离线 CLI |
| I | 两轨精确 SHA 交付后由总控派发 | 普通精确合并、`tests/integration/**`、必要配置/类型/导入胶水及集成报告 | 独立复验、全量测试、构建、SDK、分发；领域问题回原 Owner |

执行顺序：R/D 在互斥路径开发、各自阶段 commit/push → 总控核对 immutable SHA、remote、diff 和原始退出证据 → I 串行合并及独立检查。D 不预写 R/I 通过。跨轨变更只交 Handoff，不修改内核、冻结 Schema、锁文件、签字材料或他轨实现。

旧 A 的代码 `db283ea` 与 CI 交付事实，和旧 Orca Dispatch abandoned/失败的生命周期事实分列，不能把其中任何一个改写为另一个。此次 R/D 首次启动在 `agent_readiness` 超时；恢复派发后回收旧启动资源误关终端，两个工作树当时无 diff。`codex resume --last` 又继承了总控历史/cwd；总控随后明确更正 D 身份，所有 D 工具显式使用本 worktree。上述机械中断不证明业务失败，也不证明开发完成；实际接续与退出回执在本轨报告记录。

David 的 H1 有条件接收仅锚定原 `db283ea`；本轮源码变化不是原字节，也不自动继承新候选人工签字。DSH 原调用 exit 1，用户已选择接受推理流为评审实质，但它仍非合格结构化正式评审；不重试、不新增调用。`demo-build` 原 Tag 保留。离线入口始终 `provenance=mock` / `SIMULATED`；`interface_live`、`task_live`、Live/Hub/部署 NOT_RUN。本节是接续计划，不是冻结、发布或最终验收证明。
