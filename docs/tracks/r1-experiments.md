# R1 B · 2026-10-03 18:09 后继：Poisson 离线契约审查

Task `task_9ebbae6e5f3b` / Dispatch `ctx_85c678574200`；原 B Owner、worktree、
`songconmaisaix31-design/morph-r1-experiments-1003` 分支不变。依据主控治理
`9f42dfea066648b198d78877c8bdd9a9a55c8378` 的当前入口及18:09/18:05和Spec§14.2/14.4，
新增[可审查 Poisson 草案](../experiments/l2-poisson-review.md)，只改该稿和本短报告。

原 B SOURCE `5769005b09f1b756c94fdad0649a6b74690c0ca9` / REPORT
`5aebd2eb7af774b3dc496ad9620548f6e7852e09` 保留；当前唯一核心冻结 SOURCE
`b480fca1b10a0b6a9c93f0d1801d38f267662461` 不变。本段所在后继 commit 为 docs-only REPORT，
exact SHA 由终端交付，不作为新业务 SOURCE，不复写下方历史 / 首失败。

已静态定位 HostConfig → 原 GeneratedHostSettings / registry → 正式 MCP prepare / admit / run →
原 executor / raw archive / evaluator → 独立复核 / feedback 与原消费采用链。
EvaluationCriteria 已由 EvaluationSpec / poisson_reference_v1 提供；n/容差默认值只是未批准参考。
数值一致不证明求解方法、训练测试独立或改进；有效负结论可贡献 / 降温，但 failed 源代码不得伪造 adoption。
真实后续使用须原新任务本地再验证、源字节消费、fenced apply 与原 receipt，读文档不能替代。
两次短契约 Handoff 已发主控；未扩写评价器、业务 / 测试 / 锁 / 部署 / AOCI 或 P/F 文件。

本轮验证仅 raw Git 静态读取、docs diff、普通 commit/push `[skip ci]`、clean-tree / remote exact 核对。
原110 PASS / 210 PASS / Q65及其日志身份在草案中区分列明，**本轮未重跑测试或安装**。
治理18:09观察核心CI37114395256 Linux全门success、Windows当时运行；本轮不刷新 / 不宣称组合通过。
原OpenCode首请求Insufficient Balance、原ctx settled failed、Codex首readiness timeout保留；不重试 / 换计费入口。
正式材料导入、科学native、候选执行、实际复核 / 贡献 / 采用、AT07和L2均 **NOT_RUN**；
用量 / 费用 **UNKNOWN**，P受保护树 / human TTY receipt未触碰，不称MVP/R1完成。
独立I最后仅普通合本docs，合并保留`[skip ci]`，不再触发CI。

---

# R1 B · 2026-10-03 后继：受信 Docker 冻结导出

仍是 Task `task_a8533b909675` / Dispatch `ctx_bd976e22265e`，原 B Owner/worktree/branch。
后继 SOURCE **`5769005b09f1b756c94fdad0649a6b74690c0ca9`** 普通 commit/push，远端精确核对一致。
父 REPORT `7a6c5094c7235b1a992e0eaa8d688b08fa0fd64b`、其 SOURCE
`296ec298a23eea54f76e8c874aed551487a2999a` 及下方全部首失败保留；没有重写历史。
本段和授权包/来源调查/新增原始输出为单独 docs-only REPORT。

当前 **PREPARED_UNVERIFIED；真实 AT07 / L2 NOT_RUN**。已交付
[具体授权包](../experiments/at07-authorization.md) 与
[固定来源、实现契约和限制](../experiments/at07-export-feasibility.md)。
官方 SDK 原 pause/resume 生命周期与官方 Docker SDK7.2.0 npipe/Unix transport 读取宿主
Engine HEAD/GET archive；导出期间 main/egress 都冻结，逐层拒绝 symlink/特殊类型，
只接受有界单个普通 tar 成员，不在宿主提取、不执行容器 helper。
原 `OpenSandboxSession` / executor / result / TaskLedger / finalization 继续复用，没有新证明或调度设施。

新 `DockerExportConfiguration` 进入原 `IsolationConfiguration`：mode固定
`docker-paused-archive-v1`；endpoint仅固定npipe/Unix；真实daemon ID；Engine固定29.5.3/API1.52；
request_timeout固定10秒。SDK create前核对实际daemon/server完整ID/image/loopback端点，执行前绑定同次owned pair。
未配置默认None、旧probe、变更任何绑定或控制面未知都拒绝；实现支持不等于真实probe verified。
AT07的 `unverified_record` 始终False，mock/partial/unknown不能由工具升级为隔离或科研权威。

明确纠正早期只读runtime假设：固定上游挂载 `/opt/opensandbox:rw`。仅接受根外的原服务管理local volume、
恰好本次main/egress两个使用者、两者冻结；拒绝额外挂载/第三使用者。文件判断来自受信Engine，
不信任候选可能修改的runtime/execd。PathStat没有nlink事实，不声称inode别名完全排除；
每次成功导出均原SDK pause→Docker只读HEAD/GET→原SDK resume；finally仅在只读inspect确认两者确实暂停时恢复。
最终导出也恢复，不保持暂停到销毁；pause异常可在确认已暂停后尝试一次resume，原unknown仍保留。
不声称多文件同一快照；一次待完成底层读取可能多占一个transport timeout，不声称硬实时。
pause/resume/stream未知保留unknown并停止，不重POST、不降级为missing_artifact或退回宿主执行。
当前保存small成功的frozen-export观测及result分项/异常/cleanup，没有逐次pause/resume响应转录；
报告不把缺失的运行数据写成PASS，具体各分支/记录范围已在授权包明确。

## 后继离线证据

主控串行窗口内，B自有COPY `.venv` / CPython3.13.13；进程局部BLAS线程数1。
唯一新runtime依赖 `docker==7.2.0`，原锁其他包版本不变；官方Apache-2.0与pywin32许可已记NOTICE。
当前 `poetry.lock` SHA256 **`8558e9e065da381466d9c188bc87a88fcaf09a3b367455eb8267c0bb4c9fcc98`**。
Poetry2.3.2仅在B `.runtime/uv-lock-tools` 私有工具环境解析锁；没有系统pip、他人环境或全局配置修改。

| 原始输出（追加于at07-evidence） | 命令 / 结果 |
| --- | --- |
| `frozen-install-first.txt` | `uv pip install --python .venv/Scripts/python.exe --no-deps docker==7.2.0`，安装唯一runtime新包；UV_LINK_MODE=copy |
| `frozen-lock-first.txt` | `uv tool run --from poetry==2.3.2 poetry lock`，B私有UV工具/缓存路径，43个临时工具依赖；原锁其他版本不变 |
| `frozen-targeted-first.txt` | frozen_export、at07、at07_export、generated_configuration：**110 PASS / 3.76s** |
| `frozen-experiments-first.txt` | 全部 `tests/experiments`：**210 PASS / 27.50s** |
| `frozen-strict-first.txt` | **1 error / 140 source files**，Returning Any from bool；首RED保留 |
| `frozen-strict-fixed.txt` | **PASS / 140 source files**；已校验bool后增加类型cast，没有运行行为改动 |
| `frozen-environment-check.txt` | `uv pip check --python .venv/Scripts/python.exe`：**104 packages compatible** |

原断言命令：

```powershell
.venv/Scripts/python.exe -m pytest tests/experiments/test_frozen_export.py tests/experiments/test_at07.py tests/experiments/test_at07_export.py tests/experiments/test_generated_configuration.py -q --tb=short
.venv/Scripts/python.exe -m pytest tests/experiments -q --tb=short
.venv/Scripts/python.exe tools/typecheck.py
uv pip check --python .venv/Scripts/python.exe
```

冻结测试的Daemon/SDK均为inert fixture，阻断真实process/network；positive有真实adapter构造及SDK参数capture，
并非只测拒绝。覆盖暂停期间替换、祖先/leaf symlink、恶意tar/特殊文件/溢出/期限、额外volume使用者、
Engine身份错配、暂停/恢复未知与不重放、错误恢复ID不得kill、附着session拒绝、旧配置不得admit/direct-create。
只在宿主解析固定探针源码；没有实际Engine/socket请求、候选、科学、模型、probe或sandbox生命周期操作。
strict最后修改仅类型cast，适用运行测试此前通过；未为这项类型修复重复重回归。

## 接线、验收与真实剩余限制

已向A原Owner `ctx_4c6085d9f9d8` 及主控交SOURCE/API：只在 `GeneratedHostSettings` 增
同型 `docker_export=None`，继续由 `HostConfig.generated_experiments` 原受信嵌套承载，
原factory透传 `LocalCpuSandboxBackend(docker_export=self.settings.docker_export)`。
不新增HostConfig顶层重复权威，不让候选/MCP请求选择daemon；真实Engine/ID未知时维持None。
B未修改A/C/P/Q文件，A已ACK此最小契约。

Q在上一阶段的3项旧fixture失败仍保留（详见下方首RED）；本SOURCE没有宣称Q新全绿。
新精确配置须由Q独立正负复核，最终固定组合完整离线回归/installed输入由主控串行排队。
本轮没有fullsuite/build/installed产品验证；测试窗口已释放，不把owner210项替代组合验收。
本机只读CLI版本为29.5.3；实际Engine/daemon仍UNKNOWN，未启动Docker/WSL/service、未pull/build镜像。
sidecar/cache资源限额不受支持、总峰值UNKNOWN、动态0.0.0.0端口和既有DNS健康流量的后续范围决定保留。
真实无害AT07需后续单独明确授权且同档全部通过，再讨论一次L2；没有L3/规模化/跨宿主授权。
旧C系统误装automatic approval blocked-by-policy边界保留，没有环境清理。

---

# R1 B · 2026-10-03 AT-07 准备与原子导出边界（历史阶段）

Task `task_a8533b909675` / Dispatch `ctx_bd976e22265e`，原 B Owner、worktree 与分支。
普通精确合并核心 REPORT `08b31b39c075571ffd247e2b591d657ce09b6b34`（SOURCE
`2c63bc7c9e49edff28e26f5930a22d0415fadd65`）为 fast-forward；没有 rebase/cherry-pick/force，
此前 B source/report、SQLite 首 RED 与 C Windows 首 RED 均保留。
本阶段 SOURCE **`296ec298a23eea54f76e8c874aed551487a2999a`** 已普通 commit/push，远端核对一致。
文档单独 REPORT；这是原子导出尚不支持时的准备/拒绝阶段，不能据此宣称 R1 退出通过。

## 准备交付与当前边界

交付 [AT-07 授权包](../experiments/at07-authorization.md)、独立固定 server/egress Compose/TOML、
无害 payload/受控目标，以及原官方 SDK 上的 prepare/review/operator 入口。
明确 SDK1.1.0、server/execd/实验/egress digest、资源/时间/创建数量/清理 ID 范围与预期证据位置。
只有 parse/compile 与 inert SDK/HTTP transport 测试；没有把 payload 在宿主执行。
原 `IsolationConfiguration`、`IsolationProbeRecord`、`TrustedProbeRegistry`、session/finalize 生命周期继续复用，
没有第二 Executor/调度器/Attempt/Manifest/Hash/完成证明设施。

**真实 AT-07/L2 NOT_RUN；执行准备 NOT_READY。** 原 SDK 普通文件下载缺乏原子 root/no-follow 保证，
目录类型检查后、stream open 前可以被残留进程替换。静态路径/祖先 symlink/字节限制的加固不能消除该竞争。
AT07诊断强制 export unsupported；工具从不创建 verified/passed registry 记录；真实入口在Docker/key/SDK访问前拒绝。
生产声明和原 generated live factory 的准入也必须拒绝旧/手填 PASS 绕过；此项本轮后续验证记录见下表。

[有界官方 API 调查](../experiments/at07-export-feasibility.md) 给出精确 source/API/版本：
原 SDK/container pause 加受信 Docker Engine archive 可作为后继适配基础，暂停后不能继续依赖已冻结的 execd。
Windows npipe transport、全部祖先/挂载/有界 tar 与硬链接语义仍须原 Owner 实现和独立审查。
公开 RC 的 publish_host 修复不等于原子导出修复。没有把未实现方案、旧运行或 Mock 视为 live 能力。

## 本轮确定性证据

以下原始输出追加保存于 [at07-evidence](../experiments/at07-evidence/)，不覆盖或删除首失败。

| 阶段 | 原输出 | 真实结果 |
| --- | --- | --- |
| 原适配静态导出负例首测 | `export-first-red.txt` | 10 FAIL / 1 PASS，2.57s |
| 初版准备/修复单测 | `targeted-first.txt` | 33 PASS，0.66s |
| 当时适用 B+Q 边界 | `experiments-q-first.txt` | 227 PASS，46.96s |
| SDK wire fixture 首次错误 | `targeted-wire.txt` | 1 FAIL / 38 PASS，0.67s；误把传入 limit 预期为 Range，首失败保留 |
| 后续当时版本 B+Q | `experiments-q-final.txt` | 233 PASS，38.05s |
| metadata/open 竞争首测 | `export-toctou-first-red.txt` | 1 FAIL，0.46s；inert fake 范围外 bytes 仍被读取，诊断曾错误 passed |
| 导出 unsupported 后 | `targeted-toctou-fixed.txt` | 41 PASS，0.52s |
| 当时 B+Q 全部适用项 | `experiments-q-export-unsupported.txt` | 235 PASS，35.82s；这是能力声明同步前的中间结果 |
| 同时 strict | `strict-export-unsupported.txt` | PASS，139 source files |
| 能力声明与字节范围首测 | `export-capability-range-first-red.txt` | 5 FAIL / 13 PASS，0.68s；包括原声明错误及缺少降级接口 |
| SOURCE对应B定向单测 | `export-capability-range-fixed.txt` | 66 PASS，0.66s；两个AT07文件+generated_configuration |
| SOURCE对应B+Q原断言 | `experiments-q-failclosed-stage.txt` | **3 FAIL / 235 PASS，39.65s** |
| SOURCE对应strict | `strict-failclosed-stage.txt` | PASS，139 source files |

进一步只读固定 execd 发现 offset/limit 是行数。最终 byte stream 使用显式
`Range: bytes=0-<limit>`，宿主独立累计限制保留；中间 fixture 修正不能被写成最终实现的证据。
当前能力一致拒绝与Range修复已覆盖；三项Q失败均来自原
`test_b_configured_sdk_boundary.py`：SDK正向和两项prepare-mutation的原前置admit成功断言，
现在被真实unsupported能力门拒绝。**未删除、改写、skip这些Q断言，也未宣称全门已绿。**
B自己的配置绑定fixture显式模拟未来已实现的export能力，以保留非空SDK capture正向；
另两项默认生产负例证实完整手填probe仍不能admit/direct-create，prepared支持降级也被拒绝。
这些mock不成为当前生产可执行性或AT07证明。

主控已授权同B继续实现原SDK pause+受信Engine archive的最小后继，当前阶段先留证，
没有提前worker_done。Q等后继固定后由原Owner独立复核；实际AT07继续等待固定组合及单独授权。

实际适用回归命令（私有 `.venv/Scripts/python.exe`，进程局部 BLAS线程数1）：

```powershell
.venv/Scripts/python.exe -m pytest tests/experiments tests/integration/r1_security/test_b_configured_sdk_boundary.py tests/integration/r1_security/test_b_generated_boundaries.py tests/integration/r1_security/test_b_input_binding.py tests/integration/r1_security/test_b_mock_adoption.py tests/integration/r1_security/test_b_probe_configuration.py tests/integration/r1_security/test_b_sdk_configuration.py tests/integration/r1_security/test_b_store_admission_race.py tests/integration/r1_security/test_b_successor_authority.py -q
.venv/Scripts/python.exe tools/typecheck.py
```

测试为显式 mock/inert SDK capture；Q denyprocess/network conftest 保持开启，未修改 Q 文件。
真实探针 payload、候选、科学、模型、服务、sandbox create/run/destroy 均未执行。
没有本轮 fullsuite、build、install 或新依赖；固定组合 full offline/installed 仍由主控/I 排队完成。
保留 C 既有系统误装 automatic approval blocked-by-policy 的历史边界，没有执行环境清理。

## 只读调查的异常记录与限制

对既有上游 partial clone 查询旧 commit 时，Git 曾自动触发 lazy-fetch 和 auto packing；
立即中断该 owned 命令并报告主控，没有清理、回滚或覆盖 clone。
之后固定源码读取均设置**该进程内** `GIT_NO_LAZY_FETCH=1`；缺 blob 时只读官方公开 HTTP 源。
没有更改仓库或全局 Git 配置。此事件不能描述成 clone 字节完全未变。

当前配置还有明确基础设施边界：egress/cache 容器限额 unsupported、总峰值 unknown；
固定 server 动态端口0.0.0.0及既有 resolver 健康流量须后续范围确认。
这些与原子导出硬停止分开；负责人风险接受开关不能解除 export unsupported。
本包的512MiB/128pids/stdlib profile 不授权其他 image/依赖/资源档，独立真实AT07后才可能形成新 registry 事实。

---

# R1 B · 2026-10-03 后继：SQLite 配置并发初始化

本轮为新 Task `task_eff1006355f8` / Dispatch `ctx_37f15746c078`，仍由原 B Owner 在原
worktree/分支处理。此前 SOURCE `5faafe41b1732c83d165251600b688444186c702`、REPORT
`6ec8c7441e07824bb2b7940c1c93e590200f84ab` 及全部首次失败保留。
本轮 SOURCE **`230d283848c0879ff9c349096548d3810c4b1954`** 已普通 commit/push，远端核对一致。
本节是单独的后继报告，不把后来通过用于撤销原 CI 失败。

## 原失败与根因

[C Windows CI run 37051183488 / job 110984695266](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/37051183488/job/110984695266)
的 API 确认 `run_attempt=1`、HEAD `8bc4c282ed4db8e2be0798509b28d984240b3a06`、
`conclusion=failure`。下载原日志到本地
`.runtime/ci-37051183488-job-110984695266-first.txt`，首次为
**1 failed / 1348 passed / 5 skipped / 75 warnings，1456.91s**。

原 `tests/swarm/test_worker_evomap.py:97` 的三个 SpawnProcess 退出码不为全零：
SpawnProcess-17 在 `LocalAssetStore.__init__` 原 `store.py:100` 插入 `asset_store_settings`
时发生 `UNIQUE constraint failed: asset_store_settings.name`；其他进程随后在屏障处
`BrokenBarrierError`。本地原测试 blob `8470c3069c614e7258795f6eacb37e3e228f9aea`
与该 CI 提交完全一致，未改 C 测试、断言或等待时间。

原代码在 `executescript` 完成后先查询设置，首次 INSERT 才隐式开始写事务；因此两个初始化者
可能同时看到缺失配置。相同设置也会撞唯一键，冲突设置的失败方则收到数据库异常，而非既有的
明确拒绝。A/B 之前偶然通过不覆盖这条真实竞争证据。

## 最小修复与回归

生产变更仅 `local_assets/store.py` 三行：在原连接、原事务上下文中，读配置前执行
`BEGIN IMMEDIATE`。两个配置行、旧库迁移检查与不可变触发器创建在同一事务内提交或回滚；
竞争方取得锁后读取已提交的一整组绑定。保留原 10 秒 SQLite 等待时间、WAL、immutable
UPDATE/DELETE triggers、live/mock 隔离以及 populated legacy store 不能转换 mock 的拒绝。
没有忽略完整性异常、覆盖旧值、增加自动重试或引入调度设施。

新增 `tests/local_assets/test_store_initialization.py` 使用同一 Python 进程的两条线程、真实独立
SQLite 连接和外部写锁，以事务开始屏障固定交错；同时覆盖隐式和显式 BEGIN，不替换查询结果。
测试禁止启动进程和网络，也不执行候选。相同的四个并发断言在旧源码上首次 **4 FAIL / 1 PASS，
2.36s**（`.runtime/sqlite-initialization-first-red.txt`），修复后 **5 PASS，2.00s**
（`.runtime/sqlite-initialization-fixed-first.txt`）：

- 相同 live、相同 mock 配置的两个初始化者都成功。
- 模式冲突或 fixture 路径冲突时，仅一个完整绑定成功，另一方收到 `asset_store_provenance_conflict`；
  重开仍拒绝失败方，持久配置没有混合，UPDATE/DELETE 仍被不可变触发器拒绝。
- 有资产的旧库拒绝转换 mock，失败不留下配置行或改变原资产；之后默认 live 仍可初始化。

命令：`.venv/Scripts/python.exe -m pytest tests/local_assets/test_store_initialization.py -q --tb=short`。
使用原 B 私有 `.venv`，只设置进程局部 BLAS 线程数为 1；没有修改借用/全局环境。
Q 在旧 installed `cc2e722` 上独立首次复现 **4 FAIL，1.85s**，保存
`installed-cc2e722-store-race4-first.txt`；随后对精确 SOURCE `230d283` 的 `git archive`
执行同一 4 项断言加原 B 68 项，报告 **72 PASS，10.05s**。这是 Q 独立所有者证据，
没有替换其原 installed 包，也没有冒充本轮多进程回归已通过。
主控于 20:17:55 UTC 在 P/F 释放后授予 B 串行窗口，完成一次适用回归后归还给主控/P：

| 原命令 / 范围 | 本轮首次结果 |
|---|---|
| `python -m pytest tests/swarm/test_worker_evomap.py -q --tb=short` | **1 FAIL / 21 PASS，279.33s** |
| `python -m pytest tests/local_assets` 加下列三项原资产断言，`-q --tb=short` | **69 PASS，214.46s** |
| `python tools/typecheck.py` | **PASS，130 source files** |

三个原断言位于 `tests/swarm/test_assets.py`：
`test_report_expiry_and_immutable_evidence`、
`test_same_report_concurrent_promotion_is_consumed_once`、
`test_approved_fetch_applicability_injection_actual_execution_and_adoption`。
所有命令均用本轨 `.venv/Scripts/python.exe`；没有修改任何 `tests/swarm/**`。
原输出分别保留 `.runtime/sqlite-worker-evomap-first.txt`、
`.runtime/sqlite-assets-boundaries-first.txt`、`.runtime/sqlite-strict-first.txt`。

### 后继本地首次超时仍是 RED

`test_worker_evomap.py:97` 的新失败是原 180 秒截止时退出码 **`[0, None, None]`**，
没有原 UNIQUE 或 BrokenBarrier traceback。保留原 180/60 秒和 `[0,0,0]` 断言，没有盲重跑。
这次未完成的两个进程由原测试 finally 终止，不等于测试通过或全部任务完成。

仅复制原 fixture 的 `data` 至 `.runtime/sqlite-worker-first-artifacts`（不复制外层 credential
文件），在副本以 SQLite `mode=ro` + `query_only` 诊断，原文件不改。四个 promoted 审计对应
data-0/2/3/4 completed，data-1 claimed 且预算 reservation pending、tokens unknown，data-5
available；原资产库 4 assets/4 reports/4 approvals、0 consumptions/0 adoptions。builder-0
回执为 mock、calls=1、state=idle；其余没有完成回执。

时间记录：data-3/4 约 20:19:50 UTC 提交完成，data-0/2 约 20:21:13–16 完成，data-1
约 20:21:34 仍在 claimed；四次 MockTransport HTTP `elapsed_seconds` 均不足 0.001 秒。
reservation→settlement 约 23–27 秒，settlement→task completion 约 45–57 秒。可确定构造
已通过且有大量耗时位于 mock HTTP 之外；缺少各子命令计时，**不能确定 Node/Git/锁或其他
阶段的根因**。B 与 C 精确提交的 worker_loop 及原测试一致，未因猜测修改 C 领域。
诊断摘要保留 `.runtime/sqlite-worker-first-diagnostic.json`。

本节首次记录为 REPORT `bb259112d240a5e13b2aa6ea437617406d978dc3`，当时独立 Windows CI
仍在运行，尚未发送成功回执。本地原 worker 门未通过的事实保留；副本预算 breaker 为 null，
没有记录到熔断，但这不足以排除所有停滞原因。后来的独立成功不会解释或撤销此首失败。

### 精确 SOURCE 的独立 CI 继证

[CI 37059454013](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/37059454013)
API 确认 HEAD 为 `230d283848c0879ff9c349096548d3810c4b1954`、`run_attempt=1`、
最终 `conclusion=success`，没有为取得通过而重跑此 CI。

| 独立 runner | 原 full pytest 结果 | 后续工程检查 |
|---|---|---|
| [Windows job 111012194553](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/37059454013/job/111012194553) | **1295 PASS / 5 SKIP，75 warnings，1030.30s** | strict 130、build、官方 GEP SDK、非 editable wheel/资源/Node 验证 PASS |
| [Linux job 111012194917](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/37059454013/job/111012194917) | **1294 PASS / 6 SKIP，75 warnings，533.81s** | strict 130、build、官方 GEP SDK、非 editable wheel/资源/Node 验证 PASS |

Windows 于 20:34:53 UTC 完成。实际原命令为 `uv tool run poetry run python -m pytest -q`，
包含未修改的原 `test_worker_evomap.py`，没有针对它新增 skip 或弱化 `[0,0,0]`/时间阈值。
`python -I tools/check_distribution.py --site-dir tools/.wheel-site --check-node` 两边输出
`scope=contract_local`、`packages_from_wheel=13`、`resources_present=true`、
`installed_verifier=passed`、`node_dependency_check=true`。
下载的完整原日志保留 `.runtime/ci-37059454013-windows-complete.txt` 与
`.runtime/ci-37059454013-linux-complete.txt`。

原 Windows CI 的 UNIQUE 首失败、B 确定性首 4 RED、本地后继 180 秒首超时及此独立通过
是不同记录；最终仅以精确 SOURCE 的新独立结果确认本修复工程门槛。没有断言本地超时已修复、
没有将其原因归于未经证实的机器负载，也没有宣称科研或实时隔离验收。原 worktree/私有环境/
本地证据全部保留；最终组合由主控与 I 继续验收。

真实模型、科研候选执行、真实沙箱、探针、AT-07/L2 仍 **NOT_RUN**。本修复只处理既有本地
资产存储的原子初始化，不把 mock 或 SQLite 并发检查转换成科学/隔离验收。

---

# R1 B · 2026-10-03 恢复后的配置、结果与继承返修

当前依据 `docs/source/Morphogenesis_Research_Swarm_Spec_v1.0_2026-10-02.md` 的 FR-15 至 FR-20；
下方旧报告的 FR-26 标记只保留作历史，不替代当前 Spec。

本轮沿用原 B worktree/分支与所有权。`d175f7e2f8c3ff41a1ac8a2a4958c68acf57e275`
**NOT_ACCEPTED**：Q 精确归档原 29 项是 **21 PASS / 8 FAIL**，后补输入绑定是
**1 PASS / 7 FAIL**。下文历史报告的“修正全部”以及 18/102 PASS 只描述当时窄范围，
不覆盖这些后发现的问题；原提交、Q 原始 RED 和 AT-07/L2 NOT_RUN 均保留。

本轮源码阶段：`e8e16a5b9e755a94f8587b76ba9fc288f218b8af`（配置绑定与原报告）；
`d0c834fd381fc292443bf85c5ce1e91043143516`（隔离 fixture 继承模式）；
`56b8db589ee04bcc41652bb5e38793a1216f9a1a`（安装包内固定输出后端）；
`2d50d08811aa2337b9c0166dc114513e292bce1f`（复用时重读存档、应用前后围栏与回滚）；
最终 SOURCE **`5faafe41b1732c83d165251600b688444186c702`**（保留危险代码的结构化拒绝报告）。
每阶段均普通 commit/push 并核对远端精确 SHA。报告单独提交，不用报告 SHA 代替 SOURCE。

## 本轮修改与权威边界

- 探针比较完整有效配置：规范化 repository@sha256 镜像及实际 `image_digest`、Python/SDK、
  dependency lock、endpoint、backend instance/runtime profile、网络、全部资源和服务端进程限制。
  `prepare` 保存快照，`admit` 重算当前配置和候选字节，`LocalCpuSandboxBackend.create` 独立拒绝
  未验证或不支持的设置。重复 probe ID 不同记录拒绝；完全相同记录可重复提供。
- SDK 1.1.0 没有进程限制创建参数，默认 `process_limit=False`。只有宿主配置的、与探针精确
  匹配的服务端固定进程限制才可声明支持；未实际探针的部署不能据测试夹具启用。SDK 请求使用
  `NetworkPolicy(defaultAction="deny")`，固定镜像传 `repository@sha256`，没有实际 SDK 调用。
- 候选验证绑定已发布 Candidate 的 asset ID、base revision、scope、变更字节、ResearchClaim 和
  冻结条件。code/data 重名、重复 data、运行器保留名、输入总大小超限拒绝。发布先产生 asset ID，
  再写入冻结计划，候选地址不包含自身 ID，避免循环身份。
- `record_generated_observation` 写入原 `research_reports`，`read_generated_observation` 只读
  核对原 archive/plan/context/candidate/criteria approval 并重算；没有新完成账本。判据批准在
  执行前冻结，晚批准不能追认旧输出；静态 `approve_generated` 不是科学评价或贡献接受。
- `source_attempt` 是当前执行任务的原始 AttemptId，`source_fencing_token` 是该执行 token；
  `Candidate.attempt` 单独标记原作者。A 绑定原 TaskLedger/audit/completion；C 独立复核这些事实，
  科学贡献在 B 恒为 proposed。
- 复用原 AssetConsumer/AssetApplicator/TaskLedger.submit/AdoptionReceipt。默认 live 仍拒绝
  mock 科学结果。显式 mock 模式只用于专用 fixture 项目：资产根和应用目标受 workspace 范围
  约束，同一 SQLite 库保存不可变的模式/fixture 路径配置，跨模式重开拒绝，消费与回执标 mock。
  旧无 provenance 的回执仍可读且保持原 JSON 形状；旧 registered/literal 准入语义不放宽。
- `GeneratedFixtureBackend` 是安装包内固定输出适配器，整个 session 只保存内存字节，禁止
  候选解释、进程及网络。宿主明确选择 mock 并提供输出；它的 fixture 探针记录不能授权真实后端。
- 发现 Q 在 `56b8db5` 上的原始输出/判据/环境存档变更仍能沿缓存 PASS 复用后，保留其
  **9 PASS / 3 FAIL**；B 原断言首次也 **2 FAIL**。现在每次生成成果准入、应用前和应用后，
  都用宿主注入的同一 `generated_criteria` 重读原存档。注册表缺失/变化拒绝，应用后发现变更
  使用原快照回滚；已存历史回执不抹除，也不因此声称当前存档仍有效。

## 已交给 A/C/P 的可调用接口

```python
executor = GeneratedExperimentExecutor(backend, probe_registry=host_probes,
                                       criteria_registry=host_criteria)
preparation = executor.prepare(plan, files, data)
executor.admit(preparation)
result = executor.execute(plan, context, files, archive_root, data)
result = read_generated_result(archive_root, context.run_id,
                               expected_plan=plan, expected_context=context)
diagnostic = executor.evaluate(result, context)  # 只返回 diagnostic/proposed。
# 以下函数位于 local_assets.generated_validation。
payload = generated_result_payload(result, criteria_registry=host_criteria)
# report 阶段就是这个原 research_reports 写入入口，不另建报告事实层。
report = record_generated_observation(store, asset_id, archive_root=archive_root,
    plan=plan, context=context, purpose="original", criteria_registry=host_criteria,
    assert_owned=assert_owned, source_swarm_id=swarm_id,
    source_attempt=execution_attempt, source_fencing_token=context.fencing_token)
verified = read_generated_observation(report, criteria_registry=host_criteria)
```

`result_json` 固定键：`schema_version`, `effect_state`, `execution_state`, `scientific_verdict`,
`provenance`, `sandbox_id`, `experiment_result`, `generated_assessment`, `criteria_approval`,
`usage`, `cost_usd`。使用量/费用保持 null。`generated_conditions(plan)` 使用冻结代码、数据、环境、
参数、种子、判据和条件，排除 task/run/asset ID；复现和继承使用新任务计划且保留同一科学条件。

正式安装工厂可用 `GeneratedFixtureBackend(environment=..., resources=..., output=固定宿主字节,
instance_id=..., outcome=...)`，执行器接其 `probe_registry`，来源保持 mock。
消费/应用使用原 `AssetConsumer.inject/execute/record_adoption` 与
`AssetApplicator(..., policy_version="generated-isolation-v1").prepare(...).apply(assert_owned)`。
mock store 需显式 `LocalAssetStore(..., research_provenance="mock", fixture_workspace=...,
generated_criteria=host_criteria)`；重开仍需注入相同的宿主判据。live 生成成果复用同样需
`generated_criteria`，报告只读路径仍直接使用 `read_generated_observation`。这些都是宿主配置，
不是工具参数或调用者传来的执行许可。

## 本轮阶段验证（L0/mock；不代替最终组合）

私有环境为本 worktree `.venv`，`uv venv --python C:/Python313/python.exe` 后只从本仓库未改动的
`poetry.lock` 导出固定版本，使用局部 `.runtime/uv-cache` 和 COPY 安装；未修改借用/全局环境。
`uv pip check --python .venv/Scripts/python.exe`：102 个安装包兼容。实际 SDK=1.1.0。

| 检查 | 本轮首次结果 |
|---|---|
| 原 Q 四文件 29 项，保留 Q 进程/网络禁止 conftest | 29 PASS，20.12s |
| Q 新输入绑定 8 + 配置截获 15 项，合法配置正例确实调用截获点 | 23 PASS，1.74s |
| Owner SDK 配置/变更/直接创建/快照 22 项 | 22 PASS，0.96s |
| 原动态领域 28 项 | 28 PASS，10.03s |
| 原资产报告写入/重读/围栏/晚批准/伪造/复现 12 项 | 12 PASS，2.94s |
| 原消费/本地再验证/受围栏应用/采用与模式边界 4 项 | 4 PASS，13.30s |
| mock/report/旧 JSON 合并检查 | 17 PASS，11.89s |
| 安装包内 fixture 后端 | 6 PASS，0.62s |
| 原始存档变更拒绝：不改首 RED 断言的返修复核 | 6 PASS，17.26s |
| 受围栏应用前/后变更与快照回滚 | 8 PASS，31.46s |

## 最终源码验证与第一失败

协调器于 18:38 UTC 授予 B 独占重型窗口；使用进程局部
`OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=MKL_NUM_THREADS=1`，所有安装/pytest/Node 顺序执行。
`npm ci --no-audit --no-fund --cache .runtime/npm-cache`：exit 0，99 packages；未修改锁文件。

领域首次命令 `python -m pytest tests/experiments tests/local_assets
tests/research/test_generated_candidate.py tests/research/test_case.py tests/swarm/test_assets.py -q --tb=short`
在 `2d50d08` 上 **244 PASS / 1 FAIL，175.84s**：已有危险代码测试要求结构化拒绝报告，
新增 Candidate 检查提前抛出 `dangerous_import`。保留 `.runtime/broad-domain-first.txt`；
`5faafe4` 保留原断言及安全拒绝，把静态失败与候选错误纳入拒绝报告。该文件重跑
**5 PASS，1.80s**；静态通过但候选绑定错误仍抛异常，失败报告不能批准。

`python tools/typecheck.py`：**PASS，130 source files**（`.runtime/strict-first.txt`）。
Q 的七个 B 安全文件在最终 SOURCE、私有 Python 下执行，原禁止进程/网络 conftest 仍启用：
**68 PASS，9.02s**（`.runtime/q-final-first.txt`），覆盖 29 原边界、23 配置/输入与 16 原链
mock 消费/存档/回滚检查；合法配置正例实际到达一次被截获的 SDK create，不是全拒绝空通过。
Q 独立精确 `2d50d08` 已报告 **68 PASS，10.28s**，属于其所有者证据，不混为 B 最终重跑。

最终同一领域命令在 SOURCE `5faafe4`：**245 PASS，345.21s**，exit 0
（`.runtime/broad-domain-final-first.txt`），包含旧注册案例、原 literal 资产验证/应用和新动态路径。
七个 Q 文件为 `test_b_generated_boundaries.py`, `test_b_successor_authority.py`,
`test_b_sdk_configuration.py`, `test_b_probe_configuration.py`, `test_b_input_binding.py`,
`test_b_configured_sdk_boundary.py`, `test_b_mock_adoption.py`；在 Q worktree 设置
`R1_SECURITY_SOURCE` 为 B 根，用 B `.venv/Scripts/python.exe -m pytest
tests/integration/r1_security/<上述文件> -q --tb=short` 执行，不修改 Q 文件或断言。

安装验证顺序（全部 exit 0）：

```powershell
uv build --wheel --out-dir .runtime/wheels --python .venv/Scripts/python.exe
uv pip install --python .venv/Scripts/python.exe --no-deps .runtime/wheels/morphogenesis-0.1.0-py3-none-any.whl
# 在 .runtime 工作目录执行：
../.venv/Scripts/python.exe -I installed_smoke.py
# 回到 B 根目录：
uv pip check --python .venv/Scripts/python.exe
```

wheel 共 195 项，检查无 `.runtime`/`.venv`/`node_modules`/测试/仓库文件；构建器关于仓内
cache 的通用提示未对应实际打包泄漏。`direct_url.json` 确认为 wheel 且非 editable；
`-I` 导入落在本私有 `.venv/Lib/site-packages`，没有导入测试 helper。固定输出适配器走
prepare/admit/execute/archive/read、静态准入与原 `research_reports` 写入/重读：**PASS**，
原报告 1、adoption 0、provenance mock、cost null；同时确认静态批准不能越过独立复现门槛。
smoke 全程禁止 `subprocess.Popen`、`os.system`、socket connect；候选仍是未执行的注释字节。
这里 GEP 使用确定性 fixture，正式 GEP/原消费链由上述领域回归覆盖，不将安装 smoke 说成
正式 MCP/HTTP/UI 验收。最终 `uv pip check`：**103 packages compatible**。

原始本轮命令输出保留在 `.runtime/*first.txt`；该目录是本地运行产物，不提交。Q 首 RED
保留在 Q 分支 `tests/integration/r1_security/evidence/b-d175f7e-{exact,input-binding}-first.txt`。
C 已报告其 SOURCE `38eae47e2961e10e9cf492fe99ea02f418d57dc9` 实际消费 B writer/reader 到
trusted/accept 与下一机会引用，generated 28 PASS（C 所有者证据，B 未冒充独立重跑）。
## 接线证据与剩余范围

A SOURCE `0bcb320e843839f5f043fccd9f705d9dd9b7299e` 已报告普通合入 B `2d50d08`，
实际正式服务 fixture 走 prepare/freeze/admit/executor/archive/audit/report/complete，及独立
review、后续 discover/choose/claim 与原消费/受围栏应用/mock adoption；A 的 7 项动态 fixture
通过属 A 所有者证据。最终 `5faafe4` 已交给 A/C/P/Q；B 未把他们的验证冒充自己重跑，未替代
独立 I 最终集成。B 重型窗口在全部进程退出后已明确归还协调器，报告与源码分开提交。

本交付完成 B 配置绑定、可信原报告与显式 fixture 原链返修的 `contract_local` 及私有安装
验证。全仓 full pytest、正式 MCP/HTTP/UI 安装验收由对应 Owner/集成轨负责，本轮 B
未执行。真实探针、科学运行、模型、真实沙箱、外部研究材料、Hub、部署及 L2 均 **NOT_RUN**；
AT-07 真实隔离证明仍未取得，默认真实后端保持拒绝。需要后续有授权的宿主真实探针确认精确
image/endpoint/instance/runtime/network/resources/process 限制，才可另立真实运行证据。
使用量与费用仍 unknown/null，mock 采用不代表真实科学贡献或 live 运行。

---

# 历史：R1 B · 动态候选、隔离执行、可信评价与真实继承（d175 之前的返修记录）

B 轨（长期 Owner，`morph-r1-experiments-1003`）交付动态 Python 候选实验的版本化契约、
隔离执行安全路径、可信三轴评价、成果准入与继承接线。首版 `fbee1e5` 被独立 Q 拒绝验收，
本返修修正全部阻断项；历史冻结核心 `7062a63` / 报告 `326fd8f` 与旧 `registered_case` /
`CaseId` / `ScientificCriteria` / `literal-files-v1` 字节等值语义保持不变，新能力以
`generated-experiment/v1` 版本化并存。

## 首版诚实纠正（不擦除）

首版 `tests/experiments/generated_helpers.py` 的 `MockGeneratedSession.run` 用
`subprocess.run([sys.executable, *argv[1:]])` 在宿主实际执行了候选（Poisson 求解器）以产生
输出；当时 98 passed 因此不能声称隔离路径通过。已删除该执行能力：fixture 现按计划 case
固定原始输出（`poisson_reference_output/wrong_output/scored_output`），mock 只写固定字节，
不 exec/eval/解释候选。首版提交与首失败历史原样保留于 Git。

## 信任边界（修复 Q 6 项 RED 的核心）

`EvaluationSpec.approved/approved_by` 与 `IsolationReport.verified/probe` 均为**仅展示**字段，
执行器/评价器从不据此授予最终结论或执行准入：

- 评价：`evaluation.evaluate` 只做宿主重算，**恒返回 `mode="diagnostic"`、`trusted=False`、`contribution="proposed"`**；
  最终科学结论由 `trusted.finalize_assessment` 仅在宿主 `TrustedCriteriaRegistry` 批准该 criteria
  版本（同版本不同 spec 构造 registry 时 `criteria_version_conflict` 拒绝，不静默覆盖）、执行 `succeeded`
  且 `remote_effect="known"` 时授予 `mode="final"`+`trusted=True`；诊断路径清 `trusted`、复位 `contribution`。
- 隔离：`GeneratedExperimentExecutor.admit` 只信宿主 `TrustedProbeRegistry`，**按 `proof_ref`（probe_id）+
  backend + declared 精确绑定**；report 的 `proof_ref` 为空/异值不能复用 record；mock/caller 的
  `verified=True` 不能放行。无证明 fail-closed，宿主从不执行候选。
- `read_generated_result` **总是**从原始输出重算评估（丢弃存档里伪造的 `accepted/final/trusted`），
  并要求 `outputs/output.json` 有 digest 绑定（`missing_durable_evidence`）、输入/data digest 与整计划绑定。

## 第二次返修（Q 扩展 suite + 真实 API 接线条件）

- 隔离证明绑定 `proof_ref`：`TrustedProbeRegistry.is_verified` 以 `probe_id` 为键并要求 report 的
  `proof_ref`、backend、`declared` 与 record 全等，空/异值引用拒绝（`test_registered_probe_cannot_authorize_different_or_missing_reference`）。
- 真实 SDK 能力 fail-closed：`sandbox_adapter.declared_capability` 据已装 OpenSandbox 1.1.0 源码声明
  `process_limit=False`（`SandboxSync.create` 无 pids 参数）→ `complete=False` → 拒绝执行；`network_deny`
  通过 `network_policy=NetworkPolicy(defaultAction="deny")` 实际下发；`create` 用 `plan.environment.image`
  （不可变 `@sha256:`，`admit` 已拒可变 tag）作为有效镜像引用发 SDK，`image_digest` 与 image digest 对齐。
- `finalize_assessment` 诊断路径清 `trusted=False`/`contribution="proposed"`；`evaluate` 恒 `trusted=False`。
- 准入/批准绑定持久化不可变事实：`store.approve_generated` 按 `report_id` 重读持久化报告并全等校验
  （伪造 `passed=True` 拒绝 `tampered_generated_report`）、检查未过期、要求显式 `assert_owned`（无 no-op 默认）；
  `generated_validation` 校验所有字节对冻结 manifest digest（`manifest_digest_mismatch` 拒绝字节替换）。
- `TrustedCriteriaRegistry` 同版本异模板构造抛 `criteria_version_conflict`；`IsolationProbeRecord` 增 `image_digest`
  绑定探针环境。



## FR → 源码 → 契约 → AT 映射

| FR | 实现 | 契约/入口 | AT |
|---|---|---|---|
| FR-15 新候选程序 | `generated.py`（`GeneratedFile` manifest；候选字节≠注册示例） | `GeneratedExperimentPlan` | AT-05 |
| FR-16 计划冻结/判据写权 | `EvaluationSpec`（宿主冻结 domain/reference/tolerance/properties）+ `TrustedCriteriaRegistry` | `finalize_assessment` | AT-06 |
| FR-17 检查后隔离执行 | `security.py`（scope/syntax/dependency/danger/resource）+ `verify_isolation(isolation, registry)` | `admit` | AT-07/AT-15 |
| FR-18 可信判定/独立复核 | `evaluation.py`（Poisson 参考 + 通用性质模板，从原始输出重算，自报 score 拒绝） | `GeneratedAssessment` 三轴 | AT-06/AT-08/AT-12 |
| FR-19 真实继承 | 复用 `AssetConsumer`/`AssetApplicator`/`AdoptionReceipt` 原链；`approve_generated` 带 `assert_owned` 围栏 | `AdoptionReceipt` | AT-13/AT-17 |
| FR-20/26 输出与回归 | `GeneratedResult` 持久 archive；`read_generated_result` 重算；旧两类 case 全绿 | `GeneratedResult` | AT-17/AT-18 |

新增完整冻结身份：code/file digest、`data` manifest digest、`image_digest`（不可变 `@sha256:`，
`admit` 拒绝可变 tag）、`dependency_lock_sha256`、parameters/seed、evaluation version/tolerance、
author/reviewer 授权（宿主身份，非 caller 字符串）。

## 最小 API Handoff（A 正式 MCP；C 三轴反馈；P 产品）

- **DynamicPlan**：`orchestration.experiments.generated.GeneratedExperimentPlan`。
- **执行**：`GeneratedExperimentExecutor(backend, probe_registry=..., criteria_registry=...)`
  `.prepare(plan, files, data=None)` / `.admit(prep)` / `.execute(plan, context, files, archive_root, data=None)`；
  `read_generated_result(archive_root, run_id, expected_plan, expected_context)` 重算可信评估。
- **宿主信任**：`TrustedCriteriaRegistry` / `TrustedProbeRegistry` / `IsolationProbeRecord` /
  `finalize_assessment`（`trusted.py`）。
- **准入/应用/消费**：`local_assets.generated_validation.generated_validation(store, asset_id, plan, files,
  isolation, probe_registry=...)` → `approve_generated(store, report, assert_owned, proof_ref=...)` →
  复用 `AssetConsumer.execute/record_adoption` 与 `AssetApplicator.prepare/apply`。
- **播种**：`swarm.research.case.seed_generated_case(...)`（不生成代码/不执行）。
- **可信结果字段**：`GeneratedAssessment{execution, hypothesis, contribution, mode, trusted,
  evaluator_version, metrics, candidate_self_score, proof_ref}`。
- **本地 CPU 隔离适配**：`LocalCpuSandboxBackend(..., probe=IsolationProbeRecord | None)`；
  `registry_with_probe(record)` 供宿主在真实探针完成后登记；本轮 `probe=None` → fail-closed。

## 成熟依赖来源/版本/许可证

| 依赖 | 版本 | 许可证 | 边界 |
|---|---|---|---|
| OpenSandbox SDK（`opensandbox`/`opensandbox-code-interpreter`） | 1.1.0（已锁） | Apache-2.0 | 复用生命周期/文件/命令/资源与网络控制，不套用最新 API |
| pydantic | >=2.11 | MIT | 契约 |
| numpy / scipy | 已装 | BSD | 仅候选批准环境可选；宿主评价器只用 stdlib `math` |
| httpx | >=0.28 | BSD | 传输 |

未新增运行时依赖；`pyproject.toml`/`poetry.lock`/`THIRD_PARTY_NOTICES.md` 本轮无需改动。

## 验收与真实限制

- 本轨测试：`tests/experiments/test_generated_{experiment,evaluation}.py`、
  `tests/local_assets/test_generated_validation.py`、`tests/research/test_generated_candidate.py` 共 **28 passed**；
  连同 `tests/experiments/`（含旧两类 registered 全回归）、`tests/research/test_case.py` 共 **102 passed**。
- 独立 Q 负例（`morph-r1-boundaries-1003`，`R1_SECURITY_SOURCE` 指向本源码）：
  `test_b_generated_boundaries.py` + `test_b_successor_authority.py` 共 **18 passed**（unverified/mock boolean
  不放行、proof_ref 空/异值不复用探针 record、caller approved+reviewer 不给 final、全计划绑定拒绝变更、自报 score
  拒绝、unknown/crash/timeout 不保留伪造奖励、unknown effect 不给 final、succeeded 缺 output digest 绑定拒绝、
  伪造 passed 不能批准已失败持久化报告、manifest 字节替换拒绝）。
- 静态边界：`tools/typecheck.py`（mypy --strict，129 文件）**Success，0 错误，未扩大豁免**。
- AT-07 真实隔离探针与 L2 真实科研切片 **NOT_RUN**（无授权）：`LocalCpuSandboxBackend` 无探针记录时
  fail-closed，dynamic 本轮仅契约 fixture 安全验证实现能力，不声称 live。
- 环境限制：本 worktree 无 `node_modules`（Node GEP SDK），既有 `NodeAssetBridge` 用例以
  `sdk_process_failed` 失败，属环境缺 node 依赖；新生成用例用 `FakeBridge` 离线注入，不依赖 node。

## 未执行/待协作

- 真实沙箱探针、真实科研切片、云/GPU 后端、Hub 发布：未获授权，NOT_RUN。
- A 正式 MCP 接线、C 三轴贡献接受（绑定 `proof_ref`）、P 产品 UI 由各自 Owner 消费上述 Handoff；独立 I 最后集成。

## 2026-10-03 19:30 后继：最终 AT07 准备文档（非运行授权）

Task `task_a4ec02a052a7` / Dispatch `ctx_021ad7956531`；原 B Owner/worktree/branch不变，
依据主控 `1af65788c0223f874c61bc08514c785cc95575be` 当前决策，只更新
[AT07准备包](../experiments/at07-authorization.md)及本短追加。本次commit是docs-only REPORT，不是新业务SOURCE。
受测核心 SOURCE `b480fca1b10a0b6a9c93f0d1801d38f267662461` / 产品 SOURCE
`2b9bf73c93e732771ed3582f3bc7745ea8158b68` / P docs REPORT `c8d4197bac272cdf5f634bc7a56c87db19bfbebb`。
原Git锁384044字节，SHA256 `87B335297F95B7BF72514691CB990DB0D6441316BE90C8CB726B016B9AF025EB`；
模型字段用同值小写。旧576 SOURCE、8558锁、preparation、first RED和OpenCode余额首阻塞明确保留，不复用旧binding。

只读I `C:/r1i/final-product-1855/venv` 核心direct_url精确b480及docker7.2.0/opensandbox1.1.0 metadata；
产品wheel metadata本身不证明2b，沿用I原Git字节/非editable COPY证据。
I原core136/product36Python/53资源/98锁记录、256PASS423.71s、UI126PASS8SKIP、installed四类各2PASS
仅离线证据，本轮未重跑；原全产品10类型错误/6文件不抹除。包新增现有HostConfig/generated settings→
IsolationConfiguration/prepare→原profile/registry调用图例，显式128pids（原默认16），未造模块/profile/approval。
Handoff `msg_15b77327c6f6` / 主控答复 `msg_b3b3ae645af1`：原at07_live默认Docker CLI尚无host/私有配置参数，
须同受控子进程/空私有Docker配置/明确endpoint证明全部CLI读观察与冻结导出同daemon，一条version匹配不足；
无法证明即SDKcreate前STOP交原Owner另定scope。本次不修业务，daemon/serviceID/targetIP/实际profile/probe/授权ref仍UNKNOWN。

保持四镜像、固定endpoint、512MiB/128pids/30s/180s/1MiB、最多5容器1volume0network和
原SDK pause→只读HEAD/GET→原SDKresume单次导出；sidecar/cache限额UNSUPPORTED、动态端口/现存防火墙、
Engine可能恢复他项目容器等限制未降低。下一独立授权最小范围、条件停止、一次SDKcreate未知不重试和精确自有收尾已列明。
本次仅原Git/源码/包metadata读取、docs diff/commit/push `[skip ci]` 与remote exact/clean核对；
私有raw `C:/research-private/b-at07-final-packet-ctx_021ad7956531/`。业务/测试/lock/部署/AOCI/root/P/F/I写入零。
安装、测试、Engine/Docker/WSL/service、密钥、prepare/registry写入、SDKcreate、candidate/native科学均未执行；
AT07与L2仍NOT_RUN，Poisson review不变，费用UNKNOWN，不称MVP/R1完整通过。唯一I可普通合此docs-only REPORT，不新增集成Worker或全回归。

## 2026-10-03 19:39 后继：AT07 CLI 观察端点硬绑定

Task `task_8e19fb680605` / Dispatch `ctx_0c9ab2aea2f0`，原B角色/terminal/树/分支，
Codex GPT-6.1-Sol high YOLO；按root `df12d36e31d4dd7d7a5a54263eed710f283689c2` 当前计划。
先Handoff `msg_72c78bc64bc2`，主控接受 `msg_587d2f618928`；可消费业务 SOURCE
**`fc866465aa52a3f09773bc79a0fab95bceedc3d9`** 已普通commit/push `[skip ci]`、remote exact/clean，
父为原docs REPORT64c5fac，仅 `at07_live.py` / `test_at07.py` 两文件变更。
源码已先交主控 `msg_947038ddc820`；本段及授权包后继commit为单独docs-only REPORT，SHA由终端交付，不自嵌。

所有原CLI前后inspect/inventory、fixedexec cat/nft、筛选域名logs绑定同完整DockerExportConfiguration；
typed argv=`docker --host <原cfg.endpoint> --config <同次新空目录> <closed观察参数>`，shell=False/10s/原观察大小界限。
最小env仅PATH/SYSTEMROOT/WINDIR，大小写规范/冲突拒绝，不继承DOCKER_CONTEXT/HOST/CONFIG/TLS/CERT/API/
customheaders、代理、HOME/USERPROFILE或认证/service key；所有helper均要求明确reader，没有默认context回退。
完整配置无/无效/绕过model校验、service/runtime身份格式或server固定profile不合均在CLI/密钥/create前拒绝。
原credential-free FrozenDockerExport preflight先检查Engine/daemon/Linux/service，同原transport再读取/version匹配API1.52。
私有目录只在新probe root新建 `.at07-docker-cli`，no_links、不得已有、身份核对、只rmdir空目录，未知文件保留。
未扩大exec/秘密字段读取或访问容器范围；原单次create/UNKNOWN/no-replay/原owned SDK cleanup断言保留。

官方参数来源：[Docker CLI](https://docs.docker.com/reference/cli/docker/)；未复制上游代码、增加依赖/transport/schema/registry/调度/证明系统。
原始证据：`C:/research-private/b-at07-endpoint-ctx_0c9ab2aea2f0/`。

| 验证命令 / 阶段 | 实际结果 / 原始文件 |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest tests/experiments/test_at07.py -k 'bind_explicit_endpoint or routing_overrides or bypassed_model or engine_mismatch' -q --tb=short -p no:cacheprovider` | 首RED 18 FAIL/26 deselected/2.58s，exit1；`endpoint-first-red.txt`，主要为旧接口尚未接线，不覆盖 |
| 同python `-m pytest tests/experiments/test_at07.py -q --tb=short -p no:cacheprovider` | 首修44 PASS/11.20s；追加未知目录/配置前置/secret-free异常边界后最终52 PASS/2.04s/exit0；`at07-first-after-fix.txt` / `at07-final.txt` |
| 同python `-m mypy --strict --follow-imports=silent --cache-dir C:/research-private/b-at07-endpoint-ctx_0c9ab2aea2f0/mypy-cache orchestration/experiments/at07_live.py` | 首/最终均1个改动文件PASS/exit0；`strict-first.txt` / `strict-final.txt`；不是全核心strict重跑，原strict配置未改 |
| `git diff --check` / `git ls-remote origin refs/heads/songconmaisaix31-design/morph-r1-experiments-1003` / `git status --short` | SOURCE diffcheck通过、远端精确fc86646、clean；最终REPORT同法单独核对 |

测试捕获实际subprocess argv/env；两种受信endpoint和各只读/fixedexec/log形式、毒化环境、路由绕过、
model_copy无效配置、缺配置/非空私有目录、mutation、原Engine daemon/version/API/Linux mismatch-before-key/create均覆盖。
原disconnect用例现在通过真实reader捕获9次前后CLI调用，仍保留first bytes/UNKNOWN/不重放/唯一SDKcreate断言。
测试autouse拒绝真实Popen/socket/SDKcreate/transport，显式inert替代不构成Engine运行或verified probe。

复用本B原私有 `.venv` pytest9.1.1/mypy1.20.2/opensandbox1.1.0/docker7.2.0，未安装或写I封闭环境。
锁/依赖/部署/backend.py/generated.py/Q/A/P/F/I/root/AOCI业务写入零；原110/210/Q65/核心CI/产品256/UI门未重跑。
SOURCE尚未唯一I合入及P重新pin，b480+2b/a67离线通过明确为前组合，不能冒充新SOURCE installed或全R1完成。
真实Engine/Docker/WSL/services/pull、密钥、native模型、candidate/science、AT07/L2、main/tag/部署均NOT_RUN；
模型用量/费用UNKNOWN，OpenCode首余额阻塞和原RED保留。适用工程门后仍需用户独立AT07授权，全项实际隔离通过后才可另议L2。

## 2026-10-03 20:29 后继：最终组合AT07审核包（docs-only）

Task `task_36dcf2a5df0b` / Dispatch `ctx_d8fb1226f9a7`，parent `task_8e19fb680605`；原B树/branch/terminal。
按root核心治理 `954acd0371407ae45685f68a221948790feafc3a` / 产品治理 `1a395a6d9880d57a440cf6a7433c91d637817f27`，
只更新AT07授权包与本短追加。受测核心 SOURCE `e635b8ab3e79529403b527892e75ffb29674af0a` /
产品 SOURCE `8c716c450bf4b5b436e915726857260cc79cb17e`；P/I REPORT不是SOURCE，本次commit仅docs REPORT。
原Git核对B fc866 / Q f2b81的对应blob在e635相同、产品8c原pyproject精确pin e635；原锁384044字节，
SHA256 `87b335297f95b7bf72514691cb990db0d6441316be90c8cb726b016b9af025eb`，未改锁/profile。
唯一I新私有非editable COPY目标 `C:/r1i/successor-2018/`，I task33b99/ctx154、CI37122569886 attempt1
实际identity/完整工程结果尚未齐全，明确PENDING，不填通过，不用旧1855环境执行新probe。
随后root `msg_50383217a323` 已报告CI首RED Linux1823PASS/1FAIL/16SKIP、WindowsCANCELLED；
Q test-only junction fixture返修待原Owner，B业务零新差异。e635+8c仅已发布、工程未通过，等待后继I精确SOURCE，不覆盖原失败。

新增最少外层操作审核模板：全部deploy/inspect/info/compose以官方CLI绝对路径、同npipe、
新owned空config、typed subprocess/shell=False、必要系统PATH/SYSTEMROOT/WINDIR；不继承DOCKER_*/HOME/auth/TLS/
context/APIheaders/proxy大小写变体。仅Compose按需向新子env传原受保护key/canary，不改变父/全局env。
当前Get-Command路径 `C:/Program Files/Docker/Docker/resources/bin/docker.exe`不证明本体或Compose插件版本/完整性；
runner原argv仍为docker名字，后续须核实实际解析为同批准本体，fixture不能冒充此事实。无法确认即create前STOP。
旧裸Docker/父env示例明确降为历史不可执行，read-only docker_read白名单不扩大；外层mutation仅后来批准的
一次基础设施创建与精确自有完整IDs收尾。新目录不复用/不追链接/不覆盖/不递归清理未知文件。

root20:13 RAM5850MiB/C45.9GiB、20:21pipe=false及三firewall profile原Enabled1/Inbound4/Outbound2只作带时点观察，
不证明动态0.0.0.0:47400..47410仅批准范围。保留Desktop恢复他项目、缺镜像STOP不pull、Engine29.5.3/API1.52
不符STOP不upgrade、sidecar/cache caps UNSUPPORTED/总峰UNKNOWN、基础设施DNS边界、一次SDKcreate未知不重试。
独立授权需明确启动决定/限制接受/600s/最多5containers1volume0network/一个无害sandbox、无candidate/science/L2；
AT07全项真实PASS及独立审核后才注入原TrustedProbeRegistry，接受限制参数不把失败或UNKNOWN变PASS。

本轮仅raw Git读取、文档diffcheck、普通commit/push `[skip ci]` 与remote exact/clean/仅两docs检查，
私有raw `C:/research-private/b-at07-final-identity-ctx_d8fb1226f9a7/`；SOURCE/业务/锁/profile/部署/AOCI/他轨零写入。
未执行测试/安装/CLIhelp/prepare、密钥、Engine/Desktop/SDKcreate/candidate/native科学，旧绿门未重复。
旧b480+2b/a67、8558锁、firstRED/unsupported/unknown原段与原日志保留，Poisson review未改，费用/用量UNKNOWN。
唯一I可最后普通docsmerge，不新SOURCE repin/CI；I结果后由原Task依据root实际日志补充，不虚填PASS。
