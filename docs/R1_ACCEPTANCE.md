# R1 验收登记（2026-10-03，开发开始）

## Q 冻结导出与受信配置边界接纳（16:35）

Q SOURCE `88d0cc28d1fdb3d89d62cdb1f1312078fc3c22b0` / 最终 docs-only REPORT `6ce5a23ea256affdf9fe8a71bbaabb66695f3631` 已普通发布；原本地 REPORT `09a62370498e40d54d8e956ce6b2c941e16f7515` 及其未发布历史检查点保留。16:29真实Git连接恢复后，Q顺序发布SOURCE88、REPORT09和新docs-only报告；主控独立 `git -c http.version=HTTP/1.1 ls-remote` 核实远端=本地最终完整SHA、clean、REPORT6ce父09、SOURCE88后仅r1-boundaries.md。首push/read失败没有改写，不因发布恢复重跑已绿测试。

实际受测私有非editable分发为 A `aec86c98ffe8fc3c3a922da5a6e281d553820d05`，包含 B `5769005b09f1b756c94fdad0649a6b74690c0ca9`：原15受影响配置/领域调用 + 45导出/生命周期 + 5 HostConfig/MCP交接，共 **65 PASS / 24.98s**；136原Git Python blob相等、VCS full-SHA direct_url正确、96依赖兼容。原15首3 FAIL/12 PASS（默认None正确fail-closed与旧成功前置冲突）及首次身份脚本失败保留；使用明确可信配置和实际惰性HTTP/SDK fixture，未猴补生产能力或削弱原 installed_core/process/socket 守卫。

独立检查覆盖本机daemon/服务/main-egress精确身份，runtime RW卷仅这对独占且冻结，导出树/祖先/leaf路径与有界tar拒绝，SDK pause/create/resume/stream效果unknown阻断后续、不重发及owned最终清理边界。PathStat无nlink，不声称所有inode别名排除；逐文件resume不承诺跨文件原子快照。测试没有访问真实Engine或执行生成候选，不证明真实隔离。原始命令/输出与SOURCE身份见 `docs/tracks/r1-boundaries.md` 及 Q `tests/integration/r1_security/evidence/a-aec86c9-installed-affected65-first.txt`。

主控接纳该Task succeeded并worker-release：retained/no_owned_resource/processAction none，未宣称关闭自管终端。新最终组合、完整产品离线回归、真实AT07和L2仍待；AOCI正式语义索引尚在原A，P真实人类审批receipt仍缺，实际Token节省unknown。


## MVP 只读会话阶段与隔离准备接纳（13:05）

以下是领域阶段验收，不是新最终组合完整回归；原首次失败、旧类型债和下方历史组合分别保留。开发工作会话已按用户选择切为 GPT-6.1 Sol，OpenCode 后续指定 DeepSeek V4 Pro。

| 交付 | SOURCE / docs-only REPORT | 主控核对与实际结果 |
|---|---|---|
| P 只读会话 API | 67721aaa815e706c51e0f80a1d15ab71e34b6880；AOCI整体报告待人工确认后续交 | 真实来源记录→原权限/身份→GET会话/输出/current_local_view；无输入/启动/回放。原私库转发FR04选择，不另造上下文引擎。raw归档/COPY安装28 PASS/50.06s、适用30源types PASS、whole原10错误/6文件身份不变、100依赖兼容。 |
| F 拓扑只读终端和上下文 | 7bf17d195859a18960ee1ef933a920a286f73e61 / c08566edc492e92adfc4e24a9e8de1c18b859e02 | Codex GUI参考，成员节点右键/键盘打开精确会话，GET轮询、晚响应隔离、窄屏首屏可见。运行包07df78b/core cea7923，后继7bf只改observer。build PASS，新18/旧14/布局2 PASS；实际installed会话2 PASS/6.4s、原输入2 PASS/6.7s。主控实际看桌面/窄屏截图；原observer首2 RED保留。 |
| B 原生命周期上的冻结导出准备 | 5769005b09f1b756c94fdad0649a6b74690c0ca9 / 5aebd2eb7af774b3dc496ad9620548f6e7852e09 | 主控读实现/锁差异/报告并核对远端、clean、原始日志。官方OpenSandbox pause→官方Docker transport HEAD/GET→原SDKresume；无新执行器。定向110 PASS、experiments210 PASS、strict140 PASS、104依赖兼容。原strict首RED与旧Q三FAIL保留，Q后继ctx_a1965382b7ea独立复核中。 |

F 已结算，B 已结算且保留原Owner返修；release均为retained/no_owned_resource/processAction none，不冒充终端已关闭。A受信HostConfig配置定向9 PASS/10.18s、strict2 PASS，仍在本轨完成核心AOCI。所有科研执行事实仍为mock；HTTP页面真实观察不等于真实科研或独立人类理解。

B 的固定上游runtime volume实际RW；仅允许owned main/egress两者独占并冻结，导出树不允许挂载。单文件下载后恢复原sandbox，不宣称跨文件原子快照。Engine实际版本/ID及真实隔离均未观察，配置和离线通过不授予verified/admit。只有最终固定组合离线验收后才单独请求AT07授权。

产品AOCI正式15语义条目仍未应用，等待真实人类TTY确认的精确preview；主控不会代输入、伪造receipt或重置baseline。核心索引在原A继续。Token节省未测量。I新任务尚未派发；一次最终完整产品离线回归、相关最终installed观察、AT07、L2仍待完成。

## 三项 Spec 行为的本轮定向验收（MVP 追加前置）

本节登记新的领域证据；下方旧 core2c/product9e 的“最终固定组合”是上一阶段记录。本轮加入 AOCI 与只读节点会话 UI 后尚未冻结新最终组合，完整产品离线回归仍 NOT_RUN。

| 行为 | 已接纳 SOURCE / REPORT | 实际调用及证据 |
|---|---|---|
| 正证据影响后续路线 | C e82cae36038c386aec999642289ac1d78c82a9ed / 52b8d26da04aec41ceb7e008445ef2f1dc088d53 | 原 research-v1 证据分值最小修正；三合法分支机会由均分变为约0.386667/0.306667/0.306667，同seed正式choose改变，原TaskLedger claim保留证据引用，授权额度不变。重复/未独立接受/不适用/越权不得增益。C70+Q45+旧v0/v0.1 26共141 PASS，policy strict1 PASS。 |
| 成员局部上下文 | A cea7923fec48c10e043c1fea40c99749e0b6a114 / faf23260df7a4f530eb421680f71eb6dc7c72e40 | 私库仅转发，选择确在原ResearchService.research_context/context：权限先于分支、依赖、能力、引用可达，保留来源/条件/争议/截断。产品工作台/export显式overview=True，成员正式MCP保持局部。def0实现聚焦68 PASS；cea后继COPY安装native13+context stdio1+原dynamic stdio1+旧policy28=43 PASS/52.52s、changed4 strict PASS。不同SOURCE结果不混记。 |
| 正式 envelope 跨片段接续 | P 79ca28d81dd039b24c284494d3aa5911d7b10cfc / ffe186235318cf6c6ecb79de8e5db92906575cfe，候选pin A cea | research-member run每个有界片段给新invocation；可选resume只接受同成员已观察completed session。A host-only admit_native_invocation复用原Reservation/项目BudgetLedger，P将瞬时绑定交原MCP，既有知识/累计额度/期限/unknown守卫不重置。实际raw-Git COPY安装44 PASS/44.89s，含11新增接续及原HTTP/MCP/installed门；29适用types PASS，原10债逐条不变。 |

主控分别核实 A/P 的远端精确 REPORT、clean、SOURCE 后仅各自报告文件及原日志。A安装15原生产文件与Git blob相同、103依赖兼容；P完整raw归档153产品/657核心文件对Git blob相同、100依赖兼容。所有测试仍是本地契约或真实本机HTTP/MCP上的mock执行，不是模型真实科研或AT-07。

首失败保留：C正支持与零适用性各1 RED；A基线19 FAIL、实现组合39 FAIL/57 PASS（含SDK安装条件缺失），P基线3 FAIL/2 PASS、Windows tar中文路径失败、换行转换后的43 PASS/1 FAIL。后继修复是追加证据，不改旧结果；A原anyio重写warning、相对解释器路径未启动的失败也记录在报告。旧完整产品222/6、原第六项原因UNKNOWN、原十项类型债与C清理被策略拒绝继续保留。

下一步：B独立隔离检查包离线准备 + P真实只读会话投影/AOCI + F新UI → I唯一固定组合完整产品离线回归和installed输入/会话页面观察 → 具体AT-07单独授权 → 通过后一次L2。AOCI配置/索引对齐与MCP实际连接尚待，节省token未测量；UI成员节点不得猜测session或提供写操作；AT-07/候选真实执行/L2均未执行。


08:28 文档身份追加：产品最终文档REPORT为 `a7f657d18fae33fc2a4df92b5fcb60dcd7839c5d`，受测SOURCE9e27187与核心SOURCE2c63bc7不变，差异只有docs；下文ad104保留为07:16时点的领域/类型验收报告。主控已核实远端、clean与普通合并历史，I仅封存现有验收报告。第三次约66分31秒工具返回空档原因UNKNOWN，未触发任何测试/科研重发，未改变原始耗时或验收结论。

## 最终固定组合的适用工程验收

核心 SOURCE `2c63bc7c9e49edff28e26f5930a22d0415fadd65`；产品 SOURCE `9e2718789cb67f8b829207e17dac4d95a88e59c9`，最终产品REPORT `ad104f7c3555d04af4753c0601729f6dfef3c855`。以下仅登记本次实际受测层级，完整命令、原日志、first RED和来源见I报告及R1_STATUS。Windows精确核心CI1566 passed/15 skipped/1974.60s，Linux1565 passed/16 skipped/563.89s；同一CI37073582354两平台strict136/build/SDK/wheel均通过。

| AT | 本轮确定性 / 本机安装证据 | 真实运行范围 |
|---|---|---|
| 01 / 02 | 实际PDF/文本/已提交代码快照及来源定位、版本和解析不足；权限共享背景与成员接续契约；正式HTTP/MCP安装路径 | 公开论文HTTPS获取用受控fixture验证，实际获取未执行；AT02的L2实例未执行 |
| 03 / 04 | 原TaskLedger的非预置提议、合法候选推荐/覆盖/认领、lease/fencing与替换边界；正式stdio与原SDK接口 | 模型自行产生分支与研究选择的L2实例未执行 |
| 05 / 06 | 独立候选版本、评价前冻结、原始输出重算与篡改/自批拒绝；支持/反证/unknown三条正式HTTP链 | 候选执行为inert mock，未在宿主执行；模型生成和实际沙箱运行未执行 |
| 07 | SDK配置与无效隔离声明负例已测 | **真实无害隔离探针NOT_RUN，不标AT07通过** |
| 08 / 09 / 10 / 11 | 三轴分离、有效反证贡献、意见不直接批准、同源去重、接受证据影响原discover/choose/claim、休眠/重开与额度边界 | 反馈改变真实研究行动的L2实例未执行 |
| 12 / 13 | 独立复核来源/成员/当前执行身份、原消费/本地再验证/apply/AdoptionReceipt工程链已测且标mock | 真实独立沙箱复现及后续实际科学使用NOT_RUN |
| 14 / 15 | 独立Q最终293 passed/3历史skip；unknown、重复POST、过期token、跨项目/成员、预算不重置、provider与数据授权边界；原保护未mock | 未作额外科学调用、费用授权或外发 |
| 16 | 独立完整fixture UI108 passed/6安装场景skip；另正式installed支持/反证×两视窗共4 passed；主控/I已看真实截图，0POST | 历史mock科学事实；未参与实现的人类观察、L2页面实例NOT_RUN |
| 17 | 原始Git blob、COPY非editable安装、锁/核心pin、SDK、构建、类型身份与原案例兼容；LinuxCI1565/16、WindowsCI1566/15通过，双端strict136/build/SDK/wheel通过；产品首222/6、原6后继6/6分别保留 | 整包原10类型债仍RED；未称单轮产品228全绿；仅Windows完整产品路径受测 |
| 18 | 正式完整HTTP成果包包含源代码/环境/原输出/复核/贡献/采用与局限，支持与反证原值逐项对应 | 输出包含明确mock事实；真实L2科研成果包未产生 |

I新增类型首RED14/9已由原P最小修为仅原10/6；I独立适用29源通过，旧a25同环境诊断身份对照保留。产品首5个parser失败为I私有npm布局准备问题；第6个preflight原异常仍UNKNOWN，后继成功不追认原因。原helper超时、CI竞争、长返回空档和首RED均保留。

真实沙箱AT07、L2、L3、独立人工观察、全局系统Python人工恢复、旧Orca release_unknown分别登记，不相互抵消。新实现的本地工程证据不能替代Spec14.4的授权真实研究切片，全R1退出条件仍未达成；性能仅记录实际样本。主控仅维护治理与验收，最终分支普通历史保留并推送，main/tag/部署未执行。


## 06:43 最终组合进入独立验收

本轮受测组合固定为核心 SOURCE `2c63bc7c9e49edff28e26f5930a22d0415fadd65` 与产品 SOURCE `c9fcc6e24500ff26cd6600dfa6719278f04b8cb5`。唯一I已普通合并全部核心领域和独立Q历史，原P负责最终pin/lock；主控核实两者远端精确。最终SOURCE CI37073582354、I全新COPY非editable安装、产品完整Python、Q原安装保护、正式HTTP/MCP及四个实际浏览器观察仍PENDING，旧组合结果不能代替。

此前P0da/d85的原3兼容失败与相关门9 passed，Q同组合相关87 passed，已经验证旧exact11工具兼容、合法空项目与原HostBinding保护。Q最终SOURCE953e5cf/REPORT7936613和F最终SOURCE447d9e0/REPORTfa6bfbd均已接纳；全部首次RED、historical skip和真实耗时继续保留。P fbe完整221/3尚不能写成新组合全绿。

AT07真实探针及AT03/10/12/13/18所需L2研究实例、其他AT的L2部分、L3、独立人工观察均NOT_RUN；整体p95/传播目标未验收。C系统editable清理被自动审批拒绝且未清理、旧四项release_unknown不由本机私有环境验收消除。


## 06:24 验收收尾更新

核心组合d85精确CI37062098247 Windows1392/Linux1391通过，strict136/build/SDK/wheel均通过；F447精确安装的支持与反证两视窗各2通过，主控实际查看默认折叠条件后的截图。Q真正installed fbe/d85独立272 passed/3历史skip；对应身份与原始失败见最新R1_STATUS及各Owner报告。以上不替代最终I组合安装与回归。

P全适用installed fbe/d85首221 passed/3 failed，失败限于旧MCP代理config与exact11目录。后继0dfaceb复用原factory缩小旧工具目录，并保留原launch绝对配置/workspace/HostBinding；其相关兼容与独立负例正在验收。新generated/stdio/断连/字节门在fbe已通过，但不得把它们写成新0d包已完整通过。

原UI六项首失败、Q断连首六失败、两次工具长返回空档及所有历史RED继续保留。Q B72此次实际耗时4314.57s，原因UNKNOWN，不改成旧样本10秒。AT07真实沙箱档、L2真实研究、L3和独立人工观察NOT_RUN；性能只报告实际样本，不作全R1退出PASS声明。


## 04:50 组合与验收边界更新

本节是新的阶段记录，下文所有首失败与历史受测身份保留。A 组合 SOURCE `d85aa95e8da406d598f3658492e3d615bba8a28f` / REPORT `524a81ed7ba0b3550f6ae029e316a56293901d12` 已精确普通合并B/C最终历史。私有COPY非editable VCS、14运行文件与原Git blob一致、103依赖兼容；正式stdio1+SQLite并发5首次6 passed/11.11s，变动store strict通过。B最终230d源码CI37059454013双平台全适用回归、strict/build/SDK/wheel通过；新组合d85的CI37062098247尚运行，不将旧CI直接转移为新组合PASS。

| 对应 AT | 当前工程证据 | 仍需完成 |
|---|---|---|
| 01/02/04/09/14/15 | P真实PDF/文本/代码材料与来源版本、权限、稳定项目预算、unknown/resume边界已实现；P7a正式CLI+stdio/字节门2 passed。Q旧installed cc2/24f基础237 passed后发现SQLite和provider新缺陷；后继B230并发与原B边界72 passed，P7a native/provider/resume55 passed，均保留首RED。 | P已交pin d85的SOURCE fd7a79e，但该新组合完整baseline与Q真正installed门未跑；不能按schema或旧237赋予最终通过。 |
| 03/05/06/08/10/11/12/13/18 | P5b真实HTTP/原GEP/原账本的支持→独立复核→原mock采用→新版本与完整导出、反证可信贡献、unknown保留3 passed/41.23s；正式stdio可作实际choose/claim，核心原始artifact绑定与篡改拒绝通过。 | 执行是inert fixture，mock采用不等于真实科学继承；L2分支、新代码实际运行、独立复核、证据改变实际研究及成果包均NOT_RUN。 |
| 16 | F42ab静态build通过；P7a合并安装0e6279d产品/static52文件一致。正式SDK缺失导致首aggregate503/双视窗2 RED，按README setup-assets+doctor补齐后同包同配置API200。 | 页面后继在导航后过早读空DOM导致2 RED；仅补panel-ready等待、原DTO断言/30秒阈值不变。支持及反证双视窗最终结果待；主控已查看本次space两视窗截图，不能替代results页或人工观察。 |
| 17 | A/B/C各Owner精确报告已推送；B并发修复拥有原断言负例及双平台CI。核心旧固定案例/v0.1/literal语义未切换。 | 最终I普通精确合并、新组合独立安装与完整适用回归、产品最后pin、Q与F最终证据仍待。 |

AT07实际沙箱隔离探针、L2真实研究、L3效果比较和未参与实现的人工观察均NOT_RUN；全R1退出条件未达到。控制动作只报告实际夹具计时，原15秒超时和apply8.79秒保留，未宣称整体p95或传播目标通过。系统editable清理被自动审批拒绝的人工残留、旧4项Orca release_unknown继续见C/主控报告。


## 04:13 CI 与产品修复追加

A最终SOURCEcc2e722的Windows/Linux CI37051852669完整适用pytest分别1387/1386通过，skip分别5/6，strict136/build/SDK/wheel均通过。C报告8bc4c28 Windows CI37051183488新1 failed/1348 passed/5 skipped定位B资产库初始化SELECT/INSERT竞态；故最终并发兼容门槛未过，退原B后继任务修复，不能把其他同码CI成功作为该缺陷消失证据。

P08af新57项独立边界通过；public export6通过、旧parallel-loop3历史skip单列；首usage/resume/旧DTO失败保留。P24f+核心cc2新的真实非editable安装与Q configured factory验收进行中，F38首36/2及label修复已记录，当前不推定最终产品、页面或R1 PASS。Windows tar解包和Q私有依赖首失败均保留；后继安装以完整字节核对和真实origin为准。最新精确身份、CI链接和后继Dispatch见R1_STATUS.md。


最新Spec第14节为验收事实源。依据各精确候选源码与实际证据逐阶段登记；后继通过不改写首失败。首次失败记录在docs/R1_STATUS.md。

## 03:15 当前验收范围（后继证据，不覆盖下文首失败）

核心最终Owner：A SOURCE cc2e722 / REPORT5a0caf0，B SOURCE5faafe4 / REPORT6ec8c74，C SOURCE56de8e3 / REPORT8bc4c28；完整SHA在R1_STATUS.md。A最终运行模块与已安装/独立受测4afe462逐字节一致，最终只修MCP测试解包；不是最终SHA已安装。Q在同4afe组合独立A57/B68/C45=170项通过，明确fixture/mock、宿主未执行候选。C最终领域代码与该组合相同，I仍需普通merge保留最终报告/祖先与重新安装。

| 对应AT | 已取得工程证据 | 仍待 |
|---|---|---|
| 01/02/09 | P旧f006安装37与Q资料/意见21通过；当前f942成员5/5，核心来源/有界上下文/真实MCP边界通过 | P后继实际安装factory/HTTP/MCP，F新页面实际HTTP |
| 03/04/08/10/11 | 核心非预置提议、独立接受支持/反证、证据影响actual discover/choose/claim；Q57/C45通过 | 固定最终安装与产品接线；AT03/10的L2研究实例NOT_RUN |
| 05/06 | B领域245、Q68通过：host冻结判据、输出重算、有效probe/config绑定、静态危险输入拒绝 | 真实运行非fixture候选NOT_RUN；不借fixture赋予AT07 |
| 12/13 | 正式核心mock新run独立复核、原资产消费/本地再验证/apply/TaskLedger.submit/AdoptionReceipt正例；篡改/未知来源拒绝 | 原采用回执明确mock；实际研究独立复核与继承L2 NOT_RUN |
| 14/15 | 核心原ledger/fencing/项目预算/unknown保留与归档边界通过；P新member/egress负例通过 | Pf942 validusage 1 RED、resume身份8 RED待原P修复；最终组合中断与安装回归待 |
| 16 | F已有旧阶段双视窗证据；generated非空DTO前端源码准备，已合并Pf942 | 新静态构建、双视窗及独立安装真实HTTP未完成，不赋予AT16整体PASS |
| 17 | B精确wheel/private103依赖，C精确安装104依赖；原FC stdout与legacy后继通过，strict通过 | I精确最终组合、原固定两例/旧validator/新安全边界/全适用回归；首失败保留 |
| 18 | 核心research_package及原始artifact读取、SHA/size/path/tamper拒绝正式MCP检查通过 | 产品完整成果包/安装接线与L2可追溯科研产出 |

新增不可覆盖的首结果：A完整安装组合88 passed /1 failed，6行新测试误读官方MCP union结构，最终定向1 passed且运行源码不变；P f942 native/member/material48为47 passed /1 failed，原BudgetLedger结算格式缺陷；同P resume9为8 failed /1 passed，跨身份/缺request恢复没有拒绝。Q SOURCEd320205 / REPORT19a9bd5已推送记录；后续修复新证据追加。

AT07真实隔离探针、L2真实研究、L3对照和未参与实现的人工观察均NOT_RUN。最终工程组合仍未通过，不宣布R1 PASS。

## 初始矩阵（保留当时状态）


| AT | 验收对象 | Owner | 当前状态 / 所需证据 |
|---|---|---|---|
| 01 | 来源定位与回链、解析缺失 | A/P | NOT_RUN；原文页/段/行可到达，解析失败/摘要不伪全文 |
| 02 | 新成员有界上下文与接续 | A/P | NOT_RUN；真实正式入口重建共享背景，L2实例单列 |
| 03 | 发现/讨论产生新任务分支 | A | L0待测，L2未授权；非全部启动前写死 |
| 04 | 自主选择与可替换规划职责 | A/C/P | NOT_RUN；多个合法候选、覆盖理由、原TaskLedger最终认领 |
| 05 | 新候选版本非注册程序 | B/A/P | NOT_RUN；来源/修订真实，宿主没有执行候选 |
| 06 | 评价独立且冻结 | B | NOT_RUN；自报分数/阈值修改/隐藏数据/自批攻击拒绝 |
| 07 | 隔离有效 | B/I | 真实探针NOT_RUN/未授权；文件/网络/资源无害拒绝及自有清理证据，mock不算 |
| 08 | 有效反证获得贡献 | C/B | NOT_RUN；succeeded/refuted/accepted；crash/timeout/auth不反证 |
| 09 | 意见非事实、同源去重 | A/C/P | NOT_RUN；意见触发检查且不批准，重复来源不计独立贡献 |
| 10 | 可信反馈改变下一行动 | C/A/P | L0待测，L2未授权；解释下一推荐，实际研究行动引用证据 |
| 11 | 有界探索、休眠、重开 | C/A | NOT_RUN；越权/休眠无探索，历史保留，原因条件明确 |
| 12 | 独立复核 | B/A/P | L0/L1路径待测，L2未授权；不同成员、新run/sandbox与方法独立性 |
| 13 | 实际继承 | B/A/P | L0/L1消费链待测，L2未授权；新task再验证并真实使用，原adoption receipts |
| 14 | 故障与幂等 | A/B/C/P/I | NOT_RUN；迟到token、unknown、重复POST、反馈重读、进程/写入中断与重建 |
| 15 | 授权和数据边界 | A/B/C/P/I | NOT_RUN；项目总envelope跨branch/run不重置，支出/外发/新backend拒绝 |
| 16 | 三页可理解 | F/P/I | NOT_RUN；两视窗真实产品HTTP，keyboard/reduced-motion，三轴/采用与来源 |
| 17 | 来源与兼容回归 | 全轨/I | NOT_RUN；精确SHA/安装/依赖/报告，旧两例/v0.1/literal validator，历史快照保护 |
| 18 | 可追溯成果包 | A/B/P/I | L1待测，L2未授权；目标/来源/代码/环境/结果/复核/继承/负结论/局限 |

验收层分开：L0=确定性schema/权限/边界测试；L1=真实本机HTTP/MCP/安装/页面与可替换backend（mock注明）；L2=固定最终组合的授权真实研究；L3=同条件效果对照。本轮没有L2/L3结果，未参与实现的人工观察未测。

必须拒绝：按LLM文本/专家身份制造可信科学结论；候选作者自批；读取旧fixture充当新研究；因unknown改run/token重试；删除原等值安全检查启用动态；宿主运行候选或未经批准评价器；源资产PASS随条件变化继承；把查找/注入/释放写成adoption；把token限额标提供方账单硬封顶。

原固定阶段通过仍属于对应旧subject，新Spec不改写历史。旧类型错误只按基线身份登记，新schema/MCP/安全边界必须验证，不增加豁免。只据最终源码及实际回执标通过；阶段源码更新后适用重验，docs-only不触发收费科研。

## 首次独立安全验收（保留 RED）

Q 测试与原始证据提交 `6ceb2e2752979259be91415cf5a116df94e6aebd`，远端已核实。测试从明确 owner 精确 archive 导入业务代码；未导入或运行 B 的宿主候选 helper。可信 fixture 为预制输出，backend.create 用抛出异常的 sentinel；测试阻断宿主进程启动与外网连接。

| 待测源码 | 命令主体（Q 专属环境） | 首结果 | 处置 |
|---|---|---|---|
| A `48eeebd6c7fcfaf797d297ea5d73eb0673bddb46` | pytest tests/integration/r1_security/test_a_host_boundaries.py -q --tb=short | 14 failed / 4 passed，exit 1 | 项目越权/跨域关联/中断后 enqueue-bind 恢复等退回 A |
| B `fbee1e5edee5f5d0cb72141f511fdfc724633f69` | pytest tests/integration/r1_security/test_b_generated_boundaries.py -q --tb=short | 6 failed / 6 passed，exit 1 | 可伪造隔离/审批、unknown/failed/timeout 被信任等退回 B |
| C `71bfedbfd0cf4b6581f36cfdc70281bc877f71c8` | pytest tests/integration/r1_security/test_c_feedback_boundaries.py -q --tb=short | 3 failed / 8 passed，exit 1 | 无原 ledger/report 的任意结果和 reviewer 被接受、历史删除等退回 C |

Q 此后新增 B 成功 archive 缺 output.json size/digest 绑定的单项负例，也在同首版 SHA 失败；扩展测试尚未全组合重验，不能将其计为最终结果。Q 首次依赖缺失（faiss）collection RED 另存原报告。修复后的新结果将追加，不能覆盖此处。

P 首版 backend `80ed5e13351a9eab8b36ba03c710e98fd7544fcf` 为产品输入与未接入核心状态投影，尚非科研闭环：Owner 原基线 133 passed / 27 环境失败，仍需独立安装及完整适用回归。UI WIP `44353e35bc745b7542625b85376791b5ac68aa4f` 未 build/未 Playwright，已保留并移交 F；不赋予 AT16 PASS。L2/L3 和真实隔离探针仍 NOT_RUN。

## 后续候选与部分 L1（01:28 追加）

Q 精确 B `a322cfd53f5c330654e19a6add8438a3f8c5fab4` 首批 16 项为 14 passed / 2 failed：缺失或杜撰 probe proof_ref 可复用无关探针。随后独立新增 2 项审批 passed 与冻结 manifest 字节篡改、3 项 SDK 网络策略/合法镜像/direct-create 负例均 RED；均退回 B，不赋予隔离或实验可信 PASS。SDK 测试在调用前使用 sentinel 截断，未访问真实沙箱。

Q 精确 C `40011761c3cce6513bbeef776543740f60d1d03e` 首批 13 passed / 1 failed：假 observation 缺原 ledger 执行仍被当独立复核。新增 failed/unknown/unknown-effect 复核 3 项 RED；有效独立复核正例通过。Owner 新交付 `3161048c463b3aa4f434054755afc9787bbda989` 待 Q 归档重验；B 动态可信结果到 C 的薄转换和 A 实际下一推荐尚未验收。

F 源码 `124a71af513cfadf096c6e7f55b7be1be2f913ac` / 报告 `bc2a8ec4c505a680a847221b3950b22609e19cb5` Owner 已推送：当前三页旧+R1 回归 88 passed / 2 installed skipped，另以 fresh 非 editable 私有安装运行同源真实本机 HTTP 页面 2 passed；现有输入 HTTP 6 passed。未截获接口伪装真实 HTTP，执行后端仍明确为 mock。首次 hardlinked_path 拒绝、错误 selector、mock 时序失败、Node OOM 均保留，修复使用 COPY 私有安装及正确 selector，不弱化安装/业务不变量。该证据仅覆盖现有产品输入及安全状态显示；动态任务分支、候选冻结评价、复核和贡献关系尚待核心 DTO，AT16 总体仍未通过。

P 撤回八阶段新调度/伪造 mock accepted 的 WIP 只证明错误方案已移除；不能据此标 native 自主闭环完成。A 修复诊断和 P 局部输入通过均须对应最终交付重新验收。全 R1、最终安装组合、实际隔离探针及 L2/L3 科研仍未通过/NOT_RUN。

01:29 Q 交付 C `3161048c463b3aa4f434054755afc9787bbda989` 精确 git archive：`.venv-q/Scripts/python.exe -m pytest tests/integration/r1_security/test_c_feedback_boundaries.py -q --tb=short`，exit 0，22 passed / 5.11s。原伪造结果/复核、unknown、历史与 TaskLedger 负例，以及有效独立复核正例均保留并通过；原始输出 `tests/integration/r1_security/evidence/c-3161048-exact-boundary.txt`。仅接纳该阶段被测贡献边界，B 动态结果投影、实际下一行动与最终组合仍待验收。此前 C 首次 RED 不覆盖。

## 精确边界复验与接续（02:12 追加）

Q SOURCE `967c75a75196b3e4b8ec972ee504e658ff290b49` / REPORT `7ab8c4cf0bb3e24a4196b9847b850f6b5a330293` 已推送且远端核实。使用 Q 自有环境和 owner 精确 archive；原 conftest 禁止宿主启动候选及外网请求，保留有效输入正例。

| 源码与边界 | 实际结果 | 接纳范围 |
|---|---|---|
| A `7fc1e80845128080dfbcd5899aa9a09e37128753`；`test_a_host_boundaries.py -q --tb=short` | 26 passed，exit 0；重启前日志及恢复后复验均保留 | 项目/权限/来源/提议幂等与中断恢复的该阶段边界；不涵盖尚在开发的 generated/budget/advisory 接线 |
| B `d175f7e2f8c3ff41a1ac8a2a4958c68acf57e275`；原四个 `test_b_*.py -q --tb=short` | 21 passed / 8 failed，exit 1，20.45s | NOT_ACCEPTED；有效配置绑定、冲突 probe 和 direct create 仍失败；合法 SDK 配置正例待证实 |
| P `550e1d43b43a9b668d5255fd8f01d0a67c763c49`；`test_p_host_boundaries.py` 材料子集 | 5 passed / 4 deselected，exit 0 | 宿主允许目录、空拒绝、父目录和调用者 envelope 无法放大范围 |
| 同 P550；项目/来源服务子集 | 2 failed / 2 passed / 5 deselected，exit 1 | NOT_ACCEPTED；外项目仍可触达两个可信 callback，已退原 P，恢复后同断言仍 RED |

F SOURCE `36b8c0c9dfa400b3574af37a47508796dd5461d6` / REPORT `a1aee14f0b87e4cf1b0cce854f2d77ad23e72539` Owner 交付两视窗 24/24，加视觉修正后适用 2/2；该版动态候选、完整冻评价/复核/采用和实际安装 HTTP L1 仍待。旧 SOURCE124a 的 installed 2 PASS 不转移到新 SOURCE36b。

新增接线门槛：A/P 必须实际复用原 BudgetLedger 在稳定项目命名空间准入，跨 branch/run/resume 不重置，未知效果保留预留；C 只能从原账本/资产/归档与独立复核产生贡献及机会，不信任直接填入的 branch refs；FR02 本地代码快照须有界读取内容并提供行定位，metadata-only 不算完成。Owner 正在实现，不能以 schema/docstring/局部通过代替最终固定组合。

C 系统 Python editable 清理被自动审批在进程启动前拒绝（仅返回 `blocked by policy`），没有发生清理；主控明确禁止换工具绕过。C 用私有环境继续，原安装日志与只读 RECORD 清单、人工恢复步骤由 C 报告；未知旧依赖保留，不声称全局环境恢复。该操作限制与科研 L2 NOT_RUN 分开。

## 动态契约复验进展（02:29 追加）

Q 回执：exact B `e8e16a5b9e755a94f8587b76ba9fc288f218b8af` 的原29、输入/候选绑定8、合法SDK配置15，共52 passed / 2.41s。SDK正例捕获一次 SandboxSync.create 调用，未访问真实后端或执行候选；不证明隔离实测。B 后继 d0c834f 的 host mock 原采用链尚待独立重验。

exact P `cedbf3bc52eaabd4814e43068428e89a49ab5cf9` 独立12 passed / 3.17s（原材料/项目/回调/笔记边界与合法正例），证据在 Q SOURCE63fe5ea/REPORT29cb3f0。Owner 的材料18通过另计；此处不证明正式factory、PDF实际安装、native或动态实验闭环。

exact A8fc 新37项首结果35 passed / 2 failed：旧合法MCP任务缺 project payload、休眠重开fixture引用不存在note；Q将绑定实际持久项目/来源再跑，首失败保留，原业务断言不削弱。C99cd旧advisory新增7项首6 failed / 1 passed（杜撰/外分支/错误轴/重复/更正后来源）；C d7e561f Owner29通过，独立复验待。B d175输入8项首7 failed / 1 passed 同样保留，不能用后续52 PASS擦除。

F8e93738 的 build 3906 modules / 15.66s，聚焦两视窗8 passed / 9.2s；Owner实际查看1366x900和390x844截图。只接纳被后端返回的来源定位/多版本/缺失状态展示，不推定 P 真实导入已支持多版本；P import_source按kind+identifier吞并新版本和意见不同适用条件问题已退原 P 并交 Q。新 F8e 的 installed HTTP L1尚未运行。

剩余验收重点是同一组合的正式 configured product/身份MCP/native发现认领、生成候选到可信评价与独立复核、接受证据改变下一实际选择、原消费与采用、完整成果包与三页真实HTTP。所有Owner/独立Q/最终I各自证据须标来源和范围；AT07真实隔离探针、L2研究及L3效果研究仍NOT_RUN。

## 完整候选与归档继承返修（02:46 追加）

Q SOURCE71c4642 / REPORTac4b150精确阶段结果：A8fc的37项在仅修合法项目/note fixture后37 passed /13.49s；首35/2保留。B e8 52通过；C d7e原29及新generated12通过，首40 passed /1 failed为fixture试图写不可变SQLite而提前拒绝，修为断言拒绝后12通过，原失败保留。

Q SOURCE5fc892c6af5a749f8d7356fda613f98c2005846a / REPORT211c50422ec381a057773f15e1dc84d8986d3c86保存真实缺陷：B56的原mock消费/apply/adoption正例通过，但原output/evaluation/environment篡改后仍可继承的3个负例失败；Pced资料版本/内容/解析与意见适用条件9项为7 failed /2 passed。各Owner返修，旧日志不覆盖。

Q 最新SOURCEfff315b / REPORTbf5be87精确验收：B2d 68 passed /10.28s（含原始证据复查、host判据重开、应用前后回滚）；C4f 45 passed /11.80s（含原始来源与review locality、真实有效独立复核）；Pf006 + A8fc 21 passed /4.33s（原12访问边界+9资料/意见身份）。均为受控fixture边界，不执行候选、真实SDK沙箱或模型。当前B5faa后继与A0bcb完整正式入口须进一步验收。

P f006+A8fc 的私有非editable安装37通过只涵盖配置/HTTP/MCP/资料阶段。B静态危险输入compat首244 passed /1 failed、A缺Node依赖首51 passed /24 failed及P安装源码比较器的旧root布局误判都作为原始结果保留；后续新结果分别记录。未完成的安装/stdio/完整研究DTO/三页与最终I检查仍不赋予PASS。
