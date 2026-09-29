# G 治理与正式评审协调记录 · 2026-09-29

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
