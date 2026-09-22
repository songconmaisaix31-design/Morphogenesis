# I 固定完整彩排集成验收

范围：普通合并 R `652e3199d626f60b414b70ee523b5f9703d1e539`、V `d032aba942464800842f43c2e2fcb20aacc8fca1`，以及协调治理 `61a2027`。起点 `501c491`，独立分支 `songconmaisaix31-design/morph-rehearsal-integration`。领域返修交原 V，I 只维护验收脚本和本报告。

## 环境与本地检查

使用本 worktree 的 `.venv`，Python 3.12.13，通过 `uv venv --python 3.12 .venv` 和 `POETRY_VIRTUALENVS_IN_PROJECT=true; uv tool run --offline poetry install --sync --no-interaction` 安装原锁；`npm ci` 安装原 npm 锁。未修改全局环境或锁文件。官方 Codex CLI 0.155.1，沿用既有账号；不读取、传递或测试本轮另给的 API key。

初次适用检查：

- `.venv/Scripts/python.exe -m pytest -q`：158 passed，91.70 秒。
- `.venv/Scripts/python.exe tools/typecheck.py`：52 文件，发现 `viz/adapter.py` 两处 redundant-cast，交 V 返修。
- `node --check viz/static/app.js`：通过。
- `npm run check:sdk`：schema 1.14.0 校验、asset ID、防篡改均通过，published=false。
- `.venv/Scripts/python.exe -m build`：sdist/wheel 成功。
- `uv pip install --python .venv/Scripts/python.exe --no-deps --target .runtime/integration/wheel-site dist/morphogenesis-0.1.0-py3-none-any.whl`；设置本目录 NODE_PATH 后运行 `tools/check_distribution.py --site-dir .runtime/integration/wheel-site --check-node`：11 包从 wheel 加载，资源、独立验证器、Node 桥通过。
- `uv tool run --offline poetry check --lock`：通过，仅原有元数据弃用提示。
- PowerShell Parser 检查 `demo/run-demo.ps1`：无解析错误。

日志均在本 worktree 的 `.runtime/integration/`，不入 Git。

## 付费前浏览器预检与返修

使用 R 既有 FixtureExecutor 生成明确 mock 的完整 `rehearsal.json`，未调用模型。Chromium 通过现有 Playwright 安装启动，没有安装新的浏览器。原始 `preflight-1366.png`/`preflight-1920.png` 为 fullPage，显示 105px 图表标签裁切、小屏 Gene 区越过首屏等问题；首屏是否容纳以 viewport 截图为准。

V `35b3836adbce5c18c327cbc4f3aeba2b6475879b` 修复长任务标题、Gene 短标签、首屏紧凑布局、网络失败陈旧绿态。复查 T5 11 passed；`empty-failure.json`/`waiting.png`/`fetch-failure.png` 验证未就绪与网络错误不保留通过状态。`2aa6c297015d9a23f411e571fb1dcc12afc0a710` 修复两处 redundant-cast，完整 strict 52 文件通过。`19c3a344b11afa9c5b94f6d838e32c5a3fe74b4f` 修复顶部标签边界，付费前主动查看两种 viewport 截图，确认核心 Gene 区首屏可读、无横向溢出。

第一、二轮 live 截图发现节点圆形底端稍被裁切，V `4593ad8ab5c65a9cde3a1039a10e78d9134ea34a` 调整边界与标签，第三轮使用该修正。第三轮完全展开的 28px 节点又暴露相向标签过近，继续交 V 最小返修。每轮 live 原始截图不覆盖、不替换；最后的显示修复必须以明确 replay 标识重渲染已有证据验证，不能声称三轮都运行于最终 UI SHA。

最终 V `80220c5481e64fa197a679a7ec2ea466b6306af6` 将管道图改为 160px、稳定无动画布局、底部标签，I 已普通合并。此前 `6fb1b7891859a23123f7f1d18818b1ba3337b011` 的顶部裁切仍失败，实际 ZRender builder#1 的 y=-6.38px，拒绝截图和几何日志留存为 `layout-rejected-6fb1b78/`，没有拿它充作通过证据。

最终运行 `node tests/integration/check_rehearsal_layout.cjs http://127.0.0.1:7525 .runtime/integration/layout-final`：1366×768 / 1920×1080 均通过。脚本读取真实 ZRender 绘制矩形与节点圆形，检查 3 个标签/3 个节点都在画布内、标签两两不交叠、文字矩形与节点圆形不相交；另核对横向无溢出、Gene ledger 在首屏。已主动查看 `layout-final/replay-1366.png`、`replay-1920.png`，数据和几何明细为 `geometry.json`。该新门禁也实际拒绝过已知坏候选，并非仅断言 DOM 或字符串。最终 UI 验证明确为只读 replay；所有 live 原始截图仍保留其实际版本。

Orca 内嵌 tab 创建成功，但对同一 browserPageId 执行 snapshot 返回 `runtime_unavailable: The Orca runtime closed the connection before responding`。原错误留 `.runtime/integration/orca-snapshot.json`；未重启 Orca 或杀 helper，改用用户批准的独立 headless Chromium。

## 三轮 live

三轮顺序执行均 completed；每轮使用 `demo/run-demo.ps1 -AuthorizeLive -Mode manual|auto -Port PORT -Model gpt-5.6-luna -TimeoutSeconds 180 -TauSeconds 10 -StageDelay 2` 调用 R 官方入口；manual、auto、auto 顺序，总计六次新 CLI 调用、六个 turn，无 UNKNOWN、失败或重试。`tests/integration/observe_rehearsal.cjs` 是一次现场入口加两个只读浏览器的验收观察脚本，`audit_rehearsal.py` 只读审计留存事实，不生成或调度任务。

浏览器脚本使用环境 `MORPH_PLAYWRIGHT=C:/Users/DW/AppData/Roaming/npm/node_modules/@playwright/cli/node_modules/playwright`、`MORPH_CHROMIUM=C:/Users/DW/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe`；运行 `node tests/integration/observe_rehearsal.cjs manual|auto PORT .runtime/integration/live-N`。输出目录已存在则拒绝覆盖。Chromium 151.0.7922.34，两页同时真实 HTTP 轮询相同的新 rehearsal.json，覆盖每轮 #0—#19 全部快照。

证据根均在 `C:/Users/DW/AppData/Local/Temp/`：

| 轮 | 模式 | 独立根目录名 | runtime 首/末 UTC | 结束 |
|---|---|---|---|---|
| 1 | manual | `morph-rehearsal-478415a14d4345ae87edf564c10a17aa` | 05:23:40.716862 / 05:25:30.556849 | completed |
| 2 | auto | `morph-rehearsal-f1ef4bbac84247b9919a4e7a927b6112` | 05:26:04.219718 / 05:27:39.966394 | completed |
| 3 | auto | `morph-rehearsal-8a253c1f138c4d79b18dffc5bb888350` | 05:28:24.145570 / 05:29:51.460674 | completed |

时间日期均 2026-09-22；完整 viewer/进程启动和结束时刻另见每轮 `summary.json`。第一轮在 `05:24:28.934Z` 真正写入 stdin Enter，记录于 `live-1/manual-enter.json`；不杀任何在途模型进程。

| 轮 / 新任务 | 实际 CLI call / turn | input tokens | output tokens | 合计 tokens | cost_usd |
|---|---|---|---|---|---|
| 1 repair | 1 / 1 | 14056 | 288 | 14344 | null |
| 1 recovery | 1 / 1 | 14418 | 314 | 14732 | null |
| 2 repair | 1 / 1 | 14062 | 267 | 14329 | null |
| 2 recovery | 1 / 1 | 14411 | 274 | 14685 | null |
| 3 repair | 1 / 1 | 14062 | 264 | 14326 | null |
| 3 recovery | 1 / 1 | 14410 | 307 | 14717 | null |
| 总计 | 6 / 6 | 85419 | 1714 | 87133 | null |

六条 turn.completed 均有 usage，cached_input_tokens/cache_write_input_tokens 均为 0。reasoning_output_tokens 分别 86、81、80、51、74、62，已包含在 output_tokens，不重复累加。所有命令的 model 参数实际为 gpt-5.6-luna。

每轮审计命令：`.venv/Scripts/python.exe tests/integration/audit_rehearsal.py <上述根>`，输出至 `live-N/audit.json`。实际核对两次独立外部 `python -I -S acceptance_runner.py` 的前后四份 checkpoint 报告：坏样例 clamp/mean/unique 均 false，修复后三者均 true；实际 TaskResult 分别属于 builder#0、builder#1，后者为新的 TaskId。核对获胜成员不可用、对应管道 inactive、实际 ECharts links 权重 1→1.9、线宽 5→8.6、离线虚线、第二条管道反馈 0.9→1.81。每轮准确一条采用记录，first Gene 的 source_attempt=首次真实调用、use_count=1、injected_count=1、采用 Attempt=第二次真实调用。

逐点用已有 GeneView 的时间验证 `exp(-(evaluated_at-anchor)/10)`，不是快进时钟；归档时间距创建/最后采用至少 `10*ln(5)` 秒。归档后两条 Gene 均低于 0.2，snapshot 的实际 resolve 列表为空；额外 SQLite immutable 只读查询确认正文表为空，没有读写原数据库。

原始 CLI `command.json`、`codex.jsonl`、proposal、stdout/stderr 和外部评审报告留在各 TEMP 根的 repair/recovery 子目录，未入 Git。每轮 `.runtime/integration/live-N/{1366,1920}.json` 保存页面状态、真实 ECharts option、HTTP 回执；`{1366,1920}-0.png` 至 `-19.png` 是 viewport 实图，涵盖初始、反馈、生成、下线、重新选路、采用、衰减、归档、完成。已主动打开关键图片检查，不仅断言文字。

回放现场入口 `demo/run-demo.ps1 -Replay <第一轮/rehearsal.json> -Port 7525` 正常就绪，页面 provenance=replay、原始证据只读，interface_live/task_live=not_run。`replay_immutable.py` 在 CLI `--replay` 和真实浏览器回放前后比较 35 个原始文件的字节与 mtime，全部不变，见 `replay-immutable.json`。回放不计入本轮三次 live。

最终接受版本的静态资源变更后，重新执行 `python -m build` 和安装 wheel 后 `check_distribution.py --check-node`，结果见 `build-accepted.log`、`wheel-accepted-check.log`：sdist/wheel 和 11 包/资源/固定外部验证器/Node 桥通过。上述 pytest 158 项与 strict 52 文件通过属于当时的本地检查结果，不代表后续远端 CI 全绿；已知 Windows CI 时间竞态见下节。后续领域变更仅 UI JS/CSS，执行过 Node 语法和真实浏览器几何检查，未重复付费任务。没有改 Python/npm 锁或全局配置。

## 后续 CI 时间竞态

协调者交接指出：候选 `e83a816` 的 [CI 35691719303](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/35691719303) 在 Windows 上为 157 passed、1 failed，失败位于 `tests/t2/test_rehearsal.py:81` 的 `weight > 0.5` 断言。fixture 的 `tau_seconds=0.1`，该断言隐含从采用到快照必须少于 `0.1*ln(2)` 秒（约 69ms）；已记录的实际间隔约 0.103 秒、权重约 0.3563，与产品真实墙钟衰减一致，不能据此改产品时钟或扩大运行时修复范围。

原 R Worker 负责该测试及 R 报告的限定返修；早先暂停阶段仅保留报告草稿，未集成。新的网关任务获授权后，I 以 `882ac25` 保存纠正，并普通合并 R `94b70816784fcd46ce4f74b8e205bd009b789cc3` 及主线 `f774e18`。R 按实际采用时间锚点验证衰减，另覆盖真实延迟 0.2 秒的快照；本候选全套 pytest 的 200 项已通过，未改产品墙钟或旧三轮证据。R 精确提交的双平台 [CI 35701298167](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/35701298167) 由协调者交接为通过；I 最终候选 CI 单独核对。

## 服务清理与只读演示交接

已按 Win32_Process 的父子 PID、命令行和专用端口核验并清理自有 viewer：7520（70272→61464）、7521（53424→24048）、7522（42044→49704）、7523（14960→58732）、7524（54128→48820）。证据 `.runtime/integration/cleanup.json`；上述端口不再监听。各次 Playwright 浏览器正常 close，临时 Orca 页面 `0d89fe97-b8b9-4524-be08-3845bb1aca87` 已确认所属本 worktree 后关闭；未触碰 Orca helper/运行时或队友进程。

**交接纠正：此前关于 7525 服务可跨 Worker 释放继续存活的结论错误。** 旧服务在原 I 的 `worker-release` 后退出；PowerShell 46168 → Python launcher 61712 → 监听 Python 70764 均为失效的历史身份，不得再据此执行关闭操作。`.runtime/integration/replay-processes.json`、`replay.stdout.log` 和 `replay.stderr.log` 仅保留为当时启动和验证的历史记录，不能证明跨释放存活。

根据协调者本次交接，root 已在协调者进程树下重建 [第一轮只读回放页面](http://127.0.0.1:7525/)，新身份为 launcher **65808** → listener **57100**。协调者已验证 HTTP 200、provenance=`replay`、task_live=`not_run`；这是协调者交接的验证结果，本次限定报告修订未重新探测或操作该服务，也不据此保证它跨未来生命周期继续存活。

重建服务的日志为 `C:/Users/DW/AppData/Local/Temp/morph-replay-coordinator-983d9f27fa08480a9c1836c25c9dbb64/stdout.log` 和同目录 `stderr.log`。其读取的第一轮原始证据仍为 `C:/Users/DW/AppData/Local/Temp/morph-rehearsal-478415a14d4345ae87edf564c10a17aa/rehearsal.json`，协调者交接确认原始证据不变；回放不计为新的 live 或模型调用。

该重建服务归 root 协调者管理，I 不负责启动、停止或更改。此前验证过的 `demo/run-demo.ps1 -Replay <第一轮/rehearsal.json> -Port 7525` 是回放入口，不是跨 Worker 释放存活的保证；后续服务处置由协调者重新核验实时端口、父子身份和命令行后执行，不使用本报告的历史 PID 直接停止进程。所有 TEMP 原证据、截图、锁环境和分支均保留。

## 真实限制

固定逻辑成员在两任务之间下线，不证明在途 CLI 被杀后恢复；Hub 待发布，无外部 Hub 写入；运行时供给为固定成员池；真实投影接线 NOT_RUN。CLI 不提供调用中美元硬上限，cost=null 保持未知。静态、fixture、package 证据均不替代三轮 task_live。

## 第四轮网关：付费前集成与验收入口

本轮采用 EvoMap Chat Completions，独立于上述三轮 Codex CLI；I 实际模型请求预算为 **0**。协调者审阅以下入口后，才在子进程环境注入 `MORPH_EVOMAP_API_KEY`，手动模式最多两个新 POST；失败/UNKNOWN 不自动重试，不换根重做。独立短文本 smoke 也不计入本轮。入口提交 `7c0bb6a2f7b39a7eb524c0c71bc31c7a110f883c` 先完成下述本地门禁；随后协调者运行唯一第四轮，结果见下一节。

观察器沿用原三个位置参数，新增 `--executor codex|evomap` / `--model`，旧 CLI 默认不变。实际 runtime 到达 `awaiting_offline` 且两个页面均显示等待时，经 stdin 发送一次 Enter；没有强杀在途进程。每个历史 sequence 必须出现在两个浏览器的现场记录中，实际 ZRender 边界在逐阶段截图时检查。网关审计读取实际 request/response/proposal，核对 HTTP 200、请求模型、provider 返回模型原文、usage 与 result、任务/Agent 身份、应用正文与完整 Gene 注入/采用；不生成 CLI 事件或把 request 意图单独算成功。

密钥仅转交 demo 子进程；观察器在加载 Playwright 前从自身环境移除该变量，Chromium 启动再次显式排除；demo 的 viewer 使用 PowerShell 7.4+ `Start-Process -Environment` 的空值删除，Mock/Replay 入口也删除，执行器保留专用环境。没有持久 `.env`、header/env/key 输出或含密钥命令行。Windows 真实 PowerShell 启动测试用本地 fixture 模块和非秘密 sentinel，证明 viewer 不含变量、执行器含变量且参数正确；没有外网或真实请求。首次该测试的 finally 清理连接遇到已按 25 秒期限退出的 fixture 服务，核心断言此前已通过；仅修正测试清理，不改领域逻辑，后续全套通过。

本地结果及不入 Git 的日志：

- `.venv/Scripts/python.exe -B -m pytest -q --basetemp <唯一私有目录>`：**200 passed / 135.27s**；进程 TEMP/TMP 限于本轨，日志 `.runtime/integration/verify-gateway-cc8fb864855f4d27b9d67fef26fd47b5/pytest.log`。
- `tools/typecheck.py`：**53 source files clean**；全部 integration JS `node --check`、PowerShell Parser、`npm run check:sdk`、`python -m build`、独立目标安装 wheel 后 `python -I tools/check_distribution.py --site-dir ... --check-node` 均通过。包日志 `.runtime/integration/package-gateway-d81ec2c43afa42219ae894330246aaa8/`，11 个包来自 wheel，published=false。
- `node --test tests/integration/test_browser_options.cjs`：2 passed，包括实际无 sentinel 子进程；pytest 新增 7 个 gateway 收据审计与 1 个 Windows demo 环境集成测试。坏证据覆盖缺/错 usage、缺返回模型、错 Attempt、错 Gene 正文及不同应用文件。
- `check_rehearsal_stages.cjs` 读取旧 **mock** fixture 的只读原件，以全新 TEMP 副本逐阶段展示：19 snapshots × 双视口 = **38 张截图**，真实几何检查通过；全程 task_live=not_run。截图/几何 `.runtime/integration/preflight-gateway-aa82b2ca751b45499d94cb462f1d9133/`；主动查看了 1366 初始/采用、1920 下线/完成实图。临时根 `C:/Users/DW/AppData/Local/Temp/morph-i-gateway-stages-1dcace8868a04d9c8f91eecbd506c5b1`；原 mock 字节/mtime 未改，自有 7526 viewer 经父子 PID 与命令行核验后已清理。7525 root 服务未操作。

协调者执行命令（本工作树；预先通过专用进程环境注入凭据，命令中不含凭据；目录必须尚不存在）：

```powershell
$env:MORPH_PLAYWRIGHT = 'C:/Users/DW/AppData/Roaming/npm/node_modules/@playwright/cli/node_modules/playwright'
$env:MORPH_CHROMIUM = 'C:/Users/DW/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe'
node tests/integration/observe_rehearsal.cjs manual 7526 .runtime/integration/live-4-gateway-20260922-01 --executor evomap --model evomap-gpt-5.6-luna
# 完成后由 I 读取 summary.json.root，对该新根执行 audit_rehearsal.py；不得重跑 live。
```

demo 在启动前拒绝占用的 7526，自行生成全新 OS TEMP 根，打印当前 launcher/listener PID 与 stdout/stderr 路径。不承诺 viewer 跨 worker-release 存活。网关 cost 仍为 null，httpx phase timeout 不是绝对在途截止；物理投影与远端 Hub 未验证。

## 第四轮网关：真实结果与只读交接

协调者在精确入口 `7c0bb6a2f7b39a7eb524c0c71bc31c7a110f883c` 上运行一次 manual 彩排。观察器 UTC **2026-09-22 08:12:23.186–08:13:36.586**，实际 rehearsal 快照 **08:12:31.186430–08:13:35.489003**；最终 stage=`completed`、task_live=`passed`、exitCode=0、failure=null。`manual-enter.json` 记录 **08:12:52.836Z** 在真实 `awaiting_offline` 时通过 stdin Enter，随后 builder#0 的逻辑可用性下线，builder#1 执行新任务；没有在途进程强杀。

全新原始根为 `C:/Users/DW/AppData/Local/Temp/morph-live4-98b36399c0324192b5af81f8077bc11d/morph-rehearsal-86e5351d49fe49a1b60ba0a4bb4c4e4e`。每任务保留 `gateway/request.json`、`response.json`、`proposal.json` 与 config/result/独立验证/事件；没有 CLI 调用或伪造 CLI turn。两次请求模型均为 **evomap-gpt-5.6-luna**，provider 响应模型原文均为 **gpt-5.6-luna**：

| 新任务 / 实际 Agent | 请求开始–响应结束 UTC | HTTP / 请求数 | prompt / completion / total tokens | HTTP 实测耗时 |
|---|---|---|---|---|
| repair / builder#0 | 08:12:35.255422–08:12:43.344883 | 200 / 1 | 544 / 343 / **887** | 8.078 秒 |
| recovery / builder#1 | 08:12:59.423884–08:13:09.767748 | 200 / 1 | 905 / 443 / **1348** | 10.343 秒 |

合计 **2 POST / 2235 tokens / 0 CLI calls**；I 自行发送 **0**。usage 与两份实际 TaskResult 完全相符，cost_usd 全部保持 null。此后没有 retry、额外任务或模型探测；旧三轮仍单列为 6 CLI calls / 87133 tokens，不与本轮混称。

I 执行 `python -B tests/integration/audit_rehearsal.py <上述新根>`，结果保存 `.runtime/integration/live-4-gateway-20260922-01/audit.json`：

- 四份真实独立 `python -I -S acceptance_runner.py` 报告依次为失败/成功/失败/成功；两个全新样例各自 **0/3→3/3**，任务身份不同。
- 请求、选路、结果与实际 Agent 身份对应，第二次 eligible 仅 builder#1；第一条边 inactive，ECharts 权重 **1.00→1.90**，反馈线宽 8.6，下线后为虚线。
- 第一 Gene 的 source_attempt 对应 repair；第二份请求中的完整 experience 正文与 `repair/gene.json` 相等，含第一份真实 proposal 修复正文。第二 proposal 声明采用该 ID，adoption 记录对应第二次实际 Attempt，use_count=1、injected_count=1；没有只凭页面“成功”认定采用。
- **21 个**非归档 GeneView 按真实 `exp(-(evaluated_at-anchor)/10)` 核验，τ=10 秒；两条 Gene 均在距真实锚点至少 `10*ln(5)` 秒后归档，权重低于 0.2，实际 resolve 列表为空，SQLite immutable 查询正文缓存为 0。
- 只读审计和 replay 转换前后 **29 个原始文件 bytes+mtime 完全不变**。

现场图像目录 `.runtime/integration/live-4-gateway-20260922-01/` 含 **20 个实际 sequence × 2 尺寸 = 40 张 live 阶段图**，另各一张 waiting 图；`1366.json`、`1920.json` 保存对应 ECharts、页面、几何和 HTTP 记录，两个页面均无 browser error，所有实际阶段均已观察。真实 ZRender 的 3 个节点/标签无裁切、标签相互及与节点不遮挡，无横向溢出；最终 Gene ledger bottom 分别为 696.36/723.86px，均在首屏。已主动查看初始、修复反馈、Gene 生成、等待 Enter、下线、第二 builder 选中、采用、衰减、归档、完成关键实图；小屏关键图为 `1366-{0,4,5,10,18}.png`，大屏为 `1920-{3,6,8,15,19}.png`。

本轮常驻 live viewer 使 Node 的继承管道在生成 summary 后尚未自然结束。协调者核验并仅停止本次 live launcher **46756** / listener **41428** 后，观察父进程正常 exit 0；这是生命周期清理，不是彩排中的下线注入，也没有新调用。该限制如实保留，没有为结项修改领域或验收代码。

协调者随后独立重建 [第四轮只读回放](http://127.0.0.1:7526/)：交接时 launcher **47180** → listener **26576**，日志目录 `C:/Users/DW/AppData/Local/Temp/morph-replay4-coordinator-5790d05a35a0492699a4b8c356093bfd`，身份记录 `live-4-gateway-20260922-01/replay-processes.json`。I 未操作此服务，只运行 `check_rehearsal_layout.cjs` 做 HTTP 只读复查；双视口截图为同目录 `replay/replay-{1366,1920}.png`，已目视 provenance=replay、原始证据只读，interface_live/task_live=not_run。该浏览器检查前后再次确认 29 个原文件 bytes+mtime 不变，见 `replay-immutable.json`。服务归 root 管理，不保证跨未来 release 存活；7525 旧回放未操作。

精确源码入口的 [CI 35703445239](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/35703445239) 已由 I 使用 `gh run view` 核验：`headSha=7c0bb6a2f7b39a7eb524c0c71bc31c7a110f883c`，Ubuntu 与 Windows 两 job 均 success，pytest/strict/build/SDK/独立 wheel 步骤全通过。后续提交仅补本轨结果报告；根协调者已读取 audit 并明确接受，负责主线治理记录与最终推送。上述物理投影、远端 Hub、在途强杀、OpenCode 工具调用/流式仍不属于本轮已验证范围。

## OpenCode 项目级备选模型

新增显式选用的 `opencode.evomap.json`，复用已安装 **opencode-ai 1.18.31 / MIT**、官方 [`@ai-sdk/openai-compatible` provider](https://opencode.ai/docs/providers/#custom-provider) 和 [环境变量引用](https://opencode.ai/docs/config/#env-vars)。固定 baseURL 为 `https://api.evomap.ai/v1`，apiKey 仅 `{env:MORPH_EVOMAP_API_KEY}`；无默认 model，不影响未选此配置的项目，分享 disabled、自动更新关闭、操作默认 ask、外部目录及 `.env` 读取 deny。七个文本 ID 与主线目录一致；三个图片模型未纳入代码池。

`check_opencode_config.py --executable C:/Users/DW/AppData/Roaming/npm/node_modules/opencode-ai/bin/opencode.exe` 在独立临时 cwd/XDG 目录、白名单进程环境、仅 sentinel 下先核验 `debug paths`，再执行 `models evomap`：**配置解析和七项枚举通过**。版本 1.18.31，日志位于上述 verify 目录的 `opencode.log` 及 `morph-opencode-config-3oc70v7m/`；禁用远端目录获取、默认插件、升级与 LSP 下载，未读写全局账号配置、没有七模型付费探测。未打印解析后的 key。

后续由协调者在已绑定 owner/worktree/branch/write_paths 的专用 Orca 终端中启动；每工作树单独配置与本地状态，保留现有 R/I 会话模型。本轮仅交命令，不实际启动新开发 Worker：

```powershell
$taskState = Join-Path (Get-Location).Path '.runtime/opencode'
$env:XDG_CONFIG_HOME = Join-Path $taskState 'config'
$env:XDG_DATA_HOME = Join-Path $taskState 'data'
$env:XDG_CACHE_HOME = Join-Path $taskState 'cache'
$env:XDG_STATE_HOME = Join-Path $taskState 'state'
$env:OPENCODE_CONFIG = Join-Path (Get-Location).Path 'opencode.evomap.json'
# 凭据由授权方仅注入此进程；不用 auth login 或全局配置。
opencode --model evomap/evomap-gpt-5.6-luna
```

初始分配建议沿主线：小改动/测试/文档用 Luna 或 DeepSeek V4 Flash；常规模块用 Terra、GLM 5.1/5.2；复杂契约/跨模块审查用 Sol 或 Gemini 3.1 Pro Preview。这是待实测的初始选择，不是性能/价格排名；仍须明确每轨 owner、独立分支和互斥 write_paths。**OpenCode 工具调用、流式兼容和七模型端到端开发均 NOT_RUN**；第四轮 Chat Completions 即使通过，也不能算该工具链验收。
