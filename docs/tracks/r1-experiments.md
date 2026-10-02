# R1 B · 动态候选、隔离执行、可信评价与真实继承（返修后）

B 轨（长期 Owner，`morph-r1-experiments-1003`）交付动态 Python 候选实验的版本化契约、
隔离执行安全路径、可信三轴评价、成果准入与继承接线。首版 `fbee1e5` 被独立 Q 拒绝验收，
本返修修正全部阻断项；历史冻结核心 `7062a63` / 报告 `326fd8f` 与旧 `registered_case` /
`CaseId` / `ScientificCriteria` / `literal-files-v1` 字节等值语义保持不变，新能力以
`generated-experiment/v1` 版本化并存。

## 首版诚实纠正（不擦除）

首版 `tests/experiments/generated_helpers.py` 的 `MockGeneratedSession.run` 用
`subprocess.run([sys.executable, *argv[1:]])` 在宿主实际执行了候选（Poisson 求解器）以产生
输出；当时 98 passed 因此不能声称隔离路径通过。已删除该执行能力：fixture 现按计划 case
固定原始输出（`poisson_reference_output/wrong_output/scored_output`），mock 只写固定字节，
不 exec/eval/解释候选。首版提交与首失败历史原样保留于 Git。

## 信任边界（修复 Q 6 项 RED 的核心）

`EvaluationSpec.approved/approved_by` 与 `IsolationReport.verified/probe` 均为**仅展示**字段，
执行器/评价器从不据此授予最终结论或执行准入：

- 评价：`evaluation.evaluate` 只做宿主重算，**恒返回 `mode="diagnostic"`、`contribution="proposed"`**；
  最终科学结论由 `trusted.finalize_assessment` 仅在宿主 `TrustedCriteriaRegistry` 批准该 criteria
  版本、执行 `succeeded` 且 `remote_effect="known"` 时授予 `mode="final"`（贡献接受仍是 C 的独立复核）。
- 隔离：`GeneratedExperimentExecutor.admit` 只信宿主 `TrustedProbeRegistry`（`backend`+`declared`
  匹配且真实无害探针 `passed`）；mock/caller 的 `verified=True` 不能放行。无证明 fail-closed，
  宿主从不执行候选。
- `read_generated_result` **总是**从原始输出重算评估（丢弃存档里伪造的 `accepted/final/trusted`），
  并要求 `outputs/output.json` 有 digest 绑定（`missing_durable_evidence`）、输入/data digest 与整计划绑定。

## FR → 源码 → 契约 → AT 映射

| FR | 实现 | 契约/入口 | AT |
|---|---|---|---|
| FR-15 新候选程序 | `generated.py`（`GeneratedFile` manifest；候选字节≠注册示例） | `GeneratedExperimentPlan` | AT-05 |
| FR-16 计划冻结/判据写权 | `EvaluationSpec`（宿主冻结 domain/reference/tolerance/properties）+ `TrustedCriteriaRegistry` | `finalize_assessment` | AT-06 |
| FR-17 检查后隔离执行 | `security.py`（scope/syntax/dependency/danger/resource）+ `verify_isolation(isolation, registry)` | `admit` | AT-07/AT-15 |
| FR-18 可信判定/独立复核 | `evaluation.py`（Poisson 参考 + 通用性质模板，从原始输出重算，自报 score 拒绝） | `GeneratedAssessment` 三轴 | AT-06/AT-08/AT-12 |
| FR-19 真实继承 | 复用 `AssetConsumer`/`AssetApplicator`/`AdoptionReceipt` 原链；`approve_generated` 带 `assert_owned` 围栏 | `AdoptionReceipt` | AT-13/AT-17 |
| FR-20/26 输出与回归 | `GeneratedResult` 持久 archive；`read_generated_result` 重算；旧两类 case 全绿 | `GeneratedResult` | AT-17/AT-18 |

新增完整冻结身份：code/file digest、`data` manifest digest、`image_digest`（不可变 `@sha256:`，
`admit` 拒绝可变 tag）、`dependency_lock_sha256`、parameters/seed、evaluation version/tolerance、
author/reviewer 授权（宿主身份，非 caller 字符串）。

## 最小 API Handoff（A 正式 MCP；C 三轴反馈；P 产品）

- **DynamicPlan**：`orchestration.experiments.generated.GeneratedExperimentPlan`。
- **执行**：`GeneratedExperimentExecutor(backend, probe_registry=..., criteria_registry=...)`
  `.prepare(plan, files, data=None)` / `.admit(prep)` / `.execute(plan, context, files, archive_root, data=None)`；
  `read_generated_result(archive_root, run_id, expected_plan, expected_context)` 重算可信评估。
- **宿主信任**：`TrustedCriteriaRegistry` / `TrustedProbeRegistry` / `IsolationProbeRecord` /
  `finalize_assessment`（`trusted.py`）。
- **准入/应用/消费**：`local_assets.generated_validation.generated_validation(store, asset_id, plan, files,
  isolation, probe_registry=...)` → `approve_generated(store, report, assert_owned, proof_ref=...)` →
  复用 `AssetConsumer.execute/record_adoption` 与 `AssetApplicator.prepare/apply`。
- **播种**：`swarm.research.case.seed_generated_case(...)`（不生成代码/不执行）。
- **可信结果字段**：`GeneratedAssessment{execution, hypothesis, contribution, mode, trusted,
  evaluator_version, metrics, candidate_self_score, proof_ref}`。
- **本地 CPU 隔离适配**：`LocalCpuSandboxBackend(..., probe=IsolationProbeRecord | None)`；
  `registry_with_probe(record)` 供宿主在真实探针完成后登记；本轮 `probe=None` → fail-closed。

## 成熟依赖来源/版本/许可证

| 依赖 | 版本 | 许可证 | 边界 |
|---|---|---|---|
| OpenSandbox SDK（`opensandbox`/`opensandbox-code-interpreter`） | 1.1.0（已锁） | Apache-2.0 | 复用生命周期/文件/命令/资源与网络控制，不套用最新 API |
| pydantic | >=2.11 | MIT | 契约 |
| numpy / scipy | 已装 | BSD | 仅候选批准环境可选；宿主评价器只用 stdlib `math` |
| httpx | >=0.28 | BSD | 传输 |

未新增运行时依赖；`pyproject.toml`/`poetry.lock`/`THIRD_PARTY_NOTICES.md` 本轮无需改动。

## 验收与真实限制

- 本轨测试：`tests/experiments/test_generated_{experiment,evaluation}.py`、
  `tests/local_assets/test_generated_validation.py`、`tests/research/test_generated_candidate.py` 共 **28 passed**；
  连同 `tests/experiments/`（含旧两类 registered 全回归）、`tests/research/test_case.py` 共 **102 passed**。
- 独立 Q 负例 `tests/integration/r1_security/test_b_generated_boundaries.py`（`morph-r1-boundaries-1003`）
  对返修后代码运行 **13 passed**（unverified/mock boolean 不放行、caller approved+reviewer 不给 final、
  全计划绑定拒绝变更、自报 score 拒绝、unknown/crash/timeout 不保留伪造奖励、unknown effect 不给 final、
  succeeded 缺 output digest 绑定拒绝）。
- 静态边界：`tools/typecheck.py`（mypy --strict，129 文件）**Success，0 错误，未扩大豁免**。
- AT-07 真实隔离探针与 L2 真实科研切片 **NOT_RUN**（无授权）：`LocalCpuSandboxBackend` 无探针记录时
  fail-closed，dynamic 本轮仅契约 fixture 安全验证实现能力，不声称 live。
- 环境限制：本 worktree 无 `node_modules`（Node GEP SDK），既有 `NodeAssetBridge` 用例以
  `sdk_process_failed` 失败，属环境缺 node 依赖；新生成用例用 `FakeBridge` 离线注入，不依赖 node。

## 未执行/待协作

- 真实沙箱探针、真实科研切片、云/GPU 后端、Hub 发布：未获授权，NOT_RUN。
- A 正式 MCP 接线、C 三轴贡献接受（绑定 `proof_ref`）、P 产品 UI 由各自 Owner 消费上述 Handoff；独立 I 最后集成。
