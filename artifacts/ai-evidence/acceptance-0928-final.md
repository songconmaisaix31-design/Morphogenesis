# FC 独立验收 — 0928 任务跨日收口

时间：2026-09-29T00:06:36+08:00（Asia/Shanghai）；验收者 codex；任务 task_7a9030034e77 / ctx_582a19d0a929。验收分支 `songconmaisaix31-design/morph-fc-acceptance-0928-final`，起点 `7b9954cffd81b5dc112cdfdd3f03591406c9e0c4`；本报告最终提交以该分支 `git log -1 --format=%H -- artifacts/ai-evidence/acceptance-0928-final.md` 为准。主控只派发汇总；本轨独立取证、判定，不代 H1 人类签字，不做 FC-E 评审。

**验收结论：Schema BLOCKED（原九例 8/9，扩展十二例 11/12，退出码 1）；A/B 静态复核与十段逐字引用通过；案例来源核对通过。T6 merge/tag/smoke 全部 NOT_RUN。** “明天”固定指 2026-09-29 下一工作时段，跨日不自动放行任何后续动作。

## V1：预算七项与 A/B 结论

全部源码锚定生产 `73e64cc70116ac658d85591d082c0684a4952c99`，不是当前验收或 Owner 工作区源码。以下是 SQL/调用链静态事实及有限推论；未执行 Worker/真实账单/服务端扣费实验，不构成人工复核。

| 项 | 源码事实（swarm/ 下） | 限定结论 |
|---|---|---|
| 1 / A pending | budget.py:229–235 仅 pending→uncertain；178–180 同 task 只阻塞 pending，相同 request_id 始终阻塞 | **A场景：不死锁**，限定“同任务 pending 自锁”，新 request_id 下旧 hold 不再命中该冲突 |
| 2 / A 调用前提 | worker_loop.py:739 遍历候选，757–758 的 request_id 含 lease.token/index；793–800 已确认拒绝且 uncertain 使用 mark_unknown_rejection；809–826 真正未知效果提前停止 | 只有已确认拒绝可受控切换；容量/价格匹配/attempt/burn/租约等仍须满足，不推断所有 unknown 都能继续 |
| 3 / B 双计 | budget.py:43–46 列顺序，199–202 初始 admitted_usd=NULL；233 仅改 status/time；82 holds 累加非 settled，191–193 SUM(admitted_usd)+holds+新 hold | **B场景：无双计**，限定当前账本同一 reservation：unknown 仍扣容量且未同时记 admitted；不证明服务端账单/实际费用安全 |
| 4 / 可用额度 | budget.py:82、191–194 持续扣 unknown hold；90–100、181–190 未知 hold 还计入 burn，跨 burn 窗口也未因时间自动排除 uncertain | 移出 pending 后仍占 allowance；B≥H1+H2 才可能准入，否则容量拒绝，不把预算不足叫 pending 死锁 |
| 5 / 晚到结算 | budget.py:244–257 虽先解析 usage，但非 pending 直接返回（已有 settlement 冲突另抛错）；源码写账和 Worker 调用点无账单消费/uncertain→settled 分支 | **无事后结算路径**；晚到 usage 不更新原 unknown 的 tokens/cost/estimate/admitted；服务端账单存在不能自动变成本地事实 |
| 6 / 任务终结 | worker_loop.py:796 标 unknown，800 清 _active；987–991 finally 只处理仍 active；budget.py:82 仍计旧 hold；Worker:424–425 恢复只找 pending | 原 unknown 不释放、不按晚到 usage 结算，在同一 swarm 的当前生命周期持续悬挂：按队长术语为预算慢性占用/泄漏；不是双计或已发生重复收费 |
| 7 / lower usage | budget.py:281–286 admitted=max(estimate,reserved)，253–257 先挡 uncertain | 普通 pending→settled 不退承诺 allowance；根本不存在 unknown→settled 转换，不能称该不存在路径已遵守或动摇规则；未来补结算须保留单次记账和不退承诺额 |

额外边界：budget.py:130–153 的 unbounded 仅 operator allowance，并非上游硬上限；实际费用可能超过预留，“无双计”不能推出“无超支风险”。usage/cost 保持未知，不猜为 0；`actual_cost_usd` 未知。H1 仍需真人交叉核对、接受限制并签字。

TASKS 十段与生产 Git blob **逐字相等 10/10**（仅统一文本行分隔，不裁掉源码缩进）：budget.py **80–82、178–180、191–194、199–202、229–235、251–257、281–286**；worker_loop.py **757–758、793–800、987–991**。`2e56fa1efaa030da5a52c614172654a4e6ea1188` 的 TASKS 该整段与起点完全相同，保留本轮核对有效性。

## V2：精确 Schema 候选与真实门禁

候选 `decentralized-swarm@2e56fa1efaa030da5a52c614172654a4e6ea1188`，已核对远端同 SHA、Owner 工作区 clean；提交仅修改 TASKS.md、docs/FC_DAY_PLAN_0928.md、docs/FC_LOG_SCHEMA_DRAFT_0928.md。主控确认已收真实 worker_done，不把其自报 12 例通过当独立证据。候选提交缺 `Swarm-Agent` trailer，未 amend/重写公开历史。

从 `git show 2e56fa1efaa030da5a52c614172654a4e6ea1188:docs/FC_LOG_SCHEMA_DRAFT_0928.md` 取原始字节、提取唯一 JSON 代码块；文件 SHA-256 **c44691a7895013d99c7d2c1a94b049c7cd6ddea9a14234f37e92ae468db2d59d**。Python 3.12.13 / jsonschema 4.26.0 / Pydantic 2.13.5，复用指定既有环境，无依赖安装。合法原 fault_observation 外壳先单独 VALID；判定代码只捕获 ValidationError，assert 在 try 外。

| 用例 | 预期 | 实测 | 结果 |
|---|---|---|---|
| 01_both_missing | VALID | VALID | PASS |
| 02_both_null | VALID | VALID | PASS |
| 03_only_count_null | VALID | INVALID | **FAIL** |
| 04_only_audit_null | VALID | VALID | PASS |
| 05_zero_complete | VALID | VALID | PASS |
| 06_zero_partial | INVALID | INVALID | PASS |
| 07_negative_complete | INVALID | INVALID | PASS |
| 08_integer_no_audit | INVALID | INVALID | PASS |
| 09_audit_no_count | INVALID | INVALID | PASS |
| 10_integer_null_audit | INVALID | INVALID | PASS |
| 11_null_count_object_audit | INVALID | INVALID | PASS |
| 12_positive_partial | VALID | VALID | PASS |

失败定位：候选 Schema 文档 **1633–1654**（required 在 **1650–1652**）/ JSON `allOf[1].then.required`，报错 **`'issue_audit' is a required property`**。`type:null` 改 `const:null` 并未去掉 required；object audit 缺 count 已修复，但只给 null count 仍错误拒绝。故文档标题“冻结版”、TASKS/计划的“12 个全部通过 / 阻塞已解决”不能采信；本轮没有冻结通过时点。

最小问题原文（上述候选 docs/FC_LOG_SCHEMA_DRAFT_0928.md:1650–1652）：

```json
        "required": [
          "issue_audit"
        ]
```

通过范围：Draft202012 元 Schema；生产 FaultObservation **14 字段完整 model_json_schema 深比较一致**；除 audit 条件组以外 JSON 结构全部相等（含 $defs、required、provenance/drill/event 条件）；audit 字段仍为 optional、无 default（尤其无 default 0）；验证不修改输入。字段为 observation_id/run_id/task_id/request_id/attempt/provider/model/failure_class/normalized_reason/retry_after_seconds/switched_to/cost_state/occurred_at/evidence_ref。missing/missing、null/null、仅 audit=null 被保留，但仅 count=null 被错误拒绝，所以不能总体声称 missing/null 兼容已通过。

独立控制 9/9：错误 LIVE/SIMULATED、drill/live、缺 replay URI、空 fault payload、空 task_id、未知顶层字段、空证据均 INVALID；合法 mock drill 与合法 replay VALID。跨字段 count 与唯一 issue 数量、语义证据真实性、生产采集接线不由本 Schema 自动证明，NOT_RUN。

红项已实际发主控 escalation `msg_06d985589f15`，原 Owner handoff `msg_81c3aa10b3da`（终端邮箱投递非长期 durable）；不接手实现。同一缺陷已有前轮失败记录，本轮仍红，保持停止/返修需主控处理。

Owner 原生 CLI 已回 PowerShell：`orca terminal show` preview 与有界 `terminal read` 尾行均为 `PS C:\Users\DW\orca\workspaces\Morphogenesis\decentralized-swarm>`，并见原 worker_done 真实回执 `Sent msg_93ee89c6f757`；终端 running 只表明 shell 尚在。主控已接受红项、停止实现修改，后续返修需其新指令。

## V3：已有案例出处核对

`songconmaisaix31-design/morph-fc-docs-0928@ca1a6fad4c44e4cd87b70980153cea8f7c208900` 的案例页已写入。来源核对 **10/10**：`78c0745` 原拒收稿第65行称 assert 在138行，生产73边界文件138行实际为 test_all_candidates_down_boundary 定义，assert 在85行；原稿109行声称 reservation 覆盖充分，73边界文件无 call_count；`2180e02` high 断言及 `78c0745:41` 作者撤回文字存在。仅核对这些来源，不重新判断整个 breaker、测试覆盖或评审有效性。

mutation 两次仍绿是 TASKS 既有台账证据，本轨 **NOT_RUN**；不能扩为全面有效性/相关性统计证明。`docs/FC_E_REVIEW_PROTOCOL_V2.md@7b9954c` 已存在，系 9月29日后续 deepseek-r1 正式评审准备；本轮 FC-E 评审/返修均 **NOT_RUN**。

## V4：交付、阻塞与未执行

| 交付/门禁 | 分支与完整 SHA | 本轮准确状态 |
|---|---|---|
| FC 生产取证基线 | songconmaisaix31-design/morph-fc-integration-0927 / 73e64cc70116ac658d85591d082c0684a4952c99 | 仅本次取证基线；历史 698/87/build/SDK 不冒充本轮重跑 |
| Schema/治理候选 | decentralized-swarm / 2e56fa1efaa030da5a52c614172654a4e6ea1188 | **BLOCKED**；远端已推送，三文件范围 |
| T2 案例 | songconmaisaix31-design/morph-fc-docs-0928 / ca1a6fad4c44e4cd87b70980153cea8f7c208900 | 来源核对通过，远端一致 |
| T3 WIP | fix/fcd-interface-alignment / 2d9d4304cfc0e1a3d4bfaeccb6ec5688aef60366 | 两次 mutation 绿后裁撤，排除冻结候选；保留 fix 分支作 demo-build.1 首次 bump，不表示已打 tag |
| FC-E 拒收稿 | fc/review-only / 78c07459e14b4817c83c608c68978a07b68b5f9f | 拒收；缺可接受的正式报告，远端一致 |
| H4 | codex/morphogenesis-mainline / 2957b408ce922369a595a8acd43a882eb85897d3 | README 单行文档修订完成，主线远端一致 |
| H1 / T6 | 真人签字缺；门禁全绿 + 可接受 FC-E 无高危报告 + H1 人类签字三锁未齐 | T6 合并/tag/三连 smoke **NOT_RUN**；不是三项人类签字 |
| T9 / T10 / benchmark | 无本轮代码交付 | T9 Schema 未过，样例/消息 **NOT_RUN**；T10 9月29日下一工作时段 acceptance 后/彩排前；POLL_MS 1000→120000 风险未改、不入冻结基线 |

本轮 `contract_local=failed` 仅指候选 Schema；`interface_live=not_run`、`task_live=not_run`。未运行全量 pytest/类型/构建、mutation、模型/Hub/生产调用、T6、T9、T10、FC-E；无对外消息、无人工签字。Schema 属原 Owner 领域返修，H1/可接受 FC-E 及后续完整门禁尚待完成。

## 可复现命令、退出码与文件证据

在本 worktree 执行，`PY=C:\Users\DW\orca\workspaces\Morphogenesis\morph-fc-integration-0927\.venv\Scripts\python.exe`（下列为实际 PowerShell 调用的缩写，不创建 PY 环境变量）。独立脚本与日志保留在 ignored `.runtime/acceptance-0928/`，不提交临时副本/运行产物。

Owner 可直接重跑的本轮唯一验收命令（以后只替换最后的精确 SHA；脚本自行从 Git 提取，不读取候选工作区）：

```powershell
& 'C:\Users\DW\orca\workspaces\Morphogenesis\morph-fc-integration-0927\.venv\Scripts\python.exe' 'C:\Users\DW\orca\workspaces\Morphogenesis\morph-fc-acceptance-0928-final\.runtime\acceptance-0928\validate_schema.py' 2e56fa1efaa030da5a52c614172654a4e6ea1188
```

| 实际命令（前缀 `& '上述 python 绝对路径'`） | 退出码 | 结果/证据 |
|---|---|---|
| `.runtime/acceptance-0928/prepare.py` | 0 | 十段引文 10/10，citations.json / source-hashes.json；源码以 git show，依赖快照以 git archive 提取 |
| `.runtime/acceptance-0928/check_case.py` | 0 | 案例来源 10/10；case.log / case-results.json |
| `.runtime/acceptance-0928/validate_schema.py 2e56fa1efaa030da5a52c614172654a4e6ea1188` | **1** | 11/12 + 控制9/9；schema.log / schema-results.json / schema.exit.txt，AssertionError 未被吞掉 |
| `.runtime/acceptance-0928/write_report.py` | 0 | 最终 TASKS 引文段与已核验段字节相等；桌面旧内容后缀逐字节保留 |
| `git diff-tree --no-commit-id --name-only -r 2e56fa1efaa030da5a52c614172654a4e6ea1188` | 0 | 仅上述三文件 |
| `git ls-remote origin refs/heads/decentralized-swarm` 及上述其他4个分支 | 0 | 远端分别匹配表中 SHA |

生产原始文件 SHA-256：budget.py=`2549690513f6fae1e16a2ac52f316646625d0012f9b57972b1382e44966bb9f3`；worker_loop.py=`7f2f4d245adcf0e560fd40da4fddf50a8997897eaa974449c4bf4091828c7cd3`；fault_observations.py=`672df5968c11ead0a5bf43778d3d327e8c980f18b8d36834a8b5d83f2ae5dfeb`。使用 Python hashlib，未新增哈希/证明基础设施。

桌面更新：`C:\Users\DW\Desktop\Morphogenesis_项目改动整合_2026-09-28.md`，前置本轮真实时间和状态，旧 35158 字节原文完整保留；旧内容 SHA-256=`a63ca5e302f69d6696aa73360b53d8b13d3acc7826eeffa8094d9115463d1154`，原始备份 `.runtime/acceptance-0928/desktop-original.bin`。未覆盖历史、生产代码、AGENTS/SWARM/锁文件或人类签名。本轮一度误建其他路径的空 unused.tmp，已立即删除本轨刚建的零字节文件，未触及既有内容；最终变更范围仍仅授权报告与桌面文件。
