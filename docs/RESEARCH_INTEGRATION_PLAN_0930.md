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

每轨一个 Agent、一个 worktree、一个分支，开发/测试/文档/返修持续同 Owner；阶段 commit + push。A/B/C 首个检查点交付薄接口 Handoff（启动 MCP 参数、实验计划/结果、科研准入），跨轨不写文件。集成 I 最后只合并并补少量导入/配置/类型/路由胶水，领域问题退回 Owner。

## 验收与运行边界

1. contract_local：真实既有账本路径拒绝陈旧租约；执行失败、产物缺失、复现失败、条件不匹配、unknown、外部会话不误杀。适用 pytest / strict / build / 分发与双平台 CI，首次失败保留。
2. interface_live：两种原生 Agent、MCP、官方 OpenSandbox 服务独立记录版本、调用/工具/会话/沙箱/日志证据；配置存在不等于支持。
3. task_live：紧凑公开 CPU 案例，Agent 自主发现认领续租，一方实验，另一方干净环境复现，判据准入，后续任务本地验证并实际 adoption，中断/接续/旧持有者拒绝；运行无需 ORCA。
4. 首批 live 仅此案例，最多 3 个原生研究会话（实验/复现/继承），每会话有时长与工具轮次上限；调用前 Owner/I 核实原生权限、现有授权与预算配置，缺少可信成本保持 unknown。不自动重试未知远端效果；首次未知停止该 live 路径。
5. 启动单机 Docker/OpenSandbox 与隔离 CPU 案例属于本轮授权范围；GPU 可选。正式复现干净沙箱/内核，探索可保留内核；大文件通过 SDK/存储，必要原始证据在沙箱关闭后保留。
6. 官方认证保持原状，不复制 HOME、不接管凭证、不绕过原生权限；缺条件写 blocked/NOT_RUN，继续其余实现与门禁。无 DSH 强制评审，无生产 Hub 发布、部署主线覆盖或新 tag。

当前状态：已核验基线与官方认证；三轨待启动，所有新验收项 NOT_RUN。最终只报告实现、分支/完整 SHA、命令/结果、真实限制、未执行/人工操作。
