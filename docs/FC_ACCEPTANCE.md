# FC 轮失败接续链验收报告（2026-09-27）

## 结论

失败接续链五不变量已实现并合入集成树；**698 项测试全绿、87 源文件 strict mypy 无错、
build（sdist/wheel）与官方 SDK 校验通过**。受控切换（confirmed_rejection 才切换）与
他者避让（共享熔断 + 唯一探测名额）已进入 `Worker._process` 生产路径。

## 最终 SHA

| 轨 | 分支 | 最终 SHA | 内容 |
|---|---|---|---|
| FC-A | `fc/failure-classify` | `4b91c24` | 传输分类 + Retry-After 语义 + 子进程回传 |
| FC-B | `fc/fault-observation` | `92e1de3` | FaultObservation JSONL + 聚合 |
| FC-C | `fc/breaker-state` | `8c7e2b6` | 共享四态熔断 + 探测 token fencing |
| FC-D | `test/failure-chain` | `d210b23` | 六夹具 + 五不变量边界测试 |
| FC-R | `songconmaisaix31-design/morph-fc-runtime-0927` | `bbe9d77` | worker_loop 有界候选链 + failure_chain 数据模块 |
| 集成 | `songconmaisaix31-design/morph-fc-integration-0927` | `27e3891` | 五轨 exact-SHA no-ff 合并 + 集成胶水 |

全部已推送远端，`fc/fault-observation` 本轮之前已推送（`92e1de3`）。

## 门禁命令与结果（集成树 morph-fc-integration-0927，本机 `.venv`）

```
$env:POETRY_VIRTUALENVS_IN_PROJECT='true'; uv tool run poetry install
$env:OPENBLAS_NUM_THREADS='1'; $env:OMP_NUM_THREADS='1'; $env:MKL_NUM_THREADS='1'
.venv/Scripts/python.exe tools/typecheck.py   # Success: no issues found in 87 source files
.venv/Scripts/python.exe -m pytest -q          # 698 passed, 2 warnings
uv tool run poetry build                        # sdist + wheel 构建成功
node tools/check_sdk.cjs                        # schema_valid, tampering_rejected, published=false
```

两个 warning 是 `test_budget.py` 中故意用非法 `model_copy` 输入验证预检拒绝，属预期。

## 五不变量落地位置

1. **换 provider 不产生新任务预算、不清空已有消耗** — `BudgetLedger.reserve` 以
   `(swarm_id, request_id)` 唯一计数，`max_attempts`/`max_attempts_per_task` 与累计
   `admission_charged_usd` 在切换中持续累加，不因换候选重置。
2. **未知费用预留永不被 fallback 自动释放** — `mark_uncertain` 与
   `mark_unknown_rejection` 保留 full hold；`settle` 的「lower usage 不释放 allowance」
   注释与实现一致。
3. **attempt 计数覆盖全部真实远端请求** — `_process` 在每次发送前 `reserve`（持久计数），
   跳过候选（熔断 block）不计数。
4. **失租 Worker 即使成功也不得提交** — 每次发送前 `keeper.check()`，提交前
   `keeper.handoff()` + 现有 fencing；`LeaseLost` 路径不改。
5. **全候选不可用有界退出** — 熔断 block 全部候选时 `all_candidates_suspended` 有界退出，
   `decide` 的 `exit_candidates_rejected` 分支 + `max_attempts` 上限，无绕回链首。

## 本轮作为新会话完成的修复

- **FC-A**：`parse_retry_after` 整数分支拒绝带符号值（RFC 7231 `delay-seconds = 1*DIGIT`），
  `+3`/`-3` 归 unknown；同步两处测试断言。
- **FC-R**：`_process` 内 `retry` 未定义名改为 `retry_after`；验证拒绝路径恢复
  `quarantined` outcome（原误写 `execution_failed`，回归两个 `test_worker_runtime`）。
- **集成**：`test_demo_environment` 对中文 locale 下 pwsh 输出加 `errors='replace'`。

## 真实限制（未执行 / 保留）

- **FC-E 异构评审未执行**：dsh 首轮有真实调用但未产出报告文件，评审未达标；本轮未重跑，
  报告路径 `artifacts/ai-evidence/review-0927-fc-*.md` 仍空缺。
- **interface_live / task_live = not_run**：全部验证用本地 fixture / mock transport，
  无真实远端模型请求；`contract_local` 通过不代表蜂群 task_live。
- **86400 语义三选一决策槽未落**：仍待用户拍板。
- **`# TODO-HUMAN-REVIEW` 标记保留**：`swarm/breaker.py` 的四态转移表与半开竞争
  fencing（`try_claim_probe` / `_finish_probe`）仍需人工复核并发语义。
- **FC-D 边界测试为浅层**：14 项覆盖预算/熔断接口与五不变量断言，但未做
  worker 候选链端到端属性测试；真正 fallback 链的端到端验证依赖集成后人工/实测。
- **费用全程 unknown**：未伪造任何 usage/cost；欠费类失败如实分类。

## 分支与工作树

- 施工基座 `decentralized-swarm`（治理提交 `ee5d606`）未改业务代码。
- 第一代主线 `codex/morphogenesis-mainline` 全程只读未动。
- 集成树 `morph-fc-integration-0927` 为最终联合验证现场，工作区 clean。
