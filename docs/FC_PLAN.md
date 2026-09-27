# FC 轮接手计划（2026-09-27）

事实源：本工作树 `AGENTS.md`、`QWEN.md`、`TASKS.md`；用户指定原终端
`term_6f3f7e62-386b-4926-b9e0-304ee7076b55` 的 FC 轮会话。第一代主线只读，
其已有 `docs/SWARM_SOL_PLAN.md` 改动保留。本轮不修改冻结文档或锁文件。

## 接手与已核实状态

- 基线及施工分支：`decentralized-swarm@8c43f984f6d2eb77a2e8f3fd67d43ea0da37defa`。
- 继续既有 Run `run_e46ee274f7c9`；主控已绑定
  `term_e7feb562-1f4f-4045-9c1d-1b2ed3844b81`，generation=2；不新建重复 Run。
- FC-B 已由原 Worker 完成、推送并释放；本次 `git ls-remote` 核实远端
  `fc/fault-observation@92e1de321ba70e515d4587be716e71826af3ee43`。
  仅修改观察模块及其测试，工作树 clean。独立复验：52 项定向测试通过，
  strict 类型检查 82 个源文件通过。597 项全量测试与 build/SDK 是原 Worker
  的已归档回执，本次未重复执行，不混为本次全量复验。
- FC-A/C/D/E 尚无 Dispatch，也无未释放 Worker；四个原 worktree 和分支保留。
- Run objective 的“统一用 codex”与用户后续指定 CLI 指令冲突。原会话最后要求
  “用cli，去装对应的cli”，以该指令与 QWEN.md 的轨道安排为准。
  qwen/qoder/dsh 命令均存在；原终端报告认证阻塞。当前明确命名的凭据环境变量
  均未配置，但这不单独证明 CLI OAuth/本地认证不可用。未扫描历史寻找秘密，
  未执行模型请求。引擎回退偏好已询问，尚待答复。
- CLI 只读检查：qwen 与 dsh 帮助可读；qoder 输出帮助后出现
  `Assertion failed: !(handle->flags & UV_HANDLE_CLOSING), file src\win\async.c, line 94`。
  未因帮助可读就宣称 Qoder 可启动工作；认证与运行能力仍待确认。

## 所有权与接续顺序

| 轨 | 原 worktree / branch | 独占写权 | 接续条件 |
|---|---|---|---|
| FC-A / qwen | morph-fc-a / fc/failure-classify | gateway_transport.py、provider_adapters/** 及对应测试；evomap_executor.py 仅 QWEN.md 指定两处 | 认证可用或用户明确引擎替代；分类及 evidence_hash 回传接口先交付 |
| FC-B / codex | morph-fc-b / fc/fault-observation | fault_observations.py、test_fault_observations.py | 已交付；领域返修仍归原轨 |
| FC-C / qoder | morph-fc-c / fc/breaker-state | breaker.py、test_breaker.py | FC-B 已具备；认证或引擎决策后接入精确 B SHA |
| FC-D / qwen | morph-fc-d / test/failure-chain | test_failure_chain_boundaries.py、tests/fixtures/fault_injection/** | A 首个接口提交后启动；缺注入点按 TASKS.md 留痕，不改生产代码 |
| FC-E / dsh | morph-fc-e / fc/review-only | artifacts/ai-evidence/review-0927-fc-*.md | A/B/C/D 各阶段 diff 滚动评审；不写业务代码 |
| 主控 | decentralized-swarm | 本计划、TASKS.md 的状态及决策记录 | 协调、核对真实回执、最终验收；不写业务代码 |
| 最后集成 | 待四轨领域交付后确定一个独立集成 Agent | exact-SHA 普通合并、必要导入/类型胶水与验收报告 | 不接管领域逻辑；缺陷退原所有者 |

## 接手发现的验收缺口

目前 `_process()` 仅调用一次 `executor.execute()`，预算按 request_id 预留并以
持久化 reservation 数量计 attempt；FC-A 与 FC-C 的授权写权明确不覆盖
worker_loop.py 或预算/attempt 逻辑。分类、观察与熔断模块单独完成，不能证明
“受控切换”和“他者避让”已进入执行路径。该缺口需由领域轨报告到 TASKS.md，
确认后续接入所有者及窄写权；集成 Agent 不得把它作为少量胶水擅自实现。

## 验收与停止条件

沿用每轨本地锁环境、全部适用 pytest、strict 类型检查，以及最终 build/SDK/分发。
先保留全部五不变量，再进行 A/B/C/D 联合边界验证。未知 usage/cost/远端效果保持
unknown/null 与原预留，禁止自动重试或换模型绕过。真实 API 调用不因引擎选择
而自动启动；contract_local、interface_live、task_live 分别结算。
核心纯函数的 TODO-HUMAN-REVIEW、他者避让实录和原用户 86400 语义决策槽仍未完成。
最终普通 exact-SHA 合并、逐阶段 commit + push；不合入第一代主线、不改变部署。
