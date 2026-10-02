# R1 B · 动态候选、隔离执行、可信评价与真实继承

B 轨（长期 Owner，`morph-r1-experiments-1003`）交付动态 Python 候选实验的版本化契约、
隔离执行安全路径、可信三轴评价、成果准入与继承接线。历史冻结核心 `7062a63` / 报告
`326fd8f` 与旧 `registered_case` / `CaseId` / `ScientificCriteria` / `literal-files-v1`
字节等值语义保持不变；新能力以 `generated-experiment/v1` 版本化并存，不改旧行为。

## FR → 源码 → 契约 → AT 映射

| FR | 实现 | 契约/入口 | AT |
|---|---|---|---|
| FR-15 新候选程序 | `orchestration/experiments/generated.py`（`GeneratedFile`/manifest）；候选字节≠注册示例，独立 `candidate_revision` | `GeneratedExperimentPlan` | AT-05 |
| FR-16 实验提议与计划 | `GeneratedExperimentPlan`（参数/seed/环境/评价/资源/授权全部冻结，`Contract` frozen）；`EvaluationSpec.approved` 门控可信判据写权 | `EvaluationSpec`，`prepare` | AT-06 |
| FR-17 检查后隔离执行 | `orchestration/experiments/security.py`（scope/syntax/dependency/danger/resource 静态门）+ `IsolationReport.admitted`（fail-closed）；宿主从不执行候选 | `static_checks` / `verify_isolation` | AT-07/AT-15 |
| FR-18 可信判定与独立复核 | `orchestration/experiments/evaluation.py`（Poisson 参考 + 通用性质模板，从原始输出重算）；`GeneratedContext` 强制 reviewer≠author | `GeneratedAssessment`（execution/hypothesis/contribution 三轴） | AT-06/AT-08/AT-12 |
| FR-19 真实成果继承 | 复用既有 `AssetConsumer`/`AssetApplicator`/`AdoptionReceipt`/`ConsumptionExecution`；`local_assets/generated_validation.py` 的 `generated_validation`/`approve_generated`/`generated_candidate` 接入准入与应用 | `AdoptionReceipt` 原链 | AT-13/AT-17 |
| FR-20 结果输出 | `GeneratedResult` 持久 archive（plan.json/result.json/inputs/outputs/sandbox/execution/runtime），`read_generated_result` 重算 | `GeneratedResult` | AT-17/AT-18 |
| FR-26 结果输出/回归 | 旧两类 case 原测试全绿；新 schema 显式 `generated-experiment/v1`，旧客户端无法把未知 CaseId 塞入旧接口 | 分版本拒绝 | AT-17 |

## 最小 API Handoff（供 A 正式 MCP 接线；C 三轴反馈；P 产品入口）

- **DynamicPlan**：`orchestration.experiments.generated.GeneratedExperimentPlan`（`schema_version="generated-experiment/v1"`）。
- **执行流水**：`GeneratedExperimentExecutor.prepare(plan, files)` → `.admit(prep)` → `.execute(plan, context, files, archive_root)`；`read_generated_result(archive_root, run_id, expected_plan, expected_context)` 重算可信评估。
- **准入/应用/消费**：`local_assets.generated_validation.generated_validation(store, asset_id, plan, files, isolation)` → `approve_generated(store, report)` → 复用 `AssetConsumer.execute/record_adoption` 与 `AssetApplicator.prepare/apply`。
- **播种**：`swarm.research.case.seed_generated_case(...)`（不生成代码/不执行，仅入账与写 HostConfig）。
- **可信结果字段**：`GeneratedAssessment{execution, hypothesis, contribution, mode(diagnostic|final), trusted, evaluator_version, metrics, candidate_self_score}`。
- **本地 CPU 隔离适配**：`LocalCpuSandboxBackend`（复用 OpenSandbox SDK 1.1.0 生命周期，`isolation()` 返回 `IsolationReport`；本轮 probe `not_run` → `admitted=False` 拒绝执行）。

A 只接 service/server/HostConfig 与 MCP；C 消费三轴 `GeneratedAssessment` 做贡献/路线/可靠性分离；P 用 `seed_generated_case` 与 `GeneratedResult` 展示时间线与成果视图。

## 三轴与安全边界

- `execution ∈ {not_run,running,succeeded,failed,cancelled,unknown}`、`hypothesis ∈ {not_evaluated,supported,refuted,inconclusive,disputed}`、`contribution ∈ {proposed,accepted,rejected,superseded}`。执行成功但假设被否（`succeeded/refuted`）可保留为反例贡献；崩溃/超时 → `failed/not_evaluated`，绝不 `refuted`。
- 静态门先于隔离：scope（保留名/重复）、syntax（ast+compile）、dependency（allowlist：safe stdlib ∪ 批准依赖；未批准依赖拒绝）、danger（eval/exec/subprocess/socket/os/… 拒绝）、resource（大小/数量）。静态不证明安全。
- 隔离逐项：无宿主写/无凭据/无宿主控制/无特权/导出受限/网络 deny/CPU/内存/进程/时间上限/自有资源清理。`IsolationReport.verified` 必须真实探针证明；mock/声明不得升级为 real，无证明即 `unsupported`，宿主绝不执行候选。

## 成熟依赖来源/版本/许可证

| 依赖 | 版本 | 许可证 | 边界 |
|---|---|---|---|
| OpenSandbox SDK（`opensandbox`/`opensandbox-code-interpreter`） | 1.1.0（已锁） | Apache-2.0 | 复用生命周期/文件/命令/资源与网络控制，不套用最新 API（未查最新上游，只据已装源码） |
| pydantic | >=2.11 | MIT | 契约 |
| numpy / scipy | 已装 | BSD | 仅候选批准环境内可选，宿主评价器只用 stdlib `math` |
| httpx | >=0.28 | BSD | 传输 |

未新增任何运行时依赖；`pyproject.toml`/`poetry.lock`/`THIRD_PARTY_NOTICES.md` 本轮无需改动。

## 验收与真实限制

- L0 契约/确定性：`tests/experiments/test_generated_experiment.py`(13)、`test_generated_evaluation.py`(6)、`tests/local_assets/test_generated_validation.py`(4)、`tests/research/test_generated_candidate.py`(1)；连同 `tests/experiments/`(全部)、`tests/research/test_case.py` 共 **98 passed**。
- 负例覆盖：非模板候选、评价变更/自报 score 拒绝、未批准镜像/依赖、超范围/危险 import、unverified 隔离拒绝执行、崩溃不反证、输出有效但 refuted 保留、author 自评拒绝、篡改重算拒绝。
- 静态边界：`mypy --strict orchestration local_assets swarm` 与 `tools/typecheck.py`（128 文件）均 **Success，0 错误，未扩大豁免**。
- AT-07 真实隔离探针：本轮 **NOT_RUN**（未获真实沙箱/探针授权）；`LocalCpuSandboxBackend.isolation().probe="not_run"` → fail-closed。L2 真实科研切片同样 **NOT_RUN**。
- 环境限制：本 worktree 无 `node_modules`（Node GEP SDK），`tests/research/test_registered_cases.py` 与 `tests/local_assets/test_research.py` 的既有 `NodeAssetBridge` 用例以 `sdk_process_failed` 失败，属环境缺 node 依赖，非本轮改动引入；新生成用例用 `FakeBridge` 离线注入，不依赖 node。

## 未执行/待协作

- 真实沙箱探针、真实科研切片、云/GPU 后端、Hub 发布：未获授权，NOT_RUN。
- A 正式 MCP 接线、C 三轴反馈策略、P 产品 UI 由各自 Owner 消费上述 Handoff；独立 I 最后集成。
