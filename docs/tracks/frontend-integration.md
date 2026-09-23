# 前端重构集成轨（I）

2026-09-23；I 分支 `songconmaisaix31-design/morph-front-integration`，基线 `972d4bab8b7a86d11ae74b850fe013710b58ace5`。按协调者交付的精确 SHA 普通 `--no-ff` 合并，保留历史；只做集成胶水与 `tests/integration`，领域缺陷退回原 Worker。

## 合并清单

| 轨 | 来源分支 | 精确 SHA | 合并提交 | 冲突 |
|---|---|---|---|---|
| E EvoMap 只读闭环 | `songconmaisaix31-design/morph-front-evomap` | `8275f578ae2aaaf81a044beeaebd453d2e72f31a` | `fe09589` | 无 |
| T 真实拓扑视图 | `songconmaisaix31-design/morph-front-swarm` | `ee65171934595cc5fb21d608bc52a3e5f760c786` | `af740e9` | 无 |
| P WebGL2 黏菌首页 | `songconmaisaix31-design/morph-front-physarum` | `f5448b8f59ce7a592fc0bf38de002a47b333672d` | `af1578d` | 无 |
| E 最终增量（降级 loader 修复 + categories） | 同上 | `4da31ebd2988cffc9a204bba6c6d82230014feed` | `3b0bd00` | 无 |
| S 页面壳 + EvoMap 探索器（协调者确认最终） | `songconmaisaix31-design/morph-front-shell` | `ab24fb539cb199b1d298cbd08733750cd72e8b8a` | `1ea0f19` | 无 |
| E cache_age 契约修复（live→null、非负钳制） | 同上 E 分支 | `89b0d65fdd209c2357f3f1c1aed15ad566d95139` | `5f332f2` | 无 |

全部五批合并且四轨最终 SHA 均已并入；均为协调者交付/确认的精确 SHA，普通 `--no-ff` 合并，无冲突、零胶水改动。`viz/static/assets/finals-shell.{js,css}` 由集成轨在四轨合并后统一 `vite build` 重建（3906 模块，247.84 kB JS / 71.15 kB CSS）。

## `/api/evomap` 集成审查结论

- 端点 `GET /api/evomap`（`morph.evomap.readonly/1`）为服务端只读闭环：社区搜索走官方公开只读 `GET https://evomap.ai/a2a/assets/semantic-search`（与锁定的 `@evomap/gep-mcp-server` 1.7.0 同路由），单次请求不重试，进程内按查询键缓存（TTL 300s），状态明确区分 `live / cache / stale_cache / error`。
- 输入边界与官方 MCP 工具 schema 一致：`q` 1–500 字符、`type` 仅 Gene/Capsule、`limit` 1–50；越界返回 `400 {"schema","error":"invalid_query","detail"}`，远端响应文本不进入报告，错误为固定码。
- `MORPH_EVOMAP_API_KEY` 只以布尔 `api_key_configured` 报告配置与否，从不读取、发送或记录密钥；本机未配置时如实为 `false`。
- `local_pool` 以 stdlib sqlite3 `mode=ro` 打开运行存储，Gene 正文经共享 `contracts.resolution.Gene` 契约重验；未配置 `--evomap-store` 时如实 `unconfigured`。字段白名单投影，未知键丢弃不补全。
- 响应含固定 `boundaries` 声明：EvoMap 是来源上下文，不是本项目运行拓扑/任务事实，符合计划"页面不得将其写成运行拓扑事实"。
- 结论：无需集成胶水改动；`viz/server.py` 路由接入（`urlsplit` + `parse_qs`，`max_num_fields=8`）与既有 `/api/dashboard` 互不影响。

## 验证命令与结果

全部从本 I worktree 运行；Node 依赖 `npm ci --ignore-scripts --no-audit --no-fund` 安装，锁文件未变。验证服务器只用 7799 端口，未触碰 7526/7527。

| 命令 | 实际结果 |
|---|---|
| `git merge --no-ff 8275f578…` / `… ee651719…` / `… f5448b8f…` / `… 4da31ebd…` | 四轨均干净合并，无冲突，无胶水改动 |
| `python -m pytest tests/t5/test_evomap.py -q` | 18 passed |
| `python -m pytest tests/t5 tests/integration -q`（合并 T 后） | 36 passed，1 failed 为预存环境问题（见下） |
| 同上（合并 E 最终增量后） | 41 passed，同 1 个预存环境失败 |
| `python -m viz.server --port 7799 --input demo/data/mock-run.json` 后 `curl /api/dashboard` | HTTP 200；保留 `provenance`、`acceptance`、`source_label` 等原有全部键 |
| `curl "/api/evomap"`（默认参数） | HTTP 200；首次 `state=live` 真实命中 Hub 返回真实社区 Gene 资产，相同查询再请求为 `state=cache`；`api_key_configured=false`、`local_pool=unconfigured` |
| `curl "/api/evomap?limit=99"`、`?type=Bad` | 均 HTTP 400 `invalid_query` |
| 全新服务进程 7802 首请求 `curl "/api/evomap?q=repair&limit=1"` | search 与 categories 均 `live`；第二请求均 `cache`，live→cache 状态机正确 |
| `curl "/api/evomap?q=topology&type=Gene&limit=3"`（E 增量后） | HTTP 200；`community_categories` 真实 Hub 计数（by_type: Gene 2509437 / Capsule 2505905 / EvolutionEvent 2094531；by_gene_category: optimize 376082 / repair 342783 / innovate 269904），`hub.categories_endpoint` 如实标注 |
| `python -m pytest tests/t5 tests/integration -q`（全部合并后） | 44 passed，同 1 个预存环境失败 |
| `npm run build`（viz/frontend，合并四轨源码后集成重建） | vite 5.4.21 成功；`finals-shell.js` 247.84 kB / `finals-shell.css` 71.15 kB；锁文件未变 |
| `MORPH_PLAYWRIGHT=… MORPH_CHROMIUM=… node tests/integration/check_frontend_integration.cjs http://127.0.0.1:7899 .runtime/front-integration/final` | **27 passed / 0 failed**（真实 Chromium 1366×768，headless；证据截图+summary.json 在 `.runtime/front-integration/final/`，已亲看） |
| `node tests/integration/check_frontend_replay.cjs http://127.0.0.1:7898 .runtime/front-integration/replay replay`（7898 为本轨独立 `--replay` 服务，读既有真实证据 `morph-rehearsal-40f04885…/rehearsal.json`，未触碰 7527） | **23 passed / 0 failed**（证据 `.runtime/front-integration/replay/`，已亲看） |
| `node tests/integration/check_frontend_replay.cjs http://127.0.0.1:7897 .runtime/front-integration/nodata nodata`（7897 为无数据源服务） | **9 passed / 0 failed**（证据 `.runtime/front-integration/nodata/`，已亲看） |

浏览器验收覆盖（final 轮，E cache_age 修复合并后）：首屏唯一大字 MORPHOGENESIS + 真实 WebGL 黏菌 canvas（无降级）；标题覆盖区域多点 pointermove 无 pageerror；首屏设计性隐藏 header、hero AGENT SWARM 标记可点；切换后 header 导航可见、`/api/dashboard` 来源如实 `mock`；T 拓扑模块加载、mock fixture 无彩排快照时如实空态（"模拟快照" 徽标，0 虚构节点）；验收三态与来源条呈现；EvoMap 面板首次进入自动加载一次（live · 实时）、Hub 来源行如实（公开只读、API key 未配置）、16 个类别真实计数、6 条边界声明、本地池如实未配置；手动两类有效查询（q=optimize limit=5 与 q=repair type=Capsule limit=5）均 live 返回真实资产（sha256 asset_id）；EvoMap 数据不进入拓扑面板；5 次标记切换 + 键盘 1/2 无重复 id、无 pageerror（S 重复切换 effect 修复复核）；CRT 开关可切换且 localStorage 持久化；reduced motion 下静态降级 + CRT 静止 + 切换正常；浏览器全程仅同源请求（Hub 访问只发生在服务端）。

回放验收覆盖（真实第五轮证据，独立 7898 端口 `--replay`）：页头与拓扑徽标均为"回放视图 · 原始证据只读"；验收三态 `contract_local=passed / interface_live=not_run / task_live=not_run` 且 provenance=replay，回放从不冒充 task_live；拓扑 5 个节点身份与 `/api/dashboard` 的 members+pipes 逐一相等（planner#0 / builder#0 / builder#1 / reviewer#0 / aggregator#0）；边数 2 与 active 计数 1 均与 pipes 一致；HUD 阶段/快照号/任务 ID 来自快照（彩排完成 · #19 · recovery-rehearsal-d67607bc…）；ghost 横幅如实呈现 builder#0 下线原因、重路由 builder#1 及"恢复任务已成功"（字面短语仅在真实成功结果存在时出现）；点选全部 5 个节点详情均引用各自键与真实事实；事件流 20 行与 rehearsal.history 等长、最新 #19 在前；checkpoint 大数字 3/3 · 100% 与快照 checks（clamp/mean/unique 全通过）逐一相等；tokens 大数字 1226 来自真实 result usage；Gene 台账 2 卡均"已归档"与快照 archived_at 一致；管道列表 2 行权重/流量/在线态与 pipes 一致；下线卡片含真实原因与恢复选路。

无数据验收覆盖（协调者 provenance 视觉核对）：`empty_dashboard` 语义 provenance=live + source_label=未加载导出。实测页头"来源：live"与"未加载导出"同屏并列，拓扑明确"AGENT SWARM · 空态"+"未加载彩排快照；不展示预设节点或边"，Gene/谱系/消息/指标/事件各区空态文案均如实，验收三态全 not_run，零虚构节点边。**结论：不构成误导，无需胶水修改，不改后端 provenance 语义**；唯一可斟酌点为空态拓扑徽标沿用 provenance 文案"现场快照"，已作可选建议记录，不改动。nodata fullPage 截图曾现 hero 叠影，经视口复测确认为 fullPage 拼接伪影（隐藏视图 visibility:hidden/opacity:0，实际交互无叠影）。

live 标注：上表真实出站仅为公开只读 `semantic-search` 与 `categories` 的 GET（E 轨已验证授权的既有路径，无密钥、无写操作）；回放轮只读既有真实证据文件，不修改原件、不冒充 task_live；其余均为本地契约。回放/mock/live 未混用。验证只用 7799/7801/7802/7897/7898/7899 动态端口，结束后均按命令行核对精确关闭；7526/7527 进程全程未触碰（7527 仍由协调者管理运行中）。曾观察到一次首请求 categories 误标 `cache`，受控复验（进程内双请求 + 全新真实服务进程首请求）均未复现，判定为该次 7799 进程残留请求的观测假象而非代码缺陷。

## 预存问题（非本次合并引入，已核对基线）

- `viz/server.py` 异常闭包 `lambda: empty_dashboard(f"输入未加载：{error}")` 在 `except` 块外访问被清除的 `error`，输入加载失败或缺少 `node_modules/echarts` 时 `/api/dashboard` 每次请求抛 `NameError`。基线 `972d4ba` 第 107 行已存在；已由 E 增量 `f354f11` 修复（`degraded_loader` 立即绑定原因字符串），集成侧复核通过。
- `tests/integration/test_demo_environment.py::test_demo_excludes_sentinel_from_viewer_and_passes_executor_args` 在本机失败：`shutil.copy` 找不到 `C:\Python313\pyvenv.cfg`（本机 Python 安装无此文件）。在 E 轨合并前内容（`8275f57` worktree）复跑同样失败，属环境预存。
- `tests/t1` 38 errors + 5 failed：Node 桥子进程 `sdk_process_failed` 等，集中在 hub/bridge，与本次合并文件无交集（合并只触及 `viz/`、`tests/t5`、`docs/tracks`），判定为环境预存。

## 契约偏差（已修复并复核）

- `morph.evomap.readonly/1` 文档写明 `cache_age_seconds: null = 本次为 live`；初版实测 `live` 响应携带负数 age。报协调者后由 E 轨以 `89b0d65f` 修复（live→null，cache/stale 钳制非负）；集成侧复核：t5 新增用例通过，最终浏览器轮查询行不再出现负数缓存年龄。

## 交付说明

- 本轨改动仅限：合并提交、`tests/integration/check_frontend_integration.cjs` 与 `tests/integration/check_frontend_replay.cjs`（新增验收脚本）、`viz/static/assets/finals-shell.{js,css}`（计划规定的集成重建）、本文件。未改任何轨道领域代码、锁文件或 CI。
- 证据类别：contract_local + 明确 mock fixture + 只读 replay（既有真实证据，原件未动）+ 真实公开只读 Hub GET（无密钥/写操作）。未发起新付费任务；interface_live/task_live 在本轮浏览器验收中保持页面如实 `not_run`。
- 验收端口 7799/7801/7802/7897/7898/7899 均已在结束后按确切命令行核对并关闭；7526/7527 进程全程未触碰。

## 2026-09-23 最终 S/E 增量集成

- 依协调者交付的精确 SHA，先普通 `--no-ff` 合并 E `6046ab8b36a6963db56cfb11452dd587510cf39a`（合并提交 `5d6b8d7`），再普通 `--no-ff` 合并 S `26b6e1a19b7307a0041817fd298f6d065e81a344`（合并提交 `4a87b58`）。唯一冲突是两份规定由本轨统一产出的 `viz/static/assets/finals-shell.{js,css}`；以合并后 S 源码重新执行 `cd viz/frontend && npm run build` 解决，Vite 5.4.21 成功（JS 255.78 kB，CSS 72.51 kB）。未改领域源码、锁文件或后端语义。
- `python -m pytest tests/t5 tests/integration -q`：**58 passed**；唯一失败仍为预存本机环境问题：`tests/integration/test_demo_environment.py` 复制 `C:\Python313\pyvenv.cfg` 时该文件不存在。`node --check tests/integration/check_frontend_integration.cjs` 与 `git diff --check` 通过。
- 更新本轨验收脚本：真实 Chromium mock 页面新增 375×768 hero 边界/无横向溢出检查，以及真实公开只读 GET 下分别点击 Gene 与 Capsule 后的 `/api/evomap/asset` 详情、时间线、分支状态检查；空数据脚本按 S 已确认语义，在没有任何已加载快照时以 `source_label=未加载导出` 替代 raw `provenance=live` 的展示，避免把“未加载”说成现场结果。
- 实际浏览器验收均在本轨隔离端口完成，浏览器路由限制为同源，Hub 请求只由本地服务端发起。`7899 --input demo/data/mock-run.json`：**31 passed / 0 failed**（1366×768、375×768、WebGL 食物鼠标、转场 0.34s 后 inactive Physarum `visibility:hidden`、反复视图切换、Gene/Capsule asset detail/timeline/branches、无 JS error）；稳定态截图为 `.runtime/front-integration/final-settled-rerun-20260923/05-final-swarm.png`，已亲看，无首屏叠层。`7897` 无数据：**9 passed / 0 failed**（零虚构拓扑，三项 acceptance=not_run）；`7898 --rehearsal C:/Users/DW/AppData/Local/Temp/morph-rehearsal-40f04885b37e489fa3ea1a04f61a984d/rehearsal.json --replay`：**23 passed / 0 failed**（既有真实证据只读回放、来源/节点/管道/checkpoint/tokens/Gene 与 API 同源事实逐项相符）。截图及 JSON summary 位于 `.runtime/front-integration/{final-settled-rerun-20260923,nodata-rerun-20260923,replay-20260923}/`，不入库。
- 证据边界：mock 页面仍是 `mock`；空数据不等于 live 任务；回放只是既有真实证据的只读显示；本轮唯一对外访问是 EvoMap 官方公开只读 GET（无 API key、无写操作），不构成 `task_live` 或物理投影验收。7526/7527 未触碰。
