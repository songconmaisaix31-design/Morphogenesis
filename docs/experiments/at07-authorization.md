# AT-07 可审查授权包（准备完成不等于执行授权）

本包针对 Spec §10.1、AT-07、§14.4。**真实 AT-07：NOT_RUN；L2：NOT_RUN。**
**当前状态：用户已专项批准；本次创建前STOP，SDKcreate=0，PREPARED_UNVERIFIED。科学L2未获授权。**

## 21:44 专项批准后的真实前置STOP与独立只读诊断

用户已提交“我现在批准AT-07，继续开发”，原C转交`msg_f469ac99f92f`（UTC13:23:20），
root治理`a3880ffb8e83a5df8f22a3880f47483e9754ac01`已直接核原提交终端stream并接纳；不是draft或本B代批。
本次使用原15de+c84/r2非editable来源，**有授权不等于实际AT07已完成**。
原600s窗口为UTC13:29:15.9497674至13:39:15.9497674，不延期、不重置。
Desktop仅一次Hidden启动；首官方受控Compose调用exit125，立即创建前STOP并交root。
没有prepare、密钥读取、基础设施创建、SDKcreate、pause/HEADGET/resume、探针或科学执行。
原首stderr仅记存在，内容未保存，明确**MISSING**，不能补写或借后继诊断恢复首错误原因。

root `msg_0fc604f1bb10`、`msg_c0ce00419282`、`msg_a38c276da9e4`随后仅追加必要只读工程诊断
与本授权包docs修正范围，**不恢复probe/create，不新启动Desktop，不改变冻结业务/测试/锁/profile**。
原证据见[本次secret-free摘要](at07-evidence/live-20261003.txt)，完整私有first/diagnostic分档根
`C:/research-private/b-at07-live-ctx_6b1c2488a3d2/`。

| 当前实际观察 | 结果 / 保持的停止条件 |
| --- | --- |
| 首`docker --host <固定npipe> --config <新空目录> compose version --format json`，三system子env | exit125/4.768s/stdout空/stderr内容MISSING；首失败原样保留，未推根因 |
| 新只读Compose诊断，固定非秘密`ProgramFiles`定位项 | UTC13:42:30.747，exit0/5.254s/`v5.1.4`/stderr空；只证明这次插件version路径，不是首失败翻绿或AT07 |
| 新同endpoint只读version/info | UTC13:44:06，实际LinuxEngine29.5.3、advertised API1.54/MinAPI1.40，daemon `6cc73c96-c021-4a82-ade6-2fc9ae693fff`。冻结配置为Literal1.52且原runner严格比较，**API不匹配STOP**；不得用DOCKER_API_VERSION、配置伪值或upgrade/downgrade绕过 |
| 新固定四digest同次image inspect | server68ca…/execd6cf7…/python229a…存在；固定egress `opensandbox/egress:v1.1.7@sha256:db7345d567b0970f384b8e3fa7a93a71b7f43d4b16bb2009de34096e9a87b3b5`返回No such image，exit1，**缺镜像STOP，不pull/build** |
| 动态端口与宿主 | 首host RAM5781MiB/C42.83GiB、pipe=false、activeFW mask4，三profile启用且COM inbound0/outbound1；Docker Backend TCP/UDP规则remote/local/ports均*，另有非loopback block规则。未核实际有效匹配/未来0.0.0.0:47400..47410可达范围，仍UNKNOWN/STOP；不改防火墙或开监听器证明 |
| 收尾 | 三个新私有空config各核同身份后rmdir，不递归删；0自有新容器/volume/network、无server ID可停止保留。Desktop启动对他项目影响NOT_ASSESSED，未停Engine/他人对象；不称全宿主资源清空 |

### 最少后继Compose发现路线（仅工程诊断已观察，不开放部署）

[官方Docker CLI v29.5.3 Windows manager](https://github.com/docker/cli/blob/v29.5.3/cli-plugins/manager/manager_windows.go)
使用`ProgramFiles`推导系统`Docker/cli-plugins`；
[同版本manager](https://github.com/docker/cli/blob/v29.5.3/cli-plugins/manager/manager.go)
也会查私有config下plugin目录及配置扩展目录。本次空config无这些条目，不读取用户HOME/auth或追加配置。
三system首env未含定位项是静态发现缺口推断；第一stderr缺失，不确定它就是首错误原因。

实读`C:/Program Files/Docker/cli-plugins/docker-compose.exe`为常规Archive、非link、33657776字节，
SHA256 `E295CD078CACEBC2081CB266275268B3895EC14452B31A9D7568CE295BD59915`、Valid Docker Inc，
与原resources本体精确相同。root只批准这个固定系统locator，没有批准任意父env或插件路径。
保留下面原官方绝对CLI/同npipe/新空owned config/typed argv/shell=False/10s格式，Compose子env最少增加：

```python
# Read-only diagnostic format observed once; not a deploy/probe retry.
task_compose_env = {**task_process_env, "ProgramFiles": "C:/Program Files"}
subprocess.run(
    [*task_prefix, "compose", "version", "--format", "json"],
    shell=False, env=task_compose_env, cwd=task_owned_new_root,
    capture_output=True, timeout=10, check=False,
)
```

`task_process_env`仍仅固定必要PATH/SYSTEMROOT/WINDIR；非Compose Engine读与原SDKreader不加locator。
Compose的必要key/canary仍仅在未来条件全部满足的已批准动作child内存传递，本次均未读取/传递。
DOCKER_*/HOME/USERPROFILE/TLS/auth/context/APIheaders/proxy大小写变体均不继承，父/全局环境、空config不改。
不扩read-only docker_read白名单，不复制上游代码或新造执行器。官方参数依据仍为
[Docker CLI文档](https://docs.docker.com/reference/cli/docker/)。
当前[Compose main/standalone转换](https://github.com/docker/compose/blob/main/cmd/compatibility/convert.go)
不列`--config`为被提到根层的string flag；未实际验证同边界standalone，不将它写成替代可运行路线。
源码main是本次观察参考，不冒充已安装v5.1.4精确源码绑定。

此前外层模板三system项对Windows Compose发现不足，后继以上述固定locator/已核本体为准；
它没有解决Engine API、缺镜像、动态端口或资源未知等门。当前实际runtime配置/server/target/probe/registry仍不存在，
API字段和SOURCE不得由本docs修改。只交原Owner/主控处理真实阻塞，不恢复已结束window、不重放probe。
原同64ID retained_stopped选项仍需全项真实PASS与原Q独立审核，当前不适用，L2/候选/科学NOT_RUN。

## 历史21:14 最终离线工程接纳与实际授权边界

依据root `msg_3035355dbf6a` 的实际原日志接纳，以下取代历史20:29的等待身份。
本B只读Git/metadata/原日志并更新两docs，未运行测试、安装、prepare或任何Docker/Engine/SDK操作。
**离线工程阶段已接纳；原整套首RED与定向后继分别保留，不称新整套256PASS、真实AT07或R1完整通过。**

| 当前对象 | 精确身份 / 已观察范围 |
| --- | --- |
| 受测核心 SOURCE | `15de4959646df264530b978dfde9152552b9a76b`；e635→15de仅治理docs与Q两行跨平台fixture，B生产blob仍精确fc866，非任何REPORT |
| 产品 runtime SOURCE | `c84e49bd8e926f50d2c057793e8789cf137b310a`；原Git三pin指向15de。测试 SOURCE `756d5069e7739089f0e5ba1c33eebfb2657b03f0`仅两测试文件，P REPORT `eca3fd48c33fc602f1ddb3f45d91bd88e17b941b`不是产品runtime SOURCE |
| 实际锁 | 15de原Git `poetry.lock` 384044字节，SHA256 `87b335297f95b7bf72514691cb990db0d6441316be90c8cb726b016b9af025eb`；与e635/b480相同，旧8558历史保留 |
| 唯一I实际installed | `C:/r1i/successor-2018/r2/venv/Scripts/python.exe`，Python3.13.13；新私有非editable COPY。core direct_url为Git15de；product direct_url为本私有wheel，原Gitc84→wheel→installed字节核对，不能把wheel URL当VCS commit |
| 安装身份原证据 | `r2/logs/installed-identity-first.json`：core136Py、product53文件=36Py+17资源、raw字节相同/single links、98锁记录、docker7.2.0/opensandbox1.1.0；product wheel SHA256 `bc7f6a69a3268072b96ba463be52eb18a60103b2d11f16ce2a54575dd34379e0` |
| 原配置文件身份 | 15de `deploy/opensandbox/at07.config.toml`原blob1013字节，SHA256 `438fe04be51d07188b6bc4b26fbd85c2e7ce28dc02e31ed3af2a4cf27f3c0b79`；这是源码文件身份，非服务实际加载或真实runtime profile证明 |
| I/P/B REPORT | 承载原日志和治理；I最终docsmerge/REPORT尚待唯一I交付，不改上述受测SOURCE、不新pin/CI。本B当前交付也仅docs REPORT |
| 实际运行身份 | Engine版本/API/daemon、server完整ID、targetIP、服务加载配置、实际runtime profile、probe/授权ref仍UNKNOWN；没有真实AT07通过档，AT07/L2 NOT_RUN |

I原日志根为 `C:/r1i/successor-2018/r2/`；以下都是contract_local/installed离线证据，B仅只读消费：

| 原命令 / 原日志 | 实际结果与边界 |
| --- | --- |
| 原CI `37123370202` attempt1 / head15de；`python -m pytest -q`、`python tools/typecheck.py`、`python -m build`、`npm run check:sdk`及wheel安装检查；`logs/ci-full-first.log` | Windows1825PASS/15SKIP/75warnings/1820.43s；Linux1824PASS/16SKIP/75warnings/399.47s；两端strict140/build/SDK schema1.14.0校验/wheel13包及node门PASS。SDK校验published=false；未retry原run，skip/warnings原样保留 |
| I installed `test_at07.py`+`test_at07_route_boundary.py`，精确argv在`logs/commands.jsonl`；`logs/installed-core-boundaries-first.log` | 106PASS/0.84s（外层7.022s），只捕获argv/env与inert transport；不证明实际Engine隔离 |
| I r2整套产品首测，`logs/commands.jsonl`与`logs/full-product-first.log` | **255PASS/1FAIL/539.16s/exit1**（外层542.527s）；唯一四phase HTTP用例客户端15s读取超时，剩余断言当时未完成，首RED不覆盖 |
| 原P定向诊断/修复；I `test-repair/logs/test-source-identity-first.json`、`original-assertions-first.json` | 原P新fixture原15s仍1FAIL；后继P1PASS/72.29s。仅测试helper默认15s不变、该四phase POST显式900s；原assert AST全相同、53生产字节及三pin不变，无新runtime/预算/权限改动 |
| I独立 `python -I -B -X utf8 -u ... tests/test_research_api.py::test_four_phases_real_runner_boundary_and_three_page_facts --basetemp <新私有目录>`；`test-repair/logs/independent-target-command-first.json` / `independent-target-first.log` | 新测试SOURCE756、业务runtime15de+c84，**仅该node1PASS/75.32s/exit0**（外层77.785s）。无整套/UI/安装/CI重跑，不将255+1算作另一整套256PASS |
| I产品适用mypy与whole，`logs/product-mypy-applicable-first.log` / `product-mypy-whole-first.log` / `product-type-identities-first.json` | 适用30文件PASS；whole36文件10errors/6files/exit1，原表达式/identity对齐、new_errors=0，历史债务保持，不称whole strict green |

原HTTP失败phase经原P时点核对为replication；旧错配inheritance推断与修正文件均保留。
25.031594秒仅server request至response-marker落盘间隔，**不是完整HTTP客户端response时间或性能目标证明**。
旧b480+2b/a67的产品256PASS、UI126PASS/8SKIP与installed8只属前组合；原UI/生产字节无delta故未重跑，不能移植为新组合新实测。
原CI37122569886/e635 Linux1823PASS/1FAIL/16SKIP、WindowsCANCELLED和B首RED18FAIL等原记录完整保留。

最终受测输入已知，但真实授权尚无。随后`runtime_profile`必须采用原格式
`git:15de4959646df264530b978dfde9152552b9a76b:deploy/opensandbox/at07.config.toml`并实际核对加载字节；
这个要求不等于已生成或已加载profile。不得用旧1855环境执行新probe，也不从I/P REPORT取SOURCE。
主控20:13 RAM5850MiB/C45.9GiB、20:21pipe=false及Firewall原值仅带时点观察，不是当前运行/端口范围证据。
工程接纳后仍须用户独立批准下表最小范围；Desktop启动可能恢复他项目，镜像缺失STOP不pull，
实际Linux29.5.3/API1.52不符STOP不upgrade；sidecar/cache caps UNSUPPORTED、总峰UNKNOWN，
动态 `0.0.0.0:47400..47410`可达范围未证即create前STOP，不改变现存防火墙或DNS边界。
接受限制参数不能把上述UNKNOWN/UNSUPPORTED改为PASS；无候选/native模型/科学/L2授权。

| 下一独立AT07授权需明确的决定 | 仅审核准备的最小范围 / 停止条件 |
| --- | --- |
| 实际受测输入 | 固定15de+c84及r2非editable installed、锁87b/原profile438fe；先只读preflight，完整配置/真实daemon与版本/API/镜像/CLI路由不相符即STOP，不造绑定或授权ref |
| Desktop启动 | 明确是否允许启动既有Desktop，以及可能恢复他项目restart容器的影响；未批准/未运行即STOP，不停他人对象 |
| 资源与网络 | 明确是否接受sidecar/cache caps UNSUPPORTED/总峰UNKNOWN、NET_ADMIN及既有DNS健康流量；动态0.0.0.0:47400..47410范围须实际确认，否则create前STOP；不改变防火墙，不pull/build/upgrade |
| 一次无害SDKcreate | 整个部署/检查/精确收尾600s；至多5新容器/1自有volume/0新network、一个sandbox/并发1/仅一次SDKcreate；固定四digest、endpoint及512MiB/128pids/30s/180s/1MiB、原pause→HEAD/GET→resume单次导出限制保持 |
| 未知与归属 | create/readiness/pause/resume/stream/对象/清理未知不重试、不第二POST、不切宿主；只对本次已确认归属完整IDs收尾。必须明确下述成功停止保留或全部销毁选项；不能把未返回ID或cache未知补为已清理 |
| 排除与后继 | 无候选/science/native模型/L2/外发/付费/Hub，不变权限/全局HOME/auth/账号/AOCI。真实AT07全部PASS并独立审核才可注入原registry，L2再单独有界授权；本docs Task绝非运行授权 |

### 同server ID接续的待授权生命周期选项

root普通Handoff `msg_d46e0ad66e72`接纳静态说明，**没有授予真实保留/start/AT07/L2权限**。
原 `TrustedProbeRegistry` 精确比较完整configuration，`instance_id`绑定server64位ID；
原export preflight重新核同ID、daemon/版本、固定镜像与实际运行状态。删后重建即使同名也换ID，旧probe失效。

原runner只对已返回且归属明确的sandbox/sidecar IDs及其volume清理；
`cleanup_observed`仍要求这些对象消失，`unrelated_resources_unchanged`仍要求host-before基线全部保留。
server/target在此基线内。**保留原host-after/result/review，不删除基线项、不改cleanup断言或把外层清理写回原PASS。**
runner没有cache专用ID或清理PASS字段，不能从cleanup布尔推cache已清；
外层需实际记录本次cache完整ID、归属与前后观察，无法确认则UNKNOWN/禁止转L2，不能发明归属或新证明模块。

| 后续授权包中的条件选择 | 同600s窗口内的基础设施处置 / 后续边界 |
| --- | --- |
| 真实AT07全部PASS并独立审核，sandbox/sidecar/volume和明确归属cache均确认清理 | 在原runner结果封存之后，target精确stop/rm；server精确stop并确认**retained_stopped同64ID**。不称全部资源删除、不持续运行；保留归属/配置及外层原观察。未批准此选项则不能自行保留 |
| 失败/unknown，或明确批准全部销毁 | 保持原路径，只尝试归属明确的自有对象精确收尾；未知不重放/不扩大删除范围，记录剩余对象及效果。server删除/重建后旧probe不可继承 |
| 未来另行有界L2授权 | 仅在上述真实全部通过与审核之后，才可获准启动原同64ID并重新核对完整profile/lock/endpoint/daemon/image/resources/原settings。删除/重建/配置变化/未知即旧probe无效、L2 BLOCKED；不增加第二probe/candidate或权限外重放 |

停止保留是随后用户可审阅的明确决策，不由offline PASS或接受资源限制选项自动生效。
原Poisson review不变，科学L2仍NOT_RUN。基础设施DNS若要求绝不外发而固定栈不满足，STOP。

## 历史20:29 最终组合审核框架（当时工程/安装结果 PENDING）

本次仅docs，依据核心治理 `954acd0371407ae45685f68a221948790feafc3a` / 产品治理
`1a395a6d9880d57a440cf6a7433c91d637817f27` 当前 `docs/R1_PLAN.md`。
以下保留当时审核入口与等待结论；当前身份以上文21:14为准，不能将历史等待或旧绿门代入新组合。

| 当前对象 | 精确身份 / 状态 |
| --- | --- |
| 最终受测核心 SOURCE | `e635b8ab3e79529403b527892e75ffb29674af0a`；不是root/I/B REPORT |
| 最终产品 SOURCE | `8c716c450bf4b5b436e915726857260cc79cb17e`；原Git pyproject pin精确e635，不从P/I REPORT pin |
| 已普通合入的B/Q | B SOURCE `fc866465aa52a3f09773bc79a0fab95bceedc3d9`、Q测试 SOURCE `f2b81cd9c0e0623c224b0501580a19e3fc1d37da`；本次只读原Git blob均与e635相同，未重测 |
| 实际锁 | e635原Git `poetry.lock` 384044字节，SHA256 `87b335297f95b7bf72514691cb990db0d6441316be90c8cb726b016b9af025eb`；本次核对，不修改锁或profile |
| 唯一I安装目标 | `C:/r1i/successor-2018/`，新私有非editable COPY；实际python路径/direct_url/原Git字节/包metadata及工程结果 **PENDING**，不由目录名推完成 |
| 工程门 | I Task `task_33b99bbe70e8` / Dispatch `ctx_154fc9202fc1`；原CI `37122569886` attempt1派发时仍运行；原结果齐全之前 **PENDING**，本次不重复门 |
| P/I REPORT | 只承载报告、待实际交付；不作为SOURCE或真实AT07授权。后续I结果只读按精确原日志补充，缺项不填PASS |
| 当前实际隔离 | Engine版本/API/daemon、service完整ID、targetIP、实际runtime profile、probe/授权ref仍UNKNOWN；AT07/L2 NOT_RUN |

后续root Handoff `msg_50383217a323` 报告原CI37122569886 attempt1首RED：Linux
**1823 PASS / 1 FAIL / 16 SKIP**、Windows **CANCELLED**。原Q win32 junction fixture在Linux缺stat常量，
由原Q作test-only返修；B生产模块无新差异。e635+8c目前是已发布组合，**工程未通过**，
不把通过项拆出来称最终green；后继I SOURCE/新实际工程结果仍PENDING，原首失败与取消不覆盖。

旧b480+2b/a67、旧8558锁、B首RED18FAIL、Q独立首失败与各unsupported/unknown、原日志完整保留。
旧 `C:/r1i/final-product-1855/venv` 不得直接执行新probe；`$taskFinalPython` 须由I实际新installed证据给出。
本轮新私有只读取证：`C:/research-private/b-at07-final-identity-ctx_d8fb1226f9a7/`，不是新preparation或probe档。

主控带时点宿主观察：20:13 RAM5850MiB / C盘45.9GiB，20:21 DockerLinuxpipe=false；
三Firewall profile原值为Enabled=1 / InboundAction=4 / Outbound=2。
这些原值不是 `0.0.0.0:47400..47410` 仅在批准范围可达的证明；本B没有Engine或防火墙实测。
sidecar/cache资源限额UNSUPPORTED、总峰值UNKNOWN，内存数字不构成整个栈的硬上限或运行准入。

### 随后必须独立审阅的AT07决定（当前未批准）

| 需明确的决定 | 最小范围 / 停止条件 |
| --- | --- |
| 工程与installed前置 | e635+8c的适用工程/完整产品离线及安装身份结果齐全并可审阅；历史绿色结果不替代，未齐即STOP |
| Docker Desktop启动 | 明确是否允许启动既有Desktop及可能恢复他项目restart容器的宿主影响；本工具不启动Engine，不停他人对象；无权限/Engine未运行即STOP |
| 本体/镜像/daemon | 官方CLI绝对路径及实际本体/Compose插件身份须核验；固定四镜像缺失STOP不pull/build；实际Linux29.5.3/API1.52/daemon不匹配STOP不upgrade |
| 基础设施与网络 | 明确接受sidecar/cache无资源caps与总峰UNKNOWN、NET_ADMIN、既有DNS健康流量边界；动态0.0.0.0端口范围须实际确认，否则create前STOP；不改现存防火墙/daemon/网络 |
| 唯一无害检查 | 新唯一probe ID/真实授权ref；整个部署/检查/精确收尾窗口600s；最多5新容器/1自有volume/0新network、一个sandbox/一次SDKcreate/并发1；512MiB/128pids/30s/180s/1MiB及原时限不变 |
| 未知与收尾 | create/readiness/pause/resume/stream/对象/清理未知不重放、不第二POST、不切宿主执行；只对记录并重新核对归属的本次完整IDs收尾，未知即停止/保留证据 |
| 明确排除 | 无候选、science/native模型、L2、外发/付费/Hub；不改变Poisson review、账号/权限/AOCI或全局HOME/auth/config；本Task绝非上述运行授权 |

只有随后真实AT07全部PASS、精确归属清理确认、独立审核及完整profile匹配后才可注入原TrustedProbeRegistry。
`--accept-disclosed-infrastructure-limits` 仅记录运行范围决定，不能把UNSUPPORTED/UNKNOWN/失败改成PASS。
若授权要求基础设施DNS也绝不外发，固定栈不满足即STOP。科学L2仍须实际隔离通过后另行有界授权。

## 原外层CLI审核模板（未部署；本次只读事实见21:44）

这是e40原模板；本次少量只读诊断与必要Compose locator更正以上文21:44为准，不把旧等待结论代入新观察。
runner受信endpoint已修，但外层deploy/inspect/info/compose也必须使用同一明确npipe、全新空私有config和受控子环境。
**下方历史裸docker/父shell环境示例不可执行，不是当前最终路线。**
root原Get-Command定位到 `C:/Program Files/Docker/Docker/resources/bin/docker.exe`。
随后root `msg_fe8570ca7a63` / 时点纠正`msg_f2090357c4e8`，UTC2026-10-03 13:12:51附近只读文件观察：
该CLI42748848字节，SHA256 `C0E4F0379277708EEA93B39FCBBFB9BAD6F4EE97CC3EB7D326BF5D534FBF1762`；
`C:/Program Files/Docker/Docker/resources/cli-plugins/docker-compose.exe` 33657776字节，
SHA256 `E295CD078CACEBC2081CB266275268B3895EC14452B31A9D7568CE295BD59915`。
两文件Authenticode状态Valid、Signer Docker Inc；LastWriteUTC分别
2026-06-05T19:39:28.2997437Z / 2026-06-05T19:39:31.1540471Z。
这是当时文件身份/签名观察，当时未启动CLI/Compose/Engine；后继实际版本诊断以上文21:44为准，不改此原时点记录。
后续须重核本体身份与受控实际解析；argv fixture/签名都不能替代，无法确认即STOP。
runner当前仍以`docker`名字调用；随后受控runner启动环境还须确认该名字实际解析为同一批准本体，
不能仅用外层绝对路径或一次version相同替它授予本体身份。本任务不改代码来绕过这个实际确认。

下面只是一次官方CLI调用的typed argv格式，不是新增执行器或可运行脚本：变量均待真实批准与原安装证据。
`task_outer_config` 必须在本次新保护根下以 `.at07-outer-docker-cli` 新建空目录；
复用原no_links检查、拒绝已有/链接/未知覆盖，记录自有目录身份，结束只rmdir仍同身份的空目录。
runner自己的 `.at07-docker-cli` 与外层目录分开；未知新增文件保留，不递归删除或改用户Docker配置。

```python
# REVIEW TEMPLATE ONLY: no values for the pending approval/install variables.
task_cli = "C:/Program Files/Docker/Docker/resources/bin/docker.exe"
task_endpoint = "npipe:////./pipe/dockerDesktopLinuxEngine"
task_prefix = [task_cli, "--host", task_endpoint, "--config", str(task_outer_config)]
task_process_env = {
    "SYSTEMROOT": task_approved_system_root,
    "WINDIR": task_approved_system_root,
    "PATH": str(Path(task_approved_system_root) / "System32"),
}
task_observation = subprocess.run(
    [*task_prefix, *task_approved_suffix], shell=False, check=False,
    env=task_process_env, cwd=task_final_source_copy,
    capture_output=True, text=True, timeout=10,
)
```

`Path/subprocess`为stdlib；`task_approved_suffix`只能是下表负责人核准的一项字面参数，不能来自候选/任意MCP请求。
必要系统路径/大小写须按实际批准宿主核对，不拷贝任意父PATH。所有DOCKER_*、HOME/USERPROFILE、
auth/TLS/context/API/custom headers、HTTP(S)/ALL/NO_PROXY及其大小写变体均不继承，不修改父进程/全局环境。
Compose两项仅按需在这个新子env附加原受保护key的内存值 `OPENSANDBOX_SERVER_API_KEY` 和本次
synthetic目录 `AT07_CANARY_DIR`；其他CLI子env不带key/canary。不打印/复制key、不展开compose配置/env，
只记录非秘密结果，stderr/异常可能含敏感值时保持secret-free错误和UNKNOWN，不原样发布。
所有调用受剩余600s总窗口限制；超时/启动返回不确定都不重试，不能把进程退出码当远端效果已知。

| 外层操作 | 加在同一task_prefix之后的typed参数（仅授权后） |
| --- | --- |
| version / info只读 | `["version", "--format", "{{.Server.Version}} {{.Server.APIVersion}}"]`；`["info", "--format", "{{.ID}} {{.OSType}}"]`，须与原受信transport实际daemon一致 |
| 四固定镜像只读 | `["image", "inspect", task_fixed_image_at_digest, "--format", "{{json .RepoDigests}}"]`；只用下方四完整固定镜像，不pull |
| 既有ID基线只读 | `["ps", "-aq", "--no-trunc"]`；`["volume", "ls", "-q"]`；`["network", "ls", "-q", "--no-trunc"]` |
| 固定名称不存在检查 | `["ps", "-aq", "--no-trunc", "--filter", "name=^/morph-r1-at07-server$"]`及target同式；已有任一对象STOP不复用 |
| Compose校验 | `["compose", "-f", task_final_compose, "config", "--quiet"]`，只用15de同字节文件与实际核验解析的插件，子env仅额外带受保护key/canary |
| 一次新基础设施创建 | `["compose", "-f", task_final_compose, "up", "-d", "--no-build", "--pull", "never", "server", "target"]`；仅批准后一次，返回未知STOP不重试 |
| 新server/target事实 | `["inspect", "--format", task_nonsecret_fixed_format, task_owned_full_id]`；首次从上述固定名称取得完整ID，再确认owner/image/创建时点/loopback/config挂载/实际targetIP；格式不得包含完整Env或token labels |
| 全PASS后获准同ID停止保留 | 原runner结果封存且sandboxpair/volume/cache清理确认后，`["stop", "--time", "5", task_target_full_id, task_server_full_id]`，确认两个stop效果后仅`["rm", task_target_full_id]`；600s内server确认stopped，保留同完整ID与原观察；真实保留目前NOT_RUN |
| 失败/unknown或获准全销毁 | 只对归属/状态已核对的本次完整IDs，原`stop --time 5`后`rm`两个ID路线；未知不盲重放、不删他人对象，不按名/标签批量删除、不compose down/prune；server删除使旧probe无效 |

上表外层操作不进入`docker_read`，不扩展它的read-only/fixedexec白名单；唯一sandbox仍由原SDK创建/暂停/恢复/清理。
后续prepare/live runner仍使用原正式参数、最终私有python、同完整configuration以及真实授权ref；
当前serviceID/targetIP/runtime profile/ref均UNKNOWN，不能把这张审核表生成虚构profile或批准记录。
官方参数来源仍为[Docker CLI文档](https://docs.docker.com/reference/cli/docker/)，没有复制上游实现或新建运行调度系统。

## 历史19:39 端点绑定工程后继（仅离线验证）

依据主控 `df12d36e31d4dd7d7a5a54263eed710f283689c2` 当前计划，原 B 后继业务 SOURCE
`fc866465aa52a3f09773bc79a0fab95bceedc3d9` 已普通push，仅改 `at07_live.py` 与本文件对应的AT07测试。
此 SOURCE 尚待唯一 I 精确合入、原 P 重新pin以及适用工程门；**不能用前组合 b480+2b/a67 的installed或离线通过结果验收新组合**。
本 SOURCE 未改变锁/依赖，B旧分支的8558锁也未升级；最终受测集成SOURCE、产品SOURCE、锁和installed路径
须由 I/P 后续精确给出，当前不伪造新固定值。下文19:30组合与87B锁仍是前组合记录。

修正复用原 `DockerExportConfiguration` 和官方CLI：所有inspect/inventory、固定cat/nft与筛选域名日志
都通过同次execute绑定的reader，typed argv含 `docker --host <配置endpoint> --config <本次空私有目录>`，
`shell=False`、10秒、原262144字符观察上限。仅保留子进程PATH/SYSTEMROOT/WINDIR，按大小写规范读取；
不继承HOME/USERPROFILE、任何DOCKER_*、TLS/证书/API/context/custom headers、代理或service key。
闭合原命令形式，拒绝附加全局路由选项、其他inspect格式、任意exec和mutation；没有fallback默认reader。
`execute` 在CLI/密钥/SDKcreate前重验完整IsolationConfiguration、128pids固定profile及真实service/runtime身份格式；
继而用原 `FrozenDockerExport.preflight()` 核对Engine版本/daemon/Linux/server绑定，并用同一原transport读取
`/version` 核对实际 `ApiVersion=1.52`，不以CLI自报或配置字面值代替。
真实控制面读取本次均未发生，测试只注入原transport的inert数据和捕获subprocess argv/env。

空目录仅在新的probe root下创建 `.at07-docker-cli`，拒绝已有目录、symlink/junction/hardlink路径；
收尾核对目录身份，仅rmdir空目录。非空/替换目录保留并报错，不递归删未知内容，不改全局配置或HOME。
原一次SDKcreate、create-requested/no-replay、UNKNOWN与原owned SDK cleanup结构保持；目录清理错误不得当成探针PASS。
原SDK pause→Docker只读HEAD/GET→原SDKresume及全部实际隔离限制仍适用。

依据 [Docker官方CLI文档](https://docs.docker.com/reference/cli/docker/)（本次只读）：context可覆盖host环境项，
默认用户配置可能含认证；显式host、空config和不继承这些环境项共同固定此调用的本机路由。
来源为官方参数说明，未复制上游代码，未增加transport/registry/证明/调度系统或配置schema。
定向首测18 FAIL、后继44 PASS、最终52 PASS/2.04s及改动文件strict1 PASS原日志保留于
`C:/research-private/b-at07-endpoint-ctx_0c9ab2aea2f0/`；都是contract_local，非Engine/AT07隔离证据。
没有重跑原110/210/Q65、核心CI或产品256/UI门；费用/模型用量UNKNOWN。

## 19:30 前组合准备记录（历史受测身份保留）

下列段落为此前docs-only准备，依据主控
`1af65788c0223f874c61bc08514c785cc95575be` 的 `docs/R1_PLAN.md` 19:30 决策，仅更新准备文档。
前组合受测核心 SOURCE 为 `b480fca1b10a0b6a9c93f0d1801d38f267662461`，产品 SOURCE 为
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

## 前组合与历史边界（2026-10-03 19:30 后继）

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
| Engine / API | 冻结要求 Linux Docker Engine **29.5.3 / API 1.52**；本次实际只读Engine29.5.3/advertised API1.54及daemon ID见21:44，API不匹配STOP。CLI版本相同不解除此门，不用环境覆盖或自动升级 |
| server | `opensandbox/server:release-1.1.0@sha256:68ca0212a2749b2c73096ce2ec0264455c64442c45f81007db442f52bf84c9d1` |
| execd | `opensandbox/execd:v1.1.0@sha256:6cf7dba2f21f0b536e100563d841ac58a9f31c2b0a081b7ac76796a24d6f47e2` |
| 实验 / 受控目标 image | `python:3.12.13-slim@sha256:229a2c5bfa27522db7815ea81f9bed70af17ccb9de9fc7ad142b1877b5830d36`；Linux amd64，Python 3.12，stdlib，无科研依赖安装 |
| egress | `opensandbox/egress:v1.1.7@sha256:db7345d567b0970f384b8e3fa7a93a71b7f43d4b16bb2009de34096e9a87b3b5` |
| egress 平台清单 | Docker Hub Registry manifest 只读核对于 2026-10-03；amd64 子清单 `sha256:1361851fc54f0175da55c6e63978338d6cfc408a6cdaae6534965b9f76eaf605`；arm64 `sha256:bc1dc7791d2857ca08c31d17f8ad6886b127d42bedb372517886171ef7d287e2`；没有拉取 layer |
| 宿主锁 | 当前受测15de原 `poetry.lock` SHA256 `87b335297f95b7bf72514691cb990db0d6441316be90c8cb726b016b9af025eb`，本次raw核对；与e635/前组合b480同锁。锁变更必须重新匹配，不从B旧8558锁复用binding |
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

下列旧 B 私有 COPY 命令仅保留历史离线审查格式：19:30文档任务未执行它们；
19:39只执行上文定向AT07测试和改动strict，没有重跑下列旧绿全门或调用CLI --help/prepare/review：

```powershell
.venv/Scripts/python.exe -m pytest tests/experiments/test_frozen_export.py tests/experiments/test_at07.py tests/experiments/test_at07_export.py tests/experiments/test_generated_configuration.py -q --tb=short
.venv/Scripts/python.exe -m orchestration.experiments.at07 --help
```

`prepare` 输入为**现有 `IsolationConfiguration`** JSON，不是 HostConfig 整体或新 Manifest。
b480 原调用链已核对，本次只读确认以下原路径到15de零Git差异：`swarm/research/models.py:HostConfig.generated_experiments` →
`swarm/research/service.py:ResearchService` → `swarm/research/dynamic.py:GeneratedHostSettings/GeneratedResearch` →
`LocalCpuSandboxBackend` → 原 `GeneratedExperimentExecutor` 的 prepare/admit/execute，
使用同一 `TrustedProbeRegistry` / `TrustedCriteriaRegistry`；候选与产品请求不能选择 daemon 或颁发隔离 authority。
这是已存在的透传代码，不是实际 live 配置已落盘或 probe 已注册的声明。

| 原字段 / profile 路径 | 本固定包的要求 / 当前事实 |
| --- | --- |
| `domain/protocol` → `IsolationConfiguration.endpoint` | 目标 `127.0.0.1:8099` / `http` → `http://127.0.0.1:8099`；实际服务尚未创建/确认 |
| `instance_id` | 随后本次新 server 的完整64位ID；当前 UNKNOWN，不填占位值充当真实配置 |
| `runtime_profile` | 原约定要求`git:15de4959646df264530b978dfde9152552b9a76b:deploy/opensandbox/at07.config.toml`；前组合为b480；须实际核对服务加载的438fe…同字节配置，当前实际 profile UNKNOWN，不伪造已加载值 |
| `environment` | canonical `image=python@sha256:229a2c5bfa27522db7815ea81f9bed70af17ccb9de9fc7ad142b1877b5830d36`、`image_digest=sha256:229a2c5bfa27522db7815ea81f9bed70af17ccb9de9fc7ad142b1877b5830d36`，原3.12/SDK1.1.0/opensandbox字段，`dependencies=[]`；最终15de锁为上文完整87b…，只能匹配这个实际受测锁 |
| `resources: BackendProfile` | 明确1 CPU/512MiB/180s/30s/1048576 bytes/**process_limit=128**/原network.default=deny；默认process_limit=16不能省略后误当128 |
| `server_process_limit/network_deny/use_server_proxy` | 128 / true / true；pids必须由同次实际server配置和压力观测确认，不由 SDK create 参数宣称 |
| `docker_export: DockerExportConfiguration` | 原mode=`docker-paused-archive-v1`、固定npipe endpoint、29.5.3/API1.52、`request_timeout_seconds=10`；本次daemon只读观察见21:44，但完整实际配置尚未生成，实际API不匹配STOP，无绑定保持None/拒绝 |
| `probes: tuple[IsolationProbeRecord,...]` | 当前无本最终组合的真实通过档；必须随后实际全项通过并独立审核才可注入，不能复制旧档或把JSON自报布尔当事实 |

target IPv4当前 UNKNOWN，只能在授权后读取本次新target实际IP。旧离线示例的
`UNBOUND-NOT-RUN`、`172.17.0.2` 和review-only ID是历史样本，不进入新真实配置。

另一受支持 transport 为 `unix:///var/run/docker.sock`，仍须同一个已绑定 Linux daemon；
不接受 TCP、任意 socket 路径或 `DOCKER_HOST` 覆盖。真实服务 instance 为完整64位container ID，
preflight 在 SDK create 之前复核 daemon版本/API/ID/Linux、固定server image和loopback宿主8099→容器8090绑定。
历史b480 `at07_live.docker_read` 继承默认CLI路由，不能靠一次version匹配补足此缺口。
后继B SOURCE已按上文硬绑定reader及前置核对，路由取自原configuration，不增加可由候选覆盖的CLI全局参数。
实际运行仍须使用上文已核对的15de+c84精确installed组合，确认server使用同Engine；无法确认就SDKcreate前STOP。
下列 `$taskFinalPython` 仅对应已核对的 `C:/r1i/successor-2018/r2/venv/Scripts/python.exe`，并不授权调用，
不能继续用I前组合1855的python执行新代码。

```powershell
& $taskFinalPython -m orchestration.experiments.at07 prepare --configuration $taskConfigurationFile --server-config $taskServerConfig --probe-id $taskProbeId --target-ipv4 $taskTargetIPv4 --archive-root $taskEvidenceRoot
& $taskFinalPython -m orchestration.experiments.at07 review --result "$taskEvidenceRoot/$taskProbeId/result.json"
```

以上只是原CLI的命令格式，除安装路径外其他运行变量尚未赋实际值；本次未生成真实configuration/profile/probe或授权记录，
测试中的inert preparation始终与真实运行输入分开。
`$taskServerConfig` 须对应随后最终集成SOURCE原blob；不能把I前组合的配置/路径当成新installed验收。
输出只有固定probe源码、配置副本和 NOT_RUN 诊断。目录不可重用。Mock/replay/partial/unknown不会产生verified记录，
完整 inert fixture 可覆盖实际判据的分支，但不会成为运行事实；`unverified_record()`始终
`verified=False,passed=False,process_limit=False,export_bounded=False`。

## 历史一次执行顺序（裸CLI/父env示例不可直接执行）

此段保留原准备顺序和未知效果/收尾限制；外层命令以上文当前审核模板与同ID保留条件为准，
这里的裸docker与父shell `$env:` 示例不构成当前可执行路线或授权。原runner参数形式保留，不在本次调用。

以下命令本轮 **全部 NOT_RUN**。执行者先写下授权引用、最终核心/产品SOURCE、私有installed环境、唯一probe-id、
允许的宿主基础设施边界与600秒停止时间；同一授权不允许重试第二次create。
**第0步：固定组合完整离线/installed 输入验收与单独真实授权未齐全时，停止在这里。**
SOURCE 中的实现和这份文档不构成授权；不能通过CLI风险接受参数解除该停止。
未来执行命令的相对 `deploy/opensandbox/...` 路径须来自随后最终集成SOURCE同字节私有 COPY，
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
& $taskFinalPython -m orchestration.experiments.at07_live --execute-separately-authorized-probe --authorization-ref $taskAuthorizationRef --accept-disclosed-infrastructure-limits --prepared-root "C:/morph-r1/at07/evidence/$taskProbeId" --service-key-file $taskServiceKey --canary-directory "C:/morph-r1/at07/$taskProbeId/canary"
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
   **此全删路线保留为历史/获准全销毁路径；删server后重建不能继承旧probe。**
   后续若用户明确批准全PASS的同ID停止保留选项，则按上文仅删除target、server停止保留，
   原runner cleanup/host-after/result/review不改；cache实际归属与消失必须另有原观察，不由cleanup布尔推断。

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
以上为原退出提醒；当前专项授权已实际接纳，但本次创建前STOP且原窗口已结束，所以AT07仍NOT_RUN，不能重复索同一批准或凭诊断成功恢复执行。
