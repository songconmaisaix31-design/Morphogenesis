# F 轨报告：决赛前端重建（TDesign 外壳 + 黏菌黄设计系统）

2026-09-23（Asia/Shanghai） · 实现者：Kimi（Kimi Code 0.43.1 / K3）· 分支 `morph-frontend-stack` · 从主线快进（含计划 `3821248`）

用户最新指令完全放弃此前 Stack 前端（保留在 git 历史，最终 Stack 提交 `29c5e3de79da0d7bf27f4fb0847e2902b590730e`），改为按指定深色黏菌黄设计系统重建，并复用核验过的官方大厂模板。后端、数据格式、验收语义与历史证据不变。

## 模板来源与实际复用映射

| 项 | 值 |
|---|---|
| 上游 | https://github.com/Tencent/tdesign-react-starter |
| 版本/许可 | package 0.3.1，commit `fce97863edd5d5556f766dd4e342aace31a99487`，MIT（Copyright 2021-present TDesign，全文在 `viz/static/licenses/`） |
| 本机只读克隆 | `C:/Users/DW/AppData/Local/Temp/morph-tdesign-fce97863` |

实际源码复用（非模仿）：
- `src/components/Board/index.tsx` → `viz/frontend/src/components/Board.jsx`（Card+title/count/desc 结构；删 trend/demo 微图，count 改为数据所有的大数字 span）；
- `src/pages/Dashboard/Base`（`index.tsx` + `TopPanel.tsx` 的 Row/Col Board 组合）→ `viz/frontend/src/App.jsx` 顶部三 Board（TDesign 栅格为 12 列：xs=12 / md=4）；
- `src/layouts/components/AppLayout.tsx` 顶栏式布局 → `App.jsx` 外壳（Layout.Header + Content + Footer）；
- 主题：TDesign 暗色变量经 `[theme-mode='dark']` 用用户令牌覆盖。
- 裁去：登录、Redux modules、路由、mock 服务、i18n、全部无关页面与假统计；未复制 `.agent`/CLAUDE 类指令。

工程：`viz/frontend/**` 独立 package.json + package-lock（react 18 / tdesign-react 1.15 / vite 5，不动根锁）；`vite build` 以 library/IIFE 形式只产出 `viz/static/assets/finals-shell.{js,css}`（`emptyOutDir:false`，不动 licenses/app.js/echarts）；`define` 内联 NODE_ENV 消除浏览器 `process` 引用；入口用 `flushSync` 保证 defer 结束时静态壳 DOM 已在位。无 Node 运行时服务器、无 CDN/外部字体/登录。React 壳只渲染一次（无状态），数据与 ECharts 仍由独立 `viz/static/app.js` 管理（4 处真实 `renderMode: "richText"`，测试断言不变）。

## 设计系统落实

- 令牌：`#0B0E14` 页面 / `#151A23` 面板 / 边框 `rgba(255,255,255,.08)` / 唯一主色 `#F5D547` / 文字 `#E8ECF4`、`#8A93A6`、`#64748B`；`#34D399` 仅用于 checkpoint 全过的瞬时脉冲（约 0.9s 一次，`prefers-reduced-motion` 下禁用）。hover/active 复用 surface/slime 透明度，未新增色值；无渐变横幅、光晕、玻璃、emoji。
- 页头：项目名 + 实际在线成员数（`members` 中 available 计数，回放末帧 4/5）+ 实际任务轮次（task_id 前缀：repair→`1 · 修复`、recovery→`2 · 恢复`，与 I 核实事实 seq0-5=1、6-19=2 一致；不用快照序号冒充轮次）。
- 三大等宽数字（Consolas，`clamp(2.5rem,6vw,4.5rem)`）：checkpoint `3/3`（`· 100%` 拆小字号防换行，textContent 语义不变）；本轮 tokens 取 `current.results` 中 task_id 等于当前任务的 usage.tokens（seq0-1/6-8 无匹配为未知，不泄漏上一任务 911、不累加 2137）；活跃 Gene = archived_at 为空的数量（不按 weight 阈值推断）。
- 拓扑：ECharts circular，透明底；权重线宽公式保持 `clamp(2, 1+weight*4, 12)`（weight 1.9→8.6）；在线边 slime 色 shadowBlur 10；离线边 opacity .25 虚线；在线节点亮环 30px、离线灰点 20px；节点标签在节点正下方（几何断言保持）；签名比对使图只在真实数据变化时以 300ms 过渡。
- Gene 台账四态卡（真实状态类驱动卡体）：新生成=slime 描边、已采用=slime 实底深字、衰减中=opacity .45+轻缩、已归档=dim+删除线；归档优先，衰减按与上一快照真实 weight 比较，采用按 use_count，新生成按上一快照不存在；权重条 0..1 固定尺度（1=初始满权重），保留真实数值。
- 事件流：仅由 `rehearsal.history` 真实阶段生成（20 快照 seq0..19），最新一条 slime 强调，依次渐暗，无编造事件。
- `replay/mock/live` 徽章与验收三态、来源/Hub 状态常驻；费用 null 显示未知；API 失败清空全部数据区（含图表）。
- 次级区保留 Gene 谱系/消息流/指标/运行说明全部既有功能。
- 390px 窄屏纵向堆叠无横向溢出；reduced-motion 禁脉冲与图动画。

## 验证（全部真实执行）

```
node --check viz/static/app.js                                        # 通过
.venv python -m pytest tests/t5 -q                                    # 11 passed（未改断言）
node tests/integration/check_rehearsal_layout.cjs http://127.0.0.1:7528 .runtime/finals/legacy-check
# {"viewports":[1366,1920],"labels":3,"nodes":3,"clipping":false,"overlap":false}（原检查原样通过）
node tests/t5/check_finals_layout.cjs http://127.0.0.1:7528 .runtime/finals/check
# 1280x720 / 1920x1080 / 390x844：无横向溢出；Gene 台账底部分别 686/746（首屏内）；
# 拓扑 3 节点 3 标签无裁切无重叠；checkpoint "3/3 · 100%"、tokens 1226、活跃 Gene 0、
# 成员 4/5、轮次 2 · 恢复、事件 19+ 条、归档四态文本在；reduced-motion 无脉冲
```

证据截图：`.runtime/finals/check/finals-{1280,1920,390}.png`（只读回放第五轮 `morph-rehearsal-40f04885b37e489fa3ea1a04f61a984d/rehearsal.json`）、`legacy-check/replay-{1366,1920}.png` 与各自 geometry/finals-layout JSON。

## 变更文件

`viz/frontend/**`（新增工程与锁）、`viz/static/{index.html,style.css,app.js,assets/finals-shell.*}`、`viz/static/licenses/`（Stack/Tabler/hamburgers 许可随代码移除，新增 TDesign MIT + NOTICE）、`tests/t5/check_finals_layout.cjs`（新增；Stack 专用 `check_stack_layout.cjs` 随旧版移除）、`demo/README.md`、`THIRD_PARTY_NOTICES.md`、本报告。`tests/t5/test_adapter.py` 11 项测试未改。

## 交接与限制

- 新增 selector 交接 I：`#metric-tokens`、`#story-gene-count`、`#header-members`、`#header-round`、`#event-feed .event-row`、`.gene-fact.gene-{new|adopted|decayed|archived}`；既有语义 ID（#provenance、#rehearsal-mode `#seq`、#story-checkpoint-rate `N/3` 前缀、#story-genes、.gene-ledger、#story-pipe-chart、node.online/links.active 等）全部保留。
- I 的 `check_finals_replay.cjs`（其分支 a63edd9）覆盖 20 快照全阶段；本轨未运行付费演示，原 live 全流程本轮未执行。
- 预览用 7528（验证空闲后启用）；7526/7527 未触碰；未读凭据、未新增网关/Hub 调用。
- 阶段中途 tokens/轮次边界以 I 核实事实为准（seq6-8 未知、轮次 2）；其他执行器（codex）快照无 executor/model 字段时不受影响。
