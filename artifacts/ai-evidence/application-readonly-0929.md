# C 轨只读应用盘点与交付 · 2026-09-29

Owner: codex。工作树 `morph-readonly-app-0929`，开工分支同名，HEAD `2957b408ce922369a595a8acd43a882eb85897d3`，开工 `git status --short` 空。remote `origin=https://github.com/songconmaisaix31-design/Morphogenesis`。本轮不碰根树 WIP、FC、锁文件或 TASKS。

## 事实源与复用盘点

已读取 AGENTS、PLAN、source/README 权威顺序、统一对齐与多轨规则、v2 的身份/采用/来源要求、FRONTEND_REFACTOR_PLAN、既有界面轨报告，以及指定 release-readiness / algorithm-baseline 两份 0929 审查。审查均允许受限只读应用先行，不能冻结 FC；本工作树是第一代应用基线，不是 FC 联合候选。

| 现有能力 | 基线证据与边界 |
|---|---|
| 同源只读仪表盘 | `viz/server.py` 已提供 `/api/dashboard`，可读取 `--rehearsal --replay`、`--t2-root`、Envelope/mock 导出；无需新 API。 |
| 有类型彩排 | `orchestration/rehearsal_models.py` 的 RehearsalDocument/current/history；`viz/adapter.py:81-118` 通过原 read_rehearsal 转 replay，并原样导出 UseRecord。 |
| 契约与来源 | `viz/adapter.py:121-164` 校验 Acceptance/RehearsalDocument/TaskResult，mock/replay 的 interface_live/task_live 必须 not_run。 |
| 任务与拓扑 | `viz/static/app.js:156-170,205-291` 显示阶段、检查点、成员和未知 tokens；`viz/frontend/src/swarm/SwarmTopology.jsx:89-105` 已有成员任务/事件/Gene 摘要。 |
| Gene 与采用 | `viz/static/app.js:129-153,294-306` 有生命周期、计数、Gene→采用成员图；成员详情已列 Gene ID/版本/采用时间。不得重造这些能力。 |
| 真实采用契约 | `metabolism/models.py:71-77` UseRecord 包含 run_id、AttemptId、GeneRef、used_at、provenance；`contracts/identity.py:17-20` AttemptId 保留 task/agent/attempt。T2 导出也已支持 adoption.json（adapter:310-346）。 |

## 单一交付与授权

在现有 Gene 池增加可展开的采用记录明细：直接消费 dashboard.adoptions，每条记录展示完整 Gene/版本、run、task、成员、attempt、时间和 provenance；空列表明确无记录，缺失字段显示未知，绝不从注入/计数/图连线推断采用。现有视图仅以成员和 Gene 概述采用，不能从页面对应到采用发生的具体任务与尝试；这是现行多轨说明 §3.7 和三层身份要求的展示缺口。

本 Dispatch 的阻塞 ask 在开工十分钟内发出，主控明确批准“现有 Gene 池的可展开采用明细”，并赋予以下精确 write_paths：`viz/frontend/src/backend/Backend.jsx`、`viz/frontend/src/backend/backend.css`（仅必要布局可访问性）、构建产物 `viz/static/assets/finals-shell.js` / `finals-shell.css`、`tests/t5/check_adoption_trace.cjs`、本报告及 ignored `.runtime`。后端修改路径为空；不改 adapter、契约、static/app.js 或 API。另批准两个 ignored node_modules junction 及既有 Python/Playwright/Chromium 的只读复用，不安装、不改锁。

实施于 `Backend.jsx:21-49,148`：原生 details/summary + dl 消费 dashboard.adoptions，保留每条记录，不过滤未知值、不按 Gene/成员合并；资产为空显示未知；时间按明确 UTC 格式展示。缺失列表与空列表区别呈现，attempt=0、instance=0、epoch=0 保留。使用既有 React 数据轮询与失败保留逻辑、原导航和桥接 DOM；没有新增 fetch、日志 Schema、状态机、调度或控制入口。`backend.css:79-84` 仅 6 条新明细换行/栅格规则，焦点直接复用既有 summary:focus-visible。

复用来源：React 18.3.1、Vite 5.4.21、@vitejs/plugin-react 4.7.0 均为已锁定 MIT 依赖；既有 Linear 用户包移植布局沿用 `THIRD_PARTY_NOTICES.md` 的来源说明（原包版本/再分发许可未核实，不重标开源许可证）。本次没有复制外部代码或引入新依赖。使用了 orca-cli / orchestration 与 React best-practices 技能。

## 实际验收与退出

本地证据目录 `L=.runtime/application-readonly-0929/`（ignored）。本树本来没有 .venv/node_modules；主控授权后只读使用 `P=C:/Users/DW/orca/Morphogenesis/.venv/Scripts/python.exe`，并核实 import 的 viz.adapter 路径是**本工作树**。本树两个 node_modules junction 指向根树对应已存在绝对目录，创建前确认不存在且被忽略。两份 package-lock 和 poetry.lock 与根树逐字节校验一致；没有依赖安装或共享环境修改。Python 使用 `-B` / PYTHONDONTWRITEBYTECODE，pytest cache/basetemp、临时 Vite 配置与浏览器 TEMP/TMP 均在 L。

真实历史原件 `S=C:/Users/DW/AppData/Local/Temp/morph-sol-20260924-e27e2dc198664413a2a8333b236bd123/rehearsal.json`；rehearsal ID `rehearsal-85ff3bf872d941aa9eade0ddc92cd485`。当前重新读取并校验原件，20 个历史快照、1 条采用，原件来源 live；通过原 loader 的 replay 降级后再提供页面。原文件前后 SHA256 均 `bc6c277cf0cebeb899bce98f312ca2e102771bb0d0ad07607e84c41eccea0916`。这只是原件完整性检查，非自建证明系统。

| 命令（均在本树；L/P/S 如上） | 实际结果 / 原件 |
|---|---|
| `P -B -m pytest -q tests/t5 -o cache_dir=L/pytest-cache --basetemp L/pytest-temp` | **53 passed，exit 0**；`L/pytest-t5.log`。 |
| 在 viz/frontend：`node node_modules/vite/bin/vite.js build --config ../../L/vite.config.mjs` | **49 modules，exit 0**；CSS 69.25 kB、JS 219.19 kB；`L/build.log`。运行时字体 URL 的原有提示不影响 build，实际浏览器本地字体加载检查通过。临时配置只把原配置的两个 import 改成现成依赖绝对 file URL，防止 Vite 临时配置落到非授权源码目录；构建仅改变两个获准生成文件。 |
| `node --check tests/t5/check_adoption_trace.cjs`、`git diff --check` / staged check | **exit 0**；Git 仅提示既有 CRLF 转换。 |
| `P -B -m viz.server --host 127.0.0.1 --port 7859 --rehearsal S --replay` + `P -B L/check_contract.py` | **契约检查 exit 0**；实际 HTTP JSON == 原 load_rehearsal(..., replay=True)，RehearsalDocument / Acceptance / UseRecord 均校验、原始身份字段保留、cost_usd=null、原件未改；`L/contract.log` / `dashboard.json`。 |
| `node tests/t5/check_adoption_trace.cjs http://127.0.0.1:7859 L/browser-final` | **44 项通过，exit 0**；`L/browser-final.log` / `browser-final/summary.json`。1366×768、1920×1080、375×812 逐字段对照真实 HTTP；键盘开合/焦点、明细底部可滚动到达、无横向溢出；zero pageerror / forbidden requests。 |
| `P -B L/serve_regression.py` + `node tests/integration/check_frontend_replay.cjs http://127.0.0.1:7860 L/replay-regression replay` | **72 passed / 0 failed，exit 0**；`L/replay-regression.log` / `replay-regression/summary-replay.json`。仪表盘仍使用原 DashboardHandler + 同一真实 replay；**仅不相关 EvoMap 上游 transport 注入 httpx.MockTransport 的 503**，该分支只验错误呈现，未发 Hub 请求。 |

浏览器环境使用既有 `MORPH_PLAYWRIGHT=C:/Users/DW/AppData/Roaming/npm/node_modules/@playwright/cli/node_modules/playwright`、`MORPH_CHROMIUM=C:/Users/DW/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe`，没有安装。`check_adoption_trace.cjs` 对 EvoMap 路由仅返回空浏览器夹具；其余只放行同源 GET。44 项中真实回放、显式 mock 边界探针及故意不完整的 UI 输入分别编排，不能把后两者叫实际采用：同 Gene 多 attempt/不同 task、0 与 null、仅注入无采用、列表缺失/空、原 replay 断线保留并恢复均通过。不完整输入探针不表示后端会接受坏契约。

人工视图审阅实际 Chromium 截图 `browser-1/adoptions-1366.png`、`browser-1/adoptions-375.png` 和 `browser-final/adoptions-375.png`，确认原布局保留、长身份自动换行与手机滚动明细可读；截图仅辅助，语义结论来自 API/DOM 对照。第一轮 41 项已通过，随后补手机明细末项可达性检查成为最终 44 项；没有隐藏失败门禁或为截图扩功能。

最终显示 `provenance=replay`，`contract_local=passed / interface_live=not_run / task_live=not_run`。新 UI 本地验收通过不提升历史/模拟数据等级。所有测试服务仅 loopback，核对本轮 launcher/child/命令及 listener 身份后停止 7859（43796→46844）和 7860（4672→36608），已确认端口不再监听；未清理其他进程/文件。

## 提交与剩余边界

产品提交 **`8c57c4964fbf78b90d7232d3644975dab277d277`**（`Swarm-Agent: codex`），分支 `morph-readonly-app-0929`；`git push -u origin morph-readonly-app-0929` **exit 0**，`origin=https://github.com/songconmaisaix31-design/Morphogenesis`，主控可按最终报告提交精确验收。证据文档另一个同 trailer 提交，最终 HEAD/remote 回执随 worker_done 提交。

完整 tracked 交付恰为：Backend.jsx、backend.css、两个 finals-shell 生成文件、tests/t5/check_adoption_trace.cjs、本报告。AGENTS、docs/SWARM_*、TASKS、锁、后端、根树 WIP 均未写入。

真实限制：此页面仅展示第一代既有 UseRecord，采用事实不证明效果收益、FC 完成/冻结、当前模型执行或跨机器能力；数值/来源未知仍未知。完整历史数据的原件位于上述本地路径，未入 Git；独立环境复现需提供相同契约的真实记录并显式 replay。没有追加业务依赖或控制写入。

**NOT_RUN / 人工或后续操作**：新模型/Hub/付费调用、真实 T2 导出专项浏览器场景、全仓 Python 回归/strict/分发/远端 CI、生产部署/merge/tag、FC-E/H1/FC 冻结、物理现场验收。本轮适用 T5/构建/本地契约和实际浏览器已通过；独立验收及集成由主控派发，台账由 B 登记。无需要用户付费确认或额外安装的待办。
