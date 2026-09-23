# D 部署轨交接

## 身份与范围

- Worker：Codex / GPT-6，本轨未派子 Agent。
- worktree：`C:/Users/DW/orca/workspaces/Morphogenesis/morph-beijing-deploy`。
- branch：`songconmaisaix31-design/morph-beijing-deploy`。
- 业务起点 `c68def4de25cedb48acd258bea614f7dff35cc16`；先普通合并 `2b71d635016bbd800a4f6a06fee688d6e401e304`。规划与状态文件仅由该合并带入。
- 修改仅 `deploy/**`、`viz/server.py`、`tests/deployment/**` 与本报告；F 的 `viz/frontend/**`、`viz/static/**`、`tests/t5/**` 和锁文件均未改。
- 已读取 F 原报告 `morph-gpt-reference/docs/tracks/frontend-gpt-reference.md`，复用其字体 URL、哈希路由和数据边界，没有复制其未提交文件。I 仍需普通合并 F 精确提交，再构建最终静态资源。

## 实现

- 原只读服务增加 `--host`，默认保持 `127.0.0.1`；容器显式 `0.0.0.0:7500`。HEAD 使用同一路由/Content-Length 且不写响应体；过多 query 参数返回 JSON 400，避免公开输入触发断连。
- 独立 Compose project `morphogenesis`，Web 对外 7799（初验默认 loopback），Python 无发布端口；只读文件系统、非 root、全部 capabilities 丢弃、资源/日志上限、healthcheck 和 `unless-stopped`。
- Nginx 仅固定静态路径、两份 F 字体、许可证与三个 API；GET/HEAD、无请求体、速率/并发/连接/读写超时限制、禁目录列表、禁符号链接，固定上游，无 task/DB/任意 URL 代理。API 出站仍限于原代码中的 EvoMap 公开只读路径，无新 secret 配置。
- 三个官方基础镜像使用实际查询的 manifest digest；Poetry 2.5.1 构建阶段按原 `poetry.lock` 安装 main，Node 按原根 `package-lock.json` 安装后只复制 ECharts；最终静态产物直接来自审阅 SHA，不重写 UI。无 export 插件、无锁变更。
- `deploy/package.py` 是标准 git archive 白名单包装，拒绝非完整 SHA、非普通文件与已有输出；只读已提交 blobs，排除工作站秘密、脏文件和本地证据。Docker context 再做默认拒绝，COPY 明确。
- 基础配置为显式 mock；主控后续消息已指定最终公网选第四轮真实历史文件，以 `compose.replay.yaml` 单文件只读挂载并强制 `--replay`。文件单独交付、不进入镜像/Git；不升级新 interface_live/task_live。
- 发布、回滚、Docker Hub 不可达时本机 build/save 后远端 load、故障停止步骤见 [deploy/README](../../deploy/README.md)。无远端写入脚本、自动重试、prune 或其它项目操作。

## 已执行核验

2026-09-23 使用阿里云 CLI 3.4.11 的 `ecs DescribeInstances` / `DescribeSecurityGroupAttribute`，仅输出实例、公网 IP、安全组端口信息；未读出配置/凭据。目标 `i-2ze2nztd89vevmw21wif` running，`47.93.118.110`，`cn-beijing`，`sg-2zeedkqp6urfm9c29ghm`；入站仅现有 22/80/443/3389/ICMP，未开放 7799。

SSH `BatchMode=yes` 只读核验 Ubuntu 24.04.4 LTS x86_64，Docker 29.1.3，Compose 2.40.3，共治四容器 healthy，80/443/127.0.0.1:8080 已占用，7799 空闲；根盘剩余 9.7GB、内存可用 6.5GiB、UFW inactive、`/opt/morphogenesis` 尚不存在。未改远端文件、容器、配置或安全组。

本机初查 Docker daemon 不可达；协调者随后启动 Desktop 并明确授权本轨隔离本机 build/up/HTTP 验收。后续验收只使用 `morphogenesis-d-check` / `127.0.0.1:17899`，不触碰其它容器。

| 验证 | 结果 |
| --- | --- |
| `uv tool run poetry install --no-root --no-interaction` | 成功，原锁 82 packages，专属 worktree cache venv Python 3.12.13；Poetry 2.5.1 |
| `npm ci --ignore-scripts --no-audit --no-fund` | 成功，99 packages，锁未改 |
| `uv tool run poetry run python -m pytest tests/deployment tests/t5 -q` | 67 passed（31.54s）；16 部署 + 51 原 T5 |
| `python -m mypy --strict viz/server.py`（同锁环境） | Success，1 source file |
| `docker compose -p morphogenesis-d-check -f deploy/compose.yaml config --quiet` | 通过；Compose 本机 v5.1.4，合并 replay 配置另由测试实际解析 |
| `git diff --check` | 通过；Windows LF/CRLF 提示，无空白错误 |
| 本机 Linux 镜像 build / HTTP / replay | 实施提交时构建进行中，最终验证记录待追加 |

## 边界

`contract_local` 本地测试与容器 HTTP 验证独立记录；历史回放不是新任务。远端构建/容器加载/部署/安全组、公网 HTTP 与浏览器、最终 F+D 集成 SHA 验收、物理投影与生产 Hub 写入均未在本轨执行。依赖下载和官方镜像可达性是部署环境前提；北京节点 Docker Hub 不通由主控实测报告，本轨不修改全局配置规避。最终上线和任何领域返修由主控 / I 与原轨衔接。
