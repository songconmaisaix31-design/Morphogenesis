# 集成验收（2026-09-22）

所有权仅为 Git 合并、集成检查和本报告；没有自行修改各轨领域实现，没有新增 Agent、付费模型调用或外部 Hub 效果。既有测试已覆盖接线、来源隔离与三态，不为增加数量另写镜像测试。

## 合并与环境

- 分支：`songconmaisaix31-design/morph-integration`，起点 `02f42c2`，已纳入协调者主线 `366d12b`。
- 精确合入 T0 `cdc8972`（含完整 11 包配置 `f5c725b`）、桥 `adca7f6`、Hub `07636c1`、供给 `1c4e5e9`、拓扑 `a12d288`、代谢 `240aaf0`、执行 `33ed929`、展示 `0655110`（含 `46aa58e`）。全部使用普通 Git merge，保留各轨历史，无源码覆盖、force push 或贡献删除。
- 首个已推送集成头 `506d7badc975455bd6b1aa4c0677c1bccb81a791`；T5 原作者类型返修 `e2f1bbe91046d0a26d8f661b458dbbe921887b9e` 合入后为 `970e6b2710dae760b7408072815cabda08bc03b2`。
- T5 原作者 CSS 返修 `218ba08bbdc001192645e9f40f1bf6e15e5a02d1` 合入后的最终实现为 `70360e9f03ad4f41cc034539175f4db6ffe9740a`；后续本轨报告提交不改变实现。全部要求的提交（包括已有祖先）经 `git merge-base --is-ancestor` 核对在历史内。
- Windows；本工作树 `.venv`：Python **3.12.13**、Poetry **2.5.1**（`uv tool run poetry`），Node **24.16.0**。全部包合入后才执行 Python 安装。未改全局环境或锁文件。

## 命令和结果

以下命令在本工作树执行，`.venv/Scripts/python.exe` 是该 Poetry 环境的解释器。详细日志和浏览器产物位于忽略目录 `.runtime/integration/`，不提交原始模型证据。

| 命令 | 结果 |
|---|---|
| `$env:POETRY_VIRTUALENVS_IN_PROJECT='true'; uv tool run poetry env use 3.12` | 创建专用 `.venv`，Python 3.12.13 |
| `uv tool run poetry check --lock` | exit 0；仅现有 tool.poetry 元数据弃用提示 |
| `uv tool run poetry install --no-interaction` | 锁定安装 82 个依赖及当前完整项目成功 |
| `npm ci --no-audit --no-fund` | exit 0；99 packages，未改 package-lock |
| `.venv/Scripts/python.exe -m pytest -q` | **149 passed / 89.85 s**，`pytest.log`；本地合同测试，无真实模型调用 |
| `.venv/Scripts/python.exe tools/typecheck.py` | 初次报 T5 两处 redundant-cast；原作者修复后 **50 source files，0 errors**，`typecheck-final.log` |
| `node --check bridge_node/asset_bridge.mjs`、`node --check tools/check_sdk.cjs`、`node --check viz/static/app.js` | 三个已跟踪 Node 源文件全部通过 |
| `npm run check:sdk` | schema_valid / asset_id_verified / tampering_rejected=true；published=false |
| `.venv/Scripts/python.exe -m build` | sdist 和 wheel 成功，`build.log` |
| `uv pip install --python .venv/Scripts/python.exe --no-deps --target tools/.wheel-site dist/morphogenesis-0.1.0-py3-none-any.whl` | 实际 wheel 安装成功 |
| `.venv/Scripts/python.exe -I tools/check_distribution.py --site-dir tools/.wheel-site --check-node` | 11 包均从 wheel 目标导入；资源齐全；安装后验证器拒绝坏样例；官方 Node 桥通过，`distribution.log` |

CSS 返修合入后全套 pytest 再次 **149 passed / 67.58 s**（`pytest-final.log`），统一 strict 再次通过 50 文件；重新 `python -m build`、用 `uv pip install ... --reinstall --target tools/.wheel-site` 更新 wheel，分发检查再次通过（`build-final.log`、`distribution-final.log`）。初次 GitHub CI `35681613502` 因上述两处 cast 失败；类型修复后的 `970e6b2` 在 [CI 35682449626](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/35682449626) 的 Ubuntu / Windows 两端均成功，使用 Python 3.13 / Node 24。最终推送候选的精确 CI 回执随 merge_ready 提交给协调者。

wheel 验证复用锁定 Python 依赖，目标 `tools/.wheel-site` 位于源码之下，Node ESM 能向上找到源码 `node_modules`。这证明源码 `npm ci` 配合安装后 Python 包的限定布局；不证明任意 site-packages 中 wheel 单独运行 Node/MCP。官方 MCP 本地真实握手与工具调用由全套测试执行，输入是合成数据，仍仅 `contract_local`。

## 原始真实运行与最终代码本地复核

原始证据根为 `C:/Users/DW/AppData/Local/Temp/morph-t2-{normal,resume,reuse}-20260922`。读取并交叉核对 summary/result/events/genes/adoption、CLI JSONL/提案/prompt、routing、原始独立 verify 日志与 `resume-observation.json`。三次各有一个真实 thread/turn 和一个 execution intent，独立三个函数测试均通过。

| 既有实际运行 | tokens | cost | 原始结果 |
|---|---:|---|---|
| normal | 14327 | unknown/null | 成功，0 Gene / 0 adoption |
| resume | 14330 | unknown/null | 新进程接续后成功，总调用仍 1 |
| reuse | 14509 | unknown/null | 成功，1 Gene / 1 adoption |
| 合计 | **43166** | unknown | **3 次旧实际调用，集成本轮额外调用 0** |

reuse 的经验正文与 normal 的实际成功提案一致，完整出现在 prompt；模型提案明确报告采用，UseRecord 绑定同一个实际 attempt，注入/使用计数各 1。预设权重 1/1.5 在载入 normal 的真实复核反馈后使 builder1→builder0，实际执行 builder0。这是受控固定例子的路径证据，不是性能或最优组织证明。

最终代码复核命令：`.venv/Scripts/python.exe .runtime/integration/audit_runs.py`，结果在 `audit-runs.json`。三个保留候选均通过最终语法门和最终独立验证器；这些是旧产物的当前本地复验，未产生新 task_live。对每个已完成 checkpoint，先确认图 `next=()`、已有且仅有一个 execution intent，再在数据库副本上两次 `Runtime.resume()`；执行器和复核器方法被设置为一旦调用立即失败，两次均返回同一结果，事件与采用记录不增加。

审计工具调试期间，首版直接对原 SQLite 做只读 backup，发现 normal 的 `checkpoints.db-shm` **只有 mtime 改变、bytes 未变**，严格全文件断言因此失败。随后改为先复制完整 DB 与 sidecars，只在副本连接/backup，显式关闭 SQLite 连接；最终三组全部原始文件 bytes/mtime 断言通过。不能据此声称整个集成期间所有 SQLite 辅助文件 mtime 从未变化。CLI 文件、sample.py 和业务证据未因续接重复写入；原始模型调用未重试。

## 浏览器验收

先读取 `orca skills get orca-cli` 和 `references/browser.md`。Orca **1.4.199** 状态 ready，创建本轨页面成功（page `78c75f3c-0fe3-46eb-9af0-6cde15eaea5f`）。命令：

```powershell
orca tab create --url http://127.0.0.1:7510/ --json
orca reload --page 78c75f3c-0fe3-46eb-9af0-6cde15eaea5f --json
orca snapshot --page 78c75f3c-0fe3-46eb-9af0-6cde15eaea5f --json
```

reload/snapshot 均 exit 1：`browser_owner_unavailable: Could not reset stale helper session orca-tab-78c75f3c-0fe3-46eb-9af0-6cde15eaea5f; retry after agent-browser exits`。分别保存在 `orca-reload.json` / `orca-snapshot.json`；没有重启 Orca、终止 helper 或操作他人窗口，嵌入浏览器验收仍未通过。

依据用户授权使用已安装 `@playwright/cli` 所带 Playwright 与已有 Chromium **151.0.7922.34**，独立 headless 实例。未安装全局软件。服务以 `Start-Process -WindowStyle Hidden` 启动，运行 `.venv/Scripts/python.exe -m viz.server --port 7510 --t2-root C:/Users/DW/AppData/Local/Temp/morph-t2-reuse-20260922`，父 PID **65604** / 实际监听子 PID **46720**。

`node .runtime/integration/browser.cjs` 通过真实浏览器渲染检查：5 条消息边、1 个 Gene、1 条来源边和 1 条采用边；两个 Canvas；`contract_local=not_run`、`interface_live=passed`、`task_live=passed` 独立呈现；Hub 待发布；历史指标明确空态；ECharts **6.1.0** 由本地 `/vendor/echarts.min.js` 返回 200。五个页面资源请求均为 `127.0.0.1:7510` 且 200，console/page errors 均空。HTTP 与 DOM/Canvas/截图为分别检查的证据。

截图本地绝对路径：`C:/Users/DW/orca/workspaces/Morphogenesis/morph-integration/.runtime/integration/reuse-desktop.png`；浏览器结构与网络日志 `browser.json`，终端结果 `browser.log`。等待 ECharts 动画后截图并实际查看。首次截图发现 `.empty { display:grid }` 覆盖 `[hidden]`，导致已加载图下方两个空框；T5 原作者 `218ba08` 修复后重新跑浏览器并查看截图，computed display 为 `none / none / grid`，两个多余框消失，真正的指标空态仍显示。原始前后截图均保留（修复前为 `reuse-before-hidden-fix.png`）。

验证结束后，先从 Win32_Process 核对父 PID 65604 的本工作树命令行与子 PID 46720 的父子关系/7510 参数，再仅终止这两个服务进程；确认 7510 无监听，记录 `cleanup.json`。Playwright 通过 `finally browser.close()` 关闭自己启动的 headless 实例；本轨 Orca 测试 tab 单独关闭。没有终止 T5 的 7500/7501/7502 服务或 Orca 进程。

## 保留限制与未执行项

- Hub 仅本地 stub / 待发布；正式沙箱与凭据未提供，没有外部发布、发现性或生产验收。
- ORCA 供给为固定逻辑成员 fallback；开发阶段真实 Orca 多开不等于产品运行时供给已接通。
- CLI 不能硬封顶单次 token/费用，cost unknown，unknown_usage 不自动继续；不盲目重试 UNKNOWN。
- GEP 本地 SDK/MCP 证据不等于 Hub 远端验收；Python 验证命令也未证明通过远端平台策略。
- 词法 HashingVectorizer + FAISS 不是语义模型；本地经验归档不等于远端原子同步。
- 可选 T4 未开发；三次真实例子不证明性能提升或最优组织；独立验证器/语法门不是通用敌对代码沙箱。
- 嵌入 Orca 浏览器仍受 helper 能力阻塞；外部 headless 页面验证通过不冒充该能力恢复。
- 最终候选待协调者终审；不由本轨修改主计划、状态、决策或验收矩阵。
