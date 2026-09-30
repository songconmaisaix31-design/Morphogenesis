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

代码阶段：`f72f82efc0119e2fc59a3d83536aab073bb4f4e5` 增最小源码与五项回归；随后 `f0d6f520c3e230af0c2718dbcc993a4a53a9ee7d` 增 native reparse tag 不存在时的短路，避免非 Windows 访问 Windows 专有常量。复用现有 CPython 3.12.13 stdlib 原生 lstat/mode/reparse API；没有复制第三方实现。两次 conventional commit 均有 `Swarm-Agent: codex`，无 force；f0d6f52 push 后 `git ls-remote --heads origin songconmaisaix31-design/morph-fc-stable-runtime-0930` exact match、tree clean 后才开始以下检查。guard WIP 不在提交中。

## 实际门禁与 Handoff

以下全部在精确代码 SHA `f0d6f520c3e230af0c2718dbcc993a4a53a9ee7d`，无 profiler、串行 slow checks；进程内 `OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=MKL_NUM_THREADS=1`，pytest 默认 OS TEMP，无 source-tree basetemp。命令均前缀 `.venv/Scripts/python.exe`；OS TEMP log 前缀 `morph-fc-log-f0d6f52-`（node/full-logger/path-safety/strict.log）。

| 真实命令（上述 Python 前缀） | exit / 结果 |
|---|---|
| `-m pytest tests/swarm/test_fc_logging.py::test_concurrent_append_and_partial_tail_preserve_facts -q` | 0；1 passed / 6.49s，修改源码后原失败节点单次实跑 |
| `-m pytest tests/swarm/test_fc_logging.py -q` | 0；29 passed / 50.74s，全部原文件加两项 native 回归 |
| `-m pytest tests/swarm/test_assets.py -q -k 'no_links or hardlink_path or alias_link or protected_target or unsafe_paths or prepared_baseline_and_own_swarm_tree or fixed_frozen_mainline or native_worktree'` | 0；21 passed / 38 deselected / 21.84s；未把 deselected 说成通过 |
| `tools/typecheck.py` | 0；Success: no issues found in 89 source files |

精确依据：`local_assets/paths.py:47` canonical 单 lstat、`:56` native tag 缺失短路；`fc_logging.py:114` 完整保护检查、`:143` 原 50ms transaction/锁内重检查与 open 仍在原位。`test_fc_logging.py:136` 原三线程六 append / partial tail / 序列节点不变；`:188` 真实 Worker 的 14 字段与未知成本 hold；`:212` 日志失败仍 completed 且不重发；`:287` 新真实 SQLite 锁拒绝保持原 bytes，`:310` 新锁后 hardlink 拒绝。`test_assets.py:25/:35/:54` 增 missing/regular-ancestor、dangling alias 和 metadata PermissionError 回归，`:255/:263` 既有真实 hardlink / alias；只读检查测试遗留 alias 与 dangling 两者均 **Windows junction**（tag `2684354563`），未冒充 native symlink 或 Linux gate。PermissionError 项是 primitive 异常注入，其他对应项为真实文件/锁操作。

核对：基线至代码 SHA 只五条授权路径；源码实际 **15 insertions / 5 deletions**，两个测试只增 51 / 44 行。AST 对比全部原 logger 17、asset 37 个顶层 function/class 定义不变；原 R 四个代码/测试与旧失败报告逐路径 diff 空。代码 SHA 所有命令后 tree clean。最后仅本报告增实际证据，报告 doc SHA 与最后 remote exact/clean 回执由最终 Handoff 单列，避免自引用 SHA；不在 doc SHA 重跑源码不变的门禁。

限制：带 profiler 的局部竞争仍失败且观察开销未知，不删除该诊断、不据局部实际 green 宣称 Windows 全量或稳定时延保证；根因的所有贡献与环境影响保持未知。现有安全策略位置与检查保留，single-lstat 对非 link 组件给同一 mode/nlink 决策，symlink/junction 不跟随；仅明确 missing 继续、其余 metadata 异常更保守 failclosed。没有新 prepare/身份层的检查移动或替换窗口。最终最小修复 Owner 门禁已过，独立 I 仍须精确合并 SHA 验收。

NOT_RUN：本次全量、build、SDK 专项、分发、双平台 CI、I 独立 merge SHA；Windows native symlink 创建（本环境原生创建拒绝后走 junction），Linux/native 无 tag 分支实际运行；模型 API/DSH/Hub/Live/部署/H1/原 tag 操作。38 deselected 不属于本次适用安全选择。

`contract_local=PASS`（本次固定 SHA、上述 Owner self-test 范围，不是 I 验收）；`interface_live=NOT_RUN`；`task_live=NOT_RUN`。旧 R/D/外部旧代码失败证据保持 failed，不改 H1、Schema、原 tag 或三 TODO。

## 第二次窄返修：Windows reparse API 的平台类型边界

- 本阶段 Run `run_5b66cce8b4b8`；Task `task_3652d4ea5fe4`；Dispatch `ctx_2d01027925fc`。同一 Owner/worktree/branch，开始时 HEAD/remote exact `973fe64a6403112dfd72b7de69b5661f74b7237e` 且 clean。唯一 write_paths：`local_assets/paths.py`（仅 no_links/stdlib import）和本报告（仅追加本阶段）。前面记录和原 R 失败报告原样保留，不改旧 Task 结果。
- 本次派发提供 I 新整体候选 `20ddb85562872f2e93a84295da14fd0688fcf986` 的 CI `36696567218` 真实失败：Ubuntu `python tools/typecheck.py` exit 1，`local_assets/paths.py:58` 的 `IO_REPARSE_TAG_MOUNT_POINT [attr-defined]`，89 files / 1 error；Windows matrix cancelled。此处记录派发事实，未独立重取 CI。此前运行时短路与 Windows strict green 不证明平台类型可移植性；本次修复不抹去该失败。
- FIFO `msg_00be64c8a981` 明确通知 I 实际测试父/子/后代停止 `survivors=0`、原 full 为 INTERRUPTED 且 partial/exit 留存，并准许本阶段串行验证；已处理并 ack，未把 elapsed 当许可。沿用锁定环境，不安装依赖或改工具/锁/CI。
- 最小源码 diff **5 insertions / 3 deletions**：增加 stdlib `sys`；`local_assets/paths.py:57` 继续普遍拒 symlink，`:59` 显式 `sys.platform == "win32"` 分支中 `:60` 直接读取 `metadata.st_reparse_tag` 与 `stat.IO_REPARSE_TAG_MOUNT_POINT`。mypy 据平台分支选择类型桩；Linux 不访问两项 Windows API。Windows 原生字段/常量意外缺失会抛错，未用 getattr/default/ignore 吞成成功。每组件一次 lstat、regular hardlink 拒绝、ENOENT/ENOTDIR 与其余异常 failclosed、返回 None 不变；50ms、logger 和所有其他领域/测试原位不动，无新增测试或 guard/队列/重试。
- 代码 SHA **`9f6d57417d16125d45cc2ce920c400f358b44776`**（`fix(paths): type narrow Windows reparse metadata by platform`，`Swarm-Agent: codex`）；先 commit+push，无 force，再核验 remote exact/clean 后执行下列真实检查。本阶段代码 commit 只改一条源码路径；最后纯报告 commit SHA 由 Handoff 单列，不自引用。

本阶段全部命令在上述精确代码 SHA，无 profiler，slow checks 串行；进程内 `OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=MKL_NUM_THREADS=1`。Python 全部为本树 `.venv/Scripts/python.exe`；状态/默认 pytest tmp 与 log 均 OS TEMP，无 source-tree basetemp。日志前缀 `morph-fc-portable-9f6d574-`（windows-strict/linux-platform-strict/path-safety.log）。

| 实际验证 | exit / 结果 |
|---|---|
| `.venv/Scripts/python.exe tools/typecheck.py`（原 Windows strict） | 0；Success: no issues found in 89 source files |
| `.venv/Scripts/python.exe -` wrapper 读取 `tools.typecheck.PACKAGES`，按原工具相同 `is_dir()`/`any(rglob("*.py"))` 选择、cwd/config 不变，执行下列实际子命令 | 0；Success: no issues found in 89 source files；是 Linux **平台类型检查**，非 Linux 实际行为 |
| `.venv/Scripts/python.exe -m pytest tests/swarm/test_assets.py -q -k 'no_links or hardlink_path or alias_link or protected_target or unsafe_paths or prepared_baseline_and_own_swarm_tree or fixed_frozen_mainline or native_worktree'` | 0；21 passed / 38 deselected / 32.81s；现有原断言/真实 subprocess，不新增或修改测试 |

Linux 类型检查实际完整子命令（与工具同一 15 包源集合，argv 已写真实 log）：

```powershell
.venv/Scripts/python.exe -m mypy --strict --platform linux contracts persistence bootstrap tools hub_client bridge_node orca_provision orchestration topology metabolism mocks viz demo swarm local_assets
```

路径回归含既有真实 regular hardlink/保护目录拒绝、missing/regular ancestor/dangling alias 与 metadata 异常回归；后者是原有 primitive PermissionError 注入，不冒充原生权限测试。只读检查此次 pytest-287 留存的 alias 与 dangling，均 `symlink=False / junction=True / tag=2684354563`，证明新 Windows 分支实际经过真实 junction；未将 Windows 无权创建 symlink 的 fallback 或 Linux 类型检查说成 Linux native 验收。

本阶段核对：源码 fixed SHA 时 tree clean；原测试、logger/50ms、预算/租约/ledger/breaker/fault store/provider/Schema/锁/CI/TODO 和旧 R 报告未改。最终纯报告提交前后逐路径/blob 与 remote exact/clean 回执由最终 Handoff 提供，只两条授权路径；纯报告提交不重复源码未变的门禁。

本阶段 `contract_local=PASS`，仅 Owner 的 Windows native 适用路径回归及 Windows/Linux-target strict；`interface_live=NOT_RUN`；`task_live=NOT_RUN`。本次不重复不受影响的完整日志套件；全量/actual wheel/分发/Linux 实际行为/双平台 CI/新 merge SHA 独立验收与 target 推进均由 I，**NOT_RUN** 于本阶段。没有模型 API/Live/DSH/Hub/部署、tag 移动或 H1 签字；原 R/D/logger/旧 CI 的失败及 I INTERRUPTED 保持原事实。
