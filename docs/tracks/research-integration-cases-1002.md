# I / 两类科研案例集成与独立验收

工程和独立安装已通过；root `msg_35c7ce0634cd` 曾明确释放两类新真实案例。
新NIST首同UUID恢复为RED，完整checker首次exit1；root已hold后续native与科学并交原A返修。
synthetic新科学NOT_RUN；当前完整目标未完成，旧case06不能替代新闭环或有效续租标准。

## 冻结来源

- 分支 `morph-research-integration-0930`，起点90dd1bc418d3adfb9e3151fbde9f74635af25ef8。
- 接受日志祖先ec24ebb4519845bf677786e0480260bc76c85407。
- C SOURCE08b37827e6e6b48db93962611b1a79a230b1f2c1，B SOURCE5fb0cee3753b5169856f7ea8e0490c2daa2bad4f。
- C ff-only、B普通合并fc065979686379424b5d4089455c94adb234cd9d；原Owner历史保留。
- CORE SOURCE **9363fa822a004d12d57aee78ecf04fe3ab6555ed**，正常push/remoteexact/clean。
- 产品独立仓 SOURCE **497e72b5de3a8008d3e2babaae516343e249f58d**，REPORT41de858e93586559778ded803b313c720e20bfee仅文档；不搬入core。
- 原完整NIST checker blob39948d9615bce07b40b96eeaf5dfb263b993c6d3不变。
- 新完整checker `tests/integration/check_research_case_live.py` blob538f6b1852ccbba3f1cef6d09ad16b2a6fe8d4f5。
- 原日志、workflow/tools/poetry与npm锁、原checker相对接受日志祖先无变。

新checker复用原完整三角色归档与wire校验：原main105断言保留，适配注册输入名；
另4项绑定synthetic case、注册计划、role同条件和原ScientificAssessment。
科学判据由C trusted read_result(expected_plan,expected_context)检查，不复制NIST/OLS公式。
首次43ab隔离help因helper名称导入失败退出1；固定相邻文件importlib加载修复后冻结9363，
另14行真实-I subprocess入口回归1PASS4.29s。该editable源码环境证据只属parser/prepared。

## 原完整双平台工程

[foundation36868449137 / attempt1](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/36868449137)
准确head9363；Python3.13/Node24，原18steps两平台全部success，无重试或自建workflow。

| 平台/job | 原完整pytest | strict | build/SDK/实际wheel分发 |
|---|---|---|---|
| Windows110389754113 | 1151PASS/5SKIP/75warnings，2004.15s | 119files PASS | sdist+wheel、SDK1.14、13packages/resources/installed verifier/node PASS |
| Ubuntu110389754298 | 1153PASS/3SKIP/75warnings，450.13s | 119files PASS | 同原完整流程PASS |

包括原poetry install、npm ci --ignore-scripts、python -m pytest -q、tools/typecheck.py、
python -m build、npm run check:sdk、原wheel安装后-I tools/check_distribution.py --check-node。
原始元数据/命令/exit0/raw：证据根logs/ci9363-checkpoint-03.json、ci9363-full-logs-first.*。
首43ab run36867656932历史分列；其job日志API两次EOF首错误保留，不以其结果代签9363。

## I 独立安装

证据根R=`C:/Users/DW/orca/workspaces/Morphogenesis/morph-research-cases-integration-1002-state-ctx2e1675f71616`。
最终安装X=`R/lf-corrected-installation`；新CPython3.13.13 venv、固定GitLF归档、自建产品wheel、
非editable COPY安装；仅复用自己不可变公共依赖下载缓存，不借Owner环境/node_modules/测试产物。
实际科研入口为X/venv/Scripts/morph-research.exe，checkers来自X/sources/core-9363固定归档。

| 实际门禁 | 结果 | X/logs原始证据 |
|---|---|---|
| git -c core.autocrlf=false archive / uv venv/export/build/offline install | exit0；全部归档成员逐字节对Git | 01–06命令/输出/exit |
| strict Git/archive/实际wheel/site、noneditable/nlink1 | 16product+4coreinputs PASS；93active锁定依赖+core/product=95packages，两case binding verified | 07-strict-verifier.*，08-install-verification.json，10-source-provenance.json |
| installed version/两case setup-assets、doctor | 全exit0，自己的原锁Node依赖 | 11–15 |
| 两checker-I-B --help（I worktree） | 全exit0，后改用固定归档重新验收 | 16–17 |
| 固定9363归档两checker实际-I-B --help / Git blob校验 | 全exit0，39948/538f真实字节一致 | 20–21 |
| 原完整产品50项（补齐Node前置后、新temp） | 50PASS65.54s / exit0 | 18-product-full50-after-assets.* |
| 正式只读历史audit | exit1：原case06 checker PASS；author5/third6 SAT、peer0 NOT_SAT；六DBsidecars字节/mtime相同 | 19-readonly-historical-audit-first.* |

额外pending-auth离线NIST init/inspect/observe均exit0，replication入口exit2正确拒绝pending auth；
无native归档/observation。观察器两次错误预期dependency字符串而失败，保留22纠正记录；
产品未变、CLI未重放，额外synthetic离线fixture未执行，原50门禁不受这些额外观察器代替。

## 首失败保留及边界

- 公共依赖首UV opentelemetry-api下载timeout、第二窗口timeout、offline缺SciPy、urllib63.02s部分7340032bytes和curl120s/exit28部分24946496bytes保留。
- 新copy有界curl恢复exit0/40.78s，SciPy36622841bytes与原lock SHA256完全匹配后标准offline安装；不是科研请求重放。
- I首名为LF的archive实际CRLF，严格verifier首exit1保留；不归一化冒通过，另新X显式命令级autocrlf=false归档/新venv/wheel。
- X首次完整50为7FAIL43PASS63.82s，因我漏正式setup-assets导致SDK前置失败；原9日志不覆盖。原锁Node安装后相同源码/断言的18完整50绿分列。
- C原116PASS1FAIL618.16s、08b首121PASS1FAIL204.21s；B3.068s RED、默认hardlink13/14 RED和旧P CRLF安装RED全部保留，不以新绿洗掉。
- 旧01–06 raw/clock/RED/unknown及旧case06原完整PASS/peer新标准NOT_SAT只读。

## 新NIST首真实失败与安全封存

唯一新swarm `research-formal-1002-nist-01`，R/live下host/project/state/profile在创建前实际不存在；
固定X正式init首次exit0，仅一次新clock。原精确owned服务安全核验后启动，未新建服务/容器。
复合准备命令首被工具自动审查拒绝、CreateProcess未执行；root给最小单动作正常审查处置后，
docker start、纯apply_patch配置和各正式CLI动作分别执行；未禁用/绕过审批。

原始证据分别位于R/live/research-formal-1002-nist-01-host及research-formal-1002-nist-01-state。

| 正式阶段 | 首次实际结果 | 对应host/state内原始证据 |
|---|---|---|
| interrupt | CLI exit0；native UUID01a0f7df-bcbd-7cd3-8aec-e2dda578d278，cancelled/exit1，55.5414s/5tools，guard interruption=true、warnings2/errors0 | formal-interrupt.*、interrupt-observation/native/audit、interrupt-actual-summary.json |
| 实际TTL | token1 expiry1790865114.4019966；观察1790865110.3096352余4.09s，实际5s等待后过期 | ttl-expired-before-resume.json；未手工expire/改账本 |
| 同UUID resume | 正式首exit1；native failed/exit1，12.0067s/0tools，native stdout空、stderr747bytes，remote/usage/cost未知 | formal-resume.*、resume-observation/native/audit |
| 原完整固定归档checker | FIRST exit1，FileNotFoundError缺replication-observation.json；未补造文件/放宽断言 | full-checker-first.command/stdout/stderr/exit |
| 科学事实 | 原账本1claim/1renew、0stale拒绝、0research_execution、0execution_unconfirmed，experiments空；无候选/继承/adoption | resume-first-failure-summary.json、formal-observe-after-failure.* |

首恢复的主错误是官方`thread-store conflict ... already has an active writer (code -32600)`；
前置两条`codex_models_manager::manager ... failed to refresh available models: request timed out`分列。
恢复没有完成两个合法旧token拒绝/freshclaim，也未开展任何实验；peer/third和synthetic均停在NOT_RUN。
原生remote effect未知不能由0tool重标known，trusted科学未派发单独记录。

guard的interruption=true不等于完整owned树退出：14:36只读核验仍存在初次interrupt链
Node78292→Codex81300→Python82928→77316（原creation14:30:29–37Z、精确新case exec、非resume）。
与active writer主错误一致，归原A native lifecycle/Windows owned清理域；I不修改领域代码。
root授权逐PID/creation/完整命令身份复核仅清该owned链；实际操作前四PID已全部退出，
没有执行任何Stop-Process，退出原因不推断。14:41:03Z精确case/UUID匹配进程集为空。
保留owned-native-closure.json的首非零、owned-cleanup-actions.json的already_exited和after.json实际零。

原fullID eb6152fbdee01a0044cc1fdd881cf05c00dbbf3905411bc6c5a480f6a7141ec6
已docker stop exit0并只读核验exited；实际compose_project为morph-research-c-0930。
未实验故无sandbox创建/销毁可冒称，其他容器/终端/全局配置均未操作。
原nist-01不重放、不重置clock，不切model/provider/endpoint/key，不把writer清零回写首恢复成功。
当前I Task保持active等待root原Owner修复、新冻结集成与明确新unique科研释放；未worker_done。

新NIST与synthetic各需三distinct native UUID/twoCLIbrands/三once实验、各role当前token有效成功续租、
真实作者中断/TTL/sameUUID恢复及两合法stale拒绝、复现/文件验证批准应用、第三role本地再验证继承和唯一adoption。
每类完整原checker+正式audit实际PASS前不能签task_live。原900s/64tools/3600runtime/3attempts与阈值保持；
unknown不重试，usage/cost未知保持null。真实密钥仅产品正式context读，不输出值或hash。
更多Agent、EvoMap、桌面、Hub/main/tag/发布不在授权范围。

## owned Windows 进程修复后的新冻结工程验收

CORE SOURCE **bf67c1a4134a25d009cff2acccbfab027999bea6**，普通合并A
56ee35bcc31ab704ba53884b1ba96e3c93d00c4c；仅原native process/windows_job及其测试变化，
原日志/锁/workflow/科学及两个checker blob保持。产品SOURCE
**dfbc88cbc5fb90f41f6ba01a0f5d16a5a59294fa**，REPORT
e9a68668ac1e15038faaa3b04a34e2a5aa0c9f4a仅文档；产品只重新pin该core。

[原完整foundation36879998711 / attempt1](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/36879998711)
准确head bf67，两个独立平台全部18steps首次success：Windows110429046089
1154PASS/5SKIP/75warnings/1649.81s，Ubuntu110429046228
1153PASS/6SKIP/75warnings/359.69s。两平台原poetry/npm安装、全量pytest、strict119files、
sdist+wheel、SDK1.14、实际wheel13packages/resources/verifier/node检查全通过。
完整raw及准确run_attempt/head/job/step元数据在R/native-repair-bf67/logs的
ci-bf67-{windows,linux}-job-api-first.*与ci-bf67-final{,-jobs}-first.*。
首Linux gh run view --log因整个run尚未完成退出1保留，不属于测试RED。

新独立安装X=`R/native-repair-bf67/installation-dfbc`，CPython3.13.13新venv，
新GitLF归档/自建wheel/非editable COPY安装及新Node依赖；不复用旧环境或Owner产物。
Git/archive/实际wheel/site严格bytes为16产品+4注册输入+3native文件，95packages
完整pins、direct_url准确bf67/noneditable/nlink1和7Node原锁全部通过。
X/logs/07–17记录原始安装和正式version/双case setup-assets/doctor、两固定归档checker help；
18原完整产品50首次 **50PASS67.45s**。19只读历史audit首次exit1是原case06
peer0 NOT_SAT（author5/third6 SAT），subject旧版本与generator新版本分列，六DB/sidecars
字节与mtime均未变化。08-install-verification.json及10-source-provenance.json绑定准确来源。

额外prepared NIST21与synthetic22正式init/inspect/observe均exit0，未准备replication
exit2/formal_role_dependency_not_completed，未创建native observations且不存在key仍不存在。
synthetic21首次误用NIST代码目录导致init exit2，project/state未创建；operator RED原样保留。
另全新prepared02从可信registered plan取目录demo/research_cases/synthetic_linear_regression
后通过，未修改业务或原50断言。以上只属engineering/prepared，不能替代实际科研。

以上工程完成时尚待live release；旧nist-01始终不恢复/重放。后续实际结果如下，SOURCE不变。

## 最终两案例完整 task_live 与紧凑验收清单

root release msg_64e4732a7bb4 后，从同一X正式入口执行新
`research-formal-1002-nist-02`、`research-formal-1002-synthetic-01`。
各project/state/profile/host先确认不存在，正式init各一次；可信registered plan提供不同程序目录。
作者均真实claim/renew后owned中断，原生后代实际0、科学派发0，实际TTL过期后同UUID恢复；
原token合法renew与candidate submit均被拒绝，随后新canonical token2继续。
每案例三distinct UUID/twoCLIbrands/三fresh sandbox实验，独立复现与第三角色本地再验证。
Claude是CLI品牌，provider为StepFun，actual native init model均step-3.5-flash匹配；
Codex原选定身份/model/tier、权限、11tools、900s/64tools/3600s/3attempts均未修改。

| 案例/角色 | 实际native UUID | 累计native秒/tools | 当前token有效成功续租 |
|---|---|---|---|
| NIST作者 | 01a0f816-7c60-7a62-95ae-bfa293b66896 | 230.3774/21（中断+同UUID恢复） | 2 / 5次 SAT |
| NIST复现 | 90fd24dd-3d0a-45ad-8ce0-eb69675f4a3c | 115.8514/26 | 1 / 7次 SAT |
| NIST继承 | 01a0f81d-fa75-7343-b292-f0a31608e8c5 | 195.2450/19 | 1 / 7次 SAT |
| synthetic作者 | 01a0f822-96e3-7383-b852-6d0d444720f3 | 128.0820/20（中断+同UUID恢复） | 2 / 5次 SAT |
| synthetic复现 | f8485353-f13d-4cc3-b9ec-1dbf2c52cc1e | 92.6514/17 | 1 / 3次 SAT |
| synthetic继承 | 01a0f827-b51e-72e1-b550-43d5e40200ff | 106.7188/18 | 1 / 7次 SAT |

每role只有一次registered original实验，trusted read_result绑定expected_plan/context；
全部live/succeeded/scientific passed/remote known/cleanup destroyed，科学usage/cost均null。
NIST三次Fraction重算1001行、mean50000001/5、variance1/100，实际variance绝对误差
1.1175870992530257e-10；synthetic三次slope/intercept/SSE误差0、SSE0.25，判据由C现有
ScientificAssessment提供，checker没有复制科学公式。六个run/sandbox完整身份及不可变执行token
与当前写token见各首完整checker stdout和正式audit；全部distinct。

| 首完整验收 | 命令/真实结果 | R/live下原始证据 |
|---|---|---|
| NIST原39948完整checker | X/venv/Scripts/python.exe -I -B 固定bf67归档check_research_live.py --state新NIST；FIRST exit0/task_live passed | research-formal-1002-nist-02-host/full-checker-first.* |
| synthetic完整538f checker | 同固定归档check_research_case_live.py --state新synthetic；FIRST exit0/task_live passed | research-formal-1002-synthetic-01-host/full-checker-first.* |
| 两案例正式audit | formal CLI audit +既有generator-installation-evidence；各exit0/checker PASS/allroles SAT，subject/generator corebf67/productdfbc verified | 各host/formal-audit-generator-bound.* |
| 安全收尾 | 实际owned native0；六实验known/destroyed；仅原fullID docker stop exit0/post exited、Pid0 | two-case-owned-and-science-closure-first.json、owned-service-stopped-first.json |

两案例各真实唯一AdoptionReceipt绑定source/child/ConsumptionExecution/ledger result：
NIST execution1171ca87bf104107b0e9917ea32fede7→result a879b54ed92a4c4ca2af2a02deeaa775；
synthetic executionfe0c43d3766f4e0fbe9e07c33e971d71→result5ab232c4e73541a6a48b774cec0190b8。
完整source/child资产ID、文件验证批准应用顺序、retrieved/injected/applied/adopted区分与fencing
在对应正式audit清单和原始receipt中，不手造另一套UseRecord或完成证明系统。

两checker共同SOURCE bf67c1a4134a25d009cff2acccbfab027999bea6；完整Git blob分别
39948d9615bce07b40b96eeaf5dfb263b993c6d3（NIST）和
538f6b1852ccbba3f1cef6d09ad16b2a6fe8d4f5（synthetic）。

| 案例/role | 实际run_id | 实际sandbox_id |
|---|---|---|
| NIST/author | ee7d2b102cff4a5d942e427b79d485f7 | 481fa3c1-3260-4715-9d4c-d3a86b84560e |
| NIST/replication | 867461d84a8c4ac582a61e21f68a5ee4 | 9ddcfcb6-7dcd-469f-ba9f-663827021742 |
| NIST/inheritance | af7ea7178d4a4bf681562d298963a8a3 | fc06a531-8460-485a-bd6c-268b5752eb22 |
| synthetic/author | 4652267f7bb24b34a93764ec4bcb1994 | 8763e2ae-3eaa-4cf0-9c74-89d301641e6d |
| synthetic/replication | cdef868b086846c189fe51dace6eb630 | 8581d37c-0203-4da9-94be-72c8f03ad10b |
| synthetic/inheritance | 2d26481904be4f9685a2055618403fba | f7d92153-55eb-4365-b0b0-d76a0fcf85f4 |

NIST source `sha256:448ba799e76d5c5468a938dfa8e4548058a75c747872ebf3e727ecce77953c00`
→ child `sha256:64b06772a8926af0a37ef9cde7b1e1fca279e1dd359fa7e7f0c9308ed1d447c2`；
synthetic source `sha256:1a604a80ee6f4ada38b3316f8efc012cf40c59130e15d3285c1048d447889dc4`
→ child `sha256:67fcd39a6f435170bf7e41b2e73a4189730b227baf4e070278ac2b04e2b040a6`。

NIST首次audit exit2因我首捕获文件名未遵循.json/.log接口；原错误及原文件保留，实际命令
元数据与同bytes日志补正后仅只读audit通过，未重跑checker/科研。首generator未传时binding未知
也保留，后用产品既有参数验证准确来源。安全post汇总首次PowerShell管道语法错误未执行动作，
纠正后才只读核验。所有旧RED/unknown仍原样；未因doc-only报告重跑模型或实验。
原生中断usage/effect仍unknown/null；后续CLI非零usage与其报告cost保留原raw，不能解释为
实际已结算费用或把synthetic0当零费用。科学运行usage/cost未知与native报告分列。
本次只签当前冻结双案例完整闭环；Linux/WSL native现场、Notebook/卷、更多Agent、EvoMap、
桌面/main/tag/Hub发布未执行且不在本轮。报告Commit与CORE SOURCE分列，文档正常push。
