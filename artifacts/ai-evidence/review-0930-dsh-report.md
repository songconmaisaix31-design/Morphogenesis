# DSH 异构评审记录 · db283ea（推理流为评审实质）

受审代码：`db283eaa1f1d71d36e7b8a3520aafbce5becf1dd`
评审模型：`dsh --profile headless`（deepseek-official / deepseek-flash，安装目录名 DeepSeek-V41-Flash）
调用方式：一次真实有界 `dsh --profile headless --patch overlay.json`，禁用工具、`retry=0`、`maxTokens=16384`。
**结果：进程 exit 1，未产出结构化 fact/hypothesis JSON（stdout 仅 `\r\n`），16 格矩阵未覆盖，fact 引用不可机械校验。**

> 处理决定（用户确认）：接受推理流为评审实质，如实标注其边界；本记录不冒充「合格的 DSH 正式评审」。

## 边界声明

- 推理流（`review-0930-dsh-reasoning.log`，60,924 bytes，785 行）是本次评审的实质内容，已归档。
- 输出预算（16384 tokens）在推理阶段耗尽，模型停在「Now matrix cells」；最终 JSON 数组、逐字 fact、16 格转移矩阵覆盖均未产出。
- 因此**无机械校验通过的 fact**，所有引用仅为推理草案中的行号/ID，不做为已核实事实。
- 本次未运行任何代码，模型未声称执行测试；历史 D/I 证据不计为本次重跑。

## 推理流中的实质发现（草案，非机械校验结论）

| 维度 | 推理要点（非已核实事实） |
|---|---|
| inv1 | 候选链每个候选以同一 task_id 走 `budget.reserve`，request_id 带 index；切换在同一 task 预算下新增计数，holds 汇总所有非 settled。结构上满足；未验证真实多候选 live 并发聚合 |
| inv2 | `settle(None)`→uncertain 保留 reserved_usd；holds 对 status!='settled' 求和，fallback/切换不释放未知持有 |
| inv3 | 发送前 reserve + `begin_execution` 持久化 request_id；**缺口**：reserve 与 begin_execution 间崩溃留 pending reservation；subprocess 超时可能已发请求但 child 未返回，settle 记 unknown。需 live child 证据 |
| inv4 | `_owned` 校验 owner/token/scope/expiry/status/now；**注意点**：幂等重放分支（status completed 且 same_owner）直接返回旧记录、不复查 expiry（不产生新提交，但可被指出） |
| inv5 | 候选链无回绕；全 guard 跳过→sleeping + all_candidates_suspended，有界退出 |
| repair1 | unknown_effect 保留 unknown hold、不 confirm_execution、unconfirmed_request_id 保持→status blocked，跨重启/worker/handoff 不可重放 |
| repair2 | claim 在 expiry<=now 时取新 token（token+1）；_owned 要求 expiry>now，边界无重叠 |
| repair3 | after_recovery 用 sequence>recovery_sequence 且 occurred_at>=at 过滤；**未证实**：store 未实现 checkpoint 时退化为严格时间，等时新事实会被丢弃 |
| repair4 | 5xx/transport 先于 body 解析；Arrearage/quota/中文 body 不会降级为 rejection |
| repair5 | cost_state 读当前 reservation（reservation_cost_state），不读聚合 |
| fencing | try_claim_probe / _finish_probe 均 guarded UPDATE + rowcount!=1；同 owner 旧 token 被 fence。未证实跨进程真实竞争 |
| budget_ab | reserve 先 capacity 再 pending 冲突；settle 低 usage 用 max(estimate, reserved) 不释放承诺。未证实真实并发 A/B 交错 |
| false_green1 | fault_drill.require 在 Worker 异常处理外；但 _process 的 try/except 吞异常转 failed，若只断言 failure_count 可能假绿 |
| false_green2 (**high**) | fault_drill 用 `Mock(spec_set=FixtureExecutor, wraps=fixture)` 替换 executor 边界，并覆盖 `bound().return_value` 为 unbounded；budget/lease/breaker 未被替换，但 executor.bound 的请求边界语义被 mock |
| false_green3 | demo 断言 call_count + reservation 行数 + budget.snapshot，非仅预算 |
| false_green4 | 本批无测试文件、无 skip/decorator 证据，无法确认删/跳 |
| false_green5 | 语义断言（failure_class/switched_to/cost_state/evidence_ref），未断言 usage/cost 数值 |
| false_green6 | recover() 断言历史字节不变，但无 mutation 工具/restore 校验 |
| limitations | 只给 14 文件，缺 gateway.py/models/router/pheromone/hub_mirror/local_assets 与测试文件；verification 全 NOT_RUN |
| matrix 16 格 | **未覆盖**（预算耗尽） |

## 结论

- DSH 推理流对五不变量、五修复、fencing、预算 A/B、六类假绿给出方向性评审，最值得注意的高危项为 **false_green2**（demo 的 Mock 覆盖了 `bound()` 边界语义，需区分 executor 边界 mock 与生产 Worker/ledger/breaker 行为）。
- 因未产出结构化 fact/hypothesis 且 16 矩阵未覆盖，本记录**不构成「合格的 DSH 正式评审」**，仅作为已捕获评审实质的归档。
- 未发现推理流中有「五不变量被明确违反」的机械结论；所有判断均为待验证假设，不据此放行 live。
