# Decentralized Swarm v0.2 状态

## P0 隔离与计划

- 2026-09-23：只读核验主线 HEAD `605cf48b8b05baf86fd68e5d63f495ba3e5d7e69`，工作区干净。Orca 创建独立 worktree `C:/Users/DW/orca/workspaces/Morphogenesis/decentralized-swarm`，分支精确为 `decentralized-swarm`，基线相同。
- 三个业务 Worker 互斥路径并行，同分支串行提交；独立 I 最后验收。当前业务测试数：0（尚未运行）。
- 验收状态：contract_local=not_run，interface_live=not_run，task_live=not_run，双平台 CI=not_run。主线不参与任何写入或推送。
- 已核对复用点：`hub_client/assets.py` 委托官方 NodeAssetBridge schema/hash；`metabolism/service.py` 指数时间衰减；`orchestration/gateway.py` 有界单次响应/usage 解析；现有 `.github/workflows/check.yml` Ubuntu/Windows 矩阵。
- 真实边界：工作树隔离不等于 OS 沙箱；本地预算不能承诺上游不提供的在途硬封顶；无计量/未知效果须停止后续花费。Hub 镜像实现和本地验证不意味着生产 Hub 资产晋级。
