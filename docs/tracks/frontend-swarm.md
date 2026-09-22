# T 轨：AGENT SWARM 真实拓扑视图（frontend-swarm）

基线：`origin/codex/morphogenesis-mainline` 972d4ba。唯一 write_paths：`viz/frontend/src/swarm/**` 与本文件。

## 交付物

- `viz/frontend/src/swarm/SwarmTopology.jsx` — 默认导出 `SwarmTopology({dashboard, active, reducedMotion})`，供 S 轨页面壳在 `AGENT SWARM` 视图挂载。
- `viz/frontend/src/swarm/derive.js` — 纯函数视图模型派生，无 React 依赖，可单测。
- `viz/frontend/src/swarm/swarm.css` — 冷白 / 青绿 HUD 主题（`#070b0d` / `#e8efed` / `#8ca3a0` / `#65d9c7`）。
- `viz/frontend/src/swarm/preview.jsx` + `vite.preview.config.mjs` — 独立预览 / 浏览器验证入口，不进页面壳构建（壳构建 entry 仍是 `src/shell.jsx`），输出必须指向临时目录，不写 `viz/static`。

## 事实来源（不造数据）

只消费 `/api/dashboard` JSON：`rehearsal.current.members / pipes / routing / results`、`events`（Envelope）、`genes`（GeneView）、`adoptions`（UseRecord）。

- 节点 = members ∪ pipes 端点的真实 AgentId；管道之外的成员无边，快照未声明可用性的成员标「快照未声明」。
- 边 = `pipes` 原样（src/dst/weight/flow/success_rate/active），宽度 ∝ 权重，离线虚线；无 pipes 时显示空态注记，不虚构边。
- Gene / EvoMap 只出现在选中成员的「Gene 来源 / 采用」事实列表（`source_attempt` / 精确 `UseRecord`），不拼进运行拓扑。
- Ghost 五态准确区分（返修后）：`waiting`（已移除、未选路）→「等待重路由」；`rerouted`（已选路、恢复任务结果尚未记录）→「恢复选路 → X；恢复结果尚未判定，不代表已恢复」；`recovered`（恢复任务自身 TaskResult `succeeded`，或阶段 completed）→「已离开，任务重路由 → X；恢复任务已成功」；`failed`（`stage === 'failed'` / 有 `failure` / 恢复结果非 succeeded）→「彩排已停止，未完成恢复」+ 真实 failure 文本，role=alert，绝不暗示失败已恢复；`offline`（成员不可用但路由未记录移除）→ 只标不可用，不谈重路由。「任务重路由」成功文案仅出现在 `recovered`；`rerouted` 只声称选路事实。移除边界注明「两任务之间」。
- provenance（live/replay/mock）、阶段（14 个 Stage 中文映射 + 原始 key）、快照序号、task_id 全部如实显示；replay 标「只读」。

## 交互与可用性

- 布局：角色泳道 planner → builder（扇形）→ reviewer → aggregator，确定性坐标，未知角色回退环形。
- 选中：点击或方向键循环（Enter/点击切换、Escape 取消），详情面板按需展示该成员的管道 / 任务结果（status、复核、tokens）/ 事件 / Gene 记录。
- 鼠标响应：视差微移 + 光标辉光（RAF 节流）；`reducedMotion` 或 `active === false` 时不挂监听器、CSS 过渡全停（`.swarm-reduced` / `.swarm-paused`），并遵守 `prefers-reduced-motion` 媒体查询。
- 空态：`dashboard` 为空对象缺 rehearsal → 空态说明；`dashboard == null` → 「数据不可用」断线态（role=alert）；均无残留旧画面。

## 依赖说明

未引入任何新依赖：拓扑为手写 SVG（React 18 已有）。锁文件由 T0 独占、页面壳 package*.json 归 S 轨，本轨零改动。

## 验证（真实浏览器）

数据 fixture：`python` 运行 `orchestration.rehearsal.Rehearsal` + `tests/t2/test_rehearsal.FixtureExecutor`（mock provenance，无模型调用）生成真实 rehearsal.json，经 `viz.adapter.load_rehearsal` 得到 `/api/dashboard` 同构 JSON。返修后 Ghost 五态各有真实 fixture：`recovered`（completed，两个任务均 succeeded）、`waiting`（member_offline，已移除未选路）、`rerouted`（recovery_selected，已选路、恢复结果未记录）、`recfailed`（恢复执行真实失败：removed+selected 同时存在且结果 insufficient_evidence）、`repairfailed`（修复阶段失败、无移除，不得出现 Ghost）。

- 构建：`cd viz/frontend && npx vite build --config src/swarm/vite.preview.config.mjs --outDir <tmp>` ✓；壳构建 `npx vite build --outDir <tmp>` ✓（不触碰 `viz/static`）。
- 浏览器：Tabbit（Chromium, Playwright 1.62）加载 harness 页面，首轮 7 场景断言全部通过（节点/边/详情/键盘/鼠标/reduced/hidden），completed 与 waiting 两态留存截图核对。返修轮 5 个 Ghost 场景 DOM 断言全部通过：recovered 显示「任务重路由 → builder#1；恢复任务已成功」；rerouted 显示「恢复结果尚未判定，不代表已恢复」；waiting 显示「等待重路由」；recfailed 横幅与详情均为「彩排已停止，未完成恢复：RuntimeError…」（role=alert，无恢复暗示，节点标签「已离开 · 恢复未完成」）；repairfailed 无任何 Ghost 元素。
- Python 回归：`python -m pytest tests/t5/test_adapter.py tests/t2/test_rehearsal.py -q` → 18 passed。

## 限制

- Tabbit 截图运行时在完成态与等待态各成功一次后，后续 page.screenshot 持续超时（capture 阶段挂起，已上报为 recoverable warning）；failed/empty/disconnected 及返修轮五态以 DOM 断言验证，未留截图。与本组件无关（页面 DOM 断言均即时返回）。
- `tests/integration/*.cjs` 需要 `MORPH_PLAYWRIGHT` / `MORPH_CHROMIUM` 环境，本机未配置，未运行。
- 组件未接入页面壳（S 轨负责在 AGENT SWARM 视图挂载并传 `dashboard`）；与壳的字段契约即 props `{dashboard, active, reducedMotion}`。
