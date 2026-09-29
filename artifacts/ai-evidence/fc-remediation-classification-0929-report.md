# FC remediation C：分类优先级与过期探测路由证据

本报告是 C Owner 自验，**不是独立验收或 FC 冻结**。生产五项修复已获本轮授权；旧 cost_state 未授权限制已覆盖，H1/H3、正式 deepseek-r1 FC-E v2、入口/演练仍 OPEN。全程无网络 API 查询、无付费 live、无 live 子进程 mock。

## 交付与精确源码

- Worktree / branch：`C:/Users/DW/orca/workspaces/Morphogenesis/morph-fc-classification-fix-0929` / `morph-fc-classification-fix-0929`。
- Base：`3a34ecafe5f48b1a5a7c94c9e063797427817cab`，初始 HEAD 一致且 clean。
- 一页计划：`d09e6e0c43046de535a6c4f7f50957ac3b77c180`，`docs/FC_REMEDIATION_0929.md`；旧共同计划/TASKS 未修改。
- TTL guard 阶段：`42b6115b0815289c22678aaec6240515f700b881`，已通过 Orca Handoff 交 B `ctx_c1fadb326ac0` 精确 blob 组合验证；最终分支未交叉 cherry-pick。
- 原分类生产行为复现：`c505f7e696adeee2c9b3d0a1c0472248a76cdc41`。两 adapter 和 `worker_loop.py` 在该提交与 base **逐字节相同**，见 `.runtime/source-bytes.log`。
- 修复后测试源码：`36aa0e7ec7b355ad0c8e2eacfc5489df9d577ad4`。后续仅计划/本报告材料；最终交接 SHA、远端同值与 clean 由完成回执和 `.runtime/remote-verification.log` 记录，不将旧日志称为最终组合 SHA 重跑。
- Remote：`origin` = `https://github.com/songconmaisaix31-design/Morphogenesis`，目标 `refs/heads/morph-fc-classification-fix-0929`，普通 push，无 force。

相对 base 的全部修改路径：`orchestration/provider_adapters/dashscope.py`、`orchestration/provider_adapters/evomap.py`、`swarm/failure_chain.py`、新增 `tests/orchestration/test_rejection_classification_boundaries.py`、新增 `tests/swarm/test_rejection_runtime_boundaries.py`、`docs/FC_REMEDIATION_0929.md`、本报告。既有测试逐字节保留；无 A/B 生产路径、AGENTS、SWARM 文档、锁文件或五不变量修改。

## 修复行为与断言

1. `dashscope.py:42` / `evomap.py:42` 在解析正文前裁定 `status_code >= 500` 为 unknown_effect。无论中英文欠费/配额/余额/账户正文、结构化 Arrearage/FreeTierOnly code/message，均不可降级为可续发的拒绝；沿用已有 transport=0 更高优先级、4xx/429、预算/能力分类和 Retry-After 契约，不引入新 API 猜测或重试。
2. `swarm/failure_chain.py:138` 在 probing_recovery 中先调用既有原子 `try_claim_probe`；过期赢家使用返回的新 token，未到期既有 owner 继续走 eligible，其他 Worker 被挡。复用 SharedBreaker 的 SQLite 认领与 fencing，没有新调度/身份系统。
3. 新分类测试 102 项：两家 × status 0/500/502/503/504 × 中英文结构化消息；非 JSON/null/list 5xx；普通 4xx、明确欠费/配额拒绝、429、预算/能力和成功对照。
4. 新运行时测试 42 项：真实 `single_request → EvoMapAdapter → EvoMapExecutor → Worker._process` 与持久 SQLite/JSONL。仅 HTTP 使用显式 `httpx.MockTransport`，executor 的 `Mock(wraps=real)` 计数但执行真方法；断言在 `_process` 返回后检查实际调用、reservation、usage/cost unknown、full hold、switched_to、哈希、脱敏和 not_run。无 usage 的模拟 HTTP 响应保持缺失，没有用 0 或构造 usage 伪装费用。
5. 同文件含 3 项真实 SQLite guard 测试：TTL 精确到期同/异 owner、旧 token 不可报告、两个连接并发唯一赢家。B 另拥有真实 Worker TTL/恢复生命周期测试；本报告不替 B 宣称通过。

EvoMap demo CLI 的一任务一次请求契约保持。新夹具先按该契约播种，再把相同任务/验收事实复制到**独立状态**的新 Worker 运行，预先设定多候选 attempt 和足够的 burn capacity，不修改已持久化 limits。

## 原失败、修复门禁与 mutation

所有运行日志和数据库只留在本 worktree ignored `.runtime`；以下路径均相对该目录，未把运行产物入库。

| 证据 | 精确源码 / 结果 | 事实 |
|---|---|---|
| `runtime-pre-fix.log` | `c505f7e...`；exit 1，2 failed / 7 passed / 33 deselected，22.37s | 500 + 英文/中文 Arrearage：`test_rejection_runtime_boundaries.py:74` 的 `assert later.execute.call_count == 0` 实际 **1**；4xx 受控切换和 transport unknown 对照 7 项通过 |
| `original-red-valid-fixtures.log` 的 guard 部分 | `3619d9dffd05ec0867ff6c10c0b5663069caccd4`；3 个 guard 行为红 | 同/异 owner 到期后 routable=False；并发赢家数实际 0，应为 1 |
| `guard-green.log` | `42b6115...`；exit 0，3 passed / 39 deselected | 过期 slot 重认领、新 token 和唯一赢家 |
| `focused-green.log` | `36aa0e7...`；exit 0，**246 passed / 137.52s** | 全部旧 provider、Retry-After、gateway/child mock、两旧 failure_chain、breaker 与两新增文件 |
| `strict.log` | `36aa0e7...`；exit 0，87 source files | 项目 `tools/typecheck.py` strict |
| `sdk.log` | `36aa0e7...`；exit 0 | 官方 SDK 1.14.0 schema_valid / asset_id_verified / tampering_rejected，published=false |
| `build.log` | `36aa0e7...`；**exit 1** | 指定只读 venv 中 `python -m build --no-isolation`：`ModuleNotFoundError: No module named 'poetry'`；未安装依赖 |
| `mutation.log` | `36aa0e7...` 精确导出；driver exit 0 | 两 adapter 各自把 5xx guard 移回正文分类之后；EvoMap 真实 Worker 2 failed/exit 1（later.execute=1），恢复 2 passed/exit 0；DashScope 2 failed/exit 1（confirmed_rejection），恢复 2 passed/exit 0 |
| `guard-mutation.log` | `36aa0e7...` 精确导出；driver exit 0 | 仅临时把 guard 还原为 base 原实现，3 failed/exit 1；恢复后 3 passed/exit 0 |
| `source-bytes.log` | exit 0 | mutation `finally` 恢复后，两 adapter、guard、两新测试逐字节等于 `git show 36aa0e7...:<path>`；原分类复现的生产字节与 base 相等 |

原失败关键摘录（原日志与 mutation 均实际出现）：

```text
assert later.execute.call_count == 0
E   AssertionError: assert 1 == 0
2 failed, 7 passed, 33 deselected in 22.37s
```

Mutation 保留原 bytes，于 `finally` 写回并比较；恢复后运行同一组测试。EvoMap 恢复文件 SHA-256 为 `43ee7c56ac712bc0d24b785f39a9f70faaa0a607a1f62f60e13a0ecf3727e197`，DashScope 为 `91a3575347ef30a3ef63607cd9c585c85faaf6b44e90949686239c44430f5f95`。这两值仅用于核对恢复，不创建产品哈希设施。

前期夹具/环境失败同样保留，**不冒充缺陷验收、不抹掉**：

- `16c9139b94ace65a6b81c3a168ad5857a62eedad` / `original-red.log`：58 分类失败、44 通过、42 setup errors，exit 1；pytest basetemp 的父目录未创建。补目录后 `original-red-layout-corrected.log` 为 100 failed / 44 passed，exit 1，含 EvoMap seed limits 与 dict 错传 observation 的夹具错误。
- `3619d9d...` / `original-red-valid-fixtures.log`：100 failed / 44 passed，exit 1；分类 58 失败和 guard 3 真实失败外，39 个运行时仍被 EvoMap seed 契约拒绝。
- `95c21d17e9c5bac642c9ddb4f7978574568b7e59` / `runtime-original-red.log`：39 failed / 3 passed，exit 1；重开播种 TaskLedger 未传原 limits。
- `ba01787bbae25169568c3158e210b143afe50b8a` / `runtime-original-red-2.log`：32 failed / 10 passed，exit 1；分类错误确实到达下一候选，但 4 个正对照受默认 burn capacity 阻挡，尚不足证明第二次实际发送。
- `c505f7e...` 修正**新增夹具**预算配置后才取得上表干净的 2 行为失败 / 7 对照通过。未改旧断言、无 skip，所有生产 adapter 仍与 base 相同。生产修复后的第一轮 focused 已全绿，无连续两轮修复门禁失败。

## 可复跑命令与环境

Python 只读复用 `C:/Users/DW/orca/workspaces/Morphogenesis/morph-fc-integration-0927/.venv/Scripts/python.exe`，初次 import 路径实测为本 worktree `.runtime/candidate-src/...`。`git -c core.autocrlf=false archive --format=zip --output=.runtime/candidate.zip <上述精确SHA>` 后用标准 `zipfile` 导出到 `.runtime/candidate-src`；state 在平级 `.runtime/test-state`，没有改 protected_runtime_state 检查。已有 SDK junction 仅位于 ignored 导出目录，创建前路径不存在，目标为 `morph-fc-integration-0927/node_modules`，目标版本和本项目 package.json 都是 1.14.0。

在 `.runtime/candidate-src` 执行（`$fcPython` 为上述绝对 Python 路径，`PYTHONPATH` 为当前源码目录；`PYTHONDONTWRITEBYTECODE=1`，三个 BLAS/OMP/MKL 线程变量=1，TEMP/TMP 为平级 `.runtime/test-state/tempfiles`）：

```powershell
# 修复前 c505f7e 的干净行为复现
& $fcPython -u -m pytest tests/swarm/test_rejection_runtime_boundaries.py -k '(server_error and Arrearage and 500) or confirmed_rejection or transport_unknown' -q --tb=short --basetemp=../test-state/runtime-pre-fix
# 36aa0e7 的完整本轨 focused
& $fcPython -u -m pytest tests/orchestration tests/swarm/test_rejection_runtime_boundaries.py tests/swarm/test_failure_chain_runtime.py tests/swarm/test_failure_chain_boundaries.py tests/swarm/test_breaker.py -q --tb=short --basetemp=../test-state/focused-green
& $fcPython tools/typecheck.py
node tools/check_sdk.cjs
& $fcPython -m build --no-isolation
```

Mutation driver 在工作树根执行 `& $fcPython -u .runtime/classification_mutation.py`、`& $fcPython -u .runtime/guard_mutation.py`，脚本只操作导出副本。它们的日志包含每条精确 argv / basetemp / exit；再次复跑应另建新 basetemp 以保留现有证据。

主控已明确本轨 scoped 收口：不为 build 安装依赖或扩范围。已只读定位并实际 import 核实 `C:/Users/DW/AppData/Local/uv/cache/archive-v0/8IuHKNOGrMpTxzu6/Lib/site-packages` 中 `poetry-core 2.5.0`，见 `poetry-backend-readonly.log`；单进程 PYTHONPATH 复用建议已 Handoff，**未用它重跑 build，不把可 import 算作 build 通过**。现有 CI `.github/workflows/check.yml:23` 为 build；后续用 `uv pip install --no-deps --target tools/.wheel-site <wheel>` 与 `python -I tools/check_distribution.py --site-dir tools/.wheel-site --check-node`。这些由最终集成 Agent 在共同 SHA 的隔离环境执行。

## 证据文件 SHA-256

```text
original-red.log 177199af438b13f4096c4b36824d1634ffc5b609de0a7d0a871af8498c665055
original-red-layout-corrected.log bfd1fb0d9af63a22418139e4dd11422114b15cf9c5e211e6fe579c0a169666a9
original-red-valid-fixtures.log b43939fca7b826b14dcd520ac68b110deccc7fa000a4a1d5d36b64d9e6f1721c
runtime-original-red.log 464dcbd26c3adf3a7d0f7da756ac2dcc3cfe7e3ab59ce33c66b0342b0febb9a3
runtime-original-red-2.log b849774b93c3067c935432e930d09a0428064a5c0cfe10b4ad549d1c72ae5eac
runtime-pre-fix.log 63a3241f76d58dce5b6e4e561ff06ec04501a9a9a90e69bbf77b393c8f68e2f1
focused-green.log 0f24829e590f8ec14691e2847bca8d926c1c3c5f62e87c24b52efb9973d49aa7
mutation.log 0d1cd5374423248a6dc1610c0a13b219b09daa4ba730651fd31b475a5502dd23
guard-mutation.log 96cfe73cfae36742eb9a7af3cca0e91f3c586cc251c31fc57786d51281e08f7b
strict.log e5e2f5ad00c77c77911b70e177d9653cd94b6f1b3f5cf2ec0ef3ae641b33f7f0
sdk.log 66ec219083b8cbae441e7f26fe6d3ebe95b56f18b51cb5ac3fbc216c70c6b293
build.log 052e5f4184ee5d2de635e27f258e6e07372cd339996a974a38b87292de0de794
```

## 真实剩余限制 / NOT_RUN

- 本轨全部证据为 contract_local、provenance=mock，interface_live/task_live=not_run；无第三方 API 文档推测、付费/live 模型请求或生产发布。
- C 未执行全量 full 或分发；Owner build 如上失败保留。A+B+C 共同不可变候选仍须独立 focused/full/strict/build/官方 SDK/分发全套重跑，不能复用本轨绿灯或以前 699/full 日志冒充组合门禁。
- H1/H3 人工签字、正式 deepseek-r1 FC-E v2、入口与演练、生产 merge/tag/冻结不在本报告中关闭；A/B 领域修复以各自交付与共同验收为准。
