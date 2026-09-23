# D 轨：封板夜 G5 软件链路

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
