# MorphBench 真实 Swarm 测评集成报告

2026 年 10 月 8 日 · Morphogenesis · 独立集成 I

## 本轮结论

**本轮目标未全部完成。** 本次交付整合了前轮 75 个合成试验、A 的有限核心优化、B 的真实调用部分结果及 F 的页面修复。B 的四类真实测评在一次 ConnectTimeout 后按冻结协议停止，结算为 failed；本报告和工程集成交付不能改变这个结果。

真实调用只覆盖 seed 0 的四个局部代码单元。23 次请求意图中，22 次明确 HTTP 200，且逐条通过独立固定测试、完成受 fencing 约束的应用；1 次效果和用量未知，保留 CNY 0.1 预留。另有 legacy 的 1 道到达任务未尝试。动态能力反转、正式跨 session 经验收益、正式进程故障恢复均未执行，未证明算法优势。

| 读者需要区分的结果 | 当前结论 |
|---|---|
| 实际到达与解决 | 24 道代码任务到达，22 解决，1 未尝试，1 unknown；固定分母 22/24 |
| 计划代码覆盖 | 12 个代码单元只观察 4 个；72 道计划任务中到达 24 道，解决 22 道 |
| 全部代码与动态单元 | 4/24 已观察，20/24 NOT_RUN；经验与四故障正式批次亦 NOT_RUN |
| 费用 | 已知 12830 tokens 的原价估计小计 CNY 0.0170944；完整 tokens、完整估计、实际账单均 null |
| 前轮合成矩阵 | 75/75 有记录，67 PASS、8 INCOMPLETE；矩阵原退出码 1 保留 |
| 工程与页面 | 独立安装、类型、构建及适用回归成立；最终页面复验见后文，不等于科研验收 |

四系统共用 A 新执行器，这是机制消融。legacy 使用 cycle/v0，successor 使用 claim/v0.1，同时改变能量计费与路由策略，无法独立归因路由。各系统仅一个 allocation seed，退化 bootstrap 区间不能支持科学推断。Single 和 Central 的耗时还受到主机内存干预污染，不能据秒数宣称效率优势。

本报告的 Markdown 是唯一正文源，同内容导出中文 DOCX。旧证据根 `C:/Users/DW/orca/mb021-1007` 与新轮其他轨目录只读保留；I 的新证据仅写入 `C:/Users/DW/orca/mb-live-1007/integrate`。I 新模型调用为 0。

## 评测范围与独立证据

原方案为 `C:/Users/DW/Downloads/MorphBench_对标评测方案.docx`，本轮已读取全文。它要求 Tier A 四机制、Tier B 五科研任务、Tier C 开放式研究对接；默认预算 24 单位、正式发布至少 5 seeds、相同预算、bootstrap 与 FDR，并提出序贯检验。其样例数字和外部产品宣传分数不是本系统已验证成绩。

本轮追加授权由 `docs/PLAN.md` 的后继执行页限定为动态热点与能力反转、真实代码缺陷、经验复用和租约故障。B 冻结协议改为 3 个 allocation seeds、4 系统及有界真实请求，不能与原方案的 5 seed 发布目标混称已达标。唯一正式批次绑定 A 产品 SOURCE、B 工具 SOURCE 和主控窗口 `msg_4e6d99d6cf88`，本次独立从 arguments.json 核对一致。

三种证据维度分别保留。contract_local 是固定夹具或本地契约证据；interface_live 描述真实提供方接口；task_live 描述对应任务的实际验证与应用。22 个成功任务的 worker/ledger 旧字段仍为 `evidence_class=contract_local`，原 worker_audit 同时保留 `evidence_class=interface_live`、`provenance=live` 和独立 `task_live=passed`。它们不是可互相覆盖的单一等级。

I 使用 SQLite `mode=ro&immutable=1`，逐条核对 24 个到达任务及 23 份请求/响应，未调用产品写入构造器。22 个成功均同时满足 completed、effect_applied、匹配 worker/fencing token、关联验证报告 passed、固定 policy 与隔离字段、对应 approval、HTTP 200 与相同 provider request ID；实际 target 文件与报告候选的 after 字节一致。I 未重跑模型或修改账本。

独立验证器为安装产品的 `bootstrap.acceptance_runner`，policy 为 sample-tests-v1 / fixed-sample-v1，隔离字段为 fixed_pure_sample_subprocess。测试未送给本次模型，也未放入可修改目录；公开仓库内容是否进入训练数据不可知。AST 白名单、纯函数检查和 Python `-I -S` 不等于完整操作系统沙箱、任意代码执行安全或 AT-07。

## 真实调用成绩与计划覆盖

这是 clamp、mean、unique 三族纯函数的六个本地缺陷任务。不是 SWE-bench、一般工程仓库修复、真实科研论文、BM-05 GPT 训练或官方榜单评测。

| 系统 | 解决/到达 | 请求意图 | 已知 tokens | 完整 tokens/解决 | 单元秒数 |
|---|---:|---:|---:|---:|---:|
| Single | 6/6 | 6 | 3515 | 585.83 | 426.017 |
| Central 串行 | 6/6 | 6 | 3500 | 583.33 | 75.651 |
| legacy cycle/v0 | 5/6 | 5 | 2899 | 579.80 | 28.986 |
| successor claim/v0.1 | 5/6 | 6 | 2916 | null | 40.877 |

Single 每题为新的 Worker 身份/进程；Central 是单 Worker 串行；两蜂群各 3 Workers。所有系统使用同模型、固定独立验证和共享流程预算口径。表中的 22 次已知响应均解决对应任务；这个条件性 22/22 不代替包含未知和未尝试的 22/24 固定到达分母。

legacy 的 t02-mean-denominator 为 available、attempts=0；三个 Worker 都 energy=0、exhausted、senses=2，完成数为 2/2/1。它没有获得请求，不是模型错误。successor 的 t03-mean-empty 为 blocked，唯一请求效果未知，不是已经确定的错误答案。两项均保留在各组 6 题分母内。

| 冻结计划 | 实际覆盖 | 未执行部分及解释 |
|---|---|---|
| 代码 4 系统 × 3 seeds × 6 题 | 4/12 单元；到达 24/72；解决 22/72 即 30.56% | seed 1/2 共 8 单元、48 题 NOT_RUN；另有本轮 1 未尝试、1 unknown |
| 动态 4 系统 × 3 seeds × 12 题 | 0/12 单元，0/144 计划任务 | 全部 NOT_RUN，能力反转与适应延迟均未证明 |
| 经验 3 生成加 9 transfer | 0/12 请求槽 | 正确、错误、无经验正式控制均 NOT_RUN |
| 故障 before_reserve 等 4 阶段 | 0/4 请求槽 | 全部正式 NOT_RUN，API 超时不等于真实 kill 实验 |
| 单独预检与保留槽 | 0/1 与 0/7 | 未使用，不用于重发未知或追分 |

计划覆盖率不是模型错误率。已分配 233 槽使用了 23 次意图，余 210 槽未用；另 7 保留槽未用。代码组按原 18 题计划分母计算，Single/Central 为 6/18，legacy/successor 为 5/18；这些是计划完成覆盖，不是对未调用模型评分。

各组只有一个 allocation seed，已观察解决率为 100%、100%、83.33%、83.33%，SE 均 null。旧/新唯一配对差为 0。冻结统计器执行 10000 次 seed bootstrap 后给出 n=1、区间 [0,0]；I 原样复算并与 B summary 逐字段一致，但这个退化区间没有有效的科学不确定性解释，不证明等价、优越或稳定。动态 n=0，均值、SE 和 CI 均 null。

## 未知停止与费用时间

正式批次约在 UTC 2026-10-07 17:00:31.034 开始，17:10:02.715 停止，墙钟约 571.68 秒。唯一未知请求位于 successor 的 `state/execution/455d6b744b11412d9a3ea607ce98749b-gateway`；ConnectTimeout 用时约 21.062 秒，classification=unknown_effect、uncertain=true，HTTP 状态、provider request ID 和 usage 均 null。

trace 保存 child entered、send-entry、transport-returned，没有 response-headers。本地 send-entry 不是供应商收件或发包证明，也不能据 ConnectTimeout 判定肯定未发送或零费用。预算 breaker=unknown_usage，1 个 uncertain reservation、0 pending，保留 USD 0.0166666667，即固定会计参数下 CNY 0.1。Worker 睡眠，主控确认停止，正式 exit=2。

| 会计项目 | 独立复核值 |
|---|---:|
| 本地 intent / send-entry | 23 / 23 |
| 明确 HTTP 200 / provider request ID | 22 / 22 |
| 已知输入 / 输出 tokens | 7138 / 5692 |
| 已知总 tokens | 12830 |
| 已知用量原价估计小计 | CNY 0.0170944 |
| 完整 tokens / 完整估计 / 实际账单 | null / null / null |
| 未知保守 hold | CNY 0.1 |
| 协议准入 hold 上限 / 用户上限 | CNY 24 / CNY 30 |

模型固定 qwen-plus-2025-12-01，非思考、temperature=0.2、provider seed=1234、输入上限 12000 UTF-8 bytes、max_tokens=1536。provider seed 与 allocation seed 是不同变量。23 条 cache 字段均 null，未补零或套缓存折扣。

本报告按 B 冻结的原价参数复算：输入每百万 tokens CNY 0.8、输出 CNY 2，算式为 `(7138 × 0.8 + 5692 × 2) / 1000000`。来源为 B 当日记录的阿里云 qwen-plus 官方价格页。小计不是实际账单，也不是实际扣费下界；优惠、免费额与缓存未对账。预算 schema 的 6 CNY/USD 是固定会计换算参数，不是市场汇率。

已记录 API elapsed 合计 165.183 秒，含超时且可并行重叠，不能作为批次墙钟。Single 在资源释放前完成，Central 跨越释放时点。F 于 UTC 17:08:04.4807526 / 17:08:05.0190449 关闭其两项已核身份服务，每项 80 线程，合计约 10.980 GiB 私有提交；这不是常驻物理内存。整机可用提交内存变化也包含其他活动。跨系统耗时受这次干预污染，后两组亦不是专用硬件实验，因此不作性能因果归因。

没有重试未知、补能量、换模型、重置账本、恢复 Worker 或继续其他付费单元。账单与远端效果仍待真实外部核对；后续独立实验须另有新授权和新目录，不属于此次停止批次。

## 核心优化及离线验证

A 增加可选择的 claim 能量策略：按获得租约计费，包括执行被拒；原 cycle 默认保留。max_senses 对持久化感知次数设置上限，重启不补能量、不清未知；可选择等待未来任务到达。WorkerConfig 显式暴露既有 Router v0/v0.1，没有另建调度器、账本或路由算法。

新 DashScopeCodeExecutor 只接收受限 JSON 补丁，限制一个既有 sample.py、最多 16 KiB，并检查 preimage、路径、纯函数语法。独立验证后复用原审批、租约、应用链；派生经验保留原消费关系，只有后继验证与 fenced 应用完成才记录 adoption。未知用量优先于能量耗尽；固定代码 HTTP 错误停止共享预算的新准入，已在途结果仍可结清，不声称撤销已发请求。

| A 验证身份 | 结果和解释 |
|---|---|
| d5cb717 前序广回归 | 核心与资产 576 PASS，1053.47 秒，2 个保留 warning |
| 审计标签后继 | 8 PASS；首个标签测试 1 FAIL 原件保留 |
| d5bd40c 最终定向 | 执行器、预算与失败链 79 PASS，68.38 秒；strict 11 文件、wheel/sdist 通过 |
| A 首失败 | 13 PASS/1 FAIL；16 PASS/2 FAIL；HTTP 停止 2 FAIL/1 PASS；OOM 中断、build 403、类型债均保留 |

576 PASS 属于前序 SOURCE，不能冒充最终后继的整套回归。本次未无理由重跑这套长测试。最终 79 的源码身份和本次 I 安装测试分别列示。

B 离线 v2 前 7 项与 v3 后 5 项合计覆盖 12 个代表门。动态旧/新通过真实时钟 0/45/90 秒到达，mock 各 12/12 完成；经验控制使用 4 个 fresh 进程/target，有 1 次程序 adoption，错误资产被拒。四故障控制分别覆盖自然 TTL/fencing、提交前 needs_review 且零重发、提交后仅 finalization、离线在途 hold。全部只属 contract_local，不补齐正式 NOT_RUN。

B 的经验报告首 RED 为 SQLite tuple 无法直接转 dict；修复后只重跑经验和未执行故障，原失败目录不覆盖。离线在途没有真实 HTTP，不把合同 hold、API 超时或进程退出码混称真实故障恢复。

## 前轮合成结果保留

前轮产品 SOURCE 为原版 50396909，评测为 5 任务 × 5 allocation seeds × 3 系统。expected=75、observed=75；67 PASS、8 INCOMPLETE、0 ERROR、0 NOT_RUN、0 missing。每 trial 搜索预算为 8，低于原方案默认 24。8 个 partial 都在 Worker，每个只完成 7/8 单元；不补跑或删分母。

下表使用所有可观察端点，含 partial，数值为均值 ± SE。

| 任务与实际指标 | Single | Central | 安装态 Worker |
|---|---:|---:|---:|
| BM-01 合成 suite Spearman | 0.790824 ± 0.017796 | 0.814602 ± 0.002744 | 0.812125 ± 0.003459 |
| BM-02 合成 AUROC | 0.985441 ± 0.000573 | 0.986014 ± 0 | 0.986266 ± 0.000154 |
| BM-03 合成 Accuracy | 0.932500 ± 0.003333 | 0.930833 ± 0.002500 | 0.932500 ± 0.003333 |
| BM-04 合成 Accuracy | 0.995261 ± 0 | 0.995261 ± 0 | 0.995261 ± 0 |
| BM-05 负数学目标 | -1.112888 ± 0.028573 | -1.112743 ± 0.028455 | -1.113452 ± 0.015394 |

Worker 各任务完整 trial 数为 3/4/3/3/4，各搜索完成数为 38/39/38/38/39。partial seeds：BM-01 的 1/4、BM-02 的 4、BM-03 的 1/4、BM-04 的 1/4、BM-05 的 4。BM-05 是缓存数学函数，没有 held-out 数据、真实 GPT 训练或 val_bpb。

| 旧预算口径 | Single | Central | Worker |
|---|---:|---:|---:|
| 完整 trial / 25 | 25 | 25 | 17 |
| 搜索完成 / 200 | 200 | 200 | 192 |
| 搜索重复 | 39 | 0 | 0 |
| acceptance 预计算 | 0 | 0 | 525 |
| 含最终评价的 evaluate 总数 | 225 | 225 | 742 |

矩阵合计搜索 592/600，evaluate 1192；另有机制评价 258，总计 1450。smoke 的 123 次数学调用单列，含首失败，不并入统计。Worker 比基线多出 acceptance 预计算，只有搜索 allowance 对齐，总计算没有匹配，不能宣称算力效率优势。

完整预算和所有端点两套配对 bootstrap 区间均含 0；完整预算十项探索性 BH q 均为 1。分配 seed 不是数据集/模型 seed；完整子集可能选择偏差，全端点分析是看到 partial 后增加的描述性分析。序贯检验未预注册或执行，NOT_RUN。原人工 median/p75/p90/sota 锚点不构成官方人类分布。

| 原机制 | 实际观察 | 保留的边界 |
|---|---|---|
| SB-01 预留前 kill | Q 实际 kill 两 Worker，自然 TTL 后后继完成 6/6，旧 submit 无效 | contract_local/mock；不是原三 Worker 连续存活率，中央真实 kill 对照 NOT_RUN |
| SB-01 预留后 kill | unknown_usage，uncertain=2，完成 0/6 | 正确保守停止，tokens/估计/实账均 null |
| SB-02 经验 | cold/warm 到目标同为 [5,4,8,3,6]，gain=0 ± 0 | 原 adapter/数据库复制；Q consumptions=0、adoptions=0，不是科研经验收益 |
| SB-03 开销 | Worker wall/serial wall−1 为 22.7842 ± 4.1861 | n=5，含整条搜索 pipeline；非纯协调成本，非原方案占位 0.15 |
| SB-04 重复 | Single 39/200=19.5%；Central 0/200；Worker 0/192 | 只指实际搜索配置，不涵盖全部科研冗余或外部效果 |

旧 M 的 adapter 容错只是列表/布尔变更、真实 kill=0；不计入 Q 的实际进程控制。原 I 阶段 93 PASS/14 FAIL、Q 首轮 2 FAIL/1 PASS、后继 3 PASS、旧矩阵 exit=1、页面空白 RED 均保留。后继 25 PASS/1 deselected 不覆盖原 14 失败；旧 8099 与新页面是不同运行身份。

## 原方案条目覆盖

| 原条目 | 本轮覆盖 | 仍缺的正式证据 |
|---|---|---|
| SB-01 容错 | 旧本地双 kill 与新离线四阶段控制 | 正式真实调用的四阶段故障及中央 kill 对照 |
| SB-02 经验 | 旧零增益观察，新离线完整采用/错误拒绝链 | 真实 correct/wrong/none 对照与含生成成本的收益 |
| SB-03 协调 | 旧同配置 pipeline 墙钟比值 | 可分离协调计时、相同资源及无干预对照 |
| SB-04 冗余 | 旧搜索配置重复统计 | 真实科研任务/外部效果的完整重复口径 |
| BM-01 ProteinGym | 合成蛋白代理 | 正式 assay、split、ties/聚合 scorer 与版本 |
| BM-02 TDC 与 Polaris | 合成 AUROC 代理 | 具体 benchmark ID、数据许可、scaffold split、对应指标 |
| BM-03 Open Problems | 合成单细胞代理 | AnnData、release、跨 batch 划分与官方处理/metric |
| BM-04 Kaggle 与 BioML | 合成影像代理 | 具体赛题、数据、split、提交/grade 与榜单分布 |
| BM-05 nanochat | 数学函数代理 | 语料/tokenizer、真实训练/GPU与 val_bpb |
| 完整 BioML-Bench | NOT_RUN | 原完整任务、执行容器、隐藏 grade 和人类分布 |
| Tier C MLR-Bench | NOT_RUN | 正式任务与产物、九维 judge、专家校准 |
| Tier C ScienceAgentBench | NOT_RUN | verified 数据、正式程序与 VER/SR/CBS 评分 |
| 外部 MLE-bench | NOT_RUN | Kaggle 任务、submission、官方 grading 与同资源协议 |
| 外部 PaperBench | NOT_RUN | 论文/rubric、复现实验、容器、GPU和 judge |
| 外部 RE-Bench | NOT_RUN | 原任务/时限、资源、评分与人类基线 |
| Sakana 盲审 | NOT_RUN | 实际论文与独立盲审 |
| Adaption 垂直胜率 | NOT_RUN | 同一垂直任务、人工配置、模型和资源 |
| EvoMap AutoResearch | NOT_RUN | 同问题/资源的想法、实验与独立验证链 |
| R1 AT-07 与 L2 | NOT_RUN | 既有隔离门及明确问题、材料、资源授权 |

仅替换数据加载器不会自动得到官方同口径成绩。原方案引用的竞品分数与本次成绩不做排名比较；本报告没有重新验证外部宣传值，也不以关键词判官、自造锚点或调用方布尔值补正式科学评分。

## 页面修复和运行交接

F 修复了多余闭合标签导致 Swarm 落到 BODY 的结构问题，恢复六视图在唯一 main 内；去掉研究服务断开时的示例数据回退，未知费用不补零，节点详情只读，未接入会话终端时明示缺口。原 390 窄屏溢出、后台标签点击/截图失败与后继成功证据分别保留。

I 在 B 的真实结束状态发现缺少局部测评范围说明，退回原 F Owner。后继仅增加显式展示配置 display_context 和说明：scope_label、scope_reference、run_status 来自 operator_configuration；未配置不猜范围或是否结束。整体 acceptance 的 not_run 与单任务 audit passed 分开解释，配置引用不是验收证据，也不改原 provenance 或账本。

最终入口为 `http://127.0.0.1:8100/#/swarm` 空态及 `http://127.0.0.1:8101/#/swarm` 历史观察。后者绑定 B formal-v1 successor state，显示 5 completed、1 blocked、unknown_usage 及原 live/contract_local 字段；明确局部三函数六缺陷、seed 0、运行已结束及完整科研未验收。整体 acceptance 仍由后端保留 not_run；研究服务未配置，API 503 不被空态伪装成成功。

Orca 真实浏览器完成 1440×900、1280×800、390×844 六个空态/历史状态布局案例，唯一 main、Swarm 首屏位置和无横向溢出通过；三视口节点详情、关闭、滚动和 Home→Swarm 导航通过。390 首导航未切页的 RED、后台淡白及滚动截图记录保留；重选可见浏览器、滚回页首并确认菜单后物理交互通过，没有修改业务源码或用程序 click 代替。详情保留原 contract_local 字段，以及单任务 passed 和 unknown_usage/not_run；会话终端未接入。

服务使用冻结安装的产品包，静态 HTML/JS/server 为冻结 Git 导出字节副本，其祖先目录没有产品包，产品导入来自 venv/site-packages。启动在 import 前设置 OPENBLAS/OMP/MKL/NUMEXPR 四项为 1、Hidden、loopback、PROBE=0。前序 I 服务为 9/13 线程、约 158/162 MiB 私有提交；替换只终止核对过 PID、创建时刻、父子关系、命令和端口的 I 自有 listener，没有操作未知进程。

最终进程交接于 2026-10-08 02:07:39 +08:00 核对：8100 launcher/listener 为 52100/55880，创建于 01:56:37.513054/01:56:37.551532；8101 为 50224/56180，创建于 01:56:38.032226/01:56:38.071121。两个 listener 均 7 线程，私有提交分别 167272448/169099264 bytes，工作集 197554176/200507392 bytes。完整启动参数、环境与父子身份见 final-preview-processes.json 和 scope-preview-8100/8101.launch.json；交接服务保留运行，状态目录严格只读。

## 独立安装与工程验收

I 从合并 SOURCE 归档为私有 COPY，uv 非 editable 安装；direct_url 为本地 source 目录、dir_info={}，没有 VCS commit 字段。精确 SHA 绑定来自归档命令、祖先核验和原始 Git blob 比较，不能称 direct_url 自带 commit。包版本仍为 0.2.1，源码包含 A/F 后继，与原版 50396909 不同。

| 源码及检查 | 结果 |
|---|---|
| 7017f7e 安装必要组合回归 | 171 PASS，127.88 秒；3 个原 warning |
| 7017f7e SDK 与前端 | SDK 1.14.0 schema/address/tampering PASS；Node 8 PASS |
| 7017f7e strict | 首 RED：移除 cast 后 frozen_export.py:246 Returning Any，1 error |
| 96dfbfa 一行后继 | 改为 `actual is True`，strict 全 172 文件 PASS；导出边界 86 PASS |
| 96dfbfa 安装与分发 | COPY 与实际 wheel 各 219 个文件对 raw Git blob 完全一致，pip 103 packages compatible；build wheel/sdist PASS，14 包 wheel 来源/资源/Node 验证 PASS |
| 0176d5e F 范围后继 | strict 172 文件 PASS；observatory 69 PASS，18.90 秒，1 个原 warning；Node 10 PASS；COPY/wheel 各 219 raw Git blob 一致、pip 103 包兼容、wheel/sdist 和 wheel 分发 PASS |
| B 原始数据独立复算 | 24 任务/23 请求逐条核对 PASS；新 summary 与 B 原件逐字段完全相同 |

7017 到 96df 只改变已授权的 bool 返回行，171 项涉及的业务/测试字节未改；96df 到最终源码只有 F 的 scope 展示及其测试/报告变化。按增量运行适用门，未把前序结果移贴到后继源码，也未重跑 A 的 576 项长套件。没有本轮全仓 pytest、双平台 CI 或真实 Docker Engine/科研沙箱通过声明。

原 strict 38 错误分别由 B 修复 37 项和 I 处理授权一行。I 最初安装了非锁定 mypy/build 做探索检查，随后使用锁定 mypy 1.20.2/build 1.6.1 验证；日志分别保留，三锁未改。I 替换进程时首次因 PowerShell JSON 日期自动转换产生身份比较拒绝，未执行 kill；按 DateKind String 精确核对后才停止。其连带首 build 启动为 WinError 267、未进入构建，后继独立日志保留。

A/B/F 的全部首 RED、OOM 中断、GitHub 500/连接错误、B 安装失败与 offline-v2 RED 仍在各原目录。后继 green 是新证据，不改历史断言。AOCI 服务本 Run 未提供、worktree 无 .mcp.json，没有当前完整认知或维护收据；本轮 source-bound 工作未写索引或锁文件。

## 版本身份

| 身份 | 精确 SHA |
|---|---|
| 原产品基线 | 50396909c3fbaa510e755b8e2361e05d84afdfaa |
| 旧 I 集成 SOURCE | bc12c1dd947e80e5e4288efa254c40c84cf1e288 |
| 旧 I REPORT | 47f089ad92e0c459b2deeadab65109246d64ae9a |
| 旧 M 运行 SOURCE | b76d5e17c5462209e511a46d29b5a55b146050b7 |
| 旧 M 后处理 SOURCE | a05431259748fdf98340a02e7734ccb934eb35db |
| 旧 M REPORT | 3c52e17b44a86b619f7cdfafca5ca7997793ade2 |
| 旧 Q SOURCE | 12479cfa5a058f1dab4413a6464f6d691dec53af |
| 旧 Q REPORT | fbb67d10f9977a00f78a730c9b645f70439031f1 |
| 本轮治理交付 | 609f29412a2e101c8c5522ce0fdd5d9c3d9d8948 |
| 治理后继 | b16068a55d6395e96104ec4f6c4fe319f45511ca |
| A 广回归 SOURCE | d5cb717f734eb34cb17855d3075c4f37c43667ca |
| A 最终 SOURCE | d5bd40cea91b09ddf669be5e063e726186191fc4 |
| A REPORT | 99a7b66fb2a1c49bd9a4984e81b2a6d1027fb522 |
| B 冻结协议工具 SOURCE | b41de607b6a020963bd1bd4c2b03432386279c73 |
| B 部分结果 REPORT | 640aa5f2e7c85061fb4e1bd6bf7a3551910f0fc4 |
| F 初次最终 SOURCE | 820488e84a666712f247cfce9b36931d88646c1e |
| F 资源收尾 REPORT | f47ed8a975bd32d305fd5653d203c0d530868204 |
| I 首集成候选 | 7017f7ea7003bb3f1fd3b49315c52b8df24112bf |
| I 类型一行后继 | 96dfbfaaa75780a57062b5d33509f63b244a899d |
| F 范围 SOURCE | 1aa78efd6f2681e5cd78c771cd62362e655e1e44 |
| F 范围 REPORT | d8aaed0b89249ab70db3d8ffe7912b1a8da26556 |
| I 最终集成 SOURCE | 0176d5ee93e98684e42f5dfca575aef471f82c9c |

I 分支为 `songconmaisaix31-design/morphbench-integrate-1007`。指定交付均普通精确 merge，未 force、未改公共历史；所有 source/report 祖先关系已核对。最终 SOURCE 已普通 push 且 ls-remote 一致。I REPORT 是本文件的文档提交，最终 REPORT、remote SHA 与 clean 状态由 `integrate/publication-final.json` 和结算消息分列，避免在提交正文中自引用尚未存在的 SHA。

## 命令与证据索引

以下是实际执行入口，已有输出不可覆盖。R 为 `C:/Users/DW/orca/mb-live-1007/integrate`；P 为 R 下 `venv/Scripts/python.exe`。各原始命令、cwd、exit、耗时在 commands.json、final-commands.json、scope-commands.json。所有运行进程的 BLAS/OMP/MKL/NUMEXPR 线程变量均为 1。

```powershell
git merge --no-ff <上表交付完整SHA> -m <对应合并说明>
git -c core.autocrlf=false archive --format=zip --output <R>/source-scope.zip 0176d5ee93e98684e42f5dfca575aef471f82c9c
uv pip install --python <P> --link-mode copy -r <eval>/dependencies.txt
uv pip install --python <P> --no-deps <R>/source-scope
uv pip check --python <P>
<P> tools/typecheck.py
<P> -m build --installer uv --outdir <R>/dist-scope
npm ci --ignore-scripts
npm run check:sdk
node --test tests/observatory/frontend.test.cjs
<P> -B -m pytest -q --import-mode=importlib -p no:cacheprovider <适用测试路径> --junitxml <新XML路径>
uv pip install --python <P> --no-deps --target <R>/wheel-site-scope <R>/dist-scope/morphogenesis-0.2.1-py3-none-any.whl
<P> -I tools/check_distribution.py --site-dir <R>/wheel-site-scope --check-node
<P> audit_formal.py
<P> tools/morphbench/live_summary.py --root <eval>/formal-v1 --out <R>/formal-summary.json
```

171 项对应 code_executor、budget、budget_evomap、failure_chain_runtime、failure_chain_boundaries、claim_energy、fixed_sample、morphbench 与 observatory；86 项对应 test_frozen_export.py 与 test_b_frozen_export_boundary.py。最终 F 增量为 observatory Python 和 frontend.test.cjs。完整可执行参数保存在 I runtime 脚本和命令 JSON；上面的占位路径用于阅读，不要求原目录重跑。正式付费入口仅在 B 原报告中记历史，不作为本轮可再次执行命令。

| 证据根与路径 | 用途 |
|---|---|
| 旧 mb021-1007/eval/matrix-b8-s0-4 与 summary-b8-s0-4 | 75 trials、原 JSONL/ledger、两套配对统计及原 exit |
| 旧 eval/mechanisms-b8-s0-4 与 verify/kill-controls-first、second | 机制、实际双 kill 的首失败及后继 |
| 旧 integrate/identity、trials-audit、mechanisms-audit、summary | 旧 I 独立核账与 216 文件比较，非本轮重做 |
| core/core-regression-first、recovery 与 final-boundaries | A OOM 首记录、576 前序、79 最终及其 XML/SHA |
| eval/formal-v1/arguments.json、stopped.json、各 cell/result.json | 冻结身份、主控窗口、原单元与停止事实 |
| formal-v1 各 state/tasks.sqlite3、budget.sqlite3、assets/assets.sqlite3 | 原 ledger、预算、独立报告/approval；只读 |
| formal-v1 各 state/execution、audit、workers 与 target | 请求响应/trace、审计三态、Worker 和实际应用 |
| eval/formal-v1-summary、validation-audit、product-audit | B 原汇总与领域核对 |
| eval/offline-v1、v2、v3 与所有 commands/log | 负控、代表门、经验首 RED、四故障合同控制 |
| ui/preview-stop-1008-before、events、after | F 原服务身份和资源干预时点 |
| ui/accepted1008 与 scope-clarification-1008 | F 三视口旧验收及范围返修首 RED/后继 |
| integrate/formal-independent-audit.json、formal-summary.json | I 独立三链及实际应用复核、统计原样复算 |
| integrate/installed-identity.json 与最终安装身份文件 | I COPY/direct_url、raw Git blob、wheel 身份 |
| integrate/*commands.json、*.log、*.exit.txt、*.xml | I 每次门禁、原 strict RED 与后继结果 |
| integrate/browser-*、最终浏览器检查 JSON、preview-* | I 实际截图、DOM、交互与服务进程交接 |
| integrate/document-* 与 render/ | 同源 DOCX 构建、文本核对、渲染和逐页视觉记录 |
| docs/tracks/morphbench-live-core、evaluation、protocol、ui-1007.md | A/B/F 详细领域报告与冻结协议 |

## 剩余限制与未执行项

未执行的正式实验包括其余 20 个代码/动态单元、经验控制和四故障、额外 seeds、完整官方数据/榜单、真实科研质量、BM-05 训练、AT-07/L2、云/GPU和实际账单对账。未知请求保持停止和 hold；不自动恢复或重放。

页面通过仅说明可读事实投影，不能替代用户视觉认可、一般工程修复、科研验收或算法优势。节点终端未接入，研究 HostConfig 未配置，费用实账未知。独立安装和适用工程门不等于本轮全仓测试或跨平台发布验证。

DOCX 使用 documents 技能、runtime Python/Node 和逐页 PNG 视觉检查。Windows runtime 未打包 LibreOffice，主控以 `msg_fa3295eec675` 明确批准仅本次使用本机绝对路径 LibreOffice 的 headless 转换及私有 profile；未改变系统 PATH、默认应用或用户配置，未覆盖原方案或已有目标文件。同源文字核对和逐页视觉记录见 integrate/document-content-check.json、document-visual-check.json 与 render/。收尾期间主控按用户节省 Token 要求，将原 I 终端模型切换为 GPT-6.1-Sol low；任务与 Dispatch 保持，未重复已通过门禁或新增付费调用。

本次完成的是有边界的集成、独立复核和单文档交付。继续独立未启动实验须由主控在新授权后另派 B；本任务 I 全程保持零新模型调用，不以报告完成宣告四类实测完成。
