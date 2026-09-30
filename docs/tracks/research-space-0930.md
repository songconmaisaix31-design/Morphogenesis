# B 科研空间 / MCP / 资产语义

Owner 固定 B，branch `songconmaisaix31-design/morph-research-space-0930`；baseline `ef77af603577d4539d8dbdf780e1536a369b0d12`，plan `6ba12b24781318383454d2e7fb0b132e897b8a8d`。仅本轨 write_paths，未创建其他 Agent/Run。

第一阶段：官方 FastMCP stdio 入口、宿主身份/scope/capability 工具边界；复用 TaskLedger 主动claim/renew/release/handoff/begin_execution，补续租审计与短事务 evidence fencing。既有 Candidate 增 research claim，assets.sqlite3 追加不可变 research_reports；静态安全与 literal-files-v1 验证保留。

A 已确认 `python -m swarm.research --config ABS_TRUSTED_JSON`，通过原生每次启动配置，不动认证/HOME。C 选唯一 NIST NumAcc4 CPU 案例，提供 ExperimentPlan/Context/Result/Executor/read_result；B 用该唯一契约，不平行定义实验执行状态。

当前自验：`python -m pytest tests/research -q` → 6 passed；真实 SQLite scope/capability、stale holder、renew审计、handoff、unknown/crash不重放、外部调用期间独立writer通过；模拟 executor 只证明 contract_local。首次 `python -m mypy ...` → 6 errors（JSON字段类型与apply返回值），修正后 `python -m mypy swarm/research local_assets swarm/task_ledger.py` → Success，17 files。首次失败保留于此，尚未全链验收。

剩余：C executor 接线、独立科研复现/反例/缺失产物/条件拒绝与真实既有 adoption 契约测试、完整适用回归、打包、最终 commit/push。interface_live/task_live NOT_RUN，Docker当前问题属于C/I外部前置，不阻断本轨本地开发。无付费调用。

保留首次扩大回归：`python -m pytest tests/research tests/swarm/test_ledger.py tests/swarm/test_lease.py tests/swarm/test_assets.py -q` → **52 failed / 31 passed**, exit 1；资产发布统一 `bridge_node.assets.BridgeError: sdk_process_failed`，正在检查官方 Node SDK 本地安装。未改断言、阈值或mock官方SDK。

主控准入决定：新的科研经验 approve/继承必须真实执行与独立复现；mock/replay仅观察，保持科研 quarantine。旧literal静态资产兼容，正向完整科研链由I真实OpenSandbox case验收，缺条件NOT_RUN。本轨不放宽生产准入取得绿色测试。

原独立失败保留：主控在 `29446a0bf6619310a448599292b9197662425dc9` exact LF archive 运行只读探针，mock backend 返回 succeeded/exit0 但缺 effect 字段，实际调用1次，`missing_effect_still_unconfirmed=True` 断言实际 False，exit1，`FAILED GATE: absent effect cleared execution_unconfirmed`。B修正为只接纳明确已知的执行状态与effect正向值，补缺失/未知effect真实ledger+call_count测试；等待新SHA主控同断言复验。

Node失败诊断：本 worktree `node_modules/@evomap/gep-sdk` 不存在；按原package-lock `npm ci --ignore-scripts --no-audit --no-fund` 安装99包，未改锁或官方SDK。原扩大回归同断言重跑含新增stdio一项 → 84 passed，115.69s。新增科研拒绝链首次 `1 failed / 6 passed`：静态report.passed=False，定位fixture write_text在Windows产生CRLF，与candidate LF preimage不符；改fixture原始write_bytes，生产验证断言保留。

阶段2当前门禁：科研/stdio/资产拒绝链19 passed（mock仅contract_local）；`python tools/typecheck.py` → Success，97 source files。C已冻结接口12ffb925后续6179d41（签名不变），B不合并对方分支，调用C唯一ExperimentPlan/Context/Executor/read_result，源码模块由最终I集成。

打包失败历史：CPython313 `python -m build` 缺build模块；原项目CPython3.12 venv隔离build下载poetry-core被已有Tsinghua索引HTTP403拒绝；no-isolation诊断发现该venv缺poetry-core，BackendUnavailable。未修改任何全局index/venv；仅该命令进程指定官方PyPI后隔离构建使用poetry-core2.5.0，sdist/wheel均成功，输出TEMP目录 `morph-research-B-build-0930`。

科研/工具增量保留首次失败：11工具跨action参数测试实际被官方FastMCP拒绝并包装为ToolError，测试误期待内部ValueError，`1 failed / 20 passed`。修为SDK公开ToolError类型；原拒绝条件及message断言均保留。工具协作契约收敛、作者/peer科学plan等价（排除role/local_path但完整原plan保留）、候选与归档代码byte绑定、unknown正向值判定、child消费关联均已实现；未造live批准。

离线桥接：`tests/research/bridge_probe.py --c-source <C6179d41 exact LF archive>` 使用C锁环境且B当前源码，调用C唯一Executor/expected_plan+context/read_result与真实公共CPU脚本产物；mock provenance，科研quarantine拒绝批准，contract_local passed。

基线迁移：`tests/research/migration_probe.py --baseline-source <ef77af6 exact LF archive>` 用基线实际Candidate/Store/Validator/Promoter生成旧持久证据，新B读取旧candidate_json、official asset_id、report及approval不变并允许静态消费，contract_local passed。新增research=None仅在其独立可选metadata字段省略，旧base_head/before等null和值0不改；科研metadata存在时完整进入canonical JSON/官方资产身份。该探针不加入依赖Git历史的普通CI测试，浅克隆不需旧源码；普通测试覆盖序列化边界。

业务阶段提交：`9f20d34a4e4f1e760a6449d029314957e8c9f210` 已远端核实；97文件strict和隔离wheel/sdist通过。随后主控要求可运行初始化入口，原B负责新增 `python -m swarm.research.case` 与 [I公开case步骤](../research/PUBLIC_CASE.md)，再冻结新SHA；I不建设领域harness。初始化通过原TaskLedger登记三项任务和角色资格、真实依赖、C唯一plan、固定静态policy及三份HostConfig；不自动claim/execute/approve/adopt。2项初始化WIP保护/资格边界通过，19业务文件strict通过；当前最终整库门禁未结算，不能据旧WIP测试宣称新候选通过。
