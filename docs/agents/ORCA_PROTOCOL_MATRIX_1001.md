# ORCA 全 Agent 接口盘点 / P 复用 Handoff（1001）

本轮仅源码研究与文档交付。核心基线 `c45888f64c1cec60e5f9df45677b6547c4527cac`；ORCA 固定 `85f8d6b5f507df795cd3cef1cdea08124cf801ee`。43 个注册条目均列出，核心 `RuntimeId` 只有 Codex/Claude（`orchestration/native_agents/models.py:14`）；下表的上游支持不代表产品已接入或 live 验收。

## 来源、版本与许可

- 实际来源是 [stablyai/orca 固定提交](https://github.com/stablyai/orca/tree/85f8d6b5f507df795cd3cef1cdea08124cf801ee)。已有只读文件集位于 `C:/Users/DW/orca/workspaces/Morphogenesis/morph-research-agents-0930/docs/agents/.reference`，不是 Git clone，本 D worktree 没有 `.reference`。本轮 GitHub tree SHA 与 `git hash-object --no-filters` 比较了其中22个 ORCA 文件：22/22 精确匹配；`.gitignore` 和独立 Codex Rust 参考文件不计入 ORCA 核验。
- [LICENSE:1–21](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/LICENSE#L1-L21) 为 MIT / Copyright 2026 Lovecast Inc.；已复制许可 `orchestration/native_agents/ORCA_LICENSE.txt` 与参考许可 diff=0。只读补读的官方文件留在进程内，没有扩建源码镜像或复制桌面。
- 固定来源 [package.json](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/package.json) 为 **1.4.214**，声明 `@anthropic-ai/claude-agent-sdk=0.3.251`、`node-pty=^1.1.0`。本机 `orca --version` / `orca status --json` 是 **1.4.212 / ready**；源码与本机发行版不混写。若需要新版兼容性，先交来源/版本 Handoff，本轮没有更新软件。
- 只读已安装 manifest：Codex **0.159.0 / Apache-2.0**，Claude Code **2.1.238 / SEE LICENSE IN README.md**，Node **24.16.0**。这不是认证/调用结果；未复制提供方 CLI/SDK 实现。ORCA 的 MIT 不自动适用于第三方 SDK 或各 Agent，后续依赖须独立核验版本与许可。

## 阅读方式：每族完整能力由共同边界 + 本行覆盖项组成

`S`=固定源码有实现/配置；`D`=仅识别某模式，未提供完整调用契约；`unsupported`=指定 ORCA/核心接口明确不支持；`unknown`=源码证据不足，不能断言提供方不存在该能力。所有本轮模型接口 **NOT_RUN**。引用 `C:27–34` 表示下文来源索引 C 的精确行，均固定上述 SHA。

| 接口维度 | 所有族的共同边界；本行 SC/SD 等覆盖项优先 |
|---|---|
| launch / interactive | `S`：C 启动配置 + L:24–101 拼装，托管 PTY；这不是 Python SDK 实现。Windows/WSL Agent Teams 明确 unsupported。 |
| headless / stdin | H 列 `A/B/O` 是独立一次性文本生成 preset，包含真实 argv/stdin 选择；`D` 只是避免把非交互命令认作 TUI。其余 **unknown**；不能把 HEADLESS matcher 的 false 当“无 headless 能力”。 |
| SDK / Agent stdio / MCP | 默认全部 **unknown**。SC=Claude JS SDK query + stdio；SD=Codex app-server stdio JSON 请求；DSH 的 SDK/ACP stdio 仅有源码描述。Agent stdio、MCP server 的 stdio、PTY stdin 是三件事。 |
| resume / attach | R 列给20族恢复 argv，其余 **unsupported in ORCA resume registry**（R:6–27），提供方自身 unknown。warm attach 复用既有 pane，不得冷启动第二个 owner（R:70–75）；不是任意 PID/socket attach 授权。 |
| cancel | PTY 生命周期由现有 ORCA owner 管理，语义/tool取消 **unknown**；SC/SD 有结构化 turn cancel。核心仅 owned process cancel；外部 AttachedSession.cancel 明确 unsupported/False。 |
| streams / events | 所有 TUI 是 PTY 字节/ANSI，不能当结构化 tool/result JSON。E 列列出已注册 hook/plugin 正规化来源；SC/SD 是 provider stream。没有 E 时结构化事件 **unknown**，不由屏幕字样合成。 |
| token-cost / error | U 列是已有 usage scan，不是统一实时账单或硬预算；其余 **unknown**。headless 通用错误只保存退出与脱敏 stdout/stderr（F:114–186），无全族统一错误码。SC/SD 可传 provider 错误，失败/取消不能证明远端无效果。 |
| auth / permissions / file scope | 所有族的真实本机 auth **unknown/NOT_RUN**；detectCmd 只证明发现。P 列只盘点 ORCA 权限 argv/env，未执行；`—` 表示该权限表未注册/unknown。cwd/trust/yolo 都不证明路径隔离；每族精确 file scope enforcement **unknown**，产品另依赖官方 sandbox + 身份绑定 MCP scope。 |

stdin 模式缩写：`argv` 位置参数；`paste`=`stdin-after-start`（PTY 输入，不是 headless stdin）；`prompt`=`flag-prompt`（`--prompt`）；`prompt-interactive`=`flag-prompt-interactive`（`--prompt-interactive`）；`interactive`=`flag-interactive`（`-i`）；`query`=`hermes-query`。实际 flag 拼装见 `src/shared/tui-agent-startup.ts:118–175`，不把 shell 字符串直接搬到 Python。

## 43族逐项映射

H 的 A/B/O 来源下文列明；R 是 `getAgentResumeArgv` 行；E 是 `provider-dispatch` switch 行（`openclaude` hook installer 独立但读取 Claude 格式）。P 是 permissions 的行号，**这里只给位置，绝不选择上游 yolo 为产品默认**。U 指来源 U/V 的 usage scan；空缺一律 unknown。未标 SC/SD 的族沿用上表 SDK/stdio/MCP/attach/cancel 等完整边界。

| Agent / C行 | detect → launch；交互stdin | H / headless transport | resume（R行） | E / 结构化来源 | P行；token-cost |
|---|---|---|---|---|---|
| claude / 27–34 | claude；argv | A:31–47，`-p` / stdin；SC | `--resume ID` 284–285 | E:67–69；SC | P:7；U/V Claude |
| claude-agent-teams / 35–52 | orca(+claude) → `orca claude-teams`；paste；win32/wsl unsupported | unknown | unsupported | unknown（不是独立 provider SDK） | P:9；unknown |
| codebuddy / 53–57 | codebuddy/cbc；argv | D，`-p`/`--serve`/`--acp`/`--bg`（H、HB） | `--resume ID` 282–283 | E:57–66 | P:8；unknown |
| openclaude / 58–62 | openclaude；argv | unknown（不能从 Claude 继承 query 支持） | unsupported | K:46；N:43–46 读取 Claude transcript | P:10；unknown |
| codex / 63–71 | codex；argv | A:80–100，`exec` / stdin；SD | `resume ID` 286–287 | E:70–72；SD | P:11；U/V Codex |
| autohand / 72–75 | autohand；paste | unknown | unsupported | unknown | P:19；unknown |
| ante / 76–80 | ante；paste | D，`--prompt/-p`（HA:3–16） | unsupported | unknown | P:35；unknown |
| trae / 81–90 | traecli；argv+`--` | D，print/json（H:23） | unsupported | unknown | P:36；unknown |
| opencode / 91–102 | opencode；prompt | A:155–171，`run` / stdin | `--session ID` 294–295 | E:90–107 plugin | —；U/V OpenCode |
| opencode2 / 105–112 | opencode2 → `opencode2 --standalone`；prompt | A:191–204，`run` / stdin | `--standalone --session ID` 296–299 | E:90–107 plugin | —；unknown（不泛化 OpenCode scan） |
| mimo-code / 113–118 | mimo；prompt（ready signal 未单独验证） | unknown | `--session ID` 308–309 | E:90–107 plugin | —；unknown |
| pi / 119–126 | pi；argv；prefill env | A:218–233，`--print --mode text` / stdin，无tools | `--session FILE` 300–303 | E:111–122 extension | —；unknown |
| omp / 127–133 | omp；argv；prefill env | O:92–108，`--print --mode text` / stdin，无tools/extensions | `--resume FILE-or-ID` 316–323 | E:111–122；N:25–27 local transcript | —；unknown |
| prime-agent / 134–143 | prime-agent；argv+`--` | D，print / mode json,rpc,acp,daemon（HP:3–21） | `--resume FILE` 304–307 | E:111–122 extension | —；unknown |
| qoder / 144–148 | qodercli；prompt-interactive | D，print/stream-json/acp等（HQ:3–30） | `--resume ID` 288–289 | E:164–166 | P:12；unknown |
| gemini / 149–152 | gemini；prompt-interactive | unknown | `--resume ID` 290–291 | E:73–75 | P:13；unknown |
| antigravity / 153–164 | agy；prompt-interactive | B:259–272，`--print=TEXT --sandbox` / argv | `--conversation ID` 292–293 | E:76–86 | P:14；unknown |
| aider / 165–168 | aider；paste | unknown | unsupported | unknown | P:15；unknown |
| goose / 169–172 | goose；paste | unknown | unsupported | unknown | P:40–42 env；unknown |
| amp / 173–176 | amp；paste | B:22–35，`--execute` / stdin | unsupported | E:87–89 | P:16；unknown |
| kilo / 177–180 | kilo；paste | unknown | unsupported | unknown | —；unknown |
| kiro / 181–187 | kiro-cli → `kiro-cli chat --tui`；paste | unknown | unsupported | unknown | P:17（chat位置）；unknown |
| crush / 188–191 | crush；paste | unknown | unsupported | unknown | P:18；unknown |
| aug / 192–196 | auggie；paste | unknown | unsupported | unknown | —；unknown |
| cline / 197–200 | cline；paste | unknown | unsupported | unknown | P:20；unknown |
| freebuff / 201–204 | freebuff；paste | unknown | unsupported | unknown | —；unknown |
| codebuff / 205–208 | codebuff；paste | unknown | unsupported | unknown | —；unknown |
| command-code / 209–215 | command-code → `command-code --trust`；argv | unknown | unsupported | E:126–144 | P:21；unknown |
| continue / 216–220 | cn；paste | unknown | unsupported | unknown | P:22；unknown |
| cursor / 221–226 | cursor-agent；argv | B:57–72，`--print --mode ask` / argv | unsupported | E:108–110 | P:23；unknown |
| droid / 227–233 | droid；argv | unknown | `--resume ID` 310–311 | E:123–125 | P:37；unknown |
| kimi / 234–240 | kimi/kimi-code；paste | B:78–95，`--prompt TEXT --quiet` / argv | `--session ID` 329–331，cwd绑定 | E:167–169 | P:24；unknown |
| mistral-vibe / 241–246 | vibe/mistral-vibe；paste | unknown | unsupported | unknown | P:28；unknown |
| qwen-code / 247–251 | qwen；paste | unknown | unsupported | unknown | P:29；unknown |
| rovo / 252–255 | rovo；paste | unknown | unsupported | unknown | P:30；unknown |
| hermes / 256–262 | hermes → `hermes --tui`；query | unknown | unsupported（R:267–271） | E:158–160 | P:31；unknown |
| openclaw / 263–266 | openclaw；paste | unknown | unsupported | unknown | —；unknown |
| copilot / 267–273 | copilot；interactive | B:161–176，`--prompt TEXT --stream off` / argv | `--resume=ID` 324–328 | E:155–157 | P:32；unknown |
| grok / 274–285 | grok；argv+`--` | unknown | `--resume ID` 312–313 | E:145–154；N:25–27 local transcript | P:33；unknown |
| muse / 286–291 | muse → `muse --trust-workspace`；paste | B:113–134，`exec -- TEXT` / argv | `resume ID` 332–333 | E:170–172 | P:25；U/V Muse |
| dsh / 292–309 | dsh-tui/dst(+dsh)，expected=dsh；paste | B:140–159，`dsh --profile headless -` / stdin；DH:1–18 描述sdk/sdk-minimal/acp JSON-RPC stdio | `--resume ID` 336–339，cwd绑定 | E:173–175 | —；unknown |
| zcode / 310–322 | zcode，expected=zcode-cli；paste | D，`-p/--prompt/--target`（HZ:3–19） | `--resume ID` 334–335 | E:176–178 | P:26–27；unknown |
| devin / 323–327 | devin；paste | unknown | `--resume ID` 314–315 | E:161–163 | P:34；U仅列provider ID，实际scan unknown |

SC 证据：Claude SDK **JS** `query({prompt: async iterable, options})`，cwd/env/CLI binary/`canUseTool` 见 `src/main/claude/claude-stream-json-connection.ts:115–142`，三根 pipe 见 `claude-agent-sdk-process-spawn.ts:45–79`，turn cancel 见 `claude-structured-session-adapter.ts:196–204`。SDK 不是现有核心 Python 已导入的能力；其源码只挑选部分 Options，不能凭 query 推断 ORCA 已暴露完整 MCP 配置。

SD 证据：`src/main/codex/codex-app-server-connection.ts:34–69,196–238` 持久子进程/请求；`codex-structured-turn-cancellation.ts:9–40` 调 `turn/interrupt` 并等待取消判定。它是官方 app-server 协议适配，不能标成 ORCA 使用 Codex SDK。结构化 router 只 `claude | codex`（`src/main/native-chat/agent-session-wire/structured-agent-session-adapter-router.ts:9–24`）；远端/WSL/account gate 见 `structured-agent-session-create-support.ts:19–47`，不能由43族 TUI支持推导同等结构化支持。

MCP 配置发现：`src/shared/mcp-config.ts:24–70` 只定义 stdio/http/unknown 及 `.mcp.json`、Cursor、Claude候选；发现配置不证明工具可调用。19种 managed installer 在 K:44–64；24种 hook source 在 `src/shared/agent-hook-relay.ts:37–62`，plugin/extension 与 managed install 状态不同。OpenClaude 不是独立 hook source discriminator，不伪造新事件格式。所有 hook installed/partial/error/skipped（`agent-hook-types.ts:29–43`）仍需实测，不读取或改写全局配置。

## P 最小完整接口适配：复用核心 Python 包，不搬桌面

以下行均在核心冻结基线；P 固定依赖完整核心 SHA，角色/科研权限/启动归档属于产品入口。现有 `__init__.py:3–10` 已导出入口，不再制造 dispatcher、Attempt/Manifest/hash/账本。

| 产品需求 | 核心现有位置 | 真实缺口 / Handoff |
|---|---|---|
| 发现/选择已安装CLI | `registry.py:28–35,49–87` RuntimeSpec、npm真实bin；`:95–127` probe | P默认启动不隐式换provider/model；本轮只读manifest，probe含auth所以未执行。41族尚未实现，不扩大RuntimeId骗过类型。 |
| typed launch / headless / interactive | `models.py:52–100`、`launch.py:10–73`、`process.py:85–90,124–145` | headless Codex exec --json、Claude print stream-json；交互继承真实终端，未实现PTY UI/ready/实时stdin API。无需Electron/node-pty/Zustand。 |
| MCP stdio / host身份 | `models.py:35–49,83–100`、`launch.py:16–26,31–36,51–56,76–81` | 官方FastMCP `swarm/research/server.py:3,11–110`，HostConfig `models.py:8–23` scopes；配置独占创建，不改HOME/账号。这里是科研工具宿主，不是Agent自身MCP server。 |
| 会话resume / attach / cancel | `models.py:67–79`、`launch.py:41–48,63–64`、`process.py:24–90` | exact UUID；attach仅元数据并拒绝kill。owned进程树清理返修归A，本基线尚有父进程先退出的缺口；后续合入A精确SHA，不复制新清理器。 |
| streams / events / token-cost / error | `events.py:13–31,57–145`、`process.py:157–265`、`models.py:103–126` | raw保留；unknown事件保留；CLI完成≠科研通过；取消/失败合成zero→null，已知正值保留；Codex成本无报告为null；remote_effect固定unknown，不重试。 |
| 科研权限与file scope | `models.py:60–79`、`launch.py:29–36,59–68` + HostConfig/现有Ledger | 基础build_launch没完整科研参数：P正式入口须拥有per-tool审批、禁其它工具/服务器、sandbox等官方配置。旧runner `tests/integration/run_research_native.py:173–209` 提供已有配置证据，测试脚本不得继续承担正式权限。 |
| 官方SDK/双向Agent stdio | registry `sdk.supported=None`（`:25`） | SC/SD是后续复用来源，不是已实现Python能力；本轮不新增依赖、解析器或SDK包装。 |

顺序锁：**A进程清理 + P正式安装入口 → 冻结三角色完整原checker通过 → NIST案例抽离及第二类任务通过 → D同Owner新增运行时**。此前只交来源/映射/缺口，不启动模型或native/live，不更改核心启动。本轮 EvoMap 明确后置。

## 紧急 Handoff：Codex exact11 与原checker的真实边界

固定 [openai/codex rust-v0.159.0](https://github.com/openai/codex/tree/rust-v0.159.0)，不是ORCA MIT源。官方 [spec_plan.rs:1132–1144](https://github.com/openai/codex/blob/rust-v0.159.0/codex-rs/core/src/tools/spec_plan.rs#L1132-L1144) 在 `mcp.has_servers()` 时注册三个资源helper；[1269–1271](https://github.com/openai/codex/blob/rust-v0.159.0/codex-rs/core/src/tools/spec_plan.rs#L1269-L1271) 根据model capability注册apply_patch。`features.shell_tool=false`只影响shell门（1083–1087），read-only限制执行权限；`mcp_servers.morph_research.enabled_tools`只筛服务器工具，均不是全模型工具目录exact11。

公开 [TS SDK ThreadOptions:18–30](https://github.com/openai/codex/blob/rust-v0.159.0/sdk/typescript/src/threadOptions.ts#L18-L30) 无全工具白名单；官方 [config.schema.json:4247–4259](https://github.com/openai/codex/blob/rust-v0.159.0/codex-rs/core/config.schema.json#L4247-L4259) 的tool_registry只有碰撞/元数据字段，ToolsToml只有plan/user-input/web选项。**现有官方headless CLI/TS SDK配置下，完整模型目录exact11未得到可行支持证据，不应宣称已满足。**

官方app-server [ThreadStartParams:62–151](https://github.com/openai/codex/blob/rust-v0.159.0/codex-rs/app-server-protocol/src/protocol/v2/thread.rs#L62-L151) 提供config overrides和附加dynamicTools；[ThreadResumeParams:354–410](https://github.com/openai/codex/blob/rust-v0.159.0/codex-rs/app-server-protocol/src/protocol/v2/thread.rs#L354-L410) 提供config overrides，均未见ToolPolicy白名单字段；不能把换用stdio/app-server或追加dynamicTools当全目录过滤。

有一个不同的官方能力：[Rust ExtensionDataInit ToolPolicy.allowed_tools:6–20,37–44](https://github.com/openai/codex/blob/rust-v0.159.0/codex-rs/ext/extension-api/src/tool_policy.rs#L6-L44) 是启动前嵌入式工具上限，registry/hosted specs应用它（spec_plan:150,356）。这不是既有CLI/TS SDK配置入口，不把嵌入Rust核心改造包装成现有Python产品能力；本轮不使用自造catalog、monkeypatch、model/provider/auth替换来实现它。

原 `tests/integration/check_research_live.py:141–144` 只断言**实际调用名**属于11个MCP工具，`:153–161` 断言launch权限；不检查完整模型目录恰好11项。本轮保持checker字节与基线一致、不运行、不削弱它。三项必须分别留痕：server tools/list=11、允许/实际调用⊆11、完整模型工具曝光exact11；前两项不能代替第三项，更不能把源码推断标为live。若用户要求第三项，主控/P需记录未满足限制并决定官方支持路径，不能默改验收定义。发现已通过 `msg_e5d6b19309d3` 发主控转P。

## Case02 只读诊断：Code Mode 与直接 MCP 候选

本节固定官方 [Codex rust-v0.159.0 / 687a119f0fcaace47e1f1abcc77cec6c813fd6da](https://github.com/openai/codex/tree/687a119f0fcaace47e1f1abcc77cec6c813fd6da)，[Apache-2.0](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/LICENSE)。仅源码诊断 prepared；不代表模型可用或 live 通过。

实际 case02 的只读证据位于 `morph-research-integration-1001-state/research-formal-1001-02-state`：`interrupt-native/native.jsonl:1–7` 记录 UUID `01a0f553-a495-7c12-98b6-afa311fce378`、两个官方 error item（memory_tool 弃用及 host disabled）、Agent 报研究入口不可达与 turn.completed；`stderr.txt:1` 为 router 的 `code-mode host is disabled`。`native-bound.jsonl:2–3` 的 event 是 unknown、tool_name=null，不能将官方 error 当已执行工具。P 的 guard 分类返修与研究入口可达性是两个问题。实际研究工具调用为0、未认领/实验；raw :7 已响应 input30763/output349（cached_input15104、reasoning_output119），不能声称没有模型外部效果或零费用。旧 raw、cancelled、unknown/null 和原完整 checker RED 均保留。

当前终端仅选择性读取顶层非秘密 `model` 得 `gpt-6.1-sol`，本机该模型缓存 `tool_mode=code_mode_only`；launch request.model=null，**当前配置/缓存不是 case02 实际请求 metadata 的证明**。官方 [tools/mod.rs:75–96](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/core/src/tools/mod.rs#L75-L96) 让 model_info.tool_mode 优先于 code_mode/code_mode_only features；host 不可用的 Direct 回退只适用于 CodeMode，CodeModeOnly 继续 fail closed。[disabled provider:88–101](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/code-mode/src/remote_session.rs#L88-L101) 拒绝创建 session，[warning:108–121](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/core/src/tools/code_mode/mod.rs#L108-L121) 与实际 raw 一致。故三个 feature=false 并不覆盖模型指定模式；对 CodeModeOnly 的默认 nested/deferred MCP 暴露，关闭 host 使 discovery/执行路径不可用。这是源码支持的根因解释，未重建 case02 模型请求。

给 P 的最小官方配置候选，仅增加服务器级参数：

```text
-c mcp_servers.morph_research.omit_tools_from=["deferred","code_mode"]
```

原 enabled_tools=11、defaultprompt、per11approve、read-only、never、禁 host/shell/js_repl 等继续保持；D 不改产品配置。完整来源判断链：

| 官方源码（同一固定 commit） | 结论 |
|---|---|
| [mcp_types.rs:267–270](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/config/src/mcp_types.rs#L267-L270)、[config_types.rs:396–407](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/protocol/src/config_types.rs#L396-L407) | server 支持 omit_tools_from，枚举为 snake_case direct/deferred/code_mode。 |
| [spec_plan.rs:235–268](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/core/src/tools/spec_plan.rs#L235-L268) | ALL 减去 deferred/code_mode，得到 DirectModelOnly，不经过 deferred 选择。 |
| [tool_executor.rs:68–96](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/tools/src/tool_executor.rs#L68-L96)、[spec_plan.rs:553–590](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/core/src/tools/spec_plan.rs#L553-L590)、[794–805](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/core/src/tools/spec_plan.rs#L794-L805) | DirectModelOnly 是 direct、不是 code-mode available；进入模型列表，CodeModeOnly 的 nested 隐藏条件不命中。provider 不支持 namespace 时仍会过滤 namespace spec，不能推定所有 provider 可用。 |
| [spec_plan.rs:825–839](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/core/src/tools/spec_plan.rs#L825-L839)、[653–665](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/core/src/tools/spec_plan.rs#L653-L665) | DirectModelOnly 被排除出 nested；search 取决于模型与 provider 能力，旧 tool_search feature=false 不能作为关闭 discovery 的证明。该11工具候选不再以 metadata/tool_search 为必经路径。 |
| [官方测试:1003–1067](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/core/tests/suite/mcp_tool_exposure.rs#L1003-L1067) | mock 请求断言 direct-only MCP 在 CodeModeOnly 仍 top-level、不 deferred、不 nested；D 未运行该测试，也不能用它证明真实模型接受。 |

P 提到的 direct_only_tool_namespaces 是另一官方方案：[feature_configs.rs:39–46](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/features/src/feature_configs.rs#L39-L46) 与 [config/mod.rs:2990–2994](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/core/src/config/mod.rs#L2990-L2994) 表明配置来自 features.code_mode 对象；不是裸 code_mode 表。它要求规范化后的 exact namespace，[MCP tools.rs:107–142,225–233](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/codex-mcp/src/tools.rs#L107-L142) 存在前缀/消毒/碰撞处理；本轮未取得 case02 tools/list 的实际 wire metadata，故不猜名称，优先服务器级 omit 候选。

metadata 与 effects 边界：官方 [globals.rs:22–48,70–101](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/code-mode-runtime/src/runtime/globals.rs#L22-L48) 的 ALL_TOOLS 是 exec 内工具元数据，不是独立科研业务调用；读它仍需能运行该 JS cell。raw 未保存 metadata 函数的实际调用名，不能补造。开启 host 会允许 [V8 JS 模块执行:9–43](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/code-mode-runtime/src/runtime/module_loader.rs#L9-L43)，[imports:225–237](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/code-mode-runtime/src/runtime/module_loader.rs#L225-L237) 拒绝外部模块；不因此自动执行 Python/shell，也不能声称无 effect：nested 调用会 [dispatch 到真实工具:335–412](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/core/src/tools/code_mode/mod.rs#L335-L412)。此候选继续禁 host；已有资源 helpers、model-driven apply_patch 和 [exec/wait 注册:932–936](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/core/src/tools/spec_plan.rs#L932-L936) 不会因此全局移除，完整目录 exact11 仍未满足。

原 checker :141–144 的实际调用⊆11及 :153–161 的权限断言可原样保留；真正是否成功须原三角色完整 checker 判断。若模型仍调用额外 discovery/exec/helper，应保持 RED，不能修改原11标准。当前候选仅 source-prepared；modelrequest、开启 host、模型/提供方更换均 NOT_RUN，由根主控裁决。没有必须换模型/开代码执行的源码结论，也没有当前模型实际成功的证据。

### 验收返修：startup notice 不是 fatal，但必须精确兼容

上一轮遗漏了 notice 语义，surface proof 本身不足以释放入口。以下仍固定官方 `687a119`，不扩工具盘点。**CodeModeOnly + host=false 的首次警告必发一次，与 direct11 exposure 无关；它是 WarningEvent，不是 fatal ErrorEvent。** [turn_input.rs:353–365,485–487](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/core/src/session/turn_input.rs#L353-L365) 在启动 turn task 前调用；[turn_context.rs:1312–1324](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/core/src/session/turn_context.rs#L1312-L1324) 仅检查 host availability、requested CodeMode/CodeModeOnly、service 的 once 状态，不检查 MCP/tool exposure；[code_mode/mod.rs:108–121](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/core/src/tools/code_mode/mod.rs#L108-L121) 用 availability.err 和 AtomicBool.swap 生成一次文字，再由 caller send_event(WarningEvent)。direct11 候选不会消除警告；服务已经发过时不重复，不能把“首次条件满足”说成所有 turn 无条件发。

官方 [bespoke_event_handling.rs:274–281,1017–1024](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/app-server/src/bespoke_event_handling.rs#L274-L281) 将 Warning/DeprecationNotice 保留为各自 ServerNotification；[exec JSONL:409–418,442–472](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/exec/src/event_processor_with_jsonl_output.rs#L409-L472) 却把两者都变为 `item.completed` / `item.type=error`，返回 Running、不写 last_critical_error。真正 Error notification 在同文件 :447–457 发顶层 `type=error` 并记录 critical error；[:525–557](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/exec/src/event_processor_with_jsonl_output.rs#L525-L557) 按 TurnStatus 发 turn.completed 或 turn.failed，因此官方 startup notice 后仍 completed 正常；completed 不证明科研成功。

memory_tool 是同类非fatal弃用通知：[legacy.rs:40–43,85–94](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/features/src/legacy.rs#L85-L94) 的 Some(false) 也记录 alias usage；[features/lib.rs:743–757](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/features/src/lib.rs#L743-L757) 生成 summary/details，[session.rs:1231–1238,1812–1842](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/core/src/session/session.rs#L1231-L1238) 装为 DeprecationNotice，在 SessionConfigured 后发。case02 raw :1–4 确认为 thread.started → deprecated ErrorItem → host warning ErrorItem → turn.started，:7 completed；bound :2–3 仍 unknown/null。归档状态、原红、模型响应/用量不回写。

**支持决定按 root `msg_3de099d9d0f9` / P `msg_0230d128ca92` 收窄：仅固定版本、已审 direct-only own MCP/required11/per11/defaultprompt/read-only/never/hostfalse 正式 plan 下，官方 item.completed/error envelope 加完整 host-disabled message 可单列 compatibility_notice，保留 raw 与单独计数。** 完整 message 必须保留反引号和标点：

```text
Code Mode is unavailable because code-mode host is disabled. Code mode will fail closed; enable `features.code_mode_host` and install `codex-code-mode-host`.
```

D 的初始两notice语义识别提议不扩大 root 批准：memory_tool deprecated **不豁免**，P 删除 alias、保留 memories=false。未知 ErrorItem、ConfigWarning、model reroute、顶层 error、turn.failed，以及同文字的顶层 fatal 均继续停止；真实非研究工具调用仍按原权限停止，科研工具预期业务拒绝按原合同/checker处理。

[exec_events.rs:8–36,308–312](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/exec/src/exec_events.rs#L308-L312) 的 ErrorItem 只有 message（外层 id/type），**wire 已丢源 severity/notice 类型**；wording/启动顺序是固定已知 case 的佐证，不能通用可靠反推所有 item.error 严重性，不以 contains/prefix/单纯位置或最后 completed 豁免。未知版本、文字、上下文保持 fail closed；若需完整 typed severity，官方 ServerNotification 保有 Warning/Deprecation/Error 区别，但换入口不属于本次授权。此 known warning 不是必发 fatal 的 block，不必开启 host/换模型；实际模型是否选择 direct11仍 NOT_RUN。另 [execute_handler.rs:85–100](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/core/src/tools/code_mode/execute_handler.rs#L85-L100) 将 disabled host 的真实执行失败映射 RespondToModel；router stderr ERROR 不是 startup notice，也不必导致 turn.failed，不能被 notice 分类掩盖。

## Case03 metadata 网络与继承配置诊断

仍固定官方 Codex `687a119` / rust-v0.159.0 / Apache-2.0，仅只读诊断与这两文档。事实源为 I 的 `morph-research-integration-1001-state/research-formal-1001-03-state`：native :1–3 是 UUID `01a0f57a-2412-7dd1-9392-685f15a75fd3`、priority 未 advertised、metadata not found/fallback；stderr :1–2 两次 `failed to refresh available models: request timed out`。12.605616s，无 turn/modelreply/研究工具/claim/实验；归档 outcome unknown、tokens/cost=null 不变。I 既有 `formal-1001-03-full-checker-first.exit:1` 为1，log :20 缺 resume-observation，证据 SHA `06ee5e4beec2fb92d88fdc0e172ce3dc7de12fed`；未重跑原checker。无回复不是远端效果/费用零，case02同模型回复不能证明case03 metadata正确。

**已确定的失败链是 catalog refresh deadline 失败、匹配 metadata 缺失、fallback descriptor、priority 被 omit；历史 timeout 的底层 DNS/TLS/proxy/auth/server 原因仍 unknown。** 不把本地 fallback 当实际模型无效或可用的证明，不扩 host known-warning 白名单。

| 固定官方运行路径 | 来源与结论 |
|---|---|
| HOME / provider / auth | [home-dir/lib.rs:13–61](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/utils/home-dir/src/lib.rs#L13-L61) 用 CODEX_HOME，否则系统 home/.codex；[config/mod.rs:3800–3813](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/core/src/config/mod.rs#L3800-L3813) 合并 provider/默认openai；[provider-info:419–437](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/model-provider-info/src/lib.rs#L419-L437) 按 auth mode/default 选 Codex backend 或 API base，显式base优先。[loader:126–134](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/config/src/loader/mod.rs#L126-L134) 还有 system/cloud/user/profile/project/runtime 层；不能只凭 HOME 配置断言历史完整effective config。 |
| 刷新 / 缓存 | [session/mod.rs:638–661,712–714](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/core/src/session/mod.rs#L638-L661) root session 使用 OnlineIfUncached再取metadata；[manager.rs:31–32,282–286](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/models-manager/src/manager.rs#L31-L32) HOME/models_cache.json TTL300s；[cache.rs:200–216](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/models-manager/src/cache.rs#L200-L216) 拒绝版本不符/过期，[manager:607–643](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/models-manager/src/manager.rs#L607-L643) 另验证provider/auth identity。身份按 [models_identity.rs:13–47](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/model-provider/src/models_identity.rs#L13-L47) 对provider路由/账号/plan等做digest，本轮不读取/导出这些身份或token值。 |
| endpoint / deadline | [models_endpoint.rs:95–134,150–183](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/model-provider/src/models_endpoint.rs#L95-L134) 选官方auth/provider路由，并将transport build、GET、decode包在5秒deadline；[API models.rs:33–45,97–115](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/codex-api/src/endpoint/models.rs#L33-L45) GET models 加client_version，无model请求body。public /v1/models不能替代Codex capability metadata；自配catalog仅是官方支持入口，不授权自造目录或换endpoint。两条timeout不能仅凭时间戳精确归属各caller/网络阶段。 |
| fallback / tier | [model_info.rs:98–146](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/models-manager/src/model_info.rs#L98-L146) fallback service_tiers空、tool_mode=None、used_fallback=true；[session/mod.rs:813–819,916–922,1076–1107](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/core/src/session/mod.rs#L1076-L1107) 检查继承tier的advertised支持，缺失则omit并Warning；[turn_context:1298–1309](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/core/src/session/turn_context.rs#L1298-L1309) 对fallback另Warning。与case02相同JSONL映射会丢notice类型；非fatal并不等于可豁免metadata失真。不能由此认定远端实际不支持priority。 |

实际继承边界：I `formal-1001-03-interrupt.command.json` 绝对调用 `morph-research-agents-install-c25-1001-state-ctx22e488c4a387/venv/Scripts/morph-research.exe`；其**真实installed** site-packages `orchestration/native_agents/registry.py:90–92` 只过滤 ORCA_*，`process.py:135,142` 使用 child_environment，`morph_research/auth.py:16–30` 仅按Claude选项临时排除/恢复ANTHROPIC键。native launch/probe实际仍 `C:/Program Files/nodejs/node.EXE` + 全局npm `@openai/codex/bin/codex.js`，0.159/authenticated=true、auth声明 inherited-selected/model inherited_unchanged。I `msg_02bceade7532` 确认不activate A venv，gate仅TEMP/TMP/BLAS/MYPY缓存调整。因此无 A venv 改Codex身份的源码证据；parent/child env未归档，不能补造历史逐键证明。

当前 D/I 安全键检查：USERPROFILE=C:/Users/DW，CODEX_HOME/HOME/OPENAI_BASE_URL/HTTP_PROXY/HTTPS_PROXY/ALL_PROXY/NO_PROXY不存在；默认配置路径推导为 `C:/Users/DW/.codex/config.toml`，选择性非秘密字段 model=gpt-6.1-sol、service_tier=priority，无读到的system/project配置覆盖这些字段。当前 cache fetched `2026-10-01T03:04:06.344673900Z`、client_version0.158.0、无该slug，0.159不能复用且已超TTL；**当前文件不是case03时点快照**，不能据此证明旧cache究竟因version/TTL/identity哪项失效。只检查auth.json存在性，不读凭据；未dump auth/env/provider。现装官方 `debug models --bundled` exit0、内置metadata无该slug；[cli/main.rs:2068–2095](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/cli/src/main.rs#L2068-L2095) 的bundled分支跳过config/auth/network，此发现只说明需要正确远端metadata，不能证明实际model有效。

有界无凭据网络观测（D当前 `2026-10-01T03:27:56Z`）：chatgpt.com DNS=198.18.1.88；TCP443 7ms通过；TLS1.3校验通过973ms；官方 `/backend-api/codex/models?client_version=0.159.0` HEAD返回405/1186ms，无认证、无redirect follow/响应body归档。Windows .NET 当前system proxy为 `http://127.0.0.1:7890`、无URL credential，与代理env absent并存。官方 [config/mod.rs:1688–1704](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/core/src/config/mod.rs#L1688-L1704)、[outbound_proxy.rs:100–104](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/http-client/src/outbound_proxy.rs#L100-L104)、[windows.rs:53–93](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/http-client/src/outbound_proxy/windows.rs#L53-L93) 区分 transport-default 与显式system/PAC路由。这不是旧Codex authenticated GET的route/身份/时点复现，405不能认定metadata已恢复、auth正确或proxy有错。

root `msg_7b6072e819f8` 要求核对 ORCA 供给路径；`msg_883d378dd578` 明确批准官方非bundled metadata 检查、正常cache写入/既有认证访问及必要正常刷新，`msg_96aabbb0c304` 仅在默认失败时批准一次进程级system proxy对照，均已读取并ACK。当前 `orca account list --json` 的host选中 managed id `2a305740-3098-46da-a63f-2d9e42ae9d72`；路径 `C:/Users/DW/AppData/Roaming/orca/codex-accounts/<id>/home` 实际存在及有ownership marker。CLI无秘密摘要的selected/default provider及workspace身份在内存比较均相等，未打印身份原值；两路径top config均gpt-6.1-sol/priority，但目录不同、当前相等不能证明03历史身份。固定ORCA [managed-home-path.ts:17–28](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/main/codex-accounts/codex-managed-home-path.ts#L17-L28) 定义userData账户root；[runtime-home-service-launch.ts:83–111](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/main/codex-accounts/runtime-home-service-launch.ts#L83-L111) 提供selected HOME无副作用解析，managed选择返回其owned home，default real-home返回null。产品若要声明复用当前ORCA选择，应通过既有供给路径解析并保留身份边界，不能把省略CODEX_HOME当已接入selected-home；D未业务修改或切换HOME。

**实际默认路由官方metadata检查通过**：`2026-10-01T03:36:26.927Z`，同现装0.159、formal03 project cwd、默认HOME及原model/tier，`codex debug models` 2.774s/exit0、10 models、stderr空；目标gpt-6.1-sol公开metadata为 `tool_mode=code_mode_only`、`supports_search_tool=true`、`service_tiers=[priority/Fast]`、default reasoning low。调用前只归档非秘密cache时间/版本：03:36:04.115406300Z/0.158/无目标；之后官方cache为03:36:29.678634100Z/0.159/目标存在。因此本次成功获取原模型metadata，当前priority确被advertised，case03旧omit不能当远端不支持priority；先前03:04 cache观测仍保留且不是历史原请求快照。限30s及输出大小，在内存接收官方catalog后仅选择公共目标字段落盘，新私有 sibling `morph-agent-protocols-1001-state/metadata-diagnostic-2026-10-01T03-36-26-923Z/{cache-before,default}.json`，无凭据/header/全catalog归档。官方正常auth/cache行为已授权；没有人工auth/config/provider/model/HOME改写、科学turn或新UUID。

默认已成功，按授权不额外proxy对照，也不另发自制GET。官方进程级 `features.respect_system_proxy=true` 仍只是失败时获准对照候选，[FeatureSpec:1314–1324](https://github.com/openai/codex/blob/687a119f0fcaace47e1f1abcc77cec6c813fd6da/codex-rs/features/src/lib.rs#L1314-L1324) 属UnderDevelopment、默认false，system_proxy_fallback默认true；未设flag或改全局代理，不能声称它修复旧timeout。支持的最小建议是保持原模型/tier、direct11/required/per11/defaultprompt/read-only/never/host禁止及exactwarning规则，由root另派产品/验收使用当前有效官方metadata；无需换model、删除tier或豁免fallback通知。已交root `msg_a9c58e43b03c` / I `msg_0b6fb1c63506`，请root转未来P。证据仅当前metadata可达，底层历史timeout仍UNKNOWN，不代签模型工具选择/原三角色科研checker；NIST/更多Agent/EvoMap仍后置。

## Case04 Claude 正式 OAuth 与 ORCA 账户复用

基线 `b581825`；仅认证接口诊断/Handoff，A installed c25/coreCBC、I case01–04原件只读。case04 `replication-native/native.jsonl:1–3`：UUID `40438687-3d24-437d-893a-c5c3a51ed848`，init为Claude2.1.238/claude-sonnet-4-6/dontAsk/MCPconnected/恰11tools/apiKeySource none，随后authentication_failed、Not logged in，result虽然subtype success但is_error=true。4.053978s/exit1/0工具，正式outcome failed、remote_effect unknown、tokens/cost null；raw synthetic usage0不回写成可信零费用。作者唯一科学实验 `03748c9c347b4b2394f50bd5f31864f0` passed、known/destroyed与源Gene quarantine分别保留；I证据 `a3dcc85`、原完整checker exit1缺inheritance-observation，不重跑、不改窗口。

**当前无可复用的已选Claude OAuth**：公开 `orca account list` Claude accounts=[]、activeId=null、host未选；与Codex managed选择无关，不能做Claude身份比较或凭空指定selected home。当前CLAUDE_CONFIG_DIR/HOME absent、USERPROFILE=C:/Users/DW，formal默认为 `C:/Users/DW/.claude`，目录存在、`.credentials.json`不存在（只查存在性）。仅安全字段检查user settings.json的env两gateway键存在；shell同两键存在，ANTHROPIC_API_KEY/CLAUDE_CODE_OAUTH_TOKEN不存在。未输出email/org/provider身份、token/key或whole config/auth/env；这些当前观测不补造04历史环境快照。

| 同shim/cwd、15s有界官方auth status | 实际结果（安全原件在新private sibling） |
|---|---|
| probe-equivalent：child过滤ORCA_*且pop ANTHROPIC_AUTH_TOKEN/ANTHROPIC_BASE_URL，仅auth status --json | 2026-10-01T03:47:34.724Z，1189ms/exit0，loggedIn=true、authMethod=oauth_token；apiKeySource字段缺失、stderr空。 |
| formal-effective：相同child，再加root --setting-sources user --settings {disableAllHooks:true,env:{ANTHROPIC_AUTH_TOKEN:"",ANTHROPIC_BASE_URL:""}}，auth status --json | 03:47:35.914Z，557ms/exit1，loggedIn=false、authMethod=none；apiKeySource字段缺失、stderr空。 |

实测普通true→正式false、完整JSON/明确exit0/1证明root flags实际生效并执行auth子命令，非仅接受argv或误入TUI。真实installed `orchestration/native_agents/registry.py:90–112` 的probe只用child_environment+auth_args；产品 `morph_research/auth.py:16–30`只pop两shell键，`permissions.py:48–58`正式额外清空settings.env两键。因此user settings可把gateway重新引入普通probe；**loggedIn=true/oauth_token不等于正式subscription OAuth就绪**。正式配置已排掉gateway却无登录，这是准确外部登录阻塞，P修复预检不能创造凭据。

固定上游ORCA `85f8d6b` / MIT： [runtime-paths.ts:13–32](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/main/claude-accounts/runtime-paths.ts#L13-L32) 用CLAUDE_CONFIG_DIR或home/.claude，并给envPatch；[runtime-auth-preparation.ts:16–36,67–86](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/main/claude-accounts/runtime-auth/runtime-auth-preparation.ts#L16-L36) WSL managed注入选中目录，host使用runtime paths并按选中状态stripAuthEnv/provenance；[environment.ts:3–41,61–69](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/main/claude-accounts/environment.ts#L3-L41) 清理auth env并apply patch。host已有选择时会materialize，不等于Codex每账户HOME路线：[runtime-auth-sync.ts:259–282](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/main/claude-accounts/runtime-auth/runtime-auth-sync.ts#L259-L282)。[service.ts:18–24,59–60](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/main/claude-accounts/runtime-auth-service.ts#L18-L24) prepareForClaudeLaunch会sync；路径读取可复用getRuntimeConfigDir/preparation，诊断不调用同步/材料化/复制secret。当前空账户的provenance是system，不声明已接入不存在的managed Claude。

官方Claude [settings](https://code.claude.com/docs/en/settings) / [CLI](https://code.claude.com/docs/en/cli-reference) 说明user来源与session --settings覆盖；[authentication](https://code.claude.com/docs/en/authentication) 说明Windows默认credential路径和CLAUDE_CONFIG_DIR选择。滚动文档不是2.1.238全功能证明：如auth status configDirectory字段要求>=2.1.268，本版不能依赖。已装实际shim是 `C:/Users/DW/AppData/Roaming/npm/node_modules/@anthropic-ai/claude-code/bin/claude.exe`，package2.1.238许可证 `SEE LICENSE IN README.md`，不是ORCA MIT源码；仅只读使用，未复制bundle。binary SHA256 `223bc058b5aef48138876e28de5d00387e4fd7362a18e733143bf00819c01aab`：内嵌官方函数Bk（byte300440059）将AUTH_TOKEN/OAUTH_TOKEN/helper/profile等与存储claude.ai分开；authStatus _ZA（输出byte324844268）将generic token来源统称oauth_token，claude.ai也可来自Console `/login managed key`。status注册byte324948435、setting-sources注册byte323720335；编译单行源码以byte定位，不能伪造上游行号或当server验证。

给P最小正式接入：复用原ProbeResult/REGISTRY/command/child_environment，保留普通probe原证据；另从正式plan抽取auth相关argv+同cwd/env/home跑官方status，不带print/resume/model/MCP。版本必须匹配，要求loggedIn严格true、apiProvider firstParty、authMethod claude.ai且排除Consolemanagedkey/APIkey/helper；apiKeySource缺失保持null+field_present=false，不造none。oauth_token/第三方/陌生来源不冒认subscription；成功字段的官方分支已证明，但本机实际成功OAuth **未发生**，status也只是凭据存在性，不代签remote模型/科研。fixture应覆盖普通true/formalfalse、Consolekey/thirdparty/unknown/缺字段、timeout/无效JSON、版本漂移、拒绝发生于native/MCP/sandbox-key读取前，并核查parent环境恢复；无需I脚本补home/env或改core。

用户人工登录的已确认官方入口是同shim、同child排除两gateway键、同formal settings，`auth login --claudeai`；随后同配置 `auth status --json`。`--console`为API计费，不选；准确无secret PowerShell子进程命令已交root `msg_4fa48999b5b9` / P `msg_397d917865a8`，本D仅运行login --help，**login未执行**。当前无selected目录，未运行CLAUDE_CONFIG_DIR对照；以后有合法既存选中Claude目录也需P正式供给、root新验收，不能偷塞I环境或重试04。诊断安全输出仅 `morph-agent-protocols-1001-state/claude-auth-diagnostic-2026-10-01T03-47-34-719Z/{probe,formal,provenance}.json`，没有科学turn/新UUID/模型API/沙箱或全局修改。

## 固定来源索引

以下均为 `85f8d6b5f507df795cd3cef1cdea08124cf801ee`，表内引用的行号以官方LF文件为准。

| 键 | 源码位置 |
|---|---|
| C / L | [src/shared/tui-agent-config.ts](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/shared/tui-agent-config.ts) / [tui-agent-launch-command.ts](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/shared/tui-agent-launch-command.ts)；43族union另见 tui-agent.ts:3–46 |
| R | [src/shared/agent-session-resume.ts](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/shared/agent-session-resume.ts) |
| P | [src/shared/tui-agent-permissions.ts](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/shared/tui-agent-permissions.ts) |
| E / K | [src/shared/agent-hook-listener/provider-dispatch.ts](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/shared/agent-hook-listener/provider-dispatch.ts) / [src/main/agent-hooks/managed-agent-hook-registry.ts](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/main/agent-hooks/managed-agent-hook-registry.ts) |
| N | [src/shared/native-chat-agent-support.ts](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/shared/native-chat-agent-support.ts) |
| A / B / O | [commit-message-agent-specs-primary.ts](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/shared/commit-message-agent-specs-primary.ts) / [secondary.ts](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/shared/commit-message-agent-specs-secondary.ts) / [commit-message-agent-spec.ts](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/shared/commit-message-agent-spec.ts)；这是13族文本preset，不是科研tool loop |
| H / HB / HQ | [agent-headless-command.ts:17–32](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/shared/agent-headless-command.ts#L17-L32) / [codebuddy-headless-command.ts](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/shared/codebuddy-headless-command.ts) / [qoder-headless-command.ts](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/shared/qoder-headless-command.ts) |
| HA / HP / HZ / DH | [ante-headless-command.ts](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/shared/ante-headless-command.ts) / [prime-agent-headless-command.ts](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/shared/prime-agent-headless-command.ts) / [zcode-headless-command.ts](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/shared/zcode-headless-command.ts) / [dsh-launch-command.ts](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/shared/dsh-launch-command.ts) |
| U / V / F | [src/main/usage/usage-provider-contract.ts:4–16](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/main/usage/usage-provider-contract.ts#L4-L16) / [src/main/ipc/usage-provider-handlers.ts:66–70](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/main/ipc/usage-provider-handlers.ts#L66-L70) / [src/shared/commit-message-agent-output.ts](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/shared/commit-message-agent-output.ts) |
| SC / SD | [Claude query/stdin/options:115–142](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/main/claude/claude-stream-json-connection.ts#L115-L142) / [Codex app-server:34–69](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/main/codex/codex-app-server-connection.ts#L34-L69) / [Codex turn interrupt:9–40](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/main/codex/codex-structured-turn-cancellation.ts#L9-L40) |

验证、提交与剩余限制见 [D轨报告](../tracks/agent-protocols-1001.md)。本矩阵是来源盘点，不是接口运行证明。
