# R1 C 贡献与研究路线政策（research-v1）

**状态：三轴贡献与研究路线政策（research-v1）领域返修完成，新接口 strict + pytest 通过。** 这是独立于既有策略 v0/v0.1 的**新增**层；`swarm/router.py`、`swarm/feedback.py`、`swarm/pheromone.py`、`swarm/worker_loop.py`、`swarm/research/service.py`、`server.py`、`models.py` 的既有语义未被修改。L2 真实科研行动未获运行级授权，全部 **NOT_RUN**。

本轮返修（相对首版 71bfedb）修复验收阻断：贡献持久化接受入口改为从可信持久事实解析并绑定 host 自身审核身份，不再接受调用者 `ThreeAxisResult`/`reviewer` 字符串即奖励；`replace=True` 删除历史已移除，改为追加 supersession；`trusted_refutations` 只把 `purpose=counterexample` 的可信反例当反证；机会建议补齐 spec 七要素。

## 范围与不修改

本轨只写 `swarm/research/policy.py`（新增）、`swarm/research/feedback.py`（新增）、`tests/research/test_research_policy_v1.py`（新增）与本报告。不触碰 A 的 `swarm/research/service.py`/`server.py`/`models.py`/`HostConfig`，不触碰 B 的 `orchestration/experiments/**`/`local_assets/**`/`swarm/research/case.py`，不触碰 P 产品。跨轨接口只通过主控 Handoff。

- **v0/v0.1 原样保留**：`Router` 的 `strategy_version` 仍是 `Literal["v0","v0.1"]`（有测试断言 Router 拒绝 `research-v1`）。`trusted_facts`、`policy_diagnostics`、FC 投影、Worker 续租边界均未改动。
- **closed FC `RouteCandidate` 不放宽**：research-v1 的机会/理由只存在于 `RouteOpportunityPlan`，不新增 FC 路由候选字段，不改 `fc_log_schema.json` 的 `additionalProperties=false`。
- **复用而非新建**：复用 `TaskLedger`/`trusted_facts`/`ResearchObservation`/`Candidate`/`LocalAssetStore` 与标准 `result_id`/`report_id`/`task_id`/`actor(worker_id)`；不新增任务、执行、审计、Hash 或完成证明系统。贡献去重键是 `result_id` + `source_ref`，**不按 Agent 品牌**判断独立。
- **不建平行事实模型**：B 的动态三轴/候选模型在 `orchestration/experiments/generated.py`；本轨只做**政策层结果投影**（spec 5.2 的三轴结果模型），不重复 B 的候选/判据事实。B 安全 Handoff 后由本 Owner 提供薄转换或复用，不各自 pending 归 I。

## FR → 当前代码 → 新契约 → AT 映射

| FR | 旧代码现状 | 新契约（research-v1） | AT |
|---|---|---|---|
| FR-12 贡献与路线分离 | `trusted_facts` 只给正例三类奖励，无三轴 | `ThreeAxisResult(execution, hypothesis, contribution)` 三独立轴；`succeeded/refuted` 可 `accepted`，`crash/timeout/auth/unknown` 无科学条目；有效反证降低该路线未来机会但认可反证贡献 | AT-08, AT-10 |
| FR-13 投入调整 | 无版本化路线政策 | `RouteOpportunityPlan(version="research-v1", exploration_fraction, total_share=1.0)`；`apply_correction`（sleep/downgrade/reopen）追加不擦除；refuted 重开须 `new_condition_branch`；证据改变下一次可解释推荐，claim 仍由原 TaskLedger 权威 | AT-10, AT-11, AT-14 |
| FR-14 探索与多样性 | v0.1 任务级 softmax 保底 | `exploration_fraction`（默认 0.20）作为合法分支探索配额下限；dormant/refuted/archived/越权 `eligible=False` 无执行权；同 `result_id`/同 `source_ref` 去重，不因品牌重奖 | AT-09, AT-11, AT-14, AT-15 |
| FR-24 拓扑可解释 | 无分支机会视图 | `RouteOpportunity.factors`（evidence/insufficient_evidence/applicability/goal_relevance/risk/known_cost）与 `reasons` 逐项可解释；`snapshot()` 输出三轴 + 机会 + 理由 | AT-10, AT-11 |

## 可信贡献接受与审核身份

`ResearchFeedbackStore.accept(result_id)` 是**唯一**持久化接受入口，且**不再接受调用者 `ThreeAxisResult` 或 `reviewer` 字符串**：

- 结果从 `research_feedback(ledger, assets_root)`（可信事实投影）按 `result_id` 解析，不存在的 `result_id` → `untrusted_result`（伪造）。
- `provenance == "replay"` → `replay_not_acceptable`（回放不能建立新接受）。
- reviewer 是**构造时绑定的 host 自身 Agent 身份**（来自 `HostConfig.worker_id`，由 A 的 identity-bound service 提供），不是调用者字符串。`_reviewed` 要求该 host 身份在**可信投影**里有对本候选的独立派生结果（不同 task 的同 asset 的 `supported`/`refuted` 事实，即真实已确认 TaskLedger 运行的 reproduction/counterexample），仅 JSON 宣称 `purpose=reproduction`/`worker_id` 而无 ledger 执行的伪造 observation 不会出现在可信投影，故被拒（`reviewer_not_admitted`）。结果 id 不能提升 authority。
- 跨作者（`reviewer == actor` 由纯策略 `self_approval_rejected` 拒绝）、跨 scope/project（事实绑定本 swarm 账本，跨项目结果根本不在本 store 可信事实内 → `untrusted_result`）。
- 去重按 `result_id` + `source_ref`；纯 `ResearchPolicy.accept` 仅作计算建议，不是持久化权限入口。

历史只追加：贡献按 `result_id` 追加去重；更正按 `event_id` 追加；supersession 按 `event_id` 追加并把有效视图标记 `superseded`，**原贡献记录不删除**。fresh rebuild 建新 destination store，不改原 store。`research_feedback` 纯读投影确定性幂等、读失败不吞。

## 最小可调用接口（供 A/P 接线）

```python
# 纯策略引擎（无 DB、无 Node 桥、无执行器）
from swarm.research.policy import ResearchPolicy, Branch, CorrectionEvent, SupersessionEvent
policy = ResearchPolicy(exploration_fraction=0.20)   # version == "research-v1"
policy.accept(result, reviewer=..., seen=set())       # 纯计算建议，非持久化入口
policy.opportunities([branch, ...])                   # -> RouteOpportunityPlan
policy.apply_correction(branch, event)                # -> Branch (sleep/downgrade/reopen)
policy.new_condition_branch(refuted, new_id, conds)   # -> Branch (不擦旧反证)
policy.snapshot(results, branches)                    # -> dict 三轴视图

# 从可信事实投影三轴（research-v1 反馈）＋ 可信接受入口
from swarm.research.feedback import research_feedback, ResearchFeedbackStore
results = research_feedback(ledger, assets_root)      # -> list[ThreeAxisResult]（正例+可信反证）
store = ResearchFeedbackStore(path, ledger, assets_root, reviewer=host_worker_id)
store.accept(result_id)                               # 唯一持久化接受入口（绑定 host 身份+真实独立审核）
store.record_correction(event)                        # 追加更正事件
store.record_supersession(event)                      # 追加 supersession（不删原记录）
store.contributions() / store.effective_contributions() / store.corrections() / store.snapshot()
store.advisory(branches)                              # A/P 接线：已接受贡献 + 引用贡献的 branch 机会建议
```

**`advisory(branches)`** 是给 A/P 的正式 advisory projection：返回已接受贡献 + `RouteOpportunityPlan`，每个 `RouteOpportunity` 带 `supported_by`/`refuted_by`（真实贡献 `result_id`），所以下一推荐**真引用贡献而非单纯快照**；`advisory_only=True`、`claim_requires_recheck=True`，宿主权限/地方/scope/dependencies/预算过滤与真实 claim 仍走原 `TaskLedger`。默认不改旧 v0/v0.1（`Router` 仍是 v0/v0.1，research-v1 是独立建议层）。

**审核身份权威来源**：host 自身 `HostConfig.worker_id`（A 的 identity-bound service 已绑定）；`_reviewed` 要求该 host 身份在资产库对本候选有真实 `reproduction/counterexample` observation。C 需要 A：接线时把 host 绑定身份传给 `reviewer=`，并把 branch/task/source 关联（`ThreeAxisResult.asset_id/task_id/actor` → branch）暴露给机会/快照；需要 B：可信评价方式（当前 `trusted_facts` 正例 + `ResearchObservation(purpose="counterexample", execution_state="succeeded", scientific_verdict="failed", known_effect)` 作可信反证）。接口未定前，本实现不依赖 A/B 新代码，负例（forge/replay/自批/同源/未审核 actor）先独立成立，后由同一 Owner 持续接线返修。

## 测试与首 RED

`tests/research/test_research_policy_v1.py` 共 23 项全通过（纯策略 + 投影 + 存储，不调用 Node GEP 桥/执行器）。首 RED 保留：先写测试，首次收集 `ModuleNotFoundError: No module named 'swarm.research.policy'`。Q 对 71bfedb 的伪造/未审核 actor RED（`test_c_feedback_boundaries.py` 3 failed/8 passed）已由本轮修复覆盖。

关键断言：有效反证独立接受；crash/unknown 无科学条目；同 actor 自批拒绝；同 result/source 去重；伪造 result_id→`untrusted_result`；replay→`replay_not_acceptable`；未审核/仅 claim 的 known actor→`reviewer_not_admitted`；跨项目→`untrusted_result`；legacy `purpose=original` 的 failed 不是反证；机会总额固定、dormant/refuted/archived/越权不探索、`exploration_fraction` 有界、可信反证降机会、spec 因素与 `unknown_cost` 理由；sleep/downgrade/reopen + refuted 新条件分支；supersession 追加不删原记录；fresh rebuild 不改源；损坏资产库抛 `sqlite3.Error`；Router 拒绝 `research-v1`。

## 验证命令与结果

```text
python -B -m pytest -q tests/research/test_research_policy_v1.py -p no:cacheprovider
# 23 passed

python -m mypy --strict swarm/research/policy.py swarm/research/feedback.py
# Success: no issues found in 2 source files
```

本机环境限制：`tests/swarm/test_policy_feedback_v01.py`、`tests/research/test_policy_entry_v01.py`、`tests/swarm/test_fc_projection_v01.py::test_all_six_existing_fact_kinds...` 依赖 Node GEP SDK（`node_modules` 未装，`bridge_node` 返回 `sdk_process_failed`），属环境前置（`npm ci` 由 B/CI 提供），与本轨无关；改动前已存在，未改这些文件或断言。本轨测试不依赖 Node 桥：直接按 `publish` 输出形状写 `assets` 表。

## 限制与 NOT_RUN

- **L2 实际研究行动未跑，NOT_RUN**：无真实科研模型调用、无外发、无新沙箱探针、无 GPU/云后端、无 Hub/发布授权。
- `research-v1` 是建议层：机会份额只建议 + 已批准容量分配；真实认领仍走原 `TaskLedger` 重查 scope/capabilities/dependencies/lease/fencing/`BudgetLedger` reserve。未知预算不视为 0，branch/run 不重置 envelope。
- A 未接线前，`snapshot`/`research_feedback`/`accept` 是薄接口，不在 `ResearchService` 的 11 个 MCP 工具内（服务接线与 host 绑定身份传递归 A）。
- 三个轴的 `disputed`/`inconclusive` 状态已建模，产生这些状态的独立评审入口由 A 的共同研究层（FR-08/FR-18）接入，本轨仅提供模型、建议机会与接受边界。
