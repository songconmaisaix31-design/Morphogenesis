# A 原 Owner · 2026-10-01 进程清理

原 worktree `morph-research-agents-0930`、分支 `songconmaisaix31-design/morph-research-agents-0930`、原 Owner 接续 Task `task_45acb7d726b1` / Dispatch `ctx_500e88b29bfb`。初始 `b2199c2fcc03a41389f69c3a8ac20e69ec7eb87c` clean，按任务 `git merge --ff-only c45888f64c1cec60e5f9df45677b6547c4527cac` 成功；读取 AGENTS.md 与治理 worktree 的 RESEARCH_NEXT_PLAN_1001.md。没有新 Agent/Run 或其它轨道编辑。

仅修改 `orchestration/native_agents/process.py`，新增 `tests/native_agents/test_posix_process.py` 与本报告。WindowsJob、_windows_exec、原 test_process.py 和其它 native/科研/实验/锁/checker 保持。阶段运行源码 `0a192c6b037df0e70cedb17e8d2e8bfa28f0dd09` 已 commit+push，ls-remote 与 local HEAD 完整 SHA 一致、clean；最终报告提交与它的代码/测试树机械 diff=0。

## 修复与接口 Handoff

- 复用标准库 Popen.start_new_session、os.getpgid/getsid/killpg、signal 和官方 Windows Job，没有新增依赖、进程枚举/名称匹配、持久 PID、调度或自动重试。
- OwnedProcess 记录本次 fresh Popen 的私有组归属。原构造调用继续有效，新增兼容的可选 keyword `private_group=False`；`:42` 实际验证 pgid/sid==root pid，`:137` 的 `_spawn_owned` 对已明确请求 start_new_session=True 的内部调用显式传 True，覆盖 root 极快退出的构造竞态。只有 root 归属时只 terminate/kill 该 Popen，不向调用方的组发信号。
- `process.py:92` 的 `_cancel_group` 不以 root.poll/root.wait 判断后代清理完成：TERM 后最多原3秒观察该私有组，必要时 KILL 同组，再回收直属 root。ProcessLookupError 表示该组不存在；完成后丢弃组归属，重复 cancel 不重复发信号。没有扩大原3秒等待预算或原测试4秒阈值。
- `run_headless` 外部 API 不变。`:283` 在已观察 root exit 后仍需强制清理 owned descendants 时，reason 明确 outlived native exit，Outcome/usage 保守 unknown/null；raw terminal/usage 和实际 root exit 保留，remote_effect 仍 unknown。正常无残留组的完成、原 timeout/cancel/失败零用量规则保持。Windows Job 的分配/启动屏障/终止/句柄关闭及 attached 无取消权限路径未改。
- 小 Handoff `msg_336ee9c32255` 先交设计、真实 WSL 环境和计划命令；RED/PASS及兼容 keyword 说明 `msg_e0c905b6c4c8`，源码冻结/完整结果 `msg_2d68b20069cb` 已交主控。D 不与 A 共写；后续精确合并由主控分发。

## 真实环境与原 RED

Ubuntu 已处于 WSL2 Running，真实内核 `Linux 6.6.114.1-microsoft-standard-WSL2`、Python3.12.3。仅新建 `/tmp/morph-process-1001-a-ctx500e88` 独立 venv，按现有项目约束安装 pytest9.1.1、Pydantic2.13.5、httpx0.28.1、mypy1.20.2；未改全局安装/配置、认证、WSL 或 Docker 服务。Windows 使用已有 `C:/Python313/python.exe`，实际 Python3.13.13。两环境/cache 分开，BLAS/OpenMP/MKL/NumExpr 均仅进程局部1。

环境首次探针 `python3 -c ...import pytest...` 为 ModuleNotFoundError；首次带 `<` 的 WSL pip 参数发生 shell 重定向错误 `/bin/bash: 10: No such file or directory`，产生本轮自己的0字节 `=8,` 文件。保留终端错误，改从 `/dev/stdin` 读取约束后隔离安装成功；核对绝对路径/长度后只清理自身空文件，未入库、未删除其他贡献。该环境错误与以下行为 RED 分开。

真实 Ubuntu、原 c458 运行源码加新 regression：

```text
python -m pytest tests/native_agents/test_posix_process.py -q --basetemp=/tmp/morph-process-1001-a-ctx500e88/pytest-first --tb=short
5 failed in 1.99s, exit=1
```

原五个失败均保留：父已退出 cancel=False；父被TERM停止而同组子进程仍持有stdout/stderr，communicate(0.5)超时；headless自然退出和timeout后子进程heartbeat继续变化；非私有root错误地killpg(rootpid)报 ProcessLookupError。每个 RED 的 finally 都只停止测试自己 start_new_session 的组/自己的Popen，未留下活动后代或关闭旁路进程。

新五例是实际 POSIX 进程，不在 Windows 用 mock 冒充：子进程安装 SIGTERM ignore 后才发布 readiness，持续写 heartbeat并继承stdout/stderr；父明确退出或在TERM时退出。`:58` 检查EOF、4秒取消边界、重复cancel和旁路/attached活；`:89` 检查真实 run_headless 的自然退出/timeout、单次Popen、heartbeat停止、unknown/null；`:127` 的 root/旁路与pytest同组，验证只清理root而不发组信号。原断言、0.05/0.5/0.2/4秒阈值自首红起保持。

## 适用验证结果

以下命令在对应宿主运行；Ubuntu调用经 `wsl -d Ubuntu --cd /mnt/c/Users/DW/orca/workspaces/Morphogenesis/morph-research-agents-0930 -- env ... /tmp/morph-process-1001-a-ctx500e88/bin/python`，不是 Windows --platform 的 POSIX运行替代。

| 实际宿主 / 命令 | 原结果 |
|---|---|
| Ubuntu `python -m pytest tests/native_agents/test_posix_process.py -q --basetemp=/tmp/morph-process-1001-a-ctx500e88/pytest-fixed --tb=short` | 同原断言5 passed，13.12s，exit0 |
| Ubuntu `python -m pytest tests/native_agents -q --basetemp=/tmp/morph-process-1001-a-ctx500e88/pytest-native --tb=short` | 92 passed / 2 skipped，16.40s，exit0；skip为Windows Job API及无Linux Node的原TS oracle |
| Ubuntu `python -m mypy --strict --cache-dir=/tmp/morph-process-1001-a-ctx500e88/mypy-linux orchestration/native_agents` | 10 source files成功，exit0 |
| Windows `python -m pytest tests/native_agents -q --basetemp=tests/native_agents/.runtime/pytest-process1001-windows --tb=short` | 89 passed / 5 POSIX skipped，7.75s，exit0；原Windows Job后代清理/外部附着保护实际通过 |
| Windows `python -m mypy --strict --cache-dir=tests/native_agents/.runtime/mypy-process1001-windows orchestration/native_agents` | 10 source files成功，exit0 |
| `git diff --check`，源码/路径diff审核 | exit0，仅本轨指定3文件；相对完整c458基线核对 |

ignored 原日志在 `tests/native_agents/.runtime/process1001-posix-first.log`、`process1001-posix-fixed.log`、`process1001-native-linux.log`、`process1001-strict-linux.log`、`process1001-native-windows.log`、`process1001-strict-windows.log`。环境缓存与临时 pytest state 不入库；没有重复全量门禁或新增几十外围测试。

## 剩余范围与未执行

仅本轨进程清理 contract_local 结算；声明mock的CLI输出不是模型/科研live。源码分支CI `36761071721` 在收口时 in_progress，完整集成/full/build/双平台CI由主控分发 I，不预写通过。没有模型/科研实验/Hub/EvoMap调用、账号/provider切换、全局配置改动或main/tag操作。

本次只覆盖保持在 owned 私有组中的后代；脱离该组的daemon保持外部所有权。标准组信号可能仍观察到僵尸，直属root由Popen回收，孤儿收尸由OS承担；实际验证要求后代停止活动与管道EOF，未宣称所有/proc条目已消失或远端效果为零。附着/无关进程不纳入清理，原Windows归属边界保持。
