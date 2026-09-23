# 封板夜 E：Evolver 前置与 Hub 适配

## 当前结论（2026-09-23）

前置二 **BLOCKED**。唯一真实 bootstrap hello 未满足本轮固定身份/model 元数据要求，且被 Hub 明确拒绝；未获得节点凭据，未执行第二次 authenticated hello、heartbeat、远端 PUBLISH/FETCH/REPORT。G3/G4 没有新增通过证据，不能称已完成合规 hello。

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
