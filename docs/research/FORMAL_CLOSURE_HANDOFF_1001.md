# 三角色正式闭环 Handoff（2026-10-01）

状态：**prepared；完整 task_live 未通过**。接收方：主控、P（Morphogenesis-Research / research-product-1001）、I。B 原 Owner 保留原 worktree / branch；本阶段只写本文件及 `docs/tracks/research-space-1001.md`，不修改领域源码、原 checker、认证或旧案例。

本次只读源码基准：`c45888f64c1cec60e5f9df45677b6547c4527cac`；其中冻结业务候选为 `bde3412d2257fd1581ce1d7f88b254fb0c13a269`。下列 `file:line` 均对应该基准。新产品最终依赖必须由 P/I 冻结并记录完整 SHA，不能把本文件的准备状态当其验收。

引用简写：service=`swarm/research/service.py`，server=`swarm/research/server.py`，checker=`tests/integration/check_research_live.py`，ledger=`swarm/task_ledger.py`，research=`local_assets/research.py`，consume=`local_assets/consume.py`，promote=`local_assets/promote.py`，models=`local_assets/models.py`；同一括号的后续行号沿用前一个文件。

## 给 P/I 的薄接口契约

- 已有独立 stdio 入口：选定环境的 Python 执行 `-m swarm.research --config <绝对可信配置路径>`；入口不需要 ORCA（`swarm/research/__main__.py:12`）。保留 venv 原启动路径，不能换成 resolve 后的系统解释器（`swarm/research/case.py:33`）。
- HostConfig 绑定 `ledger_path/swarm_id/workspace/worker_id/agent/authorized_scopes/capabilities/assets_root/evidence_root/project_context/experiment_backend/max_experiments_per_task`（`swarm/research/models.py:8`）。配置、账本、资产和实验归档放在项目外的受保护 state；Agent 工具参数没有身份、配置、判据、metric 或 approved 管理入口。
- P 正式 CLI 承担原生权限和配置，测试只观察。Codex 为 read-only、never，11 工具可见且每项 approval_mode=approve，默认 prompt；Claude 为 dontAsk、严格单 MCP 配置、精确 allowed_tools、关闭内建 tools/slash commands。原 checker 核验实际 request/argv/host_binding（`tests/integration/check_research_live.py:145`）。仅 enabled_tools 不等于许可（现有集成启动适配 `tests/integration/run_research_native.py:184`）。不能依赖测试夹具补权限。
- 工具集合为 `discover_tasks/project_context/lease_task/search_evidence/research_experiment/research_candidate/verify_research/complete_research_task/approve_candidate/inherit_experience/apply_candidate`（`swarm/research/server.py:12`，原 checker `:22`）。宿主不自动派单；角色主动 discover/context/claim/renew，依赖结果来自账本。
- nativebrand 不在 HostConfig 或科学晋级门禁中。领域门禁要求不同 worker/run/sandbox，正式跨品牌要求由原 checker 的 Claude 复现、Codex 作者/继承及三个不同 native UUID 核验（`local_assets/research.py:69`；`tests/integration/check_research_live.py:129`）。P 不能用三个同品牌逻辑 worker 替代此标准。
- 前置依赖：A 原进程树回收返修冻结；P 正式安装入口/权限/身份与档案契约冻结；主控明确 Claude 认证身份选择，保留原生工具/认证/会话。旧 401 不授权自动切换 provider/account/model。B 本次不启动模型、沙箱、Hub，不改 auth。

## 标识与信任边界

以下 `S` 表示作者原 `asset_id`，`C` 表示继承子 `candidate_asset_id`，`ta/tr/ti` 分别为各角色**实际 claim 返回的当前 token**。这些是说明符号，不是可预填的结果。

| 字段 | 实际来源和用途 | 门槛 / 引用 |
| --- | --- | --- |
| canonicalAttemptId | 工具字段实际叫 `attempt_id`，来自 `lease_task(action=claim)`；形状 `task_id + agent(role,instance) + attempt` | 作者 Candidate.attempt 必须完整照用当前返回值；不能用 token 数字或 native UUID 代替（service `:74`、`:158`） |
| token / fencing_token | claim/renew 返回的租约；写工具传 `token`，报告/context 用 `fencing_token` | 绑定宿主 worker、scope、capability、当前 owner/token、TTL；耗时操作后再检查，提交/晋级/应用短事务 fencing（service `:84`、`:176`、`:282`、`:313`、`:377`） |
| native session_id / runtime | 正式原生启动与事件归档 | 与领域 AgentId/worker 分别保留；作者实际中断后同 UUID，复现/继承各独立 UUID，品牌由 checker 核验（checker `:106`、`:129`） |
| source_swarm_id/source_fencing_token/source_attempt | ResearchObservation 由权威 research_execution 和 task_attempts 推导 | 原执行身份不可改写；当前 token 只授权新观察写入；跨 token 仅允许已确认 original 恢复，不能恢复 unknown（service `:191`、`:279`） |
| run_id / sandbox_id | run_id 由宿主生成，sandbox_id 来自 C 持久结果 | 必须属于当前 task/worker 的账本审计；不同角色独立 fresh sandbox，不接受任意外部归档（service `:122`、`:140`） |
| report_id | verify 返回科学观察；validate_files 返回文件报告 | approve/apply 用**文件报告**的 report_id，不能用科学报告 ID；报告绑定 candidate/attempt/base/policy/env/TTL 且 passed（promote `:15`） |
| S / C | submit 返回 S；inherit 返回 C | S 保留作者原 Candidate.attempt；C 使用继承者本次 canonical Attempt，不能把 S 改成复现者身份（consume `:44`） |
| execution_id | `inherit_experience` 返回 **context.execution_id** | ConsumptionExecution 顶层没有 execution_id 字段；apply 时提取此值。此执行表示原资产字节复用，不是 sandbox run_id（models `:111`、`:129`） |
| target bytes / result_id | apply 回调落地后 TaskLedger.completed/effect_applied 和实际目标文件 | receipt 要求 owner/token/result/context/S/C/目标 bytes 完整一致，检索计数或模型自评不能生成 receipt（consume `:95`） |

公开 request 只读返回预注册 plan 和 allocation=on_execute；不会创建环境。run 才创建一次实验，并在调用前记录 execution_unconfirmed；长外部调用不持 SQLite 写锁。仅明确终态及 effect_state known/confirmed 清除 hold；unknown 禁止自动重放、释放后换人重跑或伪造确认（service `:116`、`:122`；`swarm/task_ledger.py:373`）。result 操作传 task_id/run_id，不传 token；写操作必须当前 token（server `:54`）。

## 实际公开工具顺序

| 角色与步骤 | 工具和必需字段 | 返回与下一步 | 信任门槛 / 源码 |
| --- | --- | --- | --- |
| 作者发现/上下文/认领 | discover_tasks；project_context(author)；lease_task(claim,author,ttl_seconds)，然后 renew(author,ta) | 读取 acceptance、payload.candidate_template、base_revision、attempt_id、token | research.author 资格、scope、依赖、租约；service `:49`、`:66`、`:74` |
| 中断/接续 | 实验前已 claim/renew 后，仅取消自有原生进程；等实际 TTL；同 UUID 恢复 | 旧 token renew 拒绝；原 canonical Attempt + 合法 candidate_template 的 submit 拒绝；随后新 claim | 两个真实旧持有者拒绝必须在 fresh claim 前，不能拿结构错误冒充 stale rejection；checker `:171` |
| 作者唯一实验 | research_experiment(request,author,ta)；run(author,ta)，必要时 result(author,run_id) | 实际 ra 和持久结果；request 不算实验 | 预注册代码/数据/env/seed/判据；每 task 至多 ONE run；service `:110`、`:122` |
| 原候选与科学观察 | research_candidate(submit,author,ta,candidate=template+attempt_id)；verify_research(author,ta,S,ra,purpose=original) | S quarantine；科学观察 report，不能自报 metric | claim 完全匹配 acceptance；可信 evaluator 从归档重算，代码 after 必须等于实际执行代码；service `:158`、`:222` |
| 作者证据完成 | complete_research_task(author,ta,S,ra) | task completed、effect_applied=false、result.asset_id=S、approved=false | 此完成释放依赖/租约 scope，S 仍 quarantine；**不算批准/采用**；service `:286` |
| 复现者发现/认领 | discover/context(replication)；claim→tr/attempt_id；renew；context.dependency_results.author.result.asset_id | 取得原 S，不重新 submit、不覆盖作者 Attempt | 不同 worker + Claude nativebrand + UUID；service `:66`、checker `:129` |
| 独立复现 | request/run(replication,tr)→rr；verify_research(replication,tr,S,rr,purpose=reproduction) | 对 S 的复现报告；不是 child | 独立 sandbox/run、相同全科学计划（仅 role/local_path 可不同）；live+succeeded+passed+known；research `:45` |
| 原候选文件验证/批准 | research_candidate(validate_files,replication,tr,asset_id=S)→文件 report_id；approve_candidate(replication,tr,S,该文件 report_id) | S local approved；目标尚未改写 | 固定 literal-files、静态语法/SDK/范围/preimage/env/报告 TTL；original+独立复现科学准入；promote `:15`、`:55` |
| 复现应用并完成 | apply_candidate(replication,tr,S,该文件 report_id)，不传 execution_id | result_id；stage=applied、adopted=false；task.result.candidate_asset_id=S，effect_applied=true | 写 science/experiment.py 等于原 after bytes；不调用 complete_research_task 替代 apply；service `:377` |
| 第三角色主动检索 | discover/context(inheritance)；claim→ti；renew；search_evidence(query=实际经验词) | stage=retrieved/adopted=false，核对返回 S 与 dependency_results | search 可以返回 quarantine；必须核验 approved 和科学报告，检索本身无 adoption；service `:326`；原 checker `:169` |
| ONE fresh 本地再验证 | request/run(inheritance,ti)→ri；verify_research(inheritance,ti,S,ri,purpose=inheritance) | 观察写在 **S**，不是尚未存在的 C | 相同条件/完整计划、当前 task/worker/token、live known，条件不匹配/缺产物/科学失败不能继承；research `:36`、`:84` |
| 原链生成子 candidate | inherit_experience(inheritance,ti,S,path_map={science/experiment.py:science/reused.py},preimages={science/reused.py:null},base_revision=payload.base_revision) | ConsumptionExecution：asset_id=S、context.execution_id、candidate_asset_id=C、candidate | 当前 HEAD 锚点匹配；宿主 scope snapshot 纳入先前真实 apply；原字节产生 child.after；service `:349`；consume `:44` |
| 子文件验证/批准 | research_candidate(validate_files,inheritance,ti,asset_id=C)→新文件 report_id；approve_candidate(inheritance,ti,C,新文件 report_id) | C approved；此时仍未 adopted | 新 child 重新静态/文件验证；parent 科学准入和当前 inheritance 观察链继续检查；research `:58` |
| 子实际应用/采用/完成 | apply_candidate(inheritance,ti,C,新文件 report_id,execution_id=返回的context.execution_id) | task completed/effect_applied=true；result.execution_id、consumed_asset_ids=[S]、input_context、candidate_asset_id=C；返回 adoption | AdoptionReceipt.asset_id=S、candidate_asset_id=C、context 与 ConsumptionExecution 相等、result_id 相等，science/reused.py 真实 bytes 校验；service `:390`；consume `:95` |

release/handoff 是公开租约动作，均带当前 token；handoff 的 next_worker_id 只表示交接目标，不改变调用者宿主身份（server `:28`）。该正式正向案例没有必要用它们替代各角色的主动 claim 或 completed。

科学通过、执行通过、独立复现、条件可继承、争议/反例分别保留。failed reproduction 使经验 disputed，failed counterexample 使其 invalidated，缺文件/基础设施失败保持 not_evaluated，不能把 exit0 等同 passed（research `:45`；service `:240`）。科学 normalized plan 保留代码/data身份、environment、parameters、seed、资源/模式/criteria；不偷偷改 reverse（research `:20`）。此路径使用既有 ConsumptionExecution/AdoptionReceipt；原 checker 明确不生成 metabolism UseRecord（checker `:287`），没有授权手造另一套 adoption。

## 旧唯一案例的只读现状与续接结论

归档根：`C:/Users/DW/orca/workspaces/Morphogenesis/morph-research-integration-0930-state/research-host-7d04`。本次读取 JSON 和 SQLite `mode=ro`，专项核验另启 `query_only=ON`；不调用会初始化表的领域构造器、不写旧 DB、不 claim、不运行 checker.main。

| 项目 | 实际读取值 |
| --- | --- |
| swarm / 上限 | nist-i-0930-7d04；started_at=1790782122.151175；runtime=3600；max_attempts_per_task=3；到期 2026-09-30T16:28:42.151175Z |
| 作者身份/状态 | worker=author、builder/0、UUID=01a0f2ee-ae2a-7ce3-9470-e485066fb8d2；completed、attempts=3/token=3、effect_applied=0、无 unconfirmed hold |
| 原来源 | S=sha256:ddd070985e6ee0d895d0c8a3270a4688208c4d4051907a4c79711b40c97b90f5；原 source Attempt2/token2；当前 observation token3；result_id=93ed6e923ec64096ad243585c908b915、approved=false |
| 唯一实验 | run=a79578f21ff148c6a86708bddd9f611b；sandbox=14580dc2-65ee-4c0c-b724-9e70fb4f04dd；succeeded/scientific passed/remote_effect known/cleanup destroyed；usage/cost=null |
| 原失败 | 文件 report a9b79ce344fe4a24ac8547efcd69c320，passed=false、reasons=[TimeoutExpired]；保留原 item18 失败与报告，不能删除或改绿 |
| 作者原生预算 | interrupt+interrupt-recovery+resume+local-completion 累计602.586241秒、36工具，未超过900/64；native outcome.remote_effect 仍 unknown，与实验 known 分开 |
| 复现 | Claude UUID=5c787eb6-602b-4e03-9fea-313af2b5c826；401 failed、0工具；ledger available、attempts/token=0，未 claim |
| 第三角色 | inheritance-observation 不存在；ledger available、attempts/token=0；NOT_RUN |
| 资产链 | assets=1、静态 reports=1、research_reports=1；approvals=0、consumptions=0、adoptions=0 |

旧 Claude 观察归档曾记 tokens=0/cost=0.0；这只是旧解析输出，不能当实际账单零值。原文不改写；冻结源码的后续错误回放已输出 null（集成验收记录 `docs/RESEARCH_INTEGRATION_ACCEPTANCE_0930.md:174`）。本次不重新认证/请求来消除 unknown。

**不能通过现有公开工具在旧窗口完成全原 checker。** 作者 known 结果此前已合法以 source2/current3 完成本地续接，checker 保留了这条恢复分支及原失败报告比较（checker `:202`、`:219`）。但复现者现在没有有效 lease；任何新 claim 首先经过 `_check_runtime` 并因原 started_at+3600 到期抛 run_runtime_limit（ledger `:141`、`:291`）。作者已 completed/attempts3，不再 claim；也不存在公开跨 swarm 导入 task_attempts/research_execution/confirmation/原生事件的接口。复制旧作者结果到新 ledger 会破坏信任与完整 checker 的统一 swarm/原来源/当前 Attempt/唯一实验核验。

只读已有 known 作者证据仍可用于独立科学检查、保留原失败和恢复证据；不能以作者局部检查替代完整 checker。完整 checker 要读取继承观察/原生事件，并要求三角色 completed、三份单次实验、不同 run/sandbox、三个 native UUID、实际 source/child bytes 和唯一 receipt（checker `:101`、`:162`、`:192`、`:211`、`:259`、`:265`）。旧缺失不能标 passed。

可行建议：在 A/P 代码与正式安装入口冻结、主控解决原生认证选择后，由 I 执行**明确命名的新完整正式案例**，建议名字 `research-formal-1001-01`（仅建议；本次未创建）。使用不存在的独立 sibling project/state 和新 swarm_id，通过现有可信初始化入口准备相同 NumAcc4 三任务/原条件，先保存预算/版本/权限/身份/启动事实，再真实执行三角色全链。新窗口重新做作者实验前中断、真实 TTL、同 UUID 恢复及两个合法 stale 拒绝；每角色累计900秒/64工具、每任务ONE实验、run runtime3600/attempts3保持原上限；不能重置旧 clock 或把旧 archive 拼接为新通过。新案例的一次作者实验是明确新案例执行，绝不是旧 unknown 的自动重试。旧科学 known/原 unknown 接口实验及全部失败原封保留。

## 原 checker 的冻结验收清单

| 原要求 | file:line | P/I 应提供的实际事实 |
| --- | --- | --- |
| 三宿主身份、一 swarm、state 项目外 | checker `:86` | 各 HostConfig 与每 phase host_binding 对齐 |
| 原生中断、同 UUID、实验前无 unconfirmed | checker `:106` | 自有进程退出归档、旧 lease、原 native events，不伪造取消 |
| 三 UUID/Claude复现/Codex作者继承/累计900与64 | checker `:129` | 原生 session/event/outcome 与 phase wall；unknown usage/cost 原样保留 |
| 精确正式权限、仅11工具、主动claim/renew/search | checker `:145`、`:162` | P CLI 正式 request/argv；I不注入放宽参数 |
| 两个合法 stale 拒绝在claim之前 | checker `:171` | 原旧 canonical candidate/template 和真实拒绝文本 |
| 三任务completed及 effect、原 Candidate身份/旧失败报告 | checker `:192`、`:202` | 权威 ledger/result、原candidate及未改的失败报告 |
| 每task ONE execution、known/live/passed/destroyed、source字段 | checker `:211` | C归档+账本审计；原 executed bytes 与 S.after 相等；usage/cost=null |
| Fraction独立重算完整1001 residual，三独立run/sandbox | checker `:55`、`:259` | 原 metrics/data/判据；不改任一容差/断言 |
| 唯一adoption与source/child/context/result/目标bytes一致 | checker `:265` | 现有receipt/ConsumptionExecution+真实science/experiment.py、science/reused.py |

本轨未发现需要本阶段改领域源码的已证实新缺口；nativebrand 由 checker 审核、主动 search 由正式角色行为提供、context.execution_id 字段位置属于产品接线注意点。若正式链出现真实领域失败，保留原失败、具体字段和 file:line Handoff 主控，再授权原 B ownership 修复；不放宽 fence、文件门禁、科学条件、时限或 checker。

## 本次验证及限制

- 原工作树 clean 后 `git merge --ff-only c45888f64c1cec60e5f9df45677b6547c4527cac` 成功。
- 标准库只读专项：从原 checker AST 提取**原样** load/events/native_calls/fraction_check（不执行 main 或 DB 构造器），重算旧 known 作者1001数据/residual；均通过，exact mean=50000001/5、sample variance=1/100。核验原 resume 两个真实 stale 拒绝、同作者 UUID、local-completion 不含新实验/发布/批准/应用，以及旧 DB 原限额和过期状态，exit0。
- 此专项使用既有可信原生/沙箱归档；model_calls=0、sandbox_calls=0。完整 `python tests/integration/check_research_live.py --state <正式新案例>` **本次未执行**，其原文件和断言一行未改；没有几十项测试或全量门禁重复。
- 两文档提交后用 `git diff --check`、引用行定位与授权路径检查；结果及完整交付 SHA/远端一致状态由本轨报告和 Handoff 回传。
- 真实剩余：A/P冻结、原生认证决策、I正式新案例和全原 checker；Hub/EvoMap/第二案例抽离均未执行。
