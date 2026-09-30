# A 原生 Agent 接入轨 · Owner 报告

基线 ef77af603577d4539d8dbdf780e1536a369b0d12，计划提交 6ba12b24781318383454d2e7fb0b132e897b8a8d；Owner 分支 songconmaisaix31-design/morph-research-agents-0930。仅写 orchestration/native_agents/**、tests/native_agents/**、docs/agents/** 与本报告，未改旧 sample executor、公共依赖/锁或其它轨道，未创建 Agent/Run。

实现：两种官方 native_cli 注册、实际 npm bin 发现、只读 auth/version、typed argv 交互/headless/resume/MCP、bootstrap 主动发现认领提示、未知事件/usage/exit 语义、原生 raw JSONL、绑定既有 AgentId/AttemptId 的持久证据接口、own/attached 取消隔离。Windows 使用官方 Job Object + 启动屏障，POSIX 私有进程组；没有派单或自动恢复/重试。

来源：stablyai/orca 固定 85f8d6b5f507df795cd3cef1cdea08124cf801ee，MIT Copyright 2026 Lovecast Inc.，许可已保留；已核对指定 shared 文件、真实依赖和有关测试，窄行为适配与独立原模块运行见 docs/agents/upstream.md。Codex 0.159.0 Apache-2.0 和 Claude 2.1.238 自身许可独立，未复制 CLI 实现，无 SDK 结论。

第一阶段代码提交 `5623ee73d948ed3b6494d43ca0cf1027ce0943a4` 已 commit+push，`git ls-remote` 与本地完整 SHA 一致。后续仅工具面测试/启动示例与验证报告收口，运行源文件未再改变。

当前本地证据：

- `python -m orchestration.native_agents probe`：Codex 0.159.0 / Claude 2.1.238，两者 version/auth exit=0、authenticated=true、精确版本相符。只读前置，不是模型/MCP interface_live。
- 新建/恢复、交互/headless 共 8 个原生 argv 的 `--help` 解析：全部 exit=0，未发送模型请求。
- `python -m pytest tests/native_agents -q --basetemp=tests/native_agents/.runtime/pytest-stage1 --tb=short`：73 passed；真实 subprocess / Windows Job Object / 外部附着进程保留 / unknown / canonical binding fixture 契约均覆盖，provider 数据为 mock。
- 最终工具面收口后 `python -m pytest tests/native_agents -q --basetemp=tests/native_agents/.runtime/pytest-final --tb=short`：75 passed，新增旧 claim_task / 新 lease_task 名称兼容的 canonical 回包追踪；运行代码仍为第一阶段 SHA，未在适配器分配任务。这是 Owner self-test；独立 I 验收尚 NOT_RUN。
- `python -m mypy --strict orchestration/native_agents`：10 source files，通过。
- `git diff --no-index docs/agents/.reference/src/shared/print-mode-headless-command.ts tests/native_agents/upstream/print-mode-headless-command.ts`：exit=0；pytest 实际用 Node 24.16.0 内置 TS stripping 跑 unchanged 上游纯模块，与 Python port 比较。上游全套 Vitest/Electron测试 NOT_RUN。
- `python -m pytest tests/t2/test_codex.py -q --tb=short`：默认 OS temp 下 11 passed，旧安全门/代码/断言未改；保留初次源码树 --basetemp 失败。
- 已有项目 Python 3.12 .venv 的 `python -m build --outdir tests/native_agents/.runtime/dist`，仅该子进程设 PIP_INDEX_URL=https://pypi.org/simple / PIP_EXTRA_INDEX_URL=''：sdist 与由 sdist 构建 wheel 均成功，isolated poetry-core=2.5.0；未改全局 pip 配置、源码依赖或锁。
- wheel 分发检查：10 native Python 文件 + ORCA_LICENSE.txt 均在 wheel；无 .reference/.runtime 产物。解包到本轨 ignored wheel-site，隔离 cwd 导入分发包后运行真实 subprocess mock headless（含 Windows 屏障/Job），PACKAGE_SMOKE_EXIT=0。非 native/model验收。

历史失败保留，不覆盖：

| 首次/阶段命令 | 原结果 | 有界诊断和处理 |
|---|---|---|
| 错猜 `node .../@anthropic-ai/claude-code/cli.js` version/auth | MODULE_NOT_FOUND | 实读当地 npm shim/package.json：2.1.238 bin 为 bin/claude.exe，解析使用真实 bin map，未安装/升级/切换账号 |
| 初次新目录 strict | 11 errors | 修正 object narrowing、Literal 和跨平台类型；未降 strict |
| native pytest-first，指定未存在 .runtime 父目录 | 38 passed / 26 setup errors，WinError 3 | 新建本轨测试输出父目录；未改断言 |
| native pytest-second | 58 passed / 6 failed | `orca` 子串断言误把合法工作区父目录当依赖；保留失败，改为实际 executable/argv 语义检查，未增加 Orca 产品依赖 |
| native pytest-third，新增启动屏障 | 62 passed / 2 failed | native 未启动却误用屏障 exit，修复独立 launch-error 日志使 exit 保持 None；保留 0.2 秒 timeout 阈值，错误留存测试用确定 observer clock 等待真实 subprocess 发出错误，另加真实 wall timeout 检查 |
| native binding strict | 1 object-not-indexable error | 使用窄化的 dict payload 修复；未加 ignore |
| 系统 Python `-m build --no-isolation` | No module named build | 复用原项目已有 .venv 作构建检查，不动公共依赖/锁 |
| 原项目 .venv `-m build --no-isolation` | Backend poetry.core.masonry.api unavailable | 改用构建工具标准 isolated build，不往原 venv 安装后端 |
| isolated build 默认镜像 | sdist成功，wheel fresh backend 下载 HTTP403 | 原失败日志保留；仅 build 子进程显式选择官方 PyPI，sdist/wheel完整同候选复验通过 |
| wheel smoke 初次临时 harness | SyntaxError：嵌套引号，native未调用 | 修正 harness 用 repr 构造 Python 字面量，包内代码不改；实际分发 mock subprocess smoke exit=0 |
| 旧 tests/t2/test_codex.py，源码树 --basetemp | 2 passed / 9 failed：既有 executor 要求 OS temp | 原门禁、断言和旧代码保持不变；默认 OS temp 复验单列 |

首次 readiness timeout 为开发终端历史：已 skip 升级提示，用户只读 cwd/SHA/branch 探针通过后沿同 Task retry；这不是产品门禁。

接口 Handoff：B 提供官方 FastMCP stdio `python -m swarm.research --config ABS_TRUSTED_JSON`，host 身份权限不由工具参数决定。A 不合并 B 分支；canonical claim 回包新 attempt_id 随 B 最终 SHA 交付，旧阶段29446a0只有 Lease，A 不凭空补身份。B已通知工具面最终收敛为11工具，claim入口为 lease_task(action=claim)；测试覆盖旧/新名称，bootstrap示例对应最终面，以I候选实际metadata为准。native-bound 只是可追溯报告，不替代 B authoritative ledger / fencing / 科研判据。

实现证据（基于运行代码5623ee73，以下行号属于该SHA；测试/文档收口不改变源文件）：

- `orchestration/native_agents/registry.py:49`：实际 npm bin map，拒绝 package逃逸与未知Windowsshim；`:95`：有界版本/认证，不执行模型；`:90`：原认证位置继承、ORCA环境能力剔除。
- `orchestration/native_agents/launch.py:10`：typed argv / 原生权限 / 逐次MCP配置 / trusted host binding；`:76`：MCP文件独占创建。
- `orchestration/native_agents/models.py:83`：复用既有AgentId身份；`:103`：原事件与报告的AttemptId；`:129`：bootstrap只提供空间/角色/规则/工具，不挑选任务。
- `orchestration/native_agents/events.py:38`：只解析原canonical attempt_id，不构造新身份；`:57`：未知事件/原始回包/真实CLI结构化事件保留。
- `orchestration/native_agents/process.py:24`：attached取消无权限；`:35`：仅own Popen/Job取消；`:93` 与 `_windows_exec.py:12`：Windows归属后才启动CLI；`:124`：单次有界headless、无重试；`:192`：host/session/原回包持久trace；`:251`：exit与terminal同时判定，不冒充科研通过。

ignored原始检查日志保留在 `tests/native_agents/.runtime/`（pytest-second/third/fourth/binding/stage1/final、legacy与legacy-os-temp、mypy-binding、build-existing-venv/build-isolated/build-official-index、package-smoke等）；初次setup/strict/错误CLI路径的准确命令/原错误同时保留在本报告和终端记录。秘密、prompt运行数据和缓存未入库。

限制与未执行：真实原生模型、MCP工具连接、真实 claim/实验/复现/adoption、原生持久 session 恢复与交互 TUI 均 NOT_RUN，由最终 I 在统一候选按最多3会话运行；Linux/WSL实际进程组及原生环境尚 NOT_RUN。无硬 token/cost 封顶，observer工具限制不能撤回已发出请求，费用/远端效果 unknown不重试；附着会话无 stdin 接管，后台脱离进程组资源无清理保证。Hub/生产部署/tag/公共主线合并未执行。

## 原 Owner 返修：CI fixture 可移植性

原交付 `648f43c54203f555b1b05827cfe119c8e3dfa622` 与其 accepted worker_done 保留。其本机 75 passed 是安装了 Codex 的 Windows Owner self-test，不能据此推断无原生 CLI 的 contract CI 通过。

首次合并候选 `85a921c49addcdd46c2cb4a307c3515356b3e186` 的 CI run `36728997575` 原结果永久保留为 failure：Ubuntu job `109933248463` 为 1 failed / 1062 passed / 2 skipped / 75 warnings，388.10s；Windows job `109933248105` cancelled，下游 strict/build 未通过。唯一失败是 `tests/native_agents/test_process.py::test_unknown_launch_exit_and_mock_cannot_be_live`：原行143的 `pytest.raises(ValueError, match="official CLI")` 在无 Codex 环境先遇到 `registry.py:58` 的 `FileNotFoundError`。

此次仅固定该测试的外部 `process.resolve_executable` 发现边界，返回确定的 official command prefix（不创建或认证可执行文件），与 Python fake_plan / missing.exe argv 均不同。真实 `run_headless` 和 `_require_native_command`、原 ValueError 类型/quote 断言、mock missing launch 的 exit=None/state=unknown 断言与 live 目录不存在断言保持不变；未修改生产文件、安装 CLI 或执行模型。`process.py:140` 的防伪 guard 在 `:144` 创建 evidence 目录、`:207` 调用 `_spawn_owned` 之前，原 live 目录不存在后置断言验证拒绝发生在任何 live Popen 之前；没有替换 guard 或 Popen。

阶段静态检查为 `git diff --check` 和完整 diff 审核，通过后先 commit+push `f37ada292f61a28899666a84a8c988da5a4c0a40`，远端 SHA 一致且 clean；该阶段本地 test / suite / strict 均准确记录为 NOT_RUN 待窗口，没有预写通过。

主控释放短时 Python 窗口后，固定上述 SHA，使用 `C:/Python313/python.exe` 与进程局部 OPENBLAS_NUM_THREADS / OMP_NUM_THREADS / MKL_NUM_THREADS / NUMEXPR_NUM_THREADS=1 串行执行：

- 仅此子进程 PATH=''，`python -m pytest tests/native_agents/test_process.py::test_unknown_launch_exit_and_mock_cannot_be_live -q --basetemp=tests/native_agents/.runtime/pytest-ci-portability-empty-path --tb=short`：1 passed，1.06s，原 guard/异常 quote/unknown/live-dir 断言均通过，不依赖 installed native CLI。
- 恢复 PATH，`python -m pytest tests/native_agents -q --basetemp=tests/native_agents/.runtime/pytest-ci-portability-native --tb=short`：75 passed，25.66s，contract_local/mock。
- `python -m mypy --strict orchestration/native_agents`：10 source files 成功，Windows 本机静态验证。

串行命令 exit=0，原始日志为 ignored `.runtime/ci-portability-empty-path.log`、`ci-portability-native.log`、`ci-portability-strict.log`；完成后立即明确释放 Python 窗口给 I，没有重跑全库或任何模型/沙箱 live。

阶段分支 CI run `36731189645`、固定 `f37ada2` 的 Ubuntu job `109940929487`：原 pytest 998 passed / 2 skipped / 75 warnings，360.84s；随后原 strict/typecheck 失败，`windows_job.py` 的 ctypes.WinDLL / WinError / get_last_error 在 Linux 类型定义下共 11 errors / 99 source files。该新失败保留，已经跨轨 Handoff 主控；Windows job `109940929018` 查阅时仍运行，下游 build/分发未通过。Windows 本机 strict 通过不能替代 Linux strict。可用 `gh api repos/songconmaisaix31-design/Morphogenesis/actions/jobs/109940929487/logs` 读取原完成 job 日志，不改变 workflow 或门禁。

完整合并门禁、真实科研 live、SDK 仍未由本次 fixture 返修执行，归 I 统一验收；原 `85a921c` CI failure 保持 failure。

### 同 Owner 追加：Linux strict 的 Windows FFI 类型绑定

主控收到上述新失败后明确授权原 A 在原路径内窄修 `windows_job.py` 并继续短 Python 窗口。`os.name != "nt"` 的原运行时拒绝保持；仅在其后通过 `getattr` 绑定官方 ctypes.WinDLL / WinError / get_last_error，避免非 Windows typeshed 缺少专用符号的静态错误。没有 type ignore、检查排除、Linux gate 改为 win32、认证/权限更改或新 Job 系统。原 kernel32 签名、Windows Job 归属、启动屏障、cancel、关闭句柄与原生错误码保持。

新运行源码冻结为 `2f4b51587e53ecd31dfaf070957f638deed77d4a`（父 `a77317933c00537853e80204a5de6520d8a03152`），已 commit+push、远端 full SHA 一致、工作区 clean。仅这一源码文件相比父提交改变；固定上述代码重新运行原门禁，同样进程局部 BLAS 线程1：

- `python -m pytest tests/native_agents -q --basetemp=tests/native_agents/.runtime/pytest-ci-portability-ffi --tb=short`：75 passed，25.14s，含真实 Windows owned Job / 外部 attached 保留检查。
- `python -m mypy --strict orchestration/native_agents`：Windows 默认平台，10 source files 成功。
- `python -m mypy --strict --platform linux orchestration/native_agents`：Linux 类型目标，10 source files 成功；这是 Windows 主机上的静态检查，不是 Linux runtime 实测。
- 实际 Windows FFI 边界：创建/关闭真实 WindowsJob，检查绑定函数分别为 ctypes.WinError / get_last_error 本身；使用官方 set_last_error(123) 调用 error factory，实际 OSError.winerror=123，恢复原 thread-local error 后关闭 Job。`WINDOWS_NATIVE_FFI_BINDING_OK error.winerror=123`、exit=0；没有替换 native API 或假装 Linux 环境。

ignored 原始日志为 `.runtime/ci-portability-ffi-native.log`、`ci-portability-ffi-strict-windows.log`、`ci-portability-ffi-strict-linux.log`、`ci-portability-ffi-binding.log`。完成源码冻结推送后再次明确释放 Python 窗口给 I，文档收口不再启动 Python。

证据：`tests/native_agents/test_process.py:138` 的外部发现 fixture 与原异常/unknown/live-dir 后置断言；`orchestration/native_agents/windows_job.py:35` 原平台拒绝及其后的原生 FFI 绑定。最终文档提交仅更新本报告，代码/测试树需与 `2f4b515` 机械 diff=0；不为文档重复 suite/strict。

源码候选分支 CI run `36732932318` 在收口时 in_progress，尚无双平台通过结论；合并候选的原完整 gate 仍由 I 执行，不能用本机75或 Linux 静态目标替代。`f37ada2` 的 CI run `36731189645` 保持 failure（Ubuntu strict failure，Windows cancelled）；原 `85a921c` 的首 CI failure 也保持。真实科研 live、原生 SDK、Linux/WSL runtime 仍 NOT_RUN，本轮没有任何模型/OpenSandbox live、公共 main/tag 操作或其它轨道修改。

## 原 Owner 用量返修（2026-10-01）

本次 Task `task_527f87788de5` / Dispatch `ctx_cd11934cb2dd` 从原 A `84d59c167dd7fbb96081ce40b5cdfa5ba32d3bf3`、同 worktree/branch/write_paths 接续；原交付和前述各失败保留，不创建新 Agent/身份，不修改 B/C/I、锁或门禁。

触发记录：I 候选 `363cac52f515f5e810de2e3a65fa83bc8c7b859e` 的真实 Claude 2.1.238 session `5c787eb6-602b-4e03-9fea-313af2b5c826`（依据本次 I Handoff）实际 10 次 api_retry / 401 authentication_failed 后自然 exit1、tools0。只读核对 `C:/Users/DW/orca/workspaces/Morphogenesis/morph-research-integration-0930-state/research-host-7d04/replication-native/native.jsonl` 的结构和允许字段：10 条 system/api_retry，result 为 subtype=success、is_error=true、terminal_reason=api_error，四个 token 分量及 total_cost_usd 均0。原 Usage(0,0) 观察、认证阻塞、原文件和原第三任务 NOT_RUN 不覆盖；没有读取 prompt、凭据值或重新调用模型来验证修复。

规则先与主控明确后实施：Claude failed/未确认终态的零字段分别 normalized=None，有效正 tokens / 正 cost 独立保留；成功明确报告的零保持零。原 is_error=true / error_* 先于 success 的终态 guard 不改。真实 nonzero exit 可使 Invocation 失败，即使 event 明确 success-zero，失败 Outcome 的零也为 None，原 event/raw 报告不重写。原 missing/invalid 分量、多终态须各项已知才汇总、cancel/观察失败整次 unknown、远端效果 unknown、无自动重试规则保持。reported 数据不是可信完整账单，失败零不能证明无消耗。

最小生产改动仅 `events.py:106` 的 Claude result 用量字段与 `process.py:259` 的 failed Outcome 零字段；没有把全部失败清空，已知正数和 partial 字段继续保留。使用指南 `docs/agents/README.md:77` 对应明确此规则。

主控 `msg_ee6955b7c43f` 在 I 所有 Python/原生进程结束后明确移交短窗口。使用 `C:/Python313/python.exe`，仅进程局部 OPENBLAS_NUM_THREADS / OMP_NUM_THREADS / MKL_NUM_THREADS / NUMEXPR_NUM_THREADS=1：

- 首红：原 `84d59c1` 运行源码 + 新回归，`python -m pytest tests/native_agents/test_error_usage.py -q --basetemp=tests/native_agents/.runtime/pytest-error-usage-first --tb=short`，7 failed / 7 passed，3.97s、exit1；七个失败均为模糊零仍被当作已知零，正数/partial/cancel 原正向已通过。原日志 `.runtime/error-usage-first.log` 保留，断言和阈值不修改。
- 修复：`python -m pytest tests/native_agents -q --basetemp=tests/native_agents/.runtime/pytest-error-usage-fixed --tb=short`，89 passed，7.49s、exit0（原75 + 新14）。原 fixture/断言/阈值保持。
- `python -m mypy --strict orchestration/native_agents`，Windows 默认目标，10 source files 成功、exit0。
- `python -m mypy --strict --platform linux orchestration/native_agents`，Linux 类型目标，10 source files 成功、exit0；这是本机静态检查，不是 Linux 原生模型实测。

新 `test_error_usage.py:74` 的12种结果经过真实 run_headless / owned Popen / Windows barrier / stdout /实际 exit，Popen spy 使用 wraps 转发真实实现、每 case 调用1次，子进程 invocation marker 恰一条。子进程 httpx.MockTransport handler 的实际调用数由子进程记录：401复现 case 恰10，其它 case 恰1；Client 使用内存 transport + trust_env=False，无网络/model/API/MCP/sandbox 调用，不读取或变更账号/proxy/认证配置。raw stdout / on_event.raw 保留原数字，tools0，remote_effect 仍 unknown，acceptance 仍 not_run。`:103` 覆盖原失败不会被后 success 抹去及已报告正数保留，`:114` 覆盖正数报告之后实际取消仍 unknown、raw正数保留。这些是 contract_local/mock 传输数据，不能冒充真实401的新 live 或真实模型费用。

运行源码与新测试/指南冻结并 commit+push `3c4bc28e19abff7863007a2452b331762d10802e`，远端 full SHA 一致、clean。最终源码注释已纠正为 failure zeros cannot establish absent billing；纯注释澄清不改变已测试的可执行语句。Python 窗口完成后明确回交 I，随后只收口此报告，不重复 full/native/strict。ignored 原日志还有 `.runtime/error-usage-fixed-native.log`、`error-usage-strict-windows.log`、`error-usage-strict-linux.log`；秘密和本地运行产物未入库。

分支源码候选 CI run `36745648723` 在收口时 in_progress，尚无新双平台/full/build通过结论。I 负责精确合并、原完整门禁与真实 case 收尾；本次仅修正归一化，不解除真实 Claude 认证失败、不补第三任务通过，完整科研 task_live 仍未达成。模型/账号/认证/proxy 原状，原失败 JSONL/归档只读，未新调用任何模型/MCP/OpenSandbox，未操作 main/tag。最终文档提交仅本报告；代码/测试/指南树与 `3c4bc28` 保持机械 diff=0。
