# Stack 前端独立集成验收

2026-09-22；I 分支 `morph-frontend-stack-integration`。从主线 `3a30d9de8c81670f4becb2d0d81400039cbb508f` 普通 `--no-ff` 合并 F 精确提交 `29c5e3de79da0d7bf27f4fb0847e2902b590730e`，合并提交 `a2d8c9d73e7f75484d5d7bbdd1e727dfaa3aa279`；验收脚本最终代码提交 `a94d1e5bec7ae314e966be6db8d9d2e1f1288588`。本报告随后单独提交，最终交付 SHA 和远端核对回执保存在 `.runtime/stack-integration/delivery.md` 并通过 worker_done 交付，避免在提交内容中自引用其 SHA。未推主线。

## 完成与所有权

F 相对共同基线 `0fe307a32032993386afe876b27a3b74cf5aa52e` 的 11 个文件仅涉及 `viz/static/**`、`tests/t5/**`、`demo/README.md`、`THIRD_PARTY_NOTICES.md` 和 `docs/tracks/frontend-stack.md`；远端 F 分支 SHA 已核对一致。I 没有修改产品、后端、锁文件或 F 领域文件，仅新增 `tests/integration/check_stack_behavior.cjs` 并复用 `rehearsal_browser.cjs`：手机可以纵向滚动 Gene 区，但仍执行全部节点/文字边界、圆形覆盖、标签相交检查。原桌面完整 Gene 台账首屏断言保持默认启用，未放宽或删除。

主题固定复用 Hugo Theme Stack **v4.0.3** / `3e123a30b79b5d52a3a8e88a9dd678fcfd28e418`；独立 `git ls-remote https://github.com/CaiJimmy/hugo-theme-stack.git refs/tags/v4.0.3` 与该 SHA 一致。官方该 commit 的 LICENSE 下载到本轨产物目录，规范化 CRLF 后与随包 GPL-3.0 文本完全相同。Tabler Icons、hamburgers 的 MIT 文本、版权和 Stack GPL-3.0-only 署名见 `viz/static/licenses/NOTICE.txt`、页面页脚及第三方清单。参考站 `davidwang.space` 的部署版本仍未知，未将固定复用版本宣称为站点版本。F 的 Kimi 实现身份记录沿用其轨道报告，本轮未另发模型请求。

## 验证命令与结果

全部从本 I worktree cwd 运行。`PY` 表示只读复用 `C:/Users/DW/orca/workspaces/Morphogenesis/morph-onsite-integration/.venv/Scripts/python.exe`；Node 依赖在本轨 `npm ci` 安装，锁文件未变化。浏览器使用任务指定的既有 Playwright 和 Chromium，未新增浏览器安装。

| 命令 | 实际结果 |
|---|---|
| `npm ci` | 99 包安装成功 |
| `PY -m pytest tests/t5 -q` | 11 passed，13.28 秒；含 live/mock/replay 适配和不得升级验收三态的契约测试 |
| `node --test tests/integration/test_browser_options.cjs tests/integration/test_observer_control.cjs tests/integration/test_operator_enter.cjs` | 31 passed；最终脚本提交前再次通过 |
| `node --check viz/static/app.js`；`node --check tests/t5/check_stack_layout.cjs`；两个 I JS 文件的 `node --check` | 全通过 |
| `PY -m build` | sdist 和 wheel 构建成功 |
| `uv pip install --python PY --no-deps --target .runtime/stack-integration/wheel-site dist/morphogenesis-0.1.0-py3-none-any.whl`，设置本轨 `NODE_PATH` 后 `PY tools/check_distribution.py --site-dir .runtime/stack-integration/wheel-site --check-node` | 11 个包确实从 wheel 加载；资源、安装后独立验证器及 Node 桥通过 |
| Python `ZipFile` 读取 wheel 样式和 `viz/static/licenses/*`，逐项与源码 `read_bytes()` 比较 | 样式、3 份许可、NOTICE 均入包且字节完全一致 |
| `node tests/integration/check_rehearsal_layout.cjs http://127.0.0.1:7529 .runtime/stack-integration/replay-layout-ready` | 双桌面各 3 节点 / 3 标签，无裁切、覆盖和横向溢出；1366 Gene 底 745.28125 < 768 |
| `node tests/t5/check_stack_layout.cjs http://127.0.0.1:7529 .runtime/stack-integration/stack-ready` | 1366×768、1920×1080、390×844 明暗截图，手机菜单、键盘、验收导航通过 |
| `node tests/integration/check_rehearsal_stages.cjs http://127.0.0.1:64204 C:/Users/DW/AppData/Local/Temp/morph-i-fixture-ail6xpua/rehearsal.json .runtime/stack-integration/mock-working/rehearsal.json .runtime/stack-integration/mock-stages-ready` | 原有明确 mock fixture 的 19 阶段 × 双桌面，共 38 帧通过；1366 全阶段 Gene 底最大 745.28125；fixture 原件字节/mtime 不变 |
| `node tests/integration/check_stack_behavior.cjs http://127.0.0.1:7529 .runtime/stack-integration/behavior-final` | 三视口实际点击四个锚点均可达，主题 reload 持久化，各 10 次 API 读取，0 JS pageerror、0 外部请求；包括手机拓扑几何和两条 Gene 详情可达 |
| `git diff --check` | 通过 |

行为检查对只读回放页面注入明确本地 HTTP 503 和空态 fixture：错误后不保留通过率或验收通过态，三态均 `not_run`，来源显示数据不可用；空态明确 `mock`，谱系/消息/指标为空，随后恢复原 replay。成功 replay 为 `contract_local=passed / interface_live=not_run / task_live=not_run`。这些注入仅是 `contract_local` 浏览器测试，不创建或改写任何 live 原件。

## 实图与原证据

产物根：`C:/Users/DW/orca/workspaces/Morphogenesis/morph-frontend-stack-integration/.runtime/stack-integration/`，日志、截图、安装目录均被 Git 忽略。

- `stack-ready/stack-{1366,1920,390}-{light,dark}.png` 六张已逐一亲看；桌面摘要三卡、完整拓扑、Gene 台账可见；手机为纵向文档布局，暗色截图包含打开的导航菜单。
- `replay-layout-ready/replay-{1366,1920}.png` 和 `geometry.json` 留存桌面实际绘制边界。
- `mock-stages-ready/{1366,1920}-{0..18}.png` 共 38 张；亲看 1366 的初始、成员下线、Gene 采用以及 1920 完成阶段，数据与 mock 标签一致。
- `behavior-final/` 含主题重载、各视口错误/空态及 `phone-gene-detail.png`；手机 Gene 详情、错误/空态实图已检查。`behavior.json` 保留三视口几何、来源状态、API 次数及异常/外部请求计数。
- 原第五轮根 `C:/Users/DW/AppData/Local/Temp/morph-rehearsal-40f04885b37e489fa3ea1a04f61a984d/` 共 **29 个文件**，前后逐文件 SHA-256、字节数及 `st_mtime_ns` 完全一致，文件集合也一致；记录在 `original-before.json`、`original-after.json`、`original-audit.json`。服务只读该根 `rehearsal.json --replay`。

首轮本地 fixture 读取使用 Windows 默认编码曾报 `UnicodeDecodeError`；改显式 UTF-8 后继续。两次 viewer 就绪前访问出现 `ERR_CONNECTION_REFUSED`，失败日志保留，未视为产品通过。确认本地 API 就绪后使用全新输出目录完成所有验收；未删除或覆盖失败截图。

## 证据类别与限制

本轮只有 **contract_local + 只读 replay + 明确 mock**。没有新模型/网关请求、Hub 写入或付费彩排；第五轮历史 live 原件仍保持原样，不算本轮新 task_live。Hub 仍显示待发布，费用未知不改写。参考站精确部署版本、其它平台字体和物理投影没有新增验证。

未运行 Python 全仓测试或 CI；按本次前端范围完成了指定 T5、现有 Node 集成、JS、构建/安装包与实际浏览器验收。wheel 的 Node 运行依赖仍由本地 `npm ci`/`NODE_PATH` 提供，未宣称 wheel 自带 node_modules。

本轨仅使用 7529 与事前探测空闲的动态端口 64204。结束前按记录 PID、父子关系及确切 `viz.server` 参数核对，清理本轨 viewer 9072/35412、18408/13116；未操作 7525/7526/7527/7528。主线接收、7527 服务切换由协调者执行，本轨不做。最终推送与远端 SHA 核对见交付回执。
