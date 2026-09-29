# B 共享熔断 / 探测生命周期修复

## 交付边界

- 基线：`3a34ecafe5f48b1a5a7c94c9e063797427817cab`。
- 分支：`morph-fc-breaker-fix-0929`。
- 原失败阶段：`3dacf9f`；实现与全部测试：`751864580d7043e4187d896bf7036ffc756b5b04`。
- B 仅修改 `swarm/breaker.py`、`swarm/fault_observations.py`、两份既有测试、
  新 `tests/swarm/test_probe_lifecycle_recovery.py` 和本轨 evidence。
- TTL 路由缺陷实际位于 C 独占的 `swarm/failure_chain.py`。已 handoff，由 C 提供
  `42b6115b0815289c22678aaec6240515f700b881`。本分支没有跨改/合入该文件；组合验证
  在 ignored 导出目录只覆盖该 SHA 的精确 blob。`worker_loop.py` 无需接线修改。
- 以下属于 Owner 自验、`contract_local`。未跑付费 live，未 mock live 子进程，未代签
  H1/H3 或正式 FC-E，未把局部门禁称为共同候选验收。

## 实现与证据入口（行号基于 75186458）

`fault_observations.py:75,165,202` 保留有效事实的原 JSONL 行位置，原观察模型、
idempotence key 和 append-only 文件不变；坏行、重复行不被重写或删除。
`:104` 在恢复边界后重算计数与 Retry-After，要求 `sequence > recovery_sequence`
且 `occurred_at >= recovered_at`，因此同时间戳的新追加仍计数，恢复前快照及晚到旧事件
不计数。`:206` 使用现有 writer SQLite sidecar 锁读文件行数，避免把正在追加的同时间戳
事实误判为恢复后事实。没有引入新日志、调度器、Attempt、Manifest 或哈希机制。

`breaker.py:266,334,378` 新增并持久化两个可空字段，原 SQLite 库采用 additive migration；
已有状态、token 和 audit 保留。`:440` 绑定本次真实观察存储；`:477–492` 在 breaker
写事务中重读恢复边界后过滤聚合，覆盖他者旧 TTLCache 和恢复前已读取、恢复后才 apply
的快照。`:629–693` 只对有效 probe success 写入恢复时间与追加 checkpoint；失败、
过期 token、错误 owner、同 owner 旧 token 都不能改此边界。checkpoint 锁失败使整个
成功事务回滚，原 probe 保留，不假装恢复。

`test_probe_lifecycle_recovery.py` 使用真实 `Worker._process`、真实 guard、任务账本、
预算、租约、故障 JSONL 与 breaker SQLite，mock 仅为 executor 外部边界。成功响应复用
既有 FixtureExecutor；usage 明确是 fixture 数据，恢复后继续请求的对照显式配置相符
fixture 价格。断言位于 Worker 调用外；并发 callback 只采样状态/阻塞 executor，断言
在 finally 释放以后。覆盖：

- TTL 前不放行、精确 TTL 到期的新 Worker / 同身份新 token 实际调用 executor。
- 并发争抢期间只有一个 executor 调用；旧 token success/failure 都无效。
- 成功恢复后，同 Worker、已有其他 Worker 缓存、重新创建 Worker、独立 OS 子进程
  均保留原 JSONL，旧事实不导致路由拒绝。
- 恢复时刻相同时间戳的两个新真实 Worker 失败仍使下一任务被熔断，executor 调用
  恰好为 2；没有通过清历史或永久禁用熔断通过测试。
- 两项 store 回归检验迟到旧事件/相同时间戳/坏行追加位置与 writer 锁；两项 breaker
  回归检验在途聚合、checkpoint 回滚、既有 DB schema/token/audit 保留。

既有 `test_breaker.py` 的 39 个函数/类、`test_fault_observations.py` 的 16 个函数/类
用 AST 对比基线均未改变；没有删减、skip 或放松旧断言。

## 原失败、修复与语义 mutation

所有原始日志保留于本工作树 ignored `.runtime/`。原实现行为失败详情见
`fc-remediation-breaker-0929-reproduction.md`。测试状态一直与导出源码平级。

| 运行 | 实际结果 | 解释 / 本地日志 |
| --- | --- | --- |
| 原实现新增 Worker 测试 | 6 failed / exit 1 / 36.49s | `baseline-red-2.log`；TTL 调用 0、恢复后旧历史重熔断 |
| 更早测试 setup | 6 errors / exit 1 | `baseline-red.log`；缺 test-state 父目录，创建目录后才进入行为测试 |
| 首轮 B 恢复门禁 | 3 failed, 81 passed, 4 deselected / exit 1 | `recovery-1.log`；旧记录已不重熔断，但成功 fixture 无价格，后续请求被既有 unknown_cost 保护阻止；增加匹配 fixture 价格，未改生产保护或断言 |
| B 恢复门禁重跑 | 84 passed, 4 deselected / exit 0 / 48.36s | `recovery-2.log`；当时等待 C，不包含 expired_probe；不作为全部门禁通过 |
| B+C 首轮组合 | 1 failed, 95 passed / exit 1 / 83.87s | `composed-1.log`；采样时赢家尚未进入 executor，增加 entered Event 同步，保留 `[0,1]` 断言 |
| B+C 全部领域与 runtime 组合 | 96 passed / exit 0 / 54.09s | `composed-2.log`，没有 deselect/skip |
| 精确 LF TTL guard mutation | 2 failed / exit 1 → 2 passed / exit 0 | `exact-ttl-mutation-red.log`, `exact-ttl-restored-green.log`；guard 换回基线，两个 executor call_count 均 `0 != 1` |
| 精确 LF 历史过滤 mutation | 1 failed / exit 1 → 1 passed / exit 0 | `exact-history-mutation-red.log`, `exact-history-restored-green.log`；禁用恢复边界过滤，真实 Worker 新任务 executor 调用 `0 != 1` |

两项 mutation 都只修改 ignored `.runtime/mutation-src`，`finally` 恢复并验证原字节再跑
green；TTL SHA-256 为 `ee1f7393e8ce1b5fdf30d197a028381fd8b83cc21ef00545143fdbfe43f5e6e4`，
breaker 为 `f668dcf772024efc437769c0f6fd2b3ddc6ed4686bf818c0f9c502ef426198d7`。
`exact-mutation-results.json` 留存真实 exit、字节一致性和行为断言命中；更早工作树覆盖版
mutation 日志也保留，精确 LF 结果为交付证据。

## 验证环境与命令

只读解释器 `C:/Users/DW/orca/workspaces/Morphogenesis/morph-fc-integration-0927/.venv/Scripts/python.exe`。
最终源码导出：

```text
git -c core.autocrlf=false archive --format=zip --output=.runtime/final-source.zip 751864580d7043e4187d896bf7036ffc756b5b04
# 解压到 .runtime/final-src；仅组合 C 精确 failure_chain.py blob
# PYTHONPATH=.runtime/final-src 的绝对路径，import 文件位置已打印验证
# OPENBLAS_NUM_THREADS / OMP_NUM_THREADS / MKL_NUM_THREADS = 1
python -m pytest -q tests/swarm/test_breaker.py tests/swarm/test_fault_observations.py tests/swarm/test_probe_lifecycle_recovery.py tests/swarm/test_failure_chain_runtime.py --basetemp=../test-state/composed-2
python -m pytest -q --basetemp=../test-state/full
python tools/typecheck.py
python -m build --no-isolation --outdir ../dist
node tools/check_sdk.cjs
```

上述 scoped 96 门禁在 candidate-src 组合上完成；精确 LF final-src / mutation-src
均由同一 B SHA 归档加同一 C blob 构成，不是一个新 merge SHA。
ignored node_modules junction 仅在确认原路径不存在后创建，目标为已有集成树；官方
`@evomap/gep-sdk` 1.14.0 与 package.json 匹配。不安装依赖、不改锁。

- strict-final：87 source files，无错误，exit 0。
- sdk-final：schema_valid、asset_id_verified、tampering_rejected=true，published=false，exit 0。
- build-final：exit 1，指定共享 venv 缺 `poetry.core.masonry.api` / `No module named poetry`。
  未安装/修改依赖；按主控要求将已有缓存路径 handoff 给 C，B 不重复排查。
- full：**47 failed, 656 passed, 2 warnings, 7 errors / exit 1 / 578.25s**，
  `.runtime/full.log` 完整保留。此结果未通过，未在 B 重跑。

7 个 setup errors 全部来自 `tests/integration/test_gateway_audit.py:21` 的 receipt
fixture：`GatewayExecutor.execute` → `orchestration/gateway.py:113` →
`orchestration/codex.py:54` 抛出
`ValueError: executor requires a dedicated directory under the OS temp root`。
47 个 failures 位于 `tests/t2/test_codex.py`、`test_gateway.py`、`test_rehearsal.py`、
`test_runtime.py`；代表性异常是同一 workspace 守卫，或
`orchestration/rehearsal.py:130` 的
`ValueError: rehearsal requires a new private root under OS TEMP`。
少量 regex 断言也因先遇到该目录守卫而未到预期分支。没有将这些失败改为 skip。

环境事实：`TEMP` 和 `TMP` 都是 `C:/Users/DW/AppData/Local/Temp`，显式 basetemp
却位于本工作树 `.runtime/test-state/full`，与既有 OS TEMP 安全契约不一致。
已向主控 handoff：I 在启动 Python **之前**将本进程 TEMP/TMP 设置为已创建的
ignored `.runtime/test-state` 绝对路径，继续使用独立 `.runtime/candidate-src`
源码及 test-state 下的 basetemp；无需修改生产守卫。该修正路径尚未由 B 重跑验证，
应在最终共同候选门禁中实测；不得将这个归因写成 full 已绿。

## 更新后的四态矩阵 / H1 阅读材料

核心纯转移函数 `breaker.py:193`，既有 TODO-HUMAN-REVIEW 仍在 `:202,:592,:672`。
本表提供实现语义，不是 H1 签字。

| 当前态 | aggregate | cooldown_expired | probe_success | probe_failure |
| --- | --- | --- | --- | --- |
| insufficient_evidence | 达故障阈值且 min_samples → suspended；确认欠费可直接 suspended；仅足 min_samples → normal；否则保持 | 保持 | 保持 | 保持 |
| normal | 恢复后有效新证据达阈值 → suspended；否则保持 | 保持 | 保持 | 保持 |
| suspended | 仅更晚 Retry-After 可延长 deadline，旧样本不重新起冷却 | 到期才原子认领 → probing_recovery | 保持 | 保持 |
| probing_recovery | 保持，结果由 probe 回报决定 | TTL 到期才原子换 owner/token，仍为 probing_recovery | live owner + exact token + 未过 TTL → normal，并持久化恢复边界 | 同样 fencing → suspended，新冷却；无恢复边界推进 |

半开认领 `breaker.py:569`：短 `BEGIN IMMEDIATE` 与条件 UPDATE 使冷却或 TTL 到期时
只有一个 token 递增赢家。完成 `:629`：exact caller token、owner、当前状态、TTL 全部
匹配才接受 success/failure；同 owner 的旧 token 也无效。C 精确 blob
`failure_chain.py:138` 尝试 TTL reclaim，把**返回的新 token**放入 ProbeClaim；未获得
认领仍按 live owner eligibility 判断。Worker 继续通过原生产 guard 和 outcome 方法，
不取得预算/租约豁免。

恢复边界依赖既有 append-only 文件顺序和 UTC occurred_at：不支持外部截断/重排文件；
迟到且早于恢复时间的事件不会计入恢复后窗口。结构化调用者没有 checkpoint 时仅采用
严格晚于恢复时间的证据，不能推断同时间戳先后。迁移不会捏造老库缺失的历史 checkpoint。

## 未执行 / 限制

最终组合的六门禁与独立验收由集成统一重跑，本报告不替代。H1/H3、正式 deepseek FC-E、
interface_live/task_live、付费模型、生产 merge/tag/release 均未执行；现有五不变量、
TODO、人类签字槽不变。build 的环境失败与 full 的实际结果必须保留，不能用 scoped 96
或 SDK 通过宣称共同候选全绿。

## Git 交接

实现 SHA `751864580d7043e4187d896bf7036ffc756b5b04` 已 push，
`git ls-remote --heads origin refs/heads/morph-fc-breaker-fix-0929` 精确匹配。
remote 为 `https://github.com/songconmaisaix31-design/Morphogenesis`。
最终 evidence-only 提交的 SHA 由 worker_done 交接，生产/测试 blob 保持该实现 SHA；
文档提交后再次验证 remote 与 clean。源码导出和 mutation 恢复文件已逐字节比对 Git
中 B 的五个源码/测试 blob 及 C 的 guard blob，全部一致。最终候选必须同时合入 C
的 guard 修复，本 B 分支单独运行 TTL 新测试仍会暴露基线 guard 缺陷。
