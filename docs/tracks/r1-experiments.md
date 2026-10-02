# R1 B · 2026-10-03 恢复后的配置、结果与继承返修

当前依据 `docs/source/Morphogenesis_Research_Swarm_Spec_v1.0_2026-10-02.md` 的 FR-15 至 FR-20；
下方旧报告的 FR-26 标记只保留作历史，不替代当前 Spec。

本轮沿用原 B worktree/分支与所有权。`d175f7e2f8c3ff41a1ac8a2a4958c68acf57e275`
**NOT_ACCEPTED**：Q 精确归档原 29 项是 **21 PASS / 8 FAIL**，后补输入绑定是
**1 PASS / 7 FAIL**。下文历史报告的“修正全部”以及 18/102 PASS 只描述当时窄范围，
不覆盖这些后发现的问题；原提交、Q 原始 RED 和 AT-07/L2 NOT_RUN 均保留。

本轮源码阶段：`e8e16a5b9e755a94f8587b76ba9fc288f218b8af`（配置绑定与原报告）；
`d0c834fd381fc292443bf85c5ce1e91043143516`（隔离 fixture 继承模式）；
`56b8db589ee04bcc41652bb5e38793a1216f9a1a`（安装包内固定输出后端）；
`2d50d08811aa2337b9c0166dc114513e292bce1f`（复用时重读存档、应用前后围栏与回滚）；
最终 SOURCE **`5faafe41b1732c83d165251600b688444186c702`**（保留危险代码的结构化拒绝报告）。
每阶段均普通 commit/push 并核对远端精确 SHA。报告单独提交，不用报告 SHA 代替 SOURCE。

## 本轮修改与权威边界

- 探针比较完整有效配置：规范化 repository@sha256 镜像及实际 `image_digest`、Python/SDK、
  dependency lock、endpoint、backend instance/runtime profile、网络、全部资源和服务端进程限制。
  `prepare` 保存快照，`admit` 重算当前配置和候选字节，`LocalCpuSandboxBackend.create` 独立拒绝
  未验证或不支持的设置。重复 probe ID 不同记录拒绝；完全相同记录可重复提供。
- SDK 1.1.0 没有进程限制创建参数，默认 `process_limit=False`。只有宿主配置的、与探针精确
  匹配的服务端固定进程限制才可声明支持；未实际探针的部署不能据测试夹具启用。SDK 请求使用
  `NetworkPolicy(defaultAction="deny")`，固定镜像传 `repository@sha256`，没有实际 SDK 调用。
- 候选验证绑定已发布 Candidate 的 asset ID、base revision、scope、变更字节、ResearchClaim 和
  冻结条件。code/data 重名、重复 data、运行器保留名、输入总大小超限拒绝。发布先产生 asset ID，
  再写入冻结计划，候选地址不包含自身 ID，避免循环身份。
- `record_generated_observation` 写入原 `research_reports`，`read_generated_observation` 只读
  核对原 archive/plan/context/candidate/criteria approval 并重算；没有新完成账本。判据批准在
  执行前冻结，晚批准不能追认旧输出；静态 `approve_generated` 不是科学评价或贡献接受。
- `source_attempt` 是当前执行任务的原始 AttemptId，`source_fencing_token` 是该执行 token；
  `Candidate.attempt` 单独标记原作者。A 绑定原 TaskLedger/audit/completion；C 独立复核这些事实，
  科学贡献在 B 恒为 proposed。
- 复用原 AssetConsumer/AssetApplicator/TaskLedger.submit/AdoptionReceipt。默认 live 仍拒绝
  mock 科学结果。显式 mock 模式只用于专用 fixture 项目：资产根和应用目标受 workspace 范围
  约束，同一 SQLite 库保存不可变的模式/fixture 路径配置，跨模式重开拒绝，消费与回执标 mock。
  旧无 provenance 的回执仍可读且保持原 JSON 形状；旧 registered/literal 准入语义不放宽。
- `GeneratedFixtureBackend` 是安装包内固定输出适配器，整个 session 只保存内存字节，禁止
  候选解释、进程及网络。宿主明确选择 mock 并提供输出；它的 fixture 探针记录不能授权真实后端。
- 发现 Q 在 `56b8db5` 上的原始输出/判据/环境存档变更仍能沿缓存 PASS 复用后，保留其
  **9 PASS / 3 FAIL**；B 原断言首次也 **2 FAIL**。现在每次生成成果准入、应用前和应用后，
  都用宿主注入的同一 `generated_criteria` 重读原存档。注册表缺失/变化拒绝，应用后发现变更
  使用原快照回滚；已存历史回执不抹除，也不因此声称当前存档仍有效。

## 已交给 A/C/P 的可调用接口

```python
executor = GeneratedExperimentExecutor(backend, probe_registry=host_probes,
                                       criteria_registry=host_criteria)
preparation = executor.prepare(plan, files, data)
executor.admit(preparation)
result = executor.execute(plan, context, files, archive_root, data)
result = read_generated_result(archive_root, context.run_id,
                               expected_plan=plan, expected_context=context)
diagnostic = executor.evaluate(result, context)  # 只返回 diagnostic/proposed。
# 以下函数位于 local_assets.generated_validation。
payload = generated_result_payload(result, criteria_registry=host_criteria)
# report 阶段就是这个原 research_reports 写入入口，不另建报告事实层。
report = record_generated_observation(store, asset_id, archive_root=archive_root,
    plan=plan, context=context, purpose="original", criteria_registry=host_criteria,
    assert_owned=assert_owned, source_swarm_id=swarm_id,
    source_attempt=execution_attempt, source_fencing_token=context.fencing_token)
verified = read_generated_observation(report, criteria_registry=host_criteria)
```

`result_json` 固定键：`schema_version`, `effect_state`, `execution_state`, `scientific_verdict`,
`provenance`, `sandbox_id`, `experiment_result`, `generated_assessment`, `criteria_approval`,
`usage`, `cost_usd`。使用量/费用保持 null。`generated_conditions(plan)` 使用冻结代码、数据、环境、
参数、种子、判据和条件，排除 task/run/asset ID；复现和继承使用新任务计划且保留同一科学条件。

正式安装工厂可用 `GeneratedFixtureBackend(environment=..., resources=..., output=固定宿主字节,
instance_id=..., outcome=...)`，执行器接其 `probe_registry`，来源保持 mock。
消费/应用使用原 `AssetConsumer.inject/execute/record_adoption` 与
`AssetApplicator(..., policy_version="generated-isolation-v1").prepare(...).apply(assert_owned)`。
mock store 需显式 `LocalAssetStore(..., research_provenance="mock", fixture_workspace=...,
generated_criteria=host_criteria)`；重开仍需注入相同的宿主判据。live 生成成果复用同样需
`generated_criteria`，报告只读路径仍直接使用 `read_generated_observation`。这些都是宿主配置，
不是工具参数或调用者传来的执行许可。

## 本轮阶段验证（L0/mock；不代替最终组合）

私有环境为本 worktree `.venv`，`uv venv --python C:/Python313/python.exe` 后只从本仓库未改动的
`poetry.lock` 导出固定版本，使用局部 `.runtime/uv-cache` 和 COPY 安装；未修改借用/全局环境。
`uv pip check --python .venv/Scripts/python.exe`：102 个安装包兼容。实际 SDK=1.1.0。

| 检查 | 本轮首次结果 |
|---|---|
| 原 Q 四文件 29 项，保留 Q 进程/网络禁止 conftest | 29 PASS，20.12s |
| Q 新输入绑定 8 + 配置截获 15 项，合法配置正例确实调用截获点 | 23 PASS，1.74s |
| Owner SDK 配置/变更/直接创建/快照 22 项 | 22 PASS，0.96s |
| 原动态领域 28 项 | 28 PASS，10.03s |
| 原资产报告写入/重读/围栏/晚批准/伪造/复现 12 项 | 12 PASS，2.94s |
| 原消费/本地再验证/受围栏应用/采用与模式边界 4 项 | 4 PASS，13.30s |
| mock/report/旧 JSON 合并检查 | 17 PASS，11.89s |
| 安装包内 fixture 后端 | 6 PASS，0.62s |
| 原始存档变更拒绝：不改首 RED 断言的返修复核 | 6 PASS，17.26s |
| 受围栏应用前/后变更与快照回滚 | 8 PASS，31.46s |

## 最终源码验证与第一失败

协调器于 18:38 UTC 授予 B 独占重型窗口；使用进程局部
`OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=MKL_NUM_THREADS=1`，所有安装/pytest/Node 顺序执行。
`npm ci --no-audit --no-fund --cache .runtime/npm-cache`：exit 0，99 packages；未修改锁文件。

领域首次命令 `python -m pytest tests/experiments tests/local_assets
tests/research/test_generated_candidate.py tests/research/test_case.py tests/swarm/test_assets.py -q --tb=short`
在 `2d50d08` 上 **244 PASS / 1 FAIL，175.84s**：已有危险代码测试要求结构化拒绝报告，
新增 Candidate 检查提前抛出 `dangerous_import`。保留 `.runtime/broad-domain-first.txt`；
`5faafe4` 保留原断言及安全拒绝，把静态失败与候选错误纳入拒绝报告。该文件重跑
**5 PASS，1.80s**；静态通过但候选绑定错误仍抛异常，失败报告不能批准。

`python tools/typecheck.py`：**PASS，130 source files**（`.runtime/strict-first.txt`）。
Q 的七个 B 安全文件在最终 SOURCE、私有 Python 下执行，原禁止进程/网络 conftest 仍启用：
**68 PASS，9.02s**（`.runtime/q-final-first.txt`），覆盖 29 原边界、23 配置/输入与 16 原链
mock 消费/存档/回滚检查；合法配置正例实际到达一次被截获的 SDK create，不是全拒绝空通过。
Q 独立精确 `2d50d08` 已报告 **68 PASS，10.28s**，属于其所有者证据，不混为 B 最终重跑。

最终同一领域命令在 SOURCE `5faafe4`：**245 PASS，345.21s**，exit 0
（`.runtime/broad-domain-final-first.txt`），包含旧注册案例、原 literal 资产验证/应用和新动态路径。
七个 Q 文件为 `test_b_generated_boundaries.py`, `test_b_successor_authority.py`,
`test_b_sdk_configuration.py`, `test_b_probe_configuration.py`, `test_b_input_binding.py`,
`test_b_configured_sdk_boundary.py`, `test_b_mock_adoption.py`；在 Q worktree 设置
`R1_SECURITY_SOURCE` 为 B 根，用 B `.venv/Scripts/python.exe -m pytest
tests/integration/r1_security/<上述文件> -q --tb=short` 执行，不修改 Q 文件或断言。

安装验证顺序（全部 exit 0）：

```powershell
uv build --wheel --out-dir .runtime/wheels --python .venv/Scripts/python.exe
uv pip install --python .venv/Scripts/python.exe --no-deps .runtime/wheels/morphogenesis-0.1.0-py3-none-any.whl
# 在 .runtime 工作目录执行：
../.venv/Scripts/python.exe -I installed_smoke.py
# 回到 B 根目录：
uv pip check --python .venv/Scripts/python.exe
```

wheel 共 195 项，检查无 `.runtime`/`.venv`/`node_modules`/测试/仓库文件；构建器关于仓内
cache 的通用提示未对应实际打包泄漏。`direct_url.json` 确认为 wheel 且非 editable；
`-I` 导入落在本私有 `.venv/Lib/site-packages`，没有导入测试 helper。固定输出适配器走
prepare/admit/execute/archive/read、静态准入与原 `research_reports` 写入/重读：**PASS**，
原报告 1、adoption 0、provenance mock、cost null；同时确认静态批准不能越过独立复现门槛。
smoke 全程禁止 `subprocess.Popen`、`os.system`、socket connect；候选仍是未执行的注释字节。
这里 GEP 使用确定性 fixture，正式 GEP/原消费链由上述领域回归覆盖，不将安装 smoke 说成
正式 MCP/HTTP/UI 验收。最终 `uv pip check`：**103 packages compatible**。

原始本轮命令输出保留在 `.runtime/*first.txt`；该目录是本地运行产物，不提交。Q 首 RED
保留在 Q 分支 `tests/integration/r1_security/evidence/b-d175f7e-{exact,input-binding}-first.txt`。
C 已报告其 SOURCE `38eae47e2961e10e9cf492fe99ea02f418d57dc9` 实际消费 B writer/reader 到
trusted/accept 与下一机会引用，generated 28 PASS（C 所有者证据，B 未冒充独立重跑）。
## 接线证据与剩余范围

A SOURCE `0bcb320e843839f5f043fccd9f705d9dd9b7299e` 已报告普通合入 B `2d50d08`，
实际正式服务 fixture 走 prepare/freeze/admit/executor/archive/audit/report/complete，及独立
review、后续 discover/choose/claim 与原消费/受围栏应用/mock adoption；A 的 7 项动态 fixture
通过属 A 所有者证据。最终 `5faafe4` 已交给 A/C/P/Q；B 未把他们的验证冒充自己重跑，未替代
独立 I 最终集成。B 重型窗口在全部进程退出后已明确归还协调器，报告与源码分开提交。

本交付完成 B 配置绑定、可信原报告与显式 fixture 原链返修的 `contract_local` 及私有安装
验证。全仓 full pytest、正式 MCP/HTTP/UI 安装验收由对应 Owner/集成轨负责，本轮 B
未执行。真实探针、科学运行、模型、真实沙箱、外部研究材料、Hub、部署及 L2 均 **NOT_RUN**；
AT-07 真实隔离证明仍未取得，默认真实后端保持拒绝。需要后续有授权的宿主真实探针确认精确
image/endpoint/instance/runtime/network/resources/process 限制，才可另立真实运行证据。
使用量与费用仍 unknown/null，mock 采用不代表真实科学贡献或 live 运行。

---

# 历史：R1 B · 动态候选、隔离执行、可信评价与真实继承（d175 之前的返修记录）

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

- 评价：`evaluation.evaluate` 只做宿主重算，**恒返回 `mode="diagnostic"`、`trusted=False`、`contribution="proposed"`**；
  最终科学结论由 `trusted.finalize_assessment` 仅在宿主 `TrustedCriteriaRegistry` 批准该 criteria
  版本（同版本不同 spec 构造 registry 时 `criteria_version_conflict` 拒绝，不静默覆盖）、执行 `succeeded`
  且 `remote_effect="known"` 时授予 `mode="final"`+`trusted=True`；诊断路径清 `trusted`、复位 `contribution`。
- 隔离：`GeneratedExperimentExecutor.admit` 只信宿主 `TrustedProbeRegistry`，**按 `proof_ref`（probe_id）+
  backend + declared 精确绑定**；report 的 `proof_ref` 为空/异值不能复用 record；mock/caller 的
  `verified=True` 不能放行。无证明 fail-closed，宿主从不执行候选。
- `read_generated_result` **总是**从原始输出重算评估（丢弃存档里伪造的 `accepted/final/trusted`），
  并要求 `outputs/output.json` 有 digest 绑定（`missing_durable_evidence`）、输入/data digest 与整计划绑定。

## 第二次返修（Q 扩展 suite + 真实 API 接线条件）

- 隔离证明绑定 `proof_ref`：`TrustedProbeRegistry.is_verified` 以 `probe_id` 为键并要求 report 的
  `proof_ref`、backend、`declared` 与 record 全等，空/异值引用拒绝（`test_registered_probe_cannot_authorize_different_or_missing_reference`）。
- 真实 SDK 能力 fail-closed：`sandbox_adapter.declared_capability` 据已装 OpenSandbox 1.1.0 源码声明
  `process_limit=False`（`SandboxSync.create` 无 pids 参数）→ `complete=False` → 拒绝执行；`network_deny`
  通过 `network_policy=NetworkPolicy(defaultAction="deny")` 实际下发；`create` 用 `plan.environment.image`
  （不可变 `@sha256:`，`admit` 已拒可变 tag）作为有效镜像引用发 SDK，`image_digest` 与 image digest 对齐。
- `finalize_assessment` 诊断路径清 `trusted=False`/`contribution="proposed"`；`evaluate` 恒 `trusted=False`。
- 准入/批准绑定持久化不可变事实：`store.approve_generated` 按 `report_id` 重读持久化报告并全等校验
  （伪造 `passed=True` 拒绝 `tampered_generated_report`）、检查未过期、要求显式 `assert_owned`（无 no-op 默认）；
  `generated_validation` 校验所有字节对冻结 manifest digest（`manifest_digest_mismatch` 拒绝字节替换）。
- `TrustedCriteriaRegistry` 同版本异模板构造抛 `criteria_version_conflict`；`IsolationProbeRecord` 增 `image_digest`
  绑定探针环境。



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
- 独立 Q 负例（`morph-r1-boundaries-1003`，`R1_SECURITY_SOURCE` 指向本源码）：
  `test_b_generated_boundaries.py` + `test_b_successor_authority.py` 共 **18 passed**（unverified/mock boolean
  不放行、proof_ref 空/异值不复用探针 record、caller approved+reviewer 不给 final、全计划绑定拒绝变更、自报 score
  拒绝、unknown/crash/timeout 不保留伪造奖励、unknown effect 不给 final、succeeded 缺 output digest 绑定拒绝、
  伪造 passed 不能批准已失败持久化报告、manifest 字节替换拒绝）。
- 静态边界：`tools/typecheck.py`（mypy --strict，129 文件）**Success，0 错误，未扩大豁免**。
- AT-07 真实隔离探针与 L2 真实科研切片 **NOT_RUN**（无授权）：`LocalCpuSandboxBackend` 无探针记录时
  fail-closed，dynamic 本轮仅契约 fixture 安全验证实现能力，不声称 live。
- 环境限制：本 worktree 无 `node_modules`（Node GEP SDK），既有 `NodeAssetBridge` 用例以
  `sdk_process_failed` 失败，属环境缺 node 依赖；新生成用例用 `FakeBridge` 离线注入，不依赖 node。

## 未执行/待协作

- 真实沙箱探针、真实科研切片、云/GPU 后端、Hub 发布：未获授权，NOT_RUN。
- A 正式 MCP 接线、C 三轴贡献接受（绑定 `proof_ref`）、P 产品 UI 由各自 Owner 消费上述 Handoff；独立 I 最后集成。
