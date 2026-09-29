# G 治理与正式评审协调记录 · 2026-09-29

**当前封存结论：五项 C552 本地验收完成；正式 deepseek-r1 响应取得但 v2 门禁 REJECTED；FC 整体 BLOCKED、未冻结。** H1/H3 unsigned，入口/演练 NOT_RUN。下文按阶段保留真实过程，早期“等待 SHA/尚未调用”仅为当时状态；最终状态以本文末与 [正式评审接收记录](review-0929-formal-v2-report.md) 为准。治理文档 SHA、D 报告 SHA 均不能替代共同代码候选 SHA。

## 阶段一：配置定位与备料

Owner 为 codex；本文件不是 deepseek-r1 评审。治理分支 `morph-fc-governance-final-0929` 从 C 单轨 `e6ac45ffefc171a7215f8db19bc4a28af24ec4fc` 创建，**不得将本分支 HEAD 当作 A+B+C 测试候选**。共同候选 SHA 尚待主控转发；I 六门禁和 D 独立验收尚待原日志核对。FC 未冻结，H1/H3 unsigned。

已读 AGENTS、QWEN、docs/source 当前索引、FC_ACCEPTANCE、FC_CLOSEOUT_0929、FC_E_REVIEW_PROTOCOL_V2、FC_REMEDIATION_0929 与原 H1 材料。用户本轮授权五项生产修复，覆盖早先 cost_state“未授权”限制；本 G 轨仍无生产、测试、Schema、AGENTS/SWARM/锁写权。

### 已定位的既有配置（仅安全元数据）

路径前缀 `P=C:/Users/DW/orca/workspaces/Morphogenesis/decentralized-swarm/.runtime/fc-auth`。

| 检查 | 2026-09-29 当前观察 |
|---|---|
| CLI | `C:/Users/DW/AppData/Roaming/npm/dsh.ps1` → 已安装 `@deepseek-ai/dsh`，版本 `0.1.5-rc.3`，MIT |
| 原 launcher | `P/launch-dsh.ps1`，接受 PromptFile；子进程设置 `DSH_HOME=P/dsh-home`，运行 `dsh --profile headless --patch P/dsh-dashscope.patch.yml` |
| 隔离 profile | `P/dsh-home/profiles/headless/package.json`：bundles 为 `@deepseek-ai/dsh-base` 与 `@deepseek-ai/dsh-headless`，patchReload=startup；cordis.yml/cordis.patch.yml 是空层 |
| provider / model | `dashscope-fc` / `deepseek-r1`；DashScope OpenAI-compatible endpoint；只证明配置，未证明返回模型或 provider 当前可用 |
| 重试及额外调用 | patch 配置 `maxRetries: 0`；`session-title-llm`、`web-search-deepseek` disabled；仍加载通用 `llm-retry`、compaction、subagent/tool 插件，不推定完整调用边界已落实 |
| 单模型能力声明 | contextWindow=131072，maxTokens=16384，reasoning=true；是配置值，不是总调用/费用上限 |
| 权限 | 原 launcher 设置 danger-full-access；工具配置包含文件/Pwsh。本次只读，不把配置存在当作工具真正执行成功 |
| 本 Dispatch | DSH_HOME 初始未绑定；临时仅在检查进程绑定原 home，完成后恢复，不修改全局配置 |
| 正式评审状态 | **NOT_RUN / BLOCKED**：共同 SHA 未到；尚缺整次评审可验证的请求/费用边界。前次字面工具标记/连接错误仍未由成功工具证据消除 |

只读命令：`Get-Command dsh -All`、读取上述明确路径的安全字段、`dsh --profile headless --help`（exit 0）、临时绑定原 DSH_HOME 后 `dsh --profile headless --patch P/dsh-dashscope.patch.yml --dump-config`（exit 0）。dump 只输出白名单字段，未输出凭据。官方已安装 README 明确 dump 不启动 profile；未执行 launcher、未读凭据内容、未安装、未模型调用。

现有 Run `run_e46ee274f7c9` 已核对；没有创建新 Run 或重复评审。历史 FC-E `ctx_20b51afb27b6` 为 failed，不能把旧重试当成当日成功。原 `fc-e-spec.txt` 只有错误停止/不重试要求，未给整次请求或费用上限。已向主控回报具体路径与缺项；不是重新索取“是否允许评审”。配置查找在这些已知目录内结束，不继续全盘探索。

### v2 执行准备与停止条件

范围固定为原 FC `348cf8d..73e64cc` 加主控共同候选增量。逐项覆盖五不变量、breaker 四态矩阵/token/TTL/recovery 水位、unknown_effect 持久任务隔离、本次 reservation 费用语义、5xx 分类、假绿清单。

正式条目只接收 `hypothesis`（状态“待验证”）或 `fact`（完整 40 位 SHA、file:line、逐字 quote）。短机械脚本 [review-0929-formal-v2-verify.py](review-0929-formal-v2-verify.py) 读取指定 git blob；引用不相等即 INVALID，不支持结论。引用 PASS **只证明文字存在，不证明推论成立**。Codex 生成的 H1 引文必须标为备料，不能成为 deepseek 评审意见。

调用仅在共同 SHA 与可执行的有界配置齐备后进行一次；provider 错误、未知付费效果、字面伪工具输出、缺少正式报告时停止，不自动重试、不降级引擎。真实返回模型、profile、调用结果、provider usage 若不可得就写 unknown/未采集，不能用 0 或 null 冒充成功。若边界仍缺，封存 BLOCKED 及可交付材料。

### 待收齐的证据

- 主控共同不可变 SHA，A/B/C 输入 lineage、remote、clean、paths。
- I 在该 SHA 的 focused/full/strict/build/官方 SDK/分发六门禁命令、exit 与原日志。
- D 独立验收报告 SHA 与实际行为/失败/恢复日志，分别区别 Owner 自验。
- H1 新位置逐字材料、H3 candidate/未采集语义、入口/演练 NOT_RUN 依赖，见 [人工复核包](../../docs/FC_HUMAN_REVIEW_0929.md)。
- TASKS、CLOSEOUT、本轮 remediation 状态与桌面 0929 章节在证据收齐后封存；保留历史失败和桌面 0928 原文件。

阶段一验证：`git diff --check` exit 0；指定既有 integration-0927 venv 的 `python.exe -B` 对引用脚本执行六个机械控制（正确行、尾随空格错误、错行、短 SHA、越界行、hypothesis），6/6 符合预期、exit 0。控制仅绑定 C 基线的 QWEN 首行，不是正式评审或共同候选测试。阶段一仅新增本报告、H1/H3 包、短引用脚本。

## 阶段二：共同 SHA 备料（尚未发出模型请求）

阶段一提交 `bfbc0845b538661ab2a3fd3375a4713defb3c7ac` 已 push，远端同 SHA、当时 clean。主控随后明确共同代码候选 `c552250c0d07f5f70f09eb0a5ab3c322195e34ec`，分支 `morph-fc-candidate-0929`；本轨 `git ls-remote` 核对一致。其父为 B 合并 `5cf2612c04a34dfb17af12af817ebee8c08432dc` 与 C `e6ac45ffefc171a7215f8db19bc4a28af24ec4fc`。本轨未合入生产增量。

主控消息 `msg_c3507f7bbc6d` 将既有授权具体化为最多 **1 次模型 API 请求**、maxRetries=0、输出≤16384、不启 agent 工具循环/自动第二轮；可复用现有成熟 SDK 与原模型/凭据/endpoint。`msg_d86174518fd5` / `msg_ae59dec7c8bc` 明确必须等主控六门禁全绿通知才能提交，故不是收到 SHA 即调用。

- [单次脚本](review-0929-formal-v2-call.cjs) 复用 dsh 已安装的 **OpenAI SDK 6.40.0 / Apache-2.0** 与 YAML 解析器；从原 patch 校验 provider/model/endpoint/maxRetries。仅在正式发送时读原 launcher 所用凭据路径，绝不输出值。一次 SDK chat completion，省略 tools，maxRetries=0、max_tokens=16384、timeout=600000；拒绝 redirect 与第二次 fetch。调用前以排他创建保存原始意图证据，失败/未知效果停止，不自动重试。不是新调度或 Attempt 系统。
- 原 dsh help 未提供已核实的单次无工具模式；复用 SDK 是主控明确允许的同 provider 适配，不是 Codex 代评或切换模型。dry-run 的 `submitted=false` 是本地控制事实，费用仍 unknown，usage 未采集。
- [官方 Model Studio 模型页](https://help.aliyun.com/en/model-studio/deepseek-r1) 检索显示 context=131072、max input=98304、max output=16384；原 profile 能力声明一致。输入限制采用更保守的 **95000 UTF-8 bytes**；本地未安装精确 tokenizer，tokens 不冒充已测。
- [精确输入包](review-0929-formal-v2-input.md) 本地实际 **94486 bytes**（包括 CRLF），含 `73e64cc..C552` 完整 swarm/orchestration 生产增量 diff 和逐行标注的 budget/Worker/breaker/task_ledger/failure_chain/fault_observations 片段。其余纳入/排除路径在输入包中逐项列明。原 `348cf8d..73e64cc` 核心 diff 单独为 **110195 bytes**，连同必要代码无法装入该保守包；完整旧 diff、完整测试、lease keeper 与 executor/transport 内部等未入模型，**coverage=PARTIAL**，即使收到报告也不能宣称整个原 FC 范围无高危/解除 FC-E 锁。
- `node --check review-0929-formal-v2-call.cjs` 与无发送参数的 `node review-0929-formal-v2-call.cjs` 均 exit 0；未读凭据、未发网络请求。H1 21/21 exact-blob 引用 PASS（指定 Python，exit 0）；Schema 与原已验收 318dd 的 blob 同为 `ecf43b4f705bc8733af90751bbae6c9f0cf6fb29`。H1/H3 仍 unsigned。

桌面保留基准：0929 文件原长 **8277 bytes**，原 SHA256 `D6B2195FA9B8F3635AFC96AF0E691CB7F0138A0F51F05B08EA5EC9F674A2DF52`；0928 原文件 `Morphogenesis_项目改动整合_2026-09-28.md` SHA256 `FBD02354C818A9770E6E4329B75CCA738658604B677D6BA959D77B614B2C36DF`。最终只追加/维护 0929 本轮章节，核对原前缀与 0928 原字节未变。

### 输入边界纠正（主控 msg_ba90b5f88eed，正式请求之前）

上述 95000-byte 缩包方案已撤回、未调用；它是 G 自选代理限制，**不是 provider token 限制，110195 bytes 也不等于超 98304 tokens**。按主控明确要求，完整生产范围恢复后再准备唯一请求。未安装 tokenizer，exact tokens 仍 unknown。

当前正式输入为 **288865 UTF-8 bytes / 288741 Unicode 字符**，防误传体积上限改为 **300000 bytes**；服务端 max_input=98304/context=131072 才是 token 约束，max_output=16384 不变。包内含完整 `348cf8d..73e64cc` 核心生产 diff（110195 bytes）、完整 `73e64cc..C552` 生产增量（30063 bytes），均 `git diff --unified=3 -- swarm orchestration`、无缺失 hunk。补充了必要最终源码行号、全部三个 adapter 与 lease 文件，以及以下七个完整最终测试：unknown_effect_recovery、reservation_cost_state、probe_lifecycle_recovery、rejection_classification_boundaries、rejection_runtime_boundaries、failure_chain_boundaries、failure_chain_runtime。其他测试全文、未选中的不变源码、文档/锁/前端内容不在评审包，明确列出范围，不称全仓审查。

脚本 dry-run 与 `node --check` 重新 exit 0；当前输入未调用模型。若服务端拒绝长度或发生未知远端效果，原始错误保留、停止且不重试，不再缩包第二次调用。此纠正不改变六绿前不得提交的依赖。

输入载体调整：完整 Markdown 直接复制 Git diff 时，`git diff --check` 报原源码继承的 trailing whitespace（真实失败，非产品门禁）。为保留逐字代码而不清洗源文，改为 [input.json](review-0929-formal-v2-input.json) 的 `content` 字符串，经标准 JSON 一次解码后提交；input.md 只作为范围索引。第一次 Python round-trip 自检遗漏 UTF-8 参数，Windows 默认 GBK 抛 UnicodeDecodeError；显式 UTF-8 后重新核对两个完整 diff 字符串、输入字节数均通过，exit 0。SDK dry-run、最终 `git diff --check` 均 exit 0；这两项本地材料错误未触发模型请求。

## I 共同候选六门禁：已核原日志

I 于 19:15 转发最终结果，主控 `msg_3a5321683756` 于 19:16 明确六绿并允许唯一正式调用。G 读取六个原日志及 final-verification，独立比较精确 archive 与 I 测后 source 的 **346 文件**均原字节相等。原日志以标准 JSON 字符串原文保存在 [I 证据](fc-remediation-governance-0929-i-evidence.json)，包含来源绝对路径、命令、SHA、原退出码、时间及最终 I 报告；没有将此读回检查称作 G 重跑六门禁。

所有门禁绑定 **C552**，源码位于 I `.runtime/candidate-src`，Python 为既有 integration-0927 `.venv/Scripts/python.exe`；TEMP/TMP 在 Python 启动前绑定平级 `.runtime/test-state`。build 仅进程内复用已有 Poetry 2.5.0 后端缓存，SDK 复用已存在 1.14.0；分发仅离线安装本候选自建 wheel 到新目标，不安装第三方依赖或修改锁。

| 同一候选的实际命令 | 结果（I 执行，G 核日志） |
|---|---|
| `python -u -m pytest -q tests/orchestration` + 日志所列 Worker/预算/熔断/任务/租约 focused 文件，`--basetemp=../test-state/focused -p no:cacheprovider` | **408 passed / 2 warnings / 278.45s / exit 0**；无 skip/deselect |
| `python -u -m pytest -q --basetemp=../test-state/full -p no:cacheprovider` | **862 passed / 2 warnings / 589.58s / exit 0**；无 skip/deselect |
| `python tools/typecheck.py` | **87 source files / exit 0** |
| `python -m build --no-isolation --outdir ../dist` | **新 sdist+wheel / exit 0** |
| `node tools/check_sdk.cjs` | **SDK 1.14.0 schema/asset ID/tampering 通过，published=false / exit 0** |
| `uv pip install --python <既有venv> --offline --no-deps --target ../wheel-site ../dist/morphogenesis-0.1.0-py3-none-any.whl`；`python -I tools/check_distribution.py --site-dir ../wheel-site --check-node` | **install 0 + checker 0；13 packages、resources、installed verifier、Node check 通过** |

两项 warnings 为原 budget 非法 model_copy（nan/string）预检夹具，未过滤。它们不是模型 usage 或费用。I final-verification 的 HEAD/remote 为 C552、PORCELAIN_LINES=0、diff-check/remote/source-byte exit 均 0；I 没有提交后续文档或变异测试候选。原 B full **47 failed / 656 passed / 7 errors / 2 warnings / exit 1**、B/C 缺 Poetry 后端 build exit 1、A 首修 1 failed/117 passed、各 Owner 初始复现和 mutation 红/恢复绿全部保留；新六绿不是重写旧失败。历史 protected_runtime_state 18 failed/2 passed、T3 两次假绿与 Schema 原 8/9、11/12 也未追认为通过。

本次是 `contract_local`，不能扩写为蜂群 `interface_live/task_live`。唯一正式 FC-E 模型请求是独立评审调用，不是业务 live 验收；于主控通知之后 11:16:12Z 提交，SDK 日志显式关闭，结果另记。

## D 独立验收与材料来源

主控 `msg_186bd179e3ff` 转发 D 最终 `9a6705c7aeae9c812329c015f13e440842beff17`，分支 `morph-fc-independent-final-0929`；G `git ls-remote` 核对同 SHA，读取 exact report blob、focused-final 原日志和两轮 mutation 原 summary。D **47 passed / 73.71s / exit 0**；已接受的前两对加短目录恢复后的七对共 **9 组 red_exit=1 / restored_exit=0 / byte_restored=true**。D 原 equal-time 恢复失败 `git_operation_failed:worktree`、Git `$GIT_DIR too big` exit 128 及短路径修正后的复验均保留，不能把那次恢复红写成绿。

- [D 报告原字节副本](fc-remediation-governance-0929-independent-report.md) 来源 `9a6705c7aeae9c812329c015f13e440842beff17:artifacts/ai-evidence/fc-remediation-independent-0929-report.md`。原文内未带超链接的 D evidence/script 名称仍相对于原 D 树；完整原证据在 [D 原文证据 JSON](fc-remediation-governance-0929-d-evidence.json)，脚本可从该 SHA 读取，本轨未改写它们。
- [I 最终报告原字节副本](fc-remediation-governance-0929-integration-report.md) 来源 `C:/Users/DW/orca/workspaces/Morphogenesis/morph-fc-candidate-0929/.runtime/fc-remediation-integration-report.md`；I 报告不是 Git 提交，所测 candidate 固定 C552，六原日志另存 I evidence JSON。
- D 464 旧函数/1558 assert/decorators 保留、同候选 collect 862/旧 54 失败节点仍在、I/D 346 源码及 wheel/安装目标 83 Python 文件一致为 D 执行证据；G 核读原报告/证据，未冒称自己重跑 D 行为或 wheel 门禁。

真实限制：DashScope 完整生产 executor **NOT_IMPLEMENTED**，其真实 adapter 已测，完整 HTTP→executor→Worker 证据属于 EvoMap；无晚到 uncertain→settled 对账/自动解锁/未知 hold 释放，新旧混合部署及生产历史状态迁移未验证。Windows 深临时路径限制保留。独立第一代应用 `morph-readonly-app-0929@621f588988899bdbc7c7a83e893369c4145d89b3` 仍独立；C552 仅 FC 共同候选，不称全项目主线统一。

## 正式评审和最终门禁边界

真实 returned_model=deepseek-r1、finish_reason=stop、一次 fetch；prompt71611/completion4642/total76253（reasoning2930），费用 unknown。四个 fact 中 **2 PASS、2 INVALID**；四项 hypothesis 待验证，原 h2 high 已立即上报但无具体交错且引用无效，不是确认缺陷；h4 与用户要求冲突。原始模型输出没有五不变量完整逐项评审，**v2 校验 exit 1 / FC-E REJECTED**。主控 `msg_9cce787460cd` 明确维持拒收，禁止追加调用、生产返修或以 G/Codex 补稿代充。详见正式报告，原响应与所有错误引用保留。

H1 21/21 引文只作 AI 备料，预算 A/B、四态矩阵、fencing、TODO 新位置、六点和上述风险均待真人复核；H3 1.0.0 optional+nullable candidate 未采集、不补 0、unsigned/未冻结。T6 merge/tag/三连冒烟、T9 采集接线、T10 演练、T11 原入口条件、长期运行、生产发布/冻结仍 OPEN/NOT_RUN。没有自动解锁、费用确认、未知效果重试或业务 live 调用。

## 治理交付与材料校验

本 G 轨的授权材料工作已完成，正式 FC-E 的 **REJECTED/exit 1** 是交付内保留的实际门禁结果，不编码成通过。TASKS 仅增加本轮五项附录；CLOSEOUT/REMEDIATION 仅增加本轮状态与索引；新 H1/H3 包、指定 evidence 前缀以及桌面 0929 本轮章节为全部改动范围。生产/测试/Schema/AGENTS/QWEN/SWARM/锁、原 H1 与 v2 协议无 diff。

指定 venv 的最终材料检查 exit 0，详见 `fc-remediation-governance-0929-final-check.json`：授权路径、原有三文档前缀、桌面 0929 原8277字节/0928原哈希、I/D报告原字节、H1 21条原引文、正式原条目未改且仍2INVALID、模型响应usage与一次fetch、26个新本地链接均核实。保存这些结果没有把引用相等当推论正确。`node --check` exit 0；模型脚本实际运行 exit 0仅表示响应收到；正式引用脚本的 exit 1 与拒收独立保留。

阶段提交均带 `Swarm-Agent: codex`：`bfbc0845b538661ab2a3fd3375a4713defb3c7ac`（配置/备料）、`8fd30f687fa9c95b204c5eaa1e0069fbe2559a6d`（共同SHA备料）、`f0fee3d11712851964de9608ce2fbd91f38d6aef`（正式完整输入）。最终治理提交、remote exact 与 clean 以本任务最终交付回执为准；origin 为 `https://github.com/songconmaisaix31-design/Morphogenesis`，不合主线、不打tag、不冻结。

## 预算 A/B 文档验收返修（基于 cb102af；原历史保留）

本次仅补 TASKS 本轮预算附录、H1 备料说明、本段、final-check 材料校验与桌面回执。用 `git show c552250c0d07f5f70f09eb0a5ab3c322195e34ec:<path>` 核当前行号，明确“C552代码核对结论（AI备料，不是H1签字）”：A 在新 request_id 及额度/attempt/burn 等允许时不因同任务 pending 冲突死锁（budget:179–181、248–249；worker_loop:757–758）；B 同一 unknown hold 无双计（budget:83、192–203、248–249），不排除上游实际超支。附录同时说明无晚到 unknown 转换（budget:268–272）、任务终结后的长期占额（worker_loop:795–803、994–998）、普通结算 lower usage 不返还承诺额（budget:295–301），并区分确认拒绝的 unknown 费用 hold 与 unknown_effect 故意持久隔离。H1 人工判断/签名及源 TODO 未改，用户对五不变量交叉核对仍待完成。

本次只核文档引用、授权范围和 diff，结果追加在 [final-check](fc-remediation-governance-0929-final-check.json) 的 `budget_ab_document_repair`；原材料校验记录保留。I 在 C552 的 focused408/full862/strict87/build/SDK/分发与 D `9a6705c7aeae9c812329c015f13e440842beff17` 的 47/9mutation 仅沿用既有证据，未重跑；没有追加模型调用或可选测试/分析。正式 deepseek 仍为唯一调用，2 fact PASS / 2 INVALID / 4 hypothesis，FC-E REJECTED；H1/H3 unsigned、FC BLOCKED 未冻结、T6 禁止执行状态不变。此前 `cb102af1ac85716176ba0a3cac603c3e7be373aa` 保留为本次父提交，最终新材料 SHA/remote/clean 以交付及桌面末尾回执为准。

## 2026-09-29 G续接：dsh / V4.1 Flash 替换预检回执

本轮起点`403909204c8b589d33943298e1cde0a2094bb15e`，唯一受评代码仍C552。用户已新授权dsh指定模型正式评审，不沿用旧R1额度限制；以上旧R1原文、INVALID、REJECTED与失败证据原样保存。

已使用安装内dsh 0.1.5-rc.3 / MIT及其原生配置/认证代码核实`DeepSeek-V41-Flash = deepseek-official / deepseek-flash`。原FC配置仍为DashScope R1，两个许可home及当前cwd标准认证文件与Process/User/Machine同名变量未提供官方路由凭据；真实阻塞是认证，未发模型请求。主控`msg_a077597131fd`明确一轮原生invocation/最多10分钟/零自动重试/有限输出，CLI无max-step/request只记能力限制，不新增硬一次HTTP门禁。

[具体交接及完整覆盖矩阵](review-0929-v41flash-report.md)、[预检证据](review-0929-v41flash-preflight.json)、[输入校验](review-0929-v41flash-input-check.json)已落盘：完整两段核心diff、22组原编号块和12份完整C552上下文，532215 bytes，tokens null，37维要求包括16格四态矩阵。模型原输出不存在，request_count=0、returned_model/usage/cost/review_exit=null；新验收exit2/NOT_RUN、旧条目对照exit1仍2PASS/2INVALID，不用Codex代评或补引用换绿。

本轮只追加TASKS本轮附录、HUMAN非签字槽、REMEDIATION状态、本报告，新增指定review前缀证据和一页发布计划；桌面只追加回执。I六门禁与D测试未重跑，生产/测试/Schema/原TODO/人工槽/AGENTS/SWARM/锁未改，主线/tag未动。H1/H3 unsigned，正式替换未完成，FC-E OPEN、FC BLOCKED；合并/tag/三连冒烟/入口演练与业务live仍NOT_RUN。最终材料校验见[final-check](review-0929-v41flash-final-check.json)，分支/remote exact/clean以最终交付回执为准，worker按failed而非假成功结算。
