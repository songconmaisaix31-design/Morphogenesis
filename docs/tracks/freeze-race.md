# 封板夜 T 轨：环境准备与彩排竞态核对

日期：2026-09-23。工作区：`C:/Users/DW/orca/Morphogenesis`；分支：`codex/morphogenesis-mainline`。本报告只记录本机命令及其产物，不代表 CI、Hub、真实模型调用或现场验收。

## 当前结论与范围

- 项目内锁定依赖准备完成，可复用解释器 **`C:/Users/DW/orca/Morphogenesis/.venv/Scripts/python.exe`**。安装完成已通过 Orca 向主控汇报。
- 历史 Windows CI `35691719303` 的失败断言是 **Gene 采用快照的 `weight > 0.5`**，不是 `after_feedback.pipes[0].weight > original_topology[0].weight`。历史失败依据来自仓库 `docs/ACCEPTANCE.md`、`docs/tracks/rehearsal-runtime.md`，本轮未访问远端 CI。
- `git diff e83a816 94b7081 -- tests/t2/test_rehearsal.py` 确认：`94b70816784fcd46ce4f74b8e205bd009b789cc3` 已删除 Gene 固定下界，按采用记录、GeneRef、实际时间差及 tau 校验衰减，并加入 `normal` / `slow-adoption-snapshot` 参数。本轮不重复实现已存在的修复，不新增等待，不修改业务实现或测试文件。
- 正式 `tests/t2` 回归已在 19:45–19:46 CST 完成：**56 passed in 68.94s，exit 0**，包含既有正常与 0.2 秒采用快照延迟用例。没有复现新问题，本轮仅更新本报告，未改测试或业务实现。
- 当前范围以 `docs/PLAN.md` 19:32 与协调消息 `msg_487a913da91c` 为准：主控确认两个前置通过，恢复 T 的正式适用回归。完整回归、类型、构建及双平台 CI 由 E/D 完成后的独立 I 对最终累计 SHA 统一复验；本轨不重复全量。
- 前一 Dispatch 因 18:31 前置拒绝而未完成，已于报告提交 `9f59c0046ea6079f92c42b28eec5661c04c9373b` 留档；本次 `ctx_1108d942d74b` 复用既有环境完成上述收尾，不重装依赖。本轨未调用 Hub 或真实模型。

## 环境准备

复用已安装的 Python `3.12.13` 和 Poetry `2.5.1`；未安装全局工具、未修改全局配置。CI 配置使用 Python `3.13`，因此本机 Python `3.12` 结果不能替代最终 CI。

复用的基础解释器：`C:/Users/DW/AppData/Roaming/uv/python/cpython-3.12.13-windows-x86_64-none/python.exe`。

复用的 Poetry 环境解释器：`C:/Users/DW/AppData/Local/uv/cache/archive-v0/EPS9RnUeXNpjmRSc/Scripts/python.exe`；通过 `-B -m poetry` 调用，未写其安装目录。

运行安装前将进程级 `TEMP` / `TMP` 设为本仓库 `.runtime/freeze-test/temp`，`POETRY_CACHE_DIR` / `npm_config_cache` 分别设为 `.runtime/freeze-test/poetry-cache` / `.runtime/freeze-test/npm-cache`；`POETRY_VIRTUALENVS_IN_PROJECT=true`、`PYTHONDONTWRITEBYTECODE=1`。缓存与证据均不入 Git。

| 命令 | 本机结果 | 原始日志 |
|---|---|---|
| 基础解释器 `-B -m venv .venv` | exit 0 | 终端回执 |
| Poetry 环境解释器 `-B -m poetry install --no-root --no-interaction --no-ansi` | exit 0，82 installs；按现有锁安装 | `.runtime/freeze-test/logs/poetry-install.log` |
| `npm ci --no-audit --no-fund` | exit 0，99 packages；Node 24.16.0 / npm 11.13.0 | `.runtime/freeze-test/logs/npm-ci.log` |
| `.venv/Scripts/python.exe -B -c "import sys,pytest,langgraph,pydantic,sqlmodel,httpx,mcp,faiss,sklearn; print(sys.executable); print(sys.version.split()[0]); print('locked imports OK')"` | exit 0，项目解释器、3.12.13、imports OK | 终端回执 |
| `npm run check:sdk` | exit 0；schema 1.14.0，schema_valid / asset_id_verified / tampering_rejected=true，published=false | 终端回执；仅 contract_local |
| `git diff --exit-code -- poetry.lock package-lock.json pyproject.toml package.json` | exit 0，无变动 | 终端回执 |

`--no-root` 安装全部锁定第三方依赖；项目代码由当前工作区导入。这不是 wheel 安装或前端构建验收。

## 反馈顺序与墙钟原因

当前源码的调用顺序是同步的：`Runtime._feedback` 调用拓扑 `record_feedback`，随后写 `feedback` 事件并触发观察器；`Runtime.start` 的同步 graph 调用返回后，`Rehearsal._task` 才生成 Gene 并发出 `gene_generated`。拓扑的 `snapshot()` 复制管道状态，`_record()` 按离散反馈更新权重；此流程没有定时拓扑衰减或待等待的后台反馈任务。

第一条管道初始权重为 1.0，成功反馈按既有策略更新为 `(1 - 0.1) * 1.0 + 1.0 = 1.9`。因此现有管道断言检测真实反馈效果，不依赖快照足够快；没有复现到该断言的竞态。

Gene 的 `LocalMetabolism.mark_used` 则以实际采用时刻刷新锚点，快照以实际观察时刻计算 `exp(-(evaluated_at - last_used_at) / tau_seconds)`。当 tau 为 0.1 秒时，超过约 0.0693 秒后权重就低于 0.5；旧断言把正确衰减误判为失败。既有 0.2 秒延迟用例在采用后、观察前延迟，用来暴露旧假设，而不是等待系统变绿。

本轮原始快照核对（`baseline-inspection.json`）如下：

| 既有参数 | 采用至快照耗时 | Gene 权重 | 旧 `> 0.5` | 初始 / feedback 事件 / gene_generated 管道权重 |
|---|---:|---:|---|---|
| normal | 0.016468763 秒 | 0.848158599 | true | 1.0 / 1.9 / 1.9 |
| slow-adoption-snapshot | 0.216462612 秒 | 0.114792845 | false | 1.0 / 1.9 / 1.9 |

两次均 `completed`，feedback 时间不晚于 gene_generated，现有测试保留采用身份、时间锚点、实际执行成员改变、归档后不可检索和只读 replay 检查。

## 前置放行后的正式 T2 回归

开始及结束 HEAD 均为 `25968dc8440a25f2472df8cfb7ff62eb3302366d`，分支仍为 `codex/morphogenesis-mainline`。实际起止时间为 **2026-09-23T11:45:38.4399564Z–11:46:49.9648330Z**。运行期间共工作区保留 E/主控未提交改动；T2 测试及运行时相关目录无工作区差异，所以此处记录的是该基线加当时共工作区的本机适用结果，不是最终累计主线验收。

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:TEMP=(Resolve-Path .runtime/freeze-test/temp).Path
$env:TMP=$env:TEMP
.venv/Scripts/python.exe -B -m pytest tests/t2 -q -p no:cacheprovider --basetemp .runtime/freeze-test/temp/pytest-t2-ctx1108-01 --junitxml .runtime/freeze-test/formal-t2-ctx1108-01/junit.xml
```

结果：**56 passed in 68.94s，exit 0**；JUnit 为 tests=56、failures=0、errors=0、skipped=0。解释器实际为项目 `.venv/Scripts/python.exe`，Python **3.12.13**、pytest **9.1.1**。本次 basetemp 是进程 TEMP 下的新目录，没有复用或清理前次产物。测试使用 fake CLI、mock transport 和真实本地子进程复核，仍只建立 `contract_local` 证据。

原始命令/起止 SHA/退出码、pytest 输出、JUnit 及只读提取摘要分别保存在 `.runtime/freeze-test/formal-t2-ctx1108-01/` 下的 `command.txt`、`pytest-t2.log`、`junit.xml`、`inspection.json`。两个完整彩排 fixture 原件保存在 `.runtime/freeze-test/temp/pytest-t2-ctx1108-01/test_complete_rehearsal_routes{0,1}/run/rehearsal.json`；本次未改写原件。

| 既有参数 | JUnit 用例耗时 | 采用至快照耗时 | Gene 权重 / 公式期望 | 旧 `> 0.5` | 初始 / feedback / gene_generated 管道权重 |
|---|---:|---:|---:|---|---|
| normal | 8.310 秒 | 0.014764071 秒 | 0.862741038 | true | 1.0 / 1.9 / 1.9 |
| slow-adoption-snapshot | 8.508 秒 | 0.217553139 秒 | 0.113547800 | false | 1.0 / 1.9 / 1.9 |

两次快照均完成并满足实际衰减公式；延迟用例明确跨过旧固定下界仍通过，验证既有修复无需新增 sleep。`repair_reviewed` 阶段先后用于 review 与 feedback 两个事件，第一次独立复核快照的管道权重仍为 1.0，反馈后的同名阶段才为 1.9；提取摘要保留两个快照的 sequence/时间/权重，不能把第一次 review 当成反馈完成。最终快照均为 `provenance=mock`、`contract_local=passed`、`interface_live=task_live=not_run`、`cost_usd=null`。

回归后 `git diff --exit-code -- tests/t2/test_rehearsal.py poetry.lock package-lock.json pyproject.toml package.json` 为 exit 0。本次不新增竞态修复，也未改动锁文件。

## 放行前的本机基线命令与失败保留

定位时 HEAD：`2b58b5923286af8e11e556a1579e239bceee539b`；`tests/t2/test_rehearsal.py` 无工作区修改。

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:TEMP=(Resolve-Path .runtime/freeze-test/temp).Path
$env:TMP=$env:TEMP
.venv/Scripts/python.exe -B -m pytest tests/t2/test_rehearsal.py -q -p no:cacheprovider --basetemp .runtime/freeze-test/temp/pytest-baseline-2
```

结果：**7 passed in 30.72s，exit 0**。日志：`.runtime/freeze-test/logs/pytest-baseline-2.log`；完整 fixture 产物位于 `.runtime/freeze-test/temp/pytest-baseline-2/test_complete_rehearsal_routes{0,1}/run/`；提取摘要为 `.runtime/freeze-test/logs/baseline-inspection.json`。

首次命令误用 `--basetemp .runtime/freeze-test/pytest-baseline`，位于进程 TEMP 的同级，触发 `Rehearsal` 原有的 `ValueError: rehearsal requires a new private root under OS TEMP`：**6 failed / 1 passed in 5.40s，exit 1**。日志保留在 `.runtime/freeze-test/logs/pytest-baseline.log`。这属于本轨验证命令配置错误，不是产品回归；只修正命令路径并使用新目录重跑，没有修改隔离校验或删除旧产物。

## 待执行与限制

- T 的正式适用回归已完成；最终累计 SHA 的全量 pytest、类型、构建和双平台 CI 由 I 确认。本轮未运行或查询远端 CI，不声明其通过；本机 Python 3.12 不能替代工作流指定的 Python 3.13。
- 本次提交范围仅本报告，独占 Git 时段由主控串行协调；只显式暂存自有路径，不暂存其他轨文件。
- 本轨未执行真实模型请求、Hub 写入、live 彩排、公网部署或物理展示；未知费用不估算，两轮定位/回归 fixture 始终为 mock。
