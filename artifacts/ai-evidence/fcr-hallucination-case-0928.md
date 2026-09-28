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

## FC-E 同源降级评审失实案例

基于 `artifacts/ai-evidence/review-0928-integration-qwen-fallback.md` 及 commit 2180e02/78c0745 的真实代码（73e64cc）与测试（a821783）分离分析：

### 引用行号错误案例
- **原报告声称**（78c0745版本第65行）："Line 138: `assert response.error_kind is not None` followed by `assert "Timeout" in response.error_kind or "Connection" in response.error_kind`"
- **实际代码**（git show 73e64cc的tests/swarm/test_failure_chain_boundaries.py）：Line 138 实际是 `def test_all_candidates_down_boundary(self):` 而不是该assert所在位置
- **该assert实际在line 85**，原报告的行号引用错误

### call_count缺失却称覆盖充分案例
- **原报告声称**（78c0745版本第109行）："Missing call_count: The tests seem to cover the reservation counts and states adequately."
- **实际边界对照**：报告109行只讨论reservation状态，未给出Worker执行次数证据；原73边界文件搜call_count无命中

### 无依据high后作者撤回案例
- **原报告**（2180e02版本）将"半开探测令牌围栏竞态条件"标记为高危
- **代码分析**：`swarm/breaker.py` 的 `_finish_probe` 方法通过数据库UPDATE的token匹配确保只有合法持有者能修改状态
- **测试验证**：`tests/swarm/test_breaker.py` 中 `test_same_owner_stale_probe_result_is_fenced_by_token` 明确验证了该机制
- **作者修正**（78c0745版本report40-41概述）：明确撤回了高危判断，承认"原始关于半开探测令牌围栏竞态条件的高危发现已被**修订**。围栏机制按预期正确实现。原始担忧基于实际实现是无根据的。"（真实英文逐字："The high-severity finding regarding the race condition in probe token fencing is hereby **REVISED**. The mechanism is correctly implemented as per the code analysis and existing tests. The original concern was unfounded based on the actual implementation."）
- **这是作者修改自己断言的真实例子**

### 三重锁方法论说明
三重锁是指：门禁测试+独立评审+人类签核的验证过程，不是静态代码分析/测试存在/作者修正的组合。

## 机制启示
- 异构复核能够补充发现潜在问题，如在不同开发者的代码审查中发现了未定义变量和错误的状态赋值
- 测试通过并不等于测试有效，特别是当测试针对的是不存在的接口或错误的假设时
- 少数复核案例不足以衡量错误相关性，本案例未做统计独立性检验
- 可验证的流程案例：这次同源降级评审产出的拒收
- 同源降级不能称异构，这不是正式的人工或异构复核

### T3变异测试案例
根据主控验收台账记录，T3 mutation两次仍绿，这是已记录案例而非本轨重跑。三重锁未齐就未打demo-build；两例和mutation证明能暴露这些具体失误，不是全面有效性或统计因果证明。