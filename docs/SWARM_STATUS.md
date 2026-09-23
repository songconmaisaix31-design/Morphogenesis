# Decentralized Swarm v0.2 状态

## P0 隔离与计划

- 2026-09-23：只读核验主线 HEAD `605cf48b8b05baf86fd68e5d63f495ba3e5d7e69`，工作区干净。Orca 创建独立 worktree `C:/Users/DW/orca/workspaces/Morphogenesis/decentralized-swarm`，分支精确为 `decentralized-swarm`，基线相同。
- 三个业务 Worker 互斥路径并行，同分支串行提交；独立 I 最后验收。当前业务测试数：0（尚未运行）。
- 验收状态：contract_local=not_run，interface_live=not_run，task_live=not_run，双平台 CI=not_run。主线不参与任何写入或推送。
- 已核对复用点：`hub_client/assets.py` 委托官方 NodeAssetBridge schema/hash；`metabolism/service.py` 指数时间衰减；`orchestration/gateway.py` 有界单次响应/usage 解析；现有 `.github/workflows/check.yml` Ubuntu/Windows 矩阵。
- 真实边界：工作树隔离不等于 OS 沙箱；本地预算不能承诺上游不提供的在途硬封顶；无计量/未知效果须停止后续花费。Hub 镜像实现和本地验证不意味着生产 Hub 资产晋级。

## P1 并行开工（2026-09-23T22:04:30+08:00）

- 计划提交 `fc29680cc793071ff620bab1ae261f07d01233ae`（2026-09-23T22:02:17+08:00）已推送 `origin/decentralized-swarm`；业务测试 0，尚未执行。该提交 CI 运行 `35871276925` 正在运行，不作通过声明。
- Orca Run `run_78114f173f9d`；A `task_28fdad4925e1 / ctx_a4f7bdea3bd2`，B `task_80a341e94c40 / ctx_e80c740a94d7`，C `task_1883ba1c5300 / ctx_4474e18dc2b4`。三者实际 transcript 已显示读取/实施动作，liveness=live；非仅 input_accepted。
- A 负责唯一环境初始化；B 先交预算门禁；C 在门禁前仅做独立准备。主控只做计划、状态、决策、验收和串行提交协调。

## P1 预算门禁（2026-09-23T22:47:26+08:00）

- B M6 提交 `5f6a544feab6b7a1f832189c8007fe2840667e4e`（2026-09-23T22:46:44+08:00）已推送开发分支。`.venv/Scripts/python.exe -m pytest tests/swarm/test_budget.py -q`：20 passed，22.34 秒；两条警告来自刻意绕过 Pydantic 的坏输入测试。`-m mypy --strict swarm/models.py swarm/budget.py`：2 文件通过。
- 覆盖真实多进程预算预留/结算竞争、账户持久化、逐 Worker burn rate、严格 gateway usage 解析、未知用量保留预留并熔断、fake 高消耗触发全账户休眠、不可重试、公开输入重验证。金额仅为显式价格表本地估算，actual_cost_usd 仍未知；provider_enforced 仍是可信执行器的边界声明，不能变成上游在途封顶证明。
- 首轮预算 15 测试已于 22:09 通过，随后允许 C 接本地有界闭环；20 测试为补充 API 边界回归。其他模块/全量验收尚未通过，interface_live/task_live 仍 not_run。
- A 完成锁定本地环境（Python 3.12.13、Poetry 锁定依赖、npm ci --ignore-scripts）。M1 首轮实际 SDK 拒绝额外 content 属性，正在原 Worker 内修复并重测，未改变上游 schema/hash。C 只读 observer 3 测试通过；官方镜像范围审查缺陷已退 C。
- Orca 等待请求 `8e149801-eca4-4c23-a736-2b2ae63aff3d` 曾 runtime_timeout；request-show 证实原等待 cancelled/connectionLost，同 ID 重放后恢复。22:45 三个原 Dispatch 均回到 live，未重复派发、未推断未知 Worker 已退出。

## P1 环境与资产（2026-09-23T23:03:36+08:00）

- B 环境/路由/租约提交 `57f27b6b3689a46e841fb7ba8fa49dfd4d47248a`（2026-09-23T22:58:16+08:00）已推送。组合领域/旧代谢门禁 52 passed / 77.33 秒（budget20、field5、router5、lease9、legacy13）；10 源文件 Windows/Linux mypy target 均通过。Linux typing target 不是 Linux 运行验收，仍待 CI。
- A 本地资产提交 `05cc7f72a4bfd5fb1624b282ff7965cec45022c1`（2026-09-23T23:01:15+08:00）已推送。`python -m pytest tests/swarm/test_assets.py -q`：42 passed / 273.97 秒；`python -m mypy --strict local_assets`：7 文件通过；暂存 diff 检查通过。
- A 已通过 SDK 地址、真实 worktree 试运行、静态/范围检查、失败隔离、不可变报告/防替换、保护目标、真实 B 租约 fencing，以及同一文件连续两代修改测试。后者复用 Git 临时索引与未引用快照对象，保留目标 HEAD、索引原始字节及无关暂存/未跟踪 WIP，不构建新哈希系统。
- 路由审查发现初始权重 1 与普通成功回报 0.5 会使首次成功缩细；B 已改保守 prior=0.25 并验证普通成功增粗/失败衰减。权重仍是指定的质量移动平均；历史高收益后的普通成功可能降低质量均值，不宣称持续无界增粗或论文收敛保证。
- C 首次组合 13 passed / 5 failed，134.13 秒，其中真实三进程、六任务觅食至晋级反馈测试通过；fake 高消耗全群休眠暴露元数据锁 10 秒等待，B/C 原轨返修。其余 C 夹具问题已修正后 14 个 worker_runtime/mirror 测试通过，整体最终门禁尚未结算。全量源码 strict 74 文件已通过，但尚不能代替最终提交验证。
- A 另发现 AST 解析本身不能拒绝所有上下文语法错误，正在原轨补无执行的 compile 检查；B 正在补有界锁等待参数/进程竞争回归。所有修复按原路径所有权、串行提交进行。
- B 锁等待返修已推送 `da3e18e7cf27070c74933b47c6a20969e384cdaf`（2026-09-23T23:03:46+08:00）：原 lease 9 测试通过，新增真实进程等待上限测试 1 项通过；局部双平台类型目标及全量 strict 74 文件通过。运行轨负责将等待超时转为有界跳过/休眠，仍须完整闭环重验。
- 误配置的 C 测试曾在 `C:/Users/DW/orca/workspaces/Morphogenesis/forbidden-runtime-state` 生成 assets/、leases/ 及三份 SQLite 文件（各 28672 字节，创建于 22:56:39）。递归清理与随后经过绝对路径核对的非递归精确文件清理都被自动审批审查以 `blocked by policy` 拒绝，未删除任何文件；停止进一步删除尝试，列为人工清理项。被冻结主线未被写入。

## 修正版续接（2026-09-23 23:47 CST）

用户 23:33 修正任务书优先；本节及 SWARM_TASK/PLAN 替代下方/前文旧账户预算、文件租约、画布半径、晋级写入等规划认账，不追溯改写旧测试事实。治理修正版 f1a02093a5ccf844acbfc8731ce338650ecc8125 已推送；原业务 e9a3836 保留，尚未完成修正版验收。

- 接手前实验树 clean；冻结主线仍 605cf48 且 clean。独立记录 `.runtime/swarm-revision-coordinator/frozen-baseline.json` 保存治理文件原始字节哈希；接手时 7526/7527/7799/7844 均无本机监听，本轮不恢复演示进程。
- 原 Run run_78114f173f9d 已绑定新协调终端 term_4ce39ead-b2e7-4779-aa57-1095c746c88d，generation=2。原 A/B 已 succeeded，但旧终端消失导致两次指定 release 返回 release_unknown，不强杀/广泛清理；C 已因 terminal_missing failed，release 成功后 Task 自动 ready，按实际 ready 状态恢复同一 Task。
- 新 A：task_fa6fb9291943 / ctx_03499a7a3dee；B：task_1e934e6bf0cf / ctx_f4110e84e8b8；C：task_1883ba1c5300 / ctx_d551d3198d73。三轨 transcript/fleet 均证明 working/live；未另开分支或重复编辑同一路径。
- B 已发布 SWARM_CONTRACTS，C 确认；A 提案为 index-only promote + 单独 prepare/apply + approved 消费/实际采用。最终提交权统一由 SQLite task/fence/owner/TTL 校验，昂贵验证/模型/Git 均在事务外。
- 既有锁定 Python3.12.13/Pydantic2.13.5/SQLite3.53.1 可用，npm run check:sdk 通过 schema1.14/address/tamper 检查，published=false；只是环境就绪，不是修正版预算或运行门禁通过。
- A 的 Docker 探测失败（dockerDesktopLinuxEngine named pipe missing），不启动可能恢复其它项目容器的 daemon。采用限制为声明式固定文件操作的本地路径，拒绝无强制隔离的任意命令；此范围不等于通用代码安全验证或真实模型验收。
- 旧代码精确 SHA f1a0209 CI run35883583313 的 Ubuntu strict 报 local_assets/validate.py:141 CREATE_NEW_PROCESS_GROUP attr-defined；交 A 原领域返修。前次本地全量测试只有中断输出，不能算通过。修正版全量门禁由独立 I 后续执行。
- observer 采用标准 SQLite mode=ro + query_only 读取已提交 WAL；不创建、认领、推进任务，不更新租约/审计/验证结果或调用 checkpoint。SQLite 读者的 SHM 锁/读标记属于原生协调元数据，不等于业务写入；测试检查权威业务行和 DB 内容，不要求锁文件字节不变。依据 https://sqlite.org/wal.html 的 Read-Only Databases 与并发语义，不自造 WAL 解析/复制系统。

## 修正版领域交付（2026-09-24 00:08 CST）

- A 已推送 b83c2744c1f4d1962f4b4ff267fe47f60a849a26：资产批准仅状态、隔离目标应用独立、固定版本声明式验证策略、SDK 地址不变、approved 消费/真实字节采用。56 项完整资产测试通过（110.75s）；后续历史采用幂等修复另跑1项通过（39.83s，55 deselected），Windows/Linux目标 strict 均9文件通过。不是声称最终又跑一遍完整56项。
- B 已推送313a902d1a17111078770b61fedc4958e408076e及普通返修6fd611e7a23ee88e56625ca6e224da24cde3a26d：WAL任务事实/租约/fencing/提交，scope局部与实际历史权重抽样；tau86400、独立alpha；保守swarm预算。原60项领域+旧代谢通过21.37s，追加26项预算通过8.19s，最终34项预算/账本通过10.22s；对应strict Windows/Linux目标通过，数量为不同阶段覆盖，不相加为总测试数。
- 主控发现无可信上界分支会释放估算差额，交B修为所有无账单结算均占用max(原预留,用量估计)，展示admission_charged_usd/unreconciled_reservations；实际费用保持None。新测试覆盖低用量不会释放额度及重启一致性。预算违约优先级unknown > bound violation > exhaustion，防止运行时把违约误作准入耗尽。
- 跨轨返修均回原所有者：C在读preimage前做scope与256KiB检查；B将相对scope保存POSIX格式而绝对lease路径保留原生；A历史采用回放不因后续合法文件改动失效；B提供有界pending(worker_id,limit=100)以恢复预留已落盘但Worker状态未写的崩溃窗口。
- C首轮运行/自增长19项通过183.28s，observer/mirror9项通过18.55s。随后两个新增预算恢复反例先实际失败，再由C修复；最新完整C领域测试尚在运行，未宣称总体通过。
- A/B已分别worker_done succeeded，按用户同一Worker持续负责返修的约定暂保留原会话，供独立I缺陷回派；验收结束后释放。C仍原Task开发，无额外业务Agent。
- 独立I Task task_966c65aed2e9 已登记，真实依赖A/B/C完成后才派发；只负责SWARM_REVIEW、必要独立集成反例与少量批准胶水。冻结主线不合并，付费模型/生产Hub/任意代码沙箱仍未执行。

## EvoMap API 追加阶段（2026-09-24 00:18 CST）

- 用户明确要求所有参与算法尝试的测试 Agent、蜂群 Agent 使用 EvoMap 提供的 API；SWARM_TASK/PLAN 的 0e03dde 已推送并替代旧的本轮不调用模型限制。真实请求仍受先预留、无自动重试、未知停止规则约束，生产 Hub 与冻结主线不在变更范围。
- C 本地检查点 bc1827a 已推送：最终运行/自增长/observer/mirror 合并30项通过207.79s，CLI状态退出码4项通过1.21s；Windows/Linux strict 通过。新 CLI demo 与 resume 均 exit0，三个成员完成六个任务，恢复未增加原六条完成记录；这些都是 contract_local。
- C 原 Worker 继续最小 EvoMap 接入；B 原 Worker 以新 Task task_845f576515e4 / Dispatch ctx_ec7174adeeab 继续预算契约。已观察真实 transcript 和 live/working，未把派发成功当成开发已开始。A 保持原领域返修会话；I 等新的 C/B 门禁后再开始。
- 复用固定 EvoMap 网关和既有安全传输，模型请求单独子进程，源任务独立验证且不向模型提供参考答案；复用任务也必须经过模型请求并追踪 source asset/context/execution。限定 JSON 数据任务不放开任意候选代码执行。
- 当前 Process/User/Machine 均无 MORPH_EVOMAP_API_KEY，已通过异步问题请求安全凭据配置位置及可选模型/额度。没有搜索旧日志里的凭据、发出模型请求或套用 fixture 价格。真实 API / 算法实验暂未运行；缺少可信计价时保留 unknown，不伪造硬费用保证。
- 冻结主线重新检查仍为605cf48且clean，7526/7527/7799/7844没有新增监听；不启动演示进程或 Docker daemon。

## EvoMap 代码阶段交付与独立验收启动（2026-09-24 00:40 CST）

- B 追加阶段 b3f1bc32a8f9448211eb749934db60636ba0b632 已推送：显式 unbounded_reservation_usd 默认为拒绝；无价格时已知 tokens 与未知费用分开、预留不释放，unknown_cost 阻止后续准入。43 项预算测试通过10.59s，Windows/Linux strict各2文件通过，没有真实模型调用。
- C 追加阶段 d4808870bf5b196babf40ebf3f82503365fe9074 已推送：EvoMap HTTP专用凭据子进程、既有单请求传输提取、6个固定oracle数据任务、真实API入口与模型/请求/用量/采用证据。最终84项相关测试通过156.61s，包含原网关33项回归；Windows/Linux strict各9文件通过。三进程API路径单项通过108.47s，6次MockTransport请求、每成员2次、6个固定验证结果及1次跨成员采用，仍只计contract_local。
- 原CI35887345947@bc1827a的Ubuntu全量为2 failed/433 passed/1 skipped，Windows因fail-fast取消。C修复POSIX Barrier引用寿命；旧0.25s续租失败只有stopped日志，原因未确定，新增确定性SQLite/线程续租和2s墙钟测试均通过。新API首次三进程测试182.80s失败因能力不匹配而零请求，已明确data能力并增加局部终态退出；诊断读取暴露Windows状态文件共享冲突，增加已知失败的有界本地rename重试，不重试API。失败原件保留。
- 独立I已实际开始：task_966c65aed2e9 / ctx_58ee16b22270 / term_9e6c4217-cce7-4d41-9a66-5f390113a708。初次input_accepted停在终端粘贴输入框，检查无权限问题后仅补Enter，随后transcript与fleet证实working/live，没有重复派发。I负责完整pytest、strict/build/SDK/wheel、独立边界审阅与精确SHA CI。
- A/B/C原领域会话保留供I返修，最终结算后释放。主控仅SWARM_STATUS有未提交状态记录，I不得覆盖。d480887的CI35889933044仍在运行；没有把此前本地域测试写成全仓通过。
- 用户尚未提供可用凭据路径与具体实验配置。源码接入完成不等于真实API算法实验完成；interface_live/task_live真实阶段继续pending/not_run，未调用生产Hub、合并主线或部署。

## 独立验收与续租返修（2026-09-24 01:04 CST）

- I 对 d480887 完整本机 pytest：467 passed、0 skipped、2 条故意坏输入警告，524.53s；独立跨成员采用后重启反例另跑 1 passed / 34.46s。读取原始进程、账本、采用和预算证据，未把 fixture 或 MockTransport 升级为 live。完整记录见 SWARM_REVIEW。
- d480887 的 CI35889933044：Ubuntu 466 passed / 1 skipped，strict79文件、build、SDK与安装后wheel检查均通过；Windows 466 passed / 1 failed，唯一失败为真实墙钟续租。原错误只有截断后的 stopped 状态，原CI确切原因仍未知；原失败日志保留，未以本机通过覆盖CI失败。
- C 原所有者新增真实墙钟/SQLite反例：TTL仍为2秒，submitting状态写入延迟2.5秒；旧流程先停续租再写状态，实际1 failed / 11.75s，已续租9次但提交时LeaseLost。修为续租期间完成慢准备、停止线程后按原TTL作最终fenced续租并立即提交；过期或旧持有者仍拒绝，恢复审计读取权威完成记录的最终期限。该反例证明独立真实缺陷，不断言它是原CI失败唯一原因。
- 修复后关键3项通过29.88s；完整Worker25项通过149.46s；最终诊断增量+selfgrowth+EvoMap模拟20项通过205.49s；Windows/Linux目标strict通过。未扩大TTL或放宽fencing。I随后运行适用本地回归与完整strict/build/SDK/wheel，新精确SHA双平台CI提供最终全仓证明，旧SHA本机全仓结果保持单独标注。
- C自动复用原终端返回agent_unconfigured且未创建Task；检查注册表后按Orca恢复指南手工创建task_c61a9ee0b646 / ctx_ebeb8d3e8606，向原term_eb48b960-a63e-4136-89d5-4cff1d605681仅投递一次preamble，确认turn_started与真实开发。此次为注册Task/Dispatch的unsupervised投影，不冒称supervised启动；原ctx_d551d3198d73资源保留至返修结算后精确释放。
- 真实EvoMap尚无凭据或有效实验计价配置，仍未发请求。无价格的已知tokens不等于零费用：unknown_cost保留预留并停止新准入，不能保证无价格配置完成六题。最终执行与人工限制以独立SWARM_REVIEW及实际API回执为准。
- C返修已普通提交推送fc6983ea598c94fc9e7e2a04b40b648e48cc50cf（01:04:21 CST），只含原轨三个文件；I开始最终适用回归及构建验收。01:04主控再次核验冻结HEAD/clean、四份治理文件原始字节及四个保留端口，均与接手基线一致。最终独立报告为docs/SWARM_REVIEW.md；报告之后的文档提交不改变本节明确标注的测试版本，最终head双平台CI另按确切SHA核验。
