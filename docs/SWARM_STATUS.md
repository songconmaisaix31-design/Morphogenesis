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

## P1 预算门禁（2026-09-23T22:47:26+08:00）

- B M6 提交 `5f6a544feab6b7a1f832189c8007fe2840667e4e`（2026-09-23T22:46:44+08:00）已推送开发分支。`.venv/Scripts/python.exe -m pytest tests/swarm/test_budget.py -q`：20 passed，22.34 秒；两条警告来自刻意绕过 Pydantic 的坏输入测试。`-m mypy --strict swarm/models.py swarm/budget.py`：2 文件通过。
- 覆盖真实多进程预算预留/结算竞争、账户持久化、逐 Worker burn rate、严格 gateway usage 解析、未知用量保留预留并熔断、fake 高消耗触发全账户休眠、不可重试、公开输入重验证。金额仅为显式价格表本地估算，actual_cost_usd 仍未知；provider_enforced 仍是可信执行器的边界声明，不能变成上游在途封顶证明。
- 首轮预算 15 测试已于 22:09 通过，随后允许 C 接本地有界闭环；20 测试为补充 API 边界回归。其他模块/全量验收尚未通过，interface_live/task_live 仍 not_run。
- A 完成锁定本地环境（Python 3.12.13、Poetry 锁定依赖、npm ci --ignore-scripts）。M1 首轮实际 SDK 拒绝额外 content 属性，正在原 Worker 内修复并重测，未改变上游 schema/hash。C 只读 observer 3 测试通过；官方镜像范围审查缺陷已退 C。
- Orca 等待请求 `8e149801-eca4-4c23-a736-2b2ae63aff3d` 曾 runtime_timeout；request-show 证实原等待 cancelled/connectionLost，同 ID 重放后恢复。22:45 三个原 Dispatch 均回到 live，未重复派发、未推断未知 Worker 已退出。
