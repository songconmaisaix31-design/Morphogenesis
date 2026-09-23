# 北京 ECS：独立只读页面和 Python API

目标：`47.93.118.110:7799`，Compose project 固定 `morphogenesis`，版本目录 `/opt/morphogenesis/releases/<完整提交 SHA>`。共治现有 80/443/8080、容器、数据与 Docker 配置不变。2026-09-23 封板夜由 D 唯一操作本项目部署，主控协调每次外部写入；独立 I 最后复验。

探针使用项目锁定 Python 环境及真实 `Acceptance` / `RehearsalDocument` / `TaskResult` 契约，校验快照、来源与结果一致性；合法 live 证据可为 `passed`，空态、mock、replay 不升级。探针通过不等于新模型调用、真实公网或现场演示通过。Python 直接服务也限制 GET/HEAD、拒绝请求体和目录枚举、使用静态文件白名单；`MORPH_BIND_IP` 默认为 loopback，显式 `--host` 优先。公网使用 nginx 的限流与超时边界，Python 不提供任务写入路由，因此没有新增 token 机制。

## 内容与来源

- Web：Nginx 官方镜像，唯一发布端口 7799；根页面、现有脚本/CSS/ECharts、F 的两份字体及许可证文件白名单；不存在的路径 404，目录不列举，非 GET/HEAD 405，带请求体 413。每 IP 8 个并发连接；静态 20 req/s + burst 40，dashboard 2 req/s + burst 10，两个 EvoMap 路径共享 6 req/min + burst 3，超限 429。
- API：原 `python -m viz.server --host 0.0.0.0 --port 7500`，只在本项目默认容器网络，不发布宿主端口。不新增数据库、登录、任务控制或付费调用。`/api/dashboard`、`/api/evomap`、`/api/evomap/asset` 同源，固定代理目标，不信任 URL 提供的上游。EvoMap 仍可向现有公开 Hub 发出只读 GET，因此该容器网络保留出站网络。healthcheck 只访问 dashboard。
- Python 官方 3.13.7 slim Bookworm、Node 官方 22.19.0 Bookworm slim、Nginx 官方 1.28.0 Alpine，均固定 registry manifest digest（2026-09-23 本机实际解析）。Python 运行依赖由原 `poetry.lock` / `poetry install --only main --no-root --no-directory` 安装；Poetry 2.5.1 是仅构建阶段工具，不用 export 插件、不改锁。既有读取器会导入 FAISS、LangGraph 等，保留主依赖避免破坏读取。Node `npm ci --ignore-scripts` 使用原根 `package-lock.json`，最终只复制 ECharts 文件与其 Apache-2.0 LICENSE；无 Node/Poetry/编译器运行时。
- 原 `viz/static` 从最终集成 SHA 直接复制；Docker 不构建或修改 UI。F 必须先 commit，再由 I 普通合并并按其报告构建，最终包应有 `fonts/Jost-latin.woff2`、`fonts/InterVariable.woff2`。`#/physarum`、`#/workspace`、`#/swarm` 都是浏览器哈希路由，无需代理 SPA fallback。
- 项目/前端第三方声明仍由 `THIRD_PARTY_NOTICES.md` 与 `viz/static/licenses` 承载。部署配置是项目自有胶水，语义参考 [Docker Compose services](https://docs.docker.com/reference/compose-file/services/)、[Docker build context](https://docs.docker.com/build/concepts/context/)、[Poetry install](https://python-poetry.org/docs/cli/#install)、[Nginx proxy](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)。没有复制外部实现代码。

## 生成可审查的标准包（本地）

只对已审阅并提交的集成完整 SHA 打包，示例变量必须替换为真实值。脚本调用标准 `git archive`，按文件白名单读提交，不读工作区脏文件；不创建自研 manifest/hash/调度系统。包不含 `.git`、`.env`、账户、SSH key、运行证据、node_modules 或测试数据。Dockerfile 另有默认拒绝的 context allowlist 和明确 COPY。

```powershell
$release = git rev-parse HEAD
python deploy/package.py $release "$env:TEMP\morphogenesis-$release.tar.gz"
tar -tzf "$env:TEMP\morphogenesis-$release.tar.gz"
```

正式发布前 I 必须确认这个 HEAD 已含 F + D 精确提交，不能把 D 分支的旧 UI 当 F 候选。API secret 无需配置，Compose 不透传主机环境；不要添加密钥 build args、`.env` 或前端配置。

## 首次部署与更新（本轮 D 执行，主控协调）

1. 复核 `gongzhi-ecs` 主机身份、7799 空闲、磁盘与共治容器健康。目录必须尚未存在；旧版本保留作回滚。
2. `scp` 标准包到服务器 `/tmp/`，在 `/opt/morphogenesis/releases` 下解压；包内已包含 `<SHA>/` 前缀。只创建本项目目录，不覆盖旧版本。
3. 下面是服务器 Bash 命令，`MORPH_RELEASE` 填本次完整 SHA；先保持 loopback，构建并验收后再开放。

```bash
export MORPH_RELEASE=<reviewed-full-SHA>
cd /opt/morphogenesis/releases/"$MORPH_RELEASE"
export MORPH_BIND_IP=127.0.0.1
docker compose --env-file /dev/null -p morphogenesis -f deploy/compose.yaml config --quiet
docker compose --env-file /dev/null -p morphogenesis -f deploy/compose.yaml build
docker compose --env-file /dev/null -p morphogenesis -f deploy/compose.yaml up -d --no-build --force-recreate --wait --wait-timeout 120
docker compose --env-file /dev/null -p morphogenesis -f deploy/compose.yaml exec -T api python deploy/smoke.py http://web:8080 --with-fonts
docker compose --env-file /dev/null -p morphogenesis -f deploy/compose.yaml ps
```

`--force-recreate` 使 Web 随 API 重建，更新 Nginx 启动时解析的 API 地址。更新不是零停机。`--wait`/健康检查不等于自动恢复；Docker restart 策略处理进程退出，健康失败由操作者诊断，不自动重试构建、上游调用或上线。

北京节点目前 Docker Hub 连接失败的事实由主控预检报告；若仍无法 pull，I 可在本机对**同一最终包**构建 linux/amd64 镜像，然后 `docker save morphogenesis-api:$MORPH_RELEASE morphogenesis-web:$MORPH_RELEASE -o <file.tar>`，`scp`，服务器 `docker load -i <file.tar>` 后执行 `up --no-build`。不要调整全局镜像源或重启 Docker；留意本机镜像与 tar 的磁盘占用，未验收前不清理旧版本，不 prune。

4. 本次最终公网选择历史回放：先在 loopback 执行下节完整 replay 命令并验收，再由主控设置 `MORPH_BIND_IP=0.0.0.0`，保留 `MORPH_REPLAY_FILE` 和两份 `-f` 配置，对同一版本再次执行 `up -d --no-build --force-recreate --wait --wait-timeout 120`，并仅为指定安全组新增 TCP 7799。此包不执行安全组变更。再从外部真实浏览器访问 `http://47.93.118.110:7799/` 核对字体、布局、哈希路由与 API。HTTP 无域名/无 TLS，符合本次 IP 展示范围；不承载账号或秘密。
5. 可选 `python3 deploy/smoke.py <URL> --with-fonts --evomap-live` 只发起一次实际公开只读搜索，不重试。报告里的每块 status/error 才代表上游结果；HTTP 200、mock 数据或页面展示都不是新的 task_live。

## 数据与历史回放

基础配置仅项目 `demo/data/mock-run.json`，三态保留；EvoMap 本地 Gene pool 未配置则如实缺失。**主控已选定最终公网版本使用第四轮历史回放**，由 I 单独复制私有快照并使用以下 override，不进 Git/镜像。需要空态时操作者可用 Compose command 空列表覆盖默认参数；不注入假运行。历史快照必须先审阅是否适合公开展示，只读挂载**单个** `rehearsal.json`，不挂载证据根/数据库/家目录。

```bash
export MORPH_REPLAY_FILE=/opt/morphogenesis/data/rehearsal.json
docker compose --env-file /dev/null -p morphogenesis -f deploy/compose.yaml -f deploy/compose.replay.yaml config --quiet
docker compose --env-file /dev/null -p morphogenesis -f deploy/compose.yaml -f deploy/compose.replay.yaml up -d --no-build --force-recreate --wait --wait-timeout 120
docker compose --env-file /dev/null -p morphogenesis -f deploy/compose.yaml -f deploy/compose.replay.yaml exec -T api python deploy/smoke.py http://web:8080 --with-fonts
```

文件必须存在且 UID 10001 可读；`create_host_path: false` 防止路径错写创建目录，`--replay` 强制沿用现有降级读取语义。源文件无写入、无模型调用，数据只是历史 replay。重新启动默认 mock 时仅使用基础 Compose 文件；保留先前实际使用的数据模式和路径作回滚记录。

## 回滚与停止

保留前一版完整目录和 `morphogenesis-{api,web}:<SHA>` 两个镜像及数据模式记录。回滚时 `cd` 前一版目录，`export MORPH_RELEASE=<previous-full-SHA>`，按原来的 `MORPH_BIND_IP`、数据模式/override 运行同一 `up --no-build --force-recreate --wait`，再做 smoke 和外部浏览器核验。失败时不自动反复部署；记录 `ps` 与本项目 `logs --tail 100` 供原轨返修。初次上线无前版时使用同一配置 `docker compose ... stop` 停本项目，由主控撤去本轮安全组规则；不影响共治。不自动删镜像、版本目录或数据。

## 本地验证

```powershell
uv tool run poetry run python -m pytest tests/deployment tests/t5 -q
$env:MORPH_RELEASE='d-local-check'
docker compose -p morphogenesis-d-check -f deploy/compose.yaml -f tests/deployment/compose.local.yaml config --quiet
docker compose -p morphogenesis-d-check -f deploy/compose.yaml -f tests/deployment/compose.local.yaml build
docker compose -p morphogenesis-d-check -f deploy/compose.yaml -f tests/deployment/compose.local.yaml up -d --no-build --wait --wait-timeout 120
python deploy/smoke.py http://127.0.0.1:17899
docker compose -p morphogenesis-d-check -f deploy/compose.yaml -f tests/deployment/compose.local.yaml down
```

本地验收使用独立 project + loopback 17899；只清理这些临时容器/网络，保留其它项目。D 尚未合入 F 时不加 `--with-fonts`；这不替代 I 对最终 SHA 的测试、容器构建、实际浏览器与远端 HTTP 验收。
