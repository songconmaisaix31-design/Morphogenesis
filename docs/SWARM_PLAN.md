# Decentralized Swarm v0.2 修正版一页计划

当前事实源 SWARM_TASK.md，替代旧规划冲突项。冻结主线 605cf48，续接实验检查点 e9a3836；唯一开发/推送分支 decentralized-swarm，工作树 C:/Users/DW/orca/workspaces/Morphogenesis/decentralized-swarm。不修改主线树、冻结文档、演示进程或部署。
按单分支并行要求，沿用同一隔离工作树互斥文件所有权。三个长期领域轨，最后独立 I；提交前申请串行 Git slot，显式暂存自有文件，不 git add .。主控仅写 SWARM_TASK/PLAN/STATUS。旧 Run run_78114f173f9d 的 A/B 已结算，C 因 terminal_missing failed；保留全部提交，恢复须检查真实进程。

| 轨 | 独占 write_paths | 修正版交付 |
|---|---|---|
| A 资产 | local_assets/**; tests/swarm/test_assets*.py; docs/SWARM_ASSETS.md | SDK不变；promote仅状态；隔离补丁应用独立；验证策略/实际执行边界；approved FETCH/适用/注入/采用 |
| B 安全环境 | swarm/{__init__,models,task_ledger,pheromone,router,lease,budget}.py; metabolism/{decay,service}.py; tests/swarm/test_{field,router,lease,budget,ledger}*.py; docs/SWARM_ENVIRONMENT.md; docs/SWARM_CONTRACTS.md | 先锁契约；SQLite WAL任务/租约/fencing/提交；任务与偏好分离；scope局部；w/概率审计；tau=86400；swarm预算 |
| C 自主运行 | swarm/{worker_loop,observer,hub_mirror,evomap_executor,cli,__main__}.py; tests/swarm/test_selfgrowth.py; tests/swarm/test_{worker,observer,mirror}*.py; pyproject.toml; tools/{typecheck,check_distribution}.py; docs/SWARM_RUNTIME.md | 先包声明/审阅；等A/B接口与底座通过再跑循环；经验消费/故障/续租/预算/恢复；只读observer和镜像四态；追加 EvoMap 模型 API 执行入口与有界算法实验 |
| I 独立验收 | docs/SWARM_REVIEW.md; tests/swarm/test_integration*.py; 明确Handoff的少量导入/类型/配置胶水 | 全量pytest/strict/build/SDK/分发/精确SHA CI；领域问题退原轨；不合主线 |

P0续接/认账 → P1 A/B共同确认接口、B汇总SWARM_CONTRACTS、C注册包 → P2 A资产与B安全底座并行 → P3 C连接循环及反例 → P4独立I完整验证 → P5精确SHA推送结算。接口变更先Handoff，不能各自猜测契约。

EvoMap 追加阶段文件交接：C 可独占 `orchestration/gateway.py` 的通用单次传输/解析窄提取、新 `orchestration/gateway_transport.py`（如需要）及 `tests/t2/test_gateway.py` 的对应回归；保留旧 sample/TASK 权限和 no-retry/usage/脱敏/STOP 行为。原 B 同一 Worker 继续核对真实请求 `unbounded` 准入契约与显式配置，原 A 保持资产/验证领域返修所有权。首轮受限数据算法题的参考答案由独立固定策略保存，不能发给模型；API 生成的数据候选不作为任意程序执行。复用路径也须真实经过 EvoMap，并把源资产内容、上下文、执行记录和验证后的实际结果关联起来。
沿用锁定.venv/node_modules，不升级依赖或改锁。测试子进程BLAS/OMP/MKL线程数1；领域测试可并行，全量由I串行，避免并发重型测试。产物仅实验树忽略目录，保留失败原件，不杀无关进程。
验收矩阵见SWARM_TASK；真实多进程/SQLite竞争与本地文件验证单列，fake仅contract_local。worktree不是OS沙箱，历史usage不是硬费用上界，历史远端回执不算本轮live。2026-09-24 用户追加要求授权测试/蜂群 Agent 用 EvoMap API 做算法尝试；C 完成本地检查点后继续接入，I 等新增入口稳定后独立验收。凭据和有效预算配置尚未具备的真实阶段保持not_run，不把本地通过当作任务终点。决赛之后另行决定是否合主线。
