# MorphBench 0.2.1 本地评测

已执行 5 BM × 5 seeds × 3 systems，**expected=75、observed=75、missing=0**；67 个完整预算试验、8 个 partial，正式批次 **exit=1** 如实保留。真实 Worker 搜索完成 **192/200** 个允许单元，17/25 个试验达到 8 次；加上 525 次预计算和 25 次最终评价，共 **742 次 evaluate 调用**，两个串行基线各为 **225 次**。仅搜索 allowance 相同，总计算并不等量；不能据本结果宣称 Morphogenesis 优于竞品。

本报告测量固定合成任务上的本地 CPU 拟合与已安装 Worker 执行，不提供官方科学榜单成绩。原 Word 方案的 5 个 BM、4 个 SB 分别保留证据层级：SB-02 适配器的五种子经验迁移增益均为 0；SB-03 是含进程/Git/SDK/验证的流水线开销，SB-01 的真实故障边界来自 Q 独立控制。BM-05 是数学函数，Tier C 尚未接入正式数据或判官。全部原始失败、partial 与未执行项保留。

被测产品 SOURCE：`50396909c3fbaa510e755b8e2361e05d84afdfaa`，版本 0.2.1。评测工具 SOURCE：`b76d5e17c5462209e511a46d29b5a55b146050b7`，分支 `songconmaisaix31-design/morphbench-eval-1007`。工具 SOURCE 在长跑前 commit、push，并用 `git ls-remote` 核实；后继报告提交单列，不把报告提交当产品源码。

后处理 SOURCE：`a05431259748fdf98340a02e7734ccb934eb35db`，只修正展示/覆盖率、增加包含 partial 的描述性配对表和相应测试；不修改本批 `run_local.py`、`mechanisms.py`。Q 测试 SOURCE `12479cfa5a058f1dab4413a6464f6d691dec53af`，Q REPORT `fbb67d10f9977a00f78a730c9b645f70439031f1`。本文件 REPORT SHA 由 docs-only 提交和最终交接给出，避免文件自引用。

事实源：`C:/Users/DW/Downloads/MorphBench_对标评测方案.docx`（v1.0，2026-10-07），当前 Dispatch 的 CPU/本地授权，以及 HEAD `89e3c49f32e3bcb57fded741565ec4b3e889d777` 中的 MorphBench 一页计划。该 checkout 的计划实际附在 `docs/PLAN.md` 底部，顶部仍是 R1 历史段；本轮以 Dispatch 与本次计划为准。

## 复现与前置

运行工具、协议和完整命令见 [tools/morphbench/README.md](../../tools/morphbench/README.md)。没有复制或发布来源许可不明的 suite；复现需要已提供的私有快照 `C:/Users/DW/orca/mb021-1007/suite`。原始 `C:/Users/DW/orca/Morphogenesis/artifacts/morphbench/**` 未写入。所有 M 运行产物在 `C:/Users/DW/orca/mb021-1007/eval/**`。

正式 Python：`C:/Users/DW/orca/mb021-1007/verify/venv/Scripts/python.exe`，由 Q 建立并授权 M 只读使用。M 不修改任何共享环境、产品领域源码、锁文件或其他轨文件。Q 的 Node 依赖位于 `verify/node_modules`，按照被测产品原锁安装，供 installed `bridge_node` 的 ESM 父目录查找。原 `mb021-1007/venv` 的 Python 包版本对齐不等于完整运行前置已满足。

父进程和每个 Worker 都检查 `swarm.worker_loop`、`local_assets.validate` 来自当前 `sys.prefix/Lib/site-packages`，分发版本 0.2.1 且非 editable。版本号不能证明源码字节；Q 的 `verify/exact-source-comparison.json` 对产品 SOURCE 比较了 216 个 installed 文件、222 个 archive 文件及 1 个原测试副本，mismatches/missing 均为空。该结果是本轮读到的 Q 独立证据，不宣称 M 重新做了同一字节审计。进程从 eval 运行，仅把 suite 路径加入导入路径；不注入产品源目录。线程限制只在评测进程环境设置：OpenBLAS/OMP/MKL/NumExpr 均为 1，不改系统配置。

仓库存在 AOCI root/meta/code 文件，但本 Agent Run 没有可调用的 AOCI MCP 工具；未建立当前完整认知收据，也未写托管索引。仅依据当前读到的源码、方案和所有权完成此范围内工作；索引状态不冒称已刷新或已对齐。

## 首失败与验证链

| 证据 | 结果与解释 |
|---|---|
| Word 初次 stdout 提取 | GBK 编码在 `−` 字符抛 UnicodeEncodeError，未完整读取；改进程内 `PYTHONIOENCODING=utf-8` 后完整读取，未修改 Word |
| `eval/smoke-first-sdk-missing.log` 及同名目录 | 原 installed venv，BM-05 / seed 0 / budget 1 / 1 Worker；搜索执行 1、completed 0、最终测试 0，60 次 acceptance 预计算；Worker 在 publish_asset 报 BridgeError，保留原 failure、账本和结果 |
| Q `verify/installed-probe-first.json` | Q 独立定位 Node ERR_MODULE_NOT_FOUND: ajv / sdk_process_failed；M 不修改环境或放宽验证 |
| `eval/smoke-sdk-ready.log` 及同名目录 | Q 修复前置后新独立目录，BM-05 / seed 0 / budget 1 / 1 Worker：PASS，1 completed；共 60 + 1 + 1 = 62 次评估调用，60.567 秒；与 Q 并行，不能作为正式时间对照 |
| `eval/statistics-first.log` | 6 PASS / 0.22 秒，配对对齐、负差、缺失配对、五样本精确检验、BH 调整、全局 energy 与不完整试验隔离 |
| `eval/statistics-final.log` | 后处理修正后 7 PASS / 0.19 秒；增加 expected/observed/first exception/NOT_RUN 的覆盖测试，保留 partial 描述性端点 |
| 3 个工具模块编译 / `git diff --check` | PASS；编译输出写 eval，不写产品或私有 suite |

适用测试命令（cwd=eval）：

```powershell
& C:/Users/DW/orca/mb021-1007/verify/venv/Scripts/python.exe -m pytest -q -o addopts= -p no:cacheprovider C:/Users/DW/orca/workspaces/Morphogenesis/morphbench-eval-1007/tests/morphbench
```

本轨没有改产品源码，不把最终 7 项检查当产品全量回归或构建。Q 的原产品安装态回归单列引用。原主控 `protocol-b24-s0.log` 和 `protocol-b24-s0/morphbench_report.{json,md}` 只读保留，不与新 Worker 批次混并；该旧复跑来自源码 cwd 现有 venv，其 round-robin 驱动、alive 列表、锚点百分位和早期报告结论不能升级为真实去中心化/官方榜单证据。

首 smoke 的 Python exit 未单独保存，组合 PowerShell 命令最后执行了 Get-Content，因此外层返回 0 不能代表试验通过；其 JSON 明确为 INCOMPLETE、0 completed、publish_asset BridgeError。后继 smoke 外层保留 Python exit=0。正式矩阵和机制均另存 `.exit.txt`，不把 shell 尾命令或后继成功覆盖原失败。原 budget24 runner 的全空间反查 best 引入额外评估，但旧输出未记录确切次数，不能追认其总计算为仅 24 单元。

## 预算、随机性和统计边界

正式设计是 5 BM × 5 allocation seeds（0..4）× 3 systems，搜索上限每系统 8。SingleAgent 与 CentralScheduler 复用私有 suite 的串行分配策略；MorphSwarm 是 3 个独立真实 `Worker.run()` 进程，以原 `TaskLedger` 和 `RunLimits(max_attempts=8)` 裁决，energy 分配 3/3/2。实际 WorkerConfig.seed 为 `1000 * trial_seed + worker_index`。不增加第二账本、调度器或补预算重试。

energy 消耗的是感知循环，不保证每次都执行；争抢或停止会让实际执行少于 8。实际次数、进程退出码、completed 数和每次配置索引独立保存；少于 8 明确记 INCOMPLETE，并保留在 observed/partial 统计，不能进入完整搜索预算的配对比较。

首个 partial 是 BM-01 / seed 1：其 `state/tasks.sqlite3` 的 `task_audit` 中 seq14 的 builder-1 与 seq16 的 builder-0 都推荐 cfg-10；seq17 只有 builder-1 成功 claim；builder-0 随后 seq19 推荐 cfg-1、seq20 claim。全试验 8 routing、7 claimed、7 completed，builder-0 energy=3 但只 completed=2，三个进程均正常退出，无执行失败。结合原 Worker 在感知前扣 energy 的代码，这支持一次认领争抢消耗 energy 的解释；账本没有持久化失败 claim 的独立拒绝 reason，因此不捏造更细的失败事件，也不把它误写为全局 max_attempts 超限。

原 executor 在预置不可变 validation policy 时对全配置 evaluate：BM-01/02/03/04/05 分别 13/9/12/11/60 次。该开销仅 Worker 组承担，另加有结果时选定配置的一次 final evaluation（BM-01..04 为 held-out 测试，BM-05 为同一数学函数、无独立 test）；因此本研究只对齐搜索 allowance，**总计算成本不等预算**。不重新遍历所有配置反查最佳分数；直接用实际执行/应用文件选 best。每次 started/finished 日志和 ledger-snapshot 供复核；不把 fixture token/cost 当真实费用，实际 cost 保持 null。

BM-01 至 BM-04 实际拟合 sklearn 模型，但数据固定为合成矩阵；数据/模型种子不随 allocation seed 改变。BM-05 只是带缓存的数学目标，每次 evaluate 调用不代表 GPT 训练或独立模型拟合。Worker 并发顺序、墙钟衰减和运行 ID 仍可能产生非种子确定性。

每项原始最终评价报告均值、样本标准差/√n 的 SE；BM-01..04 使用合成 held-out 测试，BM-05 再算同一数学函数，**没有独立 held-out 测试集**。配对按同 BM、同 seed 对齐，10,000 次 percentile bootstrap（RNG 20261007），输出 Worker 减两个基线的均值差与 95% 区间。结果仅描述固定代理任务下分配策略变动，不覆盖数据集、科学问题或模型泛化不确定性。附加十个完整预算对照的双侧精确 sign-flip 检验及 BH FDR 调整均为探索性；五对数据最小双侧 p=2/32，不能据此宣称显著优势。原方案序贯检验没有预先指定停止规则，记 NOT_RUN。

Q 在长跑初期提出两项展示修正：把 Held-out 列改为 Final evaluation，明确 expected/observed/missing 组合。M 只调整汇总后处理与文档，运行 driver、budget、判据和本批时序没有变化；并另列固定 allowance 下包含 partial 的可观察端点配对 CI。该补充分析是观察到首个 partial 后添加的描述性分析，不冒称预注册；完整预算子集可能有选择偏差，不能只用其较好的 CI 断言总体优势。缺失分数保持缺失，不补成 0。

## 正式结果

运行时间：`2026-10-07T14:46:16.650150Z` 至 `14:55:57.667317Z`。原始矩阵：`eval/matrix-b8-s0-4/` 与 `.log` / `.exit.txt`；汇总：`eval/summary-b8-s0-4/summary.{json,md}`；机制：`eval/mechanisms-b8-s0-4/mechanisms.json` 与 `.log` / `.exit.txt`。每个 trial 目录含 result、实际配置和逐次 evaluation 日志；Worker 另含状态、账本快照、实际应用文件、原 SQLite 和进程结果。

| 系统 | 计划/观测试验 | 达 8 次执行 | 搜索完成/上限 | 搜索重复 | acceptance 预计算 | 最终评价 | 全部调用 |
|---|---:|---:|---:|---:|---:|---:|---:|
| SingleAgent | 25/25 | 25/25 (100%) | 200/200 | 39 | 0 | 25 | 225 |
| CentralScheduler | 25/25 | 25/25 (100%) | 200/200 | 0 | 0 | 25 | 225 |
| MorphSwarm / installed Worker | 25/25 | 17/25 (68%) | 192/200 (96%) | 0 | 525 | 25 | 742 |

8 个 partial 均为 7 次搜索完成：BM-01 seeds 1/4、BM-02 seed 4、BM-03 seeds 1/4、BM-04 seeds 1/4、BM-05 seed 4。没有缺失组合、没有补跑。三个系统共 592 次搜索、525 次预计算、75 次最终评价，合计 **1192 次调用**；其中 BM-01..04 共 **758 次真实 sklearn 拟合**，BM-05 共 **434 次数学函数 evaluate 调用**，不把缓存命中当训练。

下表保留每个系统全部五个 allowance 端点，包含 partial；每格为均值 ± SE。独立合成测试仅 BM-01..04；BM-05 为同一数学目标。

| 任务 / 原始指标 | SingleAgent (n=5) | CentralScheduler (n=5) | Worker (n=5，含 partial) | Worker 完整预算 n |
|---|---:|---:|---:|---:|
| BM-01 / suite Spearman | 0.790824 ± 0.017796 | 0.814602 ± 0.002744 | 0.812125 ± 0.003459 | 3 |
| BM-02 / AUROC | 0.985441 ± 0.000573 | 0.986014 ± 0.000000 | 0.986266 ± 0.000154 | 4 |
| BM-03 / Accuracy | 0.932500 ± 0.003333 | 0.930833 ± 0.002500 | 0.932500 ± 0.003333 | 3 |
| BM-04 / Accuracy | 0.995261 ± 0.000000 | 0.995261 ± 0.000000 | 0.995261 ± 0.000000 | 3 |
| BM-05 / 负数学目标 | -1.112888 ± 0.028573 | -1.112743 ± 0.028455 | -1.113452 ± 0.015394 | 4 |

固定 allowance 的描述性配对差值（Worker − baseline，n=5；均值差 [95% bootstrap CI]）：

| 任务 | 对 SingleAgent | 对 CentralScheduler |
|---|---|---|
| BM-01 | +0.021301 [-0.010949, +0.059859] | -0.002476 [-0.010949, +0.005997] |
| BM-02 | +0.000825 [0.000000, +0.002224] | +0.000252 [0.000000, +0.000503] |
| BM-03 | 0.000000 [-0.008333, +0.008333] | +0.001667 [-0.005833, +0.009167] |
| BM-04 | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] |
| BM-05 | -0.000564 [-0.061899, +0.060770] | -0.000709 [-0.061899, +0.060480] |

完整预算子集的 Worker 最终评价均值 ± SE：BM-01 0.808360 ± 0.004707 (n=3)，BM-02 0.986171 ± 0.000157 (n=4)，BM-03 0.936111 ± 0.002778 (n=3)，BM-04 0.995261 ± 0 (n=3)，BM-05 -1.108489 ± 0.018813 (n=4)。该子集全部 10 个配对差值、SE、CI 和原始 seed 列表位于 summary.json / summary.md，探索性 BH q 均为 1.0。BM-04 的零方差只是本代理任务得分饱和，不构成普遍等效性证明；没有稳定整体优势或竞品优越性结论。

| 机制 | 本次结果 | 层级及限制 |
|---|---|---|
| SB-01 | 原适配器 5 seeds 每次 swarm 执行 8、central 执行 4；共 60 次数学评估 | contract_local_adapter_only；实际 process kill=0，所谓存活布尔值不可作为真实 Worker 指标。真实 kill 另见下方 Q 两阶段控制 |
| SB-02 | signed gain 均值=0、SE=0、n=5；cold/warm 到目标单元分别都是 [5,4,8,3,6]；无删失 | contract_local_adapter_field_transfer；每 seed 四个完整 budget=8，实际共 160 次数学评估，不因提前达标少算执行。没有 real Worker 科研资产消费/采用链，科研经验收益 NOT_RUN |
| SB-03 | `(Worker wall / same-config serial wall) - 1`：均值 22.7842、SE 4.1861、n=5；逐 seed 38.3709/20.9694/19.1560/13.2619/22.1630 | 本机 installed Worker 流水线相对墙钟增量；包含 spawn、Git、SDK、验证、并行及时间顺序影响，不含 acceptance 预拟合；不是纯协调算法开销，更不是 Word 的占位 0.15 |
| SB-04 | Single 39/200=19.5%；Central 0/200=0%；Worker 0/192=0% | trial 内重复配置 / 实际搜索 evaluate；不计 acceptance/test refit，但它们已列总成本。0 重复不代表零争用、无所有外部重复效果或零科研浪费 |

SB-03 各 seed 的 Worker wall / 串行回放秒数为：45.696393/1.160665、13.285493/0.604728、11.787721/0.584825、12.563701/0.880930、11.847861/0.511500。回放配置数量为 8/7/8/8/7，共 38 次真实拟合；两侧使用该 trial 实际相同配置集合，不把未执行的第八次填入 partial。机制整体 **258 次调用 = 60 + 160 + 38**，exit=0。

正式矩阵与机制总计 **1450 次调用 = 796 次 sklearn 拟合 + 654 次数学函数调用**。独立的两个 M smoke 另计 **123 次数学调用**（61 + 62），不纳入统计；M 本轮含 smoke 共 **1573 次调用**。主控原 budget24 run、原 worker-first 和 Q 控制不并入此账。Provider usage/actual cost 仍非计费测量，真实费用 null。

已执行命令记录（cwd 为 `C:/Users/DW/orca/mb021-1007/eval`，这些目录已存在，复现须换新输出目录；本次没有重跑）：

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONDONTWRITEBYTECODE='1'
$benchPy='C:/Users/DW/orca/mb021-1007/verify/venv/Scripts/python.exe'
$benchTools='C:/Users/DW/orca/workspaces/Morphogenesis/morphbench-eval-1007/tools/morphbench'
# 原始 smoke 首失败用的是 .../mb021-1007/venv/Scripts/python.exe
& C:/Users/DW/orca/mb021-1007/venv/Scripts/python.exe "$benchTools/run_local.py" --suite C:/Users/DW/orca/mb021-1007/suite --output C:/Users/DW/orca/mb021-1007/eval/smoke-first-sdk-missing --tasks BM-05 --seeds 0 --systems MorphSwarm --budget 1 --workers 1
& $benchPy "$benchTools/run_local.py" --suite C:/Users/DW/orca/mb021-1007/suite --output C:/Users/DW/orca/mb021-1007/eval/smoke-sdk-ready --tasks BM-05 --seeds 0 --systems MorphSwarm --budget 1 --workers 1
# 75/75 observed，67完整 + 8 partial，exit 1
& $benchPy "$benchTools/run_local.py" --suite C:/Users/DW/orca/mb021-1007/suite --output C:/Users/DW/orca/mb021-1007/eval/matrix-b8-s0-4 --budget 8 --seeds 0 1 2 3 4 --measurement-window Q_quiet_after_2026-10-07T14:44:05Z
# 机制258调用，exit 0
& $benchPy "$benchTools/mechanisms.py" --suite C:/Users/DW/orca/mb021-1007/suite --matrix C:/Users/DW/orca/mb021-1007/eval/matrix-b8-s0-4 --output C:/Users/DW/orca/mb021-1007/eval/mechanisms-b8-s0-4 --measurement-window Q_quiet_after_2026-10-07T14:44:05Z
# 汇总75 trials / 15 groups，exit 0
& $benchPy "$benchTools/summarize.py" C:/Users/DW/orca/mb021-1007/eval/matrix-b8-s0-4 --output C:/Users/DW/orca/mb021-1007/eval/summary-b8-s0-4
```

首 partial 的最小审计读取为 SQLite 只读连接，查询 `SELECT sequence,task_id,event,at,body FROM task_audit WHERE event IN ('routing','claimed') ORDER BY sequence`，仅解析 body 中 worker_id/selected/reason；不修改 DB 或新增任务。统计测试与汇总在机制计时退出后运行，未与拟合重叠。

最终只读一致性复核 PASS（`eval/consistency-check.log`）：75 个 trial 的 started/finished 与原日志逐个相等；25 组 Worker 的实际 config seed、energy=3/3/2、75 个进程 exit=0 与状态一致；原 SQLite completed 数与保存快照/结果相同；所有执行不超过 8，汇总覆盖率 75/75、67 complete、1450 正式调用与原记录一致。此为 M 自检，不替代 I 独立复核。没有启动 timeout kill，也没有通过重启进程填补 partial。

Q 于 `2026-10-07T14:44:05Z` 明确释放 CPU 测试窗口。M 正式矩阵在此之后启动，Q 仅继续浏览器、文档及轻量只读核对；这不是独占机器或固定硬件基准，背景负载未隔离，时间仅作本机描述性观测。

BM-01 seed 0 的首个 Worker 总时长 65.524 秒，后续部分试验约 14–16 秒，两个首串行基线也明显更慢；启动、缓存与系统背景负载可能影响，未独立定位其贡献。不重排或剔除这些较慢试验；SB-03 的同配置串行回放发生在矩阵之后，不能消除时间顺序和热缓存偏差，不能把整个差值归因为纯协调算法。

SB-01 的独立真实进程证据由 Q 提供，不能用原 suite 的 `alive` 数组删除或 central 布尔值替代：

| 故障注入点 | 实际观察 | 不能证明什么 |
|---|---|---|
| `verify/kill-controls-second/two-kill-before_reservation.json` | 2 个实际 Worker PID 被 kill；无人工 release/reset，等待自然 TTL 后 3 个后继 Worker 完成 6/6，stale submit 无副作用 | 是 mock fixture 的机制边界，不是科研任务存活概率估计，也没有真实中央调度器 kill 对照 |
| `verify/kill-controls-second/two-kill-after_reservation.json` | 2 个实际 Worker PID 在 reservation 后被 kill；恢复报告 unknown_usage，预算 sleeping，2 个 uncertain reservations，0/6 completed，tokens/actual cost 为 null | 正确保守停止不能写成“杀两个仍 100% 成功”；未知效果不可自动重试 |

上述两控制的 provenance=mock、evidence_class=contract_local、task_live=not_run。Q 的首故障控制 RED 与 Windows launcher PID 修正均在 `verify/kill-controls-first*` 保留；M 只读取第二轮 JSON，不重放它们或修改其试验。

## 真实科研与榜单缺口

| 任务或范围 | 本次本地可执行部分 | 正式接入状态 |
|---|---|---|
| BM-01 ProteinGym / BioML | 固定合成回归，suite Spearman 实现为双 argsort；不是官方 tied-rank scorer | NOT_RUN：官方 assay、数据版本、划分、标准评估与参赛协议未接入 |
| BM-02 TDC / Polaris ADMET | 合成二分类，AUROC | NOT_RUN：官方分子数据、划分、任务与 scorer 未接入 |
| BM-03 Open Problems 单细胞 | 合成四分类，Accuracy | NOT_RUN：单细胞矩阵、标签、官方拆分与运行协议未接入 |
| BM-04 Kaggle / BioML 影像 | 合成 8×8 patch 图片分类，Accuracy | NOT_RUN：竞赛原始影像、授权、私榜与官方 scorer 未接入 |
| BM-05 nanochat | 缓存数学函数的负目标，较高为好 | NOT_RUN：没有 GPT、语料、训练执行器、GPU或真实 bpb 计算；云/GPU/收费执行未授权 |
| BioML 官方均值百分位/奖牌 | 不计算自造锚点百分位 | BLOCKED：无官方参考分布与同协议真实任务成绩；不能与方案里的外部产品百分位比较 |
| MLR-Bench / MLR-Judge | 原 suite judge 为关键词启发式，本次不生成科研质量分 | NOT_RUN：官方任务、完整研究产物、九维判官、专家校准、付费调用授权均未提供 |
| ScienceAgentBench VER/SR/CBS | 本地 ML 试验不等于正式代码任务 | NOT_RUN：官方任务/数据环境、执行沙箱、测试与 CodeBERT scorer 未接入 |
| PaperBench / MLE-bench / RE-Bench / ICLR 盲审 | 本轮无对应正式运行 | NOT_RUN：数据、专用评测环境/资源与独立评审缺失 |
| 正式 R1 AT-07 / L2 科研 | 未触发 | NOT_RUN：本任务为离线本地代理 CPU 测评，不替代既有科研隔离/授权门 |

未验证 Word 中外部产品的公开成绩、日期或引用真伪，也不依此给产品排名。后续真实榜单对齐需要分别确认官方数据版本、许可、scorer、split、预算、资源和运行批准；直接替换数据加载器并不能自动获得官方可比性。

## 交接和未执行事项

M 的本地测评、工具、统计与证据说明已交付；正式矩阵仍是 67 完整 / 8 partial，未知费用仍为 null。所有 Worker 自有进程句柄已 join 并观测 exit=0，原 Git 工作区、SQLite、日志保留供审计；不清理证据目录。独立 I 需要普通精确合并运行 SOURCE、后处理 SOURCE、本报告提交与 Q 交付，再核对原始结果，M 不代做该独立验收。

Q 的产品地址为 `http://127.0.0.1:8099/` 和 `http://127.0.0.1:8099/#/swarm`；Q REPORT fbb67d10 已核验页面/HTTP，同时明确研究服务未配置、布局缺陷与示例数据边界。M 没有重复浏览器验收、重启该服务或改前端。源安装 Node 前置、页面领域缺陷与正式科学接入由主控交原 Owner，不能用本地 ML 得分替代。

未执行：产品全量 pytest/mypy/build/SDK 工程门、官方科研数据/模型/判官、AT-07/L2、GPU/收费资源、完整科研经验消费/采用链、序贯检验与任何官方榜单提交。没有用户手工操作能把这些状态自动变为通过；后续需在各自范围明确数据、资源和授权后另立运行，不重放未知操作。本分支正常 commit/push，不 force push、不修改产品公共历史；最终远端 SHA 与 clean 状态见完成交接。
