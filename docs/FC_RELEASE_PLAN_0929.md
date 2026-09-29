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

## 发布预检与 T10 窄续接（最新有效；以上为原阶段计划）

本节更新当前分工和实际结算；以上原文、原权限与门禁是历史记录，不据其扩大本 Dispatch 写权。G 当前起点 `669b191bf41d3fa42e2ab34a2c1fa68d53498f49`；共同受测代码仍为 C552，治理 HEAD 不替代完整共同候选。

| 轨 / 固定职责 | Worktree / Branch 与当前事实 | 后续边界 |
|---|---|---|
| G / 原治理与 dsh | `morph-fc-governance-final-0929` / 同名分支；本次只写 `TASKS.md` 本轮附录、本文、`artifacts/ai-evidence/fc-release-status-0929.md`，桌面 0929 只追加 | 登记 E/T10 实际状态并一次 commit+push；本次无模型调用/安装/依赖动作。原 dsh Flash 评审认证 BLOCKED、请求 0、review NOT_RUN、FC-E OPEN；凭据/profile 信息未回复 |
| E / 发布预检已完成 | `morph-fc-release-preflight-0929@7347f5c1a7eaf0f5a3279c2db0ffb751a730792c`（父 `c1107b63911e44269b586a1252cb84836cdeacf3`）；主控已验收并 release，G 已只读核材料/远端 exact | [精确预检与 T10 六阶段任务单](https://github.com/songconmaisaix31-design/Morphogenesis/blob/7347f5c1a7eaf0f5a3279c2db0ffb751a730792c/docs/FC_RELEASE_PREFLIGHT_0929.md)；未执行三连/正式演练/live，不以预检补锁 |
| T10 / 原生 Qwen CLI 宿主已失败结算 | `morph-fault-drill-0929` / `feat/fault-drill`，HEAD 仍 `c552250c0d07f5f70f09eb0a5ab3c322195e34ec`、clean；`task_5a07cc5ef0f5 / ctx_f5dfba4a52b3` 已由主控验收失败并 release | 唯一产品写权仍 `demo/fault_drill.py`、`tests/swarm/test_fault_drill.py`，两文件均未生成；Qwen 0.24.6 原生调用 exit 1 / 无 auth type，实际模型/usage/cost unknown。没有 Codex 代写或新 commit/push，开发/自验未完成 |

E 原预检快照确认 FC 目标 `decentralized-swarm@73798cd6f05210f2bd9b1eebfd6f9f0dd6e842db`，C552 可快进，demo-build 无现存 tag，两次 merge-tree 无文本冲突；11 份旧回放只标 replay，59 树/refs 当时未发现 T10。这些是 E 指定 SHA 的历史快照，G 不重跑预检，也不把后来宿主启动当成实现完成。主控首次 remote TLS 失败及只读重试成功均保留。

T10 前一次 Orca `--agent qwen` 在 `agent_unconfigured` 前置拒绝，无 Task/树/终端；之后 Codex 宿主只启动已装 Qwen CLI并核验，其唯一原生 session 为 `45763f00-a28a-4a98-a800-06b82fba27bb`。认证前失败的 CLI `num_turns=0 / duration_api_ms=0` 不证明 provider 实测 usage 或零费用；实现、focused、typecheck、完整序列 CLI、避让测试、mutation 均 NOT_RUN。主控关于改派 Codex 的询问未获回复，不据此换模型；正式 dsh Flash 要求独立保留。

用户“继续”已授权 T10 隔离开发自验，无需等待 H1/H3 才开发；此次未完成的原因是 Qwen 认证，而不是重新索取开发许可。正式演练验收与发布仍等原三锁：共同候选门禁、可接受 FC-E、H1 本人签字；H3 是 Schema 采集/准入/冻结的独立人工条件。H1 预算 A/B、breaker 六点与姓名结论、H3 optional+nullable 1.0.0 candidate 拍板均 pending，普通“继续”不代签。

当前下一步由主控接收既有 Qwen 认证入口或用户明确的 T10 改派决定、dsh 原生 profile/认证信息与 H1/H3 结论；G 本轮登记不等这些答复。T6 merge/tag/三连、T9 采集、T10 正式演练、T11 课题入口、业务 interface_live/task_live 均 NOT_RUN；不冻结、不发布。C552 I 六门禁与 D 47 focused / 九组 mutation 保留原身份，不重跑或改标签。详见 [状态与材料校验](../artifacts/ai-evidence/fc-release-status-0929.md)。


## 2026-09-30 生产接线发布状态（G；第一阶段最新）

用户现已授权多 Agent 生产接线、合并/tag/三连/live；上文未改派/T10 未实现/H3 待冻结只保留为历史，不能再作为当前事实。H3 `decentralized-swarm@be4fb7a685e951c9e42d8dc0c7eeb900cb5518f1` 已由 David 于 2026-09-29 冻结 Schema 1.0.0（单文档，原 Owner 12/12 + 9 controls），不等于 H1 或生产验收。

A `cb0902395d4e1fa89390c67c1cdfb6cec1607b72`（production `1516d67b9b7d9316025533949b105fff36bc37c3`）、B `cbec0b31fc1e27bfee1b83bd84e1f34097c19a19`、C `1d7753957a982f1f67f29ffa02e8f064d4f67a41` 已交付且 release。A 最终 focused55/strict88/build/wheel 是 Owner 自验，6a 的888全量仅历史；B 的81/strict89/六阶段21行/mutation是 A6a+B 精确组合 Owner mock 自验；C 的10 controls+7配置检查仅离线预检。正式模型评审 NOT_RUN，不能填无高危。

I 固定 `morph-fc-production-integration-0929`，task `task_ee23e2bde40a` / 恢复 Dispatch `ctx_af144abe21c7`，正在合 H3+A+B+C 并跑最终共同 SHA 的独立门禁，**最终 SHA/结果待报告**。前次重启 failed/terminal_missing 保留；本树开工治理 `40577cb841e8d89c08e1336d7254c4ca7bb3984e` 及后续治理提交均不是受测代码。

用户已授权多 Agent 生产接线、合并/tag/三连/live；不是重新索取这些授权。执行仍须共同候选适用门禁、合格 FC-E 与 H1 三锁齐备；当前不可发布，G 不动公共主线/tag、不代签。主控已异步收取缺项，“继续任务”没有补齐本人结论、认证、live 目标/预算或 auto 路径选择。现有单任务 `orchestration.acceptance` 固定 Codex 样例，无 EvoMap/真实课题入口，exit0 可能仍 pending_review；不能冒充完整 live。未审计的计数不填0，未知实际 usage/费用保留 null/unknown。T9 GUI mock/队友消息、benchmark POLL_MS 及候选外 WIP 本轮未做。

G 先普通 commit+push 台账 checkpoint，随后仍在本任务接收 I raw 报告，核验实际 Git 身份/原日志后更新；I 返修/阻塞照实登记，不以文档绿补锁。当前 FC BLOCKED、整体未发布；H3 文档契约已经冻结，两者分别陈述。详见 [生产计划](FC_PRODUCTION_PLAN_0929.md) 与 [一页索引](../artifacts/ai-evidence/fc-production-status-0929.md)。
