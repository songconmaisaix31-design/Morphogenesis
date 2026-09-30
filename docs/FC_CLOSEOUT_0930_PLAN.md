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

### Phase 2 D 实际过程（原 Dispatch `ctx_52f16a4a4b06`）

- D 计划阶段 `4ab0b2e` 已 commit/push，保留先前计划 WIP。实际 preamble 能力用于 CLI，已有 heartbeat/status receipt；不沿用此前基于隐藏 dispatch-show 推测的能力缺失结论。
- 首次 focused 在 collection 前 exit 1（`.venv` 缺 pytest），保留原始日志；按总控接续授权完成独立锁环境 `uv tool run poetry install --no-interaction` 与 `npm ci --ignore-scripts --no-audit --no-fund`，均 exit 0，依赖声明/锁不改。运行时/SDK 不用 Mock 代替。
- 显式 OfflineExecutor 复用 fixture 输入验证及真实物化、本地 ProviderAdapter 分类；无动态 Mock.bound/execute 覆盖，真实预算继续走 unbounded operator allowance，usage/cost 未观测、hold 保留。strict 已实际 exit 0（89 source files）。
- 唯一六阶段离线 CLI 实际 exit 0，Run `fault-drill-07e1cc4f9dfc4030a8261f208d1acd14`，21 条 FC 日志、5 个 unknown/uncertain hold 合计 1.0 USD，usage/cost=null，mock/SIMULATED；focused 完整结果仍待本轮实际退出，不预写最终通过。
- H1 附带独立读取：旧 `db283eaa1f1d71d36e7b8a3520aafbce5becf1dd` 资源 Git blob 与 H3 `be4fb7a685e951c9e42d8dc0c7eeb900cb5518f1` 文档唯一 fence（96–1913）的 JSON 内容/精确内容字节相等，38,309 bytes；当前 importlib 资源 bytes 为 40,124，仅 LF→CRLF checkout 转换，原 bytes 不等仍明列。H3 当时无打包资源（cat-file exit 128）；首次错误计入 fence 分隔 LF/断言 checkout 与 blob 原字节相同的比较 exit 1 原样保留，清晰提取内容后的对照 exit 0，不改 Schema、不以 CI 合法性冒充冻结对照。
- 完整证据与命令见 [D 轨报告](tracks/fc-stable-drill-0930.md)，忽略产物 `.runtime/fc-stable-drill-0930/`，运行状态 OS TEMP。新源码不继承旧 H1 签字；R/I 独立验收、全量/build/SDK/分发及模型/Hub/Live/部署均不由此条放行。

### Phase 2 D focused 实际失败与代码阶段交付

- D 实现提交 `0ad1a0d06f88197c70e8909d505a6db261d2aee0`，仅修改两个自有代码/测试文件，`Swarm-Agent: codex`；strict/唯一 CLI exit 0，未改预算、fencing、breaker、Schema 或依赖锁。
- 指定 focused 实际 exit **1：42 passed / 1 failed / 797.77s**。D 16 个 drill case 无失败；唯一失败为只读 `test_fc_logging.py::test_concurrent_append_and_partial_tail_preserve_facts` 的 SQLite 50 ms 写锁等待（`fc_logging.py:142` → `task_ledger.py:47 BEGIN IMMEDIATE`，`database is locked`）。原失败完整保留，未以绿色子集冒充整套通过。
- 有界只读诊断确认写锁覆盖日志 append/flush/fsync，相关实现及测试在指定基线上未改；不能仅凭 traceback 断定机器负载原因。已经真实 CLI escalation/ask 交总控决定同源码/同门禁的受限串行复验或他轨修复；D 无该路径写权，不改变 50 ms 超时、断言、线程数或 mock 持久化。

### Phase 2 D 最终处置（不覆盖历史失败）

- 总控曾有条件批准 D 固定相同实现 SHA、等 R 回归退出后做一次原两文件串行复验。D 固定/推送 `0ad1a0d` 后持续等明确准入；首次测试时 HEAD 为计划提交、源码未提交，报告如实区分事后固定提交与当时 HEAD。
- 16:35（UTC+8）D 实际收到 `msg_7b345a26cc5b`：总控因 R 回归与日志节点诊断重复锁失败而撤销尚未开始的 D 复验。D 串行复验 **NOT_RUN（零次启动，授权撤销）**；共同 focused gate 仍为 **exit 1 / 42 passed / 1 failed**。日志域后续交原 Owner，不修改超时/测试/持久化绕过。总控交接的 R 结果不是 D 代验事实。
- D 开发阶段已交付显式 adapter，Owner strict/唯一 mock CLI exit 0；Schema 附带字节证据仅针对旧 db283ea，并保留首次比较错误与当前 CRLF 原 bytes 不等。最终文档归档后按真实原 Dispatch `worker_done --outcome failed` 结算，再 idle；实现交付与任务验收失败是两个事实。I/全量/build/SDK 专项/分发/新 CI、新签字及模型/Hub/Live/部署仍 NOT_RUN，本条不冒写最终通过或放行 I。
