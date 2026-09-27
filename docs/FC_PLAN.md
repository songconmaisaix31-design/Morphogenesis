# FC 轮接手计划（2026-09-27）

事实源：本工作树 `AGENTS.md`、`QWEN.md`、`TASKS.md`；用户指定原终端
`term_6f3f7e62-386b-4926-b9e0-304ee7076b55` 的 FC 轮会话。第一代主线只读，
其已有 `docs/SWARM_SOL_PLAN.md` 改动保留。本轮不修改冻结文档或锁文件。

## 接手与已核实状态

### 认证恢复与首波接续（本次用户追加指令）

用户要求通过 aliyuncli 配置 DashScope API，并通过 computer-use 完成 Qoder 登录，
本轮保留原生引擎，不再等待 Codex 回退选择。

- aliyun 3.4.11 的既有默认身份经 STS GetCallerIdentity 验证；安装官方
  aliyun-cli-modelstudio 0.9.2 插件，使用北京默认工作空间。只创建一枚本轮专用
  `morphogenesis-fc-20260927` Key，ID=7471526；未重置/删除任何已有 Key。
  真实 CreateApiKey success=true，回执与秘密分别保存在 Git 忽略的私有目录，
  ACL 仅当前用户。对 OpenAI-compatible `/models` 一次查询 HTTP 200，包含
  qwen3-coder-plus 与 deepseek-r1；这只是认证/模型目录证据，不是蜂群 task_live。
- Qoder CLI 1.1.64 的 browser login，经 Tabbit 的真实 Google 账户选择与基本
  资料授权完成。网页“登录成功”与 CLI “Login successful”相符；随后
  `qoder status --output json` 的 logged_in=true、auth_source=local、
  login_method=browser，截图留在忽略目录。没有查找或导出 Qoder 令牌。
- FC-C 已派发 task_4aef0ca00aef / ctx_0df29cd2f91c，原树原分支；终端
  term_9680d646-f027-48ee-bcec-9da4ced2e1cf 经 trust 确认并有真实文件读取/开发活动。
  可见实际默认模型 Qwen3.8-Max；不把请求物种名等同于返回模型。
- FC-A 已派发 task_021476b9728f / ctx_908e3cf0b7a5，终端
  term_607d7ea6-bff8-464e-8111-1b8d7684457e 使用 Qwen Code 0.24.6 / DashScope
  qwen3-coder-plus。Orca 当前不能识别其 agent，worker-start 在任何任务创建前以
  agent_unconfigured 拒绝；核对 Task 列表后，按现行恢复指南 dispatch 不 inject、
  回传 preamble，再 terminal send。首个输入停留在 composer，读回后仅补 Enter；
  随后读取 AGENTS.md/QWEN.md 的实际工具活动，才记开工，未重发模型请求。
- 两轨均为复用外部终端，launch_token_hash 为空。Orca 的生命周期结算与真实业务
  交付分开复核；不得因 worker_done 机械拒收便宣布业务失败或伪造生命周期成功。
- 认证 Key 由仅本地 launcher 读入子进程环境，不传 argv、提示或 Git，不改全局
  用户环境。D/E 等接口提交与评审条件满足后出闸；最终独立集成仍未执行。
- FC-A 已产生分类模块 WIP，首批定向测试回执 13+3 项通过，但全量测试失败且
  原命令使用全局 Python。本次独立诊断工作树 `.venv/Scripts/python.exe -m pytest
  -q --maxfail=1` 得到 `No module named pytest`；未把环境不合格测试当作领域
  验收。Poetry 环境修复、未授权 uv.lock、读超时优先级、非 UTF-8 原始响应、
  Retry-After 完整语义及真正子进程回传测试已通过原 Dispatch 退回 FC-A；
  native Qwen Ctrl+Q 入队后读回“1 queued”，未重复启动或接管业务代码。
- dsh 原生 headless profile 的隔离配置通过 `--dump-config` 与 `--help`；模型
  配置指向 DashScope deepseek-r1，maxRetries=0，附加标题模型调用禁用。
  尚未发送 FC-E 模型请求，因此只记配置成功，不记 R1 审查或返回模型证据。

### 原接手快照（以下认证待办已由上节取代）

- 基线及施工分支：`decentralized-swarm@8c43f984f6d2eb77a2e8f3fd67d43ea0da37defa`。
- 继续既有 Run `run_e46ee274f7c9`；主控已绑定
  `term_e7feb562-1f4f-4045-9c1d-1b2ed3844b81`，generation=2；不新建重复 Run。
- FC-B 已由原 Worker 完成、推送并释放；本次 `git ls-remote` 核实远端
  `fc/fault-observation@92e1de321ba70e515d4587be716e71826af3ee43`。
  仅修改观察模块及其测试，工作树 clean。独立复验：52 项定向测试通过，
  strict 类型检查 82 个源文件通过。597 项全量测试与 build/SDK 是原 Worker
  的已归档回执，本次未重复执行，不混为本次全量复验。
- 原接手时 FC-A/C/D/E 尚无 Dispatch，也无未释放 Worker；四个原 worktree 和分支保留。
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
