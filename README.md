# Morphogenesis

### 形态发生 · 去中心化 Agent 蜂群研究系统

> 让研究像形态发生一样生长——没有中央指挥，却能长出最优的拓扑。
>
> *Morphogenesis · decentralized Agent swarm*
> ![Uploading 6d850dd4b18f3f7d5e13fb2196cf2ed5.png…]()


---

## 一、我们为什么出发

今天的大部分 Agent 系统，本质上仍是"指挥官—士兵"模型：一个中央调度器决定谁做什么、做到什么程度、何时停止。它高效，却脆弱——调度器的认知上限就是整个系统的认知上限；它聪明，却健忘——每一次任务结束后，经验随上下文窗口一起蒸发，下一次任务从零开始。

而自然界早已给出另一种答案。多头绒泡菌（*Physarum polycephalum*）没有大脑、没有中枢，却能在迷宫中找到最短路径，能长出逼近人类工程师设计水平的铁路网络。它依靠的不是规划，而是**形态发生（morphogenesis）**：无数个局部个体沿着彼此留下的化学痕迹行动，痕迹沉积、强化、消退，网络在持续的重塑中逼近最优。

Morphogenesis 把这套生物学原理搬进 Agent 蜂群：**让研究自己去中心化地发生，让经验像化学物质一样沉积、代谢、复用，让整个系统的拓扑在每一次任务后变得比上一次更好。**

## 二、长期愿景

我们的愿景分三层，层层递进：

**1. 一座可观测的蜂群。** 每一个 Agent 的每一次认领、续租、转交、完成、失败，都被写入一条全局自增、不可篡改的研究账本。蜂群不再是黑箱——它有自己的"仪表盘"，任何时刻你都能看见它正在想什么、做什么、卡在哪里。

**2. 一片会沉积经验的土壤。** 研究不再是"跑完即焚"的一次性过程。每一个结果都沿着三根轴被永久记录——执行是否成功（execution）、假设是否成立（hypothesis）、贡献是否被采纳（contribution）。经验被命中时记入复用凭据，被更好的结果取代时留下取代轨迹，被证伪时触发分支休眠。土壤越来越肥沃，而不是被反复犁平。

**3. 一张持续重塑的机会网络。** 蜂群的注意力分配不由任何人拍板，而由机会路由策略给出：每条研究分支按证据、适用性、目标相关性与风险获得自己的机会份额，探索与利用被显式配比。网络像黏菌一样，向养分浓度高的方向生长，从被证伪的方向体面撤退。

最终，Morphogenesis 希望成为**科研与工程组织的"经验基础设施"**——人提出方向，蜂群负责探索，系统负责记住，时间站在复利这一边。

## 三、核心理念

### 3.1 蜂群，而不是指挥官

任务以"信号（signal）"的形式释放到工作区，携带目标、分支归属与所需能力。成员 Agent 依据策略自主选择任务（`research_choice`），系统记录推荐与覆盖行为——**推荐可以被尊重，也可以被合理地推翻**，两者都是账本中的一等公民。

### 3.2 租约，而不是占有

认领即租约：持有 fencing token，到期（`expires_at`）必须续租、完成或释放。Agent 掉线，任务自动回到池中；任务卡壳，可以转交（`handoff`）给更合适的成员。**没有任何一个个体能永久绑架一项工作。**

### 3.3 三轴结果，而不是一句"成功了"

一个结果必须同时回答三个问题：

| 轴 | 回答的问题 | 取值 |
|---|---|---|
| execution | 它真的跑起来了吗 | `not_run / running / succeeded / failed / cancelled / unknown` |
| hypothesis | 它支持原假设吗 | `not_evaluated / supported / refuted / inconclusive / disputed` |
| contribution | 它被群体采纳了吗 | `proposed / accepted / rejected / superseded` |

"执行成功但假设被证伪"与"执行失败"是两种完全不同的知识。Morphogenesis 拒绝把它们混为一谈——`recorded_result` 与 `verified_result` 分列，归档状态独立标注（`verified / refused`），未确认的执行以 `execution_unconfirmed` 显式留痕。

### 3.4 意见不等于事实

专家意见（`expert_opinion`）携带署名、来源引用与许可证信息进入系统，但 `review_state` **恒为 unverified**——无论署名多么权威。系统刻意在"有依据的判断"与"被验证的事实"之间保留一条清晰的证据边界（`per_record_provenance`），并让这条边界出现在界面的每一处相关展示中。

### 3.5 撤退也是一种进展

分支可以休眠（`branch_sleep`）、降级（`downgrade`）、重开（`reopen`）；贡献可以被取代（`superseded`）而原轨迹完整保留。在 Morphogenesis 里，**体面的否定与漂亮的肯定同样被庆祝**——它们都让网络更聪明。

## 四、系统全貌

```
┌────────────────────────────────────────────────────┐
│  观测台 Observatory · Wayfinder 引航蜂 · 开场页      │  ← 呈现层
├────────────────────────────────────────────────────┤
│  数据契约 API_CONTRACT.md                            │  ← 契约层
│  research-package/v1 · research-v1 · 逐字段对齐       │
├────────────────────────────────────────────────────┤
│  service.py · models.py · task_ledger.py             │  ← 事实源
│  policy.py · records.py · feedback.py                │
├────────────────────────────────────────────────────┤
│  蜂群运行时 swarm · 研究层 research                   │  ← 系统层
└────────────────────────────────────────────────────┘
```

### 4.1 蜂群运行时（swarm）

- **信号场**：任务以信号形式广播，携带 workspace、scope、kind、required_capability 与载荷。
- **任务账本（task_ledger）**：全局自增 `sequence` 的事件流——创建、认领、续租、释放、转交、完成、失败、阻塞，一条不漏。任何任务都可按 `sequence` 升序完整回放。
- **租约与 fencing token**：认领、续租、转交全部携带 token，杜绝幽灵持有者。
- **策略选择**：`policy_selection` 事件记录系统推荐，`research_choice` 记录成员的实际选择与覆盖行为，策略效果本身成为可研究的对象。

### 4.2 研究层（research）

- **七类笔记**：observation / hypothesis / supporting_evidence / opposing_evidence / dispute / expert_opinion / cross_domain_link，每条带来源引用（identifier、version、license、location、excerpt）。
- **分支生命周期**：proposed → exploring → testing → supported / disputed / refuted / archived，休眠与重开由纠偏事件驱动，理由强制留痕。
- **经验代谢**：贡献被采纳记入 `contributions`，被复用记入 `adoption_receipts`，被取代记入 `supersessions`——沉淀、复用、加速三个复合指标让"经验复利"第一次变得可度量。

### 4.3 机会路由（policy）

`RouteOpportunityPlan` 为每条分支计算机会份额（share ∈ [0,1]），因子完全透明：evidence、applicability、goal_relevance、risk、支持/反驳计数、探索下限。探索配比（exploration fraction）是显式参数，而非隐藏魔法；不可路由的分支必须标注理由——证据不足、成本未知、条件下被反驳、休眠、归档、越界，**没有"系统不喜欢你"这种理由**。

### 4.4 观测台（Observatory）

以 GitHub Dashboard 为蓝本逐区块复刻的研究工作台，让蜂群像代码仓库一样被浏览：

- **Dashboard**：问候区、Wayfinder 提问卡（读取机会份额回答"下一步去哪"）、In-flight tasks（进行中的认领）、Ledger 更新流（按日期分组的重要事件）、专家意见栏、Swarm Assembly 横幅。
- **Signals**：按契约泳道组织的全部信号——待认领（available / partial / handoff）、进行中（claimed / submitting）、已沉积（completed / failed / blocked），过滤即搜。
- **Feed**：`task_audit` 全量事件流，实时事件以金痕高亮入场，点击任意事件进入任务回放。
- **任务回放**：抽屉式时间线，从创建到归档的每一跳（含执行核验状态、观察笔记、复用凭据）一目了然。
- **快捷键即信仰**：`g d` 回 Dashboard、`g i` 看信号、`g p` 看 Feed、`g n` 开通知、`/` 唤起命令面板、`W` 呼叫 Wayfinder、`Esc` 逐层退出。

### 4.5 Wayfinder · 引航蜂

蜂群的导航 Agent。它不做决策，只做翻译——把机会路由的份额、因子与理由翻译成一句人话："当前最高机会在软边界分支，份额 48%，证据充分，风险为零；硬边界分支正在休眠，理由是基线被证伪。"它住在顶栏、住在卡片里、住在快捷键 `W` 上，也住在每一条路线卡片背后的完整数据里。

### 4.6 开场页与背景引擎

系统的入口本身就是一次形态发生演示：全屏黏菌 WebGL 模拟（移植自 Bewelge/Physarum-WebGL，MIT）自然生长数秒后，"Morphogenesis · decentralized Agent swarm" 浮现。观测台的背景则是一张常驻的黏菌拓扑场——65,536 个 agent 组成金色族三物种，在纸面底色上持续萌发、沉积、消退，**让"不断重塑的网络"成为整个系统的底色**。

### 4.7 数据契约

`API_CONTRACT.md` 是前后端之间唯一的数据契约：字段名照抄、口径公开（活跃、空闲、沉淀、复用、加速、时延，全部给出精确定义）、schema 带版本号（`research-package/v1` / `research-v1`）。数据层被收敛为四个函数——`fetchPackage` / `fetchSnapshot` / `fetchReplay` / `subscribeActivity`——视图组件对 mock 与真实后端完全无感，**换后端不动视图**。

## 五、这个项目里生长出来的一切

围绕这套理念，Morphogenesis 已经长出了自己的完整器官：

- **观测台单文件应用**：GitHub Dashboard 1:1 复刻界面，Primer 设计语言 × 黏菌金品牌色，零依赖、双击即开。
- **黏菌开场页**：Physarum WebGL 实时模拟 + 品牌宣言，既是门面也是隐喻的现场演示。
- **PhysarumField.jsx**：独立的 React 黏菌场组件，可嵌入任何需要"活的背景"的界面。
- **数据层契约 mock**：与 API_CONTRACT.md 逐字段对齐的本地数据源，支撑界面独立迭代。
- **Wayfinder 引航蜂**：机会路由的对话式入口与路线面板。
- **黏菌背景引擎**：从开场页特效蒸馏而来的常驻拓扑场，三物种金色族、随机萌发、减动效降级。
- **交付工具链**：单文件组装、语法校验、ID 对账、token 核验、制品检查器，保证每一次交付可复制、可验证。
- **完整交付包**：成品、源码、契约文档、使用说明一体的 zip 制品。

## 六、价值主张与合作方向

Morphogenesis 面向所有**"经验比算力更稀缺"**的组织：

- **AI 实验室与 Agent 团队**：蜂群协作过程全程可观测、可回放、可审计；策略推荐与成员选择的偏差本身成为研究对象。
- **科研机构**：研究过程即数据——三轴结果、证据边界、纠偏轨迹，让"失败"也沉淀为组织资产，让复现性从口号变成账本字段。
- **企业研发中心**：经验代谢指标（沉淀 / 复用 / 加速）第一次让"组织有没有变聪明"可以被度量，而不是被感觉。

我们期待三类伙伴：

1. **联合研究伙伴**——把真实研究问题放进蜂群，共同打磨机会路由与证据边界的学术与实践价值；
2. **试点部署伙伴**——在真实研发流程中运行 Morphogenesis，用你们的经验数据验证"经验复利"；
3. **生态共建伙伴**——契约即接口。围绕 `research-package/v1` 契约，任何观测端、执行端、存储端都可以接入这张网络。

这不是一个被做完的系统，而是一片正在被耕耘的土壤。我们寻找的不是用户，而是一起种地的人。

## 七、设计哲学

- **形式追随生物**：界面里反复出现的不是装饰，而是隐喻本身——沉积的卡片、泳道的状态、拓扑的背景、金痕的通知。
- **诚实优先于好看**：unverified 的意见不会被美化成事实，被取代的贡献不会被悄悄删除，未知成本显示为 `—` 而不是一个编出来的数字。
- **克制即是氛围**：黏菌金只出现在该被注意到的地方——机会、命中、生长；其余交给纸张般的底色与发丝般的边框。

## 八、仓库结构

```
morphogenesis-observatory/
├── README.md                ← 你在读的这篇
├── env-observatory.html     ← 观测台单文件（双击即开）
├── physarum-landing.html    ← 开场页单文件
├── PhysarumField.jsx        ← 黏菌场 React 组件
├── docs/
│   └── API_CONTRACT.md      ← 前后端唯一数据契约
└── src/
    ├── env-observatory/     ← 观测台源码（骨架/样式/视图/数据层/背景引擎）
    └── physarum/            ← 开场页源码
```

## 九、许可与署名

- 黏菌模拟引擎移植自 [Bewelge/Physarum-WebGL](https://github.com/Bewelge/Physarum-WebGL)，遵循 MIT License。
- 界面设计参照 GitHub Dashboard 的信息架构与 Primer 设计语言。
- 其余部分属于 Morphogenesis 项目自身的工作。

## 十、参与我们

蜂群的拓扑，由每一个加入的个体改变。

带着你的研究问题来，带着你的失败数据来，带着你对"Agent 应该如何协作"的偏见来——把偏见写成假设，把假设交给蜂群，把结果留给账本。

**The swarm remembers. The network grows.**
