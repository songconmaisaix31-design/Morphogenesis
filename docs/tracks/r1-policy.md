# R1 C 贡献与研究路线政策（research-v1）

**状态：三轴贡献与研究路线政策（research-v1）领域实现完成，新接口 strict + pytest 通过。** 这是独立于既有策略 v0/v0.1 的**新增**层；`swarm/router.py`、`swarm/feedback.py`、`swarm/pheromone.py`、`swarm/worker_loop.py`、`swarm/research/service.py`、`server.py`、`models.py` 的既有语义未被修改。L2 真实科研行动未获运行级授权，全部 **NOT_RUN**。

## 范围与不修改

本轨只写 `swarm/research/policy.py`（新增）、`swarm/research/feedback.py`（新增）、`tests/research/test_research_policy_v1.py`（新增）与本报告。不触碰 A 的 `swarm/research/service.py`/`server.py`/`models.py`/`HostConfig`，不触碰 B 的 `orchestration/experiments/**`/`local_assets/**`/`swarm/research/case.py`，不触碰 P 产品。跨轨接口只通过主控 Handoff。

- **v0/v0.1 原样保留**：`Router` 的 `strategy_version` 仍是 `Literal["v0","v0.1"]`，`research-v1` 不是 Router 策略版本（有测试断言 Router 拒绝 `research-v1`）。`trusted_facts`、`policy_diagnostics`、FC 投影、Worker 续租边界均未改动。
- **closed FC `RouteCandidate` 不放宽**：research-v1 的机会/理由只存在于 `RouteOpportunityPlan`/`policy_candidates` 语义，不新增 FC 路由候选字段，不改 `fc_log_schema.json` 的 `additionalProperties=false`。
- **复用而非新建**：复用 `TaskLedger`/`trusted_facts`/`ResearchObservation`/`Candidate`/`LocalAssetStore` 与标准 `result_id`/`report_id`/`task_id`/`actor(worker_id)`；不新增任务、执行、审计、Hash 或完成证明系统。贡献去重键是 `result_id` + `source_ref`，**不按 Agent 品牌**判断独立。

## FR → 当前代码 → 新契约 → AT 映射

| FR | 旧代码现状 | 新契约（research-v1） | AT |
|---|---|---|---|
| FR-12 贡献与路线分离 | `trusted_facts` 只给正例三类奖励，无三轴；`scientific_verdict=passed/failed/not_evaluated` 单字段 | `ThreeAxisResult(execution, hypothesis, contribution)` 三独立轴；`ResearchPolicy.accept` 独立接受：`succeeded/refuted` 可 `accepted`，`crash/timeout/auth/unknown` 拒绝；有效反证降低该路线未来机会但认可反证贡献 | AT-08, AT-10 |
| FR-13 投入调整 | 无版本化路线政策 | `RouteOpportunityPlan(version="research-v1", exploration_fraction, total_share=1.0)`；`apply_correction`（sleep/downgrade/reopen）与 `new_condition_branch`（refuted 需新条件）追加不擦除；证据改变下一次可解释推荐，claim 仍由原 TaskLedger 权威 | AT-10, AT-11, AT-14 |
| FR-14 探索与多样性 | v0.1 有 `exploration` 但属任务级 softmax 保底 | `exploration_fraction`（默认 0.20，可配置、有界）作为合法分支探索配额下限；dormant/refuted/archived/`authorized=False`（越权）`eligible=False` 无执行权；同 `result_id`/同 `source_ref`（同源论文/origin copy）去重，不因品牌重奖 | AT-09, AT-11, AT-14, AT-15 |
| FR-24 拓扑可解释 | 无分支机会视图 | `RouteOpportunity.factors`（evidence/support_count/refute_count/exploration_floor）与 `reasons` 逐项可解释；`snapshot()` 输出三轴计数 + 机会 + 理由 | AT-10, AT-11 |

`ResearchFeedbackStore` 是幂等、追加式派生存储：贡献按 `result_id` 去重、更正事件按 `event_id` 追加；`research_feedback` 是纯读投影（重读同档案结果确定、不重跑科学），读失败不被吞（有测试断言损坏资产库抛 `sqlite3.Error` 而非返回空）。

## 最小可调用接口（供 A/P 接线）

```python
# 纯策略引擎（无 DB、无 Node 桥、无执行器）
from swarm.research.policy import ResearchPolicy, Branch, CorrectionEvent
policy = ResearchPolicy(exploration_fraction=0.20)   # version == "research-v1"
policy.accept(result, reviewer="reviewer-0", seen=set())   # -> ContributionDecision
policy.opportunities([branch, ...])                        # -> RouteOpportunityPlan
policy.apply_correction(branch, event)                     # -> Branch (sleep/downgrade/reopen)
policy.new_condition_branch(refuted_branch, new_id, conds) # -> Branch (不擦旧反证)
policy.snapshot(results, branches)                         # -> dict 三轴视图（advisory_only=True）

# 从可信事实投影三轴（research-v1 反馈）
from swarm.research.feedback import research_feedback, ResearchFeedbackStore
results = research_feedback(ledger, assets_root)   # -> list[ThreeAxisResult]（正例+可信反证）
store = ResearchFeedbackStore(path, ledger)
store.accept(result, reviewer=...)                 # 幂等去重接受
store.synchronize(accepted_results)                # 幂等重建
store.record_correction(event)                     # 追加更正事件
store.corrections(branch_id=...)
store.snapshot()                                   # 三轴 + 贡献 + 更正历史
```

A 在 `service` 中接线：把 `ThreeAxisResult` 关联到 branch/task/source，暴露 `snapshot` 给产品三页。C 需要 A 提供 branch/task/source 关联契约（branch 如何从研究任务/假设建立）；需要 B 确认可信评价方式（当前：`trusted_facts` 正例 + `ResearchObservation(purpose="counterexample", execution_state="succeeded", scientific_verdict="failed", known_effect)` 作为可信反证）。接口未定前，本实现不依赖 A/B 新代码，负例（crash/unknown/自批/同源）先独立成立，后由同一 Owner 持续接线返修。

## 测试与首 RED

新文件 `tests/research/test_research_policy_v1.py` 共 16 项，全部通过（纯策略 + 投影 + 存储，不调用 Node GEP 桥/执行器）。首 RED 保留：先写测试，首次收集即 `ModuleNotFoundError: No module named 'swarm.research.policy'`（RED），随后实现到 GREEN。

关键断言覆盖：
- 有效反证 `succeeded/refuted` 独立接受为正贡献；`failed/unknown/cancelled + not_evaluated` 无科学奖励；同 actor 自批拒绝；同 `result_id` 与同 `source_ref` 去重（不同品牌同源不重奖）。
- 机会总额固定 `total_share=1.0`；dormant/refuted/archived/越权 `eligible=False, share=0`；`exploration_fraction` 有界可配置；可信反证使同条件分支机会下降。
- sleep/downgrade/reopen 显式原因转移；refuted 重开须 `new_condition_branch`，旧反证保留。
- `research_feedback` 把 supported 与 refuted 分列，crash/unknown 不产出三轴条目；损坏资产库抛 `sqlite3.Error`（不吞）。
- `ResearchFeedbackStore` 幂等（重复同步/重复接受不双计数）、更正事件追加且重复 `event_id` 拒绝。
- 回归：`Router` 仍拒绝 `research-v1` 作为 `strategy_version`，证明 v0/v0.1 语义未变。

## 验证命令与结果

```text
python -B -m pytest -q tests/research/test_research_policy_v1.py -p no:cacheprovider
# 16 passed in ~3s

python -m mypy --strict swarm/research/policy.py swarm/research/feedback.py
# Success: no issues found in 2 source files
```

本机环境限制：`tests/swarm/test_policy_feedback_v01.py`、`tests/research/test_policy_entry_v01.py`、`tests/swarm/test_fc_projection_v01.py::test_all_six_existing_fact_kinds...` 依赖 Node GEP SDK（`node_modules` 未安装，`bridge_node` 返回 `sdk_process_failed`），属于环境前置（`npm ci` 由 B 锁文件/CI 提供），与本轨无关；这些失败在改动前已存在，非本轨引入，未改动这些文件或断言。本轨测试不依赖 Node 桥：直接按 `publish` 输出形状写入 `assets` 表。

## 限制与 NOT_RUN

- **L2 实际研究行动未跑，NOT_RUN**：无真实科研模型调用、无外发、无新沙箱探针、无 GPU/云后端、无 Hub/发布授权。
- `research-v1` 是建议层：机会份额只建议 + 已批准容量分配；真实认领仍走原 `TaskLedger` 重查 scope/capabilities/dependencies/lease/fencing/`BudgetLedger` reserve。未知预算不视为 0，branch/run 不重置 envelope。
- A 未接线前，`snapshot`/`research_feedback` 是薄接口，不在 `ResearchService` 的 11 个 MCP 工具内（服务接线归 A）。
- 三个轴的 `disputed`/`inconclusive`/`superseded` 状态已建模，但产生这些状态的独立评审入口由 A 的共同研究层（FR-08/FR-18 独立复核）接入，本轨仅提供模型与建议机会。
