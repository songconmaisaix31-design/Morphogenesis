# Sol 去中心化蜂群与拓扑验收（2026-09-24）

用户指定 `term_5fa3f898-f976-4758-a6ea-4bbe3914a0b9`，已核对其去中心化交付为 `decentralized-swarm@d3cb391d096e94e52136cf8161b558017fcbc4ea`。当前用户指令授权此版本的前端替换、真实 API 扩容实验及部署验收，覆盖旧任务书的未授权部署限制。主线治理基线 `cfbaf6b`；实验和业务仍留在去中心化分支，暂不合并主线。

所有新开发 Worker 和蜂群模型请求仅使用 EvoMap `evomap-gpt-5.6-sol`。旧终端显示 DeepSeek，旧原轨已结算，故不向旧模型继续派发。凭据在仓库外私有目录，仅配置引用路径，不进入提示、提交、日志或前端。

| 轨 | Worktree / Branch | 唯一 write_paths | 交付与验收 |
|---|---|---|---|
| V | morph-swarm-viz / songconmaisaix31-design/morph-swarm-viz | viz/**, tests/t5/**, tests/integration/check_swarm*.cjs, docs/tracks/swarm-viz.md | 同步 d3cb391；以 /api/swarm 真实事实重构拓扑，去掉 planner 回退和旧彩排说明；Ghost 为成员更替后保留的关系与经验；明确空、错误、陈旧、未知状态；构建及三视口浏览器 |
| R | morph-sol-scale / songconmaisaix31-design/morph-sol-scale | swarm/cli.py, swarm/evomap_executor.py, tests/swarm/test_worker_evomap.py, tests/swarm/test_scale*.py, tools/run_swarm*.py, docs/SWARM_SOL_EXPERIMENT.md | 复用 Worker/账本/路由，将固定三进程六任务入口参数化；真实 Sol 3→8→16 进程、6→48→96 任务；保留租约、预算、未知请求停止、一次尝试和实际采用证明；规模受资源与成功门禁约束 |
| I（两轨后） | decentralized-swarm / decentralized-swarm | 精确 SHA 普通合并，少量配置胶水，docs/SWARM_SOL_ACCEPTANCE.md | 完整测试/类型/构建/分发，真实状态 viewer、computer-use；必要部署配置调整须先明确归属，领域缺陷退原 Worker |
| 主控 | 主线工作区 | 本计划、状态与验收记录 | 监督、凭据配置、运行/部署操作、独立验收；不写业务代码 |

实验记录独立 OS PID、唯一任务接受数、源/目标成员、实际采用、路由概率与权重、用量、估算和未知实际费用。对比为保留历史、清除历史、成员替换的可重复局部机制检验；简单数据题不能宣称普适算法优势或论文收敛。Hub 不进入关键路径，不发生产发布/付费 FETCH。

先核对网关模型/计价元数据；没有价格不冒充已知费用，不为扩容关闭 unknown 熔断或重复新建 run 绕过熔断。所有写入与有限 API 调用已由用户授权，无需重复确认。每轨 commit + push，独立 I 普通 exact-SHA merge，最终记录不可完成的外部限制。Computer-use 与 Playwright、单测、真实模型三类证据分开。
