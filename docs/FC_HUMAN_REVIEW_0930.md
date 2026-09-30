# H1 人工复核签字记录 · 受审 SHA `db283eaa1f1d71d36e7b8a3520aafbce5becf1dd`

> 复核人：**David**　复核时间：**2026.9.30 12:31**
> 复核方式：本人阅读并确认所附源码推演、CI 记录及已声明限制；采用 AI 辅助解释，不将 AI 或主控执行的测试记录为本人亲自执行。
> 源码锚定 db283ea（FC 收口候选）。budget.py 与 breaker.py 与 C552（`c552250`）字节一致，此前行号材料仍有效。TODO-HUMAN-REVIEW 三处原样保留（breaker.py:202/592/672）。

## 材料修正（不要求修改预算实现）

- `mark_unknown_rejection` 与 `mark_uncertain` 分开说明：前者在明确拒绝、usage/cost 未知时保留 hold，不由该方法主动触发停止；后者调用 `settle(None)`，在 `allow_unknown_usage=False` 时会触发 unknown_usage 停止。本修正不要求修改预算实现。

## 预算 A/B 逐行工作表（归档）

| 代码入口（db283ea） | 语义 |
|---|---|
| swarm/budget.py:179–181 | 相同 request_id 恒冲突；相同 task_id 仅 status='pending' 触发冲突（幂等防重复） |
| swarm/budget.py:227–241 | mark_uncertain / mark_unknown_rejection：pending→uncertain，不写 admitted_usd/estimate_usd，不在此时 _trip |
| swarm/budget.py:259–278 | settle：非 pending 早退返回快照；有既存 settlement 冲突时抛错 |
| swarm/budget.py:298 | admitted=max(estimate, reserved_estimate_usd)，不返还承诺额度 |
| swarm/budget.py:131–205 | reserve 校验价格/请求边界；verified 用明确上限，unbounded 用 operator allowance（非服务端硬上限） |

## breaker 四态 × 四事件转移表（归档）

状态：`insufficient_evidence`(IE) / `normal`(N) / `suspended`(S) / `probing_recovery`(PR)。
事件：`aggregate` / `cooldown_expired` / `probe_success` / `probe_failure`。

| 状态 \ 事件 | aggregate | cooldown_expired | probe_success | probe_failure |
|---|---|---|---|---|
| insufficient_evidence | 达悬浮阈值→S；否则 sample_count≥min_samples→N；否则停留 | 停留 | 停留 | 停留 |
| normal | 达悬浮阈值→S；否则停留 | 停留 | 停留 | 停留 |
| suspended | 停留（仅更晚的服务端 Retry-After 可延长 cooldown） | cooldown 到期→PR（原子 claim probe slot） | 停留 | 停留 |
| probing_recovery | 停留 | TTL 过期→PR（回收陈旧 slot，重 claim） | live probe→N（release+reset_window） | live probe→S（release+set_cooldown） |

注：`_live_probe` 要求 worker_id==probe_owner 且 probe_expires_at>now；非 live 事件一律停留。熔断只授予路由资格，不读写预算/租约/attempt。

## 场景 A 结论

**两者都不是**，仅限本地准入和同任务 pending 自锁问题。首笔必须是 `confirmed_rejection`，不适用于 `unknown_effect`。不同 request_id、首笔非 pending、其他准入条件均满足时，累计承诺＋未结清 hold＋新 hold 不超过预算上限才可继续。额度不足时拒绝新请求，属于预算保护，不是死锁。该结论不证明 unbounded 请求的实际账单具有硬上限。

## 场景 B 结论

本地账本未发现该路径重复计入同一 reservation；unknown hold 会长期保留，晚到 usage 对非 pending 的 settle 早退，不代表已经完成账单对账。对于「上游实际费用绝不超支」，结论为**证据不足**。接受本候选没有自动晚到对账、allowance 不等于服务端硬限额的限制。不得以清库、换 run 或伪造结算释放未知 hold。

## breaker 六点结论

1. 接受所附 16 格状态转移及其条件，不把到期等同于自动恢复。
2. 接受 sample_count 双阈值和 confirmed 欠费例外的现有语义。
3. 接受同机可信协作进程、同一持久库下的原子 slot 与 token fencing；不扩写为跨机一致性保证。
4. 接受已知 Retry-After 截止时刻及未知时正冷却值的处理。
5. 接受纯 transition 与持久恢复水位分离；新增故障索引纳入正式评审范围。
6. 接受 breaker 仅授予路由资格，预算、租约和未确认执行保护不可绕过。

## 候选接收结论

**有条件同意 `db283ea` 进入受限 FC 冻结候选。** 这不是最终发布完成证明，也不替代合格的 DSH 正式评审。保留既定合并、Tag、Live 授权的原前置条件；本记录不额外放行尚未满足条件的自动三连 Live 或通用科研入口。

## 附带条件

- 归档本候选打包 Schema 与 H3 批准版的独立一致性证据；不得把新 CI 的 Schema 合法性检查写成冻结版本一致性检查。
- 实际 Live 的目标、模型、安全配置、累计预算及停止规则仍须明确。

## 源码变更授权

本次只允许原样登记本人结论及纠正文档，不要求为签字修改生产行为。三个 TODO 如需更新为已复核引用，另记录授权范围和新提交，不得把修改后的源码冒称原候选原字节未变。

---

准备人：主控（不代签、不代得结论）。以上结论由 David 提供，主控仅登记归档。
