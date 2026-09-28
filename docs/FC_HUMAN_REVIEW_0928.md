# P0 预算语义 / T5 / H1 — 人工复核材料

## 今晚先做：budget.py 场景 A/B（人类专属结论）

队长 2026-09-28 晚间要求逐行手推。以下仅为 AI 整理的源码索引和空白工作表，
**没有人工签字，没有替人给出“死锁/超支/两者都不是”的结论**。
使用 `morph-fc-e` 的 `73e64cc70116ac658d85591d082c0684a4952c99`，不要误读尚未合入 FC
的 decentralized-swarm/budget.py。先完成预算复核，再看本文后半 breaker 矩阵。

### 源码字段与计数入口

| 代码（swarm/budget.py） | 需人工逐项核对的真实语句 |
|---|---|
| 80–82 | uncertain 计 status='uncertain'；pending 计 status='pending'；holds 求和所有 status!='settled' 的 reserved_usd |
| 83、103–111 | estimate_usd、tokens、usage/cost unknown 与 admission_charged_usd 是不同口径，不能混作服务端账单 |
| 130–153 | reserve 校验模型价格/请求边界；verified 使用明确上限，unbounded 使用 operator allowance（不是服务端硬上限） |
| 162–172 | 持久请求数/每任务尝试数/运行上限、既有 sleeping 检查 |
| 178–180 | 相同 request_id 总是冲突；相同 task_id 只有 pending 触发该冲突 |
| 181–194 | burn-rate 另有约束；准入式为 SUM(admitted_usd)+holds+新 reservation_amount <= max_cost_usd |
| 199–202 | 插入新 pending reservation，保留 request_id 与 reserved_usd |
| 215–235 | mark_unknown_rejection 仅 pending→uncertain，并设置 settled_at；没有写 admitted_usd/estimate_usd，也没有在此调用 _trip |
| 244–257 | settle 先解析 usage；非 pending 时立即返回已有 snapshot（有既存 settlement 冲突时抛错） |
| 265–269 | 真正未知 usage 的 pending→uncertain 路径可能 _trip('unknown_usage') |
| 271–286 | 已知 usage 但费用未知仍留 hold；可估费用时 admitted=max(estimate,原hold)，status='settled' |
| 287–298 | 单次边界违反与已估费用耗尽触发 _trip |

Worker 对应入口（swarm/worker_loop.py）：757–758 每个候选预留的 request_id 为
`task_id:lease.token:index`；777 调该候选 executor；793–799 区分 confirmed_rejection +
uncertain 与真正 unknown_effect；809–826 未知效果提前停止；849、856–859 决定受控切换。
切换事实 switched_to 要到下一候选准入成功后才写入（760–764）。

### 场景 A：unknown hold + 同任务切换请求

建议先固定同一 task_id、不同 request_id，预算 B、首笔 hold H1、新请求 hold H2；
满足价格匹配、尝试上限、burn-rate、租约等前置。把 B>=H1+H2 与 B<H1+H2 分别走一遍。
不能把模型价格不匹配或预算容量用尽导致的拒绝误记为“自己的 pending 自锁”。

| 步骤 | 代码入口 | 首笔 status / pending计数 / hold总和 / admitted总和 | 人工核对记录 |
|---|---|---|---|
| 首笔 reserve | 130、178、193、199 | 待填写 | 待填写 |
| 已确认拒绝但费用未知 | 215、229、233 | 待填写 | 待填写 |
| Worker 选择后一候选 | worker_loop:849；757 | 待填写 | 待填写 |
| 新 request_id 的 reserve 冲突判断 | 178 | 待填写 | 待填写 |
| 容量与请求计数判断 | 162–194 | 待填写 | 待填写 |
| 第二次 execute 是否发生 | worker_loop:777 | 待填写 | 待填写 |

### 场景 B：unknown hold + 服务端事后扣费 + 任务终结

先走 A，再分两种输入：外部账单只在服务端出现；以及调用方尝试用晚到 usage 对原
reservation 调 settle。请明确账单是否有真实接入函数，不能假定代码里存在自动对账。
在所审 budget.py 中，非 pending 的 settle 早退（253–257），没有“uncertain→billed”
分支；这是需要人工判断的事实边界，不是已通过的账单处理设计。

| 步骤 | 代码入口/需确认项 | hold / admitted / estimate / 外部真实账单四列分别填写 | 人工核对记录 |
|---|---|---|---|
| 首笔保持 unknown hold | 82、233 | 待填写 | 待填写 |
| 服务端事后扣费 | 明确本项目是否接收账单、入口在哪里 | 待填写 | 待填写 |
| 晚到 usage 尝试 settle 原笔 | 244–257 | 待填写 | 待填写 |
| 切换请求结算 | 271–286；区分已知估值与未知费用 | 待填写 | 待填写 |
| 任务终结/重复结算 | worker_loop 调用点；settle 幂等早退 | 待填写 | 待填写 |
| 次日重启/再次准入 | snapshot、reserve 持久化读取 | 待填写 | 待填写 |

人工需单独判定：①是否重复计算同一 reservation；②是否长期保守占用而不是重复收费；
③unbounded 请求的实际费用可能超过 allowance 时能否宣称硬预算保证；④账单晚到是否
可被记录以及需要怎样的人工对账流程。请在结论中写清前提，不能仅写笼统“没问题”。

### 人工结论登记槽（原文由队长提供，随后同步 TASKS.md）

- 复核人真实姓名/签名：**待填写**。
- 时间与生产 SHA：**待填写**（材料基线 73e64cc）。
- 场景 A：死锁 / 超支 / 两者都不是 / 证据不足；逐行记录：**待填写**。
- 场景 B：死锁 / 超支 / 两者都不是 / 证据不足；逐行记录：**待填写**。
- 费用未知、晚到证据、unbounded 前提与可接受限制：**待填写**。
- 是否允许进入冻结候选；如需修改，明确批准的生产 Owner/文件：**待填写**。

---

准备人：codex/master-control，2026-09-28。**这是材料，不是人工签字或通过结论。**
源码锚定 `73e64cc70116ac658d85591d082c0684a4952c99` 的 `swarm/breaker.py`；该文件来自 FC-C `8c7e2b6`。复核前若生产代码变化，重新生成行号与材料。原始 `TODO-HUMAN-REVIEW` 保留于第 192、558、633 行。

## 四态 × 四事件转移矩阵

符号：I=insufficient_evidence，N=normal，S=suspended，P=probing_recovery；“保持”表示无动作。以下精确描述现有实现，不代表审批。

| 当前状态 | aggregate | cooldown_expired | probe_success | probe_failure |
|---|---|---|---|---|
| I | 满足熔断条件→S；否则 sample_count≥min_samples→N；否则保持 | 保持 | 保持 | 保持 |
| N | 满足熔断条件→S；否则保持 | 保持 | 保持 | 保持 |
| S | 仅较晚 Retry-After 延长冷却；否则保持 | cooldown_until 非空且≤now→P，申请探测槽；否则保持 | 保持 | 保持 |
| P | 保持，等待探测事件 | probe_expires_at 非空且≤now→P，重领探测槽；否则保持 | 当前 owner 且未过期→N，释放槽、清窗口；否则保持 | 当前 owner 且未过期→S，释放槽、设冷却；否则保持 |

转移核心 `transition` 为第 183–240 行。熔断条件第 153–161 行：reason 属于配置 direct_suspend_reasons 且 confirmed_rejections>0 可立即熔断；其他原因必须同时 `sample_count >= failure_threshold` 与 `sample_count >= min_samples`。这里是故障样本计数，**不是故障率**。默认 min_samples=5（123 行），threshold、窗口、冷却、探测 TTL 均需注入（120–125 行）。

动作落地：`_apply_aggregate` 第 456–487 行；`_next_values` 第 489 行起；`try_claim_probe` 第 535–580 行；`_finish_probe` 第 595–655 行。纯函数只判断 owner/时效；token 校验由持久化层完成，须联合复核。

## 半开竞争与 fencing 摘录

事务入口复用 `swarm/task_ledger.py:41–47`：

```python
# task_ledger.py:47
db.execute("BEGIN IMMEDIATE" if write else "BEGIN")
# breaker.py:329–332
@contextmanager
def _write(self) -> Iterator[sqlite3.Connection]:
    with connection(self.path, write=True, timeout=self.timeout_seconds) as db:
        yield db
```

唯一探测槽：同事务内读取现状、纯函数判断、带 token 和时效的条件 UPDATE；只认 `rowcount == 1`。

```python
# breaker.py:560–572
cursor = db.execute(
    "UPDATE breaker_states SET state='probing_recovery', probe_owner=?, "
    "probe_token=probe_token+1, probe_expires_at=?, updated_at=? "
    "WHERE swarm_id=? AND provider=? AND reason=? AND probe_token=? "
    "AND ((state='suspended' AND cooldown_until IS NOT NULL AND cooldown_until<=?) "
    "OR (state='probing_recovery' AND probe_expires_at IS NOT NULL AND probe_expires_at<=?))",
    (worker_id, expires_at, at, self.swarm_id, provider, reason,
     current.probe_token, at, at),
)
if cursor.rowcount != 1:
    return None
```

旧结果隔离：调用方传入其当时领取的 token，不使用数据库最新 token 代替。即使同一 worker 重领，旧 token 也应失败。

```python
# breaker.py:636–643
cursor = db.execute(
    f"UPDATE breaker_states SET {fields} WHERE swarm_id=? AND provider=? AND reason=? "
    "AND state='probing_recovery' AND probe_owner=? AND probe_token=? "
    "AND probe_expires_at IS NOT NULL AND probe_expires_at>?",
    (*args, self.swarm_id, provider, reason, worker_id, probe_token, at),
)
if cursor.rowcount != 1:
    return False
```

## 六个核对点（队长填写）

| 核对点 | 代码/测试证据入口 | 人工结论 |
|---|---|---|
| 转移穷举 | transition:183；四态四事件及非法输入；tests/swarm/test_breaker.py:144、208、227 | 待签 |
| suspended 双条件和欠费例外 | breaker:153；test_threshold_and_min_samples_both_gate_suspension:144；确认 sample_count 的语义 | 待签 |
| 竞态窗口与同 owner 旧 token | breaker:535、595；test_same_owner_stale_probe_result_is_fenced_by_token:436；test_multiprocess_half_open_race_yields_exactly_one_probe:571 | 待签 |
| Retry-After 优先级、到期、延长 | cooldown_deadline:172；transition:201；test_retry_after_hint_sets_probe_time_verbatim:353；过期提示原值保留 | 待签 |
| 纯函数、无隐含 I/O/时钟读 | transition:183；test_transition_is_pure_and_repeatable:257；参数 frozen/strict:57–58 | 待签 |
| 预算/租约隔离 | breaker:283–285、395；Worker._process 的 reserve:757、提交前 handoff:957；逐条对照 QWEN 五不变量 | 待签 |

## FC-E 意见与门禁

补评范围为 `348cf8d..73e64cc`，目标 `morph-fc-e/artifacts/ai-evidence/review-0928-integration.md`。本日首次 dsh 启动真实返回 `dsh: TRANSPORT: Connection error.`，进程已回 shell，未见报告，成本/远端效果未知。队长随后明确“开始修复”，总控发射一次同模型 deepseek-r1 新调用；它返回字面工具调用标记后退出，没有实际读取文件或生成报告，`ctx_20b51afb27b6` 已按真实退出证据 abandon，未再次自动调用。**此栏目前无 FC-E 评审意见，不能填写“未发现高危”或“五不变量未发现违反”。** 下一步建议先修复/验证评审工具通道，再由队长决定新的有界补评调用；模型保持 deepseek-r1。

T3 正在修复旧 FC-D 假绿测试；本材料引用的是现有测试入口，尚不是今天全量或 mutation 验收回执。昨夜 698 passed/87 strict/build/SDK 仅作为历史记录；interface_live、task_live 仍 not_run。

## 人类签字槽与 T6

- 复核人：待队长填写。
- 时间：待队长填写。
- 复核生产 SHA：待队长确认（当前为 73e64cc）。
- 六项结论/发现与处理：待队长填写。
- 是否允许将三处 TODO-HUMAN-REVIEW 替换为签名：待队长明确授权，交生产 Owner 操作。
- T6 的 merge/tag 授权：待队长明确授权；门禁全绿 + FC-E 无高危 + 人工签字缺一不可。

总控不会替人签字，也不会因预定时间到达而推定批准。
