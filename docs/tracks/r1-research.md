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

- `python -m pytest tests/research/test_research_semantics.py tests/research/test_service.py tests/research/test_stdio.py -q` → **25 passed**（新轨 13 + 既有 service 11 + stdio 1）。
- `python -m pytest tests/research/test_policy_entry_v01.py -k "test_original_mcp_discovery... or test_no_recommendation... or test_uncheckpointed_wal..."` → **3 passed**（`len==11` 断言已更新为 `15`）。
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
