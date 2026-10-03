# Poisson 开放研究入口审查草案（2026-10-03，B docs-only）

状态：**question_prepared / reviewable_draft；不是运行授权**。正式材料导入、科学 native 调用、候选执行、实际独立复核、贡献接受、后续代码使用与采用全部 **NOT_RUN**；用量与费用 **UNKNOWN**。本稿不称 MVP / R1 完成。

依据：主控治理 `9f42dfea066648b198d78877c8bdd9a9a55c8378` 的 `docs/R1_PLAN.md` 当前入口及 18:09 / 18:05 决策、现行 Spec §14.2 / §14.4。本轮 Task `task_9ebbae6e5f3b` / Dispatch `ctx_85c678574200`，保留原 B 树与分支；仅本稿和 `docs/tracks/r1-experiments.md`。

| 分类 | 固定身份 / 证据边界 |
| --- | --- |
| 原 B 业务 SOURCE | `5769005b09f1b756c94fdad0649a6b74690c0ca9`，本稿不改其实现 |
| 原 B docs-only REPORT | `5aebd2eb7af774b3dc496ad9620548f6e7852e09`，原方案、首失败、原日志全部保留 |
| 唯一核心冻结 SOURCE | `b480fca1b10a0b6a9c93f0d1801d38f267662461`，以下源码与测试定位均以此 Git 对象为准；本稿不改变该 SOURCE |
| 本轮 REPORT | 本稿所在后继 docs-only commit；由终端交付 exact SHA，不作为新业务 SOURCE |
| CI 状态来源 | 治理 18:09 对 CI `37114395256` 的观察：Linux 全门 success，Windows 当时仍运行；本轮没有刷新 CI，不据此宣称组合通过 |

## 问题与材料

仅提供问题 `-u''(x)=π² sin(πx), x∈[0,1], u(0)=u(1)=0`，解析参考 `u(x)=sin(πx)`，以及方法背景。群体实际产生的假设、方法选择、候选新代码和后续工作必须另有来源与原记录；本稿不预置分支、完整候选程序、论文实例代码或实验结论。

原论文：[arXiv:1907.04502v2](https://arxiv.org/abs/1907.04502v2)。私有原文 `C:/research-private/l2-materials/1907.04502v2.pdf`，1118278 字节、21 页，SHA256 `d17f9bf6b8f346baaa52b6ec81223c53dd3da6899324114c72c7e8c3432d9368`。PDF 第 4–5 页为边界 / 方法背景 locator，第 10 页 §2.8 RAR 为可讨论背景 locator，不指定必须采用 RAR。以上是 Task / 既有治理已核对的材料身份，本轮没有重读整篇、重新核验 PDF 或正式导入产品；正式引用仍须经原导入链绑定材料与原文位置，解析缺失须显式标注。本稿未复制论文代码或正文。

## 正式调用链与权威位置

业务名 EvaluationCriteria 在现有 Python 契约中对应 **`EvaluationSpec`**，不是缺失的新模块。源码入口可从[冻结核心树](https://github.com/songconmaisaix31-design/Morphogenesis/tree/b480fca1b10a0b6a9c93f0d1801d38f267662461)查看；下表行号固定于该 SOURCE。

| 位置 | 现有契约 / 调用事实 |
| --- | --- |
| `orchestration/native_agents/launch.py:10`；`swarm/research/__main__.py:11` | 正式 MCP argv 为 `-m swarm.research --config` 加绝对宿主配置路径；`build_launch` 保留 `HostBinding`，核对 workspace，再由 `HostConfig` → `build_service` → `create_server` 接入。此处仅记契约，不启动进程 |
| `swarm/research/models.py:31`；`service.py:75`；`dynamic.py:45,77` | `HostConfig.generated_experiments` 经闭合 `GeneratedHostSettings` 验证；`criteria` 构造 `TrustedCriteriaRegistry`，`probes` 构造原 `TrustedProbeRegistry`，注入原 executor / asset store。live factory 使用 `LocalCpuSandboxBackend`；mock 不授予 live 权威 |
| `service.py:695`；`server.py:35`；`dynamic.py:180` | 科学 native 的 host-only admission 使用原项目 BudgetLedger / `NativeInvocationBinding`；MCP 不能自授此权。研究 Agent 生成后通过 `prepare_candidate_experiment(task_id,token,plan,files,purpose="original")` 提交新文本；该工具只保存 / 静态检查，不调用模型生成器，也不在宿主 import / 执行候选 |
| `orchestration/experiments/generated.py:165`；`trusted.py:33,43`；`dynamic.py:115` | `EvaluationSpec` 固定版本、kind、reference、域、n、容差；`TrustedCriteriaRecord(spec,approved_by,approved_at)` 是宿主评价批准记录。精确模板不匹配、未来批准时间、作者自己担任批准者均不能取得权威；候选 `approved/approved_by` 字段仅建议，不是批准 |
| `dynamic.py:180,270`；`generated_executor.py:69`；`local_assets/generated_validation.py:77` | lease / fencing / project / branch / authorization / environment / data 检查后，以原资产字节、静态检查、原探针记录生成 admission report；plan 写入原 TaskLedger acceptance 与 `generated_plan_frozen` audit。prepare/admit 成功仍 `execution_started=False` |
| `server.py:79`；`service.py:311`；`dynamic.py:336` | `research_experiment(action="run",task_id,token)` → 原 `GeneratedResearch.execute` → reserve / `begin_execution` → 原 executor；无有效探针不创建 sandbox。原参数 / seeds 文件与候选上传后，执行只在批准 sandbox 内发生；unknown 走原 uncertain，不自动重发 |
| `orchestration/experiments/evaluation.py:25,46,52,96`；`generated_executor.py:204,216` | 宿主从原 `outputs/output.json` 解析网格、边界与参考误差。archive reader 验证原 plan / context / 输入输出字节并重算；忽略缓存 assessment 的自报权威 |
| `local_assets/generated_validation.py:144,171,224`；`feedback_generated.py:65,132` | 原 `generated_result_payload` 仅在成功、已知效果、开跑前独立批准及原批准快照匹配时 final / trusted；仍 contribution proposed。后续 observation / feedback 复读原 archive、ledger completion / audit / 资产与清理事实，不能由提交者布尔授奖 |

上述六个 B 评价 / 执行 / 验证 / 研究资格文件（generated、evaluation、trusted、generated_executor、generated_validation、local_assets/research）在原 B SOURCE 与冻结核心 SOURCE 之间 `git diff --name-only` 为空；A 正式 HostConfig / factory 以冻结核心定位为准，不能把 B checkout 的旧 A 接线当最终组合。

## 独立评价的既有格式

评价网格由宿主事先批准的 `EvaluationSpec` 固定，不由候选输出自行选点：`x_i=x_left+i*(x_right-x_left)/n_intervals`，`i=0..n_intervals`。该 Poisson 问题须明确域 `[0,1]`，评价端硬编码参考 `sin_pi_x` 与两端零边界。候选只交原始值，不写评价器、宿主 registry、参考数据或判据；更改任一模板字段须被原精确匹配拒绝。

| 现有字段 | 本问题的审查约束 / 未批准参考 |
| --- | --- |
| `kind` / `reference` | 已有 `poisson_reference_v1` / `sin_pi_x`；不能以注册例程 / 模板字节替代实际新候选 |
| `version` | 待 operator 在真实评价前固定版本并取得独立批准；不在本稿伪造记录 |
| `x_left` / `x_right` | 问题域 0 / 1；这是问题定义，不是 L2 执行授权 |
| `n_intervals` | 源码默认 100，即 101 个评价点，**仅未批准参考**；真实 n 待明确，不能默认作已批准 |
| `max_abs_tolerance` / `boundary_tolerance` | 源码默认 `1e-6` / `1e-8`，**仅未批准参考**；真实容差、理由、批准人 / 时间待确定，禁止看结果后改口径 |
| `approved` / `approved_by` | 默认 false / None；候选改 true 不生效，必须原宿主 record 精确匹配且批准早于执行 |
| `output_schema` | plan 现有 `generated-output/v1`；原 `output.json` **仅含** `x` 和 `u` 两个数组，每个 n+1 项、有限数字、顺序匹配上述网格 |

结构记法（不是可提交 JSON / 程序）：`{"x":[x_0,...,x_n],"u":[u_0,...,u_n]}`。布尔、非有限数、错长度 / 错网格 / 额外 `score` 或 `passed` 键均不能形成有效支持结论。网格点匹配的源码常数为 `rel_tol=abs_tol=1e-9`；它只是解析规则，不是已批准的科学误差阈值。

评价端独立计算 `max_absolute_error=max_i |u_i-sin(πx_i)|` 与 `boundary_error=max(|u_0|,|u_n|)`。合法原始输出超容差给 `refuted`；结构无效给 `inconclusive`；未成功执行 / unknown 不冒充有效反证。直接 `evaluate` 始终 diagnostic / untrusted / proposed；开跑前批准与已知执行只允许原 projection 赋予 final / trusted，贡献接受仍单独复核。

**科学解释限制**：独立固定评价网格不等于已经证明训练网格与测试独立。现有执行器上传 `parameters` / `seeds`，没有自动把完整 `plan.evaluation` 写入参数文件；未来新候选须从获准任务上下文取得输出网格契约，不能假定另一隐藏参数通道。当前评价器不测 PDE 残差，不做方法 / 效率比较，也不能判别候选是否直接输出解析参考。数值一致只支持这个 EvaluationSpec 的采样判据；真实求解方法、训练 / 测试独立、方法改进、新代码来源需原实验记录和实际独立复核证明，当前均 NOT_RUN。更高层科学主张缺证据时记不支持 / 未测，不暗增评分模块。

## Operator 后续步骤草案（本轮不执行）

1. 固定最终核心 / 产品组合，完成唯一完整离线验收；之后取得单独 AT07 授权并实际全部通过，再取得一次明确 L2 授权。原 P protected worktree / human TTY receipt 门保持，不代填、不触碰。本研发 Dispatch 或 Codex 模型接续均不授予科学执行权。
2. 在原授权 / HostConfig / registry 中明确项目、数据和允许外发范围、金额与模型配额、模型 route、环境 / image / runtime / daemon / probe 身份、资源上限、n / 容差与独立批准人 / 时间。上述值当前 **待授权或 UNKNOWN**，不提供伪 live 配置；不读取真实 key，不改全局 auth / HOME / PATH / provider。真实配置必须与获准 AT07 记录完全绑定。
3. 经正式产品导入链导入获准材料，记录原 SHA / locator / 解析状态；给 Agent 的启动内容限问题和材料。由原 native host admission / 项目预算发起获准研究，保留实际选题、来源、讨论和新代码字节。`prepare_candidate_experiment` 接收真实产生的 files / plan，绑定原资产、revision、sources / data_refs / seeds 与 claim / hypothesis；不是让 operator 填完整候选答案。
4. 用原 `lease_task` 取得实际 token，原 prepare / admit 后才调用 `research_experiment(action="run")`；`result` / `artifact` 回读原 run，`verify_research(...purpose="original")` 后 `complete_research_task` 提交原 evidence。记录执行、科学、贡献三个轴及原 blocker；未知执行 / 用量不自动重试或换 case / seed / 计费入口。
5. 作者完成释放范围后，由不同成员 / worker 的依赖新任务以同源资产 `asset_id`（不再传 files）prepare `purpose="reproduction"`，使用不同 run / sandbox 实际重跑，原 `verify_research` / completion / `accept_result` 链复核。`dynamic.py:161` 核对原 owner / dependency；`local_assets/research.py:59` 核对不同 worker、run、sandbox、相同科学条件与已知效果；实际独立性等级与来源照实记，不凭 author/reviewer 名称宣称独立。
6. 有效 supported 或 refuted 证据可经原 feedback 的独立复核获得贡献；refuted 可降低原路线机会或触发拒绝 / 休眠。记录随后实际研究行动引用何证据、如何改变选择；`research_advisory` 的建议或一次阅读不等于该行动已经执行。崩溃 / 超时 / 无效输出不奖励为有效反证。
7. **至少一次真实代码使用**仍走原链：真实产生且符合原资格的源资产经 `approve_candidate` 后，新消费任务以 `purpose="inheritance"` prepare 原资产并在新 sandbox 本地再验证 → `verify_research` → `inherit_experience(path_map,preimages,base_revision/base_head)` → 原 `AssetConsumer.inject/execute` 从源资产提取真实 after 字节，产生 child asset / consumption → 对 child `research_candidate(action="validate_files")` 与 `approve_candidate` → `apply_candidate(...execution_id)` 经原 fencing 完成任务及字节应用，再由 `record_adoption` 取得原回执。逐项保存 source / child / consumption / result / receipt 与真实 provenance；检索、注入、静态通过、approved 都不是 adoption。源精确定位：`swarm/research/service.py:584,614`、`local_assets/consume.py:31,44,96`。

原代码采用门只接受 original / reproduction / inheritance **passed**；failed reproduction / counterexample 会阻断 `require_reproduced`，refuted 源资产不能伪作通过代码采用。有效负结论的贡献与后续使用要求必须分开：方法改进可以不支持，但若实际没有可按原链使用的新代码及本地再验证，AT-13 / Spec §14.4 仍未完成；不以读负结论文档或假 receipt 补齐，也不事先安排一个保证采用的分支。若实际研究无法满足原链，仅向原 Owner Handoff 原记录和契约缺口，不放宽通过条件。

## 已有证据与本轮验证边界

以下是冻结源码中的**已有测试定位**，本轮仅静态阅读，不运行它们；inert fixture 的数值输出 / 模拟沙箱不等于实际候选执行或科学验证。

| 固定于 b480 的测试定位 | 能证明的离线边界 |
| --- | --- |
| `tests/experiments/test_generated_evaluation.py:21,31,39,46,57` | supported 仍 diagnostic；合法 refuted 区分无效输出；拒自报 score / approved / reviewer 布尔 |
| `tests/experiments/test_generated_experiment.py:37,56,68,128,168` | fixture 执行 / 重算、有效负结果、崩溃不冒充反证、原 registry finalization 与 archive 篡改拒绝 |
| `tests/integration/r1_security/test_b_generated_boundaries.py:108,130,153,165` | 调用者无权授 final、未知效果不可 final、成功 archive 必须绑定输出原字节 |
| `tests/research/test_dynamic_service.py:256,288,345` | 正式配置 / factory / MCP 参数拒绝自授评价或控制面权限；未配置不 implicit admit |
| `tests/integration/r1_security/test_a_dynamic_mcp.py:162` | 正式 MCP mock：不同原始 / 复核任务形成贡献，负结论降低机会；usage/cost 未知，没有 adoption |
| `tests/integration/r1_security/test_a_dynamic_mcp.py:182` | 正式 MCP mock：新消费任务、fixture 再验证、原字节真实 apply 与原 mock receipt；不是 L2 |
| `tests/integration/r1_security/test_b_mock_adoption.py:205,243,263,308`；`tests/local_assets/test_generated_consumption.py:117,186` | 原消费 / fencing / mock receipt；失败、混合 provenance、原 archive 篡改拒绝与应用前再次核查 |
| `tests/integration/r1_security/test_c_generated_trust.py:107,132,178` | 原 ledger / 独立复核 / 贡献与 advice；调用者 / 缓存不能替代原 archive 或宿主批准 |

历史已跑结果及命令由原报告 / 原日志承载，不冒充本轮运行：

| 原记录 | 命令 / 结果 / 分类 |
| --- | --- |
| B REPORT `5aebd2eb7af774b3dc496ad9620548f6e7852e09` 的 `docs/experiments/at07-evidence/frozen-targeted-first.txt` | `.venv/Scripts/python.exe -m pytest tests/experiments/test_frozen_export.py tests/experiments/test_at07.py tests/experiments/test_at07_export.py tests/experiments/test_generated_configuration.py -q --tb=short`：110 PASS / 3.76s，local inert SDK / daemon fixture |
| 同 REPORT 的 `frozen-experiments-first.txt` | `.venv/Scripts/python.exe -m pytest tests/experiments -q --tb=short`：210 PASS / 27.50s，local/mock，包含原评价器边界 |
| b480 的 `tests/integration/r1_security/evidence/a-aec86c9-installed-affected65-first.txt` | 原 Q 私有 installed 受影响专项：65 PASS / 24.98s；原 Aaec / B576 组合证据，不替代 b480 完整验收；命令身份见原 Q 报告 |

本轮只执行 raw Git 源码 / 既有测试与日志读取、限定 docs diff 检查、普通 docs commit / push 和 remote exact / clean-tree 核对；未重跑上述 110 / 210 / Q65、完整测试或安装。文档检查命令为 `git diff --check`、`git diff --cached --check` 和 `git diff --cached --name-only`；交付身份用 `git rev-parse HEAD`、`git ls-remote origin refs/heads/songconmaisaix31-design/morph-r1-experiments-1003`、`git status --porcelain=v1` 核对。交付时另报本 docs REPORT exact SHA 与结果。

OpenCode 原首次请求真实 `Insufficient Balance`（request `9165a37c-a4c8-48b7-94be-dcf826a113fa`），原 Task 未执行工具 / 写入，原 ctx 随自建终端关闭已 settled failed；首错误私有记录保留，费用不能推为 0。前一个 Codex readiness timeout `ctx_03a9cd950de1` 也保留；本次后继不重试 DeepSeek、不换计费入口、不改全局账号。

材料正式导入、科学 native、候选 sandbox 执行、实际复核 / 贡献 / 采用、AT07、L2、人工理解观察均 **NOT_RUN**；未启动 Docker / WSL / services，未装包、读真实凭据或改环境。P human TTY receipt 与最终产品组合门仍待，不更新他轨状态。独立 I 只按 ordinary merge 合本 docs REPORT 且保留 `[skip ci]`，不改变冻结 SOURCE、不再触发 CI；本稿不替代最终产品离线、真实隔离或 R1 科研退出条件。
