# Morphogenesis · AI 原生多 Agent 多轨开发说明（v1）

> **读者：接入本项目的 AI 开发 Agent（下称"你"）。** 本文是**可执行的作业规范**，不是背景介绍。开工前请完整读完 §0–§3，再读你自己的任务卡。
> **项目**：Morphogenesis（形态发生）——会自我代谢与进化的去中心化蜂群（深圳 EvoMAP 进化酒馆 · 赛道4 多 Agent 分群协作）。
> **架构边界（已定）**：本系统为**独立原型，不依赖、不派生自 ORCA 或任何既有工程**。
> **关联文档**：《作战方案 v2》《开发文档 v2》《深度思考》《时间安排表》。**本文与《开发文档 v2》冲突时，以本文的隔离与作业规范为准。**

---

## §0 你是什么、你要交付什么

- 你是**多轨并行开发中的一个 Agent**，被分配到**一条且仅一条轨道**（T0–T5）。
- 你**只对自己轨道的文件目录有写权限**（见 §4 所有权表）。**越界写 = 严重违规。**
- 你的产出必须能被**别的轨道的 Agent 直接接上**——接口先行，隔离运行（见 §5）。
- 你**禁止 mock 通过验收**（见 §6）。你**禁止臆测上游结构**（见 §3 铁律）。

**一个任务"完成"的定义**（缺一不可）：
1. 你轨道交付物已实现；
2. 契约调用方与实现方**用同一份契约跑通一次真实调用**（不是"列出类和函数"）；
3. 验收状态被**如实标记**（`contract_local / interface_live / task_live`，见 §6）；
4. 变更只落在你的目录内，合并时**无跨轨文件冲突**。

---

## §1 绝对不变量（任何轨道、任何时刻都不得违反）

| # | 不变量 | 含义 |
|---|---|---|
| I1 | **独立原型（代码不依赖 ORCA）** | 代码库自建，**不派生自 ORCA/任何既有工程**，不假设存在未声明的上游模块。**但运行时可用 ORCA 批发 Agent（数量无上限）** —— ORCA 是"兵源"非"地基"。对外已声明接口：EvoMap A2A/GEP（经验侧）+ ORCA 批发接口（供给侧，可选）。 |
| I2 | **身份三层** | `Role`(职责) / `AgentId`(成员) / `AttemptId`(尝试) 缺一不可，禁止用 Role 代替成员或尝试。 |
| I3 | **消息成封装** | 一切跨 Agent 通信走统一 `Envelope`（见 §5.4），禁止裸枚举或自定义消息体。 |
| I4 | **目录命名唯一** | 编排目录统一为 **`orchestration/`**（禁止 `orchestrator/`）；所有跨文档引用名必须与此一致。 |
| I5 | **经验所有权** | 经验使用状态归 `metabolism`；发布归 T1 且须过批准门；Evolver 不得按自身阈值自动发布。 |
| I6 | **mock 不验收** | 模拟数据带 `provenance=mock`，**永不进入 `task_live` 验收**；勿用夹具冒充真实发布。 |
| I7 | **锁文件统一** | `poetry.lock`/`package-lock.json` 由 **T0 独占生成与维护**，其他轨不得独立更新依赖。 |
| I8 | **无凭据入库** | 任何密钥/token **不写入仓库**；Hub 凭据未确认前**只用本地隔离 stub**。 |

---

## §2 系统一句话与三层闭环（你要接的那条线）

```
外层·进化循环(可选T4) → 解码为蜂群配置
        ↓
内层·协作拓扑(T3 topology) ← 执行由(T2 orchestration + 真实执行入口)驱动
        ↓ 执行中消费/产出 Gene
代谢·经验整理(T3 metabolism) → 最优 Gene
        ↓
EvoMap Hub(T1 hub_client) ← 本地验证 → Gene+Capsule 打包 → 发布
```

**闭环成立的最低要求**：外层产出配置 → 内层按配置运行并把**真实成功/失败**回写 → 代谢据此更新经验 → 最优经验发布并回流为新一代候选。**任一环断开，系统退化为"一堆 Agent 在跑"。**

---

## §3 给 AI Agent 的铁律（违反即判不合格）

1. **契约只读**：`contracts/` 只允许 **T0** 写；你要改契约，**提交"契约变更提案"**（§5.3），不得直接改。
2. **禁止臆测上游**：不得假设存在未在本文出现的模块、宿主、配置或数据。
3. **禁止 mock 冒充**：`provenance=mock` 的结果不得标记为 `interface_live` 或 `task_live`。
4. **禁止越界写**：只写你轨道目录；需要别轨数据，**走接口，不走文件偷读**。
5. **禁止静默降级**：接口跑不通时**上报阻塞**，不得私自换实现、改语义、绕过验收。
6. **接口先行**：先确认契约（§5），再写实现；**"跑通一次"才是冻结**，不是"签名看起来对"。
7. **可追溯**：每个产物、每条经验、每次发布都要有身份与来源标记（`AttemptId` / `provenance` / `asset_id`）。
8. **诚实标注**：能力与命名对齐——只做配置参数优化就**不叫**"策略遗传"。

---

## §4 多轨总览、所有权与目录（隔离的骨架）

### 4.1 六轨与依赖图

```
T0 契约与地基 ──┬─► T1 Hub/跨语言
(契约/持久化/   ├─► T2 编排与执行
 锁文件/样例任务)─┼─► T3 拓扑与代谢(含共享 mock 唯一所有者)
                ├─► T4 外层进化(可选, 出主链)
                └─► T5 演示与可视化(尽早接真实事件)
```
- **T0 是所有轨的前置**：契约未"跑通一次"，其他轨**不得进入真实验收**（可先写实现，但只能用 `contract_local` 状态）。
- **T3 是共享 mock 的唯一所有者**：T2/T4/T5 需要拓扑/代谢 mock 时**只读** T3 的实现。

### 4.2 目录所有权表（**唯一写入者**）

| 目录 | 唯一写入者 | 其他轨权限 |
|---|---|---|
| `contracts/`（identity/messages/resolution/schema） | **T0** | 只读 |
| `persistence/`（SQLite+SQLModel 元数据） | **T0** | 只读 |
| `bootstrap/`（启动入口、固定样例任务） | **T0** | 只读 |
| `hub_client/`、`bridge_node/`（MCP 客户端 + 子进程哈希） | **T1** | 只读 |
| `orchestration/`（LangGraph 图、执行入口） | **T2** | 只读 |
| `topology/`、`metabolism/`（自研核心） | **T3** | 只读 |
| `mocks/`（**共享 mock 唯一实现**） | **T3** | 只读 |
| `evolution/`（外层进化，可选） | **T4** | 只读 |
| `viz/`、`demo/`（可视化与演示） | **T5** | 只读 |
| `tests/`（**分轨子目录**，见 §5.5） | 各轨自持 | 各自只读他人 |
| `poetry.lock` / `package-lock.json` | **T0** | 只读 |
| `.gitignore` / CI 配置 | **T0** | 只读 |

> **规则**：任何需要修改非自有目录的诉求，**走 §5.3 契约变更提案或接口请求**，不得直接编辑。

### 4.3 建议目录树（以 T0 冻结版为准，此处仅示意）

```
morphogenesis/
├─ contracts/            # I2 I3 —— T0
│  ├─ identity.py        #   Role / AgentId / AttemptId
│  ├─ messages.py        #   Envelope / MsgType
│  ├─ resolution.py      #   Gene / GeneRef / Metabolism(Protocol)
│  └─ provenance.py      #   live|replay|mock
├─ persistence/          # T0（SQLite+SQLModel）
├─ bootstrap/            # T0（launch + 固定样例任务）
├─ hub_client/           # T1（A2A publish/fetch）
├─ bridge_node/          # T1（MCP 客户端 + 子进程哈希 + Python 降级）
├─ orchestration/        # T2（LangGraph，统一命名）
├─ topology/             # T3
├─ metabolism/           # T3
├─ mocks/                # T3（共享唯一实现）
├─ evolution/            # T4（可选）
├─ viz/ demo/            # T5
└─ tests/
   ├─ t0/ t1/ t2/ t3/ t4/ t5/     # 分轨隔离
   └─ integration/                # 合流门用（只读各轨）
```

### 4.4 ORCA Agent 批发接入（供给面 · 可选）

- **定位**：ORCA 是**运行时 Agent 供给面**，用于按需批发蜂群成员，**数量无上限**；**不是代码上游**（不得引入 ORCA 代码作为项目地基）。
- **接入边界**：
  1. 批发得到的每个 Agent **必须获得本项目三层身份**（`Role`/`AgentId`/`AttemptId`）；ORCA 侧 ID 仅作**外部映射**，不得替代内部身份；
  2. **单一所有者**：ORCA 适配层独立为 **`orca_provision/`**（与 `hub_client/` 同级），**归 T1 唯一所有者**，不得散落各轨；
  3. **降级可用**：ORCA 不可用时，系统**降级为固定规模蜂群**，主闭环不受影响；
  4. **供给无上限 ≠ 支出无上限**：仍受 §3.5 运行规格（总预算/最大重试/停止条件）约束；每次批发登记 `Provision`（来源/数量/配额/`provenance`）。
- **隔离要求**：供给接口独立 channel + 独立凭据 + 独立日志，**不与经验侧（EvoMap）混用**。

---

## §5 多链路隔离模型（**本文核心**）

> 目标：**多条轨道像多条独立管线并行，互不污染、互不阻塞，最终能在同一真实系统里合流。** 隔离不是"物理分开就完事"，而是**每一条链路都定义清楚"边界、所有权、接口、观测点"。**

### 5.1 隔离维度矩阵（逐维度落做法）

| 维度 | 要隔离什么 | 具体做法 | 违反后果 |
|---|---|---|---|
| **1 文件系统** | 各轨代码互相覆盖 | 每轨**独立 `git worktree` + 独立分支**（`feat/t0-contracts`…）；目录所有权见 §4.2 | 合并冲突、互相覆盖 |
| **2 契约** | 接口漂移 | `contracts/` 归 T0；变更走提案（§5.3）；契约**版本号 + 语义测试** | 两轨"同名不同义" |
| **3 进程** | 运行时互相干扰 | 各轨**独立进程**，各自 PID/日志文件；不共享常驻进程 | 端口/状态串扰 |
| **4 端口/网络** | 服务端口冲突 | 统一端口分配表（§5.6）；MCP/HTTP 各自独占端口 | 绑定失败 |
| **5 数据存储** | DB/索引串写 | **每轨独立 SQLite 文件 + 独立表/命名空间**；检索索引按轨隔离（`idx_<track>`） | 数据互相污染 |
| **6 消息/事件** | 事件流混线 | 一切消息走 `Envelope`；**用 `task_id`+`attempt`+`seq` 做关联与去重**；测试用独立事件日志 | 事件不可追溯 |
| **7 mock** | 模拟数据假冒真实 | `provenance` 标记 + 三态分离（§6）；**共享 mock 唯一所有者 T3** | 假结果进真验收 |
| **8 凭据** | 密钥泄漏/越权 | 每 worktree 独立 `.env`（**git-ignore**）；Hub **只用沙箱/stub** | 安全事故 |
| **9 产物** | 产物覆盖/来源丢失 | 产物按轨目录存放 + 内容寻址（`asset_id`/哈希）；登记 `attempt` 与 `provenance` | 无法复现 |
| **10 时间/调度** | 抢资源、长任务拖累全队 | 各轨 CI 独立；**合流门**（§7）定时收敛；T4 出主链不阻塞 | 全队等待 |

### 5.2 git worktree 与分支模型（维度 1 落地）

```bash
# 每轨一次（示例：T3）
git worktree add ../morphogenesis-t3 -b feat/t3-topology-metabolism
cd ../morphogenesis-t3
```
- 共享同一 `.git`，但**工作目录独立**，互不覆盖。
- **禁止**在他人 worktree 里提交。
- 分支命名：`feat/t<数字>-<主题>`；合流分支 `main`（受保护，只由 §7 合流门推入）。

### 5.3 契约变更提案（维度 2 落地）

你要改 `contracts/` 时，提交一份提案（附在 PR 描述里），包含：
1. **动机**：当前契约哪里不足以表达系统；
2. **兼容性**：破坏性 or 兼容；影响哪些轨；
3. **调用方 + 实现方**：分别是谁，怎么"跑通一次"；
4. **语义测试**：同签名不同语义如何被暴露（`tools/contracts_check.py`）。
> **T0 审核通过并更新 `contracts/` 后**，其他轨再对齐。**契约冻结条件 = 一个调用方与一个实现方用同一份契约跑通一次真实调用。** 时间不是门禁。

### 5.4 统一消息封装 Envelope（维度 6 落地）

```python
# contracts/messages.py（T0 维护；示意最小集）
class MsgType(str, Enum):
    INTENT = "intent"; RESULT = "result"; SIGNAL = "signal"

class Envelope(BaseModel):
    msg_id: str                       # 幂等键（去重）
    msg_type: MsgType
    sender: AgentId
    receiver: AgentId | Literal["broadcast"]
    task_id: str
    attempt: AttemptId
    artifact_uri: str | None = None   # 关联产物
    seq: int                          # 事件顺序
    handled: bool = False
    provenance: Literal["live", "replay", "mock"] = "live"
    ts: float
```
**隔离要点**：跨轨事件必须能回答"谁在哪个任务的哪次尝试、向谁、发了什么、关联哪个产物、是否已处理"。**重复反馈按 `msg_id`/`attempt` 去重，不重复奖励。**

### 5.5 测试隔离（维度 5 + 1 落地）

- `tests/` 按轨分目录：`tests/t0 … tests/t5`，各轨只跑自己 + 只读他人。
- 测试**数据库独立**：`tmp/<track>_<runid>.db`，用完即弃。
- `tests/integration/` 只用于**合流门**，不属于任何单轨。
- 单测**不得**依赖他人的私有 mock（共享 mock 只由 T3 提供）。

### 5.6 端口与进程分配表（维度 3/4 落地）

| 用途 | 端口 | 归属 | 说明 |
|---|---|---|---|
| MCP 客户端桥 | 7101 | T1 | `bridge_node` 主路径 |
| Hub A2A（沙箱/stub） | 7102 | T1 | 未确认凭据前指向本地 stub |
| LangGraph/编排调试 | 7200 | T2 | 仅本地 |
| 拓扑/代谢调试 | 7300 | T3 | 仅本地 |
| 可视化本地预览 | 7500 | T5 | 静态或 dev server |
| 合流集成 | 7900 | 合流门 | 全链路 |
| ORCA Agent 批发 | 7103 | T1 | 供给面；未确认凭据前用本地 stub |

> 各轨**不得占用他人端口**；需要临时端口时登记到本表（PR 中同步更新）。

### 5.7 运行来源与三态（维度 7 落地，与 §6 联动）

- 运行来源：`provenance ∈ {live, replay, mock}`；`replay` **必须指向原始运行记录**。
- 验收三态**各自独立、不共用绿色**：
  - `contract_local`：本地契约通过；
  - `interface_live`：真实接口通过（如真实 Hub stub/沙箱）；
  - `task_live`：真实任务通过。

---

## §6 验收纪律：mock 与真实验收的硬隔离

| 规则 | 内容 |
|---|---|
| R1 | 事件与结果**必须携带 `provenance`**。 |
| R2 | 三态验收（`contract_local/interface_live/task_live`）**分开记录**，不得用一个绿灯代表全部。 |
| R3 | **测试夹具不得冒充实际经验发布**；Hub 沙箱无官方地址/凭据前**只用本地隔离 stub**；Hub 不可用时产品显示**"待发布"**并保留本地产物。 |
| R4 | `provenance=mock` 的结果**永不**进入 `task_live`。 |

**能力检查（替代"覆盖率数字"）——勾选即算数，用 mock 通过不计分：**
- [ ] 权重真的影响调用：改权重后下一次 `select()` 结果随之改变。
- [ ] 重复结果不重复奖励：同一 `msg_id`/`attempt` 重复上报，权重只更新一次。
- [ ] 接续不重复副作用：恢复后无重复文件写入/重复工具调用。
- [ ] 经验真的被使用：`inject` 后的 Gene 在运行中留有 `mark_used` 记录。
- [ ] 模拟结果不冒充实测：`provenance=mock` 不进入 `task_live`。
- [ ] 三态验收分离：三项各自独立可查。

---

## §7 协作与合流协议

### 7.1 分支与提交流程
1. 在自有 `feat/t<N>-*` 分支开发；
2. 提交前本地跑：`mypy/pyright`（覆盖契约与实现）+ 你轨测试 + `tools/contracts_check.py`；
3. 提 **PR**：描述**变动目录、依赖的契约版本、验收状态、是否触及接口**；
4. 触及 `contracts/` 的 PR **必须附 §5.3 提案**，由 T0 审。

### 7.2 合流门（Milestone Gate）
| 门禁 | 条件 |
|---|---|
| **G0 开工前六项** | 执行入口 / 身份与事件 / 机制闭环 / 兼容环境 / 受控运行 / 真实验收 —— 最小完成 |
| **G1 契约冻结** | 一个调用方 + 一个实现方**跑通一次**（非"T+2h"） |
| **G2 轨道集成** | 各轨在其目录内 `contract_local` 全绿 |
| **G3 真实接口** | T1/T2 达 `interface_live` |
| **G4 端到端** | `interface_live` + `task_live` **分别**通过（拆开，不合并） |
| **G5 可选进化** | T4 在主闭环稳定后再接（出主链） |

### 7.3 冲突解决
- **文件冲突**：按 §4.2 所有权判定，**唯一写入者**说了算；其他人改回并提接口请求。
- **语义冲突**：以 `contracts/` 的**语义测试**为准，两边对齐后再继续。
- **阻塞上报**：任何"跑不通"立即上报，**禁止**私改契约/换实现/绕过验收。

---

## §8 分轨任务卡（作业单）

> 每张卡：**目标 / 交付物 / 依赖契约 / 验收 / 禁止 / 隔离要求**。只读你被分配的那张。

### T0 · 契约与地基（前置，最先）
- **目标**：让全队有**唯一契约 + 可复现环境 + 一个固定样例任务**。
- **交付物**：`contracts/`（identity/messages/resolution/provenance）、`persistence/`（SQLite+SQLModel）、`bootstrap/`（启动入口 + 固定样例任务）、`poetry.lock`/`package-lock.json`、CI 与 `.gitignore`、`tools/contracts_check.py`。
- **依赖契约**：无（它**产出**契约）。
- **验收**：`contract_local` + 一个调用方与实现方**跑通一次**；`mypy/pyright` 覆盖契约与实现；锁文件已提交。
- **禁止**：写任何其他轨目录；允许他人改契约。
- **隔离要求**：契约变更须走 §5.3；锁文件独占。

### T1 · Hub 与跨语言边界
- **目标**：**固定 Python→Node 边界**并打通真实资产校验与受控接口。
- **交付物**：`hub_client/`（A2A `publish/fetch`、`hello` 凭据处理、状态生命周期）、`bridge_node/`（**MCP 主路径** + 子进程做 `canonicalize/computeAssetId/verifyAssetId` + Python 降级）。
- **依赖契约**：`contracts/resolution.py`（Gene/GeneRef）、`contracts/identity.py`。
- **验收**：`interface_live`（对**真实沙箱/stub** 跑通 hello→publish→fetch；**假 Gene 跑通只能证明调用方与假实现配合，不算真实验收**）。
- **禁止**：把 SDK/CLI/MCP 三路混用而不说明谁调用、何时调用；用降级路径声称"官方校验通过"。
- **隔离要求**：凭据入 `.env`（git-ignore）；端口 7101/7102 独占；Hub 只用 stub。

> **已核实事实**：`@evomap/gep-sdk` **不含算法代码**（只提供 schema/hash）；`gep-a2a` 消息有 **7 必填字段**；Evolver 要求 **Node ≥18（推荐 ≥22.12）且必须在 git 仓库内运行**；SCHEMA 版本会漂移，**以锁定版本为准**。

### T2 · 编排与执行（真正干活的节点）
- **目标**：**一个真实执行者跑通一个小任务、返回真实产物与执行记录**，再串入独立复核。
- **交付物**：`orchestration/`（LangGraph 图 + **固定执行入口**）、身份/事件运行时、恢复（checkpoint）接线。
- **依赖契约**：`contracts/messages.py`（Envelope）、`contracts/identity.py`。
- **验收**：`interface_live` + 能力检查（权重影响调用 / 重复不重复奖励 / 接续不重复副作用）。
- **禁止**：把"LangGraph 骨架"当作交付（框架只决定调用顺序，**不提供真正干活的节点**）。
- **隔离要求**：目录统一 `orchestration/`；**SqliteSaver 用 `with` 上下文**（并补 `langgraph-checkpoint-sqlite`）；**checkpoint 只保存线程范围图状态，不自动保存外部工作目录/防重复副作用**。

### T3 · 拓扑与代谢（自研核心 + 共享 mock 唯一所有者）
- **目标**：权重**真的影响选路**；经验有正文解析、注入、采用记录；`mocks/` 提供**唯一共享实现**。
- **交付物**：`topology/`（管道权重 + `select()`）、`metabolism/`（`resolve/inject/mark_used/decay/archive`）、`mocks/`。
- **依赖契约**：`contracts/resolution.py`、`contracts/identity.py`。
- **验收**：`contract_local` + **证明"改权重→下次 `select()` 结果改变"**、"重复反馈只更新一次"。
- **禁止**：让 `mocks/` 被他人写入；归档/停用不同步检索索引。
- **隔离要求**：**共享 mock 唯一所有者**；归档须**原子同步**记忆图/本地缓存/检索索引三处。

> **公式边界（必须写进代码）**：`D ← (1−λ)·D + α·Q·s` —— 恒定输入只收敛到权重值（`→αr/λ`），**不等于最优拓扑**；闲置链路有限步**不归零**，须显式定义阈值+低活跃窗口+保留条件；**更新已有边不会自动生新边**，新边候选规则须另行定义。

### T4 · 外层进化（**可选，出主链**）
- **目标**：主闭环稳定后，再接候选生成与有限评估。
- **交付物**：`evolution/`（编码/解码、`evaluate`→`next_generation` 闭环）。
- **依赖契约**：`contracts/identity.py`、`resolution.py`。
- **验收**：`contract_local`；**名称与能力对齐**（只做配置参数优化就叫"配置进化"，不叫"策略遗传"）。
- **禁止**：进主链阻塞；把 `approval` 作为自由变异维度。
- **隔离要求**：**只读** T3 的 `mocks/`；"20×3"= **60 个候选评估槽位**，若跑真蜂群 = 60 次真实调用，成本须显式标注。

### T5 · 演示与可视化
- **目标**：**尽早接入第一条真实事件**，mock 只补齐未完成场景。
- **交付物**：`viz/`（Gene 谱系图 + 消息流双视图）、`demo/`（5 分钟可跑可量化任务）。
- **依赖契约**：`contracts/messages.py`（读 Envelope 流）。
- **验收**：`interface_live`（展示真实事件流）；图表区分**当前/均值/历史最佳**，**不预设单调上升**。
- **禁止**："一路上涨""经验池越小越省 Token"等绝对化表述。
- **隔离要求**：端口 7500；只读他人事件，不写他人目录。

---

## §9 开工顺序（给全队 AI 的调度）

1. **T0 先起**：冻结契约（跑通一次）+ 锁文件 + 样例任务 + 启动入口；
2. **T1/T2/T3 并行**（均只依赖 T0 契约）；**T5 尽早接第一条真实事件**；
3. **G2 各轨 `contract_local` 全绿**后进 **G3 `interface_live`**；
4. **G4 端到端**：`interface_live` 与 `task_live` **分别**通过；
5. **T4 可选**：主闭环稳定后再接。

---

## §10 一页速查（贴在你的工作区）

```
只写自己目录   —— 越界写=违规；跨轨走接口/提案
契约只读       —— contracts/ 归 T0；变更走提案 + 跑通一次
命名唯一       —— orchestration/（不是 orchestrator/）
身份三层       —— Role(职责) / AgentId(成员) / AttemptId(尝试)
消息成封装     —— Envelope：msg_id+task+attempt+artifact+seq+provenance
mock 不验收    —— provenance 标记 + 三态分离(contract_local/interface_live/task_live)
SDK 无算法     —— gep-sdk 只给 schema/hash；选择/记忆图在 evolver/mcp-server
跨语言先定     —— MCP 主路径 + 子进程哈希 + Python 降级
ORCA 批发      —— 供给面可选，Agent 数量无上限；代码不依赖 ORCA
隔离十维       —— 文件/契约/进程/端口/DB/消息/mock/凭据/产物/调度
先补六项       —— 执行入口/身份事件/机制闭环/兼容环境/受控运行/真实验收
```

> **一句话**：**每条链路都边界清晰、所有权唯一、接口先行、隔离运行——这样多条轨道才能像多条独立管线并行，最后在同一真实系统里合流，而不是互相污染。**
