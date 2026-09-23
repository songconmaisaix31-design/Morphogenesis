# 封板夜 T 轨：环境准备与彩排竞态核对

日期：2026-09-23。工作区：`C:/Users/DW/orca/Morphogenesis`；分支：`codex/morphogenesis-mainline`。本报告只记录本机命令及其产物，不代表 CI、Hub、真实模型调用或现场验收。

## 当前结论与范围

- 项目内锁定依赖准备完成，可复用解释器 **`C:/Users/DW/orca/Morphogenesis/.venv/Scripts/python.exe`**。安装完成已通过 Orca 向主控汇报。
- 历史 Windows CI `35691719303` 的失败断言是 **Gene 采用快照的 `weight > 0.5`**，不是 `after_feedback.pipes[0].weight > original_topology[0].weight`。历史失败依据来自仓库 `docs/ACCEPTANCE.md`、`docs/tracks/rehearsal-runtime.md`，本轮未访问远端 CI。
- `git diff e83a816 94b7081 -- tests/t2/test_rehearsal.py` 确认：`94b70816784fcd46ce4f74b8e205bd009b789cc3` 已删除 Gene 固定下界，按采用记录、GeneRef、实际时间差及 tau 校验衰减，并加入 `normal` / `slow-adoption-snapshot` 参数。本轮不重复实现已存在的修复，不新增等待，不修改业务实现或测试文件。
- 未修改测试的本机基线为 **7 passed in 30.72s**。这是前置门禁放行前的定位证据；正式 `tests/t2` 和全量验证仍待门禁放行。
- 主控于 2026-09-23 10:31:41 UTC 通知：Evolver 唯一 hello 被 Hub 以 CAPTCHA 拒绝，等待用户决定是否调整前置；T 仅整理已完成核查，不执行领域修改、live 或部署。该事实为主控回执，本轨未调用 Hub。
- 本 Dispatch 的完整验收受前置门禁阻塞，不能标为完成；已准备的环境和既有修复核对可供后续复用。本轨没有未提交的业务代码，交付范围仅本报告。

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

## 本机基线命令与失败保留

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

- 等待主控转达用户对 Evolver 前置门禁的决定；门禁放行前不执行正式 T2 / 全量回归。
- 放行后按主控要求运行一次 `tests/t2` 和全量 pytest，使用不同的新 basetemp；最终累计 SHA 的测试与双平台 CI 仍由 I 确认。
- 主控治理 `d750a0e` 推送后已批准本报告的独占 Git 提交时段。提交范围仅本报告；只显式暂存自有路径，不暂存其他轨文件，测试、锁文件和业务实现保持不变。
- 未执行真实模型请求、Hub 写入、live 彩排、公网部署或物理展示；未知费用不估算，基线 fixture 始终为 mock。
