# 2026-09-29 三轨增量独立验收 D

**独立验收工作已完成；A 测试增量、B nullable 修复、C 只读 replay 展示分别通过下列限定门禁。FC 整体仍 BLOCKED：cost_state 生产语义检查真实 exit 1，且正式 FC-E、真人 H1、Schema H3 未闭合。不能称五不变量已经全部验收、FC 已冻结或生产稳定。** 本报告由 Codex 产出，不冒充 deepseek FC-E 或人类签字。

已读取当前 AGENTS、QWEN、PLAN、FC_ACCEPTANCE、现行 source README 及指定两份 0929 算法/发布基线审查。历史 698 项、昨夜 Schema 11/12、历史真实模型运行均保持原范围；本轮没有把不同分支、历史运行或 Owner 自验合算为新联合候选通过。证据脚本、缓存、隔离导出均在本树 ignored `L=.runtime/acceptance-0929/`；唯一 tracked 写入是本报告，未修 Owner 实现。

## 精确版本、远端与范围

| 别名 | 分支 / 不可变 SHA | 本轮核实 |
|---|---|---|
| F | FC 原生产候选 `73e64cc70116ac658d85591d082c0684a4952c99` | A 的父基线；生产语义、预算及 breaker 引用均绑定此 SHA |
| A | `morph-fc-tests-0929` / `3d8bb856efadbb1bee4a69bc37c56d3ef4d24cfd` | 测试阶段 `f4779d45a1b1417ffa6bce37708e9a68d46cf4e5`；最终仅再加 full/strict 日志和报告，测试/生产差异为空 |
| B | `morph-schema-closeout-0929` / `318dd4f26f27cda25e4278772bcce6b508023c26` | 基 `73798cd6f05210f2bd9b1eebfd6f9f0dd6e842db`；修复提交 `188fae46de4f3d2fe4943461a62a9626caa5325d`，最终 Schema 与该修复相同 |
| C | `morph-readonly-app-0929` / `621f588988899bdbc7c7a83e893369c4145d89b3` | 基 `2957b408ce922369a595a8acd43a882eb85897d3`；产品 `8c57c4964fbf78b90d7232d3644975dab277d277`，最终仅加报告 |

`origin=https://github.com/songconmaisaix31-design/Morphogenesis`。三轨各在交付时 HEAD/remote 一致、工作区 clean，已实际 `git ls-remote` 核实。A 仅两个 failure_chain 测试与 `fc-tests-0929-*` 共 11 文件；B 初交付 17 文件均在计划/台账/Schema/`schema-0929-*` 范围；C 恰为 Backend.jsx、backend.css、两个 finals-shell bundle、check_adoption_trace.cjs、application-readonly-0929.md 六文件。各最终提交含 `Swarm-Agent: codex`。

B 在本轮后段出现 TASKS/PLAN 与新 `docs/FC_CLOSEOUT_0929.md` WIP，已立即上报，主控 `msg_cfd04c916ce1` 确认属于新任务 `task_507418789086 / ctx_bf1fdfa6a61e` 的授权审批索引。**本报告仍锁 B=318dd4f2，不将后续 WIP 计入验收，也不误判为原提交越权。** 新文档候选由集成人核对 Schema 字节未变。原 PLAN 旧前缀、TASKS 标题及旧正文逐字保留；B 今日段明确 A cost_state 未解、C 是 Owner replay 自验、Schema candidate/H3 未签，未发现原 B 台账将失败误报通过。检查时状态与只读关系原件见 `L/lineage.json`、`lineage.log`。

## C：限定 replay contract_local 通过

独立读取 C 完整 Owner 报告、六文件 diff 和原始 T5/build/browser 日志。源码仅增加原生 details/summary/dl 采用明细及六条必要 CSS，直接消费既有 dashboard.adoptions；无新增后端、网络写入、控制路径或依赖。React 18.3.1、Vite 5.4.21、plugin-react 4.7.0 的现成 package metadata 均为 MIT；锁文件未变。既有 Linear 用户包来源声明沿用，原包版本/再分发许可未核实，不能重新宣称其开源授权。

独立命令 `P_C -B L/check_c.py` 中运行 T5 与 Vite：**53 passed / exit 0**；**49 modules / exit 0**。Vite 使用 C 的真实源码与原配置，仅把构建输出指向 L/重建目录、依赖 import 指向现成只读目录，重建 JS **222721 bytes**、CSS **69245 bytes** 与 C 工作树及不可变 Git blob 均逐字节相同。运行字体 URL 提示是原 build 提示，无本轮新增依赖。`P_C=C:/Users/DW/orca/Morphogenesis/.venv/Scripts/python.exe`；实际导入 viz.adapter 明确来自 C 树。

独立浏览器脚本是 `L/check_c.cjs`，未直接重跑 Owner 的 44 项脚本来替代独立验收。Python 原 DashboardHandler 在 loopback 临时端口提供真实 `load_rehearsal(..., replay=True)`；HTTP JSON 与原类型 loader 完整相等，RehearsalDocument/UseRecord 通过原模型校验，浏览器执行 C 的已提交 bundle。逐字段核对三份不同历史运行的记录如下；每份原件 current 只有一条采用，未复制或拼成伪多记录 replay。

| 历史 rehearsal ID（run/task/Gene 均逐字段读回） | agent / attempt / version | used_at | HTTP 与 DOM 来源 |
|---|---|---|---|
| `rehearsal-85ff3bf872d941aa9eade0ddc92cd485` | builder#1 / 0 / 1 | 1790194396.5110512 | replay |
| `rehearsal-30227ce2036e4048900c42c2ee25631d` | builder#1 / 0 / 1 | 1790194005.8515778 | replay |
| `rehearsal-f0fbafb37b28448ca4f4eea6a4de1840` | builder#1 / 0 / 1 | 1790064792.3217974 | replay |

三个实际 run_id 分别为上述 ID 加 `-recovery`，task_id 为 `recovery-` 加 ID，gene_id 为 `verified-` 加 ID 再加 `-repair`；这些是从 API 读回的值，不是页面猜测。每条独立比较 run、task、agent、attempt、gene、version、asset、UTC time/datetime、provenance 九项 DOM 值；源原文和 API 保存在 `L/c-sources.json`、`c-expected-{0,1,2}.json`。原件路径分别在 Temp 的 `morph-sol-20260924-e27e2dc198664413a2a8333b236bd123`、`morph-review-20260924-768b91a264cf4397ab1174c11af47cc5`、`morph-live4-98b36399c0324192b5af81f8077bc11d/morph-rehearsal-86e5351d49fe49a1b60ba0a4bb4c4e4e` 下，文件名均 rehearsal.json。三份原件检查前后字节未改；原件声明 live，本轮只证明历史 replay 的展示，不重新认证历史远端执行。

真实记录经 Enter 展开、Space 关闭，焦点轮廓、命名 region、语义 time、375/1366 宽度下末字段可滚动到达与无横向溢出均通过。随后明确标 mock 的独立反例核对同 Gene 不同 run/attempt（0 与 17）不合并，version/instance/epoch 的 0 保留；null/缺失身份显示未知；use_count/injected_count 即便为 99 也不会凭空产生 UseRecord；缺失列表与空列表文字不同。三组最终浏览器命令各 **exit 0**，没有外部或写请求，interface_live/task_live 始终 not_run。服务在 finally shutdown/close，未留下本轮 listener。

**保留首轮失败：** 额外越契约输入 `adoptions=[...,null,...]` 触发原谱系图 `Cannot read properties of null (reading 'ref')`，浏览器总检查 **exit 1**，原件 `L/c-null-element.json/.log`、`c-run-null-element.log`。C 新明细仍正确呈现未知，但旧 app.js 不能容忍整个 null 记录；`C:viz/static/app.js:297` 与 `C:viz/static/app.js:306` 相对 2957b408 未变。主控确认按既有非法输入限制记账；未修写权外模块，也未把该样本说成绿。后续只对合法历史记录及 ref/attempt 对象中的缺字段/null 做已授权检查，命令 `P_C -B L/check_c.py --browser-only` exit 0；不是同一失败用例修复通过。

Owner 证据复用：`C:artifacts/ai-evidence/application-readonly-0929.md` 的 T5 53、build 49、浏览器 44 及旧页面回归 72/0，已核对其 `.runtime/application-readonly-0929/` 原 log/summary；72 项未重复执行。C 结论限 replay contract_local；新模型、Hub、付费调用、生产部署均 NOT_RUN。

## A：测试敏感性通过，生产 cost_state 仍失败

新用例进入真实 Worker._process；Mock 只替换 Executor 边界，成功候选仍调用原 FixtureExecutor。SQLite reservation/task、FaultObservationStore、SharedBreaker、租约、验证和最终文件是实际机制。side_effect 只生成/记录事实或施加真实 handoff，关键断言在 _process 返回后；没有 try 吞断言或 mock Worker/guard 换绿。调用数还和发送前 pending 行、持久 request_id、提交结果交叉检查。

| 原场景 | 独立确认的新覆盖/保留范围 |
|---|---|
| 原 400/403/429 自建响应断言 | `A:tests/swarm/test_failure_chain_runtime.py:157-195` 真实拒绝→切换→提交；具体分类仍在未修改的 `F:tests/orchestration/test_provider_adapters.py:150-180` 的 interpret 断言 |
| 原有效进程内 single_request | `F:tests/swarm/test_failure_chain_boundaries.py:562-580` 虽被替换，未修改的 `F:tests/orchestration/test_integration.py:18-46` 仍真实执行 _request→single_request、检查分类和 hash；429/ReadTimeout 保留于同文件 49/87 起的用例 |
| 原“子进程”只构造 Reply | 不再作为证明；真实 mock 子进程在未修改的 `F:tests/orchestration/test_integration.py:104-232`，纳入 Owner 699 全量，不冒充 live 子进程 |
| 累计容量、全局/任务次数与 unknown | `A:tests/swarm/test_failure_chain_boundaries.py:16-128`：unknown 后不续发、重启保留、六种预算边界两次真实调用而第三次为 0，hold+admitted=0.4；合法未知字段不填零 |
| 有界退出与失租 | `A:tests/swarm/test_failure_chain_boundaries.py:130-185`：1/2/4 候选单遍历、成功候选后真 handoff 拒交且最终文件原字节；`A:tests/swarm/test_failure_chain_runtime.py:231-255` 检查全 suspended 零预留/零发送 |
| 原 direct guard / identity / decide | decide、identity/ValidationError 保留；`A:tests/swarm/test_failure_chain_runtime.py:198-228` 由前 Worker 的 observation 驱动后 Worker 真实路由，补充行为敏感性 |

原 Hypothesis 随机 ledger 循环改为明确边界参数化，不能称随机覆盖范围保持或全部并发组合穷尽；有效传输用例有保留映射，非纯删测试。没有另加长期运行或自动结算原型门槛。

使用 `P_A=C:/Users/DW/orca/workspaces/Morphogenesis/morph-fc-integration-0927/.venv/Scripts/python.exe`，在 `L/a-src` 导出 f4779d45；Node 只读 junction 位于 L/a-src/node_modules，指向现成 integration 依赖，无安装。所有临时文件/cache/TEMP 在 L。最终导出使用 `git -c core.autocrlf=false archive --format=zip f4779d45a1b1417ffa6bce37708e9a68d46cf4e5`；源码逐字节对 Git blob，未改全局配置。

| 独立门禁 | 完整调用与真实结果 |
|---|---|
| Focused | 在 L/a-src：`P_A -B -m pytest -q tests/swarm/test_failure_chain_boundaries.py tests/swarm/test_failure_chain_runtime.py -o cache_dir=L/a-cache --basetemp L/a-focused`；**20 passed，65.25s，exit 0**；L/a-focused.log/.exit |
| 语义 mutation | `P_A -B -m pytest -q tests/swarm/test_failure_chain_runtime.py::test_worker_observation_suspends_provider_and_routes_later_candidate -o cache_dir=L/a-cache --basetemp L/a-mutation`；**1 failed，7.81s，exit 1**，明确 `assert 1 == 0` / executor.execute.call_count；L/a-mutation.log/.json |
| 原字节恢复 | 同目标、basetemp=L/a-restored；**1 passed，5.90s，exit 0**；L/a-restored.log/.exit；finally 恢复后 breaker bytes==Git blob，本工作树生产/测试 diff 为空 |
| 另行 cost_state | `P_A -B L/check_cost.py`；**exit 1**，L/a-cost.log/.json/.exit。真实 Worker 调用 `[1,0]`、ledger=uncertain/unknown，fact.cost_state=settled，断言应为 unknown 失败 |

mutation 仅将 F breaker 第 212 行 `if _suspension_required(params):` 改成 `if False and _suspension_required(params):`，没有语法/依赖失败混入红项。本轮恢复的 Git LF bytes SHA256 为 `07d76f698d7212248a09ac08d5e57bb27dbe646d4f9fca25695084cbb5f2a66f`；Owner CRLF 工作文件 hash 不同不能误作语义差异。驱动脚本 `P_A -B L/check_a.py` 最终 exit 0 表示绿色基线→有效语义红→恢复绿的流程完成，绝非把 mutation 用例本身写成通过。

**成本缺陷仍 OPEN/BLOCKED：** 无价格但合法本地合成 usage=2 时，budget.py 正确保留 reserved_usd=0.2、tokens=2、estimate/admitted=null；后继请求未发生，unknown hold 未释放。F worker_loop.py 第 839 行却仅根据 result.uncertain 写 cost_state，故 durable FaultObservation 标 settled。这是观察元数据失真，不是已发生预算释放/超支的证据；不授权 D 修生产。A focused 20 通过与此额外语义 exit 1 分开记。

复用 A 已提交原日志：`A:artifacts/ai-evidence/fc-tests-0929-pytest-full.log` 为 **699 passed、2 warnings、450.96s**，Owner 同目录 `.runtime/fc-tests-0929/pytest-full.exit` 实值 0；`A:artifacts/ai-evidence/fc-tests-0929-typecheck.log:1` 为 strict **87** 文件无错，Owner 报告记录真实 exit 0。已核对最终相对 f4779d45 测试/生产未变，不重跑全仓。SDK 复验 1.14.0/exit0 为 Owner 报告证据，D 未重跑；不把报告取值包装为 D 独立执行。新 build/wheel NOT_RUN，后续组合候选需跑适用联合门禁。

预算结论仍有边界：新 request_id 的 confirmed rejection 仅在其他容量/次数允许时不被旧 uncertain 的 pending 互斥自锁；同一 hold 不同时计入 admitted 与 reserved。unknown-effect 不因此获准续发；无 uncertain→settled 晚到结算入口，长期占用需人工停止/恢复决策；unbounded allowance 不等于上游账单硬上限。缺新结算接口作为已知限制保留，不追加本轮实现任务。

## B：nullable 修复通过，候选与 H3 保留

独立直接从 B Git blob 提取唯一 JSON fence，Draft202012Validator 校验；以 task/blocked 的 replay envelope 和 count×audit 交叉组合构造 **44 例**，没有导入 Owner 的 validate.py 或复制其矩阵。缺失/null 四组合通过；0/7 缺审计、audit 对象缺 count、null count 配对象、partial 0、布尔/负数/小数/字符串/集合 count、重复/空 ID、空 evidence、额外字段等按原规则拒绝；replay 来源、drill、event payload、时间和状态等非 audit 反例保留。

`P_A -B L/check_b.py --before`：**43/44，exit 1**，唯一失败仍 count=null/audit 缺失，路径 allOf/1/then/required。`P_A -B L/check_b.py`：**44/44，exit 0**。原件 L/b-before.log/.json/.exit 与 b-after.log/.json/.exit。机械比较整个解析 Schema 仅允许删除 allOf[1].then.required，其他结构完全相同；FaultObservation 14 字段导出与 F 原模块一致，实际导入四个模块原字节对 F Git blob。

额外反例 count=7+空 IDs、count=7+单 ID 在旧/新 Schema 均接受。它们明确违反计数业务语义，但属于文档已声明的消费侧 cardinality/scope/证据回溯责任，生产消费者尚未实现；不是本次 nullable 删除产生的回退，也不能称 Schema 自动验证全部审计事实。可选字段无 default、不被校验器补 0；版本仍 1.0.0 candidate，optional 新增 minor、optional→required 为 major/2.0.0；H3 待真人。

## 机械引用核对

下列短引文均在指定 Git blob 的行号内逐字匹配；报告其他带别名前缀的行范围也检查存在。`P_A -B L/check_references.py` 最终 **25 处行范围、13 条短引文、B TASKS 的 10 段预算原文全部通过，exit 0**，见 L/references.log/.json；任何更正仅改本报告，没有改源代码。

| 锚点 | 原文短引文 | 本次解读 |
|---|---|---|
| `C:viz/frontend/src/backend/Backend.jsx:21` | `const adoptionValue = value => value == null || value === '' ? '未知' : String(value);` | 缺失与 0 区分 |
| `C:viz/frontend/src/backend/Backend.jsx:31` | `// React keys only: retain every supplied record, including repeated uses.` | 独立 DOM 已确认不合并不同 attempt |
| `A:tests/swarm/test_failure_chain_runtime.py:124` | `assert executor.execute.call_count == expected` | mutation 红由执行次数导致 |
| `F:swarm/breaker.py:212` | `if _suspension_required(params):` | 本轮仅此语义行临时变异 |
| `F:swarm/worker_loop.py:839` | `cost_state: Literal["settled", "unknown"] = "unknown" if result.uncertain else "settled"` | 合法 usage 不等于已知价格/费用 |
| `F:swarm/budget.py:178-180` | `request_id=? OR (task_id=? AND status='pending')` | pending 互斥的有限结论 |
| `F:swarm/budget.py:82` | `holds = sum(float(row["reserved_usd"]) for row in rows if row["status"] != "settled")` | unknown 持续占 hold |
| `F:swarm/budget.py:253-257` | `if row["status"] != "pending":` | 非 pending 没有晚到结算更新 |
| `B:docs/FC_LOG_SCHEMA_DRAFT_0928.md:1613-1632` | `"type": "integer"` | 数值仍要求审计对象 |
| `B:docs/FC_LOG_SCHEMA_DRAFT_0928.md:1645-1651` | `"const": null` | 移除 required 后仍拒 null count 配对象 |
| `B:docs/FC_LOG_SCHEMA_DRAFT_0928.md:1653-1673` | `"audit_confirmed_issue_events"` | 孤立 audit 仍被拒绝 |
| `B:docs/FC_LOG_SCHEMA_DRAFT_0928.md:1686-1702` | `"maxItems": 0` | 零值不能配问题 ID |
| `B:docs/FC_LOG_SCHEMA_DRAFT_0928.md:47-49` | `消费侧还需检查 count == unique(confirmed_issue_ids) 数量，issue 属于声明 scope，` | 未接线的既有责任 |

## 只读集成建议、未执行与失败保留

只读 `git merge-base` / `git rev-list --left-right --count` / legacy `git merge-tree <base> <left> <right>`（非 write-tree）实际结果：A/B 共同基为 **f159f1e698101a48579822a6ad0ee3e13e412bcd**，两侧 20/21 提交、相对共同基变更路径交集为空，预览无冲突标记。**可以交集成人形成 FC 隔离候选**；这只是文本关系，尚未生成/验证联合运行版本。

C 与 A/B 的共同基为 **605cf48b8b05baf86fd68e5d63f495ba3e5d7e69**；A/C 为 81/10，B/C 为 82/10。Backend.jsx 与两个 finals-shell bundle 双侧修改，merge-tree 预览确有冲突；B/C 另有 PLAN 双侧改动。**建议 C 保留第一代只读应用候选，与 FC A/B 分开整合。** 不能用覆盖 bundle 或少量胶水名义强行合并架构；未来如需统一由主控明确范围、领域 Owner 处理并重建。原件 L/merge-tree-AB.txt、AC.txt、BC.txt；未写 index/工作树合并、未生成 merge commit/tag。

保留取证环境失败：C 初次 helper 路径错误 ModuleNotFoundError/exit1，修正自身脚本后才进入门禁；A 默认 git archive 因 core.autocrlf 导致 CRLF，准备检查和 mutation 前置字节检查各失败一次，及时上报，主控认可仅命令局部 false 导出继续；二者绝不算 mutation 杀死。CRLF 导出 focused 20/exit0 仅作环境先验，最终正式结果来自精确 LF blob 导出。关系 helper 一次错误要求“TASKS 整份连续包含”而失败，实际新增段位于标题下，后按保留标题/旧正文逐字核实；后续 clean 检查又因 B 新授权 WIP 拒绝，已分别解释，未隐去。报告引用检查先后发现本报告末行范围 258 超出文件 255 行、消费者引文起点应为 47 而非 44，两次 exit1 已上报，仅更正本报告。Owner 早期 SDK 缺 ajv、初始化 limits、B CRLF 取证失败仍在各 Owner 原报告中。

**NOT_RUN：** D 新全仓 pytest/strict、A 新 build/wheel/SDK；联合 A+B 组合门禁；C 新模型/Hub/生产调用、真实 T2 导出专项场景；FC-E 正式 deepseek v2、H1/H3 真人审批、T9 生产接线、T10 演练、三连 smoke、长期运行、生产 merge/tag/部署。无安装、锁变更、付费调用或自动释放 unknown。cost_state 生产修复待队长/领域 Owner，D 未代修。

交付分支 `morph-closeout-acceptance-0929`，基 f4779d45；仅本报告 commit+push，trailer `Swarm-Agent: codex`。最终报告提交 SHA 见交付回执；本文件不自引用尚未产生的提交 SHA。验收报告完成不解除上述冻结门禁。
