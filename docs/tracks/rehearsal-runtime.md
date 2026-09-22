# R 固定彩排运行链路

原三轮阶段基线：`791d3cf`，该阶段真实调用预算六次；以下原阶段记录保留。新增第四轮 Gateway 阶段见文末，R 的真实模型/API 调用预算仍为零。

## V 消费契约（第一阶段）

直接导入 `orchestration.rehearsal_models.RehearsalDocument`；不复制类型。运行目录下的 `rehearsal.json` 为该模型序列化，`current` 是 `history[-1]`。读取端用 `model_validate_json`。

- 每幕包含 `stage / sequence / at / task_id / task_description`。
- `checkpoints.checks` 为 clamp / mean / unique 的独立 unittest 真判定；未知是 null。`passed_count / total / ratio` 验证一致，3/3 必须有通过的独立验证证据。
- `members` 为具体 AgentId 可用性；`pipes` 直接复用 `PipeState[]`。不可用成员的管道只在展示快照设 inactive，不修改拓扑正常策略。
- `routing` 给出有效成员、实际 selected_attempt、removed_member/removed_at；`boundary=between_tasks`。
- `genes` 直接复用 `GeneView[]`，`adoptions` 复用 `UseRecord[]`，`results` 为每个任务原有 TaskResult；`retrievable_gene_ids` 来自实际 resolve。
- `tau_seconds / archive_threshold / at` 显式披露墙钟演示参数；不加速或伪造时钟。
- `mode / provenance / acceptance` 严格区分 live/mock/replay 及 contract_local/interface_live/task_live；`cost_usd=null` 是费用未知，不能显示为零。
- `scope=fixed_pool_between_tasks` 仅证明固定逻辑成员在新任务分配前移除后的选路恢复，不证明杀死在途 CLI 后恢复。没有 PID 死亡/进程心跳模拟。Hub 始终 `pending_publish`。

## 已实现入口和操作顺序

```powershell
# 仅 I / 操作员执行：明确授权两次不同的新任务，每个任务一次调用。
python -m orchestration.rehearsal --root "$env:TEMP/morph-rehearsal-new-1" --mode auto --authorize-task repair --authorize-task recovery --model gpt-5.6-luna --tau-seconds 10 --stage-delay 2 --timeout 180
# 手动模式：同样参数改成 --mode manual，在 awaiting_offline 按 Enter。
# 只读回放：输出 JSON 至 stdout，不创建目录、不改原始证据、不调用模型。
python -m orchestration.rehearsal --replay "$env:TEMP/morph-rehearsal-new-1/rehearsal.json"
```

`--root` 省略时创建新的空 TEMP 根。已有非空根一律拒绝再次运行；读回放不接受任何执行授权。默认模型 gpt-5.6-luna；不改变账号/认证配置。可调整 `--tick-seconds`（默认 1）、`--archive-threshold`（默认 0.2）、`--max-tokens`（每任务默认 20000）、`--max-cost-usd`（每任务申明默认 1）。现有 CLI 不提供调用中美元硬上限，不能将该参数或 token 数称作费用证明。

两次调用以 `--authorize-task repair --authorize-task recovery` 明确授权；第二次为新 TaskId、新工作目录里的坏样例，绝非重试。第一次失败、执行未知、token usage 缺失时停止，不进入第二次；第二次失败也不重试。费用未知保留 null；旧 Runtime 的 unknown_usage 语义不改，第二次调用依赖独立的新任务授权。三次彩排总计最多六次真实调用，R 无真实调用，I 必须跨三个根累计预算，不能在失败后换根变相重试。

顺序：

1. task_ready：外部固定 unittest 对坏样例产生真实 0/3。
2. repair_selected：Runtime 选中第一名 builder；唯一 execute_intent 进入现有执行器。
3. repair_reviewed：外部独立 reviewer 给出真实结果；先保存复核，再保存反馈后的管道权重，成功管道从 1.0 增至 1.9。
4. gene_generated：仅从本次已通过独立验收的 proposal.summary/content、verdict 和 source_attempt 生成本地 Gene。
5. awaiting_offline → member_offline：auto 按顺序执行，manual 等待 Enter；移除获胜 builder 后展示原管道 inactive。底层拓扑策略/权重不受展示覆盖影响。
6. recovery_ready → recovery_selected → recovery_reviewed：新空工作目录的新任务；有效列表只剩另一名 builder，实际执行后独立复核。
7. gene_adopted：只有 executor 明确声明采用已注入 Gene 且独立复核成功，原有 LocalMetabolism.mark_used 才增加采用记录并刷新权重。未声明采用则不能完成彩排；不会补造采用事实。第二次成功也生成自己的 Gene。
8. decaying → archived → completed：真实 time.time() 墙钟计算 exp(-elapsed/tau)，逐幕记录；低于阈值调用原有本地 archive，再对每个 Gene 调用 resolve，全部不可检索才完成。远端 Hub 不发布、不同步。

所有阶段均原子更新 `root/rehearsal.json`，其中 current/history 有完整前后快照。每次任务的 config/result/gene/events/CLI 原始证据/外部 verification 文本和 JSON 保存在 `root/repair`、`root/recovery`；元数据与 LangGraph 检查点使用原有 SQLiteStore/SqliteSaver。失败保存 stage=failed、failure 和已知结果，UNKNOWN 为 blocked 或 not_run，不伪称已知修复失败。`root/STOP` 可阻止继续；现有执行器负责自己的调用超时，不用进程死亡制造恢复故事。

V 可先启动只读 HTTP viewer，再在前台运行 CLI；初次独立验证完成前文件短暂不存在，应显示等待。live 轮询 `read_rehearsal(path)`；回放用 `read_rehearsal(path, replay=True)`，返回数据所有来源为 replay，interface_live/task_live 降为 not_run，保留原始证据 URI、时间、结果和未知费用，message 标注原始来源。`--replay` 仅输出至 stdout，不覆盖传入源文件；V 持续读取原 `--rehearsal` 路径即可。已与 V 确认显式授权和只读回放入口。

## 验证与剩余限制

复用 `../morph-integration/.venv/Scripts/python.exe` 的锁环境，仅执行工具、不改该 worktree；无全局安装、无模型/API 调用。

- `python -m pytest tests/t2 tests/t0/test_bootstrap.py tests/t3/topology -q`：37 passed，包括完整 fixture 流程和真实外部 unittest 子进程。fixture 的所有任务/Gene/快照均 mock，interface_live/task_live 保持 not_run。
- `python tools/typecheck.py`：52 source files strict clean。
- `uv tool run --offline poetry check --lock`：锁一致（仅元数据弃用提示）。
- `uv tool run --offline poetry build --output "$env:TEMP/morph-rehearsal-runtime-dist"`：sdist/wheel 成功；wheel 内含新入口、共享模型、固定 runner 和 fixture。直接 `python -m build --no-isolation` 曾因复用环境未装 poetry-core 报 BackendUnavailable，改用已有离线 Poetry 构建成功，未安装全局工具或修改其他 worktree。
- 真实模型调用、真实 Gene、三次真实全流程、页面浏览器证据由 I 验证；本轨测试不能代替。真实投影接线仍需人工完成，固定成员池下线不证明在途 CLI 被杀后的恢复。

契约首交提交：`e3fe21d`。完成提交与最终 SHA 见本轨交付消息；开发和返修仍由 R 负责，待协调者明确放行后才发 worker_done。

## 2026-09-22 Windows CI 时间断言返修

最初的限定草稿仅修改 `tests/t2/test_rehearsal.py` 和本报告，未提交。分支为 `songconmaisaix31-design/morph-rehearsal-runtime`，返修起点为 `652e3199d626f60b414b70ee523b5f9703d1e539`；以上原阶段验证记录不是本轮返修验证。新的第四轮任务已取代草稿阶段“不提交、不推送”的限制，将该修复纳入本轨交付。

协调者提供的失败事实：候选 `e83a816` 的 Windows CI `35691719303` 为 1 failed / 157 passed；原断言 `adopted.genes[0].weight > 0.5` 在 tau=0.1 秒、采用后约 0.103 秒取样时得到 `0.3563490268443933`。这是正确的真实墙钟衰减，错误在测试隐含要求快照足够快；后续 `c1542b2` / CI `35691937011` 偶然通过不能排除竞争。本轮未重新访问远端 CI。

修改内容：

- 按第二次实际 AttemptId 找到采用记录，并按 GeneRef 找到对应 Gene，验证其 source_attempt 是第一次执行。
- 验证 use_count=1、last_used_at 精确等于该采用记录的 used_at，且 created_at < last_used_at <= evaluated_at，明确采用刷新了时间锚点。
- 用快照实际 `(evaluated_at - last_used_at) / tau_seconds` 计算 `exp(-elapsed/tau)`，通过 `pytest.approx` 校验观察到的权重，不再对机器速度或快照权重设固定下界。
- 将原完整 fixture 流程参数化为 normal 和 slow-adoption-snapshot 两种观测；慢分支仅在测试中、mark_used 后且 gene_adopted 快照计算前真实等待 0.2 秒，保留产品 tau=0.1 与真实时钟，覆盖旧断言会误报的迟到快照。

草稿阶段验证记录（当时沙箱内执行，无权限升级）：

- `& ../morph-integration/.venv/Scripts/python.exe -B -m pytest tests/t2/test_rehearsal.py -q -p no:cacheprovider`：命令已启动，结果为 `7 errors in 11.92s`、退出码 1；所有用例在 `tmp_path` fixture 的 setup 阶段因 `PermissionError: [WinError 5]` 无法访问 `C:\Users\DW\AppData\Local\Temp\pytest-of-DW` 而中止。测试正文为 **NOT_RUN**，不能宣称返修运行通过；未请求升级、未更换工具或临时目录绕过限制。
- `& ../morph-integration/.venv/Scripts/python.exe -B -m mypy --strict tests/t2/test_rehearsal.py`：**PASS**，`Success: no issues found in 1 source file`，退出码 0；此结果仅为修改后测试文件的静态类型检查。
- 新增真实模型调用：0；三轮六次真实调用证据未修改；产品时钟、产品延迟及其它轨文件未修改。
- 当时 Commit / push：NOT_RUN，按当时指令保留工作区修改。

第四轮任务已明确授权在本 worktree 的 `.runtime` 使用私有进程 TEMP/TMP 和全新 pytest basetemp，未修改全局配置、旧 pytest 目录或产品隔离检查。按此方式重跑 `tests/t2/test_rehearsal.py`：**7 passed in 105.30s**，包括正常与慢快照完整流程。对应 Windows CI 仍由集成验证；原三轮六次模型调用证据未修改。

## 第四轮：EvoMap Gateway 执行器

功能范围依据主线 `84ede61:docs/PLAN.md`，当前授权依据为 `4467003:docs/PLAN.md`。本轨仅修改 `orchestration/**`、`tests/t2/**`、本报告；`.runtime/**` 仅保存不入库的本地测试产物。复用现有 httpx、Executor 协议、Proposal、task_workspace、validate_sample、LangGraph Runtime、SampleVerifier 与 LocalMetabolism，没有依赖或锁变更。

入口与凭据：

```powershell
# 仅获授权的 I / 协调者执行；由协调者在该 Python 进程环境预先注入 MORPH_EVOMAP_API_KEY。
# key 不作为命令参数、请求 payload 或模型上下文的一部分。
python -m orchestration.rehearsal --executor evomap --root "$env:TEMP/morph-rehearsal-round4-new" --mode auto --authorize-task repair --authorize-task recovery --tau-seconds 10 --stage-delay 2 --timeout 180 --max-tokens 20000
# 手动成员下线：将 --mode auto 改为 --mode manual；其余授权参数相同。
# 只读回放不需要凭据，不发请求。
python -m orchestration.rehearsal --replay "$env:TEMP/morph-rehearsal-round4-new/rehearsal.json"
```

`--executor` 默认为 `codex`，原默认 `gpt-5.6-luna`、CLI 参数及 `cli/` 证据目录保持兼容；选择 `evomap` 且未指定 `--model` 时默认 `evomap-gpt-5.6-luna`。共享 `RehearsalSnapshot` 增加 `executor` 与 `model`；历史快照缺少字段时按 `codex` / null 读取，不推断未记录的历史模型。V / I 继续直接消费共享类型。

`GatewayExecutor` 仅请求已确认的 `https://api.evomap.ai/v1/chat/completions`，使用 Bearer，禁止重定向与环境代理，不提供任意主机参数或工具循环。密钥只从 `MORPH_EVOMAP_API_KEY` 进程环境或构造器内存参数读取；持久化时不保存 Authorization，异常只记录安全类别，provider 回显的密钥会被脱敏并拒绝应用。自定义 transport 必须是 `httpx.MockTransport` 且声明 mock 来源；replay 禁止执行。

每个 execute 最多一个 POST，不对超时、429、5xx、UNKNOWN 或失败自动重试。请求为 `messages / max_tokens / stream=false`；输出 token 上限为 `min(RunConfig.max_tokens, 4096)`。完成响应必须提供严格非负整数的 prompt/completion/total usage 且总数相符，并检查实际总 token 及输出 token 预算。美元成本一律保留 null；配置中的美元限额不是硬计费上限。

超时边界：httpx connect/read/write/pool 分阶段 timeout 为 `min(config.timeout_seconds, 180)` 秒，**不是绝对请求截止时间**。持续到达的数据可能让总墙钟时间超出该值；HTTP 完成后再次比较已测时长与配置，超限不应用 proposal。STOP 在请求前和写入前检查，无法取消正在阻塞的 HTTP 请求；不声称在途即时取消或硬美元封顶。响应读入限制为 1 MiB。

应用前复用原路径隔离、Proposal 与 sample AST 限制；只接受正常 stop 的单一 assistant JSON proposal。缺 usage、拒绝、截断、工具调用、错误路径、未注入 Gene 的采用声明、STOP、预算超限均不应用，不进入下一新任务。有效 proposal 只产生 pending_review，最终成功仍由原外部固定 unittest 独立判定；真实 Gene 仍来自成功 proposal/source_attempt，采用仍通过原 adoption_reader 与 LocalMetabolism。

证据约定（repair、recovery 各自目录）：

- `gateway/request.json`：executor、来源、固定 URL/方法、run/attempt、实际无密钥 payload、有限 max_tokens、分阶段 timeout 及其限制、开始时间、max_requests=1；这是发送前的意图，单独存在不证明服务器收到请求。
- `gateway/response.json`：HTTP 状态或 null、响应 body（含 provider model/native usage）、安全 error_kind、HTTP 实际耗时、结束时间及 cost_usd=null；超时保留 UNKNOWN，不伪造成功或 usage。
- `gateway/proposal.json`：通过验证的共享 Proposal；保留 adopted_gene_ids 供原链路读取。
- config/result/events、独立 verification、SQLite 与 rehearsal current/history 沿用原目录。Gateway 不生成 `codex.jsonl`、CLI `command.json` 或伪造 CLI 事件；Runtime execute_intent 仍是通用执行意图。

本轮本地验证使用既有锁环境 `../morph-integration/.venv/Scripts/python.exe`。测试进程设置 `TEMP=TMP=<本 worktree>/.runtime/temp-gateway-20260922`、`PYTHONDONTWRITEBYTECODE=1`，每次使用全新 `.runtime/.../pytest-<GUID>`；不安装依赖、不写其它 worktree：

```powershell
$taskTemp = Join-Path (Get-Location).Path '.runtime/temp-gateway-20260922'
$env:TEMP = $taskTemp
$env:TMP = $taskTemp
$env:PYTHONDONTWRITEBYTECODE = '1'
& ../morph-integration/.venv/Scripts/python.exe -B -m pytest tests/t2 tests/t0/test_bootstrap.py tests/t3/topology -q -p no:cacheprovider --basetemp (Join-Path $taskTemp ('pytest-' + [guid]::NewGuid().ToString('N')))
& ../morph-integration/.venv/Scripts/python.exe -B -m mypy --strict orchestration tests/t2/test_gateway.py tests/t2/test_rehearsal.py
& ../morph-integration/.venv/Scripts/python.exe -B tools/typecheck.py
```

- Gateway 定向测试 `tests/t2/test_gateway.py`：**33 passed in 6.93s**。覆盖正常提案、真实 HTTP 结构（MockTransport）、注入/采用 Gene、凭据缺失、固定主机、mock 来源、错误状态/超时单请求、无效 usage/提案/采用/路径、STOP、token/墙钟预算以及复用整个彩排闭环。
- strict（orchestration 与两项修改测试）：**11 source files clean**；全包 strict：**53 source files clean**。
- T2 + 固定验收器 + topology 回归：**2 failed, 69 passed in 174.30s**。Gateway、新旧彩排与墙钟断言通过；失败是未修改的 `test_codex.py::test_no_progress_stops_subprocess_without_retry` 与 `::test_timeout_and_manual_stop_during_invocation`，均在原 `CodexExecutor._stop_process` 调用 taskkill 后的 `process.wait(timeout=15)` 抛出 `subprocess.TimeoutExpired`，不能宣称完整套件通过。
- 同一锁环境用一个自动在 3 秒后退出的本地测试子进程诊断 `taskkill /PID <该子进程> /T /F`，得到 `taskkill_exit=1`、`ERROR: Access denied`，随后自然退出。未更改进程权限或产品停止逻辑；该沙箱进程停止限制已交协调者，待 I 在获准环境复验上述两项。该诊断不属于路演成员下线证据。
- R 新增真实模型/API 请求 **0**；以上全部 gateway 请求均为 MockTransport，所有 fixture acceptance 保持 mock/not_run。第四轮最多两个真实 POST 由原 I 准备、协调者注入凭据执行；不会借重跑或换根重试消费预算。
- 第四轮真实 usage、真实 Gene/采用/归档、浏览器观察与对应 Windows CI：本轨 **NOT_RUN**，交 I / 协调者验收。原三轮六次调用证据只读保留。

协调者已确认本次沙箱 taskkill 限制，授权提交并推送带上述限制的候选，由 I 在获准环境复验；不修改原 Codex 停止策略、不扩大权限、不重复本机失败用例。精确 SHA 通过 Handoff 发送，当前候选不标记为全套验收完成；集成完成前 R 继续承担领域返修，不提前发送 worker_done。

前次提交阻塞（历史）：正常执行 `git add -- orchestration/gateway.py orchestration/rehearsal.py orchestration/rehearsal_models.py tests/t2/test_gateway.py tests/t2/test_rehearsal.py docs/tracks/rehearsal-runtime.md` 返回退出码 1：`fatal: Unable to create 'C:/Users/DW/orca/Morphogenesis/.git/worktrees/morph-rehearsal-runtime/index.lock': Permission denied`。当时未暂存、commit 或 push，HEAD 为 `652e3199d626f60b414b70ee523b5f9703d1e539`；它是本次候选的父提交，不是 Gateway 交付提交。六个候选文件保留于本 worktree，未改 Git 配置、权限或其它 checkout，阻塞通过 Orca 报告。

前一 dispatch 收尾（历史）：协调者确认当时权限问题已询问用户但尚未答复，要求保留六文件候选，以 **failed** 结束该次交付。上列六文件、现有分支与原会话全部保留；该次真实请求为 0，commit / push / 第四轮 live 均未执行。

## 用户授权后的同轨重试

用户已明确批准原 R/I 会话提交推送、集成复验及第四轮彩排，授权记录为主线 `4467003:docs/PLAN.md`。本次使用新的 dispatch，继续原 worktree、分支与完整六文件候选；上述权限失败为前次历史记录。仅按已授权范围执行本项目必要的单次沙箱外测试和 Git 操作，不修改全局权限、账号或永久允许规则；测试仍使用本轨私有 TEMP/TMP 和全新 basetemp。

重试验证：原锁环境的 T2 / bootstrap / topology 同一完整命令得到 **71 passed in 59.73s**（退出码 0），包含先前受阻的两项 Codex 停止测试，未修改其产品停止逻辑。产品与测试代码自前次验证后未修改，原 strict 53 源文件与 11 定向文件 clean 的结果仍对应本候选；本次新增真实模型或 API 请求为 **0**。提交推送后以 Handoff 交精确 SHA、入口与证据契约，由 I 继续集成与第四轮验收；R 保持领域返修 owner 等待反馈，不提前 worker_done。
