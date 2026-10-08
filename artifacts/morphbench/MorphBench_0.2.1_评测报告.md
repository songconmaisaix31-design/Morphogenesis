# MorphBench × Morphogenesis 0.2.1 —— 评测报告

- **被测版本**：Morphogenesis `0.2.1`（`pyproject.toml` → `[tool.poetry] version = "0.2.1"`）
- **评测套件**：MorphBench（`morphbench.zip`，自包含，CPU-only）
- **运行日期**：2026-10-07
- **运行命令**：`python run_demo.py --budget 24 --seed 0 --out ../outputs`
- **运行环境**：项目 `.venv`（Python 3.13）· numpy 2.5.3 · scikit-learn 1.9.1 · 无 GPU · 墙钟 **1m43s**
- **产出**：`outputs/morphbench_report.json`、`outputs/morphbench_report.md`

> **一句话结论**：套件跑通、数字可复现，**但它测的不是 Morphogenesis 0.2.1 本身**。
> MorphBench 里的 `MorphSwarm` 是一个自包含的搜索策略重实现，与 0.2.1 仓库零代码耦合。
> 因此本报告的数字应读作「**评测框架自检结果**」，**不能**读作「0.2.1 的能力分」。

---

## 一、Tier B：端到端科研 ML（5 任务 × 3 系统，budget=24）

| 系统 | 平均排行榜百分位 | 完成率 | 平均冗余率 |
|---|---|---|---|
| SingleAgent | 87.12 | 1.0 | 0.4833 |
| CentralScheduler | 87.29 | 1.0 | 0.4250 |
| MorphSwarm | 87.29 | 1.0 | 0.4250 |

逐任务明细（`val_score` / 排行榜百分位 / 冗余率）：

| 任务 | SingleAgent | CentralScheduler | MorphSwarm |
|---|---|---|---|
| BM-01 蛋白质适应度回归 | 0.7829 / 95.15 / 0.5417 | 0.8199 / 96.02 / 0.4583 | 0.8199 / 96.02 / 0.4583 |
| BM-02 ADMET 分类 | 0.9866 / 98.00 / 0.6250 | 0.9866 / 98.00 / 0.6250 | 0.9866 / 98.00 / 0.6250 |
| BM-03 单细胞注释 | 0.9345 / 94.44 / 0.5417 | 0.9345 / 94.44 / 0.5000 | 0.9345 / 94.44 / 0.5000 |
| BM-04 生物医学图像 | 1.0000 / 98.00 / 0.5833 | 1.0000 / 98.00 / 0.5417 | 1.0000 / 98.00 / 0.5417 |
| BM-05 GPT 超参优化 | −1.0521 / 50.00 / 0.1250 | −1.0521 / 50.00 / 0.0000 | −1.0521 / 50.00 / 0.0000 |

## 二、Tier A：蜂群原生机制指标

| 指标 | 数值 | 含义 |
|---|---|---|
| SB-01 swarm_survival | **1.0** | 杀掉 2 个 worker 后蜂群仍完成 |
| SB-01 central_survival | **0.0** | 中心调度器被杀即停摆（单点失效） |
| SB-02 reuse_gain | **1.0** | 第二轮"复用经验"后节省的新实验比例 |
| SB-02 round1_units / round2_new_units | 24 / **0** | 第二轮新增实验数 |
| SB-03 overhead_ratio | **0.15** | 相对无协调基线的墙钟开销 |
| SB-04 redundant_rate | **0.3542** | 重复执行配置占已执行单元的比例 |

---

## 三、关键结论

1. **容错是唯一站得住的机制信号**：SB-01 是本次运行里唯一真正体现机制差异的指标——蜂群存活率 1.0，中心调度器 0.0。这与 Morphogenesis 的机制主张方向一致。
2. **任务级分数三系统几乎无差异**（87.12 vs 87.29 vs 87.29），且 BM-02 / BM-04 双双顶到 98 分上限——代理任务区分度不足。
3. **CentralScheduler 与 MorphSwarm 的逐任务结果完全相同**（见第五节问题 2），所谓"三系统对照"实际只有两种不同行为。

---

## 四、证据边界与问题清单（必读）

以下问题**均为本次实跑核验发现**，不是推测。若把本套件结果对外呈现，需先处理。

### 问题 1 —— 套件未接入 0.2.1 引擎（性质：致命，影响结论有效性）
- `morphbench/morphbench/agents.py` 里的 `run_morph_swarm()` 是**约 50 行独立重实现**：一个 `set` 当账本 + 随机抽样 + 固定预算循环。
- 全仓 grep：套件源码对 `morphogenesis` / `swarm` / `bootstrap` / `orca` 的引用数为 **0**。
- 结论：**这不是在测 0.2.1 的蜂群引擎**，而是在测一个"模仿其机制假设"的玩具策略。0.2.1 真实的 lease / task_ledger / pheromone / sandbox 路径完全没有被执行。

### 问题 2 —— CentralScheduler 与 MorphSwarm 结果逐字节相同（性质：对照失效）
```
BM-01: central=(0.8199, dup=11, imp=6)  swarm=(0.8199, dup=11, imp=6)  identical=True
BM-02: ... identical=True
BM-03: ... identical=True
BM-04: ... identical=True
BM-05: ... identical=True
```
原因：两者都用"全局 seen 集 + 相同 `random.Random(seed)` + 相同 20 次重抽"，在无 kill 场景下抽取序列完全一致。中心调度器本应体现"串行化 + 单点失效"的代价，但代码里没有这个代价，于是两组数字退化成同一个。
**影响**：Tier B 的"三系统对照"是虚假的，只剩 SingleAgent vs (其余两者)。

### 问题 3 —— SB-02 reuse_gain 结构性恒为 1.0（性质：同义反复）
`experience_reuse_experiment()` 的第二轮把第一轮账本预热后，先算 `prebest`（= 第一轮最优 = target），再进入 `while best < target` 循环。由于 `prebest` 已经等于 `target`，循环**一次都不执行** → `new_units=0` → `gain = (24−0)/24 = 1.0`。
即：**这个指标在任何输入下都会输出 100%**，不携带信息。

### 问题 4 —— SB-03 overhead_ratio 是硬编码占位值（性质：非实测）
`runner.py` 原文：
```python
base_wall = 1.0
swarm_wall = 1.15  # +15% orchestration, representative placeholder
```
`0.15` 不是测出来的，是写死的。（方案文档第九节已承认"需接入真实引擎运行时后替换"——此处仅确认属实。）

### 问题 5 —— SB-04 分母污染（性质：指标口径错误）
报告的 `0.3542 = 51 / 144`，其中分母 144 把 **SB-02 那一行（24 units、0 dup）** 也算进了 Tier B 的冗余率统计。
只统计 5 个 Tier B 任务时：`51 / 120 = 0.4250`。
**正确值应为 0.4250**，报告值 0.3542 偏乐观。

### 问题 6 —— BM-05 百分位被钉死在 50（性质：任务/锚点不匹配）
BM-05 代理目标的理论最优 val ≈ **1.0521**（−1.0521），而百分位锚点的 `median` 设在 **0.98**（−0.98）。任务可达最优**劣于中位数锚点**，于是 `np.interp` 一律返回左端 50.0。
**影响**：BM-05 对任何系统都贡献常数 50，零区分度；且它把三个系统的均值同时向下拉。

### 问题 7 —— 排行榜百分位不可与头部成绩横向比较（性质：口径声明）
`reference_scores` 锚点（median/p75/p90/sota）是**套件自造**的，不是 BioML-Bench / ProteinGym 的公开分位数。
所以 87.29 这个数**不能**和 AutoScientists 的 74.40%、Autoresearch 的 66.07% 放在一起说"我们更高"。方案文档第八节已给出"换真实数据集"的路径，但当前数字仍是代理口径。

---

## 五、建议的下一步（按性价比排序）

| 优先级 | 动作 | 解决什么 |
|---|---|---|
| P0 | 写一个 `MorphSwarmAdapter`，让 `MorphSwarm` 路径真正调用 0.2.1 的 `swarm/` 模块（账本/路由/费洛蒙）来分配实验 | 问题 1 |
| P0 | 给 CentralScheduler 加上真实代价：串行化排队 + kill 即全停 | 问题 2 |
| P1 | 修 `experience_reuse_experiment`：第二轮必须从"新任务/新空间"起步，或统计"达标所需新单位"而非"是否已达标" | 问题 3 |
| P1 | SB-03 接真实运行时墙钟；SB-04 分母只取 Tier B 行 | 问题 4、5 |
| P2 | 重设 BM-05 锚点或难度，使任务最优落在锚点区间内 | 问题 6 |
| P2 | 若要对外发布：按方案第八节切换真实数据集，或明确标注"代理口径，不可横向比较" | 问题 7 |

---

## 六、复现方式

```bash
# 1. 解压并进入
unzip morphbench.zip && cd morphbench
# 2. 运行（依赖 numpy / scikit-learn；pandas 在 requirements.txt 里但代码未实际使用）
python run_demo.py --budget 24 --seed 0 --out ../outputs
# 3. 产出
#    ../outputs/morphbench_report.json
#    ../outputs/morphbench_report.md
```

本报告全部数字来自上述命令的一次真实运行，未做人工调整。
