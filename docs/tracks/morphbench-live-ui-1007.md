# MorphBench Swarm 前端后继修复（F，2026-10-07—08）

任务 `task_333785bd89cc`，原 Dispatch `ctx_ef1075461ad3`；Orca 内存不足重启后沿同一会话由 `ctx_2fa0e1c926dd` 恢复。依据 `445aad4e3066e7cbfc0123adc1779d24d0c74cd4` 的 `docs/PLAN.md` 末页。已先读上一轮 Q `morphbench-verification-1007.md` 与 I `morphbench-final-1007.md`；原 RED 和 `C:/Users/DW/orca/mb021-1007/verify/browser-*` 保持只读。

## 源码与范围

- 分支：`songconmaisaix31-design/morphbench-live-ui-1007`。
- 初次实现 SOURCE：`2a66ee077b8c6fedc039218162a91bc60a7d6d22`，已正常 push。
- 最终 SOURCE：`820488e84a666712f247cfce9b36931d88646c1e`，已正常 push。追加窄屏返修，原提交和 RED 均保留。
- REPORT：本文件的 docs-only 提交；完整 SHA 由最终交接消息给出，避免自引用。
- 仅修改 `src/env-observatory/data.js`、`env-observatory.html`、`tests/observatory/test_server.py`、新增 `frontend.test.cjs` 及本报告。未修改核心、锁文件、A/B 产物或旧环境。

根因是 Compute 的 `cloudGrid` 后残留 `</article>` / `</div>`，浏览器修复非法结构时提前关闭主区，后续 Swarm 落入 BODY。删除多余标签后，六个 view 都保留在唯一 main 内；路由在研究请求完成前即初始化。保持原页面布局，仅补齐可伸缩容器、移动顶栏、卡片与详情尺寸。

两个旧数据层原本在 HTTP 503 / file 打开时自动加载 2024 示例，并循环产生看似实时的活动。现共用 `data.js`：未连接保留空任务、空分支和错误提示；不再默认发送 `project_id=p1`，优先使用服务绑定项目。`source=backend` 只描述接口来源，不改每条记录的 mock/live/replay、费用或验收状态。回放失败显示未连接，不将旧切片伪装为本次读取结果。

Swarm 节点、任务/租约、fencing token、预算预留、费用与审计均来自既有 `/api/swarm` 投影。无来源、读取失败时统计为 unknown；费用 null 不显示为零。回放不显示在线数量，模型矩阵保留同一单元格混合来源；三种 acceptance 状态单列。节点按钮与拓扑键盘入口打开只读详情，展示原 worker、相关任务/预算/审计。既有研究任务回放保留；当前入口与后端无节点 session API，详情明确“会话终端未接入”，未新建执行器或伪终端，主控已确认该边界。

## 工程与 HTTP 验证

本轨私有根：`C:/Users/DW/orca/mb-live-1007/ui`。本页引用的日志、截图和 JSON 均在此，未入库。

| 顺序 | 命令/检查 | 结果 |
|---|---|---|
| 原 Python 首轮 | `venv/Scripts/python.exe -m pytest -q tests/observatory --basetemp .../pytest-first-temp --junitxml .../pytest-first.xml` | **60 passed / 1 failed**，27.88s；`pytest-first.*` 原样保留 |
| Python 后继 | 同一原 suite，独立 `pytest-second-temp` / `pytest-second.xml` | **61 passed**，30.81s，1 个既有 Starlette deprecation warning |
| 前端事实与语法 | `node --test tests/observatory/frontend.test.cjs` | **8 passed**；`frontend-first.*`、`frontend-second.*`、`frontend-mobile-fix.*` |
| 静态检查 | `git diff --check` | 通过 |
| 隔离安装 | `uv pip install --python .../ui/venv/Scripts/python.exe --no-deps --reinstall-package morphogenesis .../ui/source-820488e` | 非 editable 安装成功；`install-820488e.log` |
| 安装一致性 | `venv/Scripts/python.exe -B audit_install_http.py`，cwd 为私有根 | **216 个分发文件原字节相同、0 mismatch；10 项 HTTP 检查通过**，`installed-identity.json` / `http-checks.json` |
| 依赖检查 | `uv pip check --python .../ui/venv/Scripts/python.exe` | 97 packages compatible |

首轮唯一失败是既有静态接线断言：提取内联数据层后 HTML 不再包含 `/api/research/` 字符串。补回真实接线声明，保留原断言并补充实际 `data.js` 资源断言后通过；没有降低或删除原判据。前端测试覆盖 503/file/network 空态、更新失败清空旧研究数据、mock/null 不被提升、无默认 p1、回放/未知心跳不推断在线、租约与费用 null、危险文本转义和全部内联 JS 语法。

`source-820488e/` 来自精确 SHA 的 `git archive`；`serve-820488e/src/env-observatory/` 仅含相同静态服务文件，其祖先无 swarm 源包，因此真实服务导入来自独立 venv/site-packages。`direct_url` 为该 Git 导出目录的非 editable file URL，精确 SHA 另以原始字节比较证明。HTTP `/` 与 `/data.js` 也逐字节比对冻结源文件。

HTTP 与视觉证据分开：8100 `/api/swarm` 为 missing/空数组；8101 为 replay/3 workers/60 tasks，原 worker audit 仍为 mock、整体 task_live=not_run；两端 `/api/research/package` 均为 503，`service_ready=false`、`probe_enabled=false`。这些是本地接口和展示观察，不是本轮 DashScope 科研结果。

## 浏览器验收

使用 Orca 真实内嵌浏览器，page `8b655b70-a140-4abd-a2da-a87eb99bc147`；`orca goto / exec set viewport / snapshot / click / scroll / eval / screenshot`。每次导航后重设尺寸，以 `innerWidth/innerHeight` 确认，截图保存 PNG；没有用 DOM fixture 替代真实页面。

原 390 首检为 **RED**：header 右沿 433px，实际 class 为 `has-dd`，窄屏选择器误用了 `dd-wrap`。证据 `replay-390.first-dom.json` / `replay-390-RED.png` 保留。后继 SOURCE 修正真实选择器；没有裁掉页面或隐藏横向溢出来掩盖问题。

浏览器第二轮的屏外节点详情点击虽返回 `clicked`，实际 dialog 未打开，原断言失败，证据 `final-replay-1440-detail.dom.json` / `.png`、`browser-second.log` 保留。将真实按钮滚入视口、重新 snapshot 后，一次独立物理点击成功；随后批量第三轮再次失败，`verified-replay-1440-detail.dom.json` / `.png`、`browser-third.log` 也保留，不宣称已稳定通过。诊断时 `document.visibilityState=hidden`、`document.hasFocus()=false`，按钮中心 hit-test 正确，程序触发同一按钮 click 后 dialog 打开；物理点击、程序 click 与白屏截图是不同证据。没有改页面隐藏判据制造通过。

10-08 资源门放行后，仅恢复两项轻量只读服务并复用同一浏览器页面，没有重新安装、构建、运行 pytest 或新开 Chromium。Orca 实际选中的仍是终端标签；单独 `tab switch --focus` 没有使页面可见。通过 Orca computer-use 点击应用顶层的 Dashboard 标签后，页面确认为 `visibilityState=visible`、`hasFocus()=true`；随后使用原详情打开、只读内容和导航断言完成整轮物理交互，未以程序 click 代替最终验收。

| 视口 | 空态与回放首屏 | 节点详情/关闭 | 滚动 | Home → Swarm 导航 |
|---|---|---|---|---|
| 1440 × 900 | PASS，Swarm top=193px | PASS，原 mock 字段可见，只读 | PASS，唯一导航/顶栏，无横溢 | PASS，研究任务/分支为空，返回 scrollY=0 |
| 1280 × 800 | PASS，Swarm 位于首屏 | PASS，同上 | PASS，同上 | PASS，同上 |
| 390 × 844 | PASS，Swarm top≈251px | PASS，详情有界滚动，无横溢 | PASS，同上 | PASS，菜单展开/选择/关闭，返回 scrollY=0 |

六个首屏案例均为唯一 main 包含全部六个 view，只有 Swarm 可见；8100 节点为 0 条、统计 unknown，8101 显示后端历史 replay 的 3 节点/60 任务。合计六个布局案例与三个交互案例通过，保存为 `browser-1008-checks.json`，执行日志 `browser-1008.log` / `browser-1008.success.txt`；最后一次 console 读取无消息，见 `browser-1008-console.json`。这是 F 的真实浏览器观察，不代替用户视觉确认或 B 的 task_live 验收。

截图、DOM 与 snapshot 使用 `accepted1008-{empty|replay}-{1440|1280|390}*` 前缀；详情为 `-detail.png`，滚动为 `-scroll.png`。逐图核对首屏、桌面/窄屏详情及移动导航：内容可读，首屏不空白，页面未重复生成导航。`accepted1008-replay-390-nav-open.png` 捕获了 0.2s 菜单动画中间帧，原样保留；补拍 `accepted1008-replay-390-nav-settled.png` 并保存对应 DOM，确认菜单 left=0/right=300、transform=none、文档无横溢。原 RED 与失败日志不被此次通过覆盖。

## 服务交接与限制

10-08 新 Dispatch 恢复后，轻量核对发现 8099/8100/8101 均无 listener，浏览器记录 `ERR_CONNECTION_REFUSED`；不把旧服务身份当作当前存活。主控释放本轨轻量服务/单浏览器窗口后，使用原冻结 SOURCE 的安装恢复 8100/8101，最终健康端点均为 HTTP 200。启动脚本 `restore-services-1008.ps1`，当前进程身份 `process-handoff-1008.json`，最终 listener/health 核对为 `listeners-final-1008.json` / `health-final-1008.json`。

| 当前入口 | launcher / listener | 创建时刻（+08:00） | 数据绑定 |
|---|---|---|---|
| `http://127.0.0.1:8100/#/swarm` | **41624 / 39376** | 2026-10-08 00:22:27.229 / 00:22:27.789 | 无 state；空态 |
| `http://127.0.0.1:8101/#/swarm` | **38544 / 41608** | 2026-10-08 00:22:31.446 / 00:22:31.751 | `C:/Users/DW/AppData/Local/Temp/morphbench-workers-95xpu2s3/state`，显式 `--swarm-replay` |

- launcher 是 `ui/venv/Scripts/python.exe`，listener 是 uv CPython 3.12；完整命令行与父子关系见上述进程文件，均启动 `ui/serve-820488e/src/env-observatory/server.py --host 127.0.0.1 --port 8100|8101`。两服务均 Hidden、loopback、`OBSERVATORY_PROBE=0`，未配置研究 HostConfig；启动日志 `8100-1008.*` / `8101-1008.*`。
- 10-07 历史 launcher/listener 为 8100 **40112/51500**、8101 **51220/28868**，记录在 `process-final.json`。早期 `replace-owned.ps1` 仅终止核对过 command line 与 parent identity 的本轨旧 listener，原身份仍在 `process-before-replacement.json`。
- 旧 8099 的历史 launcher **29344** / listener **41064** 已在 Orca 重启后消失；F 未停止、重启或 seed 8099，最终该端口仍无 listener。旧 state 与旧验证目录保持只读，不改原记录。
- 一次包含环境移除的组合启动命令被自动审批以 `blocked by policy` 拒绝，未执行；改用显式子进程 Environment 参数和端口占用检查的更窄启动脚本成功。后继新服务首次浏览器导航早于 listener 就绪，`ERR_CONNECTION_REFUSED` 保留在 `browser-final.log`，之后确认健康端点再继续，未重复启动。
- 当前 AOCI MCP 未提供且 worktree 无 `.mcp.json`，未声称获得当前认知收据或完成索引维护；未修改 AOCI 托管文件。
- F 未发模型请求，未改预算/租约/任务/执行器，未运行 AT-07、真实科研或 B 的付费测试。B 的新真实 state 尚待独立 I 接线后复验，不把当前旧 replay 页面当作它的结果。
- 本入口为直接交付 HTML/JS，无前端打包步骤；已执行 JS 语法检查。全仓 pytest/typecheck/SDK/wheel 工程门由独立 I 对最终合并 SHA 完成，本轨未宣称通过这些门。
