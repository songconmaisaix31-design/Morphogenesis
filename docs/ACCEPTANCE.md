# 验收矩阵

## G3/G4：真实候选已入 Hub，FETCH 被余额确认门禁阻止（2026-09-23 21:03 CST）

官方 Proxy 2.0.38 与最新 GEP SDK 1.14.0 的 Capsule schema 不支持当前 Hub 必填的 `validation` 字段；原 `local_only` 校验器、SDK/schema、锁文件均未修改。按任务书允许的直连路线，复用官方 HubFetch、GEP envelope 与 SDK 内容寻址，以固定原节点发布一次 Gene/Capsule/EvolutionEvent；所有资产记录真实模型 `evomap-gpt-5.6-luna`、实际 blast_radius=1 file/17 lines，`kg_enrich=false`。基础 schema 投影通过不等同于完整 wire schema 通过；Python 独立行为验收与自包含 Node 结构检查分别记录，后者不冒称执行 Python。

| 真实阶段 | 回执及结论 |
|---|---|
| PUBLISH | `2026-09-23T12:42:12.977Z` 发出，HTTP 200；请求 `msg_1790167332976_8501df49`，HTTP ID `a2b3a3d7-d1ef-44c6-b687-8c233a45262c`，响应 `msg_1790167338046_00f46f86` / `12:42:18.046Z`。明确 **quarantine / newcomer_candidate**，bundle `bundle_d4f8d679b30b5974`；没有正常 accepted receipt，未重发。 |
| 同一 Gene | `sha256:c3862d97f0f2e93f06b250b9046b2f56fa6858afaa29102fe22d59ae934f9b6e`；Capsule `sha256:a372fba521210354bdfcf22fcf499478f8a46a5ee8634b0da0c157edfcca0f78`；EvolutionEvent `sha256:cd57f8d2a15363f8c6ae4af32799ab6705fedd396d72653ed8f5b2ef1be036ae`。三个 ID 与官方 SDK 完整内容哈希一致。 |
| 认证详情 GET | `12:47:31.850Z`，HTTP ID `cc914342-b983-45e9-a8fb-3481d70d2bf8`；candidate，validation_status=noop、validation_credible=false、payload_ready=false、callable=false。返回摘要缺正文，不能以本地候选补齐或视为完整 FETCH。 |
| 精确 POST FETCH | `12:56:30.491Z`，HTTP 200，HTTP ID `5afdf2ed-b399-4081-9ca0-dad626ebcaa6`，响应 `msg_1790168190181_c4fa12da`；**confirm_required**，1 项资产预览 **3.36 credits，余额 0**，result_count=0。没有确认付费、充值或重复请求，确认 token 脱敏。 |
| 实际使用 / REPORT | **NOT_RUN**。没有取得可验证的远端完整资产，不能拿本地副本、离线运行或 HTTP 200 代替闭环。 |

源码基于发送时主线 `78dfdd9e39a513cd6c602dc78d4b3f3c76d2ee13` 加 E 待提交修改，不能冒称当时已有 E 提交 SHA；E 最终实现及报告随后提交推送为 **`4938bb9230cf3acaf2cff63774f743a8a20d5bad`**。证据分别在 `.runtime/freeze-evolver/direct-live-20260923-01/`、`candidate-status-20260923-01/`、`candidate-fetch-status-20260923-01/`；原 runner 的 unknown 保留，单独 disposition 解释明确候选回执。前三次 Proxy HTTP 400、一次发送前 MemoryError、离线 mock 结果均保留于 [E 报告](tracks/freeze-evolution.md)。E 最终领域回归 66 passed，尚待 I 全量复核。

21:00 前后主控通过用户指定 Chrome 读取官方节点页面：固定节点 Online、Published=1、Promoted=0、Rejected=0，三个精确资产链接均已出现。这证明平台展示了候选，不等于 promoted、可调用或成功 FETCH。官方[可信验证框架](https://evomap.ai/wiki/13-verifiable-trust)和 [FETCH 说明](https://evomap.ai/a2a/skill?topic=fetch)支持按正常候选审核流程继续；没有更换身份、修改信号、提升信誉、调用 Hub sandbox 或改变账户开关。**G3/G4 仍未通过：需满足平台可信验证/晋升条件，并解决真实 FETCH 余额与确认门禁，再验证同 ID 内容、实际使用和 REPORT。**

## G5 网络切换后的只读复验（2026-09-23 21:01 CST）

主机 WLAN 从 `192.168.60.54` 变为 `172.20.10.2`、网关 `172.20.10.1`。旧地址恢复 viewer 时返回 WinError 10049；该失败日志保留，没有修改网络配置。主控核实新接口及空闲端口后，以进程环境 `MORPH_BIND_IP=172.20.10.2` 恢复 7799，7526 保持 loopback 历史 replay；局部 BLAS/OMP/MKL 线程数为 1，未改全局设置。7527 未启动，仍缺独立模型网关凭据。沿用 DECISIONS 已记录的“本机单屏运行，无需外接投影”决定；不把投影接线重新加入前置，现场人工观看仍与浏览器自动检查分开。

在新网络配置下运行 `python deploy/smoke.py http://172.20.10.2:7799 --direct --with-fonts` 及 `python deploy/smoke.py http://47.93.118.110:7799 --with-fonts`，分别 32 / 38 项检查、两者 exit 0；未调用 Hub 或模型。日志与网络元数据位于 `.runtime/freeze-demo/coordinator-network-*`，三态仍为 replay / passed,not_run,not_run。系统仍有 Mihomo 虚拟网卡；热点身份尚待操作者确认，不能据私网地址推断已经完成无代理热点、第二设备或现场人工验收。

## G5 公网只读软件链路通过（2026-09-23 20:39 CST）

公网入口：[http://47.93.118.110:7799/](http://47.93.118.110:7799/)。实际部署代码为主线 **`53bb52c31ab68655e2bca620508488d7f95e00e6`**：在本机按标准89文件白名单构建 linux/amd64 API/Web，容器 healthy 后完成包含限流/方法/请求体/字体的 nginx smoke，再 `docker save` → SCP → `docker load`。镜像归档 **172410880 bytes**，SHA-256 `4f732b04d365531d192b3235a9882b4b53c1fb4581f43ec47313161267088040`；远端独立目录 `/opt/morphogenesis/releases/53bb52c31ab68655e2bca620508488d7f95e00e6`，只挂载前述第四轮单个 `rehearsal.json`，强制 replay，不含节点或模型凭据。

先验证 loopback 两容器健康与 smoke，再按环境变量将 Web 7799 绑定到 `0.0.0.0`。20:35:18 的唯一安全组新增请求 `01A0CE43-6F8C-5D25-B744-43AD24C15E7F` 成功，规则 `sgr-2ze0gdv6v5l8uvesxy6p` 仅开放 TCP `7799/7799`；原五条规则保持，共治四容器 healthy，80/443/8080 映射未改。公开脚本尾部 CRLF 空行曾报错，前面的 up 已成功；仅只读确认状态后接续，未重放整个 recreate 脚本。

从本机经真实公网地址执行 `node tests/integration/check_frontend_replay.cjs`，**72 passed / 0 failed**，覆盖1366、1920、375三个视口、同源API、字体、拓扑、详情及三态；无 pageerror、console error、HTTP failure。原件 `.runtime/freeze-demo/browser-public-53bb52c/summary-replay.json` 与实图已由主控复核。一次正常页面读取真实 Hub 公共数据，`evomap.json` 显示 `/a2a/assets/semantic-search`、`public_read_observed_no_credentials_sent`；它是公开只读区的 live 证据，不是当前 Gene 发布或执行闭环。主任务仍为 **replay / passed,not_run,not_run**。

本次解决公网部署与软件显示/探针链路；**G5 整体现场验收仍未通过**：新7527网关演示缺独立模型凭据，热点/第二设备和现场单屏人工见证未执行。G0 上游硬预算限制不变。G3/G4 的 Proxy 发布因最新官方SDK与远端结构契约不兼容仍未通过，正在按任务书允许的官方HTTP直连准备真实证据，不把公开搜索、回放或本地测试换算成发布成功。

## 封板夜适配、回归与首次发布结果（2026-09-23 19:54 CST）

D 实现 `25968dc8440a25f2472df8cfb7ff62eb3302366d` 已推送：探针复用有类型的验收证据，合法 live 可以通过，空态/mock/replay 保持原三态；只读 viewer 收紧方法、请求体和静态路径。适用测试 **85 passed**，strict **55 files / 0 errors**。[该精确提交 CI](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/35856386250) 的 Windows 与 Ubuntu 均 success，包含 pytest、类型、构建、SDK 和分发检查，修复了之前 Compose 输出省略 false 键导致的失败。此结论不覆盖尚未提交的 E 适配。

T 正式回归在同一代码基线运行 `tests/t2`，**56 passed in 68.94s**，报告提交 `0d7191a43bbc783b2586baa33067269501c08562` 已推送。原竞态修复已在主线：人为延迟 0.217553139 秒时 Gene 权重 0.113547800 仍严格满足实际时间衰减公式，管道反馈权重 1.0→1.9；无需新增 sleep 或改动测试/锁文件。最终累计实现仍交独立 I 完整复验。

E 第一次真实发布在 **2026-09-23T11:50:35.072Z–11:50:38.314Z** 收到 HTTP **400 / validation_error**，明确缺少 `payload.assets[0].summary`。官方 SDK 1.14.0 接受缺少该字段的 Gene，但当前远端 schema 不接受；不能把 SDK 校验通过当作发布成功。请求 ID `msg_idem_4f6c68d8bd882450819e8ecfa014e81eab34cac2`，HTTP 请求 ID `fda29001-ead0-4b4f-accb-6a7ef9874a63`，无响应 message ID。脱敏原件 `.runtime/freeze-evolver/asset-cycle-live-20260923-01/`；publish/fetch/report 次数 **1/0/0**，`kg_enrich=false`，无新增 hello/heartbeat、后台 tick 或自动重试。该候选 Gene 为 `sha256:76c7584dfb2c59c77a8577fd6a23306ae623eef7fa77fb032f42b81cb41d1574`，未发布成功。主控已按原闭环授权安排补齐 schema、生成新不可变候选并验证后执行一次修正请求；G3/G4 仍未通过。

G5：本机 7799 与 7526 的第四轮只读 replay 已经 smoke、healthcheck 和真实 Chromium 三尺寸检查；三态为 passed/not_run/not_run，不算新 live 演示。远端只发送标准白名单代码归档及单个已授权历史快照，后者 SHA-256 与本机一致。唯一 Docker build 因 `registry-1.docker.io:443` metadata 超时失败，未进入 up、没有远端 Morphogenesis 容器或 7799 listener，安全组未改；共治四容器保持 healthy。公网仍 blocked；新网关演示缺独立模型凭据，热点/第二设备与物理展示尚未执行。详见 [D 报告](tracks/freeze-demo.md)。

## 前置二真实通过与领域放行（2026-09-23 19:32 CST）

在主线 `8d0893f957acd0ba463ecc9ec2a8dbac20ad4512` 上，使用用户提供的原节点凭据运行 `node .runtime/freeze-evolver/authenticated-preflight.mjs --live`。真实过程为 **2026-09-23T11:31:11.257Z–11:31:14.845Z / 北京时间 19:31:11–19:31:14**，晚于服务端最早重试时间；主控已独立读取下列脱敏证据核对。

| 环节 | 真实回执 |
|---|---|
| authenticated hello | HTTP 200，`acknowledged`，`your_node_id=node_e2ad48c0d0d63625`；请求 `msg_1790163071257_4eff132f`，Hub 响应 `msg_1790163073002_6cad4984`、时间 `2026-09-23T11:31:13.002Z`，HTTP request ID `1cbd6886-e510-4ada-a356-877ec0b2e183` |
| heartbeat | 唯一一次 POST，HTTP 200 / `ok`，同一节点；请求时间 `2026-09-23T11:31:13.234Z`，结束 `11:31:13.616Z`，HTTP request ID `253de986-5a0a-4209-a3bc-b018ea6a4b8b`。REST 回执没有 GEP message ID，保持 null |
| Proxy | `http://127.0.0.1:19820`，`running=true / hub_auth_status=ok`，出入队列均 0；官方 settings 写入本项目真实证据目录 |
| 官方 MCP 进程 | npm 包 2.0.38，握手 `evolver-mcp / 0.0.0`，23 tools，`evolver_proxy_status` 返回同一节点及 running=true，子进程 exit 0 |

两次回执均无 CAPTCHA、secret 返回或 force update，credit_balance=0；不推断零余额下资产接口的可用性。hello=1、heartbeat=1，无网络 tick、重试或 secret 轮换；前置进程 PID 47272 随 stdin EOF 正常 stop/退出，以上是成功运行证据，不是持续在线声明。原件保存在 `.runtime/freeze-evolver/recovery-evidence/authenticated-20260923-01/` 的 `hello-request.json`、`hello-result.json`、`heartbeat-request.json`、`heartbeat-result.json`、`summary.json`；settings 含本地 IPC 凭据，私有忽略、不发布。

**前置一、前置二均通过，领域工作已放行。** G3/G4 的资产 PUBLISH→远端同 ID FETCH→实际使用 REPORT 尚未执行，不能因注册/心跳成功提前翻绿；G5、正式全量回归和最终双平台 CI 也保持待完成。

19:42–19:43 CST，主控通过 Chrome 正常地址栏重新打开官方 `/account/agents`，已在实际视口确认同一 `Codex Agent / node_e2ad48c0d0d63625` 为 **Online**、reputation=50、published=0；截图 `.runtime/hub-discovery/chrome-agent-node-after-hello-20260923-1942.png` 已查看，仅留本地。Online 是网页对近期心跳的状态展示，不覆盖前置进程已正常退出的事实，也不表示已发布资产。窗口变化后的导航使用现有 Chrome 的 computer-use 完成，未改账户开关、重置凭据、质押或领取任务。

页面同时显示“Auto-enrich Genes via Knowledge Graph on publish”开启。当前 [官方 KG 说明](https://evomap.ai/wiki/20-knowledge-graph) 明确支持单次 publish payload `kg_enrich: false`；E 已核对并将在实际 Hub 出站信封中显式设置、以离线 transport 观测验证，避免官方 Proxy/adapter 只透传 assets 而丢失该字段。保持账户设置原样；这属于原任务不调用 KG 的实现约束，不追加付费动作。

## G0：三层预算护栏与上游边界（2026-09-23）

采用现有实现的“三层预算护栏：入口参数约束 → 过程超时兜底 → 事后审计留痕”，本条只补文档，不修改执行器或自造在途封顶能力。

1. **入口参数约束**：`orchestration.acceptance` 默认 `--max-tokens 20000 --max-cost-usd 1.0 --timeout 120`，参数进入 `RunConfig` 和执行意图；每个 run 至多一次模型调用、`max_retries=0`。网关请求的输出上限为 `min(max_tokens, 4096)`，不等于输入加输出总量硬限；美元参数表达运行预算，不是上游美元扣费开关。
2. **过程超时兜底**：CLI 按超时、无进展或人工停止结束自有子进程；网关使用 httpx 分阶段超时，**不提供整个远端请求的绝对在途截止**。中断后的远端执行/消耗可能未知，不据此自动重试。
3. **事后审计留痕**：保存请求、响应、配置、Attempt 与事件。网关在应用 proposal 前检查实际耗时及上游 reported tokens；超时、超 token 或 usage 不完整则拒绝应用。费用未知保持 null，runtime 标记 unknown_usage，不能把历史任务的未知费用估成 0 或称已证明美元硬封顶。

真实用量沿用已只读复核的第四轮原始记录（2026-09-22 16:12–16:13 CST，入口提交 `7c0bb6a2f7b39a7eb524c0c71bc31c7a110f883c`，报告 `61784b73be6b2a47a3a45f8e206678d4f932ae59`）：请求模型 `evomap-gpt-5.6-luna`，实际返回 `gpt-5.6-luna`。repair 请求 `chatcmpl-EQpuANHdosqb3LPB9d5BwQR7htK71`：544 输入＋343 输出＝887 tokens、8.078 秒；recovery 请求 `chatcmpl-EQpuYs6th4TaCYHgMxMBqm7nNT65Y`：905＋443＝1348 tokens、10.343 秒；均 HTTP 200，两次合计 **2235 tokens，cost_usd=null**。这是两个分别授权的新任务，不是失败重试，本次未为文档追加模型调用。原始证据根及验收命令见下文“第四轮”。

G0 的受控运行叙事已补齐，**上游单次调用的在途 token/美元硬封顶限制仍然存在**，不因此把 G0 硬预算判为充分通过。Chrome 已核实 Free 方案；KG 访问受方案限制，已预留接口，未请求 KG 或购买 Premium。

## 原节点凭据恢复与完整离线前置（2026-09-23 19:14 CST）

用户已提供 Chrome 账户中固定节点 `node_e2ad48c0d0d63625` 的新凭据。仅保存于项目 `.runtime/freeze-evolver/private/node_secret`，Git 忽略和仅当前用户可访问的目录权限已检查；秘密不进入文档、参数、Git 或日志。没有再次 Reset Secret、创建身份或修改全局 settings。主线授权记录为 `8d0893f957acd0ba463ecc9ec2a8dbac20ad4512`；真实请求必须遵守原回执的最早时间 **19:30:52.373 CST**，不是视为 CAPTCHA 已解除。

E 新增的忽略目录前置 runner 使用未修改的官方 2.0.38 Proxy/PublicHubCapability 与受限 transport：hello 补齐真实执行模型 `gpt-6-astra`、名称和官方环境指纹，明确禁止 secret 轮换；仅允许一次 hello 和其确认成功后一次 heartbeat。HTTP 200 rejected、不完整身份、认证错误、断连或未知效果均停止；不开周期 tick、资产同步、自动发布、任务领取、自更新或付费功能。成功时仅在项目目录发布官方 Proxy settings，监听 `127.0.0.1:19820`；之后调用官方 npm `evolver-mcp` 子进程的状态工具，验证发现与认证路径。此处模型是当前接入 Worker 的模型，不覆盖历史资产生成模型。

验证命令：`node --test .runtime/freeze-evolver/authenticated-preflight.test.mjs`。Worker **8 passed / 0 failed / 8956.7705 ms**，证据 `authenticated-offline-uIp41Y`；主控独立复核 **8 passed / 0 failed / 9072.4801 ms**，证据 `authenticated-offline-BLHwNr`。覆盖完整 Proxy/MCP 启停、准确两条注入出站、跨 5.5 秒 verifier 窗口无额外请求、拒绝不生成 settings、错误不重试、诊断脱敏、spawn/EOF 超时有界、原 guard 与用户 settings 不变。全部网络回执为 `mock`；没有将真实本机进程成功等同于真实 Hub 接口成功。

本条记录时真实新增 hello/heartbeat/PUBLISH/FETCH/REPORT 均为 0，前置二仍未通过；等待时限后继续已授权的单次真实恢复，不要求用户重复确认凭据使用。

## Hub 官方协议与浏览器恢复调查（2026-09-23 18:52 CST）

用户追加要求继续沟通 Hub、核对官方接入材料，必要时 computer-use。本轮在 `3786659dfde536a3b37b571ff0b198821f07aa24` 上继续前置调查，没有再次注册、发送 heartbeat 或发布资产。官方公开文档、Help API 均可访问，说明当前不是整站不可达；这不代表节点认证通过。

### 已核实的接入要求

| 接口层 | 需要接入的内容与本项目验收要求 |
|---|---|
| Hub 节点认证 | 首次 `POST /a2a/hello` 使用完整 GEP-A2A 信封、唯一请求 ID/UTC 时间、真实 `model`、公开名称和环境指纹。当前 [hello 协议](https://evomap.ai/a2a/skill?topic=hello) 明确首次 `sender_id` 可省略、由 Hub 分配；后续固定使用 `payload.your_node_id`。先恢复已有身份，不能把拒绝响应的 Hub sender 当作本机节点。`skill.md` 要求名称，简版 Help 示例未展示该字段，本项目取完整要求。任务书的随机 8 位 hex 和旧 helper 的 12 位 hex 均不再作为最新协议唯一要求。 |
| 节点凭据 | 成功 hello 的 `payload.node_secret` 用于后续 `Authorization: Bearer`。网关模型 API key、Hub node_secret、Proxy 本地 IPC token、网站账户 session 是四类独立凭据，不能互换。仅项目内私有状态或进程内存可写；不得按文档默认路径改全局配置。已有 secret 不自动轮换或清除。 |
| Evolver Proxy | 固定官方 2.0.38；`EVOMAP_PROXY=1`，loopback `127.0.0.1:19820`。状态/settings 显式定向项目目录，保留 local_only 校验器。本机 Proxy 监听、认证状态和一次真实 heartbeat 均须单独通过；安装或 HTTP 200 不算通过。 |
| PUBLISH | 官方 GEP SDK 生成/验证内容地址；发布 Gene + Capsule bundle，`blast_radius` 取实际非零变更，`model_name` 取真实生成模型。已装 Proxy 提供 `POST /asset/submit` 的 `mode=sync` bundle 路径；queued/local stored 不能算 Hub 接收。仍须审计内部重试，未知写结果不重发。 |
| FETCH / REPORT | 指定发布的同一 asset_id；Proxy `POST /asset/fetch` 有本地缓存/降级路径，必须保留真实远端拉取证据。实际使用后才发送验证/使用报告；`POST /asset/reuse-result` 的 HTTP 200 仍可能 `recorded=false`，不能算成功。Hub 协议 `POST /a2a/report` 需要 target_asset_id 与真实 validation_report。 |
| 查询与可选服务 | hello/publish/fetch/report 是 POST，但不能泛化成全部 `/a2a/*` 都 POST；官方 Help、部分状态与发现接口使用 GET。KG 是独立方案/凭据范围，不是本轮 Hub 闭环前置；本轮没有请求 KG，仍未核验账户方案。 |

来源：[完整接入说明](https://evomap.ai/skill.md)、[For AI Agents](https://evomap.ai/wiki/03-for-ai-agents)、[A2A 协议](https://evomap.ai/wiki/05-a2a-protocol)、[Evolver 配置](https://evomap.ai/wiki/35-evolver-configuration)。本地只读对照 `@evomap/evolver-adapter-public@2.0.38` 与 `@evomap/evolver-proxy@2.0.38` 的实际安装文件；尚未以真实 Hub 验证上述 Proxy 链路。

### 拒绝解释和 computer-use 实测

官方 `GET /a2a/skill?topic=hello` 返回了与上轮完全同型的拒绝示例：HTTP 200 下 `payload.status=rejected`，原因 `hello_blocked: bulk-fetch antibody active`，带 `captcha_required` 与 `retry_after_ms`。它明确这与设备、IP 或节点身份的反滥用信号有关，拒绝不会发 node_secret；没有据此确定本次究竟是哪一维触发。上次 `10:30:52.373Z + 3600000 ms` 对应最早 **19:30:52.373 CST**，不是保证届时恢复。`GET /a2a/help?q=captcha&limit=5` 返回 0 项，仅表示该发现查询没有结果，不证明不存在人工验证渠道。

Orca computer-use 已在 Tabbit 新标签打开 `https://evomap.ai/account`，页面显示未登录；进入官方登录页 `https://evomap.ai/login?redirect=%2Faccount`，提供 Google、GitHub、邮箱登录。实际窗口树与截图已检查，截图保留 `.runtime/hub-discovery/evomap-login.png`。当前等待用户在浏览器登录或指出已登录的浏览器；没有读取浏览器 cookie、密码或账户 session，也未发送申诉。

官方 [账户状态与恢复说明](https://evomap.ai/wiki/06-billing-reputation) 提供拥有者认证的 `GET /account/agents/:nodeId/status`，可查看 suspension_context、active_antibodies 和 can_self_unsuspend。自助恢复仅适用指定低严重度 bulk_fetch_suspend，一位拥有者每 7 天一次，且不清除 IP/device/user 维度限制；本次尚无登录、已确认节点或适用性证据，不能声称已恢复。需先查看实际状态，再按正常官方流程处理。

公开参考原件缓存位于忽略目录 `.runtime/hub-discovery/`：`official-skill.md`、`official-wiki.json`、`help-hello-concept.json`、`hello-reference.md`（JSON 内容）、`help-captcha.json`。主控恢复原 E Task，仅离线修正前置脚本并复现 v2 hello 的拒绝判定风险；没有修改官方依赖或业务 HubClient。G3/G4 仍 BLOCKED，后续真实闭环、G5 与最终 CI 结论保持下文限制。

### Chrome 账户实测与离线修正结果（19:00 CST）

用户随后指定 Chrome。主控通过其现有登录会话打开 `/account` 和 `/account/agents`：账户显示 **Free**、余额 0、绑定节点 1；节点为 `Codex Agent / node_e2ad48c0d0d63625`，界面 **Offline**、reputation 50、published/promoted/rejected/revoked 均 0，展开 Activity 显示尚无记录。页面未显示 Suspended 或自助解封按钮，这不能代替底层账户状态 API，也不能证明原 hello 限制已解除。已实际检查截图 `.runtime/hub-discovery/chrome-agent-node.png`；截图与账户原文不提交 Git。

本机用户 canonical、当前 Orca Codex 账户 home 的 `.evomap` 及 `.codex/.evomap` 指定路径未找到 node_id/node_secret（仅存在检查，无全盘扫描）。官方页面提供 **Reset Secret**；尚未点击，因为它会替换现有节点凭据，可能使旧客户端失效。已请求用户确认仅重置上述节点，或提供原凭据路径供复用。没有新建/解绑节点、变更 worker/付费开关、质押或充值。账户已登录，故上文“等待登录”已被本条取代；当前待决项为原节点凭据恢复。

E 轨报告 `04602b6223388098d0060576141b9276f88d72a9` 已推送：注入 transport 离线实测，官方 v2.0.38 adapter 对 HTTP 200 CAPTCHA rejected 且已有 sender 的回执返回 `ok=true`，请求还缺顶层 model/name。独立恢复 helper 复用官方信封/HTTP 助手，显式要求身份及元数据，拒绝时 fail-closed，无默认真实网络入口。Worker 与主控各运行 `node --test .runtime/freeze-evolver/recovery-offline.test.mjs` 均 **6 passed / 0 failed**；主控证据根 `offline-PQ8O1X`。旧 bootstrap guard 内容和 mtime 不变，新增真实 Hub 请求 0；这属于 mock 回执验证，不能算 Hub 前置通过。脚本只保留于项目忽略目录，具体限制见 [E 报告](tracks/freeze-evolution.md)。E 本次完整任务仍以 failed/blocked 结算并 release。

KG：Chrome 已核实当前账户为 Free；依据 [API Access](https://evomap.ai/wiki/28-api-access) 的方案要求，**KG 访问受方案限制，已预留接口**。未调用 KG，未伪造一次 403 实测，也未购买或创建 Premium key。账户零余额是否限制具体发布/拉取仍待实际服务回执，不作推断。

## 封板夜前置核查（2026-09-23 18:31 CST）

本轮从主线 `bd10f37c0ad378955210a1a76bd431f31a25ffee` 开始，互斥文件并行计划 `2b58b59` 已推送。**前置一通过，前置二 BLOCKED；尚未放行领域改造、真实 Hub 闭环或新一轮现场演示。** 用户任务书要求两个前置都通过后继续，本条保留实际失败，不以离线适配或旧彩排代替。

| 前置 / 只读核查 | 本轮实测 |
|---|---|
| 网关与第四轮合入 | `git merge-base --is-ancestor 94b70816784fcd46ce4f74b8e205bd009b789cc3 HEAD` 与 `61784b73be6b2a47a3a45f8e206678d4f932ae59 HEAD` 均 exit 0；第四轮报告仍在下文 |
| 历史第四轮原件 | 当前主线 `.venv/Scripts/python.exe -B tests/integration/audit_rehearsal.py <下文第四轮原始根>` exit 0；2 请求、2,235 tokens、21 衰减采样、实际采用和归档一致，29 份文件不变；本轮新增模型调用 0 |
| Evolver 工具准备 | 项目 `.runtime/freeze-evolver/` 内固定安装官方 2.0.38，并安装 1.94.0 比对官方 bootstrap API；没有全局安装或修改用户 home。2.0.38 Proxy CLI 要求已有节点凭据；旧版默认 start 会启动持续行为，因此采用官方模块的受控组合前置，未修改官方源码 |
| 唯一真实 hello | UTC `2026-09-23T10:30:49.970Z`–`10:30:52.458Z`，Hub 回执 `msg_1790159452373_c5ed9018`，`status=rejected`、`reason=hello_blocked: bulk-fetch antibody active`、`captcha_required=true`、`retry_after_ms=3600000` |
| 本次请求不符合任务书之处 | 后续源码审计发现官方 v1 helper 自行生成 `node_` 加 12 位 hex，未按任务书预置固定身份，payload 未携带 `model`；拒绝前请求 node ID 未留存。此项是本次执行缺口，不能仅把前置失败归因于外部 CAPTCHA，不能称已发出符合全部硬规则的 hello；不补造元数据、不重注册 |
| 尚未发生的副作用 | 没有获得节点凭据；v2 authenticated hello、heartbeat、19820 Proxy listener、PUBLISH/FETCH/REPORT 全未执行；没有自动重试、更换身份、升级、领任务或质押 |
| 本机/远端条件 | 初始仅 7844 本地回放监听；7799/7526/7527 尚未激活。本机 Docker daemon 不可用；已配置 `gongzhi-ecs` 只读连接成功、原共治容器健康，Morphogenesis 公网仍未部署。当前 Worker 进程没有 `MORPH_EVOMAP_API_KEY` |
| 竞态历史定位 | `e83a816` 失败针对 adopted Gene `weight > 0.5`，已由 `94b7081` 改为实际 elapsed/tau 公式并覆盖 0.2 秒延迟。`pipes[0].weight` 的反馈更新为同步路径，不能靠额外等待改善；T 轨已在未改测试代码下基线 7 passed，正式收尾回归尚未放行 |

脱敏回执位于本项目 `.runtime/freeze-evolver/bootstrap-hello.json`、`preflight-result.json`，不入 Git。外部拦截的 CAPTCHA 需用户在正常官方流程处理；不以换身份或换网络规避。E/D/T 当前只整理前置报告，等待用户是否调整开工门禁。G3/G4 外部部分保持 BLOCKED，G5 新软件演示/陌生网络/物理展示保持 NOT_RUN。

### 本阶段报告与自动 CI（18:40 CST 收尾）

T 核查报告 `9f59c0046ea6079f92c42b28eec5661c04c9373b`、E 阻塞及请求缺口报告 `4962d52053fc8654857a6825d223f2eb1a891926`、D 只读审计报告 `8141d5de4a87e5d31b1bf1c3ecc95efac6c59feb` 均由各自 Worker 直接提交并推送主线；详见 [T](tracks/freeze-race.md)、[E](tracks/freeze-evolution.md)、[D](tracks/freeze-demo.md)。三个 Dispatch 均以 `failed / preflight blocked` 如实结算并释放，表示完整原任务未完成；已完成的环境和核查产物保留。未启动 I 集成或后续开发。

文档 push 自动触发的 CI 已实际运行，不能写成 CI 未执行，也不能沿用双平台全绿。`gh run view 35849890857 --json headSha,status,conclusion,jobs` 与 `--log-failed` 核实 [8141d5d 的 CI](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/35849890857)：Ubuntu `python -m pytest -q` 为 **1 failed / 254 passed / 1 skipped**，`tests/deployment/test_deployment.py:128` 在 `mount["bind"]["create_host_path"]` 处 `KeyError: 'create_host_path'`；Windows job 被矩阵取消，后续类型/构建/包验证未完成。前一文档提交的 [CI 35849678131](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/35849678131) 同一失败。本轮变更只含文档，这不是上文已修复的 Gene 墙钟断言；恢复工作后由 D 负责核查 Compose 配置输出兼容性和返修，不能简单删掉只读挂载安全断言。

尚未完成：合规 hello/heartbeat 与真实 Proxy、G3/G4 适配及三步证据、G5 软件和公网部署、正式本地全量验证与最终双平台绿灯、G0 三层护栏文档实施。G0 的历史真实用量已只读复核为 2,235 tokens / cost=null，未增加模型调用；KG 未请求，当前账号方案/权限未核验。恢复需要用户明确处理原开工门禁；新网关运行另需安全提供项目凭据，热点/第二设备及物理展示仍需人工。

## Linear 原包直接改造与本地后端集成（2026-09-23）

F `d0724a6a2f32f2f03860bbab06ebb82266abdcaf` 直接复用用户 Linear 包的应用 DOM/组件结构、源 CSS 与 11 个 SVG，形成真实任务、拓扑、Gene、证据、EvoMap 五视图；保留黄色原生黏菌、无鼠标/触屏趋食和双语序幕。独立 I 普通合入 F、D `50d1353` 与治理；最终 `7c24398e99b526b8ca45de077079db9c46de86ed` 已推送并由主线 fast-forward 接收。旧 `2df3138` 后台视觉通过结论仍撤回，不混用旧截图。

| 本轮实际验证 | 结果 |
| --- | --- |
| 锁环境 `npm --prefix viz/frontend run build` | 通过；归一化构建产物与 F 相同 |
| `.venv/Scripts/python.exe -m pytest tests/t5 tests/deployment -q` | 67 passed |
| `.venv/Scripts/python.exe -m mypy --strict viz/server.py` | 1 source file success |
| `node tests/t5/check_reference_layout.cjs <7844> <output> <fixture>` | 131 项通过；明确 mock/浏览器注入，0 页面错误、非同源/非 GET 请求 |
| `node tests/integration/check_frontend_story.cjs <7844> <output>` | 原序幕、显式进入、键盘、深链、三视口与减少动态效果通过 |
| `node tests/integration/check_frontend_replay.cjs <7844> <output> replay` | 72 项通过；直接读取真实 API，未注入响应；1366/1920/375 五视图、字体、详情、数据事实、0 控制台/HTTP/页面/外域错误 |
| 历史原件与来源 | 226518 bytes、mtime、SHA-256 前后不变；API 为 replay / passed / not_run / not_run，费用未知 |

主控亲看源应用、新版桌面/手机、成员详情、稳定后的 Gene 图和黏菌双语帧。I 发现默认 favicon 404 后，经主控认定为入口配置胶水补一行 data favicon；保留首次 71/1 失败记录，修复后严格复验通过。未弱化事实或错误断言。命令、证据根和资源来源见 [完整 I 报告](tracks/frontend-gpt-reference-integration.md)。

预览 [后台](http://127.0.0.1:7844/#/workspace) / [序幕](http://127.0.0.1:7844/#/physarum) 使用服务端 `--replay` 读取第四轮单个原件。I 终端释放后，主控核验空闲并 Hidden 恢复同一验收工作树，launcher 41400 / listener 44240；恢复后真实 API 已复查。未新增模型任务或 Hub 写入。公网部署交接命令被自动审批拒绝，最终 F+D 组合容器、公网与物理展示仍 NOT_RUN；D 单轨历史容器通过不替代这些验收。用户提供快照及字体许可未核实的限制保留。

## 视觉改版验收（2026-09-23）

按用户最新“完全放弃现有前端、复用大厂模板”指令，复用腾讯官方 [TDesign React Starter](https://github.com/Tencent/tdesign-react-starter) Dashboard，固定 `fce97863edd5d5556f766dd4e342aace31a99487` / package 0.3.1 / MIT。实际接入 Board、Dashboard TopPanel 和 AppLayout 源码结构以及 TDesign 组件，来源映射见 [F 报告](tracks/frontend-stack.md)。仅触达产品展示层：本次包含 DOM、展示 JS、React/Vite 静态构建与 CSS，不是仅 CSS 改版；后端、数据格式、原 11 项 T5 测试、原 observer 和几何断言未改。旧前端保留在 Git 历史。

Kimi F `morph-frontend-stack` 最终 `f99d13988465cd7e56db591ec2cdbbbca2bee553` 已推送；其中 `b2f61d476fab43dfa0d78c8c84cd83f234169e84` 补齐三大数字 300ms 淡入，最终提交补齐实际 bundle 的 lodash-es 许可证。独立 I `morph-finals-integration` 完成精确 SHA 普通合并，最终 `c62bab718265580cbe9941bfcb8d6ca9f63828c6` 已推送且远端一致，主线 fast-forward 接收。完整命令、失败修正和证据见 [集成报告](tracks/finals-integration.md)。

| 验证 | 结果 |
|---|---|
| `PY -m pytest tests/t5 -q` | 原 11 项全部通过 |
| `node --test tests/integration/test_browser_options.cjs tests/integration/test_observer_control.cjs tests/integration/test_operator_enter.cjs` | 原 31 项全部通过 |
| `node tests/integration/check_finals_replay.cjs SOURCE OUTPUT` | 历史 20 快照 × 1280×720 / 1366×768 / 1920×1080，共 60 帧通过；原几何检查、真实阶段事实、当前任务 token、活跃 Gene 与四态、错误/空态复位通过；0 JS 错误、0 外部请求 |
| 数字与动态效果 | 真实变化 300ms 淡入、同值轮询不闪烁、reduced-motion 无动画；F 另测 390×844 窄屏通过 |
| `npm --prefix viz/frontend ci` / `npm --prefix viz/frontend run build` | 干净依赖安装、构建通过，生成文件可复现 |
| `PY -m build` / `tools/check_distribution.py --site-dir ... --check-node` | sdist/wheel、11 个安装包资源、独立验证器、Node 依赖通过；15 个静态资源与源码字节一致；7 个实际 bundle 运行依赖的许可证齐全；无 node_modules / .runtime 入包 |
| 原证据只读审计 | 29 文件集合、大小、SHA-256 与纳秒 mtime 不变；模型请求 0 |

最终动效版截图和 JSON 在 `C:/Users/DW/orca/workspaces/Morphogenesis/morph-finals-integration/.runtime/candidate-b2f61d4/`，许可补丁不改变页面。两档各保留 `initial`、`task-in-progress`、`member-offline`、`recovery-completed` 四张命名截图，共 8 张，并保留全部 60 帧。I 已逐张检查关键帧，协调者检查初始、下线及完成画面。

协调者核对旧 7527 listener 14944 / parent 36668 的命令行与回放源后，仅停止该 listener，在已验收 I worktree 启动相同只读源的新页面，listener 40228。API 返回 replay 与 `passed / not_run / not_run`；实际 `http://127.0.0.1:7527/` 通过 `check_finals_layout.cjs` 三视口及动效检查，1280/1920 的 Gene 台账底部分别为 686/746，均在首屏；截图在 I 的 `.runtime/finals-7527-handoff/`，页面已在 Orca 打开。工具管理的本地服务不承诺跨宿主退出常驻，7526 未操作。

原 `observe_rehearsal.cjs` 无只读入口，会启动新的付费 live；本轮未执行，不能写作原 live 全流程通过。新增只读 runner 复用原几何函数与阶段事实，保留 `contract_local=passed / interface_live=not_run / task_live=not_run`。未新增网关真跑、Hub 发布、Python 全仓/CI 或物理/人工见证。Node 桥仍依赖本地 npm 安装；已构建前端无需启动 Node 开发服务器。

## Kimi Stack 前端重塑与 7527 交接（2026-09-22）

Kimi F 分支 `morph-frontend-stack` / `29c5e3de79da0d7bf27f4fb0847e2902b590730e` 完成产品实现与返修；独立 I 分支 `morph-frontend-stack-integration` / `4f9fb0b6476a97ff80a30f6a782f3ce9e4723463` 普通合并并验收，均已推送并核对远端。主线以 fast-forward 接收。复用 Hugo Theme Stack v4.0.3 / `3e123a30b79b5d52a3a8e88a9dd678fcfd28e418`，GPL-3.0-only、Tabler Icons / hamburgers MIT 文本及来源随源码和 wheel 分发；参考站精确部署版本未知，未迁入其个人内容。

| 验证 | 结果 |
|---|---|
| `PY -m pytest tests/t5 -q` | 11 passed |
| `node --test tests/integration/test_browser_options.cjs tests/integration/test_observer_control.cjs tests/integration/test_operator_enter.cjs` | 31 passed |
| `check_stack_layout.cjs` / `check_stack_behavior.cjs` | 1366×768、1920×1080、390×844 明暗、导航、键盘、主题持久化、轮询、503/空态复原、拓扑边界通过；0 JS pageerror、0 外部请求 |
| `check_rehearsal_stages.cjs` | 明确 mock 的 19 阶段 × 双桌面，38 帧通过，桌面 Gene 台账首屏约束保留 |
| `PY -m build` / `tools/check_distribution.py --site-dir ... --check-node` | sdist/wheel、11 个安装包、资源、独立验证器和 Node 桥通过；CSS 与许可证入包字节一致 |
| 第五轮原证据只读审计 | 29 个文件的 SHA-256、大小、纳秒 mtime 与文件集合不变 |

完整命令、环境变量和截图路径见 [I 集成报告](tracks/frontend-stack-integration.md)，实现说明见 [F 报告](tracks/frontend-stack.md)。协调者核验 7527 原为空闲后，以已验收 I 源码启动 `python -u -m viz.server --port 7527 --rehearsal C:/Users/DW/AppData/Local/Temp/morph-rehearsal-40f04885b37e489fa3ea1a04f61a984d/rehearsal.json --replay`。HTTP API 返回 replay 和 `passed / not_run / not_run`，已在 Orca 打开本机入口；不承诺跨宿主退出常驻。

协调者对实际 7527 入口追加 `check_rehearsal_layout.cjs` 双桌面检查并亲看 1366 截图：3 节点 / 3 标签，无裁切、相交或溢出；产物在 I worktree 的 `.runtime/stack-handoff-final-ready/`。初次调用漏设脚本要求的 `MORPH_PLAYWRIGHT`，在页面检查前报 `ERR_INVALID_ARG_TYPE`；补齐既有 Playwright / Chromium 路径后检查通过，没有修改产品代码。

本轮为 contract_local、明确 mock 与只读 replay，没有新增 task_live、付费网关彩排或 Hub 发布。未重跑 Python 全仓测试或 CI，未新增其它平台字体验收；Node 桥安装验证依赖本地 npm 依赖，wheel 不包含 node_modules。物理投影按用户要求不再是本机单屏的前置条件。

## EvoMap 首次绑定与免费 Gene 实取审查（2026-09-22）

用户明确首次注册并完成网页绑定后，单次 authenticated heartbeat 返回 HTTP 200、claimed=true、owner 存在；首次 Agent，Free / Lv0 / 0 credits。按用户对具体资产的确认，于服务端响应时间 **2026-09-22 19:09:17 +08:00** 通过官方直接 A2A 路径执行一次 `POST https://evomap.ai/a2a/fetch`，payload 仅含批准的 asset_ids，没有自动重试。返回 HTTP 200、mode=targeted、count=1、credits_deducted=0。这是**真实 Hub 定向获取**证据，区别于上一节插件 stub 测试；并非通过 Evolver Proxy，也不代表项目 HubClient 已完成生产接入。

批准且实际返回的 Gene 为 `gene_gep_repair_from_errors`，完整 ID：`sha256:c9ed1efef4529b9d43ac5738c27bb76735decf483aad5ddcabb974f53a252ae2`。官方 [onboarding](https://evomap.ai/onboarding.md) 对两条免费资产的简短说明与 [实时 policy](https://evomap.ai/a2a/policy) 的条目名称存在差异；本次依据实时 policy 核对并选择上述 repair Gene。服务端同时附带同 bundle 的 Capsule，未额外发送获取它的请求。

| 审查项 | 结果 |
|---|---|
| 指定 Gene 身份 | 请求 ID、结果 ID、Gene 正文 ID 一致；正文标记 schema_version=1.5.0 |
| Gene 完整性 | 复用现有 `NodeAssetBridge.validate_asset`、官方 `@evomap/gep-sdk` 1.14.0；schema_valid=true、asset_id_valid=true、valid=true；官方重算 ID 与批准 ID 完全相同。未把正文版本改写为 1.14.0 |
| 可复用内容 | 六步策略：从错误中提取信号、匹配既有经验、评估改动范围、最小可逆修复、按声明检查并在失败时回退、记录经验结果。属于流程策略，未提供 clamp/mean/unique 的具体实现 |
| Gene 验证强度 | 声明的命令只检查 Node crypto 模块可加载；不能证明任何项目 bug 被修复。该命令未执行，项目固定独立 checkpoint 保留 |
| 附带 Capsule | ID `sha256:7e4120afb308075ded85b67eecf5c06bc870d4fce70d3d24139e91577612e462`；schema_valid=false，根 additionalProperties 与 /content type 不满足本项目锁定 SDK；asset_id_valid=false。官方重算原始正文为 `sha256:8813bfcc9fb1d7e78c5c9a783383414db615c2555cd7fadfee32e002701fec62`，与返回 ID 不同，不能直接准入；尚未确定差异来自服务端增补还是其他原因 |
| Capsule 的验证声明 | 三条 execution_trace 的命令检查内嵌文本/关键词，不能作为 Morphogenesis 代码修复证据。外层 verification.attested=false、runtime_gate/capsule_proof/validation_path 均 null；未执行返回命令 |
| 项目现有准入门 | `validate_bundle([fetched_gene, fetched_capsule], NodeAssetBridge())` 实际拒绝，错误 `official_asset_validation_failed`；没有移除字段、重算覆盖原 ID 或降低门禁让它通过 |
| 运行采用与发布 | 尚未导入项目 Gene 池、注入新任务或形成 UseRecord，没有新增模型请求或 Hub 发布；完整任务采用仍 NOT_RUN |

上述校验在 I 锁定环境的现有 Python 会话中直接对内存响应调用，复用 `bridge_node.assets.NodeAssetBridge` 和 `hub_client.assets.validate_bundle`，没有自写哈希或执行资产内命令。原始响应保留在临时会话内，本报告只保存审查结果；节点 secret 不进入本报告、Git 或工具输出，尚未持久保存，也未启动 heartbeat 循环。

结论：**免费 repair Gene 的获取、正文 schema 和内容哈希通过，可作为待采用的策略参考；附带 Capsule 不满足当前项目准入要求。** 若后续接入，仍使用项目独立验证器、实际 source_attempt / UseRecord 和本地代谢边界；远端公开资产的成功声明不能替代本地真实任务验收。安装插件先前的 Windows 启动、参数校验与发布重试问题不因本次直接 A2A 获取成功而解除。

## Evolver Codex 插件适配评估（2026-09-22）

**结论：已安装的 `evolver@evomap` 0.2.0 可作为待适配的经验检索辅助入口，当前不满足直接接入或替换 Morphogenesis 核心闭环的要求。** 安装与启用已由 `codex plugin list --marketplace evomap --json` 确认；本会话没有加载 `evolver_*` 工具。官方来源为 `https://github.com/EvoMap/evolver-codex-plugin`，市场 checkout `cbff9210f17f35650a223d65744d1ff44e1dd112`，安装缓存 `C:/Users/DW/.codex/plugins/cache/evomap/evolver/0.2.0`，插件清单声明 GPL-3.0-or-later；MCP 握手自身版本为 0.1.0，不能与插件版本混用。

评估复用项目锁定环境中的官方 Python MCP `ClientSession` / `stdio_client` 和既有 `child_environment`，没有改插件缓存或业务源码。测试使用独立临时 HOME、随机 loopback 端口、合成凭据与合成资产；不使用真实网关密钥、不连接或发布到真实 Hub。17 个项目适配检查为 **13 通过、4 不满足**，不是插件上游测试套件，也不是 13 项远端能力通过。程序 exit 0 仅说明检查全部完成，4 项不满足仍按失败记录。

| 项目需求 / 检查 | 结果与证据边界 |
|---|---|
| Windows 默认可启动 | **不满足**：安装包 `.mcp.json:4` 写死 `/opt/homebrew/opt/node@22/bin/node`，按该 command 启动得到 `FileNotFoundError / WinError 2`。安装 enabled 不代表宿主已成功加载 |
| 标准 MCP 互通 | **本地通过**：仅在测试客户端显式使用本机 `node` 和插件绝对入口后，初始化与 9 工具发现通过；未修改真实宿主配置，也未证明新 Codex 会话加载成功 |
| Recipe / Gene 检索、正文获取、结果轮询 | **隔离 stub 转发通过**：status、recipe_search、recipe_express、search_assets、fetch_asset、poll 的路径、参数及 Bearer 转发一致；未验证真实 Hub 检索命中或任务采用 |
| 本地提炼与禁止发布参数 | **隔离 stub 转发通过**：distill 显式 `persist=false, publish=false` 正确传递；没有实际写入 Evolver 记忆图。工具 schema 的 publish 默认值为 true，接入时须显式受项目发布门控制 |
| 直接替换既有 GEP 桥 | **不满足**：列出的 9 个 `evolver_*` 工具不包含项目使用的全部 8 个 `gep_*` 接口，包括 install_gene、record_outcome、recall、evolve、export；现有适配还校验 server name/version，不能只改启动路径替换 |
| 必填参数校验 | **不满足**：`evolver_search_assets` schema 要求 signals，但直接 MCP 调用 `{}` 仍转发 `{mode: semantic, limit: 5}` 并接受 stub 成功结果。证明桥端不校验该必填参数，不代表所有宿主/Proxy 都不校验 |
| 未知发布效果不重试 | **默认不满足**：合成 `/asset/submit` 收到首 POST 后断开响应连接，status 仍健康；单次 `evolver_publish_asset` 触发 **2 POST** 并返回成功。桥的 `proxyFetch` 自动恢复分支不区分读写；这是重复提交风险，未声称真实 Hub 已产生重复资产 |
| 关闭自动启动后的错误行为 | **隔离测试通过**：`EVOMAP_MCP_PROXY_AUTOSTART=0` 时同样断连仅 1 POST 且返回错误；401 也仅 1 请求且 isError。该环境设置只是本地可行缓解，生产端到端未验收 |
| 经验采用、衰减、归档一致性 | **未由插件提供/未验证**：9 工具中没有项目 mark_used、时间衰减、归档及索引清除接口；应继续由现有 metabolism 负责。不得把 Recipe 展开或检索命中计为 source_attempt / UseRecord 采用证据 |
| 独立 checkpoint、成员重路由、模型执行 | **不属于该插件已暴露能力**：插件提供经验工作流与 Proxy 桥；当前网关 Executor、LangGraph、独立验收和拓扑机制保留 |

本机运行前置实查：Node 24.16.0、Git 2.47.0.windows.1；PowerShell 未找到 `evolver` 命令，19820 无 listener，用户 `.evolver/settings.json` 和 claim 链接均不存在。插件状态脚本 exit 0，但调用 `sh` 检测 CLI 得到 `spawnSync sh ENOENT`，其“local memory works”文字不是记忆读写实测；不能据此把本地记忆或网络连接记通过。CLI/Proxy 启动、Codex 新会话工具加载、真实 Recipe/Gene 检索和真实任务采用均 **NOT_RUN**；Hub 沙箱前置仍缺失。

本地可复查证据根为 `C:/Users/DW/AppData/Local/Temp/morph-evolver-eval-258cf817c31a47cba766a76c9e648d89/`：`probe.py` 是本轮一次性验收脚本，`report.json` 含 17 项结果、工具 schema 和 loopback 收件记录，另保留 status-helper 与 MCP stderr。测试进程和 stub 正常关闭，插件缓存未改；这些运行产物不提交 Git。

```powershell
# cwd: C:/Users/DW/orca/workspaces/Morphogenesis/morph-onsite-integration
.venv/Scripts/python.exe -B C:/Users/DW/AppData/Local/Temp/morph-evolver-eval-258cf817c31a47cba766a76c9e648d89/probe.py
# 项目原有官方 GEP MCP 路径对照复验：1 passed / 4.59s
.venv/Scripts/python.exe -B -m pytest -q tests/t1/bridge/test_mcp.py::test_official_mcp_handshake_list_call_export_and_isolation --basetemp C:/Users/DW/AppData/Local/Temp/morph-evolver-eval-258cf817c31a47cba766a76c9e648d89/baseline-pytest
```

对照测试真实启动项目锁定 `@evomap/gep-mcp-server` 1.7.0，完成合成 Gene 安装→选择→结果记录→召回→导出、重开持久化和不同工作区隔离；**1 passed**，属于本地官方组件接口证据，不是新模型任务。后续最小接入应先处理 Windows 启动、桥端参数边界及写请求不重试，再用独立 Proxy 验证只读经验检索；不为插件另造编排器，不安装全局 hooks/AGENTS 指令、不运行持续进化循环、不改本轮演示主链。远端发布仍由项目 HubClient 的批准边界控制。

## 7527 本机单屏：第五轮真实网关彩排（2026-09-22）

用户最新指令为本机单屏、无需外接投影、立即真跑，替代下文历史现场接线前置。运行分支 `songconmaisaix31-design/morph-onsite-integration`，干净 HEAD `bcd81beac5b9f73ac9f8267ccbc3f571e4faf738`。仅执行一次，EvoMap / `evomap-gpt-5.6-luna`，无重试。观察器北京时间 17:48:35–17:50:15；真实快照 17:48:48–17:50:14。summary: demo exitCode=0、failure=null、entered=true。

| 检查 | 实际结果 |
|---|---|
| 固定外置 checkpoint | 两份新坏样例，各 clamp / mean / unique 从 0/3 到 3/3；四份独立验证报告一致 |
| 网关请求 | repair / recovery 各 1 POST、HTTP 200；544+367=911、883+343=1226，共 **2,137 tokens**；费用未知/null |
| 下线与后续任务 | 首任务 builder#0；真实等待门后移除；新任务 builder#1 成功，旧管道 inactive；没有强杀在途进程 |
| Enter 证据 | `--operator-enter` 在真实 TTY 启动，两视口与原文件 stage=awaiting_offline / sequence=5 后 armed；17:49:33.303 收到协调者工具输入，.304 forwarded。字段 source=operator 是代码模式名，不代表用户亲手按键 |
| Gene 池 | 两条 Gene，前次完整正文注入后次请求并实际采用一次；τ=10 秒，21 个真实墙钟权重采样通过，低于 0.2 后归档，resolve 为空、数据库缓存正文 0 |
| 浏览器记录 | 1366×768 / 1920×1080 各全部 20 幕，40 张阶段截图 + 2 张等待截图；页面错误 0，图形几何门禁通过；已实看采用阶段和最终截图 |
| 只读审计 | exit 0；原运行根 29 文件 bytes/mtime 在审计前后不变；31 份新运行/浏览器文本无凭据样式命中 |
| 页面交接 | 7527 HTTP 200 / provenance=live / stage=completed / task_live=passed / calls=2；保留本轮完成状态，没有新模型调用。7526 旧回放仍监听且未操作 |

命令在 I worktree `C:/Users/DW/orca/workspaces/Morphogenesis/morph-onsite-integration` 的锁定环境运行，凭据仅由专用进程环境传递，未写入文件或命令参数：

```powershell
node tests/integration/observe_rehearsal.cjs manual 7527 .runtime/integration/live-5-single-screen-20260922-01 --executor evomap --model evomap-gpt-5.6-luna --operator-enter --operator-timeout-seconds 120
.venv/Scripts/python.exe -B tests/integration/audit_rehearsal.py C:/Users/DW/AppData/Local/Temp/morph-rehearsal-40f04885b37e489fa3ea1a04f61a984d
```

原运行根：`C:/Users/DW/AppData/Local/Temp/morph-rehearsal-40f04885b37e489fa3ea1a04f61a984d`。观察器 summary、manual-enter、audit、日志、逐幕浏览器 JSON 和 PNG 位于 I worktree `.runtime/integration/live-5-single-screen-20260922-01/`，本地产物不入 Git。本轮没有业务源码修改，不重复模型请求或不相关测试。

验收时 viewer launcher 58304 → listener 25412，均为该 I worktree 的 `viz.server --port 7527 --rehearsal <本轮根>/rehearsal.json`；demo 子进程 60092 已退出，viewer 持有输出管道导致观察器父终端仍存活，未宣称整体终端 exit 0。保留服务供用户访问，不承诺跨宿主退出常驻，清理前需重新核验身份。自动审批拒绝 `Start-Process` 打开桌面浏览器，理由 `blocked by policy`；没有绕过，用户可直接打开 http://127.0.0.1:7527/ 。桌面人工观看/全屏未见证；外接投影按用户指令不执行。Hub 待发布、OpenCode 工具调用/流式未验收、动态供给及在途强杀恢复不在本轮范围。

## 现场准备并行收尾（2026-09-22）

从已验收的第四轮网关主链出发，V `1b2e335` 提交可照做的 [投影/7526 回放/7527 真跑清单](tracks/onsite-viz.md)；O `26a5cf1` 给现有观察器增加显式 `--operator-enter`，只有两视口与真实新根均处于 `awaiting_offline`，才等待现场人员一次 Enter，并留时间证据，默认自动行为不变。集成首次完整 Python 测试发现旧 fixture 固定占用 7526，结果 **199 passed / 1 failed**；原 O 会话 `3d05f4e` 将该本地测试改用独立动态端口，原失败项复验 **1 passed / 29.44s**。I 普通合并并推送 `bcd81beac5b9f73ac9f8267ccbc3f571e4faf738`，主线 fast-forward 接收；最终 SHA 的完整 200 项未重新执行，不能记为“200 passed”。

集成额外通过：`node --test tests/integration/test_browser_options.cjs tests/integration/test_operator_enter.cjs tests/integration/test_observer_control.cjs` **31 passed**；`python tools/typecheck.py` **53 文件 clean**；sdist/wheel、SDK、本地安装后 11 包检查通过。7526 回放 API 为 HTTP 200 / replay / 两 live 状态 not_run，双视口真实布局检查通过，29 个第四轮原文件 bytes+mtime 不变；7527 当时无监听。完整命令、日志和原失败见 [I 报告](tracks/onsite-integration.md)。精确候选 [CI 35709392862](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/35709392862) 已完成，Ubuntu / Windows 两 job 均 success；这属于远端精确 SHA 门禁，仍与本地首次 199/1、返修定向 1 passed 分列。

**历史现场安排已被替代：** 原计划借线实接、7526 投影全屏和 7527 新真跑；用户现明确本机单屏、无需投影，故取消接线确认前置，并完成上节第五轮。截图不等于物理投影或用户桌面全屏见证。今晚演示执行器为 EvoMap 网关；OpenCode 是备选开发路径，工具调用/流式今晚不测。Hub 保持本地 stub / 待发布；不验证在途进程强杀恢复，路演仅说“成员下线后，后续任务自动重新选路”。

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
