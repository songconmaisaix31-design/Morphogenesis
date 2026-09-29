# A 轨 FC 执行链测试收口报告 · 2026-09-29

状态：A 轨测试改造及本地门禁完成：focused 20 passed，完整 pytest 699 passed，strict 87 文件通过，真实 breaker mutation 首轮红、原字节恢复后绿。**另有未解决的生产 cost_state 元数据缺陷，语义检查 exit 1**；绿色测试门禁没有覆盖或消除这个红项，本报告不代表 H1 签字、FC-E 完成或冻结。

## 基线、所有权与环境

- 工作树 `C:/Users/DW/orca/workspaces/Morphogenesis/morph-fc-tests-0929`；分支 `morph-fc-tests-0929`。起始 HEAD 精确为 F=`73e64cc70116ac658d85591d082c0684a4952c99`，起始 tracked/untracked 状态为空。
- 测试阶段提交并 push：`f4779d45a1b1417ffa6bce37708e9a68d46cf4e5`，trailer `Swarm-Agent: codex`；`git ls-remote origin refs/heads/morph-fc-tests-0929` 核对一致。完整 pytest 与恢复后 strict 绑定这个测试提交；后续只补本报告/证据，不改执行内容。
- 持久修改仅 `tests/swarm/test_failure_chain_boundaries.py`、`tests/swarm/test_failure_chain_runtime.py`、`artifacts/ai-evidence/fc-tests-0929-*`。其他 tests、生产、TASKS、锁、AGENTS、SWARM 文档无持久修改。临时 mutation 只触及本树 `swarm/breaker.py` 的一行，并在 finally 原字节恢复。
- 已读 AGENTS/QWEN、FC_ACCEPTANCE、PLAN、现行 source README/统一对齐和相关 v2 运行规格，以及指定的 0929 算法基线/发布审查报告。历史 T3 `2d9d430` 不作测试实现来源，不作为生产永久阻塞；保留独立 F 基线。
- 本树没有 `.venv`。使用既有 `P=C:/Users/DW/orca/workspaces/Morphogenesis/morph-fc-integration-0927/.venv/Scripts/python.exe`（Python 3.12.13）；import 实测 `swarm.worker_loop.__file__` 指向 A 树。两树 pyproject.toml/poetry.lock 的 SHA256 分别相同（`88aa7b3bb4f13d9c507b42da24f1e796bd8f0533503effcd1531e54906fb2265` / `e7fb011e4efa2070f4ff6bf204a13c2a91f6f8b3495e606421a01d156e038818`）。没有安装依赖、修改依赖目录或锁。
- 首次 `node tools/check_sdk.cjs` **exit 1**，缺少 `ajv`。主控消息 `msg_2df213364fb8` 明确授权本树 ignored `node_modules` junction 只读复用 integration 的同名目录。创建前核对两个 package.json SHA256 均 `7b31b67eff190a3569ab65af160441eb8d8deb02cdaf2b9522f6f0fa40d9aad8`，package-lock.json 均 `af4f22e1fe20fa036cd5f00795edc315882ffa44b5d96baa473de89f61e5119e`，SDK 1.14.0，`git check-ignore -v node_modules/` 明确命中 `.gitignore:2`，目标目录存在、本树路径不存在。复用后同一 SDK 命令 exit 0，schema/hash/tamper 检查通过，published=false。

## 测试行为与原场景映射

全部新关键用例进入真实 `Worker._process`，使用真实 TaskLedger/BudgetLedger/FaultObservationStore/SharedBreaker/租约和本地文件。mock 仅在既有 FixtureExecutor 边界：成功候选仍由现成 FixtureExecutor 生成并做真实本地校验/提交。没有 patch live 子进程、guard、breaker、ledger 或 Worker 来换绿，没有 respx 冒充跨进程拦截。表中 `boundaries.py` / `runtime.py` 分别简指 `tests/swarm/test_failure_chain_boundaries.py` / `tests/swarm/test_failure_chain_runtime.py`，行号绑定测试阶段 SHA。

断言全部在 `_process` 返回后或独立 helper 中运行；executor side_effect 只产生结果/记录入场快照/施加真实 lease handoff，不放断言。明确检查 `execute.call_count/call_args`、发送前已提交的 pending reservation、同 task 的 request_id 序列、观察的 switched_to、SQLite 终态和最终字节/提交结果。未知 usage 保留 None，合法本地 fixture usage 明确为 1+1=2；二者均不冒充远端计费。

| 原场景 | 现在的对应证据 |
|---|---|
| 自建 400 Arrearage / 403 FreeTier / 429 response 后检查自身字段 | Worker 受控拒绝切换 `runtime.py:157`；具体传输分类保留既有未修改 `tests/orchestration/test_provider_adapters.py:150,162,174` 真实 interpret 断言与 `test_integration.py:18,49` 实际 `_request`，纳入全量，避免在 owned 文件重复浅层响应断言 |
| 自建 ReadTimeout response | `boundaries.py:16` unknown_effect（usage 未知/已知两种），首候选只发一次、后候选 0 次；未知 usage 重启仍不续发；传输 ReadTimeout 分类由原 `test_integration.py:87` 保留 |
| 预算不足、换 provider 不重置、计数覆盖请求、未知预留不释放 | `boundaries.py:81` 六组：容量/每任务次数/全局次数 × known/unknown usage，真实发出 2 次，第 3 次被拒，预留与 admitted 合计固定 0.4；实际跨 provider 的 unknown case 仍使用同 task/request budget |
| unknown_effect 的属性测试只 mark_uncertain/读 ledger | `boundaries.py:16` 从 Worker 产生 unknown，查 durable hold/token/cost 及重启；`boundaries.py:49` 有 tokens 无价格单列 unknown_cost 停止续发 |
| all_candidates_down 只 reserve 到上限 | `boundaries.py:130` 候选数 1/2/4 全拒绝后单次遍历退出；`runtime.py:231` 实际 Worker 先产故障事实，下一任务全候选被真实 breaker 阻断，执行/预留均零新增 |
| 失租仅 sleep 后 is_valid | `boundaries.py:153` 成功候选已产生后实际 lease handoff，Worker 拒交；最终文件原字节、无 result/effect/promotions、audit=stale_lease |
| in-process transport 实际 single_request / 子进程仅自建 Reply 占位 | 原有效 `_request` integration 检查保留；原 `test_integration.py:104,168` 已有真实 mock 子进程分类/evidence 返回。本轨不再把 Reply 构造当作子进程证明，不修改这些非 owned 测试 |
| decide / candidate_identity / fact validation / healthy guard | decide 分支保留；identity 合并到 fact validation 并只捕获 ValidationError；healthy routing 在真实受控切换成功提交中覆盖 |
| suspended guard 仅直接调用 | `runtime.py:198` 首个 Worker 真正产生拒绝 observation，下一 Worker observe→transition→guard→跳过 alpha、调用 beta；这是 mutation 敏感性目标 |

旧两文件合计 19 项（14+5），新为 20 项（15+5，含参数化），删除重复/占位断言并扩为真实链行为，因此本树全量从历史 F 的 698 项变为 699 项。Hypothesis 的随机 ledger 循环改为明确边界参数化；不宣称保持随机探索范围或穷尽所有并发组合。未修改非 owned 存量测试。

## 命令与退出码

以下命令 cwd 均为 A 树；Python 命令前设 `OPENBLAS_NUM_THREADS=1`、`OMP_NUM_THREADS=1`、`MKL_NUM_THREADS=1`。`P` 是上文现成解释器的完整绝对路径，PowerShell 调用方式 `& '.../python.exe'`。

| 门禁 | 实际命令/证据 | exit 与结果 |
|---|---|---|
| SDK 初检 | `node tools/check_sdk.cjs` | **1**，Cannot find module ajv；环境阻塞，非产品/mutation 失败 |
| SDK 复验 | 相同命令，复用已授权依赖后 | **0**，1.14.0，schema_valid/asset_id_verified/tampering_rejected=true，published=false |
| Focused 第 1 轮 | `P -m pytest -q tests/swarm/test_failure_chain_boundaries.py tests/swarm/test_failure_chain_runtime.py`；`.runtime/fc-tests-0929/focused-1.log` | **1**，18 failed / 2 passed，11.62s。新夹具使用 seed_demo 默认已持久化 RunLimits 后更改 limits，被正确拒绝；没有把该初始化错误计为业务失败 |
| Focused 第 2 轮 | 同命令；`fc-tests-0929-focused.log` | **0**，20 passed，34.04s。改为在新 state 创建目标 limits 的独立运行并复用 seed_demo 的任务/验收数据；不改既有运行 limits |
| Mutation 目标 | `P -m pytest -q tests/swarm/test_failure_chain_runtime.py::test_worker_observation_suspends_provider_and_routes_later_candidate` | **1**，1 failed，16.45s；execute.call_count 实际 1、应为 0。见 mutation.log |
| 原字节恢复后的目标 | 同上 | **0**，1 passed，10.17s；见 restored.log |
| Mutation 恢复核对 | `git diff --exit-code -- swarm orchestration` + SHA256/字节比较 | **0**，空 diff；before/after 哈希相同 |
| strict 初次与恢复后复验 | `P tools/typecheck.py`；`.runtime/fc-tests-0929/typecheck.log` / `typecheck-restored.log`，恢复后日志另存 `fc-tests-0929-typecheck.log` | **0 / 0**，87 source files 无错。以恢复后复验为准 |
| 本树完整 pytest | `P -m pytest -q`；`fc-tests-0929-pytest-full.log` | **0**，699 passed / 2 warnings，450.96s（7m30s），绑定 f4779d45a1b1417ffa6bce37708e9a68d46cf4e5。两 warning 来自既有 test_budget.py 非法 model_copy 输入预检，不新增忽略规则 |
| 生产元数据语义取证 | `P .runtime/fc-tests-0929/cost_state_repro.py`；`fc-tests-0929-cost-state-repro.json` | **1**，semantic_check_passed=false；真实预算 unknown、观察记录 settled。脚本首次因报告父目录缺失的 FileNotFoundError/exit1 单独保留，不计作语义复现 |
| 文本检查 | `git diff --check` | **0** |
| 阶段提交/推送 | `git commit ...`、`git push -u origin morph-fc-tests-0929`、`git ls-remote origin refs/heads/morph-fc-tests-0929` | **0 / 0 / 0**，远端测试 SHA 一致 |

初轮夹具缺陷修复后没有同缺陷连续红两轮；mutation 首轮即被真实行为断言捕获，没有重跑凑红。

## Mutation 原件与关联

`swarm/breaker.py:212` 原行为 `if _suspension_required(params):`，临时仅改成 `if False and _suspension_required(params):`。这使真实 aggregate 不再触发 suspended；生产 Worker 的下次路由实际多发了 alpha 一次。失败点是 `runtime.py:124` 的 `assert executor.execute.call_count == expected`，不是依赖、导入、语法错误，也不只是状态字面值不同。

`fc-tests-0929-mutation.json` 保留原行、变异行、路径、SHA256、命令和退出码：原/恢复 `943613494823feec7598a87e7de936c14f43ebe3d14296099ebafc4fe09a27b4`；变异 `45ac1ac5815145683c4ccfd9d8488c44b2a5dd867122dba913a2b0c11110bf9d`。临时脚本 `.runtime/fc-tests-0929/check_mutation.py` 使用 finally 恢复；两次 pytest 用独立 PYTHONPYCACHEPREFIX，避免缓存掩盖磁盘变化。正式提交没有生产 mutation。

## 预算 A/B：供 H1 交叉核对，不代签

以下源码行号绑定 F，也适用于本轨测试提交（生产无持久 diff）。

- **A：unknown hold 不因同 task pending 互斥而自锁。** `budget.py:178-180` SQL 为 `request_id=? OR (task_id=? AND status='pending')`；`mark_unknown_rejection` 在 `229-235` 仅把当前 pending 写为 uncertain、不清旧 hold、不置全局 stop。Worker `793-799` 区分 confirmed rejection 与 unknown effect，`757-758` 以 `task_id:lease.token:index` 生成新 request_id。因此确认拒绝可在容量等门禁允许时继续；不是所有 unknown 都允许续发。`runtime.py:157` 和 `boundaries.py:81` 的 unknown 参数实测同任务第 2 次能入场。
- **B：同一 unknown hold 不同时计入 spent 与 hold。** `budget.py:82` 只把非 settled 行算 hold；`191-194` 准入使用 `SUM(admitted_usd) + reserved_estimate_usd + 新预留`；`199-202` 新行 admitted 为 NULL；`233-235` unknown rejection 只更新 status/settled_at。已知估算结清在 `283-286` 写 status=settled/admitted，原 allowance 不因较低 usage 被退回。真实两次 unknown 记录的 hold=0.4/admitted=0；known 控制 hold=0/admitted=0.4；第三次 0.2 请求在 0.5 限额下不发。
- **没有 uncertain→settled 晚到结算闭环。** `budget.py:253-257` 在 status 非 pending 时返回快照（冲突 settlement 还会拒绝），不更新 uncertain；`82` 持续持有其额度；Worker `987-991` 清理 active 也只是 mark_uncertain。任务结束/重启并不自动退额，长期运行可能耗尽可准入容量，需要人工停止/恢复决策。没有新结算 API，没有自动释放。
- unbounded allowance 的 `budget.py:130-153` 是本地准入额度，不是上游价格或账单硬上限。`actual_cost_usd` 保持 None；上述证据不证明真实 provider 费用上限，也不替代 H1 对并发与操作边界的人工核对。

## 未解决问题、交接与 NOT_RUN

- **生产缺陷：** F `worker_loop.py:839` 只看 result.uncertain，将“有 usage、无价格”的 failure observation 写为 cost_state=settled，账本仍正确保留 unknown 和 full hold。具体复现、逐字引文、最小只改元数据的建议、语义回归清单在 `fc-tests-0929-cost-state-handoff.md`；已经主控接收，生产修改须另行决策。本轨未代修，也未把该红项转绿。
- 台账由 B 更新；本轨不写 TASKS.md。阶段 SHA、各 gate 及该独立语义红项通过注入的 Orca dispatch 交主控转 B，不能只写“全绿/已冻结”。交接字段应为：测试门禁通过、mutation 有效、生产 cost_state 缺陷 OPEN、H1/FC-E/冻结 NOT_RUN；最终交付 tip 是测试提交后的报告专用提交，以 worker_done / git log 的精确 SHA 为准。
- `contract_local`：本报告列出的测试为 mock 执行器边界 + 真本地 Worker/DB/文件机制证据。`interface_live=not_run`、`task_live=not_run`；无真实模型/Hub/付费调用，无 live 子进程路径改写。历史 F Windows698/Ubuntu697+skip 为参照，不能覆盖本次变化。
- **NOT_RUN：** 新 build/wheel、真实模型/Hub/生产演练、长时间服务验收、FC-E 正式异构评审、H1 人类签字、tag/冻结/部署、集成合并、unknown 晚到结算/自动释放。生产修复、人类 H1 与 FC-E 后续动作留主控/原 Owner；本轨完成不宣称这些完成。
