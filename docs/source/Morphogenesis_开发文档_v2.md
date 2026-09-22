# Morphogenesis 开发文档 v2（评审修订版）

> 项目：会自我代谢与进化的去中心化蜂群（赛道4 · 多 Agent 分群协作）
> v2 的定位：**保留 v1 的复用优先与分轨思想，修正"接口未闭合却被当作已冻结"的根本问题。**
> 关联：《作战方案 v2》《时间安排表》

---

## §0 本版修订说明（证据分级）

本版对另一 AI 评审意见**逐条核验**后分三类处理。**证据分级：**

| 级别 | 含义 | 标记 |
|---|---|---|
| ✅ 已核实 | 本轮从官方源/源码快照/自有文档确认 | 附来源 |
| 📝 采纳（设计） | 属工程判断，评审合理，采纳 | 无条件采纳 |
| ⚠️ 需你确认 | 依赖我未掌握的上下文（如既有工程） | 待确认 |

**核心结论采纳**：**v1 最薄弱处正是它最强调的"T+2h 冻结契约"。当前契约不足以表达系统，冻结只会把缺口冻结下来。** 本版不再以时间冻结契约。

**本轮已核实的关键事实：**

- ✅ **`@evomap/gep-sdk` 不含算法代码**。官方原文："This package intentionally carries no algorithm code. Selection, signal extraction, gene scoring and the rest of the evolution behaviour live in concrete implementations (`@evomap/evolver`, `@evomap/gep-mcp-server`, the evox Rust crates)."（来源：npm @evomap/gep-sdk）→ v1 说"封装 SDK 完成 publish/fetch"不成立，SDK 只提供 schema/hash。
- ✅ **`gep-a2a` 消息是带 7 个必填字段的封装**（`protocol / protocol_version / message_type / message_id / sender_id / timestamp / payload`），不是裸的 `intent/result/signal` 枚举。
- ✅ **Evolver 环境要求 Node ≥18（推荐 ≥22.12）**，且**必须在 git 仓库内运行**。→ v1 只写"Node ≥18"不完整。
- ✅ **SCHEMA_VERSION 已远高于 1.7.0**（核查时 npm 已发布 gep-sdk 1.13.0，源码快照显示 1.14.0）。→ v1 写"当前 1.7.0"过时，且版本会漂移。
- ✅ **v1 内部一致性错误**（自查确认）：`orchestrator` 与 `orchestration` 目录名不一致；角色编码归一化丢失总人数；T2 与 T4 都写 `mocks/topology.py`；`SqliteSaver.from_conn_string(...)` 直接当 checkpointer 传入。

> **总原则升级**：**"列出了类和函数" ≠ "接口已完整"；"库提供某能力" ≠ "项目已解决该问题"。**

---

## §1 复用优先原则（保留 + 补"缝合成本"）

### 1.1 三条硬规则（保留）

1. **官方优先** 2. **成熟库优先** 3. **自研仅限差异化**

### 1.2 新增第四条：**缝合成本显式化**

v1 只列"复用什么"，忽略了**最贵的部分——如何接起来**。本版新增要求：每个复用项必须写明**接入方式**与**所有权**（见 §3、§4）。

### 1.3 复用决策矩阵 v2

| 模块 | 决策 | 复用对象 | 接入方式（新增） | 所有权（新增） |
|---|---|---|---|---|
| GEP 资产模型 / schema / hash | **复用** | `@evomap/gep-sdk` | Node 依赖 | T1 |
| 选择 / 信号提取 / 记忆图 / solidify | **复用** | `@evomap/evolver`（CLI） | Node 子进程 | T1 |
| Agent 侧 GEP 工具 | **复用** | `@evomap/gep-mcp-server` | MCP 客户端 | T1 |
| Hub 发布 / 拉取 | **复用** | A2A HTTP | Python httpx | T1 |
| 多 Agent 编排 + 状态机 | **复用** | **LangGraph** | Python 原生 | T2 |
| 外层进化 | **复用（移出主链）** | EvoX | Python，见 §6 | T4（可选） |
| 向量检索 | **复用** | Chroma/FAISS | Python 原生 | **T3（唯一所有者）** |
| 持久化 | **复用** | SQLite + SQLModel | Python 原生 | T0（元数据） |
| 校验 | **复用** | Pydantic | Python 原生 | 契约层 |
| 可视化 | **复用** | ECharts/D3 | 前端 CDN | T5 |

> **许可提示**：Evolver 为 **GPL-3.0**（来源：RepoRank 对比页）；gep-sdk 许可以其 `package.json` 为准。黑客松本地使用无碍，再分发需确认。

### 1.4 自研边界（不变量，保留）

自研仅限：`topology/`、`metabolism/`、`evolution/`、`swarm/`。

---

## §2 接口契约 v2（**不冻结**，以"跑通"为冻结条件）

### 2.1 冻结条件修正（📝 采纳）

> **v1**：T+2h 冻结。
> **v2**：**冻结条件 = 一个调用方与一个实现方，已用同一份契约跑通一次真实调用。** 时间只是参考，跑通才是门禁。

理由：接口签名不变也可能语义漂移（如 `success` 一轨理解为"模型说完成"，另一轨理解为"独立验收通过"）。

### 2.2 身份模型（📝 采纳，**关键补强**）

v1 用 `Role` 同时承担"职责"和"成员身份"，导致 3 个 builder 无法区分。修正为**三层身份**：

```python
# src/contracts/identity.py
Role = Literal["planner", "builder", "reviewer", "aggregator"]

class AgentId(BaseModel):
    """成员实例：Role 表示职责，AgentId 表示具体成员"""
    role: Role
    instance: int                       # 同一 Role 下的序号

class AttemptId(BaseModel):
    """某次执行尝试"""
    task_id: str
    agent: AgentId
    attempt: int                        # 重试序号，用于去重与副作用控制
```

**规则**：路由可先选 Role 再选实例，也可直接选实例——**但不得省略实例层**。

```python
class PipeState(BaseModel):
    src: AgentId                        # 由 Role 升级为 AgentId
    dst: AgentId
    weight: float = 0.0
    flow: float = 0.0
    success_rate: float = 0.5
    active: bool = True
```

> **说明**：Role 级统计可保留为**聚合视图**，但**实例级执行必须单独记录**。

### 2.3 消息契约（📝 采纳，**关键补强**）

v1 只有三个枚举，没有结构。v2 定义**统一消息封装**（呼应有 7 必填字段的 `gep-a2a` 封装）：

```python
# src/contracts/messages.py
class MsgType(str, Enum):
    INTENT = "intent"; RESULT = "result"; SIGNAL = "signal"

class Envelope(BaseModel):
    """本项目内部消息封装——最小集，非 EvoMap A2A 全部类型"""
    msg_id: str                         # 幂等键（去重用）
    msg_type: MsgType
    sender: AgentId
    receiver: AgentId | Literal["broadcast"]
    task_id: str
    attempt: AttemptId
    artifact_uri: str | None = None     # 关联产物
    seq: int                            # 事件顺序
    handled: bool = False               # 是否已处理
    provenance: Literal["live", "replay", "mock"] = "live"  # 见 §7
    ts: float
```

**能回答**：谁在什么任务的哪次尝试中，向谁发送了什么，关联了哪个产物，是否已处理。

### 2.4 补齐"真正使用机制"的路径（📝 采纳）

v1 契约缺口 → v2 补全：

| 缺口 | v2 补法 |
|---|---|
| `TopologyEngine.record(src,dst,success)` 无身份、重复反馈 | 改为 `record(attempt: AttemptId, success: bool)`；**以 `msg_id`/`attempt` 去重，重复反馈不重复奖励** |
| `snapshot()` 无人用它选执行者 | 增 `select(targets: list[AgentId]) -> AgentId \| None`（按权重过滤不合格成员），并**证明下一次分配读取了权重** |
| `Metabolism` 无经验选择/解析/注入/采用 | 增 `resolve(ref: GeneRef) -> Gene`（正文解析）、`inject(agent, budget) -> list[Gene]`、`mark_used(gene_id, attempt)` |
| `HubClient.publish(GeneRef, capsule)` 正文不明 | 明确 **GeneRef 只是轻量引用**；发布前须 `resolve()` 出**完整 Gene + Capsule 打包** |
| `TaskResult.success: bool` 语义太粗 | 改 `status: Literal["succeeded","failed","interrupted","pending_review","insufficient_evidence"]`，并绑定**实际验收**字段 `verdict: Verification` |
| `EvolutionEngine.next_generation()` 无反馈闭环 | 增 `evaluate(results: list[TaskResult]) -> None`（候选 ↔ 评估结果绑定），再 `next_generation()` |

```python
# src/contracts/resolution.py（新增）
class Gene(BaseModel):
    """完整 Gene 正文（用于注入与发布）；GeneRef 是其轻量引用"""
    ref: GeneRef
    signals_match: list[str]
    strategy: list[str]                 # 有序步骤
    avoid: list[str]
    verification: list[str]

class Metabolism(Protocol):
    def ingest(self, gene: Gene) -> None: ...
    def resolve(self, ref: GeneRef) -> Gene: ...
    def inject(self, agent: AgentId, budget: int) -> list[Gene]: ...
    def mark_used(self, gene_id: str, attempt: AttemptId) -> None: ...
    def decay_weights(self, now: float) -> None: ...
    def merge_candidates(self) -> list[list[GeneRef]]: ...
    def archive(self) -> list[str]: ...
```

### 2.5 Python 类型检查（📝 采纳）

v1 写"依赖走契约，编译期即可发现漂移"——**Python 不会自动强制执行**。v2 要求：

- 配置 **mypy 或 pyright**（strict 到足以覆盖 `contracts/` 与实现）；
- **具体实现必须进入检查范围**（不能只检查契约文件签名）；
- `tools/contracts_check.py` 扩为：**语义契约测试**（同签名不同语义要能暴露），而非只比签名。

---

## §3 跨语言边界：Python → Node（📝 采纳，**必做决策**）

主系统是 Python，GEP 实现是 Node。**v1 把它留给了 T1 随意决定——这是错误。** v2 固定：

| 角色 | 选定路径 | 调用方式 |
|---|---|---|
| **主路径** | **MCP 客户端**（`@evomap/gep-mcp-server`） | Python MCP client，通过标准协议调用 `gep_recall / gep_evolve / gep_export` |
| **资产哈希/校验** | **gep-sdk**（Node） | Node 子进程，仅做 `canonicalize / computeAssetId / verifyAssetId` |
| **降级路径** | 纯 Python 最小客户端 | 仅实现 `publish`/`fetch`（⚠️ 需自行对齐 schema，**不得**用于声称官方校验通过） |

**必须明确**（不能留给 T1 猜）：启动方式、超时、错误返回、进程退出、凭据管理。
**禁止**主流程同时依赖 SDK + CLI + MCP 却不说明谁调用、何时调用。

---

## §4 经验所有权矩阵（📝 采纳，**新增**）

v1 同时安排了 Evolver 记忆图、本地代谢、SQLite、Chroma、外层进化——**存在多管理者冲突**。v2 明确：

| 问题 | 唯一所有者 |
|---|---|
| **谁拥有经验正文？** | Evolver 记忆图（本地） + Hub（远端）；本地 `Gene` 正文由 `metabolism` 缓存 |
| **谁维护本地使用状态？** | `metabolism`（`mark_used` / 衰减） |
| **谁决定停用？** | `metabolism`（`archive`），**停用须同时清除检索索引**（避免归档后仍被返回） |
| **谁产生候选？** | `evolution`（配置候选）/ `metabolism`（合并候选） |
| **谁最终发布？** | T1 HubClient，**且须通过 §10 发布批准门**（本地要求人工批准时，Evolver 不得按自身阈值自动发布） |

> **一致性约束**：归档/停用必须**原子地**同步记忆图、本地缓存、检索索引三处，否则会出现"已归档仍被检索"。

---

## §5 执行入口：真正干活的节点（📝 采纳，**T2 首个交付重定义**）

v1 的 T2 首交付是"LangGraph 骨架"——**但框架只决定调用顺序，不提供真正干活的节点**。

**v2 规定 T2 首个交付**：

> **通过选定执行入口，完成一个小任务，返回真实产物与执行记录。**

执行入口三选一，**必须固定**：① 模型 API（自定义 loop）② 现有 CLI（如 evolver / agent host）③ 既有执行宿主。
并定义：工作区、工具调用、模型超时、成本采集。

### 5.1 ⚠️ 需你确认：架构边界

若本项目**基于既有工程**（评审提到"ORCA 派生工程"）二次开发，本版**无法自行确认该关系**。请确认：

- Morphogenesis 是**独立原型**，还是接到某个既有工程的二开？
- 若是二开：复用其哪些执行宿主/工具层？本方案的 `swarm/` 与它的边界在哪？

**在确认前，各轨不得臆测上游结构**；本方案按**独立原型**编写，接入上游前先补一份《架构边界说明》。

---

## §6 外层进化 v2（📝 采纳：修 bug + 移出主链）

### 6.1 修正角色编码丢总数（📝 明确错误）

v1：`counts = counts / sum(counts)` → 配置 A（5 人）与配置 B（10 人）编码相同 `[0.2,0.4,0.2,0.2]`，**无法还原人数**。

```python
# v2：保留总人数 + 受约束整数计数编码
def encode(cfg: SwarmConfig) -> np.ndarray:
    total = sum(cfg.role_counts.values())          # 保留总人数
    counts = np.array([cfg.role_counts[r] for r in ROLES], dtype=float)
    return np.concatenate([
        one_hot(cfg.topology, TOPOS),
        counts,                                     # 原始整数计数（非归一）
        [total / MAX_SWARM],                        # 总量维度
        [cfg.gene_budget / 10],
    ])
```

### 6.2 审批移出自由染色体（📝 明确回退修正）

v1 把 `approval` 放进 one-hot 编码 → **违反 v2 设计方案"不可豁免审批不能被优化解除"**。

> v2：`approval` **不作为自由变异维度**；仅在用户授权 + 平台允许范围内可调，**解码后强制约束检查**。
> 权限上限、必要验收、安全检查属**可行性约束**，不由适应度解除。

### 6.3 能力与命名对齐（📝 采纳）

v1 染色体只编码**拓扑/角色比/审批/数量**，**不含 Gene 内容或引用** → 按此实现只是**优化蜂群配置参数**，**不能宣称完成"经验策略的变异与遗传"**。

> v2 两种都可以做，但**名称与能力必须对齐**：若只做配置参数优化，就叫"配置进化"，不叫"策略遗传"。

### 6.4 "20×3" 不是轻量验收 + 降级逻辑修正（📝 明确错误）

- "20 个体 × 3 代" = **60 个候选评估槽位**；若每槽跑真蜂群，成本 = 60 次真实调用。
- **"EvoX 太慢 → 换轻量 GA"是错的**：换优化器**不会减少评估候选所需的真实运行**。若耗时来自模型调用，换优化器通常无效。代理评估可用于筛选/演示接口，**但其分数不能充当实际任务结果。**

> **v2 决策**：**T4 保留为可选扩展，不进入首个真实闭环的关键路径。**

---

## §7 mock 与真实验收隔离（📝 采纳，**关键铁律**）

v1 同时写"只展示真实模块"和"卡住就切 mock 拼故事"——**没有规定模拟数据如何与真实结果隔离**。v2 三条硬规则：

**① 运行来源必须标记。** 事件与结果携带 `provenance: live | replay | mock`；`replay` 须指向原始运行记录。

**② 验收状态必须分开记录。** 三个独立状态，**不共用绿色标志**：
- `contract_local`：本地契约通过
- `interface_live`：真实接口通过
- `task_live`：真实任务通过

**③ 测试夹具不得冒充实际经验发布。**
- **Hub 沙箱无官方地址/凭据前，只能使用本地隔离 stub**；**禁止转向生产平台发布虚构结果**。
- Hub 不可用时，产品显示**"待发布"**并保留本地产物——**比伪装成已发布更稳、更好解释**。

> **修正 v1 的 T1 验收**："对假 Gene 跑完 hello→publish→fetch"**只能证明调用方与假实现配合正常**，**不能证明**官方 schema 通过、认证有效、发布被接收、资产可检索。T1 真实验收必须是 `interface_live`。

---

## §8 多轨并行 v2（📝 采纳：调整顺序与所有权）

### 8.1 启动条件调整

v1："T3 最容易，所以最先完成"——**公式可早跑，但它依赖的真实语义（什么算成功、何时更新、权重如何影响分配）未定，单跑绿公式不能证明系统用上了它。**

| 轨道 | v2 先交付什么 |
|---|---|
| **T0** | 统一契约 + **依赖锁** + **一个固定样例任务** + **启动入口** |
| **T1** | 选定 Python→Node 接入方式；完成**真实资产校验**与受控接口联调 |
| **T2** | **一个真实执行者跑通任务**，再串入**独立复核** |
| **T3** | 按**已定义的真实结果**更新权重，并**证明下一次分配读取了权重** |
| **T5** | **尽早接入第一条真实事件**；mock 只补齐未完成场景 |
| **T4** | 主闭环稳定后，再接候选生成与有限评估（可选） |

### 8.2 并行冲突修正

- **共享 mock 唯一所有者**：T2/T4 都写 `mocks/topology.py` → 改为由 **T3（提供方）**维护唯一实现，他人只读。
- **目录命名统一**：`orchestrator` → **统一为 `orchestration/`**（v1 跨节不一致，会让生成代码的 Agent 造出两套目录）。
- **独立工作区**：各 Agent 用**独立 git worktree + 临时目录 + 独立测试数据库**，避免代码分开但运行数据互相覆盖。
- **跨节引用编号**统一校对。

---

## §9 依赖与环境 v2（📝 采纳，含明确技术修正）

### 9.1 锁文件（📝 采纳）

v1 大量 `"*"` 且未要求提交锁文件。**v2**：由 **T0 统一生成、提交、维护 `poetry.lock` / `package-lock.json`**；其他轨**不独立更新依赖**。

### 9.2 版本事实修正（✅ 已核实）

- **SCHEMA 版本**：v1 写"当前 1.7.0"**过时**（核查时 npm gep-sdk 已 1.13.0，源码快照 1.14.0）。**v2：不写死版本号，以实际安装并锁定的版本为准**；schema 版本会漂移，须从 `package-lock` 读取。
- **Node 版本**：gep-sdk 声明 ≥18；**Evolver 官方要求 ≥18（推荐 ≥22.12）**；若用 Evolver，整套环境不能只要求 Node 18。**v2：以 Evolver 的 engine 字段为准（≥18，推荐 22.12+）。**
- **Evolver 必须在 git 仓库内运行**（否则报错退出）。

### 9.3 LangGraph 用法修正（📝 明确错误）

v1 `SqliteSaver.from_conn_string("checkpoints.db")` **是上下文管理器**，不能直接当 checkpointer 传入：

```python
# v2 正确用法
from langgraph.checkpoint.sqlite import SqliteSaver
with SqliteSaver.from_conn_string("checkpoints.db") as saver:
    app = g.compile(checkpointer=saver)
    app.invoke(..., config={"configurable": {"thread_id": "t1"}})
```

**并补齐依赖**：`langgraph-checkpoint-sqlite`（v1 漏了）；异步执行需用相应**异步 saver**。

> **重要边界**：**checkpoint 保存的是线程范围的图状态**，**不自动**保存外部工作目录、结束旧进程、防止工具动作重复执行。**"开启 checkpoint"是恢复的基础，不能直接作为恢复功能的验收结果。**

### 9.4 httpx 重试（📝 采纳）

v1"不要手写重试"方向保留，但 **httpx 传输层重试主要覆盖连接错误/连接超时**；读取错误、服务端状态码需另配策略。**v2 必须定义**：哪些操作可重试、最多几次、**发布超时后如何确认是否已提交成功**。

---

## §10 运行规格（📝 采纳，**v1 缺失**）

v1 唯一的"预算"是 `gene_budget`（限制携带经验数），**不限制整轮模型费用/执行次数/自动重试**，循环数据流也**无停止条件**。v2 补齐（属**运行规格**，非开发者默认行为）：

| 项 | 要求 |
|---|---|
| **总预算** | 总 Token / 总费用上限，超限即停 |
| **最大重试** | 每 `AttemptId` 的重试上限 |
| **停止条件** | 达成/预算耗尽/无进展 N 轮/手动停止 |
| **文件权限** | 可写目录白名单、禁止越界写 |
| **发布批准** | 发布前的人工/自动批准门（见 §4） |

---

## §11 验收标准 v2（📝 采纳：能力检查替代覆盖率）

v1 的"70% 单元测试覆盖率"**不必成为黑客松主要目标**。v2 改为**少量验证承诺的能力检查**：

- [ ] **权重真的影响调用**：改权重后下一次 `select()` 结果随之改变
- [ ] **重复结果不重复奖励**：同一 `msg_id`/`attempt` 重复上报，权重只更新一次
- [ ] **接续不重复副作用**：恢复后无重复文件写入/重复工具调用
- [ ] **经验真的被使用**：`inject` 后的 Gene 在运行中留有 `mark_used` 记录
- [ ] **模拟结果不冒充实测**：`provenance=mock` 的结果不会进入 `task_live` 验收
- [ ] **三态验收分离**：`contract_local / interface_live / task_live` 各自独立

> 单有覆盖率和一个 `TaskResult(success=True)`，不足以证明以上能力。

---

## §12 开工前六项补充（📝 采纳：最小完成标准）

| # | 补充项 | 最小完成标准 |
|---|---|---|
| 1 | **执行入口** | 一个明确模型/CLI/宿主入口，能完成固定任务并生成真实产物 |
| 2 | **身份与事件** | 区分运行/任务/成员/执行尝试；事件能去重、可追溯 |
| 3 | **机制闭环** | 权重影响真实选路；经验有正文解析、注入、采用记录 |
| 4 | **兼容环境** | 修正 saver 用法、补齐依赖、提交锁文件、验证 Python→Node 边界 |
| 5 | **受控运行** | 配置总预算、最大重试、停止条件、文件权限、发布批准 |
| 6 | **真实验收** | 正常交付、一次接续、一次经验复用，**均不允许 mock 替代通过** |

---

## §13 里程碑门禁 v2（调整）

| 门禁 | v1 | v2 调整 |
|---|---|---|
| G1 契约冻结 | T+2h 冻结 | **改为"调用方+实现方跑通一次"** |
| G3 T3 全绿 | 公式单测 | **增：证明权重影响真实选路** |
| G4 端到端 | 发布 1 资产（可 stub） | **拆为 `interface_live` + `task_live`** |
| T4 接入 | 主链必做 | **移出关键路径，可选** |
| T5 | 最后接真实 | **尽早接第一条真实事件** |
| 新增 G0 | — | **六项开工前补充完成** |

---

## 附录 A：v1 → v2 修订对照

| # | 位置 | 修订 | 证据级 |
|---|---|---|---|
| 1 | §2.1 | T+2h 冻结 → **跑通即冻结** | 📝 |
| 2 | §2.2 | Role → **Role + AgentId + AttemptId** | 📝 |
| 3 | §2.3 | 三枚举 → **Envelope（含 msg_id/任务/尝试/产物/provenance/seq）** | ✅ 呼应 7 字段封装 |
| 4 | §2.4 | 补齐 resolve/inject/select/mark_used/status/feedback 闭环 | 📝 |
| 5 | §2.5 | "编译期发现漂移" → **实配 mypy/pyright + 语义契约测试** | 📝 |
| 6 | §3 | SDK 不含算法 → **固定 MCP 主路径 + 子进程哈希 + 降级** | ✅ 官方原文 |
| 7 | §4 | 新增**经验所有权矩阵** | 📝 |
| 8 | §5 | T2 首交付 → **真实任务+真实产物**；增架构边界待确认 | 📝/⚠️ |
| 9 | §6.1 | **修角色编码丢总人数** | 📝 明确错误 |
| 10 | §6.2 | **审批移出自由染色体** | 📝 回退修正 |
| 11 | §6.3 | "经验遗传" → 名称与能力对齐 | 📝 |
| 12 | §6.4 | **"换轻量 GA"降级逻辑错误** → T4 移出主链 | 📝 明确错误 |
| 13 | §7 | mock 与验收隔离（provenance + 三态 + 禁止夹具冒充发布） | 📝 |
| 14 | §8 | 启动条件调整；共享 mock 唯一所有者；目录命名统一；worktree 隔离 | 📝 |
| 15 | §9.1 | 提交并维护锁文件，T0 独占 | 📝 |
| 16 | §9.2 | schema 1.7.0 → **不写死，以锁定版本为准**；Node 以 Evolver engine 为准 | ✅ |
| 17 | §9.3 | **修 SqliteSaver 上下文管理器用法** + 补 `langgraph-checkpoint-sqlite` | 📝 明确错误 |
| 18 | §9.4 | httpx 重试需**定义策略** | ✅ 传输层范围 |
| 19 | §10 | **新增运行规格**（预算/重试/停止/权限/批准） | 📝 |
| 20 | §11 | 覆盖率目标 → **能力检查** | 📝 |

> **保留不变**：复用优先、模块责任划分、契约集中管理、mock 解锁并行。**这些方向是对的，v2 不推翻。**

---

## 附录 B：一页速查

```
不冻结契约 —— 以"调用方+实现方跑通一次"为冻结条件
身份三层   —— Role(职责) / AgentId(成员) / AttemptId(尝试)
消息成封装 —— 非裸枚举：msg_id + task + attempt + artifact + seq + provenance
SDK 无算法 —— gep-sdk 只给 schema/hash；选择/记忆图在 evolver/mcp-server
跨语言先定 —— MCP 主路径 + 子进程哈希 + Python 降级
mock 不验收 —— provenance 标记 + 三态分离 + 禁止夹具冒充发布
T4 出主链 —— 外层进化可选；"换优化器"不减评估成本
修两个 bug —— 角色编码保留总数；SqliteSaver 用 with 上下文
先补六项  —— 执行入口/身份事件/机制闭环/兼容环境/受控运行/真实验收
```

> **一句话**：v1 的方向对，但**最弱处恰是"冻结契约"**。v2 先补身份、事件、执行入口、跨语言边界，把 T4 移出主链，再让各轨并行——**不是降低技术含量，而是让每个模块真的能接到同一个真实系统里。**
