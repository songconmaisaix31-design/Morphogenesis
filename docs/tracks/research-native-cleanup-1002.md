# A 原生进程清理返修（1002）

本轮只交付原生进程清理的 `contract_local` 修复。固定 Owner / terminal / worktree / branch 保留；没有科学、模型、认证、API、现场进程或服务器操作。SOURCE **`56ee35bcc31ab704ba53884b1ba96e3c93d00c4c`**，基线 **`9363fa822a004d12d57aee78ecf04fe3ab6555ed`**；原分支 `songconmaisaix31-design/morph-research-agents-0930`。从原 clean `dbbc08da5b5dbe4200beee6ffac254c913dc8db7` 正常 ff-only 到授权基线，随后正常 commit / push。最终 REPORT 是后续仅本文件的提交，其完整 SHA 随结算交付；SOURCE→REPORT 的业务/测试 diff 必须为零。

只修改 `orchestration/native_agents/process.py`、`windows_job.py` 和 `tests/native_agents/test_process.py`。`_windows_exec.py`、POSIX 原测试、其它 native 模块、产品、TaskLedger、日志、锁、科学判定及两个完整 checker 保持。原 checker blob `39948d9615bce07b40b96eeaf5dfb263b993c6d3`，新两类任务 checker blob `538f6b1852ccbba3f1cef6d09ad16b2a6fe8d4f5` 均在 SOURCE 未变。

## 原始现场事实与归属

只读原新案例 `research-formal-1002-nist-01` 的安全 summary 与 resume stderr：原 interrupt 55.5413967s / 5 tools，UUID `01a0f7df-bcbd-7cd3-8aec-e2dda578d278`，exit1 / state unknown / cancelled；首次同 UUID resume 12.0067s / exit1 / 0 tools，native JSONL 空，stderr 747 bytes / 5 行。两条模型目录刷新 request timed out 之后，明确 primary error 是 **thread-store conflict / already has an active writer / thread/resume code -32600**。这不是科研实验超时，不能据此修改模型目录、provider、TLS 或科学预算。

14:36 的 I 只读观察仍有 interrupt 自有 node→codex→python→python 四进程链，支持同 UUID writer 尚未及时退出的事实。原 trusted ledger claimed1 / renewed1 / research_execution0 / execution_unconfirmed0 / stale_rejected0，experiments 为空；它与 native usage / remote effect unknown 分开。root 后续 Handoff `msg_0909641af0d1`：I 于14:41:03.751Z行动前已观察这四 PID 不存在、exact case/UUID matching0，**没有执行 Stop-Process**，退出原因未知；原自有服务由 I 停止。本轨不操作现场，不将后来消失归因于成功 kill，也不回写首 resume / checker RED。

原证据只读根：`C:/Users/DW/orca/workspaces/Morphogenesis/morph-research-cases-integration-1002-state-ctx2e1675f71616/live/`，安全文件为 `research-formal-1002-nist-01-host/interrupt-actual-summary.json`、`resume-first-failure-summary.json`、`owned-native-closure.json` 及 `research-formal-1002-nist-01-state/resume-native/stderr.txt`。没有读取 profile、密钥、凭据或 provider 环境值。

## 确定性无模型复现与最小修复

Windows CPython venv `python.exe` 是本机 redirector，先创建真实解释器，再运行 Python 级 stdin gate。旧代码在 `Popen` 返回后给 redirector PID 分配 Job；如果解释器已创建，它不因父 PID 后来入 Job 而追溯加入。redirector 的子 Job 有 silent-breakaway 设置，后续 native 子进程可因此不在本适配层的 Job 中。依据是 [CPython v3.13.13 venvlauncher.c](https://github.com/python/cpython/blob/v3.13.13/PC/venvlauncher.c) 的实际 CreateProcess / AssignProcess 顺序，以及 [Microsoft Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects) 的子进程继承与 nested-job 规则。复用既有 ctypes 官方 Job API 和 CPython / subprocess，没有复制上游源码或新增依赖。

新增真实用例只在启动资源前记录实际解释器 PID，并在外部 Job.assign 边界等待该就绪信号；真实 Popen、Job.assign / terminate、run_headless / cancel 都执行。这样强制解释器先创建再 assign，而非反复运行等运气。无模型 stand-in 是实际 Python 子进程，事件明确 mock；持有真实 SYNCHRONIZE handle，取消后 `WaitForSingleObject` 首次返回258，证明 child 当时仍活；test finally 只清本 fixture 已明确拥有的 child Job。另一用例先让已入 Job 的父明确退出，子仍持 stdout/stderr，原 communicate 0.05s 超时；旧 cancel 返回 False。

精确旧基线非 editable wheel 上两项首次 **RED exit1：2 failed / 16 deselected / 8.23s**，原日志/XML/临时就绪信号全部保留。后来的绿色结果是新代码证据，没有改写旧结果。

修复仅包含：

- Windows 内部 stdlib 启动屏障直接使用当前 CPython 的 `_base_executable`，带 `-I -S`，避免 venv redirector 先派生以及 Python startup customization 在 gate 前派生；显式验证其类型和文件存在，缺失则报 launch failure。该屏障不需要 venv 第三方包，**正式 native argv、MCP 安装解释器、workspace、child_environment、认证及模型/tier保持原合同**，不把产品或 MCP 改到全局 Python。
- WindowsJob 增加官方 `QueryInformationJobObject(JobObjectBasicAccountingInformation)` 的 active-process count，覆盖嵌套 Job。取消先按 Job 活跃归属处理，父已经退出仍清 owned descendants；Terminate 后只等待这一个 owned Job 的 actual active0，等待界限3s，保留原 Popen reap timeout3s。查询/终止/等待失败实际抛错，CloseHandle 失败也抛错；不以 parent.wait / close 调用成功冒充后代已停止，不枚举进程名或持久 PID。
- root exit 后必须清后代时，Windows 与既有 POSIX 一样保持 Outcome unknown、normalized usage null；raw terminal / usage 和实际 exit 原样保留。正常 Job 已空返回False；重复 cancel 不再信号任何旧归属；AttachedSession 无取消能力、外部子进程保持存活。公开 `run_headless` / interactive / AttachedSession API 不变，Job accounting 只是内部归属检查。

三个必要新增 Windows 用例分别覆盖 venv gate 竞态、父先退出后 stdio 后代、真实 exit0/zero terminal 与后代强制清理时 unknown/null。没有更改原测试 body、时间阈值或 POSIX 断言，也没有外围库存测试。

## 独立环境与命令结果

`W = C:/Users/DW/orca/workspaces/Morphogenesis/morph-research-native-cleanup-1002-state-ctx3f0d93c01fc8`；创建前确认不存在。fresh CPython3.13.13 copy venv、原 poetry.lock 导出的冻结 runtime+dev、103 distributions（含本轮 core wheel），只复用 A 自身同锁官方下载 cache。没有复制旧 venv/site/node_modules/test artifact。TEMP/TMP、pytest basetemp、mypy cache 均本轨私有；BLAS/OMP/MKL局部1，未改全局配置/认证/HOME。

准备：`git -c core.autocrlf=false archive --format=tar ...9363...`，标准库 tarfile 解包（排除不用于构建的历史 docs），`uv tool run --with poetry-plugin-export poetry export --with dev --without-hashes --format requirements.txt`，`uv venv --python C:/Python313/python.exe`，`uv build --wheel`，`uv pip install --link-mode copy --python W/venv/Scripts/python.exe -r W/requirements.txt <wheel>` 均实际 exit0。候选轮没有代替冻结轮：SOURCE 提交后再从精确 GitLF archive 构建 `W/frozen-dist`，实际非 editable reinstall。

`W/22-frozen-installed-provenance-first.log` 首 exit0：三个 native 文件 archive/wheel/site bytes 一致、nlink1；测试来自本轮 frozen archive，安装到私有 site/tests，`python -I` / importlib 执行。direct_url 只指向 `W/frozen-dist/morphogenesis-0.1.0-py3-none-any.whl`，非 editable；没有工作树 source import。

| 命令 / 本轮首结果 | 实际结果与日志 |
| --- | --- |
| 旧基线 `python -I -m pytest ...test_process.py -k 'venv_barrier or cancel_after_parent_exit'` | **exit1 / 2 failed / 8.23s**，`05-regression-first-red.log/.xml/.exit` |
| 第一修复同两项 | exit0 / 2 passed / 4.29s，`08-regression-fixed-first.*` |
| 第一 strict `python -I -m mypy --strict .../orchestration/native_agents` | **exit1 / attr-defined1**，`09-native-strict-first.*`；未静默忽略类型问题，改为显式 getattr/类型验证 |
| 最终候选三个必要 Windows 用例 | exit0 / 3 passed / 5.64s，`12-regression-three-first.*`；候选 strict10 exit0，`13-native-strict-fixed.*` |
| 精确 SOURCE `python -I -m pytest W/venv/Lib/site-packages/tests/native_agents --import-mode=importlib -p no:cacheprovider --basetemp W/frozen-native-temp --junitxml W/19-frozen-native-first.xml -q` | **exit0 / 92 passed / 5 POSIX skipped / 66.66s**，`19-frozen-native-first.*`；原 Windows 防误杀/attached/timeout/failed/usage 和 Node builtin TypeScript oracle均实际运行 |
| 精确 SOURCE `python -I -m mypy --strict --cache-dir W/mypy-frozen-cache orchestration/native_agents`，cwd W/frozen-source | **exit0 / 10 source files**，`20-frozen-native-strict-first.*` |
| `python -I -m build --outdir W/build-dist W/frozen-source` | **exit0 / sdist + wheel**，`21-frozen-build-first.*`；官方 isolated poetry-core2.5.0 |

`L = /tmp/morph-research-native-cleanup-1002-state-ctx3f0d93c01fc8`：WSL Ubuntu Python3.12.3 全新 Linux filesystem state，创建前确认不存在；测试 TEMP/basetemp 都在真实 Linux filesystem，避免 /mnt/c 的 truncate/管道差异。首 inline Bash 命令跨 Windows 参数传输在 mkdir 前 exit1，`W/00-linux-shell-first.log` 留原命令/错误；改用本轨显式 Bash script，不更改全局 shell。官方 PyPI、private pip cache、原 requirements 约束只安装 native 专项必要依赖；没有额外科学/Node 模块安装或模型/科研调用。Linux 从同一精确 SOURCE tar 构建新的本机 wheel，非 editable 安装到新 venv，没有复制 Windows 安装产物。

- `L/venv/bin/python -I -m pytest L/venv/lib/python3.12/site-packages/tests/native_agents --import-mode=importlib -p no:cacheprovider --basetemp L/temp-native --junitxml L/04-native-first.xml -q`：**首 exit0 / 92 passed / 5 skipped / 15.83s**，`L/04-native-first.log/.xml/.exit`（Windows 收集输出也在 `W/16-linux-prep-first.log`）。原5个 POSIX真实父先退、TERM忽略后升级、stdio EOF、timeout、非私有root/外部保护全部通过，原断言/计时未变。4个 Windows-only 与1个本机 Node oracle 条件不满足跳过；Windows 已实际覆盖这5项。
- `L/venv/bin/python -I -m mypy --strict --cache-dir L/mypy-cache orchestration/native_agents`，cwd L/source：**首 exit0 / 10 source files**，`L/05-strict-first.*` 与 `W/23-linux-strict-provenance-first.*`。
- `python -m build --wheel --no-isolation --outdir L/dist L/source` / `python -m pip install --no-deps <L/dist wheel>`：实际 exit0，`L/02-build-first.log`、`L/03-wheel-install-first.log`；整个 script set-e、最终专项 exit0。
- `L/06-installed-provenance-first.log`：三 native 文件 source/wheel/site bytes 一致、nlink1，direct_url 为本轮 L/dist wheel，非 editable。原 POSIX 测试文件的 Git blob 与9363机械相等。

SOURCE 正常 push/ls-remote 的首命令均 exit0，原工作树 clean，日志 `W/14-source-push-first.*`、`15-source-remote-first.*`；原 strict RED1 / native RED2 / WSL参数传输失败保留，无重复同代码洗绿。没有运行未变工程全库、科学 checker 或模型。原 Node oracle 只用内置 TypeScript stripping，不需要 Node依赖安装。

## 真实限制

本次本机归属与停止检查只覆盖适配层新发起、保持在该 private Job / POSIX group 中的进程。未知远端效果/成本/用量保持 unknown/null；不能由本机 Job active0 推导远端没有效果或认证/模型兼容成功。对已自行派生的任意外部 Popen，事后分配 Job 不承诺追溯接管；产品正式路径从修复后的 stdlib gate 建立归属，没有恢复/杀附着会话权限。

原新 NIST 首 interrupt / resume / full-checker RED、无 experiment 和 active-writer 事实保留，未重试/回放原 case，也没有新科学 clock/UUID。原科学 case06历史证据不变。I 在新冻结 SOURCE 上的原完整 Linux+Windows full pytest/type/build/SDK/wheel-distribution、独立产品 pin/安装门及 root 释放后的新唯一科研闭环，均由 I 另行验收；本报告的 native focused green 不代签这些门禁。
