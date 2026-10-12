# MorphBench 0.2.1 独立集成与最终验收

本轮已交付可核对的本地合成 CPU 评测：5 任务 × 5 allocation seeds × 3 系统，**expected=75、observed=75；67 PASS、8 INCOMPLETE、0 ERROR、0 NOT_RUN、0 missing**。8 个不完整试验均只完成 7/8 搜索单元，矩阵原退出码 **1** 保留。真实安装态 Worker 完成 192/200 搜索单元；合并后的统计测试 7 PASS，独立核账和汇总重算通过。**方案要求的完整官方榜单评测、真实 LLM 科研质量及科研经验收益尚未完成，均不能从本地分数推导。**

完整预算与包含 partial 的全部端点比较，其 95% bootstrap 区间均包含 0；完整预算十项探索性 BH q 均为 1。没有系统优越性、官方百分位或竞品胜出结论。产品地址仍为 <http://127.0.0.1:8099/>；HTTP 可达，但研究服务未配置、视觉验收未通过。

本报告由 I 独立集成 Worker 完成，Task `task_3abb815be5a8` / Dispatch `ctx_0b8bc5841673`。依据当前 Dispatch、`docs/PLAN.md` 末尾 2026-10-07 执行页与原 Word 方案；原 Word 和 `C:/Users/DW/orca/mb021-1007/MorphBench_original.docx` 经只读字节比较相同。详细领域证据见 [M 测量报告](morphbench-evaluation-1007.md)、[Q 独立核验报告](morphbench-verification-1007.md)，旧 R1 计划不扩展此次授权。

## 版本、合并与安装身份

| 身份 | 精确值 |
|---|---|
| 被测产品 SOURCE / 版本 | `50396909c3fbaa510e755b8e2361e05d84afdfaa` / `morphogenesis==0.2.1` |
| 治理基线 | `89e3c49f32e3bcb57fded741565ec4b3e889d777` |
| M 运行 SOURCE | `b76d5e17c5462209e511a46d29b5a55b146050b7` |
| M 后处理 SOURCE | `a05431259748fdf98340a02e7734ccb934eb35db` |
| M 精确合并目标 REPORT | `3c52e17b44a86b619f7cdfafca5ca7997793ade2` |
| Q 测试 SOURCE | `12479cfa5a058f1dab4413a6464f6d691dec53af` |
| Q 精确合并目标 REPORT | `fbb67d10f9977a00f78a730c9b645f70439031f1` |
| I 最终集成 SOURCE | `bc12c1dd947e80e5e4288efa254c40c84cf1e288` |
| I 分支 | `songconmaisaix31-design/morphbench-integrate-1007` |
| I SOURCE 发布核对 | `origin` 同名分支为上述 SOURCE；当时工作树 clean，见 `integrate/lineage-source.json` |
| I REPORT / 最终 remote / clean | 本报告随后单独 commit；最终三项以完成消息和 `integrate/publication-final.json` 为准，正文不自引用提交 SHA |

I 从治理基线按两个完整 REPORT SHA 依次 `git merge --no-ff`，没有冲突、领域修复或胶水修改；两轨运行/后处理/测试 SOURCE 的祖先关系全部通过。相对产品 SOURCE，集成 SOURCE 只有 `docs/PLAN.md` 的治理修改，以及 `tools/morphbench/**`、`tests/morphbench/**`、`tests/integration/morphbench/**` 和 M/Q 报告新增；I 再仅新增本报告。产品、锁、原断言与 AOCI 索引无变化。

独立验证使用 Q 稳定非 editable 环境 `C:/Users/DW/orca/mb021-1007/verify/venv/Scripts/python.exe`，从 integrate 目录启动，清除产品源码 `PYTHONPATH`，禁止 bytecode 写入。`swarm.worker_loop` 和 `local_assets.validate` 实际来自该环境的 `Lib/site-packages`；版本 0.2.1，`direct_url` 为本地 source 安装、`dir_info={}`，不是 VCS receipt。I 重新对分发中的 **216 个文件**与产品 SOURCE 原始 Git blob 逐字节比较，全部相同。Q 原 `exact-source-comparison.json` 另有 222 个 archive 文件及 1 个原测试副本相同；后二者是 Q 证据，未声称 I 重做。环境未安装、更新或修改。

AOCI MCP 未在本 Run 提供，当前 worktree 无 `.mcp.json`；未取得完整认知收据或维护主仓索引。遵守此次禁止索引写入的边界，只依据指定源码和证据完成审计，不声称索引已刷新。

## Tier B：5 任务 × 3 系统

下表每格为 **最终评价均值 ± SE；完整预算 trial 数/5；实际搜索单元/40**。分数使用全部五个可观测端点，包含 8 个 partial。BM-01..04 是固定合成数据的测试评价；BM-05 是同一数学函数再评价，**没有 held-out 数据、GPT 训练或真实 val_bpb**。

| 任务 / 原始指标 | SingleAgent | CentralScheduler | MorphSwarm / installed Worker |
|---|---|---|---|
| BM-01 / suite Spearman | 0.790824 ± 0.017796；5/5；40/40 | 0.814602 ± 0.002744；5/5；40/40 | 0.812125 ± 0.003459；3/5；38/40 |
| BM-02 / AUROC | 0.985441 ± 0.000573；5/5；40/40 | 0.986014 ± 0；5/5；40/40 | 0.986266 ± 0.000154；4/5；39/40 |
| BM-03 / Accuracy | 0.932500 ± 0.003333；5/5；40/40 | 0.930833 ± 0.002500；5/5；40/40 | 0.932500 ± 0.003333；3/5；38/40 |
| BM-04 / Accuracy | 0.995261 ± 0；5/5；40/40 | 0.995261 ± 0；5/5；40/40 | 0.995261 ± 0；3/5；38/40 |
| BM-05 / 负数学目标 | -1.112888 ± 0.028573；5/5；40/40 | -1.112743 ± 0.028455；5/5；40/40 | -1.113452 ± 0.015394；4/5；39/40 |

partial 均在 Worker：BM-01 seeds 1/4、BM-02 seed 4、BM-03 seeds 1/4、BM-04 seeds 1/4、BM-05 seed 4。未补跑或把缺失执行填成成功。25 个 Worker trial 的 75 个进程均正常退出；进程 exit=0 不等于完成全预算。M 对首 partial 的账本解释是感知/认领争用消耗 energy；没有独立持久化失败 claim reason，故不扩写成已证实的具体内部故障。

为保留完整预算和所有观测端点的区别，完整预算子集另列如下；两个基线的完整子集仍是各五个 trial，数值与上表一致。

| 任务 | Worker 完整预算均值 ± SE | n | 全端点 n |
|---|---:|---:|---:|
| BM-01 | 0.808360 ± 0.004707 | 3 | 5 |
| BM-02 | 0.986171 ± 0.000157 | 4 | 5 |
| BM-03 | 0.936111 ± 0.002778 | 3 | 5 |
| BM-04 | 0.995261 ± 0 | 3 | 5 |
| BM-05 | -1.108489 ± 0.018813 | 4 | 5 |

完整预算配对样本数依次为 3/4/3/3/4；全部 allowance 端点为每项 5 对。两套各十项差值、原始 seed、SE、95% CI 保存在 `eval/summary-b8-s0-4/summary.json` 的 `paired_contrasts` 与 `fixed_allowance_paired_contrasts`，I 重算 `integrate/summary/summary.json` **逐字段完全相同**。M 报告逐项列出了全端点差值/CI。完整子集可能有选择偏差；全端点分析是观察 partial 后增加的描述性分析，不能称预注册。

5 seeds 是分配 seed，实际 Worker RNG 为 `1000 * seed + worker_index`；数据分割和模型 seed 固定。采用配对 allocation-seed bootstrap 10,000 次、RNG 20261007；完整预算十项另做精确双侧 sign-flip 和 BH。五对数据最小双侧 p 为 0.0625；所有 CI 含 0，完整预算 BH q=1，端点表未另声称 BH 结果。零方差或含 0 不证明一般等效。序贯检验未预注册/执行，**NOT_RUN**。

### 预算与测量边界

此次 allowance=8，**不是 Word 默认 24**。Worker 复用原 TaskLedger / RunLimits，三个进程 energy=3/3/2；两个 baseline 为串行分配机制消融，分别是有放回随机搜索与去重分配，不能代表实际 Autoresearch、AutoGen、MetaGPT。

| 系统 | 完整预算/观测 | 搜索完成/上限 | 搜索重复 | acceptance 预计算 | 最终评价 | 全部 evaluate 调用 |
|---|---:|---:|---:|---:|---:|---:|
| SingleAgent | 25/25 | 200/200 | 39 | 0 | 25 | 225 |
| CentralScheduler | 25/25 | 200/200 | 0 | 0 | 25 | 225 |
| Worker | 17/25 | 192/200 | 0 | 525 | 25 | 742 |
| 总计 | 67/75 | 592/600 | 39 | 525 | 75 | 1192 |

Worker 每 trial 的预计算按 BM-01..05 分别为 13/9/12/11/60 次，用于固定 acceptance gold；每 trial 有结果再评价一次。完整 Worker trial 的总调用相应为 22/18/21/20/69，partial 少一次搜索；baseline 各 9。因此只对齐搜索 allowance，**总计算不匹配**，不能据此宣称算力效率或科学优势。

矩阵总调用 1192，其中 BM-01..04 为 758 次 sklearn 拟合、BM-05 为 434 次缓存数学函数调用。机制另有 258 次：38 次拟合与 220 次数学调用；正式合计 1450。M 两个 smoke 另有 123 次数学调用，含原首失败；不并入统计。原 budget24、主控 worker-first 与 Q 控制均独立，不混账。未知真实 tokens/费用不补零，`actual_cost_usd=null`；fixture usage 不是真实模型账单。

I 读取全部 trial JSON、原始 started/finished JSONL、Worker ledger snapshot 和实际 `workspace/cfg/*/result.json`，核对每个已应用分数均来自完成的评价事件，best 取自实际结果而非未执行 gold。预计算与搜索事件数逐项一致，费用空值、实际种子及进程结果一致；审计明细为 `integrate/trials-audit.json`。最终评价值由 driver 在选定 best 后写入 trial JSON，**没有独立 final-evaluation JSONL**；I 核对调用代码和统计引用，没有重拟合或声称独立复算最终分数。固定 gold 验证仍只是夹具一致性，不是独立科学判断。

## Tier A：四项机制

| 项目 | 成立的观测 | 证据范围与剩余缺口 |
|---|---|---|
| SB-01，before_reservation | Q 实际 kill 两个 Worker；自然 TTL 后三个新启动的后继 Worker 完成 **6/6**，旧 submit 无副作用 | `contract_local / mock`；是租约接管控制，非原三活 Worker 连续存活概率；中央调度器真实 kill 对照 NOT_RUN |
| SB-01，after_reservation | Q 实际 kill 两个已预留预算 Worker；恢复为 `unknown_usage`，uncertain=2、pending=0，完成 **0/6**；tokens/estimated/actual cost 均 null | 正确保守停止；不得把两个阶段合并成 survival=1，不重放未知操作 |
| SB-02 | M adapter cold/warm 到目标均为 [5,4,8,3,6]，signed gain=0 ± 0，n=5，无删失；160 次实际评价 | 旧 field DB 复制/adapter 偏好迁移不能代表资产消费与科研经验采用；Q 原9任务有9 assets/reports/approvals，consumptions=0、adoptions=0；**科学经验复用 NOT_RUN** |
| SB-03 | BM-01 同实际配置回放，`Worker wall / serial wall - 1` 为 **22.7842 ± 4.1861**，n=5；回放38次 | 整条搜索 pipeline 增量，含 spawn/Git/SDK/验证/并行及时间顺序，不含 acceptance 预计算；非纯协调开销，非 Word 占位 0.15 |
| SB-04 | trial 内实际搜索重复：Single 39/200=19.5%，Central 0/200，Worker 0/192 | 仅 evaluation 配置重复；不代表所有科研冗余、所有重复外部效果或零争用，预计算和末次评价已另列成本 |

M 原 adapter SB-01 是删除 alive 列表/改变 central 布尔值，5 seeds 共60次数学评价，真实进程 kill=0；不计为真实容错结果。I 只读核对 Q 两组实际 kill JSON、PID/marker 对应、后继完成、费用空值与 stale-submit 结果，未重新 kill。Q 首轮 Windows venv redirector PID 断言失败保留，后继修正测试启动方式，不改产品或原成功判据。

I 逐日志复核机制 258 个 started/finished，重算 SB-02 到目标单元、SB-03 同配置顺序和比值、SB-04 分母，均一致，见 `integrate/mechanisms-audit.json`。Q 真实机制和 Worker 任务结果的 `provenance=mock`、`evidence_class=contract_local` 保留；接口可达属于本地接口观测，不能升级为真实科研 `task_live`。页面自身 acceptance 各档仍为 not_run，不由 I 改写。

## 原始失败、后继验证与产品页面

| 观测顺序 | 原结果 | 原始证据（相对证据根） |
|---|---|---|
| 主控安装态首轮 | **93 PASS / 14 FAIL，exit 1** | `pytest.log`、`pytest.xml` |
| Q 修复 Node 前置后的原 runtime 子集 | **25 PASS / 1 deselected，exit 0** | `verify/original-runtime.log`、`.xml` |
| Q 双 kill / 安装根控制首轮 | **2 FAIL / 1 PASS，exit 1** | `verify/kill-controls-first.log`、`.xml`、同名目录 |
| Q 后继控制 | **3 PASS，exit 0** | `verify/kill-controls-second.log`、`.xml`、同名目录 |
| M 矩阵 / 机制 | **67 PASS + 8 INCOMPLETE，exit 1 / 机制 exit 0** | `eval/matrix-b8-s0-4.exit.txt`、`eval/mechanisms-b8-s0-4.exit.txt` |
| M 统计初版 / 后处理版 | **6 PASS / 7 PASS** | `eval/statistics-first.log`、`eval/statistics-final.log` |
| I 合并后统计 | **7 PASS，0.30s，exit 0** | `integrate/statistics.log`、`.xml`、`.exit.txt` |
| I 独立身份/原数据/机制/HTTP 核对 | **PASS，exit 0**；重算汇总与 M 完全一致 | `integrate/audit.log`、`.exit.txt`、`identity.json`、`trials-audit.json`、`mechanisms-audit.json` |

I 只读复核上述测试 XML 计数；deselected 来自 Q 命令及日志，不伪装成 XML 的 skipped。原14失败包括 SDK 缺失、Windows spawn 的 tests 包导入失败、源码祖先推断与安装根不一致；Q 后继修复环境/测试启动边界，未把首轮改写成全绿。M 首 smoke 的 `ajv` 缺失 / 0 completed / BridgeError 仍保留，后继 smoke 为独立目录。**没有全仓 pytest、mypy、build 或 SDK 工程门通过的本轮结论。**

I 在 **2026-10-07 23:07:31 +08:00** 只读 GET 验证：

| 端点/页面 | 最终观测 |
|---|---|
| `/` | 200；330330 bytes 与产品 SOURCE HTML 原始 blob 完全相同 |
| `/api/health` | 200，PID 41064，实际字段 `service_ready=false`；缺 OBSERVATORY_HOST_CONFIG |
| `/api/swarm` | 200，health partial / mirror missing；3 个已耗尽节点、60 tasks、9 completed 且 applied，mock 来源 |
| `/api/readiness` | 200，overall degraded；machine ok、interface/account not_run；readiness 不是执行验收 |
| `/api/research/package` | **503**，研究服务未就绪 |
| Q 实际页面 / I 只读复核截图 | 主区空白与 Swarm 区域归属异常，**视觉验收未通过**；DOM `swarmAncestorMain=false`、parent=BODY |

原服务未重启、未 seed。CIM 当前 launcher PID 29344 / CreationDate `2026-10-07T22:26:37.7528640+08:00`，listener PID 41064 / parent 29344 / CreationDate `2026-10-07T22:26:38.4504820+08:00` 与 Q 记录一致；交接 launcher 的末尾 100ns 位 `.7528646` 比 CIM 返回更细，本文保留实际读取精度，不声称复核到该位。见 `integrate/server-process-final.json`。

首页 p1/b-soft 等为2024示例内容；Swarm 9/60 是原状态目录的 mock 任务，**不是 M 的 75 trials 或 192 次搜索结果**，矩阵不会自动写入该页面。Q 的真实快照、截图与 DOM 记录在 `verify/browser-*.json`、`verify/browser-swarm*.png`、`verify/browser-layout-observation.json`；I 查看了原截图，没有新增视觉通过声明。页面领域缺陷由主控交产品 Owner，冻结产品本轮不修。

## 官方任务逐项 NOT_RUN 与前置缺口

以下是对原方案完整 Tier A/B/C 与外部对标的映射。官方协议来源与 Q 当日核对详情见 [Q 官方任务接入表](morphbench-verification-1007.md#官方任务接入-readiness)，本地测量范围见 [M 报告](morphbench-evaluation-1007.md)；I 不另行下载数据、联网评分或验证外部宣传成绩。

| 层级/对象 | 本轮状态 | 完整协议尚缺 |
|---|---|---|
| A / SB-01..04 | 以上限定本地机制观测已交付；真实科研容错/复用收益 NOT_RUN | 等资源真实科学工作流、实际经验消费/采用链、中央进程故障对照与可分离协调计时 |
| B / BM-01 ProteinGym | 官方任务 NOT_RUN | DMS/assay 数据版本、规定 split、预测与官方 tied-rank/聚合 scorer；当前 suite 双 argsort 不是官方 ties 处理 |
| B / BM-02 TDC ADMET | 官方任务 NOT_RUN | 指定数据集、版本、scaffold split、对应指标；不能把所有 ADMET 一律当 AUROC |
| B / BM-02 Polaris | 官方任务 NOT_RUN | 药物发现 benchmark ID、数据/访问与 evaluation/submission adapter |
| B / BM-03 Open Problems | 官方任务 NOT_RUN | AnnData 与标签、指定 release、跨 batch 划分、官方处理/metric 环境 |
| B / BM-04 Kaggle/BioML 影像 | 官方任务 NOT_RUN | 具体赛题 ID、数据授权与 split、任务相关 scorer、私榜/参考分布 |
| B / BM-05 nanochat/autoresearch | 官方任务 NOT_RUN | 语料/tokenizer、训练入口、GPU、真实 val_bpb 评估和明确资源授权 |
| B / BioML-Bench 完整官榜 | NOT_RUN；百分位不可计算 | 原完整任务集、容器/提交/grade、隐藏测试与对应人类提交分布；合成5任务不足以对齐 |
| C / MLR-Bench、MLR-Judge | NOT_RUN | 正式任务、代码/实验/论文产物、九维 judge、专家校准与需要的调用授权 |
| C / ScienceAgentBench VER/SR/CBS | NOT_RUN | verified 数据/artifacts、正式程序、隔离 harness、实际执行与需要的 judge/CodeBERT 评分 |
| 外部 / MLE-bench | NOT_RUN | 竞赛数据、任务执行器、submission、官方 grading 与同资源协议 |
| 外部 / PaperBench | NOT_RUN | 论文/rubric、代码提交、复现实验、容器、GPU 与 judge |
| 外部 / RE-Bench | NOT_RUN | 原任务环境、资源/时限、评分与人类基线对应 |
| 外部 / Sakana AI Scientist v2 盲审 | NOT_RUN | 实际论文及独立盲审、相应实验协议 |
| 外部 / Adaption AutoScientist | NOT_RUN | 同一垂直任务集、人工配置、模型与资源、原比较协议 |
| 外部 / EvoMap AutoResearch | NOT_RUN | 同问题/资源、实际产物、实验与独立验证链；Word 宣传数字不迁移为本系统成绩 |
| R1 AT-07 / L2、真实 LLM 科学质量 | NOT_RUN | 既有隔离/授权门、明确问题/材料/资源及科研执行与验收 |

原 suite 的 median/p75/p90/sota 人工锚点不能冒充官方人类分布；仅替换数据加载器不会自动形成同款官榜结果。关键词判官或调用方给定的布尔执行结果也不构成官方科学评分。本报告不引用外部产品分数为已核实比较结果，方案引用修正沿用 Q 的来源说明。

## 复现命令与证据索引

证据根：`C:/Users/DW/orca/mb021-1007/`。原 `eval/`、`verify/`、主控旧产物只读；I 新输出全部位于 `integrate/`，没有 runtime 证据入库。私有 suite 未获再分发许可，仓库工具并非独立完整数据包。

I 本次实际执行的关键命令（PowerShell）：

```powershell
git merge --no-ff 3c52e17b44a86b619f7cdfafca5ca7997793ade2 -m 'merge: exact MorphBench measurement report 3c52e17'
git merge --no-ff fbb67d10f9977a00f78a730c9b645f70439031f1 -m 'merge: exact MorphBench verification report fbb67d1'
git diff --name-status 50396909c3fbaa510e755b8e2361e05d84afdfaa bc12c1dd947e80e5e4288efa254c40c84cf1e288
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
$benchPy='C:/Users/DW/orca/mb021-1007/verify/venv/Scripts/python.exe'
$benchRepo='C:/Users/DW/orca/workspaces/Morphogenesis/morphbench-integrate-1007'
Set-Location C:/Users/DW/orca/mb021-1007/integrate
& $benchPy -B -m pytest -q -o addopts= -p no:cacheprovider "$benchRepo/tests/morphbench/test_statistics.py" --basetemp ./pytest-temp --junitxml ./statistics.xml
& $benchPy -B "$benchRepo/tools/morphbench/summarize.py" ../eval/matrix-b8-s0-4 --output ./summary
& $benchPy -B ./audit.py
```

这些输出已存在，后续复核须使用新目录；`audit.py` 用 exclusive-create 保存输出，只是此次本地只读核账脚本，不是产品证明系统。统计与汇总命令 stdout/exit 已分别保存。I 辅助打印已有 HTTP JSON 时曾因默认 GBK 解码失败，改为显式 UTF-8 后读完，未改原数据；不涉及主审计或统计测试失败。原矩阵和机制的重跑命令见 [M 复现说明](../../tools/morphbench/README.md) 及 M 报告；I 本轮未重跑拟合、kill、真实科研或任何付费任务。

| 证据路径 | 内容 |
|---|---|
| `eval/matrix-b8-s0-4/arguments.json`、`environment.json` | 原75组合、budget、seed、安装身份 |
| `eval/matrix-b8-s0-4/BM-*/result.json`、`*.jsonl` | 原逐 trial 结果、搜索/预计算事件 |
| 同 trial 的 `ledger-snapshot.json`、`workspace/cfg/*/result.json`、`state/` | 已应用结果、原账本与运行状态，保持原件 |
| `eval/summary-b8-s0-4/summary.{json,md}` | 两套配对统计、coverage 与全部 trials |
| `eval/mechanisms-b8-s0-4/` | SB 原日志、adapter 状态、同配置回放与结果 |
| `verify/kill-controls-first*`、`verify/kill-controls-second*` | 双 kill 原首失败与后继边界证据 |
| `verify/exact-source-comparison.json`、`asset-consumption-observation.json` | Q 原字节/资产链核对 |
| `integrate/identity.json`、`lineage-source.json` | I 216字节比较、身份、精确祖先与 diff |
| `integrate/trials-audit.json`、`mechanisms-audit.json`、`summary/` | I 独立核账、新目录汇总 |
| `integrate/http-final.json`、`http-*.json`、`http-root.html`、`server-process-final.json` | I 只读 HTTP、原页面字节与进程身份 |
| `integrate/statistics.*`、`audit.*`、`summary.*`、`publication-final.json` | 本次命令结果与最终发布身份 |

本轮完成的是上述评测交付与独立集成。未执行全仓工程门、官方任务/官榜提交、真实模型科学评审、完整科学经验采用、序贯检验、AT-07/L2、云/GPU/付费调用或页面领域修复。需要人工/原 Owner 后续完成的是分别确定官方数据、许可、指标、预算和资源授权，处理产品页面/HostConfig 前置，并在独立批准范围运行；不能通过改历史断言、补 seed 或重放未知执行把这些状态变绿。服务和 M/Q 原终端均保留，资源 release 由主控处理。
