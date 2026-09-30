# Phase 2 R：稳定运行时边界（Owner self-test）

## 范围与锚点

- Run `run_5b66cce8b4b8`；Task `task_f3ade7340d5b`；Dispatch `ctx_e2fb57a930f6`。
- 基线：`7cc64e3eb0031a6b06b9482e95707de17dfe0885`（`decentralized-swarm`）。
- 工作树：`morph-fc-stable-runtime-0930`；分支：`songconmaisaix31-design/morph-fc-stable-runtime-0930`。
- 唯一修改路径：`swarm/worker_loop.py`、`swarm/failure_chain.py`、`tests/swarm/test_failure_chain_boundaries.py`、`tests/swarm/test_failure_chain_runtime.py`、本报告。
- 业务依据：本次 TASK 优先；已读本树 `AGENTS.md`、`docs/FC_CLOSEOUT_0930_PLAN.md`、`docs/source/README_包内说明.md` 与现行实现。旧计划的 Phase 2 未启动记录由本次派发接续，不改其他治理文件。

## 删除旧 fallback 的证据与保留兼容性

基线 `swarm/worker_loop.py:43` 已顶层导入 `FaultObservationStore`，且 `orchestration/fc_logging.py:26` 同样直接依赖 `FaultObservation`；因此 `_load_failure_components()` 的 `ImportError -> (None, None)` 不能让缺失 FC-B 的完整发行版运行。基线 `swarm/worker_loop.py:69` 的 loader 仅在 `:411` 被 Worker 构造调用；全仓 Python/TOML 搜索未发现替换 loader、删除模块或 partial FC 发行的现行调用者/测试。`pyproject.toml` 完整打包 `swarm` 与 `orchestration`，锁依赖已有 `cachetools`。删除 loader 的理由是完整发行版无该缺失组件用例，并让损坏安装或 breaker 内部 ImportError 明确暴露。

保留 `breaker_config=None` 的显式选择（CLI 与 Fixture Worker 原有使用方式）：不创建 breaker，但仍创建真实 fault store。保留 `FailureObservationFact`、`BreakerViewLike`、`SharedBreakerLike`、`FaultStoreLike` 的现有名称；`FailureObservationFact` 被真实 Worker 与现有 tests 直接使用，且 FC 事件先缓存不带 observation_id 的事实，再读取落盘身份。没有将兼容数据模型直接替换成另一套验证语义。

## 实际修改

- 直接导入真实 `FaultObservationStore`、`SharedBreaker`、`BreakerConfig`，删除 `tuple[Any, Any]` loader 与构造 cast。真实类直接赋给协议属性，strict mypy 能实际核查结构兼容性。
- `FaultStoreLike` 继承 `swarm.breaker.FaultStoreLike` 的既有 read/aggregate 契约，append 参数限定为权威 `FaultObservation`；`SharedBreakerLike.observe` 使用同一读契约并返回 `ObservationReport`。
- `views()` 返回 `Sequence[BreakerViewLike]`：真实 API 的 `list[BreakerView]` 可以协变满足该消费边界，避免不变 list 迫使 cast。
- 常量与已知分类集合引用 `orchestration.provider_adapters.base.FailureClassification`；事实字段类型复用 `swarm.fault_observations.FailureClass/CostState`。已有 membership 检查后的 cast 仅收窄到实际 Literal 类型。
- append 前使用 `FaultObservation.model_validate(fact.model_dump())` 显式转换。仍由原 store 处理 fsync、去重和权威 JSONL，FC 日志仍读取落盘 observation_id。
- 增补真实 Python 缺失组件失败检查、无 breaker 配置的真实 Worker 检查；加强 confirmed rejection 测试，检查真实 append 参数、落盘身份与 FC 日志身份相同。

预算、租约、breaker transition、故障存储与适配器实现未改；Executor、ExecutionBound、candidate 次数/额度/hold、probe token、未知效果停止和重试策略沿用现有实现。未新增调度器、facade、注册器或其他基础设施。

## 验证记录

环境准备：命令进程内设置 `POETRY_VIRTUALENVS_IN_PROJECT=true`，执行 `uv tool run poetry install --no-interaction`，exit 0（锁定安装 88 个包，Python 3.12.13，本树独立 `.venv`）。锁文件未改。

第一次工作区 focused：`.venv/Scripts/python.exe -m pytest -q tests/swarm/test_failure_chain_runtime.py tests/swarm/test_failure_chain_boundaries.py`，**exit 1：2 failed / 21 passed，236.68s**。原失败保留：

1. `test_confirmed_rejection_switches_provider_and_submits_success` 在既有 `publish_asset` 阶段 `BridgeError`，真实 Worker 返回 failed；原审计位于 OS TEMP `pytest-of-DW/pytest-279/test_confirmed_rejection_switc0/chain-state/audit/builder-0/6763e54fc0674c26893e82f0163d4db2.json`，reason 为安全脱敏的 `exception_details_withheld`。本树 `node_modules/@evomap/gep-sdk` 不存在，README 明确要求源 checkout 的 Node 锁依赖；已执行 `npm ci --ignore-scripts --no-audit --no-fund`，exit 0（99 packages）。缺失依赖是有证据的诊断，不修改 BridgeError 路径或 mock SDK。
2. 新增 missing-component 检查的 `swarm.breaker` 子进程在 30 秒 `communicate` 阈值超时，原 `TimeoutExpired` 未删除。暂按冷导入/环境假设诊断，不提高 timeout，不删测试，不 mock 子进程；重跑保留同一选择、断言和 30 秒阈值。

第一次工作区 strict：`.venv/Scripts/python.exe tools/typecheck.py`，**exit 0：Success, 89 source files**。后续固定 SHA 自验与远端验证将在实际执行后补入；此结果并不抹去上述失败。

代码阶段已固定并推送为 `0cf04ab5548c42d1f546f675843cfa50b39d67ca`（conventional commit，`Swarm-Agent: codex`）。`git ls-remote --exit-code origin refs/heads/songconmaisaix31-design/morph-fc-stable-runtime-0930` 返回该精确 SHA，exit 0；`git diff --name-only 7cc64e3eb0031a6b06b9482e95707de17dfe0885 HEAD` 恰为上述五个授权路径。

环境诊断命令 `.venv/Scripts/python.exe -c "import time; started=time.perf_counter(); import swarm.worker_loop; print(f'worker_import_seconds={time.perf_counter()-started:.6f}')"` 返回 **18.493002s / exit 0**；支持导入启动成本假设，但不能证明第一次超时的唯一根因。未提高任何阈值。

固定代码 SHA `0cf04ab5548c42d1f546f675843cfa50b39d67ca` 上，同一 focused 命令再次执行：**23 passed / exit 0 / 348.97s**。命令进程内 `OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=MKL_NUM_THREADS=1`，两次选择、断言和 30 秒子进程阈值相同，未修改代码或测试后重跑。日志：OS TEMP `morph-fc-stable-runtime-0930-focused-0cf04ab.log`。

固定代码 SHA 上第一次完整适用回归：**exit 1 / 323 passed / 1 failed / 2 warnings / 1713.24s**。唯一失败为 `tests/swarm/test_fc_logging.py::test_concurrent_append_and_partial_tail_preserve_facts`；三个线程同时 append 六条合法事件时，`orchestration/fc_logging.py:142` 的既有 `connection(..., timeout=0.05)` 在 `swarm/task_ledger.py:47` 的 `BEGIN IMMEDIATE` 抛出 `sqlite3.OperationalError: database is locked`。这是实际失败门禁，不能用绿子集或单节点诊断覆盖。

原日志在 OS TEMP `morph-fc-stable-runtime-0930-regression-0cf04ab.log`；原失败目录 `pytest-of-DW/pytest-281/test_concurrent_append_and_par0`。两条 warnings 均为 `test_budget.py` 故意非法 model_copy 的 Pydantic serializer warnings（nan、字符串 input_tokens）。`git diff --exit-code 7cc64e3eb0031a6b06b9482e95707de17dfe0885 HEAD -- orchestration/fc_logging.py tests/swarm/test_fc_logging.py swarm/task_ledger.py`，exit 0、无输出，证明三个相关文件未改。

已通过 Orca 向总控升级 `msg_47a7c92b504a`：日志并发写路径及其测试不属于 R write_paths，不修改源码、测试或 0.05 秒期限，不改用 emit 吞掉此失败。相同 SHA 上只进行了一次相同断言、期限的失败节点有界诊断：`.venv/Scripts/python.exe -m pytest -q tests/swarm/test_fc_logging.py::test_concurrent_append_and_partial_tail_preserve_facts`，**exit 1 / 1 failed / 75.49s**，仍为同一 `BEGIN IMMEDIATE` 的 `database is locked`。诊断日志为 OS TEMP `morph-fc-stable-runtime-0930-lock-diagnosis-0cf04ab.log`，失败目录为 `pytest-of-DW/pytest-283/test_concurrent_append_and_par0`。已再次升级给总控；不继续盲重试，需由具有日志源码写权的 Owner 处理。整组回归未通过，全量与 build/SDK/分发不在本轨运行。

固定代码 SHA 的 strict 复核：`.venv/Scripts/python.exe tools/typecheck.py`，**exit 0 / Success: no issues found in 89 source files**。最终报告提交只更新本文件，四个代码/测试 blob 与该验证 SHA 相同；因此精确记录这些验证属于 `0cf04ab5548c42d1f546f675843cfa50b39d67ca`，并未声称最终合并 SHA 或 I 的门禁已运行。

适用回归命令（进程内相同三个线程变量为 1，默认 pytest 临时目录在 OS TEMP）：

```powershell
.venv/Scripts/python.exe -m pytest -q `
  tests/swarm/test_budget.py tests/swarm/test_budget_evomap.py `
  tests/swarm/test_lease.py tests/swarm/test_ledger.py `
  tests/swarm/test_breaker.py tests/swarm/test_fault_observations.py `
  tests/swarm/test_probe_lifecycle_recovery.py tests/swarm/test_rejection_runtime_boundaries.py `
  tests/swarm/test_unknown_effect_recovery.py tests/swarm/test_reservation_cost_state.py `
  tests/swarm/test_fc_logging.py tests/swarm/test_worker_evomap.py tests/swarm/test_worker_runtime.py `
  tests/orchestration/test_provider_adapters.py tests/orchestration/test_fc_a_comprehensive.py `
  tests/orchestration/test_integration.py
```

代码证据全部以 `0cf04ab5548c42d1f546f675843cfa50b39d67ca` 为锚点：`swarm/worker_loop.py:395` 真实 store 赋值、`:399` 真实 breaker 赋值、`:609` 规范 append 转换、`:727` 有 membership 前置的 Literal 收窄、`:793` 原观察调用；`swarm/failure_chain.py:62` 可协变 views、`:77` observe 原契约、`:83` canonical append。生产赋值不再隐藏于 cast；strict 会检查真实实现满足协议，真实实例、执行调用、JSONL、预算表、任务状态和 FC 日志由行为测试共同确认。

## 三态、限制与交接

- `contract_local`：BLOCKED（Owner focused 已通过，适用回归的日志并发门禁真实失败；尚非 I 独立验收）。
- `interface_live`：NOT_RUN。
- `task_live`：NOT_RUN。
- 本轨终态：**failed / 有限交付**。稳定接口实现、focused 和 strict 已有 Owner 自验；完整适用回归和单节点诊断均未通过，不冻结、不签收、不发布候选。
- 未解决：既有 FC 日志 append 的 0.05 秒 SQLite 写锁并发门禁。修复 `orchestration/fc_logging.py` 及其 test 超出 R 写权，已交总控归属；不能以本轨不修改它为理由忽略真实失败。
- 未调用模型 API、DSH、Hub 或 live；全量、build、SDK、分发与精确合并后独立验收由 I 串行执行，R 不复用旧通过结论。
- D 所属 `demo/fault_drill.py` 仍有 `cast(SharedBreakerLike, breaker)`（基线 `:217`）；稳定协议已使真实 breaker 可直接满足边界，移除此 cast 属 D 的 Handoff，R 未改 demo 或其 tests。
- TODO-HUMAN-REVIEW/H1 治理未改，不用本次接口收尾宣称新的人工生产放行。
