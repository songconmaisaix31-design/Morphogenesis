# MorphBench 0.2.1 独立核验

2026-10-07，Q Worker，Task `task_e851ab515e11` / Dispatch `ctx_45d6a1096a05`。本报告依据用户 `C:/Users/DW/Downloads/MorphBench_对标评测方案.docx`、Dispatch 与 `docs/PLAN.md:339` 的本轮计划；旧 R1 规划不扩展本轮授权。

结论：指定 0.2.1 安装态的租约接管、旧 token 拒绝、未知费用停止在限定夹具控制中得到验证；产品 HTTP 和 Swarm 数据接口可达，研究服务未配置，页面视觉布局有缺陷。官方科研任务与真实科研评分全部 `NOT_RUN`。Q 没有复跑 M 的 BM/SB 多 seed 数据，不以本报告替代 M 最终数据或 I 独立集成验收。

## 版本与写入范围

| 身份 | 精确值 |
|---|---|
| 被测产品 SOURCE | `50396909c3fbaa510e755b8e2361e05d84afdfaa`，`morphogenesis==0.2.1` |
| 本轮治理基线 | `89e3c49f32e3bcb57fded741565ec4b3e889d777`；计划在文件末尾，不是顶部 |
| Q 测试 SOURCE | `12479cfa5a058f1dab4413a6464f6d691dec53af` |
| Q 分支 | `songconmaisaix31-design/morphbench-verify-1007` |
| Q REPORT | 本文件的 docs-only 提交；完整 SHA 由交接消息和 `git log -1 -- docs/tracks/morphbench-verification-1007.md` 给出，避免自引用 |
| 已审核 M 运行 SOURCE | `b76d5e17c5462209e511a46d29b5a55b146050b7`；后续汇总展示修正是独立版本 |

只新增 `tests/integration/morphbench/test_installed_worker_boundaries.py` 和本报告。原产品源码、锁、共享 venv、suite、主控文档及他人 `artifacts/morphbench` 未修改。私有运行资产均在 `C:/Users/DW/orca/mb021-1007/verify/`（下文简称 `verify/`）。没有新建调度器、账本或完成证明系统。AOCI 工具未提供，当前 worktree 无 `.mcp.json`；未改认知索引，不声称完成维护。

## 安装与精确源码

共享原环境 `C:/Users/DW/orca/mb021-1007/venv` 是非 editable 本地源安装。首轮探针的实际导入来自其 `Lib/site-packages`，Node v24.16.0 / npm 11.13.0 已在 PATH，但已安装 `bridge_node/asset_bridge.mjs` 的祖先路径没有 npm 依赖。`NodeAssetBridge.canonicalize` 首次返回 `sdk_process_failed`；直接 Node stderr 明确为 `ERR_MODULE_NOT_FOUND: Cannot find package 'ajv'`，见 `verify/installed-probe-first.json`。在 `source` 下安装 Node 包不能使安装态 ESM 自动解析到它们。

有界环境修正：在 `verify/venv` 新建 Python 3.12.13 环境，用共享环境的精确 freeze 非 editable 安装同样的 97 包；将原 `package.json` / `package-lock.json` 复制到 `verify/` 后执行锁安装。M 获准只读复用该稳定环境；Q 不再修改它。

```powershell
uv venv --python C:/Users/DW/orca/mb021-1007/venv/Scripts/python.exe C:/Users/DW/orca/mb021-1007/verify/venv
uv pip freeze --python C:/Users/DW/orca/mb021-1007/venv/Scripts/python.exe
uv pip install --python C:/Users/DW/orca/mb021-1007/verify/venv/Scripts/python.exe --no-deps -r C:/Users/DW/orca/mb021-1007/verify/frozen-installed.txt
# cwd = C:/Users/DW/orca/mb021-1007/verify
npm ci --ignore-scripts --no-audit --no-fund
uv pip check --python C:/Users/DW/orca/mb021-1007/verify/venv/Scripts/python.exe
```

Python 安装 exit 0；npm 安装 exit 0 / 99 packages；pip check 97 包全部兼容；同一 `NodeAssetBridge.canonicalize({'x':1})` 后继调用成功。日志为 `install-python.log`、`install-node.log`，环境清单为 `frozen-installed.txt`。这证明所需前置补齐，不代表源码安装本来就完整。

`verify/exact-source-comparison.json` 保存对 Git 原始 blob 的直接字节比较：216 个安装分发文件、222 个源副本文件、1 个原 runtime 测试副本全部一致，0 missing / 0 mismatch。覆盖 `swarm/worker_loop.py`、`task_ledger.py`、`budget.py`、`lease.py`、资产存储/消费与 Node 桥。`direct_url.json` 是 `file:///C:/Users/DW/orca/mb021-1007/source` 且 `dir_info={}`，不是 editable，也不是 VCS receipt；精确 Git 身份来自另做的字节比较，不从包版本推断。

另由 `verify/served-source-comparison.json` 核对实际提供页面的 `src/env-observatory/env-observatory.html` 和 `server.py` 均与 50396909 原 blob 一致，HTTP `/` 的 330330 字节也与前者完全一致。未把文档 HEAD 89e3c49 或 Q 测试 HEAD 当作产品改版。

## 原失败与后继验证

| 次序 | 命令/范围 | 原始结果与证据 |
|---|---|---|
| 主控首轮 | 私有原 venv pytest：`test_worker_runtime.py test_worker_renewal_v01.py test_budget.py test_ledger.py test_lease.py test_router.py` 与 `tests/observatory/test_server.py` | **93 PASS / 14 FAIL / 3 warnings，225.05s，exit 1**；根目录 `pytest.log` / `pytest.xml`，Q 不覆盖、不重复此组 |
| 安装环境后继 | 原 runtime 测试原字节复制到 `verify/original-tests/tests/swarm`；仅使该 tests 包可被 Windows spawn 导入，产品仍从 installed site-packages 导入 | **25 PASS / 1 deselected，87.83s，exit 0**；`original-runtime.log` / `.xml` |
| Q 控制首轮 | 新测试的两组双 kill 与 installed 根目录保护 | **2 FAIL / 1 PASS，84.21s，exit 1**；`kill-controls-first.log` / `.xml` / `kill-controls-first/` |
| Q 控制后继 | 修正 Q 子进程启动对 Windows venv redirector 的处理，原断言不降低 | **3 PASS，59.36s，exit 0**；`kill-controls-second.log` / `.xml` / `kill-controls-second/` |

首轮 14 失败的诊断分开：12 项在资产发布相关路径受缺失 SDK 阻断；actual-worker-kill 项在 Windows spawn 子进程先报 `ModuleNotFoundError: No module named 'tests'`，没有进入期望控制点；own-repository 项用测试文件祖先推断源码根，与非 editable 安装的产品根不同。原测试失败保持原样，不能称安装态全套 107 项通过。

后继 runtime 命令：

```powershell
# cwd = .../mb021-1007/verify；original-tests 只含原 runtime 测试及空 tests/__init__.py、tests/swarm/__init__.py
$env:PYTHONPATH='C:/Users/DW/orca/mb021-1007/verify/original-tests'
$env:PYTHONDONTWRITEBYTECODE='1'
& ./venv/Scripts/python.exe -m pytest -q --import-mode=importlib ./original-tests/tests/swarm/test_worker_runtime.py -k 'not runtime_refuses_own_repository_and_state_before_mutation' --basetemp ./original-runtime-temp --junitxml ./original-runtime.xml
```

唯一 deselected 的原断言没有改写；Q 新测试显式使用当前 `swarm.worker_loop.__file__` 的安装根，验证 target/state 在真实 package root 内均先拒绝且不创建状态目录。source archive 不是 installed package root，不拿不同路径语义强行合并结论。原 tests 副本字节已与 50396909 对上；未将产品源码根放入 PYTHONPATH。

原 25 PASS 包括实际单 Worker kill 后自然 TTL 接管与旧 submit 拒绝、未知 usage 保留、续租、审批间隙、finalization 恢复等原行为测试。没有执行全仓 pytest、mypy、SDK 工程门、构建或官方科研判官，不能外推全仓绿。

## 双 Worker 实际进程控制

复现需使用新的 basetemp 和证据目录，脚本用 `open('x')` 拒绝覆盖旧观测。以下是已执行的后继命令；再次复现须更换 `second` 后缀。

```powershell
# cwd = C:/Users/DW/orca/mb021-1007/verify；无产品源码 PYTHONPATH
$env:PYTHONDONTWRITEBYTECODE='1'
$env:MORPHBENCH_EVIDENCE_DIR='C:/Users/DW/orca/mb021-1007/verify/kill-controls-second'
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
& ./venv/Scripts/python.exe -m pytest -q --import-mode=importlib C:/Users/DW/orca/workspaces/Morphogenesis/morphbench-verify-1007/tests/integration/morphbench/test_installed_worker_boundaries.py --basetemp ./kill-temp-second --junitxml ./kill-controls-second.xml
```

| 控制 | 真实 kill / 时点 | 实际结果 | 可成立的结论 |
|---|---|---|---|
| before_reservation | 两个独立 Worker，PID 42160 / 35352；`FixtureExecutor.bound` 中持有租约、未 reserve；marker epoch 1791384165.857075 / 1791384166.880144 | 两 killed exit=1；2 个待接管租约自然 TTL 过期；随后启动三本地作用域 Worker，PID 28696 / 17444 / 42844，均 exit=0、各完成2，共6/6，原两个任务 token 1→2；旧 submit 回调零执行 | 无未知执行费用的过期租约允许合法后继接管；不是原三活 Worker 中的连续存活实验，第三作用域 Worker 在 kill 后才启动 |
| after_reservation | 两个独立 Worker 在 executor.execute 入口持有预算预留后被 kill；精确 PID/time/租约见 `two-kill-after_reservation.json` 与 config/marker 文件 | 同身份恢复各自 hold，`uncertain_reservations=2`、`pending_reservations=0`、tokens/estimated_cost/actual_cost 均 null、`reason=unknown_usage`；0/6 完成，新 worker 也 sleeping | 未知执行效果与费用不被 lease 到期消除；没有自动重试、人工 release/reset 或伪造结算 |

两组都保留 marker、配置、stdout/stderr、lease token/expiry、结果和私有 SQLite。`two-kill-before_reservation.json` / `two-kill-after_reservation.json` 的 `runtime_file` 均指向 verify installed 包。只调用拥有的 `Popen` 进程句柄 kill，实际 child marker PID 与句柄 PID 相等后才执行；不是按陌生 PID 或进程名杀进程。CreationDate 当时未采集，如实缺失；marker 的时刻是到达控制点时间，不冒充创建时间。

首轮 Q 脚本把 Windows venv redirector PID 当作真实 Python PID，marker 身份断言拒绝继续；日志中的 22600≠39460、28288≠28452 是这个失败。后继按 CPython 3.12 `multiprocessing.popen_spawn_win32` 的 bpo-35797 做法，使用 base executable 配 `__PYVENV_LAUNCHER__` 保持同一 venv并直接拥有真实进程句柄（参考来源：本机 CPython 标准库，PSF License）。不改产品、租约 TTL、预算策略或成功断言。首轮和后继观测保留在不同目录；后续只读进程核对未发现 Q 控制 child 残留。

这些是 `contract_local` 的真实本地进程机制证据，executor、输入和 usage 都是 `mock/fixture_mock`，`task_live=NOT_RUN`。不能将两个不同阶段的结果合并为普适“survival=1.0”，也不能代表大规模 BM 任务、真实模型故障或网络分区。Q 机制测试结束后已向 M 交付 CPU 静默窗口；之后未再跑拟合、pytest 或机制控制。

## 产品启动与真实页面

保留地址：<http://127.0.0.1:8099/>；Swarm 路由：<http://127.0.0.1:8099/#/swarm>。Q 接管后无需重启，没有终止其他终端。launcher PID 29344 / CreationDate `2026-10-07T22:26:37.752864+08:00`，health 返回 listener PID 41064，CIM parent=29344 / CreationDate `2026-10-07T22:26:38.450482+08:00`；完整命令与身份见 `verify/server-identity.json`。原 `server-process.json`、`server.*.log`、`http-*` 保留不覆盖。

| HTTP/浏览器观测 | 结果与边界 |
|---|---|
| `/` | HTTP 200，提供 50396909 原 HTML；页面标题 Dashboard · Morphogenesis |
| `/api/health` | HTTP 200；`service_ready=false`，`OBSERVATORY_HOST_CONFIG 未设置` |
| `/api/research/package` | HTTP 503，科研服务没有就绪；没有为变绿运行 seed 或造研究成果 |
| `/api/readiness` | HTTP 200；overall degraded，machine ok，interface/account not_run；readiness 不是执行验收 |
| `/api/swarm` | HTTP 200，health partial（mirror missing）；3 注册节点、60 任务、9 completed且effect_applied；原任务 `mock/contract_local` |
| Orca 导航 | 通过真实导航点击 Swarm；DOM明确显示3终止态节点，各 completed3，在线0，租约0；显示真实状态目录与mock来源 |
| 首页 | 展示 p1/b-soft 等2024示例任务和专家意见；页尾 completion_claim=false 不足以把这些变为真实科研；不是本次9/60的研究结果 |
| 视觉 | **未通过完整视觉验收**。首屏主区域空白，Swarm区滚动/全页截图出现空白与重复导航；实际DOM `view-swarm.closest('main')=false`、parent=BODY，块落在主内容区外。已交主控，产品冻结未修 |

Orca 使用 `orca-cli` 当前运行版本的 browser 指南，保留 page ID `5222eb88-9226-4fd1-a371-1f129ee8ef65`；没有用外部浏览器替换证据。`browser-home.json`、`browser-swarm-after-click.json`、`browser-final.json` 是快照；`browser-swarm.png`、`browser-swarm-scrolled.png`、`browser-swarm-full.png` 是实际查看的截图；`browser-layout-observation.json` 是只读 DOM 几何/归属核对。截图呈现异常与DOM能读取数据分开记，未将接口可达升级为视觉通过。

## SB 指标与原资产链

| 项目 | 独立审核 |
|---|---|
| SB-01 | 原 `real_swarm.py:182` 是中心 for 循环轮流选 `alive` 列表中的 worker，kill为pop；central是布尔变量变false。两者都没有实际进程kill。Q提供上述真实双kill限定事实，原声明的普适生存率及中心进程丢失对照仍未验证 |
| SB-02 | 原 field DB copy 只转移派生偏好，不构成原资产已消费、输出已采用。交接9任务状态只读SQL观测：9 assets/9 reports/9 approvals，consumptions=0、adoptions=0；9条audit的consumed_asset_ids均空，actual_cost均null。见 `asset-consumption-observation.json`；科学经验复用增益 `NOT_RUN` |
| SB-03 | M用已实际执行的 BM01 config序列做串行重放，并把spawn/Git/SDK/validation及并行差异计入pipeline墙钟增量；可作本机描述性结果，不能称纯协调开销或沿用Word占位0.15 |
| SB-04 | M按每task/seed的实际evaluation_finished重复config计数；prefit与final evaluation另计。不是不分阶段的“总科研冗余率”，更不证明避免所有重复外部效果 |

产品有 `test_assets.py::test_approved_fetch_applicability_injection_actual_execution_and_adoption` 检验实际消费/验证/完成效果/采用，Q本轮**未执行**它；已有测试的存在不替代本次SB-02数据。若后续正式验收SB-02，必须在任务结果、consumed_asset_ids、validation report和adoption之间得到同一条可核对链，且比较等资源的冷/热轮。不能用copy DB或注入上下文本身声明科研继承成功。

## M 运行源码与科学口径审计

只读审核 M `b76d5e17...` 的 `run_local.py`、`summarize.py`、`mechanisms.py`、README。可接受范围是**搜索 allowance相同的本地合成任务和机制消融**，不是全计算预算匹配，更不是同款官榜复现：

- 真 Worker路径确实用spawn的独立 `Worker.run`，非旧轮转引擎。driver执行身份检查要求非editable且site-packages导入；Q提供精确字节补证。
- search总预算8，energy按3/3/2分配，TaskLedger既有 `RunLimits(max_attempts=8)`；争用消耗energy导致不足8则INCOMPLETE，不补worker、不重跑。与Word默认24不是同一协议，应显示差异。
- M修正了原suite仅把seed写入swarm_id的问题：worker RNG实际为`seed*1000+i`。数据/模型seed仍固定；五个allocation seed不代表五个独立数据集，也不消除异步调度/墙钟衰减差异。
- 原 `seed_workspace` 为每个配置先算gold并放入ValidationPolicy/`executor_spec.json`：BM01–05分别13/9/12/11/60次预计算。M保留并单列成本，成功trial再做1次final evaluation；预算8仅搜索阶段，MorphSwarm总调用22/18/21/20/69，串行baseline各9。BM05是带cache的数学函数，不是GPT训练，更没有独立测试集。
- 返回分数从已应用result.json读取，再与executor evaluation事件交叉核对；没有将未执行gold当作已执行结果。但精确gold验证只证明固定结果符合预置事实，不证明科研发现或独立科学判断。
- token用固定USAGE，cost使用fixture价格；真实cost为null，不能称实际LLM成本或节省。
- SingleAgent是有放回随机配置搜索，central是串行去重分配；不是实际Autoresearch、AutoGen或MetaGPT代理。任务级分数不能用来声称胜过这些产品。
- summary使用完整预算trial做配对差值、固定seed10000次bootstrap和精确双侧sign-flip，BH为探索性调整；5对时最小非零双侧p为0.0625，不足以支持p<0.05；样本数减少须显式报告。序贯检验没有预注册/执行，维持NOT_RUN。
- SB02应保留负增益与未达标删失，不把负数裁零或没达到目标替换成预算值；M脚本已做到。其固定加性扰动目标/参考选择依然只属于adapter实验。

已给M两项Handoff并收到接受：汇总列 `Held-out mean` 改为 `Final evaluation`，BM05明确无独立test；依据arguments显式展示expected75、observed与missing NOT_RUN，不能只枚举已有文件。M承诺仅后处理修正、保留b76运行SOURCE、不重跑。本报告不预先宣称这些后继修改已交付，I须核对实际后处理SHA和表格。

原suite自造median/p75/p90/sota锚点线性插值不是公开人类提交分布，换真实数据也不会自动变为官方百分位。BM01 `_spearman` 对ties使用双argsort而非平均秩，亦需在正式数据入口改用官方评测；Q不改suite以刷分。Tier C `heuristic_judge` 根据长度/关键词/数字打分，`execution_verdict`接收调用方布尔值和相似度；没有执行官方judge或CodeBERT模型，不输出官方质量成绩。

## 官方任务接入 readiness

2026-10-07 只读核对下列官方原始来源。下表本地缺口仅针对本轮交付的source/suite/verify环境，没有全盘搜索用户其他科研数据，也没有下载受限数据、建立科研沙箱、启动模型或执行外部评分。

| 对标 | 官方契约/来源 | 本轮缺口与状态 |
|---|---|---|
| BM01 ProteinGym | [官方仓库](https://github.com/OATML-Markslab/ProteinGym)：217 substitution assays；supervised/zero-shot、CV与UniProt/功能类别聚合需分别固定 | 当前是合成回归，缺官方DMS数据、规定划分、模型/预测文件与官方聚合；**NOT_RUN** |
| BM02 TDC | [ADMET官方协议](https://tdcommons.ai/benchmark/admet_group/overview/)：scaffold split，20% held-out；AUROC/AUPRC/MAE/Spearman随任务变化 | 缺指定数据集/版本/split/官方metrics；不能把所有ADMET统一当AUROC；**NOT_RUN** |
| BM02 Polaris | [Polaris药物发现官方文档](https://polaris-hub.github.io/polaris/stable/)：benchmark对象与其资源、协议、评测接口 | 缺benchmark ID、数据与访问、官方evaluation/submission adapter；**NOT_RUN**。不是同名视觉Polaris-Bench |
| BM03 Open Problems | [Label Projection官方任务](https://www.openproblems.bio/benchmarks/label_projection/)：跨训练/测试batch投射标签，Accuracy与多种F1，版本化任务 | 缺AnnData数据、指定release、官方处理/方法/metric组件与执行环境；当前合成4分类；**NOT_RUN** |
| BM04 Kaggle/BioML | 未指定具体赛题不能确定输入/指标；例如[RSNA官方页](https://www.kaggle.com/c/rsna-pneumonia-detection-challenge/overview)使用IoU阈值下的检测评分，并非Accuracy | 缺具体competition ID、数据许可/下载、split、官方评分与榜单快照；**NOT_RUN** |
| BioML-Bench整套 | [官方仓库](https://github.com/science-machine/biomlbench)：prepare → agent submission → grade；依赖任务数据与容器执行。 [AutoScientists官方页](https://autoscientists.openscientist.ai/)所报24任务百分位参照公开人类提交/隐藏test | 缺24原任务、容器adapter、submission/grade与对应人类榜单分布；合成5任务不能比74.40%；**NOT_RUN** |
| BM05 nanochat/autoresearch | [官方autoresearch](https://github.com/karpathy/autoresearch)：固定5分钟训练预算、val_bpb、单NVIDIA GPU，数据/tokenizer准备独立 | 当前数学函数无训练；缺语料/tokenizer、GPU、训练与官方eval入口及科研授权；**NOT_RUN** |
| Tier C MLR-Bench | [官方仓库](https://github.com/chchenhui/mlrbench)：201任务、四阶段agent与官方MLR-Judge入口 `mlrbench/evals` | 缺正式任务/代码与实验/论文产物、judge配置与执行、专家校准；关键词判官不替代；**NOT_RUN** |
| Tier C ScienceAgentBench | [官方仓库](https://github.com/OSU-NLP-Group/ScienceAgentBench)：102任务；2026-04-30要求verified split/`benchmark_verified.zip`，正式程序产物、隔离evaluation及部分可视化judge | 缺verified数据/artifacts、pred_programs、环境/harness、需用到的judge配置；VER/SR/CBS均无真实评分；**NOT_RUN** |
| MLE-bench | [官方仓库](https://github.com/openai/mle-bench/)的竞赛数据准备与官方grading，需固定benchmark版本与资源协议 | 没有75竞赛数据/执行器/submission/grading；**NOT_RUN**。官方README还提示榜单新提交暂停，不能假设当前可直接上榜 |
| PaperBench | [官方当前实现](https://github.com/openai/frontier-evals/blob/main/project/paperbench/README.md)：20篇ICML论文、LFS数据，agent/reproduction/grading三个隔离阶段，复现阶段GPU | 缺论文rubric数据、代码提交、复现实验、容器与judge；**NOT_RUN** |
| RE-Bench | [METR官方仓库](https://github.com/METR/RE-Bench)：7任务，METR Task Standard与Vivaria设置 | 缺官方任务环境/资源、评分、相同时间预算和人类基线对应；**NOT_RUN** |
| Sakana AI Scientist v2 | [官方论文盲审实验说明](https://sakana.ai/ai-scientist-first-publication/) | 无论文产物、独立评审和对应实验协议；**NOT_RUN**；不是可由本地rubric模拟的官榜 |
| Adaption AutoScientist | [官方报告](https://adaptionlabs.ai/blog/autoscientist)比较特定数据/垂直领域/model training设置 | 缺同一任务集、人工配置与模型资源、原协议；48→64胜率不可迁移；**NOT_RUN** |
| EvoMap AutoResearch | [官方研究说明](https://evomap.ai/research/autoresearch-evidence-loop)描述生成、实验、独立验证链 | 缺同一问题集、资源、产物、独立验证记录；Word的2584/14未在本次读到页面中核实，不引用为已证实成绩；**NOT_RUN** |

方案的两个具体引用/统计修正：PaperBench应为 [arXiv:2504.01848](https://arxiv.org/abs/2504.01848)，文中 `2502.16069` 实为 [Curie](https://arxiv.org/abs/2502.16069)。Sakana官方说明6.33来自提交3篇中的1篇，另2篇未达到接受线，不能写作整个系统/三篇均值；该篇按事先协议撤回，也不能映射为MorphBench论文通过。

## 交接与剩余操作

Q测试SOURCE已正常push，报告随后单独commit/push；最终精确远端/clean状态由完成消息给出。产品页面保持本次进程与原状态目录，未启动真实沙箱、AT-07、付费科研、云GPU、官方benchmark任务或新HostConfig。

最终只读检查在 2026-10-07 22:54:39 +08:00 确认 `/`、`/api/health`、`/api/swarm` 均为200，launcher/listener的PID、父子关系与CreationDate均与接管时一致，见 `verify/server-final.json`。22:55:01 的 `verify/process-final.json` 核对所有Q双kill marker PID均已退出，未发现Q控制命令子进程；Orca仍停在上述Swarm页面。

领域Handoff：页面示例数据及Swarm DOM/视觉布局缺陷交主控转产品Owner；原安装路径缺少Node依赖作为部署前置保留；M两项展示口径修正等待实际后继SHA；I核对M最终expected/observed/NOT_RUN表和原始数据。本轮不把这些限制全部算通过，也不为补字段重放未知执行。
