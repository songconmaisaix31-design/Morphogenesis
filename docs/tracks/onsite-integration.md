# I 现场阶段独立集成

## 范围与提交

Orca 新工作树 `C:/Users/DW/orca/workspaces/Morphogenesis/morph-onsite-integration`，分支 `songconmaisaix31-design/morph-onsite-integration`，从已推送主线 `9778356347cf2636baabc53d99b6d6632e66acd7` 建立。收到协调者精确交接后用 `git ls-remote` 核对两远端，再执行普通 `--no-ff` 合并，保留历史；没有 force push、重写历史或锁文件修改。

| 轨 | 已推送输入 SHA | 合并 SHA | 文件归属检查 |
|---|---|---|---|
| V | `1b2e335af52bd2e7de780d65fc14246a50bd2fd9` | `f609cfa0692d0323c423b63edf3a113cb388b8b6` | 仅 `demo/README.md`、`docs/tracks/onsite-viz.md` |
| O | `26a5cf1e417813244809807de44c44e917993713` | `e11367c4eb304807650353a6712853241271e528` | 仅 `tests/integration/**`、`docs/tracks/onsite-observer.md` |

I 自身仅维护本报告，暂未需要导入/配置胶水。V/O 域文件不由 I 代改。本轮新模型请求数为 **0**；未启动真实 demo、未操作回放服务生命周期。

## 锁环境与实际验证

Windows、Node `v24.16.0`、Python `3.12.13`，全新本工作树 `.venv` / `node_modules`。本地日志根 `.runtime/onsite-integration/`，已被 Git 忽略。安装命令：

```powershell
uv venv --python 3.12 .venv
$env:POETRY_VIRTUALENVS_IN_PROJECT='true'
uv tool run --offline poetry install --sync --no-interaction
npm ci --ignore-scripts --no-audit --no-fund
```

| 命令 | 实际结果 / 日志 |
|---|---|
| `node --test tests/integration/test_browser_options.cjs tests/integration/test_operator_enter.cjs tests/integration/test_observer_control.cjs` | **31 passed**，`node-tests.log`；含实际观察器 VM 流程、合成 TTY、默认自动 Enter、人工门禁失败收尾、凭据哨兵与未知转发不重试 |
| `.venv/Scripts/python.exe -B -m pytest -q --basetemp "$testTemp/pytest"` | 首次 **199 passed / 1 failed / 115.95s**，`pytest.log`；端口冲突返修见下节 |
| `.venv/Scripts/python.exe tools/typecheck.py` | **53 source files clean**，`strict.log` |
| `.venv/Scripts/python.exe -m build` | sdist / wheel 成功，`build.log` |
| `npm run check:sdk` | schema 1.14.0、asset ID、防篡改通过，`published=false`，`sdk.log` |
| `uv pip install --python .venv/Scripts/python.exe --no-deps --target .runtime/onsite-integration/wheel-site dist/morphogenesis-0.1.0-py3-none-any.whl` | 成功，`wheel-install.log` |
| `$env:NODE_PATH=Join-Path (Get-Location) node_modules; .venv/Scripts/python.exe -I tools/check_distribution.py --site-dir .runtime/onsite-integration/wheel-site --check-node` | **11 包从 wheel 加载**，资源、独立验证器、Node 桥通过，`wheel-check.log` |
| `uv tool run --offline poetry check --lock` | 通过，仅既有 Poetry 元数据弃用提示，`lock.log` |
| `Get-ChildItem tests/integration/*.cjs \| ForEach-Object { node --check $_.FullName }; node --check viz/static/app.js` | 全部语法通过，`syntax.log` |
| PowerShell `Parser.ParseFile` 检查 `demo/run-demo.ps1` | 无解析错误，`syntax.log` |
| `git diff --check` | 通过 |

首次 pytest 进程的 TEMP/TMP 均设为 `C:/Users/DW/AppData/Local/Temp/morph-onsite-i-tests-09e617b92c3a4e1bb7ddefa2edb11067`，使用该目录下 `pytest` 作为 basetemp；原始测试证据保留，不覆盖。

### 既有测试端口冲突

`tests/integration/test_demo_environment.py:20` 在 `probe.bind(('127.0.0.1', 7526))` 抛出 `OSError: [WinError 10048]`。该测试在 probe、fixture viewer、demo 参数和收尾 URL 硬编码 7526，与协调者常驻只读回放冲突；失败发生于模型/子进程启动之前。I 没有停止或重启 7526，也没有跳过该测试冒充全套通过。已通过 Orca escalation 退回拥有 `tests/integration/**` 的原 O Worker；等待其端口隔离修订的精确推送 SHA 后合并复验。

## 7526 只读回放与 7527 准备状态

2026-09-22 **08:58:10 UTC / 16:58:10 北京时间**，`Invoke-WebRequest http://127.0.0.1:7526/api/dashboard -TimeoutSec 10` 返回 HTTP 200、`provenance=replay`、`contract_local=passed`、`interface_live=not_run`、`task_live=not_run`、stage=`completed`。记录见 `replay-api.json`。`Get-NetTCPConnection -State Listen -LocalPort 7526,7527` 当时只返回 `127.0.0.1:7526` / PID 26576；**7527 没有监听**。这是当时的准备状态，不是端口预留或未来可用保证；不按本报告历史 PID 终止进程。

```powershell
$env:MORPH_PLAYWRIGHT='C:/Users/DW/AppData/Roaming/npm/node_modules/@playwright/cli/node_modules/playwright'
$env:MORPH_CHROMIUM='C:/Users/DW/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe'
node tests/integration/check_rehearsal_layout.cjs http://127.0.0.1:7526 .runtime/onsite-integration/replay
```

1366×768、1920×1080 均通过真实 ZRender 几何断言：3 标签 / 3 节点在画布内，互不遮挡、无横向溢出，Gene 区 bottom=696.359375 / 723.859375，均在首屏。主动查看了 `replay/replay-1366.png` 和 `replay/replay-1920.png`；两图明确标注 replay / 原始证据只读，小屏验收状态卡在首屏下缘，完整状态以 API 或滚动复核，不声称所有内容都在首屏。

浏览器检查前后对 API 指向的第四轮原始根逐文件比较字节和 mtime，**29 个文件不变**，见 `replay-readonly.json`。原始根为 `C:/Users/DW/AppData/Local/Temp/morph-live4-98b36399c0324192b5af81f8077bc11d/morph-rehearsal-86e5351d49fe49a1b60ba0a4bb4c4e4e`。未改写旧证据或创建新彩排任务；浏览器检查结束正常 close。回放归协调者管理，不保证跨后续进程生命周期存活。

## 交给现场的 7527 操作员入口（本轨未执行）

在本集成工作树根、普通交互 PowerShell/TTY 中运行；由协调者在专用进程环境注入凭据，不放入命令、文件、页面或日志。沿用上节 Playwright / Chromium 路径。先确认现场新一轮授权并仅执行一次；不可同时启动 V 文档中的直接 demo 命令和以下观察器命令，否则会形成两个入口。

```powershell
if (Get-NetTCPConnection -State Listen -LocalPort 7527 -ErrorAction SilentlyContinue) { throw '7527 已占用；停止，不处理未知进程。' }
if (-not $env:MORPH_EVOMAP_API_KEY) { throw '缺少协调者注入的专用凭据；停止。' }
$onsiteOutput=Join-Path $env:TEMP ('morph-onsite-operator-7527-'+[guid]::NewGuid().ToString('N'))
node tests/integration/observe_rehearsal.cjs manual 7527 $onsiteOutput --executor evomap --model evomap-gpt-5.6-luna --operator-enter --operator-timeout-seconds 120
```

该入口会产生真实模型请求，**不是验证命令**。必须保留 `--operator-enter`：省略它会沿用旧自动 Enter。非 TTY / 管道输入在启动 demo 前拒绝。仅在观察器提示“双视口与真实 awaiting_offline 已核对”后由操作员按一次 Enter；不预输入、不粘贴多行。等待默认最多 120 秒且受观察器总截止时间限制；超时、取消、EOF、阶段变化和未知转发结果均停止并保留证据，不重跑、不换模型、不创建第二轮替代失败。

现场展示 7527 使用实际投影屏浏览器；观察器的两个 headless 视口只产生软件证据，不能证明投影接线。`manual-enter.json` 的 `at` 是收到输入时间，`forwardedAt` 仅是一次管道写入回执；实际下线、第二 builder 运行、checkpoint 和 Gene 采用/衰减必须再审计新根。完成后从 `$onsiteOutput/summary.json` 读取 `root`，仅运行 `.venv/Scripts/python.exe -B tests/integration/audit_rehearsal.py <实际新根>`，不重新调用观察器。

## 真实限制与未执行操作

- 本次新付费真跑、真实人工 TTY Enter 流程及物理投影均 **NOT_RUN**；31 项测试使用本地合成边界，回放和 wheel 结果不能升级为 `interface_live` / `task_live`。
- 7527 仅检查无监听，没有启动或预留；现场执行前需再次检查。7526 未停止、重启或改配置。
- 观察器摘要可能早于 demo 退出，`exitCode=null` 不能表示成功结束；viewer 可保留继承管道，须由所有者核验本轮 launcher/listener 身份后处理，禁止广泛 kill 或未知效果重试。
- 固定成员在两任务间下线不证明在途进程强杀恢复。Hub 仍本地 stub / 待发布，动态 ORCA 供给、T4、OpenCode 工具调用/流式均未验证。
- 没有新增远端 CI 通过声明；远端精确候选状态须单列。网关费用仍未知，未读取或输出任何实际凭据。
