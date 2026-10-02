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
