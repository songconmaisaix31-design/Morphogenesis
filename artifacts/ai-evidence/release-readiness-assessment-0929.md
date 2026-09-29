# 发布与应用层准入审查 B — 2026-09-29

审查者 codex；09:17–09:25 CST 只读取证。**建议：仅可保留精确候选快照并开展受限应用开发；目前不具备 FC demo-build 冻结资格，也尚未证明生产稳定。** 有真实本地门禁和历史任务成功，不能写成“全系统已证明不稳定”；原始算法逐项完成度由 A 轨另审，本报告不把长期运行新增为原始原型合同门槛。

| 决策对象 | 本次判断 | 实际边界 |
|---|---|---|
| 原型代码基线 | 可保留、复用已验证部分 | 第一代、去中心化基座、FC 联合候选须分别标 SHA |
| FC 发布冻结 | **不可冻结** | 有效 FC-E、H1 尚缺；统一发布分支/tag/smoke 尚未形成 |
| 上层先开工 | **有条件可开工** | 只读展示、离线分析、可替换适配层；使用既有字段并保留 unknown/provenance |
| 稳定 API / 自动运行承诺 | **未准入** | 预算对账、自动重试/切换、调度/租约写入、正式日志写入分别等待对应契约与运行验收 |

以下别名均为本次 `git ls-remote --heads --tags origin` 核实的不可变快照；`L` 为本工作树 ignored `.runtime/release-readiness-0929/`，查询和退出码原件在 `L/audit.log:1-143`。

| 别名 / 分支 | 精确 SHA | 当前事实 |
|---|---|---|
| M / codex/morphogenesis-mainline | `2957b408ce922369a595a8acd43a882eb85897d3` | 应用若从此分支开发，将取第一代实现；无 swarm/worker_loop.py |
| G / decentralized-swarm | `73798cd6f05210f2bd9b1eebfd6f9f0dd6e842db` | 去中心化基座及治理/Schema 文档；未合入 FC |
| F / songconmaisaix31-design/morph-fc-integration-0927 | `73e64cc70116ac658d85591d082c0684a4952c99` | 本次 **FC 唯一联合代码取证候选**，不是已发布稳定基线 |
| T / fix/fcd-interface-alignment | `2d9d4304cfc0e1a3d4bfaeccb6ec5688aef60366` | 相对 F 仅边界测试变化；已裁撤，保留 demo-build.1 后续候选 |
| E / fc/review-only | `78c07459e14b4817c83c608c68978a07b68b5f9f` | 仍为被拒收的同源降级评审稿 |

**不存在把以上全部整合且已冻结的唯一 SHA。** F→M、F→G 的 `merge-base --is-ancestor` 均 exit 1；F→T exit 0。G 缺 breaker/failure_chain/fault_observations，不能套用 F 的通过记录；原 integration 工作树现检出 T，并非 F。M 另有 `docs/SWARM_SOL_PLAN.md` WIP；其余上述检查工作树 clean，均未修改。证据 `L/audit.log:54-132`。

| 当前事实 / 证据权重 | 精确验证出处与影响 |
|---|---|
| **完整 CI 确实存在** | F 的 [CI 36337808956](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/36337808956) 双平台 success：Windows **698 passed**，Ubuntu **697 passed / 1 skipped**；strict **87** 文件；sdist/wheel、SDK **1.14.0**、13 包安装检查通过。`L/ci-fc.log:372,386,415,433,465,882,895,923,940,970`。原本机 698/2 warnings 为 `F:docs/FC_ACCEPTANCE.md:22-33` 的报告记录；本次另取 CI 原件（73 warnings），没有伪称重跑本机全量。 |
| **各分支 CI 不可混算** | M [CI 36432868496](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/36432868496)：Windows 294、Ubuntu 293+1 skip、strict55；G [CI 36449303917](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/36449303917)：545、544+1 skip、strict81；两者 build/SDK/安装检查均过。`L/ci-main.log:368,381,841,855`，`L/ci-governance.log:386,399,877,891`。三份 CI JSON 的实际 steps 8–13 均 success；覆盖各自已提交代码，未覆盖跨分支组合、WIP、Schema 语义或稳定性。 |
| **假绿降低五不变量的证明强度** | F 的边界用例只构造响应后断言 error_kind（`F:tests/swarm/test_failure_chain_boundaries.py:84-86`），子进程用例仍只构造 Reply（同文件 `:584-603`），无 call_count。T 的两次 mutation 存活来自 `G:TASKS.md:124-127` 的历史台账，本次未重跑，也未取得其完整 mutation 原日志。已排除 T（`:166-167`）不再是所有生产代码的永久阻塞；上述事实也**不证明生产不变量已被违反**。 |
| **未知费用没有事后结算闭环** | `F:swarm/budget.py:253-257`：`status != "pending"` 即返回；`:82` 持续计非 settled hold，`:178-180` 同 task 仅 pending 互斥，`:191-202` hold 与 admitted 分账。故新 request_id 不因旧 uncertain 自锁，同一 hold 未双计；但迟到 usage 不能结清 uncertain，任务结束仍长期占额度（`F:swarm/worker_loop.py:793-800`、`:987-991`）。`:130-153` 的 unbounded allowance 不是上游账单硬上限；这是应用预算风险，不是已发生重复收费的证据。 |
| **fencing 有实现；H1 / FC-E 未闭合** | `F:swarm/breaker.py:560-570` 原子竞争，`:636-643` 条件为 `probe_owner=? AND probe_token=?` 加有效期，旧 token 不能靠读取新 token 直接覆盖；这是静态证据。`G:docs/FC_HUMAN_REVIEW_0928.md:69-74`、`:171-176` 签字仍空。E 报告 `:41` 已撤回原 token high 推断，但 `:65` 错引138行（实际 F 的85行）、`:109` 仍称计数充分；拒收不只是缺 trailer。未发现更新的正式报告，不能用本审查替代 FC-E 锁。 |
| **Schema 仍红，属于应用日志契约** | G 与 `2e56fa1efaa030da5a52c614172654a4e6ea1188` 的 JSON **38342 字节相同**（`L/audit.log:134`）。本次独立最小校验：基础事件 VALID，count=null/audit 缺失 INVALID，`allOf/1/then/required`，**exit 1**（`L/schema-current.log:1-9`）；G 当前 required 在 `G:docs/FC_LOG_SCHEMA_DRAFT_0928.md:1649-1651`。历史独立报告 `4409a60e278ce328fd76588d680e3c4438bdaa84` 的 `artifacts/ai-evidence/acceptance-0928-final.md` 保留8/9、11/12与原exit1。版本规则见 G 同 Schema `:11-15`：optional 新增 minor，optional→required 为 major/2.0.0。尚未正式验收/生产接线，不能因 G CI 绿当 Schema 绿；也不能据此否定底层算法。 |
| **发布与稳定性证据范围有限** | 远端/本地仅 archive tag，无 demo-build 或 demo-build.1；F 未合回 M/G。`G:TASKS.md:171-176` 仍记 T6 merge/tag/三连smoke、T10 未执行；F 本轮 `interface_live/task_live=not_run`（`F:docs/FC_ACCEPTANCE.md:58-68`）。历史有真实 Sol 两任务成功：`M:docs/ACCEPTANCE.md:20-24`，root `.runtime/review-20260924/sol-audit.log` 可读、原 rehearsal.json 仍在；是旧固定样例和局部接口证据，不能代替 FC 故障链、三连smoke或长期稳定证明。 |

最短放行门槛按性质排序（本轮不执行）：

1. **实质风险**：预算 Owner 明确 unknown 的保守占用/人工对账边界；若应用要求自动结算，先实现并验收迟到证据与单次记账，不能自动释放。可接受 FC-E 报告和真人 H1 必须针对所选精确代码；有效高危发现由领域 Owner 处理。正式日志消费者先修 nullable 红项并验收兼容/版本规则；这不是所有只读页面的前置。
2. **测试证据**：补足真实 Worker 请求计数、未知效果不续发、失租拒交、探测竞争的敏感性证据；T 保留后续 bump，若按裁撤方案冻结 F，需显式保留该证据缺口，不能称五不变量已完备验证。现有同 SHA CI 可复用；任何新组合/修复再跑适用全量、strict、build、SDK，保留失败和真实退出。
3. **发布流程**：三锁满足后由授权集成人选择唯一应用分支、合并精确候选、标 tag，再记录三连smoke和计划内演练；长跑/live 只决定能承诺的稳定性等级，不追加为原始本地原型完成条件。本轮未作冻结、合并或授权变更。
4. **治理元数据**：缺 Swarm-Agent trailer、旧段落状态冲突用后续提交补说明，不改公共历史；严重性低于预算/并发风险与错误契约，不能把补文案当运行时修复。

**现在可做**：固定 F 或已核实的既有只读数据源 SHA，保留可替换 adapter、missing/null 和 live/replay/mock 三态，开发布局、筛选、离线分析。**等待**：依赖未冻结 Schema 的 T9 正式样例/日志写入，或驱动预算、重试、调度、租约、Hub 外部效果的应用，以及对外稳定 API 承诺（`G:TASKS.md:174-176`；`F:QWEN.md:21-26`）。

本轮命令：`git ls-remote / log / diff / ls-tree / merge-base`；`gh run view <上述ID> --json headSha,status,conclusion,jobs,url` 与 `--log` 均取回成功（exit0）；指定 integration `.venv/Scripts/python.exe -B L/audit.py` exit0；`-B L/schema_check.py` **exit1**；`-B L/check_references.py` **55 处引用通过/exit0**，原件 `L/references.log`、`L/references.json`。脚本和日志仅在 L。**NOT_RUN**：新全量 pytest/strict/build/SDK、mutation、三连smoke、故障演练、付费/live、长期运行、FC-E 返修、H1 签字、生产 merge/tag；未安装依赖。交付仅此报告，分支 `morph-release-readiness-review-0929`，报告提交 SHA 以实际 push 回执为准。
