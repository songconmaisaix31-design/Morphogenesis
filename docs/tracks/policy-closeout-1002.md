# D 策略 v0.1 有限收尾

**当前状态：策略 v0.1 在 contract_local / prepared_local / manual-MCP 支持范围内五门通过，冻结并停止扩展。**
本次只补录最终记录，不运行科研、模型或重复已通过实验/工程门。root 当轮 Handoff `msg_edc529b0acef` / `msg_8e8db9590fa2` 及 PLAN `2384776969ce1a156b75423d73159cde54d9c1d6` 替换早期 9ceb/359 候选；独立 I REPORT `f5e3d33a4ca119d7d173e61fe801d3a4d36cdb09` 的 `docs/tracks/policy-integration-1002.md` 为最终验收输入。

核心 SOURCE `7062a632b8c625c05b35bdec4c36fce63a31c2a4`；产品 SOURCE `c2c2d18b3dfcf5831e8e438f92654d4bdca66fbc` 精确 pin 该核心，A docs-only REPORT `3b17cc0a7120f1d2381871b336293ee301b857de`。D 代码 SOURCE 仍为 `69f586e79adb23cae5d6bb21f3c46e22b0cc850e`，旧 REPORT `d5b3db8cf68f4cb1416b2cf8ed60eb298f797ea4` 与本次 docs-only REPORT 均不替代业务 SOURCE；本次完整 REPORT SHA 随完成 Handoff 提供，不自引用提交身份。

最终原完整 CI `36960486155` attempt1 / head7062 全部工程步骤通过：Windows 1214 PASS / 5 SKIP / 75 warnings / 1541.58s，Linux 1213 PASS / 6 SKIP / 75 warnings / 387.33s；各平台 121 文件 strict、完整构建、SDK、13 包 wheel 分发通过。I 新独立本机全量 1214 PASS / 5 SKIP / 944.11s、实装产品原 53 项 PASS（pytest 72.02s；JUnit 72.016s）；A 独立原 53 项 PASS / 62.882s。未测的 skipped 路径保留。

五门事实、旧 CI `36955261297` 精确结算、新安装 origin、原完整科学 checker 和现有 audit 路径/身份见 [策略验收](../STRATEGY_V01_ACCEPTANCE.md)。正式 MCP 的推荐、认领与主动覆盖仅为手动离线客户端 contract_local；历史真实科学 subject bf67/dfbc 与当前审查生成器7062/c2分列。两原完整 checker 仅经已有只读构造入口复核全部断言，原115文件 bytes/mtime 不变；不是新 task_live。

默认前100候选按 created_at/task_id，窗外不探索；评分仅建议，原账本/执行安全守卫继续裁决。投影 available 只表示有限记录可读，不是完整决策或科学/采用证明。旧 first RED、C CI1190 PASS/1 FAIL/6 SKIP 与 Windows cancelled、D40 PASS/2 FAIL及首typing、A SDK/setup RED和中断 NOT_COMPLETED、R1/R2失败、unknown/null费用均保留。初始D readiness FAIL与retry agent_unconfigured也是原生命周期失败，本正式恢复 Dispatch 不替代其结果。

新版本 native 自主选择、科研 task_live、模型/auth、main/tag/Hub/EvoMap 发布均 NOT_RUN；最终 I2 仅精确收取 D REPORT 与 root PLAN 作文档收口。以下保留 D 原领域开发与首轮验证历史，阶段性“待验”不表示当前重新阻塞。

## 范围与缺口

固定分支 `songconmaisaix31-design/morph-policy-closeout-v01-1002`，从科研 REPORT `7b66f0dd0a285c1b6cf789aa3c5a41d22d655993` 普通合入治理 `5a4fe1d2f5bdaf941493e9c195188c9a7dee408c`。原文档 ea8d 与科学 7b 分支保留，main 和根 WIP 未修改。

基线 `orchestration/fc_logging.py` 的 `observe_ledger` 在 `emit` 前推进 `_cursor`，并忽略 `emit(False)`：账本源行写入失败后可能永久跳过。`diagnostic` 只记录进程内计数与固定日志；Worker 状态未展示该失败。既有 append 会保留半截首行并在其后写新记录，却没有有界结构完整性读视图。

## 最少实现与跨轨接口

- 保留原 1 秒 SQLite append 锁、半截字节、fsync/commit 与失败不重发规则。账本读使用原表的一次有界只读快照；游标仅在确认投影后前进。写失败或读故障停止该 writer 后续自动账本投影，不影响原执行事实。
- `FCLogWriter.projection_status()` 返回 `state`（missing / available / incomplete）、`scope=fc_sidechannel`、failure_count、ledger_cursor、record_count 与固定 reasons。`available` 不是执行覆盖证明，失败计数不会因后续可读字节清零。
- 新 `swarm.fc_projection.read_projection` 对半截/无效记录、读故障、并发变化、字节/行数边界返回 incomplete；不输出异常文本、原始坏行或秘密。
- 显式 `rebuild_projection` 只写新目标，从可信已有六类 FC 记录及原账本 routing/claim 补充有限投影；保留原记录/序号，不覆盖源，不执行/学习。源 partial 与输出写故障仍 incomplete，不凭新文件语法完整洗掉原错误。

Worker `_status` / `_audit` 最少可见性接线已 Handoff 唯一 C `ctx_72737f3d2607`；D 不改 Worker 或 observer。状态字段仅观察，不能作为执行、认领、奖励、重放或采用权威。

## 原 D 领域验证与证据（历史）

本轮独占开发环境与原始日志：工作树 sibling `morph-policy-closeout-1002-state-ctxa1febd889687`。CPython 3.13.13；从原 poetry.lock 导出依赖，在 fresh venv 安装；本地开发使用本 WT editable 以验证原源码/子进程测试，独立 I 的最终非 editable 安装另验。只在测试进程设置 BLAS/OMP/MKL=1。

准备时 `poetry export` 无插件首次 exit1 保留；随后独立 tool 环境加载既有 export 插件导出锁，未改锁或全局配置。首 focused strict 为 1 类型错误（emit 的默认 duration 与 kwargs），已显式传入 duration=None 修复；`strict-first.log` 保留。

| 命令 / 门禁 | 首结果与后续验证 | 原始证据（上述私有根） |
|---|---|---|
| `python -m pytest -q tests/swarm/test_fc_projection_v01.py tests/swarm/test_fc_logging.py` | 首 40 PASS / 2 FAIL，114.95s；原 logger 34 用例全部首次通过，新 8 中 6 通过 | `pytest-first.log`、`pytest-first.xml` |
| 同新测试文件 `-k 'failed_ledger_append or fsync_unknown'` | 两个新测试首断言误要求 cursor=0；真实账本前 6 个 enqueue 行可合法跳过。改为 cursor 小于实际失败源序号，2 PASS / 6 deselected，6.15s；生产未因该纠正再变更 | `pytest-corrected.log`、`pytest-corrected.xml` |
| `python -m mypy --strict orchestration/fc_logging.py swarm/fc_projection.py` | 首 1 类型错误；emit 的 kwargs 可能匹配未显式传入的 duration，改为 duration_seconds=None | `strict-first.log` |
| `python tools/typecheck.py` | 修复后完整 strict：120 source files PASS | `strict-final.log` |
| `git diff --check` 与原 checker Git blob 核对 | PASS；原两个 checker 字节/断言未变 | 当前 SOURCE Git 对象 |

新增 8 个行为门最终全通过：首轮 6 PASS，加纠正后 2 PASS；这组结果与原日志 34 门构成合并证据，不声称有一次全 42 绿的运行，也不重标首 RED。新行为涵盖真实锁耗尽、fsync 写后失败不重发、同 writer 并发观察、缺失只读源不建库、partial/变化/读故障、六事实完整复制而不再执行、不同来源/新目标及输出失败拒绝。所有首次结果原样保留，不删除原门禁断言或阈值。

未运行全库/双平台 CI、模型/auth/API/MCP 科研、实验或容器；完整工程由最终 I 在累计 SOURCE 一次执行。跨轨新接口尚不在本 D 单分支中，C 在合入准确 SOURCE 后完成 Worker 可见性门。主控确认 D 先交 prepared/local 候选；待累计核心工程和 A 产品最终 pin 到位，本 Owner 在新 Task 补录领域验收版本，I 只独立检查与集成，不代写 D 报告。

版本、五停止条件、首版 100 候选窗口与复用产品 audit 清单见 [策略验收](../STRATEGY_V01_ACCEPTANCE.md)。原 NIST blob `39948d9615bce07b40b96eeaf5dfb263b993c6d3`、synthetic blob `538f6b1852ccbba3f1cef6d09ad16b2a6fe8d4f5` 不变；历史科研只读证据不能签本轮新 task_live。
