# F 轨报告：Stack 风格前端重塑（保留拓扑）

2026-09-22 · 实现者：Kimi（Kimi Code 0.43.1 / K3，会话 `session_b4a6ad0c-3fc4-4df3-8ef9-3f3f725da760`）· 分支 `morph-frontend-stack` · 基线 `0fe307a32032993386afe876b27a3b74cf5aa52e`

## 范围与来源

按用户指定，以参考站 https://davidwang.space/ 实际使用的 **Hugo Theme Stack** 重塑 `viz/static` 展示层；Python 静态服务、`/api/dashboard`、ECharts 与数据契约不变，未引入 Hugo 或任何应用框架、外部字体或 CDN。

| 来源 | 精确版本 | 许可证 | 用途 |
|---|---|---|---|
| https://github.com/CaiJimmy/hugo-theme-stack | v4.0.3，commit `3e123a30b79b5d52a3a8e88a9dd678fcfd28e418`（2026-05-25）——本轨固定复用的版本；参考站实际部署的主题确切版本未确认 | GPL-3.0-only | 设计变量（`#f5f5fa` 底色 / `#34495e` 强调色 / 卡片与阴影 token）、extended 三栏栅格断点、粘性左侧边栏 + 菜单 + 汉堡按钮、明暗主题 `StackColorScheme` 模式、页脚样式 |
| 参考站 https://davidwang.space/ | 实测 1366：底色 rgb(245,245,250)、左栏 ≈197px、右栏 ≈328px | — | 布局核验基准（协调者截图 `morph-stack-reference-qqnJgo/reference-1366.png`）；未复制博客文章、头像、背景图等私人内容 |
| Tabler Icons（随 Stack v4.0.3 内嵌） | 同上 | MIT | `index.html` 内联菜单/主题切换图标 |
| hamburgers（Jonathan Suh） | 随 Stack v4.0.3 | MIT | 汉堡按钮模式（简化适配） |

主题署名保留在页面页脚与 `viz/static/style.css` 头部；完整 GPL-3.0 / MIT 许可与 copyright 文本在 `viz/static/licenses/`（含 NOTICE 逐项说明），明细见 `THIRD_PARTY_NOTICES.md`。

## 实际结构（协调者 handoff 后的授权布局）

- 左侧粘性边栏：项目 SVG 标识 + 🧬、站点名/描述、`#provenance` 徽章、锚点菜单（彩排剧情/验收状态/谱系与消息/运行说明）、明暗切换（`StackColorScheme` localStorage + `prefers-color-scheme`，与 Stack 同键同语义）。
- 主栏首屏（1366×768 实测）：首行 01 出题 / 02 checkpoint / 04 故障恢复三张紧凑概要卡（恢复卡显式占第三格）；第二行全宽拓扑主卡（画布实测 375×220，管道列表在右侧 280px 可滚动列）；第三行 Gene 池摘要（ledger 实测 599..745，整体在首屏内）。长详情（谱系/消息/指标/运行说明）在主栏下移，菜单锚点可达。
- 右侧边栏（≥1024）：数据来源（`#source-label`/`#hub-status`）与验收三态（`#contract_local` 等）。<1024 不再 `display:none`（msg_486505a2e5e7 修复），在主栏之后正常文档流堆叠，滚动与菜单锚点均可达。
- 移动端（390×844 实测）：汉堡按钮带 `aria-expanded`/`aria-controls`，点开菜单为卡片式列表；点击锚点后菜单自动收起且目标滚入视口；Enter/Space 开合、Escape 关闭并还焦。
- 字体：实测 Windows Chromium 经 Segoe UI 字体链接把中文回退成衬线（`.runtime/frontend-stack/font-test.png` 对照），故 `--base-font-family` 以 `Microsoft YaHei` 领衔，其余平台落到各自系统 sans；不加载外部字体。
- ECharts 四个图按 `data-scheme` 切换亮/暗调色板；拓扑保留真实节点、权重线宽公式（weight 1.9 → 8.6）、下线虚线与恢复语义，核心 DOM id 与 `mock/replay/live` 标记全部保留，`renderMode: "richText"` 仍为 4 处。

## 验证命令与结果

环境：本轨 `npm ci` 锁定安装（99 包，锁文件未改）；Python 用同级 `morph-onsite-integration/.venv`；Playwright/Chromium 用既定本机安装；预览端口 7528（事前确认空闲；7525/7526/7527 未触碰）。

```
node --check viz/static/app.js && node --check tests/t5/check_stack_layout.cjs   # JS-OK
.venv python -m pytest tests/t5 -q                                              # 11 passed
node tests/integration/check_rehearsal_layout.cjs http://127.0.0.1:7528 .runtime/frontend-stack/layout-final
# {"viewports":[1366,1920],"labels":3,"nodes":3,"clipping":false,"overlap":false}（含 geneBottom<视口 旧断言，仍通过）
node tests/t5/check_stack_layout.cjs http://127.0.0.1:7528 .runtime/frontend-stack/stack-final
# 1366/1920/390 三视口：无横向溢出、锚点齐、主题切换持久化、页脚署名在；
# 390 实点 #acceptance-widget 锚点目标可见、菜单收起；键盘 Enter 开/Escape 关、aria-expanded 正确
```

真实 Chromium 截图（回放 `morph-rehearsal-40f04885b37e489fa3ea1a04f61a984d/rehearsal.json`，只读）：`.runtime/frontend-stack/stack-final/stack-{1366,1920,390}-{light,dark}.png` 及 `layout-final/replay-{1366,1920}.png`、`geometry.json`、`stack-layout.json`。1366 首屏：拓扑、checkpoint 3/3、Gene 摘要（ledger 底 745 < 768）同屏。

## 限制与交接

- 页面数据为只读回放；本轨未做新的真跑、未动网关/Hub/凭据，7527 交接与 `tests/integration` 适配（含逐阶段 mock fixture 的 geneBottom 余量复核，本布局 1366 余量约 23px，长文本阶段可能更紧）交 I 轨。
- `check_rehearsal_stages.cjs` 的逐阶段全量重放属 I 验收范围，本轨未运行。
- 管道行的权重以下边框厚度编码（沿用原设计）；离线管道为灰色虚线。
- 字体方案在本机验证；无 YaHei 的平台回退系统 sans，未逐一实测。
