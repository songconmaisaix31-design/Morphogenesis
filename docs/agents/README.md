# 原生研究 Agent 启动与接续

产品入口为 `python -m orchestration.native_agents`，无需 Orca、Electron 或桌面状态库。既有 `orchestration/codex.py` 及固定 sample 提案入口保持兼容；本目录调用官方 CLI 的原生工具循环和 MCP，不实现模型 loop、任务调度或派单。上游固定来源、许可和修改说明见 [upstream.md](upstream.md)。

## 支持与实测分别记录

`python -m orchestration.native_agents matrix` 输出 connection=native_cli、精确 expected_version、supported 与 validated。supported 来自已核对的 native help / 行为契约；静态注册表 validated 保持 not_run，实际运行证据由每次探针/测试/最终 I 报告单独记录，不能预写 interface_live。

| 能力 | Codex CLI 0.159.0 | Claude Code 2.1.238 | 本轨实际证据 |
|---|---|---|---|
| 当地版本/原生登录 | 官方 npm bin/codex.js，通过 Node .exe 启动 | 当地 npm bin/claude.exe，原生 .exe | probe 两者 version/auth exit=0，authenticated=true；不调用模型 |
| 交互入口 | argv 提示、--no-daemon、原生终端 | argv 提示、原生终端 | 新建/恢复参数各自 help exit=0；真实 TUI 交互 NOT_RUN |
| headless 工具循环 | exec --json，UTF-8 stdin，保留 session | --print --output-format stream-json --verbose，UTF-8 stdin | argv / 真实子进程 mock 契约通过；原生模型与工具 NOT_RUN |
| 恢复 | exec resume UUID / resume UUID | --resume UUID | 严格 exact UUID，不用 --last、不自动恢复；真实持久会话恢复 NOT_RUN |
| 本地 MCP stdio | 每次 -c mcp_servers.morph_research.* | 独立 JSON --mcp-config | 保留原全局设置；实际科研 MCP 连接 NOT_RUN |
| 结构化事件/usage | thread/turn/item/MCP 原 schema | system init / assistant tool_use / user tool_result / result | fixture 均 mock；未知字段/坏行保留 raw，不填零 |
| 取消与清理 | 仅本适配器创建的进程 | 同左 | Windows Job Object/附着进程不误杀：真实本地子进程通过，非真实模型验收 |
| SDK | 未接入 | 未接入 | supported=null，NOT_RUN；CLI 支持不代表 SDK 通过 |

验证范围仅为上述版本。其他版本先只读 probe，再核对其 help、事件和会话契约；CLI `launch --execute` 对版本不符或认证不明直接拒绝，不替换账号/升级运行时。Python API 调用者也须先核实 probe；低层启动 API 不自行登录。

## 独立研究空间与宿主绑定

B 的官方 FastMCP stdio 启动契约：绝对 Python executable，args=["-m", "swarm.research", "--config", "ABS_TRUSTED_JSON"]。每个 Agent 使用独立宿主配置，包含既有 agent={role,instance}、worker_id、swarm_id、workspace、权限与数据库/归档路径。配置和证据由宿主保护，置于模型可写研究项目之外；同 OS 用户直接访问 SQLite 不由 MCP 参数验证防护，须由原生沙箱/权限及宿主隔离实现。

`build_launch` 检查 B config 的 workspace 与 CLI workspace 一致，只把既有 AgentId/worker_id/swarm_id/config_path 复制到 HostBinding；不复制配置中的凭据或接管 HOME。启动后的 `native.jsonl` 和 `stderr.txt` 是原始日志，`native-bound.jsonl` 用同一 native session/工具 ID 将原事件与宿主身份关联，并 flush/fsync。MCP 回包显式有 `attempt_id` 时只用现有 `contracts.identity.AttemptId` 解析；旧 Lease 没有该字段则保持 unknown，不从 task_id/token 推导另一种身份。reported_attempt_matches_host 只是身份一致性观察，不证明租约仍有效或任务通过；AgentId 不一致即停止且不重放，账本与 fencing 仍由 B 验证。

同一原生 session 可主动发现并处理多个任务；适配层从不选择 task_id，也不实现派单轮询。bootstrap 以研究空间、既有 role/instance、目标、规则和真实工具名提供入口：

```python
from pathlib import Path
import sys
from contracts.identity import AgentId
from orchestration.native_agents import LaunchRequest, McpStdio, ResearchBootstrap, build_launch

workspace = Path("C:/research-project")  # 已存在的隔离项目，Linux 用该宿主自己的绝对路径
host_config = Path("C:/research-state/author.json")  # B 的宿主配置，权限由宿主保护
bootstrap = ResearchBootstrap(
    space="research-demo", agent=AgentId(role="builder", instance=0),
    objective="阅读共享科研问题、证据和经验，自主认领合适任务，记录实验与反例。",
    tool_names=("project_context", "discover_tasks", "lease_task", "search_evidence",
                "research_experiment", "research_candidate", "verify_research",
                "complete_research_task", "approve_candidate", "inherit_experience", "apply_candidate"),
    rules=("通过 lease_task(action=claim, task_id=自己选择的任务) 认领，renew/release/handoff 同一工具。",
           "research_experiment 的 action=request/run/result；research_candidate 的 action=submit/validate_files。"),
)
request = LaunchRequest(
    runtime="codex", workspace=workspace, prompt=bootstrap.prompt(),
    mcp=McpStdio(command=sys.executable, args=("-m", "swarm.research", "--config", str(host_config))),
)
plan = build_launch(request)  # 仅生成 argv，不启动模型
Path("C:/research-state/launch.json").write_text(request.model_dump_json(indent=2), encoding="utf-8")
```

bootstrap 的 role/instance 用于提示；实际身份来自受保护的 B host_config，提示不能更改授权。研究判据与独立复现、候选批准和实际 adoption 全部由 B/C 的既有服务执行，CLI 结束或生成代码不能代替。

上述工具列表对应 B 最终收敛的11工具接口；B早期29446a0阶段仍为17工具。以统一候选上的实际 MCP metadata 为准。事件解析不依赖 claim_task/lease_task 名称，既有 canonical attempt_id 和完整 tool/result raw 都保留，不能因为名称变更丢失认领证据。

## 安全探针、预览与明确执行

```powershell
python -m orchestration.native_agents probe
python -m orchestration.native_agents matrix
python -m orchestration.native_agents launch --request C:/research-state/launch.json --evidence C:/research-state/author-session
```

前两条只读版本/认证，第三条只输出 LaunchPlan；不调用模型、不写 MCP 配置。最终 I 在统一候选、原生权限/预算/可信成本已核实后，可在授权会话额度内给同一 launch 命令加 `--execute --timeout 120 --max-tool-calls 12`。A 分支不运行付费 case；auth true 不等于具有模型配额或 MCP 工具权限。

Claude request.runtime 改为 claude。执行时独占创建 `author-session.mcp.json`，不会覆盖现有文件或用户全局 MCP/auth 设置；Codex 用逐次 TOML 覆盖，不写 config.toml。原生工具/权限保留，默认不增加 bypass flags；Codex sandbox 或 Claude permission_mode/allowed_tools 必须由可信宿主显式提供。CLI 不加入 --ephemeral / --no-session-persistence，也不删除原生会话。

显式恢复需把已观察到的原生 UUID 写入 request.session_id，且宿主确认该 session 当前由自己持有并已停止旧运行。恢复是另一次明确原生调用，可能再次产生外部副作用；不能用于自动重试 unknown。附着 session 仅 `AttachedSession` 元数据，不提供输入注入或 PID 杀进程；live/attached 双向 stdin、外部 TUI 接管、自动恢复均未实现。

Windows headless 使用一次 Python 启动屏障：先给新进程分配官方 Job Object，再送原生 argv，CLI/MCP/工具后代继承 Job，关闭 Job 清理归属后代；原生启动失败日志与屏障 exit 分开，native exit 保持 unknown。POSIX 用独立 session/process group 取消；已经脱离该组的后台 daemon 不在所有权内，父进程正常结束后的外部后台资源不作清理保证。interactive 需要调用者的真实终端，Windows 子进程读取 CONIN$，不会伪造屏幕 ready 信号；此交互路径尚未实测。

headless 的 timeout / max_tool_calls 是观察上限，不能阻止 CLI 在事件被观察前已发出工具请求，不能充当硬美元/Token封顶；interactive 只有 wall timeout，不承诺工具轮次限制。Codex 不提供本适配器可依赖的硬美元上限，Claude 可选 --max-budget-usd 也不能等同 OAuth 实际账单。CLI 报告 usage 与真实费用结算分开；缺失、null、异常值保持 unknown，测得零才是零，Codex cost 一直 unknown。超时/取消/失去观察后整次 usage 保守回到 unknown，原始已报告值仍保留日志。

Claude result 的 is_error=true / error_* 终态优先于 success 字样。失败或未确认终态可能合成 tokens=0 / cost=0：normalized usage 对每个零字段分别置为 null，保留每个有效正数字段及原 raw 数值；成功明确报告的零保持零。真实进程非零 exit 即便 result 写 success-zero，失败 NativeOutcome 的零仍为 null，原成功 event 的已报告零不重写。缺失/部分无效 token 分量不补数；现有多终态汇总须各项已知才汇总，取消/unknown/远端效果规则不变。reported 正数也不等同完整账单，unknown 不能证明没有消耗。

NativeOutcome completed 仅表示原生 terminal event 与 exit=0 相符，不是科研通过；Acceptance 各门禁始终 not_run，由独立验收基于证据另行判定。原失败留存，错误后出现 completed 不抹去错误，evidence_dir 已存在则拒绝再次调用，不重放原 invocation。

## 新增第三种 Agent

复用原生官方 CLI/SDK，先固定版本/许可证并执行无模型 help/auth；新增 RuntimeId 与 registry.RuntimeSpec，显式实现 launch 的 argv/权限/MCP/交互/headless/resume 分支及 events 的真实 schema。不支持的能力保持 null/false、validated=not_run；当前未配置的 runtime 直接拒绝，不能套用 Claude 分支或声称 SDK 通过。每种 runtime 需要自己的 contract-local argv、未知事件/usage/exit、显式 session 恢复和 attached 不误杀测试；精确候选上的真实原生工具/MCP案例由独立 I 证明。

不增加调度器、Attempt系统、Manifest/hash/完成证明或全局配置持久化。Windows 若 CLI 通过 npm .cmd/.ps1 安装，只读取其包的 bin map 并调用 native .exe 或 Node .exe + JS entry；entry 逃逸、未知 shim 或非 native Node 直接拒绝。Linux/WSL 在各自宿主执行同一 Python API，使用该宿主的 PATH 和原生认证；本轨只验证了 Linux/WSL 参数契约，实际 Linux/WSL 原生服务 NOT_RUN。
