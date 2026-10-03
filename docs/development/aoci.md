# 核心开发 AOCI

本索引用于减少开发时重复定位当前 MVP 的稳定调用边界，不能作为科研执行依赖、授权、科学结论或完整 R1 验收。研究工具仍走原 ResearchService、TaskLedger、BudgetLedger 和 AssetStore；AOCI 不参与这些运行路径。

## 官方来源与本机接入

复用官方 [aoci-code v0.1.0-rc17](https://github.com/aoci-spec/aoci-code/tree/v0.1.0-rc17)，release commit `93d6ad5a87fd9624a51cae61b2134d33944501fb`，许可证 [FSL-1.1-MIT](https://github.com/aoci-spec/aoci-code/blob/v0.1.0-rc17/LICENSE)。本轮没有重新下载、复制二进制或安装系统 Python 包。

A Owner 实际核对版本与本机文件 SHA256：

```text
C:/Users/DW/orca/tools/aoci/v0.1.0-rc17/windows-amd64/aoci.exe
0.1.0-rc17 / 93d6ad5a87fd9624a51cae61b2134d33944501fb
4013002f49d66e2a3998c7b852a8d28d37052af2fc3328ba7fb45246a3c75c67
```

此前二进制包由 P 校验；本轮 A 只重新观察版本、文件摘要及实际 stdio serverInfo，不把这描述为重做上游签名、构建可复现性或全部功能审核。

本机执行官方 `aoci init --locale en-US --agent codex`，没有 `--hooks`。项目配置 `.codex/config.toml` 被 Git 忽略，实际配置为：

```toml
[mcp_servers.aoci]
command = "C:/Users/DW/orca/tools/aoci/v0.1.0-rc17/windows-amd64/aoci.exe"
args = ["--repo", "C:/Users/DW/orca/workspaces/Morphogenesis/morph-r1-research-1003", "mcp"]
```

这是 A worktree 的绝对路径，不能直接复制到另一宿主。旧 Codex 会话没有热加载，最初连接证据来自 A 自有私有解释器中的官方 MCP `ClientSession`，实际 initialize/list_tools/call_tool。2026-10-03 Orca 重启后的本 Run 已加载原生 `mcp__aoci__*` 工具，实际执行 rules、maintain、update_entry、overview 与 search，服务响应根目录和版本均匹配本 worktree。配置文件存在、私有连接成功和当前工作 Agent 原生工具可用分别记录。全局 HOME、认证、provider、PATH 没有修改；`.aoci/config.json` 的 AI 仍 disabled，没有模型端点或资料外发。

## 明确索引范围

本次只选择以下 10 个实际阅读并手工理解的源码文件。每个语义 Entry 由模型逐条编写 F/R/A/S，官方 Maintain 只发来源绑定，不通过模板、AST、导入列表或路径批量生成语义。

| 文件 | 开发问题 |
| --- | --- |
| `swarm/research/service.py` | FR-04 权限先过滤的 branch/dependency/reference 局部选择；discover/choose/claim；native 原预留接续 |
| `swarm/research/server.py` | 正式 FastMCP 的局部上下文、提案、选择与原 lease 工具 |
| `swarm/research/models.py` | 宿主项目 envelope、预算与 transient native 绑定；封闭 generated 配置边界 |
| `swarm/research/dynamic.py` | 宿主 Docker export 透传；原 generated Executor/ledger/asset 调用 |
| `swarm/research/knowledge.py` | 项目持久记录、来源关系、事件选择后截断 |
| `swarm/research/records.py` | 来源回链、条件、争议与未验证研究记录契约 |
| `swarm/research/policy.py` | research-v1 正证据份额、探索与可选分支限制（只读 C 领域） |
| `swarm/research/feedback.py` | 原可信事实重读、独立接受、生命周期历史（只读 C 领域） |
| `swarm/budget.py` | 原项目累计预留/结算、unknown 与不能跨片段重置（只读） |
| `swarm/task_ledger.py` | 原 locality/dependency/lease/fencing/未知效果与短事务（只读） |

Root `aoci.txt`、Meta `aoci.meta.txt`、Code `aoci.code.txt` 是官方初始化/治理支持资产，不是三个业务源码 Entry。默认 Meta 字典覆盖标签和 FRAS 协议；Root 只标识该 worktree，没有手造项目授权或系统完成证明。数据库 Volume 未启用，数据库实际 schema/运行数据也未索引。

规则以有限源码文件为精确白名单，其它路径默认 exclude；官方支持资产单独 index。测试、历史报告、锁文件、产品私库、UI、安装目录、generated executor/验证器/asset store 的内部实现及其它核心模块没有本次语义 Entry。R 中对未索引文件的引用只是重要调用关系，不能推出这些模块已全部阅读或覆盖。特别是 B 最新源码虽已普通合入并作为当前调用契约消费，不能把 A 的有限索引称为 B 所有隔离实现的全量索引。

索引 freshness 只针对上述明确范围。后续 I 组合有源码 delta 时，由原 Owner 按官方 Guide/Maintain 维护；不能用旧 hash 或旧安装结果证明新组合 fresh。其它路径在 exclude 下不会产生漂移提示，需普通源码检索补充上下文。

`aoci.code.txt` 的官方目录 section 和本机 MCP 配置绑定 A worktree 的绝对路径；本轮没有验证其它 checkout 的直接复用。进入 I 或其它 checkout 时须先用该 checkout 的官方 Guide/工具核对 Root、Volume、目录绑定、source 与 baseline，遵循实际返回的重新绑定或迁移步骤；未完成前不能称新组合 fresh。不能自行字符串替换目录、复制 runtime receipt 或以 P 的 human approval 代替本库治理。

## 日常维护与观察

从对应项目目录使用同一官方二进制，先读当前 Guide：

```powershell
& 'C:/Users/DW/orca/tools/aoci/v0.1.0-rc17/windows-amd64/aoci.exe' index agent guide --agent codex --json
```

初次官方 scan 建立来源 baseline；可写阶段通过正式 MCP 无参数 `aoci_maintain` 获取完整机器批次，再逐条阅读源码、手写完整 Entry，使用 `aoci_update_entry` 保留同一 `code_plan.batch_id`、candidate_id 与 source_sha256 一次提交完整批次。不能截取前缀、手写 baseline、伪造 receipt 或调整权限绕过守卫。最后执行官方 `verify`、`check` 和 Guide。

正常只读定位可用 `aoci_search(keyword=...)`、必要时 `aoci_get_entries(paths=...)`；它们不替代完整 Overview。Overview 如分块必须读完官方 cursor 链，真实观察 delivery 与 model attestation，不把部分正文或派生摘要当整库认知。稳定后需要优化已对齐条目时，使用官方明确的 `intent="cognition_optimization"`，重新读对应完整 Entry/源码/关系，提交完整替换或不变 Entry；不编造源码变更来制造增量证据。

官方行为依据 [cognition volumes](https://github.com/aoci-spec/aoci-code/blob/v0.1.0-rc17/docs/cognition-volumes.md) 与 [Managed Scope](https://github.com/aoci-spec/aoci-code/blob/v0.1.0-rc17/docs/managed-scope-and-budget.md)。真实 scope/维护/检索输出和首次失败保存在本机 `.runtime/aoci-core/`，最终结果在 `docs/tracks/r1-research.md` 后继章节记录。

2026-10-03 本轮收口实测：普通 scan 建立 13 个 fingerprint（10 业务源 + 3 官方支持资产），MCP 完整机器批次应用 10/10 Entry；Verify/Check/Guide 对齐且 `complete=true,next_action=none`。完整 Overview 实际传输两次，各 10 Entries、3 sections、约 2916 estimated tokens，无分块。两次 Challenge 均 10/10；最终 delivery confirmed、attestation pass、governance aligned、`current_system_cognition_reliable=true`，框架掌握为模型自评 90%，不是运行事实。

两轮相同 search 查询命中相同 Entries：`FR04` → service（1），`native` → models/service（2），`positive` → policy/service（2），`docker_export` → dynamic/models（2）。在两次 Overview 之间，仅按官方 `cognition_optimization` 的单对象机器批次将 knowledge 的规模标签 `PD8L` 校准为 `PD8M`（源码 374 行）；完整 F/R/A/S 和来源摘要不变，原子 replaced=1/remaining=0、无 warning。没有制造源码变更来伪装 source-drift 验收；未来真实源码增量仍须由 Owner 维护。

最终 requested-scope Index identity 为 `20cc06d43efd858321a49ad6a79235c7d020332c1a0979d620553df07ef9430c`，Composite 为 `2b20d17adec60e2e28a9f51d22502ce3cec7317d0430f972dab62b64b3596de2`。这些是官方机器事实，不是另建完成证明设施。首次 confirmation 因 version 使用错误返回 delivery incomplete，但同一 Challenge 的语义答案已 pass；按[官方 delivery 规范](https://github.com/aoci-spec/aoci-code/blob/v0.1.0-rc17/spec/public/aoci-overview-delivery-v1.txt)只补正确 `overview-delivery-receipt/v1` confirmation，语义答案未重试，原 incomplete 日志保留。

工具自己的 `estimated_tokens` 只描述估算索引大小；本轮没有真实模型 token 用量或前后对照，实际 token 消耗与节省比例均 UNKNOWN。不据检索成功声称效率百分比、完整 MVP/R1 或真实科学能力。

## Git 与运行边界

初始化恢复历史完整保留在 `.runtime/aoci-core/failed-init-preserved-20261003T051653763Z/`，包括旧 `.aoci` 与三个 support 文件；没有删除旧 ledger/receipt 或修改 baseline 绕过守卫。旧 `scope-support-activate.json` 为 exit2 `managed_scope_source_guard_snapshot_changed`，后续 Guide 的 `recovery_pending`、官方 rollback、policy-bound auto apply、explicit observe review apply 均保留。root 在 `msg_a13825ef12b7` 明确授权一次仅本轨自有未跟踪 0Entry 初始化保留归档后重建；该动作在恢复检查点前已完成，本 Run 未再次归档/init。恢复比较记录证明 managed_scope、cognition_budget、automation 三项完全相同。本轮从普通首次 scan 继续，最终 pending_transactions=0、recovery_pending=false、third_party_conflict=false。

官方 `.aoci/.gitignore` 只允许正式配置、baseline 与 curation，运行 Ledger、事务、批次和 receipts 保留本机；`.codex/config.toml` 也不提交。原仓库没有 `.gitattributes`，本轮保留官方 LF 规则并标识区块，没有原例外被移除，没有 `git add --renormalize` 或批量重写历史源码/证据。既有 CRLF 使用官方 line_ending_tolerance，不改已安装字节或原 installed 字节门。AGENTS 的 init 行尾产物经 root 核对后按其明确指令恢复原 Git blob；原 backup 保留并作为本机 init 产物忽略，不提交。

AOCI 是离线开发工具，本次不执行 Docker/WSL、真实沙箱、模型科研、外部科学资料抓取/上传、云或部署。AT-07、L2 仍 NOT_RUN。产品 P 的人类 TTY 审批配置、baseline 和受保护文件不在本 worktree 初始化/复核范围，也没有复制或修改。
