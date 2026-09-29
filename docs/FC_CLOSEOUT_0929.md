# FC 2026-09-29 人类审批 / 下一步包

**主控 11:13 已确认本轮结果齐备并通知封存；FC 整体仍 BLOCKED、未冻结。** 本包仅索引证据和待决项，不替代 H1/H3 签字或正式 FC-E。FC 生产基线固定为 `73e64cc70116ac658d85591d082c0684a4952c99`；“B 治理树未合入 FC”是 B 交付阶段事实。I 已将 A/B 合入隔离候选 `4c3dc46e7c0459680a7567ff6d91ba44301c3819`，生产主线未合，C 仍是独立第一代候选。

## 1. 已有交付与证据级别

| 项目 / 精确候选 | Owner 自验 | 独立验收 / 当前边界 |
|---|---|---|
| A 测试 `f4779d45a1b1417ffa6bce37708e9a68d46cf4e5`；最终 `3d8bb856efadbb1bee4a69bc37c56d3ef4d24cfd` | focused 20、full 699（2 warnings）、strict 87，exit 0；breaker mutation 行为红/恢复绿、生产 diff 空 | D 独立 focused 20、mutation call_count 红/恢复绿通过；cost_state 独立仍 exit 1，OPEN |
| B Schema 修复 `188fae46de4f3d2fe4943461a62a9626caa5325d`；交付 `318dd4f26f27cda25e4278772bcce6b508023c26` | 原矩阵 12/12、扩展 24/24、控制 13/13，exit 0 | D 独立修前 43/44、修后 44/44，nullable-only；仍 `1.0.0 candidate`，H3 pending |
| C 只读应用 `621f588988899bdbc7c7a83e893369c4145d89b3` | 主控转发契约、53 T5、build、44 采用语义 / 72 页面浏览器检查 exit 0 | D 独立 T5 53、双 bundle 字节一致、3 历史 run replay HTTP→DOM、缺失/0/多 attempt/可访问性通过 |

证据入口：[A 最终报告](https://github.com/songconmaisaix31-design/Morphogenesis/blob/3d8bb856efadbb1bee4a69bc37c56d3ef4d24cfd/artifacts/ai-evidence/fc-tests-0929-report.md)、[B Owner 报告](../artifacts/ai-evidence/schema-0929-report.md)、[D 独立报告 969d3274622538a36ac8a60e09c41be86bea9c60](https://github.com/songconmaisaix31-design/Morphogenesis/blob/969d3274622538a36ac8a60e09c41be86bea9c60/artifacts/ai-evidence/acceptance-0929-closeout.md)、[今日台账](../TASKS.md)。B 只登记 D 结果，不评审自己；A full/strict 为 D 核对 Owner 原日志，非 D 重跑。C 非法 `adoptions=[null]` 引发原 app.js 错误（exit 1），为越契约既有限制、未修复；没有新 live 证据。历史 Schema 8/9、11/12、exit 1 和 T3 两次 mutation 假绿不被追认。

## 2. H1 审批材料索引

- **预算 A：有条件不自锁。** 新 request_id、同任务旧 reservation 已从 pending 变为 uncertain，且容量、attempt、burn、租约等允许时，可继续处理已确认拒绝；相同 request_id 仍被幂等保护拒绝，unknown effect / unknown cost 的停止规则仍有效。证据：精确 FC `budget.py:178–180,229–235`、`worker_loop.py:757–758,793–799` 及 A 报告预算章节。
- **预算 B：同一 hold 不双计。** 非 settled 的 hold 与 admitted 分开计入准入；unknown 不因离开 pending 被释放。证据：`budget.py:80–82,191–202,233–235`。这不证明上游实际费用不超预留或 unbounded 具有账单硬上限。
- **未实现事后 settle / 长期占用仍在。** `budget.py:253–257` 对非 pending 早退，无 uncertain→settled 晚到对账；旧 hold 跨任务终结/重启继续占额度。普通结清的 `max(estimate,reserved)` 不返还承诺额，不能据此声称未知费用已结算；长期占用/人工停止恢复限制留待队长判断。
- **生产缺陷 OPEN：** 有合法 usage、无价格时，账本 uncertain/unknown、full hold 保留，`worker_loop.py:839` 却把 FaultObservation.cost_state 记为 settled；语义检查 **exit 1**。见 [A 原始 Handoff](https://github.com/songconmaisaix31-design/Morphogenesis/blob/3d8bb856efadbb1bee4a69bc37c56d3ef4d24cfd/artifacts/ai-evidence/fc-tests-0929-cost-state-handoff.md)。未见释放或超支证据，最小生产元数据修复仍待队长授权；B 无生产写权。
- [既有 H1 材料](FC_HUMAN_REVIEW_0928.md)：四态 × 四事件矩阵、半开竞争/fencing、六项核对及签字槽。三处 `TODO-HUMAN-REVIEW`（breaker:192/558/633）原样保留；该历史材料的旧测试状态以本包今日证据级别区分，不改其签名/TODO 或复制全文。

## 3. H3、FC-E 与下一步

**H3：** [Schema 草案](FC_LOG_SCHEMA_DRAFT_0928.md) 仅修 count=null/audit 缺失的误拒绝，optional+nullable 保留，无采集可缺失/null，不补 0。数值需要 audit，0 需要 complete/证据/空 issue IDs；正数与 unique IDs 数量一致、scope、证据追溯仍是消费侧责任，未实现生产消费者。**可选字段新增为 minor；optional→required 为破坏性 major/2.0.0**，不称 1.1 可升级必填。D 独立通过只关闭此次 nullable 行为缺陷，人类 H3 仍 pending。

**FC-E：** 正式 deepseek-r1 v2 报告仍未补，D/Codex 验收不能替代。沿用 [v2 协议](FC_E_REVIEW_PROTOCOL_V2.md)：hypothesis 标待验证；fact 具精确 SHA、file:line、逐字 quote 和机械结果，引用匹配不证明推论成立。历史 qwen 降级稿仍拒收。

只读通道盘点：B 的 `dsh --help`、`dsh --profile headless --help` 均 exit 0；现有 headless 语法是 `dsh --profile headless "任务文本"`。B Dispatch 未继承 `DSH_HOME`，未证明默认 profile 就是既有 DashScope deepseek-r1 隔离配置；正式报告文件 `morph-fc-e/artifacts/ai-evidence/review-0928-integration.md` 未补。因此仅帮助命令可直接复用，**尚无已核实可直接执行的正式评审命令**；需恢复原有已授权的 v2 正式 deepseek 评审范围，核实原隔离 launcher/profile、工具通道与适用调用上限后由 FC-E 执行，不能擅用默认 provider 或猜配置。本次未安装、读出密钥、调用模型或付费 live，不以 CLI 可启动宣称工具通道已修复。

I 实际整合：A `3d8bb856efadbb1bee4a69bc37c56d3ef4d24cfd` + B 最终材料 `092cadaf497482e00518dfd86d958a81c876a7bd` 已标准 no-ff 合并为 `4c3dc46e7c0459680a7567ff6d91ba44301c3819`，D `969d3274622538a36ac8a60e09c41be86bea9c60` 报告按精确 blob 引入。B 后续四治理文档范围、Schema 对 318dd 原字节、生产与 A 两测试及 protected 路径不变均已核实。精确合并源码 focused **20 passed / exit 0 / 43.60s**；Schema 原 **12/12**、扩展 **24/24**、控制 **13/13 / exit 0**。首次 I 根目录下 basetemp 触发既有 protected_runtime_state，**18 failed / 2 passed / exit 1**；按主控确认的精确 LF archive + 平级状态目录布局纠正后复验通过，没有改保护或测试。全量 699 / strict 87 复用 A 测试 SHA f4779d45 原日志，**未在 merge SHA 重跑**；详见 [I 集成报告](../artifacts/ai-evidence/integration-0929-closeout.md)。

下一步：队长决定 cost_state 最小生产元数据修复范围，由原 Owner 实施后独立复验；真人完成 H1/H3，原 FC-E 核实隔离通道并补正式评审。C 与 FC 从 `605cf48` 分叉，Backend.jsx/两 bundle 冲突，**本轮分别保留候选，不强合前端**。本包仅为今日首批三轨收口，不代表 T1–T11 或今日全部开发完成，继承待办未清空；benchmark 的 BENCHMARK_POLL_MS 风险本轮未核验，不替其他工作树断言修复状态。候选门禁不解除发布三锁；**生产 merge/tag、Schema 冻结、人工签字、依赖 H3 的 T9 生产采集/接线、T10 演练均 NOT_RUN**，`contract_local` 不扩写成 `interface_live/task_live`。
