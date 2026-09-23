# Decentralized Swarm v0.2 一页计划

本轮任务书及后续“用 Orca CLI 多 Agent 并行开发，尽量参考可复用成熟库代码”优先。基线 `605cf48b8b05baf86fd68e5d63f495ba3e5d7e69`。仅开发/推送 `decentralized-swarm`，工作树 `C:/Users/DW/orca/workspaces/Morphogenesis/decentralized-swarm`。冻结主线工作树以及 `docs/ACCEPTANCE.md`、`docs/PLAN.md`、`docs/STATUS.md`、`docs/tracks/**` 全部只读。决赛仍使用主线。

为同时满足单分支和并行要求，本轮采用同一隔离工作树内的互斥路径所有权，替代历史每轨各开分支的规则。三个业务 Worker 并行开发，Git 提交/推送须先向主控申请串行时段，只暂存自有文件；不得 `git add .`。主控只写本计划、SWARM_TASK、SWARM_STATUS。业务领域修复归原 Worker。全部完成后独立 I 在相同分支复验，只写 `docs/SWARM_REVIEW.md` 和必要集成胶水；不合并主线，不创造无意义合并。

| Owner | 独占 write_paths | 阶段与验收 |
|---|---|---|
| A 资产库 | `local_assets/**`, `tests/swarm/test_assets*.py`, `docs/SWARM_ASSETS.md` | M1：SDK 内容地址兼容、静态扫描、隔离试运行、ValidationReport、晋级/隔离；首先交付接口，再完成测试 |
| B 局部环境与预算 | `swarm/__init__.py`, `swarm/models.py`, `swarm/pheromone.py`, `swarm/router.py`, `swarm/lease.py`, `swarm/budget.py`, `metabolism/decay.py`, `metabolism/service.py`, `tests/swarm/test_field*.py`, `tests/swarm/test_router*.py`, `tests/swarm/test_lease*.py`, `tests/swarm/test_budget*.py`, `docs/SWARM_ENVIRONMENT.md` | M2/M3/M4/M6：持久化局部信号、抽样与管道、TTL 文件租约、预算先行；只抽取既有衰减公式，保持旧代谢行为 |
| C 自主运行 | `swarm/worker_loop.py`, `swarm/observer.py`, `swarm/hub_mirror.py`, `swarm/cli.py`, `swarm/__main__.py`, `tests/swarm/test_selfgrowth.py`, `tests/swarm/test_worker*.py`, `tests/swarm/test_observer*.py`, `tests/swarm/test_mirror*.py`, `pyproject.toml`, `tools/typecheck.py`, `tools/check_distribution.py`, `docs/SWARM_RUNTIME.md` | M5/M7：实际离线闭环、只读观察器、可选镜像；等待 A/B 实际接口后接线；预算测试通过后才运行自主循环 |

三轨均可读全库，不得写他轨路径。`.venv`/`node_modules` 仅 A 负责初始化，其他 Worker 等待环境就绪，避免并发安装。测试进程局部设置 OPENBLAS_NUM_THREADS/OMP_NUM_THREADS/MKL_NUM_THREADS=1，避免既有大进程内存问题。不修改任何锁文件或上游 SDK/Proxy schema，不新增依赖来规避锁约束。复用来源/版本/许可证记入各轨 SWARM 文档。

阶段：P0 隔离与计划；P1 A 本地资产与 B 预算/环境并行，C 阅读文献并实现观察/镜像及验收准备；P2 M6 通过后 C 集成三 Worker 自主循环；P3 原 Worker 领域测试、全量 pytest、strict typecheck、build/SDK/分发；P4 独立验收与精确 SHA 双平台 CI。每阶段 SHA、时间戳、测试数写 SWARM_STATUS（引用已经存在的提交，避免自引用）。

必要决策：本地“mainline”指显式配置的非保护晋级工作树/运行目录，绝不是被冻结的 `codex/morphogenesis-mainline`；晋级器必须拒绝保护分支/路径。隔离 worktree 不等于 OS 安全沙箱，文档如实记录。运行态共享环境采用 SQLite 和文件租约，不增加中心调度/Attempt/Manifest/哈希/证明设施。所有 Worker 只读局部信号与自身管道历史；observer 的全局读视图不得传入 Worker。预算不明/未知外部效果保留 unknown 并停止后续自主开销，不补造零费用。镜像默认关闭，不在本轮自动调用生产 Hub 或付费模型。

验收：`tests/swarm/test_selfgrowth.py` 断网、无主控、3 个独立 Worker 完成至少 5 个真实本地修改的觅食→执行→验证→晋级→反馈循环；无调度回调分配任务；重启恢复信号/租约，含崩溃 TTL/旧持有者安全释放；fake 高消耗触发账户熔断使全群休眠。测试模拟执行器只算 contract_local；真实文件/进程行为据实列明，interface_live/task_live 不因此变绿。全量类型覆盖新增包；现有 Ubuntu/Windows CI 两平台均绿后才可称候选验收通过，主线仍不合并。
