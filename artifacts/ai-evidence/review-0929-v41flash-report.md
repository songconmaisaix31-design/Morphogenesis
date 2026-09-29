# FC-E dsh / DeepSeek-V41-Flash 替换预检与交接（2026-09-29）

**正式替换未完成：认证 preflight BLOCKED，模型评审 NOT_RUN，FC-E OPEN，任务按 failed 结算。** 没有模型响应，不能宣称审查合格或“未发现高危”。用户本轮授权有效，实际阻塞是原生认证缺失，不是要求用户重复授权；原生 CLI 的 step/request 参数限制另列，不升级为额外审批或绝对阻塞。旧 R1 原响应/报告及 REJECTED 保留。H1/H3 仍 unsigned，发布锁未闭合。

唯一受评代码 `c552250c0d07f5f70f09eb0a5ab3c322195e34ec`，源树 `morph-fc-candidate-0929` 只读；本轮治理起点 `403909204c8b589d33943298e1cde0a2094bb15e`，治理 SHA 不当作受测代码。启动时两分支均 remote exact，工作树 clean。

## 模型来源、原配置与原生认证

[预检原始结果](review-0929-v41flash-preflight.json) 由 [只读脚本](review-0929-v41flash-preflight.ps1) 生成，无秘密值。`dsh --version`、`dsh --help`、`dsh --profile headless --help` 均 native exit 0，版本 **0.1.5-rc.3 / MIT**。只读复用安装内官方代码，没有安装、修改全局配置或替换执行器。

| 项 | 已核实事实 | 证据边界 |
|---|---|---|
| 用户名称解析 | 安装内 `dsh-llm-deepseek/lib/index.js:1838–1850` 的 `DeepSeek-V41-Flash` → provider `deepseek-official` / ID `deepseek-flash` | 内置官方目录，不是联网模型可用性或实际返回模型 |
| 易混模型 | `:1852` 的 `deepseek-v4-flash` 是另一条目录项 | 未自动替换为 V4 Flash、R1 或其他模型 |
| 原 launcher | `decentralized-swarm/.runtime/fc-auth/launch-dsh.ps1` 使用其 `dsh-home`、headless、`dsh-dashscope.patch.yml`；原 permission mode 为 danger-full-access | 只读检查，没有直接复用其宽工具权限运行 |
| 原 patch/composed | configured `dashscope-fc / deepseek-r1`；endpoint `https://dashscope.aliyuncs.com/compatible-mode/v1`，retry max 0 | 原配置没有 V41 ID；不把原 DashScope 凭据送往官方 DeepSeek endpoint |
| 标准 profile | 原隔离 headless、`C:/Users/DW/.dsh` 的 headless/web 用户 patch 均空 `[]`；官方默认 bundle 为 `deepseek-official / deepseek-flash` | 没有发现已保存的替代精确模型路由 |
| 官方 endpoint | 安装实现 `dsh-llm-deepseek/lib/index.js:1993` 默认 `https://api.deepseek.com` | 是代码声明的默认地址；认证与在线服务未验证 |
| 凭据解析 | `dsh-credentials-local/lib/index.js:13–20`：Process env → `$DSH_HOME/.credentials.yaml` → invocation cwd `/.env` → `$DSH_HOME/.env` | 仅核对实现指向的标准路径，不广扫历史/日志/凭据库 |
| 实际缺项 | Process/User/Machine 的 `DEEPSEEK_API_KEY`、`DEEPSEEK_BASE_URL`、`DSH_HOME`、`DSH_SETTINGS_FILE` 均不存在；两个允许 home 的 settings.yaml/.credentials.yaml/.env 及当前 cwd/.env 均不存在 | 只输出存在性，不能推断机器其他未授权位置没有配置 |

主控已收到 `msg_fe425f064523` 和 `msg_6e5ecde8c394` 的具体 Handoff；按主控 `msg_ef73b17e0992` 补查原生解析及三层环境，不改用 SDK。随后 `msg_a077597131fd` 明确本轮是一轮原生 invocation、非 exactly-one-HTTP 限额，以下记录按此纠正。待主控/用户给出现有精确 profile 路径或该官方路由认证入口，凭据不进入 Git/消息正文。

## dsh 能力核查与剩余执行限制

真实 CLI 命令形状为 `dsh --profile headless --patch <isolated-overlay-path> <task-text>`；此处是已核实的语法形状，**不是已具备全部参数的可运行交付命令**。本轮没有执行模型命令，review process exit 为 null。

- 输出：原生 provider 支持 `maxTokens`（`dsh-llm-deepseek/lib/index.js:1894`）并发送 `max_tokens`，可设置有限输出；当前并未发请求，未宣称某个输出预算生效。
- 重试：原生 provider 接受 `retryPolicy`，`mode: normal / maxRetries: 0` 可禁止该重试策略；headless 本身不是单请求保证。
- 工具：loader `disabled` 可停具体工具插件；`tools.mode` 只接受 native/ptc/both，没有 `none` 模式。仅 read-only 不能限制工具轮数；新隔离组合的零工具/title/compaction/subagent 行为尚未实证，不能称限制已生效。
- 步数：headless 帮助只有 task/help，`headless-runner` 动态创建 Agent 时只传 provider/model（`:127–145`）；`agent-loop` 配置提供并行工具数和输出 tokens，没有显式 step/request 上限（`:1490–1503`）。实际循环 `:927–981` 与 `:1115–1119` 对工具回复可继续下一步。这是 CLI 能力限制，不是用户新增门禁，也不要求另行批准；按主控明确边界允许一轮 dsh invocation、retry=0、有限输出、禁用非必要工具/title/compaction、最多 **10 分钟**。超时终止后保留可能已发送/unknown，不重试；实际请求数无法证明时为 unknown，不能伪造为 1。
- 输入：本包 532215 UTF-8 bytes / token 数 null；headless positional task 不能直接承载普通 Windows 命令行的该体积。需要核实原生配置 task 读取/绑定方式，不截断输入、不用自建代理循环绕过。
- 实际模型：headless 输出最终文本；已读 `agent-loop` 中 session `source.model` 来自 request.model。未来须从原生证据核实实际服务返回模型和请求数，不能用 configured model 冒充 returned model。

以上区分“已见配置能力”和“尚未通过运行验证”；10 分钟 invocation 约束已经主控明确，无需为不存在的硬一次请求要求继续研究。没有为试探能力发模型请求，没有本地伪模型或付费小请求，没有 SDK 替代、自动重试、依赖安装、全局修改或自建调度器。

## 精确输入与覆盖矩阵

[输入 JSON](review-0929-v41flash-input.json) 的 `content` 是待提交原文，[生成器](review-0929-v41flash-prepare.py) 从 Git immutable blobs 只读构造，[机械结果](review-0929-v41flash-input-check.json) exit **0**：

- 完整 `348cf8d42719402a7a5fcc09595e5040f96fa5be..73e64cc70116ac658d85591d082c0684a4952c99` 与 `73e64cc..C552` 的 swarm/orchestration 核心生产 diff，各完整字符串恰好出现一次；没有删 hunk。
- 完整复用旧 v2 的数据正文（两个 diff、路径清单、七个完整测试、全部原片段），仅替换已失效 R1 指令前言。22 组原编号片段逐行核 Git；追加 12 份完整 C552 核心文件，去编号后还原原始 UTF-8 bytes，全 PASS。
- 额外附现有 D 报告并标为历史 evidence；不把 D47/九 mutation 或 I408/full862/strict87/build/SDK/分发说成 G 本轮重跑。模型不得声称自己执行了测试。
- 输出限两类：逐字 fact（完整 C552 / file:start_line / quote）或 hypothesis（待验证）。全部风险、无缺陷意见与结论是 hypothesis；每个 fact 起始行/原字节不符整条 INVALID，不事后修引用换绿。

[37 项覆盖清单](review-0929-v41flash-coverage.json) 是任务要求，**不是模型已覆盖**：

| 范围 | 要求 | 当前模型覆盖 |
|---|---|---|
| 五不变量 inv1–5 | 共用累计预算；未知 hold 不释放；真实请求计数；失租不提交；全候选有界退出 | 5 项 NOT_RUN |
| 五新增真实路径 repair1–5 | 已知费用 unknown 跨重启/handoff；TTL fresh token Worker 路由；恢复水位/equal-time 新故障；双 adapter 5xx/transport 优先；本笔 cost_state | 5 项 NOT_RUN |
| fencing / old_h2 / old_h3 / budget_ab / limitations | 具体交错与证据或明确未证实；预算 A/B；旧假设与新事实分离；缺失范围 | 5 项 NOT_RUN |
| 假绿 false_green1–6 | catch 吞断言、mock 生产、只测预算、弱化/删除/skip、字段无语义、mutation/恢复无效 | 6 项 NOT_RUN |

| 四态 × 事件 | aggregate | cooldown_expired | probe_success | probe_failure |
|---|---|---|---|---|
| insufficient_evidence | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |
| normal | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |
| suspended | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |
| probing_recovery | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |

旧 h2 high 未提供有效具体失败交错，仍为未证实假设；本次缺响应，不能称已排除或确认新 bug。5xx unknown 优先是用户约束，旧 h4 不得当作反转约束的理由。输入有源码不等于输出有评审覆盖。

## 实际结果与验证

本轮 **request_count=0、submitted=false、returned_model=null、usage=null、cost=null、review_exit_code=null**；零请求是本轮未提交的实际计数，不是伪造 usage=0 或免费账单。没有 raw model output，因此不创建空“模型报告”伪装响应，输出原文明确 **ABSENT / NOT_RUN**。

验证均使用既有 `C:/Users/DW/orca/workspaces/Morphogenesis/morph-fc-integration-0927/.venv/Scripts/python.exe -B`：

| 命令 / 结果文件 | 真实 exit / 结果 |
|---|---|
| `review-0929-v41flash-prepare.py` | **0**；532215 bytes、22 原编号块、12 完整最终文件、37 维 |
| `review-0929-v41flash-verify.py review-0929-v41flash-raw.txt --output review-0929-v41flash-verification.json` | **2**；[NOT_RUN_NO_RESPONSE](review-0929-v41flash-verification.json)，37 维未获得模型输出 |
| 同一 verifier 只读输入旧 `review-0929-formal-v2-items.json`，输出 `review-0929-v41flash-legacy-control.json` | **1**；[旧样本对照](review-0929-v41flash-legacy-control.json) 仍 2 fact PASS / 2 INVALID / 4 hypothesis 待验证；不是新模型审查 |
| `git diff --check` 与最终授权路径/历史前缀/人工槽/旧 R1 bytes 检查 | 以 [最终材料检查](review-0929-v41flash-final-check.json) 及交付回执为准；不替代行为门禁 |

Shell 探索中两次 PowerShell foreach 后直接管道解析错误 exit 1，以及对不存在的安装文件路径读取错误已纠正为实际路径；均在本地发现阶段，未触发模型请求。材料脚本首轮误写旧 v2 文件数为12，assert exit 1；`git ls-files` 实际枚举11份后修正该检查并重跑，不涉及产品代码/测试或模型原引用。原 v2 所有响应/引文/拒收文件不变。

需要后续完成：核实用户既有原生认证/profile，按已授权的单次原生 invocation / 最多10分钟 / 零自动重试 / 有限输出执行 review；大输入绑定、实际 token 及原生返回模型证据仍是运行前核对项，未宣称 532KB 必然可用，也不删必要 diff 冒称覆盖。真实输出按上述 protocol 机械验收，再核完整覆盖及风险；不预写接受，不改用 SDK。H1/H3 用户签名/拍板、E 的只读合并与入口条件、T6 merge/tag/三连冒烟、T9/T10/T11/业务 live 均独立未完成。计划见 [两轨一页协调计划](../../docs/FC_RELEASE_PLAN_0929.md)。
