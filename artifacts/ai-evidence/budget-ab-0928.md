# 预算 A/B 分析报告（修正版）

## A 场景：死锁/不死锁 + 行号

**结果：不死锁（Line 233）**

根据 git show 73e64cc 的内容，当 `mark_unknown_rejection` 被调用时：

```python
# Line 233 in budget.py from git show 73e64cc
db.execute("UPDATE budget_reservations SET status='uncertain',settled_at=? WHERE reservation_id=?",
           (now, reservation.reservation_id))
```

A 场景不死锁的原因：
1. `mark_unknown_rejection` 将状态从 'pending' 更新为 'uncertain'（Line 233）
2. 根据 Worker 循环 757-758 行，不同候选者使用新 request_id，避免了相同 request_id 的冲突
3. 相同 task_id 仅在 'pending' 状态时阻塞（Line 178 SELECT查询中的status='pending'条件）
4. 因此不会发生 pending 自锁，但其他预算/燃烧率/尝试次数限制仍可能拒绝新请求

## B 场景：双计/无双计 + 行号

**结果：无双计（Line 82、191-193、199、233）**

根据 git show 73e64cc 的程序切片：

```python
# Line 82 in budget.py from git show 73e64cc
unreconciled_reservations=len(rows)

# Lines 191-193 in budget.py from git show 73e64cc
spent = float(db.execute("SELECT COALESCE(SUM(admitted_usd),0) FROM budget_reservations "
                         "WHERE swarm_id=?", (self.swarm_id,)).fetchone()[0])
reserved = state.reserved_estimate_usd
allowance = spent + reserved + reservation_amount

# Line 199 in budget.py from git show 73e64cc
if self.policy.admission_control == "enabled" and spent + state.reserved_estimate_usd + reservation_amount > self.policy.max_cost_usd:

# Line 233 in budget.py from git show 73e64cc
db.execute("UPDATE budget_reservations SET status='uncertain',settled_at=? WHERE reservation_id=?",
           (now, reservation.reservation_id))

# Lines 251-257 in budget.py from git show 73e64cc
if row["status"] != "pending":
    if row["settlement"] is not None and settlement is not None and row["settlement"] != settlement:
        raise ValueError("conflicting usage settlement")
    # Idempotent replay does not overwrite unknown evidence or charge twice.
    return self._snapshot(db, reservation.worker_id, now)

# Lines 281-286 in budget.py from git show 73e64cc
admitted = max(estimate, reservation.reserved_estimate_usd)
db.execute("UPDATE budget_reservations SET status='settled',usage_metering='verified',cost='estimated',settled_at=?,tokens=?,estimate_usd=?,settlement=?,admitted_usd=? "
           "WHERE reservation_id=?", (now, reported.total_tokens, estimate, settlement, admitted,
                                      reservation.reservation_id))
```

B 场景无双计的分析：
1. **重要修正**：Line 82、191-193、199、233 显示：unknown行admitted_usd保持NULL、hold由status!='settled'计入一次（通过state.reserved_estimate_usd），reserve以SUM(admitted_usd)+hold+新reserve扣allowance
2. **重要修正**：不存在 "uncertain→settled 真实入口"，根据 budget.py:251-257，对于任何 status!='pending' 的情况，函数直接返回而不执行结算逻辑
3. 任务终结时不回收旧 uncertain hold，导致同一 swarm 长期占用（Worker 757-758 不同request_id，794-800 _active=None，finally 989-991 只处理 _active）
4. lower observed usage 规则仅在 pending 状态结算时保持 max(estimate, reserved)，不存在的 uncertain→settled 转换不能声称已被验证
5. Line 283 保证了 "lower usage never restores allowance" 规则，但前提是状态为 pending 且有实际 usage 传入

**注意**：无双计不等于真实unbounded费用有硬上界，这只是账本层面的预留控制。

**关键事实**：A 场景中不同 request_id 的请求不受影响（避免自锁），但相同 request_id 的请求会被阻塞；B 场景中不存在从 uncertain 状态转换到 settled 的入口，因此无事后结算路径。