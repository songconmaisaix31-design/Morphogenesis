# 策略 v0.1 独立累计集成与验收（I，1002）

当前状态：**R1 真实反馈 RED，不能冻结 v0.1**。累计核心 `9ceb3aa` / 产品 `35934f1` 保留为失败候选，等待 C 原 Owner 最小返修及独立新一轮精确累计/安装/完整工程。仅候选分支，新增科研、收费模型与 main 发布 NOT_RUN。Linux 原完整 CI 已 PASS；Windows 尚在运行，本地首全量结果为 1192 PASS / 2 FAIL / 5 SKIP。

## 范围与不可变输入

在原 morph-agent-protocols-1001 Worktree 从科学基线 `7b66f0dd0a285c1b6cf789aa3c5a41d22d655993` 新建 `songconmaisaix31-design/morph-policy-release-v01-1002`。原协议分支 `5788ca3ff78a75e3f4da4dda3e42f628c24ece00` 保留；根工作树 `2957b408ce922369a595a8acd43a882eb85897d3` / WIP 不操作。

协调器正式 follow-up 替换早期 Task 阶段 SHA：

| 输入 | SOURCE | 单独 REPORT |
|---|---|---|
| B | `4ed6561504c56288e2335d88da72bd172b1c2a7f` | `62e9277ef8dd8615cdc69a647892d113cebf92a8` |
| C | `9796d23c1f978b96baec5b8625ced55aa98816ea` | `8770ac46f7b1d23e9f53ec82dfd1214cb34a77c5` |
| D | `69f586e79adb23cae5d6bb21f3c46e22b0cc850e` | `d5b3db8cf68f4cb1416b2cf8ed60eb298f797ea4` |
| 主控治理 | `1f47d0ddf0f24a6a44aedcbdff826a885cc69d4c`（包含原要求 cf7876） | 不作产品源码 |

C SOURCE 已包含 B/D SOURCE，经 Git ancestry 验证。累计核心 SOURCE `9ceb3aaef16a7f65a8a457d525e01202150ac1ab` 已正常 push，远端 exact；源码冻结，已 Handoff 主控供 A pin。后续 B/C/D REPORT 精确普通合并为 `c03c9d2b18a77628f59088a721c70e2f8b4796d3`，相对 SOURCE 只有四个文档变化，不替换产品 pin。I 仅写本报告和必要独立行为验收；领域错误退原 Owner。

两原完整科学检查器保持 Git blob / assertions / bytes：`tests/integration/check_research_live.py` = `39948d9615bce07b40b96eeaf5dfb263b993c6d3`；`tests/integration/check_research_case_live.py` = `538f6b1852ccbba3f1cef6d09ad16b2a6fe8d4f5`。`.github/workflows/check.yml`、`poetry.lock` 及原检查器相对基线无 diff。

## 独立环境与证据位置

I 私有根：`C:/Users/DW/AppData/Local/Temp/morph-policy-I-1002-2baebea8415f`。新 Git archive、私有 venv、Poetry 原锁导出及 `uv pip sync --require-hashes`；不使用 Owner venv/node_modules/artifacts。原日志保存在该根 `logs/`。完整原 workflow CI：`https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/36955261297`，精确 head 为累计 SOURCE；Windows/Linux 尚在运行。

A 最终产品 SOURCE `35934f1e3afcbb6a2028a14fe998611c4cbd509b` / docs-only REPORT `05626f7a278fec7d3e73ee2edd6c4a63d6f76767` 已正式交付；核心 pin 为累计 `9ceb3aaef16a7f65a8a457d525e01202150ac1ab`。I 最终产品安装使用独立 `product-final-installation/`，Git 归档与 Git VCS 构建均仅子进程指定 LF，COPY 非 editable 安装，固定 Git core 实际 `direct_url.json` 绑定 SHA。实测 Git/archive/自建 wheel/site 全字节核对 17 产品及 181 核心文件，nlink=1；复用原 audit 的 `logs/08-install-verification.json` 和 `10-source-provenance.json`，不建立新证明框架。首批不合格安装保留在 `product-installation/`，不得用于最终门禁。

主控指出后已修 Delivery ACK：首批完整读取后以 deliveryId 逐批 ACK，原遗漏导致 FIFO 后续消息延迟，但未丢消息或创建新 Task。主控要求复用 A 原完整产品测试和其三项 policy/JUnit traces；I 删除了自己尚未提交、未执行的重复验收脚本草稿，只维护本报告。

## 首次失败及当前验证

- `00-archive-first-red.txt`：PowerShell `--output=(...)` 解析成额外 tree-ish，archive 未创建；修正参数后新证据成功。
- `00-tar-first-red.txt`：Windows tar.exe 对四个中文文档路径失败；部分 `core-source` 保留未用，Python tarfile 在新 `core-archive` 完整解包。
- `01-export.txt` / `02-core-sync.txt`：原 poetry.lock 导出及哈希约束同步通过。
- `04-npm-ci.txt`：全新 archive 中 `npm ci --ignore-scripts` 通过。
- `03-core-build.txt`：完整 build 首次失败，现有 pip 镜像安装 poetry-core 返回 HTTP 403；后续仅子进程设置官方 PyPI 重跑，不修改全局配置，结果待记。
- `05-core-build-official-index.txt`：完整 build 重跑 PASS；`07-core-typecheck.txt` 121 源码 strict PASS；`09-sdk.txt` SDK PASS；`11-wheel-distribution.txt` 13 包 installed wheel/resource/verifier/Node PASS。
- 核心首次 `06-core-pytest.txt` 仍在完整运行，已见两个 F。首轮仅同步依赖、未安装项目，且 archive 受全局 autocrlf 影响；不在运行期间改变环境、不提前归为领域缺陷。另行准备全新 exact LF archive / 非 editable wheel / 私有 core-final-venv，待完整首结果明确后新一轮验收。
- 产品首 `product-installation/logs/02-dependencies.txt`：hash 模式不接受 Git dependency，无安装；原 frozen export 分离哈希依赖与完整 SHA VCS，分别强制哈希 / 实际 Git 安装。
- 产品首 `09-setup-assets.txt`：uv 默认 hardlink 的核心源码 nlink2 导致 AssetSafetyError，COPY 重装同 SHA 后通过，不改守卫。
- 首 `08-verification-command.txt`：Git archive 受 core.autocrlf=true 转 CRLF；同语义不等于字节一致。首 archive/wheel/安装保留，以新 LF archive 和新 venv 重做。最终 LF 环境首次字节检查又发现既有 VCS wheel 为 CRLF；仅 Git 子进程指定 LF + `--no-cache` 真 VCS 重建后 `08b-verification-command.txt` 的 17/181 字节核对 PASS，不修改全局 Git 配置或 direct_url 元数据。
- Linux CI 原始日志 `logs/20-ci-linux.txt`：1193 passed / 6 skipped / 75 warnings，448.57s；121 源码 strict、build、npm/SDK、wheel 安装和隔离 distribution 全 PASS。Windows 尚未结算，不签双绿。
- C 旧完整 CI `36915351295` 首 RED（Linux 1190 passed / 1 failed / 6 skipped，Windows cancelled）、B 首 FC schema RED、A setup-assets 首 RED及 D 原首 RED 保持各自原报告，不由后续通过重标。

## 待完成门禁

R1 中已完成的契约/来源/历史复核不能替代新候选验收。等待 C 原 Owner 修复真实合法 applied 结果的反馈来源绑定，再由 I 精确合入新 SOURCE、正常推送供 A 同 Owner repin，并在新 archive / 新环境执行完整双平台工程与正式产品入口。原 R1 correct-env 整套复跑按主控指令暂不执行，避免重复验证已存在真实领域缺陷的旧组合。contract_local 不升级为 task_live；D 最终领域状态与版本由 D 同 Owner 后续 Task 补录。

历史 canonical 根 `R=C:/Users/DW/orca/workspaces/Morphogenesis/morph-research-cases-integration-1002-state-ctx2e1675f71616`，两 state 为 `R/live/research-formal-1002-nist-02-state` 和 `R/live/research-formal-1002-synthetic-01-state`，各 `-host` 保存原完整 checker command/exit/stdout 以及原 audit。历史安装 `X=R/native-repair-bf67/installation-dfbc`；subject 为 core `bf67c1a4134a25d009cff2acccbfab027999bea6` / product `dfbc88cbc5fb90f41f6ba01a0f5d16a5a59294fa` / REPORT `e9a68668ac1e15038faaa3b04a34e2a5aa0c9f4a`。I 的新 core/product 仅为 generated_by，不能成为旧科学 subject。

原 full checkers 的默认构造器会初始化 SQLite。主控明确允许仅 I 独立子进程绑定产品现有 `checklist.ArchivedLedger` / `ReadOnlyAssets`，运行原 checker 未修改字节的全部断言；真实 SQL、mode=ro/immutable/query_only，保留 canonical 配置/身份/限制/时钟，核查无非空 WAL/journal 和源文件 bytes/mtime 前后不变。此应记作 readonly full archive checker（instrumented constructors），不叫完全原 argv 的新 task_live；原历史 argv/两 exit0 保留。不得 mock 返回、剪断言或新增读账本框架。

## R1 独立结果与真实返修 Handoff

最终 LF 安装的正式 `version`、`setup-assets`、NIST 与 synthetic 的 `doctor` 均 exit0。neutral cwd 的 installed `python -I -B -m pytest <exact product archive>/tests --import-mode=importlib`：**53 passed / 99.39s / exit0**；原完整产品测试无修改，标准 JUnit `product-final-installation/logs/15-installed-full-product.xml` 保留原 traces，抽取为 `16-policy-junit-traces.json`。实际标准 MCP 11 名称、正式 startup/env/config、两合法候选、成功 claim/主动覆盖、routing sequence7、当前 token renew、非法 scope/依赖/能力拒绝均为独立 contract_local。推荐 author，实际 policy-other，overridden=true。

离线 mock 持久科学 lineage 的正式 CLI 概率：policy-higher 从 `0.5197813505320237` 到 `0.5207708366731852`，后 unknown 样本未增加，概率 `0.5207738904905898` 的微小差异是正常墙钟衰减，不能说概率字节相同。幂等样本=1、新派生库重建与源 state 不变由原测试断言核验。此是 mock 契约证据，非真实 native Agent 自主改变或新科研。

两原完整 checker 的新只读复核 `logs/30-readonly-full-checker-nist.json` / `31-readonly-full-checker-synthetic.json` 均 exit0，全部原断言执行，各 canonical state+workspace 115 文件 bytes/mtime 前后不变。bootstrap 为私有根 `readonly_full_checker.py`，使用最终安装 Python 的 `-I -B`；仅两构造入口绑定既有产品 facade，科学 checker 文件/阈值/断言不改。输出明确 historical_readonly_reverification / new_task_live=not_run，历史 subject bf67，生成器9ceb。

原正式 `morph-research audit` 两 case exit0：`logs/48-audit-{nist,synthetic}.{stdout.json,command.json}`；旧 subject core bf67 / product dfbc / REPORT e9 和新 generated_by core9ceb / product359 均 binding=verified，三原实验、原租约与唯一采用事实保持历史身份。默认 policy 各读两次，canonical state 共70文件 bytes/mtime 不变，反馈重复输出一致，无新学习；已完成历史档案无候选，不用它宣称概率排序变化。首次 audit 误传 I worktree 作为 core-repository，与原 checker command 的旧 integration cwd 绑定不符，exit2 / case_binding_mismatch 保留在 `logs/46-audit-nist.*`；按原 actualargv 修正后新48通过，不修改原 command/evidence。

**真实领域首 RED：** `logs/44-historical-review.txt` 和 `49-historical-remaining-correct-binding.txt`。两旧 canonical 档案三任务 completed、原完整科学 checker 全 PASS、唯一真实 AdoptionReceipt/ConsumptionExecution 存在，但新正式 policy feedback **仅 author scientific_result live**，遗漏 replication scientific_result 和 inheritance scientific_adoption。原 C `swarm.feedback.trusted_facts` 对非 evidence_submitted 的合法 applied 结果要求 `result.report_id`，而正式原结果没有该键，查询 report 得到 None 即跳过。replication 合法应用 author 源候选，其 Candidate Attempt 也不能要求属于 replication。I 未改领域、可信事实、旧档案或断言；精确只读链路 `logs/45-feedback-lineage-readonly.json` 已交 root 和 C 原 Owner 新 Dispatch。不能以本地 mock 通过或 CI 绿覆盖此真实缺口。

本地首全量 `logs/06-core-pytest.txt` 结束：**1192 passed / 2 failed / 5 skipped / 75 warnings，1112.72s，exit1**。失败一为原 isolated checker help 缺 `local_assets`，失败二为原 FC 子进程在 READY 前 stdout 空；首轮只安装依赖，未安装项目，`-I` 子进程无法使用父进程 cwd import。后续独立同旧 env 的精确 `from orchestration.fc_logging import FCLogWriter` 负 probe（`18-first-core-isolated-import-probe.txt`）确认 ModuleNotFoundError。后者的 import 原因有该新增证据支持；不伪称原子进程 stderr 已被测试捕获，也不归为已证实 SQLite 锁缺陷。原120s/30s预算、断言及首次失败保留，正确新源码安装后须新完整运行，不能只定点转绿。

| 五项停止条件 | R1 的实际范围 / 结论 |
|---|---|
| 正式入口共享策略与实际选择 | installed 正式11 MCP + 成功claim/覆盖契约 PASS；manual client，非 native Agent 新 live |
| 两合法候选可信反馈改变偏好 | mock 持久 lineage 方向 PASS；真实历史复现/采用事实遗漏 **RED**，不能整体满足 |
| 原安全硬约束 | 原产品53测试/领域原测试有支持；原核心完整首轮环境 RED，仍须最终完整双平台门 |
| 同事实幂等、崩溃/重建不重放 | 原契约与只读复核通过部分；实际旧科学 feedback 漏来源，不能签整体冻结 |
| 版本、安装与完整工程一致 | exact R1 bytes/origin/历史audit PASS、Linux完整 CI PASS；Windows待结算、本地首全量RED，且该组合已有真实领域缺口 |
