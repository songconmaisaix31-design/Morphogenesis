# FC 日志边界窄修 · 0930（Owner self-test）

- Run `run_5b66cce8b4b8`；Task `task_9a9daee53406`；Dispatch `ctx_add4c83b0089`。
- 原 Owner、worktree 与 branch 连续：`morph-fc-stable-runtime-0930` / `songconmaisaix31-design/morph-fc-stable-runtime-0930`。clean 基线 `090b6920336ae8bcce407c215aa4c01f29c4835c`，稳定运行时源码阶段 `0cf04ab5548c42d1f546f675843cfa50b39d67ca`。
- 本次原授权三路径；实测 Handoff `msg_f7bb759faa98` 后，总控以 `msg_0eeae51f34d0` 批准同一 Owner 增加 canonical helper 与既有安全测试。最终唯一 write_paths：`orchestration/fc_logging.py`、`local_assets/paths.py`（仅 no_links 与 stdlib 导入）、`tests/swarm/test_fc_logging.py`、`tests/swarm/test_assets.py`（两者仅增加回归）、本报告。不改原 R 四个代码/测试或旧失败报告。
- Scope 变化直接依据本次派发：R 原完整适用回归 **323 passed / 1 failed**，R 相同单节点诊断 **1 failed**；D 原 focused **42 passed / 1 failed**（D 数值由派发提供，未拿旧 CI 或其他轨 green 覆盖）。三次均是 `test_concurrent_append_and_partial_tail_preserve_facts`，既有 `fc_logging.py:142` 的 `timeout=0.05` / `BEGIN IMMEDIATE` / `database is locked`。原 R 失败档案保持不变。

## 一页诊断与窄修计划

1. 在源码仍与基线一致时，用 stdlib profiler 只读计时真实调用；诊断 JSON 与本地 JSONL 留 OS TEMP。有限 serial append 和原三线程/六 append 形状用于测量，不作为验收；分别记录验证、protected/no_links、序列化、scan/append/flush/fsync、SQLite 获取/提交及持锁时间。计时自身开销、未测项与根因未知均明示，不据 CPU 重叠判环境原因。
2. 实测后决定最小修复；若无法在固定 50ms 期限、原断言和并发度内可靠实现，则给出设计阻塞并 failed。不得添加无界锁前排队、等待、自动重试、锁注册表、队列、索引或证明系统。
3. 安全等价须说明受保护源码、symlink/junction/hardlink、检查后的替换与锁内重检查；保持行序、partial tail、flush/fsync 和失败不会重发/覆盖 completed。只增加必要真实安全/行为回归，原测试原样保留。
4. 代码 commit+push 后，在精确代码 SHA 串行运行整个原 `test_fc_logging.py`、必要安全/Worker 回归与 strict；记录实际命令、exit、选择与失败。报告 doc commit 单列，remote exact/clean/写权核对后交接 I；全量/build/SDK/分发/双平台 CI/合并 SHA 验收留 I。

## 当前事实

已读取本树 AGENTS、包 README、收口计划与旧 R 报告；本次 check 无待处理 FIFO。已有锁定 `.venv` 和 Node SDK 沿用，不重装。

基线真实计时命令：`.venv/Scripts/python.exe C:/Users/DW/AppData/Local/Temp/morph-fc-log-baseline-diagnosis-0930.py`，exit 0（诊断完成，不是测试通过）。脚本只用 `sys/threading.setprofile` 观察原真实调用，源码与 `090b692` 一致；OS TEMP 产物 `morph-fc-log-baseline-0930-ri24u2rr/timing.json` 留完整逐线程事件。两次 serial append、三线程六次 concurrent append；构造 mock 任务事实仅用于诊断，六次 concurrent 中四次 append、两次 `database is locked`。inclusive 计时包含 profiler 开销，未扣除，不能据此判定环境根因。

| 实际段（ms） | count | min / median / max |
|---|---:|---|
| SQLite 持锁（BEGIN 成功至 commit 返回） | 6 | 53.44 / 84.85 / 255.25 |
| 锁内完整 check_path（含 no_links 与 protected resolve） | 6 | 32.04 / 39.05 / 215.20 |
| 锁内 no_links（上行子区间，勿相加） | 6 | 12.56 / 13.75 / 162.62 |
| 锁内 Path.open | 6 | 6.70 / 10.37 / 44.86 |
| 锁内扫描 / JSON 序列化 | 6 / 6 | 0.11 / 0.37 / 1.77；0.11 / 0.15 / 0.16 |
| 锁内 write / flush / fsync | 7 / 6 / 6 | 0.01 / 0.02 / 0.03；0.51 / 0.58 / 2.77；3.76 / 4.68 / 6.07 |
| SQLite BEGIN 调用（含等锁） / commit | 8 / 6 | 0.44 / 22.66 / 154.17（2失败）；0.17 / 0.24 / 22.64 |
| SQLite connect / pragma foreign / pragma sync | 8各 | 2.80 / 4.27 / 8.33；0.13 / 0.89 / 4.77；0.92 / 1.75 / 3.02 |
| 锁外验证 / check_path | 8各 | 57.33 / 103.52 / 8880.74；35.41 / 119.77 / 191.39 |

总控补充另一台 Windows 的独立旧代码失败：CI run `36688759422`，head `0ad1a0d06f88197c70e8909d505a6db261d2aee0`，Windows 1 failed / 916 passed，同一锁失败，Ubuntu success（由总控提供，非本 Owner 当前 SHA 验收，未独立重取）。不能归结为单机偶发。

canonical-only 修改后的同一有限 profiler 诊断：exit 0；产物 `morph-fc-log-baseline-0930-u1j96r_v/timing.json`，六 concurrent 中五 append、一锁失败；持锁 min/median/max **36.90/60.97/185.68 ms**，check_path **22.33/24.58/149.18**，no_links **6.96/7.41/114.27**，open **6.85/7.08/50.18**。该带计时观察不能替代不带 profiler 的原门禁。按总控 `msg_a7b755cf4246`，先固定并 push 最小 candidate，再单次原失败节点，不据 profiler 扩建 guard。

最小修复：canonical no_links 每 component 用一次 non-following lstat，复用 stdlib mode/reparse tag/nlink，仍拒 symlink、Windows junction 和 regular hardlink；仅 ENOENT/ENOTDIR 继续走缺失路径，其他 metadata 错误向上 fail closed。保护路径每次完整检查内复用同一次 resolve，无跨调用缓存。锁内外完整 no_links/protected 检查、open、scan/partial tail/序列、append/flush/fsync、50ms 与原 connection/emit 语义保持原位。没有 facade、重试、等待、队列、身份层或 API 变化。

中途准备/身份守卫 WIP 已保存在 OS TEMP `morph-fc-log-guard-wip-0930.patch`、`morph-fc-log-guard-wip-0930.py`、`morph-fc-log-guard-wip-test-0930.py`；未验证、未入最小 candidate。Windows 原生 stat/lstat/fstat 身份一致探针、open 子文件后的父目录 rename 被 OS 拒绝，均只是诊断，非验收。新回归覆盖真实锁拒绝不补 partial tail、锁取得后出现真实 hardlink 的新鲜检查、缺失路径/regular 祖先、dangling alias，以及注入底层 metadata PermissionError 的 failclosed。

代码 SHA 与实际无 profiler gates **PENDING**：先原失败单节点一次；成功再完整 FC logger（含真实 Worker）与适用路径安全选择、strict。最后报告 doc SHA、remote exact/clean 和五路径核对另记。

`contract_local=PENDING`（Owner，不是 I 验收）；`interface_live=NOT_RUN`；`task_live=NOT_RUN`。不调用模型/DSH/Hub/Live/部署，不改 H1、Schema、原 tag 或三 TODO。
