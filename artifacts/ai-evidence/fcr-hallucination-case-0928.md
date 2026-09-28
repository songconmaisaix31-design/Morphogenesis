# FC-R 幻觉案例一页证据

## 三个幻觉接口事实核查

### get_latest_by_provider_and_reason
在仓库中未找到此接口定义。该名称仅出现在人类队长任务书中，无直接代码证据支持其存在。

### EvoMapProviderAdapter  
在仓库中未找到此接口定义。该名称仅出现在人类队长任务书中，无直接代码证据支持其存在。

### record_failure
在 `swarm/worker_loop.py` 中找到相关实现：
- `swarm/worker_loop.py:678`: `_record_failure_fact` 方法定义
- `swarm/worker_loop.py:813`: 调用 `_record_failure_fact` 的位置

## Codex 新会话捕获过程
根据任务书描述，Codex 新会话捕获过程涉及异构工具可能暴露不同错误模式。但在当前仓库中，没有独立的终端交互记录、时间戳或运行证据来验证该过程的具体实现细节。

## 已核实修复
根据 Git 历史（commit bbe9d77）：
- `retry` 未定义名修复为 `retry_after`：在 `swarm/worker_loop.py` 中，相关字段从 `retry` 更改为 `retry_after_seconds`
- `quarantined` 被误写为 `execution_failed` 的修复：在 `swarm/worker_loop.py` 中，状态从 `execution_failed` 修正为 `quarantined`

## 机制启示
- 异构工具确实可能暴露不同的错误模式，这在 FC-A 中体现为不同 provider 的失败分类逻辑差异
- 但本次案例不能证明统计独立性，因为幻觉接口（`get_latest_by_provider_and_reason` 和 `EvoMapProviderAdapter`）并未在代码库中实际存在
- 测试通过并不等于测试有效，特别是当测试针对的是不存在的接口或错误的假设时