# Decentralized Swarm v0.2 修正版任务书

事实源：用户 2026-09-23 23:33 修正版，续接终端 term_d00db8e6-745d-4e13-b787-426319b1a019。本文件替代此前 SWARM_TASK 的相冲突规划，不改冻结开发包和历史验收。
基线 codex/morphogenesis-mainline @ 605cf48b8b05baf86fd68e5d63f495ba3e5d7e69，决赛只读。仅在既有 decentralized-swarm 分支与工作树开发；检查点 e9a3836e03ef022e9a5f0986cd82cea4593a5492 保留。不得合回主线、改变演示运行状态或用绿色 CI 解除冻结。
定位：同机多进程、可信 Worker、共享持久化环境、无常驻任务派发者。SQLite WAL 不承诺跨机器一致性。

## 认账清单

1. Physarum 的 Qij=Dij/Lij*(pi-pj)，适应方程更新 D 而非 Q。本实现采用受 Physarum 管道适应与蚁群环境记忆启发的局部奖励路由，不是原求解器离散实现，不继承论文收敛保证。
2. metabolism/service.py 的 0.05 是 archive_threshold。rho(dt)=1-exp(-dt/tau)，默认 tau_seconds=86400.0；半衰期=tau*ln(2)。奖励学习率 alpha 独立设置。
3. 减少显式点对点协调和对主控持续在线的依赖，通过有界局部查询控制协调开销；不宣称 O(n²) 到 O(n)。局部性由后端 scope 权限、模块归属或任务依赖邻域定义，不使用前端画布坐标。
4. 历史路由权重必须实际参与下一次抽样，保存信号、过滤约束、权重和概率。
5. 资产晋级只改 quarantine → approved 索引；任务补丁落地是独立动作，只能写显式隔离目标库。禁止修改 swarm 自身执行器、预算规则、验证器、冻结文档和决赛树。
6. 原子认领 + TTL/续租 + 递增 fencing token + 幂等提交统一使用 SQLite 短事务；模型调用不在写事务内。
7. 先预算预留、后执行、再结算。未知 usage/cost/远端效果保留预留、停止新付费调用。历史 usage 估计本身不是可信上界。熔断是本 swarm 运行级，不是账户级或上游在途硬保证。
8. 经验沉积后必须有 FETCH approved → 适用性检查 → 注入 → 真实采用记录；仅注入不算采用。
9. Hub 镜像 pending/confirmed/rejected/unknown 可见；本地批准不等于 Hub promoted。Hub 不在关键路径，未知写效果不重发。
10. 任务事实、依赖、尝试、结果及追加审计不参与遗忘；信息素和历史权重独立可衰减。重复错误合并已有任务证据，失败不抹掉任务。
11. observer 严格只读，不创建、认领或推进任务。
12. Docker 健康检查 53bb52c 已由 5 秒改为 15 秒，若后续部署须包含该修改的精确 SHA。本轮不改变已有部署。

## 模块要求

M1 local_assets/store.py 复用基线 NodeAssetBridge 与官方 SDK canonicalize/computeAssetId/verifyAssetId/schema，不自写 Python JSON 哈希。不可变正文与验证、晋级、镜像等可变状态分离。
validate.py 为限定行为/环境的本地验证：测试和验证器不能由被测 Worker 修改；报告绑定 exact asset_id、目标 baseline 和验证策略版本。路径、网络与秘密访问由实际执行环境限制，静态扫描和普通 worktree 不作为安全隔离证据；缺隔离时拒绝任意代码执行并明确未验收。promote.py 只改 approved 可用状态。补丁应用另设受提交端 fencing 约束的隔离目标入口。消费检查依赖/能力/scope，采用绑定 asset_id、输入上下文和执行记录。

M2 swarm/task_ledger.py 持久保存任务身份/状态/依赖/尝试/验收/结果及去重错误证据。路由偏好另表，JSONL 仅导出，不作权威账本。

M3 swarm/router.py 更新 w_next=(1-alpha)*w+alpha*r。先过滤无权限、能力不符、依赖未完成、已完成、不可认领任务，再 softmax(beta*w_history*pheromone*capability_match*urgency) 加权抽样。记录归一化概率及输入信号，使用探索或 aging 避免热门竞争/饥饿，查询有界。

M4 swarm/lease.py 以同一 SQLite 事务更新 available → claimed，写 worker_id/expiry/递增 token。提交端核验 task_id+token+owner+TTL；同一结果幂等，旧代次和冲突提交拒绝。覆盖父子/别名 scope 重叠；旧 Worker 不能释放新租约。必测 A(token=1)暂停，B(token=2)接续完成，A恢复提交被拒绝。finally 清理、续租、退避均有界。

M6 swarm/budget.py 先于 M5：默认每任务 max_tokens=20000，共享账本原子预留；Worker burn rate 休眠；swarm 已结算+在途预留+新预留不超准入上限。有可信请求费用上界才可主张相应保证；可靠限额缺失、隐藏调用/自动重试时仅是准入控制。持久字段 usage_metering=verified/unknown，request_bound=verified/unbounded，admission_control=enabled/disabled，cost=estimated/billed/unknown。未知请求不释放，不盲目重发。增加 max_tasks/max_attempts/运行时长/派生任务上限。

M5 swarm/worker_loop.py：循环顶部 admission/能量/运行界限 → 局部账本 → 路由 → 原子租约 → 预算预留 → FETCH/检查/注入经验 → 隔离执行 → 固定验证 → fencing 提交 → 本地批准与隔离成果落地 → 正负反馈/真实采用审计 → finally 按 token 释放。空闲与竞争指数退避+抖动；定期续租；完成状态持久化后其它 Worker 排除，重启不重复晋级/未知调用。

M7 observer.py 只读账本、租约、审计、ValidationReport。hub_mirror.py 复用 E 直连实现，默认关闭、异步可选且四态可见，不调用生产 Hub/付费模型或搜索秘密。

## 顺序与验收

先锁任务/租约/资产/预算契约与包声明，再并行 M1/M6 和 M2/M4；路由依赖账本，M5 等安全底座，最后 M7/独立 I。沿用 pytest、strict、build、SDK/分发；pyproject.toml 与 tools/typecheck.py 纳入新增包。成熟实现优先，记录来源/版本/许可证，不建新调度器、Attempt、Manifest、哈希/证明设施。

| 场景 | 必须证明 |
|---|---|
| 无派发者 | 三个独立 Worker 进程完成至少五个不同任务；observer 不推进 |
| 在途故障 | 杀持租约 Worker，其他成员接续；旧代次恢复提交拒绝 |
| 跨成员复用 | A 已验证资产被 B 新任务/新会话真实采用；asset_id、上下文、执行记录一致 |
| 预算竞争 | 多进程争最后额度不重复预留；缺失 usage 不变零成本 |
| 重启边界 | 完成任务不重复晋级；未知请求不重发；冻结树/分支/演示状态不变 |
| Hub 离线 | 模型网关仍可用的真实证据单列，不能以完全断网 fake 替代 |
| 完全断网 | 仅本地执行器/模型或显式 fake，不冒充远程模型 task_live |

contract_local/interface_live/task_live 分开。没有真实证据保留 not_run。最终报告完成内容、分支/SHA、验证命令结果、真实限制及未执行/人工操作。
