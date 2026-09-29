# H1 人工复核签字材料 · 受审 SHA `db283eaa1f1d71d36e7b8a3520aafbce5becf1dd`

> 本文是人工复核材料，**不是签字或结论**。源码锚定 db283ea（FC 收口候选）。budget.py 与 breaker.py 与 C552（`c552250`）字节一致，此前已记录的行号材料仍有效，本节仅重绑 SHA 并保留签字槽。TODO-HUMAN-REVIEW 三处原样保留（breaker.py:202/592/672）。

## 预算 A/B（人类专属结论，逐行手推）

| 代码入口（db283ea） | 需人工核对的真实语义 |
|---|---|
| swarm/budget.py:179–181 | 相同 request_id 恒冲突；相同 task_id 仅 status='pending' 触发冲突（幂等防重复） |
| swarm/budget.py:227–241 | mark_uncertain / mark_unknown_rejection：pending→uncertain，不写 admitted_usd/estimate_usd，不在此时 _trip |
| swarm/budget.py:259–278 | settle：非 pending 早退返回快照；有既存 settlement 冲突时抛错 |
| swarm/budget.py:298 | admitted=max(estimate, reserved_estimate_usd)，不返还承诺额度 |
| swarm/budget.py:131–205 | reserve 校验价格/请求边界；verified 用明确上限，unbounded 用 operator allowance（非服务端硬上限） |

- **场景 A（unknown hold + 同任务切换请求）**：同一 task_id、不同 request_id，预留 B、首笔 hold H1、新请求 hold H2，满足价格匹配/尝试上限/burn-rate/租约后，B>=H1+H2 与 B<H1+H2 分别走一遍。判定：死锁 / 超支 / 两者都不是 / 证据不足。
- **场景 B（unknown hold + 服务端事后扣款 + 任务终结）**：走 A 后，分外部账单只在服务端出现、以及调用方用晚到 usage 对原 reservation settle 两种输入；budget.py 对非 pending settle 早退，没有 uncertain→billed 分支。判定：是否重复计算同一 reservation；是否长期保守占用而非重复收费；unbounded 实际费用超 allowance 时能否宣称硬预算保证；账单晚到如何记录与人工对账。

## breaker 六点（人类专属结论）

1. 16 格状态转移（insufficient_evidence/normal/suspended/probing_recovery × 事件）
2. 双阈值 + 欠费例外直入
3. 并发 fencing / 唯一 probe token（breaker.py:592、672 两处 TODO）
4. Retry-After 到期的探测时机
5. 纯函数 transition 与恢复水位
6. 预算/租约隔离（熔断只影响路由资格，不影响预算与租约）

## 签字槽（由队长填写）

- 复核人真实姓名/签名：**待填**
- 时间与受审 SHA：**待填**（材料基线 `db283eaa1f1d71d36e7b8a3520aafbce5becf1dd`）
- 场景 A 结论（死锁 / 超支 / 两者都不是 / 证据不足）+ 逐行记录：**待填**
- 场景 B 结论 + 逐行记录：**待填**
- 费用未知、晚到证据、unbounded 前提与可接受限制：**待填**
- breaker 六点逐项结论（各写结论或未解决项）：**待填**
- 是否允许进入冻结候选；如需修改，明确批准的生产 Owner/文件：**待填**

> 准备人：主控（不代签、不代得结论）。仅登记队长提供的结论并同步，不改写 TODO 或源码行号。
