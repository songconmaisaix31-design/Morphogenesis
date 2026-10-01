# I / 两类科研案例集成与独立验收

工程和独立安装已通过；root `msg_35c7ce0634cd` 明确释放两类新真实案例。
本阶段两类新 task_live 尚 NOT_RUN；旧 case06 不能替代新闭环或新有效续租标准。

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

新NIST与synthetic各需三distinct native UUID/twoCLIbrands/三once实验、各role当前token有效成功续租、
真实作者中断/TTL/sameUUID恢复及两合法stale拒绝、复现/文件验证批准应用、第三role本地再验证继承和唯一adoption。
每类完整原checker+正式audit实际PASS前不能签task_live。原900s/64tools/3600runtime/3attempts与阈值保持；
unknown不重试，usage/cost未知保持null。真实密钥仅产品正式context读，不输出值或hash。
更多Agent、EvoMap、桌面、Hub/main/tag/发布不在授权范围。
