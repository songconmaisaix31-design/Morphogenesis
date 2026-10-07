# MorphBench 有界真实调用协议（B，2026-10-07）

状态：**DRAFT / 正式运行未授权窗口**。本页与 `tools/morphbench/live_plan.py` 一同提交给主控审阅；实际调用必须再绑定 A 的精确产品 SOURCE、B 的协议/工具 SOURCE、安装字节检查与主控运行窗口回执。当前尚无正式分数，不能据后续分数调整题目、策略、预算或判据。旧产品 `50396909c3fbaa510e755b8e2361e05d84afdfaa`、报告 `47f089ad92e0c459b2deeadab65109246d64ae9a` 与 `mb021-1007` 全部保持原件。

## 1. 范围与事实层级

本轮为 **local code-defect benchmark**，六个原创新缺陷种子覆盖 clamp、mean、unique 三族纯函数。绝不称 SWE-bench、真实论文科研任务、BM05 GPT 训练或官方排行榜。统一复用产品 Worker.run、TaskLedger、租约/fencing、BudgetLedger、验证/推广/应用/采用链。harness 仅注入预定任务、启动受控 Worker、观察已有产物与统计，不新增调度器或完成证明系统。

冻结前旧产品没有相同代码 executor/独立测试 policy，故四组全部采用同一 A 后继执行器和安装 SOURCE；旧组仅选择旧路由及能量策略。这是**共同执行器上的策略/机制消融**，不是纯 0.2.1 对后继端到端比较。

独立 Python `-I -S` 及严格 AST 白名单限制代码能力，不声称 OS 沙箱或一般不可信 Python 隔离。仅固定 sample.py 三个函数，禁 imports/IO/反射/任意命令。隐藏测试在安装产品的 `bootstrap.acceptance_runner`，不发给模型、不落到待修仓库、不接受模型修改；该公开仓库测试的“隐藏”仅指本次模型输入隔离，不保证模型训练时从未见过。

## 2. 模型、预算、凭据

- 精确候选模型 `qwen-plus-2025-12-01`，北京 `https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions`。固定 `enable_thinking=false`、`temperature=0.2`、provider seed=1234、非流式；allocation seeds 为 0、1、2。provider seed 仅尽力复现，不保证远端确定性。
- 模型 request JSON 最多 12,000 UTF-8 bytes，输出 `max_tokens=1536`。规划上额外按输入16,384、输出2,048 tokens 估算；这仍是本地估计，不冒充供应商计费硬承诺。采用现有 unbounded request admission，未核实真实 usage 时保持 unknown 并停止付费分支。
- 2026-10-07 只读核对 [官方模型页](https://help.aliyun.com/zh/model-studio/qwen-plus)、[价格页](https://help.aliyun.com/zh/model-studio/model-pricing)：北京、输入≤128K、非思考输入 CNY0.8 / 输出 CNY2 每百万 token。快照页未声明可用缓存折扣，成本上界不给缓存折扣；保留返回 cache usage，缺失为 null。实际账单 `null`，估计不能等同扣费。
- [官方 Chat Completions 参数](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions)核对 seed、max_tokens、enable_thinking；本机 `bailian-docs-llm-wiki/wiki/api/qwen-api-reference.md` 和 `raw/model-api-reference/qwen-api-reference.md` 提供接口索引。知识库更新时间与在线核对日期分开。
- 默认授权总上限 CNY30 / 256新请求；本协议更窄：240请求槽，预分配233，7槽保留且不能自行用于校准或追分。每请求保守 admission=CNY0.1，全槽CNY24；按上述 token 余量233次估计CNY4.0083456。重试、预检、失败、经验生成全计入，禁止只计成功任务。初稿232+8原件保留；主控消息 `msg_7b0684d34186` 在正式前批准从保留槽划1槽给before_commit。
- USD schema 保持 USD 语义：声明 **6 CNY/USD 的固定会计换算参数，非实时市场汇率**；CNY单价除6写入 ModelPrices，CNY0.1除6作为 unbounded_reservation_usd。汇总将估计USD乘6还原CNY，并同时展示转换参数。不得把人民币单价直接塞进USD字段。
- 每个预登记 trial 有不可挪用的请求/成本/attempt 子上限；各子上限之和为总上限，Worker共用该trial现有账本。通常 `max_attempts_per_task=1`，不自动重试失败；唯独预留前kill控制允许第二次lease/attempt，两个attempt仍合计只有1次请求的成本/token上限。经验组共享4请求账本（生成1+三arm各1），不复制或重置状态。不得通过改swarm/session/身份或重建账本重复申请槽。
- 凭据仅在受控HTTP子进程用 Windows `Environment.GetEnvironmentVariable("DASHSCOPE_API_KEY", "User")` 读取。不打印值、不保存明文、不进命令参数/模型上下文/补丁执行器。父进程和补丁验证子进程不持有key。密钥缺失、明确401、在途unknown分别留证；unknown不自动重试/换模型。
- 最多一次预检（已预留一槽），正式批准前可不使用；不做有分数的在线选题/调参。A/F/I均不发付费请求，B为唯一Owner。

## 3. 冻结矩阵

| 类别 | 固定设计 | 最大新请求 |
|---|---|---:|
| 统一代码修复 | 四组 × 3 seeds × 6缺陷 | 72 |
| 动态热点/配置反转 | 四组 × 3 seeds × 3 phases × 4到达任务 | 144 |
| 正误经验 | 3个独立生成任务 + 3 seeds × correct/wrong/none transfer | 12 |
| 租约崩溃 | before_reserve / before_commit / after_commit / inflight 各≤1真实请求 | 4 |
| 有界预检 | ≤1 | 1 |
| 合计已分配 / 保留 | 233 / 7 | 240 |

四组同模型、任务、输入输出限制、独立验证器、资产流程和每cell总请求/token/cost上限。实际调用少于额度需明确，不按名义预算替代实际。

1. **single**：每个任务 fresh Worker进程/身份，串行，每个Worker只获得一次lease；共享真实到达的task/预算账本，Worker自身选路历史不复用，不声明经验依赖；总额度与其他组相同。不是独立大模型对话工具。
2. **central_serial**：单个产品 Worker 使用共享待办/路由/历史，串行处理；这是中心串行机制对照，不冒称旧suite CentralScheduler实现。
3. **legacy_cycle_v0**：3个产品 Worker，旧cycle能量策略、router v0；共享现有任务/预算账本。
4. **successor_claim_v01**：相同3 Workers，claim能量策略、router v0.1、独立max_senses硬界。这同时改变两因素，结果不能单独归因路由；A离线因果测试分别检验计费和选择器。

顺序预先按seed循环平移四组；统计使用按seed配对，不把任务重复当独立allocation种子。统一代码cell为6请求，动态cell为12请求。成功是独立测试通过且正常 fenced 完成应用；模型声称修好、HTTP200、资产生成或process exit0均不算成功。

## 4. 动态热点及配置反转

预定每cell相对启动时刻0、45、90秒各注入4任务；使用真实ledger注入，模型输入只含该任务代码/公开规格。三phase的题目顺序固定在 `live_cases.PHASES`：clamp占多数 → unique占多数 → unique占多数。热点改变由真实到达分布产生，不设置任何成功率。

Workers初始分别使用 boundaries/arithmetic/order 的真实提示配置，第三phase交换第0与第2个Worker的提示配置，其他输入限制一致。所有提示都是合理帮助，不故意要求出错；capability名与可接题范围一致，不靠伪造capability权重指定赢家。配置变化只能称“能力反转干预”，**若独立测试没有测出能力差异/反转，报告条件未形成或不可辨识**，不换难题重跑。

保留每task到达/claim/响应/验证/完成时间、真实Worker/phase/profile、积压、已用请求、争抢失败和未完成项。报告各phase成功率、等待时长、浪费请求、最大/结束积压。适应延迟仅在观察到前后最佳worker发生反转且有足够重复时定义；否则null并给原因。首次碰到新热点的时间只称服务延迟，不能偷换成适应成功。

旧cycle可能把争抢/idle计入energy，因此可较早停止；如发生，按原规则保留并说明可用请求额度未用尽。不能通过补能量掩盖该差异。动态phase若没有存活worker仍注入并记录积压，不补跑它们。

2026-10-08 冻结前运行机制澄清（尚无付费数据）：统一代码场景两swarm每Worker energy=2、共享6请求；动态两swarm每Worker energy=64、max_senses=128、max_idle=64、idle_seconds=15、stop_when_local_terminal=false，共享12请求。实际 `_backoff` 被产品截为每次2.5–5秒，64次空闲下界160秒可覆盖90秒到达；sleep_seconds=0.1只用于预算停止。Single/central 的动态额度也是12请求，single每个新身份energy=1，central energy=64。lease=180秒，独立验证timeout=20秒，cell硬界600秒；硬界kill只作用于owned handle并停后续付费。

全部phase到达且全部任务完成/已耗唯一attempt、没有任何pending reservation或有效lease后，harness可停止仍在等待新任务的owned进程，并明确标 `stopped_after_all_attempts_quiescent`；这种正常测量窗口收尾不计为故障恢复成功。三阶段离线实跑仍为冻结门。

统一代码四组都用默认提示 `Check boundary cases carefully.`。动态single/central也固定这条通用提示；仅两swarm使用相同预定异质提示pool并互相作策略配对。跨single/central的动态比较同时包含进程机制/提示pool差异，不能据它单独声称路由收益。适应指标若缺独立能力分离，只报告观察到的到达→claim服务延迟和配置干预，不给虚假的适应秒数。

## 5. 租约与崩溃

复用已有真实Worker边界观察方法，仅管理本轮 `Popen` 的PID及create-time，并保留启动命令、父子归属与阶段trace。TTL按真实时钟自然经过，禁止直接改数据库时间/lease行证明恢复。

- **before_reserve**：实际claim后、预算预留前kill，待自然TTL后继Worker接管，至多1个真实请求；检查新fence与唯一完成。
- **inflight**：在真实请求已发出但尚未得到已保存响应时kill ownedWorker；保留requestintent及未知效果，不对该task或保留预算自动重试。若阶段只用contract阻塞来精确控制，分开标注，不把它升级为task_live请求。
- **before_commit**：真实响应与usage持久化、预算settled、独立验证通过后，在lease.submit前hold/kill；同身份重启只允许既有 `_resume/_finalize` 核验。预期 `needs_review` 且没有apply，记BLOCKED恢复。只有同一原始响应/usage完整、settlement全部settled、pending/uncertain均0、重启后新增请求0时可继续下一个独立cell，否则全batch停止。绝不patch账本或补发此任务。
- **after_commit**：响应已保存、独立验证和真实lease.submit已完成，进入最终提交阶段但尚未 `_finalize` 时kill；由同身份fresh进程核对已有completed effect后只恢复finalization，不重发请求。

仅before_reserve使用TTL2秒；其他三个故障阶段TTL180秒，仍保留真实keeper心跳。次序为预留前→提交前→提交后→在途。在途观察后先验证HTTP子PID的CIM父链、Windows原始创建时间与保留的进程句柄；若阶段已错过，记录INCOMPLETE并让原请求结束，不伪造kill时点。确认owned子进程后最多等75秒自然退出，必要时经同一句柄精确结束，保留未知效果；不杀未知PID、不按名称清理全机Python。

强制在最后运行inflight组，防止unknown后仍启动其他付费分支。阶段若无法可靠定位即INCOMPLETE，不能用随便kill任意Python或fixture全覆盖替代。

## 6. 跨session正误经验

生成任务与transfer任务分离，每seed至多1次真实生成。生成使用 `generation-composite`：三个函数全有缺陷，必须真实提出并独立验证全部修复，避免把预置正确的mean当成新生成经验；transfer为另一种 `mean-empty` 缺陷。生成只见公开规格/buggy源码，不见transfer独立测试/gold。两阶段仍是相同三函数语义，不能声称跨领域或新功能泛化。

正确经验必须由真实生成、验证、推广出的源资产，经现有 AssetConsumer 注入fresh Worker/session/workspace，模型明确声明使用，后继candidate独立验证，通过fenced应用后才记录adoption。输出 `consumed_asset_ids → validation → application → adoption` 的原始引用，不能copy数据库后称跨session采用；资产仓库可共享只读approved source，任务/session/workspace必须新建。

错误经验为安全但可由相同测试判错的纯函数补丁，走相同审核门；被拒则测“拒绝”，不绕过审核让其成为approved资产，不伪造consumption。此时wrong arm的模型调用可以是未注入经验的任务，但必须标 `wrong_asset_rejected_before_injection`，不能声称测到了模型抵抗错误注入。none无经验；三arm相同transfer题、固定provider参数和总额度。

模型declared-use与真实注入/派生采用链是程序证据，不等于经验带来的因果性能收益。三个seed样本过少；如全通过不得声称跨session增益。

## 7. 独立统计与停止规则

每cell成功数/固定到达数为主指标；未运行/失败/unknown不从主分母删除。并列报告实际执行成功率，区分缺请求和请求失败。各seed均值、样本SE、按seed配对bootstrap95%CI（10,000次，固定bootstrap seed=20261007）使用现有统计工具；n=3区间只能作描述，无普遍算法优越性结论。

报告完整尝试usage：input/output/cache tokens、请求id、返回model、HTTP/classification、elapsed、asset IDs。每解决token=全流程所有已测tokens/解决数；解决0或usage缺失为null并列已知下界。不把unknown当0。成本估计、保守hold、实际账单严格分列。任务时间含全流程与API elapsed分开；CPU/浏览器争抢未隔离则时间指标标污染。

遇已发送unknown，停止后续付费启动并保留未执行矩阵；明确401/余额/额度拒绝同样停止，不换模型；超输入、schema拒绝、验证失败均保留首次结果，不自动补跑。修改工具后使用新证据目录，不覆盖原件；冻结正式批次不能边看分数边修工具继续伪装同一批。

## 8. 可复现命令与待冻结项

新私有根仅 `C:/Users/DW/orca/mb-live-1007/eval`。现有锁版本从上一轮已核验清单只读复制，剔除旧产品路径后装入本轮venv；Node依赖按冻结package-lock准备。本轮不改上一轮环境。非editable产品安装及原始Git blob逐字节核对是正式前置条件；运行cwd在私有eval，导入应来自site-packages。

```powershell
$py = 'C:/Users/DW/orca/mb-live-1007/eval/venv/Scripts/python.exe'
$tools = 'C:/Users/DW/orca/workspaces/Morphogenesis/morphbench-eval-1007/tools/morphbench'
& $py "$tools/live_plan.py" --out 'C:/Users/DW/orca/mb-live-1007/eval/plan-v1.json'
# 在eval cwd执行；输出目录必须全新
& $py "$tools/live_offline.py" --out 'C:/Users/DW/orca/mb-live-1007/eval/offline-v1'
& $py -m pytest -q tests/morphbench/test_live_plan.py
```

**待冻结而非既成结果**：A SOURCE与精确API、正式harness命令、每组Worker energy/max_senses/idle边界、phase提示切换、正确经验导入路径、三个fault checkpoint、安装字节/Node依赖、主控批准窗口。全部具备且主控审核后才将此协议状态改为FROZEN；不能以文档代替真跑。最终领域结果写 `morphbench-live-evaluation-1007.md`，I再汇总为单一最终报告。

已接入候选 A SOURCE `d5cb717f734eb34cb17855d3075c4f37c43667ca`（普通merge），已有阶段 B SOURCE `254989b07541f5b504dcf3815d70543a8d541ae4`（已push）。A源码中的transport trace仅证明本地HTTP send-entry/headers/return，不证明封包或供应商收到请求。原安装9482523失败 `0xc000012d` 的日志保留在 `eval/install-9482523.log`；主控因宿主内存压力划分串行窗口，A重测试期间B不做安装/批量pytest/90秒动态运行。

正式入口拟为 `live_batch.py --mode live --out <全新目录> --product-source <A SHA> --protocol-source <B SHA> --window-message <主控消息ID>`；未使用单独preflight，预留槽保持空置，正式首个cell中的请求照常计费。24个代码/动态cell每个≤600秒、3经验组每个≤720秒、4故障组每个≤510秒，主循环保守总界18,600秒（5小时10分，另有有限本地启动/写证据开销）；正常预计45–90分钟，不能以此替代真实elapsed。在途fault永远最后，unknown停止即为协议停止，不继续其他付费分支。
