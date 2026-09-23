# D 轨：封板夜 G5 软件链路

## 领域恢复与软件核验（2026-09-23 19:34–19:45 CST）

主控消息 `msg_3b877f1a471c` 明确两前置通过并恢复 D 开发，已消费 ACK；本节取代下文只读阻塞结论，历史记录保留。仍使用同工作区 `codex/morphogenesis-mainline`，未切分支；E 的报告和 Hub 代码改动完整保留，未暂存。当前进程网关 key 只检查存在性，结果 false；没有读取 Hub node_secret 充作模型 key。

### 实现及边界

- Compose 配置测试兼容序列化省略 false 的 `bind.create_host_path`，同时保留源 YAML 显式 `create_host_path: false` 的约束；没有允许自动创建宿主源目录。
- `viz.server` 支持 `MORPH_BIND_IP`，缺省 loopback，显式 `--host` 优先。Python 也只允许 GET/HEAD、拒绝请求体/Transfer-Encoding、目录/点文件/非白名单文件/符号链接；日志省略 query/header，返回 nosniff/frame/referrer 头。静态白名单沿用 nginx。公网仍通过 nginx 限流/超时，Python 不替代其流量边界。
- 审计未发现任务启动、文件写入、模型调用等写路由；三条 API 均只读，没有添加无依据的 token 或控制面。nginx 继续剥离 Authorization/Cookie、禁止上游重试，不暴露 API 容器端口。
- `validate_dashboard_snapshot` 复用 `Acceptance`、`RehearsalDocument`、`TaskResult`，检查来源/当前结果/验收一致及 passed 所需结果证据；`load_rehearsal`、smoke、healthcheck 共用它。合法历史 live 的 passed 原样传播，mock/replay 的 live 维度保持 not_run，空态三维 not_run；没有改默认值。探针只是契约一致性，不证明新任务或远端文件存在。
- smoke 使用项目锁定 Python，`--direct` 明确跳过仅 nginx 提供的限流检查。已兼容最终 UI 的 `data:,` 空 favicon，仅该固定 icon 免取网络资源，其它有 scheme/外域资源拒绝。API 镜像包含 smoke，可在容器锁环境核验同源 nginx。

### 命令与证据

本轮本地原件仍为下文第四轮 `rehearsal.json`；没有新网关调用，请求模型/usage 只作历史核对。全部运行产物位于忽略目录 `.runtime/freeze-demo/`。

| 命令 / 核验 | 结果 / 证据 |
| --- | --- |
| `orca skills get orca-cli`、`orca skills get orchestration`、`orca skills get orca-cli --reference references/browser.md` | 读取当前 CLI 指南；浏览器由主控允许使用独立 Chromium，避免操作账户窗口 |
| `netstat -ano -p tcp` + 指定 PID 的 `Get-CimInstance Win32_Process` | 开始仅 7844 listener 44240 / parent 41400，命令仍为历史 worktree 的 replay；未停止或重启 |
| `.venv/Scripts/python.exe -m pytest tests/deployment tests/t5 -q` | 最终 **85 passed / 16.34s**；`pytest-final.txt`。首次 83 passed / 1 failed 为新测试尝试修改 frozen fixture，已改为重新 model_validate；没有变更共享模型 |
| `.venv/Scripts/python.exe tools/typecheck.py` | **55 source files / 0 errors**；`typecheck-first.txt` |
| `Start-Process .venv/Scripts/python.exe -ArgumentList '-u -m viz.server --host 127.0.0.1 --port <7799或7526> --rehearsal <第四轮原件> --replay' -WindowStyle Hidden ...` | 19:41:15 启动；7799 launcher 55676，7526 launcher 13016；`viewer-<port>.json/out.log/err.log`。凭据存在性 false，viewer 不继承任何已知网关秘密；7527 未启动替代品 |
| `.venv/Scripts/python.exe deploy/smoke.py http://127.0.0.1:7799 --with-fonts --direct`；7526 同命令 | 均 exit 0；`smoke-local-7799.json`、`smoke-replay-7526.json`，provenance=replay / passed,not_run,not_run。首次因最终 UI favicon data URI 不属 HTTP 而失败，已补有界解析和回归测试 |
| `node .runtime/freeze-demo/browser.cjs http://127.0.0.1:7799 .runtime/freeze-demo/browser-local-7799-v2` | exit 0；1366×768、1920×1080、375×812 各 5 视图＋验收详情实图；零 pageerror、零实际 HTTP 失败、无横向溢出、字体已加载，三态等于真实 API |
| 上述浏览器命令改为 7526 / `browser-replay-7526` | exit 0；同样 15 视图，真实 replay API。浏览器自动只读 GET 已按协调消息 `msg_64efbecf0954` route abort，每个服务一次；没有 fulfill 假回执，没有 Hub 请求，EvoMap 错误态/未验收单列 |
| 实际查看 `1366-task.png`、`1920-topology.png`、`375-acceptance.png` | 桌面任务/拓扑与手机验收弹层可读；回放和 not_run 明确。属于本机浏览器证据，不是手机或投影实测。初版等待条件误写为 replay 而非“来源：replay”，超时保留于 `browser-local-7799.log`，修正 helper 后通过 |
| `.venv/Scripts/python.exe -B -` 只读调用原件 `load_rehearsal` / `validate_dashboard_snapshot` | `historical-contract-check.json`：live 三态 passed；replay 为 passed/not_run/not_run；原件 bytes/mtime 不变；历史请求模型 evomap-gpt-5.6-luna，calls=2，tokens=887+1348，费用 null；新调用 0 |
| `ssh -o BatchMode=yes -o ConnectTimeout=10 gongzhi-ecs` 执行 `uname -n` / `docker ps` / `ss -ltnp` / `ls -ld` / `docker image ls` / `df -h /opt` | 服务器身份吻合，共治四容器 healthy，7799 空闲，项目目录尚不存在，9.7G 可用；`remote-preflight.txt`。未创建远端目录或改变容器 |
| `docker version --format '{{.Server.Version}}'` | 本机 Docker daemon 仍不存在 npipe，未启动 Docker Desktop或修改全局配置 |

### 本阶段剩余项

尚未 commit/push、远端构建或公网部署；待主控串行提交时段及外部写命令协调。7527 新 live 缺模型网关凭据，未发 Enter、未请求模型、未重试。EvoMap 正常公开只读入口待 E 写链结束后串行核验。热点、第二设备和物理投影未执行；不将本机监听、截图或历史 passed 当公网/新 live/现场通过。

### 19:45–19:49 提交及一次远端部署尝试

主控授予独占 Git 时段后，只暂存 10 个 D 文件，`git diff --cached --name-only` 和 `git diff --cached --check` 通过。实现提交 **`25968dc8440a25f2472df8cfb7ff62eb3302366d`**，`git push origin codex/morphogenesis-mainline` 成功，`git ls-remote origin refs/heads/codex/morphogenesis-mainline` 同 SHA；随即释放 Git 时段。E 和主控的未提交文件未触碰。

主控另经 `orchestration ask` 放行以下确切版本的远端写入，要求 loopback 先验收、镜像构建总 deadline 600 秒、不自动重试。部署只用标准白名单包，不读并行工作区：

```powershell
.venv/Scripts/python.exe deploy/package.py 25968dc8440a25f2472df8cfb7ff62eb3302366d .runtime/freeze-demo/morphogenesis-25968dc8440a25f2472df8cfb7ff62eb3302366d.tar.gz
scp -o BatchMode=yes -o ConnectTimeout=10 .runtime/freeze-demo/morphogenesis-25968dc8440a25f2472df8cfb7ff62eb3302366d.tar.gz gongzhi-ecs:/tmp/morphogenesis-25968dc8440a25f2472df8cfb7ff62eb3302366d.tar.gz
scp -o BatchMode=yes -o ConnectTimeout=10 C:/Users/DW/AppData/Local/Temp/morph-live4-98b36399c0324192b5af81f8077bc11d/morph-rehearsal-86e5351d49fe49a1b60ba0a4bb4c4e4e/rehearsal.json gongzhi-ecs:/tmp/morphogenesis-rehearsal-25968dc8440a25f2472df8cfb7ff62eb3302366d.json
Get-Content -Raw .runtime/freeze-demo/remote-install.sh | ssh -o BatchMode=yes -o ConnectTimeout=10 gongzhi-ecs 'bash -s'
```

包为 **89 个已提交白名单普通文件 / 109 项含目录条目**，`archive-members.txt` 保存清单；审计绝对路径、`..`、symlink、点文件及每个文件 `deploy.package.allowed`，均通过。首次辅助检查误将 tar 根目录名要求带尾斜线而触发 assertion，只进行了传包，未据此解包；更正标准根目录判定且完成完整白名单检查后才执行远端脚本。没有改写、绕过打包白名单。

远端脚本先确认 release/data 文件和 Compose project 不存在、7799 无监听，再仅创建 `/opt/morphogenesis/releases/25968dc8440a25f2472df8cfb7ff62eb3302366d` 与 `/opt/morphogenesis/data`，解包版本并安装单个 `rehearsal.json`。原件、本机传输前、远端 `/tmp`、最终 data 文件的标准 SHA256 均为 **`f3639cd4e96edbe04cea63d4522df12cf16d84817bb84650a19885268b61c818`**，未传运行根/数据库/账户配置/密钥。

远端命令的环境固定为 `MORPH_RELEASE=25968dc...`、`MORPH_BIND_IP=127.0.0.1`、`MORPH_REPLAY_FILE=/opt/morphogenesis/data/rehearsal.json`，Compose 固定 `--env-file /dev/null -p morphogenesis -f deploy/compose.yaml -f deploy/compose.replay.yaml`。`config --quiet` 通过；唯一 `timeout 600 docker compose ... build` 返回 **exit 1**，三个固定基础镜像都在 metadata HEAD 阶段失败：

```text
failed to do request: Head https://registry-1.docker.io/v2/library/<python|node|nginx>/manifests/sha256:<Dockerfile固定digest>
dial tcp 103.200.31.172:443: i/o timeout
target web: failed to solve: DeadlineExceeded ... failed to resolve source metadata
```

完整原错误保留 `remote-install.log`，未重试、未改镜像源、未启动本机 Docker Desktop、未操作全局 daemon。脚本 `set -eu` 在构建失败处停止，**没有执行 up、远端 smoke/healthcheck 或 0.0.0.0 公开步骤，未新增安全组规则**。归档、远端版本/data 和失败日志保留可复核，没有自动删除。

失败后 `docker ps`、`docker ps -aq --filter label=com.docker.compose.project=morphogenesis`、`ss -ltnp` 复核：本项目无容器、远端 7799 无监听，共治四容器仍 healthy，80/443/8080 保持原映射。证据 `remote-after-failed-build.txt`；`.runtime/freeze-demo/listener-identities.json` 记录本机 7799 listener 55020/parent 55676、7526 listener 53392/parent 13016，7844 listener 44240/parent 41400 仍不变。公网仍 **blocked / not_run**，不是部署 passed。

已向主控发送 `msg_ebae5db384b7` 升级：可由主控协调已有构建环境与同 SHA 镜像转运路径；本机 daemon 当前不可用，不自行通过全局改动绕过。7527 新 live、EvoMap 正常公开只读核验、热点/第二设备/物理项仍保留前述限制，本轮模型新增调用/usage 为 0 / 无新增记录，未知费用仍 null。

### 19:53–19:55 WLAN 与既有产物核查

主控要求不重试远端，先只读查已有构建/转运物并完成特定 WLAN 绑定。`Get-CimInstance Win32_NetworkAdapterConfiguration -Filter 'IPEnabled=true'` 返回 MediaTek Wi-Fi 7 MT7925 无线网卡 IPv4 **192.168.60.54**、网关 192.168.60.1；另一个 Meta Tunnel 的 198.18.0.1 未选。先通过 `msg_3ebdca9d9503` 明确地址/端口，随后以仅当前子进程环境 `MORPH_BIND_IP=192.168.60.54`、清除 `MORPH_EVOMAP_API_KEY`，`Start-Process -WindowStyle Hidden` 启动原命令但不传 `--host`，验证环境绑定实际生效。

- 地址 `http://192.168.60.54:7799/`；launcher **56004**、listener **51992**。`netstat` 与 CIM 复核准确监听和父子命令；原 127.0.0.1:7799、7526、7844 均保持，7527 仍无替代服务。没有系统网络/防火墙/代理配置修改。
- `.venv/Scripts/python.exe deploy/smoke.py http://192.168.60.54:7799 --with-fonts --direct`：exit 0，`smoke-wlan-7799.json`；`curl.exe --noproxy '*' --max-time 10 --silent --show-error --head http://192.168.60.54:7799/api/dashboard`：200 与 nosniff/frame/referrer/no-store 头。
- `node .runtime/freeze-demo/browser.cjs http://192.168.60.54:7799 .runtime/freeze-demo/browser-wlan-7799`：exit 0，三视口 15 视图及验收弹层，零 pageerror/实际 HTTP 失败、真实 replay API 和三态匹配。仍按主控要求 abort 一次自动 `/api/evomap`，该模块未验收；实际查看 WLAN 375-task 与 7526 1366-topology 截图。**这只证明本机访问真实 WLAN 地址，不是第二设备、异网或公网可达证明**。
- 已读 `docs/tracks/beijing-deployment.md` 和 integration 报告，并仅列其指向的 `%TEMP%/morph-beijing*`、原 `morph-beijing-deploy` 根 tar 与 `.runtime`。找到 `morph-beijing-d-package-check/da393da87036637387bb398689c1b5677c9f5b86/` 源码解包及 smoke 记录；没有已记录的 save/OCI 转运文件或当前 `25968dc` 成品镜像路径。历史报告曾保留 Docker daemon 内旧 Linux 镜像/缓存，但 daemon 当前不可用，不能声称它们仍在或冒充最终 SHA。

已发 `msg_a06a99a14f5f` 回传以上结果。后续需可用的同版本构建/镜像转运环境；本轮没有配置全局 Docker、启动 Desktop 或重试远端失败构建。新网关 key、正常公开 Hub 面板一次读取窗口、热点/第二设备/现场条件仍由主控协调。

## 当前状态（2026-09-23 18:32，北京时间）

**只读核查完成，领域实现、live 演示与部署尚未开始。** 工作区为 `C:/Users/DW/orca/Morphogenesis`，分支 `codex/morphogenesis-mainline`；核查时 HEAD 为 `2b58b5923286af8e11e556a1579e239bceee539b`，开始时 `git status --short`、`git diff` 均为空。本报告不把历史结果计作本轮验收。

18:31:38 主控通知：E 的唯一 Hub hello 被 `rejected / CAPTCHA / 3600000ms` 拒绝，禁止新身份、重试或绕过；用户尚未决定是否调整前置规则。主控仅放行自有 track 报告，D 保持门禁等待，不修改领域代码、不启动 live 或部署、不发送终结回执。此项为主控转交结果，D 未自行调用 Hub。

独占路径遵循本轮 PLAN：`deploy/**`、`viz/adapter.py`、`viz/server.py`、`tests/deployment/**`、`tests/t5/test_adapter.py`、本报告、`.runtime/freeze-demo/**`。不开分支，不 stash/reset/checkout，不改前端、锁、contracts 或 orchestration；串行提交需先向主控申请。

## 只读发现

1. Nginx 已限制 GET/HEAD、精确 API 和静态白名单、禁止目录列表及请求体，剥离上游 Authorization/Cookie，限制连接与请求速率；只有 `/api/dashboard`、`/api/evomap`、`/api/evomap/asset` 三个只读 API。未找到任务启动、文件写入、模型调用或其他写路由，因此没有添加 token 的具体写接口依据。
2. Python `DashboardHandler` 只定义 GET/HEAD，但静态请求仍交给默认 `SimpleHTTPRequestHandler`，缺少与 nginx 一致的路径白名单/目录拒绝/请求体拒绝；未实现写方法也不等于完整外网边界。`--host` 当前默认 127.0.0.1，不读取 `MORPH_BIND_IP`；Compose 已支持该环境绑定且默认 loopback。
3. `deploy/smoke.py`、`deploy/healthcheck.py` 把两项 live 断言固定为 `not_run`，会错误拒绝有证据的真实 live 快照。`load_rehearsal` 已直接读取上游 `RehearsalDocument` 并传播 acceptance；`load_runtime_export` 也直接传播 `TaskResult`。本轮只读调用证实历史 live 与显式 replay 的三态正确，不能靠修改默认值制造通过。
4. 当前进程 `MORPH_EVOMAP_API_KEY` 存在性为 false；仅检查布尔值，没有搜索历史聊天、全局配置或其他目录，没有查看或输出任何凭据。已通知主控安全协调，7527 新 live 不可启动。
5. 本机 Docker CLI 可用，但 Docker daemon 不可用，错误为 `failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine; ... The system cannot find the file specified.` 未启动 Docker Desktop、修改镜像源或全局配置。
6. 初查本工作区 `.venv/Scripts/python.exe`、`node_modules/echarts/dist/echarts.min.js` 均不存在；18:29:31 主控转交 T 已完成锁安装。D 随后用本地 `.venv/Scripts/python.exe -B` 成功只读导入现有 adapter，无依赖/锁文件修改。

## 命令、时间与返回

所有时间为北京时间；命令完整输出留在本次 Orca worker 终端，本报告记录有意义返回和边界。未建立运行证据目录、未复制历史原件。

| 时间 | 命令/读取 | 返回 |
| --- | --- | --- |
| 18:26–18:28 | `git status --short`、`git diff`、`git diff --stat`、`git branch --show-current`、`git rev-parse HEAD` | 工作区 clean；主线；上述完整 SHA |
| 18:26–18:28 | `Get-Content AGENTS.md`、`docs/source/README_包内说明.md`、`docs/PLAN.md` 顶部、`docs/ACCEPTANCE.md`；按相关章节读统一对齐文档；读 deploy、viz、共享结果/彩排契约及适用测试 | 核对事实源、权限与三态；未修改 |
| 18:26–18:28 | `orca skills get orca-cli`、`orca skills get orca-cli --reference references/browser.md`、`orca status --json`；读已安装 `vercel:agent-browser` 技能 | Orca 1.4.199 running/ready；浏览器指南已读，未把 API 请求当截图验收 |
| 18:26:52 | `[bool]$env:MORPH_EVOMAP_API_KEY`、`[bool]$env:MORPH_BIND_IP` | 均 false；未输出环境值 |
| 18:27 | `Get-NetTCPConnection -State Listen`，仅筛选 7799/7526/7527/19820/7844；对监听进程和父进程 `Get-CimInstance Win32_Process` | 仅 7844，身份见下节；未停止进程 |
| 18:27 | `Get-NetIPAddress -AddressFamily IPv4`（排除 169.254.*） | WLAN 192.168.60.54/24；WSL 172.25.144.1/20；Mihomo 198.18.0.1/30；loopback 127.0.0.1/8；未更改网络 |
| 18:27:46 | `docker version --format '{{json .Server}}'`、`docker ps --format '{{.ID}} {{.Names}} {{.Ports}}'` | 服务端 null / daemon pipe 缺失；未创建或修改容器 |
| 18:28 | `Test-Path .venv/Scripts/python.exe`、`Test-Path node_modules/echarts/dist/echarts.min.js` | 初查均 false，已交 T |
| 18:28 | `Test-Path C:/Users/DW/AppData/Roaming/npm/node_modules/@playwright/cli/node_modules/playwright`；`Test-Path C:/Users/DW/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe` | 均 true；未安装或启动浏览器 |
| 18:29:37 | `ssh -o BatchMode=yes -o ConnectTimeout=10 gongzhi-ecs docker image ls` | exit 0；已有共治、Caddy、Node、pgvector、GoTrue 镜像，无 Morphogenesis 所需锁定 Python/Node/nginx 镜像；不拉取、不删除 |
| 18:29:37 | `ssh -o BatchMode=yes -o ConnectTimeout=10 gongzhi-ecs ls -ld /opt/morphogenesis /opt/morphogenesis/releases /opt/morphogenesis/data` | exit 1；三个目录均不存在；没有创建 |
| 18:29:37 | `ssh -o BatchMode=yes -o ConnectTimeout=10 gongzhi-ecs df -h /opt` | exit 0；20G 总量、8.7G 已用、9.7G 可用、48% |
| 18:30:15 | `.venv/Scripts/python.exe -B -`，stdin 仅导入 `viz.adapter.load_rehearsal`，对下述同一原件依次 `replay=False/True`，只输出 provenance/acceptance | exit 0；历史源 live 为 passed/passed/passed；显式 replay 为 passed/not_run/not_run，保留 original_run_uri；无模型调用 |
| 18:31:52 | `git status --short`、`git rev-parse HEAD`、`Test-Path docs/tracks/freeze-demo.md` | clean；HEAD 未变；报告此前不存在 |

### 既有进程与原件

7844 listener PID **44240**，parent **41400**，地址 `127.0.0.1`；两者命令均为 `-m viz.server --host 127.0.0.1 --port 7844 --rehearsal <第四轮原件> --replay`。父进程使用 `C:/Users/DW/orca/workspaces/Morphogenesis/morph-gpt-reference-integration/.venv/Scripts/python.exe`，listener 为 uv Python 3.12。未操作 7844；PID 仅为核查时身份，未来操作需重新确认。

第四轮原件：`C:/Users/DW/AppData/Local/Temp/morph-live4-98b36399c0324192b5af81f8077bc11d/morph-rehearsal-86e5351d49fe49a1b60ba0a4bb4c4e4e/rehearsal.json`。

- 大小 **226518 bytes**，mtime UTC `2026-09-22T08:13:35.4930093Z`，标准 `Get-FileHash -Algorithm SHA256` 为 `f3639cd4e96edbe04cea63d4522df12cf16d84817bb84650a19885268b61c818`；与已记录历史证据一致。
- 原件 mode=`live`、stage=`completed`、model=`evomap-gpt-5.6-luna`、calls=2，两个结果为 succeeded，usage.tokens 为 **887** 与 **1348**，cost_usd 均 **null**。实际返回模型的历史依据在 ACCEPTANCE，此次没有读取网关响应或创建新的模型请求。
- 这是历史证据存在性与 adapter 读取检查，**不是本轮新 live 演示**。未执行历史 observer、audit 或重跑历史任务。

## 门禁解除后的最小实施计划（尚未执行）

1. 在自有路径复用 `Acceptance` / `RehearsalDocument` / `TaskResult` 做探针证据一致性检查：允许合法有证据 live passed，空态、replay、mock 仍不得升级；补适用正反例，不重建契约、不改默认值假绿。
2. Python 入口支持 `MORPH_BIND_IP`，保留 CLI 显式覆盖和 loopback 默认；参照 nginx 收紧 GET/HEAD、静态白名单、目录/请求体拒绝，测试真实 HTTP 的 GET/HEAD 和拒绝行为。不新建写路由或 token 设施。
3. 主控已将本轮唯一部署执行所有权交给 D，覆盖旧部署文档的主控/I 执行约定。严格顺序：E 门通过或用户明确调整 → D 实现/适用验证 → 申请独占提交时段 → 仅暂存自有路径 commit+push → 标准白名单归档 → `/opt/morphogenesis` 独立项目、7799 → 真实公网 HTTP/浏览器。共治 80/443 及其配置、容器、数据不变。
4. 本机核验后按角色启动 7799、7526 明确 replay、7527 新网关 live；所有后台 `Start-Process -WindowStyle Hidden`，启动前复核 PID/父进程/命令。页面/API/console 全部 awaiting_offline 后只发一次 Enter。
5. 网关仅必要一轮最多 2 调用，每调用 `max_tokens=20000 / max_cost_usd=1`，无未知结果重试；具体命令、参数、目标根先交主控协调，避免与 E 重复花费。当前无凭据，不执行此项；凭据只在执行子进程内存环境，不进入 viewer/browser、argv 或日志。历史文档已明确实际网关输出上限另取 min(max_tokens,4096)，美元费用未知不能称硬封顶已证实。

## 尚未执行与真实限制

本轮源码修复、pytest/类型检查/构建、服务启动、浏览器截图与布局/console 验收、网关请求、远端构建/部署、安全组变更及领域代码提交 **均未执行**。没有本轮新请求模型/usage，未知费用保持 null；没有新 task_live 或 interface_live 成功结论。只读报告的独立提交按下节处理，不代表领域工作完成。

本机 0.0.0.0、WLAN 可用或 SSH 成功都不等于公网部署通过。热点、第二设备、异网访问及物理展示没有结果，不切系统网络、不伪造手机/投影。Docker daemon、本轮凭据和 E 前置分别记录；不通过增加重试或替换身份绕过阻塞。所有状态由主控据实际证据更新，D 不编辑 ACCEPTANCE。

## 本轮阻塞结算（2026-09-23 18:36）

18:36:08 主控在 E 报告 `4962d52` 已推送后授予 D 独占 Git 时段，只允许 `git add -- docs/tracks/freeze-demo.md`，检查暂存路径后 commit + push。报告提交的完整 SHA 和远端一致性由终端最终回执给出，避免报告自引用提交 SHA；本轮不提交任何领域修改，也不暂存 E/T/主控文件。

本报告使用 `git diff --no-index --check -- /dev/null docs/tracks/freeze-demo.md` 检查，未发现空白错误，仅提示工作区 LF 后续可能转换为 CRLF；仅文档变更，不运行业务测试。提交前再次核对 `git diff --cached --name-only`，提交后核对 `git show --stat --oneline HEAD` 与远端分支 SHA。

用户尚未解除 E 前置，主控明确要求报告推送后以 `outcome=failed`、原因 `preflight gate blocked` 发送一次终结回执并结束本次 turn。这里的失败指原定 G5 软件链路任务未能进入实施，不能用已完成的只读核查替代任务成功。后续需要主控/用户解除前置并重新派发；网关凭据仍需安全提供，热点/第二设备/物理展示仍由实际条件决定。
