> ⚠️ **本文件已归档（DEPRECATED）**：含已被《开发文档 v2》判定的错误（如 T+2h 冻结契约、`orchestrator/` 目录名、角色编码丢总人数、`SqliteSaver.from_conn_string()` 直接传入、gep-sdk 封装 publish 等）。**请勿据此开工**，一律以《开发文档 v2》《AI 原生多 Agent 多轨开发说明》《统一对齐与矛盾消解说明》为准。

# Morphogenesis 开发文档 v1

> 项目：会自我代谢与进化的去中心化蜂群（赛道4 · 多 Agent 分群协作）
> 定位：**实现规格 + 多轨并行开发手册**。前半是"造什么、复用什么"，后半是"怎么用多个 Agent 分轨并行、不打架"。
> 阅读顺序：`§0 复用原则` → `§4 接口契约` → `§5 分轨方案` 是必读；`§6 实现要点` 供各轨 owner 按需查。

---

## §0 复用优先原则（不造轮子）

### 0.1 三条硬规则

1. **官方优先**：EvoMap 官方 SDK / CLI / MCP 已实现的，**一律复用**，不自行实现 GEP 资产、记忆图、Hub 发布、签名校验。
2. **成熟库优先**：编排、持久化、向量检索、可视化等通用能力，优先用成熟开源库，自研只写"胶水"和"独有算法"。
3. **自研仅限差异化**：只有**本项目独有的机制**才自研——黏菌式管道权重更新、信息素-基因耦合、代谢半衰期的本地策略、外层目标函数。

> **反例警戒**：不要手写 HTTP 重试、JSON 校验、任务队列、向量索引、图表渲染。这些全部有库。

### 0.2 复用决策矩阵（核心表）

| 模块 | 决策 | 复用对象 | 来源 / 安装 | 备注 |
|---|---|---|---|---|
| **GEP 资产模型**（Gene/Capsule/EvolutionEvent） | **复用** | `@evomap/gep-sdk` | npm（Windows/.NET 无关，Node ≥18） | 含 `canonicalize` + `computeAssetId`；schema 当前 1.7.0，向前兼容 |
| **进化循环 / 记忆图 / solidify** | **复用** | `@evomap/evolver`（CLI） | `npm i -g @evomap/evolver` | 已有 7 阶段循环 + 自动发布阈值 + 本地记忆图 |
| **Agent 侧 GEP 工具** | **复用** | `@evomap/gep-mcp-server` | MCP | 提供 `gep_recall` / `gep_evolve` / `gep_export` / `gep_search_community` |
| **Hub 发布 / 拉取 / 鉴权** | **复用** | A2A HTTP API | `https://evomap.ai/a2a/*` | `hello`/`publish`/`fetch`/`heartbeat` 等，见 §4.4 |
| **多 Agent 编排与状态机** | **复用** | **LangGraph** | `pip install langgraph` | 关键：**自带 checkpointing**，正好满足故障恢复需求 |
| **外层进化算法** | **复用** | **EvoX** | `pip install "evox[default]"` | PyTorch 后端，50+ EA；需把染色体编码为张量，见 §6.3 |
| **本地经验向量检索** | **复用** | Chroma 或 FAISS | `pip install chromadb` | 记忆图近邻查询，避免自写索引 |
| **持久化** | **复用** | SQLite（+ SQLModel） | 标准库 / `pip install sqlmodel` | 运行记录、管道权重、Gene 元数据 |
| **数据校验 / 序列化** | **复用** | Pydantic | `pip install pydantic` | 契约模型即 pydantic model |
| **可视化图表** | **复用** | ECharts / D3（前端） | CDN | 进化树 + 消息流 |
| **实时推送** | **复用** | FastAPI + WebSocket | `pip install fastapi uvicorn` | 演示台实时刷新 |
| **信息素调度** | **参考** | `stigmergy-scheduler` | `pip install stigmergy-scheduler` | 只借鉴"信息素场"组织方式；本项目做结构化语义版 |

> **许可提示**：EvoMap 相关包请以仓库 `LICENSE` 为准（部分为 GPL 系）；黑客松本地使用无碍，若要再分发需确认。

### 0.3 自研边界（唯一允许手写的算法）

- `topology/` ：管道权重更新 `D ← (1−λ)·D + α·Q·s`、阈值裁剪、新边生成规则
- `metabolism/` ：经验半衰期衰减、合并候选生成与校验、归档停用
- `evolution/` ：染色体 ↔ 蜂群配置的编解码、外层适应度 `完成度 × √新颖度 ÷ Token`
- `swarm/` ：信息素-基因耦合的消息路由策略（在 LangGraph 之上）

---

## §1 系统架构

### 1.1 分层

```
apps/demo        演示台（FastAPI + WebSocket + 前端双视图）
     │
src/orchestrator 编排层：LangGraph 图 + 检查点（复用）
     │
src/swarm        蜂群运行时：角色 Agent、消息最小集(intent/result/signal)、信息素路由（自研）
src/topology     黏菌管道引擎：权重更新 / 裁剪 / 新边（自研）
src/metabolism   代谢引擎：半衰期衰减 / 合并候选 / 归档（自研）
src/evolution    外层进化：染色体编解码 + EvoX 适配（半自研/半复用）
src/genome       GEP 资产适配层：封装 EvoMap SDK（复用为主）
src/hub          Hub/A2A 客户端：封装 publish/fetch/hello（复用）
src/contracts    冻结接口契约（pydantic models + Protocol）
```

### 1.2 运行时数据流

```
任务输入
  → orchestrator 建图
  → swarm 按当前拓扑分派 planner/builder/reviewer/aggregator
  → topology 记录每条链路的 (Q 流量, s 成功率) → 更新 D
  → metabolism 消费执行结果 → 衰减/合并/归档 Gene
  → genome 把成功经验 solidify 为 Gene+Capsule
  → hub 打包发布（candidate → promoted）
  → evolution 用本轮指标更新适应度 → 产生下一代配置
  → 回流 orchestrator（循环）
```

循环体对 `topology`、`metabolism`、`evolution` 的调用一律走 `contracts/` 中的 Protocol，**禁止跨轨直接 import 实现**。

---

## §2 工程结构

```
morphogenesis/
├─ pyproject.toml            # 依赖锁定（见 §10）
├─ Makefile                  # make dev / test / demo
├─ src/
│  ├─ contracts/             # ★ 冻结目录，仅 T0 可改
│  │  ├─ models.py           # pydantic: SwarmConfig, GeneRef, PipeState, ...
│  │  ├─ protocols.py        # 各模块接口 Protocol
│  │  └─ events.py           # 消息/事件枚举
│  ├─ genome/                # T1
│  ├─ hub/                   # T1（与 genome 同轨，共用 SDK）
│  ├─ swarm/                 # T2
│  ├─ orchestration/         # T2（LangGraph 图）
│  ├─ topology/              # T3
│  ├─ metabolism/            # T3
│  ├─ evolution/             # T4
│  └─ viz/                   # T5（数据接口）
├─ apps/demo/                # T5（FastAPI + 前端）
├─ tests/
│  ├─ unit/                  # 每轨自测
│  └─ integration/           # T0 维护的集成测试
├─ mocks/                    # ★ 每轨的 stub 实现，供他人并行开发
└─ tools/
   └─ contracts_check.py     # 契约漂移检查（CI 用）
```

> **不变量**：`src/contracts/` 是唯一的跨轨依赖；`mocks/` 是可运行的假实现，任何轨在依赖未就绪时都靠它跑通。

---

## §3 接口契约（并行开发前提 · 冻结）

> 契约在 **T+2h 冻结**。之后任何修改走 T0 评审的 PR。**契约先行是分轨开发唯一不翻车的保证。**

### 3.1 数据模型（`src/contracts/models.py`）

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional

Role = Literal["planner", "builder", "reviewer", "aggregator"]

class GeneRef(BaseModel):
    gene_id: str                      # EvoMap asset_id (sha256:...)
    signals: list[str]                # 触发信号
    summary: str
    confidence: float = Field(ge=0, le=1)
    created_ts: float
    last_used_ts: Optional[float] = None
    last_verified_ts: Optional[float] = None

class PipeState(BaseModel):
    """一条协作链路（有向边）的状态"""
    src: Role
    dst: Role
    weight: float = 0.0               # D
    flow: float = 0.0                 # Q（累计/窗口）
    success_rate: float = 0.5         # s
    active: bool = True

class SwarmConfig(BaseModel):
    """外层染色体解码后的蜂群配置"""
    topology: Literal["hierarchical", "flat", "ring"] = "hierarchical"
    role_counts: dict[Role, int]
    approval: Literal["paranoid", "supervised", "autonomous"] = "supervised"
    gene_budget: int = 3              # 每角色携带的 Gene 数

class TaskResult(BaseModel):
    task_id: str
    success: bool
    tokens: int
    novelty: float = 0.0
    latency_ms: int = 0
    artifact_uri: Optional[str] = None

class FitnessScore(BaseModel):
    task_id: str
    input: float                      # 完成度
    novelty: float
    tokens: int
    value: float                      # 本项目拟定目标函数输出
```

### 3.2 模块接口（`src/contracts/protocols.py`）

```python
from typing import Protocol, Iterable
from .models import *

class TopologyEngine(Protocol):
    def record(self, src: Role, dst: Role, success: bool) -> None: ...
    def decay(self, rounds: int = 1) -> None: ...
    def prune(self) -> list[tuple[Role, Role]]: ...      # 返回被删除的边
    def spawn_candidates(self) -> None: ...               # 新边候选生成
    def snapshot(self) -> list[PipeState]: ...

class Metabolism(Protocol):
    def ingest(self, gene: GeneRef) -> None: ...
    def decay_weights(self, now: float) -> None: ...       # w = w0 * 2^(-t/h)
    def merge_candidates(self) -> list[list[GeneRef]]: ... # 候选组，需校验
    def archive(self) -> list[str]: ...                    # 返回归档 gene_id

class EvolutionEngine(Protocol):
    def decode(self, genome: "Genome") -> SwarmConfig: ...
    def encode(self, cfg: SwarmConfig) -> "Genome": ...
    def score(self, r: TaskResult) -> FitnessScore: ...
    def next_generation(self) -> list[SwarmConfig]: ...

class HubClient(Protocol):
    def hello(self) -> dict: ...
    def publish(self, gene: GeneRef, capsule: dict) -> dict: ...
    def fetch(self, query: str, limit: int = 10) -> list[GeneRef]: ...
```

### 3.3 消息事件（`src/contracts/events.py`）

```python
from enum import Enum

class MsgType(str, Enum):
    INTENT = "intent"      # 声明意图（默认最小集）
    RESULT = "result"      # 返回结果
    SIGNAL = "signal"      # 广播信号（信息素）

# 注意：这是本项目首版最小集，非 EvoMap A2A 全部消息类型。
```

---

## §4 多 Agent 分轨开发方案

### 4.1 分轨原则

1. **一轨一目录**：每个开发 Agent 只写自己的 `src/<track>/` 与对应 `mocks/`，**绝不越界改他人目录**。
2. **依赖走契约**：轨间只能通过 `contracts/` 交互，编译期即可发现漂移。
3. **契约先冻**：T+2h 前完成契约，之后各轨并行。
4. **桩先行**：每轨先提交"能跑的假实现"到 `mocks/`，解锁下游并行。
5. **集成不等人**：T0 用 mocks 随时能跑通全链路。

### 4.2 轨道划分与依赖图

```
            ┌─────────────────────────────┐
            │ T0 集成/契约（人 or 主 Agent）│
            │ contracts/ · CI · 集成测试    │
            └──────────────┬──────────────┘
                           │ 冻结契约
   ┌───────────┬───────────┼───────────┬───────────┐
   ▼           ▼           ▼           ▼           ▼
 [T1 资产]  [T2 编排]   [T3 引擎]   [T4 进化]   [T5 演示]
 genome/    swarm/      topology/   evolution/  viz/
 hub/       orchestration metabolism/            apps/demo
   │           │           │           │           │
   └───────────┴─────┬─────┴───────────┴───────────┘
                     ▼
              [T6 集成验收] ← 汇入 T0
```

**依赖关系**：

| 轨道 | 依赖（接口） | 被谁依赖 | 阻塞风险 |
|---|---|---|---|
| T1 资产/Hub | contracts（无内部依赖） | T2/T3/T4 | 低 |
| T2 编排/蜂群 | contracts + T1 的 `HubClient`（用 mock） | T5 | 中 |
| T3 引擎 | contracts（纯算法，无外部依赖） | T2/T4 | **最低，最先可完成** |
| T4 进化 | contracts + T3 `TopologyEngine`（用 mock） | — | 中（EvoX 编码） |
| T5 演示 | T2 输出 + contracts（全部用 mock） | — | 低 |

> **关键洞察**：T3 是纯算法、零外部依赖，**应最先开工并最先完成**，为 T2/T4 提供可替换的真实实现。T5 全程用 mock 开发，最后才接真实数据。

### 4.3 任务卡（每轨交付物）

**T1 · 资产与 Hub（reuse 为主）**
- 交付：`genome/` 封装 `@evomap/gep-sdk`；`hub/` 封装 A2A `hello/publish/fetch`
- 关键点：publish 必须 **Gene+Capsule 打包**；处理 `candidate → promoted`；记录"发布/可发现/被获取/复用"四态
- mock：`mocks/hub.py` 返回假 asset_id
- 验收：能对一个假 Gene 走完 `hello → publish → fetch`（可打 EvoMap 沙箱或本地 stub）

**T2 · 编排与蜂群**
- 交付：LangGraph 图（planner→builder×N→reviewer→aggregator）；`MsgType` 最小集；信息素路由钩子
- 关键点：**开启 LangGraph checkpoint**（故障恢复用）；每角色只携带 `gene_budget` 条紧凑 Gene
- mock：`mocks/topology.py` 返回固定拓扑
- 验收：用 mock 拓扑跑通一个端到端任务，输出 `TaskResult`

**T3 · 拓扑与代谢引擎（自研核心）**
- 交付：管道权重更新、阈值裁剪、新边候选；半衰期衰减、合并候选、归档
- 关键点（必须实现的三条限制处理）：
  1. 恒定输入收敛到 `αr/λ`，**不等于最优拓扑** → 显式记录并断言
  2. 闲置边**不会自动归零** → 必须阈值 + 连续低活跃窗口 + 保留条件
  3. **更新已有边不生成新边** → 单独实现 `spawn_candidates()`
- 半衰期公式用 **`w(t)=w₀·2^(−t/h)`**（h 为半衰期；勿把时间常数 τ 当半衰期）
- mock：无需 mock（纯函数，直接单测）
- 验收：单元测试覆盖三条限制 + 衰减/裁剪/合并边界

**T4 · 外层进化**
- 交付：`SwarmConfig ↔ Genome` 编解码；`FitnessScore`；EvoX 适配
- 关键点：染色体是结构化配置，需**编码为定长张量**才能喂 EvoX（见 §6.3）；若编码成本过高，降级为轻量 GA
- mock：`mocks/topology.py`
- 验收：小种群（20×3 代）能产出适应度序列

**T5 · 演示台**
- 交付：FastAPI + WebSocket；进化树视图 + 消息流视图
- 关键点：图表区分**当前值/均值/历史最佳**，**不预设单调上升**
- mock：`mocks/swarm_stream.py` 造模拟事件流
- 验收：用 mock 数据把两个视图跑起来，帧率稳定

### 4.4 边界纪律（避免合并冲突）

| 规则 | 说明 |
|---|---|
| 目录独占 | 一轨只碰 `src/<own>/` + `mocks/<own>` + `tests/unit/<own>` |
| 契约只读 | 任何人改 `contracts/` 必须提 PR 给 T0，评审后合并 |
| 不改他人测试 | 集成测试归 T0 |
| 接口不臆造 | 需要新接口 → 提给 T0，不自行在本地加字段 |
| 提交粒度 | 每轨每 30–45 分钟一提交，消息格式 `[T3] topology: prune 阈值可配` |

### 4.5 集成点与时间线

| 时点 | 事件 | 门禁 |
|---|---|---|
| T+0h | 各轨读契约，提交 mocks 骨架 | 全链路用 mock 跑通一次 |
| T+2h | **契约冻结** | T0 确认 contracts 不再改 |
| T+6h | T3 真实实现替换 mock（first integration） | topology+metabolism 单测全绿 |
| T+12h | T2 接 T3 真实实现；T1 打通 Hub 沙箱 | 端到端任务成功一次 |
| T+20h | T4 接入；T5 接真实事件流 | 适应度曲线有真实数据 |
| T+30h | 代码冻结前合流；T6 验收 | 集成测试全绿 |
| T+36h | 演示彩排 | 5 分钟脚本跑通 |

### 4.6 Git 工作流

- 主干 `main` 保护；各轨 `feat/t1`…`feat/t5`
- 短生命周期分支，**每 4h 从 main rebase**（避免长分支）
- `contracts/` 改动 → 单独 PR + T0 review + 全员通知
- 合并顺序：T3 → T1 → T2 → T4 → T5（依赖自下而上）
- CI 跑 `tools/contracts_check.py`（检测是否有人改了契约签名）

---

## §5 关键实现要点（复用映射）

### 5.1 GEP 资产层 → 复用 EvoMap SDK（不要手写）

- 用 `@evomap/gep-sdk` 的 `canonicalize` + `computeAssetId` 生成 `asset_id`，**不要自己实现哈希规范化**。
- schema 版本以 **1.7.0** 为基准（`SCHEMA_VERSION` 常量），向前兼容。
- **合规发布至少包含 Gene + Capsule**（社区所称 "triple" 指 Gene + Capsule + EvolutionEvent；Skill 为可选第四类）。
- 复用 Evolver 的 7 阶段循环与自动发布阈值逻辑，**不要重造 solidify**。

### 5.2 编排 → 复用 LangGraph

选 LangGraph 而非 CrewAI/AutoGen 的理由：
- 有 **checkpointing**（本项目故障恢复必需，见设计文档 §8）
- 显式状态机，**可审计**（评审要看流程）
- 支持条件边 → 正好表达"信息素路由"
- CrewAI 偏固定角色（与本项目动态拓扑冲突）；AutoGen 会话式（Token 开销高）

```python
# 骨架示意（T2 负责）
from langgraph.graph import StateGraph
from langgraph.checkpoint.sqlite import SqliteSaver

g = StateGraph(SwarmState)
g.add_node("planner", planner_node)
g.add_node("builder", builder_node)
g.add_node("reviewer", reviewer_node)
g.add_node("aggregator", aggregator_node)
g.add_conditional_edges("planner", route_by_pheromone)  # 信息素路由钩子
app = g.compile(checkpointer=SqliteSaver.from_conn_string("checkpoints.db"))
```

### 5.3 外层进化 → 复用 EvoX

EvoX 是数值优化框架，**染色体要先编码为定长张量**：

```python
# 编码示意：topology(3) + role_counts(4归一) + approval(3) + gene_budget(1)
def encode(cfg: SwarmConfig) -> np.ndarray:
    topo = one_hot(cfg.topology, ["hierarchical","flat","ring"])
    counts = np.array([cfg.role_counts[r] for r in ROLES], dtype=float) / max(1, sum(cfg.role_counts.values()))
    appr = one_hot(cfg.approval, ["paranoid","supervised","autonomous"])
    return np.concatenate([topo, counts, appr, [cfg.gene_budget/10]])
```

- 用 EvoX 的 GA/DE 算子跑选择-变异-交叉；**适应度回调** = 跑一轮真蜂群或代理评估。
- **风险**：若"编码-运行-解码"闭环太慢（每代要真跑蜂群），降级为**轻量 GA**（自写 30 行）或用代理模型。T4 需在 T+8h 前给出可行性判断。

### 5.4 信息素 → 参考 stigmergy-scheduler

- 只借鉴其"信息素场"**组织思想**，不直接依赖（其抽象是标量场）。
- 本项目的信息素 = **结构化语义对象**（迷你 Gene + 权重），挂在 `topology` 的边上。

---

## §6 里程碑（48h）

| 时段 | 交付 | owner |
|---|---|---|
| H0–2 | 契约冻结 + mocks 骨架 + CI 跑通 | T0 + 全员 |
| H2–8 | T3 算法实现并全绿；T1 SDK 封装；T2 LangGraph 骨架；T5 静态视图 | T1/T2/T3/T5 |
| H8–16 | T3 替换 mock 集成；T2 接真实拓扑；T1 打通 Hub 沙箱 | T1/T2/T3 |
| H16–26 | T4 接入真实适应度；T5 接真实事件流；T6 首轮集成 | T4/T5/T6 |
| H26–34 | 联调、性能、可视化抛光 | 全员 |
| H34–40 | 代码冻结 + 端到端验收 + 演示彩排 | T0/T6 |

> 时间线按"**先纵向打通最窄闭环，再横向加宽**"设计；任何时刻 main 上都有一条能跑的链路。

---

## §7 测试与验收

| 层级 | 范围 | 工具 | 通过条件 |
|---|---|---|---|
| 单元 | 每轨自身 | pytest | 覆盖率 ≥ 70%；T3 必测三条数学限制 |
| 契约 | `contracts/` 一致性 | `contracts_check.py` | 无未评审签名变更 |
| 集成 | 端到端任务 | pytest + mock/真实 | 一个任务成功产出 `TaskResult` + 发布 1 个资产 |
| 演示冒烟 | 5 分钟脚本 | 手动 | 双视图稳定刷新，无崩溃 |

**T3 专项测试（必过）**：
1. 恒定 `r` 下 `D_t → αr/λ`（断言收敛值）
2. `r=0` 时 `D_t=(1−λ)^t·D₀ > 0`，必须显式 `prune` 才删除
3. `spawn_candidates()` 能产生新边（证明拓扑可生长）
4. 半衰期：`t=h` 时 `w ≈ 0.5·w₀`

---

## §8 风险与降级预案

| 风险 | 触发信号 | 降级方案 |
|---|---|---|
| EvoMap 沙箱不可达 | Hub 调用超时 | 全量走 `mocks/hub.py`，本地记录，演示用录播资产 |
| EvoX 编码闭环太慢 | 每代 > 30s | 降级轻量 GA 或代理评估 |
| LangGraph 版本坑 | 安装/API 冲突 | 降级为自写 asyncio 状态机（保留 checkpoint 用 SQLite） |
| 某轨阻塞 | 该轨未按时交付 | 用其 mock 继续，演示只展示已就绪的真实模块 |
| 合并冲突 | `contracts/` 被多轨改 | T0 强制串行评审 + CI 拦截 |
| Node/npm 缺失（EvoMap SDK） | T1 装不上 | 用 Python 复刻最小 publish 客户端（仅 `publish`/`fetch`） |

> **降级原则**：**演示必须稳定**。任何模块卡住，立刻切 mock，用"已就绪的真实模块 + 其余 mock"拼出一个能跑的故事，绝不把崩溃当演示。

---

## §9 依赖清单（锁版本）

```toml
# pyproject.toml（示意）
[tool.poetry.dependencies]
python = "^3.11"
langgraph = "*"            # 编排 + checkpoint
pydantic = "^2"
fastapi = "*"
uvicorn = "*"
sqlmodel = "*"             # SQLite ORM
chromadb = "*"             # 向量检索（可选）
numpy = "*"
httpx = "*"                # 调 A2A
evox = {extras = ["default"]}   # 外层进化
# stigmergy-scheduler = "*"     # 仅参考，非硬依赖
```

```jsonc
// package.json（EvoMap 侧）
{
  "dependencies": {
    "@evomap/gep-sdk": "*",
    "@evomap/gep-mcp-server": "*"
  },
  "devDependencies": { "@evomap/evolver": "*" }
}
```

**外部服务**：EvoMap A2A `https://evomap.ai/a2a/*`（需 `node_secret`，经 `POST /a2a/hello` 获取）。
**运行环境**：Node ≥ 18（SDK）；Python 3.11+。

---

## §10 复用 Checklist（开工前逐条确认）

- [ ] 没有手写 SHA-256 规范化 → 用 `gep-sdk.computeAssetId`
- [ ] 没有手写 solidify/发布阈值 → 用 Evolver
- [ ] 没有手写状态机/检查点 → 用 LangGraph
- [ ] 没有手写 GA/DE 算子 → 用 EvoX（或确认降级）
- [ ] 没有手写向量索引 → 用 Chroma/FAISS
- [ ] 没有手写 HTTP 重试/JSON 校验 → 用 httpx + pydantic
- [ ] 没有手写图表渲染 → 用 ECharts/D3
- [ ] 自研代码仅存在于 `topology/`、`metabolism/`、`evolution/`、`swarm/` 四处

---

## 附录 A：多轨并行一页速查

| 轨 | 目录 | 依赖 | 先交什么 | 关键约束 |
|---|---|---|---|---|
| T0 | `contracts/` `tests/integration/` | — | 冻结契约 + CI | 唯一可改契约者 |
| T1 | `genome/` `hub/` | contracts | SDK 封装 + mock | Gene+Capsule 必打包；四态分别记 |
| T2 | `swarm/` `orchestration/` | contracts + T1(mock) | LangGraph 骨架 | 开 checkpoint；最小消息集 |
| T3 | `topology/` `metabolism/` | contracts | **最先完成** | 处理三条数学限制；半衰期用 2^(−t/h) |
| T4 | `evolution/` | contracts + T3(mock) | 编解码 + 适应度 | 张量编码；慢则降级 |
| T5 | `viz/` `apps/demo/` | contracts + T2(mock) | mock 双视图 | 区分当前/均值/最佳 |

> **一句话**：**契约先冻、桩先跑、目录独占、先通窄闭链、再横向加宽**。剩下 48 小时，先让 T3 把纯算法跑绿，全场就有了地基。
