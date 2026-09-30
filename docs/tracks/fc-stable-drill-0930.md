# Phase 2 D：显式离线 Executor 与证据归档

## 一页执行计划

- 基线：`7cc64e3eb0031a6b06b9482e95707de17dfe0885`；模型按派发为 Codex `gpt-6.1-sol`。
- 本轨：worktree `morph-fc-stable-drill-0930`；branch `songconmaisaix31-design/morph-fc-stable-drill-0930`；Task `task_6e86025af1bf` / Dispatch `ctx_52f16a4a4b06`，接续原 Run `run_5b66cce8b4b8`，不复用旧任务身份。
- 唯一写权：`demo/fault_drill.py`、`tests/swarm/test_fault_drill.py`、本报告、`docs/FC_CLOSEOUT_0930_PLAN.md` 的 Phase 2 追加内容。R 独占运行时与两份 failure_chain 测试；I 后续负责精确合并及独立验收。跨轨只 Handoff。
- 复用 `Executor` / `FixtureExecutor` / `ExecutionBound` / `ExecutionResult`，由现有 EvoMap ProviderAdapter 通过本地 httpx mock transport 分类；替换动态 Mock 边界，不改预算、租约、breaker、Schema、锁或依赖。
- 自测：指定 `.venv/Scripts/python.exe`，focused `test_fault_drill` / `test_fc_logging`、`tools/typecheck.py`；真实 CLI 一次，状态位于 OS TEMP，忽略日志留 `.runtime/`。全量、build、SDK、分发由 I 串行执行。
- H1 附带证据：独立从 Git 读取 `db283ea` 的打包资源及文档确认的 H3 `be4fb7a` fence，比较 JSON 内容和精确资源字节；CI 合法性与冻结一致性分别记录。
- 历史不改写：旧 A `db283ea` 代码/CI 交付与旧 Orca abandoned 生命周期是不同事实；总控既有计划 WIP 原样接续。此次从原始注入读取真实 dispatch-capability，能力是否有效只据 CLI receipt。
- 限制：`provenance=mock` / `SIMULATED`，usage/cost 保持 None，未知 hold 不释放；Owner 自测不等于独立验收。David 原条件签字仅锚定 `db283ea`，新代码不继承签字；三处 TODO 不改。DSH 原 exit 1、推理流被用户接受但非合格正式评审，引用机械校验未完成，本轮不调用 DSH。原 `demo-build` 不覆盖；第一代主线/WIP、C 前端只读；模型/Hub/Live/部署 NOT_RUN。

## 实际执行与证据

### 环境与保留的首次退出

- 初次 `.venv/Scripts/python.exe -m pytest tests/swarm/test_fault_drill.py tests/swarm/test_fc_logging.py -q` 在 collection 前 exit **1**：`No module named pytest`。环境是前 D 取消安装留下的不完整 `.venv`，仅有 python.exe 不证明锁安装完成；原始日志及 exit 保留于 `.runtime/fc-stable-drill-0930/focused-initial.*`。
- 总控经原 Dispatch 明确接续环境修复：局部 `POETRY_VIRTUALENVS_IN_PROJECT=true`，`uv tool run poetry install --no-interaction` exit **0**；`npm ci --ignore-scripts --no-audit --no-fund` exit **0**（99 packages）。未改锁或依赖声明、未借 R 环境、未绕过官方 NodeAssetBridge。实际 Python 路径为本树 `.venv/Scripts/python.exe`，pytest 9.1.1，官方 `node_modules/@evomap/gep-sdk` 存在。

### H1 附带 Schema 独立一致性读取（仅旧候选）

来源先由 `docs/FC_CLOSEOUT_0930_PLAN.md:7`、`docs/FC_LOG_SCHEMA_DRAFT_0928.md:18` 确认 H3 冻结 1.0.0 / David / 2026-09-29，再以 `git rev-parse be4fb7a` 得到 immutable `be4fb7a685e951c9e42d8dc0c7eeb900cb5518f1`。受审旧候选为 `db283eaa1f1d71d36e7b8a3520aafbce5becf1dd`。

实际读取命令为 `git show db283eaa1f1d71d36e7b8a3520aafbce5becf1dd:orchestration/fc_log_schema.json` 与 `git show be4fb7a685e951c9e42d8dc0c7eeb900cb5518f1:docs/FC_LOG_SCHEMA_DRAFT_0928.md`（Python `subprocess.check_output` 保留原 bytes）。H3 文档唯一 JSON fence 位于 **96–1913 行**；正则 `rb'```json\r?\n(.*?)\r?\n```'` 的 group(1) 是 JSON 内容，不含 Markdown 分隔符换行，未 strip、未重序列化。

| 比较对象 | 实际结果 |
|---|---|
| db283ea 资源 Git blob vs H3 fence JSON 内容 | JSON 相等，精确 bytes 相等；两者 **38,309 bytes** |
| db283ea 资源 vs 将 fence 后 Markdown 分隔 LF 也计入的文本 | 精确 bytes **不等**；后者 38,310 bytes |
| 本轨基线资源 Git blob vs db283ea 资源 Git blob | 精确 bytes 相等 |
| 当前 `importlib.resources.files("orchestration").joinpath("fc_log_schema.json").read_bytes()` vs db283ea Git blob | JSON 相等，原 bytes **不等**；当前资源 **40,124 bytes**，精确等于 Git blob 的 LF→CRLF checkout 转换 |
| H3 SHA 的打包资源 | **不存在**：`git cat-file -e be4fb7a685e951c9e42d8dc0c7eeb900cb5518f1:orchestration/fc_log_schema.json` 实际 exit **128**；H3 批准对象是该 SHA 的文档 fence，不能捏造当时已打包 |

LF candidate/fence SHA256：`1b4fc1f2dfe603a691b7a4d0dfe977a36bc99aebbfc40e37a0418f0e6355bffc`。当前 importlib CRLF 资源 SHA256：`7118d331e80fe4a8e8626bba1b5934ab433897de2419493fd5283a6a3d2f4eb8`。这些是标准库只读 bytes 对照，无新增哈希/证明系统。

首次 `.venv/Scripts/python.exe -` 比较脚本 exit **1**，因把 Markdown 分隔 LF 纳入内容并断言 CRLF checkout bytes 等于 LF Git blob。原 `schema-compare.log` / `.exit` 和 `schema/comparison.json` 原样保留。明确提取边界后，第二份 `schema-compare-final.log` / `.exit` 实际 exit **0**，逐项保留原 bytes 不等结果；另经 importlib 真实资源读取 `schema-resource.log` / `.exit` exit **0**。缺失 H3 打包资源的 exit 128 另留 `h3-packaged-resource.*`。输入原 bytes 与 JSON 结果都保存在 `.runtime/fc-stable-drill-0930/schema/`，不是 CI 的 `check_schema` 合法性冒充冻结对照。

复现内容和资源比较可在本树运行（与实际命令采用相同的原字节读取/提取方式）：

```powershell
@'
import json, re, subprocess
from importlib.resources import files
c = subprocess.check_output(['git','show','db283eaa1f1d71d36e7b8a3520aafbce5becf1dd:orchestration/fc_log_schema.json'])
d = subprocess.check_output(['git','show','be4fb7a685e951c9e42d8dc0c7eeb900cb5518f1:docs/FC_LOG_SCHEMA_DRAFT_0928.md'])
m, = list(re.finditer(rb'```json\r?\n(.*?)\r?\n```',d,re.S))
f = m.group(1)
p = files('orchestration').joinpath('fc_log_schema.json').read_bytes()
print({'json_equal':json.loads(c)==json.loads(f)==json.loads(p),
       'git_blob_equal_fence_content':c==f,
       'raw_packaged_equal_git_blob':p==c,
       'packaged_exact_crlf_conversion':p==c.replace(b'\n',b'\r\n'),
       'lengths':[len(c),len(f),len(p)]})
'@ | .venv/Scripts/python.exe -
```

本结果独立补录旧 db283ea 的 H1 附带证据。本轮 demo 源码将改变，原有条件签字不得继承；本报告不是 David 重新签字，不将 CRLF 原字节称为 LF 原字节，也不把 JSON 相等扩写为新的冻结/发布/Live 通过。

### 实现与 I Handoff

`OfflineExecutor` 以显式 `bound(signal)`、`execute(signal, attempt, repository, directory, *, base_revision, base_head, experience=None)` 满足既有 Executor 协议。`check_paths` 与输入边界复用 FixtureExecutor；模拟 provider 不承接 fixture 的虚拟 verified 价格/费用证据，实际返回 unbounded / provider_enforced=false / max_cost_usd=None / bound_evidence=None，必须经真实预算的 operator allowance 准入。成功仍由 FixtureExecutor 物化候选，抹去虚拟 usage，固定 mock/SIMULATED metadata；400/503 在本地 httpx.MockTransport 经现有 `_request` / EvoMap ProviderAdapter 分类，未写第二套分类器或发远端请求。

`ExecutionCall` 只记录本地调用参数，`bound_calls` / `calls` 是被动证据；不调度、不生成新 AttemptId、不写业务状态或完成证明。原六阶段过程、真实 Worker、官方 SDK、持久预算/租约/fault store/breaker/统一日志均继续使用。断言仍位于 Worker 回调外，生产 demo 已移除 unittest.mock、动态 return_value、side_effect 与宽松参数签名。

固定实现 `0ad1a0d` 的入口为 `demo/fault_drill.py:112`（adapter）、`:139`（bound）、`:147`（execute）；被动参数记录 `:100`。测试证据锚点为 `tests/swarm/test_fault_drill.py:193`（真实 Worker 参数与持久 bound）、`:226`（准入拒绝）、`:239`（fixture 输入边界）、`:254`（未知效果停链/重启不重发）、`:271`（旧 token）、`:289`（执行时到期、无应用且 hold 不释放）。`swarm/breaker.py:202/592/672` 的三个 TODO-HUMAN-REVIEW 仍在原位，该文件未改。

R 的稳定协议 Handoff 已接收：本轨在旧 immutable 基线上保留 `cast(SharedBreakerLike, breaker)`，不为了去 cast 合入可变 R 分支；I 精确合并 R/D 后可删此必要类型胶水。运行时类型/领域修复仍属 R，本轨未改 R 路径。

### Owner 验证状态

`.venv/Scripts/python.exe tools/typecheck.py` 已实际 exit **0**：`Success: no issues found in 89 source files`，日志 `typecheck-initial.*`。此前 focused 与唯一 CLI 的运行中状态不作为通过；最终结果分别如下。

本轮唯一六阶段 CLI 已实际 exit **0**：

```powershell
.venv/Scripts/python.exe -B -m demo.fault_drill --directory C:/Users/DW/AppData/Local/Temp/morph-fc-stable-drill-0930-ecdf7307b9964791b9dc724cf16100c9
```

使用真实墙钟等待冷却，未用 time-machine 或替代 Worker 的返回值。Run `fault-drill-07e1cc4f9dfc4030a8261f208d1acd14`；顺序为 normal / rejection / controlled_switch / peer_avoidance / cooldown_probe / recovery，调用 alpha/beta 分别为 1/0、1/1、0/1、1/0（对应 normal/switch/peer/recovery）。最终实际 request_id 为 `fixture-0:1:0`、`fixture-1:1:0`、`fixture-1:1:1`、`fixture-2:1:1`、`fixture-3:1:0`；5 行均 uncertain/unknown，每行 reserved_usd=0.2、tokens=None，累计 hold=1.0 USD。usage/cost_usd 为 null；21 条 FC 日志，writer_failure_count=0；history_preserved=true。`contract_local=passed` 仅是该模拟入口的自身输出；interface_live/task_live=not_run。

忽略证据：`.runtime/fc-stable-drill-0930/cli.log` / `cli.exit` / `cli-directory.txt` / `cli-result.json` / `cli-events.jsonl` / `cli-summary.json`，原 SQLite、故障 JSONL、工作区与 result 保留在上述 OS TEMP 根。未重跑此六阶段 CLI。

指定 focused 最终 **exit 1：42 passed / 1 failed / 797.77s**（`.runtime/fc-stable-drill-0930/focused-ready.log` / `.exit`）。唯一失败为 `tests/swarm/test_fc_logging.py::test_concurrent_append_and_partial_tail_preserve_facts`：该只读测试 3 个真实线程提交 6 行时，`orchestration/fc_logging.py:142` 的 `connection(lock, write=True, timeout=0.05)` 在 `swarm/task_ledger.py:47` 的 `BEGIN IMMEDIATE` 抛出 `sqlite3.OperationalError: database is locked`。D 的 16 个 drill case 均无失败，但 42 个通过不能代替整个 focused 门禁。

限定只读诊断：FCLogWriter 在持 SQLite 写锁期间检查真实路径、读取既有日志计 sequence、写入/flush/fsync JSONL，已有 50 ms 锁等待。失败路径与测试相对指定基线均无 diff；无法从本次 traceback 确认锁持有者耗时或把它断定为机器负载导致。未修改超时/线程数/断言，未 mock fsync/SDK，不删除原失败。该实现/测试不在 D write_paths；已由原 Dispatch escalation 交总控决定受限接续，未擅自重试。

可观察的并发事实（OS 本地时间 UTC+8，日志创建与 exit 写入时刻）：focused 15:59:44–16:13:56，与本轨 strict 16:01:00–16:04:44、唯一 CLI 16:06:11–16:09:07 存在重叠。focused 实际子 Python PID 60892 的累计 CPU 观测为 16:03:38 的 74.8125s、16:08:20 的 134.84375s、16:13:54 的 252.28125s；16:11 左右观察到其真实 Node 子进程。它没有被当作挂起杀掉。并发 I/O 争用只是一项假设，现有证据没有给出失败线程的精确持锁/排队时长，不能宣布唯一根因。

总控经原 `orca orchestration ask` 的真实回复准许一次受控串行复验：先固定/推送相同实现 SHA，再等 R 回归明确退出，只执行原完整两文件 focused 命令，保持相同源码、选择、断言与 50 ms 阈值，不并发 CLI/其他测试、不第二次重试。实现 SHA 为 `0ad1a0d06f88197c70e8909d505a6db261d2aee0`，已 push 且 `git ls-remote origin refs/heads/songconmaisaix31-design/morph-fc-stable-drill-0930` 精确匹配；两个代码/测试路径无 HEAD diff，原 failed focused 对应相同源码。当前等待总控 R-exited 明确准入，未把等候当授权。

SHA 时序说明：首次 focused / strict / 唯一 CLI 运行时 Git HEAD 是计划提交 `4ab0b2e`，两个实现/测试文件为本轨未提交修改；随后未改这两个文件，原样固定为上述 `0ad1a0d`。不能把首次命令的当时 HEAD 写为尚未存在的提交；原计划的受控复验须运行固定实现提交，但实际未启动（见最终处置）。报告/计划追加 WIP 不改变被测源码。

### 最终处置：开发已交付，共同门禁未通过

2026-09-30 16:35（UTC+8）实际收到原 Dispatch 的总控消息 `msg_7b345a26cc5b`：**撤销尚未开始的 D 整组复验**。总控提供的新证据说明 R 完整回归 323 passed / 1 failed，固定 `0cf04ab` 的单独日志节点诊断仍 exit 1 / database is locked；这些是总控交接事实，D 未执行或代验 R 的命令。D 的受控复验 **NOT_RUN（授权已撤销，零次启动）**，没有第二轮 focused，也没有再跑 CLI、DSH 或 Live。此前的准许/等待记录保留为过程，不将其写为已完成复验。

最终 Owner 命令与退出汇总（Python 为本树 `.venv/Scripts/python.exe`；focused/strict/CLI 均使用局部 OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=MKL_NUM_THREADS=1）：

| 命令 / 对象 | 实际退出与结果 |
|---|---|
| `python -m pytest tests/swarm/test_fault_drill.py tests/swarm/test_fc_logging.py -q`，首次不完整环境 | exit 1，collection 前缺 pytest，日志保留 |
| 相同两文件 focused，锁环境完成后、后来固定为 0ad1a0d 的源码 | **exit 1，42 passed / 1 failed / 797.77s**；16 个 drill case 无失败，共同 gate 不通过 |
| `python tools/typecheck.py`，同一源码 | exit 0，89 source files |
| `python -B -m demo.fault_drill --directory <上述真实 OS TEMP 路径>`，唯一一次 | exit 0，六阶段、21 事件、5 行 unknown hold 共 1.0 USD，mock/SIMULATED |
| 独立旧 Schema 原字节比较，首次 | exit 1，Markdown 分隔 LF/CRLF 边界错误，原结果保留 |
| 明确 fence JSON 内容边界的 Git bytes 对照与 importlib 资源读取 | 各 exit 0；Git candidate/fence 精确内容字节相等；CRLF 当前资源原 bytes 不等明确保留 |
| H3 SHA 打包资源存在性读取 | exit 128，不存在；批准对象是文档 fence |
| 计划阶段 Git commit/push | `4ab0b2e`，已 push |
| 实现阶段 Git commit/push/remote | `0ad1a0d06f88197c70e8909d505a6db261d2aee0`，push exit 0，ls-remote 精确匹配；仅自有两代码/测试路径 |

原失败关键栈（完整原始 trace 在 focused-ready.log，未删）：

```text
tests/swarm/test_fc_logging.py:141 -> ThreadPoolExecutor(max_workers=3), range(6)
tests/swarm/test_fc_logging.py:47 -> writer.append("task", ...)
orchestration/fc_logging.py:142 -> connection(lock, write=True, timeout=0.05)
swarm/task_ledger.py:47 -> db.execute("BEGIN IMMEDIATE" if write else "BEGIN")
sqlite3.OperationalError: database is locked
FAILED tests/swarm/test_fc_logging.py::test_concurrent_append_and_partial_tail_preserve_facts
1 failed, 42 passed in 797.77s (0:13:17)
```

**真实限制与 NOT_RUN**：日志并发持久化 gate 尚未通过；根因与修复交原日志 Owner，总控继续协调，I 尚未因此放行。R/I 精确合并后的独立验收、全量 pytest、build、SDK 专项验证、分发及新候选 CI **NOT_RUN**；安装并实际调用 Node SDK 不等于专项分发验证。DSH 原 exit 1 / 非合格正式评审 / 引用机械校验未完成继续保留，本轮 DSH 调用 **NOT_RUN**。模型/Hub/interface_live/task_live/部署、新候选人工签字 **NOT_RUN**；旧 `demo-build`、三处 TODO、第一代主线/WIP 与 C 前端均未修改。最终按总控指令发送一次 `worker_done --outcome failed`，表示本 Task 的共同验收未完成；不能将开发提交、16 个 drill case、strict 或 CLI 绿色子集改写为整套通过。
