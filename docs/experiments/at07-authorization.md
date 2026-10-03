# AT-07 可审查授权包（准备完成不等于执行授权）

本包针对 Spec §10.1、AT-07、§14.4。**真实 AT-07：NOT_RUN；L2：NOT_RUN。**
**当前准备状态：PREPARED_UNVERIFIED；真实执行仍未获授权。** 本次依据主控
`1af65788c0223f874c61bc08514c785cc95575be` 的 `docs/R1_PLAN.md` 19:30 决策，仅更新准备文档。
最终受测核心 SOURCE 为 `b480fca1b10a0b6a9c93f0d1801d38f267662461`，产品 SOURCE 为
`2b9bf73c93e732771ed3582f3bc7745ea8158b68`；P docs-only REPORT 为
`c8d4197bac272cdf5f634bc7a56c87db19bfbebb`。REPORT（包括 I 的报告 HEAD 和本次 B 文档 commit）
均不作为受测 SOURCE。b480 已包含原 SDK pause/resume、受信 Docker 控制面冻结导出及宿主配置透传；
实际 live HostConfig、Engine/daemon、服务 instance、target IP、runtime_profile、probe 和授权引用仍未确认。
没有 `docker_export` 精确配置时，`at07_live` 在 Docker/key/SDK create 前拒绝，原 live adapter
也声明 `export_bounded=False`。旧 probe 不含新配置，不能授权新路径；接受基础设施边界的参数不改变该门禁。
`prepare` 的 `ready_for_real_at07` 仅表示配置选择了已实现路径，不是 Engine 已核对、探针已通过或真实执行授权。
官方 API、精确版本、暂停期路径契约和 nlink 限制见
[冻结导出实现与来源](at07-export-feasibility.md)。离线 fixture 不是隔离实测。
Spec 在 b480 的原Git blob SHA256 为 `AB73F60E26AF1BC1B44CA5DA9B94B2CFDDA91A5D4ACB25683B9386462DCFB165`；
本次已核对，Windows checkout行尾产生的文件hash不能代替此原始blob值。
不得用旧 C/I sandbox、旧成功/失败/unknown 档案、Mock 或本包的离线结果授权动态候选。
先固定组合完成离线回归和 installed 输入验证，再由负责人单独授权下面的一次无害检查；
全部实际通过后才讨论一次 L2。本包不授权候选、科学、模型、付费、外部材料或 Hub 操作。

## 当前组合与历史边界（2026-10-03 19:30 后继）

本次从 b480 原始 Git `poetry.lock` blob 读取 384044 字节，SHA256 为
`87B335297F95B7BF72514691CB990DB0D6441316BE90C8CB726B016B9AF025EB`。
写入 `ApprovedEnvironment.dependency_lock_sha256` 时按原模型使用小写
`87b335297f95b7bf72514691cb990db0d6441316be90c8cb726b016b9af025eb`；这是同一个实际锁值，
不能改用 B 当前旧 checkout 的锁。未修改锁、生成新 profile 或运行 `prepare`。

I 私有 installed 路径为 `C:/r1i/final-product-1855/venv`，非 editable COPY。
本次只读其包 metadata：核心 `direct_url.json` 的 commit/requested_revision 均精确为 b480，
Docker 7.2.0 / OpenSandbox 1.1.0；产品 `direct_url.json` 为私有 wheel 路径，**该 metadata 本身不能证明产品 2b 来源**。
产品 2b 原 Git `pyproject.toml` 精确 pin b480；2b→P REPORT c8 仅一份报告文档。
产品原 Git/资源/锁和 installed 对应关系沿用 I 的独立证据，不将 wheel 路径当 SOURCE SHA。
本次只读核对原 I `FINAL_REPORT.md` / `logs/installed-identity-first.json`：core136 / product36 Python、
产品53资源、98 lock records；原 I 报告区分97兼容锁包与4个私有类型工具，不混用记录数和包数。
I 原全产品 **256 PASS / 423.71s**、fixture UI **126 PASS / 8 SKIP**、installed
input/session/support/refute 各 **2 PASS** 均为离线产品证据，本次未重跑，不能冒充 AT07、人工理解或科研完成。
原全产品类型门10 errors/6 files仍保留，适用30文件通过不写成整个36文件strict green。
主控后续 Handoff `msg_b3b3ae645af1` 已接纳 I docs-only REPORT
`a67c0af1e27bea08a8e2ce426337f0608e62f216` 的push/remote exact/clean及上述离线证据；它仍不是受测SOURCE。

旧 B SOURCE `5769005b09f1b756c94fdad0649a6b74690c0ca9` / REPORT
`5aebd2eb7af774b3dc496ad9620548f6e7852e09` 与旧锁
`8558e9e065da381466d9c188bc87a88fcaf09a3b367455eb8267c0bb4c9fcc98` 是明确历史输入，
旧 preparation、first RED、unsupported、unknown 及原日志全部保留；旧 binding 不能套用最终组合。
原 OpenCode Insufficient Balance 和 Codex readiness 首阻塞不改，不重试计费 route，费用仍 UNKNOWN。
本轮新私有 raw：`C:/research-private/b-at07-final-packet-ctx_021ad7956531/`，
只含原 Git 锁字节和只读来源/包 metadata 记录，不是新 preparation 或 probe evidence。

## 固定对象与资源

| 对象 | 固定值 / 本次上限 |
| --- | --- |
| 宿主 | 当前 Windows 单宿主；既有 Docker Desktop Linux engine；不改 daemon/WSL/全局 HOME |
| SDK | 现有 `opensandbox==1.1.0`；既有官方 SDK，重试 disabled、metrics disabled、server proxy 开启 |
| 受信导出 transport | 官方 `docker==7.2.0` 的 npipe/Unix requests adapters；不构造读取账户配置的 APIClient，不读取 Docker auth/context，不从环境选择 endpoint |
| Engine / API | 只支持已审查的 Linux Docker Engine **29.5.3 / API 1.52**；实际 Engine 版本、daemon ID 仍 UNKNOWN，CLI 29.5.3 不能替代它们；版本不符即停止，不自动升级 |
| server | `opensandbox/server:release-1.1.0@sha256:68ca0212a2749b2c73096ce2ec0264455c64442c45f81007db442f52bf84c9d1` |
| execd | `opensandbox/execd:v1.1.0@sha256:6cf7dba2f21f0b536e100563d841ac58a9f31c2b0a081b7ac76796a24d6f47e2` |
| 实验 / 受控目标 image | `python:3.12.13-slim@sha256:229a2c5bfa27522db7815ea81f9bed70af17ccb9de9fc7ad142b1877b5830d36`；Linux amd64，Python 3.12，stdlib，无科研依赖安装 |
| egress | `opensandbox/egress:v1.1.7@sha256:db7345d567b0970f384b8e3fa7a93a71b7f43d4b16bb2009de34096e9a87b3b5` |
| egress 平台清单 | Docker Hub Registry manifest 只读核对于 2026-10-03；amd64 子清单 `sha256:1361851fc54f0175da55c6e63978338d6cfc408a6cdaae6534965b9f76eaf605`；arm64 `sha256:bc1dc7791d2857ca08c31d17f8ad6886b127d42bedb372517886171ef7d287e2`；没有拉取 layer |
| 宿主锁 | 最终核心 SOURCE b480 原 `poetry.lock` SHA256 `87B335297F95B7BF72514691CB990DB0D6441316BE90C8CB726B016B9AF025EB`；模型字段用上文同值小写；锁变更必须重新匹配，不复用旧8558 binding |
| 新自有服务 | Compose project `morph-r1-at07` / container `morph-r1-at07-server`；loopback `127.0.0.1:8099`；1 CPU / 512 MiB / 无额外 swap / 128 pids / restart=no |
| 受控目标 | `morph-r1-at07-target`；0.25 CPU / 64 MiB / 无额外 swap / 8 pids / 只读 root / caps ALL dropped；TCP loopback8098→9000、UDP loopback8053→9053；600 秒自行退出 |
| 无害 sandbox | **最多一次 SDK create、一个 sandbox、并发 1**；1 CPU / 512 MiB / 128 pids / 180 秒 lifetime / 30 秒 command / 1 MiB export；零 host/PVC bind、零 credential proxy、零 extensions |
| 网络 | 原 default bridge；`defaultAction=deny`、egress `dns+nft`、IPv6 disabled；不创建网络、不改变已有网络或全局防火墙；测试只指向本次受控私有 IPv4 与 `.test` 域名 |
| 创建数量 | 成功路径最多 5 个新容器：server、target、sandbox、egress、一次 server 自用 execd cache 临时容器；1 个 `opensandbox-runtime-<sandbox_id>` 自有 volume；0 个新 network。实际 IDs 均记录，未返回 ID 的创建保持 unknown |
| 时限 | sandbox 请求后命令窗口240秒，SDK调用上限45秒、Docker只读调用10秒；观察与清理总预算300秒；整个准备部署/检查/精确收尾窗口600秒。超时停止新增动作，剩余资源/效果 unknown，不称硬实时清理完成 |
| 导出时限 | 每个 archive 下载含检查的总期限10秒、每次 transport 请求最多10秒；每次 read1 前后检查期限，已在等待的一个底层读取最多再占一次请求超时。SDK pause/resume 与归属检查另计，不能把它写成单文件硬实时10秒 |

配置文件是 [`at07.config.toml`](../../deploy/opensandbox/at07.config.toml) 和
[`at07.compose.yaml`](../../deploy/opensandbox/at07.compose.yaml)。它们没有覆盖历史 `config.toml/compose.yaml`。
server/execd/egress 来自 Apache-2.0 的官方 OpenSandbox；CPython 为 PSF-2.0，镜像 OS 组件保留各自许可。
本项目诊断代码为原创，没有复制上游实现。固定 release 源为
[`b1a29cf93a823a95913f7943010febb3f29de05c`](https://github.com/opensandbox-group/OpenSandbox/tree/b1a29cf93a823a95913f7943010febb3f29de05c)，
execd image 的旧 source tag 记录见 [upstream.md](upstream.md)；源 commit 与 image digest 分别固定，不声称二进制构建溯源已得到证明。

## 授权前必须明确的实际限制

1. 主控19:28只读观察 Docker Linux pipe=false、Docker进程0、空闲RAM12720MiB、C盘49.72GiB；
   这是带时点的宿主观察，不是 B 本轮重测或 Engine/隔离事实。实际29.5.3/API1.52仍 UNKNOWN。
   **本轮没有启动 Docker/WSL/service**。
   启动既有 Docker Desktop 可能恢复其他项目的 restart 容器；这是授权时必须接受/处理的宿主影响，
   本工具不启动引擎，也不停止他人容器。再次只读确认空闲物理内存、CPU、磁盘及端口。
2. 固定 server 的 Docker egress sidecar 没有承接 CPU/memory/pids 配额，`[egress].limits` 只适用于 Kubernetes。
   它额外持有 NET_ADMIN；无害 sandbox 自身必须 drop ALL、非 privileged、NoNewPrivs=1。
   固定 server 的 execd cache 临时容器也没有这些限额。两项**基础设施限额 UNSUPPORTED/总峰值 UNKNOWN**，
   不能把 sandbox 的512MiB写成整个栈的硬内存上限。工具不对已创建对象做 `docker update`，
   否则探针档将不再对应原 GeneratedResearch factory 的同一部署行为。
3. 固定 server 给 egress 发布端口在 `0.0.0.0:47400..47410`，没有 loopback-only 配置开关。
   生命周期服务自身仍只绑定 loopback8099。执行前须确认既有宿主网络/防火墙使动态端口仅处于批准范围；
   若不能确认，**不创建 sandbox**。不得临时改全局防火墙/daemon、或把“使用 proxy”当成端口隔离。
4. 上游 IPv6 sysctl 不支持时存在创建 fallback。实际 sysctl/IPv6 bind 负例必须通过；fallback 不获豁免。
   默认 `dns` 模式不够，必须实际 `dns+nft`。egress 的基础设施 DNS 健康检查可能使用既有 Docker resolver；
   它不在候选 deny 规则内。若授权要求基础设施也绝不外发 DNS，本固定栈不满足，停止并交原 Owner，不能虚报零外发。
5. **原 SDK 普通下载仍不提供暂停期间的路径稳定性。** SDK 1.1.0 下载只接收path/range/offset/limit；
   目录元数据检查与stream是分离请求。
   官方固定execd source `48b0215f1bd097b31d0f022a44640e00c11ac49d` 的
   [`filesystem_download.go`](https://github.com/opensandbox-group/OpenSandbox/blob/48b0215f1bd097b31d0f022a44640e00c11ac49d/components/execd/pkg/web/controller/filesystem_download.go)
   第71行按解析后的路径调用 `os.Open`。没有据此得到原子root/no-follow保证；源码也不等于已部署binary证据。
   SDK 的 offset/limit 是行数，本适配的字节界限改用 `Range: bytes=0-<limit>`（含一个超限检测字节），
   宿主仍独立累计/拒绝超限字节；范围大小控制也不能解决路径替换竞争。
   本轮inert负例确实在第三层metadata检查后替换读取源，原适配仍返回fake范围外字节。
   首次竞争负例和当时强制 unsupported 的 SOURCE/REPORT 保留。后继选择官方 pause 冻结 main/egress
   全部进程，宿主 Engine HEAD 逐层拒绝 symlink/特殊类型，GET 同一个普通文件的有界 tar；不执行容器内 helper、
   不提取到宿主、不信任可能被候选修改的 execd 自报。读取前后都核对同一 owned pair 实际 Paused。
   每次成功下载为原SDK `pause` → Docker只读HEAD/GET → 原SDK `resume` 同一sandbox；
   不把最终导出留在暂停状态直到销毁。因此只保证单次读取的稳定性，不宣称多个文件来自同一原子快照。
   pause/resume/stream/TTL 或对象身份未知即 unknown、不重放；最终仍走原 owned kill/close。
6. 固定上游的 `/opt/opensandbox` runtime volume 实际是 **RW**，早期调查中的“只读”假设已纠正。
   唯一例外是根外、服务管理、local driver 无 options 的 `opensandbox-runtime-<id>`，使用者必须恰为
   同次 main/egress 两个完整 ID，读取期间两者均冻结；拒绝其他挂载、第三使用者及导出树共享写入。
   该例外不意味着 runtime/execd 不可被候选改写，所有文件判据都来自受信 Engine 控制面。
   PathStat 不提供 nlink，不能声称 inode 别名完全排除；本次批准路径契约不增加这种退出条件。
7. caps ALL、冻结与 HEAD/GET、egress 镜像和固定 server/execd/Engine 组合未经真实运行；
   启动或接口不支持须报 UNSUPPORTED/UNKNOWN。缺原始事实不能由负责人接受风险后改成 PASS。

`--accept-disclosed-infrastructure-limits` 仅记录负责人对第2/3项运行范围的明确决定，
不是权限授予，不把任何必测失败改为 PASS。若负责人不接受这些边界，包仍可离线审查，实际检查保持 NOT_RUN。
不要为“完成 AT07”自动升级 server/SDK、换后端或部署新的证明设施。

## 每项试验与判据

| 项目 | 有效负试验 / 原始观测 | 通过条件 |
| --- | --- | --- |
| host 文件 | 新建 synthetic `canary/credentials`；目标容器正向确认存在；sandbox 对3个固定 fake canary 路径尝试只读和 r+b 写入；宿主前后核对原字节 | 均 ENOENT/EACCES，宿主字节不变，同时 Docker无宿主bind |
| 账户凭据 | 仅 target 带 `AT07_FAKE_CREDENTIAL`，只检查布尔可见性；不读真实账户目录 | target正向可见、sandbox不可见，真实key未作为sandbox env/bind传入 |
| host control / 权限 | Docker mounts、Privileged、CapDrop/CapAdd、security opts；sandbox检查3个control socket；尝试 raw socket 与 unshare mount namespace | 无 socket/host bind，非特权，NoNewPrivs=1、CapEff/CapBnd=0；两项无害权限动作 EPERM/EACCES |
| export | 原 `OpenSandboxSession.download` 的配置化冻结路径：16字节正常文件、1MiB+1文件、绝对越界、`..`、symlink 指向另一个 fake 文件；Engine实际Paused、owned pair/volume使用者、逐层PathStat和单文件tar | 正常 bytes 一致；超限和3类越界明确拒绝，非网络错误伪装拒绝；`frozen-export.json` 有真实控制面观测且恢复同一原ID，无未知效果 |
| IPv4 / 直连 | target TCP 正向前后可达；sandbox连接真实私有 target:9000 并发送固定 canary；target记录命中 | 连接被拒绝/超时，target无deny命中，且原始 nft规则为 default drop，不能仅拿一个本来不可达地址作证 |
| 域名 | target DNS 对 `canary.at07.test` 固定正答；sandbox向target:53发送同一问题，必须被egress DNS重定向拒绝；真实egress deny日志 | 精确query-id、NXDOMAIN、0 answers；target正答和明确的egress拒绝同时存在，单独NXDOMAIN不足 |
| IPv6 | 读取 all/default/lo disable_ipv6，并在本 namespace尝试绑定 ::1 | 三者1、bind EADDRNOTAVAIL/EAFNOSUPPORT；不是靠公网IPv6不可达过关 |
| CPU | cgroup v2 cpu.max + 2个明确自有子进程各忙4秒，读取cpu.stat前后 | quota/period=1，nr_throttled实际增加；不执行科研 |
| memory | memory.max/swap.max/events；一个子进程oom_score_adj=1000，8MiB步进、上限576MiB、8秒alarm | RAM上限512MiB，memory.events max实际增加（回收/OOM记录原样保留）；不能用声明值替代压力观测 |
| pids | 读取pids.max/events；最多129次fork、子进程最多8秒；只 kill/wait自己记录的child PID | pids.max=128、EAGAIN且max事件增加；不无限fork、不全局kill |
| command 时间 | SDK30秒执行35秒sleep，completion marker只能在超时未生效时写出；SDK日志+同command状态 | 官方timeout错误、command stopped、28–45秒、marker不存在；transport timeout为UNKNOWN |
| lifetime | 读取SDK expires_at，原ID持续观测至180秒到期；Docker ID/volume实际消失 | 到期后真实消失，不能以主动kill或metadata自报代替TTL生效 |
| 清理归属 | 原SDK `kill`+`close`/自然到期；只核对本次sandbox/sidecar/volume；全局仅只读ID基线 | 自有消失，已有其他ID保留；清理响应不确定则UNKNOWN，不重POST、不按通配符删除 |

每个子项是 `passed / failed / unsupported / unknown / not_run`。
缺正向控制、缺配置观测、缺原始事实均不通过；失败停止后续压力试验。
探针源码是固定字符串，由宿主仅 parse/compile（不exec），上传至本次sandbox；没有候选代码/学科判断。

## 现有离线 prepare/review 入口（本次未执行）

下列旧 B 私有 COPY 命令仅保留离线审查格式，**本次不安装、不测试，也不调用 --help/prepare/review**：

```powershell
.venv/Scripts/python.exe -m pytest tests/experiments/test_frozen_export.py tests/experiments/test_at07.py tests/experiments/test_at07_export.py tests/experiments/test_generated_configuration.py -q --tb=short
.venv/Scripts/python.exe -m orchestration.experiments.at07 --help
```

`prepare` 输入为**现有 `IsolationConfiguration`** JSON，不是 HostConfig 整体或新 Manifest。
b480 原调用链已核对：`swarm/research/models.py:HostConfig.generated_experiments` →
`swarm/research/service.py:ResearchService` → `swarm/research/dynamic.py:GeneratedHostSettings/GeneratedResearch` →
`LocalCpuSandboxBackend` → 原 `GeneratedExperimentExecutor` 的 prepare/admit/execute，
使用同一 `TrustedProbeRegistry` / `TrustedCriteriaRegistry`；候选与产品请求不能选择 daemon 或颁发隔离 authority。
这是已存在的透传代码，不是实际 live 配置已落盘或 probe 已注册的声明。

| 原字段 / profile 路径 | 本固定包的要求 / 当前事实 |
| --- | --- |
| `domain/protocol` → `IsolationConfiguration.endpoint` | 目标 `127.0.0.1:8099` / `http` → `http://127.0.0.1:8099`；实际服务尚未创建/确认 |
| `instance_id` | 随后本次新 server 的完整64位ID；当前 UNKNOWN，不填占位值充当真实配置 |
| `runtime_profile` | 原约定格式 `git:<最终核心SOURCE>:deploy/opensandbox/at07.config.toml`，SOURCE 必须 b480；须实际核对服务加载的同字节配置，当前实际 profile UNKNOWN，不伪造已加载值 |
| `environment` | canonical `image=python@sha256:229a2c5bfa27522db7815ea81f9bed70af17ccb9de9fc7ad142b1877b5830d36`、`image_digest=sha256:229a2c5bfa27522db7815ea81f9bed70af17ccb9de9fc7ad142b1877b5830d36`，原3.12/SDK1.1.0/opensandbox字段，`dependencies=[]`，锁字段用上文完整小写值 |
| `resources: BackendProfile` | 明确1 CPU/512MiB/180s/30s/1048576 bytes/**process_limit=128**/原network.default=deny；默认process_limit=16不能省略后误当128 |
| `server_process_limit/network_deny/use_server_proxy` | 128 / true / true；pids必须由同次实际server配置和压力观测确认，不由 SDK create 参数宣称 |
| `docker_export: DockerExportConfiguration` | 原mode=`docker-paused-archive-v1`、固定npipe endpoint、29.5.3/API1.52、`request_timeout_seconds=10`；实际 `daemon_id` UNKNOWN，须来自随后获准的只读info；无实际绑定保持None/拒绝 |
| `probes: tuple[IsolationProbeRecord,...]` | 当前无本最终组合的真实通过档；必须随后实际全项通过并独立审核才可注入，不能复制旧档或把JSON自报布尔当事实 |

target IPv4当前 UNKNOWN，只能在授权后读取本次新target实际IP。旧离线示例的
`UNBOUND-NOT-RUN`、`172.17.0.2` 和review-only ID是历史样本，不进入新真实配置。

另一受支持 transport 为 `unix:///var/run/docker.sock`，仍须同一个已绑定 Linux daemon；
不接受 TCP、任意 socket 路径或 `DOCKER_HOST` 覆盖。真实服务 instance 为完整64位container ID，
preflight 在 SDK create 之前复核 daemon版本/API/ID/Linux、固定server image和loopback宿主8099→容器8090绑定。
原 `at07_live.docker_read` 使用默认 `docker` CLI（未显式传 `--host`），冻结导出控制面则使用配置中的endpoint。
这是尚未闭合的调用链边界：后续必须在**同一受控子进程、空私有Docker配置、明确本机endpoint**条件下，
证明全部CLI只读观察与FrozenDockerExport使用同一实际daemon，并确认server使用同一个Engine。
默认context/env/认证配置未经核实不能采信，一条version/info匹配不足以证明整段调用均绑定。
原 `at07_live` CLI没有 `--host` / 私有Docker配置参数；下方只列它现有的正式参数，
不虚构已支持这些路由约束。无法对当前调用完整证明就在SDKcreate前STOP并Handoff原Owner，
必要工程后继由主控另给精确scope；本次不改b480+2b或补模块，也不改全局context/DOCKER_HOST/认证。

```powershell
& 'C:/r1i/final-product-1855/venv/Scripts/python.exe' -m orchestration.experiments.at07 prepare --configuration $taskConfigurationFile --server-config $taskServerConfig --probe-id $taskProbeId --target-ipv4 $taskTargetIPv4 --archive-root $taskEvidenceRoot
& 'C:/r1i/final-product-1855/venv/Scripts/python.exe' -m orchestration.experiments.at07 review --result "$taskEvidenceRoot/$taskProbeId/result.json"
```

以上只是原CLI的命令格式，各变量尚未赋实际值；本次未生成configuration/profile/probe或授权记录。
`$taskServerConfig` 须对应 b480 原blob；后续如复用 I `core/deploy/opensandbox/at07.config.toml`，先确认同字节。
输出只有固定probe源码、配置副本和 NOT_RUN 诊断。目录不可重用。Mock/replay/partial/unknown不会产生verified记录，
完整 inert fixture 可覆盖实际判据的分支，但不会成为运行事实；`unverified_record()`始终
`verified=False,passed=False,process_limit=False,export_bounded=False`。

## 仅在随后单独批准后：一次执行顺序

以下命令本轮 **全部 NOT_RUN**。执行者先写下授权引用、最终核心/产品SOURCE、私有installed环境、唯一probe-id、
允许的宿主基础设施边界与600秒停止时间；同一授权不允许重试第二次create。
**第0步：固定组合完整离线/installed 输入验收与单独真实授权未齐全时，停止在这里。**
SOURCE 中的实现和这份文档不构成授权；不能通过CLI风险接受参数解除该停止。
未来执行命令的相对 `deploy/opensandbox/...` 路径须来自 b480 同字节私有 COPY，
不在原 B 旧 SOURCE checkout 中直接运行，也不修改 I 工作树或现有安装。下列代码块是批准后的格式说明，当前全部未执行。

下一次独立授权的最小范围：仅当前Windows宿主、上述最终组合和四个固定镜像、只读preflight、
在全部条件满足后新建本包server/target及最多一次原SDK无害sandbox create，执行表中固定探针并精确收尾；
最多5个容器/1个自有volume/0新network，资源、时限和导出限制不变。
Engine启动可能恢复其他项目容器，须另有明确启动决定；未获准/引擎未运行就停，不提供启动或修复命令。
镜像缺失、版本不符、动态端口与现存防火墙范围不能确认、默认CLI不指向同daemon、未知已有对象归属或未接受sidecar/cache边界均停止，
不pull、不改防火墙、不重配置daemon、不更新对象、不放宽权限。
不包含science/candidate/native模型、材料外发、Hub、付费或L2；AT07全部实际通过且独立审核后，才可另议一次科学L2。
原[Poisson review](l2-poisson-review.md)本次不改，题目/容差/额度/实际运行仍待独立授权。

1. 人工确认上述限制与既有引擎启动权限；引擎未运行就停止。本工具不提供 engine 启动命令。
   已获准后，仅用明确 endpoint 只读确认实际Engine版本与ID：
   `docker --host npipe:////./pipe/dockerDesktopLinuxEngine version --format '{{.Server.Version}} {{.Server.APIVersion}}'`、
   `docker --host npipe:////./pipe/dockerDesktopLinuxEngine info --format '{{.ID}} {{.OSType}}'`。
   必须29.5.3/API1.52、linux且ID准确；同时满足上文全部CLI的受控路由条件，不能只以默认CLI的一条version/info相等放行。
   其他值或完整路由不能证明时停止交原Owner审查，不更新daemon、不猜值。
   固定4个image应已存在，使用 `docker image inspect <完整image@digest> --format '{{json .RepoDigests}}'`
   逐一只读核对。缺镜像即停止；本包不pull、不build，补镜像需独立批准。
   保留所有已有container/volume/network IDs，不停旧C/I或其他项目。
2. 创建**全新** `C:/morph-r1/at07/<批准probe-id>/canary/credentials`，仅含
   `AT07-SYNTHETIC-NOT-A-SECRET` 与LF。此目录不能已有历史run，不能是symlink。
   `AT07_CANARY_DIR`只指向此目录，不挂载账户/HOME/仓库。保留此文件，收尾不删证据。
3. 服务key只引用原受保护文件
   `C:/Users/DW/AppData/Local/Temp/morph-sandbox-live-0930/service-key`。
   不读任何原生Agent账户凭据，不打印/复制key，不展开compose环境。

```powershell
$taskProbeId = '负责人批准的新唯一ID'
$env:AT07_CANARY_DIR = "C:/morph-r1/at07/$taskProbeId/canary"
$taskServiceKey = 'C:/Users/DW/AppData/Local/Temp/morph-sandbox-live-0930/service-key'
$env:OPENSANDBOX_SERVER_API_KEY = [IO.File]::ReadAllText($taskServiceKey).Trim()
try {
    docker compose -f deploy/opensandbox/at07.compose.yaml config --quiet
    if ($LASTEXITCODE -ne 0) { throw 'Prepared owned compose validation failed' }
    # Before this first creation ensure BOTH fixed names are absent, not reused.
    docker compose -f deploy/opensandbox/at07.compose.yaml up -d --no-build --pull never server target
    if ($LASTEXITCODE -ne 0) { throw 'Owned startup unknown; no retry' }
} finally {
    Remove-Item Env:OPENSANDBOX_SERVER_API_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:AT07_CANARY_DIR -ErrorAction SilentlyContinue
}
```

4. 用 `docker inspect --format '{{.Id}}' morph-r1-at07-server` 和 target 对应命令捕获**完整ID**，
   分别确认label `morph.owner=r1-at07`、image、loopback ports、配置ro挂载。
   target IP命令为 `docker inspect --format '{{.NetworkSettings.IPAddress}}' morph-r1-at07-target`。
   将实际值与第1步的daemon ID填入 `IsolationConfiguration`，以最终锁和固定SOURCE生成 runtime_profile，运行上面的 `prepare`，
   改用新的 `<批准probe-id>`、真实target IP与保护的 `C:/morph-r1/at07/evidence` 根。
   不能将offline review目录改名冒充新执行，也不能改变任何资源参数。
5. 若基础设施限额/动态端口/既有DNS边界已明确接受，运行一次：

```powershell
& 'C:/r1i/final-product-1855/venv/Scripts/python.exe' -m orchestration.experiments.at07_live --execute-separately-authorized-probe --authorization-ref $taskAuthorizationRef --accept-disclosed-infrastructure-limits --prepared-root "C:/morph-r1/at07/evidence/$taskProbeId" --service-key-file $taskServiceKey --canary-directory "C:/morph-r1/at07/$taskProbeId/canary"
```

它只读Docker状态/archive，只有官方SDK新建/暂停/恢复/操作/清理这个无害sandbox；不操作服务/target生命周期。
未知create/readiness会先留 `create-requested.json` 与UNKNOWN result，**拒绝第二POST**。
没有自动创建第二sandbox、renew、放宽caps/network/limits、切换宿主执行的路径。
原始文件在每步后保留，未知时不复跑；命令失败只可只读调查原ID。
本CLI保守返回非零，直到所有观测齐全；非零不构成重跑授权。
`$taskAuthorizationRef` 当前 UNKNOWN；参数必须指向随后真实批准记录，不能以本包或I离线报告代填。

6. 工具在已知owned sidecar上只读运行固定 `nft -j list ruleset`，保存 `effective-nft.json`；
   只保留 `canary.at07.test` 的日志行到 `domain-denial.log`，不保存完整环境/任意label/token。
   timeout之后用官方SDK `files.get_file_info(['/tmp/morph-research/at07-timeout-completed'])` 确认精确404，
   前后再确认sandbox仍可读取；连接失败/未找到sandbox不算“marker不存在”。
   这3项保存在 `effective_nft_default_deny`、`egress_domain_denial_observed`、`timeout_marker_absent`，
   原始nft/marker响应和域名拒绝行均须由独立宿主审核员检查。上游日志格式若不匹配明确的 `action=deny`，
   保持UNKNOWN，人工只读核对已保存原始记录；不能重跑，也不能直接把缺失的布尔字段写true。
7. sandbox异常时 `finalize_session`只删除已有owned session，清理失败保持UNKNOWN。
   自然到期必须看到原sandbox/sidecar/volume消失；不会再DELETE一个重建/附着对象。
   最后只清理第4步记录的两项新基础设施**完整ID**，先再次核对owner、image、创建时间与原基线不冲突：
   `docker stop --time 5 <本次target完整ID> <本次server完整ID>`，然后
   `docker rm <同两个完整ID>`。禁止 `compose down`、`prune`、按名称/标签批量rm或删除其他volume/network。
   如这两个ID不是本次创建，或任何清理效果未知，立即停止并报告，保留全部证据。

## 持久证据与既有 registry 消费

保护根：`C:/morph-r1/at07/evidence/<唯一probe-id>/`。
必备文件：configuration/server/probe固定输入、create-requested、sdk-info、host-before/after、owned-resources、
effective-policy、各`*-command.json`完整官方execution/log/exit、target-after、result/review以及第6步3项独立只读观测。
另保存 `frozen-export.json`：精确main/sidecar IDs、批准路径、原始PathStat、实际bytes、读取前后Paused。
这些观测连同本次官方生命周期/异常记录审查；缺冻结证据不会只凭16字节文件成功就通过。
保留原失败、missing、unsupported、unknown；不填写usage/cost为0，不成为科学result/ledger奖励。

当前 SOURCE 的暂停/恢复语义和记录范围如下，不能把未保存的响应补写成运行事实：

| 路径 | 实际动作 / 持久记录范围 |
| --- | --- |
| 正常单次导出 | 原SDK pause一次；Engine确认owned main/egress都Paused，再逐层HEAD及GET；finally原SDK resume一次，检查返回ID一致与两者非暂停。small成功时保存`frozen-export.json`的读取前后Paused/PathStat/bytes；没有单独保存每次pause/resume原始响应文件 |
| 词法越界 | pause前明确拒绝；absolute/traversal不发生pause/resume，不应记成已做生命周期试验 |
| 超限/类型拒绝 | 已暂停后拒绝，finally只在只读inspect确认owned pair确实都Paused时尝试一次resume；各拒绝字符串进入result的export观测，不将拒绝当成没有发生暂停 |
| pause响应异常 | 保留unknown；finally只读核对实际状态。若明确两者已暂停，仍尝试一次原resume；明确都运行则不resume；混合/不可读则不盲目恢复。不重复pause/create，成功恢复不能抹掉原unknown |
| resume/ID/状态/stream未知 | 原session标记unknown，阻止后续执行/导出；负例分项保存`unknown:<异常类型>`，小文件阶段异常由operator保留remote_effect unknown及异常类型，原owned清理仍尝试并独立记录cleanup。没有这些分支的真实运行记录，不能由离线fixture替代 |

`frozen-export.json`当前在small成功后写入，因此不是每个负例的完整HTTP或生命周期响应转录。
后续真实检查须保留工具现有result/reasons/cleanup和负责人对缺失证据的判断；记录不完整时保持UNKNOWN，
不得手填“全部pause/resume已通过”、重跑探针或把代码检查写成运行证明。

工具**从不注册verified probe**。同一固定组合经过随后单独授权的真实执行、所有项通过、清理已确认、
独立审核且完整profile匹配后，
宿主才以现有 `IsolationProbeRecord` 记录真实 `probed_at/evidence_ref`、
`declared_capability(network_deny=True, probed_server_process_limit=True, configured_frozen_export=True)`、
实际image_digest、同一IsolationConfiguration（含docker_export），
并令 `verified=True,passed=True`，注入现有 `TrustedProbeRegistry` 与原HostConfig的probe配置。
这是宿主对真实记录的审核，不是导入候选/CLI自报JSON作为科学或隔离权威。
每个环境、锁、endpoint、服务instance、runtime配置、daemon/Engine/export模式、CPU/memory/pids/lifetime/command/export/network不同都会被原精确绑定拒绝。
特别是本包的512MiB/128pids/stdlib镜像不能授权另一个16pids或新增NumPy/PyTorch image的候选。
本B没有跨轨修改GeneratedResearch factory、原TaskLedger或产品入口；A受信配置接线已存在于 b480，
原离线Q复核不替代本最终组合的真实AT07。实际宿主settings/registry及与后续L2同档的确认仍待运行授权和独立审核。
最终运行档不同则交回原Owner重新匹配，不能复制布尔PASS。

仍需负责人确认：引擎启动/镜像准备权限、固定组合SOURCE与installed路径、新ID与授权引用、实际Engine/daemon/service ID与target IP、
动态端口可达范围、是否接受可信sidecar/cache基础设施限额未知和既有DNS健康流量、独立审核员、最终L2环境是否完全同档。
离线实现已覆盖冻结期间的路径契约，真实运行证据尚缺；不宣称inode级独占、多个文件同快照或严格硬实时收尾。
在这些值明确、完整离线组合通过且收到单独授权前，真实AT07保持NOT_RUN。
