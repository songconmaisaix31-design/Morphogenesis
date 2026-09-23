# Sol 去中心化蜂群与拓扑验收（2026-09-24）

用户指定 `term_5fa3f898-f976-4758-a6ea-4bbe3914a0b9`，已核对其去中心化交付为 `decentralized-swarm@d3cb391d096e94e52136cf8161b558017fcbc4ea`。当前用户指令授权此版本的前端替换、真实 API 扩容实验及部署验收，覆盖旧任务书的未授权部署限制。主线治理基线 `cfbaf6b`；实验和业务仍留在去中心化分支，暂不合并主线。

所有新开发 Worker 和蜂群模型请求仅使用 EvoMap `evomap-gpt-5.6-sol`。旧终端显示 DeepSeek，旧原轨已结算，故不向旧模型继续派发。凭据在仓库外私有目录，仅配置引用路径，不进入提示、提交、日志或前端。

| 轨 | Worktree / Branch | 唯一 write_paths | 交付与验收 |
|---|---|---|---|
| V | morph-swarm-viz / songconmaisaix31-design/morph-swarm-viz | viz/**, tests/t5/**, tests/integration/check_swarm*.cjs, docs/tracks/swarm-viz.md | 同步 d3cb391；以 /api/swarm 真实事实重构拓扑，去掉 planner 回退和旧彩排说明；Ghost 为成员更替后保留的关系与经验；明确空、错误、陈旧、未知状态；构建及三视口浏览器 |
| R | morph-sol-scale / songconmaisaix31-design/morph-sol-scale | swarm/{cli,evomap_executor,models,budget}.py, tests/swarm/test_{worker_evomap,budget}.py, tests/swarm/test_scale*.py, tools/run_swarm*.py, docs/SWARM_SOL_EXPERIMENT.md | 复用 Worker/账本/路由，将固定三进程六任务入口参数化；真实 Sol 3→8→16 进程、6→48→96 任务；本轮显式未知费用许可，默认保护保持；未知调用停止、一次尝试和实际采用证明；规模受资源与成功门禁约束 |
| I（两轨后） | decentralized-swarm / decentralized-swarm | 精确 SHA 普通合并，deploy/** 与 tests/deployment/** 的必要配置胶水，docs/SWARM_SOL_ACCEPTANCE.md | 完整测试/类型/构建/分发，真实状态 viewer、computer-use；领域缺陷退原 Worker |
| 主控 | 主线工作区 | 本计划、状态与验收记录 | 监督、凭据配置、运行/部署操作、独立验收；不写业务代码 |

实验记录独立 OS PID、唯一任务接受数、源/目标成员、实际采用、路由概率与权重、用量、估算和未知实际费用。对比为保留历史、清除历史、成员替换的可重复局部机制检验；简单数据题不能宣称普适算法优势或论文收敛。Hub 不进入关键路径，不发生产发布/付费 FETCH。

先核对网关模型/计价元数据；没有价格不冒充已知费用。当前用户明确授权“尽情用，用光为止”，优先于旧文档的缺价停止规则：允许增加默认关闭的 `allow_unknown_cost`，本轮有限实验显式打开。仅在真实 usage 已知且未越限时继续，费用始终 unknown/null、完整准入预留不释放、仍累计计入运行 allowance。未知 usage、未知远端效果、越限和额度拒绝停止，不重发或换根绕过。总请求/单请求输出/每任务尝试/时长必须有限；运行 allowance 不声称为提供商账单上限。所有写入与有限 API 调用已由用户授权，无需重复确认。每轨 commit + push，独立 I 普通 exact-SHA merge，最终记录不可完成的外部限制。Computer-use 与 Playwright、单测、真实模型三类证据分开。

## 执行状态

- Orca Run `run_cef52e19ade6`，协调终端 `term_357594e1-b3a7-43f5-97c4-61f84f997a04`。V `task_25b7ebc9f5f8 / ctx_1fcd0cb53852`；R `task_82da0ebb69e4 / ctx_78acc39a104a`。两者经实际终端开发活动核实，均为 OpenCode 1.18.32 的 EvoMap Sol API 会话；接续已有终端，因此 Orca launch model 字段为空，不把该字段当作型号证明。
- 认证 GET `https://api.evomap.ai/v1/models` 返回 200，含 `evomap-gpt-5.6-sol`，没有价格字段。已异步请求用户提供对应单价；此问题仅改善费用记录，不再作为扩容许可门禁。初始从旧任务书推导的缺价阻塞已按当前用户支出授权纠正，采用上一段显式 opt-in；不能放宽未知请求/usage 保护。
- 公网 `47.93.118.110:7799` 当前为只读旧版本 `53bb52c31ab68655e2bca620508488d7f95e00e6`，`/api/swarm` 实测 404。I 须补 Docker/打包白名单的 swarm 与 local_assets、Nginx 精确只读路由、独立 swarm 数据挂载配置及适用部署检查。保持原项目名 morphogenesis、端口 7799、其他共治容器不变；旧镜像/版本/数据保留回滚。
- 本地 viewer 绑定本轮原始 state；公网若部署复制的完成态，必须显式标注 capture/replay，不能冒称公网有活动模型进程。真实 API 在本机运行与公网展示分别验收。
