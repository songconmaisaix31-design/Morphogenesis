# Morphogenesis 前端重构执行页（2026-09-23）

## 目标与边界

保留现有 Python `viz.server`、`/api/dashboard`、T2 `events.jsonl` / `result.json`、`RehearsalDocument` 与验收三态。首页为 Physarum-WebGL 质感的鼠标趋食黏菌；点击 `PHYSARUM` / `AGENT SWARM` 切换到真实拓扑、任务、协作、事件和 Gene 信息。仅重构当前项目页面；ORCA 只用于开发。现有已提交基线 `7eb1e7d731436f53a55c3a1e9c28604269dd40de`。参考压缩包只作视觉观察，不复制其中模型、字体、脚本或文案。

## 最小共享约定

- 视觉：背景 `#070b0d`，冷白 `#e8efed`，次级 `#8ca3a0`，青绿 `#65d9c7`；项目名 `MORPHOGENESIS` 是首屏唯一大字。正常切换只出现 `PHYSARUM`、`AGENT SWARM`；全局 CRT 扫描线 opacity 0.03–0.05，`pointer-events:none`，可关闭且遵守 reduced motion。
- `PhysarumField({active, reducedMotion, onError})`：只负责首页 WebGL 黏菌、趋食和局部光标；隐藏时暂停 RAF / 高负载计算，卸载清理资源。可在组件目录中独立提供降级视图。
- `SwarmTopology({dashboard, active, reducedMotion})`：只消费 `/api/dashboard` 的 JSON；事实取 `dashboard.rehearsal.current.members/pipes/routing/results` 或 `dashboard.events` 等现有字段，布局可优化但不造节点、边、任务、通信或恢复结果。空态、错误态、回放态明确标注。
- 页面壳统一获取 `/api/dashboard`，保留 `provenance`、`acceptance`、`source_label`，按需显示原有任务、事件、Gene 和指标。EvoMap 独立只读端点提供来源字段；页面不得将其写成运行拓扑事实。
- 新依赖只由页面壳轨修改 `viz/frontend/package*.json` 与构建配置；其他轨通过 Handoff 提出所需依赖。`viz/static/assets/finals-shell.*` 由页面壳构建产出，集成轨最终重建。

## 互斥开发轨

| 轨 | Agent / 责任 | 唯一 write_paths | 验收 |
|---|---|---|---|
| P | Kimi，Physarum 来源核验、WebGL 黏菌、趋食、鼠标离开与降级 | `viz/frontend/src/physarum/**`, `docs/tracks/frontend-physarum.md`, `viz/static/licenses/physarum/**` | 真实浏览器鼠标移动聚拢、离开恢复、缩放对齐、隐藏暂停；来源版本和许可证 |
| T | Kimi，真实拓扑及协作详情 | `viz/frontend/src/swarm/**`, `docs/tracks/frontend-swarm.md` | 从真实快照与 Envelope 派生可点选节点/真实边/事件；空态、replay 和恢复阶段正确 |
| S | Kimi，页面壳、排版、动效、视图切换及数据接线 | `viz/frontend/src/App.jsx`, `viz/frontend/src/shell.jsx`, `viz/frontend/src/theme.css`, `viz/frontend/src/components/**`, `viz/frontend/package*.json`, `viz/frontend/vite.config.js`, `viz/static/index.html`, `viz/static/style.css`, `viz/static/app.js`, `viz/static/assets/finals-shell.*`, `docs/tracks/frontend-shell.md` | 首屏文案、反复切换、后端失败反馈、原数据页功能、键盘、reduced motion、CRT 开关；构建 |
| E | 优先 Kimi，EvoMap 官方接口核对及安全只读闭环 | `viz/evomap_*.py`, `viz/server.py`, `tests/t5/test_evomap*.py`, `docs/tracks/frontend-evomap.md` | 真实可用的 EvoMap 信息经服务端处理显示；无密钥/权限时准确报告，不泄密、不增加任务调用 |

主控只改本计划及 `docs/STATUS.md` / `docs/ACCEPTANCE.md`。各 Worker 在独立 Orca worktree 和分支工作，仅改本轨文件，负责测试、文档、commit、push；跨轨依赖发 Handoff。完成后独立集成 Agent 依精确 SHA 普通合并，只补少量导入/配置/路由胶水；领域问题退回原轨。主控持续检查早期链路，集成 Agent 完成适用测试、构建、真实浏览器验收与最终分支推送。

## 验收边界

优先跑通“首页趋食 → 切换 → 真正的 `/api/dashboard` 拓扑 → 查看任务/事件”，再打磨视觉。回放、mock、local API、task_live 分列；不启动新的付费模型任务来充当界面验收。性能结论记录浏览器、设备、条件与可复现观察；WebGL 不可用、低性能、减少动态效果、无数据和连接失败均实际检查。EvoMap Key 若未配置，仅验证无密钥状态及本地契约，真实接口验收保留阻塞；任何外部副作用沿用现有授权门禁。
