# Phase 2 D：显式离线 Executor 与证据归档

## 一页执行计划

- 基线：`7cc64e3eb0031a6b06b9482e95707de17dfe0885`；模型按派发为 Codex `gpt-6.1-sol`。
- 本轨：worktree `morph-fc-stable-drill-0930`；branch `songconmaisaix31-design/morph-fc-stable-drill-0930`；Task `task_6e86025af1bf` / Dispatch `ctx_52f16a4a4b06`，接续原 Run `run_5b66cce8b4b8`，不复用旧任务身份。
- 唯一写权：`demo/fault_drill.py`、`tests/swarm/test_fault_drill.py`、本报告、`docs/FC_CLOSEOUT_0930_PLAN.md` 的 Phase 2 追加内容。R 独占运行时与两份 failure_chain 测试；I 后续负责精确合并及独立验收。跨轨只 Handoff。
- 复用 `Executor` / `FixtureExecutor` / `ExecutionBound` / `ExecutionResult`，由现有 EvoMap ProviderAdapter 通过本地 httpx mock transport 分类；替换动态 Mock 边界，不改预算、租约、breaker、Schema、锁或依赖。
- 自测：指定 `.venv/Scripts/python.exe`，focused `test_fault_drill` / `test_fc_logging`、`tools/typecheck.py`；真实 CLI 一次，状态位于 OS TEMP，忽略日志留 `.runtime/`。全量、build、SDK、分发由 I 串行执行。
- H1 附带证据：独立从 Git 读取 `db283ea` 的打包资源及文档确认的 H3 `be4fb7a` fence，比较 JSON 内容和精确资源字节；CI 合法性与冻结一致性分别记录。
- 历史不改写：旧 A `db283ea` 代码/CI 交付与旧 Orca abandoned 生命周期是不同事实；总控既有计划 WIP 原样接续。此次从原始注入读取真实 dispatch-capability，能力是否有效只据 CLI receipt。
- 限制：`provenance=mock` / `SIMULATED`，usage/cost 保持 None，未知 hold 不释放；Owner 自测不等于独立验收。David 原条件签字仅锚定 `db283ea`，新代码不继承签字；三处 TODO 不改。DSH 原 exit 1、推理流被用户接受但非合格正式评审，引用机械校验未完成，本轮不调用 DSH。原 `demo-build` 不覆盖；第一代主线/WIP、C 前端只读；模型/Hub/Live/部署 NOT_RUN。

## 实际执行与证据

尚未运行本轮验收；以下仅在命令实际退出后追加。
