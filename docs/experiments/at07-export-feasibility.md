# AT-07 冻结范围导出的来源、实现与边界

2026-10-03；官方源码/API 审查及离线实现，未启动 Docker/WSL、未创建资源、未执行候选或探针。
当前 SOURCE **`5769005b09f1b756c94fdad0649a6b74690c0ca9`** 实现受信配置选择的暂停导出路径，
状态 **PREPARED_UNVERIFIED / 真实 AT-07 与 L2 NOT_RUN**。未配置的默认路径仍 unsupported。
此前强制拒绝阶段 SOURCE `296ec298a23eea54f76e8c874aed551487a2999a` / REPORT
`7a6c5094c7235b1a992e0eaa8d688b08fa0fd64b` 及首 RED 原样保留。
本文件不授予执行权限；A接线、Q独立复核与固定组合installed验收仍须后续完成。

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
实现只接受已审查的 **Engine29.5.3/API1.52**，不允许把任意版本字符串填进配置后自称支持。
真实批准后必须只读核对实际Engine/ID及安全补丁状态，版本不符即重新审查，不自动更新 daemon。

## 已实现的暂停期路径契约

原 `OpenSandboxSession` 增加配置化冻结导出，保留原 executor、result/archive、TaskLedger 和
`finalize_session`。以下机制已做 inert 单进程测试，**尚未经过真实 Engine/探针验证**：

1. 使用同一批准的 Docker daemon、完整 sandbox/sidecar IDs、原 create metadata 与 instance binding；
   不从候选输入或任意 `DOCKER_HOST/context` 选择 daemon，不读写任意宿主路径。
2. 检查非特权、caps、无 host PID/control。拒绝导出根或任一祖先上的 bind/volume/tmpfs，
   拒绝任何能让其他容器/宿主写入该导出树的共享挂载。
   早期“execd runtime只读”假设不成立：固定 server 和 sidecar 都挂载 `/opt/opensandbox:rw`。
   唯一例外是该根外、服务管理、local driver 无 options 的 `opensandbox-runtime-<id>`；
   Engine 列出的使用者必须恰为同次 main/egress 两个完整ID且两者都暂停。拒绝第三使用者、其他挂载、
   bind driver 或导出树共享写入；不把 runtime/execd 内容当成不可修改的信任根。
3. 官方 SDK pause 精确 owned session；通过 Engine inspect 确认 main/egress 都实际 Paused，
   暂停失败/回复未知即停止，不做文件读取、不自动重复 pause/create。
4. 保持暂停，逐层对 `/tmp`、`/tmp/morph-research`、所有子目录和目标 file 调用 HEAD。
   检查 Go FileMode 的目录/符号链接/普通文件位、linkTarget、size；禁止只看 Unix permission bits。
   任一 symlink、特殊类型、缺字段、越界名或 oversized 拒绝；不能“解析后发现还在根内”就放行 symlink。
5. 同一暂停状态下 GET 单个精确 file 的 archive；宿主用有总字节上限的 stream reader 读取，
   对 metadata、tar header/padding、payload 和总时间分别限额。只接受一个预期普通成员；
   拒绝 tar symlink/hardlink、absolute/`..`、额外成员、设备/FIFO、超大 header/PAX 和 truncated stream。
   不调用 `extract/extractall`、shell tar、候选 Python 或候选容器里的 helper。
6. 原归档只消费通过边界检查的 bytes。每次成功下载是原SDK pause → Docker只读HEAD/GET →
   原SDK resume；finally只在只读inspect确认owned pair确实都暂停时尝试恢复**同一个**sandbox，
   `SandboxSync.resume` 返回的新连接对象必须ID一致，再替换原session连接并核对非暂停。
   前置 fingerprint 和各最终文件均复用原单文件API；因此没有多个文件同一原子快照的承诺。
   最终仍走 `finalize_session` 的 owned kill/close。恢复对象ID不同只关闭借来的连接，不kill另一对象。
   pause/resume未知、TTL/删除/控制面并发及stream中断保持unknown，阻止后续执行/导出，不重POST或退回宿主。
   这些分支有离线负例，后来仍需单独真实AT07核对全部行为。
   pause异常后可能经只读核对确认已暂停并尝试一次resume，但不会把原unknown改成成功。
   小文件成功的PathStat/bytes/Paused观测有持久文件；当前没有逐次pause/resume原始响应转录，
   不将这部分未保存数据写成实测事实，完整记录范围见授权包。

RW来源：固定server的
[`docker_service.py`](https://github.com/opensandbox-group/OpenSandbox/blob/b1a29cf93a823a95913f7943010febb3f29de05c/server/opensandbox_server/services/docker/docker_service.py)
与sidecar的
[`networking.py`](https://github.com/opensandbox-group/OpenSandbox/blob/b1a29cf93a823a95913f7943010febb3f29de05c/server/opensandbox_server/services/docker/networking.py)
都使用`:rw`；管理标签定义在
[`constants.py`](https://github.com/opensandbox-group/OpenSandbox/blob/b1a29cf93a823a95913f7943010febb3f29de05c/server/opensandbox_server/services/constants.py)。
这项纠正已交主控确认；旧报告保留原假设，当前实现不依赖那个错误假设。

**不能忽略的限制：** Engine PathStat 不暴露 inode link count；单文件 tar 也可能把某个
拥有树外硬链接的 inode 作为普通文件输出。因此“拒绝 tar hardlink header”不证明该 inode 没有
其他名字。上述 API 足以构建“冻结后路径祖先不含 symlink、无共享写入、限定路径与字节”的方案，
但不能据此声称任意 inode 别名都已排除。如果验收要求禁止一切树外硬链接别名，必须有受信端
`fstat/nlink` 或等价的已审定官方原语；现有 API 没有该事实，不允许用容器内自报补齐。
主控于2026-10-03 04:24:23 UTC明确本轮契约为：冻结期间的批准路径、无symlink祖先/leaf、
无共享写入挂载、普通文件及字节/时间限额；拒绝tar link成员，不提取。
任意树外inode别名全面排除不是本轮新增退出条件。因此当前实现上述路径契约，
保留nlink限制，不宣称inode级独占或用静态检查冒充真实验证。

## 精确改动面与工程选择

| 位置 | 当前最小职责 |
| --- | --- |
| `orchestration/experiments/backend.py`（B） | 原 session 暂停/恢复、受信 archive 下载、owned lifecycle；不是新 Executor |
| `orchestration/experiments/frozen_export.py`（B） | 官方transport只读HEAD/GET，实际daemon/server/owned pair/volume检查，逐层PathStat、bounded tar/时间、无宿主提取 |
| `orchestration/experiments/generated.py`、`sandbox_adapter.py`（B） | 原 `IsolationConfiguration` 增可空冻结模型 `DockerExportConfiguration`；新字段进入既有prepare/admit/create精确比较；无配置/旧probe不声明导出支持 |
| `orchestration/experiments/generated_executor.py`（B） | 保留原逐文件消费；导出TimeoutError不能降成missing_artifact，原unknown/cleanup语义保留 |
| `tests/experiments/**`（B） | 原始 ancestor/leaf 替换竞争；frozen 失败/unknown；挂载替换；恶意 tar/overflow；附着 session 拒绝；仅 owned 清理；未探测档不能 admit |
| `deploy/opensandbox/**`、`docs/experiments/**`（B） | 精确Engine/daemon/export模式及无害探针；成功读取保存frozen-export原始事实；不更新全局配置 |
| `swarm/research/dynamic.py`/HostConfig（A Handoff） | 原受信配置接 `DockerExportConfiguration | None`，原factory传 `docker_export=self.settings.docker_export`；不接受候选/产品请求选择endpoint，实际ID未知保持None；B未跨轨修改 |
| 核心依赖/锁/NOTICE（B） | 新增官方 `docker==7.2.0`，原依赖版本不变；私有COPY环境安装唯一runtime新包，Python3.13构造官方npipe/Unix adapters离线通过，实际npipe连接仍NOT_RUN |

这条方案复用已有官方 freeze/archive 与原生命周期，不需要另一个 runtime、候选可写 helper、
调度器、Manifest、Hash 或证明系统，但也不是简单替换一行 download：Windows受信 transport、
暂停期边界和文件类型/挂载语义仍需独立复核与真实证据。
升级RC只解决端口设置，不能替代这些导出保证；本轮没有升级server/execd/egress。
真实科学必需的CPU路径实现已准备，实际可用性须同档AT07验证，不能将本文件解释为允许R1永久仅mock。

## 官方依赖、transport与离线证据

主控授权同B继续最小冻结导出，并已先普通提交失败/拒绝阶段、再提交后继；没有改写首RED。
已只读核对官方 Docker Python SDK **7.2.0**（2026-07-09，Apache-2.0），
源 **`5ad5327fba623897ee9a527d7eee1b01703e0726`**，支持 Python>=3.8；
Windows依赖pywin32>=304，原锁已有pywin32 312/Python3.13 wheel。
已在主控串行窗口中安装到B私有COPY `.venv` 并更新锁，未使用系统pip或修改其他Owner环境。
官方wheel SHA256 `a3f45fdeb9165e2d25d9a1d02ddf3bc70fb572cf5ebbf9b58558c22caf29b71f`；
sdist `cebb93773d334f778e023a7ee352a8d6e13ab1bd3b863a4d4a59dec897df43ac`。
当前锁SHA256 `8558e9e065da381466d9c188bc87a88fcaf09a3b367455eb8267c0bb4c9fcc98`；
私有临时Poetry2.3.2工具环境仅用于解析锁，未改变其他锁定版本。

其 `get_archive` 内部 `_stream_raw_result` 会取消 socket read timeout，
实现避开这条无超时stream包装；也不构造会读取Docker auth配置的`APIClient`。
仅把官方`NpipeHTTPAdapter/UnixHTTPAdapter`装到`requests.Session(trust_env=False)`，
固定本地endpoint，不用registry/account/context，显式timeout/identity编码/stream关闭调用只读HEAD/GET。
每个archive含逐层检查总期限10秒、每次请求至多10秒；`raw.read1`前后核对时间，
避免大chunk隐藏慢速trickle。已在等待的一次底层读取仍可能多占一次请求超时，SDK暂停/恢复另计；不声称硬实时。
npipe的官方 `recv_into` 使用overlapped ReadFile+WaitForSingleObject timeout/CancelIo，
无需自研Windows管道协议；实际Engine通道仍需后来AT07观察。
[官方 SDK 7.2.0 client](https://github.com/docker/docker-py/blob/5ad5327fba623897ee9a527d7eee1b01703e0726/docker/api/client.py)，
[官方 npipe transport](https://github.com/docker/docker-py/blob/5ad5327fba623897ee9a527d7eee1b01703e0726/docker/transport/npipesocket.py)，
[官方 package metadata](https://pypi.org/pypi/docker/7.2.0/json)。

新增冻结与既有AT07/configuration定向测试 **110 PASS**，所有 `tests/experiments` **210 PASS**，
严格类型检查 **140 source files PASS**，私有环境 **104 packages compatible**。
strict首测 `Returning Any` 失败保留，运行时已校验bool后仅补类型cast；原始输出见
[at07-evidence](at07-evidence/)。Q旧fixture三项失败仍是上一阶段事实，当前需Q按新精确配置独立覆盖正负例。
测试只执行inert SDK/HTTP fixture与宿主静态解析；没有真实Engine调用、sandbox、探针或候选执行。
