# MorphBench 真实调用测评：B领域报告（2026-10-08）

**结论：PARTIAL / STOPPED_UNKNOWN，本轮未完成用户要求的四类真实测评，也没有算法优势结论。** 唯一正式批次完成seed 0的四组代码cell，在第四组出现一次 `ConnectTimeout / unknown_effect / usage=null` 后按冻结协议停止。保留23次请求意图、22次明确HTTP200及独立验证应用成功、1次未知效果；没有重试、换模型、重置账本或继续其他付费分支。

动态热点/配置反转、正误经验、租约崩溃的**正式真实批次均为NOT_RUN**。这些通路只有单独标记的离线Mock HTTP/contract控制证据。其余两个allocation种子未运行，不满足至少3种子的目标。本文是领域材料，最终单文档由I汇总；工具交付完成不等于四类真实验收完成。

## 1. 精确版本、授权与证据位置

| 项目 | 精确身份 / 状态 |
|---|---|
| 分支 | `songconmaisaix31-design/morphbench-eval-1007` |
| 治理起点 | `445aad4e3066e7cbfc0123adc1779d24d0c74cd4`，普通merge |
| A正式产品SOURCE | `d5bd40cea91b09ddf669be5e063e726186191fc4`，普通merge及非editable安装 |
| B冻结协议/工具SOURCE | `b41de607b6a020963bd1bd4c2b03432386279c73`，正式过程中无修改，普通push远端已一致 |
| B历史阶段SOURCE | `254989b07541f5b504dcf3815d70543a8d541ae4`、`aefd3ef3a13ef4b07f33a3bc7b6853b572a8c080` |
| 协议 | [morphbench-live-protocol-1007.md](morphbench-live-protocol-1007.md)，冻结于B SOURCE |
| 独占离线窗口 | 主控 `msg_317ac7d83dda` |
| 唯一正式窗口 | 主控 `msg_4e6d99d6cf88`，ask thread `msg_7b0b40dfc20c` |
| 停止确认 | 主控 `msg_4f5e524c7469`：不新增paid，完成部分报告；后继必须另行明确授权 |
| 正式原件 | `C:/Users/DW/orca/mb-live-1007/eval/formal-v1`，下文简称 `formal-v1` |
| 退出/全日志 | `eval/formal-v1.exit.txt` = 2；`eval/formal-v1.log` |
| 全账/统计 | `eval/formal-v1-summary.json`，冻结脚本生成，无覆盖原件 |
| 本报告REPORT SHA | 本文件所在的文档后继提交；通过Orca交接精确SHA，不用它代替B SOURCE |

所有 `eval/` 简写均相对 `C:/Users/DW/orca/mb-live-1007/`。旧产品 `50396909c3fbaa510e755b8e2361e05d84afdfaa`、旧报告 `47f089ad92e0c459b2deeadab65109246d64ae9a`、旧环境和 `mb021-1007/**` 原件未改。没有搬运来源许可未明确的旧suite；本轮新增自己的小型代码任务和薄运行工具。

安装版仍声明包版本0.2.1，但内容为上述A后继SOURCE，不能称纯原版0.2.1。四组共用新DashScope代码executor及同一固定验证器，是共同执行器上的策略/机制消融。旧组选择cycle/v0，后继选择claim/v0.1；两因素同时改变，不能独立归因路由。

## 2. 四类矩阵覆盖与层级

| 类别 | 冻结设计 / 请求槽 | 真实执行 | 剩余状态 |
|---|---|---|---|
| 统一代码缺陷 | 4系统×3 seeds×6缺陷=72 | seed0四cell；23请求意图、22解决，24任务实际到达 | seeds1/2八cell、48任务未运行；legacy另1已到达任务未尝试；successor1任务unknown |
| 动态热点/配置反转 | 4系统×3 seeds×12任务=144 | 0 | **NOT_RUN**；不能证明能力反转、适应延迟或积压改善 |
| 正/误/无经验 | 3生成+9transfer=12 | 0 | **NOT_RUN**；不能声称真实跨session采用或收益 |
| 租约/崩溃 | before_reserve、before_commit、after_commit、inflight各1=4 | 0 | **NOT_RUN**；API超时不是计划中的kill故障实验 |
| 单独预检 | 1预留 | 0 | 未使用；首正式请求没有另占预检 |
| 保留槽 | 7 | 0 | 不用于补跑unknown或追分 |

预分配233槽，23次意图已占用，210个已分配槽未用；另7保留槽未用。20个code/dynamic cell缺失列表在summary `missing_cells`；经验12槽、故障4槽、预检1槽亦未执行。停止后的缺失来自治理/协议，不能记作模型任务全部失败。summary的 `planned_completion_rate` 含未运行分母，只是计划覆盖率；`observed_cell_completion_rate` 才是已观测cell描述。

这是 **local code-defect benchmark**：clamp、mean、unique三族、六个小型纯函数缺陷；不是SWE-bench、官方科研榜单、真实论文任务或GPT训练。独立测试在安装产品 `bootstrap.acceptance_runner`，不发给模型、不落到待修目录、不被patch改写；公开仓库可能进入训练数据，不能证明模型从未见过测试。

## 3. 已观测代码cell（仅allocation seed 0）

| 系统 | 解决/固定6任务 | 请求意图 | 已知tokens | 全流程tokens/解决 | cell秒数 | 秒/解决 |
|---|---:|---:|---:|---:|---:|---:|
| Single，fresh Worker/身份串行 | 6/6 | 6 | 3515 | 585.83 | 426.017 | 71.003 |
| Central，单Worker串行 | 6/6 | 6 | 3500 | 583.33 | 75.651 | 12.608 |
| legacy cycle/v0，3 Workers | 5/6 | 5 | 2899 | 579.80 | 28.986 | 5.797 |
| successor claim/v0.1，3 Workers | 5/6 | 6（含1unknown） | 2916（仅已知部分） | **null** | 40.877 | 8.175 |

取得已知响应的22个代码任务都通过固定独立测试。legacy的 `t02-mean-denominator` 为available/attempts0，三个Worker均energy0/exhausted，senses均2，完成数2、2、1；第六个名义请求槽未被使用。不能将该任务写成模型错误，也没有补能量。successor未解决任务 `t03-mean-empty` 的一次请求超时并阻塞，不能据此判为错误答案。

每组仅一个独立allocation seed，已观测均值分别100%、100%、83.33%、83.33%，**SE均null**。旧/新在唯一配对seed的解决率差为0；冻结统计器实际执行10,000次seed bootstrap，原始返回退化区间 `[0,0]`、n=1、SE=null，原件保留。这**不是有效科学不确定性区间，不证明等价、优越或稳定**；至少3 seeds要求未满足。动态n=0，均值/SE/CI均null。没有为得到区间删除unknown或重跑。

### 独立验证与应用链

只读交叉核对TaskLedger及资产SQLite：24个到达记录中，22条同时有 `status=completed`、`effect_applied=true`、关联 `report.passed=true`；policy为 `sample-tests-v1 / fixed-sample-v1`、isolation为 `fixed_pure_sample_subprocess`。每条task、worker、fencing token、candidate asset ID、validation report ID、验证命令结果及provider metadata见 `eval/formal-v1-validation-audit.json`。

原产品 `state/audit/builder-*/*.json` 共23条：22条 `outcome=promoted`、`provenance=live`、`usage_source=provider_reported`、`interface_live=passed`、`task_live=passed`；另1条 `unknown_usage` 不能提升为passed。只读汇总为 `eval/formal-v1-product-audit.json`。审计的 `evidence_class=interface_live` 与独立 `task_live` 维度并存；Worker状态和ledger.result旧 `evidence_class=contract_local` 字段仍保留，I不得改写原记录或只据单一标签臆造业务状态。

这仅是固定小型代码任务的真实调用/验证/应用证据，不能推广为一般项目修复、动态Python研究或OS沙箱安全。纯函数AST白名单和Python `-I -S`不是完整操作系统隔离。

## 4. 首个正式停止原因

停止任务：`code-s0-successor_claim_v01 / t03-mean-empty`。原始目录：

`formal-v1/code-s0-successor_claim_v01/state/execution/455d6b744b11412d9a3ea607ce98749b-gateway/`

其中request、trace、response均原样保留。response为 `error_kind=ConnectTimeout`、`classification=unknown_effect`、`uncertain=true`，HTTP状态/request id/usage均null，elapsed=21.062秒。trace有HTTP child进入、send-entry及transport-returned，没有response-headers；本地send-entry不是供应商收件证明，不能擅自改判“肯定未发送、零费用”。

BudgetLedger停止快照：reason=`unknown_usage`、uncertain reservations=1、pending=0，保留USD 0.0166666667（固定会计参数6折合CNY0.1）；整体tokens、估计费用、实账均null。task为blocked，Worker为sleeping/budget_or_uncertain_execution。既有并行调用已返回并结清已知usage，batch收cell后退出2，`stopped.json`时间Unix1791393002.7148201（UTC 2026-10-07约17:10:02.715）。首cell开始约17:00:31.034，全批约571.68秒。

没有重发该任务，没有在新swarm/身份申请相同请求，没有消耗保留槽；主控 `msg_4f5e524c7469` 确认不再paid。后续独立cell只有新明确授权和新目录才可启动，不属于此次冻结批次完成。

## 5. 全流程费用总账

| 项目 | 观察 |
|---|---:|
| 本地request intent / HTTP send-entry | 23 / 23（不是供应商收件证明） |
| 明确HTTP200 / provider request ID | 22 / 22 |
| 未知效果 / usage | 1 / 1 |
| 已知输入tokens / 输出tokens | 7138 / 5692 |
| 已知总tokens | 12830 |
| cache字段 | 23条均null，未虚构为0 |
| 已知用量按原价估计CNY | **0.0170944** |
| 完整token合计 / 完整估计费用 | **null / null** |
| 实际账单 | **null** |
| 未知请求保守hold | CNY0.1 |
| 协议准入hold上限 / 用户上限 | CNY24 / CNY30；240槽 / 256请求 |

模型 `qwen-plus-2025-12-01`，22个返回model均一致；非思考、temperature0.2、provider seed1234、输入≤12000UTF-8 bytes、max_tokens1536。allocation seed与provider seed分开。没有额外预检、在线校准、经验生成或隐藏调用，失败也计在23意图内。

2026-10-08复核[官方模型价格页](https://help.aliyun.com/zh/model-studio/qwen-plus)：北京≤128K输入，非思考原价输入CNY0.8/输出CNY2每百万tokens。这里不给缓存折扣；0.0170944是**仅覆盖已知usage的原价估算小计**，不是实账，也不是真实扣费下界（优惠/免费额/缓存未核验）。完整费用因unknown为null。既有USD预算schema使用固定6 CNY/USD会计参数，非市场汇率；CNY单价除6录入、汇总乘6还原。

逐请求id/model/input/output/cache/HTTP/classification/elapsed/原路径/估算/bill=null均在summary `accounting.rows`。已记录API elapsed合计165.183秒（含超时），并行可能重叠，不能当作批次墙钟。全部实际账单尚未对账，不能把 `unreconciled_reservations` 误读为全部效果未知；未知usage只有1。

## 6. 时间污染与owned进程收尾

主控安排串行重测试/浏览器窗口，B进程局部BLAS/OMP/MKL线程均1，未改全局pagefile或杀未知PID。但正式初段仍受遗留UI服务的提交内存压力：

- `eval/hardware-during-formal-1.json`，UTC17:04:06：FreePhysicalMemory=9913044KiB，FreeVirtualMemory=575776KiB。
- F原Owner核对PID/create-time/命令/父子关系/端口后，UTC17:08:04.4807526及17:08:05.0190449精确停止其39376/41608服务；17:08:06确认两个listener/两个launcher及8100/8101退出。B未触碰F或未知进程。
- F证据为 `C:/Users/DW/orca/mb-live-1007/ui/preview-stop-1008-before.json`、`preview-stop-1008-events.json`、`preview-stop-1008-after.json`，交接 `msg_26400ec0c8bc`。整机可用提交内存回升包含其他活动，不能全归因两服务。

Single seed0在释放前，Central seed0跨释放时刻，后两组在释放后。表内cell秒数和秒/解决**受宿主干预污染，不作效率优劣归因**；后半段也不是严格专用硬件实验。API耗时单列且仍受公网影响，没有资源好转后重跑早期样本。

各cell记录owned Popen PID、Windows create-time和exit code；停止后只读CIM检查 `eval/formal-v1-process-check.json` 于UTC17:12:42未发现匹配本批次命令行的Python（count0），匹配范围/限制保留在文件内。未进行全机Python清理。

## 7. 安装、测试、首失败与后继

| 检查 | 结果与边界 | 原始位置 |
|---|---|---|
| 新环境依赖 | 旧核验清单只读复制，旧venv不改 | `eval/dependencies.txt`、`dependencies-install.log` |
| Node prerequisites | Node24.16/npm11.13，冻结npm ci --ignore-scripts，99包 | `eval/node-install.log`、`hardware-before-window.json` |
| 基线50396909非editable | 成功，仅安装检查，没有同executor纯原版对照 | `eval/baseline-install.log`、`baseline-50396909.zip` |
| A9482523第一次安装 | **RED 0xc000012d**，不覆盖 | `eval/install-9482523.log`及对应source/zip |
| 最终A d5bd40c安装 | 非editable COPY；154个产品.py/.mjs与Git归档原字节一致，0lock漂移 | `eval/install-d5bd40c.log`、`installed-d5bd40c.json`、`source-d5bd40c.zip` |
| 依赖相容性 | 101 packages PASS | `eval/pip-check-d5bd40c.log` |
| 初次mypy | **RED No module named mypy**；后装锁内工具 | `eval/type-tools-first.log`、`dev-type-install.log` |
| 旧3工具strict类型债 | 修37项，另1项frozen_export越轨交I | A `core/type-full-first.log`、B `eval/type-tools-second.log`，中间RED依次保留 |
| 冻结pytest / strict | **15 PASS / 13 files PASS** | `eval/pytest-b-frozen.log`、`type-b-frozen.log` |
| offline-v1 | 原6 buggy seeds均被固定测试拒绝，负控PASS | `eval/offline-v1/result.json` |
| offline-v2 | 7负控、四静态、两动态通路PASS；经验汇总**首RED**，SQLite普通tuple不能dict | `eval/offline-v2.log`、`offline-v2/commands.json`、`experience-s0.stderr.log` |
| offline-v3 | 修B报告row_factory，只重跑经验及未执行4故障，5/5 PASS | `eval/offline-v3/result.json`及日志 |
| 正式批次 | **exit2 STOPPED_UNKNOWN**，未重试 | `eval/formal-v1.log`、`formal-v1.exit.txt`、`formal-v1/stopped.json` |
| SOURCE推送 | 前三次GitHub500；第四次普通push成功，remote=B SOURCE | `eval/push-b41de60-second.log`、`third.log`、`fourth.log`；首次Request ID DB46:2621DB:1026D41:152B480:6AC67953（16:54:44Z） |

Direct_url为本机git archive COPY路径，没有VCS commit字段；SHA绑定来自归档命令和原字节核对。154文件范围仅产品包.py/.mjs，不扩大为全部静态资产。正式cwd在eval，identity的产品导入来自新venv/site-packages，没有别轨源码注入。

12项代表离线门由v2前7项和v3后5项覆盖，v2首失败仍失败。动态旧/新各实际等待0/45/90到达、12/12 mock完成；经验四fresh进程/target、1程序adoption、错误资产拒绝；预留前natural TTL/fencing接管；提交前needs_review且0重发；提交后只恢复finalization；在途离线仅contract hold，无真实HTTP。它们**不补齐正式NOT_RUN的四类结果**。

## 8. 可复现命令（已有输出不可重用）

以下为实际关键命令。复现必须使用新目录和新明确paid授权，永不重发原unknown。安装/测试/离线检查不调用模型。

```powershell
# 源码cwd归档；新venv在eval，旧mb021环境只读
 git archive --format=zip --output C:/Users/DW/orca/mb-live-1007/eval/source-d5bd40c.zip d5bd40cea91b09ddf669be5e063e726186191fc4
 Expand-Archive -LiteralPath C:/Users/DW/orca/mb-live-1007/eval/source-d5bd40c.zip -DestinationPath C:/Users/DW/orca/mb-live-1007/eval/source-d5bd40c
$py='C:/Users/DW/orca/mb-live-1007/eval/venv/Scripts/python.exe'
$bench='C:/Users/DW/orca/workspaces/Morphogenesis/morphbench-eval-1007/tools/morphbench'
uv pip install --python $py -r C:/Users/DW/orca/mb-live-1007/eval/dependencies.txt
uv pip install --python $py --no-deps C:/Users/DW/orca/mb-live-1007/eval/source-d5bd40c
uv pip check --python $py
# eval cwd使用冻结package.json/package-lock.json
npm ci --ignore-scripts
& $py "$bench/verify_live_install.py" --archive C:/Users/DW/orca/mb-live-1007/eval/source-d5bd40c.zip --source d5bd40cea91b09ddf669be5e063e726186191fc4 --out C:/Users/DW/orca/mb-live-1007/eval/installed-d5bd40c.json
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
& $py "$bench/live_checks.py" --out C:/Users/DW/orca/mb-live-1007/eval/offline-v2
& $py "$bench/live_checks.py" --out C:/Users/DW/orca/mb-live-1007/eval/offline-v3 --only experience-s0 fault-before_reserve fault-before_commit fault-after_commit fault-inflight
# 下两项在B源码cwd，其余在eval cwd
& $py -m pytest -q tests/morphbench
& $py -m mypy --strict --follow-imports=silent tools/morphbench
# 唯一正式批次已执行并STOPPED，不可照此重跑
& $py "$bench/live_batch.py" --mode live --out C:/Users/DW/orca/mb-live-1007/eval/formal-v1 --product-source d5bd40cea91b09ddf669be5e063e726186191fc4 --protocol-source b41de607b6a020963bd1bd4c2b03432386279c73 --window-message msg_4e6d99d6cf88
# 只读统计，x模式拒绝覆盖
& $py "$bench/live_summary.py" --root C:/Users/DW/orca/mb-live-1007/eval/formal-v1 --out C:/Users/DW/orca/mb-live-1007/eval/formal-v1-summary.json
```

每个offline子命令/超时/exit在v2/v3 `commands.json`，每Worker实际命令/PID/create-time/配置在cell spec/result。Windows用户凭据只在受控HTTP子进程读取，不进入命令参数、补丁进程或明文证据。新依赖沿用锁版本，不安装云资源或调用额外收费服务。

## 9. 交I只读接入与剩余工作

四个真实state为 `formal-v1/code-s0-{single,central_serial,legacy_cycle_v0,successor_claim_v01}/state`，swarm_id等于目录名，target为同级 `target`。I可只读接入 `tasks.sqlite3`、`budget.sqlite3`、`assets/assets.sqlite3`、`workers/*.json`、`audit/*/*.json`、`fc-logs/runtime/live/events.jsonl` 和 `execution/*-gateway`，不可改账本/恢复/重启Worker。正式来源在根 `arguments.json`；bill未知、blocked、available与各事实维度必须原样投影。

本轮未证明：三seed稳定性、真实动态能力反转/适应、真实kill/TTL恢复、真实跨session经验收益、通用源码修复、科研榜单、SWE-bench、BM05训练、云/GPU科研或算法优势。公开价格估算不等于实账。

I可将本文与A/F/旧M证据汇成单文档。若用户另行授权继续未启动独立cell，仍由原B Owner在新后继task/新目录执行，保留此次停止、污染与unknown，不改写原结果。供应商账单/远端效果核对尚未完成，必须依赖真实外部证据，不能以本地推测清除未知hold。
