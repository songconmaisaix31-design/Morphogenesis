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

阶段1完成：SOURCE ec24ebb4519845bf677786e0480260bc76c85407，A REPORT dbbc08da5b5dbe4200beee6ffac254c913dc8db7，I REPORT90dd1bc418d3adfb9e3151fbde9f74635af25ef8。原完整 CI run36850437153/attempt1 Windows1109pass5skip、Linux1111pass3skip，原type/build/SDK/实际wheel分发全部通过；后续累计源码须取得独立的新完整双平台结果。
阶段2完成：产品SOURCE9650e37c53577490fde884f58db3f71822612fdc/REPORT60c95cffc31546bf7fbbd7d86a0af87734d6b243，准确fresh非editable安装47pass90.20s。正式readonly历史清单来源verified/DB unchanged；原checker39948 PASS，新有效renew author5/third6 SATISFIED、peer0 NOT_SATISFIED，audit exit1如实保留，不代签新live。
C域完成：SOURCE08b37827e6e6b48db93962611b1a79a230b1f2c1/REPORTdcb23d993ce3562993c20f5118209bc49ccae234 root核对remoteexact/clean/doc-only报告。C72pass/strict119、新安装两case同Executor/read_result mock pass仅contract_local；原NIST程序/数据/计算阈值/checker39948不变。扩展首116pass1fail618.16s、最终SOURCE首次121pass1fail204.21s及focused1fail15.96s原Git fixture READY失败保留；C实际身份核对后仅清理自己两个fixture后代，当前owned0不回写初始effect。
B SOURCE5fb0cee3753b5169856f7ea8e0490c2daa2bad4f已push/root核对remoteexact/clean，相对C789只case.py、新research测试、授权test_git_timeout.py。生产paths.py只读无diff；旧5assert AST、实际git前唯一started、真实0.2/整体<3全部保持。READY准备计入总耗时；仅新owned Job/原生句柄在原断言之后清理，子Python仅stdlib -I/-S。初版整体3.068秒RED保留；最终诊断首PASS3.95s，实际ready0.748/asserts0.956/cleanup0.959秒。B域已签收：准确Git冻结197PASS240.99s/strict8，新copy安装7文件Git-wheel-site bytes一致+nlink1、两case installed CLI exit0且未claim/无科研。默认UVcache硬链接13/14首RED和未发布草稿15保留；未放宽no_links。REPORTd228d43e9c12ca9743a362a7f1187cda4d8218ee root remoteexact/clean、SOURCE到REPORT仅两授权文档；worker_done已同Task结算，ACK前retain原Owner供返修。
P prepared SOURCEf47042fd6e25d05caf14e3192b899c0948ec1da3已root官方Git ref实际exact/clean；仅正式双case入口/配置/校验/audit接线与新case测试，原47/renew/权限无变化。当前仍临时pin C789，旧B拒绝synthetic init的第二轮RED保留，FINAL_PRODUCT_PIN_RELEASE msg_de46495209f4已发：消费累计CORE43ab0c50f47cccb5c110426de10e0a994e485a2f，准确新产品SOURCE/freshcopy安装原47+3完整50与入口/只读audit检查进行中，不能拿负例子集替代。
I同终端新task_5984005f6d82/ctx_2e1675f71616预检后已INTEGRATION_WRITE_RELEASE msg_e135d4cdc763；首start unobserved/requestc803b8be-cc31-41f2-986b-8752226eb986保留，实际live composer preview后一次bareEnter，已实际读取任务/Working，不重派。I所有权新完整checker tests/integration/check_research_case_live.py/自身报告及最少胶水，旧NIST checker39948只读。累计CORE_SOURCE43ab0c50f47cccb5c110426de10e0a994e485a2f已root实际Git diff/clean/官方ref exact核对；普通C ff/B merge fc065979686379424b5d4089455c94adb234cd9d，A/C/B源均ancestor。新checker actual blob2eb20fa79a69bf022d9fe8b2312cdb6860b72c61保留原105main行为断言及4项案例绑定，仅科学/输入字段交给注册案例，原39948不变。原完整双平台首次CI正在检查，产品最终pin/50与新安装并行；AST只是本地语法证据，实际无effects --help入口与最终fullchecker/live仍待检。
最终I冻结累计coreSOURCE→P finalpin/产品SOURCE/50检查与独立新安装→原完整双平台成功后才ROOT_FINAL_TWO_CASE_LIVE_RELEASE；每类新唯一case须两品牌/三角色/真实有效续租/三个实际实验/一次真实继承/唯一AdoptionReceipt，原NIST FULL checker与第二类FULL checker均必跑。当前无新native/model/auth/API/服务/真实科学/key内容读取。保留所有首失败/unknown与原case06；docs-only不科学重跑，不扩Agent/EvoMap/desktop/main/tag/publish。
