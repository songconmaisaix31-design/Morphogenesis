# 策略 v0.1 验收

**当前状态：五项停止条件在 contract_local / prepared_local / manual-MCP 支持范围全部通过，策略 v0.1 冻结并停止扩展。**
依据 root 最终 Handoff `msg_edc529b0acef` / `msg_8e8db9590fa2`、PLAN `2384776969ce1a156b75423d73159cde54d9c1d6` 与独立 I REPORT `f5e3d33a4ca119d7d173e61fe801d3a4d36cdb09`。最终核心7062/产品c2替换旧9ceb/359和54bb/e806候选，历史成功与失败均保持原身份。本次仅补文档，不为文档提交重跑科学、模型或工程门。
当前版本 native Agent 自主选择、新科研 task_live、auth/模型调用及 main/tag/Hub/EvoMap 发布均 NOT_RUN；手动 MCP 离线 fixture、历史档案只读复核不升级为新 interface_live/task_live。

## 版本与现有证据

| 对象 | 身份 / 当前用途 |
|---|---|
| 历史科研核心 | SOURCE `bf67c1a4134a25d009cff2acccbfab027999bea6`；REPORT `7b66f0dd0a285c1b6cf789aa3c5a41d22d655993`，本轮开发基线 |
| 历史科学 subject / 私库产品 | 核心 `bf67c1a4134a25d009cff2acccbfab027999bea6` / 产品 SOURCE `dfbc88cbc5fb90f41f6ba01a0f5d16a5a59294fa` / REPORT `e9a68668ac1e15038faaa3b04a34e2a5aa0c9f4a`；本轮不改历史执行主体 |
| 最终核心 / 策略 | SOURCE `7062a632b8c625c05b35bdec4c36fce63a31c2a4`；policy_version / strategy_version `v0.1` |
| 最终产品 / A 报告 | SOURCE `c2c2d18b3dfcf5831e8e438f92654d4bdca66fbc` 精确固定7062；docs-only REPORT `3b17cc0a7120f1d2381871b336293ee301b857de`，私库 `docs/tracks/policy-entry-1002.md` |
| 独立 I / root 记录 | docs-only REPORT `f5e3d33a4ca119d7d173e61fe801d3a4d36cdb09`，`docs/tracks/policy-integration-1002.md`；root PLAN `2384776969ce1a156b75423d73159cde54d9c1d6`，`docs/PLAN.md` |
| B 输入 | SOURCE `4ed6561504c56288e2335d88da72bd172b1c2a7f` / REPORT `62e9277ef8dd8615cdc69a647892d113cebf92a8` |
| C 输入及原 Owner 返修 | SOURCE `9796d23c1f978b96baec5b8625ced55aa98816ea` / REPORT `8770ac46f7b1d23e9f53ec82dfd1214cb34a77c5`；反馈修复 SOURCE `fa0216aa468ea1bd71f009e4089c1872190843e1` / REPORT `a98219a22bdaa9c7dc069b0ee0c6a90035aa87f6`；续租修复 SOURCE `5e24715c7002d254dd908aea53ce82e86c12ebf3` / REPORT `992670b37b1bb8c8a04f024b4af8e5ba8dfe668c` |
| D 投影领域输入 / 报告 | SOURCE `69f586e79adb23cae5d6bb21f3c46e22b0cc850e` / 旧 REPORT `d5b3db8cf68f4cb1416b2cf8ed60eb298f797ea4`；本次只改两份文档，完整 REPORT 随 Handoff 提供，不作为核心 pin |
| NIST 原完整检查器 | `tests/integration/check_research_live.py`，Git blob `39948d9615bce07b40b96eeaf5dfb263b993c6d3`，原断言不改 |
| synthetic 原完整检查器 | `tests/integration/check_research_case_live.py`，Git blob `538f6b1852ccbba3f1cef6d09ad16b2a6fe8d4f5`，原断言不改 |

独立 I 使用安装分发元数据、`direct_url.json` 和真实 Git 对象核对核心 / 产品 / 策略版本，复用产品已有 `morph-research audit` 清单，不建立另一套 Manifest、哈希索引或完成证明。`logs/10-source-provenance.json` 的 `case_checkers[case_id]` 必须绑定真实 SOURCE、固定检查器路径与 Git blob；不制造自引用提交身份。

现有清单已区分 `subject` 与 `generated_by`：前者是历史案例实际执行的核心、产品与检查器，后者是当前安装的审查生成器。旧 NIST / synthetic 档案可以在只读条件下核对，但应保持 `historical_readonly_reverification` / `new_task_live=not_run`；旧执行不能归到本轮新 SOURCE。

## 五项停止条件

| 条件 | 需要的实际证据 | 当前本轮状态 |
|---|---|---|
| 正式入口共享策略 | 安装后原 MCP 路径的策略版本、合法候选、推荐、实际认领与主动覆盖可关联 | PASS，原11 MCP、两合法候选、v0.1、推荐author/手动认领policy-other、routing_sequence7、overridden=true与当前token关联；manual-MCP contract_local |
| 可信反馈改变偏好 | 至少两个合法候选；可信反馈前后概率方向可解释，种子/衰减分列 | PASS，正式CLI的持久mock可信lineage使概率0.5197814644677805→0.5207710255956669；unknown不增事实/样本，后续微变是墙钟衰减。历史三live事实恢复单独通过，旧completed无候选，不能代替新排序证据 |
| 安全硬约束保持 | 依赖、能力、scope、租约、预算与未知效果仍由原边界决定 | PASS，原完整产品53/本地核心1214/双平台工程与原行为门支持；advisory_only、claim_requires_recheck，Router不评估预算准入。续租>TTL和IOerror仍拒绝，不复活过期holder |
| 恢复不双学习、不重放 | 同事实同类幂等；崩溃/重建不执行模型/实验；未知学习保留incomplete | PASS，完整fixture进程终止/反馈中断门与历史三事实重复读取、各两新派生库逐值一致、samples=1、重复同步不增、未完成pair拒绝不写；原文件bytes/mtime不变。D投影不授执行权 |
| 版本、安装与工程一致 | 最终精确源码完整Windows/Linux门、产品pin、独立非editable安装、原checker/audit绑定 | PASS，7062/c2原完整CI36960486155 attempt1及独立本机全量；17产品/181核心Git/archive/wheel/site字节、真实VCS direct_url、COPY/noneditable和原两blob一致；旧subject与新generated_by均verified |

五项全部具备即停止 v0.1，不扩展 Agent、案例、全局调度或外部平台。contract_local、interface_live、task_live 分列；首次 RED、NOT_RUN、unknown 与 null 费用原样保留。

## 已有工程、安装与 audit 证据

最终 I 私有根 `R3=C:/Users/DW/AppData/Local/Temp/morph-policy-I-r3-1002-29cba60db480`；以下相对路径均在 R3。均为已有原始结果，本次只读核对，不另造 Manifest/哈希/采用证明。

| 现有清单 / 原始日志 | 实际结果与身份 |
|---|---|
| `product-installation/logs/08-install-verification.json`、`08-verification-command.txt`、`10-source-provenance.json` | 实际 core direct_url 为 GitHub VCS完整7062；产品origin为本私有根自建 `morphogenesis_research-0.1.0-py3-none-any.whl`，非editable、COPY/nlink1；17+181文件Git/archive/实际wheel/site字节一致；case_checkers分别绑定7062、原路径与39948/538f blobs |
| `product-installation/logs/15-installed-full-product.txt`、同名 `.xml`、`16-policy-junit-traces.json` | I独立新安装原完整53 PASS / pytest72.02s（JUnit72.016s），原JUnit保留MCP/CLI traces；A另一个新安装原53 PASS / 62.882s，不与I混作同一运行 |
| `logs/11-core-workflow-full-pytest.txt`、`01`–`09`原命令日志 | 全新LF archive/私有venv/原锁安装：1214 PASS / 5 SKIP / 75 warnings / 944.11s；121文件strict、完整sdist/wheel、SDK、实际wheel安装及13包分发均exit0 |
| `logs/23-r3-ci-result.json`、`24-r3-ci-run-api.json`、`21-ci-linux-run-log.txt`、`22-ci-windows-run-log.txt` | 原完整CI [36960486155](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/36960486155) attempt1/head7062 completed/success；Windows job110692862238：1214 PASS/5 SKIP/75 warnings/1541.58s；Linux job110692862438：1213 PASS/6 SKIP/75 warnings/387.33s；各平台121文件strict/build/SDK/13包分发全PASS，skip不算已测 |
| `logs/30-readonly-full-checker-nist.json`、`30-readonly-full-checker-synthetic.json` | 原两个完整checker的全部原断言exit0；仅已有 `ArchivedLedger` / `ReadOnlyAssets` 构造入口只读绑定，115原state/workspace文件bytes/mtime无变；historical_readonly_reverification/new_task_live=not_run，不冒称新科学原argv |
| `logs/43-audit-{nist,synthetic}.stdout.json`、同前缀命令回执 | 复用正式 `morph-research audit`：subject bf67/dfbc/e9、generated_by7062/c2均binding=verified；每案author/replication/inheritance三原实验scientific passed/execution succeeded/remote_effect known/cleanup destroyed，各角色effective_renewal SATISFIED；原源/子asset、唯一AdoptionReceipt、ConsumptionExecution与ledger result绑定保留 |
| `logs/44-historical-review-{nist,synthetic}.json`、`45-historical-review-command.txt`、`40`–`42`原CLI输出 | 每案原两scientific_result/一scientific_adoption共三live事实，重复读取一致，各两独立新派生库samples=1、重复同步不增、incomplete_pair_rejected_without_write=true、execution_invoked=false；115原文件bytes/mtime无变 |

历史 canonical 根 `H=C:/Users/DW/orca/workspaces/Morphogenesis/morph-research-cases-integration-1002-state-ctx2e1675f71616`；两个原 state 是 `H/live/research-formal-1002-nist-02-state` / `research-formal-1002-synthetic-01-state`，各 `-host` 保存原完整checker命令/exit0/stdout及原audit；历史安装 `H/native-repair-bf67/installation-dfbc`。现有43清单三实验摘要/唯一adoption/effective_renewal保留；实验resource_enforcement仍unknown、usage仍null，native remote_effect仍unknown，CLI报告费用不等于provider发票，缺失费用不填0。

## 原始失败与阶段候选不重标

- R1核心 `9ceb3aaef16a7f65a8a457d525e01202150ac1ab` / 产品 `35934f1e3afcbb6a2028a14fe998611c4cbd509b` / A REPORT `05626f7a278fec7d3e73ee2edd6c4a63d6f76767`：原完整CI [36955261297](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/36955261297) completed/success；Windows1194 PASS/5 SKIP/75 warnings/1494.08s、Linux1193 PASS/6 SKIP/75 warnings/448.57s，两平台121文件strict/build/SDK/13包分发通过。原根 `C:/Users/DW/AppData/Local/Temp/morph-policy-I-1002-2baebea8415f` 的 `logs/20-ci-linux.txt`、`22-ci-windows-run-log.txt`、`23-r1-ci-result.json` 保留。该组合正式policy仅读author、遗漏合法replication/inheritance仍为真实反馈RED，CI不覆盖此缺口。
- R1原本机全量1192 PASS/2 FAIL/5 SKIP/75 warnings/1112.72s仍RED；首环境只装依赖未装项目，后独立负import probe支持隔离子进程缺包原因，原stderr未被捕获不补造。archive/tar、403构建、VCS/hash安装、CRLF字节、hardlink/setup、错误audit argv绑定等原首失败及新修正结果由I报告/私有原根保留；R1correct-env整套复跑未执行。
- R2核心 `54bb8d0897eb22c5e8a52ea158606388fe64064a` / 产品 `e806f667ad9f52409364618472b5f8a6b1c922b0` / A REPORT `da18a5e32e36b44b33cee757ab5e3d8a508974e8`：原CI36957851632 attempt1仍failure；Windows1210 PASS/1 FAIL/5 SKIP/75 warnings/1248.44s，原墙钟续租stale_lease，后strict/build/SDK/wheel/distribution SKIPPED；Linux1210 PASS/6 SKIP/403.03s及工程通过、本机1211 PASS/5 SKIP/1009.72s均不能代替该Windows首RED。R2额外neutral -I完整core收集因deploy不属wheel而ERROR保留。
- C原CI36915351295 Linux1190 PASS/1 FAIL/6 SKIP、Windows cancelled；D原40 PASS/2 FAIL及首strict类型错误/无export插件exit1；A首setup-assets SDK BridgeError、诊断wrong-import RED、optional strategy观测失败、边界首断言失败、被中断15-real-policy-contracts-first NOT_COMPLETED；B首FC schema RED均保留各Owner原报告。D后续2 PASS与首轮6 PASS/原34 PASS是合并证据，不伪造一次全42绿。
- 原R2 Windows最大续租2.3321284s具体阻塞组成仍未知；C受控节奏缺陷修复和R3新完整PASS不保证任意OS长停顿。两次冗余文档CI36959528356/36959685712仍CANCELLED；日志首次下载EOF与后续同一completed-run只读成功下载分列，不称CI重跑。D初始readiness FAIL/retry agent_unconfigured保留，本恢复Dispatch正式有效。

本D收尾仅两doc普通commit/push `[skip ci]`，验证diff-check、路径、远端exact和clean；完整REPORT由完成Handoff给root/I2。最终I2文档普通集成由其Owner完成；本D未merge业务、未改PLAN/STATUS/源码/tests/schema/checkers/锁，未运行新科学/模型或重复工程门，未发布main或tag。

## 首版候选窗口

原 TaskLedger 默认 `candidates(limit=100)` 按 `created_at, task_id` 排序；Router 在该有界窗口及既有合法性过滤内计算 softmax / 探索概率。窗口外任务当轮不参加评分或探索，不能宣称全任务覆盖、公平轮转或全局最优。只记录此支持范围，本轮不实现分页或轮转。

## 投影检查与显式恢复

FC JSONL 是 side-channel，原账本与可信实验/文件/采用档案才是执行事实。`FCLogWriter.projection_status()` 为 Worker 提供有界、secret-free 只读状态，`available` 仅指当前可读的有限 FC 记录，不表示完整执行或采用证明。写入/读取故障、半截记录、变化快照或未读完窗口必须显示 `incomplete`。

账本投影写入失败时停止后续自动投影，游标不越过失败源行；fsync 失败可能已留下字节，不能以再调用投影自动重发。显式 `rebuild_projection` 仅从调用方提供的可信日志和原账本 routing/claim 事实写全新目标：不覆盖半截原日志、不改账本、不学习、不调用 Executor。可保留的六类 FC 事实、原序号和 unknown/null 字段原样复制；缺失的资产/故障/彩排事实不能从任务 completed 推造。源日志不完整时重建结果仍为 incomplete，语法可读的新文件不能清除旧失败。

## 紧凑验收清单

只引用现有安装与产品 audit 清单、原始记录位置，不复制秘密或大段 journal：

- 核心/产品 SOURCE 与各 docs-only REPORT、策略版本、两检查器实际 Git blob、安装主体与审查生成器身份。
- 推荐候选及过滤条件、实际当前-token 选择/覆盖、可信结果来源与学习幂等事实；两候选概率变化与窗口范围。
- 原生三角色、实际实验/沙箱与 known/cleanup、源/子资产及唯一 AdoptionReceipt / ConsumptionExecution / ledger result 绑定；历史与新增执行分开。
- 首命令、stdout/stderr/exit、原始证据引用、RED/NOT_RUN/unknown、权限与人工步骤；原真实费用未知保持 null。
- 投影 status / 显式新目标重建结果，完整工程与独立安装原始结果；旧 task_live 不充当新版本 task_live。
