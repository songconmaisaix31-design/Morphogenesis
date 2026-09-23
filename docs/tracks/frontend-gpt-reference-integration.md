# I：参考包前端与真实回放本地集成

2026-09-23；独立 Codex / GPT-6 Worker，无子 Agent。工作树 `morph-gpt-reference-integration`，分支 `songconmaisaix31-design/morph-gpt-reference-integration`。

## 完成内容与提交

从干净的 `c68def4de25cedb48acd258bea614f7dff35cc16` 普通精确合并，无冲突、无源码覆盖：

| 来源 | 精确 SHA | 集成 merge |
| --- | --- | --- |
| F | `d0724a6a2f32f2f03860bbab06ebb82266abdcaf` | `398dc06` |
| D | `50d13530a7a9c7b8d1e0cc4c258dc0186710b567` | `670f312` |
| 主控治理 | `f4349824f9934d8aae900823d40f3f537720b597` | `f4c2926` |
| 主控本地范围状态 | `b258ddd749468cf49033915d54aa75563a6c7a6d` | `670cc9b` |

集成代码提交 `93efcaee903cb7350d946e99eb81861264344f6b`：更新 I 自有 `check_frontend_replay.cjs` 的实际导航路径，保留原任务/拓扑/管道/成员/事件/Gene 对 API 的事实断言，增加三视口实际视图、字体、请求与控制台记录；真实检查完全没有 `browser.route` 或 `page.route`，不注入任何响应。

真实浏览器首次发现默认 `/favicon.ico` 404，保留 `71 passed / 1 failed` 证据并上报主控。主控消息 `msg_e0b789e17e3a` 明确授权入口配置胶水后，仅在 `viz/static/index.html` 增加 `<link rel="icon" href="data:,">`；严格控制台断言未放松，复验 `72 passed / 0 failed`。未改 F 业务源码、D 服务/部署实现、锁或主控治理文件，治理变更只由上述 merge 带入。

## 锁环境与适用验证

Python 3.12.13，Poetry 2.5.1，npm 11.13.0；本工作树 `.venv`。以下结果为 I 实测：

| 命令 | 结果 |
| --- | --- |
| `$env:POETRY_VIRTUALENVS_IN_PROJECT='true'; uv tool run poetry install --no-root --no-interaction` | 原锁安装 82 packages |
| `npm ci --ignore-scripts --no-audit --no-fund` | 根锁安装 99 packages |
| `npm --prefix viz/frontend ci --ignore-scripts --no-audit --no-fund` | 前端锁安装 112 packages |
| `npm --prefix viz/frontend run build` | 49 modules，通过；保留已有 Vite CJS、字体运行时解析提示 |
| `.venv/Scripts/python.exe -m pytest tests/t5 tests/deployment -q` | 67 passed，31.40s |
| `.venv/Scripts/python.exe -m mypy --strict viz/server.py` | Success，1 source file |
| `node tests/t5/check_reference_layout.cjs http://127.0.0.1:7844 <EVIDENCE>/mock-reference-v2 <TEMP>/morph-gpt-reference-evidence/replay-dashboard.json` | 131 项通过；0 pageerror、0 非同源/非 GET 请求；mock 与浏览器 fixture 注入单列 |
| `node tests/integration/check_frontend_story.cjs http://127.0.0.1:7844 <EVIDENCE>/mock-story` | 原序幕/显式进入/Tab/深链/reduced-motion/三尺寸流程通过，8 张截图 |
| `node tests/integration/check_frontend_replay.cjs http://127.0.0.1:7844 <EVIDENCE>/real-replay-settled replay` | 72 passed，0 failed；21 张三视口视图截图，另保留原事实脚本的拓扑截图；0 pageerror/console error/HTTP error/外域请求 |
| `node --check tests/integration/check_frontend_replay.cjs`、`git diff --check` | 通过 |

`MORPH_PLAYWRIGHT=C:/Users/DW/AppData/Roaming/npm/node_modules/@playwright/cli/node_modules/playwright`，`MORPH_CHROMIUM=C:/Users/DW/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe`。未做无关全仓重测。67 项和构建完成后，仅改入口 favicon 与 I 验收脚本/报告；入口变更由真实浏览器复验覆盖。

构建最初显示两份静态产物 modified，实为工作区行尾改变；Git 归一化 blob 与 F 完全相同：CSS `e8d263a0d90ef0f1ff134de5a032645f1029eb89`，JS `9d885babb309b8188cd8f3a4cfded41b49f1720b`。F 的 `viz/frontend/**`、`tests/t5/**`、第三方声明，D 的 `deploy/**`、`viz/server.py`、`tests/deployment/**`，以及三份锁文件分别与指定来源比较无差异。最终预览使用上述集成代码提交的资源，之后报告提交不改运行内容。

## 实际视觉与事实核对

证据根 `<EVIDENCE>`：`C:/Users/DW/AppData/Local/Temp/morph-gpt-reference-integration-20260923`。读取 F/D 最新报告及 `THIRD_PARTY_NOTICES.md`；源包仍按用户提供快照记录，版本/再分发许可证及字体专项许可证未知，未重新标作开源模板。

亲看源应用 `C:/Users/DW/AppData/Local/Temp/morph-linear-structure-audit/source-app-issue.png`，对照本轮任务、拓扑、Gene、手机成员/运行详情和 EvoMap 实图：保留侧栏内品牌、内容区 44px 工具栏、文档与紧凑属性、≤40px 活动行和真实五视图。此次接受的是 F 的新源结构移植，旧 `2df3138` 后台视觉通过结论仍撤回；源包其它视图未成功点击的截图不作源交互证据。

黄色原生黏菌、小字「黏菌 / PHYSARUM」、黑底概念拓扑「自生长 / AGENT SWARM」、双语大字、显式后台入口顺序保留。原序幕脚本的第一帧在文字淡入前拍到，故额外在同一真实 7844 服务等待文字 opacity=1，保存 `physarum-caption-settled-1366.png` 与 `caption-observation.json`；亲看确认小字和黄色主体同屏，Jost / Inter Variable 实际 loaded。原脚本流程断言与截图保留，不把早期无字帧说成文字验收。

最终真实截图在 `real-replay-settled/replay-{1366,1920,375}-{task,details,topology,member,genes,evidence,evomap}.png`，API 原文为 `dashboard.json`、`evomap.json`，结果为 `summary-replay.json`。实际 5 个节点、2 条管道（1 条 active）、20 行阶段历史、任务结果的 1348 tokens、2 个已归档 Gene 与对应 API 一致；无记录的成员管道/结果/事件显示空态。费用仍为 null；三态可在实际运行详情查看。

`real-replay-final/` 是 favicon 修复后第一次完整通过；逐图检查发现 Gene 的 force layout 在 250ms 截图时仍移动，故只将 I 脚本的 Gene 截图等待延至 2s，再以同一 72 项断言完整通过并亲看桌面/手机 Gene 图。最终使用 `real-replay-settled/`，不修改产品布局、不放松事实断言；两轮通过结果均保留。

EvoMap 由同源 Python 原只读实现发起一次默认搜索/类别读取，初轮真实响应为 `live`，favicon 修复后的复验为同进程 `cache`；本地 Gene pool 为 `unconfigured`。浏览器无伪造 dashboard/EvoMap 响应，没有点击额外搜索/刷新/资产详情，没有模型请求或 Hub 写入；公开只读搜索成功不升级项目的 `interface_live` / `task_live`。

## 预览、原件与边界

当前预览：`http://127.0.0.1:7844/#/workspace`，序幕入口 `http://127.0.0.1:7844/#/physarum`。服务端确为 `--rehearsal <原件> --replay`，不是 mock 服务配浏览器注入。

启动前核验 7844 空闲，`Start-Process -WindowStyle Hidden -WorkingDirectory <本工作树>`；mock launcher/listener 为 17596/45268，切换前核对 PID、父 PID、命令后仅停止本轨进程。最终 replay launcher **41372**、监听 PID **45120**，`127.0.0.1:7844`；cwd `C:/Users/DW/orca/workspaces/Morphogenesis/morph-gpt-reference-integration`。`replay-server.json`、`replay-process.json`、stdout/stderr 保留。F 7841 和 7799/7526/7527 未操作。

原件为 `C:/Users/DW/AppData/Local/Temp/morph-live4-98b36399c0324192b5af81f8077bc11d/morph-rehearsal-86e5351d49fe49a1b60ba0a4bb4c4e4e/rehearsal.json`。前后审计均为 **226518 bytes**，mtime UTC **2026-09-22T08:13:35.4930093Z**，SHA-256 **f3639cd4e96edbe04cea63d4522df12cf16d84817bb84650a19885268b61c818**，原件 mode=live；服务端降级返回 provenance=replay、contract_local=passed、interface_live/task_live=not_run。证据 `source-before.json` 与 `source-after.json`；读取 JSON 时保持时间字段为字符串后精确比对，避免 PowerShell 自动 DateTime 转换导致比较误报。

首次 mock 浏览器启动赶在服务监听之前，`mock-reference/` 保留未完成检查目录，连接拒绝错误见本次终端记录；确认实际 API 就绪后 `mock-reference-v2/` 完整通过。首次真实检查的 favicon 失败保存在 `real-replay/`，最终通过在独立目录，不覆盖失败证据。

本轮仅本地集成。最终 F+D 容器构建/启动、服务器/安全组变更、公网 HTTP/浏览器、物理展示、新模型任务与 Hub 写入均未执行；D 单轨容器历史通过不替代最终组合验收。保留本地真实 replay 预览供查看，后续公网工作须由主控另行处理。
