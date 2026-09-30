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

## 三态、限制与交接

- `contract_local`：PENDING（Owner self-test，尚非 I 独立验收）。
- `interface_live`：NOT_RUN。
- `task_live`：NOT_RUN。
- 未调用模型 API、DSH、Hub 或 live；全量、build、SDK、分发与精确合并后独立验收由 I 串行执行，R 不复用旧通过结论。
- D 所属 `demo/fault_drill.py` 仍有 `cast(SharedBreakerLike, breaker)`（基线 `:217`）；稳定协议已使真实 breaker 可直接满足边界，移除此 cast 属 D 的 Handoff，R 未改 demo 或其 tests。
- TODO-HUMAN-REVIEW/H1 治理未改，不用本次接口收尾宣称新的人工生产放行。
