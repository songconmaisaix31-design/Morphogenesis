# 接手决策

封板夜接续（2026-09-23）：沿用本机单屏、无需外接投影的既有决定。新的 Hub node_secret 仅用于官方节点认证，不能替代模型网关 key；固定原节点，项目内私有存储、无全局设置变更。真实候选已被平台记录，认证详情和精确 FETCH 分别揭示 candidate/noop/not-callable 与 3.36 credits/余额0/confirm_required；停止费用确认与下游使用/REPORT，不通过身份或信誉变化规避平台门禁。公网只读 replay 已独立部署通过，当前余额、可调用性、新模型任务和人工观看分别记录；最终 I 只复验累计代码与 CI，不发送新 Hub/模型请求。

插件评估决策（2026-09-22）：`evolver@evomap` 0.2.0 是经验工作流/Proxy MCP 桥，可复用其 Recipe/Gene 访问，但不能以安装成功替代 Windows 宿主加载与项目契约验收。实测默认发布在响应断连后重发，违背本项目未知效果不重试要求，未完成适配前不接入生产发布路径。`EVOMAP_MCP_PROXY_AUTOSTART=0` 在隔离测试中抑制该重发，但仍需后续真实适配验收。现有 GEP MCP、本地 metabolism、受控 HubClient 和网关演示不替换；工具提炼默认 publish=true 必须由项目边界显式约束。17 项检查 13 通过/4 不满足，远端与实际任务 NOT_RUN；无真实发布、无全局指令/hook 修改、无持续进化循环。

最新现场决策（2026-09-22）：用户明确“本机单屏运行，无需外接投影。现在启动 7527 网关真跑，全流程记录”，撤销外接投影和接线确认前置。协调者直接运行已验收 I 入口，一次第五轮最多两个新请求；实际两次 HTTP 200、两任务各 3/3，完整选路/Gene 代谢审计通过。Enter 由协调者通过 TTY 发送，记录为工具输入，不以 source=operator 字段推断人工见证。保留 7527 完成页面和完整本地证据；不自动再跑，不操作 7526 旧回放。自动打开桌面浏览器被审批策略拒绝，不绕过；浏览器截图验收与桌面人工观看仍区分。

现场准备阶段：演示执行器确定为 EvoMap 网关，OpenCode 是按难度分档的并行开发备选，今晚不验证其工具调用/流式。用户要求继续多 Agent 后，只拆现场展示与人工证据两条互斥轨；观察器增加显式人工 Enter 模式，不改变已验收的默认自动模式或第四轮原始证据。Hub 缺沙箱保持本地 stub 并标“待发布”；不实现或宣传在途进程强杀恢复，统一表述为“成员下线后，后续任务自动重新选路”。

1. 原仓库仅 LICENSE，保留 Apache-2.0；开发包原文导入 `docs/source/`，不改写历史文档。
2. 初始四轨安排已被用户后续指令替代：按功能去耦合并行，八个互斥功能轨见 PLAN；T4 暂不进入主闭环，最后独立集成。
3. 用户“不要重复造轮子”优先：编排、校验、持久化、检索、协议、哈希、可视化均使用成熟依赖；项目自研限权重反馈、经验代谢和必要适配。
4. 包内“身份/AttemptId/Provision”解释为最小业务数据，不据此建设开发调度或完成证明基础设施；开发协调直接使用 Orca CLI。
5. 接手时环境实测：Python 3.13.13、Node 24.16.0、npm 11.13.0、uv 0.11.26、Codex CLI 0.155.1；Poetry 未全局安装。最终通过 uv 隔离工具环境运行 Poetry 2.5.1，集成 worktree 使用独立 .venv / Python 3.12.13；CI 使用 Python 3.13，未改全局配置。
6. 外部发布缺配置时为“待发布”；官方 SDK 本地验证通过只能证明本地校验。G3/G4 的外部部分仍需真实沙箱证据。
7. 2026-09-22 对 npm registry 实查：`@evomap/gep-sdk@1.14.0`、`@evomap/gep-mcp-server@1.7.0` 均声明 Apache-2.0；`@evomap/evolver@2.0.38` 声明 GPL-3.0-or-later，Node engine 为 `^22.13.0 || >=23.4.0`。包内“Node >=18”不能作为最新版 Evolver 要求。当前主链复用 SDK 与 MCP Server，不复制 Evolver 源码。
8. 上游依据：[GEP SDK](https://github.com/EvoMap/gep-sdk-js) 明确只提供 schema/协议助手；[GEP MCP Server](https://github.com/EvoMap/gep-mcp-server) 提供工具接口；[LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence) 的 checkpointer 保存线程状态；[FAISS](https://github.com/facebookresearch/faiss) 提供检索实现；[SQLModel](https://github.com/fastapi/sqlmodel)、[官方 MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)、[ECharts](https://github.com/apache/echarts) 分别用于元数据、协议客户端、图表。最终安装版本与 notices 由 T0 维护。
9. Orca 1.4.199 的 `worker-start --worktree new-child` 在当前会话实测返回 `selector_not_found`，没有创建 Task/Dispatch。改用受支持的 `worktree create --agent codex`，取得精确 worktree/terminal 后 `worker-start --terminal ... --worktree id:... --from <coordinator>`；无自制调度、无重复 worker。
10. 用户明确授权按难度选择模型。本机 `models_cache.json` 实查存在 gpt-6-astra、gpt-5.6-terra、gpt-5.6-luna 及 high/xhigh 等档位。复杂契约/协议/恢复/一致性分配 Astra，边界明确的拓扑/展示分配 Terra，固定规模供给适配分配 Luna；不改用户全局模型配置。
11. 执行入口采用现有 Codex CLI 的只读模式与结构化提案，由本项目适配器仅应用 `sample.py` 白名单内容，再执行固定独立验收；不自建模型工具循环。CLI 不支持的硬费用封顶如实记限制，未知 usage 不置零。
12. 协调审查发现 T3T 初版失败信号负值偏离方案成功率语义，闲置窗口未实际衰减；原 Worker 已在 `a12d288` 修复，10 项锁定测试通过。运行时需从持久复核事件恢复每轮内存拓扑。
13. P 供给原版未支持重复角色；原 Worker 在同一 terminal 续接任务，`1c4e5e9` 为每个角色分配稳定实例编号，支持两位 builder 的选路验证。该 Worker 已完成并通过 Orca worker-release 释放，分支与输出归档保留。
14. 展示不应从任意事件 payload 推断经验或成功；消费明确的事件、经验快照、复核结果导出。ECharts 使用 T0 锁定的本地依赖，不保留独立 CDN 版本。
15. 最终集成保留各轨历史。全包 strict 和远端 CI 暴露的 T5 冗余 cast、截图发现的 hidden 空框和 Gene 标签遮挡均退回原 Worker，分别由 e2f1bbe、218ba08、9ae01cf 修复，协调者没有修改业务实现。
16. Orca 内嵌浏览器 helper 不可用，未重启全局运行时；复用现有 Playwright / Chromium 独立 headless 验证真实事件页面，分别记录 HTTP、DOM/Canvas、截图与内嵌能力限制。只清理自己核验过身份的服务和页面。
17. 三次真实任务已足以核查既定正常/暂停接续/经验复用路径。集成不再次付费调用；用最终独立验证器复验保留候选，并在复制的已完成 SQLite 检查点上重复恢复，禁止执行器和复核器重新调用。早期只读 backup 导致一个 shm 的 mtime 改变，已在报告保留该失败及修正，不能删去或夸大不变性。
18. 最终交付是固定修复样例的核心原型。Hub 沙箱凭据与正式契约、产品运行时动态供给、单次模型硬费用上限、可选 T4 与正式现场稳定性均不得用本地检查替代；具体结论见 ACCEPTANCE。
19. 新一轮固定彩排采用两个已授权的新任务：第一次修复产生真实经验和反馈，随后从固定成员池移除获胜 builder，第二次新任务必须实际选择另一个 builder 并复用经验。下线发生在任务之间，不以此冒充在途模型进程强杀恢复。三次彩排最多六次调用，不重复旧任务或重试 UNKNOWN。
20. 截至 2026-09-22 本轮准备阶段，EvoMap 官方 [API Access](https://evomap.ai/wiki/28-api-access) 文档将个人 API key 描述为知识图谱范围，示例格式为 ek_，A2A 变更使用 node_secret；不能仅凭用户新提供凭据的外观推断网关和权限。Base URL / 用途未确认前不发送该凭据。密钥不进入仓库、输出或 Worker prompt。
21. 本轮读取 Windows 显示设备仅见一个活动屏幕，系统逻辑尺寸 1707×1067；这不能证明实际投影接线。软件彩排与真实投影彩排分列，页面额外验证 1366×768 / 1920×1080，但不据此声称现场投影通过。
22. API 目的地待确认只阻塞该凭据的测试，不阻塞已授权的本地软件彩排。集成沿用项目已接通的 Codex CLI，最多六次新调用完成三轮，凭据与现有账号配置不变；明确记录这些结果不验证用户本轮提供的 API key。此前等待 API 地址再做全部 live 的安排据此调整，避免把独立事项变成不必要的前置条件。
23. 三轮完整软件彩排实际完成于北京时间 13:23–13:30，6 次新 CLI / 87,133 tokens，无失败或重试。第一次经真实 stdin Enter 移除逻辑成员，另两次自动；每轮两个外部 3/3、真实采用、墙钟衰减及归档均通过。不把旧版三个单任务或回放算入本轮。
24. 实图暴露的节点/标签裁切和相互遮挡均退回 V 原 Worker；最终使用 160px ECharts 图、真实 ZRender 边界和两种视口截图验收。保留全部原始 live 图片，最终 UI 修复仅以明确 replay 的已有数据复验，不额外调用模型，也不声称三轮都运行于最终 UI SHA。仅保留 127.0.0.1:7525 只读回放应用供用户现场检查，其进程交接与 Worker 结项分开记录。
25. 候选 Windows CI 暴露真实墙钟下的测试速度假设；保留失败，不以另一轮 CI 偶然成功代替修复。仅由原 R 修测试时间语义、原 I 集成，不修改已完成彩排的产品时钟或增加模型调用。原会话通过 cwd 过滤的官方 `codex resume --last` 恢复，不重用已结算的 Task/Dispatch 身份。
26. 原集成回放服务在 worker-release 后退出，撤回“独立进程可跨 Worker 释放保留”的判断。协调者在自身进程树启动并验证同一原始证据的只读回放，交接包含当前 PID/日志和重启命令；仍不承诺跨 Orca/系统退出运行。
27. 用户补充 EvoMap 提供方及九个模型名称后，已确认这把凭据属于模型网关。实测 Base URL 为 `https://api.evomap.ai/v1`，Bearer `/models` 返回十个带 `evomap-` 前缀的 ID（额外含 Terra）；一次 `evomap-gpt-5.6-luna` Chat Completions 真实请求返回 200 / OK / 15 tokens。第 20/22 条的“目的地待确认”在模型网关范围内解除，不能据此授权或声称 Hub 发布、Responses/工具调用兼容或三轮网关彩排。现有执行器与账号配置未切换，secret 仅用于本次 HTTP 请求内存。
28. 用户现要求切换执行器并跑第四轮，采用显式 `evomap` 选项和已验证的 `evomap-gpt-5.6-luna`；复用 httpx、现有 Executor/Proposal、Pydantic 和独立 checkpoint，不自建模型工具循环。第四轮最多两个新 POST，异常或未知效果不重试。原 R 实现，原 I 集成审计和浏览器观察，协调者仅通过审阅入口注入进程凭据执行验收。旧三轮只读保留；网关 request/response 与 CLI turn 证据分别审计。
