# FC-R 幻觉案例一页证据

## 三个幻觉接口事实核查

### get_latest_by_provider_and_reason
该名称仅出现在人类队长任务书中，仓库中未找到此接口定义。名称来源：队长提供，历史调用未独立核验。

### EvoMapProviderAdapter  
该名称仅出现在人类队长任务书中，仓库中未找到此接口定义。名称来源：队长提供，历史调用未独立核验。

### record_failure
仓库中未找到名为 `record_failure` 的接口。在 `swarm/worker_loop.py` 中找到相似名称的私有方法：
- `swarm/worker_loop.py:678`: `_record_failure_fact` 私有方法定义
- `swarm/worker_loop.py:813`: 调用 `_record_failure_fact` 的位置
此名称来源：队长提供，历史调用未独立核验。

## Codex 新会话捕获过程
根据任务书描述，Codex 新会话捕获过程涉及异构工具可能暴露不同错误模式。但在当前仓库中，没有独立的终端交互记录、时间戳或运行证据来验证该过程的具体实现细节。

## 已核实修复
根据 Git 历史（commit bbe9d77）：
- `retry` 未定义名修复为 `retry_after`：在 `swarm/worker_loop.py` 中，第839行附近将 `retry` 替换为 `retry_after`（参数名 `retry_after_seconds` 保持不变）
- 删除错误的 `outcome='execution_failed'` 赋值：在 `swarm/worker_loop.py` 中，第916行附近删除了错误的赋值语句，保留原有的 `quarantined` 状态

## 机制启示
- 异构复核能够补充发现潜在问题，如在不同开发者的代码审查中发现了未定义变量和错误的状态赋值
- 测试通过并不等于测试有效，特别是当测试针对的是不存在的接口或错误的假设时
- 但本次案例不足以证明统计独立性，因为幻觉接口（`get_latest_by_provider_and_reason` 和 `EvoMapProviderAdapter`）并未在代码库中实际存在