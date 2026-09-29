# M1 local_assets — corrected v0.2

本文件替代旧版“promote 直接写目标树”的描述。继续保留 `05cc7f7` / `27581c2` 的 SDK 寻址、不可变正文、静态语法和原生 Git 快照；修正版只在 A 所有权内改动。业务事实源是 `docs/SWARM_TASK.md` 与 `docs/SWARM_PLAN.md` @ `f1a0209`，公共接口由 B 汇总 `docs/SWARM_CONTRACTS.md`。

## 验证、批准与落地

```python
from local_assets import (
    AssetValidator, AssetPromoter, AssetApplicator, ValidationPolicy, FileExpectation,
)

# 由可信任务 acceptance / 配置提供；不能从本次 candidate 反推预期。
policy = ValidationPolicy(version="task-acceptance-v1", expectations=(
    FileExpectation(path="src/value.py", content="VALUE = 2\n"),
))
report = AssetValidator(store, target, policy=policy).validate(asset_id)
prepared = AssetApplicator(store, target, policy_version=policy.version).prepare(asset_id, report.report_id)
# 调用方必须确认 B lease.scope 覆盖 prepared.scope。
def apply(assert_owned):
    receipt = prepared.apply(assert_owned)
    # callback 返回 None；receipt 只代表此处文件写入，不代表任务事务已提交。
ledger.submit(lease, result_id, result_metadata, apply=apply)
# 只有上述提交完成以后，C 才把该任务资产批准为可用。
approval = AssetPromoter(store, policy_version=policy.version).promote(asset_id, report.report_id)
assert store.state(asset_id) == "approved"
```

`promote` 不接受 target 或 lease，不创建目标文件、不写 Git 树，只在 `approvals` 索引插入批准记录。同资产同报告重放返回同一回执；同资产不同报告不覆盖原批准。候选初态 `quarantined`，失败/失效报告不能批准。历史 `promotions` 表保持原样，但旧 worktree-only 报告不会隐式变成修正版 approved 资产。

`prepare` 在 B 事务外核对官方地址、精确报告、策略版本、环境指纹、报告时效、声明边界、目标 HEAD、原生 Git scope 快照及每个 before 字节。保存受限范围内的文件字节和 Git 原生 HEAD/ref/packed-refs 元数据，用于提交时重新读取。`prepared.apply(assert_owned)` 只做短文件检查/替换，不调用 Git、SDK、模型、测试或另建账本。实际 `assert_owned` 必须来自 B `TaskLedger.submit`，不可用 `lambda: None` 作为运行时适配；单元测试中的替身仅是 contract_local。

B 在首次目标写入前持久保存 `submitting`，再以 `BEGIN IMMEDIATE` 重新核对 task、swarm、owner、递增 token 和 TTL。每个文件写入前与全部写入后再检查持有权；可捕获异常在 B 仍持锁时回滚已写文件。硬进程崩溃可能留下部分文件，B 的 `submitting` 禁止自动重领、重试和冲突 scope 接续，资产保持 quarantine；必须人工审查目标与账本后恢复。SQLite 不提供跨数据库/跨文件原子事务，本实现不声称它提供。已完成相同提交由 B 幂等返回，不再次调用写入。

显式目标必须是非保护分支的 Git 根目录；拒绝 swarm 自身树、冻结主线 `C:/Users/DW/orca/Morphogenesis`、保护分支、调用者保护路径。拒绝 `.git`、冻结文档、swarm/预算/验证器/执行器/测试/SDK/旧 orchestration/依赖锁与工具配置路径，以及路径穿越、ADS、symlink/junction/hardlink。`before` / `after` 是精确 UTF-8；`None` 表示不存在。保留 scoped snapshot 原语，不改变用户索引、分支或范围外 WIP。

## 实际执行边界

本轮只提供 `literal-files-v1` 限定的声明式本地执行。输入是有界文件替换数据，支持精确字节期望、静态 Python/JSON/JS 语法检查和路径检查；候选 Python/JS 从不 import/eval/执行，候选字符串不参与 shell、模板或环境变量插值。只允许可信实现读写显式的隔离目标/验证副本；执行数据没有任意文件读取、网络连接、读取主机秘密或启动子进程的操作。固定验证器位于 A 包，候选不能修改它或它的测试；只在纯数据层比较可信任务传入的固定期望。

`commands` 参数为兼容旧调用保留，但任何非空命令都返回失败 `arbitrary_execution_isolation_unavailable`，不会启动所给命令；缺失固定策略返回 `fixed_validation_policy_required`。不提供任意命令退回主机执行的路径。Python `compile(AST)` 仅做上下文语法验证；JS 仅调用固定 `node --check`、候选字节经 stdin 输入，工作目录为独立临时目录，官方 SDK 调用仍走既有 `NodeAssetBridge`。

报告同时绑定 exact asset_id、候选完整 JSON/AttemptId、base_revision、完整 policy_json 与 policy_version、实际文件/行范围、固定验证操作以及环境指纹。`isolation=non_arbitrary_literal_files` 说明执行器能力被限定，**不表示 OS 沙箱**；报告通过只证明声明式文件结果匹配，不能用来声称任意代码功能/安全性已通过。测试/任意模型生成代码的动态行为验收未开放。

边界：可信 Worker、可信基线和可信固定验证器；同用户恶意进程仍可改数据库/Python 内存/目标文件。worktree、环境清理和静态扫描均不被当作 OS 隔离。没有一般 CPU/内存硬隔离或恶意多租户安全保证。单文件 256 KiB、候选 64 文件；应用范围最多 2000 文件/16 MiB，验证扫描最多 20000 文件/64 MiB；Git/SDK/静态检查有超时，固定验证也有墙钟上限。默认 BLAS/OMP/MKL 子进程线程数为 1。

2026-09-23 本机只读 `docker version --format '{{json .Server}}'`、`docker image ls`、`docker ps` 均得到 `dockerDesktopLinuxEngine` named pipe 不存在。Docker CLI 在原安装目录，但 daemon 不可用；未启动服务/容器、未安装或升级、未操作演示。Docker `--network none` / 只读验证器挂载等一般执行沙箱未运行，不补写假成功证据。

## 消费与采用

```python
from local_assets import AssetConsumer, ConsumptionContext

context = ConsumptionContext(
    swarm_id=lease.swarm_id, task_id=new_task_id, worker_id=lease.worker_id, fencing_token=lease.token,
    execution_id=execution_id, scope="src", capabilities=("literal",),
    completed_dependencies=("setup",), input_context="本次任务的真实输入上下文",
)
consumer = AssetConsumer(store)
injected = consumer.inject(source_asset_id, context)
execution = consumer.execute(
    injected, attempt=attempt, base_revision=revision, base_head=head,
    path_map={"src/example.py": "src/next.py"}, preimages={"src/next.py": None},
)
# 使用 execution.candidate / candidate_asset_id 进入固定验证、B 提交和批准流程。
result_metadata = {
    "candidate_asset_id": execution.candidate_asset_id,
    "consumed_asset_ids": [execution.asset_id], "input_context": context.input_context,
    "execution_id": context.execution_id, "applied": True,
}
# B 提交与新候选批准完成以后：
adoption = consumer.record_adoption(context.execution_id, result_id, ledger)
```

候选的 `required_capabilities`、`dependencies`、scope 均进入官方寻址正文；`inject` 首先 `fetch_approved` 并核验依赖、能力和 scope，注入无采用记录。`execute` 再取官方寻址原文并核验身份，以原资产的精确 after 字节构造新任务的文件操作；调用方只可提供路径映射和目标 preimage，不能伪造被复用 after 内容。新任务必须有新的 task_id，目标路径受源资产 scope 与新任务 scope 同时限制。`consumptions` 记录原 asset_id、输入上下文、执行身份和生成候选地址，但仍不算采用。

`record_adoption` 读取 B 完成账本，要求 `TaskRecord.effect_applied` 为真；该字段由提交事务成功执行 callback 后写入，不能由调用者 `result.applied=true` 代替。核验 swarm、token、owner、task scope、result_id、execution_id、input_context、消费资产列表、生成候选地址；还要求新候选已批准、目标实际字节与消费输出一致。只有这条路径生成 `adoptions`，重复记录幂等。缺少真实执行、未提交、stale owner、报告不匹配和结果上下文替换均不算采用。未知 usage/cost 仍由 B 保留，不变成 0；本轨不调用模型或 Hub。

目标字节核验用于首次记录采用；已有不可变采用记录是历史事实，重放仍核对 B 身份和结果绑定后返回原回执，后续合法任务改动目标文件不会抹掉此前真实采用。若任务完成但尚未批准时崩溃、恢复时报告已过期，仍需重新验证/人工处理，不自动重放目标补丁。

## 存储与复用来源

`assets` 保存官方 canonical body，只 INSERT；正文和 `reports` / `approvals` / `consumptions` / `adoptions` 独立，审计不可 UPDATE/DELETE。`approvals` 是可用状态索引，不改 Gene 正文，不等于远程 Hub promoted。`promoted_assets` / `promoted_bundle` 旧兼容名称现在仅返回新 approved 资产的 Gene+Capsule，并明确 `mock` / `contract_local`。源资产保持原 ID；Capsule 由已有 `hub_client.assets.build_assets` 构造且复核官方 schema/地址，没有外部 PUBLISH。

| 来源 | 版本 / 许可证 | 用途 |
|---|---|---|
| 官方 `@evomap/gep-sdk` 与基线 `NodeAssetBridge` | 锁定 1.14.0 / Apache-2.0 | 原样调用 canonicalize/computeAssetId/verifyAssetId/schema；无 Python 哈希替代 |
| `contracts.identity.AttemptId`、`Contract`、已有 Hub build_assets | 基线 `605cf48` / Apache-2.0 | 身份、Pydantic frozen 数据模型、镜像 bundle；不建新 Attempt/Manifest/证明系统 |
| Git 原生 worktree/index/commit-tree | 本机 2.47.0.windows.1 / GPL-2.0 | 明确目标的隔离副本与 scoped snapshot；无源码复制 |
| Python stdlib / Pydantic | 锁定 CPython 3.12.13 / Pydantic 2.13.5，PSF-2.0 / MIT | SQLite、路径、静态解析、文件替换、数据校验 |

未修改依赖/锁文件、官方 SDK、Hub、旧 orchestration 或服务。B 独占 SQLite 任务/租约/预算；本轨不建立第二套账本。关于 Physarum 的论文适用范围及离散路由由 B 文档维护；资产机制不宣称物理求解器或继承收敛保证。

## 验证记录

所有命令用锁定 `.venv/Scripts/python.exe`，进程局部 `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1`。

- 修正版第一轮 `-m pytest tests/swarm/test_assets.py -q`：**43 passed in 74.49s**，原 SDK/路径/静态语法/不可变报告/快照等用例保留，旧 promote-applies 用例改为批准和应用分离。
- 第一轮 `-m mypy --strict local_assets`、`-m mypy --strict --platform linux local_assets`：均 **9 source files clean**；旧 CREATE_NEW_PROCESS_GROUP Linux 类型错误随不安全通用命令执行路径一起移除。
- 边界首轮把 fixture Git 仓库放在自身 `.runtime/assets-boundary-tests`，得到 **8 passed / 4 failed**；4 项均被 `protected_target` 正确拒绝。原目录保留，不放宽保护规则；协调者确认使用 pytest 专属、位于保护树外的临时目标。
- `-m pytest tests/swarm/test_assets.py -q -k 'fixed_policy or fixed_verifier or inert or prepared_baseline or real_sqlite or approved_fetch or process_crash'`：纠正 fixture 位置后 **12 passed, 43 deselected in 39.30s**。
- 最终 `-m pytest tests/swarm/test_assets.py -q`：**56 passed in 110.75s**，包含新增 scope、swarm 身份及伪造采用反例。真实子进程在第一文件替换后以 71 退出，确实产生部分目标字节；B 留在 `submitting`、后继不能领取、资产不批准、没有采用记录。
- 最终 `-m mypy --strict local_assets` 与 `-m mypy --strict --platform linux --cache-dir .mypy_cache/assets-linux local_assets`：均 **Success: no issues found in 9 source files**。
- 2026-09-24 恢复审查补充历史采用幂等性：`-m pytest tests/swarm/test_assets.py -q -k approved_fetch` **1 passed, 55 deselected in 39.83s**；两个平台 strict 再次 **9 files clean**。56 项全量结果属于此前完整版本，此项最小修正只做相关定向回归，不冒充再次全量运行。
- `git diff --check -- local_assets tests/swarm/test_assets.py docs/SWARM_ASSETS.md`：通过。全程只暂存 A 自有文件；Git 串行时段由协调者授予后执行。

负例覆盖：固定策略版本/内容不匹配；候选修改测试、验证器、预算和冻结文档；候选 Python 字符串保持惰性；文件外写入/网络/环境秘密访问命令在启动前拒绝；旧 token 在 B 提交时拒绝且不再次写目标；prepare 后依赖字节变化；批准但未执行/未提交不产生采用；伪造 `applied=true` 无 effect 和 no-op effect 无实际目标字节均拒绝；scope/capability/dependency/swarm/owner/token/result_id/输入上下文/执行身份替换拒绝。模拟秘密仅是测试常量，没有读取凭据。

`contract_local` 包含真实 Node SDK、Git、SQLite、多进程崩溃与本地字节行为，任务输入仍为明确 fixture。`interface_live` / `task_live` / Docker arbitrary-code sandbox 为 `not_run`；未跑付费模型、真实 Hub、全仓 suite/build/CI。完整仓库与最终精确 SHA 验收由独立 I 执行。
