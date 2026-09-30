# 异构 Agent 与科研环境集成一页计划

业务事实源：2026-09-30 用户本轮指令优先；现行包见 docs/source/README_包内说明.md。主控只分发、决策和独立验收，领域开发及返修由同一个 Owner 完成。

## 核验与基线

- 开发基线：origin/decentralized-swarm = ef77af603577d4539d8dbdf780e1536a369b0d12；foundation CI 36702905606 success。
- origin/main = 0e7826819c6780f637ff4049adfc61e8069638d9，最新为未验证 WIP 备份合并；本轮不采用、不覆盖。
- 原仓 codex/morphogenesis-mainline 的 docs/SWARM_SOL_PLAN.md 已有未提交修改，保留。
- Codex CLI 0.159.0 / Claude Code 2.1.238 已安装，官方登录检查通过；Docker 29.5.3 客户端存在，daemon 未运行；Ubuntu / docker-desktop WSL2 当前停止。此为前置事实，尚无 live 科研通过证据。
- ORCA 上游初始核验 SHA 85f8d6b5f507df795cd3cef1cdea08124cf801ee；OpenSandbox 089b59ad48af33fc2733de58bd1a39c687c93b0a。Owner 固定版本并核对源文件、依赖、许可证和测试，不以桌面产品为运行依赖。

## 模块映射

| 处理 | 模块 | 边界 |
|---|---|---|
| 保留 | swarm/task_ledger.py、lease.py、budget.py、failure_chain.py；contracts.identity；现有 local_assets 静态检查 | 事务、权限、续租、fencing、未知效果保守语义及既有身份复用；无新调度器/Attempt/Manifest/hash/证明系统 |
| 扩展 | local_assets 既有候选、验证、应用、adoption；新增科研服务调用既有账本 | 实验前版本化判据、独立复现、条件匹配、反例及实际采用；基础设施故障与科学负结果分开 |
| 新增 | orchestration/native_agents/、swarm/research/、orchestration/experiments/ | 原生适配和注册表、官方 MCP 入口、官方 OpenSandbox SDK 执行；产品不调用 ORCA |
| 替代本次路径 | 固定 sample.py 无工具提案 / fixture-only 科研入口 | 保留旧入口兼容性，本次使用 Agent 原生工具循环、主动发现认领和真实实验验证路径 |

## 固定所有权

| 轨 | Worktree / Branch 后缀 | 独占 write_paths |
|---|---|---|
| A 原生 Agent | morph-research-agents-0930 | orchestration/native_agents/**；tests/native_agents/**；docs/agents/**；docs/tracks/research-agents-0930.md |
| B 科研空间与 MCP | morph-research-space-0930 | swarm/research/**；local_assets/**；swarm/task_ledger.py（仅必要扩展）；tests/research/**；tests/local_assets/**；docs/research/**；docs/tracks/research-space-0930.md；README.md；THIRD_PARTY_NOTICES.md |
| C OpenSandbox / T0 | morph-research-sandbox-0930 | orchestration/experiments/**；tests/experiments/**；demo/research_case/**；deploy/opensandbox/**；docs/experiments/**；docs/tracks/research-sandbox-0930.md；pyproject.toml；poetry.lock；tools/typecheck.py |
| 主控 | morph-research-plan-0930 | docs/PLAN.md；本计划；docs/RESEARCH_INTEGRATION_ACCEPTANCE_0930.md（仅状态/决策/验收） |
| I 独立集成 | morph-research-integration-0930（待 A/B/C 冻结交付后启动） | 合并既有精确提交；tests/integration/**；docs/tracks/research-integration-0930.md；必要导入/配置/类型/路由胶水，领域问题退原 Owner |

每轨一个 Agent、一个 worktree、一个分支，开发/测试/文档/返修持续同 Owner；阶段 commit + push。A/B/C 首个检查点交付薄接口 Handoff（启动 MCP 参数、实验计划/结果、科研准入），跨轨不写文件。集成 I 最后只合并并补少量导入/配置/类型/路由胶水，领域问题退回 Owner。

## 验收与运行边界

1. contract_local：真实既有账本路径拒绝陈旧租约；执行失败、产物缺失、复现失败、条件不匹配、unknown、外部会话不误杀。适用 pytest / strict / build / 分发与双平台 CI，首次失败保留。
2. interface_live：两种原生 Agent、MCP、官方 OpenSandbox 服务独立记录版本、调用/工具/会话/沙箱/日志证据；配置存在不等于支持。
3. task_live：紧凑公开 CPU 案例，Agent 自主发现认领续租，一方实验，另一方干净环境复现，判据准入，后续任务本地验证并实际 adoption，中断/接续/旧持有者拒绝；运行无需 ORCA。
4. 首批 live 仅此案例，最多 3 个原生研究会话（实验/复现/继承），每会话有时长与工具轮次上限；调用前 Owner/I 核实原生权限、现有授权与预算配置，缺少可信成本保持 unknown。不自动重试未知远端效果；首次未知停止该 live 路径。
5. 启动单机 Docker/OpenSandbox 与隔离 CPU 案例属于本轮授权范围；GPU 可选。正式复现干净沙箱/内核，探索可保留内核；大文件通过 SDK/存储，必要原始证据在沙箱关闭后保留。
6. 官方认证保持原状，不复制 HOME、不接管凭证、不绕过原生权限；缺条件写 blocked/NOT_RUN，继续其余实现与门禁。无 DSH 强制评审，无生产 Hub 发布、部署主线覆盖或新 tag。

当前状态：三轨已按固定所有权启动；A已提交并核验真实前置探测，B/C正进行返修与适用门禁。首次OpenSandbox接口烟测FAILED，完整科研task_live与集成候选验收仍NOT_RUN。最终只报告实现、分支/完整 SHA、命令/结果、真实限制、未执行/人工操作。

## 继续开发检查点（2026-09-30）

用户要求继续既有任务，重点复用 ORCA 多 Agent 接入协议和官方 OpenSandbox。现有三轨、所有权及验收范围继续有效；只在已有实现上返修和集成。

- 原 Run `run_4d81d03a8550` 已绑定当前总控 `term_bdbac2dc-861f-4ba9-af30-f44bd35cc2d7`，generation=2。ORCA 重启后的原 B/C Dispatch 均为 failed/terminal_missing，Task ready；保留已交付源码及原失败，不把运行时恢复失败写成代码验收失败。
- A 固定候选 `648f43c54203f555b1b05827cfe119c8e3dfa622` 已完成原 Task；需要领域返修时恢复原 Owner。ORCA 固定来源、许可证、原模块行为对照、原生 argv/session/event/进程归属协议进入 I 独立复核。
- B 候选 `28dc6d0b4ff73edd6da7c27d8ef6f359b95bc126` 已 push、clean。恢复原 B 会话完成已知 effect、预注册计划、旧资产兼容性、案例初始化及适用门禁；原 missing-effect 失败断言继续保留。
- C 候选 `23417b09ffc93fbc432da0f63a7abec2546fd825` 已 push、clean；主控实际读取 CI `36717414791` 的 exact headSha，Ubuntu/Windows 全部门禁 success。恢复原 C 会话核对最终文档、服务归属和证据 Handoff；旧 `interface-c-0930-01` 失败保持不变，不重放。
- Python 验证串行进行，仅进程局部限制 BLAS 线程；不关闭他人进程/容器或修改全局资源设置。主控处理既有 FIFO 消息后 ack。
- B/C 交付后由独立 I 在新 Orca worktree 精确合并 A/B/C 及治理提交，只做必要胶水；源码固定后完成独立本地、双平台 CI 和已授权有界 live。缺少真实权限、资源或预算配置时只阻断依赖路径，其余实现和验证继续。

此记录为继续开发计划，尚未创建 I 或执行新 live；不预写科研验收、生产部署、主线覆盖或 tag 通过。

## 授权后接续（2026-09-30）

用户明确授予隔离开发全部权限，并要求完成原终端的原标准。已重新读取原会话 `01a0f066-d52d-7a62-956b-3b386373e8bb` 中完整八节任务，范围仍是独立异构 Agent 与科研环境集成，包含真实复现及实际经验继承。

- B/C 原审批请求以 Escape 取消，实际屏幕均记录 Conversation interrupted，随后精确 fence 旧 unsupervised Dispatch、关闭各自 PTY（ptyKilled=true）。无业务写入丢弃，无他人进程/容器操作。
- 同一原 Owner 会话以显式 `--sandbox danger-full-access --ask-for-approval never` 在原 worktree 恢复，仅开发进程。产品原生认证和权限契约保持原任务要求。
- B 当前 `ctx_e16666128554` / `term_3516bdc3-902c-4b75-ba47-a8ca3620b0e5`，C 当前 `ctx_054ccfdf62bf` / `term_c215414b-8849-4e7c-a0ca-b358cfb42fdf`；当前注入成功，unsupervised 放置仍如实记录。CLI 使用同一已加载技能的可执行文件绝对路径，不切换版本。
- B 独占当前 Python 验证窗口，修复已有四项 CI 失败并保留原断言；C 先收尾文档、诊断已有十二项本机失败、准备自有服务与 I Handoff，不重复实验或启动全量并发。
- I 尚未启动；待 B/C 冻结交付后按原标准验证两种原生工具循环、同空间主动认领续租、三份干净实验、独立判据、准入及实际 AdoptionReceipt、中断/同会话接续/陈旧 token 拒绝。上限三个科研会话、未知效果不重放，工程 CI 和真实科研通过分别判断。

最终 I 的研究调用窗口：最多三个原生研究 session 身份（作者、复现者、继承者）；每个身份累计 wall 上限 900 秒、观测工具上限 64 次，作者中断与明确恢复合计在该窗口内。此为实际调用前声明的观测停止条件，并非 Token/美元硬封顶；未知 usage/cost 保留未知，不以环境变量或认证状态推断额度。仅由 I 在冻结源码、原生权限与受保护科研状态确认后执行；任何未知外部实验效果停止依赖路径，原 invocation 不重放。
