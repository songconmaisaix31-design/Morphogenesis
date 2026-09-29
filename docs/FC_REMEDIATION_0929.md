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
