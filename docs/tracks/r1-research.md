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

## 8. 2026-10-03 恢复派工后的正式动态链后继

第 1–7 节是已交付阶段 `7fc1e80845128080dfbcd5899aa9a09e37128753` 的历史记录，不代表完整 R1。以下工作接续保留的 WIP，使用同一 A Owner、worktree、branch 和 write_paths；不改历史冻结候选。最新 Spec 优先。

- 早期 SOURCE `8fc90a9a34d3b47ced952510ea53ce2412dc38ca`：宿主 envelope/项目 budget、C 三轴与 lifecycle、实际机会选择/claim 重新检查。
- 组合 SOURCE `0bcb320e843839f5f043fccd9f705d9dd9b7299e`：普通合并 B `2d50d08811aa2337b9c0166dc114513e292bce1f` 与 C `4f83296af908352660ebf71e633e70a111eb2877`，正式 generated service/MCP、原消费/应用/mock 采纳及成果包；已 push，远端 exact，已交 P/Q。
- 后继合入 B `5faafe41b1732c83d165251600b688444186c702`：静态拒绝继续保留失败报告，归档核验和原消费链不变。

### 8.1 可调用入口与事实来源

| 能力 | 正式入口 | 原权威边界 |
|---|---|---|
| 项目 / 局部上下文 / 提议 | `create_project` / `research_context` / `propose_work` | 项目关系只在 ResearchKnowledge；实际任务仍 `TaskLedger.enqueue` |
| 自主选择 / claim | `discover` / `choose` / `claim` | C `store.advisory` 重新核验 accepted facts，结果引用进入 `research_choice` / `research_selection`；原 locality/capability/dependency/lease/fence/budget 复查 |
| 候选准备 | `prepare_candidate_experiment(task_id, token, plan, files=None, *, asset_id=None, purpose='original')` | B 既有静态检查、官方资产发布、原 Git scope snapshot、原 TaskLedger acceptance 冻结计划；返回实际 asset/revision |
| 准入 / 执行 | `admit_candidate_experiment` / `execute`，MCP `research_experiment` | B 原 `GeneratedExperimentExecutor`；先原 BudgetLedger 预留、原 `begin_execution`，再已选 backend，原 archive/audit/confirm/settle |
| 观察 / 完成 / 复核 | `observe` / `complete_research` / `approve` / `accept_result` | B 原 `research_reports` 与原账本完成，C 从原始归档/审批/独立任务重新派生三轴；reviewer 为 HostConfig 身份 |
| 继承 / 应用 | `inherit` / `validate_files` / `approve` / `apply` | 原 AssetConsumer → child → 本地再验证 → AssetApplicator → TaskLedger.submit → AdoptionReceipt，不从检索或已生成推断采用 |
| 成果包 | `research_package(project_id=None, *, limit=100)`，MCP `research_project(action='export')` | 原 tasks/acceptance、候选正文、原始 observations、重新读取的 execution、原 task_audit 和实际 adoption receipts；截断明确，不创建完成声明 |
| 有界原始输出 | `artifact(task_id, run_id, artifact_path, *, max_bytes=65536)`，MCP `research_experiment(action='artifact')` | 仅原归档允许的输出/日志，前后使用 B reader 核验，复用原 digest；上限 1 MiB，越界/篡改/超限拒绝，返回 per-record provenance |

`build_service(HostConfig)` 为 stdio 与产品的共同构造入口。动态配置仅来自受保护的 `HostConfig.generated_experiments`：批准 environment/resources、TrustedCriteriaRecord、数据名称到宿主绝对路径、已验证隔离配置等。MCP 无配置、审批人、budget 或直接科学判据写权。

mock 必须明确选择固定输出后端、`research_provenance='mock'` 和专用 `fixture_workspace`，资产根和应用目标在其中。原 AssetStore 持久化 mode/root，不能 reopen 为 live。固定输出由受保护配置提供，后端不解释候选、不启动进程或网络；仅原 Git/GEP 适配器参与文件身份。live 默认隔离不合格时拒绝，不创建沙箱或退回宿主执行。

项目的 goal/actions/data/envelope、原 ledger/swarm/workspace/assets、budget policy/path、execution bound 与 backend/evaluation 配置保存在原项目绑定中。新 branch/run、改路径、移除 envelope 均不能重置额度或继续旧授权。原预留与 execution intent 之间崩溃保留 pending；未知效果不能通过另开任务或 branch 绕过。未知 usage/cost 仍为 None。

C accepted refs 是 discover、choose、claim 和 snapshot 的同一数据源。project + 原 locality 同时过滤原作者与独立复核任务；原 archive 或 approval 变化不能继续产生可信机会。sleep/downgrade/reopen 与 supersession 追加事件，不修改原 branch/贡献历史。程序 failed/timeout/unknown 不构造反证。

### 8.2 本地验证与保留的首次结果

本节记录事实分层，最终安装检查另行追加，不用历史或窄测试代替最终源码验收。

- 原始 `test_research_semantics.py + test_research_v1.py`：29 PASS（27.71s）；pending-reservation 返修后同集 29 PASS（16.21s）；原5模块 strict PASS。
- 动态首次：7 RED / 16.42s，原因是新测试的全网络禁止同时阻断 Windows asyncio 内部 socket pair。日志 `.runtime/a-dynamic-first.log`。先建立可信事件循环后，再禁止进程和网络；未放开候选访问。
- 动态第二次：4 PASS / 3 RED / 32.94s，日志 `.runtime/a-dynamic-loop-repair.log`。两个断言误用了不存在的预算字段，改为原 `BudgetSnapshot.tokens` 和 `actual_cost_usd` 均 None；另一个攻击输入先违反 schema，把 100 改为 schema 内但未经批准的 0.5 后继续要求 `host_frozen_evaluation_required`。未降低业务阈值或旧断言。
- 动态 + 语义 + research-v1：36 PASS / 24.93s，日志 `.runtime/a-dynamic-repair-and-semantics.log`。含接受 support/refutation、实际下次机会引用、原三成员消费/应用/mock receipt、未知效果不重试。
- 组合动态/语义/v1/service/policy_entry：51 PASS / 24 RED / 33.45s，日志 `.runtime/a-combined-source-focused.log`。24 项均在旧 policy-entry 官方 Node bridge 缺依赖时 `sdk_process_failed`；不是完整回归。主控明确本地 GEP fixture 已授权，真实沙箱/云 SDK 调用仍未授权。
- changed5 strict：首次3 RED（导出 import、Protocol 可变 provenance 类型与 Literal narrowing），第二次导出代码3 RED（receipt 字段/列表类型）；对应修复后 PASS，日志 `.runtime/a-combined-strict.log`。B 修复 protocol 类型属于其普通合入源码，无类型忽略。
- Q 回报 exact `0bcb320` 正式 FastMCP dynamic 15 PASS / 20.01s；其首次14 PASS / 1 RED来自可信 Git snapshot 被测试 guard 阻挡，原业务断言保留。此处仅记录 Q 的回报，不代替 A 最终 installed/stdio 检查。
- 更早 stdio OpenBLAS RED 保留；后继 stdio 测试显式在 SDK 子进程参数传入 BLAS/OMP/MKL=1。仅进程环境变化，没有全局配置变化。

### 8.3 真实限制

L0/本地 mock 集成不能代表真实科研结果、真实隔离能力或 swarm 优势。L2、付费模型、外部科学材料抓取/上传、真实沙箱探针、新云资源、Hub、部署均 NOT_RUN。SourceRef 的获取/解析状态仍为显式来源记录，自动 PDF 全文解析未实现。原生成员进程接入和 HTTP/UI 在 P/F 轨，由其精确源码与测试报告分别验收；A 提供实际可调用协议，不宣称已运行真实原生模型会话。

### 8.4 精确后继与私有安装准备

SOURCE `4afe462b08867b4662a0bd01ee89833e56ffb32b` 已 push 且远端 exact，包含 B 最终 SOURCE `5faafe41b1732c83d165251600b688444186c702`；C 领域 SOURCE `4f83296af908352660ebf71e633e70a111eb2877` 为祖先。报告不参与 SOURCE commit。

- 该后继动态8测试 **8 PASS / 75.13s**（`.runtime/a-artifact-focused.log`），新增实际 raw output 正例以及超限/非 manifest 路径/未知 run/归档篡改拒绝。变化5模块 strict **PASS**（`.runtime/a-artifact-strict.log`）。
- `git archive 4afe462...` 保存到 `.runtime/acceptance-4afe462/source.tar`。Windows `tar.exe` 首次遇中文文件名返回错误，未删除部分输出；另建 `source-utf8`，使用 Python `tarfile`、UTF-8 和 `filter='data'` 完整提取。
- 只在 `.runtime/acceptance-4afe462/venv` 建私有 Python 3.13.13 环境，进程设置 `UV_LINK_MODE=copy`，锁依赖从未改动的 `poetry.lock` 导出。`uv pip install --only-binary :all: -r .runtime/locked-requirements.txt`：102 packages；随后 `uv pip install --no-deps <source-utf8>` 构建并非 editable 安装核心。
- 将同一归档 `package.json/package-lock.json` 复制到私有 `venv/Lib/site-packages`，`npm ci --prefix <site-packages> --ignore-scripts --no-audit --no-fund --cache .runtime/npm-cache`：99 packages，exit 0。官方 Node ESM 从已安装 bridge 的父目录解析锁定 SDK，没有改全局 Node 或复制凭据。
- `uv pip check --python <private-venv>/Scripts/python.exe`：103 packages compatible。独立 `run` 工作目录的 `service.__file__` 指向该私有 site-packages；`direct_url.json.dir_info` 无 editable；13 个 `swarm/research/*.py` 与原归档逐字节一致。日志为该 acceptance 目录的 `installed-origin.log`、`pip-check.log` 与安装日志。
- 归档 `poetry.lock` SHA256：`5fabe288babc951a1fdfd6abf980d576cba1b0bbe48b3ff2d528d00c84ffa101`；`package-lock.json` SHA256：`af4f22e1fe20fa036cd5f00795edc315882ffa44b5d96baa473de89f61e5119e`。这里只使用标准文件摘要核对既有锁文件，没有自建证明系统。

完整 installed 回归与正式 stdio 结果在下一节追加；上述安装准备本身不代表这些测试通过。

### 8.5 正式非 editable 安装回归

主控在 C 释放后授予 A 完整单进程窗口。工作目录为独立 `.runtime/acceptance-4afe462/run`，只放同一归档的 tests/demo/pyproject，包导入来自私有 site-packages；父进程及正式 MCP SDK 子进程显式设置 `OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=MKL_NUM_THREADS=1`。

```powershell
../venv/Scripts/python.exe -m pytest tests/research/test_dynamic_service.py tests/research/test_research_semantics.py tests/research/test_research_v1.py tests/research/test_service.py tests/research/test_policy_entry_v01.py tests/research/test_case.py tests/research/test_registered_cases.py tests/research/test_stdio.py tests/research/test_stdio_dynamic.py -q --tb=short
```

首轮 **88 PASS / 1 RED / 155.40s**，完整日志 `.runtime/acceptance-4afe462/installed-research-first.log`。原 policy-entry 24 项 SDK 环境失败在该锁定安装中全部通过；旧 case/registered/service/stdio 与新 dynamic/semantics/research-v1 均通过。唯一 RED 是新增 stdio 测试将 `lease_task` 的 SDK structuredContent 直接当作 lease，导致 `KeyError: token`。检查锁定官方 SDK `FuncMetadata.wrap_output` 后，测试仅对 `lease_task` 的 `dict | bool | None` 联合返回类型严格要求单键 `{result: lease}`，再断言内部为 dict；生产接口、租约 token、宿主授权、科学判断及旧断言未改变。

从新的中立 `stdio-repair-run`（保留首轮测试目录）运行：

```powershell
../venv/Scripts/python.exe -m pytest tests/research/test_stdio_dynamic.py -q --tb=short
```

结果 **1 PASS / 23.95s**，日志 `.runtime/acceptance-4afe462/installed-stdio-repair-first.log`。这是一条真正通过官方 SDK stdio、官方 GEP 和正式 `build_service` 的本地 mock 链：宿主项目上下文 → 成员动态提议 → discover/choose/claim → arbitrary generated Python 的静态准入 → 固定 mock 输出 → 原始观察与完成 → 独立身份/任务/新 fixture 实例复现 → accept → 新任务的结果引用选择/claim → 验证归档成果包。自接受和重复执行仍拒绝；usage/cost 未知保持 None；未执行候选 Python，没有真实模型或科研结果声明。

修正作为 test-only SOURCE `cc2e7227e1b423924c99113c9676ef8cc310e92b` 独立提交并 push，远端 exact；相对 `4afe462` 仅该新测试增加6行。最终 `git archive cc2e722...` 中13个研究模块与已安装包逐字节一致，执行过的修正测试与归档按 Git 文本行尾归一后一致，记录 `.runtime/acceptance-4afe462/final-source-equality.log`。安装 metadata 仍真实指向 `4afe462` 的归档目录，没有把它改写成新安装；未重复已通过且未变动的88项测试。测试完成后即向主控释放重测试窗口给 P。

### 8.6 A 轨交付边界

- 最终 SOURCE：`cc2e7227e1b423924c99113c9676ef8cc310e92b`；分支 `songconmaisaix31-design/morph-r1-research-1003`。本节报告单独提交，不混入 SOURCE。
- 原 TaskLedger/Executor/AssetStore/验证/应用/采纳链均被正式 ResearchService/MCP 调用；宿主 envelope/data/budget、C 独立复核与三轴、append-only lifecycle、实际机会排序/选择及 claim 复查已接通。早期 `7fc1e808` 仍只代表当时阶段。
- B 最终领域 SOURCE `5faafe41b1732c83d165251600b688444186c702` 和 C 领域 SOURCE `4f83296af908352660ebf71e633e70a111eb2877` 均为祖先。C 最终 `56de8e3f5d2abd1e1ba02218b422f0aba9847ae2` 相对该 C source 只普通合入同一 B 文件，无新增 C 领域差异；最终 I 可继续按 owner 的精确 SOURCE 合并历史。
- SOURCE 及具体调用签名已交 P/Q/主控；P 可安装并接原生成员/HTTP，F 可消费 DTO/UI，不等待最终 I。P/F/Q/I 的后续独立结果不计入 A 自测。
- 验收事实为 owner 的本地 contract 与正式 installed/MCP mock 接口；不宣称完整 R1、`task_live`、真实科学有效性或用户验收。完整 I 集成、P/F/Q 各轨验收仍由原 owner/主控负责；8.3 中自动 PDF 与全部 L2/外部操作限制继续有效。

## 9. 2026-10-03 精确 B/C 最终组合候选

本次新 Task `task_012ff330b0ea` / Dispatch `ctx_08b0b3d7fddb` 只由原 A Owner 准备 P/Q 安装候选，不接管领域实现，也不代替最终 I。前节 SOURCE/REPORT 与原始失败保留。主控提供的 A `37051852669`、B `37059454013` 双平台 CI 通过是各自精确源码的独立记录，不算本节新组合安装结果。

### 9.1 普通精确合并

从干净 HEAD `5a0caf0055d485d6343eaa561589a3be6d43728f` 顺序执行：

```powershell
git merge --no-ff --no-edit 387338f49045f7be7a184b868f48f325cebd9cbd
git merge --no-ff --no-edit 8bc4c282ed4db8e2be0798509b28d984240b3a06
```

两次均无冲突，组合 SOURCE **`d85aa95e8da406d598f3658492e3d615bba8a28f`** 已 push，并以 `git ls-remote` 核对 exact。A 原 SOURCE `cc2e7227e1b423924c99113c9676ef8cc310e92b`、B 最终 SOURCE `230d283848c0879ff9c349096548d3810c4b1954` / REPORT `387338f49045f7be7a184b868f48f325cebd9cbd`、C SOURCE `56de8e3f5d2abd1e1ba02218b422f0aba9847ae2` / REPORT `8bc4c282ed4db8e2be0798509b28d984240b3a06` 全部经 `git merge-base --is-ancestor` 确认为祖先。

相对 A `cc2e722`，生产 Python 仅 `local_assets/store.py` 新增两行注释和配置读取前的 `BEGIN IMMEDIATE`；新增原 B `tests/local_assets/test_store_initialization.py`，其余变化是 owner 报告。C 研究运行代码无差异，A 未修改业务代码、接口、B/C 测试或断言。SOURCE 推送后已立即交主控/P/Q，后续测试不阻塞其精确 repin 准备。

### 9.2 私有 COPY、非 editable VCS 安装

按本次授权沿用 A 自有 `.runtime/acceptance-4afe462/venv`，证据独立保存在 `.runtime/acceptance-d85aa95/`，安装前 `direct_url.json` 另存 `previous-direct-url.json`。没有使用系统 editable 或借改其他轨环境。

```powershell
# 以下环境仅限本次安装进程；无 git config --global 或全局环境改动。
$env:UV_CACHE_DIR=Join-Path (Get-Location) '.runtime/acceptance-d85aa95/uv-cache'
$env:UV_LINK_MODE='copy'
$env:GIT_CONFIG_COUNT='1'
$env:GIT_CONFIG_KEY_0='core.autocrlf'
$env:GIT_CONFIG_VALUE_0='false'
uv pip install --python .runtime/acceptance-4afe462/venv/Scripts/python.exe --no-deps --reinstall-package morphogenesis 'morphogenesis @ git+https://github.com/songconmaisaix31-design/Morphogenesis.git@d85aa95e8da406d598f3658492e3d615bba8a28f'
```

`vcs-install-first.log`：构建/安装 exit 0。锁依赖和本轨原有 Node SDK 未变动。隔离 `-I` 导入只来自该私有 site-packages；`direct_url.vcs_info.commit_id` 与 `requested_revision` 均为新组合 SOURCE，无 editable。`uv pip check`：103 packages compatible。

首字节比较 **RED** 保留为 `installed-origin-first.json`：比较用的默认 `git archive` 导出目录是 CRLF，安装包/独立 VCS checkout 是 LF；store 长度分别为21564/21180，差异恰为384个 CR，service 对照也一致。该首失败没有通过改已安装字节、行尾归一或放宽断言消除。保留原 `source.tar` / `source` / `run`，另用单进程 `git -c core.autocrlf=false archive` 生成 `source-lf.tar`，提取至新 `source-lf` / 中立测试目录 `run-lf`；直接 `git show <SHA>:<path>` 原始 blob 是最终比较依据。

`installed-origin-git-blobs.json`：新 `store.py` + 全13个正式 `swarm/research/*.py` 的 **14 文件原始 Git blob、LF archive、installed 包逐字节相等**，没有手工改 installed 文件；真实包含 `BEGIN IMMEDIATE`。该结果是本次重新安装证据，与前节旧包检查分开。

此前“PDF 未实现”只指 A 核心轨没有实现解析器；本次主控确认 P 已实现真实 pypdf 材料入口，不能将 A 轨边界写成整个产品缺功能。P 的材料/HTTP/native/页面证据仍由 P/F/Q 独立报告。C 全局 editable 清理仍是自动审批拒绝且未清理的历史人工事项；本次没有绕过或接管清理。

### 9.3 本次组合的有限适用验证

主控 `msg_ff909d31cd1d` 确认 F 已退出自有进程后授予短窗口。进程 BLAS/OMP/MKL 均为1；中立 cwd 为 `.runtime/acceptance-d85aa95/run-lf`，只有精确归档的 tests/pyproject，下面 bootstrap 只把该测试根加入路径，不加入活动核心源码。

```powershell
../../acceptance-4afe462/venv/Scripts/python.exe -I -c 'import sys, pytest; from pathlib import Path; sys.path.insert(0, str(Path.cwd())); raise SystemExit(pytest.main(sys.argv[1:]))' tests/research/test_stdio_dynamic.py tests/local_assets/test_store_initialization.py -q --tb=short
```

首次 **6 PASS / 11.11s**，`installed-focused-first.log`，exit0。原 B 并发5项实际使用 SQLite 独立连接和两线程，涵盖同配置一致、冲突配置只允许完整绑定、immutable triggers 和旧库回滚；原网络/进程禁止 guard 保留。正式 stdio1项从新 VCS 安装启动作者与独立 reviewer，走真实 MCP/GEP、原账本、固定 mock backend、接受后实际 choose/claim 引用和成果 export。原文件/业务断言未改，不将 mock 固定输出解释成候选 Python 执行或真实科研。

第一次 strict 指定私有 `site-packages/local_assets/store.py`，mypy 在该根发现 `typing_extensions.py` 遮蔽库模块，exit2；保存 `installed-store-strict-first.log`，这次没有完成代码检查。改从已与原 blob/installed 完全相同的 `.runtime/acceptance-d85aa95/source-lf` 执行同模块检查：

```powershell
../../acceptance-4afe462/venv/Scripts/python.exe -I -m mypy --strict --follow-imports=silent --cache-dir ../source-mypy-cache local_assets/store.py
```

结果 **Success: no issues found in 1 source file**，`source-store-strict-first.log`，exit0。仅检查变动模块，没有降低类型规则或改配置文件；不是声称全仓 strict 重跑。`git diff --check` 通过。结束后查询本轨安装路径对应的 Python/Node 进程为0，于消息 `msg_419e0d7d7b05` 立即释放窗口给 P。

### 9.4 交付与未执行边界

SOURCE `d85aa95e8da406d598f3658492e3d615bba8a28f` 保持不变，后继 REPORT 只修改本文件；原分支 `songconmaisaix31-design/morph-r1-research-1003` 普通 push，最终报告 SHA 以交付消息及远端精确核对为准。B/C 最终报告随普通 merge 保留，首次 archive 字节门 RED、首次 strict 调用拒绝以及全部先前失败均未覆盖。

本轮没有重跑全仓1300项，也没有重跑 B 原 worker180秒用例；其本地1 FAIL/21 PASS 的根因继续 **UNKNOWN**，B 精确 SOURCE 的双平台独立 CI 通过不解释该历史超时。本组合的新增实际证据只包括本节私有 VCS 安装、原始字节门、stdio/并发6项及变动模块 strict。

P/Q 可据该已安装组合继续精确 repin 和独立验收；I 仍待主控在 P/F/Q 前置完成后独立派发。本报告不代表完整 R1 或最终产品组合通过。真实科研/模型、资料外发、真实沙箱/隔离探针、云资源、Hub、发布和 L2 均 NOT_RUN；历史人工清理事项仍由主控按 C 报告处理。

## 10. FR-04 局部上下文与原生预算接续（2026-10-03）

本节对应新任务 `task_8f61e0bb9e35` / `ctx_c60dc35cb810`，以前各节及首次 RED/UNKNOWN/NOT_RUN 均保留。范围依据主控计划 `66e2a26` 和用户本轮指令；不扩展学科、Agent 品牌、计算语言、复杂评分或 RSI。原 A 分支不变。

### 10.1 精确来源与已有调用核查

普通合入最终核心 REPORT `08b31b39c075571ffd247e2b591d657ce09b6b34`（含 SOURCE `2c63bc7c9e49edff28e26f5930a22d0415fadd65`），形成基线 `be5b6fe9bad959c73b0234a5b64f3e7e577d16a4`。随后普通合入 C SOURCE `e82cae36038c386aec999642289ac1d78c82a9ed` 与 REPORT `52b8d26da04aec41ceb7e008445ef2f1dc088d53`；没有 cherry-pick、改写 C 文件或丢弃历史。

只读核查私库 SOURCE `9e2718789cb67f8b829207e17dac4d95a88e59c9` / REPORT `a7f657d18fae33fc2a4df92b5fcb60dcd7839c5d`，P 也确认：`backend.py:160` 的 `ServiceBackend.research_context` 只转发核心，`:208` 的 `task_research` 读取 `service.context(task_id)["research"]`；`choice_mcp.py:45` 和 `r1_native.py:135` 没有另一套按分支/依赖/引用选择的实现。`web/facts.py` 的时间线过滤不等于 FR-04 背景选择。因此本次在原核心边界补齐，P 继续薄转发，没有新知识模块或调度器。

A 初始 SOURCE `def0e6e107c7c1885f6615b945b2f6551ab9ba25` 已在 68 项聚焦及 changed4 strict 后 push，交给 P 准备精确安装。静态复核又发现 `create_project` 的幂等入口未经过其他项目动作已有的 active 检查，后继 SOURCE **`cea7923fec48c10e043c1fea40c99749e0b6a114`** 仅增加该检查及原三参数化测试中的对应动作；普通 push 与 Owner `ls-remote` 精确一致，未将前一源码测试结果冒充后继结果。主控独立远端连接曾失败的记录由主控保留，本轨成功查询不解释那次失败。

### 10.2 正式局部上下文调用链

原 `server.py:48 project_context` → `service.py:188 context` → `service.py:1257 _task_research` → `service.py:975 research_context`。原 `server.py:141 research_project(action="read")` 同样调用该选择入口；工具总数仍为 23。兼容的新增可选参数是：

```python
service.context(task_id, *, limit=100)
service.research_context(project_id=None, *, limit=100,
                         task_id=None, branch_id=None, overview=False)
```

权限先于相关性：任务从原 TaskLedger locality/project 过滤读取，任务关联的 note/hypothesis/proposal 不可通过引用绕过权限。默认种子优先当前成员持有的有效任务，其次原账本与 research-v1 允许、能力匹配的候选；这只选择读取背景，不创建/选择/认领任务。无种子时保留项目目标、共享未解决背景和有界分支目录，不广播各分支笔记。显式任务/分支锚点必须在项目与原授权范围内。

局部包保留同分支相关记录，再沿原依赖、派生关系、note references、hypothesis supporting/opposing、来源 ID 与原 result ID 选择已有记录；跨分支引用只引入关联记录，不自动展开那个分支的所有邻居。权限不允许的引用不继续遍历，原引用字符串保留并标记 unresolved。能力不同的依赖/引用结果可作为只读背景到达，原 claim 仍检查能力、依赖、租约、fence、预算与未知效果。

返回原来源/版本/许可/定位、适用条件、争议与未验证状态，保留 `research.notes` 旧字段。`selection` 给出锚点、理由、候选窗口/解释截断及未解引用；各集合在权限与相关性选择后截断。`knowledge.py:359 events` 在选入后计数，避免无关或不可见事件先占满分页。局部 research-v1 是已有事实的子集，份额不重新计算或归一化；discover 的原政策建议与 claim 审计语义保留。

人看的项目总览使用 `overview=True`，仍受原权限与 limit 限制；`research_package` 显式使用该总览，保留项目事实与原执行/资产/采纳链的有界导出。P 已接受在自身工作台调用加 `overview=True`，没有在 A 修改私库。

### 10.3 宿主原生预留连接

P 首 RED 揭示：原 native 启动预留被 `_budget_ready` 当成其它 pending，从而阻塞自己的 MCP claim；另一方面直接启动未检查原 TaskLedger 未确认效果。经主控明确授权，A/P 交换并实施最小宿主接口。

`models.py:23 NativeInvocationBinding` 保存本轮 UUID、完整原 `Reservation` 与过期时间；`HostConfig.native_invocation` 只由受保护宿主配置提供，不进入 MCP 参数，也不写入项目永久 `_host_binding`。`service.py:695 admit_native_invocation(invocation_id, bound, *, ttl_seconds)` 先核原项目、预算/未知效果、账本期限，再调用原 `BudgetLedger.reserve`；bound 必须严格等于宿主原 `research_execution_bound`。期限取 TTL、原预算与任务账本期限的最小值；预算额度与调用计数不重置。

`service.py:731 _native_reservation` 逐次核原 pending 记录全字段、project/member/request/task/provider/model/bound/时间；关闭、过期或错配绑定拒绝。HostConfig 再验证先于打开新账本，避免 `model_copy` 绕过身份验证。项目动作、任务动作和 create_project 都检查 active；`_budget_ready` 只识别自己的那一条 pending，其它 pending/uncertain 与原 TaskLedger unknown 继续阻止准入。新 invocation 不能继承旧未知预留的例外。

原动态执行的 `begin_execution → archive → budget.settle → confirm_execution` 顺序未改变：active 校验本身只检查自己的 native hold，允许合法执行完成回执继续落账；下一次准入仍检查全部未知状态。P 保持原退出 settle/mark_uncertain 和受保护配置传递，不引入第二预算账本、session/Attempt/Manifest 系统。本接口没有放行真实科研或模型调用。

### 10.4 首次失败与源码聚焦验证

原始基线 LF archive 在实现前保存到 `.runtime/fr04-native/baseline`，新测试叠加于此。`first-red-source.txt` 核实 service/models/server/knowledge/policy 五个归档文件逐字节等于原 `2c63bc7` Git blob，未回滚或覆盖工作树 WIP。从该目录运行私有解释器 `-I`，只把该归档放入导入路径：

```powershell
../../../.venv-r1-a/Scripts/python.exe -I -c 'import sys,pytest; from pathlib import Path; sys.path.insert(0,str(Path.cwd())); raise SystemExit(pytest.main(sys.argv[1:]))' tests/research/test_local_context.py tests/research/test_native_invocation.py 'tests/research/test_dynamic_service.py::test_dynamic_service_accepts_only_independent_original_chain_and_changes_opportunities[False]' -k 'not stdio' -q --tb=short
```

实际 **19 FAIL / 1 deselected / 38.78s**，`first-red.log`：六项相关性失败，十二项缺失 native 绑定入口，以及正证据 share 仍为 0.5。A 按 C Handoff 把旧支持断言从 `== .5` 收紧到 `> .5`；C 拥有公式及正式 discover/choose/claim 接线新测试，A 未代写政策领域。

首次实现组合运行加入旧 semantics/v1/service/dynamic/policy_entry，实际 **39 FAIL / 57 PASS / 1 deselected / 43.64s**，`focused-first.log`：14 项同一相对 scope 调用 absolute-only helper 的回归、1 项新 MCP 测试误读 union 的 `result` 包装、24 项原政策测试的 `sdk_process_failed`（源码工作树没有相邻官方 SDK）。修正原权限读取及测试 DTO 解包，断言目标不变；SDK 相关项留待精确 COPY 安装入口复验，不修改 SDK/门或原断言。

```powershell
.venv-r1-a/Scripts/python.exe -m mypy --strict --follow-imports=silent swarm/research/knowledge.py swarm/research/models.py swarm/research/service.py swarm/research/server.py
.venv-r1-a/Scripts/python.exe -u -m pytest tests/research/test_local_context.py tests/research/test_native_invocation.py tests/research/test_research_semantics.py tests/research/test_research_v1.py tests/research/test_service.py tests/research/test_dynamic_service.py -k 'not stdio' -q --tb=short
```

实际 changed4 **strict PASS**（`strict-first.log`），修复后 **68 PASS / 1 deselected / 89.84s**（`focused-repaired.log`），对应 SOURCE def0e6e。测试进程使用局部 `OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=MKL_NUM_THREADS=1`，不改变全局。新增行为测试覆盖同项目无关分支排除、原依赖/结果 ID/引用可达、权限先于引用遍历、能力过滤、来源条件/争议保留、可见截断、无任务成员背景、正式 FastMCP 路径，以及 native 的原 hold、关闭/过期、身份/bound 错配、未知效果、累计调用/成本与期限。

### 10.5 后继精确 COPY 安装与正式入口验证

按主控串行窗口，在 P 明确全部重进程退出后，仅更新 A 自有 `.runtime/acceptance-4afe462/venv`。本轮证据独立置于 `.runtime/fr04-native/acceptance-cea7923/`；旧 `direct_url.json` 备份为 `previous-direct-url.json`。`git -c core.autocrlf=false archive` 精确提取 cea7923，Python UTF-8 tar 读取归档；独立 `run/` 只放该归档的 tests 和 pytest 配置，没有生产源码。

以下安装进程局部设置 `UV_LINK_MODE=copy`、独立 `UV_CACHE_DIR`、`GIT_CONFIG_COUNT=1 / GIT_CONFIG_KEY_0=core.autocrlf / GIT_CONFIG_VALUE_0=false`，以及 BLAS1；没有改变全局 Git/HOME/auth/provider，未使用系统 editable 或其他轨环境：

```powershell
uv pip install --python .runtime/acceptance-4afe462/venv/Scripts/python.exe --no-deps --reinstall-package morphogenesis 'morphogenesis @ git+https://github.com/songconmaisaix31-design/Morphogenesis.git@cea7923fec48c10e043c1fea40c99749e0b6a114'
uv pip check --python .runtime/acceptance-4afe462/venv/Scripts/python.exe
```

VCS 实际解析、构建并安装 cea7923，exit0（`install-first.log`）；**103 packages compatible**（`pip-check.log`）。首次字节核对命令的相对解释器路径多写一级父目录，PowerShell 报路径无法识别，Python 尚未启动；改用 A 同一私有解释器的绝对路径后执行。没有改安装字节、门或预期源。

`installed-origin.json` 记录绝对解释器和 service 的 site-packages 路径、非 editable `direct_url` 的 commit/requested_revision 均为 cea7923、官方 GEP SDK **1.14.0**。13 个 `swarm/research/*.py`（包括原 C policy/feedback）、原 `local_assets/store.py`、原 `bridge_node/asset_bridge.mjs` 共 **15 文件**，安装内容与 LF 归档分别逐字节等于该 SOURCE 的原 Git blob；没有做换行归一化替代比对。SDK 沿用 A 自有环境原锁定安装，不借装全局包。

在 `acceptance-cea7923/run` 中，将下列 `$taskPython` 设为上述 A 私有解释器的绝对路径。父进程先核生产 service 来自 site-packages，再仅加入 tests-only 工作目录；stdio 子进程也使用同一解释器的 `-I` 正式 `swarm.research --config`：

```powershell
& $taskPython -I -u -c 'import sys,pytest; from pathlib import Path; import swarm.research.service as service; assert "site-packages" in str(service.__file__); sys.path.insert(0,str(Path.cwd())); raise SystemExit(pytest.main(sys.argv[1:]))' tests/research/test_native_invocation.py tests/research/test_local_context.py::test_official_stdio_member_local_context tests/research/test_stdio_dynamic.py tests/research/test_policy_entry_v01.py -q --tb=short
```

**43 PASS / 52.52s**（`installed-focused-first.log`）：native 13 项，包括关闭/过期配置不能重放 create_project；新 context 正式 stdio 1 项；原固定输出 generated author/independent reviewer/member loop 正式 stdio 1 项；旧 policy_entry 全部 28 项。保留 1 条 `PytestAssertRewriteWarning`：为了确认导入来源而预导入 service/anyio，pytest 未能再重写已导入的 anyio；没有修改测试断言。此前源码路径的 24 项 SDK RED 在此真实安装入口通过，旧日志不改写。

从已与安装/原 blob 一致的 `acceptance-cea7923/source` 执行后继模块检查，避免把整个 site-packages 当类型源码根：

```powershell
& $taskPython -I -m mypy --strict --follow-imports=silent --cache-dir ../mypy-cache swarm/research/knowledge.py swarm/research/models.py swarm/research/service.py swarm/research/server.py
```

**Success: no issues found in 4 source files**（`strict-final.log`）。本轮没有重跑已通过的全 68 项，也没有重跑全仓或提高任何超时/阈值。测试/type 进程均结束；按本安装路径查询 Python/Node/uv 进程为 0，于 `msg_998ec8505d6a` 立即将共享重窗口释放给主控/B。

### 10.6 交付与剩余限制

最终 SOURCE 为 **cea7923fec48c10e043c1fea40c99749e0b6a114**；后继 REPORT 仅修改本文件，独立 commit/push，精确报告 SHA 随交付消息和远端核对记录。主控在 `msg_6c8d1363b0cc` 已独立确认后继远端，前述首次网络失败仍保留。

本次完成 A 的局部上下文、宿主原生预算连接、调用测试和必要修复；C 正证据领域来自精确普通 merge，P 接续/UI 薄适配由 P 原 Owner 完成。本地原生相关测试使用 mock executor，正式 stdio 的研究执行使用固定 mock 输出，均只证明 contract_local/L1 接线；未知 usage/cost 不写成零，候选代码不在宿主执行。

完整最终产品组合、一次完整离线回归与 installed 输入观察仍由独立 I 后续固定组合验收；本报告不代表整产品 R1 完成。AT-07、真实模型/科研/沙箱或隔离探针、外部科学资料抓取/上传、云资源、Hub、发布及 L2 均 **NOT_RUN**，不能据此候选直接进入真实环境。未更改全局 Python/editable 或绕过此前 C 清理的策略拒绝；私库已有 PDF 入口不属于本轨缺口。后继 AOCI 开发索引属于另外的任务，不混入本次源与证据。

## 11. 受信 Docker 配置与有限核心 AOCI 收口（2026-10-03）

### 11.1 精确源码和本次变更

继续原 A Owner、worktree `C:/Users/DW/orca/workspaces/Morphogenesis/morph-r1-research-1003`、branch `songconmaisaix31-design/morph-r1-research-1003`。本 Dispatch `task_7943319add9b / ctx_6aadc6cb132c` 接续已完成配置，不重写领域源码。普通 exact merge 已包含 B SOURCE `5769005b09f1b756c94fdad0649a6b74690c0ca9`、B REPORT `5aebd2eb7af774b3dc496ad9620548f6e7852e09` 与治理 `11f2ff872ca815b38e33d2011208e2503bbf42b5`；后者普通 merge 为 `36134e3d26502c56c2ff2bc20a781efff707db5c`。root 后续 Q 文档治理不改变本次十源，没有为文档循环合并或重测。

已完成宿主配置 SOURCE `aec86c98ffe8fc3c3a922da5a6e281d553820d05`：`GeneratedHostSettings.docker_export` 默认 None，原 live factory 精确传 `docker_export=self.settings.docker_export`；HostConfig 仍通过封闭 generated 设置验证，候选/产品工具输入不能注入控制面，未读取 DOCKER_HOST/context，也不填假 Engine/daemon ID。该 SOURCE 已验收 **9 PASS / 8 deselected / 10.18s**、changed2 strict PASS，日志 `docker-config-final.log`、`strict-first.log`；首次失败和修复日志仍在同目录。按恢复指令，本 Run 没有重跑已绿门；Q 独立非editable安装验收以其自身 SOURCE/REPORT 为事实源，A 不把它当本次新运行。

本轮 AOCI SOURCE 为 **8dd85c1f88698cd8a22d72b5575e45e9431c0ce0**，已 push，`git ls-remote` 返回相同 SHA，SOURCE 后 `git status --porcelain` 为空。其九项变更仅为官方 Root/Meta/Code、`.aoci/.gitignore/config.json/baseline.json`、`.gitattributes`、`.gitignore` AOCI 区块和 `docs/development/aoci.md`。本章节是后继 docs-only REPORT，SHA 随终态交付/远端证据提供。

`cea7923fec48c10e043c1fea40c99749e0b6a114`、`faf23260df7a4f530eb421680f71eb6dc7c72e40` 与 B 源码的 `git merge-base --is-ancestor ... HEAD` 均 exit0；没有 cherry-pick、force push、历史证据重写或业务源变更。十个当前源文件字节与首个官方机器候选的 source_sha256 全部相同。

### 11.2 来源、权限和索引范围

复用官方 [AOCI-CODE v0.1.0-rc17](https://github.com/aoci-spec/aoci-code/tree/v0.1.0-rc17)，commit `93d6ad5a87fd9624a51cae61b2134d33944501fb`、[FSL-1.1-MIT](https://github.com/aoci-spec/aoci-code/blob/v0.1.0-rc17/LICENSE)。实际二进制 `C:/Users/DW/orca/tools/aoci/v0.1.0-rc17/windows-amd64/aoci.exe` 的 `--version` 与 SHA256 `4013002f49d66e2a3998c7b852a8d28d37052af2fc3328ba7fb45246a3c75c67` 匹配 P 已校验版本；未重下载、复制 binary、安装系统包或重新审计上游签名/构建可复现性。

精确业务白名单仅 `swarm/research/{models,service,server,dynamic,knowledge,records,policy,feedback}.py` 和 `swarm/{budget,task_ledger}.py` 十项；其它默认 exclude。各 Entry 从当前源码结构和行为决定点逐项理解，手工编写完整 Tag/F/R/A/S；仅用程序运输官方结果、检查已有字节绑定，不通过模板、AST、路径、符号或导入生成语义。C policy/feedback、预算和原账本只读，没有跨轨写入。

三个 aoci support 文件不是业务 Entry；数据库 Volume 未启用。测试、历史文档、锁文件、产品仓库/UI、运行目录、B executor/validator/asset store 内部实现及其它核心模块未索引。R 引用未索引路径只标出重要调用契约，不能推出全仓覆盖。AOCI 不成为科研执行依赖、预算或授权来源。

### 11.3 实际 CLI/MCP 与终态检查

以下 CLI 均使用上面的官方绝对 binary，完整 JSON 先落 `.runtime/aoci-core/`，再按真实 schema 选取小字段观察，未把约31MB Scope/完整状态反复注入模型：

```powershell
& $taskAoci index agent guide --agent codex --json
& $taskAoci scan --json
& $taskAoci verify --json
& $taskAoci check --json
& $taskAoci index agent guide --agent codex --json
git diff --cached --check
git ls-remote origin refs/heads/songconmaisaix31-design/morph-r1-research-1003
```

`$taskAoci` 仅表示本机该 binary 的绝对路径，未改变全局 PATH。普通首次 scan exit0：fingerprint_count=13，业务 targets=10；不是重扫或强制覆盖 baseline。Guide 指示 no-argument MCP Maintain，实际完整批次10 candidates，保留其 code_plan.batch_id/candidate_id/source_sha256，经 `aoci_update_entry(entries=完整10项)` 一次原子应用 **10/10，aligned=true，remaining=0，finding_count=0**。

按官方终态顺序 Verify → Aggregate Check → Guide 均 exit0；structure_valid/governance_aligned=true、Guide `stage=aligned,complete=true,next_action=none`。Missing/Stale/Unbaselined/Orphan、observed review 全为空，pending_transactions=0、recovery_pending=false、third_party_conflict=false。支持资产 stage 后再次 Verify 仍同 Composite 且 aligned；没有手工编辑 baseline/ledger。

本 Run 实际原生调用 `mcp__aoci__aoci_rules/maintain/update_entry/overview/search`，服务返回 root 与 rc17 匹配。两次完整 Overview 各 **10 Entries / 3 sections / 2916 estimated tokens**，body_utf8_bytes=9816、无分块；每次严格 Challenge **10/10**，最终 delivery confirmed、attestation pass、governance aligned、cognition assimilation complete，v2 `current_system_cognition_reliable=true`。框架掌握90%为模型自评，只针对所选范围，不代表完整实现/runtime知识。

最终 scope Index `20cc06d43efd858321a49ad6a79235c7d020332c1a0979d620553df07ef9430c`；Composite `2b20d17adec60e2e28a9f51d22502ce3cec7317d0430f972dab62b64b3596de2`；Code Volume `67d2c01f9ac5cd157049547f83d798834f33faa4636d1e73904e62118cddf5b7`。这些均为官方结果，不新增 Hash/Receipt/证明系统。

两轮相同 search 命中相同 Entry：FR04 → service(1)；native → models/service(2)；positive → policy/service(2)；docker_export → dynamic/models(2)。两次完整 Overview 之间，按官方明确 `intent=cognition_optimization,object_refs=[code:swarm/research/knowledge.py]` 返回的完整单对象批次，仅把 knowledge 规模标签 PD8L 校准 PD8M（实际374行），F/R/A/S 和 source binding 保持相同；原子 replaced=1/remaining=0、无 warning。随后再完成 Verify/Check/Guide 与第二次完整 Overview。没有造源文件变化来冒充 source-drift 测试，也没有扩建优化框架。

### 11.4 首失败与完整日志位置

全部原始官方初始化、Scope失败/rollback/explicit observe review、恢复及本轮实际输出保存在本 worktree **`.runtime/aoci-core/`**（本机 Git ignored，不上传秘密或 runtime receipt）。旧初始化完整归档 **`.runtime/aoci-core/failed-init-preserved-20261003T051653763Z/`**；root `msg_a13825ef12b7` 仅授权一次本轨自有未跟踪0Entry初始化保留归档，恢复检查点前已完成，本 Run 未再次归档/init。`init-recovery.json`、`scope-rules-recovery.jsonl`、`scope-recovery-before-scan.json`、`recovery-policy-comparison.txt` 证明 managed_scope/cognition_budget/automation 不变。

- 旧 `scope-support-activate.json` exit2 `managed_scope_source_guard_snapshot_changed`；`guide-support-failed.json` 保留 recovery_pending；`scope-support-rollback.json` 为 rolled_back，后续两次 policy-bound apply 仍保留，不能把历史失败改成绿。
- 本 Run `mcp-maintain-resumed.json`、`mcp-apply-resumed.json` 记录首机器批次/10项apply及knowledge规模warning；`verify/check/guide-established.json` 记录首次终态。
- `mcp-overview-established.json` → `mcp-attestation-established.json` 的首 confirmation version 不匹配：delivery incomplete，严格语义 Challenge已pass；只按[官方规范](https://github.com/aoci-spec/aoci-code/blob/v0.1.0-rc17/spec/public/aoci-overview-delivery-v1.txt)补正确 `overview-delivery-receipt/v1` confirmation（`mcp-delivery-established-corrected.json`），没有语义答案重试。
- `mcp-maintain-optimization.json`、`mcp-apply-optimization.json`、`verify/check/guide-final.json`、`mcp-overview-final.json`、`mcp-attestation-final.json` 为最后对齐和完整认知结果；`mcp-search-first-0..3.json`、`mcp-search-repeat-0..3.json` 为重复检索。
- `source-bindings-first.log` 保留首次本机JSON默认GBK读取的 UnicodeDecodeError，未开始候选比较；显式UTF-8后 `source-bindings-repaired.log` 才得到十源字节相同。`version-first.log` 保留误用 `aoci version` 的 unknown command，正确 `--version` 如前。命令原输出还保留在本 Dispatch工具会话；这些读取错误不改业务源码或阈值。

### 11.5 本机配置、未执行项和交接限制

`.codex/config.toml` 是 ignored 项目绝对 stdio 配置。旧会话仅私有官方 ClientSession initialize/list_tools/call_tool；Orca重启后的本 Run已实际加载原生MCP工具，配置/连接/热加载分别记述。AI endpoint disabled，没有改当前Agent提示、全局 HOME/auth/provider/PATH或加 hooks。AGENTS 是 root独占，其官方init行尾产物按root明确指令恢复原blob；原backup保留并忽略，不进入本次commit。没有原.gitattributes例外被移除，没有 renormalize、批量历史行尾改写。

索引section与本机配置明确绑定 **A worktree绝对目录**。其它checkout直接复用、跨宿主迁移、本索引对I新组合的freshness均未验证；I必须先沿自己的官方Guide核对并执行其实际重新绑定/迁移要求，若十源有delta仍由原A Owner按官方Maintain收口。不能手动替换目录、伪造baseline/receipt、复制P human approval或以全仓clean冒充索引fresh。

实际模型 token用量、成本、节省百分比均 **UNKNOWN**；estimated_tokens只表示工具估算的索引大小。没有重测已绿9PASS/strict2或Q门，没有新COPY/install/build窗口，也未启动OpenCode、Docker/WSL、真实AT07/沙箱/模型科研、L2、外部资料上传、系统清理或发布/main/tag。P受保护配置与未完成human TTY receipt不属本轨；本任务完成不代表完整MVP/R1通过。

## 12. 正式条件适用性定界（2026-10-03 20:01 后继）

原 A 同 worktree/branch、实际进程执行 `task_52a650c20831 / ctx_fc89f40b4357`，未委派新 Agent。先读 root `17d0ff926772d3a9fa65620b733fc2caca0c95a0` 的 R1_PLAN 顶部20:01范围、原 Spec FR13/FR19、C 私有 `c-mvp-policy-audit-1940/ACCEPTANCE.md` 与 opportunity 报告，以及精确 b480 的原 A/B/C 调用。原 A clean `d8af82791fecde1f3dadfbf9190d4cbfada80146` 普通精确 merge 已接受 b480 为 fast-forward；当前源码和本轮 **actualtestedSOURCE 均为 `b480fca1b10a0b6a9c93f0d1801d38f267662461`**，已先 push 原 branch 并由 ls-remote 核对完整 SHA。

本轮没有确认需要修复的新产品首 RED，故仅交本报告和私有调用/测试证据，不新增业务条件契约或修改 C 匹配域。这里不宣称所有适用性问题均已解决，也不把 C 的静态疑点改写成已修复漏洞。

### 12.1 实际入口与语义

`service._research_branches:1286` 仅投影身份/status/parent/authorized；`feedback.advisory:398/422` 每次重读原 accepted 事实、空条件按同路线聚合。`_task_opportunity:1426`、choose、claim 的引用是路线建议，不能直接产生科学结果或采用回执。正式 propose_work:903 没有 hypothesis/conditions 选择器；`Hypothesis.conditions` 虽由 `knowledge.put_hypothesis:167` 持久且不可变，`submit_note:864/894` 的正式 hypothesis 入口仍保留 note.applicability、创建空 conditions 的 proposed Hypothesis。成员 note 不是可信不适用裁决，多假设可属于同一路线；不能手造 C Branch 或把调用方文本变成权威事实来构造产品首 RED。

B 的 `generated_conditions`（local_assets/generated_validation.py:35）从原冻结 plan 绑定程序/数据/环境/参数/seed/评价/资源/claim/hypothesis；`read_generated_observation:224` 重读原归档。`trusted_generated_feedback` 再核对原 ledger/attempt/token/audit/asset/冻结评价，C 独立复核要求相同条件。`service.inherit:584/apply:614` 复用原 `require_inheritance`，要求源条件匹配及消费 task 的本地再验证。参数/seed不同不天然证明路线不适用，但它们改变旧资产 PASS 的精确复用条件；路线引用不能绕过此门。

私有正式 service fixture 实际观察：同路线新 claim/hypothesis 在接受旧证据后仍有路线份额 `0.5571428571428573` 和原 result ref，且可准备**独立新候选**；新 task 没有执行审计、结果、可信 observation 或 adoption。该现象只证明广义路线建议，不证明旧结果支持新主张。复用旧 asset 时，分别改变 hypothesis、parameters 或 seeds，正式 prepare 都以 `generated_candidate_conditions_mismatch` 拒绝，未冻结/执行新 task，原 report 历史和路线正证据保留。即使条件相同，没有消费 task 自身 inheritance observation，inherit 仍以 `local_revalidation_required` 拒绝。

另一个由正式 create_branch 创建的子路线，即使引用旧 result 且提交新 hypothesis/applicability，也不获得原路线 supported_by，证据先验仍 .5。旧正证据不会全部消失来“绿测试”。旧同条件独立复现→本地再验证→应用采用正对照仍通过，unknown 不重试与 MCP 自报审批/环境拒绝对照仍通过。

**覆盖限制**：这些入口没有逐 hypothesis 的权威适用性选择或 branch-wide 不适用契约；未评估每条路线引用对所有后续问题的科学相关性，不能签完整 FR13。改变条件后的真实论证、科研再验证与实际继承仍属 L2，不能从本轮 mock 得出。若未来明确这种契约并给出 formal 首 RED，再按原 Owner Handoff 修正；本轮不创造第二条件注册表/哈希/manifest/proof/调度或新评分机制。

### 12.2 验证与不可覆写首失败

本轮复用原 A `.venv-r1-a`，actual import 路径为本 worktree 的 swarm/research/service.py；是精确 checkout 调用证据，**不是新 noneditable COPY installed 验收**。只对本轨 Python 子进程设置 OPENBLAS/OMP/MKL 线程数1。私有测试复用原 service 的 host-selected inert mock、原 ledger/asset/archive/独立复核，autouse fixture 禁止候选子进程和网络，仅允许受信 Git。未手造 policy Branch 或 caller trusted 事实。

```powershell
./.venv-r1-a/Scripts/python.exe -m pytest -q -s -o cache_dir=C:/research-private/a-route-conditions-1003/pytest-cache --basetemp=C:/research-private/a-route-conditions-1003/tmp-first C:/research-private/a-route-conditions-1003/test_route_conditions.py
./.venv-r1-a/Scripts/python.exe -m pytest -q -s -o cache_dir=C:/research-private/a-route-conditions-1003/pytest-cache --basetemp=C:/research-private/a-route-conditions-1003/tmp-repaired C:/research-private/a-route-conditions-1003/test_route_conditions.py -k 'same_route or changed_frozen'
./.venv-r1-a/Scripts/python.exe -m pytest -q -o cache_dir=C:/research-private/a-route-conditions-1003/pytest-cache --basetemp=C:/research-private/a-route-conditions-1003/tmp-controls 'tests/research/test_dynamic_service.py::test_dynamic_service_original_inheritance_apply_receipt_is_explicitly_mock' 'tests/research/test_dynamic_service.py::test_dynamic_service_failure_is_not_refutation_and_unknown_is_not_retried[unknown]' 'tests/research/test_dynamic_service.py::test_dynamic_mcp_preparation_rejects_self_declared_approval_and_environment'
```

| 证据 | 结果 |
|---|---|
| conditions-first.log | **2 PASS / 4 FAIL / 30.66s，exit1**。四失败均为私有测试误将 SQLite 的 unconfirmed_request_id 当 TaskRecord 属性；三个正式条件拒绝断言已先通过。不是产品首 RED。 |
| test_route_conditions-first-preserved.py | 原首轮测试正文另存，不改首断言/日志。 |
| conditions-repaired-four.log | **4 PASS / 2 deselected / 26.92s，exit0**。只重跑四失败；改用原 ledger SQL 读取相同字段，并检查没有 execution 审计，不削弱原断言。 |
| controls-first.log | **3 PASS / 22.78s，exit0**。仅上述三个必要旧正/负对照。 |

首轮已绿两例没有重跑，不把原结果改写为首轮6绿。全部原证据、私有新测试和完整报告在 `C:/research-private/a-route-conditions-1003/`，主报告 `ACCEPTANCE.md`；identity-first.log 保留 b480 与实际 import 身份。仓库只追加本文件，未新增仓库测试。业务 source 无 delta，适用 changed-source strict/build 为 N/A；未重跑旧43/68/141/1745、完整产品256、UI126/browser8 或 B/Q AT07 门。

### 12.3 成本、AOCI 与交付限制

正式 known_cost 均为 None、理由 unknown_cost；当前 service 没有可信成本源/单位投影。原 generated payload usage/cost_usd 也为 None；fixture budget 的 tokens/actual_cost_usd 实测仍为 None。授权上限、预留估计和 admission charge 不是账单或实测验证成本。成本敏感机会分配、模型实际 Token/费用/节省均 **UNKNOWN/coverage limitation**，不填0或新数字。

本 Run 实际读 rc17 rules 和原 A root 的完整10Entry Overview（2916 estimated tokens），没有复用旧 receipt。Attestation 首次 object_ref 字段被 schema 拒绝，一次改成 path 的字段修正也被拒绝；两原错误保留，不再语义重试或声称当前认知 verified。check-only 报 semantic_change_count=0、governance aligned、host_delivery_incomplete、current_system_cognition_reliable=false，当前模型 receipt **NOT_VERIFIED**。

消费 b480 后，原 d8af827→b480 的十项 managed 源 diff 全为空；仅本报告与私有证据变更，均不在十源 managed scope，无维护/apply必要。官方绝对 binary 的 Verify→Check→Guide 新证据全 exit0，structure/governance aligned，Guide aligned/complete=true/next_action=none（私库 aoci-verify/check/guide.json）。这只是结构/freshness事实，不补造本 Run Attestation，不改 P 受保护输入、不重置索引，不证明 I 跨checkout认知。

SOURCE 继续为已接受 b480，先普通push；后继 REPORT 为本文件单一 docs-only commit `[skip ci]`，最终 full SHA/remote exact/clean 在终态消息给出。不从 REPORT pin。产品2b9bf73/I a67只作为事实基准，未重装重测。唯一原 I 负责后继精确组合与最终一次离线门，原 P 最终repin。

真实 Engine/key/SDKcreate/native模型/候选科研/新材料导入/AT07/L2/main/tag/deploy 均 **NOT_RUN**。本轮条件定界完成不代表 FR13 全场景、FR19 task_live 或完整 MVP/R1通过；如无新 formal 反例，不要求 C 重新开发或重签旧门。
