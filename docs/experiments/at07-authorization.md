# AT-07 可审查授权包（准备完成不等于执行授权）

本包针对 Spec §10.1、AT-07、§14.4。**真实 AT-07：NOT_RUN；L2：NOT_RUN。**
**当前执行准备结论：NOT_READY。原子范围导出 UNSUPPORTED，必须在最终冻结/真实授权前由原 Owner 解决。**
`at07_live` 在任何Docker读取、key读取或SDK create前拒绝；接受基础设施边界的参数也不能绕过。
下面保留完整可审查的操作方案和工具，并不声称这个固定上游组合已经可以开始真实AT07。
原 live adapter 同样须声明 `export_bounded=False`，原 factory 的 prepare/admit/create 不能由旧/手填PASS档绕过。
后继官方 API、精确版本、最小修改面与尚未解决的硬链接语义见
[原子导出可行性调查](at07-export-feasibility.md)；它是设计审查，不是运行验证。
Spec 原文件 SHA256 为 `AB73F60E26AF1BC1B44CA5DA9B94B2CFDDA91A5D4ACB25683B9386462DCFB165`。
不得用旧 C/I sandbox、旧成功/失败/unknown 档案、Mock 或本包的离线结果授权动态候选。
先固定组合完成离线回归和 installed 输入验证，再由负责人单独授权下面的一次无害检查；
全部实际通过后才讨论一次 L2。本包不授权候选、科学、模型、付费、外部材料或 Hub 操作。

## 固定对象与资源

| 对象 | 固定值 / 本次上限 |
| --- | --- |
| 宿主 | 当前 Windows 单宿主；既有 Docker Desktop Linux engine；不改 daemon/WSL/全局 HOME |
| SDK | 现有 `opensandbox==1.1.0`；既有官方 SDK，重试 disabled、metrics disabled、server proxy 开启 |
| server | `opensandbox/server:release-1.1.0@sha256:68ca0212a2749b2c73096ce2ec0264455c64442c45f81007db442f52bf84c9d1` |
| execd | `opensandbox/execd:v1.1.0@sha256:6cf7dba2f21f0b536e100563d841ac58a9f31c2b0a081b7ac76796a24d6f47e2` |
| 实验 / 受控目标 image | `python:3.12.13-slim@sha256:229a2c5bfa27522db7815ea81f9bed70af17ccb9de9fc7ad142b1877b5830d36`；Linux amd64，Python 3.12，stdlib，无科研依赖安装 |
| egress | `opensandbox/egress:v1.1.7@sha256:db7345d567b0970f384b8e3fa7a93a71b7f43d4b16bb2009de34096e9a87b3b5` |
| egress 平台清单 | Docker Hub Registry manifest 只读核对于 2026-10-03；amd64 子清单 `sha256:1361851fc54f0175da55c6e63978338d6cfc408a6cdaae6534965b9f76eaf605`；arm64 `sha256:bc1dc7791d2857ca08c31d17f8ad6886b127d42bedb372517886171ef7d287e2`；没有拉取 layer |
| 宿主锁 | 当前 `poetry.lock` SHA256 `5fabe288babc951a1fdfd6abf980d576cba1b0bbe48b3ff2d528d00c84ffa101`；最终组合若改锁，使用最终实际值并重新准备，不能套用旧 binding |
| 新自有服务 | Compose project `morph-r1-at07` / container `morph-r1-at07-server`；loopback `127.0.0.1:8099`；1 CPU / 512 MiB / 无额外 swap / 128 pids / restart=no |
| 受控目标 | `morph-r1-at07-target`；0.25 CPU / 64 MiB / 无额外 swap / 8 pids / 只读 root / caps ALL dropped；TCP loopback8098→9000、UDP loopback8053→9053；600 秒自行退出 |
| 无害 sandbox | **最多一次 SDK create、一个 sandbox、并发 1**；1 CPU / 512 MiB / 128 pids / 180 秒 lifetime / 30 秒 command / 1 MiB export；零 host/PVC bind、零 credential proxy、零 extensions |
| 网络 | 原 default bridge；`defaultAction=deny`、egress `dns+nft`、IPv6 disabled；不创建网络、不改变已有网络或全局防火墙；测试只指向本次受控私有 IPv4 与 `.test` 域名 |
| 创建数量 | 成功路径最多 5 个新容器：server、target、sandbox、egress、一次 server 自用 execd cache 临时容器；1 个 `opensandbox-runtime-<sandbox_id>` 自有 volume；0 个新 network。实际 IDs 均记录，未返回 ID 的创建保持 unknown |
| 时限 | sandbox 请求后命令窗口240秒，SDK调用上限45秒、Docker只读调用10秒；观察与清理总预算300秒；整个准备部署/检查/精确收尾窗口600秒。超时停止新增动作，剩余资源/效果 unknown，不称硬实时清理完成 |

配置文件是 [`at07.config.toml`](../../deploy/opensandbox/at07.config.toml) 和
[`at07.compose.yaml`](../../deploy/opensandbox/at07.compose.yaml)。它们没有覆盖历史 `config.toml/compose.yaml`。
server/execd/egress 来自 Apache-2.0 的官方 OpenSandbox；CPython 为 PSF-2.0，镜像 OS 组件保留各自许可。
本项目诊断代码为原创，没有复制上游实现。固定 release 源为
[`b1a29cf93a823a95913f7943010febb3f29de05c`](https://github.com/opensandbox-group/OpenSandbox/tree/b1a29cf93a823a95913f7943010febb3f29de05c)，
execd image 的旧 source tag 记录见 [upstream.md](upstream.md)；源 commit 与 image digest 分别固定，不声称二进制构建溯源已得到证明。

## 授权前必须明确的实际限制

1. 当前主控观察 Docker engine npipe 不存在，**本轮没有启动 Docker/WSL/service**。
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
5. **原子范围导出 UNSUPPORTED，是硬停止项。** 原 generated executor 先等命令返回，再download，最后destroy，
   没有冻结整个候选进程树。SDK 1.1.0 下载只接收path/range/offset/limit；目录元数据检查与stream是分离请求。
   官方固定execd source `48b0215f1bd097b31d0f022a44640e00c11ac49d` 的
   [`filesystem_download.go`](https://github.com/opensandbox-group/OpenSandbox/blob/48b0215f1bd097b31d0f022a44640e00c11ac49d/components/execd/pkg/web/controller/filesystem_download.go)
   第71行按解析后的路径调用 `os.Open`。没有据此得到原子root/no-follow保证；源码也不等于已部署binary证据。
   SDK 的 offset/limit 是行数，本适配的字节界限改用 `Range: bytes=0-<limit>`（含一个超限检测字节），
   宿主仍独立累计/拒绝超限字节；范围大小控制也不能解决路径替换竞争。
   本轮inert负例确实在第三层metadata检查后替换读取源，原适配仍返回fake范围外字节。
   静态symlink拒绝和大小限额保留，但不再构成export PASS：diagnostic强制标unsupported，
   unverified记录的 `export_bounded=False`，真实入口在create前拒绝。不能手改标志或填verified绕过。
6. caps ALL/目录类型接口/egress 镜像与固定 server、execd 的组合未经真实运行；启动或接口不支持须报 UNSUPPORTED/UNKNOWN。
   元数据不足时 fail closed；目录检查不是原子保证，尚未证实的候选进程树/文件替换安全性不能由负责人接受风险后改为PASS。

`--accept-disclosed-infrastructure-limits` 仅记录负责人对第2/3项运行范围的明确决定，
不是权限授予，不把任何必测失败改为 PASS。若负责人不接受这些边界，包仍可离线审查，实际检查保持 NOT_RUN。
不要为“完成 AT07”自动升级 server/SDK、换后端或部署新的证明设施。

## 每项试验与判据

| 项目 | 有效负试验 / 原始观测 | 通过条件 |
| --- | --- | --- |
| host 文件 | 新建 synthetic `canary/credentials`；目标容器正向确认存在；sandbox 对3个固定 fake canary 路径尝试只读和 r+b 写入；宿主前后核对原字节 | 均 ENOENT/EACCES，宿主字节不变，同时 Docker无宿主bind |
| 账户凭据 | 仅 target 带 `AT07_FAKE_CREDENTIAL`，只检查布尔可见性；不读真实账户目录 | target正向可见、sandbox不可见，真实key未作为sandbox env/bind传入 |
| host control / 权限 | Docker mounts、Privileged、CapDrop/CapAdd、security opts；sandbox检查3个control socket；尝试 raw socket 与 unshare mount namespace | 无 socket/host bind，非特权，NoNewPrivs=1、CapEff/CapBnd=0；两项无害权限动作 EPERM/EACCES |
| export | 原 `OpenSandboxSession.download`：16字节正常文件、1MiB+1文件、绝对越界、`..`、symlink 指向另一个 fake 文件 | 正常 bytes 一致；超限和3类越界明确拒绝，非网络错误伪装拒绝 |
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

## 现在可执行：离线审查

使用 B 私有 COPY 环境；命令不需要 Docker。测试窗口仍由主控串行分配：

```powershell
.venv/Scripts/python.exe -m pytest tests/experiments/test_at07.py tests/experiments/test_at07_export.py -q
.venv/Scripts/python.exe -m orchestration.experiments.at07 --help
```

`prepare` 输入为**现有 `IsolationConfiguration`** JSON，而非新 Manifest。
字段包括 endpoint、实际service完整containerID作为instance_id、`git:<固定SOURCE>:deploy/opensandbox/at07.config.toml`
作为 runtime_profile、canonical `python@sha256:...`、实际 dependency_lock_sha256、固定BackendProfile。
离线样本可以使用 `instance_id=UNBOUND-NOT-RUN`；真实create独立拒绝该值。
target IP当前 UNKNOWN，离线样本显式用受控私网示例；真实执行前必须与本次target inspect精确相等。

```powershell
.venv/Scripts/python.exe -m orchestration.experiments.at07 prepare --configuration C:/morph-r1/at07/configuration.json --server-config deploy/opensandbox/at07.config.toml --probe-id at07-review-only --target-ipv4 172.17.0.2 --archive-root C:/morph-r1/at07/review
.venv/Scripts/python.exe -m orchestration.experiments.at07 review --result C:/morph-r1/at07/review/at07-review-only/result.json
```

输出只有固定probe源码、配置副本和 NOT_RUN 诊断。目录不可重用。Mock/replay/partial/unknown不会产生verified记录，
即使完整离线fixture满足静态诊断判据，export仍unsupported；`unverified_record()`仍
`verified=False,passed=False,process_limit=False,export_bounded=False`。

## 仅在随后单独批准后：一次执行顺序

以下命令本轮 **全部 NOT_RUN**。执行者先写下授权引用、最终核心/产品SOURCE、私有installed环境、唯一probe-id、
允许的宿主基础设施边界与600秒停止时间；同一授权不允许重试第二次create。
**第0步：当前原子导出硬停止项尚未解决，停止在这里，不创建服务、target或sandbox。**
后续步骤仅供评审和下一份解决该问题的精确候选复用；不能通过CLI风险接受参数解除此停止。

1. 人工确认上述限制与既有引擎启动权限；引擎未运行就停止。本工具不提供 engine 启动命令。
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
   将实际值填入 `IsolationConfiguration`，以最终锁和固定SOURCE生成 runtime_profile，运行上面的 `prepare`，
   改用新的 `<批准probe-id>`、真实target IP与保护的 `C:/morph-r1/at07/evidence` 根。
   不能将offline review目录改名冒充新执行，也不能改变任何资源参数。
5. 若基础设施限额/动态端口/既有DNS边界已明确接受，运行一次：

```powershell
.venv/Scripts/python.exe -m orchestration.experiments.at07_live --execute-separately-authorized-probe --authorization-ref '<真实批准记录引用>' --accept-disclosed-infrastructure-limits --prepared-root "C:/morph-r1/at07/evidence/$taskProbeId" --service-key-file $taskServiceKey --canary-directory "C:/morph-r1/at07/$taskProbeId/canary"
```

它只读Docker状态，只有官方SDK新建/操作/清理这个无害sandbox；不操作服务/target生命周期。
未知create/readiness会先留 `create-requested.json` 与UNKNOWN result，**拒绝第二POST**。
没有自动创建第二sandbox、renew、放宽caps/network/limits、切换宿主执行的路径。
原始文件在每步后保留，未知时不复跑；命令失败只可只读调查原ID。
本CLI保守返回非零，直到所有观测齐全；非零不构成重跑授权。

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
保留原失败、missing、unsupported、unknown；不填写usage/cost为0，不成为科学result/ledger奖励。

工具**从不注册verified probe**，当前硬停止项也不能由人工填字段消除。
将来支持原子范围导出的后继固定候选，经过真实执行、所有项通过、清理已确认、独立审核且完整profile匹配后，
宿主才以现有 `IsolationProbeRecord` 记录真实 `probed_at/evidence_ref`、
`declared_capability(network_deny=True, probed_server_process_limit=True)`、实际image_digest、同一IsolationConfiguration，
并令 `verified=True,passed=True`，注入现有 `TrustedProbeRegistry` 与原HostConfig的probe配置。
这是宿主对真实记录的审核，不是导入候选/CLI自报JSON作为科学或隔离权威。
每个环境、锁、endpoint、服务instance、runtime配置、CPU/memory/pids/lifetime/command/export/network不同都会被原精确绑定拒绝。
特别是本包的512MiB/128pids/stdlib镜像不能授权另一个16pids或新增NumPy/PyTorch image的候选。
没有改原GeneratedResearch factory、原TaskLedger或产品入口；如最终运行档不同，交回原Owner重新匹配，不能复制布尔PASS。

仍需负责人确认：引擎启动/镜像准备权限、固定组合SOURCE与installed路径、新ID与授权引用、实际service ID与target IP、
动态端口可达范围、是否接受可信sidecar/cache基础设施限额未知和既有DNS健康流量、独立审核员、最终L2环境是否完全同档。
仍需原Owner解决而非人工豁免：原子范围导出/候选残留进程替换边界。
这不是新的L2授权问题；在这些值明确且完整离线组合通过前，真实AT07保持NOT_RUN。
