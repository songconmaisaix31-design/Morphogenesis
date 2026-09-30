# Phase 2 I：精确集成与独立验收（2026-09-30）

## 身份、范围与实际提交

- Run `run_5b66cce8b4b8`；Task `task_6641d525e46a`；Dispatch `ctx_33c0c2214dec`。I 是独立集成 Worker，使用启动指定 `gpt-6.1-sol`，没有创建其他 Task/Run 或派生 Agent。
- Worktree `C:/Users/DW/orca/workspaces/Morphogenesis/morph-fc-stable-integration-0930`；branch `songconmaisaix31-design/morph-fc-stable-integration-0930`。固定基线 `7cc64e3eb0031a6b06b9482e95707de17dfe0885`。
- 已读本树 AGENTS、包 README、收口计划，以及精确 R/D Git 提交中的三份 Owner 报告（报告尚不在初始基线树，故从 immutable Git blob 读取）。本次 TASK 和总控原 Dispatch 后续消息优先，未扩大基础设施。
- `71d46946595e3efe2cb007f856816b2ad5205395`：`merge --no-ff 973fe64a6403112dfd72b7de69b5661f74b7237e`，包含 R 原接口与日志窄修代码 `f0d6f520c3e230af0c2718dbcc993a4a53a9ee7d`。
- `af11d7fa7b41b9e62db92cab5271ed66442e8ac2`：`merge --no-ff b1569d1dfd8337a5c751f9c25d6b576a85212a5f`，包含 D 显式离线 Executor。
- `20ddb85562872f2e93a84295da14fd0688fcf986`：I 唯一源码胶水，仅删除 `demo/fault_drill.py` 的 `SharedBreakerLike` 导入和 `guard_provider` 调用上的 cast（2 insertions / 2 deletions）。没有领域返修。
- `7430605f3c3b993c2030720d727acd65baea9483`：在原 Dispatch 明确准入 `msg_e9cf0fb1ed4c` 后，`merge --no-ff 812b96ea68a36b84bef20d71476ae2860e0fcf55`。原 R 同树同分支返修代码为 `9f6d57417d16125d45cc2ce920c400f358b44776`，只追加 `no_links` 平台类型分支及原报告，不改其他领域。**这是全部下列最终源码门禁实际执行的代码 SHA**；已 push，远端精确匹配。
- 本报告及计划追加属于后续纯文档提交。报告完整 SHA、逐路径 blob 对照、最终目标实际 SHA/remote/clean 在本次原 Dispatch 的终态回执单列；不把代码 SHA 的门禁说成报告 SHA 重跑。

## 独立边界核对：事实

初次合并前核对 `git ls-remote` 的 R/D 精确远端 SHA、I/R/D clean tree、基线祖先关系与互斥 write_paths，exit 0。R 恰为 10 条授权路径，D 恰为 4 条，交集为空；没有合入可变 head、C 前端 `621f588`、第一代主线或其他 WIP。

在新 `7430605` 上再次直接读取 Git blobs/AST，exit 0：

- `tests/swarm/test_fc_logging.py` 原 17 个、`tests/swarm/test_assets.py` 原 37 个顶层 function/class 定义 AST 全部未变，仅增加 2 和 3 个回归；未修改原 3 线程、6 次 append、partial tail/sequence 断言。
- `swarm/budget.py`、`swarm/lease.py`、`swarm/task_ledger.py`、`swarm/breaker.py`、`swarm/fault_observations.py`、整个 `orchestration/provider_adapters/`、Schema、`poetry.lock`、`package-lock.json`、`pyproject.toml`、`package.json`、整个 `.github/`，以及原 H1/DSH 文件，与 `7cc64` 固定基线无差异。
- `orchestration/fc_logging.py` 和 `local_assets/paths.py` 精确等于获准 R 最终 `812b96e` blobs。I 没有改变这些领域源码；复杂 guard WIP 没有合入。
- `orchestration/fc_logging.py:139/143/144/155/156` 的锁外完整检查、原 `timeout=0.05`、锁内完整重检查、flush/fsync 均仍在原位。`local_assets/paths.py:48/52/57/59/60/62` 的每组件单次 lstat、symlink、Windows junction、regular hardlink 与异常 failclosed 原策略保留。
- `swarm/breaker.py:202/592/672` 三处 TODO-HUMAN-REVIEW、原 R 失败报告、D 撤销复验历史及 H1/DSH 原记录保留。原 tag 独立远端读取仍为 object `77becf857fa0b45cbf18fdf57a70854acab905e0` / peeled `86ade3d310898d8d2af765f4ee10b2e27271cd5b`；没有移动或新建 tag。

静态证据：OS TEMP `C:/Users/DW/AppData/Local/Temp/morph-fc-I-ctx33-0930/preflight.json` 和 `7430605/source-audit.json`。这是 Git/stdlib 独立读取，不是复制 Owner 自验结论或新建证明框架。

## 首次失败与有界处置：事实

1. **原 R/D 失败未改写**：R 原完整适用回归 323 passed / 1 failed、同节点诊断再失败；D 原 focused 42 passed / 1 failed，后续整组复验被撤销、零次启动。旧 D `0ad1a0d` CI `36688759422` Windows 1 failed / 916 passed、Ubuntu success 是旧代码的 50 ms SQLite 锁失败；不是新候选复跑。这些历史来自已保留的 Owner 报告与本次派发，I 不代称自己执行了旧 Owner 门禁。
2. **I 首个整体候选真实失败**：`20ddb85` 的 [CI 36696567218](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/36696567218)，Ubuntu pytest 924 passed / 1 skipped / 75 warnings / 251.98s，随后 strict **exit 1**：`local_assets/paths.py:58`，`stat.IO_REPARSE_TAG_MOUNT_POINT [attr-defined]`，89 files / 1 error。Windows 被 matrix fail-fast **cancelled**。原 JSON、完整 Ubuntu 日志和失败日志保存为根目录 `ci-first.json`、`ci-ubuntu-first.log`、`ci-first-failed.log`。
3. I 立即 Handoff `msg_48f782bc44ee`，未修改领域源码或 CI。按总控 `msg_5469d16823f2` 停止该候选本地全量：明确匹配本树 venv launcher PID 75840、实际 uv Python PID 59756 及其后代，定向停止并复核 survivors=0。真实 shell exit **-1**，状态 **INTERRUPTED**；`full.log` 的 54%+partial、`full.exit`、`full.status`、`full-interrupted-processes.json` 全部保留。不能写成 pytest 断言失败或全量通过。首个只读匹配发现 venv 转发父/子两个同命令，因此限制到 launcher 的实际 ExecutablePath 后才停止；没有终止其他 Owner。
4. 平台类型问题回原 R，在同工作树/分支由其窄修并交付 `812b96e`。I 仅精确 no-ff，生成新 `7430605` 后真正执行新整体全量与双平台 CI；没有盲 retry 旧 CI、放宽阈值或复用旧 green。
5. **新候选本地分发首次 exit 1**：实际新 wheel 安装至独立 OS TEMP site（安装 exit 0）后，原 `-I tools/check_distribution.py --site-dir ... --check-node` 报 `BridgeError: sdk_process_failed`。原 `7430605/distribution.log/.exit` 保留。有界真实 Node 诊断 exit 1，stderr 明确 `ERR_MODULE_NOT_FOUND: ajv`，importer 为实际 TEMP site 的 `bridge_node/asset_bridge.mjs`；证据 `distribution-node-diagnosis.log/.exit`。源码 checkout npm 依赖在源目录祖先，不能自动供给 TEMP 安装位置的 ESM imports。
6. 依照既有锁和总控 `msg_1963fb911430`，仅复制当前 `package.json/package-lock.json` 原 bytes 至 TEMP site，`npm --prefix <site> ci --ignore-scripts --no-audit --no-fund` 安装 99 包、exit 0；两文件逐 bytes 与 checkout 一致。**同一 `7430605`、同一实际 site、同一分发命令、同一真实 Node/10s 原期限与断言单次受控复验 exit 0**，原失败不覆盖。不修改 bridge、分发脚本、锁或 CI，不 mock/跳过 Node，不重复已通过全量或 CI。环境前置限制见下文。

## 新代码 SHA 的本地门禁：事实

独立环境：本树 `.venv`，进程内 `POETRY_VIRTUALENVS_IN_PROJECT=true`，`uv tool run poetry install --no-interaction` exit 0，Python 3.12.13；`npm ci --ignore-scripts --no-audit --no-fund` exit 0，Node 24.16.0。没有跨树复用 venv，Poetry/npm 锁未改。以下全部在实际 HEAD **`7430605f3c3b993c2030720d727acd65baea9483`**；本地慢检查串行，Python 为 `.venv/Scripts/python.exe`，进程内 `OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=MKL_NUM_THREADS=1`。状态及 pytest basetemp 均 OS TEMP。

日志根 `L = C:/Users/DW/AppData/Local/Temp/morph-fc-I-ctx33-0930/7430605`；每项真实退出存同名 `.exit`。除明确保留的分发首轮外，最终门禁如下：

| 实际命令 | 实际 exit / 结果 | 日志 |
|---|---|---|
| `python -m pytest -q --basetemp L/pytest-full` | 0；925 passed / 2 warnings / 1216.54s | `full.log` |
| `python tools/typecheck.py` | 0；89 source files，strict | `strict.log` |
| `python -m build` | 0；实际新 sdist + wheel，isolated poetry-core 2.5.0 | `build.log` |
| `npm run check:sdk` | 0；官方 1.14.0 schema、asset ID 验证及 tampering rejection；published=false | `sdk.log` |
| `uv pip install --python .venv/Scripts/python.exe --no-deps --target L/wheel-site dist/morphogenesis-0.1.0-py3-none-any.whl` | 0；实际新 wheel 安装 | `wheel-install.log` |
| `npm --prefix L/wheel-site ci --ignore-scripts --no-audit --no-fund`（exact 锁依赖） | 0；为独立安装 site 补真实 Node 前置依赖 | `wheel-npm-install.log` |
| `python -I tools/check_distribution.py --site-dir L/wheel-site --check-node`（明确诊断后的单次复验） | 0；13 包从实际 wheel 导入、installed verifier、真实 Node dependency check | `distribution-after-locked-deps.log` |
| `python -I -`，实际 installed importlib resource/Git fence/zip 原 bytes 对照 | 0；见 H3 表 | `schema-installed.log` / `.json` |
| `python -B -m demo.fault_drill --directory L/drill-cli` | 0；**唯一一次 CLI**，真实墙钟冷却，六阶段 | `cli.log` |
| `python -`，独立 JSONL + SQLite `mode=ro` 对照 | 0；见下一节 | `cli-independent.log` / `.json` |

两条本地 warnings 来自 `test_budget.py` 故意用非法 nan/字符串 `input_tokens` 的 Pydantic serializer 检查。`package.json` 没有 npm build，未执行或捏造该命令。没有替换真实 subprocess/fsync、删除测试或改变阈值。

## 行为、持久化与平台证据：事实及推断边界

当前全量实际包含真实 `Worker._process` 的执行调用与参数、持久预算/任务/JSONL、日志路由、未知效果停链及重启不重发、lease/probe fencing、缺失组件 failclosed 与 `breaker_config=None` 兼容：

- `tests/swarm/test_failure_chain_runtime.py:123/159/175/183`：实际 executor `call_count/call_args`、两个 candidate 参数与 durable request identities。
- `tests/swarm/test_failure_chain_boundaries.py:20/42/59/92/196`：真实缺失组件 subprocess（原 30s）、无 breaker 的真实 store、未知效果/未知费用 hold、lease 失效不提交。
- `tests/swarm/test_fault_drill.py:193/226/239/254/271/289`：显式 executor 的实际 `calls`/bound 参数、真实预算拒绝、Fixture 输入边界、未知效果不重发、过期/旧 lease token fencing。
- `tests/swarm/test_fc_logging.py:136/188/212/287/310`：原 3 线程/6 append、14 字段与 hold、日志失败不替换 completed/不重发、真实 SQLite 拒绝不补 partial tail、锁后真实 hardlink 的新鲜检查。
- `tests/swarm/test_assets.py:25/35/54/255/263`：missing、regular ancestor、dangling alias、metadata PermissionError 注入 failclosed、真实 hardlink 和 alias。PermissionError 是既有 primitive 注入，未冒称原生权限测试。

Windows 本地 full 留存 artifact 的独立只读结果 `windows-native-artifacts.json`：alias/dangling 均 `symlink=false / junction=true / st_reparse_tag=2684354563`；真实 hardlink samefile/nlink=2；logger 锁后 hardlink nlink=2，原 partial bytes 仍为 `{"incomplete":`。辅助 artifact 读取第一次 exit 1，原因是 pytest 临时 basename 截断导致 logger glob 未命中；列出实际目录后只改只读 glob，复读 exit 0，原读错及修正说明保留 `native-artifacts-first-read.log`。这不是测试断言失败或门禁复验。

Windows 原生 symlink 创建走已有权限失败后的 junction fallback，**未宣称 Windows native symlink 已执行**。Ubuntu 当前 full 包含这些无 skip 的资产测试，其 Linux helper 在 symlink 创建失败时直接 raise、没有 junction fallback；结合实际 Ubuntu full success，提供 Linux 原生 symlink 和无 Windows tag 分支行为的门禁证据。该说明依据平台源码/选择与整套 gate，不冒充另一次 Linux 独立 probe trace。

唯一 CLI Run `fault-drill-5bb0b97d5d1a4847b22c466cce1131e8`。I 在 CLI 完成后直接独立读取实际 result、21 条统一日志、权威故障 JSONL 和 SQLite `mode=ro`：

- 顺序 normal / rejection / controlled_switch / peer_avoidance / cooldown_probe / recovery；recorded executor alpha/beta 为 1/0、1/1、0/1、1/0（normal/switch/peer/recovery）。实际调用参数另由本次 full 的真实 Worker 测试验证，未将构造响应当调用证据。
- 21 条事件均 mock/SIMULATED/drill，writer_failure_count=0；每条经与 H3 相同的 Git Schema validator 验证，审计未知仍 None。
- 唯一真实故障 fact 的 14 字段与统一日志精确一致：`fixture-1:1:0`、confirmed_rejection、billing_arrearage、switched_to=beta:fixture、cost_state=unknown。
- 5 行真实 reservations 全 uncertain/unknown、tokens=None、estimate_usd/admitted_usd=None、request_bound=unbounded，每行 reserved_usd=0.2，累计仍 **1.0 USD hold**。顶层 usage/cost_usd 仍 None，没有用 0 填未知或释放 hold。
- 4 个实际 tasks 和 4 个 task_attempts completed；claim 日志 sequence/at/token 与持久 ledger 对应。probe token=1，历史保留。所有原 JSONL/SQLite/工作区留在 `L/drill-cli`。

**推断限制**：这些是本地真实 Worker/存储/官方 SDK 的模拟 executor 行为；不证明远端模型效果、生产 50 ms 时延保证、Hub 或 Live 成功。Owner profiler 竞争失败及未知观察开销保留在原 R 报告，I 没用 profiler 或单节点 green 代替全量。

## H3 冻结内容与实际 wheel 原字节：事实

独立读取批准 `be4fb7a685e951c9e42d8dc0c7eeb900cb5518f1:docs/FC_LOG_SCHEMA_DRAFT_0928.md` 唯一 JSON fence（96–1913），仅排除 Markdown 分隔符换行，不 strip 或重序列化。与 `db283eaa1f1d71d36e7b8a3520aafbce5becf1dd` 和新 `7430605` Git Schema blob 对照：

| 对象 | JSON 内容 | 原字节 |
|---|---|---|
| H3 sole fence / db283ea Git / 7430605 Git | 相等 | 精确相等，38,309 LF bytes；SHA256 `1b4fc1f2dfe603a691b7a4d0dfe977a36bc99aebbfc40e37a0418f0e6355bffc` |
| Windows checkout / 本次 build wheel zip / 实际隔离安装 Schema | 与上述相等 | 三者精确相等，40,124 CRLF bytes；SHA256 `7118d331e80fe4a8e8626bba1b5934ab433897de2419493fd5283a6a3d2f4eb8`；**与 Git LF 原 bytes 不相等**，精确 LF→CRLF 转换 |
| H3 当时的打包资源存在性 | 无该对象 | `git cat-file -e be4fb7a...:orchestration/fc_log_schema.json` 实际 exit 128；批准对象是文档 fence，不能捏造 H3 packaged resource |

实际 `-I` import 的 `orchestration.__file__` 位于 `L/wheel-site/orchestration/__init__.py`；resource 实际路径为同 site 的 `orchestration/fc_log_schema.json`，没有读回源树冒充安装资源。`schema-source.json`（首候选）、新 `source-audit.json`、`schema-installed.log/.exit/.json` 保留原字节区别。没有修改 Schema 对齐，也不以合法性检查替代冻结比较。

## 新 SHA 的外部 CI：事实

[Run 36698246456](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/36698246456) 的实际 headSha **`7430605f3c3b993c2030720d727acd65baea9483`**，completed / success。I 实际读取最终 job/step JSON 与原日志：

| 平台 | 实际 pytest | 后续实际门禁 |
|---|---|---|
| Windows | 925 passed / 75 warnings / 1021.37s | strict 89、build、SDK、实际 wheel 安装、`-I distribution --check-node` 全部 success |
| Ubuntu | 924 passed / 1 skipped / 75 warnings / 338.52s | strict 89、build、SDK、实际 wheel 安装、`-I distribution --check-node` 全部 success |

证据 `L/ci-final.json`、`ci-windows-final.log`、`ci-ubuntu-final.log`。此前 run 未结束时 GH 拒绝提供 Ubuntu 日志的返回文本保留 `ci-ubuntu.log`；最后在整体 completed 后重新读取日志，没有 rerun CI。旧 `36696567218` 的 strict exit 1 / Windows cancelled 不改写。新 source gate 与后续纯报告 SHA 分列，不为纯文档更改重复已过源码 gate。

## 三态、人工边界与目标推进

- **contract_local=PASS**：仅上述新 `7430605` 当前独立本地与双平台 CI 的明确范围；首次失败与有界环境修复同时保留。
- **interface_live=NOT_RUN；task_live=NOT_RUN**。模型 API、DSH、Hub、任何 Live、部署、新候选 H1 人工签字及 tag 操作均 NOT_RUN。
- **人工**：David 原 H1 仅 `db283ea` 的有条件接收，不自动继承新 source SHA。原 DSH 用户已接受预算耗尽的推理流为评审实质，但原 exit 1、非合格正式评审、引用机械校验未完成仍保留；没有再调用或索取密钥。三 TODO 没有关闭。
- **真实安装限制**：独立 wheel site 必须实际供给 npm 锁定的官方 SDK/Ajv 前置依赖；wheel 本身不包含 node_modules。源树 SDK gate 或 CI 在源码祖先内的 wheel site 通过，不消除这项 TEMP 独立安装要求。
- **推进前事实**：全部当前核心门禁完成后，18:17（UTC+8）初次读取目标 `decentralized-swarm` 本地 clean，HEAD/remote 均仍 `7cc64e3eb0031a6b06b9482e95707de17dfe0885`，原 tag object/peeled 不变。本报告写入时尚未执行目标推进，**不预写推进通过**。
- 本报告提交后，仅当纯报告 diff 恰为本文件及计划追加、所有其余逐路径 code/test/package/config blobs 与 `7430605` 一致，且紧邻执行前再次确认目标 clean/HEAD/remote 仍固定基线，才依原授权对完整候选执行 `merge --ff-only` 和普通 push。最终 I/report SHA、target SHA、实际命令/exit/remote/clean 由本次 exact Dispatch 终态 Handoff 给出；漂移则交总控，不覆盖贡献。

没有未完成的源码返修；生产人工放行/正式 DSH 机械校验及 Live 均仍是独立限制，不以本地验收冒称完成。
