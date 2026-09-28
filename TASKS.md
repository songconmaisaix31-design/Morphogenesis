# TASKS.md — FC 轮任务账本

## 2026-09-28 后继总控接手与暂停（10:38 CST）

总控 `codex/master-control`，Orca Run `run_e46ee274f7c9`，当前 coordinator
`term_f20e387c-dcb7-4bd1-97d7-bf6a5b446b9f`，generation=3。计划见
`docs/FC_DAY_PLAN_0928.md`。评审生产基线 `73e64cc70116ac658d85591d082c0684a4952c99`；
第一代根工作树 `f3feb7f` 与已有 SWARM_SOL_PLAN WIP 保持只读。

| 任务 | 状态 | Commit / Dispatch | 门禁与证据 |
|---|---|---|---|
| 接手计划 | 已提交 | f804fb1；Swarm-Agent: codex/master-control | git diff --check 通过；原 Run 已绑定，三轨互斥写权已登记 |
| T1 | 等待 H4，未派发修改 | 无 | FC_ACCEPTANCE 仍记三选一未拍板；已请求“选三只改文档”确认，没有以沉默代批准 |
| T2 | **拒收，待队长决定返修** | cd8f6c9641a666b0c9cd8d713490b5515e8b3240；task_e3bb4948bc47 / ctx_3981895d6cd4 | qwen3-coder-plus 实际工具活动；git diff --check 绿，内容事实不通过；push 120 秒超时，远端结果未知 |
| T3 | **按停止协议中断，未修改测试** | base 73e64cc；task_1821ef01c94e / ctx_93a537696020 | 原集成树现分支 fix/fcd-interface-alignment；基线 14 passed in 40.90s，不是修复验收；没有全量/strict/mutation 回执；Ctrl+C 后读回 PowerShell，工作区 clean |
| T4 / FC-E | **启动失败，无报告** | task_6d4cbad4ae30 / ctx_523fd9024082 | dsh 原生命令报 TRANSPORT: Connection error. 后回 shell；未生成 review-0928-integration.md；未知远端效果/费用，不自动重试；已请求同模型单次重发决策 |
| T5 | 人工材料已落盘，**晚于 10:30** | 本次治理提交，docs/FC_HUMAN_REVIEW_0928.md | 10:37 完成四态矩阵、fencing 摘录、六点清单；FC-E 意见槽明确空缺，不代签 |
| T6 | 冻结未执行 | 无 | 今日门禁、FC-E 无高危结论、breaker 人工签字均未齐；无 merge/tag/三连冒烟 |
| T7 | 未发射 | 无 | 纯分析任务尚未执行，不预判 category 消费结论 |
| T8 | 未完成草案 | 无 | 仅只读查看既有 FaultObservation 与 Rehearsal 模型；无 Schema 冻结 |
| T9 | 未执行 | 无 | 依赖 H3，未生成 mock、未向队友发送消息 |
| T10 | 未实施 | 无 | B 类演练实现需队长确认；T3 写权未交接，未碰 live 子进程 |
| T11 | 未完成 | 无 | 历史私有 DashScope Key 路径存在于既有 launcher；本日 E 连接失败不能当认证可用；云 profile/课题 workspace/彩排配置未核实 |

### 按队长格式上报：接口事实不一致

- 现象：T2 新产物将 `record_failure` 当作已有实现，并错误描述 retry 修复。
- 证据：`morph-fc-docs-0928/artifacts/ai-evidence/fcr-hallucination-case-0928.md`
  的 `cd8f6c9` 第 11–14 行引用实际 `_record_failure_fact` 来支持 `record_failure`；
  实际定义 `swarm/worker_loop.py:678`、调用 `:813`。`git show bbe9d77 -- swarm/worker_loop.py`
  明确把未定义变量 `retry` 改成 `retry_after`，参数名仍为 `retry_after_seconds`；
  案例却写成字段改为 `retry_after_seconds`。其“不同 provider 分类逻辑”也不是异构开发模型
  错误模式不相关的证据。该页不能验收，未合并或代写修正。
- 建议：保留原提交，由同一 qwen Owner 按精确 diff 返修并复验；生产代码仍只读。
- 需要队长决策：是否解除本次停止、恢复 T2 返修及 T3；另独立确认 H4 与 FC-E 单次重发。

### 终端与生命周期

三次本日启动使用既有原生 launcher。Orca 不识别其原生 agent，采用有权威 preamble 的
low-level dispatch，均如实记 unsupervised，不冒称进程受 Orca 管理。
E 已回 shell；T2 已结束，其结尾只有文本 `orcasend worker_done`，没有真正发送生命周期
消息；T3 经明确中断后回 shell。主控依据上述正向退出证据 abandon 三个本日 Dispatch，
保留终端、工作树、提交和原始记录；不伪造 worker_done。

原 Run 遗留四条邮件已复核：A/D 旧自报不是今日验收；C 旧 push 失败记录与原总控后来
“六分支推送”终端记录并存；R 旧 heartbeat 不是完成证据。今日 `git ls-remote` 再核实时
遇 `OpenSSL SSL_connect: SSL_ERROR_SYSCALL`，不宣称已实时核实所有旧分支远端。

H1 11:00–11:30 人工 breaker 复核材料已备；H2 12:15 提醒/12:30 报名、H3 16:00–17:30
拍板、药学 PhD 20:00 截止、课题提案收集、21:30 站会仍由队长执行。本会话未创建定时
提醒，不承诺离线后自动到点提醒。总目标 P1/P2 **未达成**。

## 充值后接续

进程内清除代理环境后 A/D/R 的 DashScope 实际模型与代码工具活动已恢复。
C 的 qoder dispatcher/resume 回合只返回旧测试仍运行的过期结论，未修复；
终端明确 CLI 已结束，stop_unknown 因外部终端而无法关闭；依据实际退出证据
abandon 旧 ctx_0df29cd2f91c、保留所有 WIP，同轨新 ctx_84ceea058c74。
原生 qodercli 通过 stdin 新上下文已实际读文件，返回模型标签 Auto，不冒称
Qwen3.8-Max。C 写权及 Owner 不变。R Codex 网络路由发现 turn.failed 且
没有领域代码，随后 R 首次领域实现改用原生 Qwen Code，ctx_27a0b1455ff1。

A 新提交 fc5b3934fed630c055a76fa6e3df83dc1b09f969 自报推送及25项定向/
类型通过，业务验收仍拒绝：独立合法 HTTP-date 返回 None，+3/1_0 被接受；
spawn 测试仅检查字段存在，未证明值或无秘密；parent ExecutionResult.metadata
丢失新 Reply 事实，且没有全量门禁。原 Owner 新 task_cba58721948f 接续返修。
R 自己工作树越界加了 evomap_executor.py 三行 Reply 字段，已明确退回撤销
仅自身改动；事实传播归 A parent parsing，不以合并解决领域所有权冲突。

2026-09-27 用户明确充值并要求完成总任务、更新桌面报告。原生 A/D 已基于新
Dispatch 接续原会话：ctx_63b12a67edf1 / ctx_07682b2d2cec；只在有实际模型/
工具回执后记开工。C 的 ENOSPC 后未返回请求经 Escape 取消，终端明确
Request cancelled，随后同 Owner/Dispatch 接续；先修 token fencing 与失败门禁。
新增隔离 FC-R 运行时领域轨，写权与接续条件见 docs/FC_PLAN.md；以完成用户总
目标为授权，不扩大原五轨写权。E 最终精确提交评审、I 独立集成仍在后续波次。

## 依赖申请区（五轨对 pyproject.toml/poetry.lock 只读，缺依赖在此登记，由队长批量执行）

| 依赖 | 所属轨 | 用途 | dev 组 |
|---|---|---|---|
| （空，待轨登记） | | | |

## FC-A 第 0 步探测记录（人类队长拍板 + AI 代跑核实，已固化）

结论：httpx 路线成立；live 请求走子进程；respx 仅能注入进程内路径；分类在子进程内完成。

证据锚点：

- `orchestration/gateway_transport.py:14` `import httpx`
- `orchestration/gateway_transport.py:43` `httpx.Client(transport=..., trust_env=False, follow_redirects=False, timeout=...)`
- `orchestration/gateway_transport.py:22-30` `GatewayResponse` 字段（无 Retry-After、无 raw body 字段）
- `swarm/evomap_executor.py:92-132` `_request()`（调用 `single_request`，进程内/mock 路径）
- `swarm/evomap_executor.py:135-149` `_child()`（`--request-child` 子进程入口，读 cred 文件后调 `_request`）
- `swarm/evomap_executor.py:209-224` `_send()`（live 走 `subprocess.run`；mock 走进程内 `_request`）

裁定：raw body 不出子进程；回传 `classification` + `evidence_hash`；FC-A 写权窄增补
`swarm/evomap_executor.py` 两处（见 QWEN.md [FC-A 写权扩展]）。

## FC-A 首次交付复核与返修（2026-09-27）

- 收到 worker_done：原 task_021476b9728f / ctx_908e3cf0b7a5，远端分支
  fc/failure-classify@e4396407e87e8745f8bfeff448343ecf6b6edd5f 已核实。生命周期
  completed/succeeded 仅是 Worker 自报结算，主控业务验收未通过；不集成。
- 该提交额外引入 uv.lock（3 行，基线不存在），违反锁文件/写权边界。由原
  Worker 在普通后续提交中撤销自己新增文件，不改其他锁文件、不重写历史。
- 最初工作树 Python 执行 tools/typecheck.py 失败：No module named mypy；
  随后原 Worker 真实终端回执已执行 Poetry install，84 源文件类型检查、
  tests/orchestration/ 的 19 项定向测试通过；尚无合格全量 pytest 回执。
- 独立只读复现：分类器接受 JSON null 抛 TypeError，message=null 抛
  AttributeError；_request 的非 UTF-8 响应抛 UnicodeDecodeError；HTTP 400
  Arrearage 的流在部分 body 后 ReadTimeout，Reply 却为 confirmed_rejection
  （uncertain=true）。均是进程内 MockTransport，无远端调用。
- 未实现 Retry-After HTTP-date/整数/未知解析；当前所谓 integration 测试仅
  进程内 _request 调用，无实际 spawn --request-child 回传证明。
- 返修仍归同一个 FC-A 原终端、worktree、branch。新 task_5853a2c3a4b9 /
  ctx_3993f67114a8；旧 Dispatch 已撤权，不复用旧身份。新 preamble 通过
  native Qwen Ctrl+Q 入队并读回“1 queued”；等待真正执行和修复回执。
- FC-C 仍由原 Qoder Worker 开发；FC-D/E 暂等 A 接口返修，最终集成未执行。
- 紧接原任务第二条 worker_done：19fe837b5aafdecfcc963ed90dc518071c9b6511
  仅删除 uv.lock（已推送终端回执），没有修复领域代码。本次独立执行工作树
  `.venv/Scripts/python.exe tools/typecheck.py`：84 源文件通过；
  `.venv/Scripts/python.exe -m pytest -q tests/orchestration`：19 passed in
  7.28s。上述已知缺陷与缺失需求仍阻止验收；第二条消息已读取并确认。
- 新返修 preamble 已从队列进入 native 模型新回合，屏幕读回完整新任务及
  processing 状态；不是仅记录终端输入接受。

## 最新并行开发与已知引擎阻塞

- 用户要求继续五轨并行开发及桌面报告。A 原会话达到 100 轮后保留 WIP、
  退出并原会话 resume，进程上限改 400；接续 ctx_b8e62d8a7999。D 首次
  Windows shell 配置错误后绕过 Poetry 执行全局 pip（原生记录可见安装了
  hypothesis/respx/time-machine 等）；立即停止，未盲目卸载共享包。随后
  launcher 设置 POETRY_VIRTUALENVS_IN_PROJECT=true，同一 D 会话 resume 到
  ctx_1bbdc67b67ba，实际执行 uv tool run poetry install；不以全局包为验收。
- A/D 分别真实返回 DashScope HTTP 400 账户状态异常/欠费拒绝。没有再次
  调用、创建替代 Key、充值或自动模型切换；两个 Dispatch 已 fenced/stopped，
  原工作树 WIP 保留，Task blocked。引擎替代选择已向用户提出，尚待答复。
- A 当前 WIP 的 subprocess 测试曾加 except Exception: pass，能吞掉断言；
  主控已中断该回合并退回修复。explicit mock child seam 已开始编写，但尚未
  最终验收。D 当前草稿存在 assert True/占位和错误账本调用，尚未测试、提交或
  接受，不能混为真实五不变量验证。
- E dsh/DashScope deepseek-r1 实际有模型与工具事件、provider usage，但首轮
  结束后没有报告文件或 Commit；末尾声称写入 $MARTIFACT_FILE$ 未由文件系统
  验证，且不按五不变量原文评审，未验收。ctx_588d14022e7e 已停止，不重发
  同一欠费账户调用。原 native session 与响应证据保留在忽略的运行目录。
- C Qoder 仍开发/验证；主控独立 strict 82 文件通过，尚等最终完整回执。
  欠费原因 A billing_arrearage / C arrearage 不一致已退回 C 对齐。
- 独立集成 worktree morph-fc-integration-0927 已按本轮计划创建，分支
  songconmaisaix31-design/morph-fc-integration-0927，基于治理提交 37b5b6b。
  没有集成 Worker 开工或领域合并，等最终领域交付。
- D 当前草稿独立 collect-only 失败：time_machine.travel 的字符串
  `2023-01-01 12:00:00 UTC` 不是合法 ISO 格式，no tests collected / 1 error。
  A 当前 WIP git diff --check 报 trailing whitespace；均未动原 Worker 文件。
- C 已收到主控反馈，真实终端确认 npm ci（工作树根目录）exit0，并正在补
  billing_arrearage 单样本真实 B 接口测试；旧未安装 Node 环境的全量结果作废，
  最终全量结果与原退出码另行留存。主控没有执行部署或模型任务彩排。
- A 欠费停下时的 WIP 独立 strict 检查：84 文件中 3 个错误（base.py 使用
  math 未导入，两处；mock_handler 缺类型注解）。未修复或宣称原定 19 项测试
  能代表当前 WIP。D 仅有三个 HTTP 故障夹具与 __init__.py，六夹具尚不齐。
- C 最新真实 B 联合回执 27 passed in 8.52s，包含 billing_arrearage 单样本
  立即熔断；当前正式全量仍运行。现有 Codex 的 login status 确认 ChatGPT
  登录，但仅做可用性核对，未在用户选择前替换 A/D 引擎。
- C 正式全量结束：569 passed、2 failed、1 skipped，781.42s；失败为
  demo_environment 的 sentinel/执行器参数与 t1 bridge MCP。tail 管道退出码
  不代表 pytest 退出码；已要求原 Worker 定向重跑留真实输出和退出码，不豁免。
- C WIP 独立复现同 Worker 探测隔离缺陷：A 于 t=1000 领取 token1，t=1060
  过期后同一 A 领取 token2；旧 report_probe_success(A) 被接受、state=normal。
  回传 API 未接收认领 token，不能隔离同一 Worker 的迟到结果；已退原 C Owner。
- 宿主 C 盘曾 free=0，Qoder 实际 ENOSPC，主控 apply_patch 失败将 TASKS.md
  截断。仅清理本次 py-spy 的 uv 缓存 4.9MiB，未删除其他文件；磁盘空间另有
  较大波动，原因尚未确认。TASKS.md 已从未改动的精确 HEAD 恢复，git diff
  证明恢复无差异，再追加本段。两条新领域文件长度正常，不能据此证明未受影响。
