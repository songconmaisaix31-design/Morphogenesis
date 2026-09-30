# B 科研空间 / MCP / 资产语义

Owner 固定 B，branch `songconmaisaix31-design/morph-research-space-0930`；baseline `ef77af603577d4539d8dbdf780e1536a369b0d12`，plan `6ba12b24781318383454d2e7fb0b132e897b8a8d`。仅本轨 write_paths，未创建其他 Agent/Run。

第一阶段：官方 FastMCP stdio 入口、宿主身份/scope/capability 工具边界；复用 TaskLedger 主动claim/renew/release/handoff/begin_execution，补续租审计与短事务 evidence fencing。既有 Candidate 增 research claim，assets.sqlite3 追加不可变 research_reports；静态安全与 literal-files-v1 验证保留。

A 已确认 `python -m swarm.research --config ABS_TRUSTED_JSON`，通过原生每次启动配置，不动认证/HOME。C 选唯一 NIST NumAcc4 CPU 案例，提供 ExperimentPlan/Context/Result/Executor/read_result；B 用该唯一契约，不平行定义实验执行状态。

当前自验：`python -m pytest tests/research -q` → 6 passed；真实 SQLite scope/capability、stale holder、renew审计、handoff、unknown/crash不重放、外部调用期间独立writer通过；模拟 executor 只证明 contract_local。首次 `python -m mypy ...` → 6 errors（JSON字段类型与apply返回值），修正后 `python -m mypy swarm/research local_assets swarm/task_ledger.py` → Success，17 files。首次失败保留于此，尚未全链验收。

剩余：C executor 接线、独立科研复现/反例/缺失产物/条件拒绝与真实既有 adoption 契约测试、完整适用回归、打包、最终 commit/push。interface_live/task_live NOT_RUN，Docker当前问题属于C/I外部前置，不阻断本轨本地开发。无付费调用。
