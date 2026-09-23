# Decentralized Swarm v0.2 任务与不变量

用户任务时间 2026-09-23 21:56，9/24 中午封板；决赛演示固定用主线。当前分支从 `605cf48` 拉出，所有工作只在 `decentralized-swarm`。

目标：由主控星型派发改成环境沉积信号、Worker 局部觅食、自主执行和反馈的 stigmergy 群体；主控只读审计；Hub 可选且离线全循环可用。环境（信息素场和本地资产库）是唯一 Worker 协调通道；局部相邻信号、管道历史和自身能力决定行为；成功正反馈，失败负反馈和挥发配对；预算熔断先于自主运行。O(n) 是协调结构目标，不冒充未经测量的运行时复杂度证明。

M1 `local_assets/store.py` 复用 `hub_client/` 和 `bridge_node/` 已验证 GEP envelope/官方 SHA-256 地址（4938bb9），保留 asset_id 和 PUBLISH/FETCH/REPORT 语义；不得另写哈希规范。`validate.py` 静态语法、危险模式、声明边界与实际 blast_radius 一致性检查，随后隔离 worktree 有界 dry-run，产生含 node_version/arch/platform 的 ValidationReport。`promote.py` 仅将绑定通过报告的原候选晋级到显式本地非保护工作树；失败保留隔离区及原因。不得改/删 hub_client。

M2 `swarm/pheromone.py` SQLite/JSONL 持久化恢复，信号 error_pattern/timeout_storm/retry_flood/opportunity 对应 repair/optimize/innovation。更新 sigma_next=(1-rho)*sigma+delta；lambda=0.05，复用既有代谢指数衰减，明确时间尺度和 rho 换算，不复制第二套衰减。

M3 `swarm/router.py` 管道 w_next=0.95*w+0.05*r，r 来源成功/加速/省 token。局部任务按 softmax(beta*浓度*能力匹配*紧迫度) 加权抽样，不取 argmax。能力矩阵与自身管道历史均有效参与决策；只读自身工作区半径内信号，避免全表读后伪装局部。

M4 `swarm/lease.py` 文件锁+TTL，包含 worker_id/到期时间；同 scope 静默跳过，过期可恢复。并发 acquire/renew/release 必须有原子保护；旧持有者不能释放新租约或过期后继续晋级；父子/别名 scope 冲突需覆盖，不能靠中心仲裁。

M5 `swarm/worker_loop.py` while energy>0 and budget_remaining: sense(local); weighted sample; acquire lease or continue; execute isolated; validate; passed→promote+positive deposit, failed→quarantine+negative deposit; audit result/report/env_fingerprint; release in finally。异常、无任务、竞争跳过均须有界退出/休眠，避免自旋。审计身份使用现有 Pydantic AttemptId，不创建自研 Attempt 基建。

M6 `swarm/budget.py` 必须先于 M5 接入：每任务默认 max_tokens=20000；Worker 单位时间 burn rate 超限休眠；账户累计消耗超过 --max-cost-usd 折算值则全群休眠并持久化现场。真实 usage 解析复用网关规则，可配置输入/输出单价本地估算，明确估算标签。未知 usage/cost 不能当零。并发预留和结算须原子化，先计量即使验证失败；不能用事后检查宣称上游在途硬封顶，无可靠边界的执行器不得启用无人值守。

M7 `swarm/observer.py` 只读场、租约、审计、ValidationReport 输出健康视图，不依赖旧 orchestration 派发器；旧模式完整保留。`swarm/hub_mirror.py` 复用 4938bb9 官方直连适配，只镜像本地已晋级资产，异步可选，离线/失败不阻塞循环，未知写效果不自动重试。

算法先读全文并记录来源与适用范围：
- https://arxiv.org/abs/2010.09280 The Capacity Constraint Physarum Solver
- https://arxiv.org/abs/2009.01498 Physarum-Inspired Multi-Commodity Flow Dynamics
- https://arxiv.org/abs/2103.00172 A Survey on Physarum Polycephalum Intelligent Foraging Behaviour and Bio-Inspired Applications
- ACO 信息素沉积/挥发模型、stigmergy 环境记忆（用户提到 nottldr，但未给精确 URL，优先可核查原始论文）。

该实现是任务书指定的离散启发式，不能套用原文连续系统的收敛定理。当前库 metabolism 使用 exp(-elapsed/tau)，tau 不是半衰期；允许只抽取共享 helper 并保持旧行为。旧 topology 默认 lambda=0.1，本轮 swarm 明确为 0.05，不改旧默认。

测试与纪律详见 SWARM_PLAN。锁文件、保护文档、hub_client/、bridge_node/、旧 orchestration 均只读。每阶段 commit+push 开发分支，禁止主线 push/merge，禁止 force。所有真实限制和未执行人工步骤如实结算。
