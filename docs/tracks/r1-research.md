# Track A — 共同研究层与正式 MCP（R1 / M1）

- Worker: A（长期 Owner，service/server/models 薄接线）
- 分支: `songconmaisaix31-design/morph-r1-research-1003`
- write_paths: `swarm/research/**`（除 case.py/feedback*.py/policy*.py）、`tests/research/**`（除 test_generated*.py/test_research_policy*.py）、`docs/tracks/r1-research.md`
- 范围: FR01-11（M1 核心研究语义）+ FR25-28 由本 Spec 第 9.3/9.4/10.2/5.4 节语义承担（Spec 正文 FR 仅到 FR-24，无 FR25-28 字面条目；映射见下）

## 1. FR → 实际代码 → 新契约 → AT 映射

| FR | 实际代码 | 新契约（Pydantic，数据身份） | AT / 层 |
|---|---|---|---|
| FR-01 创建研究空间 | `service.create_project` / `server.research_project(action=create)` | `ResearchProject`（project_id/goal/allowed_domains/data_bounds/authorization_ref/milestones） | AT-15 L0 |
| FR-02 资料导入与引用定位 | `records.SourceRef`（kind/identifier/version/license/fetched_at/retrieval/location/excerpt）+ `submit_note` 回链 | `SourceRef.retrieval ∈ {present,abstract_only,missing,parse_failed,formula_unreliable}`；抽取失败/仅摘要/无法全文显式可见 | AT-01 L0/L1 |
| FR-03 共同研究记忆 | `knowledge.py`（research-projects/branches/hypotheses/notes/proposals/events 表）；`research_context` 分层返回 | `ResearchNote`/`Hypothesis`/`ResearchBranch`；`review_state ∈ {unverified,verified,disputed}` 分离探索区/已验证区 | AT-01/AT-02 |
| FR-04 局部上下文包 | `service.research_context` + `context()`/`discover()` 内联 `research` 引用 | 摘要+原文 source_ref 回链，不广播全量 | AT-02 L1 |
| FR-05 持续研究 | `knowledge_path()` 由 ledger 同目录派生，project/branch/run 不重置；`put_project` 幂等且不可变 | `ResearchProject` 持久化，独立于 branch/run | AT-14/AT-15 |
| FR-06 研究工作提议 | `service.propose_work` → `TaskLedger.enqueue`（evidence_key 去重 + derived_from 派生限额） | `WorkProposal` → 合法任务（proposal_id==task_id），acceptance.research_proposal 关联 | AT-03 L2 / AT-14 L0 |
| FR-07 自主认领（权限/scope/能力/租约复查） | 保留既有 `claim`/`discover`/`_task(require_capability)` 与 v0.1 selection 审计 | `HostConfig` 绑定；scope/capabilities/token 不由模型传入赋权 | AT-04 L0/L1 |
| FR-08 动态协作 | `actor=AgentId` 记录在每条 note/proposal/event；`research_context` 供接续 | `ResearchEvent.actor` + `provenance` | AT-04 |
| FR-09 原生成员 | 不变（native_agents 归 C/执行层） | — | — |
| FR-10 成员替换 | `research_context(project_id)` 供新 worker 读取共享记录，无需重贴会话 | `ResearchEvent`/`ResearchNote` 按 project 检索 | AT-02 L1 |
| FR-11 专家意见 | `submit_note(kind=expert_opinion, signer=...)`；模型校验强制 `review_state=unverified` | `ResearchNote` 校验器：`expert_opinion` 永不 `verified`，`signer` 仅限专家意见 | AT-09 L0/L1 |

FR25-28（Spec 无字面条目，按语义对应）：
- **FR-25（研究事件最小公共字段，Spec 9.3）** → `ResearchEvent`（event_id/project_id/branch_id/task_id/source_ref/actor/at/schema_version/provenance/event_kind/payload/correlation_ref）；写入 `research_events` 表 + `ledger.record_event("research.*")`。
- **FR-26（项目级授权 envelope，Spec 10.2）** → `HostConfig.authorization_ref` + `ResearchProject.allowed_domains/data_bounds`；预算/执行仍归 BudgetLedger，不由模型传入。
- **FR-27（新增模块边界，Spec 9.4）** → 全部落在 `swarm/research/`，不新建调度器/账本/哈希/完成证明；`research-knowledge.sqlite3` 为 ledger 同目录命名空间（沿用 PheromoneField 惯例）。
- **FR-28（关联与幂等，Spec 5.4）** → `dedup_key` UNIQUE（note/proposal）+ `TaskLedger.evidence_key` 去重；同一写请求幂等，中断恢复不重复建任务。

## 2. 最小接口 Handoff（供主控转交 B/C/P）

- **模型字段**：见 `swarm/research/records.py`。`SourceRef`（source_id/kind/identifier/version/license/fetched_at/retrieval/location/excerpt）、`ResearchNote`（kind/actor/signer/source_refs/text/applicability/review_state/references）、`Hypothesis`（claim/conditions/status/supporting/opposing/source_refs/refuted_conditions）、`ResearchBranch`、`ResearchProject`、`WorkProposal`、`ResearchEvent`。
- **研究记录读取**：`ResearchKnowledge.notes/hypotheses/branches/proposals/project/events`；`service.research_context(project_id)` 返回分层（notes_unverified / notes_verified 分离）。
- **分支/task 映射**：proposal 接受后 `proposal_id == task_id`（确定性）；`TaskLedger.enqueue` 以 `evidence_key` 去重，`derived_from` 走既有派生限额；`acceptance.research_proposal` 保留原 proposal。
- **propose**：`service.propose_work(project_id, kind, goal, justification, expected_contribution, scope?, required_capability?, dependencies?, source_refs?, branch_id?, derived_from?)`；scope/capability 仅限宿主 authorized_scopes/capabilities，越权抛 `PermissionError`。
- **HostConfig 授权参数（新增，均宿主供给）**：`project_id`（默认空）、`authorization_ref`（默认 None）、`research_knowledge_path`（默认 ledger 同目录 `research-knowledge.sqlite3`）。均不从 MCP 工具参数读入。

## 3. 动态执行入口边界（与 B 的交接点）

本轮 A 不新增 generated_candidate 执行入口。`execute/observe/approve/inherit/apply` 保持 v0.1 注册案例语义；`propose_work` 产出的任务仅有 `research_proposal` acceptance，不含 `experiment_plan/research_claim/file_policy`。B 的安全契约（DynamicExperimentPlan + 隔离 + 独立评价）就绪后，由 A 在 service 接 B 的准入接口再赋权，不能用 registered_case 冒充。C 的可信三轴结果写入后，verified 区由既有 ResearchObservation 链填充，note 层不自行置 verified。

## 4. 验证结果（实际命令）

- `python -m pytest tests/research/test_research_semantics.py tests/research/test_service.py tests/research/test_stdio.py -q` → **32 passed**（新轨 20 + 既有 service 11 + stdio 1）。
- 合计定向回归（含 policy_entry 3 项 passing 断言）→ **35 passed**（`len==11` 断言已更新为 `15`）。
- Q 独立负例 `tests/integration/r1_security/test_a_host_boundaries.py`（以 `R1_SECURITY_SOURCE` 指向本 worktree）→ **26 passed**。
- `python -m mypy --strict swarm/research/records.py knowledge.py models.py service.py server.py` → **Success**。
- 新增 MCP 工具总数 **15**（11 旧工具语义不变 + `research_project` + `research_branch` + `submit_research_note` + `propose_research_work`）；`test_mcp_tools_have_no_identity_database_or_metric_write_parameters` 校验新工具同样不暴露 worker_id/agent/ledger_path/passed/approved/metric 参数。

## 5. 真实限制 / 首失败 / 未执行

- **联网获取未执行**：本轮不下载私人科研资料；`SourceRef.retrieval` 由成员声明，宿主不联网解析。PDF 解析复用成熟依赖（Docling）或显式 `parse_failed/missing`，本仓库未安装 Docling，未假装解析。
- **既有失败原样登记（非本轨引入、未扩大）**：
  - `tests/research/test_case.py`、`tests/research/test_registered_cases.py` 收集失败：缺 `code_interpreter`/`opensandbox`（B 核心锁依赖未装于当前 Python 环境）。
  - `tests/research/test_policy_entry_v01.py` 24 项失败、`tests/local_assets/test_research.py` 33 项失败：`bridge_node.assets.BridgeError: sdk_process_failed`（`node_modules` 未 `npm install`，Node bridge 属于 B/C）。
  - `mypy --strict swarm` 13 项 `import-not-found`（orchestration/experiments 的 opensandbox/code_interpreter）为既有环境缺失，非类型错误扩大。
- **L2 未运行**，不写完成。首 RED / NOT_RUN 保留。候选不在宿主执行；未知效果不重放（沿用既有 begin_execution/confirm_execution）。

## 6. 提交

- commit + push 后以 `git ls-remote` 核 SHA（见交付消息）。

## 7. 返修（第二轮，主控退回后）

- **项目稳定域，去 swarm_id 隔离**：`ResearchKnowledge` 全表改为按 `project_id` + UUID 主键（不再按 `swarm_id` 建键/过滤）；同一 `research_knowledge_path` 下，新 run（新 swarm_id/新 ledger）可读同一 project 的 branch/hypothesis/note/proposal/event（`test_project_knowledge_persists_across_runs_not_scoped_by_swarm`）。执行面 `ledger.record_event("research.*")` 仍按 swarm 记录，二者分离。
- **跨项目关系与宿主授权校验**：`_authorize_project`（HostConfig.project_id 绑定，越项目抛 `PermissionError`）+ `_require_branch`/`_require_hypothesis`（branch/hypothesis 必须归属同一 project）；`create_branch` 校验 parent_branch 归属；`submit_note`/`propose_work` 校验 task_id/branch_id/hypothesis_id 归属与宿主 scope。`HostConfig.project_id` 增加非空标识符校验。
- **同 id 不同内容拒绝**：`put_branch`/`put_hypothesis`/`record` 由静默返回/`INSERT OR IGNORE` 改为同 id 不同内容抛 `*_identity_cannot_change`，同内容返回原记录；`put_project` 已有此约束。
- **proposal 中断恢复**：`propose_work` 复用持久化 `proposal_id` 作 `task_id`，`put_proposal`/`enqueue`/`bind_proposal` 任意一步中断后重试都取回原 proposal/task 且不重复（`test_interrupted_admission_recovers_without_duplicate_task`）。
- **derived_from 与父 task locality**：`derived_from` 与每个 `dependency` 均经 `_task` 校验存在且落在宿主 authorized_scopes（越界抛 `task_outside_host_scope`）；`derived_from` 传 None 时不引入派生关系、派生限额由 ledger 在显式 derived_from 时执行。
- **上下文裁剪与 truncated**：`research_context(project_id, limit)` 按宿主 locality 过滤 task 关联 note（越界隐藏），每集合限 `limit` 并返回 `*_truncated` 标记。
- **FR-02 诚实边界**：本轮不联网、未装 Docling，`SourceRef.retrieval` 为成员声明而非宿主抓取/解析完成；`fetched_at` 保持 None（宿主从未抓取）。论文/PDF 全文提取未实现，作为真实限制登记，不假装解析。
- **未越轨**：未接 C 三轴（可信原 ledger/store 验证归 C，主控已退回，note 层不置 verified）；未接 B 动态执行入口（待 B 安全 Handoff 后由 A 接 formal service/MCP，唯一 ledger/lease/fencing/budget/unknown 保护）；未运行宿主候选、未科研真实调用。
- **caller authorization_ref 拒绝**（Q 诊断后）：`create_project` 仅在 caller 传入与 `HostConfig.authorization_ref` 不同的 `authorization_ref` 时抛 `PermissionError`，否则始终持久化宿主绑定值（caller 不能写入攻击者 ref；Q `test_caller_cannot_replace_host_authorization` 通过）。
- **proposal 恢复 payload/acceptance 身份一致**：`propose_work` 在 `put_proposal` 之后一律使用持久化 `existing`（而非一次性 `proposal`）构建 payload/acceptance/dedup，避免 `enqueue` 成功但 `bind` 前崩溃后重试因 `acceptance.research_proposal.proposal_id` 漂移而返回 `blocked`（Q `after_enqueue` 用例通过）。
