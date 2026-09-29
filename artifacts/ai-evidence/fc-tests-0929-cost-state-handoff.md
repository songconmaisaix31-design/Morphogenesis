# A 轨生产元数据 Handoff：unknown cost 被观察记录标为 settled

状态：**未解决生产缺陷，语义检查 exit 1**。本轨仅改测试/证据，没有修改生产。候选 F = `73e64cc70116ac658d85591d082c0684a4952c99`；原函数和账本保持 F 字节。仅供主控和领域 Owner 审核，不代签 H1，不表示 FC 已验收。

## 已实际复现

运行本树 `tests/swarm/test_failure_chain_boundaries.py::test_known_usage_unknown_cost_blocks_next_candidate_and_restart`：使用真实 `Worker._process`、预算 SQLite、FaultObservationStore，只替换 Executor 边界。`prices=None`，候选 alpha 返回 `confirmed_rejection`、`uncertain=False` 及已有 FixtureExecutor 同规格 mock usage（prompt=1、completion=1、total=2）；它表示明确的本地合成 usage，不是远端计费证据。beta execute 的 call_count 为 0，重启也不再发送。

持久化结果见 `fc-tests-0929-cost-state-repro.json`：同一 `request_id=fixture-0:1:0` 的账本 `status=uncertain, usage_metering=verified, cost=unknown, tokens=2, estimate_usd=null, admitted_usd=null, reserved_usd=0.2`；观察记录却是 `cost_state=settled`，`switched_to=null`。这是观察元数据错误，没有证据表明预留被释放或实际超支。

Focused 门禁检查调用/预算边界，20 passed；另行对该真实输出检查 `observation.cost_state == 'unknown'` **失败，exit 1**，不混入绿色门禁。原始实际数据已保留；未用断言把错误的 settled 固化为合法行为。

## F 的精确源码

- `swarm/worker_loop.py:793-799`：仅 `result.uncertain and classification == CONFIRMED_REJECTION` 走 `mark_unknown_rejection`，其余会调用 `self.budget.settle(self._active, usage)`。
- `swarm/budget.py:271-279`：`if estimate is None:`；写入 `status = "unknown_cost_allowed" if self.policy.allow_unknown_cost else "uncertain"`（274），SQL 保留 `usage_metering='verified',cost='unknown'`（275），并 `_trip(db, "unknown_cost")`（279）。
- **根因 `swarm/worker_loop.py:839` 原文：**

```python
cost_state: Literal["settled", "unknown"] = "unknown" if result.uncertain else "settled"
```

此处只看 usage 是否 uncertain，没有识别价格缺失导致的 unknown cost。`worker_loop.py:852-854` 把该值写入 failure fact；后续 admission 被 `unknown_cost` 拦截并在 finally 保存 deferred 事实，形成上述 durable 输出。

## 可审核的最小修复建议（未执行）

仅在 `worker_loop.py:839` 的观察元数据判断增加当前运行价格缺失条件：

```python
cost_state: Literal["settled", "unknown"] = (
    "unknown" if result.uncertain or self.config.budget.prices is None else "settled"
)
```

这是已复现分支的最小候选修复，领域 Owner 还应核验该行可达分支是否存在其他“有价格但估算失败”路径。不要简单使用整个 swarm 的 `settled.cost` 替代当前请求状态：旧请求 unknown hold 可以使聚合快照 unknown，即使当前请求已估算结清。不得修改预算预留、admission、切换、计费、settle/mark_unknown_rejection，也不加新结算 API 或自动释放。

建议语义回归：① 无价格+合法 usage+confirmed_rejection，应为 unknown，保留 full hold，beta call_count=0；② 有价格+合法 usage，观察记录 settled，admitted 正数、hold 不重复计；③ 无 usage+confirmed_rejection，unknown hold 下允许受控新 request_id；④ 旧 unknown hold + 当前已知价格/usage，当前事实仍准确；⑤ 可选 allow_unknown_cost 模式仍保持 cost_state unknown。① 可直接在现有 unknown_cost 用例外部断言 `fact.cost_state == "unknown"`，应先红后绿。审批与生产写权由主控另行处理。

附：取证脚本首次因报告父目录未建立而 FileNotFoundError/exit 1，不计为语义复现；建目录后从同一真实测试产物读回，`semantic_check_passed=false` / exit 1。mutation 是独立的 breaker 路由检查，不能拿此元数据红项替代 mutation。
