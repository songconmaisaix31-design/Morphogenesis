# V 轨：去中心化 Swarm 只读视图适配（frontend-swarm-viz）

基线分支：`songconmaisaix31-design/morph-swarm-viz`。唯一 write_paths：`viz/**`、`tests/t5/**`、`tests/integration/check_swarm*.cjs`、本文件。

## 交付物

- `viz/swarm_adapter.py`：复用 `swarm.observer.observe` 的严格只读结果，投影 JSON-only `morph.swarm.readonly/1`；输出来源可用性、worker/任务/租约、信息素/路由、预算、审计和采用谱系。
- `viz/server.py`：提供只读 `/api/swarm`；观察异常返回稳定的 503 JSON。`--swarm-state` 绑定当前本地状态，`--swarm-replay` 明确把复制快照标为历史回放。
- `viz/frontend/src/App.jsx`：独立轮询 `/api/swarm`，显式区分 loading、missing、error、ready、empty 和 stale；失败时旧事实只以“陈旧快照”继续显示。
- `viz/frontend/src/swarm/{derive.js,SwarmTopology.jsx,swarm.css}`：只用 `/api/swarm` 构建 worker、能力、任务、租约、依赖、衍生、信息素、路由和资产采用关系；不再回退 `/api/dashboard` 彩排拓扑。大状态按实体类型每组最多 8 个分页显示，公开显示“当前/总数”，全部任务仍保留在事实列表。
- `tests/t5/test_swarm.py`：覆盖只读投影、缺失目录、来源状态、HTTP 错误、replay，以及 sparse/mock/mixed provenance 不得升级全局验收。
- `tests/integration/check_swarm_browser.cjs`：真实 Chromium 检查 16 worker/96 task、stale/recovery、missing、first-load error 及 1366/1920/375 宽度，并验证键盘 Enter/Space 选择、Escape 关闭、拓扑分页和全部节点类型可达。
- `viz/static/assets/finals-shell.{js,css}`：由锁定前端构建链重建。

## 事实与边界

- 只消费 observer 暴露的 SQLite/JSON 事实；不创建、认领或推进任务，不改租约、预算、审计或验证，不调用模型。
- 路由权重按 `weight * exp(-dt/tau)` 读时衰减；信息素按 `concentration * exp(-dt/(tau/multiplier))` 读时衰减，保留原始值。
- `pending`、`settled`、`uncertain` 预算记录分别显示为 reserved、settled、unknown；未知模型费用保持 `null`/未知。
- `unknown_cost_allowed` 独立显示为“费用未知 · 允许继续”；已确认 tokens 不冒充账单结算，原保留额度继续计入 financial hold，费用不显示为 0。
- per-worker audit 只用于标记记录来源。即使单条 live/mock 记录自报 passed，也不能证明多进程或全蜂群验收，聚合 `contract_local`、`interface_live`、`task_live` 均保持 `not_run`。
- 全部 worker audit 同源时聚合 provenance 可显示 `live` 或 `mock`；混合或缺失为 `unverified`；显式 `--swarm-replay` 一律显示 `replay` 并保留原始 worker audit 供追溯。
- Ghost 仅指成员变化后仍可追溯的路由偏好、任务依赖和实际采用经验，不宣称涌现或收敛。
- Hub 状态固定为“待发布（未配置 Hub 沙箱）”。

## 验证结果

- 锁定 Python：`OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 C:/Users/DW/orca/workspaces/Morphogenesis/decentralized-swarm/.venv/Scripts/python.exe -m pytest tests/t5 -q` -> **74 passed**。
- 前端：`cd viz/frontend && npm run build` -> **49 modules transformed**；`finals-shell.js` 218.85 kB，`finals-shell.css` 72.63 kB。
- Chromium：设置协调器提供的 `MORPH_PLAYWRIGHT` 和 `MORPH_CHROMIUM` 后运行 `node tests/integration/check_swarm_browser.cjs` -> `{"ok":true}`。
- 浏览器覆盖：1366x900、1920x900、375x812；16 worker/96 task replay 拓扑、第二页可达、键盘选择/Escape、503 后 stale 保留并恢复、missing 空态和 first-load error；无控制台/page error，无横向页面溢出。
- 截图：`%TEMP%/morph-swarm-viz-browser/swarm-{1366,1920,375}.png`、`swarm-missing.png` 和 `swarm-error.png`。当前模型运行时不能渲染附件，因此未声称人工像素审阅。

## 真实限制

- 未连接 Hub、未公开部署、未调用真实远端接口或模型；integration owner 负责部署 COPY/allowlist/nginx glue。
- `live` 只表示源 worker audit 的 provenance，不表示当前进程仍在线，也不升级 aggregate acceptance；复制状态必须用 `--swarm-replay`。
- 浏览器测试使用真实构建产物和 Chromium，但以本地 HTTP fixture 提供边界完备的 `/api/swarm` 状态，不冒充真实 swarm 运行验收。
- 未修改 `swarm/**`、`local_assets/**`、锁文件或部署配置。
