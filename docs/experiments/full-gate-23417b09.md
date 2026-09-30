# 固定代码候选：本机失败与双平台 CI 分开

候选 `23417b09ffc93fbc432da0f63a7abec2546fd825`，测试期间代码和测试保持冻结。
此文档是运行后记录；不改变原断言、阈值、日志或结果，也不把本机失败改写为通过。

## 本机原始 gate

Python 3.12.13，Poetry 2.3.2 创建的独立环境；执行前已按现有锁文件安装依赖，
`npm ci --ignore-scripts` 成功，Node package/lock 未修改。
进程环境 `OPENBLAS_NUM_THREADS=1`、`OMP_NUM_THREADS=1`；未改全局设置。
命令 `python -m pytest -q`，exit 1：**12 failed, 943 passed, 2 warnings, 1615.07s**。
不是 C 专项通过后的全仓通过；12 项失败全部保留，未再次运行 full。

原完整 stdout/stderr：
`C:/Users/DW/AppData/Local/Temp/morph-sandbox-live-0930/full-23417b09.log`，
SHA256 `b82231db0ed6856a5861d1caa5d3fada6a8ca1c827d79fd96fe7fe81ef16b40c`。
同目录 `full-23417b09-result.json` 保存原 SHA、命令和退出码。
以下行号指该原日志；四个 Worker audit 已复制至同目录 `full-23417b09-audit/<case>/`，
避免后续 pytest 清理 `pytest-305` 时丢失诊断。

| # | 原失败测试（`tests/` 下） | 原始事实 / 诊断边界 |
|---|---|---|
| 1 | `integration/test_demo_environment.py::test_demo_excludes_sentinel_from_viewer_and_passes_executor_args` | 原日志 16–111：自有 demo 的 pwsh 子进程超过原 30s timeout；没有底层原因记录，不能直接归为内存。 |
| 2 | `swarm/test_assets.py::test_static_failure_quarantines_without_running[import subprocess\n-dangerous_import]` | 114–185：发布时 Node `computeAssetId` 返回非零且没有合法 SDK JSON，`sdk_process_failed`；原 stderr/退出数值未在 pytest traceback 中保留，根因 unknown。 |
| 3 | `swarm/test_assets.py::test_process_crash_leaves_partial_patch_quarantined_and_scope_blocked` | 188–272：原 publication child 已 exit 71、文件/账本断言已过；最后读取状态的 Node `validateAsset` 发生 `sdk_process_failed`。不能说 publication 原断言失败，Node 失败根因 unknown。 |
| 4 | `swarm/test_failure_chain_boundaries.py::test_unknown_effect_stops_chain_and_preserves_real_usage_state[False]` | 275–300：`failed != sleeping`；留存 `test_unknown_effect_stops_chai0` audit 的 `execution.failure_stage=snapshot`、`failure_kind=AssetSafetyError`、`failure_reason=asset_safety_rejected`，并非已观测到 unknown-effect 分支错误；更底层原因未记录。 |
| 5 | 同上 `[True]` | 301–323：同一状态偏差；`test_unknown_effect_stops_chai1` audit 同样在 snapshot 阶段 AssetSafetyError，底层原因 unknown。 |
| 6 | `swarm/test_failure_chain_boundaries.py::test_chain_cumulative_budget_and_attempts_limit_actual_sends[capacity-False]` | 325–361：`failed != sleeping`；`test_chain_cumulative_budget_a0` audit 记录首次 confirmed_rejection 切换 beta 后 snapshot 的 OSError、`os_errno=22`。不能由这个 errno 推出 pagefile 根因，也不能当成预算分支通过。 |
| 7 | 同上 `[capacity-True]` | 363–398：`failed != sleeping`；`test_chain_cumulative_budget_a1` audit 在 snapshot 阶段 AssetSafetyError，底层原因 unknown。 |
| 8 | 同上 `[task_attempts-False]` | 400–437：fixture 创建阶段 `git init -b swarm-local-demo` 返回失败，`git_operation_failed:init`；未到预算断言，Git stderr/退出数值没有被 traceback 保留。 |
| 9 | `swarm/test_fault_drill.py::test_worker_calls_explicit_executor_and_persists_its_unbounded_contract` | 438–593：准备 worker 前 `subprocess.Popen` 的 CreateProcess 抛 `WinError 1455`（页面文件太小）；有直接宿主资源错误证据。 |
| 10 | `swarm/test_fault_observations.py::test_process_crash_before_index_commit_recovers_without_duplicates[indexed-True]` | 595–647：预期 crash exit 23，实际 exit 1；子进程导入 `_sqlite3` DLL 失败，错误明确页面文件太小，尚未执行预设 crash 点。 |
| 11 | `swarm/test_fc_logging.py::test_concurrent_append_and_partial_tail_preserve_facts` | 649–702：3 线程、6 次 append，在既有 `BEGIN IMMEDIATE` / 原 timeout 0.05s 遇 `sqlite3.OperationalError: database is locked`。原锁失败真实保留；高负载是可能因素，不是已证明的唯一根因；没有调大 timeout。 |
| 12 | `swarm/test_probe_lifecycle_recovery.py::test_recovered_history_cannot_resuspend_but_new_failures_can[same_worker]` | 704–875：worker 的 snapshot 调用 CreateProcess 抛 WinError 1455，直接页面文件错误；未宣称 recovery 断言已通过。 |

本轮终端另外观察到 `System.OutOfMemoryException`、gh.exe 启动时页面文件不足、
shell startup exit -1073741502；主控也独立观察到 Python/OpenBLAS 分配失败。
这些确认当时宿主存在资源压力，**不能证明上述 12 项都只有同一个原因**。
所有失败位于现有 integration/swarm 路径，本轨没有修改它们；没有确证实验模块领域 bug，
残余 Node/Git/snapshot/锁原因已 Handoff，由主控决定原 Owner 的后续诊断。

## 同 SHA 独立 CI 事实

[CI 36717414791](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/36717414791)
的 headSha 完整匹配上述候选；两个 job 的 pytest、全仓 strict、build、SDK smoke、
独立 wheel 安装/资源验证全部 success。CI 按仓库现行 workflow 使用 Python 3.13 / Node 24，
与本机 Python 3.12.13、共享 Windows 开发宿主不是相同环境。

| 平台 / job ID | pytest 原输出 | 其他结果 |
|---|---|---|
| Ubuntu / 109893658202 | 954 passed, 1 skipped, 75 warnings, 347.76s | strict 97 files；sdist/wheel、SDK、独立 wheel 13 packages/resource/verifier/node 检查通过 |
| Windows / 109893658465 | 955 passed, 75 warnings, 1022.31s | 同上全部通过 |

CI 原日志下载到 `C:/Users/DW/AppData/Local/Temp/morph-sandbox-live-0930/ci-23417b09-all.log`，
SHA256 `d275f2ceeb19fb7c5d9ff7e181fec66b31e5b13bf5a7fff9637be90ae7fe8aaf`。
Ubuntu skip 是现有平台差异，未删测；Windows 没有 skip。
CI 成功只属于 contract_local，不修复历史失败，不提供 OpenSandbox CPU 或原生 Agent task_live 证据。

## 更早 gate 不能混入本候选

早期 full 缺少 Node 本地依赖且源文件仍在继续开发：98 failed、785 passed、69 errors，exit 1。
它是可变 checkout 的诊断，不是任何固定 SHA 验收；工具完整输出被截断，
仅实际收到的 tail/失败列表保存为 `full-first-tool-tail.log`，不能称为完整原日志。
补齐已授权的 ignored Node 依赖后才运行上面固定 SHA 的新 gate，未改旧测试断言。

最初 strict 的 8 个错误已按实际 SDK 1.1.0 API 修复；本机冻结候选的
`python tools/typecheck.py` exit 0：97 files，原日志 `strict-23417b09.log`。
官方 release 的选择性 SDK upstream 测试 33 passed，只是选定 API 的 contract 检查，不是全上游验收。
在 TEMP release 源码根目录、使用本轨锁定 SDK 环境运行的命令：

```text
python -m pytest -c sdks/sandbox/python/pyproject.toml sdks/sandbox/python/tests/test_sync_command_service_adapter_streaming.py sdks/sandbox/python/tests/test_sandbox_destroy.py sdks/sandbox/python/tests/test_filesystem_upload_transport.py sdks/code-interpreter/python/tests/test_code_service_adapter_openapi_calls.py -q
```
