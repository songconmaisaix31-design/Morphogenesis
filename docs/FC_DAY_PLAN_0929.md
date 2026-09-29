# 2026-09-29 一页日计划：底层收口、有限只读应用并行

**当前版本不统一；原始受限本地原型成立，FC 未冻结。** 今日只补已确认的测试证据和 Schema nullable 缺陷，同时开展有限只读应用，不追加无限底层功能。依据两份今晨审查：`../morph-algorithm-baseline-review-0929/artifacts/ai-evidence/algorithm-baseline-assessment-0929.md`、`../morph-release-readiness-review-0929/artifacts/ai-evidence/release-readiness-assessment-0929.md`（均相对各工作树根目录的共同父目录展开）。

## 固定所有权与基线

每轨 1 Owner + 1 worktree + 1 同名分支；主控只调度、决策与验收。以下为实际派发，未预填通过。

| 轨 | worktree / branch、精确基线 | 排他 write_paths | 当前交付 / 状态 |
|---|---|---|---|
| A / 固定 codex | `morph-fc-tests-0929`；`73e64cc70116ac658d85591d082c0684a4952c99`（FC 联合候选） | `tests/swarm/test_failure_chain_boundaries.py`、`tests/swarm/test_failure_chain_runtime.py`、`artifacts/ai-evidence/fc-tests-0929-*` | 真实 Worker 执行、计数、unknown 停止、失租拒绝、有界退出及有效敏感性证据；进行中，待主控转发简报 |
| B / 固定 codex | `morph-schema-closeout-0929`；`73798cd6f05210f2bd9b1eebfd6f9f0dd6e842db`（去中心化治理/Schema，未合 FC） | 本文件；`docs/PLAN.md` 仅今日所有权附录；`TASKS.md` 仅今日台账/本轨项；`docs/FC_LOG_SCHEMA_DRAFT_0928.md` 仅 audit nullable 条件及说明；`artifacts/ai-evidence/schema-0929-*` | 先落盘计划，再复现并修复 count=null/audit 缺失误拒绝；保留历史失败，待自验/独立验收/H3 |
| C / 固定 codex | `morph-readonly-app-0929`；`2957b408ce922369a595a8acd43a882eb85897d3`（第一代主线） | 首阶段 `artifacts/ai-evidence/application-readonly-0929.md`；主控盘点后新增 `viz/frontend/src/backend/Backend.jsx`、`viz/frontend/src/backend/backend.css`、`viz/static/assets/finals-shell.js`、`viz/static/assets/finals-shell.css`、`tests/t5/check_adoption_trace.cjs` | 主控已批准 Gene 池展开采用明细，复用 `/api/dashboard → RehearsalDocument → UseRecord`；保留 run/task/agent/attempt/Gene/version/time/provenance，缺失为未知；进行中，待验 |

派发记录：A `task_bf99e1b4ba10 / ctx_d0bbed22831d`；B `task_d536a112682f / ctx_170180e15e72`；C `task_75eedbf12038 / ctx_9320f0ef60fa`。三个 Worker 已启动；允许各自 ignored `.runtime`，只读复用现成环境。跨轨缺口 Handoff，不改他树/锁文件/AGENTS/SWARM 文档；除 C 已批准前端写权外不改生产源码，A/B 无生产写权；C 无后端或 Schema 写权。

**交付检查点（替代表内开工状态）**：B 修复 `188fae46de4f3d2fe4943461a62a9626caa5325d`、交付 `318dd4f26f27cda25e4278772bcce6b508023c26` 的 Owner 原矩阵 12/12、扩展 24/24、控制 13/13、exit 0，D/H3 pending。主控转发 C 最终 `621f588988899bdbc7c7a83e893369c4145d89b3` 已 push/clean、replay 自验通过，D pending；A 测试 `f4779d45a1b1417ffa6bce37708e9a68d46cf4e5`、最终 `3d8bb856efadbb1bee4a69bc37c56d3ef4d24cfd` 的 Owner focused 20/full 699（2 warnings）/strict 87 exit 0，真实 mutation 红/恢复绿，D pending。A cost_state 语义 exit 1 仍 OPEN，未获生产修复授权；绿色门禁不覆盖该失败。

**B 同 Owner 新任务续接**：`task_507418789086 / ctx_bf1fdfa6a61e` 取代实现阶段的后续收口安排。当前仅可写 `docs/FC_CLOSEOUT_0929.md`（新、最多两页 H1/H3 索引/下一步）、TASKS 今日段、PLAN 今日附录及本文件状态；`schema-0929-*` 仅独立验收返修需要时。Schema 本体仅在主控传回具体拒收并授权原 nullable 范围时可改，其余生产无写权。B 等主控转发 A/D 完整结果再封存，Owner 自验/独立验收/未解决/NOT_RUN 分开；不评审自己，不修改其他轨道。FC-E 仅只读入口检查：CLI 帮助可用，但原 deepseek-r1 隔离配置和正式工具通道未验证、正式报告缺失，无模型/付费调用。

**11:13 独立验收封存检查点（取代以上 D pending）**：主控确认 A/D 本轮结果齐备，D 最终报告 `969d3274622538a36ac8a60e09c41be86bea9c60` 已 push，索引见 [收口包](FC_CLOSEOUT_0929.md)。D：A focused 20、breaker mutation call_count 红/恢复绿，cost_state 独立语义仍 exit 1；B 原 43/44、修后 44/44，仅 nullable 修复，其他限制保留，H3 pending；C T5 53/双 bundle 字节/3 run replay HTTP→DOM 及缺失/0/多 attempt/可访问性通过，非法 `adoptions=[null]` 的原 app.js 错误（exit 1）为越契约既有限制、未修复。Owner 699/strict 不当作 D 重跑全量。主控 merge-tree 盘点 A/B 无重叠冲突，I 接续隔离集成、组合门禁待实际交付；C 与 FC 自 `605cf48` 分叉且前端文件冲突，本轮分别保留候选，不强合前端或生产 merge/tag。B 已据主控通知封存材料，FC 仍 BLOCKED，不宣称版本统一或三锁完成。

## 顺序、验收与停止条件

1. **计划阶段**：B 核实 HEAD/remote/clean 状态、记录写权，立即回传计划路径与阶段状态；旧计划/历史失败原样保存。
2. **实施阶段**：A 做有意义执行链测试；B 沿用 JSON Schema/jsonschema，保持 optional+nullable，无采集可缺失/null，不伪造 0；0/正数的审计约束、孤立 audit 防护、FaultObservation 14 字段及非 audit 约束保留。C 只做上述只读增量，保留 missing/null 与 live/replay/mock。
3. **同 Owner 自验/返修**：记录实际命令、exit、前后结果和精确 SHA；依赖缺失只上报，不安装/改锁；失效门禁连续两轮即停止上报。阶段 commit，最终 push，trailer `Swarm-Agent: codex`，只暂存所属文件。
4. **独立验收 → 受限集成**：主控在三轨交付后派独立验收/集成 Agent；精确候选、远端一致、changed paths、适用全量/strict/build/SDK 和行为证据分别核验。领域缺陷退回同 Owner；集成仅少量导入/配置/类型/路由胶水。

**冻结仍禁止**：三锁（适用门禁全绿、可接受的 FC-E 无高危报告、真人 H1 签字）未齐，不得生产合并/tag；今天 Codex 独立验收不替代 FC-E v2 正式 deepseek 评审或 H1。昨夜 T3 `2d9d4304cfc0e1a3d4bfaeccb6ec5688aef60366` 两次 mutation 仍绿及裁撤原样有效，仅保留 demo-build.1 后续候选，今日不追认。Schema nullable 已独立通过，仍 `1.0.0 candidate`、待人工 H3；可选字段新增为 minor，optional→required 为破坏性 major（2.0.0），不得称 1.1 可升级必填。

**明确不做**：预算事后对账、unknown 自动退额/重试、人工代签、FC-E 代评、付费 live、T9 正式日志采集/生产接线、T10 演练和额外底层功能。unknown hold 的长期占用与人工处理限制继续存在；只读 replay 验收仅支持 contract_local，不冒充 interface_live/task_live。别轨结果只按主控转发登记。
