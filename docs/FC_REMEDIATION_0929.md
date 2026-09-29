# FC 五项生产缺陷修复一页计划（2026-09-29）

本轮用户明确授权五项生产修复，覆盖旧材料中“未授权 cost_state 修复”的限制；所有轨基线为 `3a34ecafe5f48b1a5a7c94c9e063797427817cab`。旧 `FC_DAY_PLAN_0929.md`、`PLAN.md`、TASKS 和五不变量保留，不预写通过。

| 轨 / 固定 Owner | Worktree / Branch（同名，根目录 `C:/Users/DW/orca/workspaces/Morphogenesis/`） | 独占 write_paths / 交付 |
|---|---|---|
| A / codex | `morph-fc-runtime-fix-0929` | `swarm/worker_loop.py`、`swarm/budget.py`、`swarm/task_ledger.py` 和派发指定执行预算测试、证据；修复 unknown effect 已知费用跨重启禁止再次发送、本次 reservation 的 cost_state |
| B / codex | `morph-fc-breaker-fix-0929` | `swarm/breaker.py`、`swarm/fault_observations.py` 和派发指定测试、证据；修复 TTL 探测 token 生命周期、恢复后旧故障不再重熔断；真实 Worker 路由测试在 `tests/swarm/test_probe_lifecycle_recovery.py` |
| C / codex | `morph-fc-classification-fix-0929` | `orchestration/provider_adapters/{base,dashscope,evomap}.py`、`swarm/failure_chain.py`、`tests/orchestration/test_provider_adapters.py`、新 `tests/orchestration/test_rejection_classification_boundaries.py`、新 `tests/swarm/test_rejection_runtime_boundaries.py`、本文、`artifacts/ai-evidence/fc-remediation-classification-0929-*`；修复 5xx/transport unknown 优先级及真实 adapter→Worker 链路 |

路径协作：主控转交 B 的 TTL 路由 Handoff，由 C 在 `guard_provider` 调用现有原子 `try_claim_probe`，使过期 probing slot 取得 fresh token 并传入 `ProbeClaim`；B 保有 breaker/observations 写权和真实 Worker 生命周期验收。C 先交独立 guard 阶段 SHA；B 可在 ignored 候选导出中组合验证，不交叉 cherry-pick 最终分支。主控只维护计划、状态、决策与独立验收，领域实现和返修持续归原 Owner；最后独立集成 Agent 合并三轨。

执行顺序：① 读事实源、核对基线/路径并回报；② 每项新增回归，在原实现保留真实失败；③ 最小生产修复并跑适用旧/新测试；④ 语义 mutation 必须红，finally 恢复原字节并恢复绿；⑤ 阶段 commit（`Swarm-Agent: codex`）、最终 push/remote SHA/clean/路径核对；⑥ 独立集成取得不可变 SHA，在该 SHA 重跑 focused/full/strict/build/官方 SDK/分发，不复用旧日志冒充重跑。

测试纪律：真实 `Worker._process`、路由和持久存储；只 mock 外部边界，用 executor/transport 调用次数和持久状态断言实际行为，断言不埋在生产 catch 的 try 中。保留所有旧测试，不删减、skip 或放松断言；修复门禁连续两轮失败即上报暂停。5xx 配中英文欠费/配额/余额/账户正文及结构化 code/message 仍保守 unknown，普通 4xx 和现有明确拒绝契约保留受控切换。无付费 live、无 live 子进程 mock、无虚构 usage/cost、无未知效果重试或费用释放。

环境与证据：只读使用 `C:/Users/DW/orca/workspaces/Morphogenesis/morph-fc-integration-0927/.venv/Scripts/python.exe`；不安装依赖、不改锁。运行产物仅 ignored `.runtime`；源码用 `git -c core.autocrlf=false archive` 精确导出，测试 state 与源码平级；必要 SDK junction 先核实不存在、目标版本和 ignored。报告分别列原失败、Owner 修复自验、mutation、独立验收、NOT_RUN，附 exact SHA/base/diff/remote/clean、命令和 exit。

当前状态：C 源码 `36aa0e7ec7b355ad0c8e2eacfc5489df9d577ad4` Owner focused 246 / strict 87 / SDK 1.14.0 通过，分类 mutation 两家各红 2→恢复绿 2，guard mutation 红 3→恢复绿 3；[C 证据报告](../artifacts/ai-evidence/fc-remediation-classification-0929-report.md)。Guard 阶段 `42b6115b0815289c22678aaec6240515f700b881` 已交 B 组合验；A/B 独立交付、共同候选六门禁与独立验收仍待主控登记。C 的 `python -m build --no-isolation` 因指定 venv 缺 Poetry 后端 exit 1 保留，未安装依赖；主控已指定构建/分发交最终组合门禁处理。H1/H3 人工签字、正式 deepseek-r1 FC-E v2、入口与演练分别保持 OPEN；`contract_local`、`interface_live`、`task_live` 分别登记。生产合并/tag/冻结/发布、付费 live 均不在本轮 Owner 自验范围。

## 2026-09-29 五项最终状态（独立治理分支登记）

本轮五项修复已获授权并完成 C552 本地验收；不再沿用旧 cost_state 未授权限制。A `4d1098ed151d6a9859e088f13ea292baeef1acf2`、B `2c6a33ae1950fd6458543618d1c4044dcdd2596f`、C `e6ac45ffefc171a7215f8db19bc4a28af24ec4fc` 普通 no-ff 合并为唯一代码候选 **`c552250c0d07f5f70f09eb0a5ab3c322195e34ec`**，代码分支 `morph-fc-candidate-0929` remote exact/clean。治理 G 分支 `morph-fc-governance-final-0929` 不合入代码，不把文档 SHA 当测试候选。

- Owner：A119 focused/3 scoped strict，B+C96组合，C246 focused/strict87/SDK；各原始红与mutation分别保留。
- I同一C552六门禁实际执行：focused408、full862/2 warnings/589.58s、strict87、build新sdist+wheel、SDK1.14.0、分发13packages+Node，全exit0；[I报告原字节副本](../artifacts/ai-evidence/fc-remediation-governance-0929-integration-report.md)。
- D `9a6705c7aeae9c812329c015f13e440842beff17`：独立47 focused、九mutation红/恢复绿，464旧函数/1558assert保留；[D报告原字节副本](../artifacts/ai-evidence/fc-remediation-governance-0929-independent-report.md)。G已核原日志及346源码，非G重跑。
- B原full47failed/656passed/7errors/exit1、B/C缺后端build exit1、D首轮恢复失败/路径过长及其他原红继续保留，不被最终六绿改写。
- 正式FC-E实际一次deepseek-r1响应已取得，usage76253、cost unknown；引用2PASS/2INVALID、机械exit1，缺五不变量逐项覆盖，高危仅待验证假设、5xx意见与要求冲突，**REJECTED**；唯一请求用尽，未自动再试。
- [H1/H3包](FC_HUMAN_REVIEW_0929.md) 已备C552预算A/B逐字代码、矩阵/fencing/三处TODO位置/六点和待验证风险，仍unsigned；Schema仍1.0.0 optional+nullable candidate、未采集。

五项 `contract_local` 完成；蜂群 `interface_live/task_live`、T6三连冒烟、正式入口/演练、生产merge/tag/冻结/发布仍NOT_RUN。DashScope完整生产executor仍NOT_IMPLEMENTED（真实adapter已测）；unknown hold晚到对账/自动释放、任务自动解锁、混合版本/历史生产状态迁移没有被本轮证明。FC整体BLOCKED，不宣称整体稳定。完整事实与来源见[G最终治理报告](../artifacts/ai-evidence/fc-remediation-governance-0929-report.md)。

## 2026-09-29 正式评审引擎替换状态（G续接，最新）

用户本轮指定 **dsh + DeepSeek V4.1 Flash**，新授权不受旧R1请求额度限制；旧R1原响应/报告/REJECTED保留。安装目录解析为 `deepseek-official / deepseek-flash`，不同于V4 Flash；原FC配置为DashScope R1，标准原生认证来源未取得指定路由凭据。因此替换评审**NOT_RUN、认证BLOCKED、FC-E OPEN**，request_count=0，实际模型/usage/cost=null，无SDK替代或全局修改。

完整C552编号输入/37项覆盖矩阵已备，机械输入exit0；无响应验收exit2，旧R1样本对照exit1仍2PASS/2INVALID。主控已澄清一轮原生invocation/最长10分钟/零自动重试/有限输出；缺原生请求数参数只记能力限制，不另设审批或exactly-one-HTTP门禁。详细来源与真实未执行项见[新模型报告](../artifacts/ai-evidence/review-0929-v41flash-report.md)及[两轨计划](FC_RELEASE_PLAN_0929.md)。

五项本地修复和I/D旧证据状态不变，本轮未重跑六门禁或D测试；H1/H3 unsigned，T6 merge/tag/三连冒烟、T9/T10/T11/业务live NOT_RUN，整体BLOCKED未冻结。
