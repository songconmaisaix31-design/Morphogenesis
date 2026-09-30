# B 原 Owner 独立审核正式产品（1001）

结论：**冻结产品的静态契约和本次有限 contract_local 核验未发现必须返修的阻塞；prepared，不能代签 interface_live/task_live。** 无授权外代码修改，无模型/API/沙箱/Hub/EvoMap 调用。P 产品返修仍属于原 P Owner，领域返修先经主控授权原领域 Owner。

审核对象：产品 `9dd4addf4a141a42040574fef3b614ca62b22a57`（Morphogenesis-Research / research-product-1001）；不可变核心依赖 `cbc4dede782eb79b9c007520d96d7958857da0af`。B 保留原 worktree/branch，从 clean `a060564dee6d7fa790b64583fd76301e95eadb54` 开始。读取当前 AGENTS、B 的 FORMAL_CLOSURE_HANDOFF_1001 后，对 P 用指定 SHA 的 git show/git archive 审核，不依赖其随后修改的工作树。

以下 P 引用相对冻结产品根，C 引用相对 CBC 核心根；均为 file:line。CBC 对 c458 的 `swarm/research/**`、`local_assets/**`、`swarm/task_ledger.py` diff 为空，原领域门槛未变化。原完整 checker 在 CBC 和 c458 都是 Git blob **39948d9615bce07b40b96eeaf5dfb263b993c6d3**，断言一行未改。

## 薄 Handoff 与精确定位

主控薄 Handoff `msg_46378c646e94`，I 当前 dispatch 薄 Handoff `msg_97d1c07799aa`；先报当前无已证实静态必改阻塞，再完成独立核验。初次薄消息中个别定位有误，以下为复核后的精确引用，不沿用错误定位：console entry在pyproject.toml:18，inherit 返回字段引用在 workflow.py:37，auth context 在 runner.py:116，Claude strict 参数在 permissions.py:60，Codex默认权限在 permissions.py:65。

| 精确文件/行与实际原文 | 可复现原因与审核结论 |
| --- | --- |
| P `pyproject.toml:18`：`morph-research = "morph_research.cli:main"` | installed console entry 映射由实际 distribution metadata 读取；正式 CLI 自己处理 init/inspect/run/observe，不依赖测试脚本补 flags |
| P `src/morph_research/config.py:78`：`if vcs.get("vcs") != "git" or vcs.get("commit_id") != CORE_SHA:` | 真实 core direct_url 必须 CBC；不能以当前源码 cwd 代替安装依赖 |
| P `src/morph_research/permissions.py:65`：`"default_permissions": ":read-only", "approval_policy": "never",` | Codex正式 plan 自带只读/never；实际旧 installed inspection 中也存在，非测试注入 |
| P `src/morph_research/permissions.py:71`：`"mcp_servers.morph_research.default_tools_approval_mode": "prompt",`；`:87`：`overrides[f"mcp_servers.morph_research.tools.{tool}.approval_mode"] = "approve"` | 11 enabled/permitted MCP 工具逐项允许，默认 prompt；其他原生自动 catalogue 项不冒充隐藏或授权 |
| P `src/morph_research/permissions.py:60`：`argv = plan.argv + ("--strict-mcp-config", "--tools", "", "--disable-slash-commands",` | Claude精确 allowed_tools及dontAsk在同文件:49/:50；严格单MCP、内建tools空、禁slash由产品生成 |
| P `src/morph_research/workflow.py:37`：`"inherit_experience returns ConsumptionExecution: child candidate_asset_id and context.execution_id. Validate and approve child; apply_candidate receives that child and context.execution_id. Require returned AdoptionReceipt; retrieval is not adoption.",` | 明确继承执行ID在context，不混淆sandbox run_id；由原consumer实际字节生成child和receipt，产品不另建采用系统 |
| P `src/morph_research/runner.py:116`：`with selected_auth_environment(profile) as auth:`；P `src/morph_research/auth.py:6`：`OAUTH_EXCLUDED_ENV = ("ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL")` | root新案例OAuth选择已授权，产品CLI进程仅排除两已知gateway变量，auth.py:27 finally恢复；不修改父终端/全局登录/home/account/model |
| P `src/morph_research/runner.py:162`：`ok = interrupted if phase == "interrupt" else outcome.state == "completed" and task.status == "completed" and not guard.forbidden` | 非许可调用实际出现使phase失败；不是观察到cancelled就认定无外部效果或预先拦截 |

这些是静态/本地已核验的接线事实，没有发现要求 P 修改的已证实代码缺口。认证、managed config 实际效果和 live行为仍是下面的真实运行限制。

## 对原完整 checker 的逐项审核

| 原标准（C checker 行） | 产品冻结实现（P） | 本次判断及实际信任门槛 |
| --- | --- | --- |
| 三worker/AgentId、一swarm、state在workspace外（`tests/integration/check_research_live.py:86`） | config.py:94 load_state核对worker=role、AgentId实例0/1/2、scope science、role capability、权威路径/backend | 可信operator初始化，Profile extra=forbid、项目/state分离；工具参数不能选择身份或批准DB，C service.py:74/:84再次核验；实际三UUID须live |
| 作者中断在实验前、有renew、退出非0、无execution_unconfirmed（checker:106） | workflow.py:41要求claim60/renew30后不运行其它写工具；guard.py:60观察越界即stop；guard.py:66读取真实renew audit；runner.py:154检查owned cancellation/old_attempt/无实验audit | 产品用原core run_headless创建/取消自有进程；guard在事件后观察，**不证明调用前阻断**。若Agent越界到实验必须保留失败和unknown，不允许因此续接 |
| 同作者UUID、真实TTL、合法stale renew与submit在freshclaim前（checker:111、:171） | workflow.py:46读取原interrupt session；:57按真实time/expiry；:63/:64以旧token与canonical old_attempt提示两拒绝；:67才claim | 产品不手工claim或写结果；拒绝文本/结构合法Candidate及顺序由原checker实测核验。当前只有静态契约，没有新真实中断证据 |
| Claude复现、Codex作者/继承、三个UUID（checker:129） | permissions.py:44按phase选择原生runtime；非恢复阶段session=None；恢复取原UUID；config.py:111角色身份绑定 | 不能用同品牌三逻辑worker替代；科学门禁要求不同worker/run/sandbox，原checker再要求真实native品牌/UUID |
| 每角色累计900s/64tools（checker:135） | runner.py:21累计各phase wall/count，:41拒绝895执行余量或64耗尽，:43返回剩余预算，:149传原core timeout/max_tool_calls | 保留5秒观察余量，不提升原阈值；未结算launch/native无observation时拒绝自动重放，实际wall/计数还须checker |
| runtime3600、attempts3、每task ONE实验（checker:215及原core门禁） | observe.py:29只读核对原runtime/attempt限额；runner.py:53按原started_at拒绝；config.py:111 max_experiments_per_task=1；workflow.py:30显式ONE | C TaskLedger始终权威，service.py:128先begin_execution后外部调用，unknown hold不能自动再运行；产品未新建时钟/调度器 |
| 原正式权限argv/11 permitted actualcalls（checker:145） | permissions.py:42产品build_launch，单MCP/只读/never/enabled11/per11approve/defaultprompt；Claude dontAsk/strict/tools-empty/allowed11，guard.py:7解析raw及normalized | D8530/root澄清：不增加“总目录exact11”断言。resourcehelpers/apply_patch可见限制如实记录；raw越界失败不会被白名单过滤抹掉 |
| discover/context主动claim/renew（checker:162） | workflow.py:29角色自己认领并续租；runner.py:168只读检查前序已completed/live/settled后才启动模型 | observer没有推进任务或自动派单；本地inspect能构造not-ready角色计划不等于run许可，run前序守卫会拒绝 |
| 作者原canonical Candidate、original verify、quarantine完成（checker:192、:198、:210） | workflow.py:33照用candidate_template+claim attempt_id，resume rules指定original verify/complete；C service.py:158/:222/:286 | 当前token只授权写；原source Attempt/执行token保持；complete作者effect_applied=false/approved=false，不当批准/应用通过 |
| 独立Claude复现→S文件validate/approve/apply，replication completed/effecttrue（checker:194、:196、:235） | workflow.py:35完整提示原source资产、freshsandbox、purpose=reproduction、validate/approve/apply；:34指定文件report_id | C require_reproduced核查original/peer live+succeeded+passed+known、相同计划及不同worker/run/sandbox；promote.py:15静态报告门禁；apply实际落地才completed，不用作者完成替代 |
| 第三角色主动search→ONEfresh本地再验证→purpose inheritance（checker:169、:262） | workflow.py:36显式search及fresh local run、verify在原S上 | search检索不算adoption；C service.py:349和research.py:84要求条件匹配、parent独立复现、本task/currentworker/token的可信本地再验证 |
| child新文件validate/approve/apply(context.execution_id)（checker:268） | workflow.py:37精确字段提示，P不手造child/ConsumptionExecution；复用C service.py:359/:390/:403 | C inherit返回asset_id=S、candidate_asset_id=C、context.execution_id；apply使用child文件report，源S身份不变、child为继承者canonical Attempt，head/preimage/fence再核验 |
| 唯一原AdoptionReceipt与result/context/S/C/bytes一致（checker:265） | P只有提示与观察；C service.py:406调用原AssetConsumer.record_adoption，consume.py:95核查completed/effect_applied/owner/token/result及目标bytes | P没有fabricateUseRecord/receipt、未增加另一经验池；实际science/experiment.py和science/reused.py必须等于原/child after，检索/注入/批准都不能替代 |
| 单次run/C archive/known/succeeded/passed/destroyed、原完整Fraction residual重算（checker:211、:55） | P无输入metric/result/科学阈值修改接口；初始化C public_case，候选/evidence均原core路径 | 必须I从原checker读三份真实归档；本地SDK/schema/contract不能补科学报告或远端效果 |
| 可选known作者local-completion及原失败保留（checker:202、:219） | workflow.py:82只读旧resume和实验archive，known/live/pass/destroyed/单原发布；:115 mode=ro读取真实ValidationReport；:121必须正好一份原失败；runner.py:134拒绝覆盖冲突diagnosis | 当前fence仍由core验证，不修改原source token、报告或原clock。此分支只解决原作者已知结果，不能免除复现/继承 |

产品没有直接科研 MCP effects 实现：init调用现有seed_case，permissions调用原LaunchRequest/build_launch，run调用原run_headless，ReadOnlyLedger复用原decoder但不初始化/迁移DB；transaction明确抛 observer_cannot_mutate_ledger。涉及claim/renew/执行/提交/晋级/应用仍经C原TaskLedger/AssetStore/SDK权限与fencing，耗时外部调用仍不长持SQLite写事务。命令失败或mock观察没有从prepared跳到task_live。

## 安装与离线证据的独立核验

审核副本：`C:/Users/DW/AppData/Local/Temp/morph-B-product-review-198304d9a1e8426695711eab4dc2d3c7/product`，由指定SHA git archive生成，仅本地审查/fixture，无Manifest/hash/proof设施。使用 P 已交付非editable专属venv读取现有安装，B未重新安装依赖或修改该venv；不是I的新独立安装验收。局部环境 BLAS/OMP/MKL=1、UTF8=1、PYTHONDONTWRITEBYTECODE=1。

| 本次命令或只读检查 | 实际结果与界限 |
| --- | --- |
| `git rev-parse cbc4dede...:tests/integration/check_research_live.py` 与 c458同路径；两版本领域路径diff | blob完全相同39948d...；领域diff为空；这只是Git原文件比较，没有新hash系统 |
| `install-verify-01/Scripts/morph-research.exe version` | exit0，core_sha=CBC、installed Python3.12；distribution console entry映射正确 |
| 同正式installed entry `doctor` | exit0，原bridge本地canonical/schema1.14.0非法Gene拒绝、assets_sdk=ready_local、acceptance=local_only；无模型/实验/Hub |
| frozen archive与现有installed product包13文件比较，Python AST比较 | 首逐字节断言auth.py失败；定位后发现archive为CRLF、wheel为LF，13文件仅换行差异、Python AST全部相等；不能声称逐字节相同 |
| 标准库读取既有offline-installed-state-01的author/replication inspection JSON | request/HostBinding身份匹配，probe=None/model_invoked=false/prepared；Codex只读/never/enabled11/per11approve，Claude dontAsk/allowed11/strict/tools-empty实有。仅读取，不新建/覆盖P档案 |
| 冻结产品node/package-lock对CBC package-lock中对应依赖记录逐项字典比较 | 7条原依赖完全相同，包含integrity/license；无源码node_modules借用/NODE_PATH或EvoMap协议 |
| 下方4项原tests独立执行 | **4 passed / 1.58s**，exit0；raw越界/正常允许、累计预算/未结算归档、installed原SDK、拒绝system/unownedmodules/manifest覆盖 |

四项精确命令在archive cwd，未全库或全产品20项重复：

```text
<P-state>/venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
  --basetemp=<B-review-root>/pytest-bounded
  tests/test_product.py::test_actual_forbidden_raw_or_normalized_calls_stop_without_masking
  tests/test_product.py::test_cumulative_limits_and_incomplete_native_archive_fail_closed
  tests/test_product.py::test_installed_original_core_asset_bridge_ready_local
  tests/test_product.py::test_asset_setup_refuses_system_env_unowned_modules_or_manifest_without_overwrite
```

其中 P-state=`C:/Users/DW/orca/workspaces/Morphogenesis-Research/research-product-1001-state`；B-review-root为上列archive父目录。运行依赖读取现有P venv、fixture只写B自己的临时目录；pytest无cache/bytecode写产品目录，未写P/core测试。外部native事件测试始终为离线合成/原mock边界，不能标live。P自己的20pass/freshwheel88deps/init/inspect/observe/not-ready refusal记录只作为Owner既有证据；B未据此声称新独立安装或真实OAuth通过。

首错误保留：一次rg以Windows不展开的 `src/morph_research/*.py` 查找报os error123，随后用目录+`-g '*.py'`；byte比较auth.py首AssertionError及CRLF原因如上；文档逐字引用首校验发现错误的pyproject.toml:22，按实际rg定位改为:18后保留原校验断言重验。未改业务测试/科学容差来取得绿色。正式文档引用按行定位复核；先前薄Handoff错误引用在本报告精确纠正。

## 剩余条件与 release 边界

1. root已按用户真实隔离验收授权选择**新案例的本机既有Claude官方OAuth**（决策3c859ff/msg01c5798）；可选偏好未答不冒充用户回答，不将其重新标为等待新增审批。产品auth.py只在子CLI进程排除两gateway变量并finally恢复；permissions.py:59用session settings防两变量重引入，现存user model不改。真实empty-env+currentmodel兼容、managed settings/权限运行效果 **NOT_RUN**，auth status/schema离线通过不等于请求就绪。
2. Codex0.159自动resource helpers/apply_patch可见限制已如实记录。允许标准是11 permitted MCP actualcalls/原权限/无越界使用，不新增总catalogue exact11断言。guard观察取消须保留原raw与normalized越界失败，不能写成预先阻断或effect=0；若实际越界影响不明则unknown停止，不自动重放。
3. 原research-host-7d04的401、过期runtime3600、作者source2/current3、原文件验证失败及unknown全部保留；不重置旧clock/limits、不拼接/移植旧作者records。其局部known作者证据不能替代原全checker。
4. 新明确 `research-formal-1001-01` 仅root release后由I执行，从正式installed入口完成三角色/中断/真实TTL/两个合法stale拒绝/三独立run/科学判据/原与child文件门禁/实际adoption，并跑**字节未改的完整原checker**。本次没有启动该案例，也没有补flags/env/批准/完成或写known result。
5. I的CBC完整工程门禁及全新产品安装是独立工作，B并行只做本报告的轻量专项；NIST抽离、第二任务、更多Agent、Hub/EvoMap仍后置。真实新失败按具体raw/source行退回原P/A/C/B Owner，经root授权修复，不能靠放宽文件门禁、fence、阈值或checker。

本次审核仅交付本文件及B track追加记录。commit/push、完整SHA与remote clean由最终Handoff回传；审核结论不构成主控/I live验收签字。
