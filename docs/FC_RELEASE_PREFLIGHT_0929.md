# FC 发布、入口与演练预检 · 2026-09-29

本轮仅完成预检材料。**发布/合并/tag/三连冒烟/T10/业务 live 均 NOT_RUN；H1/H3 unsigned；FC 未冻结。** E 不执行模型评审；主控所述 `dsh deepseekV4.1flash` 新正式评审由 G 负责，不能用旧 deepseek-r1 拒收报告或本预检补锁。

本次为 `c1107b63911e44269b586a1252cb84836cdeacf3` 之后的同轨材料窄返修（task `task_4e9a57e7c2aa` / dispatch `ctx_2f4b8aeec806`），仅写本文件与 `artifacts/ai-evidence/fc-release-preflight-0929-validation.json`。下述原预检身份、盘点、门禁与失败均保留为历史快照；本次仅补 T10 Handoff 和授权边界，不重新预检、实现、测试或执行演练。G dsh 正式 review 仍缺凭据，H1/H3 pending；原 TLS 失败不改绿。

## 1. 任务与证据身份

- E worktree：`C:/Users/DW/orca/workspaces/Morphogenesis/morph-fc-release-preflight-0929`；同名分支；开工 HEAD 精确为 `c552250c0d07f5f70f09eb0a5ab3c322195e34ec`（C552），clean。
- 沿用 Orca `run_e46ee274f7c9`、task `task_1604c23cec02`、dispatch `ctx_31ff682fa709`；已核对终端 worktree/branch 身份，没有新增 Run、终端或预览。
- 写权仅本文件、`artifacts/ai-evidence/fc-release-preflight-0929*`、ignored `.runtime/fc-release-preflight-0929/`。未改业务/测试/Schema/签名/源 TODO/AGENTS/SWARM/锁、TASKS 或桌面材料，未安装依赖。
- 已读 AGENTS、QWEN、source README、PLAN、TASKS、FC_ACCEPTANCE、0928/0929 计划、demo README/入口及原治理树人工包和最新附录。旧 `docs/FC_ACCEPTANCE.md:5` 的 698 是历史门禁，不能当作 C552 门禁。
- G 读取快照：`morph-fc-governance-final-0929@403909204c8b589d33943298e1cde0a2094bb15e`。该树 `docs/FC_HUMAN_REVIEW_0929.md:40,66,85` 的预算结论、breaker 签字、H3 槽仍待人工；`:69–79` 的 r1 报告 REJECTED 是历史有效记录。新 flash 报告尚未在本快照中，交付前由主控核 G 最终 immutable SHA/判定。
- 稍后复查 G 树已出现未提交 `docs/FC_RELEASE_PLAN_0929.md` 和 `review-0929-v41flash-*` WIP，全部保留。其计划第15行陈述官方 Flash 路由凭据缺失、尚未发送；这是 **G 正在形成的材料**，E 没有独立验证该凭据通道或执行模型调用，不能提前当作正式最终回执。
- 本报告代码行号均绑定 C552；G 文件行号绑定上述 4039092。已有 I 六门禁（408 focused、862 full/2 warnings、strict 87、build/SDK/分发 exit 0）及 D 47/九组 mutation 引用 G 原字节 I/D 报告；**E 未重跑这些门禁，也未宣称独立复验它们**。

## 2. 真正发布目标、delta 与标签

2026-09-29 约 20:20–20:30 +08:00 的只读快照；原始命令/exit 见 [Git 证据](../artifacts/ai-evidence/fc-release-preflight-0929-git.json)。

| 引用 | 本地 SHA = `git ls-remote origin` SHA | 工作树/状态 |
|---|---|---|
| **decentralized-swarm（FC 目标）** | `73798cd6f05210f2bd9b1eebfd6f9f0dd6e842db` | `C:/Users/DW/orca/workspaces/Morphogenesis/decentralized-swarm`，clean |
| morph-fc-candidate-0929 | `c552250c0d07f5f70f09eb0a5ab3c322195e34ec` | 同名 worktree，代码候选 |
| morph-fc-governance-final-0929 | `403909204c8b589d33943298e1cde0a2094bb15e` | 同名 worktree，读取时 clean；G 正接续 |
| codex/morphogenesis-mainline（第一代） | `2957b408ce922369a595a8acd43a882eb85897d3` | `C:/Users/DW/orca/Morphogenesis`，既有 ` M docs/SWARM_SOL_PLAN.md` WIP，原样保留 |

`QWEN.md:10–12` 指定 decentralized-swarm 基地、第一代只读；`docs/FC_DAY_PLAN_0928.md:90` 指定三锁不齐不合回 decentralized-swarm。C552 包含目标：`merge-base --is-ancestor 73798… C552` exit 0；`rev-list --left-right --count decentralized-swarm...C552` = **0 / 44**；delta **69 files、8649 insertions、82 deletions**，不是只有今日五项修复，含此前 FC 集成/Schema/材料。第一代只读应用 `621f588…` 仍独立，不纳入本次 FC 发布计划。

本地 `refs/tags/demo-build*`、远端 `refs/tags/demo-build*` 均无条目，查询 exit 0，故当前**没有可报告的 tag 指向**。历史“demo-build.1 后续 bump”不等于已有 tag。将来创建前必须再次查询同名和 peeled ref；一旦已存在，记录 object/commit 并停止创建，绝不 `-f`、删除或覆盖。

只读旧式三树 `git merge-tree`（不使用 `--write-tree`）：

```powershell
git merge-tree 73798cd6f05210f2bd9b1eebfd6f9f0dd6e842db 73798cd6f05210f2bd9b1eebfd6f9f0dd6e842db c552250c0d07f5f70f09eb0a5ab3c322195e34ec
git merge-tree e6ac45ffefc171a7215f8db19bc4a28af24ec4fc c552250c0d07f5f70f09eb0a5ab3c322195e34ec 403909204c8b589d33943298e1cde0a2094bb15e
```

两条 exit 0；原输出 9242 / 2693 行，冲突标记 0。原输出保存在本轨 ignored runtime；这只是当前树的文本预演，不是实际合并/最终运行验收。G 当前相对 C 单轨只改四治理文档及证据；正式 flash 后最终 SHA 仍要重查。领域冲突交回原 Owner；治理冲突交 G；不在 E 修复。

## 3. 锁齐后的合并/tag执行顺序（本轮未执行）

1. G 交付指定 flash 正式报告、可接受性判定及精确远端 SHA；人类完成 H1 预算 A/B 前提、breaker 六点、签名/时间/候选 SHA；人类完成 H3 Schema SHA/版本/准入范围。普通“继续”不填这些槽。既有 T6 条件授权见 `docs/FC_DAY_PLAN_0928.md:38–41`，条件满足后无需另加泛化 merge/tag 审批。
2. 集成 Agent 以 **C552** 建最终材料候选，串行普通合入 G 最终治理/签字、必要 D/E 报告；确认 `git diff --name-status C552 <release-sha>`。G 文档父基为 C 单轨，必须从共同候选合入，不能把 G HEAD 当成已含 A+B 的完整代码候选。
3. 明确证据身份：若仅文档/证据新增，C552 六门禁只能登记为“C552 实跑，release SHA 复用源码等同性证据”；逐 Git blob 核产品/测试/Schema/锁和构建输入是否不变。若签字 comment 写入源码，源码 blob 已变，不能说全源码相同。必须由原 Owner 完成授权 comment，再由集成 Agent按实际 diff确定适用检查；要声明“最终 SHA 六门禁通过”，就须在最终 SHA 实跑对应门禁。README 等被打入 wheel 的材料变更也改变分发内容，需要最终分发验证；不能将旧 C552 wheel/log 标为新 SHA 产物。本轮不重复已有代码门禁。
4. 冻结最终 release SHA 后重读 H1/FC-E 与该源码的对应关系，远端/dirty/tag 状态，保留历史失败。文档变更不自动使旧引用失效，也不自动赋予新 SHA 实跑证据；任何实质行为变更返原 Owner/验收。
5. 主控指定集成 Agent 在目标原工作树检查 clean、远端仍符合预期后：`git -C <目标树> merge --ff-only <完整release-sha>`，随后普通 `git -C <目标树> push origin HEAD:refs/heads/decentralized-swarm`。目标已漂移时先读差异和 merge-tree；不得 reset/覆盖 WIP。若确需 no-ff，先在隔离集成树完成它并把新 merge SHA 纳入上一步证据范围，目标只接纳该完成验收的 SHA。
6. 执行下面的适用三轮 smoke/入口验收；每轮核真 usage 与结果，失败/未知效果停止，不自动重试或把 mock/replay 补成 live。建议三轮成功后才创建 `git tag -a demo-build <完整release-sha> -m 'FC demo build; exact acceptance recorded'`，普通 `git push origin refs/tags/demo-build`；若既定现场次序先 tag 再 smoke，失败也保留 tag 原指向并报告失败，不移动补绿。最后 `git ls-remote origin refs/heads/decentralized-swarm refs/tags/demo-build 'refs/tags/demo-build^{}'` 核远端，记录 tag object 和 peeled commit。

以上 `<完整release-sha>` 由实际集成产生，当前尚不存在，不能提前虚构。H3 是 Schema/采集冻结的独立条件，不把其合入“AI 可代签”的技术锁。

## 4. 入口边界与当前环境

`demo/run-demo.ps1:1–16` 没有 `-Workspace` 或 `-RunRoot` 参数；`:18–22` 强制使用脚本所在树 `.venv/Scripts/python.exe`，默认模型按 executor 选择 Luna。`:45–60` 的 Mock/Replay 只展示；`:63–68,100` 的 live 每轮创建 TEMP 随机目录并明确授权 repair/recovery 两个新任务。

`orchestration/rehearsal.py:127–133,265–268,311–340` 使用全新 OS TEMP 样例 workspace、`sample.py` 写白名单、`max_retries=0`，人工下线发生在两任务之间；这是现有 LangGraph 固定样例演示。**不是正在执行的 FC Worker 候选链故障演练，也没有任意课题 workspace 接入口。** `swarm/cli.py:403–418` 的 demo/worker 使用 fixture；真实数据任务入口是 `swarm.cli evomap --config <明确配置>`（`:419–435`），也不能把它当任意课题入口。DashScope adapter 的存在不等于完整生产 executor。

当前快照见 [环境](../artifacts/ai-evidence/fc-release-preflight-0929-environment.json) / [宿主](../artifacts/ai-evidence/fc-release-preflight-0929-host.json)：

| 检查 | 实际结果 / 限制 |
|---|---|
| E 预检树、C552 候选树 | `.venv`、node_modules、SDK、ECharts 缺；已有跟踪 bundle；不能直接运行入口。没有安装或借环境伪装本树已就绪 |
| decentralized-swarm、第一代原树 | `.venv`、node_modules、SDK、ECharts、bundle 存在；仅在目标树原 `.venv` 做只读 help/回放解析。第一代未运行 |
| CLI / 系统 | PowerShell 7.6.6，git/node/codex/dsh/uv 可定位；PATH poetry 不存在；不由此推断 `uv tool` 后端不可用或自动安装。C 盘快照约 46.5 GiB 可用 |
| 凭据/配置存在性 | 本进程 `MORPH_EVOMAP_API_KEY`、DASHSCOPE_API_KEY、OPENAI_API_KEY、DSH_HOME、CODEX_HOME 未设置；默认 Codex config/auth 文件存在，阿里云 config 文件存在；**未读取/输出凭据值或验证登录/云端可用性** |
| live 模型选择 | 原准备项 `evomap-gpt-5.6-sol`（TASKS:277），只是候选。网关需要本进程 MORPH_EVOMAP_API_KEY（gateway.py:120–122）；swarm executor 另需外置 credential_file（evomap_executor.py:49–55,279–289），两入口不能混用凭据传递方式 |
| 课题 | TASKS:274、G 人工包:94 仍无可核验课题绝对路径/身份/验收目标。不能擅自把样例修复当课题执行 |
| 端口/进程 | 7526、7527、7844、拟定 7861/7862/7863 当时均无 LISTEN；不等于将来保留。进程搜索匹配的 PID 73716 是核查 PowerShell 自身，已在证据纠正，未当成服务；未启动/停止任何他人进程 |
| 现场 | 浏览器、实际投影/选屏/100%缩放、1366×768/1920×1080 现场显示均 NOT_RUN；参照 demo/README.md:37–39，历史 7526/7527 不能凭旧记录声称在线 |

`-MaxCostUsd` 是本地参数，不是上游账单硬上限：`orchestration/rehearsal.py:390–392` 明说无 hard in-flight cap；`:301–305` 在 token 已知时允许第二个独立授权任务且 cost 可为 null。当前脚本无跨三轮累计成本准入器。若实际 live 约束要求已知费用才继续，本入口当前不满足，交原 Owner/主控处理，不能临场忽略或自建预算系统。

## 5. 已存在的回放证据

TEMP 的 `morph*` 一级目录找到 **11** 份 `rehearsal.json`；全部 JSON 解析通过，目标树 `.venv` 下 `read_rehearsal(path, replay=True)` **11/11、exit 0**，结果一律 `provenance=replay`、`interface_live=not_run`、`task_live=not_run`，并保留 original_run_uri。见 [源文件摘要](../artifacts/ai-evidence/fc-release-preflight-0929-replays.json) 和 [回放类型校验](../artifacts/ai-evidence/fc-release-preflight-0929-replay-validation.json)。

该解析在目标树 `73798…` 运行；已用 `git diff --exit-code 73798… C552 -- demo/run-demo.ps1 orchestration/rehearsal.py orchestration/rehearsal_models.py viz/server.py` 确认这四入口/模型文件 Git blob 无差异，exit 0。它证明现有输入可由现有解析入口读取，不是 C552 全量/浏览器运行。

可指定实际历史源：

```text
C:/Users/DW/AppData/Local/Temp/morph-rehearsal-40f04885b37e489fa3ea1a04f61a984d/rehearsal.json
```

文件自报历史 live/completed、20 snapshots、EvoMap Luna、两任务 tokens 911/1226、cost null；这次只读取，不独立追认当年的远端事实。三个 `morph-finals-replay-*` 与它是相同 rehearsal_id 的副本，**不能计作三个独立 live run**。另两份 `morph-i-fixture-*`/`morph-i-gateway-stages-*` 的源 provenance 是 mock，不能冒充历史 live。全部目录保留原样。

以下展示命令已备但本轮未启动服务，不算三连：

```powershell
Set-Location 'C:\Users\DW\orca\workspaces\Morphogenesis\decentralized-swarm'
pwsh -NoProfile -File .\demo\run-demo.ps1 -Mock -Port 7861
# 停止本次前台展示并确认7861释放后，才单独运行另一模式
pwsh -NoProfile -File .\demo\run-demo.ps1 -Replay 'C:\Users\DW\AppData\Local\Temp\morph-rehearsal-40f04885b37e489fa3ea1a04f61a984d\rehearsal.json' -Port 7862
```

## 6. 三轮独立 live 样例 smoke 的具体执行卡（NOT_RUN）

**只在锁齐、最终目标 SHA/环境已核、live 模型/凭据/六项新任务范围与实际预算约束明确后使用。** 下列 20000 tokens、1 USD、120 秒是现有默认值的具体计划，不是已收到的人类预算决定或硬费用上限。若主控安排的是 FC 蜂群 smoke，须另用经过验收的 swarm 配置；这张卡只验证固定样例入口。

| 次序 | 独立 TEMP 容器（建议根） | 端口 | Mode | 新任务 |
|---|---|---|---|---|
| 1 | `%LOCALAPPDATA%/Temp/fc-smoke-0929-01` | 7861 | manual | repair + recovery |
| 2 | `%LOCALAPPDATA%/Temp/fc-smoke-0929-02` | 7862 | auto | repair + recovery |
| 3 | `%LOCALAPPDATA%/Temp/fc-smoke-0929-03` | 7863 | auto | repair + recovery |

每次在**新的独立 PowerShell 控制台进程**逐轮执行下面同一完整模板；只改表内 `$slot/$port/$mode`（第一轮为下述值；第二轮 02/7862/auto，第三轮 03/7863/auto）。不并发、不循环自动连跑。凭据由现有秘密通道注入该控制台进程，命令/日志中不写值。

```powershell
$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\DW\orca\workspaces\Morphogenesis\decentralized-swarm'
$slot = '01'; $port = 7861; $mode = 'manual'
$slotRoot = Join-Path ([IO.Path]::GetTempPath()) ('fc-smoke-0929-' + $slot)
if (Test-Path -LiteralPath $slotRoot) { throw '已存在证据根；先核身份，不覆盖、不续跑' }
if (Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue) { throw '端口占用；不杀进程' }
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) { throw '目标树环境缺失' }
if (-not $env:MORPH_EVOMAP_API_KEY) { throw '该进程缺网关凭据' }
New-Item -ItemType Directory -Path $slotRoot | Out-Null
$env:TEMP = $slotRoot
$env:TMP = $slotRoot
$env:PYTHONDONTWRITEBYTECODE = '1'
git rev-parse HEAD | Set-Content -LiteralPath (Join-Path $slotRoot 'source-sha.txt')
Start-Transcript -LiteralPath (Join-Path $slotRoot 'console.log')
pwsh -NoProfile -File .\demo\run-demo.ps1 -AuthorizeLive -Executor evomap -Model evomap-gpt-5.6-sol -Mode $mode -Port $port -MaxTokens 20000 -MaxCostUsd 1.0 -TimeoutSeconds 120 -TauSeconds 10 -ArchiveThreshold 0.2 -StageDelay 2 -TickSeconds 1
$runExit = $LASTEXITCODE
$runExit | Set-Content -LiteralPath (Join-Path $slotRoot 'native.exit')
Stop-Transcript
if ($runExit -ne 0) { throw "本轮失败 exit=$runExit；保留证据，停止后续轮" }
```

脚本本身在 slot 内再创建 `morph-rehearsal-<guid>` 和 `morph-viz-viewer-<guid>`（demo/run-demo.ps1:67–74），从 console/log 回执登记真实路径，不猜 GUID。源码入口强制 OS TEMP 下全新空 run root；不要以源码树 `.runtime` 作真实状态根或关闭保护。

每轮验收及退出标准：

- 记录启动控制台 PID/创建时间、源码 SHA、python 路径、run root、viewer launcher PID 与 listener PID、父子关系、端口；PowerShell 不提供可靠跨进程 cwd 字段时，以启动 `-WorkingDirectory` 和完整绝对命令参数证明归属，不能伪称已读 cwd。
- `demo/run-demo.ps1:74–91` 已核 listener 属于新 viewer 子进程才允许开始任务；每轮再用 `Get-NetTCPConnection -State Listen -LocalPort <port>` 和 `Get-CimInstance Win32_Process -Filter 'ProcessId=<实际PID>'` 核父 PID、创建时间、ExecutablePath、CommandLine（只保存无凭据的 viewer 命令）。不把 HTTP 200 单独当通过。
- manual 只在同轮控制台/页面真实 `awaiting_offline` 同时出现后由现场操作员按一次 Enter（rehearsal.py:318–325）；观察成员/路由变化，不能用定时 Enter、截图或重放替代。
- 原生 exit=0 **且**本轮 `rehearsal.json.current.stage=completed`，两个 `result.json` 均 succeeded，三个 checkpoint 均真，真实 provider usage、request/attempt/run 身份与 events 对应；页面对应真实 run，provenance=live。保存 `repair/`、`recovery/` 各自 config/result/events/gateway evidence、metadata/checkpoints DB、rehearsal.json、viewer stdout/stderr 和 console/native.exit。未知费用为 null，不写 0；缺 usage、未知效果、任何失败均阻止将该轮计作成功。
- 每轮核完独立 run_id/目录/实际累计 usage 和适用预算再发起下一轮。旧历史、mock、回放副本不计数；三轮最多六项新任务，脚本参数不是六项累计账单硬上限。
- live 进程退出后 viewer **仍运行**（run-demo.ps1:102–106），保留两类退出码/存活事实，不能把终端返回当作页面已关闭。异常中断时记录已发送意图和未知状态，禁止为了补绿重新调用。
- 清理前重新核实际 PID 创建时间、父子关系、命令绝对路径、对应端口和本轮 rehearsal 路径；仅关闭已证明本轮拥有的 listener 与 launcher。PID 重用/归属不明就停止清理并交现场操作员。不停止 7526/7527 历史服务或其他人进程，不对端口查出者直接 `Stop-Process`。退出后复查本轮端口释放。证据根本轮不删除；将来确需删除时先 `Resolve-Path -LiteralPath` 校验在明确 slotRoot 内、无链接跳转，再用单一 PowerShell `Remove-Item -LiteralPath`，不跨 shell 拼接路径。

## 7. T10 查实结果与原 Owner 最小 Handoff

**原预检快照：实现未发现，演练 NOT_IMPLEMENTED / NOT_RUN。** 当时本树、全部 59 个登记 worktree 均没有 `demo/fault_drill.py` 或 `tests/swarm/test_fault_drill.py`；`git log --all -- <两路径>` 无历史；本地/远端 `feat/fault-drill` 以及已知 drill refs 无结果，查询 exit 0。范围仅原预检时可读工作树和已知/远端引用，不声称不可见仓库也绝无实现，本次不重跑盘点。[逐树清单](../artifacts/ai-evidence/fc-release-preflight-0929-drill-inventory.json)。

`docs/FC_DAY_PLAN_0928.md:88` 与 TASKS:184–185,309 保留原 acceptance/队长确认及 T3 写权串行交接要求。**当前主控决定依据用户“继续”的既定 T10 实现授权，允许后续 T10 Worker 在独立 `feat/fault-drill` 分支先开发、自验；实现本身不再等待 H1/H3 人签。正式门禁演练、发布与冻结仍须满足原锁条件，隔离自验不能替代正式验收。** 后续 Worker 由主控安排认领原任务两文件并核清原 Owner/WIP 和写权交接；E 不派人、不认领实现。

最小任务单：

- 目标：后续 T10 Worker 从主控指定的精确 FC 候选基线，在独立 **`feat/fault-drill`** 分支单轨只写 **`demo/fault_drill.py`、`tests/swarm/test_fault_drill.py`**，先开发并进行隔离自验；正式演练前再核最终验收基线及锁。先核原 Owner/WIP，无需为此重构任何目录、调度器或契约；生产注入点不足只 Handoff，不扩大写权。
- 复用真实 `Worker._process`、TaskLedger、BudgetLedger、租约、`FaultObservationStore`、SharedBreaker；参考 C552 `tests/swarm/test_failure_chain_runtime.py:198–228` 已有真实 A 观察→B 路由避让的测试。该测试只是已有 contract_local 测试，不是已实现的 CLI 演练。
- 完整预期序列按本次任务重申的原 T10 要求补齐：**正常执行 → SIMULATED confirmed_rejection → 真实受控切换 → Worker B 读取 A 观察并避让 → 冷却到期从真实 guard 获得新 probe token → 成功恢复回灌**。各阶段均走现有产品对象，transport 回执明确为模拟；不得预写成功日志或把“真实路径”写作真实 provider 调用。
- 每轮单独 logs/state/source-target 目录；不读写生产 state。演练输出外层记录 **`drill:true / provenance:mock / evidence_label:SIMULATED`**（Schema 草案:30）；演练 usage/cost 未测即 null，不能伪称 provider 实测。FaultObservation 模型本身不要求硬塞 drill 字段，复用现有外层展示/日志契约，禁止改 Schema。
- B 读取 A 的证据必须包含：A 原 observation_id/request_id/task_id/attempt、append sequence/evidence_ref；B 的新身份、共享存储路径与读取到的原事实引用、before/after breaker 视图、被避让 provider 的真实 execute 计数=0、备用候选实际 execute 计数与预算/lease审计。不能让 B 直接吃预制 aggregate 或手写状态冒充观察 A。
- **零 mock live 子进程**：只注入进程内 mock transport/fixture seam；禁止 mock `--request-child` 的 live 路径、禁止请求真实 provider/付费。产品对象仍真实执行，不能用空壳 `assert True`、吞断言、伪 fallback/日志替代。
- 后续自验：脚本失败返回非零；成功亦仅 SIMULATED；正常首段、受控切换、B 避让、冷却恢复末段、unknown hold、attempt 覆盖与预算/租约约束均需行为证据。只跑新实现适用测试，不机械重复本轮已完六门禁；本次 E 不执行这些检查。

| 阶段 | 后续实现与自验必须提供的证据（本次均未执行） |
|---|---|
| 1. 正常首段 | 新隔离离线根内由 Worker A 的真实 `Worker._process` 正常完成一个任务；记录主候选 mock execute call count=1、备用=0、task/attempt/request、预算预留与租约/提交结果，作为故障前基线 |
| 2. 明确拒绝 | A 的下一独立任务经进程内 seam 收到 SIMULATED 400 Arrearage / `confirmed_rejection`；真实分类和 JSONL append 产生可追溯 observation，记录发送计数与预算结果；未知费用仍保留 hold |
| 3. 真实受控切换 | 同一故障任务经真实 Worker 候选链调用受控备用候选，核主候选拒绝一次、备用调用一次、attempt 递增及任务预算未重置；全不可用的有界退出作为负例，不能替代本成功切换阶段 |
| 4. 他者避让 | Worker B 使用同一持久 JSONL/breaker 状态、独立 task/lease，经真实 `Worker._process` / `breaker.observe` 读取 A 原事实；本阶段被避让 provider execute=0、备用 execute=1，结果及原观察引用对应 |
| 5. 冷却探测 | 冷却到期前核 guard 不放行；到期后沿既有时间 seam/真实 guard 原子领取新的有效 probe token，记录 owner/token/期限与 audit，不能手造 token、预写半开状态或绕过 guard 直接恢复 |
| 6. 成功恢复末段 | 用该 token 经真实 Worker 路径执行一次模拟成功探测并回灌，核 breaker 恢复与 recovery checkpoint；保留原故障 JSONL，再分别让同 Worker、另一 Worker、重启后的新实例重新 observe，均不得仅因旧故障再次熔断；恢复不释放 unknown hold，不清除历史失败 |

**必需测试：`test_stigmergy_avoidance`。** 必须驱动真实 `Worker._process`，以 mock call count 断言 B 对故障 provider 的 execute=0、备用 execute=1，并核 B 消费的是 A 实际追加的观察。断言放在 Worker 异常处理之外，不吞 `AssertionError`，不以日志/空断言或预制 breaker 结果替代。对“读取 A 观察/据此避让”做有意义的行为 mutation，必须使该测试红（非零），恢复原行为后绿（零），保留两次原生输出与退出码；冷却与恢复防重熔断另有上述同/跨 Worker/重启行为检查。本段仅为后续交付要求，不是已通过的测试或 mutation。

原预检没有该模块，本次也未实现，所以**没有本次已验证可执行的 fault_drill CLI 命令**。下面仅为后续 Owner 待实现/评审的最小接口提案，不能据此声称模块已存在或正式演练获准；隔离自验按上述既定授权进行：

```powershell
# FUTURE PROPOSED CLI -- 原 Owner 落实现有接口后才定稿
.\.venv\Scripts\python.exe -B -m demo.fault_drill --directory "$env:TEMP\morph-fc-drill-0929-01" --scenario confirmed-rejection-peer-avoidance
# FUTURE scoped validation; full paths must be outside source protected runtime
.\.venv\Scripts\python.exe -B -m pytest -q tests/swarm/test_fault_drill.py --basetemp "$env:TEMP\morph-fc-drill-tests-0929-01" -p no:cacheprovider
```

## 8. 已执行检查、剩余步骤与最少人类信息

| 本轮实际检查 | 结果 |
|---|---|
| Orca status / terminal show / check | exit 0；现有 Run/dispatch/树一致 |
| Git remote/ancestry/delta/tag/drill history、两次只读 merge-tree | exit 0；结果见上文与 Git JSON |
| PowerShell Parser 读取 run-demo.ps1 | 0 parse errors；没有执行脚本 |
| 目标树 `.venv/Scripts/python.exe -B -m orchestration.rehearsal --help` / `viz.server --help` / `swarm.cli --help` | 三条 native exit 0；[命令记录](../artifacts/ai-evidence/fc-release-preflight-0929-readonly-checks.log) |
| 11份现有回放 Pydantic 只读解析 | native exit 0；未启动 viewer/模型/Run |
| 入口四文件目标→候选 blob 比较 | exit 0，无差异；不是新 SHA 全门禁 |
| 初次环境盘点 PowerShell foreach 管道 | **exit 1 ParserError：不允许空管道元素**；整段未执行，修正核查命令后 exit 0，未修产品 |
| 探索性 rg 使用两个猜测不存在的 executor 文件名 | 报 OS error 2；改按真实 `orchestration/gateway.py` / `codex.py` 读取，不当产品缺陷或 green gate；外层多命令 exit 0 不是该 rg 成功 |
| 材料 JSON/路径边界/引用/`git diff --check`/commit/push | 材料验证见 `artifacts/ai-evidence/fc-release-preflight-0929-validation.json`；提交/远端/clean 实际回执保存于 ignored `.runtime/fc-release-preflight-0929/delivery.json` 并报 worker_done，未预写通过 |

**可立即继续的授权工作**：主控安排后续 T10 Worker 认领两文件，在独立 `feat/fault-drill` 分支开发并隔离自验；G 补齐凭据后完成指定模型正式评审及人审材料；主控核本文命令/边界，按需只读重核最终 refs、环境存在性、端口/PID、回放结构，收取人类 H1/H3。本次 E 仅检查窄 diff/引用/历史保留，材料普通 commit+push 属本轮交付，不是生产发布。

**待原条件满足的工作**：接受合格 FC-E/H1 后集成及最终 SHA 证据确认；H3 后 Schema 冻结/T9 采集；锁齐后在最终验收基线上进行 T10 正式门禁演练与验收；明确 live 条件后适用三连、课题入口和现场投影。隔离实现/自验可按当前授权先行，本次 E 未实现、测试或运行 T10；G 正式 review 缺凭据、H1/H3 pending 均未由材料修订解除。若真正目标是课题，先明确现有可执行入口，不用固定 repair/recovery 样例替代。

必要最少人类信息只有：

1. H1：对完整 C552/最终待审源码的预算 A/B 结论及前提、breaker 六点结论、复核人/时间/签名；H3：Schema blob/1.0.0 candidate 的准入范围与冻结结论（G 收录，本轨不代填）。
2. 课题的绝对 workspace 路径、课题身份、实际任务与验收目标；确认三轮要验固定样例入口还是 FC 蜂群/课题链。端口可沿用本卡建议，现场实际占用由执行者即时核查。
3. 实际 live executor/model、凭据所在的既有安全通道（只需路径/配置存在性，不在消息中发值）、新任务/调用次数和跨三轮预算、超时及未知费用时是否允许独立新任务的明确约束。脚本并不保证上游硬费用上限。

现场投影/选屏和 manual Enter 仍由现场操作员完成；没有额外新增审批流程。FC-E成败由G正式回执决定，代码门禁/文档齐全/预检完成均不自动签署H1/H3。

## 9. 本轮生产前置追加事实（2026-09-29）

本节是 C / codex 的 `task_3e21836ea2c2 / ctx_6b976c62b96d` 新事实；上文历史快照逐字保留，不能把其中 H3 未签、T10 无实现等旧状态当作当前结论。当前三轨写权及后续 I 顺序见 [生产一页计划](FC_PRODUCTION_PLAN_0929.md)。本轨开工 `7347f5c1a7eaf0f5a3279c2db0ffb751a730792c`，clean；共同代码仍是 **C552**，最终 A+B+H3 候选 SHA 尚未收到。本轮交付的是前置工具和材料，**正式 FC-E / smoke / tag / 生产 merge / 业务 live 均 NOT_RUN，模型与 Hub 请求均为 0**。

### 9.1 H3 已冻结；H1 最小待签清单

本轮 `git ls-remote origin` 实查：`decentralized-swarm=be4fb7a685e951c9e42d8dc0c7eeb900cb5518f1`，parent `73798cd6f05210f2bd9b1eebfd6f9f0dd6e842db`；目标工作树 clean。提交仅改 `docs/FC_LOG_SCHEMA_DRAFT_0928.md`，`:17–26` 明确 David / 2026-09-29 / Schema **1.0.0 正式冻结**、原 12/12 与 9/9 controls。它声明是 Owner 复跑，C 没有重跑或冒充独立验收。该冻结不等于生产采集完成，也不自动成为 H1 签名。

H1 的实查 [immutable 原文](../artifacts/ai-evidence/fc-production-preflight-0929-source-facts.json)：C552 `swarm/breaker.py:202,592,672` 三处 TODO 保留；`docs/FC_HUMAN_REVIEW_0928.md:169–178` 的姓名、时间、六项结论仍待填，槽内旧目标为 `73e64cc`。治理 **40577cb841e8d89c08e1336d7254c4ca7bb3984e** 的 `docs/FC_HUMAN_REVIEW_0929.md:40,66` 绑定 C552 的预算结论/签名也待填。没有从“签字目前h1”推定人签已齐；主控已向本人收取，C 不重复问、不改人签槽。

本人只需提供以下完整记录，由主控收录到授权材料：

| 待签项 | 最少内容 | 绑定要求 |
|---|---|---|
| 预算 A | unknown hold 后同 task 新 request 的 pending 冲突/容量判断，结论与成立前提 | C552 `budget.py:179–203,230–251` 和 `worker_loop.py:757–825`；最终 SHA 到位后重新绑定，旧行号不得照搬 |
| 预算 B | 可用额度是否双计、晚到 uncertain 对账未实现、长期 hold、lower usage、无上游硬账单上限的结论与前提 | C552 `budget.py:77–101,192–203,259–313` |
| breaker 六点 | 16 格转移、双阈值/欠费例外、并发 fencing/旧 token、Retry-After、纯函数与恢复水位、预算/租约隔离，各写结论或未解决项 | C552 `breaker.py:163–251,477–521,569–695`；实际最终候选的同路径须重核 |
| 身份与范围 | 本人姓名、日期、完整受审 SHA、以上结论；是否授权原生产 Owner 替换三处 TODO | 不把 AI 源码核对、H3 David 签名、旧 SHA 自动转成最终 H1 |

三锁仍分别要求最终候选适用门禁、合格正式 FC-E、H1；“H3 已冻结”不能解锁全部 FC。

### 9.2 正式 native dsh 通道与可复用前置

只读复用治理 **40577cb** 的 `review-0929-v41flash-report/prepare/verify/preflight`，不是拿治理 HEAD 作产品基线。新脚本注明 repo Apache-2.0 来源；原生安装 `@deepseek-ai/dsh 0.1.5-rc.3 / MIT` 不变。内置目录 `DeepSeek-V41-Flash → deepseek-official/deepseek-flash` 已据原生文件复核；这是配置名称，不是实际服务返回模型。未改成 R1/V4 Flash/SDK。

[第一次环境快照](../artifacts/ai-evidence/fc-production-preflight-0929-environment.json) 与 [安装既有锁包后的快照](../artifacts/ai-evidence/fc-production-preflight-0929-environment-ready.json) 均只查存在性：Process/User/Machine 的 `DEEPSEEK_API_KEY / DEEPSEEK_BASE_URL / DSH_HOME / DSH_SETTINGS_FILE` 全缺；`C:/Users/DW/.dsh` 与原 `decentralized-swarm/.runtime/fc-auth/dsh-home` 的 `settings.yaml/.credentials.yaml/.env` 及本树 `.env` 全缺，两个标准 headless patch 文件存在。没有搜索秘密历史、读取秘密值或做远端认证。原 DashScope R1 配置不能用于官方 DeepSeek key。

可复制的安全认证入口（**仅由持有官方 key 的操作者在后续实际调用进程中运行，本阶段未执行**）：

```powershell
$fcSecret = Read-Host '官方 DeepSeek API key（不回显）' -AsSecureString
$env:DEEPSEEK_API_KEY = [Net.NetworkCredential]::new('', $fcSecret).Password
# 不打印、不写入 Git/命令正文；调用结束后 Remove-Item Env:DEEPSEEK_API_KEY
```

若用户已有标准 profile/凭据路径，交主控后由同 Owner 仅检查该路径；本次没有广扫其他位置。缺认证不阻塞下面离线准备。

| 工具 | 实际作用 / 已验证边界 |
|---|---|
| [prepare.py](../artifacts/ai-evidence/review-0929-release-v41flash-prepare.py) | 强制完整 `--candidate` SHA；从 immutable Git blobs 取原 FC diff、五修复 diff、C552→最终 A/B diff、完整核心文件与七个原测试、A/B/入口/H3 上下文；默认拒绝缺 A/B 文件的旧候选；不执行模型 |
| [native-prepare.ps1](../artifacts/ai-evidence/review-0929-release-v41flash-native-prepare.ps1) | 用本树 ignored 独立 DSH_HOME 和 JSON overlay，直接设置原生 headless-runner `config.task`，取消 startup 依赖；仅 `dsh --profile headless --patch … --dump-config`，不 boot runner |
| [verify.py](../artifacts/ai-evidence/review-0929-release-v41flash-verify.py) | 原响应只读；逐条 fact 完整 SHA + 原 `file:start_line` + 原 UTF-8 bytes，相差即整条 INVALID；hypothesis 必须待验证；不帮模型改行号、引文、风险或结论 |
| [check-materials.py](../artifacts/ai-evidence/fc-production-preflight-0929-check-materials.py) | 离线反例及组合配置检查；10 个控制，非产品/模型评审测试 |
| [readonly.ps1](../artifacts/ai-evidence/fc-production-preflight-0929-readonly.ps1) | 标准来源存在性、native help/version、端口、环境和 remote refs；不输出密钥、不开服务 |

覆盖沿用原 **37 维**：五不变量、五修复、16 个 breaker state/event 格、fencing/旧 h2/旧 h3/预算 A/B/限制、六类假绿；另加生产日志、六阶段演练、live 入口，共 **40 维**。coverage 是要求，**没有模型输出，不能称模型已覆盖**。假绿包含吞断言、mock 替代产品路径、只断言预算、弱化/删除/skip、只检查字段、mutation 不红或恢复不一致。

本次用明确 `--preparation-control` 的旧 C552 离线对照检验工具：完整输入 **524,744 UTF-8 bytes**，tokens=null；7 项 native config 检查通过，组合后 task bytes 完全相等，`retryPolicy={mode:normal,maxRetries:0}`、maxTokens=16384、工具/title/compaction/子 Agent/遥测等指定插件 disabled。**这里只证明 dump/config 组合，不证明运行时启动、provider 接受输入、真实请求数、usage/cost 或返回模型。** full final prepare 未加 control 时对 C552 四个缺失 A/B 文件按预期 exit **2**，没有生成可冒充最终候选的输入。

离线 verifier 控制的真实 exit：[最终控制回执](../artifacts/ai-evidence/fc-production-preflight-0929-tool-controls-v2.json)（保留[初版回执](../artifacts/ai-evidence/fc-production-preflight-0929-tool-controls.json)）。精确合成样本只得 MECHANICAL_ONLY/0；错行、空白改变、治理 SHA 替换、缺维度、重复 ID、无效 evidence、非数组、旧报告均 exit1；响应不存在 exit2/NOT_RUN。原 R1 quote-only 仍 **f1/f2 PASS、f3/f4 INVALID**；新协议维度不接受旧标签，旧报告不变，也没有据此获得新评审。

后续收到主控最终 `$fcCandidate` 后可按下面顺序准备，输出必须选全新目录；不得带 `--preparation-control`：

```powershell
# $fcCandidate 必须是主控交来的完整最终 SHA；$fcPacket/$fcNative 是新的 OS TEMP 或 ignored 本轨目录。
.\.venv\Scripts\python.exe -B artifacts/ai-evidence/review-0929-release-v41flash-prepare.py --candidate $fcCandidate --output-dir $fcPacket
if ($LASTEXITCODE -ne 0) { throw '保留失败，停止' }
pwsh -NoProfile -File artifacts/ai-evidence/review-0929-release-v41flash-native-prepare.ps1 -Candidate $fcCandidate -InputJson (Join-Path $fcPacket 'review-0929-release-v41flash-input.json') -OutputDirectory $fcNative
if ($LASTEXITCODE -ne 0) { throw '保留失败，停止' }
# 实际 review 由后续 Dispatch 在最终 SHA/认证/限制核完后执行一次原生 dsh；本段只 prepare。
# 返回后原始文件不改，使用同一 coverage/SHA：
.\.venv\Scripts\python.exe -B artifacts/ai-evidence/review-0929-release-v41flash-verify.py $fcRaw --candidate $fcCandidate --coverage (Join-Path $fcPacket 'review-0929-release-v41flash-coverage.json') --output $fcVerification
```

后续原生命令为 `dsh --profile headless --patch <本次overlay绝对路径>`，task 已在配置内，无需塞到 Windows argv；使用生成的独立 `DSH_HOME` 并清除不相关 `DSH_SETTINGS_FILE` 后再核组合，不借旧 DashScope home。原授权是**一轮 invocation ≤600000ms / retry0 / 有限输出 / 禁非必要工具、title、compaction**，不是 exactly-one-HTTP；需要执行者监视该轮时间、保存 stdout/stderr/原生 session 与真实 exit，超时按本轮进程身份终止并保留可能已发送/unknown，绝不自动再发。native config 尚未实际 boot；若失败只保留事实。headless session 的 source.model 来自 request.model，不能冒称返回模型；无法独立观测的 returned_model/request_count/usage/cost 留 null。

### 9.3 真正入口、auto 三轮及单任务备选

已在本树创建锁定 `.venv`（Python 3.12.13，Poetry 从现有锁装 88 包）并 `npm ci --ignore-scripts --no-audit --no-fund`（99 包）；两条 exit0，锁/依赖文件未改。`orchestration.rehearsal / swarm.cli / viz.server / orchestration.acceptance --help` 四条均 exit0；不是执行入口任务或最终候选测试。运行环境原始日志在 ignored `.runtime/fc-production-0929/`，未借用他树虚拟环境。

本次拟用 7861/7862/7863 与历史 7526/7527/7844 均无 listener；不保证将来仍空闲，不创建 listener、不停止任何进程。`demo/run-demo.ps1` 语法解析零错误，真实参数为 `-AuthorizeLive -Mode auto|manual -Executor codex|evomap -Model -Port -MaxTokens -MaxCostUsd -TimeoutSeconds -TauSeconds -ArchiveThreshold -StageDelay -TickSeconds`，无课题 workspace 参数。它在 OS TEMP 创建新的 repair/recovery 样例，read-only 页面不是任务授权；`-Mock/-Replay` 都不能算 live。

路由/费用现状：gateway 默认 `https://api.evomap.ai/v1`、`evomap-gpt-5.6-luna`（C552 gateway_transport:17–18），历史 `evomap-gpt-5.6-sol` 只是建议；当前三层 `MORPH_EVOMAP_API_KEY` 也缺，未核到本轮指明的外部 credential_file 或正式价格配置。gateway `gateway.py:166` 费用固定未知 null；swarm executor 使用外部 credential_file，拒绝把该环境 key 带入（evomap_executor:279–289），二者不可混配。`swarm.cli evomap --config <path>` 为受限 JSON 样例（3×6 / 8×48 / 16×96；每任务一次，cli:28–53），不是任意真实课题，也不替代 demo 三连。未调用 models/discover、SDK 接口或 provider 验证价格。

**双任务 auto live 当前 BLOCKED。** C552 `rehearsal.py:301–305` 仅在 tokens 未知时停止；cost null 仍返回，`:318–342` auto 随后执行 recovery。`-MaxCostUsd` 非在途硬上限，也没有跨三根累计账本。若约束是每次 unknown 费用即停止后续新任务，该入口连同一轮第二任务都不能保证阻断；不能只在轮末查 null 冒称满足。主控 `msg_58cbb50f268c` 已明确保持此阻塞，向用户提出“现有单任务并 unknown 即停”或“明确授权原 Owner 修复 auto 准入后双任务三连”；C 不把日志接线授权扩成预算实现修改。

收到路由/目标/预算决策且上述入口限制解决后，三轮均 auto，顺序为 **01/7861 → 验收 → 02/7862 → 验收 → 03/7863 → 验收**，各自新 OS TEMP 根及独立 run_id，绝不循环盲发。每轮最多 repair+recovery 两个新任务，三轮最多六个；只能按本人给定的累计 tokens/费用 allowance/任务数/超时约束准入，现有默认 20000/1USD/120秒不是本轮预算授权。使用上文第6节同一原生命令模板，把三轮 `$mode` 均设为 `auto`，模型与上限来自本轮确认值；旧第一轮 manual 安排不适用于当前 auto 方案。

每轮必须完成以下检查才考虑下一轮：源码 SHA/环境不漂移；listener PID、父 PID、创建时间和绝对 rehearsal 路径属于本轮；真实 exit0、stage=completed、两份结果 succeeded/三个 checkpoint 真、provenance=live、实际 request/attempt/run 及 usage/evidence 对应；实际累计费用/未知持有与剩余授权核实。任何失败、中断、unknown effect、unknown 成本或证据缺失立即停后续，保留证据/hold，不退款、不重发、不用 replay 补轮数。viewer 仍存活是独立事实；只按第6节归属核实后清理本轮自己进程。若改用 manual，真实 awaiting_offline 时由操作者按 Enter，C 不代按。当前未执行三轮中的任一轮。

**现有单任务备选**已核为 `orchestration.acceptance`，不是新实现：

```powershell
# 仅后续用户确认 Codex 样例路由/有限预算后执行；$fcSingleRoot 必须是新的 OS TEMP 空根。
# $fcModel/$fcTokens/$fcCost/$fcTimeout 来自本人确认，当前没有代填默认预算。
.\.venv\Scripts\python.exe -B -m orchestration.acceptance --root $fcSingleRoot --model $fcModel --max-tokens $fcTokens --max-cost-usd $fcCost --timeout $fcTimeout
$fcExit = $LASTEXITCODE
```

它 `acceptance.py:62–64` 设置 max_retries=0，`:103` 固定 **CodexExecutor**；没有 `--executor`，不能传 EvoMap 名称暗中换路由。不传 `--continue / --experience / --pause-after-execute`，执行一个新的 sample.py repair；内部一次 CLI invocation 不被扩大表述为恰好一次 HTTP。`:130` 的 exit0 也包括 pending_review，必须另核 `result.json.status=succeeded`、`acceptance.task_live=passed`、真实 verifier 与 request/usage；summary 明示费用未知、无自动下一调用，故费用仍 null 时即停止后续任务。它不自动启动 viewer、不接受任意课题 workspace，**不能充当用户实际课题或六任务三连的替代品**。本轮只运行 help，真实执行 NOT_RUN。

待主控收取的最少 live 信息仍是：真实课题绝对 workspace/身份/目标验收，选定入口及实际 provider/model、标准安全凭据路径，任务数与跨三轮累计预算/超时/unknown 处理约束。旧历史授权中的 `allow_unknown_cost` 或旧样例预算不能推定对本轮新目标有效。T9 样例/消息仍待后续；benchmark `POLL_MS` 风险保留，不触不在候选的 WIP，不外发消息/报名/发布。

### 9.4 本轮验证与交付边界

| 本轮检查 | 真实结果 |
|---|---|
| 开工身份 / remote 四 refs / H3 parent、单文档、目标 clean | exit0；H3 新冻结事实已独立读取；C552 与治理 refs 精确匹配 |
| Poetry/npm 从既有锁安装；四入口 help | 全部 exit0；不代表 final SHA focused/full/strict/build/SDK/distribution |
| PowerShell parser：run-demo、readonly、native-prepare | 3 项零语法错误，未执行 demo |
| C552 离线 control prepare / native dump | exit0；524744 bytes，40维；未请求模型；最终模式拒绝缺 A/B exit2 为预期控制 |
| 10 个 verifier 控制 / 7 项配置核对 | 汇总 exit0；内含有意的 exit1/2，分别保留；见 tool-controls-v2 |
| 探索性错误 | 对 PowerShell 通配路径 `docs/FC_HUMAN*` 的 rg 报 OS error123；猜测不存在的 `orchestration/cli.py`、`tools/check_demo_environment.py` 报 OS error2；改从 rg --files 真实入口定位，不当产品失败或通过；首份环境记录探测 `graphology.bundle.js` 不存在是错误候选路径，最终脚本改查实际 `viz/static/app.js`，保留首份快照 |
| 材料写权 / 历史前缀 / immutable 原引文 / JSON / diff | 见 [最终材料校验](../artifacts/ai-evidence/fc-production-preflight-0929-validation.json)，仅材料门禁 |

本阶段不等待用户认证/签字/目标而无限占用；材料 commit+push 后结算，后续由主控给同 C Owner 新 Dispatch 和共同最终 SHA 接正式 FC-E/入口验收。未执行 final SHA 产品门禁、独立 Schema/mutation/六阶段验收、模型评审、人签、生产合并/tag/三连/课题 live；C552 历史六绿不借名为新 SHA 实跑。交付 SHA/parent/remote exact/clean 回执保存于 ignored `.runtime/fc-production-0929/delivery.json` 并在 worker_done 报告。
