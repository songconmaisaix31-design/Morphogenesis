# V 轨：去中心化 Swarm 只读视图适配（frontend-swarm-viz）

基线分支：`songconmaisaix31-design/morph-swarm-viz`（本 worktree）。唯一 write_paths：`viz/**`、`tests/t5/**`、本文件。

## 交付物

- `viz/swarm_adapter.py` — 复用 `swarm.observer.observe` 的严格只读结果，投影为 JSON-only `SwarmView`（schema `morph.swarm.readonly/1`）。
- `viz/server.py` — 新增 `/api/swarm` 端点（沿用现有只读安全：GET/HEAD、nosniff、no-store、拒绝请求体、不记 query），新增 `--swarm-state` CLI 参数。
- `viz/frontend/src/swarm/derive.js` — 新增 `deriveSwarmView` / `layoutSwarmNodes` / `LEASE_LABELS` / `RESERVATION_LABELS` 纯派生。
- `viz/frontend/src/swarm/SwarmTopology.jsx` — 新增 `SwarmFacts` 视图：worker/能力节点 + 路由边（读时衰减权重）、任务与租约、`depends_on` 依赖、预算预留、审计流、资产采用链；`swarm` prop 存在真实数据时取代彩排拓扑，否则回退原彩排派生。
- `viz/frontend/src/App.jsx` — 独立轮询 `/api/swarm`（失败保留旧快照，不回退空白）。
- `viz/frontend/src/backend/Backend.jsx` — 透传 `swarm` 到拓扑视图。
- `viz/frontend/src/swarm/swarm.css` — 去中心化视图样式。
- `tests/t5/test_swarm.py` — 13 项投影/端点/只读测试。
- `viz/static/assets/finals-shell.{js,css}` — 由 `npm run build` 重建（`viz/frontend` 构建链 → `viz/static`，`emptyOutDir:false` 不触碰 app.js / echarts / licenses）。

## 事实来源与只读边界

只消费 `swarm.observer.observe(state)` 暴露的原始表（`tasks`/`dependencies`/`task_attempts`/`task_audit`/`pipe_history`/`pheromones`/`preference_config`/`swarm_budgets`/`budget_reservations`/`adoptions`/`approvals` 及 `workers`/`audit` JSON）。绝不写 swarm 状态：不创建/认领/推进任务，不改租约、预算、审计或验证；不调用任何模型。

- **租约态**为读时分类（非动作）：`completed`/`failed`（终态）→ `leased`（claimed 且未过期）/`expired`（claimed 已过期）/`partial`（submitting）/`handoff`（available 且历史尝试涉及多 worker）/`available`。
- **路由权重**按 `swarm/pheromone.py` 语义读时衰减：`pipe_history.weight * exp(-dt/tau)`；`pheromones.concentration * exp(-dt/(tau/multiplier))`；`tau` 取 `preference_config`（缺省 86400）。原始值与衰减值并存，不覆盖源数据。
- **预算预留态**：`pending→reserved`、`settled→settled`、`uncertain→unknown`；保留 `breaker`、`admission_control` 与 totals，费用未知保留 null。
- **资产采用链**：`adoptions`（`AdoptionReceipt` 全文）按 `asset_id` 可追溯；`approvals`（晋级）单列，不从未知 payload 推断 asset_id。
- **验收**固定为 `provenance=mock`、三态全 `not_run`（本地快照绝不升级 live 声明）；Hub 状态固定「待发布（未配置 Hub 沙箱）」。

## 改动映射

| 文件 | 改动 |
|---|---|
| `viz/swarm_adapter.py` | 新增：`load_swarm` / `project` / `empty_swarm` / `SWARM_SCHEMA`；各 section 投影函数 |
| `viz/server.py` | `DashboardHandler` 增加 `swarm_loader`（默认 None）；`do_GET`/`do_HEAD` 增 `/api/swarm`；`main` 增 `--swarm-state` |
| `viz/frontend/src/App.jsx` | 增 `swarm` state 与 `/api/swarm` 轮询；透传 `swarm` |
| `viz/frontend/src/backend/Backend.jsx` | `Backend`/`TopologyPanel` 增 `swarm` prop |
| `viz/frontend/src/swarm/derive.js` | 增 `deriveSwarmView` 等纯派生 |
| `viz/frontend/src/swarm/SwarmTopology.jsx` | 增 `SwarmFacts`；`swarm` prop 分支 |
| `viz/frontend/src/swarm/swarm.css` | 增去中心化视图样式 |
| `tests/t5/test_swarm.py` | 新增测试 |
| `viz/static/assets/finals-shell.{js,css}` | `npm run build` 产物 |

## 验证命令与结果

- `python -m pytest tests/t5 -q` → **66 passed**（含新增 13 项）。
- `python -m mypy` → **Success: no issues found in 20 source files**（`viz` 不在 mypy `files` 范围内，未纳入；未改 pyproject.toml）。
- `cd viz/frontend && npm ci && npm run build` → **built in 1.19s**（49 modules，`finals-shell.js` 228.04 kB / `finals-shell.css` 70.53 kB）。
- 端到端 `/api/swarm`：`swarm.cli.seed_demo` 生成真实 state（6 任务 + 6 pheromone 信号）→ `load_swarm` 投影 → 真实 HTTP handler 返回 200、schema 正确、6 任务，`acceptance` 全 `not_run`、hub `待发布`。
- 完整 `swarm.cli.demo`（fixture executor，mock provenance，无模型调用）在本 worktree 生成 3 worker / 6 task / 3 budget 预留 / 15 审计事件 / 3 worker 审计记录，`load_swarm` 忠实投影（租约态 available/expired）；本环境 demo 自身 `completed_tasks=0`，属后端运行域问题，非本轨，`task_live` 保持 `not_run`。

## 真实限制

- 未配置 `--swarm-state` 时 `/api/swarm` 返回 `health=missing` 的空视图；前端据此回退到原彩排拓扑，不空白页面。
- `load_swarm` 指向不存在目录时 `health=partial`（沿用 observer 语义），与 `empty_swarm` 的 `missing`（未配置）区分。
- 本 worktree 无已提交 `.venv`/`node_modules`；测试使用 `decentralized-swarm/.venv` 的锁定解释器（`<decentralized-swarm>/.venv/Scripts/python.exe -m pytest ...`），前端 `viz/frontend/node_modules` 由 `npm ci` 从锁定 `package-lock.json` 重建（未改锁）。
- 未调用任何模型、未连接 Hub、未伪造 `interface_live`/`task_live`；provenance 恒为 `mock`。
- Windows 下只读 SQLite 连接关闭后短暂文件锁，测试用 `TemporaryDirectory(ignore_cleanup_errors=True)` 延迟清理，属环境行为，非本轨缺陷。

## 未执行项

- 未运行 `tests/integration/*.cjs`（需 `MORPH_PLAYWRIGHT`/`MORPH_CHROMIUM` 环境）。
- 未启动真实 swarm 多进程完成态做浏览器截图；视图以投影测试 + `seed_demo` 端到端 HTTP 核对。
- 未改 `swarm/`、`local_assets/`、`contracts/`、`docs/SWARM_*.md`、锁文件。
