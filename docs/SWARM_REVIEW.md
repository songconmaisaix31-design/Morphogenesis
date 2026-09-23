# Decentralized Swarm v0.2 独立集成审查

独立 I；2026-09-24，Asia/Shanghai。事实源为当前 `SWARM_TASK.md`（含 EvoMap API 追加阶段），不是旧版测试数量。范围仅 `decentralized-swarm`；冻结主线不合并、不部署、不启动或停止演示服务。续租修复本机适用回归与精确双平台 CI 已通过，镜像早期失败不可见已退原 C 修复并由 I 复现关闭；最终本机分发门禁如下记录。

## 审查版本与所有权

| 交付 | 精确提交 |
|---|---|
| 冻结主线 | `605cf48b8b05baf86fd68e5d63f495ba3e5d7e69` |
| A 修正版资产与历史采用幂等 | `b83c2744c1f4d1962f4b4ff267fe47f60a849a26` |
| B 修正版环境 | `313a902d1a17111078770b61fedc4958e408076e` |
| B scope、预留恢复与预算修正 | `6fd611e7a23ee88e56625ca6e224da24cde3a26d` |
| B 显式无上界准入 | `b3f1bc32a8f9448211eb749934db60636ba0b632` |
| C 本地运行检查点 | `bc1827a046f0b65beb643726257c7c7c4f20deb7` |
| C EvoMap 代码与首次全仓源码 | `d4808870bf5b196babf40ebf3f82503365fe9074` |
| C 续租与提交准备修复 | `fc6983ea598c94fc9e7e2a04b40b648e48cc50cf` |
| C 镜像可见性修复与最终本机门禁源码 | `0aef598ea5162d5a12516ab3c155cfc65b3a2527` |

A/B/C 及 B 追加任务在 Orca Run `run_78114f173f9d` 中已结算，领域返修仍由原 C 负责。I 只增加本报告和 `tests/swarm/test_integration_restart.py`；主控独占的 PLAN/STATUS 文档由其提交，I 不暂存。I 没有领域代码修补、依赖升级或锁文件变更。基础全仓、返修后的适用测试及精确源码 CI 分别记录，不能合并为一次本机全仓重跑。

## 源码与反例审查

| 边界 | 实际实现与检查 |
|---|---|
| 事实与记忆 | `TaskLedger` 保存任务、依赖、固定 acceptance、尝试、结果、去重错误与审计；`PheromoneField` 单独衰减偏好。任务内容冲突被拒绝，十亿秒衰减后完成结果与依赖仍保存。JSONL 导出不是权威。 |
| 局部路由 | 后端 canonical scope/module/dependency SQL 过滤在候选正文读取前执行；无 scope 权限返回空集。x/y 不授予权限。实际分数为 `beta*w_history*concentration*capability_match*urgency`，softmax 与 aging/exploration 混合后的概率用于 `random.choices`；输入、过滤与概率留存。 |
| 时间与反馈 | 默认 `tau_seconds=86400`；`rho(dt)=1-exp(-dt/tau)`，半衰期 `tau*ln(2)`；alpha 独立，旧代谢 0.05 仍是 archive threshold。没有原 Physarum 求解器、收敛或复杂度保证声明。 |
| 租约与发布 | SQLite WAL、短 `BEGIN IMMEDIATE`、单任务递增整数 token；claim/renew/release/submit 核验 owner、scope、generation、expiry、TTL，父子与别名 scope 冲突。`submitting` 先独立提交，之后仅执行准备好的字节发布；Git、SDK、模型、验证在事务外。 |
| 效果权威 | `TaskRecord.effect_applied` 只由成功 callback 与最终持有权检查置真；任意 `result.applied=true` 不生效。旧 token 在 callback 前拒绝，旧 owner 不能释放后继。硬崩溃留下部分文件时保留 `submitting` 并阻止自动接续。 |
| 资产与目标 | `promote` 只改 approved 索引；`AssetApplicator.prepare/apply` 使用单独显式隔离目标及确切报告/baseline/preimage。自身源码、预算、验证器、测试、冻结文档、锁文件、保护分支及链接目标均拒绝。 |
| 固定验证 | 策略从不可变任务 acceptance 读取，未从模型候选反推；报告绑定 asset、baseline、完整 policy 与版本。任意 commands 拒绝，候选 Python/JS 不 import/eval/执行。仅声明式字节和固定语法/期望检查；不是通用代码沙箱。 |
| SDK 与复用 | 原 `bridge_node` 和官方 GEP 1.14.0 schema/hash 未改；实际调用 canonicalize、computeAssetId、validateAsset/verifyAssetId。消费先 FETCH approved 与 scope/capability/dependency 检查，再使用原资产 after 字节；采用必须绑定真实任务效果、上下文、执行和目标字节。 |
| 预算 | 仅 swarm-run 准入；预留先于执行。无账单时借记不小于原预留，低估算不释放额度。未知 usage/cost 保留 hold；价格未知时 token 仍可已知，actual cost 仍 None。显式 unbounded allowance 是准入分配，绝不是提供商价格或费用上界。 |
| 运行恢复 | SQLite `pending(worker_id)` 覆盖 reserve 已提交但 status 未写的崩溃窗口；已知有效最后额度结果可提交。unknown usage、远端效果与 token/bound 违约阻止效果，不能误作普通耗尽。已完成提交恢复只补批准/采用/审计；中断反馈显示 needs_review 且不重放奖励。 |
| 观察与镜像 | observer 使用 `mode=ro/query_only` 读取已提交 WAL；无业务 DDL/DML、认领、过期推进或 checkpoint。SHM read marks 属 SQLite bookkeeping。镜像默认关闭，四态可见；unknown/pending 不自动重发，本地 approved 不映射为 Hub promoted。 |
| EvoMap | 使用原单次 httpx 传输，禁重试/重定向/环境代理。HTTP 子进程读取指定凭据文件，父进程与 SDK/验证器不读取密钥；路径重叠、继承密钥、回显、未知用量及伪采用反例覆盖。六个受限 JSON 数据题的固定 oracle 不进入模型上下文；模拟传输不算 live。 |

## 原始验收证据

I 自有产物根：`.runtime/swarm-integration-20260924/`（Git ignored）。完整 pytest 临时目标位于保护树外，路径记录在 `pytest-command.json`；没有用源码工作树充当任务落地库，也没有删除历史产物。

冻结主线对照原 `.runtime/swarm-revision-coordinator/frozen-baseline.json`：I 初始检查、2026-09-23 17:09:48Z 及全部本机门禁后的 **17:22:12Z** 复核均为 `605cf48b8b05baf86fd68e5d63f495ba3e5d7e69`、干净工作树；`AGENTS.md`、`docs/PLAN.md`、`docs/STATUS.md`、`docs/ACCEPTANCE.md` 四项 SHA256 全部一致，7526/7527/7799/7844 无监听。原件 `frozen-initial.json`、`frozen-final.json`、`frozen-after-gates.json`。相对冻结基线的 `bridge_node`、`package-lock.json`、`poetry.lock`、`contracts/identity.py` 无变更；检查未启动、停止或清理任何演示或孤立进程。

- 本次完全离线 fixture 的三个进程 PID 为 **30552 / 5136 / 39172**，每个成员完成两个不同任务，共六任务、六完成审计。原进程回执声明 Python socket、controller import、全局 observer/field 视图均被测试拦截，启动 barrier 仅同步启动。`offline-three-process-evidence.json` 保存这些回执、六条权威任务、批准/验证报告与 12 条路由审计；I 重新计算实际分数与概率和，匹配。
- 独立六进程最后额度争抢：PID **5716 / 45280 / 41480 / 42480 / 40676 / 35656** 同步放行，只有 5716 获得预留，其余五个明确 `swarm_reservation_capacity`；权威账本仅一条 pending hold。原 stdout/stderr、退出码与 snapshot 保存于 `budget-race.json`，数据库 `budget-race.sqlite3`。未执行模型，token、估算和 actual cost 仍为 null；0.0001 仅本地 fixture 准入额。
- 新独立回归使用固定 `.txt` 数据，源成员与消费成员为独立进程。消费成员再在新进程重启时，把执行、apply、approve、record_adoption 全部替换为禁止入口；验证任务/尝试/预算/资产/报告/批准/消费/采用行、原审计、目标 HEAD/index 和实际字节不变。原进程与采用证据写入 pytest 目标内 `restart-evidence.json`。
- 新回归实际 PID **40256 / 5700 / 9652**，依次为源任务、消费任务、消费成员恢复；三者退出成功、idle、各自持久完成数为 1。九张权威表和原审计内容逐项一致；证据另保存到本产物根 `restart-evidence.json`。
- EvoMap API 路径使用明确 `MockTransport`：PID **41276 / 42436 / 32840** 各两请求，六个完成任务、六次批准和一条采用。源 `data-0 / builder-0` 资产 `sha256:9a3fd5d9b079c04c884fa12d06f3c0d332fb929bce161c0ee5a47726b62dde9e` 被 `data-5 / builder-2` 使用，execution ID `43cf77a215934ae8ad42f790392c38d0`、result ID `8b5c912d79d34dd9add9038de1d3156b` 与不可变上下文吻合。`runtime-raw-evidence.json` 保留任务、预算、报告、采用与进程回执；未发送真实 API 请求。
- 实际 `Worker.run` 子进程在持租约、预算预留前被终止，`fixture-1` 由 builder-8 以 token 2 完成；token 1 的后续 submit/release 被拒绝，禁止 callback 未执行。`kill-and-adoption-evidence.json` 保存旧/新尝试与采用证据。另一个文件发布进程以 71 退出，原始目标留下部分字节，账本为 `submitting/token=1/effect_applied=0`，批准/采用数均 0。
- 无 status 的已提交预留恢复后为 `uncertain/tokens=null/cost=unknown`，Worker sleeping/unknown_usage；最后额度的有效结果仍 `completed/effect_applied=1`，随后才 sleeping/exhausted；中断反馈保留一次批准并显示 needs_review。三者实际业务行和 JSON 状态在 `runtime-raw-evidence.json`。

## 验证命令与实际结果

所有本机 Python 命令使用 `.venv/Scripts/python.exe`（3.12.13），进程局部 `OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=MKL_NUM_THREADS=1` 和 `PYTHONDONTWRITEBYTECODE=1`。测试串行，无并行重型全仓门禁。完整 stdout/stderr 保存，不以截断终端尾部代替原始日志。

| 本机命令（Python 前缀如上） | 实际结果与产物 |
|---|---|
| `-m pytest -q --junitxml=.runtime/swarm-integration-20260924/pytest.xml --basetemp=<pytest-command.json 中的独立 TEMP>` | `d480887`：**467 passed，0 skipped，2 warnings，524.53s**；`pytest.log`、`pytest.xml`、`pytest-command.json`、`pytest-summary.json`。173 条 swarm + 294 条既有测试；两条警告均为刻意损坏 Pydantic token 输入的测试。 |
| `-m pytest tests/swarm/test_integration_restart.py -q --junitxml=.runtime/swarm-integration-20260924/pytest-restart.xml --basetemp=<pytest-restart-command.json 中的独立 TEMP>` | **1 passed，34.46s**；`pytest-restart.log/xml` 与命令元数据。此项在基础全仓收集后新增，未冒充包含在前述 467 项中。 |
| `-m pytest tests/swarm/test_worker_runtime.py tests/swarm/test_selfgrowth.py tests/swarm/test_worker_evomap.py tests/swarm/test_integration_restart.py -q --junitxml=.runtime/swarm-integration-20260924/pytest-final.xml --basetemp=<pytest-final-command.json 中的独立 TEMP>` | 续租修复 `fc6983e`：**44 passed，0 skipped，323.30s**；`pytest-final.log/xml`、命令和 JUnit 汇总、`restart-final-evidence.json`。启动 HEAD 是只加计划文档的 `39a8182`；后段 C 在互斥的镜像路径返修，本组 mirror 默认禁用，不能把此定向运行冒充后续镜像源码的全仓门禁。 |
| `-m swarm.cli demo --directory=<cli-command.json 中的独立 TEMP> --max-cost-usd 0.01`，随后同参数 `--resume` | 均 exit 0，三个子进程均 0，六任务完成；首次 47.45s、恢复 9.13s。`cli-demo.json`、`cli-resume.json`、各 stderr 原件和 `cli-command.json`。显式 `contract_local/mock`；未启动任何 HTTP 服务或真实模型请求。 |
| `-m pytest tests/swarm/test_mirror.py tests/swarm/test_observer.py -q --junitxml=.runtime/swarm-integration-20260924/pytest-mirror.xml --basetemp=<final-gates.json 中的独立 TEMP>` | 最终源码 `0aef598`：**27 passed，0 skipped，60.52s**；`pytest-mirror.log/xml`。独立重跑覆盖准备 pending、store/SDK 失败可见、已知拒绝、既存回执不改/不重发、存储失败和 observer 脱敏/只读。 |
| `tools/typecheck.py` | `0aef598`：strict **79 source files** 无错误；`strict.log`。 |
| `-m build --outdir .runtime/swarm-integration-20260924/dist` | exit 0；sdist 与 wheel 都成功，使用独立 build 环境的 `poetry-core==2.5.0`，未修改项目锁文件；`build.log`。 |
| `npm run check:sdk` | schema **1.14.0**、ID 校验、篡改拒绝均 true，published=false；`sdk.log`。 |
| `uv pip install --python .venv/Scripts/python.exe --no-deps --target .runtime/swarm-integration-20260924/wheel-site .runtime/swarm-integration-20260924/dist/morphogenesis-0.1.0-py3-none-any.whl` | exit 0，仅安装本地 wheel 到 I 自有目录；复用现有 uv，无全局安装；`wheel-install.log`。 |
| `-I tools/check_distribution.py --site-dir .runtime/swarm-integration-20260924/wheel-site --check-node` | exit 0；**13 包**来自已安装 wheel，资源、拒绝损坏练习的 verifier 和 Node 检查全部通过；`distribution.log`。 |

最终六项命令的精确 argv、源码 SHA、开始时间、退出码、耗时均保存在 `final-gates.json`。另直接打开 wheel ZIP，`swarm`、`local_assets` 及 `orchestration/gateway_transport.py` 的 **23 个 Python 文件逐字节匹配源码**；`morphogenesis-swarm=swarm.cli:main` 入口存在。既有 Node 依赖由源码树 `node_modules` 提供，因此此项不宣称 wheel 自带完整 Node 运行时。

精确源码 [CI 35889933044](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/35889933044) 的 `headSha=d4808870bf5b196babf40ebf3f82503365fe9074` 已用 `gh run view --json headSha,status,conclusion,jobs,url` 核对，原 job 日志通过 `gh run view --job ... --log` 保存。

- Ubuntu job **107279534669**：**466 passed / 1 skipped / 73 warnings，207.09s**；strict **79 files**、isolated build、SDK、wheel install 与 distribution 全步骤 success。源码 CI 的 Python 为 3.13，Node 24；不是本机 Linux typing target。
- Windows job **107279534307**：**1 failed / 466 passed / 73 warnings，469.18s**；唯一失败 `test_real_wall_clock_renewal_outlives_initial_ttl`，`stopped != exhausted`。pytest 的字典 repr 截断了具体 audit/phase；没有据此推断确切原因。后续 strict/build/SDK/wheel 步骤未执行。原件 `ci-windows.log`、`ci-ubuntu.log` 和 `ci-progress.json` 保留，已通过主控交原 C 返修。
- 本机同用例通过只代表本机当次执行，不解除 Windows CI 失败。历史 `bc1827a` 的 Ubuntu 两失败和 Windows cancelled，以及 C API fixture 曾零准入的失败，仍在 `SWARM_RUNTIME.md` 中保留，没有把修正后定向测试当历史全仓重跑。
- 原 C 新增反例先在旧流程真实失败：`test_slow_submission_status_keeps_lease_alive`，2s TTL、submitting 状态写入延迟 2.5s，**1 failed in 11.75s**。I 直接读取 `c-status-gap-before.log`：已成功续租 9 次，停止续租后状态 IO 耗时 2.516s；submit 阶段 `LeaseLost`，owner/token/expiry 与账本一致但 TTL 已过，effect_applied=false。这证明提交准备 IO 提前停止续租的真实缺陷；不是声称找到了原 CI 截断日志的唯一根因。修复与恢复身份由原 C 持续负责。

`fc6983e` 修复经 I 逐段复核：后台续租覆盖准备与 submitting 状态 IO，提交前 handoff 停线程后以原 TTL 再核验并续租一次，随即调用 submit；没有放大 TTL、重试过期租约或在写事务内引入 SDK/Git。完成记录恢复核验 swarm/owner/scope/task/token/result/effect，并采用已完成权威记录的最终 expiry，恢复不重新执行或提交。诊断只保存有界时间/计数/固定原因，不保存不受信异常文本。原 C 留存的反例与定向回归为 `c-status-gap-before.log`、`c-renewal-after.log`、`c-runtime-after.log`、`c-acceptance-after.log`；后几项有重叠，不累加为独立测试数。

续租修复精确 SHA `fc6983ea598c94fc9e7e2a04b40b648e48cc50cf` 的 [CI 35893123685](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/35893123685) **双平台 success**，I 已核对 headSha、各步骤与完整日志。Windows job **107290250568**：**472 passed，0 skipped，73 warnings，482.91s**；Ubuntu job **107290250432**：**471 passed，1 skipped，73 warnings，207.86s**。Ubuntu 跳过 Windows PowerShell demo launcher 的平台限定测试。两平台均 strict **79 files**、isolated sdist/wheel build、SDK 1.14.0 schema/hash/tamper、wheel install、13 包和 Node 分发检查 success。`ci-fc-progress.json`、`ci-fc-windows.log`、`ci-fc-ubuntu.log` 保留。此时未包含 I 的未提交重启回归及后续镜像修复。

I 根据主控指出的疑点另行复现 M7 缺陷：对真实 HubMirror 的 store.state 注入异常，显式 fixture approval 的 `enqueue=True`，队列处理完且网络调用为 0，但 `read_mirror` 返回 `missing/records=[]`，未产生任何文件。异常发生在 PublicationRecord 创建前，被 `_run` 吞掉；早期校验 return 也缺少可见结果。原件 `mirror-gap-before.json`，已退原 C 修复；没有把禁用/未授权的 enqueue=False 扩大为持久投递需求。

`0aef598` 复用既有 PublicationRecord 和原 adapter 原子写入，后台在 store/SDK 前创建不可发送的准备记录；准备异常为 unknown，已知拒绝为 rejected。既存状态阻止重发，准备更新不得覆盖已写出的 outcome；observer 只输出 allowlist 字段。I 重新运行同一 store.state 异常注入，`enqueue=True/unfinished=0/network_calls=0`，现在 observer 为 `ok`、一条 `unknown/mirror_preparation_failed`、`hub_promoted=false`，固定异常文本未落文件；原件 `mirror-gap-after.json`。C 的旧代码反例 **1 failed/16.46s** 与扩大回归时的 **1 failed/22 passed/42.75s** 原件均保留。后者错误地把不存在的资产当作已知 quarantine；修正测试区分读取异常 unknown 和真实未批准资产 rejected，没有为变绿把任意 store 异常改成确定拒绝。

镜像修复精确 SHA 的 [CI 35894786760](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/35894786760) 已查询，报告提交时仍在运行，不能引用 `fc6983e` 的绿色结果代替它。含本报告与独立测试的最后 HEAD 双平台 CI 按主控明确分工由其继续核验；此报告不声称最后 HEAD CI 已通过，也不为等候结果循环产生新文档提交。

## 验收类别与剩余边界

| 类别/场景 | 当前结论 |
|---|---|
| `contract_local`：同机三进程、任务/租约/预算、固定数据验证、真实文件效果、跨成员采用、恢复、observer、Hub 离线 fixture | 上述实测场景通过；最终镜像源码/含 I 测试的全仓精确 CI 尚待主控结算。仅限表述的本机场景，不升级为远端证明。 |
| `interface_live`：真实 EvoMap 模型 API 回执 | **not_run**；没有读取真实凭据或发送付费请求。 |
| `task_live`：三个成员至少五任务及跨成员采用的真实 EvoMap 场景 | **not_run**；HTTP MockTransport 与完全断网 fixture 单列。 |
| 模型可用而 Hub 离线的真实场景、真实 Hub 发布/晋级 | **not_run**；Hub 离线测试只证明可选镜像不阻塞本地路径。 |
| 任意代码 OS 沙箱/通用编码能力、物理演示、部署、冻结主线合并 | **not_run**；均未执行。 |

真实剩余限制：Docker daemon 不可用的背景未通过启动服务绕过；执行器仍仅 literal/data-only。人工处理 partial-submitting、过期待批准报告、未知费用/请求、旧持久格式和中断反馈；没有自动恢复远端未知效果。唯一 Worker instance ID 是操作者前提，同用户恶意进程/跨机器一致性不在安全模型内。路由候选有界但无饥饿自由或吞吐保证，超过 TTL 的调度/文件停顿仍会失败关闭。镜像内存队列可能丢失未发送项，不是持久投递系统；目录/磁盘无法写入时只有进程内 `last_error=mirror_record_unavailable`，不能保证持久可见。wheel 仍依赖已有 source `node_modules` 提供 Node SDK。旧 `forbidden-runtime-state` 孤立产物保持原状。

用户追加的真实 EvoMap 实验仍需指定安全凭据文件与有效准入/计价配置；未知费用时新请求会停，不能承诺 price-less 配置完成六题。上述未满足的 live 条件不能因本地测试或 CI 通过被宣布完成。最终报告文档提交后的精确 SHA CI 由主控继续核验，不重跑未变源码全仓门禁。
