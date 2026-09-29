# FC 五项修复候选人工复核包 · 2026-09-29

**AI 只备料，H1/H3 均 unsigned。** 共同代码候选为 `c552250c0d07f5f70f09eb0a5ab3c322195e34ec`（下称 C552），已 `git ls-remote` 核对；治理分支从 C 单轨 `e6ac45ffefc171a7215f8db19bc4a28af24ec4fc` 创建，其文档 HEAD 不是测试候选。旧材料 [FC_HUMAN_REVIEW_0928](FC_HUMAN_REVIEW_0928.md) 原文、签名槽、历史失败均保留。

本包所有新源码行号均绑定完整 C552；[21 组逐字代码](../artifacts/ai-evidence/fc-remediation-governance-0929-h1-quotes.md)、[可机械核对的原引文](../artifacts/ai-evidence/fc-remediation-governance-0929-h1-quotes.json)、[21/21 引用 PASS](../artifacts/ai-evidence/fc-remediation-governance-0929-h1-verification.json) 配套使用。PASS 只证明 Git blob 文字相等，不证明 AI 推论或人工认可。

本轮五项生产修复已经用户授权；不再沿用旧 cost_state“未授权”状态。代码修复交付、独立验收、正式 FC-E、真人审批是不同证据。

## H1：先预算 A/B，再 breaker

### 预算 A：unknown hold 与同任务 pending 冲突

逐字备料 H1-01 至 H1-11 覆盖 `BudgetLedger.snapshot/reserve/mark_unknown_rejection/settle`，Worker 每候选 request_id、confirmed_rejection 继续条件、unknown_effect 停止与 TaskLedger 持久隔离入口。不能把容量、attempt、模型价格、burn、租约拒绝当成 pending 自锁。

| 人工手推步骤 | 待补共同 SHA 引文 | 人工记录 |
|---|---|---|
| 首次 reserve | budget.py:77–86、164–180（H1-01/02） | 待填写 |
| 确认拒绝但费用未知 | budget.py:230–251（H1-06），pending→uncertain，full hold 保留 | 待填写 |
| 同任务新 request_id | budget.py:179–181（H1-03）只对同 task pending 冲突；相同 request_id 始终冲突 | 待填写 |
| B ≥ H1+H2 与 B < H1+H2 | budget.py:192–203（H1-04），admitted+holds+新预留 | 待填写 |
| unknown_effect 且费用已知 | task_ledger.py:257–266、358–393；worker_loop.py:757–825（H1-09/10/11） | 待填写 |

### 预算 B：可用额度、事后结算、终结 hold、lower usage

| 人工复核点 | 必须逐字核对的入口 | 人工记录 |
|---|---|---|
| 可用额度与同一 hold 是否双计 | budget.py:77–86、192–203，admitted 与 status!=settled 的 hold 分列 | 待填写 |
| 事后账单/晚到 usage | budget.py:259–280（H1-07），非 pending 早退；此入口没有 uncertain→settled 对账分支 | 待填写 |
| 任务终结/重启 | budget.py:77–86、230–251；任务终结未在这些预算路径释放 hold，不将长期保守占用混作真实重复收费 | 待填写 |
| lower usage | budget.py:281–313（H1-08），`max(estimate, reservation.reserved_estimate_usd)`；估费用不等于账单 | 待填写 |
| unbounded allowance | 不能声称上游真实账单具有硬上限 | 待填写 |
| reservation 的 cost_state | budget.py:213–225 / worker_loop.py:802（H1-05/11）；本次 reservation 与全局 snapshot 分开 | 待填写 |

预算人工结论槽：复核人/时间/完整候选 SHA **待填写**；A、B 各自“死锁 / 超支 / 两者都不是 / 证据不足”及前提 **待填写**。AI 不代填结论或签字。

### breaker 四态、fencing 与六点

以下是 C552 `breaker.py:163–251`（H1-13）派生的 AI 导读矩阵，仍待人工复核。I=insufficient_evidence，N=normal，S=suspended，P=probing_recovery；列名使用实际 event 值。

| state | aggregate | cooldown_expired | probe_success | probe_failure |
|---|---|---|---|---|
| I | 达熔断条件→S；否则样本≥min_samples→N；否则保持 | 保持 | 保持 | 保持 |
| N | 达熔断条件→S；否则保持 | 保持 | 保持 | 保持 |
| S | 仅更晚 Retry-After 延长；否则保持 | cooldown_until 非空且≤now→P/申请槽 | 保持 | 保持 |
| P | 保持 | probe_expires_at 非空且≤now→P/重领槽 | live owner 且未过期→N/释放槽/清窗口 | live owner 且未过期→S/释放槽/设冷却 |

三处 TODO 新位置：`breaker.py:202`、`:592–593`、`:672–674`；原文字保留。`try_claim_probe:569–614`（H1-16）以 `BEGIN IMMEDIATE`（task_ledger:41–56，H1-21）加当前 token/冷却或 TTL 条件 UPDATE、rowcount=1 取得 fresh token；`_finish_probe:629–695`（H1-17）同时核对 owner、调用方原 token、expiry。`failure_chain.py:116–149`（H1-20）将 fresh token 交给真实路由，不能用最新 token 接受旧结果。

恢复水位：`breaker.py:477–521`（H1-15）先按 recovered_at/recovery_sequence 过滤，`:657–666` 成功时取 checkpoint；`fault_observations.py:104–117、206–218`（H1-18/19）以追加序号区别同一时间戳，保留新样本并排除旧/迟到样本。`breaker.py:127–144`（H1-14）保留 window≥aggregation_interval 的约束。

| 六点 | 共同候选材料要求 | 人工结论 |
|---|---|---|
| 转移穷举 | breaker:193–251 / H1-13，以上矩阵与非法输入 | 待签 |
| suspended 双阈值及欠费例外 | breaker:163–170 / H1-13，计数不是故障率 | 待签 |
| 竞态与 fencing | breaker:569–695、failure_chain:116–149 / H1-16/17/20 | 待签 |
| Retry-After | breaker:182–191、209–223 / H1-13 | 待签 |
| 纯函数与水位 | breaker:193–251、477–521；fault_observations:104–117 / H1-13/15/18 | 待签 |
| 预算/租约隔离 | budget:164–203、worker_loop:757–825、957–977 / H1-02/04/11/12 | 待签 |

breaker 人工签名、时间、SHA、六点结论 **待填写**；三处 TODO 保持不变。门禁全绿、可接受 FC-E 无高危报告、H1 真人签字三锁必须分别成立。

### 正式 FC-E 返回的待验证风险（不代替人审）

唯一 deepseek-r1 响应已收到，**报告未通过 v2 门禁**；四条 fact 中两条行号不匹配作废，五不变量逐项覆盖不完整。参见 [正式接收记录与原文](../artifacts/ai-evidence/review-0929-formal-v2-report.md)。

| 原假设 | 人工/领域后续验证入口 | 当前状态 |
|---|---|---|
| h1 medium：未知拒绝 hold 影响后续容量 | 上文预算 A/B 的容量、不双计和晚到结算限制 | 待验证，保守占额不自动等于缺陷 |
| h2 high：崩溃/重启中的 probe fencing 竞争 | 补具体 owner/token/expiry/事务交错，再对照 H1-16/17/20 与 D 并发/旧 token 案例 | 待验证；原唯一引用 f4 INVALID，未确认代码缺陷 |
| h3 low：同时间戳新事件可能遗漏 | H1-18/19 与 D equal-time 行为/mutation；仍需具体反例 | 待验证；不能由既有测试排除所有交错 |
| h4 medium：5xx 含明确拒绝体归 unknown 可能错误 | 与本轮“5xx/transport unknown 优先”要求逐项对照 | 与用户要求冲突，不采纳削弱分类建议 |

D 在 C552 的 47 项独立 focused、九组 mutation 红/恢复绿及 I 六门禁均已完成；这些本地证据不能替 FC-E 修补原引用/意见或代替真人签名。唯一请求额度已用，本轮不追加调用。T6 三锁仍缺可接受 FC-E 与 H1 签字。

## H3：Schema 仍为 1.0.0 candidate

沿用已通过独立验收的 optional+nullable 修复；本轮未修改 Schema。无采集允许缺失/null，不能补 0；数值需要 audit，0 需要 complete/证据/空 issue IDs；正数与 unique IDs 数量、scope、追溯的消费侧限制保留。新增 optional 字段按 minor，optional→required 是 major/2.0.0；不自行冻结。

H3 人工审批人/时间/Schema SHA/准入范围 **待填写**；`collected=未采集`，`review=unsigned`，`freeze=NOT_RUN`。C552 与已验收 `318dd4f26f27cda25e4278772bcce6b508023c26` 的 Schema 文档 blob 同为 `ecf43b4f705bc8733af90751bbae6c9f0cf6fb29`，内容未变；这不是本轮重新执行 Schema 行为验收。

## 入口与演练依赖清单

| 项目 | 当前状态 | 原条件/缺项 |
|---|---|---|
| T6 merge/tag/三连冒烟 | NOT_RUN | 三锁未齐；G 无执行权，不能以本地修复门禁替代 |
| T9 生产采集/GUI 接线 | NOT_RUN | H3 Schema 冻结及消费侧约束；不伪造 audit 数据 |
| T10 演练 | NOT_RUN | acceptance 后、彩排前；保留原实现/人工安排，不碰 live 子进程 |
| T11 课题入口 | NOT_RUN | 课题路径/身份、端口、预算、输出证据及适用 live 授权待核实 |
| `demo/run-demo.ps1 -Mock` | 本轮 NOT_RUN | 仅展示；不能证明任务运行 |
| `-Replay <实际 rehearsal.json> -Port <空闲端口>` | 本轮 NOT_RUN | 仅回放；必须保留 provenance=replay |
| `-AuthorizeLive -Executor evomap -Model evomap-gpt-5.6-sol -Mode manual` | NOT_RUN | 凭据/可用性、预算、端口、证据与原条件；未执行 |

本轮 I 在 C552 实跑 `contract_local` 六门禁通过：focused 408、full 862/2 warnings、strict 87、build/SDK/分发，均 exit 0；G 核对原日志并在 [治理记录](../artifacts/ai-evidence/fc-remediation-governance-0929-report.md) 分别登记独立 D/正式 FC-E。蜂群 `interface_live`/`task_live` 均 NOT_RUN；长期运行、发布、生产合并/tag/冻结均未执行。正式 FC-E 的模型调用不替代蜂群 live 验收或人类签字。
