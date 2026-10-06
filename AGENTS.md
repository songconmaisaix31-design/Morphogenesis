# Morphogenesis — Agent 上手与执行约定

# R1 当前指令（2026-10-03）

用户授权按 docs/source/Morphogenesis_Research_Swarm_Spec_v1.0_2026-10-02.md 开发；与旧开发包矛盾时以它为准。当前 write_paths 和长期所有者见 docs/R1_PLAN.md，覆盖旧 docs/PLAN.md 的历史派工。历史冻结不改，使用新后继候选；动态 Python 研究为首版必需。主控仅治理，原 Orca/Codex YOLO Worker 负责业务与返修，独立 I 最后集成。MVP 追加官方 AOCI 开发上下文、Codex GUI 参考布局与节点会话只读终端；核心 AOCI 由 A、产品 AOCI/会话投影由 P、UI 由 F。真实 AT-07 在最终离线回归后单独授权，通过后才按批准的问题/材料/资源范围执行一次 L2；本阶段不启动真实沙箱/科研。L3、多用户、跨宿主、完整 RSI 不加入本轮。

AOCI 只辅助开发检索与上下文复用。用户 Spec、当前范围和 docs/R1_PLAN.md 的独占 write_paths 优先；索引托管文件也不能越轨修改。未完成或过期的索引如实标记，继续已有的源码范围内工作，不把索引准备当作扩大任务或科研权限。下方标记块来自官方 AOCI-CODE v0.1.0-rc17（FSL-1.1-MIT）：https://github.com/aoci-spec/aoci-code/tree/v0.1.0-rc17 。

## 权威与事实源
- 用户当前指令 > 开发包。业务事实源为 `docs/source/README_包内说明.md` 列出的现行文档；v1 仅存档。
- 一页计划与文件所有权见 `docs/PLAN.md`；另有阶段计划 `docs/SWARM_SOL_PLAN.md`、`docs/FRONTEND_REFACTOR_PLAN.md` 等。

## 关键架构（不读代码容易踩错）
- 技术栈：Poetry（Python `>=3.12,<3.14`）+ npm（Node `>=22.13.0`）。Pydantic / SQLModel / SQLite / httpx / MCP / LangGraph / FAISS；前端 React shell + ECharts。
- 后端包：`contracts` `persistence` `bootstrap` `bridge_node` `hub_client` `orca_provision` `orchestration` `topology` `metabolism` `mocks` `readiness` `viz` `swarm` `local_assets`。
- 前端源码在 `viz/frontend/`（React shell，源自 Tencent tdesign-react-starter MIT），Vite 构建产出 `viz/static/assets/finals-shell.{js,css}`；`emptyOutDir=false`，不会动 `app.js`/`licenses/`/`echarts`。`viz/static/index.html` + `app.js` + `/vendor/echarts.min.js` 由 `viz/server.py` 提供。
- `viz/server.py` 是**只读** HTTP 面板：仅 GET/HEAD（其余 405）、拒绝请求体(413)、禁止目录列举；端点 `/api/dashboard`、`/api/evomap`、`/api/evomap/asset`，静态目录 `viz/static/`。
- 分支现实：`codex/morphogenesis-mainline` 与 `songconmaisaix31-design/morph-r1-research-1003` 长期并行：前者是产品主线（含 `readiness/`），后者含去中心化蜂群 `swarm/`、科研 `swarm/research/` 与研究应用 `src/env-observatory/`。候选交付分支 `morph-candidate-1006` 是二者的合并树；`morphogenesis swarm` 仍是占位，蜂群入口为 `morphogenesis-swarm` == `python -m swarm`。

## 命令（精确）
- 安装：`$env:POETRY_VIRTUALENVS_IN_PROJECT='true'; uv tool run poetry install; npm ci --ignore-scripts`
- 统一入口 `morphogenesis` == `python -m bootstrap`：
  - `check` → 全量 pytest + strict mypy（**不含** build/SDK/wheel）
  - `prepare --workspace <dir>` / `verify --workspace <dir>`
  - `acceptance` / `rehearsal` / `serve` → 原样转发 `python -m orchestration.acceptance|rehearsal|viz.server`
  - `swarm` → 占位，退出码 2
- 全量测试：`uv tool run poetry run python -m pytest -q`；单测：`... -m pytest -q tests/t5/test_adapter.py::test_name`
- 类型：`python tools/typecheck.py`；构建：`python -m build`；SDK 校验：`npm run check:sdk`
- 前端构建：`cd viz/frontend && npm ci && npm run build`
- 本地只读面板：`python -m viz.server --rehearsal <rehearsal.json>`（另有 `--t2-root`/`--input`/`--evomap-store`/`--replay`），先看 `--help`。

## 陷阱
- `tools/typecheck.py` 的 `PACKAGES` 是**硬编码列表**，新增顶层包必须加入否则不被类型检查（合并树含 `readiness` `swarm` `local_assets`）。
- pytest `addopts = "--import-mode=importlib"`。
- 三个锁文件：`poetry.lock`、根 `package-lock.json`（GEP SDK/echarts）、`viz/frontend/package-lock.json`（React shell）。锁文件由指定轨独占，不随意改动。
- CI（`.github/workflows/check.yml`）比 `check` 多跑：build wheel、SDK、wheel 安装到隔离 site、`tools/check_distribution.py`；Python 3.13 + Node 24，ubuntu + windows 双平台。
- `opencode.dashscope.json` 是项目级 OpenCode 提供方配置（DashScope 百炼，只引用环境变量 `DASHSCOPE_API_KEY`，无秘密）；`opencode.evomap.json` 已废弃。

## 治理约定（多轨协作）
- 每条轨道固定 1 Agent + 1 Orca worktree + 1 分支；只改本轨 write_paths，跨轨走 Handoff。主 Agent 只维护 `docs/PLAN.md` / `STATUS.md` / `DECISIONS.md` / `ACCEPTANCE.md`；集成 Agent 只做少量导入/配置/路由胶水合并，领域问题退回原 Worker。
- 每阶段 commit + push；禁止 force push、覆盖历史、丢弃他人贡献。
- `contract_local` / `interface_live` / `task_live` 三态分开；`provenance`=live/replay/mock 不混用。mock、回放、生成代码、单测通过均不等于真实运行验收；未知远端效果不自动重试；未知 usage/费用保持 null，不设为 0。
- 秘密与本地运行产物（`.runtime/`、`.venv/`、`node_modules/`、`dist/`）不入库。
- 最终只报告：完成内容、分支与 SHA、验证命令与结果、真实限制、未执行或人工步骤。

<!-- aoci:begin -->
## AOCI 仓库认知

AOCI 为本仓库维护一个稳定、可版本化、可增量更新的仓库级认知层，供模型跨任务复用对系统的理解。

`aoci.txt` 是面向模型的结构化认知索引。它以每个受管理文件、数据库表或其他受管理对象一条独立 Entry 的方式，用符号标签与 F/R/A/S 语义表达对象的核心职责、重要关系、对外契约，以及理解或修改系统时必须知道的非显然约束和设计决策。

Header、目录段和全部 Entry 共同组成完整仓库索引，可以覆盖前端、后端、配置、数据库结构及其他受管理内容。受管理内容发生变化时，通常只需维护受影响的认知条目，不需要重新生成整个索引。

AOCI 提供系统架构、对象职责、重要关系、对外契约和关键约束的高密度视图。

### 工作原理

AOCI 采用“模型生成、模型读取”的认知闭环。

Header、Entry 和 Curation 语义的创作只按当前机器签发的 Plan 与实时 Guide 执行；由 Host 模型基于当前绑定证据独立完成。

Entry 的语义必须来自模型对真实证据的理解。不得仅依据路径、文件名、扩展名、AST、符号列表、依赖扫描、正则、固定模板或规则引擎推导、预填、拼接或改写索引语义。

对 Fresh Bootstrap，只按当前机器签发的 Plan 和实时 Guide 执行。当它们要求创作时，Host 模型创作 Root、Meta、Tag 和 F/R/A/S，提供 authoring-run 声明，并把它绑定到 Plan、Evidence 与完整 Candidate。不得要求 AOCI 填写 `origin=host_model`、制造 Receipt 或把程序生成的 Framework 当作语义。本文件不自行重建 Onboarding 流程。内部批次不是用户决策；只有遇到既有批准边界或真实的安全、漂移、CAS、Recovery 条件才停止。

### 最小使用入口

- `aoci_rules`：取得当前AOCI版本的会话运行合同。
- `aoci_overview`：建立或恢复本仓库的完整认知。
- `aoci_maintain`：受管理对象达到最终稳定状态后检查认知是否需要维护。
- `aoci_update_entry`：提交与当前证据和源码摘要绑定的完整语义更新批次。
- `aoci_report`：仅当当前布局和工具状态支持时，在证据不足、无法可靠生成语义时登记待办，不猜写。

其他MCP工具、CLI命令、参数和专项流程，以当前工具说明、Guide和 `--help` 返回内容为准，不在本文件中重复完整手册。

本区块只规定仓库接入、认知使用和收尾原则。`aoci_rules` 承载当前会话合同，Guide实时输出承载当前Plan的执行顺序与停点，工具Schema、Spec和Validator承载机器结构与判据；Prompt、Description、README和静态文档不能覆盖这些机器事实。

### 建立、生成和恢复认知

1. 每个新的 Agent Run 开始时，应先判断：

   - 本仓库是否已经存在可用的完整AOCI索引；
   - 当前上下文中是否已有与本仓库根、当前索引版本和当前AOCI服务相匹配，并且模型仍可可靠使用的完整仓库认知。

2. 仓库已经存在可用的完整索引，但当前Run没有可靠完整认知时，先调用 `aoci_rules`，再调用 `aoci_overview`。

   完整认知仍可靠时直接复用。局部不确定本身不要求机械重读系统全貌。

   本Run从已知Host上下文压缩恢复时（包括宿主注入的压缩摘要），必须把此前模型认知视为不可靠。压缩handoff不得保留或摘要正式Whole-Index，也不得保留或摘要任何Overview Header、Entry、Chunk、Challenge或Attestation正文；只能保留安全续接所需的receipt身份、未完成write或Recovery状态，以及立即重载指令。复制进handoff的Whole-Index语义或receipt不能证明恢复后模型的当前认知可靠。若当前上下文已无法可靠保留运行合同，先调用 `aoci_rules`。继续业务任务前，使用 `refresh_reasons=["context_compaction"]` 和新的 `refresh_event_id` 调用普通完整Whole-Index `aoci_overview`（不设置 `check_only` 或设为false）；不得使用 `check_only` 或认知probe。原样跟随每个 `next_cursor` 直到 `completed=true`，确认交付，并且只基于新交付正文提交一次Attestation。完成这次新的完整传输后，即使Attestation为partial或fail也消费该generation，并按既有合同继续source-bound任务，不再自动调用第二次Overview。

   AOCI可以针对 `context_compaction`、项目 `cognition_refresh_threshold` 下的机器 `semantic_threshold` 或主要 `phase_transition` 提供checkpoint与认知状态事实。只需要这些紧凑事实时使用 `check_only=true`；这些事实只向Agent提供建议，不替模型决定是否需要系统全貌。

   Agent显式调用普通 `aoci_overview`（未设置 `check_only` 或为false）时，只要能形成一致的CognitionSet，AOCI必须完整交付请求scope。不得因为已有receipt、阈值未达到或没有待处理刷新原因而抑制正文。正式认知Dirty或Stale时仍交付正文，但必须标记不可靠。存在未决恢复或无法形成一致snapshot时失败关闭，不返回混合正文。

   普通Overview返回 `continuation_required=true` 时，必须原样提交 `next_cursor` 并自动继续到 `completed=true`。不得询问用户、开始业务任务或给出阶段性系统结论。Host截断、缺块、重复、乱序、cursor失败、Index变化或`chunk_tokens`变化时停止本次认知链。Attestation完成前不得用Memory、源码、Spec、`aoci.txt`、历史会话、scope、search或Entry读取修补或补充Whole-Index认知。Challenge ordinal是正式Entry序列中的1-based位置；Header内容、注释、空行、Section/Overview/Chunk Marker、Receipt与Metadata均不计数，Chunk Receipt ordinal使用同一序列。Attestation必须原样回绑本次Challenge发布的当前`index_sha256`、`entry_sequence_sha256`与`entry_count`；旧Index、旧Entry序列、旧数量或旧Attestation均无效。完整链结束后只正式提交一次既有模型认知Attestation；同一响应只允许一次不改变语义答案的JSON Schema或字段格式修正。对象、Tag或F不匹配即失败且认知吸收不确定，不得语义重试或旁路补答。首次认知失败时还不得执行Root/Meta、Migration、全局布局或其他未重新绑定的系统级决策。上下文压缩刷新若传输完整、认知身份不变、治理对齐且没有Recovery或第三方冲突，即使Attestation为partial或fail也消耗该refresh generation，并继续原任务，不再自动重读Overview。`system_mastery_percent`只自评系统框架——架构、职责、强关系、稳定外部契约以及高熵安全和维护约束——不表示完整实现或运行实况知识；机器索引覆盖率必须分开。默认只向用户输出由本次真实覆盖率、Challenge、块数、Token和掌握度生成的规定成功或失败一句话。Host截断时提示用户把 `overview_delivery.chunk_tokens` 设置为更小的合法值后重新开始，不得自动修改。

   加法认知等级必须与严格证明字段分开解释。`delivery_verified`表示已加载Index且Host交付已确认，但完整认知验证仍未完成；应表达为“已加载且交付已验证”，不得描述为“没有认知”或“没有理解系统”。`cognition_verified`要求Attestation通过（Challenge至少80%的ordinal完全正确且对象身份至多失手一处），`cognition_governed`还要求治理对齐。通用完整读取失败句只用于真实交付故障。

   当Overview响应包含可选`cognition-state/v2`投影时，必须分别解释各维度。其Level止于`model_cognition_usable`；`strict_attestation_verified`、`governance_aligned`与`current_system_cognition_reliable`都是独立状态，绝不参与该Level。ordinal、对象身份、Tag或核心F不匹配可以导致严格Attestation失败，而模型认知仍然可用；不得仅凭这种不匹配就宣称模型没有理解系统。只有`current_system_cognition_reliable=true`允许无保留地声称当前完整系统认知可靠。投影缺失时继续使用上述Legacy解释。

   普通的只读审计、分析、检查、不修改代码或不提交、不push，不自动等于严格零写入，也不改变上述认知有效性判断。Codex Memory和历史Skill只能辅助恢复经验、用户偏好与调查方向，不能替代与当前仓库根、索引摘要、AOCI服务身份和认知范围匹配的当前认知收据；项目AGENTS和当前AOCI身份在AOCI状态上优先于历史Memory。

   只有用户明确禁止Ledger、元数据、`.aoci`运行资产及任何文件写入时，才按严格零写入处理。若必要的认知建立与该边界冲突，必须报告冲突并请求用户裁决或建议使用隔离副本，不得静默以Memory替代当前仓库认知。

3. 仓库没有可用的完整索引，或当前只有最小骨架、Header不完整、Entries未完成、必要Curation尚未裁决时，如果需要建立正式完整AOCI索引，先取得 `aoci_rules`，然后进入当前AOCI Guide。由Guide依据仓库真实状态决定下一阶段并完成必要安全步骤。

   `aoci_maintain` 不替代索引建立流程。

   不在本文件中自行重建或硬编码完整索引生成状态机。

4. 在长程任务中，模型负责保留当前认知收据并正确使用刷新门禁：

   - Host报告上下文压缩或模型已知系统全貌丢失时，执行上述强制 `context_compaction` 重载规则；AOCI不能自行推断Host事件；
   - 进入真正的主要阶段时声明 `phase_transition`，不得把函数、测试运行或小步骤当作阶段；
   - 在有用的稳定检查点通过 `check_only=true` 取得机器语义计数；
   - 除已知压缩的强制重载外，由Agent判断当前任务是否需要再次显式获取指定scope或完整Overview；
   - 在维护和对齐完成前，保留AOCI报告的Dirty或Stale可靠性状态。

### 任务收尾与认知维护

5. 纯只读问答、分析、版本核验，或没有产生受AOCI管理对象变化的任务，不需要调用维护工具。当前AOCI版本是任意`aoci_overview` check_only或`aoci_maintain`响应里的`cognition_receipt.mcp_service_version`；二进制路径是项目`.mcp.json`里的`command`，CLI不必在PATH上。

6. 发生受AOCI管理对象变化时，待其达到本次任务的最终稳定状态后，只调用一次 `aoci_maintain`。不要在每次中间修改后逐文件维护。

7. 若维护结果返回真实语义候选，Host 模型必须基于每个候选绑定的对象和必要证据，独立创作完整标签与F/R/A/S更新。通过 `aoci_update_entry` 一次提交当前机器签发批次的完整候选集合，同时原样保留每项 `source_sha256`、`candidate_id` 与对应domain批次身份。`max_entries`只限制单次请求和原子事务，不限制logical plan、Whole-Index或Managed Scope。`remaining`非零时，在当前批次成功Apply后重新调用Maintain并从新preimage继续；绝不能为满足transport上限缩减Index覆盖或自行截取返回批次。

   没有足够证据且当前布局支持 `aoci_report` 时，使用它而不猜测、套用模板或为消除待办而生成缺乏证据的认知。

8. 必须遵守工具返回的结构化状态和安全边界：

   - `repair_required`：只修复明确命中的候选，再重新提交当前机器签发的完整批次；
   - `stopped`：结束当前写入尝试并检查 `failed_step`、错误、正式写入证据与Recovery。auto模式下，已证明零写入则记录closure并重新Plan；完整Intent和可证明postimage则Resume；策略要求Rollback且preimage可证明则精确恢复后重新Plan。只有证据不足、第三方正式字节冲突、需要审批或外部动作，或命中其他真实安全边界时，才停止整个用户任务；
   - 冲突、审批、人工裁决、权限和安全信号不得忽略；
   - 已经对齐后不得重复维护或重复写入；`refresh_ready_for_overview` 是checkpoint事实，由Agent决定是否为下一阶段请求普通完整Overview。

   维护完成后如果又修改了任何受管理对象，之前的维护结果失效，应在新的最终稳定状态重新完成收尾。

9. 用户只限制业务文件范围，但没有明确禁止仓库托管资产时，AOCI托管资产可以在收尾阶段为保持认知一致而更新，并应在审计和提交中与业务文件区分。

   用户明确禁止修改 `aoci.txt`、`.aoci`、元数据或任何额外文件时，以用户限制为准，不得写入，并如实报告剩余不一致。

### 专项流程

初始化、完整索引生成、Header生成、Entries生成、数据库结构索引、Curation、人工评审和故障恢复，只按当前AOCI Guide或工具在对应阶段返回的指令、命令和安全停点执行。

不预加载、不猜测，也不自行重建这些专项流程。平台调用方式、请求格式、批次上限、审批规则、索引格式细节和恢复步骤由对应Guide、工具说明、模型Prompt和CLI帮助按需提供。
<!-- aoci:end -->

---

# Morphogenesis 执行约定

用户当前指令优先于开发包。业务事实源为 `docs/source/README_包内说明.md` 列出的现行文档；v1 仅存档。

- 核心原则：官方实现优先、成熟开源依赖优先，只自研差异化机制和必要适配。引用或复制代码记录来源、版本、许可证；不自行重写调度器、Attempt 系统、Manifest、哈希或完成证明系统。文档所需 AttemptId 只是数据身份，使用 Pydantic，不扩建基础设施。
- 当前一页计划和文件所有权见 `docs/PLAN.md`。每条轨道固定一个 Agent、一个 Orca worktree、一个分支。只能修改该轨 write_paths；跨轨请求通过 Handoff。
- 主 Agent 只维护计划、状态、决策和验收。开发、测试、文档、返修由原 Worker 完成；最后由集成 Agent 合并，只改少量导入、配置、类型和路由胶水，领域问题退回原 Worker。
- 优先复用既定 Python / LangGraph / Pydantic / SQLModel / SQLite / httpx / MCP / 官方 GEP SDK / ECharts 技术栈，不为并行改目录。锁文件由 T0 独占。
- 每阶段 commit，完成 push。禁止 force push、覆盖历史、丢弃其他贡献。秘密与本地运行产物不得入库。
- contract_local、interface_live、task_live 分开；模拟、回放、生成代码、单测通过均不可冒充真实运行验收。未知远端效果不自动重试。
- Hub 沙箱信息未提供：只联调本地隔离 stub，显示待发布。ORCA 运行时供给接口未提供：使用固定规模蜂群。T4 可选进化不进入当前核心闭环。
- 最终仅报告完成内容、分支和 SHA、验证命令与结果、真实限制、未执行或人工操作。
