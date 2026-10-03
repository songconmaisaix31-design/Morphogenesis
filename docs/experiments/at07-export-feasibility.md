# AT-07 原子范围导出的有界可行性调查

2026-10-03；只读源码/API 审查，未启动 Docker/WSL、未创建资源、未执行候选或探针。
当前结论仍是 **UNSUPPORTED / AT-07 NOT_READY / 真实执行 NOT_RUN**。
本文件给原 Owner 下一步的工程决策依据，不授予执行权限，也不把设计推断记成已验证能力。

## 当前组合的确定事实

| 组件 / 固定来源 | 已核对接口与结论 |
| --- | --- |
| Python `opensandbox==1.1.0`，本轨私有 COPY 安装 | `FilesystemAdapterSync._build_download_request` 只有 path、Range、offset、limit，没有原子 root/no-follow 选项；offset/limit 是**行数**，Range 才是字节范围 |
| execd v1.1.0 记录的源 `48b0215f1bd097b31d0f022a44640e00c11ac49d` | `FilesystemController.DownloadFile` 第71行 `os.Open(resolvedFilePath)`；分离的目录检查不能防止另一进程随后替换路径；源与 image digest 固定不等于已证明 binary 来源 |
| server `b1a29cf93a823a95913f7943010febb3f29de05c` | Docker `pause_sandbox` 调用 main container.pause，并暂停匹配 egress sidecar；resume 做对应恢复。原 SDK `SandboxSync.pause()` 已提供入口 |
| 2026-09-28 公开 RC `release-1.1.1-rc.1` / `e5f9102fc53f8752615fa6289acf8e5fee0afe55` | 普通文件下载仍使用相同 `os.Open`。新增 `docker.publish_host` 可限定发布地址，是另一项部署修复，不能解决导出竞争；这是预发布，RC 未发布新 SDK/CLI 包 |
| isolated-session API | 另有 `/v1/isolated/session/{id}/files/download`，RC 控制器走 merged-view `Open`；当前 Docker isolation extension 要求 SYS_ADMIN、apparmor/seccomp unconfined，不是 caps ALL dropped 的本档替换件。本次没有审定它的完整文件边界，不以名称声明安全 |

一手来源：
[固定 execd 下载实现](https://github.com/opensandbox-group/OpenSandbox/blob/48b0215f1bd097b31d0f022a44640e00c11ac49d/components/execd/pkg/web/controller/filesystem_download.go)，
[固定 server Docker 实现](https://github.com/opensandbox-group/OpenSandbox/blob/b1a29cf93a823a95913f7943010febb3f29de05c/server/opensandbox_server/services/docker/docker_service.py)，
[RC 普通下载](https://github.com/opensandbox-group/OpenSandbox/blob/e5f9102fc53f8752615fa6289acf8e5fee0afe55/components/execd/pkg/web/controller/filesystem_download.go)，
[RC isolated 下载](https://github.com/opensandbox-group/OpenSandbox/blob/e5f9102fc53f8752615fa6289acf8e5fee0afe55/components/execd/pkg/web/controller/isolated_session_files.go)，
[RC 发布记录](https://github.com/opensandbox-group/OpenSandbox/releases/tag/release-1.1.1-rc.1)。
没有查到该公开普通下载接口已发布原子范围修复的证据；这个结论限于上述精确版本和端点。

## 可复用的官方控制面原语

Docker 的 Linux pause 使用 freezer cgroup 暂停容器全部进程，包括残留子进程；不是只等父命令结束。
但这也暂停容器内 execd，因此“SDK pause 后仍调用 SDK files.read”不能构成方案。
[Docker pause 文档](https://docs.docker.com/reference/cli/docker/container/pause/)

Docker Engine 已有两个宿主控制面 API，可在不执行容器程序的情况下读文件：

- `HEAD /v1.52/containers/<完整owned-ID>/archive?path=<精确路径>` 返回
  `X-Docker-Container-Path-Stat`（base64 JSON，name/size/mode/mtime/linkTarget）。
- `GET /v1.52/containers/<完整owned-ID>/archive?path=<精确文件>` 返回 tar stream。
  CLI 等价导出形式为 `docker cp <ID>:<path> -`，不要加 `-L`，不要在宿主提取归档。

[官方 API schema](https://docs.docker.com/reference/api/engine/version/v1.52.yaml)，
[Docker cp 文档](https://docs.docker.com/reference/cli/docker/container/cp/)。

为核对实现，只读公开 `moby/moby` 的 `docker-v29.5.3`，解析到
**`285b47192d4b2f183aba5dd360a92cd52d723004`**：

- [`daemon/containerfs_linux.go`](https://github.com/moby/moby/blob/285b47192d4b2f183aba5dd360a92cd52d723004/daemon/containerfs_linux.go)
  的 `containerFSView.Stat` 在 daemon 创建的 container FS view 内使用 `os.Lstat`，
  返回 symlink mode/linkTarget。每层祖先必须分别 HEAD；单次 leaf HEAD 不会拒绝祖先 symlink。
- [`daemon/archive_unix.go`](https://github.com/moby/moby/blob/285b47192d4b2f183aba5dd360a92cd52d723004/daemon/archive_unix.go)
  的 `containerArchivePath` 在 daemon FS view 中建立 tarball，并保持 container lock 到 stream close。
  这个锁本身**不是候选进程冻结**；仍需先由官方 lifecycle pause，并在整个检查/读取期间保持暂停。

本机仅执行了 `docker --version`，返回 CLI 29.5.3 / d1c06ef；没有连接/启动引擎。
**实际 Engine 版本 UNKNOWN**，不能把 CLI 版本或上述 Moby 源码当成本机运行时证据。
真实批准前还须核对 Engine/API/安全补丁及对应源码，版本不符即重新审查，不自动更新 daemon。

## 最小后继方案与剩余缺口

可作下一步离线实现的方案是：在原 `OpenSandboxSession` 内增加受信控制面的冻结导出，
保留原 executor、result/archive、TaskLedger 和 `finalize_session`。以下是**设计推断，尚未实现/验证**：

1. 使用同一批准的 Docker daemon、完整 sandbox/sidecar IDs、原 create metadata 与 instance binding；
   不从候选输入或任意 `DOCKER_HOST/context` 选择 daemon，不读写任意宿主路径。
2. 检查非特权、caps、无 host PID/control。拒绝导出根或任一祖先上的 bind/volume/tmpfs，
   拒绝任何能让其他容器/宿主写入该导出树的共享挂载。
   execd 的原只读专属 runtime volume 位于导出根以外时，单独精确匹配；不能宽泛豁免所有 volume。
3. 官方 SDK pause 精确 owned session；通过 Engine inspect 确认 main/egress 都实际 Paused，
   暂停失败/回复未知即停止，不做文件读取、不自动重复 pause/create。
4. 保持暂停，逐层对 `/tmp`、`/tmp/morph-research`、所有子目录和目标 file 调用 HEAD。
   检查 Go FileMode 的目录/符号链接/普通文件位、linkTarget、size；禁止只看 Unix permission bits。
   任一 symlink、特殊类型、缺字段、越界名或 oversized 拒绝；不能“解析后发现还在根内”就放行 symlink。
5. 同一暂停状态下 GET 单个精确 file 的 archive；宿主用有总字节上限的 stream reader 读取，
   对 metadata、tar header/padding、payload 和总时间分别限额。只接受一个预期普通成员；
   拒绝 tar symlink/hardlink、absolute/`..`、额外成员、设备/FIFO、超大 header/PAX 和 truncated stream。
   不调用 `extract/extractall`、shell tar、候选 Python 或候选容器里的 helper。
6. 原归档只消费通过边界检查的 bytes。最终输出导出后不恢复候选，走原 `finalize_session` 的 owned kill/close；
   前置 runtime fingerprint 的读取如果必须恢复，原 SDK `SandboxSync.resume` 返回新连接对象，
   需要在原 session 封装内替换连接并确认恢复后才能继续。任何恢复/清理未知保持 unknown，不补第二 POST。
   暂停期间 TTL/删除/控制面并发、stream 中断都需要离线负例及后来单独真实 AT07 验证。

**不能忽略的限制：** Engine PathStat 不暴露 inode link count；单文件 tar 也可能把某个
拥有树外硬链接的 inode 作为普通文件输出。因此“拒绝 tar hardlink header”不证明该 inode 没有
其他名字。上述 API 足以构建“冻结后路径祖先不含 symlink、无共享写入、限定路径与字节”的方案，
但不能据此声称任意 inode 别名都已排除。如果验收要求禁止一切树外硬链接别名，必须有受信端
`fstat/nlink` 或等价的已审定官方原语；现有 API 没有该事实，不允许用容器内自报补齐。
主控于2026-10-03 04:24:23 UTC明确本轮契约为：冻结期间的批准路径、无symlink祖先/leaf、
无共享写入挂载、普通文件及字节/时间限额；拒绝tar link成员，不提取。
任意树外inode别名全面排除不是本轮新增退出条件。因此后继会实现上述路径契约，
保留nlink限制，不宣称inode级独占或用静态检查冒充真实验证。

## 精确改动面与工程选择

| 位置 | 后继最小职责 |
| --- | --- |
| `orchestration/experiments/backend.py`（B） | 原 session 冻结/受信 archive 下载、bounded stream、owned lifecycle；不是新 Executor |
| `orchestration/experiments/sandbox_adapter.py`（B） | 注入精确控制面，声明已实现能力；原 `IsolationConfiguration.runtime_profile/instance` 绑定 exporter 模式及 daemon，而非只改布尔值 |
| `orchestration/experiments/generated_executor.py`（B，确有需要才改） | 最终一批导出在同一冻结期完成，前置 fingerprint 与最终导出的生命周期位置；原错误/unknown/cleanup 语义保留 |
| `tests/experiments/**`（B） | 原始 ancestor/leaf 替换竞争；frozen 失败/unknown；挂载替换；恶意 tar/overflow；附着 session 拒绝；仅 owned 清理；未探测档不能 admit |
| `deploy/opensandbox/**`、`docs/experiments/**`（B） | 精确 Engine/daemon/export mode 部署及原子导出探针；不更新全局配置 |
| `swarm/research/dynamic.py`/HostConfig（A Handoff） | 若必须新增 trusted Docker endpoint 注入，在原 factory 配置接线；B 不跨轨编辑 |
| 核心依赖/锁/NOTICE（B，只有实际必要） | Windows npipe 的控制面 transport 优先官方 Docker Python SDK；当前 httpx 不原生提供 npipe，不能写自研管道协议。版本、Python3.13兼容和许可证须固定/验证后才加入；本轮未安装/未改锁 |

这条方案复用已有官方 freeze/archive 与原生命周期，不需要另一个 runtime、候选可写 helper、
调度器、Manifest、Hash 或证明系统，但也不是简单替换一行 download：Windows受信 transport、
暂停期边界和文件类型/挂载语义需要同 Owner 离线实现与独立复核。
若选择等待上游原子 root/no-follow API，则保持当前硬拒绝；升级 RC 只解决端口设置，不能替代该工作。
真实科学必需的 CPU 路径仍是待完成项，不能将此调查解释为允许 R1 永久仅 mock。

## 已授权的工程后继（真实运行仍未授权）

主控已决定同B继续离线实现上述最小冻结导出；先普通提交当前失败/拒绝阶段，再提交后继。
已只读核对官方 Docker Python SDK **7.2.0**（2026-07-09，Apache-2.0），
源 **`5ad5327fba623897ee9a527d7eee1b01703e0726`**，支持 Python>=3.8；
Windows依赖pywin32>=304，原锁已有pywin32 312/Python3.13 wheel。
这是拟固定依赖，当前阶段尚未安装/更新锁；不能仅凭metadata声称本机npipe验证通过。

其 `get_archive` 内部 `_stream_raw_result` 会取消 socket read timeout，
后继必须避免用这条无超时stream包装；使用同一官方 `APIClient` 的 requests transport，
显式timeout/identity编码/stream关闭及全程总期限调用只读HEAD/GET。
npipe的官方 `recv_into` 使用overlapped ReadFile+WaitForSingleObject timeout/CancelIo，
无需自研Windows管道协议；实际Engine通道仍需后来AT07观察。
[官方 SDK 7.2.0 client](https://github.com/docker/docker-py/blob/5ad5327fba623897ee9a527d7eee1b01703e0726/docker/api/client.py)，
[官方 npipe transport](https://github.com/docker/docker-py/blob/5ad5327fba623897ee9a527d7eee1b01703e0726/docker/transport/npipesocket.py)，
[官方 package metadata](https://pypi.org/pypi/docker/7.2.0/json)。
