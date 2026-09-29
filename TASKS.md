# TASKS.md — FC 轮任务账本

## 2026-09-29 今日新增台账（本次授权；历史记录保留）

**I 今日最终整合（受限候选）：** `morph-closeout-integration-0929` 的标准合并 `4c3dc46e7c0459680a7567ff6d91ba44301c3819` 接纳 A `3d8bb856efadbb1bee4a69bc37c56d3ef4d24cfd` 与 B 最终材料 `092cadaf497482e00518dfd86d958a81c876a7bd`；D `969d3274622538a36ac8a60e09c41be86bea9c60` 报告单文件原 blob 引入。B 后续仅四治理文档、Schema 对 318dd 字节不变；候选生产、A 两测试、AGENTS/SWARM/锁不变。精确合并源码 focused 20 / exit 0（43.60s），Schema 12/12、24/24、13/13 / exit 0；首次源码树内 basetemp 被 protected_runtime_state 拒绝，18 failed / 2 passed / exit 1 原样保留，改用精确导出源码与平级状态目录后通过。699/strict87 仅复用 A f477 原日志，非 merge SHA 重跑。C `morph-readonly-app-0929@621f588988899bdbc7c7a83e893369c4145d89b3` 独立保留；cost_state 语义 exit 1 / OPEN、unknown hold 无晚到结算、H1/H3/正式 deepseek FC-E 未闭合。正式 FC-E 已授权范围保留，真实限制是原隔离 profile/launcher 与适用调用上限未核实，不替代引擎。发布三锁未齐，无生产合并/tag/live；详见 [I 集成报告](artifacts/ai-evidence/integration-0929-closeout.md)，最终材料提交与 push 以交付回执为准。

用户授权今日底层收口与受限只读应用并行，取代下方昨夜“尚未收到 nullable 修复授权”的当时状态；不追认历史失败或冻结。计划和排他写权见 `docs/FC_DAY_PLAN_0929.md` 及 `docs/PLAN.md` 今日附录。

| 轨 | 基线 / task / dispatch | 今日状态与限制 |
|---|---|---|
| A `morph-fc-tests-0929` | `73e64cc70116ac658d85591d082c0684a4952c99`；`task_bf99e1b4ba10 / ctx_d0bbed22831d` | 最终 `3d8bb856efadbb1bee4a69bc37c56d3ef4d24cfd` 已 push；Owner focused 20/full 699（2 warnings）/strict 87 exit 0；D 独立 focused 20、mutation call_count 红/恢复绿通过，cost_state 独立语义 exit 1 仍 OPEN |
| B `morph-schema-closeout-0929` | `73798cd6f05210f2bd9b1eebfd6f9f0dd6e842db`；实现 `task_d536a112682f / ctx_170180e15e72`；收口 `task_507418789086 / ctx_bf1fdfa6a61e` | Schema 交付 `318dd4f26f27cda25e4278772bcce6b508023c26` 已 push；Owner 12/12、24/24、13/13 exit 0；D 独立修前 43/44、修后 44/44，nullable-only；H3 pending，仍 candidate；材料见 `docs/FC_CLOSEOUT_0929.md` |
| C `morph-readonly-app-0929` | `2957b408ce922369a595a8acd43a882eb85897d3`；`task_75eedbf12038 / ctx_9320f0ef60fa` | 最终 `621f588988899bdbc7c7a83e893369c4145d89b3`；Owner 契约/53 T5/build/44 采用语义/72 页面检查 exit 0；D 独立 T5 53、双 bundle 字节、3 历史 run replay HTTP→DOM/缺失/0/多 attempt/可访问性通过；越契约输入既有限制单列 |

历史 Schema 原九例 8/9、扩展十二例 11/12、exit 1 继续保留；今日 D 已独立验收 nullable 修复，当前目标仍 `1.0.0 candidate`、待人工 H3。optional 新增 minor、optional→required 为破坏性 major（2.0.0），不得沿用 1.1 升级必填说法。

昨夜 T3 两次 mutation 假绿、裁撤及 demo-build.1 后续候选保留；FC-E 正式 deepseek v2 与 H1 真人签字仍缺，今天 Codex 验收不代替。三锁未齐不生产合并/tag；不实现预算事后对账、生产日志接线，不跑付费 live。

主控 10:51/10:53 转发 A 中间简报（非本轨独立验收）：focused 20 passed；真实语义复现 exit 1，合法 usage 但无价格时预算账本 uncertain/unknown，`73e64cc:swarm/worker_loop.py:839` 的 FaultObservation.cost_state 却为 settled。登记为 P0 语义信息准确性待验/待队长决策；主控已请求最小元数据修复确认，尚未授权，未修复，未见预算释放/超支证据。A 首轮 breaker mutation 被 blocked executor `call_count 1 != 0` 抓获，finally 恢复后目标通过、生产 diff 为空；正式结果待提交。不得用通过的测试覆盖该真实失败。

B 启动记录：初始 prompt 未实际提交，主控仅补 Enter 恢复为 working/live，沿用原 task/dispatch，未另建派发。

主控 10:54 转发 A 阶段提交 `f4779d45a1b1417ffa6bce37708e9a68d46cf4e5`，分支 `morph-fc-tests-0929` 已 push/远端一致；focused 20 passed、breaker mutation 语义红/恢复绿、strict 87 通过，全量运行中。仅登记阶段交付/待独立验收，A 尚未完成，cost_state exit 1 继续未解决。

B 今日修前复现：基线 `73798cd6` 原矩阵 11/12、扩展 23/24、控制 13/13、exit 1，唯一失败仍是显式 count=null/audit 缺失；修后首轮原矩阵 12/12、扩展 24/24、控制 13/13、exit 0。Schema 除一个 required 删除外完全一致，FaultObservation 14 字段与精确 FC 源导出一致；零值/负值/孤立 audit/非法来源/非 audit 约束保留。任意正数与 unique(issue IDs) 数量不一致仍为已声明的消费侧校验责任，未实现生产消费者，不把该限制当本次修复能力。此前一次证据环境检查因历史提取文件 CRLF 字节不一致 exit 1，已保留日志，改从 Git 原字节提取到本轨 ignored `.runtime`，未改他树或安装依赖。

B 修复提交 `188fae46de4f3d2fe4943461a62a9626caa5325d` 已在不可变 Git blob 上复验，12/12、24/24、13/13、exit 0 与工作树结果一致；旧 PLAN 前缀和 TASKS 历史原文不变、changed paths 全在写权内。证据 `artifacts/ai-evidence/schema-0929-exact-summary.json`；最终证据提交不再改 Schema，交付为 `318dd4f26f27cda25e4278772bcce6b508023c26`，本次续接已核对远端一致及开工 clean。

主控 10:56 转发 C（Owner 结果，非 B 独立验收）：产品 `8c57c4964fbf78b90d7232d3644975dab277d277`，最终 `621f588988899bdbc7c7a83e893369c4145d89b3`；六 owned 文件，push/remote 一致/clean；契约、53 T5、build、44 采用语义浏览器、既有 72 页面回归 exit 0。真实历史输入明确作为 replay，未新跑 live；C 资源已释放，D 独立验收启动。主控要求 B 完成本轨即交付，不等待 A 全量或 D 结论；后续汇总由受限集成登记。

**本次收口续接取代上一段当时的“不等待”安排：** 同一 B Agent/树/分支以新 Task 仅维护 H1/H3 材料、今日台账和计划状态，等待主控确认 A/D 结果完整后封存；Schema 本体没有默认返修权。索引 [FC_CLOSEOUT_0929](docs/FC_CLOSEOUT_0929.md) 链接既有 H1 四态矩阵/fencing/TODO、A 报告和 Handoff，不改人工签名或 TODO。11:03 主控转发 A 最终 `3d8bb856efadbb1bee4a69bc37c56d3ef4d24cfd`；测试仍 `f4779d45a1b1417ffa6bce37708e9a68d46cf4e5`，Owner full 699/2 warnings/450.96s、strict 87、focused 20 通过，生产 cost_state 语义 exit 1 未解决、队长修复授权未到；D 独立结果仍 pending，不能宣称全部验收。

FC-E 只读入口检查：`dsh --help` 与 `dsh --profile headless --help` exit 0；本 Dispatch 的 DSH_HOME 未设置，原隔离 deepseek-r1 配置/正式工具通道未获验证，正式报告仍缺。检查没有安装、输出密钥或调用模型，不能补成 FC-E 通过；下一步须主控定位原 launcher/profile 与有界补评授权。H1/H3、生产修复、FC-E、合并/tag、T9/T10 与新 live 分别保持 pending/OPEN/NOT_RUN，不由 Owner 自验覆盖。

**11:06 主控转发 D 独立简报，11:13 最终报告补齐并通知封存：** A focused 20 与有效 breaker mutation 通过，cost_state 独立复现仍 exit 1；B 修前 43/44、修后 44/44，变化只有原 nullable 缺陷、其他限制不变；C 独立 T5 53、双 bundle 字节一致、3 历史 run replay HTTP→DOM 及缺失/0/多 attempt/可访问性通过。C 非法 `adoptions=[null]` 引发原 app.js 错误（exit 1），为越契约既有限制、未修复。B 仅登记 D 结论，不用 Owner 699/strict 冒充 D 重跑全量；D 也不代替 FC-E/H1/H3。

主控集成盘点/决策：A/B merge-tree 无重叠冲突，I 接续隔离 FC 候选、组合门禁待实际结果；C 与 FC 从 `605cf48` 分叉，Backend.jsx 和两 bundle 冲突，本轮分别保留候选，不强合前端、不触生产分支/tag。收口包阶段 `d9ce433677e2926ee1ab7b0f2e53a0ba84f005c7` 已 push；本次已补 [D 最终报告 969d3274622538a36ac8a60e09c41be86bea9c60](https://github.com/songconmaisaix31-design/Morphogenesis/blob/969d3274622538a36ac8a60e09c41be86bea9c60/artifacts/ai-evidence/acceptance-0929-closeout.md) 并按主控通知封存。D 报告分支 `morph-closeout-acceptance-0929`，B 只读核对远端同 SHA/报告 Git blob 存在；主控转发引用 25 范围+13 短引文+10 预算段最终 exit 0，初错记录仍保留。FC 整体 BLOCKED；未改 Schema/H1 签字/TODO 或他轨文件。

本次文档验证：`git diff --check` exit 0；`git diff --exit-code 318dd4f26f27cda25e4278772bcce6b508023c26 -- docs/FC_LOG_SCHEMA_DRAFT_0928.md docs/FC_HUMAN_REVIEW_0928.md swarm tests artifacts` exit 0。内联 Python 比较确认仅四个授权文档变化、TASKS 历史尾段/PLAN 旧前缀逐字保留，索引的本地目标及精确 SHA 的 Git blob 均存在；不新增测试，不重跑全量，不把文档检查计作 Schema 独立验收。

## 当前有效段（2026-09-28 治理返修）

### 预算A/B（代码核对，待队长交叉复核）

**A场景：不死锁**（指同任务pending冲突，前提新request_id且其他预算/attempt/burn限制允许）。budget.py:233将pending→uncertain；178冲突条件request_id相等 OR 同task pending；Worker:757-758 nextindex生成新request_id。相同request_id继续拒绝是幂等防重复。

**B场景：无双计**（当前账本同一hold，不代表无实际超支风险）。budget.py:82对所有非settled累加hold，191-193 SUM(admitted_usd)+holds+新hold对cap；199初始admitted_usd NULL，233只改status/time，所以unknown仍占allowance、不再作为pending互斥，未在两边重复入账。

**无事后结算路径**：budget.py:253-257 status!=pending直接return；没有uncertain→settled，迟到usage不更新tokens/cost/estimate/admitted。任务结束长期悬挂：Worker:796标记unknown后800_active=None；finally:989-991只处理仍active，旧unknown不会被释放；budget.py:82持续计入，同swarm预算周期内unknown hold长期占用。明确"按队长术语是预算慢性占用/泄漏风险"，不是实现自动双计；90-100/181-190未知hold还进入burn计算。当前hold无法自动转换为实际账单，unbounded请求的实际额可能大于预留，这点不能由无双计排除。

**lower usage规则**：budget.py:281-285 的max(estimate,reserved)维持普通pending→settled不返还allowance；uncertain guard先返回，所以没有unknown→settled转换可称它已遵守或破坏规则。未来若补结算需保留单次记账与不返还承诺额规则，今晚不实现。

### 预算A/B核对引用证据

```python
# budget.py:80-82 @73e64cc
        uncertain = sum(row["status"] == "uncertain" for row in rows)
        pending = sum(row["status"] == "pending" for row in rows)
        holds = sum(float(row["reserved_usd"]) for row in rows if row["status"] != "settled")

# budget.py:178-180 @73e64cc
            if db.execute("SELECT 1 FROM budget_reservations WHERE swarm_id=? AND (request_id=? OR (task_id=? AND status='pending'))",
                          (self.swarm_id, request_id, task_id)).fetchone():
                raise BudgetBlocked("task_already_reserved_no_retry")

# budget.py:191-194 @73e64cc
            spent = float(db.execute("SELECT COALESCE(SUM(admitted_usd),0) FROM budget_reservations "
                                     "WHERE swarm_id=?", (self.swarm_id,)).fetchone()[0])
            if self.policy.admission_control == "enabled" and spent + state.reserved_estimate_usd + reservation_amount > self.policy.max_cost_usd:
                raise BudgetBlocked("swarm_reservation_capacity", self.policy.burn_window_seconds)

# budget.py:199-202 @73e64cc
            db.execute("INSERT INTO budget_reservations VALUES (?,?,?,?,?,'pending',?,NULL,NULL,NULL,?,?,'unknown',?,?,'unknown',NULL,NULL)",
                       (reservation.reservation_id, self.swarm_id, worker_id, task_id,
                        reservation.model_dump_json(), now, reservation_amount, request_id, bound.request_bound,
                        self.policy.admission_control))

# budget.py:229-235 @73e64cc
            if row["status"] != "pending":
                return self._snapshot(db, reservation.worker_id, now)
            if now < reservation.created_at:
                raise ValueError("time cannot move backwards")
            db.execute("UPDATE budget_reservations SET status='uncertain',settled_at=? WHERE reservation_id=?",
                       (now, reservation.reservation_id))
            return self._snapshot(db, reservation.worker_id, now)

# budget.py:251-257 @73e64cc
        with self._transaction() as db:
            row = self._stored(db, reservation)
            if row["status"] != "pending":
                if row["settlement"] is not None and settlement is not None and row["settlement"] != settlement:
                    raise ValueError("conflicting usage settlement")
                # Idempotent replay does not overwrite unknown evidence or charge twice.
                return self._snapshot(db, reservation.worker_id, now)

# budget.py:281-286 @73e64cc
                    # Usage plus local prices is not a bill. Never free committed
                    # allowance on a lower estimate, even for an unbounded request.
                    admitted = max(estimate, reservation.reserved_estimate_usd)
                    db.execute("UPDATE budget_reservations SET status='settled',usage_metering='verified',cost='estimated',settled_at=?,tokens=?,estimate_usd=?,settlement=?,admitted_usd=? "
                               "WHERE reservation_id=?", (now, reported.total_tokens, estimate, settlement, admitted,
                                                          reservation.reservation_id))

# worker_loop.py:757-758 @73e64cc
                reservation = self.budget.reserve(self.worker_id, signal.task_id, bound,
                                                  request_id=f"{signal.task_id}:{lease.token}:{index}")

# worker_loop.py:793-800 @73e64cc
                if result.uncertain and classification == CONFIRMED_REJECTION:
                    # Known rejection without observed usage: faithful unknown
                    # cost hold that keeps the chain admittable under it.
                    settled = self.budget.mark_unknown_rejection(self._active)
                else:
                    settled = (self.budget.mark_uncertain(self._active) if result.uncertain else
                               self.budget.settle(self._active, usage))
                self._active = None

# worker_loop.py:987-991 @73e64cc
            try:
                lease = keeper.stop()
                if self._active is not None:
                    self.budget.mark_uncertain(self._active)
                    self._active = None
```

### 预算A/B核对引用验证

```bash
# Script executed and verified segments match git repository
# Total segments checked: 10
# All segments match git repository content
```

## 2026-09-28 H1 检查点收尾（历史记录，以上方为准）

T3 原 Worker 已停止开发，将未完成测试保存并 push 到 `fix/fcd-interface-alignment`，
SHA `a821783f4f89ae727698087f6ed5fd0a7d1fdd89`，trailer `Swarm-Agent: qwen-code`。
仅测试文件变更，`breaker.py` 无 diff；此提交是 **WIP，不可合并**。
最近命令为 `.venv/Scripts/python.exe -m pytest tests/swarm/test_failure_chain_boundaries.py -v`
返回 14 passed / 22.54s，以及 `.venv/Scripts/python.exe tools/typecheck.py`
返回 no issues in 87 source files。全量 698 零回归和 mutation 敏感性均 **NOT_RUN**。

- 现象：unknown_effect 测试仍假绿，T3 验收拒收。
- 证据：该提交 `tests/swarm/test_failure_chain_boundaries.py:437` 新增 ledger.reserve，
  `:441` 的断言可被 `:445` 裸 except 吞掉；没有真实 Worker 执行次数断言。
  子集绿色不能证明"无后续请求"或五不变量成立，也不能推断生产逻辑已违反不变量。
- 建议：H1 后原 qwen Owner 接续，先读真实 runtime fixture，删除吞断言逻辑并以真实
  Worker 的 executor 调用计数/账本预留/租约拒绝证明行为，再做 mutation 与全量门禁。
- 需要队长决策：H1 人工结论与检查点后的接续指令；FC-E 工具通道修复后是否授权新的
  有界同模型补评。H4 的"选三只改文档"仍单独待确认，H3/T6 也未获批准。

总控已请求 H1 材料复核及 H4 确认。11:00 起停止开发，等待队长；不以材料准备代替
人工签字，不替换 TODO-HUMAN-REVIEW。T6 merge/tag/三连冒烟未执行。

## 2026-09-28 最新状态更新（历史记录，以上方为准）

权属已更新：主控只派发验收，治理文档由 Worker 独占；最新有效状态置顶，旧 10:56/11:00 状态
已被晚间授权替代。原文晚间误称 H4 在 morph-fc-docs-0928，现按已记录实际
morph-h4-docs-0928 修正。H4 真实 SHA 2957b40 已 rootff/push；T6 条件授权无需再问但
三锁缺口不能绕过。

T3 当前状态：22:11 第二次 mutation 删 breaker 转移仍绿（原生明确 The test still passes），
主控已按两轮失败协议停工；保存点 2d9d4304cfc0e1a3d4bfaeccb6ec5688aef60366 已
git push fix/fcd-interface-alignment；该提交实际缺 Swarm-Agent trailer（多行 shell 被截断），
不能改写公开历史。git diff --exit-code 73e64cc -- swarm/breaker.py 返回0；没有宣称字节级快照校验。ctx_86b253aba968 已在 native 回 shell 后
abandon，task_1821ef01c94e blocked。门禁不通过、拒收不合并；22:40 裁撤规则保留但尚未到时
不能写已经触发。

FC-E 当前状态：修订稿 78c07459e14b4817c83c608c68978a07b68b5f9f 已由作者推送，
自行撤回 token high 推断；主控仍拒收，假绿清单继续声称 call_count/覆盖充分，
引用行号不匹配指定 73 源码；静态无高危意见不能据此补锁。
报告路径：morph-fc-e/artifacts/ai-evidence/review-0928-integration-qwen-fallback.md；
初稿 SHA：2180e0223fac39c5213c4a04474a8082e291bf7c；
修订稿 SHA：78c07459e14b4817c83c608c68978a07b68b5f9f；
拒收原因：high 声称 token 竞态无具体失败交错、假绿评价错误、同源标签不够、
commit 缺 Swarm-Agent trailer、引用行号不匹配指定 73 源码。
两提交均缺 Swarm-Agent trailer，不允许重写已推历史。人类已被问是否授权一次仅证据校正的返修；
未答复。ctx_925755d7dd00 原生已回 shell 后 abandon，task_fbbababc2840 blocked，
禁止重启它或代做评审。

Budget A/B 和 H1 人工结论、签字仍未收到；不签字、不替换生产 TODO、不代得出人类结论。
H3 Schema 1.0.0 候选，冻结验收 BLOCKED；两项条件逻辑缺陷待队长决定是否仅修这两项；生产接线 NOT_RUN。T6 merge/tag/smoke 全部 NOT_RUN。

- T9：今晚不生成 GUI mock 或队友消息，依赖 H3 Schema 冻结。
- T10：挪到明天 acceptance 之后、彩排之前；今晚不实现，不触碰 live 子进程路径。
- benchmark WIP：POLL_MS 1000→120000 是 demo 演示风险；明天改回独立 BENCHMARK_POLL_MS；今晚不碰，不在冻结基线内。
- FC-E：明天补 deepseek-r1 正式异构评审；没有自动预约或执行。今晚降级报告仍拒收，是否继续证据校正待队长答复。

## 2026-09-29 当前状态（最新有效）

Schema 1.0.0 冻结 BLOCKED：独立验收 Agent 已验证 2e56fa1efaa030da5a52c614172654a4e6ea1188：
原九例 8/9 通过、扩展十二例 11/12 通过，exit 1；count=null 且 issue_audit 缺失仍被错误拒绝。
位置 docs/FC_LOG_SCHEMA_DRAFT_0928.md:1650-1652/allOf[1].then.required。
主控已按两轮红规则停止进一步实现并询问队长是否仅修复此处，尚未收到授权。
已通过部分：FaultObservation 14 字段精确匹配、非 audit 规则保留。

A/B 已代码核对待人工：TASKS.md 上方保留预算 A/B 详细证据，人工结论仍未收到。

H1 无签字：FC_HUMAN_REVIEW_0928.md 的人工签字槽仍待填写，未收到人工签字。

FC-E 今晚用户禁止返修、明天 deepseek-r1 按 v2：今晚禁止对 FC-E 报告返修，等待明天
新的异构评审。今晚降级的 qwen 报告拒收，未授权返修。

T3 已过 22:40 排除冻结候选、保留 fix 分支 demo-build.1：按裁撤规则，T3 未按时完成，
不再参与今晚冻结候选，保留 fix/fcd-interface-alignment 分支的 demo-build.1 首次 bump。

H4 完成：morph-h4-docs-0928 worktree 已完成，SHA 2957b40 已推送。

T6 merge/tag/smoke 未执行：三锁为"门禁全绿、可接受的 FC-E 无高危报告、队长 H1 人工签字"；
当前没有可接受的 FC-E 报告及 H1 签字，不能执行。Schema 阻塞未解决，仍有其他验收条件。

T9 等 Schema：GUI mock 生成依赖 H3 Schema 冻结，等待 Schema 修复和批准。

T10 明天：演练实现推迟到明天，等待 acceptance 通过后再实施。

benchmark 明天：基准测试的 POLL_MS 修复推迟到明天，不在今晚的冻结基线内。

## 历史状态标记（已被上方最新状态替代）

已验收冻结：此为旧状态，已被当前 Schema 阻塞状态替代。
FC-E 今晚返修待答复：此为旧状态，已被当前 FC-E 禁止返修、等待明日 deepseek-r1 替代。

## 2026-09-28 10:56 修复验收进展

| 任务 | 状态 | Commit / Dispatch | 门禁与限制 |
|---|---|---|---|
| T2 | 返修验收通过，已 push | `2a4dcb403e8ac1366d0c416b4a43a953f16fcea5`；`songconmaisaix31-design/morph-fc-docs-0928` | 只改一页证据；核对真实 `_record_failure_fact`、bbe9d77 精确 diff、来源及统计结论边界；ls-remote 与 HEAD 相同；未合并 |
| T3 | WIP，未验收 | `fix/fcd-interface-alignment`，base `73e64cc`；`ctx_e3ede6c38728` | 修后定向 14 passed / 22.63s；这是中间版本，后续还在编辑。全量、strict、mutation 均未取得回执；unknown_effect 仍缺真实 Worker/请求计数，不能当五不变量验证通过 |
| T4 / FC-E | 无有效报告，T6 保持冻结 | `ctx_20b51afb27b6` | 队长授权后同一 deepseek-r1 新调用返回字面工具标记而非工具执行，随后回 shell；目标报告仍不存在；已据实际退出 abandon，未自动再试，未改模型 |
| T5 | 人工材料就绪 | `docs/FC_HUMAN_REVIEW_0928.md` | 四态矩阵、fencing 摘录、六项清单已备；FC-E 意见缺失，H1 签字未填 |
| T7 | 只读分析完成并登记 | 源码基线 `73e64cc`；qwen `task_464f4005cf46`，总控独立核对下列行号 | 两条路径均不消费 category 实现分级衰减；零生产/测试实现 |
| T8 | 草案已生成并结构校验 | `docs/FC_LOG_SCHEMA_DRAFT_0928.md`，本次治理提交 | `Draft202012Validator.check_schema` 通过；实际模型导出，14 个 FaultObservation 字段保留；**未冻结**，H3 待人类拍板 |
| T11 | 预检部分完成 | 本段只登记状态 | 云 profile/Key 配置存在；课题 workspace 未明确；无 live 调用、无三连冒烟 |

### T7 category 的实际调用链（基线 73e64cc）

结论：**当前无 category 分级衰减消费路径**。`hub_client/models.py:52` 定义
`GenePolicy.category`；`hub_client/assets.py:39` 将其写入官方 Gene 资产，`:83`
将其写为 EvolutionEvent.intent。这证明有分类序列化用途，不证明运行时衰减使用它。
内部 `contracts/resolution.py:16` 的 Gene 没有 category 字段。

```text
Gene 召回：
LocalMetabolism.ingest (metabolism/service.py:101)
  -> GeneRow.body 写入 (:122)，GeneState.tau_seconds=self.tau_seconds (:130)
  -> inject (:166) 读取 active/applicable (:191)，调用 _evaluate (:193)
  -> _evaluate (:76/79) 使用 state.tau_seconds 计算 exp(-elapsed/tau)
  -> inject (:200/205) 以相似度 × 权重排序，按 budget 选 Gene
  -> Runtime._select (orchestration/runtime.py:120/129) 注入 state.genes (:137)
  -> Runtime._execute (:161) 将这些 Gene 传给 executor.execute
category 没有进入上述写入、权重读取或召回决策。

路由信号：
PheromoneField.deposit (swarm/pheromone.py:55)
  -> ledger.enqueue (:58)，_save (:50/64) 写 concentration/updated_at/multiplier
  -> for_records (:67/70) 调 _materialize (:41/46)
  -> concentration *= exp(-elapsed / (self.tau_seconds / multiplier))
  -> SoftmaxRouter.choose (swarm/router.py:33/55) 读取浓度
  -> score (:62) -> softmax/探索混合概率 (:79/82)
  -> rng.choices (:86) 返回所选 task
  -> Worker.run (swarm/worker_loop.py:1021) 调 choose，随后 _process (:1056)
feedback (swarm/pheromone.py:75/86) 按 success/reward 更新浓度和 multiplier；
它不是 category 分级。此链没有读取 category。
```

证据为 qwen 只读分析加总控逐段源码核对；不是 live 运行证明，也未建议自动实现。

### T11 配置与命令准备

- 云端 profile：本机阿里云 CLI 可用；配置 default / AK / cn-hangzhou，密钥字段已配置。
  只检查存在性/配置元数据，没有回显秘密、没有验证云端授权或创建云资源。
- DashScope：既有私有 key 文件存在；本轮 qwen3-coder-plus 已有实际模型和工具响应。
  deepseek-r1 补评未成功，不能把 key 存在或 qwen 成功当作 FC-E 报告。
- 课题 workspace：队长未提供明确路径/课题身份，未就绪核验。
- `demo/run-demo.ps1` 参数已读：`-Mock` 仅旧 dashboard 展示，不执行任务；
  `-Replay <实际 rehearsal.json> -Port <已核实空闲端口>` 只回放；
  `-AuthorizeLive -Executor evomap -Model evomap-gpt-5.6-sol -Mode manual`
  是可准备的 live 入口，仍需补端口/预算/输出证据并获得相应授权，**未执行**。
  三连冒烟依赖 T6 三锁；不能将 mock/replay 计作 task_live。
- Key 目前已到，不触发“未到 Plan B”。EvoMap 网关 live 凭据及可用性未核验，不宣称可用。

## 2026-09-28 10:43 修复恢复授权

队长在收到上述停止报告后明确指令“开始修复”。据此解除 T2/T3 本次停止，原 Worker、
worktree、branch 和写权不变，以同一 Task 的新 Dispatch 接续；T2 必须按精确 diff 纠错，
T3 完成真实接口测试和 mutation/全量/strict 验收。FC-E 同一 deepseek-r1 允许一次新的
有界发射，若仍连接失败或远端效果未知立即停止，不循环。原失败/中断记录不改写。
H4 的“选三”、H1 人工复核签字、H3 Schema 冻结和 T6 merge/tag 仍保留独立人类决策。

## 2026-09-28 后继总控接手与暂停（10:38 CST）

总控 `codex/master-control`，Orca Run `run_e46ee274f7c9`，当前 coordinator
`term_f20e387c-dcb7-4bd1-97d7-bf6a5b446b9f`，generation=3。计划见
`docs/FC_DAY_PLAN_0928.md`。评审生产基线 `73e64cc70116ac658d85591d082c0684a4952c99`；
第一代根工作树 `f3feb7f` 与已有 SWARM_SOL_PLAN WIP 保持只读。

| 任务 | 状态 | Commit / Dispatch | 门禁与证据 |
|---|---|---|---|
| 接手计划 | 已提交 | f804fb1；Swarm-Agent: codex/master-control | git diff --check 通过；原 Run 已绑定，三轨互斥写权已登记 |
| T1 | 等待 H4，未派发修改 | 无 | FC_ACCEPTANCE 仍记三选一未拍板；已请求“选三只改文档”确认，没有以沉默代批准 |
| T2 | **拒收，待队长决定返修** | cd8f6c9641a666b0c9cd8d713490b5515e8b3240；task_e3bb4948bc47 / ctx_3981895d6cd4 | qwen3-coder-plus 实际工具活动；git diff --check 绿，内容事实不通过；push 曾超时，后续只读 ls-remote 已确认远端为 cd8f6c9，没有重复推送 |
| T3 | **按停止协议中断，未修改测试** | base 73e64cc；task_1821ef01c94e / ctx_93a537696020 | 原集成树现分支 fix/fcd-interface-alignment；基线 14 passed in 40.90s，不是修复验收；没有全量/strict/mutation 回执；Ctrl+C 后读回 PowerShell，工作区 clean |
| T4 / FC-E | **启动失败，无报告** | task_6d4cbad4ae30 / ctx_523fd9024082 | dsh 原生命令报 TRANSPORT: Connection error. 后回 shell；未生成 review-0928-integration.md；未知远端效果/费用，不自动重试；已请求同模型单次重发决策 |
| T5 | 人工材料已落盘，**晚于 10:30** | 本次治理提交，docs/FC_HUMAN_REVIEW_0928.md | 10:37 完成四态矩阵、fencing 摘录、六点清单；FC-E 意见槽明确空缺，不代签 |
| T6 | 冻结未执行 | 无 | 今日门禁、FC-E 无高危结论、breaker 人工签字均未齐；无 merge/tag/三连冒烟 |
| T7 | 未发射 | 无 | 纯分析任务尚未执行，不预判 category 消费结论 |
| T8 | 未完成草案 | 无 | 仅只读查看既有 FaultObservation 与 Rehearsal 模型；无 Schema 冻结 |
| T9 | 未执行 | 无 | 依赖 H3，未生成 mock、未向队友发送消息 |
| T10 | 未实施 | 无 | B 类演练实现需队长确认；T3 写权未交接，未碰 live 子进程 |
| T11 | 未完成 | 无 | 历史私有 DashScope Key 路径存在于既有 launcher；本日 E 连接失败不能当认证可用；云 profile/课题 workspace/彩排配置未核实 |

### 按队长格式上报：接口事实不一致

- 现象：T2 新产物将 `record_failure` 当作已有实现，并错误描述 retry 修复。
- 证据：`morph-fc-docs-0928/artifacts/ai-evidence/fcr-hallucination-case-0928.md`
  的 `cd8f6c9` 第 11–14 行引用实际 `_record_failure_fact` 来支持 `record_failure`；
  实际定义 `swarm/worker_loop.py:678`、调用 `:813`。`git show bbe9d77 -- swarm/worker_loop.py`
  明确把未定义变量 `retry` 改成 `retry_after`，参数名仍为 `retry_after_seconds`；
  案例却写成字段改为 `retry_after_seconds`。其“不同 provider 分类逻辑”也不是异构开发模型
  错误模式不相关的证据。该页不能验收，未合并或代写修正。
- 建议：保留原提交，由同一 qwen Owner 按精确 diff 返修并复验；生产代码仍只读。
- 需要队长决策：是否解除本次停止、恢复 T2 返修及 T3；另独立确认 H4 与 FC-E 单次重发。

### 终端与生命周期

三次本日启动使用既有原生 launcher。Orca 不识别其原生 agent，采用有权威 preamble 的
low-level dispatch，均如实记 unsupervised，不冒称进程受 Orca 管理。
E 已回 shell；T2 已结束，其结尾只有文本 `orcasend worker_done`，没有真正发送生命周期
消息；T3 经明确中断后回 shell。主控依据上述正向退出证据 abandon 三个本日 Dispatch，
保留终端、工作树、提交和原始记录；不伪造 worker_done。

原 Run 遗留四条邮件已复核：A/D 旧自报不是今日验收；C 旧 push 失败记录与原总控后来
“六分支推送”终端记录并存；R 旧 heartbeat 不是完成证据。今日 `git ls-remote` 再核实时
遇 `OpenSSL SSL_connect: SSL_ERROR_SYSCALL`，不宣称已实时核实所有旧分支远端。

后续网络恢复：治理提交 `140797c64d9b0fe7656e1d00bd68aa7936c88370` 正常 push 成功，
`git ls-remote` 确认主分支与 T2 分支分别为 `140797c` / `cd8f6c9`。T2 仍拒收，远端存在
不等于验收通过。历史 A/D release 返回 no_owned_resource，未动外部终端；四条遗留邮件
已处理并 ack；本 Run reclaimable 数为 0。

H1 11:00–11:30 人工 breaker 复核材料已备；H2 12:15 提醒/12:30 报名、H3 16:00–17:30
拍板、药学 PhD 20:00 截止、课题提案收集、21:30 站会仍由队长执行。本会话未创建定时
提醒，不承诺离线后自动到点提醒。总目标 P1/P2 **未达成**。

## 充值后接续

进程内清除代理环境后 A/D/R 的 DashScope 实际模型与代码工具活动已恢复。
C 的 qoder dispatcher/resume 回合只返回旧测试仍运行的过期结论，未修复；
终端明确 CLI 已结束，stop_unknown 因外部终端而无法关闭；依据实际退出证据
abandon 旧 ctx_0df29cd2f91c、保留所有 WIP，同轨新 ctx_84ceea058c74。
原生 qodercli 通过 stdin 新上下文已实际读文件，返回模型标签 Auto，不冒称
Qwen3.8-Max。C 写权及 Owner 不变。R Codex 网络路由发现 turn.failed 且
没有领域代码，随后 R 首次领域实现改用原生 Qwen Code，ctx_27a0b1455ff1。

A 新提交 fc5b3934fed630c055a76fa6e3df83dc1b09f969 自报推送及25项定向/
类型通过，业务验收仍拒绝：独立合法 HTTP-date 返回 None，+3/1_0 被接受；
spawn 测试仅检查字段存在，未证明值或无秘密；parent ExecutionResult.metadata
丢失新 Reply 事实，且没有全量门禁。原 Owner 新 task_cba58721948f 接续返修。
R 自己工作树越界加了 evomap_executor.py 三行 Reply 字段，已明确退回撤销
仅自身改动；事实传播归 A parent parsing，不以合并解决领域所有权冲突。

2026-09-27 用户明确充值并要求完成总任务、更新桌面报告。原生 A/D 已基于新
Dispatch 接续原会话：ctx_63b12a67edf1 / ctx_07682b2d2cec；只在有实际模型/
工具回执后记开工。C 的 ENOSPC 后未返回请求经 Escape 取消，终端明确
Request cancelled，随后同 Owner/Dispatch 接续；先修 token fencing 与失败门禁。
新增隔离 FC-R 运行时领域轨，写权与接续条件见 docs/FC_PLAN.md；以完成用户总
目标为授权，不扩大原五轨写权。E 最终精确提交评审、I 独立集成仍在后续波次。

## 依赖申请区（五轨对 pyproject.toml/poetry.lock 只读，缺依赖在此登记，由队长批量执行）

| 依赖 | 所属轨 | 用途 | dev 组 |
|---|---|---|---|
| （空，待轨登记） | | | |

## FC-A 第 0 步探测记录（人类队长拍板 + AI 代跑核实，已固化）

结论：httpx 路线成立；live 请求走子进程；respx 仅能注入进程内路径；分类在子进程内完成。

证据锚点：

- `orchestration/gateway_transport.py:14` `import httpx`
- `orchestration/gateway_transport.py:43` `httpx.Client(transport=..., trust_env=False, follow_redirects=False, timeout=...)`
- `orchestration/gateway_transport.py:22-30` `GatewayResponse` 字段（无 Retry-After、无 raw body 字段）
- `swarm/evomap_executor.py:92-132` `_request()`（调用 `single_request`，进程内/mock 路径）
- `swarm/evomap_executor.py:135-149` `_child()`（`--request-child` 子进程入口，读 cred 文件后调 `_request`）
- `swarm/evomap_executor.py:209-224` `_send()`（live 走 `subprocess.run`；mock 走进程内 `_request`）

裁定：raw body 不出子进程；回传 `classification` + `evidence_hash`；FC-A 写权窄增补
`swarm/evomap_executor.py` 两处（见 QWEN.md [FC-A 写权扩展]）。

## FC-A 首次交付复核与返修（2026-09-27）

- 收到 worker_done：原 task_021476b9728f / ctx_908e3cf0b7a5，远端分支
  fc/failure-classify@e4396407e87e8745f8bfeff448343ecf6b6edd5f 已核实。生命周期
  completed/succeeded 仅是 Worker 自报结算，主控业务验收未通过；不集成。
- 该提交额外引入 uv.lock（3 行，基线不存在），违反锁文件/写权边界。由原
  Worker 在普通后续提交中撤销自己新增文件，不改其他锁文件、不重写历史。
- 最初工作树 Python 执行 tools/typecheck.py 失败：No module named mypy；
  随后原 Worker 真实终端回执已执行 Poetry install，84 源文件类型检查、
  tests/orchestration/ 的 19 项定向测试通过；尚无合格全量 pytest 回执。
- 独立只读复现：分类器接受 JSON null 抛 TypeError，message=null 抛
  AttributeError；_request 的非 UTF-8 响应抛 UnicodeDecodeError；HTTP 400
  Arrearage 的流在部分 body 后 ReadTimeout，Reply 却为 confirmed_rejection
  （uncertain=true）。均是进程内 MockTransport，无远端调用。
- 未实现 Retry-After HTTP-date/整数/未知解析；当前所谓 integration 测试仅
  进程内 _request 调用，无实际 spawn --request-child 回传证明。
- 返修仍归同一个 FC-A 原终端、worktree、branch。新 task_5853a2c3a4b9 /
  ctx_3993f67114a8；旧 Dispatch 已撤权，不复用旧身份。新 preamble 通过
  native Qwen Ctrl+Q 入队并读回“1 queued”；等待真正执行和修复回执。
- FC-C 仍由原 Qoder Worker 开发；FC-D/E 暂等 A 接口返修，最终集成未执行。
- 紧接原任务第二条 worker_done：19fe837b5aafdecfcc963ed90dc518071c9b6511
  仅删除 uv.lock（已推送终端回执），没有修复领域代码。本次独立执行工作树
  `.venv/Scripts/python.exe tools/typecheck.py`：84 源文件通过；
  `.venv/Scripts/python.exe -m pytest -q tests/orchestration`：19 passed in
  7.28s。上述已知缺陷与缺失需求仍阻止验收；第二条消息已读取并确认。
- 新返修 preamble 已从队列进入 native 模型新回合，屏幕读回完整新任务及
  processing 状态；不是仅记录终端输入接受。

## 最新并行开发与已知引擎阻塞

- 用户要求继续五轨并行开发及桌面报告。A 原会话达到 100 轮后保留 WIP、
  退出并原会话 resume，进程上限改 400；接续 ctx_b8e62d8a7999。D 首次
  Windows shell 配置错误后绕过 Poetry 执行全局 pip（原生记录可见安装了
  hypothesis/respx/time-machine 等）；立即停止，未盲目卸载共享包。随后
  launcher 设置 POETRY_VIRTUALENVS_IN_PROJECT=true，同一 D 会话 resume 到
  ctx_1bbdc67b67ba，实际执行 uv tool run poetry install；不以全局包为验收。
- A/D 分别真实返回 DashScope HTTP 400 账户状态异常/欠费拒绝。没有再次
  调用、创建替代 Key、充值或自动模型切换；两个 Dispatch 已 fenced/stopped，
  原工作树 WIP 保留，Task blocked。引擎替代选择已向用户提出，尚待答复。
- A 当前 WIP 的 subprocess 测试曾加 except Exception: pass，能吞掉断言；
  主控已中断该回合并退回修复。explicit mock child seam 已开始编写，但尚未
  最终验收。D 当前草稿存在 assert True/占位和错误账本调用，尚未测试、提交或
  接受，不能混为真实五不变量验证。
- E dsh/DashScope deepseek-r1 实际有模型与工具事件、provider usage，但首轮
  结束后没有报告文件或 Commit；末尾声称写入 $MARTIFACT_FILE$ 未由文件系统
  验证，且不按五不变量原文评审，未验收。ctx_588d14022e7e 已停止，不重发
  同一欠费账户调用。原 native session 与响应证据保留在忽略的运行目录。
- C Qoder 仍开发/验证；主控独立 strict 82 文件通过，尚等最终完整回执。
  欠费原因 A billing_arrearage / C arrearage 不一致已退回 C 对齐。
- 独立集成 worktree morph-fc-integration-0927 已按本轮计划创建，分支
  songconmaisaix31-design/morph-fc-integration-0927，基于治理提交 37b5b6b。
  没有集成 Worker 开工或领域合并，等最终领域交付。
- D 当前草稿独立 collect-only 失败：time_machine.travel 的字符串
  `2023-01-01 12:00:00 UTC` 不是合法 ISO 格式，no tests collected / 1 error。
  A 当前 WIP git diff --check 报 trailing whitespace；均未动原 Worker 文件。
- C 已收到主控反馈，真实终端确认 npm ci（工作树根目录）exit0，并正在补
  billing_arrearage 单样本真实 B 接口测试；旧未安装 Node 环境的全量结果作废，
  最终全量结果与原退出码另行留存。主控没有执行部署或模型任务彩排。
- A 欠费停下时的 WIP 独立 strict 检查：84 文件中 3 个错误（base.py 使用
  math 未导入，两处；mock_handler 缺类型注解）。未修复或宣称原定 19 项测试
  能代表当前 WIP。D 仅有三个 HTTP 故障夹具与 __init__.py，六夹具尚不齐。
- C 最新真实 B 联合回执 27 passed in 8.52s，包含 billing_arrearage 单样本
  立即熔断；当前正式全量仍运行。现有 Codex 的 login status 确认 ChatGPT
  登录，但仅做可用性核对，未在用户选择前替换 A/D 引擎。
- C 正式全量结束：569 passed、2 failed、1 skipped，781.42s；失败为
  demo_environment 的 sentinel/执行器参数与 t1 bridge MCP。tail 管道退出码
  不代表 pytest 退出码；已要求原 Worker 定向重跑留真实输出和退出码，不豁免。
- C WIP 独立复现同 Worker 探测隔离缺陷：A 于 t=1000 领取 token1，t=1060
  过期后同一 A 领取 token2；旧 report_probe_success(A) 被接受、state=normal。
  回传 API 未接收认领 token，不能隔离同一 Worker 的迟到结果；已退原 C Owner。
- 宿主 C 盘曾 free=0，Qoder 实际 ENOSPC，主控 apply_patch 失败将 TASKS.md
  截断。仅清理本次 py-spy 的 uv 缓存 4.9MiB，未删除其他文件；磁盘空间另有
  较大波动，原因尚未确认。TASKS.md 已从未改动的精确 HEAD 恢复，git diff
  证明恢复无差异，再追加本段。两条新领域文件长度正常，不能据此证明未受影响。

## 2026-09-29 五项生产修复最终收口附录（G；不冻结）

本附录为本轮最新状态，保留以上全部历史。**用户本轮已经授权五项生产修复**，旧 cost_state“待授权/未授权”限制已被覆盖；H1/H3 真人签字、正式 FC-E 门禁、入口/演练仍分别 OPEN。五项本地验收完成不等于全系统稳定或冻结。

唯一共同代码候选：`morph-fc-candidate-0929@c552250c0d07f5f70f09eb0a5ab3c322195e34ec`；A 最终 `4d1098ed151d6a9859e088f13ea292baeef1acf2`、B 最终 `2c6a33ae1950fd6458543618d1c4044dcdd2596f`、C 最终 `e6ac45ffefc171a7215f8db19bc4a28af24ec4fc` 经普通 no-ff 合并，B 中间合并 `5cf2612c04a34dfb17af12af817ebee8c08432dc`。三轨路径互斥，无集成胶水；远端 exact/clean。G 治理分支从 C 单轨建立，其最终文档 SHA 与 D 报告 SHA 都不是受测代码 SHA。

| 五项修复 | Owner 自验（各自源码/组合，不冒充共同候选） | C552 独立验收 |
|---|---|---|
| unknown_effect 已知费用仍跨重启/换 Worker/真实 handoff 隔离 | A：119 focused / 2 warnings，3 文件 scoped strict；四组 mutation 红/恢复绿 | D：真实进程/持久账本/租约，executor 不再发送；确认拒绝/成功与失租为对照 |
| TTL 过期 probe 取得新 token 并经真实路由执行 | B+C guard：96 组合，无 skip；TTL mutation 红/恢复绿 | D：TTL 前/精确到期、同 owner 旧 token、双 Worker 只有一个 executor |
| 成功恢复后旧故障不重熔断，新同时间戳故障仍有效 | B：恢复水位和追加序号；历史过滤 mutation 红/恢复绿 | D：同 Worker/旧缓存/新进程、在途旧聚合与 equal-time 新故障均验证 |
| 5xx/transport unknown 优先于欠费/配额正文 | C：246 focused、strict 87、SDK 1.14.0；两 adapter 与 guard mutation 红/恢复绿 | D：双真实 adapter；EvoMap HTTP→executor→Worker 的 5xx [1,0]/4xx [1,1]、中断 [1,0] |
| FaultObservation.cost_state 来自本次 reservation | A：无价格两策略保留 full hold；历史 unknown 不污染本次 settled | D：本笔持久状态/字段语义与 executor 行为；usage-only/global 推断 mutation 均红 |

**I 同一 C552 六门禁实际重跑：** focused **408/2 warnings/278.45s**、full **862/2 warnings/589.58s**、strict **87**、新 sdist+wheel、官方 SDK **1.14.0**、离线自建 wheel 分发 **13 packages + check-node**，所有 native exit 0。G 核六原日志并比对测后 346 源码与 archive 原字节相等；不是复用历史 699/698。两 warnings 为原非法 model_copy 夹具。

**D 独立：** `morph-fc-independent-final-0929@9a6705c7aeae9c812329c015f13e440842beff17`，focused **47/73.71s/exit 0**，九组有效行为 mutation 均 red 1→restored 0；464 原测试函数/1558 assert/全部 decorators 保留。D 读取 I 六原日志而非重跑 full；另核 wheel/安装目标 83 Python 文件与 C552 一致。来源：[D 原字节报告](artifacts/ai-evidence/fc-remediation-governance-0929-independent-report.md)、[I 原字节报告](artifacts/ai-evidence/fc-remediation-governance-0929-integration-report.md)、[G 原日志索引](artifacts/ai-evidence/fc-remediation-governance-0929-report.md)。

**原失败保留：** B full 47 failed/656 passed/7 errors/2 warnings/exit 1；B/C 缺 Poetry 后端 build exit 1；A 首修 1 failed/117 passed；D 首次 equal-time 恢复红与 Git `$GIT_DIR too big` exit 128、短目录修正复验；旧 protected_runtime_state 18 failed/2 passed、Schema 8/9 与 11/12、T3 两次假绿仍为真实历史，不追认通过。

**正式 FC-E：已取得，未通过。** 原隔离 profile 已定位，主控六绿通知后通过同配置/凭据的现成 SDK 发出唯一 deepseek-r1 请求：returned model 同名，finish=stop，fetch=1，prompt71611/completion4642/total76253（reasoning2930），费用 unknown。四 fact 中 **2 引文 PASS / 2 INVALID，机械 exit 1**；四 hypothesis 待验证。h2 high 没有具体失败交错且依赖无效引用，不是确认代码缺陷；h4 与用户 5xx 保守 unknown 要求冲突；五不变量逐项覆盖不全，报告 **REJECTED**。不改原引用换绿、不代评、不第二次调用：[正式接收记录](artifacts/ai-evidence/review-0929-formal-v2-report.md)。

### C552代码核对结论（AI备料，不是H1签字）

以下技术结论以 `git show c552250c0d07f5f70f09eb0a5ab3c322195e34ec:<path>` 核对，全部行号属于该共同代码候选；上文历史预算 A/B 的 73e64 行号保留，不用于本轮引用。[人工复核包](docs/FC_HUMAN_REVIEW_0929.md) 与既有 21 组逐字引文配套，引用相等只证明文字存在，用户仍需对五不变量交叉核对。

**场景A：不死锁**（仅指确认拒绝后的同任务 pending 冲突；前提为新 `request_id`，且其他额度、attempt、burn、运行时限与路由/租约策略允许）。`swarm/budget.py:248–249` 将确认拒绝的费用未知预留从 pending 改为 uncertain；`swarm/budget.py:179–181` 只拦相同 request_id 或同 task 的 pending，旧 uncertain 不再造成该互斥。`swarm/worker_loop.py:757–758` 以 task/lease token/candidate index 生成每次请求 ID，`:795–798` 走确认拒绝保留 hold 路径；相同 request_id 仍拒绝是防重复。容量检查 `swarm/budget.py:192–195` 要求 admitted+旧 holds+新预留不超过 cap；`:160–173`、`:182–191` 仍分别限制运行时间/attempt/睡眠和 burn，容量不足或策略阻止不等于 pending 自锁。

**场景B：无双计**（仅指当前账本同一 unknown hold；不代表无上游实际超支风险）。`swarm/budget.py:200–203` 初始 admitted_usd 为 NULL，`:248–249` 只改 status/settled_at；`:83` 将非 settled 的 reserved_usd 计入 hold，`:192–195` 使用 SUM(admitted_usd)+holds+新预留。因此同一 uncertain hold 保留一次容量占用，并未同时记入 admitted；多次独立请求的 hold 累加是累计占额。unbounded 的 allowance 是本地准入额（`:136–154`），真实费用可能超过它，估价也不是上游账单（`:296–301`）。

**晚到结算与任务终结：** `swarm/budget.py:268–272` 对非 pending 直接返回（冲突 usage 可先抛错），没有 uncertain→settled 或 unknown_cost_allowed→settled 的晚到入口，不能声称 unknown 已转实际账单。`swarm/worker_loop.py:795–803` 记账后清空 `_active`，`:994–998` 收尾只处理仍 active 的预留；任务终结不会释放旧 unknown hold。`swarm/budget.py:79–83` 每次从持久账本累计非 settled hold，重启也保留；`:91–101`、`:182–191` 还会将这些未知预留纳入 burn。结论是同 swarm 预算周期内长期占额／预算慢性占用（泄漏风险），并非同一 hold 自动双计。

**lower observed usage 不返还承诺额：** 既有普通 pending→settled、usage 可解析且有本地价格的路径在 `swarm/budget.py:295–301` 以 `max(estimate, reservation.reserved_estimate_usd)` 写 admitted_usd，随后 settled 从 hold 集合退出（`:83`），准入仍计 admitted（`:192–195`）。无价格的 usage 留 full hold（`:286–294`）。当前 unknown 转换不存在（`:268–272`），不把这条普通结算规则冒称已覆盖晚到 unknown 对账。

**确认拒绝的 unknown 费用与 unknown_effect 分开：** 前者走 `swarm/budget.py:230–250` 保留费用 hold，可在上述条件下切换；`swarm/worker_loop.py:812–815` 可确认其执行结果。后者即使费用已知也不清除任务未确认请求（同一条件排除 unknown_effect），`:885–887` 停止；`swarm/task_ledger.py:358–382` 持久记录请求，`:257–266` 排除未确认任务，`:384–393` 将其保持 blocked。这是故意的任务持久隔离，不自动重发，不应归为场景 A 的 pending 自锁。

**H1 人工边界：** 上述为 AI 代码核对结论；预算 A/B 人工判断、五不变量交叉复核与签名仍由用户完成，所有人工结论槽和签字槽保持空白。四态矩阵、fencing、三处 TODO 新行号 202/592/672、六点及模型待验证风险仍见人工复核包；不改变 FC-E REJECTED 或 T6 禁止执行的状态。

**H3 与 NOT_RUN：** Schema 与原已验收318dd的 blob相同，仍 optional+nullable **1.0.0 candidate / 未采集 / unsigned**，不补0、不冻结。T6 merge/tag/三连冒烟（缺可接受FC-E+H1签字）、T9依赖H3的采集接线、T10演练、T11课题入口条件、长期/业务live/生产发布均 NOT_RUN。DashScope 完整生产 executor NOT_IMPLEMENTED，只有 adapter 层实测；晚到对账/自动解锁/未知hold释放/混合版本部署未实现或未验。第一代应用 `morph-readonly-app-0929@621f588988899bdbc7c7a83e893369c4145d89b3` 仍独立，不称全项目主线统一。FC 整体 **BLOCKED、未冻结**。

## 2026-09-29 dsh / V4.1 Flash 正式 FC-E 替换附录（G；最新）

用户明确“不用 deepseek-r1，用 dsh 加 deepseekV4.1flash”，本轮新授权覆盖旧 R1 额度限制；旧响应/引用/REJECTED 原封不动。唯一受评代码仍 `c552250c0d07f5f70f09eb0a5ab3c322195e34ec`，源树只读。两轨职责见 [发布前置一页计划](docs/FC_RELEASE_PLAN_0929.md)：G 正式评审/人审材料，E 独立只读 release-preflight，互斥文件，主控调度验收。

实际预检：dsh 0.1.5-rc.3 官方安装目录将 `DeepSeek-V41-Flash` 解析为 `deepseek-official / deepseek-flash`；原 FC launcher/patch/composed 是 `dashscope-fc / deepseek-r1`。按原生实现核对 Process/User/Machine 环境及两个许可 home 的标准认证文件、当前 cwd/.env，未取得指定路由凭据；没有猜 URL、重用 DashScope key 到新 endpoint、改全局或换 SDK。**认证 BLOCKED / 本轮 review NOT_RUN / FC-E OPEN**，请求0、returned_model/usage/cost/review_exit 均 null。

主控 `msg_a077597131fd` 明确允许一轮原生 dsh invocation、retry=0、有限输出、禁非必要工具/title/compaction、最多10分钟；没有原生 max-step/request 参数仅属 CLI 限制，不新增 exactly-one-HTTP 门禁或重复审批。超时效果 unknown 不重试，请求数未能观测时写 unknown。输入实际532215 bytes，精确 tokens null，尚未提交，原生大输入绑定/返回模型证据需运行前核实。

[新模型交接报告](artifacts/ai-evidence/review-0929-v41flash-report.md) 保留完整两段核心 diff、22组旧编号块、12份完整C552上下文与37项覆盖要求（含16格四态矩阵）。输入机械exit0；无新模型输出的校验exit2/NOT_RUN；旧R1样本对照exit1仍2PASS/2INVALID，不改旧引用换绿。旧h2高危假设仍未证实，5xx unknown优先仍为用户约束；五项真实路径/五不变量/假绿清单本轮模型覆盖全部NOT_RUN。

H1预算A/B与breaker六点/五不变量签字、H3 Schema optional+nullable 1.0.0 candidate的采集/准入/冻结仍待用户，签字槽不变。本轮未重跑I六门禁或D测试；生产代码/测试/Schema/TODO/AGENTS/SWARM/锁未变。T6 merge/tag/三连冒烟、T9/T10/T11入口演练、业务interface_live/task_live仍NOT_RUN，FC BLOCKED未冻结。本次材料commit+push不表示正式审查或发布锁完成。
