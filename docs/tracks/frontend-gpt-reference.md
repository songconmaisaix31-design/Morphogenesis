# F：用户网页包直接移植与 GPT 图像审查返修

## 范围、身份、基线

- 工作树：`C:/Users/DW/orca/workspaces/Morphogenesis/morph-gpt-reference`。
- 分支：`songconmaisaix31-design/morph-gpt-reference`。
- 业务基线：`c68def4de25cedb48acd258bea614f7dff35cc16`；普通合并 `b0ffef8` 的主线计划，无冲突。没有改后端、API、锁文件或其它轨文档；计划/状态文件的变化仅来自指定合并。
- 代码实施者：本 F Worker 的实际系统身份为 **Codex，基于 GPT-6**；系统没有提供可独立核验的更细型号，故不冒称某个 Astra/Sol 子型号。没有转交实现给其它 Agent。
- API 设计输入：协调者消息 `msg_7db5f217feee` 提供的真实图像审查，请求模型 `evomap-gpt-5.6-sol`，返回 `gpt-5.6-sol`，HTTP 200，3520 tokens，费用未知。Worker 没有取得或寻找密钥，没有发起额外付费请求；审查不是全部代码的生成来源。
- 首次多图设计 POST 曾由协调者报告 `RemoteDisconnected`，输出/usage/费用未知；这与后续成功审查分开记录，未将失败首调用记为零或成功。本报告不包含任何凭据。

## 原包阅读与运行观察

原始包：`C:/Users/DW/WorkBuddy/2026-09-23-01-19-38/{christmas-site.zip,linear-site.zip}`。实际读取已解压根：`C:/Users/DW/AppData/Local/Temp/morph-layout-reference-20260923/{christmas/christmas-site,linear/linear-site}`。

已读取两个 `index.html`，Christmas CSS 全文、Google 字体 face 声明和 `assets/index-f5b0afaa.js` 的 renderer/scroll/尺寸初始化，Linear 的 layout、HeroIllustration、IssueListView、Button CSS 及对应 HeroIllustration、scenarios、IssueListView、Button JS。Linear 脚本中的导航通过 `onClick` 改 `issue / agent-tasks / dashboard / projects` 视图，说明这些是真实应用示例的结构，而非一张可以当后台使用的营销图片。

端口启用前确认 7841/7842/7843 空闲。7841 是当前工作树现有 `python -m viz.server --port 7841 --input demo/data/mock-run.json`；7842/7843 是两个本地包的隔离静态服务。7799/7526/7527 的进程与内容未修改。

参考页使用真实 Playwright/Chromium 在 1366×768、1920×1080、375×812 浏览并截图。证据根：

`C:/Users/DW/AppData/Local/Temp/morph-gpt-reference-evidence`

- `reference.cjs`、`reference-observation.json`：全部视口、实际 computed style、章节文字和 pageerror 记录。
- `christmas-{1366,1920,375}-hero.png`、`christmas-{width}-chapter-{2,3,4,5}.png`：分别是 Mister & Prada、Creative Developers、Egorov Agency、Challenge 006、Merry Christmas。
- `linear-{width}-hero.png`、`linear-{width}-app.png`：营销首屏与嵌入应用示例分开。
- `linear-{width}-section-{1..7}.png`：产品介绍、Intake、Planning、AI、Build、Changelog、底部 CTA；窄屏本身隐藏的章节不强行假造显示。

Christmas 初次 `chapter-2` 截图确实仍停在第一节，不能凭文件名认定成功。随后在 TEMP 观察脚本中恢复 `.wrapper` 普通流和 `.smooth` 的实际滚动，针对 `#fake-scroll` 重拍并逐张查看第 2–5 节，最终图中实际文字已与章节匹配。参考运行时还移除了抓取层 `offline-reveal-fix` / `offline-reveal-js`，将 canvas 的 100000px 抓取高度改成视口高度，将未匹配的 `Jost Medium` 对齐到实际 face `Jost`。这些仅是参考页浏览层修正；产品没有导入抓取修补、原模型或整包脚本。原包文件保持不变，参考的 Christmas 模型/粒子没有被证明完整恢复。

参考网络由浏览器拦截为对应 loopback origin，GTM/跟踪请求另行拦截；没有把原站的营销服务、导航或品牌内容导入产品。

## 资源和声明映射

完整权利边界见根目录 `THIRD_PARTY_NOTICES.md`。两份网站包均标为**用户提供快照，源版本/许可证未知**，不称 MIT 模板。

| 原包与相对路径 | 移植目标 | 实际复用与适配 |
| --- | --- | --- |
| Christmas `assets/index-b8e6792d.css` | `viz/frontend/src/reference.css` | `100dvh`、黑底、`10%` padding、`#ffeded`、Jost、`6vmin` section 基准；奇数章节靠右，第二个章节靠左；滚动叙事适配为用户规定的自动阶段。 |
| Christmas `.section h1` 的默认倍率 | 同上 | 实测 1366 下 `h1=92.16px / 700 / normal spacing`，并非 section 的 46.08px；最终英文因长词适配为 84.48px、700、normal 字距，1920 为 108px；中文次级 46.08/64.8px；375 英文 31.5px、中文 29.25px。 |
| Christmas `_ext/fonts.googleapis.com/css2_ed0de8.css`，`_ext/fonts.gstatic.com/s/jost/v20/92zatBhPNqw73oTd4g.woff2` | `reference.css`、`viz/static/fonts/Jost-latin.woff2` | 本地 Latin Jost face，26,576 字节，与用户源文件逐字节相等；CJK 使用本机中文字体，不声称 Jost 包含中文。 |
| Linear `assets/css/layout.B05Dfi6O_cf0c9cb7.css`，`assets/font/InterVariable_36a96895.woff2` | `reference.css`、`viz/static/fonts/InterVariable.woff2` | 100–900 Inter Variable face、400/510/590/680 权重、原包灰阶和白透明边框 tokens；字体 352,240 字节，与源逐字节相等。 |
| Linear `assets/css/HeroIllustration.CR-IZ0h7_16ec15e1.css` 的 `WS84WW` / `Mmx1Wq` | `backend/backend.css`、`Backend.jsx` | 232px sidebar、28px 导航行、8px 行圆角、低对比 hover/selected、侧栏与主视图区结构；导航真正定位拓扑/Gene/证据/EvoMap，并更新 `aria-current`。 |
| 同文件 `_5YOmVq` 主文档/属性结构 | 同上 | max-width 720px 居中文档、32px 项目标记、24px 属性尺度；文档内容改为真实任务、checkpoint、Tokens、Gene 与证据。320px 右栏展示独立验收状态、来源和事件。 |
| Linear `IssueListView.BH55qTC9_ccd67967.css`、`Button.dcAi4KbO_f1b9ab6e.css` | `backend/backend.css` | 紧凑控件、细边界、背景变化、0.16s transition、原生按钮结构；移动端换行，不复制营销截图的半倍缩放。 |
| 既有 Physarum 与 Swarm 模块 | `physarum/simulation.js`、`physarum.css`、`swarm/SwarmTopology.jsx` | 仅将黏菌 composite 背景设为同舞台黑色，原算法和黄色主体不变；真实拓扑增加可读的成员按钮，复用现有详情选择，未知值不再被 `Number(null)` 误成零。 |

所有新增 CSS 和 React 仍经原 Vite/React/TDesign 构建成 `viz/static/assets/finals-shell.{css,js}`。未增依赖、未改锁。项目仍使用原 ECharts 和同源 data bridge。图表文字移到节点下方，留出边距，避免白色节点覆盖文字。

## 审查 followup 处理结论

`msg_65960c28e3af`：采纳。修正并重拍参考第二至第五章节；旧文件名不作为成功证据。修正后真实第二节为 Creative Developers，第三节为 Egorov Agency。

`msg_87f1224901a2` 和补充 `msg_c85d2c4d0c25`：采纳。以实际 h1 的 2em 倍率和 700 字重为事实源，最终 1366 下英文为 84.48px，保留 Jost/10% 右边距；字距 normal；中文次级；375 独立 `8.4vw`，没有长词溢出。产品名出现时旧 AGENT SWARM 小字退出，不在标题后叠压。

`msg_7db5f217feee`，高级 GPT API 四项建议：

1. **采纳字号层级**：backend base 14px，主体说明和 Gene/事件 13px，辅助和上下文属性 12px；仅身份 ID/状态保留等宽。标题采用已读取的文档体系 24px/590（窄屏 22px），而非硬套建议的 22px/600。
2. **采纳灰阶分层，保留原包 token**：sidebar `#090a0b`、document `#101112`、context `#141516`；正文 `#d0d6e0`、次级 `#8a8f98`、分隔 `#23252a` 和白透明细线均可回指原 CSS。未逐字采用 API 推测的 RGB；原因是协调者明确要求原包实际值优先。
3. **采纳 320px 右栏与 720px 文档**：桌面 `232px minmax(0,1fr) 320px`。不采用固定 560px 中栏下限，避免 981–1199 窗口溢出；中尺寸三栏缩小，980 以下右栏下移，640 以下导航换行且单列。此处是响应式适配，并非遗漏右栏建议。
4. **采纳扁平空态与指标**：无运行节点时取消背景、四边框、圆角，仅保留顶部细线与 16px 垂直间距；指标已是带细分隔线的紧凑行。真实运行有节点时仍保留必要图形边界与可操作详情。

默认 `orca orchestration check` 会持续重放未 ack 的 Delivery；已处理并确认旧批次及所有后续批次。最终结论通过同 Task 的 status 消息回复后才提交。

## 行为和事实边界

- 自动黄色原生黏菌 + 小字 → 自生长概念拓扑 + 小字 → 双语标题慢显 → 显式进入；不自动进入，不接鼠标/触屏趋食。
- `#/physarum`、`#/workspace`、旧 `#/swarm` 深链保留，视图隐去时 inert；Tab/Enter、焦点圈、reduced-motion、动画暂停和返回序幕重新生长已验证。
- 概念拓扑始终标记为概念动画，与实际 `/api/dashboard` 拓扑分离；后台只显示实际 members/pipes。
- mock 缺少 rehearsal 时不虚构节点，已有 `genes` 正文和 `events` Envelope 以明确 mock/导出来源显示；不从它们推断运行 Tokens、GeneView 生命周期或 checkpoint 结果。
- 来源、contract_local/interface_live/task_live、未知值、错误保留快照、Gene 生成/采用/衰减/归档、只读 EvoMap 与全部关键 DOM ID 保留。未请求新任务 API 或 Hub 写操作。

## 验证和截图

构建依赖通过既有根目录和 `viz/frontend` 的 `npm ci --no-audit --no-fund` 安装，锁文件没有变化。

| 命令 | 结果 |
| --- | --- |
| `npm run build`（`viz/frontend`） | 通过；3909 modules，最终产物已更新。Vite CJS deprecation 和 `/fonts/*` 构建时保留 URL 的提示存在；实际浏览器字体加载成功、同源文件 HTTP 正常。 |
| `python -m pytest tests/t5 -q` | 51 passed（5.31s）。 |
| `node tests/integration/check_frontend_story.cjs http://127.0.0.1:7841 <TEMP>/final-story` | 通过，原跨轨脚本未修改；顺序、CTA、Tab、深链、三态、减少动效、三视口与错误界限检查通过。 |
| `node tests/t5/check_reference_layout.cjs http://127.0.0.1:7841 <TEMP>/final-checks <TEMP>/replay-dashboard.json` | 80 项通过；记录为 `final-checks/result.json`，无 uncaught error、无非同源/非 GET 请求。控制台仅预期 EvoMap 404 和主动注入的 dashboard 503。 |
| `node --check viz/static/app.js`、`node --check tests/t5/check_reference_layout.cjs` | 通过。 |
| `git diff --check` | 通过。 |

`<TEMP>` 为上述完整证据根。最终实图：

- `final-product-{1366,1920,375}-{physarum,growth,intro,workspace}.png`：正常动态流程三尺寸实图；`*-workspace-full.png` 保留全部数据区。
- `final-checks/{workspace,evomap,intro,replay,stale}-*`：具体命名为 `workspace-1366.png`、`intro-1366-reduced.png`、`replay-1366.png`、`replay-375-member.png` 等，含三尺寸全页、EvoMap 空态、错误态和成员详情。
- `final-story/01-physarum-1366.png` 至 `08-workspace-375.png`：原集成脚本的最终复核。
- 主动打开并目视检查了参考完整章节、嵌入应用、各产品阶段、桌面/手机后台、真实回放拓扑与成员详情、错误态和全页图表；没有把仅 DOM 断言当作视觉验收。

回放数据读取现有真实第四轮文件：

`C:/Users/DW/AppData/Local/Temp/morph-live4-98b36399c0324192b5af81f8077bc11d/morph-rehearsal-86e5351d49fe49a1b60ba0a4bb4c4e4e/rehearsal.json`

使用既有 `viz.server.rehearsal_loader(path, replay=True).as_dict()` 写 TEMP 快照，再由 Playwright 只在测试页注入对应 `/api/dashboard` 响应。源文件 bytes/mtime 前后相等；provenance=replay，interface_live/task_live=not_run。实际节点、下线、恢复、1348 tokens、归档 Gene 来自该历史证据；不算本次新真实任务。7526 只读 GET 曾连接拒绝，未因此重启或替换其进程。

## 剩余限制与交接

- 网页包的源版本及授权许可证未知，按用户快照和明确复用授权如实记录；不追加开源许可声明。
- API 图像审查成功由协调者消息给出；首个断线请求的 usage/费用仍未知；Worker 未自行重试。代码完成与审查来源分别标注。
- visibility handler 测试使用合成 `document.hidden`/visibilitychange；视图隐藏是真实 UI 切换。未声称完成物理浏览器前后台切换、投影或人工见证。
- 本轮展示验证为 contract_local + mock/历史 replay，不是新的 task_live、生产 Hub 发布或物理验收。
- 原开发与参考服务随 Orca 重启退出；恢复后已核对 7842/7843 无监听，不再为提交重启参考服务。协调者恢复的 7841 当前 PID 为 **28604**，命令为 `C:\Python313\python.exe -m viz.server --port 7841 --input demo/data/mock-run.json`，源码来自本工作树；保持运行交给 I。原参考启动命令分别是在两个包根目录执行 `python -m http.server 7842 --bind 127.0.0.1` 与 `python -m http.server 7843 --bind 127.0.0.1`。TEMP `servers.json` 已更新为恢复后的进程记录；PID 只是核验时的状态。最终 7799 更新由 I/协调者按独立验收处理，本轨未执行。
- 协调者 `msg_65dcb17814af` 已确认最终标题份量/右对齐和后台扁平文档层级视觉通过；恢复后 `msg_4c15b2df92bb` 确认原截图与检查有效、仅需提交交付。本次恢复未扩展可选功能、测试或部署文件。
- I 普通合并本轨精确 SHA 后运行其集成检查；无需修改原 `check_frontend_story.cjs` 的视觉选择器。领域返修继续回 F。
