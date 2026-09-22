# P 供给轨（`orca_provision/`）

## 已实现

本轨只实现供给面元数据和身份归一，不启动进程、不创建多开任务，也不依赖 ORCA 代码。`OrcaProvisioner` 是唯一的最小 Protocol：

```python
def provision(run_id: str, count: int) -> Provision: ...
```

它不规定 HTTP、CLI、URL、凭据、请求体、响应体或重试语义。未来只有在 ORCA 提供公开契约后，才可在本轨之外接入一个实现；ORCA 外部 ID 仅保存在 T0 `Provision.external_ids` 的不透明映射中。

`ProvisioningService` 在收到显式 `remote` 实现时调用该 Protocol；`remote=None`（当前默认，因地址/凭据/公开契约均未提供）降级到 `FixedProvisioner`。固定 fallback 默认最多 4 个成员，按稳定顺序分配 `planner`、`builder`、`reviewer`、`aggregator`，来源记录为 `source="fixed"`、`provenance="live"`，表示本地供给记录本身真实生成，不表示 ORCA 远端已验证。

`provision_swarm` 将每个 `AgentId` 绑定到给定 `task_id` 的 `AttemptId`，产生明确的 `Role -> AgentId -> AttemptId` 映射。相同 run/count 的 fallback 成员身份稳定；它只产生数据记录，后续执行和调度由 T2 负责。

`BudgetGate` 在供给前检查 `RunConfig` 的总 token/费用预算和停止状态。停止状态、预算耗尽、未知用量（T0 的 `unknown_usage_policy="stop"`）均拒绝供给；数量必须为正且不得超过固定规模或声明配额。`max_retries`、文件权限和发布批准不在供给轨重复实现，仍由运行时/编排轨负责。

## 验收与限制

适用的 contract-local 测试覆盖：固定成员身份稳定、三层身份映射、配额拒绝、ORCA 配置缺失降级、负数/零请求异常、预算耗尽与停止状态拒绝。测试不会伪造 ORCA live 结果。

当前只能证明本地契约与 fallback 行为（`contract_local`）；没有 ORCA 地址、凭据或公开供给契约，因此 `interface_live` 与真实远端/多开运行任务均为未验证。T0 契约、依赖锁和跨轨集成仍由其所有者/集成 Agent 维护。
