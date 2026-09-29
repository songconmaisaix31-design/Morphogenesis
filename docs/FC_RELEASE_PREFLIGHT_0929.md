# FC 发布、入口与演练预检 · 2026-09-29

本轮仅完成预检材料。**发布/合并/tag/三连冒烟/T10/业务 live 均 NOT_RUN；H1/H3 unsigned；FC 未冻结。** E 不执行模型评审；主控所述 `dsh deepseekV4.1flash` 新正式评审由 G 负责，不能用旧 deepseek-r1 拒收报告或本预检补锁。

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

**实现未发现，演练 NOT_IMPLEMENTED / NOT_RUN。** 本树、全部 59 个登记 worktree 均没有 `demo/fault_drill.py` 或 `tests/swarm/test_fault_drill.py`；`git log --all -- <两路径>` 无历史；本地/远端 `feat/fault-drill` 以及已知 drill refs 无结果，查询 exit 0。范围仅当前可读工作树和已知/远端引用，不声称不可见仓库也绝无实现。[逐树清单](../artifacts/ai-evidence/fc-release-preflight-0929-drill-inventory.json)。

`docs/FC_DAY_PLAN_0928.md:88` 与 TASKS:184–185,309 仍要求 acceptance 后、彩排前，和 T3 写权串行交接。仓内未登记可核验的独立 T10 Owner/分支交付；已知相邻测试权属是原 T3/FC-D qwen-code（day plan:34,81）。请主控交回**原 T10 Owner**，并核实与原测试 Owner 的写权交接；E 不新派人、不认领实现。

最小任务单：

- 目标：在验收后的最终 FC 基线上，由原 Owner 单轨只写 **`demo/fault_drill.py`、`tests/swarm/test_fault_drill.py`**；分支拟用既定 `feat/fault-drill`（当前不存在）。先核原 Owner/WIP，无需为此重构任何目录、调度器或契约；生产注入点不足只 Handoff，不扩大写权。
- 复用真实 `Worker._process`、TaskLedger、BudgetLedger、租约、`FaultObservationStore`、SharedBreaker；参考 C552 `tests/swarm/test_failure_chain_runtime.py:198–228` 已有真实 A 观察→B 路由避让的测试。该测试只是已有 contract_local 测试，不是已实现的 CLI 演练。
- 可审查预期序列：新隔离离线根 → A 第一任务通过进程内测试 seam 收到明确 400 Arrearage（SIMULATED）→真实分类/预算保留/JSONL append → B 使用同一持久 JSONL/breaker 状态、独立 Worker/task/lease → B `breaker.observe`（worker_loop.py:736）读到 A observation → A provider 被跳过且 executor 发送计数=0 → 受控备用候选被实际调用一次或全部不可用有界退出 → 输出每步原生结果与 reservation/observation/route 身份对应。不得预写成功日志；若扩展 429/冷却/unknown 仅沿用既有接口，避免扩大到新功能。
- 每轮单独 logs/state/source-target 目录；不读写生产 state。演练输出外层记录 **`drill:true / provenance:mock / evidence_label:SIMULATED`**（Schema 草案:30）；演练 usage/cost 未测即 null，不能伪称 provider 实测。FaultObservation 模型本身不要求硬塞 drill 字段，复用现有外层展示/日志契约，禁止改 Schema。
- B 读取 A 的证据必须包含：A 原 observation_id/request_id/task_id/attempt、append sequence/evidence_ref；B 的新身份、共享存储路径与读取到的原事实引用、before/after breaker 视图、被避让 provider 的真实 execute 计数=0、备用候选实际 execute 计数与预算/lease审计。不能让 B 直接吃预制 aggregate 或手写状态冒充观察 A。
- **零 mock live 子进程**：只注入进程内 mock transport/fixture seam；禁止 mock `--request-child` 的 live 路径、禁止请求真实 provider/付费。产品对象仍真实执行，不能用空壳 `assert True`、吞断言、伪 fallback/日志替代。
- 验收：脚本失败返回非零；成功亦仅 SIMULATED；隔离目录、真实 B 避让、unknown hold、attempt 覆盖与预算/租约约束有行为证据；对 B 观察/避让做有意义 mutation 时必须红、恢复绿。只跑新实现适用测试，不机械重复本轮已完六门禁。

当前没有该模块，所以**没有已验证可执行的 fault_drill CLI 命令**。下面只是 Owner 待实现/评审的最小接口提案，绝不可现在运行或写作已存在：

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

**可立即继续的授权工作**：G 完成指定模型正式评审及人审材料；主控核本文命令/边界；只读重核最终 refs、环境存在性、端口/PID、回放结构；收取人类 H1/H3。E 材料普通 commit+push 属本轮交付，不是生产发布。

**待原条件满足的工作**：接受合格 FC-E/H1后集成及最终 SHA证据确认；H3后 Schema冻结/T9采集；原 Owner按最小 Handoff实施并验收T10；明确live条件后适用三连、课题入口和现场投影。T10实现与运行都未由本预检提前执行。若真正目标是课题，先明确现有可执行入口，不用固定repair/recovery样例替代。

必要最少人类信息只有：

1. H1：对完整 C552/最终待审源码的预算 A/B 结论及前提、breaker 六点结论、复核人/时间/签名；H3：Schema blob/1.0.0 candidate 的准入范围与冻结结论（G 收录，本轨不代填）。
2. 课题的绝对 workspace 路径、课题身份、实际任务与验收目标；确认三轮要验固定样例入口还是 FC 蜂群/课题链。端口可沿用本卡建议，现场实际占用由执行者即时核查。
3. 实际 live executor/model、凭据所在的既有安全通道（只需路径/配置存在性，不在消息中发值）、新任务/调用次数和跨三轮预算、超时及未知费用时是否允许独立新任务的明确约束。脚本并不保证上游硬费用上限。

现场投影/选屏和 manual Enter 仍由现场操作员完成；没有额外新增审批流程。FC-E成败由G正式回执决定，代码门禁/文档齐全/预检完成均不自动签署H1/H3。
