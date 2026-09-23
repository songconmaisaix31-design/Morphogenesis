# 封板夜 E：Evolver 前置与 Hub 适配

## 当前结论（2026-09-23）

前置二现已 **PASSED**：固定身份 authenticated hello、一次 heartbeat、完整官方 Proxy/MCP 进程均有真实证据。Hub 适配本地验证通过；三次经 Proxy 发布收到 HTTP 400，之后一次获批官方直连收到 **quarantine / newcomer_candidate**、三资产 ID 和 bundle ID。认证详情仍是 candidate，validation=noop、not credible、not callable，仅返回摘要；随后一次指定同一 Gene 的正常 FETCH 返回 **confirm_required，预览 3.36 credits、余额 0、零结果**，未确认付费。没有完整真实 FETCH 或 REPORT，G3/G4 **BLOCKED / NOT_RUN**。完整旧 SDK/Proxy schema 与当前 wire 的差异和直连范围单列，不能称 Proxy 发布或远端行为验证通过。下列章节保留历史；最新真实回执及限制见文末。

### 18:30 首次 bootstrap 历史记录

| 事实 | 证据 |
| --- | --- |
| 基线 | `codex/morphogenesis-mainline` / `2b58b5923286af8e11e556a1579e239bceee539b`；开工 `git diff` 为空 |
| 本机 | Node 24.16.0、Git 2.47；开工无 Evolver CLI、19820 listener、真实用户 `.evolver/settings.json` |
| 单次 bootstrap | 2026-09-23T10:30:49.970Z–10:30:52.458Z（北京时间 18:30:49–18:30:52） |
| Hub 回执 | `message_id=msg_1790159452373_c5ed9018`；服务端时间 `2026-09-23T10:30:52.373Z` |
| 拒绝原因 | `status=rejected`，`hello_blocked: bulk-fetch antibody active`，`captcha_required=true`，`retry_after_ms=3600000` |
| 节点 / Proxy | 无已确认 node ID / secret；没有启动 listener；计划 URL `http://127.0.0.1:19820`，不能称可用 |
| 产物 | `.runtime/freeze-evolver/bootstrap-hello.json`、`preflight-result.json`、`preflight-started.json`；均为本地忽略产物 |

未自动重试、未换身份、未请求付费操作。CAPTCHA/账户限制需要账户操作者处理；等待时间届满不构成重试授权，也不证明阻塞解除。

请求元数据限制：官方 v1 `LifecycleManager.hello()` 内部生成 `node_` 加 12 位 hex，payload 仅 `capabilities`；本次未附 `model`，拒绝后未持久化请求节点 ID，也未取得请求侧 message ID，不能补造。主控较早发出的“预生成固定 ID 并携带真实 model”消息因旧 FIFO 批次尚未 ack，在请求后才被读取；这一执行缺口违反本轮前置要求，已明确上报。上表 message ID 仅为 Hub **响应** ID。任何后续尝试必须先解决固定身份与请求追踪，不能复跑会新生成身份的 bootstrap；每次网络写边界前须消费并 ack 全部协调消息。

只读恢复核查：`state/bootstrap/state.json` 仅有 `_schema_version: 1`；`state/node_id` 及两份安装根的 `.evomap_node_id` 均不存在。`state/device_id` 存在，但设备指纹不等于节点身份，未公开其值。

## 官方版本、来源与隔离

阅读 [Evolver 官方仓库](https://github.com/EvoMap/evolver)、[官方索引](https://evomap.ai/llms.txt)、[配置说明](https://evomap.ai/docs/en/35-evolver-configuration.md) 及已安装 [Evolver 技能](C:/Users/DW/.codex/plugins/cache/evomap/evolver/0.2.0/skills/evolver/SKILL.md)。通过官方 npm registry 安装固定版本，`--ignore-scripts --no-audit --no-fund --save-exact`，安装与 npm cache 均在 `.runtime/freeze-evolver/`；没有全局安装或修改用户配置。

| 包 | 用途与来源 |
| --- | --- |
| `@evomap/evolver@2.0.38` | 本轮主版本，来自 `https://registry.npmjs.org/@evomap/evolver/-/evolver-2.0.38.tgz`；release provenance 为 `EvoMap/evolver` / `v2-beta` / `v2.0.38`；npm README 声明 GPL-3.0，根 package.json 没有 license 字段，未自行补写 |
| `@evomap/evolver@1.94.0` | 仅作官方无身份 bootstrap；独立 `v1/` 安装；package.json 声明 GPL-3.0-or-later；来源 `https://registry.npmjs.org/@evomap/evolver/-/evolver-1.94.0.tgz` |

保留 registry 完整性与来源回执 `npm-source.json`、`npm-v1-source.json` 以及两份局部 package-lock.json。没有把上游实现复制进项目业务代码。

版本取舍原因：v2 Proxy CLI 的 `connectHubRuntime()` 明确要求既有 node secret，不能直接完成空身份 bootstrap；v1 完整 `EvoMapProxy.start()` 无条件启动 heartbeat/sync，心跳还可能触发升级。主控经 `orca orchestration ask` 明确允许薄组合：只调官方 v1 `LifecycleManager.hello()` 一次，成功取得 secret 后才给同一固定身份调用 v2 `ProxyDaemon` 的 authenticated hello 与一次 heartbeat；不装配 selfUpdate、不调用周期 tick、不改上游源码。实际只执行到第一次 hello 的明确拒绝。

官方隔离变量为 `EVOLVER_HOME`、`EVOMAP_HOME`、`EVOMAP_DIR`、`EVOLVER_SETTINGS_DIR`、`EVOLVER_PROXY_SETTINGS_FILE`、`EVOLVER_PROXY_STORE`，状态根均定向到项目 `.runtime/freeze-evolver/state/`，另设置 GEP、memory、trace 目录。`EVOMAP_PROXY=1`；关闭 worker、ATP autobuy、validator、自动发布/升级与 MCP 自动启动；不运行 CLI evolve、`--loop` 或 hooks setup。真实用户 settings 在拒绝后仍不存在。后续尚未执行的 v2 步骤不能计为隔离运行验证通过。

## 已核实的 Proxy 协议差异

v2.0.38 安装源码 `evolver-proxy/dist/daemon/proxyDaemon.js` 是本轮适配事实源：

- 发布：`POST /asset/submit?mode=sync`，完整 `assets` bundle，Proxy 构建远端信封。待处理/排队回执不是成功；`compose_recipe=false` 防止附带 recipe 发布。
- 定向获取：`POST /asset/fetch`，`asset_ids`；先读本地 store，缺失才走远端。成功返回资产或 SDK hash 通过不证明一次真实 Hub fetch。
- 使用效果：`POST /asset/reuse-result`，`asset_id`、`outcome`、可选 `task_id` / `trace_id` / `reason`；`recorded=false` 不能算 REPORT 成功。它与 v1 的 `/asset/report-reuse` 及 Hub `/a2a/report` 语义不同，不猜路由替换。
- Proxy 内部存在持久待发送/恢复机制；项目侧一次 POST 不自动等于上游只发送一次。未核实代理无重放与来源证据前，不能宣称 live 写入和定向回收通过。

用户 `.evolver/settings.json` 和现有共享契约、`HubConfig.local_only`、锁文件、API sandbox、T4 均未改。第四轮证据仅只读参考，未将旧任务或缓存结果计入本轮 Hub 验收。

## 验证与剩余操作

- `node .runtime/freeze-evolver/node_modules/@evomap/evolver/bin/evolver.js --version` → `2.0.38`。
- 同安装 `evolver-proxy.js --help` → exit 0，官方项目状态路径选项可枚举；不等于 Proxy 网络可用。
- `node .runtime/freeze-evolver/preflight.mjs` → exit 1，Hub 明确拒绝，保留原回执，无重试。
- 已有 `.venv` 可导入 Python 3.12.13 / httpx 0.28.1 / Pydantic 2.13.5；依赖由 T 轨提供。

完整工具进程、项目适配测试、真实资产构建与 PUBLISH→指定 ID 的远端 FETCH→真实使用 REPORT 尚未完成。解除远端账户限制后仍需主控明确安排下一次有界请求；本报告不构成自动重跑入口。

## 18:52 恢复：离线前置修正与官方 adapter 拒绝误判

本次恢复遵守 PLAN 18:52 覆盖指令及主控消息 `msg_34a2f1a5921e`、`msg_6705e8ffd0f1`：只新增项目内离线脚本及本报告，不改 `hub_client`、官方安装包、原 `preflight.mjs` 或其 guard。没有新增真实 hello、heartbeat、publish、fetch、report，也没有生成或轮换真实身份。续接基线为 `3786659dfde536a3b37b571ff0b198821f07aa24`，期间主控治理提交推进到 `824cf66`；本报告的结果只覆盖离线检查。

官方 [hello 协议参考](https://evomap.ai/a2a/skill?topic=hello) 的主控只读缓存 `.runtime/hub-discovery/hello-reference.md` 明确说明：HTTP 200 同时承载 `payload.status=acknowledged` 与 `rejected`，客户端必须先判 payload 状态。[官方接入说明](https://evomap.ai/skill.md) 的缓存也明确 hello payload 的 `model`、`name`、`env_fingerprint` 字段。原拒绝的最早时间为 **2026-09-23 19:30:52.373 CST**，只是服务端重试下界；届时仍不能自动重发，也不证明 CAPTCHA 已解除。

### 官方 v2.0.38 的实际离线复现

在 **2026-09-23T10:54:44.470Z（18:54:44.470 CST）**，直接实例化原安装 `@evomap/evolver-adapter-public@2.0.38` 的 `PublicHubCapability`，注入内存 `fetchFn` 和明确标为 fixture 的 sender/model/fingerprint，调用一次 `hello({evolverVersion:'2.0.38', preserveCredentials:true})`。注入回执采用官方拒绝形状：HTTP 200、`status=rejected`、`captcha_required=true`、`retry_after_ms=3600000`。

- 原 adapter **返回 `ok=true`、本地 sender ID 和 `retryAfterMs=3600000`**。`hubCapability.js:181–199` 的身份回退及 `payload.ok !== false && Boolean(nodeId)` 没有拦截这类普通拒绝；专门的 secret-divergence 分支不能覆盖 CAPTCHA 拒绝。
- 原请求 payload **没有顶层 `model` 或 `name`**；`agent_name` 固定为包名，`env_fingerprint.model` 存在。不能据此声称本轮 hello 元数据要求已经满足。
- 这是 `provenance=mock` 的上游行为复现，不是另一条 Hub 拒绝回执，也不是修改官方包后的结果。官方源码保持原样。

证据：`.runtime/freeze-evolver/recovery-evidence/offline-RVhogL/official-adapter-reproduction.json`。

### 独立恢复脚本与验证

新增 `.runtime/freeze-evolver/recovery-hello.mjs` 与 `recovery-offline.test.mjs`。恢复 helper 复用原官方 `gepEnvelope` / `HubFetch`，不复用 v1 lifecycle；没有默认网络 transport 或真实网络 CLI 入口，目标固定为 `https://offline.invalid`，必须注入 transport。已有 node ID、model、name、fingerprint 均必填；没有真实模型依据时不会用 `unknown` 补足。测试所用 `node_offline_fixture_only` / `offline-model-fixture` 全部显式标记为 mock，不能用于恢复真实身份或登记 live 验收。

发送前以 `wx` 独占创建并 fsync `request.json`，保存官方生成的 request ID、请求时间、记录时间、明确输入的 model/name/fingerprint 以及 `unknown_before_send` 状态；文件已存在即拒绝再次调用。回执另存 `result.json`，只有有效 GEP hello 信封、`acknowledged` 与相同 `your_node_id` 同时成立才记本地成功。拒绝、缺失状态、不同身份、网络断连、HTTP 错误、重定向、非 JSON 均保留失败或 unknown，不重试。没有读取或持久化真实凭据，日志只输出白名单元数据，不复制异常文本、Authorization、node secret 或 claim 链接；原 bootstrap guard 的 bytes 和 mtime 均保持不变。

验证命令（项目根，2026-09-23 18:54:44 CST）：

```powershell
node --test .runtime/freeze-evolver/recovery-offline.test.mjs
```

结果：**6 passed / 0 failed / 816.3637 ms**，涵盖官方误判复现、请求元数据先落盘、HTTP 200 拒绝、7 类异常/不完整回执、显式确认同身份、必填输入缺失、秘密不落日志及原 guard 不变。断连、402、500、重定向、非 JSON、空 payload、不同身份的每个案例都只有一次注入 transport 调用，再用相同目录调用均在发送前失败。测试汇总结束于 **2026-09-23T10:54:44.521Z**，证据根 `.runtime/freeze-evolver/recovery-evidence/offline-RVhogL/`；全部脚本及运行证据被现有 `.gitignore` 忽略，不随文档提交。

拒绝测试的本地 request ID 为 `msg_1790160884472_ba466536`，请求时间 `2026-09-23T10:54:44.472Z`；注入回执 ID 为 `msg_offline_fixture_receipt`。二者仅用于离线字段关联验证，不是新增真实 Hub 请求或回执 ID。

只读存在检查：真实用户 `C:/Users/DW/.evomap/node_id`、`node_secret`、`.evolver/settings.json` 以及项目 `state/node_id`、`state/node_secret` 均不存在；仅调用 `Test-Path`，没有打开凭据值、扫描历史/日志/浏览器存储或修改 home/权限。没有新节点 ID 可报告，Proxy 19820 未启动，状态目录仍为本项目 `.runtime/freeze-evolver/state/`。

本次仅完成离线恢复准备及上游缺陷定位。完整前置二、真实工具进程、G3/G4 的 PUBLISH→远端同 ID FETCH→实际使用 REPORT 仍 **BLOCKED / NOT_RUN**；下一步需要账户操作者按官方流程处理现有账户/节点，并由主控明确放行具体一次网络动作。恢复真实 transport、凭据使用与完整 Proxy 行为仍须在该授权下验证，本离线脚本不构成这些动作的自动授权。

## 19:04 凭据续接：固定身份的一次 authenticated 前置

续接基线为主线 `8d0893f957acd0ba463ecc9ec2a8dbac20ad4512`。主控已根据用户授权将固定节点 `node_e2ad48c0d0d63625` 的新凭据存入项目私有文件；E 仅接收路径 `.runtime/freeze-evolver/private/node_secret`，不扫描历史或其它账户状态。此节取代上节的“尚待凭据授权”，不撤销此前失败记录。最早允许真实请求时间为 **2026-09-23T11:30:52.373Z / 19:30:52.373 CST**，仅一次 authenticated hello，确认同身份后才一次 heartbeat。

项目忽略目录新增 `authenticated-preflight.mjs` 与 `authenticated-preflight.test.mjs`，复用官方 2.0.38 `PublicHubCapability` / `HubFetch`、`ProxyDaemon`、`publishProxySettings` 及 `captureEnvFingerprint`，未改官方包。显式 transport 适配补齐 `model=gpt-6-astra`、`name=Codex Agent`、`rotate_secret=false`，保留官方真实主机摘要/平台/Node/架构指纹；后续历史资产的生成模型仍须按第四轮真实请求 `evomap-gpt-5.6-luna` 与返回模型分别记载。

只有 hello / heartbeat 两个出站路由被允许，写前以 `wx` + `fsync` 保存请求元数据，固定真实证据目录存在即禁止重跑。HTTP 200 必须继续检查 acknowledged、同一节点及完整 hello 信封；拒绝、未知结果或意外凭据变化立即停止。Authorization 只在内存和请求头，heartbeat 不把 secret 放入 REST body。回执仅保存明确字段、白名单诊断与请求/响应 ID；没有伪造 heartbeat 协议中不存在的 message ID。没有自动重认证、secret 轮换、领任务、质押、付费、发布、升级、同步、网络 tick 或重试。`EVOLVE_RECALL_VERIFY=0` 关闭官方 `start()` 装配的后台回收验证。

settings、mailbox、资产和事件路径均由官方环境变量定向本项目目录；没有 repurpose HOME/CODEX_HOME。旧插件 0.2.0 的 MCP 脚本硬编码用户 settings，不用于本次隔离运行；固定 npm 2.0.38 的 `evolver-mcp` 支持 `EVOLVER_PROXY_SETTINGS_FILE`，完整子进程完成 initialize → tools/list → `evolver_proxy_status` → EOF 退出。实测 23 个工具，握手 serverInfo 自报版本 `0.0.0`，安装包版本为 `2.0.38`，二者分列。启动失败、请求与 EOF 退出均有 deadline，超时只结束本次 spawn 的子进程。

离线验证命令：

```powershell
node --test .runtime/freeze-evolver/authenticated-preflight.test.mjs
```

- Worker：**8 passed / 0 failed / 8956.7705 ms**，证据 `recovery-evidence/authenticated-offline-uIp41Y/`。
- 主控独立复验：**8 passed / 0 failed / 9072.4801 ms**，证据 `recovery-evidence/authenticated-offline-BLHwNr/`，由协调消息 `msg_8f94eb1f6cb1` 回传。
- 覆盖完整 Proxy start/stop 与 MCP 子进程、5500 ms 后台观察窗口仅 hello/heartbeat 两次注入出站、HTTP 200 rejected 不写 settings/不发 heartbeat、断连/401/402/500/重定向/非 JSON/错误身份/意外 secret 变化只发送一次、重开相同目录不重发、heartbeat 失败不再 hello、MCP 启动错误和 EOF 卡住有界退出、秘密脱敏、原 guard 与真实用户 settings 不变。全部为 **mock 网络回执 + 真实本机组件进程**，不计真实 Hub 通过。
- 可选 Node `--permission` 实验为 **4 passed / 4 failed**，原错误 `ERR_ACCESS_DENIED: fsync API is disabled when Permission Model is enabled.`，影响官方资产锁与写前证据 fsync；证据 `authenticated-offline-WYa7Jk/` 保留。未使用该可选模式运行真实前置，未修改 OS 或用户权限，不声称 OS 沙箱隔离通过。

真实执行命令为 `node .runtime/freeze-evolver/authenticated-preflight.mjs --live`；执行前必须消费并 ACK 协调 FIFO。真实证据固定目录 `recovery-evidence/authenticated-20260923-01/`，Proxy 目标 `http://127.0.0.1:19820`，状态/settings 也在该目录；成功后 IPC 可保持，但仍无周期网络行为。此节准备完成时尚未发送真实请求，G3/G4 仍未开工。

## 19:31 真实前置通过

`node .runtime/freeze-evolver/authenticated-preflight.mjs --live` exit 0；完成时间 **2026-09-23T11:31:14.845Z**。固定节点 `node_e2ad48c0d0d63625`，model `gpt-6-astra`，没有生成或轮换身份。主控消息 `msg_f0e11afa14a5` 确认前置一、二均通过并恢复 E 领域工作。

| 动作 | UTC 时间 | 请求 / 回执 |
| --- | --- | --- |
| authenticated hello | 请求 `11:31:11.257Z`，Hub 响应 `11:31:13.002Z` | 请求 `msg_1790163071257_4eff132f`；响应 `msg_1790163073002_6cad4984`；HTTP request ID `1cbd6886-e510-4ada-a356-877ec0b2e183`；acknowledged、同节点、余额 0 |
| heartbeat | `11:31:13.234Z`–`11:31:13.616Z` | HTTP request ID `253de986-5a0a-4209-a3bc-b018ea6a4b8b`；status ok；协议没有 message ID，保留 null |
| Proxy / MCP | 同次进程 | Proxy `http://127.0.0.1:19820`、PID 47272；running/auth ok，MCP 23 个工具且正常 EOF 退出 |

证据根 `.runtime/freeze-evolver/recovery-evidence/authenticated-20260923-01/`，其中 `summary.json`、各请求/回执、`settings.json`、状态与邮箱均在项目内。stdin EOF 后已正常 `proxy.stop()` 并 exit 0，不能据此称 19820 持续在线。真实用户 home settings 仍未创建；私有 node secret 只读入进程内存/Authorization header，未写日志或提交。

## 领域实现与真实资产来源

- `HubConfig.local_only` 原样保留；配置及结果增加自有 `source=local_stub|evolver_proxy`，共享 Acceptance/Provenance 仍是原 `live/replay/mock`。默认 local_stub/mock，真实 Proxy 显式配置 live，IPC token 与远端 node secret 分开。
- 官方 IPC 路由分别为 `/proxy/status`、`/asset/submit?mode=sync`、`/asset/fetch`、`/asset/reuse-result`。发布 `compose_recipe=false`；发布/报告先落 unknown，再单发，未知结果不重试。REPORT 必须关联同 client 获取的资产、实际 `UseRecord` 与同 attempt 的独立成功 TaskResult；只有 recorded=true 与非空回执 id 才能确认。
- FETCH 的普通接口结果始终不单凭缓存命中提升 interface_live；实际 runner 使用新空 store 并审计远端 `/a2a/fetch` 恰好一次及指定 ID。官方内部持久队列不 tick；transport 对每阶段只放行一次，禁止重认证、额外 hello/heartbeat、自动 recipe、后台任务及循环。
- [官方 KG 文档](https://evomap.ai/wiki/20-knowledge-graph) 允许单次 `payload.kg_enrich=false`。原 2.0.38 publish adapter 仅转发 assets，故在公开 transport 注入点补入该字段并审计实际出站 JSON；不改官方源码或账户开关。
- 全部资产 hash 与 schema 校验委托项目 `NodeAssetBridge` / 锁定 `@evomap/gep-sdk@1.14.0`，没有 Python/hash fallback。使用第四轮真实 Gene、TaskResult 与请求/响应，补 official EvolutionEvent 作为已观察修复的序列化记录；不是另一次 Evolver 进化执行。

来源只读根为 `C:/Users/DW/AppData/Local/Temp/morph-live4-98b36399c0324192b5af81f8077bc11d/morph-rehearsal-86e5351d49fe49a1b60ba0a4bb4c4e4e/repair`，来源 SHA `7c0bb6a2f7b39a7eb524c0c71bc31c7a110f883c`。真实请求模型 **evomap-gpt-5.6-luna**，返回模型 **gpt-5.6-luna**，返回 ID **chatcmpl-EQpuANHdosqb3LPB9d5BwQR7htK71**；历史 tokens 887、cost null。原始输入 sample 与项目坏样本、proposal 与实际修复文件均逐字核对；实际 blast_radius 为 **1 文件 / 17 行（11 added + 6 removed）**，独立 Python 验收 3/3。

公开资产保留真实请求/返回模型，去掉本地 artifact_uri、reviewer 路径及私人内容。官方 sanitizer 会把高熵 gateway response ID 脱敏并重算 ID，因此该返回 ID 保留在本地 lineage，不进入公开 payload；初始离线阻塞是此 ID 变动，不是绑定校验失败。官方参考示例的顶层 model_name 被锁定 SDK 的 additionalProperties=false 拒绝，故使用正式允许的 Capsule env_fingerprint/content 和 Event meta 字段，不改锁文件或共享 bridge。

## 两次真实发布的明确拒绝

| 次数 / 证据目录 | UTC 请求–完成 | 请求与结果 |
| --- | --- | --- |
| `asset-cycle-live-20260923-01` | `11:50:35.072Z`–`11:50:38.314Z` | `msg_idem_4f6c68d8bd882450819e8ecfa014e81eab34cac2`；HTTP request `fda29001-ead0-4b4f-accb-6a7ef9874a63`；HTTP 400：Gene.summary 必填 |
| `asset-cycle-live-20260923-02` | `11:54:39.224Z`–`11:54:44.616Z` | `msg_idem_0185f2f3bc6693caac04880f6ae03d350c81f9b9`；HTTP request `dc4776b5-27fe-4dc6-a5ad-eb63b1b1d1b4`；HTTP 400：validation 命令须以 node/npm/npx 开头 |

两次均为 publish=1/fetch=0/report=0、kg_enrich=false；Proxy 转换为 422 明确拒绝，未重发原候选。完整脱敏请求、响应、IPC 结果与单发计数保留上述目录；不是未知结果，也不是已发布/待推广。第二次由主控 `msg_97a373f9e88e` 明确允许修正候选；后续第三次须按结构验证方案核实后执行，不能把前两次 HTTP 400 隐去。

补充官方[发布协议](https://evomap.ai/a2a/skill?topic=publish) 缓存于 `official-publish-reference.md`。SDK 虽允许 Gene.summary 缺省，远端必填，现已补入。历史 Gene.verification 是描述性观察，不能直接当执行命令；SDK validation 又要求 minItems=1，不能通过空数组绕过。领域输入增加明确 `GenePolicy.validation_commands`，Proxy 分支拒绝缺失/描述文字/Python 直接命令。

## 第三候选的真实结构检查与验收边界

主控通过 `orca orchestration ask` 明确允许新增 Node 结构验证：只读真实 `sample.py`，不 spawn Python、不执行外壳、不修改 sandbox。`candidate-v5/structural-verification.json` 记录四条实际命令对坏样本 **0/4**、历史修复 **4/4**；分别断言上下界分支、均值分母与保序去重实现。这些是 E 本轮编写的**结构检查**，不是历史模型生成，也不代替 Python 独立**行为验收**。公开 Capsule 分开记录两类事实；不声称新增模型调用。

若真实 FETCH 成功，runner 只从取回 Gene.strategy 提取代码写入新的坏样本工作区，先独立 Python 验证 0/3，再应用获取内容、记录 UseRecord、独立验证 3/3，最后才 REPORT。同一回传 ID、run/attempt、使用时间均绑定；不拿历史成功冒充本轮使用效果。离线成功仅为 mock transport + 真实本地新样本执行，不能计为 G3/G4。

本轮工具准备/请求脚本及证据均位于 `.runtime/freeze-evolver/`，被现有规则忽略；不提交凭据、官方安装包或运行产物。当前领域文件、测试及本报告是仅有拟提交路径，治理/G0 由主控维护。

第三候选三个 SDK ID：

- Gene `sha256:70484f3f6549bb5bfad413a3ebad74d388240cfe786b295330ba15d4052b2ddf`。
- Capsule `sha256:4b14b6895640da3e7dadfea8bb27e1b1a54d5bd2645e2a445739bbd4484835db`。
- EvolutionEvent `sha256:24fb8591b3bc3cd2301650554d11fa0fe608720fa0990eb3ce5a26aa18c6d003`。

### 20:16 本机发送前资源失败

`.runtime/freeze-evolver/asset-cycle-live-20260923-03/proxy-summary.json` 于 **2026-09-23T12:16:07.359Z** 结束，counts **0/0/0**，receipts 空；没有 request 文件、publication 或 IPC submit。Python 在导入原 `metabolism.models.UseRecord` 所触发的 sklearn/scipy 包链时发生 `MemoryError`。这是发送前本机失败，不是第三次 Hub 回执；主控独立确认并要求等待资源恢复。未改共享导入、锁依赖、全局配置或结束他人进程；保留旧目录，资源恢复与导入检查通过后才允许使用新目录执行尚未发生的第三次远端请求。

### 本轨验证结果

```powershell
.venv/Scripts/python.exe -B -m pytest -q tests/t1/hub --basetemp .runtime/freeze-evolver/pytest-hub-05
.venv/Scripts/python.exe -B -m mypy --strict hub_client
git diff --check -- hub_client tests/t1/hub docs/tracks/freeze-evolution.md
```

结果：**65 passed / 58.96s**；mypy **4 files passed**；diff check exit 0。包含原 local stub 测试、Proxy 路由/身份/凭据分离、官方三资产 hash/关联、远端 summary、显式 Node 验证输入、单发写入、未知与排队回执不提升、FETCH 缓存边界、实际 UseRecord 绑定、recorded=true 缺失/空 id 拒绝。相对基线 `2b58b59` 使用 AST 提取函数源码逐字比较，`HubConfig.local_only` **verbatim PASS**。

`node .runtime/freeze-evolver/asset-cycle-proxy.mjs --offline` 最终候选通过，证据 `recovery-evidence/cycle-offline-accepted-ajdYyF/`，publish/fetch/report **1/1/1**，本地新任务 0/3→3/3。`--offline disconnect` 预期 exit 1，证据 `cycle-offline-disconnect-Kaos3k/`，**1/0/0**；`--offline empty-report` 预期 exit 1，证据 `cycle-offline-empty-report-Q3Ocqv/`，**1/1/1**、报告 unknown。它们都是 mock 远端，仅验证失败关闭行为。

保留失败过程：一次可选 Node permission 模式 4/8 失败（fsync 被禁）、临时顶层 model_name 映射违反 SDK、候选结构正则尚未修正时准备失败、资源压力期 pytest **3 failed / 62 passed**（sdk_process_failed）及离线 `cycle-offline-accepted-2xGsoE/` 的导入 MemoryError；修正或资源缓解后顺序复验如上。没有将上述失败记成通过，也没有因此重试未知远端写操作。

## 20:24 第三次远端拒绝与最终契约 Handoff

主控确认 D 已正常释放本轮两个 viewer 共约 10.94 GiB private commit 后，按 `msg_57fc4d4f784b` 续接同 candidate-v5。仅本次子进程设置 `OPENBLAS_NUM_THREADS=1`、`OMP_NUM_THREADS=1`、`MKL_NUM_THREADS=1`，未改全局环境；此前单次导入检查通过。使用新目录 `asset-cycle-live-20260923-04/`，旧 live03 的零发送失败保留。

第三次实际 publish 于 **2026-09-23T12:24:04.202Z–12:24:06.292Z** 发出一次，request ID **msg_idem_531e357c11d23ae1188ae106da313e0de96b3de9**，HTTP request ID **d1e80785-e50f-4f9f-a993-ed373bf3a989**。Hub 明确 HTTP 400 `capsule_substance_required`：object 型 content 元数据不算可复用正文。计数 **1/0/0**，kg_enrich=false；未发生 FETCH/REPORT，Proxy 已停止。

自有映射已修正：Capsule.strategy 直接复制真实 Gene 的修复步骤与完整代码，不填充假正文；原 content 元数据保留。candidate-v6 的 Gene ID 不变，公开策略逐字来自真实第四轮修复。新候选 SDK 校验与完整官方 Proxy 离线链路通过，证据 `recovery-evidence/cycle-offline-accepted-q2ubQj/`；本地验收仍为 mock 远端 + 真实新样本执行。最终本轨测试命令改用 `--basetemp .runtime/freeze-evolver/pytest-hub-06`，**65 passed / 69.58s**。

完整读取[官方结构协议](https://evomap.ai/a2a/skill?topic=structure)，缓存 `official-structure-reference.json`，发现不能在 E 所有权内合法补齐的下一项：

| 官方事实源 | Capsule.validation |
| --- | --- |
| 当前 Hub structure 协议 | 必填，至少一条 Node/npm/npx 命令；缺失/空为 capsule_validation_required |
| 项目锁定 `@evomap/gep-sdk@1.14.0` / capsule.schema.json | properties 无 validation，末尾 additionalProperties=false |
| 原样 `@evomap/evolver-core@2.0.38` wire gate | 添加该字段后 `validateWireDeep.ok=false`，`wireSchemaIssues` 指明 property=validation / keyword=additionalProperties |

最小只读复现：`node .runtime/freeze-evolver/check-capsule-contract.mjs`。证据 `official-proxy-capsule-contract-gap.json`；原 Capsule schema ok，添加远端要求字段则失败。项目 `NodeAssetBridge` 独立复现保存 `capsule-validation-contract-gap.json`，**asset_id_valid=true、schema_valid=false**，再次确认 hash 沿用 SDK。没有篡改锁定 schema、移除校验、伪造验证结果或升级共享依赖；也没有为探测下一错误发送候选。

第四次远端发布 **NOT_RUN**，candidate-v6 仅是可审查本地候选。Handoff 主控/I/T：需官方 SDK 与 Proxy 同步支持真实远端 Capsule.validation，或另行批准有明确版本与验收范围的官方兼容方案；任何锁/共享 bridge 更改应由其所有者完成。E 已有 schema gap、三次明确拒绝与零发送资源失败的完整证据，不能称 PUBLISH/FETCH/REPORT 已完成。

凭据审计曾覆盖 355 份本轮 evidence/log 文本，未检出 node secret 原文；用户 `C:/Users/DW/.evolver/settings.json` 仍不存在。来源 model/返回 ID、未知 token/cost、独立结构/行为验收、缓存/真实 FETCH 边界均分别保留；API sandbox、T4、治理与锁文件未改。

### 官方最新版本与 fresh-sandbox 条件复核

只读查询 [npm 官方 registry](https://registry.npmjs.org/@evomap/gep-sdk/latest) 得到 latest **1.14.0**，gitHead **e19d83b8da63989e453cc13903e3d0acedfefca6**，SDK 许可证 **Apache-2.0**；元数据保存在 `sdk-latest-metadata.json`。官方 [EvoMap/gep-sdk-js 主分支 package.json](https://github.com/EvoMap/gep-sdk-js/blob/master/package.json) 同为 1.14.0，[Capsule schema](https://github.com/EvoMap/gep-sdk-js/blob/master/schemas/capsule.schema.json) JSON 与本项目锁定版本一致；下载证据 `sdk-master-capsule.schema.json`。没有发现已发布的官方兼容版本，因此没有安装升级、修改锁文件或自编 schema。

官方 structure 还要求 validation 可在 fresh sandbox 自包含执行。四条 Node 检查确实读取本机 sample.py：在真实坏/修复文件上的结构结果有效，但在新空本地目录中**四条均以 ENOENT 失败**，证据 `fresh-directory-structural-result.json`。这是本地文件依赖复现，不是远端 sandbox 运行；不能把它称为满足远端自包含条件，也不因此否定已有 Python 独立行为验收。不得通过嵌入“通过”常量、另造无关 Node 任务、启动 Python 外壳或移除安全门来补证据。

最终未完成操作：真实 PUBLISH 接受、指定同一 asset_id 的远端 FETCH、该远端资产实际使用 REPORT、G3/G4 翻绿。继续工作需要官方字段契约对齐，以及针对真实 Python 修复、可在目标 sandbox 独立执行的有效验证方案；当前没有该方案的官方运行证据。第四次真实写入未执行。

## 官方 HubFetch 直连替代的审阅候选

主控 `msg_c9f9d76ce7e4` / `msg_f67f4331e138` 指出任务书允许直连替代，授权先准备可审查结果，真实发送仍需具体候选审阅。新增内容全部是 `.runtime/freeze-evolver/` 下的 `direct-prepare.py`、`direct-cycle.mjs`、`direct-use.py`，**source=hub_direct**；未改变 HubClient.local_only 或冒称 Proxy 兼容。

`candidate-direct-02/` 的三个资产顶层 model_name 均为真实请求 ID `evomap-gpt-5.6-luna`，返回模型与历史网关 response ID 仍单列。官方 SDK 对**完整 wire**计算/验证内容地址，使用其默认仅排除 asset_id 的规则，没有自定义 hash 或 hash 排除列表。由于当前文档新增字段不在旧 SDK，完整旧 schema 校验为 false；另对仅移除 model_name（Capsule 再移除 validation）的基础投影重新调用官方 SDK，单列基础 schema passed，不将投影冒称完整 wire。官方 Hub 的真实远端校验继续执行；不使用或绕过原 Proxy 内部 gate。

自包含结构验证使用真实修复文本作为 Node 断言输入，验证谓词仍为原四项；在空目录里坏文本 exit 1、真实修复文本 exit 0，目录保持空。最终命令长 808 字符，无文件读取、外壳、spawn、分号或 pipe；公开 Capsule 明示 **structure only, not Python behavior**，以及由 E 编写、非历史模型生成。它证明内嵌真实 artifact 的结构，不宣称执行了 Python。FETCH 后效果仍必须由 `direct-use.py` 用独立 SampleVerifier 在新坏样本上先 0/3 再实际采用获取代码到 3/3，保存真实 UseRecord/TaskResult 后才能 REPORT。

| direct 候选 | 完整官方 SDK asset_id |
| --- | --- |
| Gene（定向获取目标） | `sha256:c3862d97f0f2e93f06b250b9046b2f56fa6858afaa29102fe22d59ae934f9b6e` |
| Capsule | `sha256:a372fba521210354bdfcf22fcf499478f8a46a5ee8634b0da0c157edfcca0f78` |
| EvolutionEvent | `sha256:cd57f8d2a15363f8c6ae4af32799ab6705fedd396d72653ed8f5b2ef1be036ae` |

官方 `HubFetch`、`gepEnvelope` 与 `publishRespToReceipt` 原样复用。每阶段 wx/fsync 先存请求，再一次 POST；固定节点/原 secret 不变，`EVOMAP_HUB_IP_FAMILY=ipv4-only` 禁用官方 transport 的地址族 fallback，不循环、不重试、不重新 hello，不启动 Proxy。路线为 `/a2a/publish`（kg_enrich=false）、`/a2a/fetch`（唯一指定 Gene ID）、真实采用后 `/a2a/assets/{encoded asset ID}/reuse-result`。FETCH 完整内容必须 SDK hash 匹配；REPORT 要有 raw recorded=true 和非空 receipt id。所有新 token/cost 继续 null，未填 tokens_saved/time_saved 估值。

直连离线结果：成功 `direct-offline-accepted-bTTbd2` 为 **1/1/1**、独立 Python 新任务 0/3→3/3；断连 `wl9lNf` **1/0/0**，缺发布回执 `6aSooK` **1/0/0**，篡改 FETCH `2dTU28` **1/1/0**，空 REPORT `TcOyOW` **1/1/1** 且 unknown。全部位于 `recovery-evidence/`，前缀分别为 `direct-offline-disconnect-`、`bad-receipt-`、`tampered-`、`empty-report-`；失败案例 exit 1 为预期停止，未重试。此节仅记录准备和 mock 网络结果，尚不构成真实 direct 接受回执。

## 20:42 真实直连决策及 20:47 认证状态核对

主控审阅全部 direct 代码与固定三个 ID，经 `orca orchestration ask` 批准一个直连窗口；D 公共读已结束。按 `msg_f60c47cc979a` 增补 HTTP 200 的 status rejected/quarantined、success=false、degraded/local_fallback 负例，均按预期停止且没有下游使用/REPORT。最终成功离线证据 `direct-offline-accepted-cwldPo/` 仍为 1/1/1；这不改变其 mock provenance。

真实命令 `node .runtime/freeze-evolver/direct-cycle.mjs --live` 于 **2026-09-23T12:42:12.977Z** 发出唯一 publish，**12:42:18.339Z** 保存回执。证据 `.runtime/freeze-evolver/direct-live-20260923-01/`：

| 字段 | 实际值 |
| --- | --- |
| source / provenance | hub_direct / live |
| 请求 message ID | `msg_1790167332976_8501df49` |
| HTTP request ID | `a2b3a3d7-d1ef-44c6-b687-8c233a45262c` |
| Hub 响应 ID / 时间 | `msg_1790167338046_00f46f86` / `2026-09-23T12:42:18.046Z` |
| HTTP / GEP | 200 / message_type=decision |
| decision / reason | **quarantine / newcomer_candidate** |
| bundle ID | `bundle_d4f8d679b30b5974` |
| asset_ids | 与 candidate-direct-02 的三个完整 SDK hash 全部一致 |
| 正常 accepted / receipt_id | 没有；不能记 accepted 或 promoted |
| transport 计数 | publish=1、fetch=0、report=0 |

runner 当时将缺正常 accepted receipt 记为 unknown 并停止，原文件保持不变；`disposition.json` 是读取原件后的单独审计解释：Hub 明确已给出候选隔离决策，不是“完全没收到内容”，也不是接受发布闭环。没有重发。领域代码补充识别单数 `quarantine`，防止矛盾的 accepted 状态/receipt 字段掩盖隔离决策；新增对应负例后本轨最终 **66 passed / 53.03s**（`pytest-hub-final`）。

主控 `msg_d2662ffd2018` 随后只授权按正常流程读本节点资产状态。官方[可信验证框架](https://evomap.ai/wiki/13-verifiable-trust) 将初始发布很少的节点纳入 candidate 审核；普通[fetch 协议](https://evomap.ai/a2a/skill?topic=fetch) 说明返回 promoted 资产，并列出认证 `GET /a2a/assets/:asset_id?detailed=true` 详情路由。未修改身份、信号、账户设置、信誉或推广状态。

执行一次 `node .runtime/freeze-evolver/candidate-status.mjs`，只读上述 Gene ID，证据 `candidate-status-20260923-01/`；**2026-09-23T12:47:31.850Z** HTTP 200，HTTP request ID **cc914342-b983-45e9-a8fb-3481d70d2bf8**。实际状态：

- Gene.status=candidate，source_node_id 为固定节点，model_name 为真实 `evomap-gpt-5.6-luna`；关联 Capsule 也为 candidate。
- validation_status=noop、validation_credible=false、payload_ready=false、callable=false、attested=false。
- payload 只有摘要字段，没有 strategy、完整 asset_id 或可用于相同内容地址的正文；官方 SDK 对该片段计算不匹配目标完整 asset_id。不是一次成功完整 FETCH，更不能用本地候选/缓存补齐后称为远端读取。

此查询只核实平台真实状态，没有运行候选或补发 REPORT。自包含 Node 检查在本机观察公开 artifact 结构的结果保留，但 Hub 的 noop/not-credible 判定说明它不构成平台认可的行为验证；没有 Hub sandbox 的通过回执。真实 Python 独立 3/3 与离线真实新任务采用仍只覆盖已注明的本地验收范围。

## 20:56 指定同一资产 FETCH 的最终外部门禁

主控允许沿正常认证流程核对本节点资产，并在请求前收到具体边界预告 `msg_f76e8844e215`。执行一次 `node .runtime/freeze-evolver/candidate-fetch-status.mjs`，通过官方 HubFetch 向 `/a2a/fetch` 发送唯一 `asset_ids` 目标 Gene `sha256:c3862d97f0f2e93f06b250b9046b2f56fa6858afaa29102fe22d59ae934f9b6e`；没有覆盖 candidate 状态、搜索其他资产或夹带任务。证据目录 `.runtime/freeze-evolver/candidate-fetch-status-20260923-01/` 保存脱敏请求、响应及 summary。

| 字段 | 实际值 |
| --- | --- |
| source / provenance | hub_direct / live |
| 请求 message ID / 时间 | `msg_1790168186661_01722cb8` / `2026-09-23T12:56:26.661Z` |
| 请求开始 / 完成 | `2026-09-23T12:56:26.702Z` / `2026-09-23T12:56:30.491Z` |
| HTTP request ID | `5afdf2ed-b399-4081-9ca0-dad626ebcaa6` |
| Hub 响应 ID / 时间 | `msg_1790168190181_c4fa12da` / `2026-09-23T12:56:30.181Z` |
| HTTP / status / reason | 200 / confirm_required / confirm_required |
| 成本预览 / 余额 | **3.36 credits / 0 credits**；这是预览，不是实际扣费或已支付成本 |
| 返回资产 / 实际使用 / REPORT | **0 / 0 / 0** |

确认 token 已在持久化响应中替换为 `[REDACTED]`，没有发出确认请求、充值、重复 FETCH 或 REPORT。主控 `msg_42eb29129505` 明确确认该外部门禁并要求封板；不从详情片段或本地候选补齐正文，不修改身份、信誉或推广状态。真实直连发布与这一次 FETCH 均已计入记录，但没有满足“同 hash 完整远端资产 → 实际使用 → 效果 REPORT”的验收。

后续只能由账户操作者沿官方审核及费用流程处理。[官方可信验证说明](https://evomap.ai/wiki/13-verifiable-trust) 将初始发布次数不超过 1 的节点资产强制纳入 candidate；新节点需较高的 AI 质量阈值（0.6）或 validator pass。[官方信誉说明](https://evomap.ai/wiki/06-billing-reputation) 列出的普通自动推广条件包含 GDI 下界至少 25、intrinsic 至少 0.4、confidence 至少 0.5、节点信誉至少 30、验证者未形成失败多数，并有小时级批处理；本轮没有这些条件全部满足的证据，也不能承诺等待后必然推广。候选的 noop/not-credible 仍需平台认可的有效验证；不通过自评、质押、刷信誉或更换身份规避。

剩余人工/外部操作：正常审核与有效验证方案、账户费用授权及可用额度；条件满足后须另获有界执行授权，实际取得完整同 hash 正文并在独立新任务中使用成功，才可提交真实 REPORT。当前没有授权确认费用或充值，未知 token/cost 仍为 null；本轮不继续远端请求。原样 Proxy 的 Capsule.validation schema 差异也仍待上游兼容，直连候选不能代替 Proxy 兼容验收。

最终领域验证（进程内 `OPENBLAS_NUM_THREADS=1`、`OMP_NUM_THREADS=1`、`MKL_NUM_THREADS=1`）：

```powershell
.venv/Scripts/python.exe -B -m pytest -q tests/t1/hub --basetemp .runtime/freeze-evolver/pytest-hub-final
.venv/Scripts/python.exe -B -m mypy --strict hub_client
git diff --check -- hub_client tests/t1/hub docs/tracks/freeze-evolution.md
```

结果为 **66 passed / 53.03s**、**mypy 4 files passed**、**diff check exit 0**。提交前审计于 `2026-09-23T13:08:55.636511Z` 扫描 **608** 份自有代码/报告与运行证据文本，未检出节点密钥原文；确认 token 已脱敏、真实用户 settings 不存在、共享 index 为空，证据 `.runtime/freeze-evolver/final-security-audit.json`。前置 hello/heartbeat/完整工具进程为真实验证；Hub 代码测试和离线收据为 contract_local/mock，真实远端只证明已记录的拒绝、候选隔离及费用确认门禁。API sandbox、T4、共享 contracts、锁依赖和治理文档不在 E 的修改范围。
