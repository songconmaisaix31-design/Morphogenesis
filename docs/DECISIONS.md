# 接手决策

1. 原仓库仅 LICENSE，保留 Apache-2.0；开发包原文导入 `docs/source/`，不改写历史文档。
2. 初始四轨安排已被用户后续指令替代：按功能去耦合并行，八个互斥功能轨见 PLAN；T4 暂不进入主闭环，最后独立集成。
3. 用户“不要重复造轮子”优先：编排、校验、持久化、检索、协议、哈希、可视化均使用成熟依赖；项目自研限权重反馈、经验代谢和必要适配。
4. 包内“身份/AttemptId/Provision”解释为最小业务数据，不据此建设开发调度或完成证明基础设施；开发协调直接使用 Orca CLI。
5. 当前环境实测：Python 3.13.13、Node 24.16.0、npm 11.13.0、uv 0.11.26、Codex CLI 0.155.1；Poetry 未安装。T0 可通过隔离工具环境运行 Poetry 并产出包内规定的锁，避免全局环境改动。
6. 外部发布缺配置时为“待发布”；官方 SDK 本地验证通过只能证明本地校验。G3/G4 的外部部分仍需真实沙箱证据。
7. 2026-09-22 对 npm registry 实查：`@evomap/gep-sdk@1.14.0`、`@evomap/gep-mcp-server@1.7.0` 均声明 Apache-2.0；`@evomap/evolver@2.0.38` 声明 GPL-3.0-or-later，Node engine 为 `^22.13.0 || >=23.4.0`。包内“Node >=18”不能作为最新版 Evolver 要求。当前主链复用 SDK 与 MCP Server，不复制 Evolver 源码。
8. 上游依据：[GEP SDK](https://github.com/EvoMap/gep-sdk-js) 明确只提供 schema/协议助手；[GEP MCP Server](https://github.com/EvoMap/gep-mcp-server) 提供工具接口；[LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence) 的 checkpointer 保存线程状态；[FAISS](https://github.com/facebookresearch/faiss) 提供检索实现；[SQLModel](https://github.com/fastapi/sqlmodel)、[官方 MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)、[ECharts](https://github.com/apache/echarts) 分别用于元数据、协议客户端、图表。最终安装版本与 notices 由 T0 维护。
9. Orca 1.4.199 的 `worker-start --worktree new-child` 在当前会话实测返回 `selector_not_found`，没有创建 Task/Dispatch。改用受支持的 `worktree create --agent codex`，取得精确 worktree/terminal 后 `worker-start --terminal ... --worktree id:... --from <coordinator>`；无自制调度、无重复 worker。
10. 用户明确授权按难度选择模型。本机 `models_cache.json` 实查存在 gpt-6-astra、gpt-5.6-terra、gpt-5.6-luna 及 high/xhigh 等档位。复杂契约/协议/恢复/一致性分配 Astra，边界明确的拓扑/展示分配 Terra，固定规模供给适配分配 Luna；不改用户全局模型配置。
11. 执行入口采用现有 Codex CLI 的只读模式与结构化提案，由本项目适配器仅应用 `sample.py` 白名单内容，再执行固定独立验收；不自建模型工具循环。CLI 不支持的硬费用封顶如实记限制，未知 usage 不置零。
12. 协调审查发现 T3T 初版失败信号负值偏离方案成功率语义，闲置窗口未实际衰减；原 Worker 已在 `a12d288` 修复，10 项锁定测试通过。运行时需从持久复核事件恢复每轮内存拓扑。
13. P 供给原版未支持重复角色；原 Worker 在同一 terminal 续接任务，`1c4e5e9` 为每个角色分配稳定实例编号，支持两位 builder 的选路验证。该 Worker 已完成并通过 Orca worker-release 释放，分支与输出归档保留。
14. 展示不应从任意事件 payload 推断经验或成功；消费明确的事件、经验快照、复核结果导出。ECharts 使用 T0 锁定的本地依赖，不保留独立 CDN 版本。
