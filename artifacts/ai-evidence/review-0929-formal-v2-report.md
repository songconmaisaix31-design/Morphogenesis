# FC-E 正式 deepseek-r1 v2：已取得响应，门禁未通过

**结论：REJECTED / FC-E OPEN。** 这是真实 deepseek-r1 的一次正式评审响应及 G 的机械接收记录，不是 Codex 代评，也不是“未发现高危”。主控 `msg_9cce787460cd` 已确认暂拒收并要求完成治理封存；不改通过本地验收的代码候选，不追加调用。

## 请求与原始证据

- 唯一代码候选：`c552250c0d07f5f70f09eb0a5ab3c322195e34ec`。
- 输入范围：完整 `348cf8d..73e64cc` + `73e64cc..C552` 核心生产 diff、必要最终源码、七个完整测试；[输入索引](review-0929-formal-v2-input.md)、[原始输入 content](review-0929-formal-v2-input.json)、[完整 diff 对照](review-0929-formal-v2-input-check.json)。288865 bytes / 288741 字符；发送前 exact tokens unknown，未将体积误称 token 计数。
- 复用原 `decentralized-swarm/.runtime/fc-auth` 的 headless profile/patch、provider `dashscope-fc`、原凭据路径和 DashScope endpoint；执行使用原 dsh 安装内 OpenAI SDK **6.40.0 / Apache-2.0** 的单次 chat completion，配置解析复用 **yaml 2.9.1 / ISC**，不启动 dsh agent 工具循环。
- 主控 `msg_3a5321683756` 确认 I 六绿后提交。提交 `2026-09-29T11:16:12.290Z`，返回 `11:18:39.393Z`；进程 exit **0** 只表示取得响应。
- configured_model / returned_model 均为 **deepseek-r1**；finish_reason=**stop**；fetch_calls=**1**，maxRetries=0，max_tokens=16384，tools 未提供，redirect 禁止，SDK logging=off。
- 实际 provider usage：prompt **71611**，completion **4642**，total **76253**，其中 reasoning **2930**；provider 返回 cached_tokens=0，这是实际字段，不是补零。**费用/真实账单 unknown**，不由 usage 推导成已结算。
- [调用记录](review-0929-formal-v2-call.json)、[完整 provider response](review-0929-formal-v2-response.json)、[原始正文](review-0929-formal-v2-raw.txt)。原文、usage、模型、响应 ID 均保留；未输出凭据，未自动重试或第二次请求。

## v2 机械校验：2 PASS / 2 INVALID / 4 待验证

原文结尾有孤立的代码围栏，不是严格 JSON-only 输出。用 Python 标准 JSONDecoder 从开头解出首个 JSON array，末尾 residue 明确为 `\n` 加三个反引号；[items](review-0929-formal-v2-items.json) 只提取原条目，没有改写引用、行号、类型或观点。

```text
C:/Users/DW/orca/workspaces/Morphogenesis/morph-fc-integration-0927/.venv/Scripts/python.exe -B artifacts/ai-evidence/review-0929-formal-v2-verify.py artifacts/ai-evidence/review-0929-formal-v2-items.json --output artifacts/ai-evidence/review-0929-formal-v2-verification.json
```

真实校验 **exit 1**；[逐条结果](review-0929-formal-v2-verification.json) 保留，不通过修改原引用换绿。

| 原条目 | 机械结果 | 接收边界 |
|---|---|---|
| f1 `budget.py:230` | PASS | 仅引文相等；其 content 把 unknown effect 停止概括为行为结论，超出本函数的直接实现，不能以 docstring/文字相等证明所有配置下的停止语义 |
| f2 `budget.py:213` | PASS | 能支持“该函数读取指定 reservation 持久行”的代码观察，不证明系统预算不超支或模型账单已结算 |
| f3 `task_ledger.py:365` | **INVALID** | 指定起始行不是其引文的函数头；整条作废，不能支持外部请求计数推论。G 备料的真实函数位置为 :358，但不替模型修正条目 |
| f4 `fault_observations.py:100` | **INVALID** | 指定起始行不匹配 after_recovery 引文；整条作废。G 材料实际入口 :104，不能将此另行核对追认为原条目通过 |
| h1–h4 | NOT_RUN（hypothesis） | 均保留“待验证”，没有自动变成事实；h2/h3 引用的 f4 已作废 |

## 风险假设和拒收理由

| 条目 / 模型原严重度 | 原命题与当前边界 |
|---|---|
| h1 / medium | unknown rejection hold 可能影响后续预算容量；属于 H1 预算 A/B 要求手推的前提，保留待验证，不把保守占额本身当成违反不变量 |
| h2 / **high** | “探头令牌 fencing 可能在进程崩溃/重启时出现竞争”；没有具体失败交错，仅指向无效 f4。已立即向主控上报；是高危标签的待验证假设，**不是已确认代码缺陷** |
| h3 / low | “序列号检查可能无法捕获同时间戳的新事件”；引用 f4 无效。D 已有 equal-time 独立行为/mutation，但这不排除所有可能的交错或替模型补足论证 |
| h4 / medium | 认为“5xx 含拒绝体归 UNKNOWN”可能是错误；**与用户本轮要求 5xx/transport unknown 优先于欠费/配额正文冲突**，不采纳其暗示的削弱方向，不改生产语义 |

D 在同候选的旧 token、精确 TTL、同 owner、并发单 executor、跨进程与 equal-time 场景已通过独立检查，可供 H1 参考；它不把 h2/h3 的所有可能风险穷尽排除，更不替代正式 FC-E 的完整论证。

除两项 INVALID 外，原稿没有逐项覆盖五不变量：累计预算/全部真实请求计数/失租提交/全候选有界退出没有形成完整评审意见；breaker 四态矩阵、假绿清单也缺完整逐项结论。输入完整不等于输出审查完整。因此不能登记 FC-E 通过或“无高危”，不能用 Codex 补稿冒充同一次模型输出。唯一调用额度已用；本轮不补第二次调用。

H1/H3 仍 unsigned，T6 merge/tag/三连冒烟及入口/演练保持 OPEN/NOT_RUN。I 六门禁及 D 五项本地验收通过与本报告拒收分别登记；FC 整体 BLOCKED、未冻结，不能宣称全系统稳定。
