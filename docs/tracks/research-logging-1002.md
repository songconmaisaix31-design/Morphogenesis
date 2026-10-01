# FC 日志写锁竞争窄修 · 1002（A focused / installed）

本轨仅修工程日志的锁等待。`FCLogWriter.append` 继续使用原 SQLite sidecar、`BEGIN IMMEDIATE`、JSONL append/flush/fsync 和锁内路径安全重检查；日志写锁的 SQLite 等待由 0.05 秒改成具名常量 `APPEND_LOCK_TIMEOUT_SECONDS = 1.0`。等待耗尽仍抛错，`emit` 仍返回 False、增加 `failure_count` 并只记录常量诊断。没有写后重试，没有 Worker/模型/科研重放，没有全局排队、锁注册表或新依赖。

## 固定归属与来源

- Task `task_22fdbd65e192` / Dispatch `ctx_b4dfaa3b07e1`；原 A terminal/worktree/branch 延续。
- Worktree `C:/Users/DW/orca/workspaces/Morphogenesis/morph-research-agents-0930`；branch `songconmaisaix31-design/morph-research-agents-0930`。
- 原 clean HEAD `53c4b463aa23e6424921b9fb55c280de6a2c8567`；授权基线 `874a6330febd8d8dcaf5cfc043f0254d466f6d71`，在原分支正常 ff-only。root 计划治理 `698328b7fb5ef181492bb474718fa9c5db8946da` 只读。
- 最终 SOURCE：`ec24ebb4519845bf677786e0480260bc76c85407`；首源码阶段 `41da403440acaf24d4414691077d56f1db242f6f`。独立 doc-only REPORT：以本文件所在的后续实际提交为准，不把报告 SHA 当 SOURCE。
- 唯一仓库改动：`orchestration/fc_logging.py`、`tests/swarm/test_fc_logging.py`、本报告。`TaskLedger` 默认 10 秒、`observe_ledger` 50ms、schema、半截尾处理、行位置序列、路径安全、既有执行/失败事实都不改。
- 复用现有 `swarm.task_ledger.connection` 与 CPython 3.13.13 标准库 SQLite 的原生 busy timeout；不复制第三方实现、不引入依赖。标准库 PSF 授权、SQLite 公共领域；源码沿用本仓 Apache-2.0。

root 在本 Dispatch 的明确 ask 回复中授权仅同步旧两条 `calls == [{"write": True, "timeout": 0.05}]` 参数期望到新常量。原并发测试完整 body、半截首行、六 facts、len7、序列1..6、validate、真实锁拒绝和安全拒绝断言均保留。本轨实际 AST 核对原19个函数：除这两条已授权参数期望外均一致。新增5个参数化 case：真实持锁200ms后三线程各写两条、两个独立进程各写三条、锁耗尽 emit 失败不写入、strict/emit 两种 fsync 写后失败均不重发。

## 全新私有安装与首次结果

`L = C:/Users/DW/orca/workspaces/Morphogenesis/morph-research-logging-1002-state-ctxb4dfaa3b07e1`，创建前确认不存在。Python 为 `L/venv/Scripts/python.exe`，从精确基线 archive 构建并非 editable 安装。允许的 A 同锁官方下载 cache 仅用于包下载；无复制以前任务的 venv/site/node_modules 或测试结果。所有 TEMP/TMP、basetemp、Poetry/npm cache 为本轨私有；BLAS/OMP/MKL 进程内1。无全局 index/auth/HOME/model/tier 修改。

基线准备使用 `uv tool run --with poetry-plugin-export poetry export --with dev --without-hashes --format requirements.txt` 导出原 `poetry.lock`，`uv venv --python C:/Python313/python.exe`，`uv build --wheel`，`uv pip install --link-mode copy --python <private-python> -r <locked-requirements> <baseline-wheel>`。tool/export/venv/build/install 均首 exit0，日志 `03` 至 `06`。Node 从本轮 archive 的原 package.json/package-lock.json 在私有 installed site 运行 `npm ci --ignore-scripts --no-audit --no-fund --prefix <site>`：首 exit0，99 packages；只运行本地既有 SDK/fixture 路径，不执行 Hub/科研/API。

源码候选只覆盖私有基线副本中的这两份本轨源码；新建 candidate wheel，`uv pip install --reinstall --no-deps --link-mode copy` 安装。`12-installed-provenance-first.log` 确认 logger 位于本轨 site-packages、wheel/工作树/site 字节一致、nlink1、direct_url 指向 `L/candidate-dist/morphogenesis-0.1.0-py3-none-any.whl` 且非 editable；TaskLedger 源字节与 archive 基线一致。

| 首次实际命令 / 场景 | 实际结果 / 保留 artifact |
| --- | --- |
| 基线 installed 原 `test_concurrent_append_and_partial_tail_preserve_facts`，`python -I -m pytest ... --import-mode=importlib -p no:cacheprovider --basetemp L/temp-original -q` | exit0，1 passed / 39.09s；`07-original-focused-first.log/xml` |
| 旧 installed874a 新 `test_contended_append_waits_for_real_sqlite_lock`，真实200ms持锁 / 三writers | **首次 RED exit1，1 failed / 15.85s**；真实 `BEGIN IMMEDIATE` 抛 `sqlite3.OperationalError: database is locked`，timeout0.05；`09-deterministic-first-red.log/xml` 与当时测试源码 `L/test_fc_logging-first-red.py` 不改写 |
| candidate installed 首整份 logger 文件（29原case+5新增case），测试从私有 archive 邻树读取 | **首 exit1，33 passed / 1 failed / 58.24s**；`13-fc-suite-first.log/xml`。唯一旧 protected-source 测试从 test `__file__` 推导 archive 根，而实际 wheel guard 保护 installed site 根；5个新增 case 已通过。这是非 editable 安装的同树测试布局差异，不是改业务 guard 或断言的理由 |
| 同一 installed candidate 与完整原断言，将本轮测试源码放到私有 site-packages/tests 后复验 | exit0，34 passed / 160.63s；`15-fc-suite-collocated-first.log/xml`。恢复原测试与实际 installed 模块同根的布局；首RED文件及其已生成的自有 fixture 日志不删除。该 wheel 与 Windows 工作树字节一致，尚不是 Git canonical blob 字节相同，见下文 |
| `python -I -m mypy --strict --cache-dir L/mypy-cache orchestration/fc_logging.py`，私有 candidate 源目录 | 首 exit0，Success: no issues found in 1 source file；`14-strict-first.log` |

全部 pytest 使用本轨 Python、独有 TEMP/TMP/basetemp、importlib 模式和禁用 cacheprovider；业务从非 editable wheel 的真实 site-packages 读取。原文件的 Worker 测试使用现有本地 mock/file fixture，不是模型或科学任务。fsync 故障仅在新增 failure fixture 注入，SQLite 竞争和跨进程写入均为真实本地操作。

## 冻结 Git 字节复核与精确安装

源码 commit/push 后额外字节复核的 **`18-source-freeze-bytes-first.log` / `20-source-freeze-bytes-scoped-first.log` 首 exit1** 均保留；没有将换行/AST 等价写成 byte equal。`21-source-bytes-diagnosis-first.log` 实际定位：Git logger 为10792 bytes/209 LF/0 CRLF，首 candidate/worktree/site 为10996 bytes/209 LF/204 CRLF；Git test 为22492 bytes/500 LF/0 CRLF，首 candidate/worktree/site 为22824 bytes/500 LF/332 CRLF。修改工具保留了 Windows 工作树原有行的 CRLF，新增行 LF；原 TaskLedger 基线 archive/site 则已是 Git LF。两个首私有核验脚本版本与全部日志保留，源码没有为此重写提交。

root `msg_1c2b5b243079` 确认该 SOURCE remoteexact/clean/仅两源码路径，并派原 I 在精确 Git 上独立双平台验收；本轨按批准方式执行 `git -c core.autocrlf=false archive --format=tar ... 41da403...`，在全新 `L/frozen-source-41da403` 标准库解包运行源码（继续排除异常历史 docs）。从这一只读 Git archive 构建 `L/frozen-dist/morphogenesis-0.1.0-py3-none-any.whl`，同一新私有 venv 正常非 editable reinstall；`22` extract / `23` build / `24` install 均 exit0，没有改全局 Git 或 SOURCE。

首轮 collocated 测试树只在已核验都位于本轨私有 state 的 source/target 之间移动到 `L/collocated-first-tests` 保留；新 site-packages/tests 只来自本次精确 Git archive，未借旧任务测试产物。`25-frozen-provenance-first.log` 首 exit0：logger、TaskLedger、schema 的 **Git/archive/wheel/site bytes 完全相同**；原 logger 测试和两份原 helper 的 **Git/archive/site bytes 完全相同**（tests 不属于发行 wheel，不冒称打包在 wheel）。各已检查 installed 文件 nlink1，原19函数与两授权参数期望一致；test.__file__ 推导根正是 `fc._SOURCE`。原 Node lock bytes、TaskLedger 与874a bytes保持。

41da轮正式安装 `direct_url` 为 `file:///C:/Users/DW/orca/workspaces/Morphogenesis/morph-research-logging-1002-state-ctxb4dfaa3b07e1/frozen-dist/morphogenesis-0.1.0-py3-none-any.whl`，editable false。正式 Python 是 `L/venv/Scripts/python.exe`，logger 为 `L/venv/Lib/site-packages/orchestration/fc_logging.py`。**精确 Git installed34 首次 RED：exit1，33 passed / 1 failed / 202.83s**，实际命令 `python -I -m pytest L/venv/Lib/site-packages/tests/swarm/test_fc_logging.py --import-mode=importlib -p no:cacheprovider --basetemp L/temp-frozen --junitxml L/logs/26-frozen-fc-suite-first.xml -q`。唯一新增跨进程测试在 `future.result(timeout=30)` 等 child READY 时超时，未进入共享 SQLite 持锁/GO阶段；finally仅 kill/reap 自己两子进程。不拿之前的 candidate34绿代替该实际退出。精确源目录 `python -I -m mypy --strict --cache-dir L/mypy-cache orchestration/fc_logging.py` 已首 exit0，1 source file；`27-frozen-strict-first.log`。

一次有界冷启动阶段诊断 `python -I L/diagnose_boot.py` 首 **exit1**，`28-coldboot-diagnostic-first.log` 与 `L/boot-diagnostic-01` 原stdout/stderr保留：一子30秒内仅 BOOT，kill/reap；另一子实际 IMPORTED29.2908452s / WARMED30.4251265s / exit0。原失败现场没有 child warm 日志文件。这支持超时发生在导入/fixture准备阶段，未验证当时系统负载或远端 I 因果，不归咎 SQLite 锁策略。当时未自行放宽冻结 fixture30秒；已通过当前Dispatch ask请求主控协调一次低负载窗口或明确新增 fixture 冷导入预算120秒的授权（共享持锁200ms/logging1秒/耗尽3秒/GO后communicate30秒/原断言不变）。后续实际结果另列，所有首次RED保持。

## 同 Owner 冷启动 fixture 窄修

本 Dispatch ask 随后获得主控明确回复：**“仅本Task新增跨进程fixture的cold import/READY准备预算改为有界120秒”**，不以低负载重跑同源码洗绿。只将新增 `test_process_writers_share_real_sqlite_append_lock` 的 READY future 等待改成120秒并加解释注释；每个 READY future 有界，两个启动等待可以累加，这不是日志锁预算。原19函数、两已授权实现参数期望、半截首行、六 facts、序列、真实锁、共享持锁200ms、production日志1秒、耗尽3秒、GO后每个communicate30秒、owned-child finally清理全部保留；不改原已有科学/TaskLedger/runtime阈值。

必要一次失败焦点确认：`python -I -m pytest <A-worktree>/tests/swarm/test_fc_logging.py::test_process_writers_share_real_sqlite_append_lock --import-mode=importlib -p no:cacheprovider --basetemp L/temp-bootstrap-repair --junitxml L/logs/29-bootstrap-repair-focused-first.xml -q`，**首 exit0，1 passed / 40.16s**，业务仍读取前轮真实 installed logger（production bytes 未变）。随后新 SOURCE `ec24ebb4519845bf677786e0480260bc76c85407` commit / normal push / ls-remote 首全 exit0、remoteexact、clean；`30` / `31` / `32` 日志。`41da→ec24` 唯一变化为该测试2插入1删除，logger本身无 diff，旧41da的CI或绿不能代签新SOURCE。

新 SOURCE 命令级 `core.autocrlf=false` 精确 archive 到全新 `L/frozen-source-ec24ebb`，新 wheel 为 `L/final-dist/morphogenesis-0.1.0-py3-none-any.whl`；正常非 editable reinstall 后只放置本次新 archive 测试源码于对应 site 根，前轮41da测试树移到本轨私有 `L/frozen-41da-first-tests` 保留。`33` extract / `34` build / `35` install 首全 exit0。最终 `36-final-provenance-first.log` 首 exit0，Git/archive/wheel/site logger/TaskLedger/schema bytes一致、原测试/helper Git/archive/site bytes一致且nlink1、19原函数与2授权期望保持、非editable direct_url准确指向本轮 `final-dist`、Node lock不变。这里未把测试文件冒称打包在业务 wheel，也未把 Windows 工作树 CRLF 与 Git LF 冒称同bytes。

最终完整34仅在此新SOURCE轮运行一次：`L/venv/Scripts/python.exe -I -m pytest L/venv/Lib/site-packages/tests/swarm/test_fc_logging.py --import-mode=importlib -p no:cacheprovider --basetemp L/temp-final --junitxml L/logs/37-final-fc-suite-first.xml -q`，**首 exit0，34 passed / 284.04s**。完整原29case与5新增case均通过；3线程/2进程分别六事实有效且序列1..6、半截原首行保留，成功writer failure_count0；锁耗尽 strict原异常/emitFalse与诊断计数、不补半截、不覆盖原bytes；写后fsync失败严格抛错/emitFalse且不重发；既有Worker侧日志失败不重发执行/不替换completed事实均保留。源码未为新轮再改业务。`41da→ec24` logger bytes 完全相同，原 `27-frozen-strict-first.log` 的受影响文件 strict PASS适用于未变logger；测试准备预算改动无需重复全库type，本轨未运行I的全包strict。

准备阶段也保留首失败：第一次抓取旧带前缀 I ref 的 fetch exit0，但 ancestry exit1，因此未 merge；`01-git-fetch-first.log` 和 `02-first-ancestry-failure-diagnostic.log` 保留。root 指正后实际无前缀 `refs/heads/morph-research-integration-0930` remote exact874a、fetch exit0、A53c4 ancestor / clean，正常 ff-only exit0；`02-correct-remote-first.log` / `02-correct-fetch-first.log` / `02-git-ff-first.log`。这不是远端写失败，不做盲重试。

第一次原生 tar 全量解包因旧 docs/source 异常文件名 `Invalid empty pathname` exit1，原 archive、partial `baseline-source` 和会话原输出保留（该首次控制台输出未独立重定向成 raw 文件，不冒称有原 log）。随后用 CPython tarfile `filter='data'` 在全新 `baseline-runtime-source` 解包运行源码，排除与 logger 无关的 docs；不删旧目录、不修改归档或运行源码。旧0930 `42 passed / 1 failed / 797.77s` 保留于 `docs/tracks/fc-stable-drill-0930.md`，本轨成功不覆盖它或其它旧 RED。

## 等待界限、风险与交接

1秒是 logging-side SQLite 获取锁的原生等待预算，不是 append 全调用的硬实时上限。已有验证、安全检查、JSONL O(n) 行扫描、磁盘 flush/fsync 和 OS 调度仍可能耗时；持续占锁超过预算仍安全失败。同步日志竞争可能增加调用线程延迟，多次 emit 的总等待可累加；未做大日志/长期持续竞争性能验收。没有把有限等待扩展成无界排队，没有修改整个 TaskLedger timeout 或事务。

SQLite sidecar 与 JSONL 是两个存储；JSONL 写后 fsync/commit 错误可能留下可见的 partial/完整 bytes，耐久效果未知。strict 抛错或 emitFalse 均不代表零写入，也不会自动再次 append。失败归失败，既有 Worker outcome、未知效果/usage/cost、旧科学记录不改写。

本轨仅 SOURCE focused / installed 工程修复验收。Windows 本机 logger 专项及受影响 strict 结果不代签 Ubuntu/Windows 完整 pytest/type/build/SDK/wheel distribution。完整双平台候选门禁由原 I 对新的冻结 SOURCE 执行，本轨 **NOT_RUN**；push 可能触发的 CI 结果单列，不能预写通过。原 case06 完整 checker PASS（产品48dd、I874a）是独立历史事实，本轨不推翻、不代跑新科研；case01–06 不重放，无新的模型/native session/scientific clock、sandbox 服务、Hub/EvoMap 或真实凭据活动。

首 SOURCE `41da403440acaf24d4414691077d56f1db242f6f` 正常 commit 和 push 首 exit0；`16-source-commit-first.log` / `17-source-push-first.log`，`19-source-remote-first.log` ls-remote 首 exit0、remoteexact、clean。最终 SOURCE `ec24ebb4519845bf677786e0480260bc76c85407` 的 `30` commit / `31` push / `32` ls-remote 首全 exit0、remoteexact、clean，root 已收取新 SOURCE 后衔接原 I 的新完整双平台门禁。后续独立 REPORT 只改本文件，source→report 业务空 diff；REPORT 的实际 normal push / remoteexact / clean 在最终交接中报完整 SHA，不在文件内编造自引用 SHA。每步非零 exit保留，不由后续成功命令覆盖。
