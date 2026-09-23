# Decentralized Swarm v0.2 状态

## P0 隔离与计划

- 2026-09-23：只读核验主线 HEAD `605cf48b8b05baf86fd68e5d63f495ba3e5d7e69`，工作区干净。Orca 创建独立 worktree `C:/Users/DW/orca/workspaces/Morphogenesis/decentralized-swarm`，分支精确为 `decentralized-swarm`，基线相同。
- 三个业务 Worker 互斥路径并行，同分支串行提交；独立 I 最后验收。当前业务测试数：0（尚未运行）。
- 验收状态：contract_local=not_run，interface_live=not_run，task_live=not_run，双平台 CI=not_run。主线不参与任何写入或推送。
- 已核对复用点：`hub_client/assets.py` 委托官方 NodeAssetBridge schema/hash；`metabolism/service.py` 指数时间衰减；`orchestration/gateway.py` 有界单次响应/usage 解析；现有 `.github/workflows/check.yml` Ubuntu/Windows 矩阵。
- 真实边界：工作树隔离不等于 OS 沙箱；本地预算不能承诺上游不提供的在途硬封顶；无计量/未知效果须停止后续花费。Hub 镜像实现和本地验证不意味着生产 Hub 资产晋级。

## P1 并行开工（2026-09-23T22:04:30+08:00）

- 计划提交 `fc29680cc793071ff620bab1ae261f07d01233ae`（2026-09-23T22:02:17+08:00）已推送 `origin/decentralized-swarm`；业务测试 0，尚未执行。该提交 CI 运行 `35871276925` 正在运行，不作通过声明。
- Orca Run `run_78114f173f9d`；A `task_28fdad4925e1 / ctx_a4f7bdea3bd2`，B `task_80a341e94c40 / ctx_e80c740a94d7`，C `task_1883ba1c5300 / ctx_4474e18dc2b4`。三者实际 transcript 已显示读取/实施动作，liveness=live；非仅 input_accepted。
- A 负责唯一环境初始化；B 先交预算门禁；C 在门禁前仅做独立准备。主控只做计划、状态、决策、验收和串行提交协调。
