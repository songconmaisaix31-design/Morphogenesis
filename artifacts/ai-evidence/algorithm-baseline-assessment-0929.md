# 底层算法基线状态分析 · 2026-09-29 上午

**结论：原始 v0.2 的受限本地功能基线已实现，并有独立回归和双平台证据；含真实模型接续/跨成员采用的完整验收不能宣布全部完成。FC 后继已有实现，但关键执行链测试不足，当前不能冻结为已验收底座。可以开始只读应用原型；“稳定”目前只能限定到已验证的本地机制与明确输入边界，不能扩为长期自主运行或持续成长承诺。** 本报告是状态分析，不是 H1 签字、FC-E 正式评审或冻结操作。

**范围与精确版本。** 按 `V:docs/source/README_包内说明.md:5–12` 的现行文档顺序读取六份开发包文件，v1 开发文档不作依据；再以用户修正版 `V:docs/SWARM_TASK.md:3–5`（“本文件替代此前 SWARM_TASK 的相冲突规划”）界定同机、可信 Worker、共享 SQLite 的 v0.2，以 `F:QWEN.md:18–26`、`G:docs/FC_PLAN.md:120–128` 界定后继受控失败链。已读 QWEN、PLAN、SWARM 契约/计划/审查、FC_ACCEPTANCE 及昨夜独立验收；未把不同轮次合并成一个完成状态。

| 代号 | 不可变提交与用途 |
|---|---|
| V | `0bc03ae60f528a62a63193048499987e8992b36a`：原始 v0.2 独立验收快照 |
| F | `73e64cc70116ac658d85591d082c0684a4952c99`：FC 集成候选，远端 `songconmaisaix31-design/morph-fc-integration-0927` |
| G | `73798cd6f05210f2bd9b1eebfd6f9f0dd6e842db`：当前审查起点及远端 `decentralized-swarm` |
| P | `b551cd4441d8fbab09dcc4d081baa4dccc73910e`：真实 benchmark 记录 |
| E | `4409a60e278ce328fd76588d680e3c4438bdaa84`：昨夜独立验收报告 |

今晨 `git ls-remote` 已核对 F/G/E；`git merge-base --is-ancestor F G` 返回 **1**，且 G 缺少 `swarm/breaker.py`、`failure_chain.py` 等 FC 文件。F 不是 G 的已整合能力；当前 integration 工作树另在测试返修分支 `fix/fcd-interface-alignment@2d9d4304cfc0e1a3d4bfaeccb6ec5688aef60366`，本报告读取 F 的 Git blob，未拿该工作区冒充 F。

**需求 → 实现 → 证据 → 完成边界。** 下表引文均对照指定 Git blob；测试文件表示检查了测试实际断言，历史执行证据见 L1/L2，本次没有重跑测试。

| 核心项与要求 | 实现锚点与短引文 | 可核验依据及判定 |
|---|---|---|
| 路由/信息素：`V:docs/SWARM_TASK.md:29`，历史权重参与 softmax，权限/依赖过滤、探索/aging、有界查询 | `V:swarm/router.py:42–87`，`score = self.beta * own_history[key] * signal.concentration * match * urgency`（62）；`V:swarm/pheromone.py:114`，`weight=(1-self.alpha)*previous.weight+self.alpha*reward` | `V:tests/swarm/test_router.py:30–42` 在相同抽样点先选 b、强化后选 a，并检查概率；field 测试 22–83 验证衰减、事实不遗忘。**本地机制已验；无吞吐/无饥饿保证或成长收益证明。** |
| 原子认领、租约/fencing、幂等提交：`V:docs/SWARM_TASK.md:27,31,35` | `V:swarm/task_ledger.py:47` 使用 `BEGIN IMMEDIATE`；305 为 `token=row["token"] + 1`；312–319 校验 owner/token/expiry/TTL；367–394 先留 intent，再 fenced apply | `V:tests/swarm/test_lease.py:21–71` 检验 token 2 接续、旧提交/释放拒绝，含真进程终止；`V:tests/swarm/test_integration_restart.py:56–116` 与 L2 支持重启无重复落地。**本地受限故障恢复已验；partial-submitting 需人工恢复，非跨机一致性/多文件事务。** |
| 预算与 unknown：`V:docs/SWARM_TASK.md:16,33` 要求保留预留、不盲目重发，只在可信上界下宣称费用保证 | `V:swarm/budget.py:82` 将非 settled 计入 holds；226–230 拒绝覆盖终态；253 `admitted = max(estimate, reservation.reserved_estimate_usd)` | `V:tests/swarm/test_budget.py:82–96,150–194,268–280` 覆盖 unknown、进程竞争和不退 allowance；`test_budget_evomap.py:49–72` 覆盖有 tokens 无价格。**准入机制已验；账单硬上限未验。F 的差异见下段。** |
| 最初 T3 拓扑/代谢：`V:docs/source/Morphogenesis_AI原生多Agent多轨开发说明.md:304–318`，选路受权重影响、重复反馈一次、衰减/归档、T4 可选 | `V:topology/engine.py:143–147,222–239` 去重/强化，163–217 显式裁剪/新边；`V:metabolism/decay.py:11`，`return math.exp(-elapsed_seconds / tau_seconds)`；`metabolism/service.py:215–244,272–286` 使用记录/归档 | `V:tests/t3/topology/test_engine.py:46–130`、`tests/t3/metabolism/test_metabolism.py:94–171,173–248` 纳入 L1。**局部能力已验。** tau 非半衰期；0.05 是 archive_threshold；257 明写 `never merge/evolve`，不等于自动进化。 |
| 经验闭环：`V:docs/SWARM_TASK.md:17,24,35`，FETCH approved→适用性→注入→真实采用 | `V:local_assets/consume.py:94–131` 查 completed/effect_applied、上下文、token 与实际字节，失败为 `adoption_requires_completed_fenced_execution`（105）；`V:swarm/worker_loop.py:438–477` 恢复并受控反馈 | `V:tests/swarm/test_selfgrowth.py:73–108,145–183` 三进程/跨成员采用；L2 有真实本地进程与字节，但执行器为 mock。**contract_local 闭环已验；不能据此说真实模型复用/进化全部通过。** |
| FC 分类/共享 breaker：`F:QWEN.md:58–82,100–138` | `F:orchestration/provider_adapters/base.py:38–105`、`dashscope.py:64` 处理 Arrearage；`swarm/fault_observations.py:105` 为 `idempotence is (run_id, request_id, attempt)`；`swarm/breaker.py:183–242,545–570,596–640` 四态与探测 token | `F:tests/orchestration/test_integration.py:104–232` 有真实子进程 mock 回传；`tests/swarm/test_breaker.py:436–464,571–602` 有同 owner 旧 token 与四进程唯一探测断言。**模块有实质实现/测试，不能说全是占位；人工复核与组合闭环仍未验收。** |
| FC 执行链五不变量：`F:QWEN.md:21–26` | `F:swarm/worker_loop.py:739–826` 候选遍历、先 reserve 后 execute、unknown 退出；`swarm/failure_chain.py:154–175` 仅 confirmed_rejection 切换 | `F:tests/swarm/test_failure_chain_runtime.py:38–88` 只测试 decide/guard/数据接口，没有运行 Worker 链；边界文件 30–43 对自建 response 断言 `assert response.status == 400`（39）和 body 字段。**此类测试不能证明 Worker 真正切换/停止、请求计数和失租拒绝；不代表全部 698 项无效。** |

**unknown 的明确判定。** F 的 `budget.py:178–180,229–235` 只阻止同任务 pending，相同 request_id 仍拒绝；已确认拒绝可把 pending 改 uncertain，再用新 request_id 继续，前提是累计容量等允许。82、191–194 仍计旧 hold；253–257 对非 pending 直接返回，故没有 uncertain→settled 晚到结算入口；`worker_loop.py:793–800,987–991` 也不会在任务结束时释放旧 hold。这是“容量长期占用”，**不是同 task pending 自锁、双计或已发生超支的证明**。原契约 `V:docs/SWARM_CONTRACTS.md:109–110` 明写 “unknown holds never expire/retry”，因此缺对账入口不是本次追加的原型完成门槛；作为长期服务必须明确接受人工停止/恢复限制，不能让应用假设任务结束即退额。F 的实验 opt-in `swarm/models.py:116–117` 默认 False，后续实验可显式允许未知成本，仍不能抹掉 hold 或把未知费用写 0。

**证据强度与“稳定”。** L1 直接核对保存的 CI 原件，支持 V 的历史本地工程可靠性；L2 支持有界真实进程故障/重启与本地采用。F 也有完整本地 CI：B 采集、A 复读的 L4 绑定精确 F，run **36337808956** 双平台 success，Windows **698 passed**、Ubuntu **697 passed/1 skipped**，两边 strict 87、build/SDK/wheel 通过；承认其工程回归价值，不把 698 写成仅 Owner 自报。另一方面，`F:docs/FC_ACCEPTANCE.md:62–68` 已承认 FC-D 浅层及 live 未跑；`G:TASKS.md:103–110,124–128` 保留两次 mutation 仍绿与拒收记录。缺口具体影响受控切换、unknown 后停止等新增组合行为的可信度，本次未重跑 mutation。Schema 的 11/12、exit 1（`E:artifacts/ai-evidence/acceptance-0928-final.md:71–86,139`）只否决该日志 Schema，不能推翻路由/租约等全部算法；以上也不是长时间服务可用性承诺。

真实模型证据并非全无：今晨读取 L3 两份结果，均 `provenance=live`、48 请求、8 进程 exit 0、`interface_live=passed`，但这两场实验的 `task_live=blocked`、跨成员采用 0；正确数分别 **25/48、30/48**，费用均 null。这与 `P:docs/SWARM_BENCHMARK.md:36–46` 相符，只是不同模型池横截面对比，未证明持续成长，也未验收对应跨成员复用闭环；不覆盖其他历史场景的 task_live，更不能由零采用推出“完全没有学习”。原设计不保证数学收敛（`V:docs/source/Morphogenesis_深度思考.md:217–220`），T4 明确可选；不新增数学证明或研究门槛，只限制“越跑越强/已进化”的宣称。

**冻结与应用建议（分析判断）。** 可以固定 V 作为标明范围的本地算法参考，并并行做 observer/仪表盘、任务/采用轨迹、unknown 与 provenance 展示、离线回放和业务需求原型；这不要求先完成 T4、生产 Hub 或账单对账 API。要冻结 FC 控制底座，先由原 Owner 补齐真实 Worker 候选链的有效行为断言（累计预算、unknown 后零新请求、失租拒绝、全候选有界退出）并完成既定验收，随后在唯一精确候选上满足 FC-E/H1 等原有门禁；`G:TASKS.md:161–172` 三锁仍未齐。应用暂不绑定自动重试/切换、unknown 自动清除/退额、恢复必成功、任意代码沙箱、永久稳定状态枚举或性能增长承诺。**当前建议是“受限只读上层先行，FC 写入/执行控制冻结暂缓”，不是继续无限扩建算法。**

**假设。** “最初基线”优先指修正版 v0.2 的本地算法原型；若把 9 月 24 日追加真实模型验收及 FC 后继也包含在内，则答案为尚未完整完成。“稳定”优先指工程行为与接口语义可依赖，不指论文级最优性。L3 的运行类别取已有产物，未重新认证远端服务或把退出 0 等同任务成功。

**可定位证据与本次检查。** `D=C:/Users/DW/orca/workspaces/Morphogenesis/decentralized-swarm`；`T=C:/Users/DW/AppData/Local/Temp`。

- **L1**：`D/.runtime/swarm-revision-coordinator/final-ci.json` 的 headSha=V、run=35895250033、两 job success；同目录 `final-ci-ubuntu.log:380` 为 “490 passed, 1 skipped”，`final-ci-windows.log:369` 为 “491 passed”；strict/build/SDK/wheel 步骤可逐项追溯。是读取历史原件，不是本次 CI。
- **L2**：`D/.runtime/swarm-integration-20260924/pytest-final-summary.json` 绑定 `fc6983ea598c94fc9e7e2a04b40b648e48cc50cf`；`pytest-final.log:2` 为 “44 passed in 323.30s”；`restart-final-evidence.json` 三 PID=37024/42344/2404、contract_local/mock、保留业务行；`kill-and-adoption-evidence.json:77` 含 token 2。相关修复及测试进入 V，未冒充 F 新增路径验证。
- **L3**：`T/morph-benchmark-8x48-sol-result.json`、`T/morph-benchmark-8x48-hetero-result.json`，核对 `benchmark`、`request_count`、`run.process_exitcodes/interface_live/task_live/cross_member_adoptions`、`cost` 字段；未导出题目、gold 或凭据。
- **L4**：`C:/Users/DW/orca/workspaces/Morphogenesis/morph-release-readiness-review-0929/.runtime/release-readiness-0929/ci-fc.json` 的 headSha=F、conclusion=success；同目录 `ci-fc.log:372,882` 为两平台 pytest 结果，386/895 为 strict 87，415/923 为构建，433/940 为官方 SDK schema/tamper 验证。未重复下载或运行 CI。
- 本次执行 `git status/rev-parse/worktree list/show/diff/grep`、源码/测试逐字核对、上述 JSON/log 只读检查和 `git ls-remote`。首轮网络读取 SSL_ERROR_SYSCALL，命令局部 `-c http.sslBackend=schannel` 重试成功；未改全局 TLS。复用 integration 的既有 `.venv/Scripts/python.exe` 运行本轨 `.runtime/audit-0929/verify_quotes.py`：36 处显式行号范围、12 条短引文全部匹配，exit 0；一次报告行号超界已更正，未修改产品。`git diff --check` 通过；此为引用检查，不是算法重验。
- **NOT_RUN**：新 pytest/类型/构建/全量/mutation、模型/Hub/生产调用、依赖安装、修 bug、合并/tag/部署/冻结、H1 代签、FC-E 正式评审。生产源码、测试、AGENTS、SWARM 文档与锁文件只读；仅本报告提交，分支 `morph-algorithm-baseline-review-0929`，提交 trailer `Swarm-Agent: codex`。
