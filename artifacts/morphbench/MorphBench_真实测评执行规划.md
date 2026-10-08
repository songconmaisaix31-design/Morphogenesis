# MorphBench × Morphogenesis 0.2.1 —— 真实测评执行规划

> 本文件回答四个问题：①为什么说"去中心化"却还有调度者；②现在还有哪些缺陷；
> ③真实数据怎么换、可行性如何；④分阶段怎么把真实测评做完。
>
> 写作日期：2026-10-07　·　基线：已完成 `real_swarm.py` 适配器（`outputs_real_b8/`）

---

## 〇、先回答：不是去中心化吗，怎么还有调度者？

**你的质疑成立。当前适配器里确实还有一个中心调度者，而且是我写的。**

需要把两件事分开：

### 不是调度者的部分
`swarm.router.Router` **不是**调度器。它自己的 docstring 写得很清楚：

> `choose()` — "Compatibility sampler: a preference, never a lease or execution."
> audit 里 `"advisory_only": True, "claim_requires_recheck": True`

它只给出**建议**，真正的排他占有权来自 `TaskLedger.claim()` 的 fencing token。这是 0.2.1 去中心化设计的核心：**建议可错，占有权由账本裁决**。我的适配器也确实走了这条路径（`choose` → `claim` → 失败即算重复单元）。

### 是调度者的部分（我的缺陷）
`real_swarm.py` 的 `run_real_swarm()` 里有这么一段：

```python
for step in range(budget):
    worker = alive[step % len(alive)]     # ← 我决定了"轮到哪个 worker 干活"
    chosen = engine.router.choose(worker, ...)
```

**这个 `for` 循环 + 轮转分配就是中心调度者。** 它决定了全局步序、决定了谁在什么时候行动、kill 也是我在循环里做的。真实引擎里这一步不该存在。

### 正确的做法（0.2.1 已经提供了）
`swarm/worker_loop.py` —— 模块 docstring 一句话：

> `"""Independent bounded forager using only authorized local task observations."""`

- `class Worker` + `Worker.run()` —— 每个 worker 独立觅食，从共享账本自愿认领
- `class Executor(Protocol)` —— `check_paths` / `bound` / `execute` —— **注入执行器的接缝就在这里**
- `swarm/cli.py` 已经给出了完整范式：
  - `seed_demo()`：建 git workspace + `TaskLedger` + `PheromoneField`，`enqueue` 带 `ValidationPolicy` 的 Signal
  - `demo_config()`：`WorkerConfig(state, target, agent=AgentId(role="builder", instance=i), locality, budget=BudgetPolicy, seed=i)`
  - `demo()`：`multiprocessing.get_context("spawn")` 起 **3 个独立进程**，每个跑 `process_worker()`

所以真正的去中心化跑法是：**N 个独立 Worker 进程 + 一个 `MorphBenchExecutor`，共享同一个账本和费洛蒙场。** 没有谁决定"下一个是谁"。

**附带收益**：SB-01 容错会变得真正有意义——可以 `kill` 真实的 OS 进程，测的是 lease 过期、任务回退给账本、其余 worker 接管，而不是我现在"少转几圈循环"。

---

## 一、缺陷总表

### P0 —— 影响结论有效性，必须先修

| ID | 缺陷 | 证据 | 修法 |
|---|---|---|---|
| **D1** | **适配器有中心驱动循环** | `run_real_swarm()` 的 `for step ... worker = alive[step % len(alive)]` | 改用真实 `Worker` 多进程 + `MorphBenchExecutor`（见〇） |
| **D2** | **只真实了"分配"，没真实"执行"** | 适配器直接调 `task.evaluate(cfg)`（Python 函数），完全绕过 `orchestration.experiments` 的沙箱执行链（`LocalCpuSandboxBackend` / `OpenSandboxBackend`） | 实现 `Executor.execute()`，走真实的执行与证据链 |
| **D3** | **Tier B 仍是合成数据** | `local_tasks.py` 全是 `_reg_data` / `_clf_data` / `_img_data` 合成的 | 见第二节数据路线 |
| **D4** | **单种子，无置信区间** | 全部 seed=0 | ≥5 seeds + bootstrap CI + FDR |
| **D5** | **预算 > 搜索空间导致饱和** | 预算 24 > 空间 13/9/12/11；预算 24 三系统分数无差异 | 预算必须 < 最小空间；或扩大空间 |

### P1 —— 影响可比性与解读

| ID | 缺陷 | 说明 |
|---|---|---|
| D6 | `SingleAgent` 仍是重实现 | 它是"无共享记忆"参照系，没有真实引擎形态 |
| D7 | 百分位锚点自造 | median/p75/p90/sota 不是公开排行榜分位数 → **不可与 AutoScientists 74.40% 横比** |
| D8 | BM-05 锚点错配 | 理论最优 −1.0521 劣于 median 锚点 −0.98 → 百分位恒为 50，真实引擎的改进看不见 |
| D9 | SB-03 依赖单元成本 | 单元是约 0.2s 的 sklearn 拟合，协调开销被放大；真实 5 分钟训练下会大幅下降 |
| D10 | 容错太弱 | 只是减少 worker 数，没测 lease 过期 / handoff / breaker / 部分结果续跑 |

### P2 —— 完整性

| ID | 缺陷 | 说明 |
|---|---|---|
| D11 | Tier C 完全未实现 | MLR-Bench / ScienceAgentBench 的 rubric 判官没有接 |
| D12 | 关键超参是拍的 | `tau_seconds=30` / `exploration=0.10` / 沉积量 / 邻域半径，未做敏感性分析 |
| D13 | 未接 `BudgetLedger` | 预算是我用 `RunLimits` 硬撑的，没走真实预算策略 |
| D14 | 学习效应未单独量化 | `pipe_history` / `reinforce` 到底学到什么，没有独立指标 |

---

## 二、真实数据：可行性与分级

### 已实测的网络条件（2026-10-07，本机）

| 检查项 | 结果 |
|---|---|
| 代理 | `HTTP_PROXY=http://127.0.0.1:52523`（已生效） |
| `pip -i https://pypi.org/simple/` | **可用**（已成功下载 openpyxl wheel） |
| 清华镜像 `pypi.tuna.tsinghua.edu.cn` | **403**（默认配置走这个，必须显式加 `-i https://pypi.org/simple/`） |
| `www.openml.org` | **200** |
| `archive.ics.uci.edu` | **200** |
| `raw.githubusercontent.com`（ProteinGym） | **200** |
| `fetch_openml` | 失败原因是缺 pandas —— 装了就能用 |

结论：**真实数据这条路是通的**，瓶颈不在网络，在任务规模与算力。

### 分级路线

| 级别 | 数据源 | 对应任务 | 工作量 | 能否与头部横比 |
|---|---|---|---|---|
| **L0** | sklearn 内置**真实**数据集：`load_breast_cancer`（569 例真实乳腺肿瘤活检）、`load_diabetes`（442 例真实糖尿病）、`load_wine`、`load_digits` | BM-02/BM-03/BM-04 的位置 | 半天，离线 | ❌ 不是 BioML-Bench 任务 |
| **L1** | OpenML / UCI 真实生物医学集（如 `breast-w`） | BM-02 分类、BM-04 影像替代 | 1 天 | ❌ 同上 |
| **L2** | ProteinGym 217 assays（GitHub raw 可达）、TDC ADMET（`pip install tdc`） | BM-01、BM-02 | 2–3 天 | ⚠️ 取决于锚点是否换成公开分位数 |
| **L3** | Open Problems 单细胞（数据量大）、Kaggle（需凭据）、nanochat 真实训练（需 GPU） | BM-03、BM-04、BM-05 | 数天 + GPU | ✅ 才能真正同口径 |

### ⚠️ 一个必须先讲清楚的点

**换上真实数据 ≠ 可以和 AutoScientists 横比。**

现在的链条是「真实数据 + 自造尺子」。要真正同口径，必须**同时**做两件事：
1. 任务数据换成公开的（L2/L3）；
2. **百分位锚点换成公开排行榜的真实分位数**（来自 BioML-Bench / ProteinGym 官方 leaderboard 的提交分布）。

只做第 1 条，得到的仍然是"真实数据 + 我自己的尺子"，对外只能说"在这些真实任务上的绝对指标"，**不能**说"百分位 87，高于 AutoScientists 的 74.40"。

另外 **CPU-only 是硬约束**：BioML-Bench 的影像/单细胞任务和 nanochat 的训练优化，在纯 CPU 上要么跑不动、要么慢到无法做 matched-budget。BM-05 的"真实训练"必须标注需要 GPU，否则只能保留代理并明确声明。

---

## 三、分阶段执行规划

### Phase 0 —— 去掉中心调度者（修 D1）· 约 1 天

1. 实现 `MorphBenchExecutor`，满足 `swarm.worker_loop.Executor` 协议：
   `check_paths` / `bound` / `execute` → 返回 `ExecutionResult`
2. 照 `cli.seed_demo()` 的范式写 `seed_morphbench_task()`：
   git workspace + `TaskLedger` + `PheromoneField` + 每个配置一个带 `ValidationPolicy` 的 Signal
3. 照 `cli.demo()` 的范式用 `multiprocessing spawn` 起 N 个独立 `Worker` 进程
4. SB-01 改为 kill 真实进程

**验收判据**（必须全部满足，否则不算完成）：
- [ ] 代码里不存在任何决定"下一个行动 worker"的中心循环或轮转
- [ ] 每个 worker 是独立 OS 进程，可被 `kill` 且不影响其他进程继续
- [ ] 所有任务状态变更只经由 `TaskLedger` 的 `claim`/`submit`
- [ ] 杀掉 worker 后，其未完成任务能 lease 过期回退、被其他 worker 接管

**已知风险**（开工前需确认）：`Executor.execute` 的签名涉及 `Candidate`、`AttemptId`、`ExecutionBound`、`ConsumptionExecution`、`Provenance` 等类型，需先读 `local_assets.models` 与 `contracts.identity` 确认构造方式；`WorkerConfig` 还要求 `BudgetPolicy`，需接真实预算策略（顺带修 D13）。

### Phase 1 —— 真实数据接入 L0/L1 + 锚点可溯源（修 D3、D7、D8）· 1–2 天

1. `local_tasks.py` 增加 `real=True` 分支，优先用 L0 内置真实数据
2. 每个真实任务在输出里记录 **数据集来源、版本、样本数、切分方式**，让数字可溯源
3. 修 BM-05 锚点（或改用有公开参考的指标口径）
4. 锚点若拿不到公开分位数，报告中**显式标注"自造锚点，不可横比"**

**验收判据**：
- [ ] 至少 3 个 Tier B 任务跑在真实数据上
- [ ] 报告里每个分数能追到具体数据集与切分
- [ ] 锚点来源有明确出处，或已明确标注不可横比

### Phase 2 —— 统计可信度（修 D4、D5）· 1 天

1. ≥5 seeds，报告均值 ± 标准误与 bootstrap 95% CI
2. 预算固定为 < 最小搜索空间（当前 8），并在文档里写明这条约束
3. 系统间差异做显著性检验（配对 bootstrap 或序贯检验 + FDR）

**验收判据**：
- [ ] 每个系统–任务组合有 ≥5 seeds
- [ ] 主结论附带置信区间；若区间跨 0，结论必须改写为"未观察到显著差异"

### Phase 3 —— 机制层补全（修 D6、D10、D11）· 2 天

1. SingleAgent 做一版真实引擎参照（裸 worker：无账本、无费洛蒙）
2. 容错扩到 lease 过期 / handoff / breaker
3. Tier C 接 MLR-Bench / ScienceAgentBench 的 rubric 判官（需人工专家校准后才能对外）

### Phase 4 —— 真实榜单同口径（L2/L3）· 数天，需 GPU

1. ProteinGym 217 assays / TDC ADMET 接入
2. 锚点换成官方 leaderboard 的真实分位数
3. BM-05 若有 GPU 则接 nanochat 真实训练，否则保留代理并声明

---

## 四、对外表述的诚信边界（完成到哪一阶段，就只能说到哪一步）

| 完成到 | 可以说的 | **不能**说的 |
|---|---|---|
| 当前（Phase 0 前） | "0.2.1 的账本/费洛蒙/路由驱动了实验分配；预算 8 下百分位 87.29，优于中心调度器 86.79、单智能体 85.86；冗余率 0" | "0.2.1 在 BioML-Bench 上 87 分"、"优于 AutoScientists" |
| Phase 0 后 | "N 个独立 worker 进程去中心化觅食，杀进程后任务被接管" | "执行链路已真实"（若 D2 未修） |
| Phase 1 后 | "在 X 个真实数据集上的绝对指标" | "排行榜百分位 87"（除非锚点已是公开分位数） |
| Phase 2 后 | "5 seeds，差异 ±CI" | 单种子结论当定论 |
| Phase 4 后 | 与 AutoScientists 同口径比较 | —— |

---

## 五、优先级建议

如果你只有有限时间，**按这个顺序**：

1. **Phase 0（去掉中心调度者）** —— 这是最能被一眼看穿的硬伤，也是 Morphogenesis 机制主张的立身之本。当前"去中心化"的宣称和我的实现之间有一道缝。
2. **Phase 2（多种子 + CI）** —— 最便宜，半天能出，但决定了 0.5 个百分点能不能拿出去说。
3. **Phase 1（真实数据 L0/L1）** —— 把"合成数据"这个标签先摘掉一半。
4. Phase 3 / Phase 4 —— 视比赛时间决定。

要我现在直接开工 Phase 0 吗？
