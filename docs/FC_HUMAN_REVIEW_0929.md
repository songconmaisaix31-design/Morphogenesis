# FC 五项修复候选人工复核包 · 2026-09-29

**AI 只备料，H1/H3 均 unsigned；共同候选 SHA 待主控提供。** 当前治理 HEAD 来自 C 单轨 `e6ac45ffefc171a7215f8db19bc4a28af24ec4fc`，不是 A+B+C 测试候选。新候选逐字代码和行号仅在收到共同不可变 SHA 后补入，旧材料 [FC_HUMAN_REVIEW_0928](FC_HUMAN_REVIEW_0928.md) 原文、签名槽、历史失败均保留。

本轮五项生产修复已经用户授权；不再沿用旧 cost_state“未授权”状态。代码修复交付、独立验收、正式 FC-E、真人审批是不同证据。

## H1：先预算 A/B，再 breaker

### 预算 A：unknown hold 与同任务 pending 冲突

共同 SHA 后逐字备料：`BudgetLedger.snapshot/reserve/mark_unknown_rejection/settle`，Worker 每候选 request_id、confirmed_rejection 继续条件、unknown_effect 停止与 TaskLedger 持久隔离入口。不能把容量、attempt、模型价格、burn、租约拒绝当成 pending 自锁。

| 人工手推步骤 | 待补共同 SHA 引文 | 人工记录 |
|---|---|---|
| 首次 reserve | request_id/task_id 幂等、pending 计数 | 待填写 |
| 确认拒绝但费用未知 | uncertain 状态、full hold 保留 | 待填写 |
| 同任务新 request_id | pending 冲突与容量判断分开 | 待填写 |
| B ≥ H1+H2 与 B < H1+H2 | 两种可用额度下是否准入/发送 | 待填写 |
| unknown_effect 且费用已知 | 任务隔离跨重启、无新远端请求 | 待填写 |

### 预算 B：可用额度、事后结算、终结 hold、lower usage

| 人工复核点 | 必须逐字核对的入口 | 人工记录 |
|---|---|---|
| 可用额度与同一 hold 是否双计 | admitted 与 status!=settled 的 hold，准入求和 | 待填写 |
| 事后账单/晚到 usage | 是否存在 uncertain→settled 的入口，非 pending settle 行为；不存在时如实说明 | 待填写 |
| 任务终结/重启 | hold 是否继续占额度；不将长期保守占用混作真实重复收费 | 待填写 |
| lower usage | `max(estimate, reserved)` 承诺额度与实际估费用分开 | 待填写 |
| unbounded allowance | 不能声称上游真实账单具有硬上限 | 待填写 |
| reservation 的 cost_state | 本次 reservation 与全局 snapshot 分开；无价格仍 unknown | 待填写 |

预算人工结论槽：复核人/时间/完整候选 SHA **待填写**；A、B 各自“死锁 / 超支 / 两者都不是 / 证据不足”及前提 **待填写**。AI 不代填结论或签字。

### breaker 四态、fencing 与六点

收到候选后从其 git blob 提取 `transition` 的四态 × AggregateUpdated/CooldownElapsed/ProbeSucceeded/ProbeFailed 矩阵，保留原三处 TODO 的文字并列出新行号。联合核对 `try_claim_probe`、`_finish_probe` 的同事务条件更新、owner/token/expiry、TTL fresh token 与恢复后的 observation 水位，不只检查纯函数。

| 六点 | 共同候选材料要求 | 人工结论 |
|---|---|---|
| 转移穷举 | 四态四事件、非法输入、更新后状态 | 待签 |
| suspended 双阈值及欠费例外 | sample_count/threshold/min_samples 与 confirmed rejection | 待签 |
| 竞态与 fencing | 双 Worker 单槽、同 owner 旧 token、TTL 前后、迟到结果 | 待签 |
| Retry-After | 提示优先级、到期、延长、未知冷却 | 待签 |
| 纯函数与水位 | 无隐式 I/O/时钟，恢复前旧样本不重熔断且新样本仍有效 | 待签 |
| 预算/租约隔离 | 路由资格不改预算，失租不提交，attempt 计数与有界退出 | 待签 |

breaker 人工签名、时间、SHA、六点结论 **待填写**；三处 TODO 保持不变。门禁全绿、可接受 FC-E 无高危报告、H1 真人签字三锁必须分别成立。

## H3：Schema 仍为 1.0.0 candidate

沿用已通过独立验收的 optional+nullable 修复；本轮未修改 Schema。无采集允许缺失/null，不能补 0；数值需要 audit，0 需要 complete/证据/空 issue IDs；正数与 unique IDs 数量、scope、追溯的消费侧限制保留。新增 optional 字段按 minor，optional→required 是 major/2.0.0；不自行冻结。

H3 人工审批人/时间/Schema SHA/准入范围 **待填写**；`collected=未采集`，`review=unsigned`，`freeze=NOT_RUN`。共同候选 Schema blob 与原验收版本的对应关系待候选到达核对。

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

本轮 `contract_local` 仅待登记共同候选实际门禁，`interface_live`/`task_live` 均 NOT_RUN；长期运行、发布、生产合并/tag/冻结均未执行。正式 FC-E 配置与缺项见 [G 记录](../artifacts/ai-evidence/fc-remediation-governance-0929-report.md)，不是 Codex 代评。
