# 下一轮：工程红灯、有效续租、第二类科研任务

业务事实源：用户2026-10-01最新指令，现行开发包与AGENTS.md。基线为CORE cbc4dede782eb79b9c007520d96d7958857da0af、产品SOURCE48ddc916a0072dea50e8caf2773775a0030942b0、原检查器blob39948d9615bce07b40b96eeaf5dfb263b993c6d3、已完成case06/I证据874a6330febd8d8dcaf5cfc043f0254d466f6d71；原全部失败、unknown、费用及未成功peer续租事实保留。主控只治理、分发和验收，通过同一Orca Run复用固定Owner，不开发业务。

## 顺序与验收

1. A先修日志锁竞争：orchestration/fc_logging.py的SQLite写锁等待当前50ms。原test_concurrent_append_and_partial_tail_preserve_facts不削弱：半截首行逐字节保留、六条事实完整、序列1–6。只重估日志层有界锁等待/串行化；严格append失败仍抛出，emit失败仍可观测且不得冒成功，不改科学/TaskLedger超时或重放科研。补必要定点并发与失败语义检查，SOURCE commit/push冻结后由I独立跑新版本完整Linux/Windows工程门禁，保留首失败和适用skip，不用单轨/串行小集合代双平台全量。
2. 第一门通过后P补有效续租验收与只读无秘密验收清单。核验真实账本renewed、匹配worker/task/current fencing token、有效租约与关键写入先后，不能只数renew调用；旧case06原标准PASS不改，新增标准对旧peer无成功续租明确NOT_SATISFIED。复用现有Pydantic/账本/可信archive模型，清单绑定准确core/product/checker Git身份、三实验摘要、唯一AdoptionReceipt及原日志位置/检查结果/unknown；不新建Manifest/哈希/完成证明系统。文档-only提交不触发科学重跑；新的行为性科研验收由I独占、从新冻结非editable安装正式入口执行。
3. 然后C/B/P并行完成案例与平台分离及第二类任务：更换数据、候选程序和科学判定，复用同一执行/独立复现/文件验证批准应用/第三角色继承路径。假设第二类采用公开说明的项目自有确定性线性回归数据与独立有理数判定，输入synthetic明确标注，实际沙箱/原生运行保持live，不能用模拟执行代替。必要时Owner先Handoff调整任务选择；不做大量算法对照、不重建架构。NIST原判定/历史checker/证据保持可读且不弱化。冻结累计core/product后I新安装、适用原完整工程检查与两类任务完整行为验收；静态清单/离线回归不得代签新live结果。

## 固定互斥轨道

| 轨 | Agent / worktree / branch | write_paths |
|---|---|---|
| A 日志 | 原A / morph-research-agents-0930 / songconmaisaix31-design/morph-research-agents-0930 | orchestration/fc_logging.py、tests/swarm/test_fc_logging.py、docs/tracks/research-logging-1002.md及独占private日志测试state。原native-process代码不改。阶段1独占开工。 |
| P 正式入口/续租/验收清单 | 原P / 新产品仓research-product-1001 / songconmaisaix31-design/research-product-1001 | 产品src/morph_research/**、产品tests/**、README、必要core固定pin与自身uv.lock、docs/tracks/product-1001.md；产品治理文档归主控。阶段2才开发，阶段3消费案例接口，不复制核心逻辑。 |
| C 科学判定与案例包 | 原C / morph-research-sandbox-0930 / songconmaisaix31-design/morph-research-sandbox-0930 | orchestration/experiments/**、demo/research_case/**、demo/research_cases/**、tests/experiments/**、docs/experiments/**、docs/tracks/research-cases-1002.md。只必要CaseDefinition/判定注册与数据/程序；不改MCP账本或全局SDK配置。阶段3开工。 |
| B 科研协作适配 | 原B / morph-research-space-0930 / songconmaisaix31-design/morph-research-space-0930 | swarm/research/**、local_assets/research.py、tests/research/**、tests/local_assets/test_research*、tests/local_assets/test_git_timeout.py（仅原真实fixture准备）、docs/research/**、docs/tracks/research-space-1001.md；local_assets/paths.py只读，不动C数据与判定，TaskLedger仅真正必要问题再Handoff。阶段3开工。 |

I原morph-research-integration-0930/branch morph-research-integration-0930负责每阶段已冻结输入的独立集成与验收，只tests/integration/**（原checker文件历史版本只读）、自身报告和最少import/config/type胶水；领域问题回原Owner。主控仅docs/PLAN.md、本计划、docs/RESEARCH_NEXT_ACCEPTANCE_1001.md；不写任何业务或观察脚本。

保持Python/LangGraph/Pydantic/SQLite/httpx/MCP/官方SDK及既有目录。核心锁不变，由现有owner管理；产品pin更新不等于新增依赖架构。所有阶段清晰commit+normal push/remoteexact/clean；源代码SHA与报告SHA分列。无force、秘密入库、共享WIP覆盖、未知远端请求重放或吞错冒成功。中国StepFun凭据只正式产品使用且保持外置；不重复quota/auth探针。只原owned sandbox可按身份核对恢复/known清理后停止。更多Agent兼容、EvoMap、Hub/main/tag/发布均不在本轮。

## 当前状态

- 当前冻结核心 SOURCE **bf67c1a4134a25d009cff2acccbfab027999bea6**，I 原分支 `morph-research-integration-0930` remoteexact/clean；正常合入 A SOURCE56ee35bcc31ab704ba53884b1ba96e3c93d00c4c，旧9363为祖先。原NIST checker39948d9615bce07b40b96eeaf5dfb263b993c6d3与第二类checker538f6b1852ccbba3f1cef6d09ad16b2a6fe8d4f5不变。新原完整双平台 foundation36879998711进行中，不能借旧9363/Stage1绿代签。
- A 原Owner新task_31a0cde1e0f2/ctx_3f0d93c01fc8只原生清理最小返修，独占process.py/windows_job.py/_windows_exec.py、tests/native_agents/test_process.py/test_posix_process.py、自身research-native-cleanup-1002报告与private产物。SOURCE56ee实际三文件变更，精确9363新venv两真实RED8.23s保留；新SOURCE三必要定点5.64s PASS、Windows完整native92PASS5POSIXskip66.66s/strict10 PASS。WSL-POSIX/build与docs-onlyREPORT待Owner完成，无模型/API/现场进程动作，不改nativeargv/环境/MCP安装解释器；I task_5984005f6d82/ctx_2e1675f71616已获正常集成与新fullCI权限，只最小胶水/验收，领域返A。
- P 原Owner新task_51b92413ae3a/ctx_62218c5b3076已收到FINAL_PRODUCT_PIN_RELEASE_NATIVE_REPAIR msg_5574b578b1d8：只既有固定pin/README更新到bf67，早SOURCE后全新GitLF/ownwheel/freshCOPY安装及原完整50/正式双caseCLI/只读audit；16产品+4案例输入+三核心native文件准确Git/archive/ownVCSwheel/site/noneditable/nlink1证明。旧SOURCE497e/REPORT41de钉9363已作者50与I独立50通过，但不是新版本结果。新SOURCE/REPORT尚待。主控随后才放I另独立新安装。
- C SOURCE08b37827e6e6b48db93962611b1a79a230b1f2c1/REPORTdcb23d993ce3562993c20f5118209bc49ccae234、B SOURCE5fb0cee3753b5169856f7ea8e0490c2daa2bad4f/REPORTd228d43e9c12ca9743a362a7f1187cda4d8218ee均已签收retained，案例数据/候选/科学规则与平台分离，两类复用同Executor/ledger/继承机制，旧NIST程序/阈值/原断言不变。阶段1日志ec24ebb已签收，保留半截字节/六事实/seq1–6与严格失败；当前原日志代码无新改动。
- 新NIST research-formal-1002-nist-01首次真实恢复因原interrupt后代持有同UUID writer导致-32600 RED；原完整39948 first checker RED、native effect/usage仍unknown/null、trusted科研派发0/unconfirmed0，失败case不重放。14:41实测owned0（操作前已退，终止动作0、原因未知）且原owned服务Stopped。第二类真实闭环NOT_RUN。代码修复后新冻结full双平台与新product独立门齐全才root明确放新唯一两类：每类两品牌/三角色/当前token有效续租/三真实一次性实验/独立复现→文件验证批准应用→第三角色本地再验→真实继承与唯一AdoptionReceipt；科学unknown即停，权限/参数由正式产品提供，密钥不入清单。

第一失败、安装来源、原始命令/退出码、各历史SOURCE/REPORT及现场事实统一保留于 [RESEARCH_NEXT_ACCEPTANCE_1001.md](RESEARCH_NEXT_ACCEPTANCE_1001.md) 和Owner原日志，不在计划复制增长。文档提交不科研重跑；主控只此计划/状态/决策/验收。全局auth/HOME/provider/model/tier/TLS与主线2957b40、docs/SWARM_SOL_PLAN.md原WIP未动；无Agent大扩容、EvoMap、desktop/main/tag/publish。
