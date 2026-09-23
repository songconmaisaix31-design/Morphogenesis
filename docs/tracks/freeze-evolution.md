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
