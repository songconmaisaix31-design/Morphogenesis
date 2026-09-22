# S 轨 · 页面壳（frontend-shell）

基线：`origin/codex/morphogenesis-mainline` 972d4ba。分支：`songconmaisaix31-design/morph-front-shell`。

## 范围与视觉契约

write_paths 见 `docs/FRONTEND_REFACTOR_PLAN.md`。视觉节奏参考 christmas.misterprada.com 与离线包 christmas-site / linear-site（实查：近黑全视口 WebGL、粗壮冷白大写标题、大面积留白、稀疏文字、轻缓粒子光感）；未复制其 JS/模型/字体/文案，版式为原创。

- 统一背景 `#070B0D`，冷白 `#E8EFED`，次级 `#8CA3A0`，青绿 `#65D9C7`；成功绿 `#34D399` 仅保留给 checkpoint 通过脉冲。
- 首屏正常态只有大字 `MORPHOGENESIS` 与 `PHYSARUM` / `AGENT SWARM` 两个极简标识；页头（品牌/事实/CRT 开关）与页脚只在 swarm 视图显示（`body[data-view='physarum']` 隐藏，数据区照常更新）。异常反馈（连接失败、模块降级）例外可显示。
- CRT 扫描线 opacity 0.04（约定 0.03–0.05 区间内），`pointer-events:none`，页头 CRT 按钮可关闭并持久化到 `localStorage('morph-crt')`，reduced motion 下静止。
- 自定义光标（点+拖尾环）只在 swarm 视图、fine pointer、非 reduced motion 时启用；首页让给 P 轨食物光标，触屏保持原生。
- 键盘：`1`/`←` 回 PHYSARUM，`2`/`→` 进 AGENT SWARM；按钮可 Tab/Enter；`inert` 保证隐藏视图不可聚焦。深链 `#/swarm`、`#/physarum`。
- 转场：两视图常驻挂载、仅 opacity/translate 交叉淡入淡出（0.34s，reduced motion 为 0），数据区 DOM 与画布不重建。

## P/T 导入契约（Handoff）

壳通过 `import.meta.glob` 惰性加载，模块未合入时 glob 为空、壳使用自身降级视图并正常构建；合入后自动生效（iife 构建已开 `inlineDynamicImports`）。

- P 轨：默认导出 `PhysarumField` 于 `viz/frontend/src/physarum/index.jsx`（也认 `index.js` / `PhysarumField.jsx`）。props：`{active, reducedMotion, onError}`。`active=false` 时暂停 RAF/高负载计算；`onError(error)` 时壳切回 CSS 降级背景并提示。首页光标归 P。
- T 轨：默认导出 `SwarmTopology` 于 `viz/frontend/src/swarm/index.jsx`（也认 `index.js` / `SwarmTopology.jsx`）。props：`{dashboard, active, reducedMotion}`，`dashboard` 为 `/api/dashboard` 完整 JSON（可为 `null`）。合入后 `body[data-swarm-module='loaded']`，`app.js` 跳过降级 ECharts 圆形拓扑；管道明细列表保留。

## 数据接线

- 壳统一同源轮询 `/api/dashboard`（1s，语义沿用实时快照）；`app.js` 不再独立 fetch/轮询，改为 `window.MorphDashboard.update(data, {redraw, resize})` / `.fail(message)` 桥。
- 文字/DOM 区每次更新；ECharts 重绘只在 swarm 视图可见且页面非隐藏时进行（`redraw`），视图激活时立即 `resize`+重绘。
- 连接失败不清空数据：保留上次快照，badge 变 `连接失败`（虚线青绿）+ `#connection-state` 给出原因；首次加载即失败显示 `数据不可用` 并在运行说明写入原因。恢复后自动回到 `来源：<provenance>`。
- `provenance` / `acceptance` / `source_label` / 任务 / 事件 / Gene / 指标等原有功能与 DOM id 全部保留；replay/mock/live 标注沿用 app.js 既有逻辑。
- EvoMap：独立只读 `/api/evomap`，首次进入信息界面读一次 + 手动刷新按钮（不轮询）。面板递归渲染嵌套契约（如 `community_search.assets`、`local_pool.genes`、source/cache/失败字段），404 显示“尚未提供”，永不并入运行拓扑。

## 验证

- `cd viz/frontend && npm ci && npm run build`：通过，产物 `viz/static/assets/finals-shell.{js,css}`（207.95 kB / 63.05 kB）。
- `node --check viz/static/app.js`：通过。
- 真实浏览器冒烟（playwright-core + chromium_headless_shell-1234，`python -m viz.server --port 7583 --input demo/data/mock-run.json`）：首屏仅大字+双标识、页头页脚隐藏、CRT 0.04、首页无全局光标；点击/键盘反复切换；swarm 视图图表激活重绘、空态真实；CRT 开关+localStorage；503 时数据保留+反馈、恢复；EvoMap 404 态与手动刷新 1 次；reduced motion 无转场无自定义光标；`#/swarm` 深链；0 页面错误。

## 限制与移交

- P/T/E 轨文件本分支尚不存在：首页为 CSS 降级漂移场（非模拟），拓扑为既有 ECharts 降级视图，`/api/evomap` 为 404 态。合入后由集成轨重建 `finals-shell.*` 并做真实浏览器验收。
- 失败语义从“清空为未知”改为“保留上次快照+反馈”（用户指令优先）：`tests/integration/check_finals_replay.cjs` 的 `checkReset` 与 `check_stack_behavior.cjs` 的失败断言（`数据不可用` 后清空）与此冲突，且这些测试假设首屏即数据页；测试归各自 owner，需由集成/测试轨加“点击 AGENT SWARM 或 `#/swarm`”前置并更新失败断言。
- 预存问题（未改，E 轨文件）：`viz/server.py` except 分支 lambda 引用已销毁的 `error` 变量，根 `node_modules/echarts` 缺失时 `/api/dashboard` 500；本地 `npm ci` 后正常。
- 未新增 npm 依赖；`package*.json` 未变。未启动任何付费任务。
