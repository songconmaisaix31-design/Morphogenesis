# 环境观测台（Environment Viewer）前端开发规格

> 交给前端开发 Agent 的完整规格。数据契约见同目录 [`API_CONTRACT.md`](./API_CONTRACT.md)。本文档是**唯一需求依据**，照做，不自行改产品叙事、字段名或设计 token。

---

## 0. 产品叙事（先吃透，再动手）

**协调与记忆都交给环境。** 前端不是后台管理工具，而是这块环境本身的呈现面：任务沉积在哪、谁认领了什么、什么痕迹正在生成。评委扫一眼 UI 就等于扫了一眼架构论文。

三根支柱 = 主界面三栏（一一对应）：

| 支柱 | 界面区块 | 隐喻 |
|---|---|---|
| 协调交给环境 | 任务沉积区（看板） | 没有中心调度器，任务躺在环境里等认领 |
| 行为从局部信号涌现 | 蜂群活动流（实时滚动） | 没有总控，只有局部认领/留痕/转交在滚 |
| 记忆交给环境 | 经验代谢区 | 痕迹沉淀、被复用、加速，是环境的代谢 |

**克制的红线**：信息密度高但不堆砌、留白要够、**别做成作战指挥室布景**。气质 = Grafana 数据密度 + htop 生命感 + Linear 排版克制 + "Ghost in the Swarm" 暗色。

---

## 1. 技术栈与交付要求

- React 18 + Vite，纯 JSX + 手写 CSS（**不引任何 UI 库**，看板/时间线/拓扑图都手写）。
- 数据层抽一个模块，是唯一取数入口；组件禁止直接 import 后端或 mock 实现。
- 拓扑图用 SVG 手绘（固定圆形布局即可，力导向可选，不引 d3）。
- 交付：`npm install && npm run build` 通过，`npm run dev` 可打开。
- **不包含现有 `environment-viewer/` 前端代码，从头开发。**

---

## 2. 视图清单

单页应用，顶栏 tab 切换三个视图：

```
┌ ① 观测台（默认着陆，评委 3 秒看这屏） ┐
├ ② 任务回放（从看板卡点击进入）          │
└ ③ 拓扑快照（顶栏 tab 进入）             ┘
```

---

## 3. 主界面（观测台）详细规格

### 3.0 顶部薄状态栏（高 36px，border-bottom）

```
⌁ MORPHOGENESIS · 环境观测台        蜂群: 6 活跃 · 2 空闲 · 时延 41ms   ●
```

- 左：品牌 + 副标题「环境观测台」。
- 右：活跃数 / 空闲数 / 时延（数字来自数据层，见 API_CONTRACT §10 口径）+ 一个呼吸状态灯（绿，`animation: pulse`）。

### 3.1 左栏 · 任务沉积区（看板，约 55% 宽）

- 三列泳道：`待认领` / `进行中` / `已沉积`（映射见 API_CONTRACT §4）。
- 任务卡字段（等宽字体，按优先级）：
  ```
  T-12 文献调研                 ← 标题 = signal.task_id + signal.payload.goal
  进行中 · 认领者 w-04          ← 状态 + owner（"认领者 w-xx" 是核心叙事，强调自主认领）
  branch: b-soft · research     ← 分支 + 能力（小字 dim）
  ```
- **卡上不出现"指派给谁"，只有"认领者"** —— 没人派工，是 agent 自己领的。
- 状态灯：待认领=琥珀、进行中=绿、已沉积=灰（failed/blocked=红）。
- 点卡片 → 进入任务回放。

### 3.2 中栏 · 蜂群活动流（实时滚动，等宽流式日志）

```
03:12  w-04 认领 T-12「文献调研」
03:14  builder-1 写入痕迹 note-1
03:15  w-04 → w-02 转交
03:18  reviewer-1 经验命中 ref:run42
03:21  w-05 完成 T-14 · 结果已留痕
```

- 新事件从底部进入、旧事件上滚（htop 生命感），`animation: fadein`。
- 时间 = `at`（Unix 秒）本地格式化 `HH:MM`；"谁"用 API_CONTRACT §5.2 的 actor 提取规则。
- 事件 → 文案映射见 API_CONTRACT §5.1。
- **高亮规则**：`经验命中`（复用）绿色高亮（记忆支柱唯一强调）；`转交`蓝；`隔离执行`青；`失败/阻塞`红；其余默认。
- 实时：开发期 mock 定时器循环播放一段预录事件序列；接真实后端改轮询 `task_audit`。

### 3.3 右栏 · 经验代谢 + 三轴 + 专家意见 + 下一步（竖排四块，约 300px）

**经验代谢区**（支柱 3）：
```
经验代谢
本轮沉淀 12 条 · 复用 5 次 · 加速 1.8×
口径：复用 = adoption 回执数 · 加速 = (沉淀+复用)/沉淀
```
- 三个数字（沉淀/复用/加速）+ 小字口径说明（口径见 API_CONTRACT §10）。

**三轴结果**：`three_axis` 三行（execution/hypothesis/contribution），每行是状态→计数的紧凑展示，状态色见 §5。

**专家意见**：从 `context.notes` 过滤 `kind=expert_opinion`，显示 `signer` + `text` + 恒 `unverified · 触发检查，非事实`（琥珀）。

**下一步 advisory**：`opportunities` 列表，每项显示 `share`（青）+ `branch_id` + `reasons`（小字 dim）。

---

## 4. 副界面规格

### 4.1 任务回放（LangSmith trace 风）

- 单任务瀑布时间线：`认领 → 执行(隔离) → 留痕 → 复核 → 复用`，即该 task 的 `task_audit` 按 `sequence` 升序渲染成纵向时间线。
- 顶部显示 task 信息：`signal.task_id` + `signal.payload.goal` + `status` + `owner`（认领者）+ `branch_id`。
- 每个事件节点**可点击展开显示原始证据**（原始 `event` + `body` 的 JSON，用 `<pre>` 等宽展示）—— 这是"可审计"叙事的 UI 证据。
- 底部显示 `executions`（`run_id` / `verified_result` / `archive_status`）和 `adoption_receipts`（复用证据）。

### 4.2 拓扑快照（LangGraph/AutoGen Studio 图，但只读）

- 节点 = agent（按 `worker_id` 聚合：来自 `tasks[].owner` + `task_audit[].body.worker_id/from/to` 去重）。
- 边 = **他们留下的共享痕迹**（同 branch 的 completed 结果 + handoff 的 from→to），**不是调度边**。
- **必须写图例**（放图下方，原文）：「图不是人编排的，是涌现出来的——边是 agent 留下的共享痕迹，不是调度边。」
- 只读：无拖拽/编辑/添加节点。节点 hover 显示 `worker_id + 关联任务数`。颜色：活跃（持有任务）=绿、空闲（仅痕迹中出现）=灰。SVG 手绘固定圆形布局。

---

## 5. 设计系统（token）

```css
:root {
  --bg: #0A0E14;          /* 深底 */
  --bg-panel: #10151C;    /* 面板 */
  --bg-card: #161C24;     /* 卡片/悬停 */
  --border: #1F2630;      /* 边框 */
  --border-strong: #2A3340;
  --text: #E6EDF3;        /* 主文本 */
  --text-dim: #8B98A5;    /* 次文本 */
  --text-faint: #5A6572;  /* 弱文本 */
  --green: #3FB950;       /* 活跃/成功/复用 */
  --amber: #D29922;       /* 待认领/意见/争议 */
  --red: #F85149;         /* 失败/反驳/blocked */
  --blue: #58A6FF;        /* 转交/信息 */
  --purple: #BC8CFF;      /* 贡献/采纳 */
  --cyan: #39C5CF;        /* 来源/回链 */
  --mono: "JetBrains Mono", "IBM Plex Mono", ui-monospace, Consolas, monospace;
}
```

- 全局等宽字体（正文、数字、标签都 mono；标题可用系统 sans）。
- 背景加极淡网格线（透明度 ~0.04 的 1px 网格，只铺主工作区）。
- 动效克制：状态灯呼吸、流式日志淡入、卡片 hover 抬升；无华丽转场。
- 三轴状态色：execution `succeeded`=绿/`failed`=红/`unknown`=琥珀；hypothesis `supported`=绿/`refuted`=红/`disputed`=琥珀/`not_evaluated`=灰；contribution `accepted`=绿/`proposed`=灰/`superseded`=紫/`rejected`=红。

---

## 6. 数据契约

见 [`API_CONTRACT.md`](./API_CONTRACT.md)。要点：

- 数据统一从数据层模块取：`fetchPackage()` / `fetchSnapshot()` / `fetchReplay(taskId)` / `subscribeActivity(onEvent)`。
- 字段名照抄后端，禁止改字段名、层级或语义。
- `at` 是 Unix 秒时间戳，展示时 `new Date(at * 1000)`。
- task 的目标/分支在 `task.signal.payload.goal` / `.branch_id`（注意 `signal` 嵌套层级）。
- 事件分两类：原生（body 含 `worker_id`）和 `research.*`（body 是 `ResearchEvent`，含 `actor`，无 `worker_id`）——"谁"统一用 §5.2 提取规则。
- 所有数字来自数据层，无写死；复合指标（加速等）有小字口径说明。

---

## 7. 验收清单

- [ ] `npm install && npm run build` 通过（exit 0）
- [ ] `npm run dev` 可打开，观测台三栏正常渲染，活动流滚动有生命感
- [ ] 任务卡显示「认领者：w-xx」，无"指派"字样
- [ ] 数字（活跃/空闲/沉淀/复用/三轴计数）全部来自数据层，无写死；「加速」有小字口径
- [ ] 任务回放可点开看板卡进入，节点可展开看原始 audit body / execution / receipt
- [ ] 拓扑快照图例写明「图不是人编排的，是涌现出来的」
- [ ] 不引入重型 UI 库；深色 terminal mission control 风；不做成浅色 SaaS 风或作战指挥室布景
- [ ] 信息密度高但留白够
