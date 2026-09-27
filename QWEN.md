# QWEN.md — 失败接续链轮（FC 轮）任务上下文 v1.1

[文档层级] 本文件是本轮任务的 stigmergy 痕迹介质，居于 AGENTS.md（仓库宪法，
继续有效，含锁文件 T0 独占规则）与 docs/SWARM_*.md（机制契约）之下。本轮不改
动上述两处任何内容。

[轨名声明] 本轮 FC-A/B/C/D/E 为失败接续链五条临时轨，与历史 B/C/A/R/V/I 模块
所有权轨无关；历史轨规则继续有效，本轮轨写权以下表为准。

[施工基地] 全部基于 decentralized-swarm 分支的 worktree。cwd 主线
（codex/morphogenesis-mainline，第一代）保持只读。环境 Python >=3.12,<3.14
（本机 3.12.13），Poetry 管理。

[质量门禁] worktree 内执行：python -m pytest -q && python tools/typecheck.py
（strict mypy 覆盖 swarm/local_assets/orchestration）。不使用 morphogenesis check
（该命令属于第一代主线）。

[本轮主线] 把"一次任务执行=一次远端请求"扩展为"既有预算、租约、审计约束内的
受控若干次尝试"：失败分类 → 受控切换 → 共享故障状态 → 他者避让。

[五不变量——违反任意一条即实现无效]
1. 换 provider 不产生新任务预算，不清空已有消耗
2. 未知费用的预留永不被 fallback 自动释放
3. 外部 attempt 计数覆盖全部真实远端请求
4. 失去租约的 Worker 即使拿到成功结果也不得提交
5. 全候选不可用时在设定上限内有界退出，不绕回链首

[核心文件] orchestration/gateway_transport.py（传输层）· swarm/evomap_executor.py
（执行器，live 经 --request-child 子进程发请求）· swarm/budget.py（预算账本）·
swarm/worker_loop.py（Worker 主循环）· swarm/lease.py（租约）·
swarm/task_ledger.py（任务账本）· local_assets/（资产库）

[传输事实锚点] single_request 已用 httpx.Client（gateway_transport.py:43）；live
请求走子进程（evomap_executor.py:209-224）。GatewayResponse 当前未捕获 Retry-After
头与原始 body，FC-A 需补齐。respx 仅能注入进程内 transport 路径，无法跨子进程
mock。探测记录原文（含行号）存档于 TASKS.md。

[子进程分类决策] 已由人类队长拍板：分类在子进程内完成，raw body 不出子进程，
只回传 classification + evidence_hash（body 摘要哈希），详见 [FC-A 写权扩展]。

[提交约定] Conventional Commits + trailer `Swarm-Agent: <物种名>`。
[写权] 只允许写本任务"写权"清单内文件；读权限全仓库；越界改动视为无效提交。
[诚实红线] 禁止 usage=0 伪装零费用；语义缺失用 null，绝不伪造 0；未知远端效果
不自动重试。

[依赖与锁文件] 锁文件由 T0 独占，本轮 T0 缺位由人类队长代理。开工前一次性预装：
cachetools（主依赖）+ hypothesis / time-machine / pytest-asyncio / respx（dev 组）。
五轨对 pyproject.toml / poetry.lock 一律只读；发现缺依赖时登记到 TASKS.md
「依赖申请区」（依赖名、所属轨、用途、是否 dev 组），由队长批量执行。

[已知冲突对照——agent 不会主动告诉你的部分]

| 库 | 默认语义风险 | 重接线方式 |
| --- | --- | --- |
| tenacity/backoff | 自动重试会把 unknown_effect 也重试 | 不用，或仅 predicate 挂 confirmed_rejection；切换是 FC-C 的决策 |
| pybreaker | 进程内内存状态多 Worker 不可见 | 仅语义参考，持久化建在任务账本+原子认领 |
| cachetools.TTLCache | TTL 到期样本过早消失 | 窗口 ≥ 聚合周期，配 min_samples 下限 |
| httpx | ReadTimeout 等异常统一抛出 | 需单独分类为 unknown_effect |

## FC-A 传输与失败分类（Swarm-Agent: qwen-code；morph-fc-a / fc/failure-classify）

写权：orchestration/gateway_transport.py、orchestration/provider_adapters/（新建）
及其测试；另见 [FC-A 写权扩展]。其余只读。

1. 补齐 GatewayResponse：捕获 Retry-After 头与原始 body 字段。body 仅在子进程内部
   被分类器消费，不进入任何回传通道——此句写死，不得"顺手"把 body 带出子进程。
   保持现有函数签名与日志挂钩不变（传输底座已为 httpx.Client，无需重写）。
2. 新建 provider_adapters/：base.py 定义 ProviderAdapter 接口
   interpret(response, request_context) -> FailureClassification；evomap.py 与
   dashscope.py 分别实现两家语义。四枚举：confirmed_rejection / unknown_effect /
   budget_exhausted / capability_mismatch。适配器为纯函数模块：子进程 live 路径与
   进程内 mock 路径调用同一份实现。子进程内对 body 计算摘要哈希作为 evidence_hash
   （即 FC-B evidence_ref 来源），只回传哈希、不回传 body。
3. 百炼语义测试覆盖：HTTP 400 code="Arrearage"→confirmed_rejection；HTTP 403 code
   含 "AllocationQuota.FreeTierOnly"→confirmed_rejection；HTTP 429→confirmed_rejection
   且保留 Retry-After 头原值；连接中断、读超时、上游代理异常→unknown_effect。
4. Retry-After 解析支持 HTTP-date / 整数秒 / 缺失三种，无法解析归"未知冷却时长"。

测试分层：进程内 respx/MockTransport 做分类逻辑全量测试；另加小型子进程集成测试
（mock 模式 spawn --request-child）验证 classification/evidence_hash 确实经 Reply
回传；live 路径不可 mock 的红线原样保留。

复用：传输层一律 httpx；分类模型用 pydantic v2；新依赖走 TASKS.md 申请。
红线：不引入自动重试（切换是 FC-C 的决策，分类只陈述事实）；不动 budget.py 与
worker_loop.py；不伪造 usage。
完成：质量门禁全绿；四分类分支 + Retry-After 三格式测试全覆盖。

[FC-A 写权扩展] 增补 swarm/evomap_executor.py，但仅限两处：
(a) --request-child 分支调用 provider_adapters 分类、并将结果与 body 摘要哈希
    写入 Reply 输出（新增 classification 与 evidence_hash 字段）；
(b) 父进程侧解析上述新字段。
禁止触碰同文件内的预算、租约、认领、attempt 逻辑——发现需要改动时停止并记
TASKS.md。

## FC-B 观察记录（Swarm-Agent: codex；morph-fc-b / fc/fault-observation）

写权：swarm/fault_observations.py（新建）、tests/swarm/test_fault_observations.py。
禁止触碰 local_assets/ 与 metabolism/。

1. pydantic v2 定义 FaultObservation：observation_id、run_id、task_id、request_id、
   provider、model、failure_class、normalized_reason、retry_after_seconds（可空）、
   switched_to（可空）、cost_state（settled/unknown/reserved）、occurred_at、
   evidence_ref（原始响应摘要哈希，即 FC-A 回传的 evidence_hash）。
2. append-only JSONL 存储，写入幂等：同一 request_id+attempt 序号重放不产生重复
   记录。原子写只读参考 local_assets 现有风格，不 import 其内部。
3. 聚合视图：按 (provider, normalized_reason) 时间窗聚合输出给 FC-C；聚合不改原始
   观察——事实永久留存，聚合仅供路由。

复用：pydantic v2 + 现有 JSON 序列化依赖；禁止手写序列化与 uuid 生成。
红线：FaultObservation 永不进入 Gene/Candidate/发布管线；switched_to、cost_state
缺失即 null，禁填 0 占位。
完成：幂等写入、聚合正确性、JSONL 损坏容错三类测试全绿；质量门禁全绿。

## FC-C 共享熔断状态机（Swarm-Agent: qoder-quest；morph-fc-c / fc/breaker-state）

写权：swarm/breaker.py（新建）、tests/swarm/test_breaker.py。
禁止修改 worker_loop.py、pheromone.py。

任务：跨 Worker 四态熔断 insufficient_evidence → normal → suspended →
probing_recovery，持久化到共享存储（复用任务账本/原子认领），多 Worker 互相可见。

1. 进入 suspended：FC-B 聚合的 (provider, reason) 滑动窗口达阈值且样本 ≥ min_samples
   （默认5）；确认性欠费类可绕过样本数直入。
2. probing_recovery：冷却期满经现有原子认领竞争唯一探测名额；有 Retry-After 时
   初始探测时间=该提示。
3. 滑动窗口用 cachetools.TTLCache；窗口、阈值、min_samples、冷却全部配置注入，
   零魔法数字。
4. 状态转移写成纯函数 transition(state, event, params) -> (new_state, actions)。

复用：cachetools；pybreaker 仅语义参考（禁止直接使用）；持久化复用现有原子认领。
红线：熔断只影响"路由资格"，不影响预算与租约；禁止因"模型答错题"触发状态转移。
完成：全部转移路径 + 半开并发竞争（两 Worker 仅一人拿探测名额）+ Retry-After 到期
恢复测试全绿；核心转移函数标 # TODO-HUMAN-REVIEW。

## FC-D 边界测试与故障注入（Swarm-Agent: qwen-code 无头 -p；morph-fc-d / test/failure-chain）

写权：tests/swarm/test_failure_chain_boundaries.py（新建）、
tests/fixtures/fault_injection/（新建）。禁止改任何非测试代码；发现被测代码缺注入点
时停止并将缺口记入 TASKS.md。

1. 故障夹具：bailian_400_arrearage / bailian_403_freetier /
   rfc6585_429_with_retry_after / drop_mid_response / budget_insufficient /
   all_candidates_down。注入锚点：respx/MockTransport 注入进程内 transport 路径验证
   分类逻辑；另加子进程集成测试（mock 模式 spawn --request-child）验证 classification/
   evidence_hash 回传链路。live 子进程路径不可 mock。
2. hypothesis 属性测试：随机生成（失败序列 × 预算初值 × 租约状态），断言五不变量
   恒成立。
3. time-machine 控制时钟，验证熔断冷却与恢复探测严格由时间驱动。

复用：respx + hypothesis + time-machine + pytest-asyncio。
红线：禁止 mock 掉真实代码路径换绿；unknown_effect 断言必须显式检查"预留保留且
未发出新请求"。
完成：新测试全绿、存量测试零回归。

## FC-E 异构交叉评审（Swarm-Agent: deepseek-r1；只读无写权；morph-fc-e / fc/review-only）

仅输出报告至 artifacts/ai-evidence/review-0927-<track>.md（artifacts/ 不存在则新建
于本轨 worktree）。

维度：五不变量逐条指出可能违反点或"未发现"；复用正确性（tenacity/httpx/pybreaker/
cachetools 雷区：自动重试默认重试 unknown_effect、TTLCache 窗口短于样本积累、进程内
熔断多 Worker 不可见）；诚实性（usage=0 占位、伪造 switched_to、切换耗时填 0）；
边界语义（四分类与预算/租约处理矛盾）。

红线：不得提议"简化"任何不变量；认为不变量不合理时记为问题而非修改建议。
