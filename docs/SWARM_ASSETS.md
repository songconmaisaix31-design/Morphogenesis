# M1 local_assets

所有写入限 `decentralized-swarm` 开发树和调用方显式指定的本地运行目录。没有 Hub 或模型调用；没有依赖、锁文件、`hub_client` 或 `bridge_node` 修改。

## 固定 API

```python
from local_assets import (
    Candidate, FileChange, LocalAssetStore, AssetValidator, AssetPromoter,
    ValidationReport, PromotionReceipt, blast_radius, snapshot_revision,
)

# 在租约范围内捕获本次基线；分支、用户索引和工作文件不变。
revision, head = snapshot_revision(explicit_target, "src", snapshot_directory)
# attempt 是 contracts.identity.AttemptId，复用既有身份契约。
candidate = Candidate(
    attempt=attempt, base_revision=revision, base_head=head,
    changes=(FileChange(path="src/value.py", before="VALUE = 1\n", after="VALUE = 2\n"),),
    declared_files=1, declared_lines=2, scope="src",
)
store = LocalAssetStore(local_state_directory)
asset_id = store.publish(candidate)  # PUBLISH；初始状态始终 quarantined
assert store.fetch(asset_id) == candidate  # FETCH；重新核验官方 schema 与地址
validator = AssetValidator(
    store, source_repository,
    commands=((python_executable, "-B", "-m", "pytest", "-p", "no:cacheprovider"),),
    timeout_seconds=30, report_ttl_seconds=300,
)
report = validator.validate(asset_id)  # REPORT；成功/失败均持久保存
receipt = AssetPromoter(store, explicit_target).promote(asset_id, report.report_id, lease_guard)
bundle = store.promoted_bundle(asset_id)  # 仅返回已有晋级回执的 Gene + Capsule
```

`before` / `after` 是精确 UTF-8 字符串；`None` 表示文件不存在，支持新建和删除。`base_revision` 是完整 Git commit SHA；重复增长使用原生 scoped snapshot commit，并以 `base_head` 绑定目标实际 HEAD。兼容直接从已提交基线验证的调用方：省略 `base_head` 时要求 `base_revision == target HEAD`。`scope` 是仓库相对目录、文件或 `.`；修改必须完全包含在该 scope。`declared_lines` 等于 `difflib.SequenceMatcher` 的新增行数加删除行数；一行替换计两行，换行符改变也计入。调用方可以先用 `blast_radius(candidate)` 获得同一标准的计数。

`store.report(report)` 接受失败观察；通过报告只能由 `AssetValidator` 内部签发。`get_report(report_id)`、`reports()`、`promotions()` 为本地审计读取，`state(asset_id)` 返回 `quarantined` 或 `promoted`。`promoted_bundle(asset_id)` 直接查询该资产回执，不扫描所有候选；`promoted_assets()` 是观察/导出用全局视图，不供 Worker 觅食。

## 持久化与绑定

SQLite `assets.sqlite3` 使用 WAL、外键和事务。`assets`、`reports`、`promotions` 都只有 INSERT；UPDATE/DELETE 被 SQLite trigger 拒绝，已知地址 PUBLISH 幂等且不同内容不能覆盖。每次 FETCH 调用官方 `validate_asset`，不信任数据库里的地址字符串。

候选是符合 SDK 1.14.0 schema 的 Gene。官方 Gene `additionalProperties=false`，因此本地候选 JSON 放入第二条 `strategy` 字符串，以 `local_candidate_json:` 标明应用层编码；没有新增 wire 字段或改动地址算法。候选、AttemptId、scope、声明边界、原始/修改后字节和基线版本全部进入官方地址。

通过报告绑定 asset_id、候选完整 JSON、AttemptId、base_revision、实际修改范围、命令 argv/exit/超时/输出限制，以及 `node_version` / `arch` / `platform` / `python_version`。报告编号是普通 UUID 行标识，不是新建 Attempt、Manifest 或完成证明设施。报告与候选分开且不可改写；过期报告需要重新验证。

晋级重新获取候选并核验 SDK、报告等同性、通过状态、实际范围、报告时效、当前环境指纹、目标 HEAD 以及每个目标文件的精确 before 字节。直接传入修改过的 ValidationReport 会与已保存报告比较并拒绝。同一 report_id 最多产生一个晋级回执。失败始终保持候选与原报告，并且不进入镜像列表。

成功后的镜像 bundle 复用 `hub_client.assets.build_assets` 生成 Capsule，再将其 Gene 链接到原始已寻址候选并由官方 SDK 重新计算 Capsule 地址、复核 bundle。全部为 `mock` / `contract_local` 证据；未知 token/cost 保留 `None`。这不触发外部 PUBLISH。

## 验证与晋级边界

- 静态检查：Python AST 加只编译不执行的上下文语法检查、JSON 解析、JavaScript `node --check`；保守危险调用/导入扫描。仅支持 `.py/.js/.mjs/.cjs/.json/.txt/.md` UTF-8 文本；单文件限 256 KiB、最多 64 文件。未知语言、二进制、无变化、重复/大小写别名或父子文件路径拒绝。
- 路径检查：绝对路径、`..`、反斜杠、NTFS ADS、控制字符、Windows 保留名称、尾点/空格、`.git` 和冻结文档拒绝；检查现有祖先及文件的 symlink、Windows junction 和 hardlink。基线含 Git symlink/submodule 也拒绝。
- 真实 `git worktree add --detach` 在提交基线创建隔离副本。先核验每个 before，再物化候选，运行调用方预设的非空 argv 命令；候选内容不决定命令。shell=False，默认累计时间 30 秒（最大 300 秒），每条输出限 128 KiB（最大 1 MiB）。超时或输出超限终止所启动的进程树；20 ms 轮询意味着输出文件可能在终止前短暂超出上限，不是 OS 磁盘配额。
- 验证环境复用既有 `child_environment`，不继承应用凭据/代理/Node 注入变量；设置三个 BLAS 线程变量为 1，并禁用 Python 字节码。验证前后比较工作树完整文件字节（最多 20000 文件 / 64 MiB）及 `.git` 指针，命令写入额外文件或改写候选即失败。原始命令输出不持久保存，避免意外秘密进入审计。
- worktree 保留在 `store.root/worktrees/<report_id>` 供诊断；权威不可变证据是数据库中的原候选及报告，诊断工作树不作为晋级字节源。没有自动清理其他 worktree。
- `LeaseGuard(absolute_scope)` 必须返回持有 B 轨文件租约原子锁的 context manager，yield `assert_owned()->None`。C 用 `LeaseManager.guard(lease)` 适配，并验证传入 scope 被租约覆盖。晋级在进入、每次写入和最终记录前检查持有权与 TTL；过期持有者不能继续。SQLite BEGIN IMMEDIATE 避免跨报告消费竞争。
- 目标必须显式给出、是 Git worktree 根目录且分支非保护分支；拒绝固定冻结主线 `C:/Users/DW/orca/Morphogenesis`、调用方 protected_paths，以及 `main/master/codex/morphogenesis-mainline`。晋级不创建 Git commit，不改公共分支历史。
- 文件替换复用 `os.replace`，写入临时文件后 fsync；Python 可捕获异常时在仍持有租约锁内回滚已写文件。多文件晋级不是跨文件原子文件系统事务；进程/机器硬崩溃可能留下部分字节，后续 before 检查会拒绝自动重放，需要人工检查恢复。

这是 worktree、进程环境和应用级路径限制，**不是 OS 安全沙箱**。同一 OS 用户仍可访问主机文件/网络、修改数据库或调用内部 Python 接口；静态危险模式不是恶意代码安全证明。只适用于信任的仓库基线、调用方验证命令、runtime 租约适配器及本地执行器。不宣称网络隔离、内存/CPU硬配额或防御恶意并发外部写入；脱离父进程的后台进程也需要 OS 沙箱/作业对象提供更强生命周期保证。运行时原生 Git worktree 不依赖 Orca daemon，开发派发和归属通过 Orca 留痕。

重复增长复用原生 Git：`snapshot_revision(repository, scope, scratch_directory)` 在临时 `GIT_INDEX_FILE` 中 `read-tree HEAD`，只读取租约范围内 Git tracked 差异和非忽略 untracked 文件，用 `hash-object/update-index/write-tree/commit-tree` 得到无分支引用的临时快照提交。不会改用户索引、分支或工作文件，不会把范围外的 WIP 放进快照。捕获前后检查 HEAD、差异路径及读取字节稳定。最多捕获 2000 个差异文件、64 MiB。临时索引自动删除；Git 原生对象由 Git 管理，不建设 Manifest/哈希/证明系统。

同一文件第一次晋级后，下一次捕获会读取上次真实已晋级字节，因此可在未改 HEAD 的情况下连续自增长。晋级在租约锁内重建当前 scoped tree，确认快照父提交为 `base_head` 且树 SHA 完全一致；范围内依赖在验证后改变也拒绝。验证基准仍为 `base_revision + candidate`，范围外未提交修改不参与该 scope 的验证；涉及跨范围依赖的任务须将依赖包含在声明 scope，并取得覆盖它们的租约。

## 实际复用

| 来源 | 固定版本/许可证 | 本轮用途 |
|---|---|---|
| [EvoMap gep-sdk-js](https://github.com/EvoMap/gep-sdk-js)，已锁 `@evomap/gep-sdk` | 1.14.0 / Apache-2.0 | `NodeAssetBridge` 调用官方 canonicalize/computeAssetId/verifyAssetId、官方 JSON schemas，Python 无哈希 fallback |
| 本仓库 `bridge_node/assets.py`, `environment.py`, `hub_client/assets.py` | 基线 605cf48，相关 Hub/SDK 4938bb9 / Apache-2.0 | 既有 shell-free SDK transport、凭据隔离环境、build_assets/validate_bundle |
| 本仓库 `contracts.identity.AttemptId`、`Contract` | 基线 605cf48 / Apache-2.0 | 既有 Pydantic 身份和 frozen 验证策略 |
| [Git worktree](https://git-scm.com/docs/git-worktree) | 本机 2.47.0.windows.1 / GPL-2.0 | 作为外部程序执行 worktree/plumbing；无源码复制 |
| Python stdlib sqlite3/subprocess/ast/difflib/pathlib/tempfile | CPython 3.12.13 / PSF-2.0 | 事务、执行、静态语法、行数差异、路径和原子替换 |
| Pydantic | Poetry lock 2.13.5 / MIT | 应用层输入和报告模型，不重造 GEP schema |

Node 本机 v24.16.0。安装命令：`uv venv --python 3.12 .venv`、`uv tool run --from poetry poetry install --no-root --no-interaction`、`npm ci --ignore-scripts`。未安装 pip 不影响该 uv/Poetry 锁定环境。

## 文献适用范围

任务指定的 [Capacity Constraint Physarum Solver, v1](https://arxiv.org/html/2010.09280v1)、[Multi-Commodity Flow Dynamics, v5](https://arxiv.org/html/2009.01498v5)、[Physarum 综述, v3](https://arxiv.org/pdf/2103.00172) 用于辨明生物启发与工程约束的边界。前两篇针对图流量/连续动力学，综述讨论局部环境交互；它们没有提供内容地址、隔离执行或安全晋级实现。本轨不移植其中算法或代码、不引入连续收敛结论；M2/M3 的离散沉积/挥发/路由由 B 轨记录全文审阅与具体公式。M1 的环境记忆是已验证资产和失败证据的持久保存，不把它当作新调度器或新的信息素算法。上述论文只作概念引用，无复制论文文字或许可推断。

## 验证记录

本轨测试命令均使用 worktree `.venv/Scripts/python.exe`，进程局部设置 `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1`。

- `python -m pytest tests/swarm/test_assets.py -q`：覆盖真实 worktree、SDK 地址一致、静态危险/语法、范围与路径、失败隔离、有界命令、报告篡改/替换/过期、保护目标、链接拒绝、租约丢失回滚、并发单次晋级、同一文件连续两代增长、范围外已暂存/未跟踪 WIP 与用户索引原字节保持、范围内基线过期拒绝。
- `python -m mypy --strict local_assets`：新增包严格类型检查。
- 最终实测数字和 SHA 由协调者写 `SWARM_STATUS`，本文件不预填未发生的成功结果。

2026-09-23 Windows 实测：M1 主提交 `05cc7f72a4bfd5fb1624b282ff7965cec45022c1` 的完整测试 **42 passed in 273.97s**；`mypy --strict local_assets` **Success: no issues found in 7 source files**；暂存自有路径 `git diff --cached --check` 通过。测试调用真实 Node SDK、Git worktree/对象和文件系统，模型任务输入仍是本地 fixture。

后续上下文语法加固增加模块顶层 `return` 和重复函数参数两项拒绝测试；仅 `ast.parse` 不足以拒绝这两种代码，因此复用 Python `compile(AST, ..., "exec")` 检查但从不执行结果。该变更验证命令 `python -m pytest tests/swarm/test_assets.py -k 'static_failure or official_address or javascript' -q` 得到 **10 passed, 34 deselected in 80.75s**；再跑 strict mypy 仍为 **7 files clean**。定向检查不冒充加固后全量 44 项重跑；全仓最终验收由集成轨记录。

尚未执行：Ubuntu CI、生产 Hub/model、interface_live、task_live；本地测试不能将这些门禁置绿。
