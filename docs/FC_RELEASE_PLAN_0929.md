# FC 正式评审替换与发布前置一页计划（2026-09-29）

最新用户指令指定 **dsh + DeepSeek V4.1 Flash**；新授权独立于已封存的 R1 一次请求。唯一受评代码为 `morph-fc-candidate-0929@c552250c0d07f5f70f09eb0a5ab3c322195e34ec`（C552），源树只读。旧 R1 响应、拒收、所有历史失败不改写。目标顺序为正式 FC-E → H1/H3 人工复核 → 主控核齐条件 → 合并/tag/三连冒烟/入口演练；本计划不代理人类签字或授权越过门禁。

| 轨 / 固定 Owner | Worktree / Branch | 互斥 write_paths 与交付 |
|---|---|---|
| G / 原 codex 治理 Worker | `morph-fc-governance-final-0929` / 同名分支，起点 `403909204c8b589d33943298e1cde0a2094bb15e` | TASKS 本轮附录、本文、`FC_HUMAN_REVIEW_0929.md` 非签字槽、`FC_REMEDIATION_0929.md` 状态、`review-0929-v41flash-*`、既有 G report；ignored `.runtime/fc-v41flash/`；桌面 0929 只追加。核模型/凭据/endpoint/有界 CLI，备 C552 编号输入和机械引用检查，满足预检才运行一轮 dsh，记录实际原文及拒收/不足。 |
| E / 主控指定 release-preflight Worker | 固定独立 worktree/branch，由主控在派发回执登记；G 不代开轨 | 建议独占 `artifacts/ai-evidence/release-preflight-0929-*` 与本轨 ignored runtime，最终以主控派发为准；只读核主线/候选合并条件、冲突、入口/端口/凭据/预算/证据条件，向主控交接，不修改 G 文档或生产树。 |

G 不重跑 I 六门禁或 D 测试，不修改代码/测试/Schema/源 TODO/人工结论与签名/AGENTS/SWARM/锁，不碰主线/tag。E 此阶段仅只读 preflight，未获条件齐备的后续执行派发前不得 merge/tag/启动 live；领域问题交原 Owner。

验收分别登记：输入完整与精确引用、真实 dsh 模型调用、模型覆盖质量、H1/H3 人工审批、业务 `contract_local/interface_live/task_live`。引用相等仅证明文字相等；模型假设保持待验证，旧 h2 high 必须给具体交错/有效证据或明确未证实；5xx/transport unknown 优先级是用户约束。取得响应不等于 FC-E 合格，风险或覆盖不足仍 REJECTED/OPEN。

当前预检：dsh `0.1.5-rc.3` 内置官方目录将 `DeepSeek-V41-Flash` 映射为 `deepseek-official / deepseek-flash`；旧隔离配置仍为 `dashscope-fc / deepseek-r1`。指定官方路由凭据在本轮允许核对的来源中缺失，正式替换尚未发送；实际模型/usage/费用为 null，不能使用 DashScope 凭据猜测官方路由或以 SDK 替代 dsh。详见 [本轮预检与交接](../artifacts/ai-evidence/review-0929-v41flash-report.md)。

H1 预算 A/B、breaker 六点/五不变量签字与 H3 Schema 1.0.0 optional+nullable candidate 的采集/准入/冻结拍板均待用户。T6 合并/tag/三连冒烟、T9 采集、T10/T11 入口演练及业务 live 保持 NOT_RUN；发布锁不因本计划或本地六绿自动闭合。G/E 各自普通 commit + push、remote exact、clean、changedpaths/实际 exit 回执后由主控验收。
