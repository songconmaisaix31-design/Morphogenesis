# 验收矩阵

## 现场准备并行收尾（2026-09-22）

从已验收的第四轮网关主链出发，V `1b2e335` 提交可照做的 [投影/7526 回放/7527 真跑清单](tracks/onsite-viz.md)；O `26a5cf1` 给现有观察器增加显式 `--operator-enter`，只有两视口与真实新根均处于 `awaiting_offline`，才等待现场人员一次 Enter，并留时间证据，默认自动行为不变。集成首次完整 Python 测试发现旧 fixture 固定占用 7526，结果 **199 passed / 1 failed**；原 O 会话 `3d05f4e` 将该本地测试改用独立动态端口，原失败项复验 **1 passed / 29.44s**。I 普通合并并推送 `bcd81beac5b9f73ac9f8267ccbc3f571e4faf738`，主线 fast-forward 接收；最终 SHA 的完整 200 项未重新执行，不能记为“200 passed”。

集成额外通过：`node --test tests/integration/test_browser_options.cjs tests/integration/test_operator_enter.cjs tests/integration/test_observer_control.cjs` **31 passed**；`python tools/typecheck.py` **53 文件 clean**；sdist/wheel、SDK、本地安装后 11 包检查通过。7526 回放 API 为 HTTP 200 / replay / 两 live 状态 not_run，双视口真实布局检查通过，29 个第四轮原文件 bytes+mtime 不变；7527 当时无监听。完整命令、日志和原失败见 [I 报告](tracks/onsite-integration.md)。精确候选 [CI 35709392862](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/35709392862) 于记录时仍在运行，未计入通过。

**现场仍待执行：** 目前只检测到一块活动显示屏；17:30–18:00 的借线实接、7526 在实际投影屏全屏可见及 7527 一次新网关真跑，必须由现场见证后分别记录。未收到接通确认前不启动新模型请求；模拟终端测试和浏览器截图均不能证明物理投影。今晚演示执行器为 EvoMap 网关；OpenCode 是备选开发路径，工具调用/流式今晚不测。Hub 保持本地 stub / 待发布；不验证在途进程强杀恢复，路演仅说“成员下线后，后续任务自动重新选路”。

## 网关第四轮：真实软件彩排通过（2026-09-22）

用户批准后，原 R 提交并推送 `94b70816784fcd46ce4f74b8e205bd009b789cc3`；原 I 普通合并后交付入口 `7c0bb6a2f7b39a7eb524c0c71bc31c7a110f883c`，最终只读报告 `61784b73be6b2a47a3a45f8e206678d4f932ae59` 已推送并由主线 fast-forward 接收。协调者在精确入口提交运行唯一第四轮，模型 `evomap-gpt-5.6-luna`，通过已确认的 `https://api.evomap.ai/v1/chat/completions` 执行两个新任务，没有重试。运行首幕至末幕为北京时间 **16:12:31–16:13:35**；观察器为 16:12:23–16:13:36，summary exitCode=0、failure=null、entered=true。

| 第四轮检查 | 实际结果 |
|---|---|
| 两次任务 | repair / recovery 两份全新坏样例，外置 `python -I -S acceptance_runner.py` 各从 0/3 到 3/3，四份独立报告一致 |
| 网关 | 恰好 2 POST、2 HTTP 200；返回模型均 `gpt-5.6-luna`；544+343=887、905+443=1348，合计 **2,235 tokens**，美元费用 unknown/null |
| 选路恢复 | 首任务 builder#0 成功；真实 awaiting_offline 后 stdin Enter 下线；新任务实际由 builder#1 完成，原成员管道 inactive |
| Gene | 2 Gene、1 次实际采用；第二次请求中的完整经验正文、proposal、source_attempt 和最终 UseRecord 对应；τ=10 秒真实墙钟衰减，21 个采样点通过，低于 0.2 后归档并 resolve 为空，数据库缓存正文 0 |
| 现场浏览器 | 1366×768、1920×1080 各捕获全部 20 幕，共 40 张阶段截图（另有两张初始等待画面）；实际图形边界无裁切/标签遮挡，Gene 区在首屏，页面错误 0 |
| 只读审计 | 原运行根 29 份文件 bytes + mtime 未变；旧首轮 CLI 审计仍通过且 35 份文件不变；旧三轮未重跑、不计入第四轮 |
| 本地门禁 | `python -B -m pytest -q --basetemp <私有目录>` **200 passed / 135.27s**；`python tools/typecheck.py` 53 文件 clean；Node 检查、SDK、sdist/wheel、安装后 11 包检查通过 |
| 精确提交 CI | [7c0bb6a / run 35703445239](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/35703445239)：Ubuntu 与 Windows 均 success |
| 凭据 | 仅专用子进程环境使用；Chromium/viewer 排除该变量；164 份运行文本/浏览器记录/跟踪文件扫描无实际凭据样式命中；无全局账号或永久权限规则变更 |

复验命令：集成工作树内 `node tests/integration/observe_rehearsal.cjs manual 7526 .runtime/integration/live-4-gateway-20260922-01 --executor evomap --model evomap-gpt-5.6-luna`，仅执行一次；只读审计为 `python -B tests/integration/audit_rehearsal.py <本轮根>`。证据根为 `C:/Users/DW/AppData/Local/Temp/morph-live4-98b36399c0324192b5af81f8077bc11d/morph-rehearsal-86e5351d49fe49a1b60ba0a4bb4c4e4e`；浏览器 summary、audit、manual-enter、阶段图片在集成工作树 `.runtime/integration/live-4-gateway-20260922-01/`。这些本地产物不入 Git，完整交付命令见 [I 报告](tracks/rehearsal-integration.md)。

原 live viewer 经父子 PID/命令行核验后关闭，观察父进程最终 exit 0。协调者另建 [第四轮只读回放](http://127.0.0.1:7526/)，launcher 47180 → listener 26576，HTTP 成功且 provenance=replay、interface_live/task_live=not_run；日志 `C:/Users/DW/AppData/Local/Temp/morph-replay4-coordinator-5790d05a35a0492699a4b8c356093bfd/`。PID 仅为验收时身份，未来停止前必须重查，不承诺跨宿主生命周期存活。第一轮 7525 回放未操作。

EvoMap 已作为并行开发备选配置加入 [opencode.evomap.json](../opencode.evomap.json)，复用 OpenCode 1.18.31 / MIT 的官方 OpenAI-compatible provider。独立 cwd/XDG 目录与虚假凭据下，配置解析、路径隔离及 7 个代码模型枚举通过；按难度的初始分配见 PLAN，3 个图片模型不进入代码池。**OpenCode 工具调用、流式兼容及其余模型端到端开发尚未实测**，配置可选不等于这些能力通过。

剩余限制：本轮仅证明两任务间的固定成员下线和重新选路，未强杀在途 Agent 进程；物理投影接线/正式现场演示 NOT_RUN；Hub 仍待发布；动态供给与 T4 可选进化未验收；网关费用未知，httpx 分阶段超时不是绝对在途截止或美元硬封顶。

## 本轮验收：固定完整软件彩排已通过

收尾测试限制：`e83a816` 的 Windows CI 35691719303 在采用权重 `> 0.5` 上失败（其余 157 项通过），墙钟 τ=0.1 秒与快照耗时约 0.103 秒给出正确的约 0.356 权重，说明测试依赖机器执行速度。后续主线 `c1542b2` 双平台 CI 35691937011 虽然通过，仍保留该已知测试竞态并由原 R 返修；待验证的新修改不计为完成。本问题不更改三轮 τ=10 秒的真实软件彩排证据。

旧版三次单任务测试不计入本轮三次完整彩排。每轮必须在独立 TEMP 根按顺序观察：真实固定 bug/checkpoint 初始失败 → 模型修复并外部复核 → 管道实际权重变化 → 两任务间下线获胜成员 → 另一成员被选中且完成新任务 → 真实 Gene 生成/采用/墙钟衰减/归档后不可检索。每轮最多两个新任务，未知执行不重试。

| 本轮项目 | 状态 |
|---|---|
| R 运行 / V 展示实现与集成 | 通过；R `652e319`、V 最终 `80220c5`、集成 `e83a816` 已推送并合入主线 |
| 完整软件彩排 1 / 2 / 3 | 通过；manual / auto / auto，均 completed，各两次真实新任务，六次调用无失败、未知或重试 |
| Checkpoint / 成员恢复 / Gene | 每轮两个新坏样例均从 0/3 到 3/3；builder#0 下线后 builder#1 实际执行；2 Gene、1 次真实采用、墙钟 τ=10 秒衰减、低于 0.2 本地归档后实际 resolve 为空 |
| 本地适用检查 | `python -m pytest -q` 158 passed；`python tools/typecheck.py` 52 文件无错误；SDK、sdist/wheel、安装后 11 包/资源/验证器/Node 桥检查通过 |
| 实时页面 / 最终显示修复 | 三轮各两种视口实时跟随全部 20 幕；最终显示修复仅以标记 replay 的只读实图复验，不能说三轮都运行于最终 UI SHA。1366×768、1920×1080 的节点/标签实际边界无裁切或遮挡，Gene 区在首屏 |
| 用户新凭据 API 测试 | 基础鉴权与一次文本生成通过：EvoMap Gateway `https://api.evomap.ai/v1`，`GET /models` 200，Luna `POST /chat/completions` 200 / OK；详情如下。未将网关接入现有 CLI 执行器，未用该 key 重跑三轮 |
| 真实投影接线 / 实际场地彩排 | NOT_RUN；准备时仅检测到一个活动显示屏，软件视口检查不证明物理接线 |

| 轮次 | 北京时间（2026-09-22，运行首幕至末幕） | 新 CLI 调用 | tokens | 结果 |
|---|---|---:|---:|---|
| 1，手动 Enter 下线 | 13:23:40–13:25:30 | 2 | 29,076 | completed |
| 2，自动下线 | 13:26:04–13:27:39 | 2 | 29,014 | completed |
| 3，自动下线 | 13:28:24–13:29:51 | 2 | 29,043 | completed |
| 合计 | 三个独立 TEMP 根 | 6 | 87,133 | 费用均为 unknown/null |

本轮使用既有 Codex CLI / gpt-5.6-luna，不验证用户另给的 API key。原始 CLI turn/usage、四份每轮外部 checkpoint、采用记录及逐点衰减时间均已交叉核对；只读回放前后原始 35 个文件字节和 mtime 未变。路径、全部命令和早期显示失败保留于 [本轮集成报告](tracks/rehearsal-integration.md)。最终边界命令：`node tests/integration/check_rehearsal_layout.cjs http://127.0.0.1:7525 .runtime/integration/layout-final`；原始运行复验命令：`python tests/integration/audit_rehearsal.py <TEMP根>`。

供现场检查的 [本地只读回放](http://127.0.0.1:7525/) 明确标记 replay，interface_live / task_live 为 not_run，不增加模型调用。进程身份、日志与安全关闭/重启命令在集成报告；实际手动入口为集成 worktree 内的 `demo/run-demo.ps1 -AuthorizeLive -Mode manual`。现场投影、Hub 远端与在途进程强杀恢复均不得用本轮软件结果代替。

### EvoMap 模型网关补充实测（2026-09-22，北京时间约 14:12）

用户补充提供方与九个模型显示名后，确认其用途为模型推理。官方 [API Grant 页面](https://evomap.ai/api-grant) 介绍模型 API 额度，与知识图谱 API key / A2A node_secret 分开。实际模型网关为 `https://api.evomap.ai/v1`：同一 `/models` 未带凭据时返回 401 / no token provided，使用本次用户提供的凭据时返回 200。凭据只在请求进程内存中使用，未写入仓库、命令参数、验收记录或 Worker prompt；不跟随认证请求重定向。

| 用户显示名 | 网关实际 model ID | 本次证据 |
|---|---|---|
| Gemini 3.1 Pro | `evomap-gemini-3.1-pro-preview` | 模型目录返回 |
| DeepSeek V4 Flash | `evomap-deepseek-v4-flash` | 模型目录返回 |
| GLM 5.1 | `evomap-glm-5.1` | 模型目录返回 |
| Gemini 2.5 Flash Image | `evomap-gemini-2.5-flash-image` | 模型目录返回；未生成图片 |
| Gemini 3 Pro Image | `evomap-gemini-3-pro-image` | 模型目录返回；未生成图片 |
| Gemini 3.1 Flash Image | `evomap-gemini-3.1-flash-image` | 模型目录返回；未生成图片 |
| GLM 5.2 | `evomap-glm-5.2` | 模型目录返回 |
| GPT 5.6 Luna | `evomap-gpt-5.6-luna` | 模型目录及真实短文本生成通过 |
| GPT 5.6 Sol | `evomap-gpt-5.6-sol` | 模型目录返回 |
| GPT 5.6 Terra（网关额外返回） | `evomap-gpt-5.6-terra` | 模型目录返回 |

最小生成请求：`POST /chat/completions`，Bearer 认证，JSON 为 `{"model":"evomap-gpt-5.6-luna","messages":[{"role":"user","content":"Reply with exactly OK."}],"max_tokens":128,"stream":false}`。实际 HTTP 200，returned_model=`gpt-5.6-luna`，正文 `OK`，finish_reason=`stop`，耗时 4813 ms。usage：prompt_tokens=11、completion_tokens=4、total_tokens=15，美元费用未报告。共一次新推理请求，无重试；它是独立连通检查，不计入前述三轮/六次 CLI 彩排。其余目录模型尚未逐个推理实测，Chat Completions 成功不证明 Responses API、工具调用或现有 Codex CLI 接入兼容。

以下为上一阶段已完成基线的证据，保留精确范围。

协调者核对命令、日志、真实任务产物与最终浏览器截图后记录；AI 生成、Mock 展示和本地测试不替代真实外部验收。详细证据见 [集成报告](tracks/integration.md)。

| 检查 | 结果与边界 |
|---|---|
| 可复现环境 | Poetry / npm 锁安装通过；Python 3.12.13、Node 24.16.0；sdist / wheel 构建通过，11 包及资源安装后检查通过 |
| G1 契约冻结 | 通过：真实调用方与实现方联通；Pydantic / SQLModel / Runtime / Metabolism 语义检查；全实现 strict 50 文件无错误 |
| G2 轨道集成 | 通过：八个功能轨合入，完整 pytest 149 passed |
| 权重影响选择 | 真实 reuse：初始权重 1/1.5，载入前次真实复核反馈后 builder1→builder0，实际执行 builder0 |
| 重复反馈 | 拓扑与代谢测试通过；重复反馈不重复奖励/计次，最终已完成检查点在副本上重复恢复两次也不增加事件或采用记录 |
| 经验使用 | 前次 normal 成功经验正文进入 reuse 执行输入，模型显式报告采用，持久 UseRecord=1；绑定实际 attempt，注入/使用计数各 1 |
| 归档一致性 | 本地 SQLite 事务、检索/缓存及重启测试通过；未证明远端归档同步 |
| 接续 | 真实执行后暂停，新进程恢复复核，总 CLI 调用仍为 1；最终代码另在三个完成检查点副本上各恢复两次，执行器/复核器均未被再次调用 |
| 独立复核 | normal/resume/reuse 均通过外置三个函数测试；最终代码再次复核三个保留候选通过 |
| 受控运行 | 单次调用、超时、停止、路径白名单、发布批准拒绝与 UNKNOWN 不重试通过；单次硬费用/token 上限受公开 CLI 能力限制 |
| SDK 本地接口 | Python→Node 官方 GEP SDK/Ajv 的 schema/hash/tamper 检查通过，published=false |
| MCP 本地接口 | 官方 MCP 客户端与 Server 握手、工具调用通过；输入合成，证据为 contract_local |
| Hub 远端接口 | 未运行。实现当前仅允许 literal loopback，本地 stub 联调不证明正式沙箱接口或发布成功 |
| 模型任务 live | 三次真实任务通过，合计 3 次调用 / 43,166 tokens；费用未知；集成复核新增调用 0 |
| 可视化 | Chromium 真实渲染既有 reuse 导出：5 条消息边、1 Gene、1 来源边、1 采用边，两个 Canvas，三态独立；本地 ECharts 6.1.0；网络/控制台检查通过，截图已查看 |
| Git 交付 | 八轨及独立集成分支已 commit + push；主线接收集成结果并提交验收记录，保留完整历史 |

## 门禁结论

G1 / G2 已通过。G0 的单次调用硬预算仍有限制；G3 / G4 仅完成本地官方接口与固定样例真实任务部分，Hub 外部链路未通过，不能标整体通过。G5 按统一对齐文件指代码冻结/现场演示，现场尚未执行。T4 配置进化是独立可选项，本次未开发。

实际 Orca CLI 多 Worker 属于开发流程；产品运行时供给仍是固定规模逻辑成员 fallback，不能以开发多开冒充运行时动态供给验收。三次固定样例不证明性能提升、最优拓扑或通用自主修复能力。

## 验证命令

命令在集成 worktree 的锁定环境运行，主线使用相同实现。最终报告记录各次检查对应提交。

| 命令 | 结果 |
|---|---|
| `uv tool run poetry check --lock` / `uv tool run poetry install --no-interaction` | 通过，项目独立 .venv |
| `npm ci --no-audit --no-fund` | 通过，锁文件未改 |
| `uv tool run poetry run python -m pytest -q` | 149 passed |
| `uv tool run poetry run python tools/typecheck.py` | 50 source files，0 errors |
| `node --check bridge_node/asset_bridge.mjs`、`node --check tools/check_sdk.cjs`、`node --check viz/static/app.js` | 通过 |
| `npm run check:sdk` | schema_valid / asset_id_verified / tampering_rejected=true |
| `uv tool run poetry run python -m build` | sdist / wheel 通过 |
| 安装 wheel 后 `python -I tools/check_distribution.py --site-dir tools/.wheel-site --check-node` | 11 包、资源、独立验证器、Node 桥通过 |
| `node .runtime/integration/browser.cjs` | 真实 DOM/Canvas/网络/截图通过；无页面或控制台错误 |

wheel 检查复用锁定依赖，目标位于源码目录下，Node 能向上找到源码 node_modules；不代表任意 site-packages 中 Python wheel 单独运行 Node/MCP。完整使用仍需源码 `npm ci`、Node、Codex CLI 和账号。

GitHub Actions 双平台结果：[run 35682995743](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/35682995743) 在精确集成提交 `b6bb49c3112a12f3c0bdcddbddbf2dde453be2e6` 上 **Ubuntu / Windows 均 success**，覆盖锁安装、149 tests、strict、构建、SDK 和安装后分发检查。主线后续只修改本验收、状态、计划与决策文档，业务实现相同。

## 三次真实任务（2026-09-22）

协调者核对了 `%TEMP%/morph-t2-{normal,resume,reuse}-20260922/` 的 summary/result/events/genes/adoption、独立复核输出、实际 CLI 提案及 resume-observation。原始日志和工作目录保留本机临时目录，不提交 Git。

| 场景 | 独立复核 | CLI 调用 | tokens | 费用 |
|---|---|---|---|---|
| normal | 通过 | 1 | 14,327 | 未知/null |
| resume（暂停后新进程接续） | 通过 | 合计 1 | 14,330 | 未知/null |
| reuse（前次真实经验） | 通过，采用记录 1 | 1 | 14,509 | 未知/null |

合计 43,166 tokens 不含开发 Worker 的消耗。使用 gpt-5.6-luna / Codex CLI 0.155.1。单轮结束不自动启动下一轮。

集成恢复复核先复制数据库与 sidecars，再在副本操作。调试首版只读 SQLite backup 曾使 normal/checkpoints.db-shm 的 mtime 改变，bytes 未变；最终副本方案全部原文件 bytes/mtime 断言通过。不能声称整个集成期间所有辅助文件的 mtime 从未变化。CLI 产物、sample.py 和业务证据未因接续重复写入。

## 真实剩余限制与人工项

- 尚无 Hub 正式沙箱地址、凭据及对接契约；接入前需替换当前 loopback 限制为经核验的正式适配，并执行受控发布/发现性验收。未进行生产发布。
- ORCA 产品运行时供给契约未提供，当前固定逻辑成员 fallback；动态供给未验收。
- 公开 CLI 无单次模型调用硬 token/美元封顶。实现仅有限调用、超时、完成后检查 token、未知费用不自动续跑；不能把未知费用记为 0。
- sklearn 字符词法向量 + FAISS 不是语义 embedding；本地经验归档不证明 Hub/Evolver 远端原子同步。
- Orca 内嵌浏览器 helper 返回 browser_owner_unavailable，未修复该全局能力。已用现有外部 Playwright/Chromium 完成页面验证，不等于内嵌浏览器通过。
- T4 可选进化与 G5 正式现场演示未执行；独立测试/语法门也不等于通用敌对代码沙箱。
