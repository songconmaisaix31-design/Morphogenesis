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
