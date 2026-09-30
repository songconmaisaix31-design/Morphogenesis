# I 首次命令失败与 C 最小兼容修复

原运行 `interface-i-0930-bc4-01` 在 I 不可变候选
`bc4d017924d8d08454b97e6d0c1b5a84d4064fd6`：**interface_live=failed，provenance=live，task_live=NOT_RUN**。
原日志、archive、断言、result 不改，不重放，也不发新 sandbox/model/live 请求。

## 原始事实

原日志 `C:/Users/DW/orca/workspaces/Morphogenesis/morph-research-integration-0930-state/interface-i-0930-bc4-01.log`，
SHA256 `45b62780926b40fe12ca6923ca84fa92d5ce24b6204d5a6da70f461502bde705`。
原保护 archive 在同 state 根下 `interface-live/interface-i-0930-bc4-01`。

`interface.json` 记录实际 sandbox `d96ce63e-c418-40e0-82b5-b483b356af6e`，
metadata绑定 morph-run/interface-i-0930-bc4-01、morph-task/nist-numacc4-interface、
morph-worker/c-sdk-interface、morph-fence/1；create/connect/renew、附着拒杀、binary_roundtrip=true。
第一个 cgroup command 的官方响应是 HTTP400 `INVALID_REQUEST_BODY`，
`RunCommandRequest.Command` failed required，request_id `cf19659930344f89b642c9ff2622449b`。
没有 cgroup 结果，CPU/memory enforcement仍unknown；cancel与正式科研脚本未到达。
原 result 的 sandbox_id=null、execution/cleanup/remote_effect=unknown、exit/usage/cost=null、
scientific=not_evaluated保持不变。主控/I另报后续只读404/无对应容器，不能事后覆盖原unknown。
C 本次未关闭/启动服务、清理容器、复用该sandbox或执行远端命令。

## 官方版本和实际 HTTP 契约

- I 实际安装路径：`.../morph-research-integration-0930-state/envs/morphogenesis-aDl55zGp-py3.13/Lib/site-packages/opensandbox`。
  dist-info METADATA确认1.1.0、Apache-2.0；读取实际 `sync/adapters/command_adapter.py`，
  `run` 调官方 `ExecutionConverter.to_api_run_command_request(...).to_dict()`。
  `adapters/converter/execution_converter.py:90` 将 list 仅放入 `argv`，字符串仅放入 `command`。
- 官方研究初始 SHA `089b59ad48af33fc2733de58bd1a39c687c93b0a`；SDK/server release 源
  `b1a29cf93a823a95913f7943010febb3f29de05c`。这个源码的 execd 已含 command OR argv；**不能说此源码不支持 argv**。
- 部署 server 实际 image ID/digest仍 `sha256:68ca0212a2749b2c73096ce2ec0264455c64442c45f81007db442f52bf84c9d1`。
  config固定 execd `opensandbox/execd:v1.1.0@sha256:6cf7dba2f21f0b536e100563d841ac58a9f31c2b0a081b7ac76796a24d6f47e2`。
  本地 image inspect确认RepoDigest；image创建时间2026-08-28，Labels=null，没有 revision provenance，不能把新 release 的源码能力直接移称为这个二进制能力。
- 官方 `docker/execd/v1.1.0^{commit}` 为 **`48b0215f1bd097b31d0f022a44640e00c11ac49d`**，Apache-2.0；
  `components/execd/pkg/web/model/codeinterpreting.go:53` 是 `Command string json:"command" validate:"required"`，没有 argv。
  与原实际 required 响应一致；源 tag 与部署 image 是分别核验的证据，没有虚构 binary→Git attestation。

SDK 使用 list 时实际发送 `{argv:["python3","-c",<原cgroup代码>],cwd:"/tmp/morph-research",timeout:10000}`，
缺 command；后端所需的是 command 字符串。问题在版本间命令 wire 兼容，不能归为领域 guard。
官方 SDK 同时提供字符串入口，可兼容旧 execd；无需改 SDK、安装整个上游或更换镜像/锁。
官方源与许可证链接见 [upstream.md](upstream.md)。

## 最小修复与 HTTP 边界回归

源码修复 **`b4b403cd098df5cf2194e32377f7bd9f18a54ade`** 已 push：
仅 `orchestration/experiments/backend.py` 与 `tests/experiments/test_command_wire.py`。
前台/后台都调用标准库 `shlex.join(argv)`，逐参数按已知 Linux POSIX shell编码后交官方字符串API；
空格、单引号、空字符串、$HOME、$(id)、分号和换行保持literal，不用未转义的join。
保留官方 InvalidArgumentException 的空argv/空可执行文件/NUL/非字符串约束，
保持原owned检查、command ID、timeout、cwd、background、no-retry与未知语义；没有新runtime或调度层。
SDK、Poetry锁、service/config/image、科学plan/阈值均未变。

回归用安装的真实 SDK 1.1.0，经 httpx.MockTransport 捕获实际 HTTP method/path/JSON。
只模拟公开的旧execd required校验和SSE回应，不执行任何命令，因此属于 **contract_local / mock**。
原 exact cgroup argv 前台/后台各保留一个官方list→400对照；适配修复前的四个正向wire断言均失败。
参数保真、JSON只含command不含argv、10000ms/cwd/background、无重试与owned ID均验证。
不会把这份HTTP边界契约当成部署后端实际执行。

## 已运行结果与原失败保留

C 获主控明确释放后的独占Python窗口，Python3.12.13 / SDK1.1.0，进程BLAS/OMP threads=1。
日志在 `C:/Users/DW/AppData/Local/Temp/morph-sandbox-live-0930/`。

| 阶段 | 命令 | 实际结果 / 原日志 |
|---|---|---|
| 初次测试准备 | `python -m pytest tests/experiments/test_command_wire.py -q` | 8failed/2passed；其中4项是新增测试误期望ValueError而SDK本来抛InvalidArgumentException，原 `command-wire-before-fix.log` 留存 |
| 校正测试异常类型，仍未改源码 | 同上 | **4failed/6passed**，四项正向command均HTTP400；`command-wire-baseline-corrected.log`。后续这些断言未改 |
| 修复工作区快照 | `python -m pytest tests/experiments -q` | **40passed**，原静态判据、attached/no-retry等测试保留；`command-fix-experiments.log`，随后源码不再修改并冻结b4b403 |
| 固定b4b403 | `python -m pytest tests/experiments/test_command_wire.py -q` | **10passed**，`command-wire-b4b403c.log` |
| 固定b4b403 | `python tools/typecheck.py` | **97files，exit0**；`command-strict-b4b403c.log` |
| 固定b4b403 | `uv tool run --from poetry==2.3.2 poetry check --lock` | exit0；`command-lock-b4b403c.log`，未更改锁 |
| 固定b4b403 | `uv tool run --from poetry==2.3.2 poetry build --output <private-root>/dist-b4b403c` | sdist与wheel成功，exit0；`command-build-b4b403c.log` |

`command-gates-b4b403c.json` 记录冻结SHA与各退出码。没有重跑全仓pytest、改变旧断言或调用live。
后续文档提交只更新报告/矩阵；旧23417双平台CI成功不能当成本修复新SHA的全门禁通过。
Python窗口已交回I；I须固定新的集成SHA，取得新的唯一run决策后才可重新独立验收，不能重放原run。
