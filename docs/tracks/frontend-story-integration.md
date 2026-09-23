# 沉浸式序幕与后台独立集成

基线 `ab87ba17625bf27afdaa840e898d48bb5db0003b`。普通精确 SHA 合并 G `3573db8584d5ae5d94b1b69d8628404e06da29d9`、B `00ad5ee63ff72e5c031438e7b08b4433d68a7682`、S `b9421e1bffa66fcf8e2ccc925905bdda2720cb4f`，并合入主线计划与状态 `6024b61a68774ef37c4cc50cd7179eef0d4f712f`（含 `96e1fd6171edd15959ce8027b304909848372203`）。S 轨根据首次截图的 CTA 初现对比度问题，在自己的工作树提交返修 `b4ac80e18cb8341abd21b7fb6f0a1e84a36144d4`，本轨再次普通合并。均无文件冲突。本轨只重建 `viz/static/assets/finals-shell.css/js`，新增浏览器验收脚本，未改 G/B/S 领域源码。

## 验证

- 根目录 `npm ci --ignore-scripts`、`viz/frontend` 下 `npm ci` 和 `npm run build`：通过；Vite 处理 3908 模块，静态 CSS/JS 重建。`npm ci` 仅安装锁定依赖，未更新锁文件。
- `python -m pytest tests/t5 -q`：51 passed。
- 隔离端口 7810：`python -m viz.server --port 7810 --input demo/data/mock-run.json`；在真实 Chromium 跑 `tests/integration/check_frontend_story.cjs`，18 项断言通过，无页面脚本错误、站外请求或意外 HTTP 失败。截图位于 `%LOCALAPPDATA%/Temp/morph-story-integration-final-3/`。之后在 7799 同一工作树预览再跑新增控制台检查，19 项通过；仅有测试故意为 EvoMap 返回 404 所产生的预期资源日志，无其它控制台错误。该次截图位于 `%LOCALAPPDATA%/Temp/morph-story-integration-console-2/`。
- 人工查看 1366×768 的黏菌、拓扑生长、产品名/CTA、后台关键帧，1920×1080 的后台，375×812 的 reduced-motion 序幕与后台。黄色原生 Physarum 背景和小字、黑底概念拓扑及标注、双语大标题、显式 CTA、后台三栏和手机单列布局可见；无横向溢出。CTA 到达可点击阶段即完整可读，键盘焦点和 hover 可用。
- 浏览器验证旧 `#/swarm` 深链进入后台，新 `#/workspace` 深链可用；mock 来源与 `contract_local` / `interface_live` / `task_live` 三态保留。fixture 无彩排拓扑快照，后台真实拓扑如实空态。EvoMap 请求在该浏览器测试中以本地 404 代替，验证请求与错误隔离而非真实 Hub 成功。旧 `check_frontend_integration.cjs` 依赖已被本次用户目标取代的 marker、CRT 和键盘 `2` 交互，不再是适用验收。

本次仅是本地 mock 布局和交互验收；没有新真跑、物理展示、真实 Hub 发布或外部任务验收。参考 ZIP 只用于观察布局，没有复制源码、字体、素材或文案。
