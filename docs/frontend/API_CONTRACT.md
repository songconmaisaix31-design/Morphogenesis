# 环境观测台 · 后端接口契约（前端对接依据）

> 本文档是前端开发的**唯一数据契约**。前端从这里取数，字段名照抄，禁止在视图层自行改名字段或臆造语义。
> 后端事实源：`swarm/research/service.py`、`swarm/models.py`、`swarm/task_ledger.py`、`swarm/research/policy.py`、`swarm/research/records.py`、`swarm/research/feedback.py`。

---

## 1. 数据源总览（后端方法 → 前端用途）

| 后端方法 | 前端用途 |
|---|---|
| `research_package(project_id, limit)` | 任务沉积区（看板）、蜂群活动流、经验代谢、任务回放、拓扑快照 |
| `research_snapshot(project_id)` | 三轴结果、经验代谢、下一步 advisory、拓扑的分支数 |
| `research_advisory(project_id)` | 下一步机会（`opportunities`） |
| `research_context(project_id, limit, task_id, branch_id, overview)` | 专家意见（`notes` 中 `kind=expert_opinion`）、局部上下文 |
| `discover(limit)` | 候选任务窗口（可选，MVP 可只用 package.tasks） |
| `choose(task_id, reason)` | 成员选择（可选，MVP 通过 `research_choice` 事件体现） |

前端 MVP 只需 `research_package` + `research_snapshot` 两个数据源即可渲染全部界面。

---

## 2. `research_package` 返回结构

```jsonc
{
  "schema_version": "research-package/v1",
  "project_id": "p1",
  "limit": 100,
  "tasks_truncated": false,
  "context": { /* research_context(overview=true) 全量，见 §6 */ },
  "tasks": [ /* TaskRecord[]，见 §3 */ ],
  "assets": [],
  "persisted_observations": [],
  "generated_validation_reports": [],
  "executions": [
    {
      "task_id": "T-15",
      "run_id": "run39",
      "audit_sequence": 7,
      "recorded_result": { "execution_state": "succeeded", "scientific_verdict": "failed", "effect_state": "known" },
      "verified_result": { /* 重读归档后的结果 */ },
      "archive_status": "verified"   // "verified" | "refused"
    }
  ],
  "task_audit": [ /* 事件条目，见 §5 */ ],
  "audit_truncated": false,
  "adoption_receipts": [],
  "export_performed_external_io": false,
  "evidence_boundary": "per_record_provenance",
  "completion_claim": false
}
```

---

## 3. `TaskRecord`（`tasks[]` 元素，`TaskRecord.model_dump(mode="json")`）

```jsonc
{
  "swarm_id": "swarm-gen-1",
  "signal": {
    "signal_id": "sig-11",
    "task_id": "T-11",                      // 任务号，看板卡的标题
    "workspace": "/workspace",
    "scope": "science",
    "kind": "opportunity",
    "module": "research",
    "required_capability": "research",      // 或 "review" / "analyst"
    "payload": {
      "goal": "文献调研：软边界与硬边界的处理方法",  // 任务目标（看板卡正文）
      "project_id": "p1",
      "branch_id": "b-soft"                 // 所属分支（可选）
    },
    // Signal 还含展示无关字段：x/y/concentration/urgency/updated_at/decay_multiplier/completed
  },
  "status": "claimed",                       // 见 §4 枚举
  "dependencies": ["T-11"],                  // 依赖的前置任务 id
  "acceptance": { "research_proposal_id": "prop-11" },
  "attempts": 1,
  "condition_fail_count": 0,
  "token": 1,                                // fencing token（前端不展示）
  "owner": "w-04",                           // 认领者（agent 编号，核心叙事点）
  "expires_at": 1731000600.0,                // Unix 秒时间戳，null 表示未持有
  "created_at": 1730999400.0,
  "updated_at": 1730999400.0,
  "derived_from": null,                      // 派生的父任务 id
  "result_id": null,                         // 完成任务的结果 id（如 "ref:run39"）
  "result": null,
  "effect_applied": false
}
```

---

## 4. `status` 枚举 → 看板泳道映射

| status | 泳道 | 颜色 |
|---|---|---|
| `available` | 待认领 | 琥珀 |
| `partial` | 待认领 | 琥珀 |
| `handoff` | 待认领 | 琥珀 |
| `claimed` | 进行中 | 绿 |
| `submitting` | 进行中 | 绿 |
| `completed` | 已沉积 | 灰 |
| `failed` | 已沉积 | 红 |
| `blocked` | 已沉积 | 红 |

---

## 5. `task_audit` 事件条目（活动流 / 任务回放数据源）

条目结构：`{ "sequence": 1, "task_id": "T-11", "event": "claimed", "at": 1730999400.0, "body": { ... } }`

- `at` 是 **Unix 秒时间戳（float）**，前端展示时 `new Date(at * 1000)`。
- `sequence` 全局自增，任务回放按 `sequence` 升序。

### 5.1 两类事件（关键契约差异）

**A. 原生账本事件**（`event` 无前缀，`body` 含 `worker_id` 等）：

| event | body 关键字段 | 前端文案（示例） |
|---|---|---|
| `created` | derived_from | 任务创建 |
| `claimed` | worker_id, token | `w-04 认领 T-12` |
| `renewed` | worker_id, token, expires_at | 续租 |
| `released` | token, evidence | 释放 |
| `handoff` | from, to, token | `w-04 → w-02 转交` |
| `completed` | token, result_id | `w-05 完成 T-14 · 结果已留痕` |
| `failed` | token, evidence | `T-15 失败` |
| `blocked` | condition_fail_count | `T-15 阻塞` |
| `policy_selection` | actual_task_id, worker_id, token, ... | 策略选择 |
| `research_choice` | worker_id, selected, recommended_task_id, overridden | 选择 |
| `research_selection` | worker_id, actual_task_id, token, ... | 认领 |
| `research_execution` | run_id, worker_id, token, result | `隔离执行 run:run39` |
| `execution_confirmed` | request_id, token | `实验完成 · 效果 known` |
| `execution_unconfirmed` | request_id, token | 未确认执行 |

**B. `research.*` 事件**（`event` 带 `research.` 前缀，`body` 是完整 `ResearchEvent`，见下）：

| event | body.event_kind | body.payload 关键字段 | 前端文案（示例） |
|---|---|---|---|
| `research.note_submitted` | note_submitted | note_id, kind | `写入痕迹 note-1` |
| `research.contribution_accepted` | contribution_accepted | result_id | `经验命中 ref:run42`（绿色高亮） |
| `research.proposal_accepted` | proposal_accepted | proposal_id | 提议准入 |
| `research.branch_sleep` | branch_sleep | correction_id, reason | 分支休眠 |
| `research.branch_downgrade` | branch_downgrade | correction_id, reason | 分支降级 |
| `research.branch_reopen` | branch_reopen | correction_id, reason | 分支重开 |
| `research.contribution_superseded` | contribution_superseded | result_id, reason | 贡献取代 |
| `research.project_created` / `research.branch_created` | 同名 | — | 项目/分支创建 |

### 5.2 `ResearchEvent`（`research.*` 事件的 `body` 结构）

```jsonc
{
  "event_id": "ev-2",
  "project_id": "p1",
  "branch_id": "b-soft",
  "task_id": "T-13",
  "source_ref": "note-1",
  "actor": { "role": "builder", "instance": 1 },  // AgentId，无 worker_id 字符串
  "at": 1730999460.0,
  "schema_version": "research-v1",
  "provenance": "live",          // live | mock | contract_local
  "event_kind": "note_submitted",  // 不带 research. 前缀
  "payload": { "note_id": "note-1", "kind": "observation" },
  "correlation_ref": null
}
```

**前端"谁"（actor）统一提取规则**：优先 `body.worker_id`，其次 `body.from`，最后 `body.actor`（格式化成 `role-instance`，如 `builder-1`）。

---

## 6. `research_context`（`research_package.context`，overview=true）

```jsonc
{
  "project": { "project_id": "p1", "goal": "...", "allowed_domains": [], "data_bounds": {}, "authorization_ref": null, "milestones": [], "created_at": 0 },
  "limit": 100,
  "selection": { "mode": "overview", "reason": "overview", "task_id": null, "branch_id": null, "read_only": true, "claim_requires_recheck": true },
  "constraints": { "authorized_scopes": [], "capabilities": [], "data_bounds": {}, "actions": [], "context_grants_execution": false },
  "notes": [ /* ResearchNote[]，见下 */ ],
  "hypotheses": [], "proposals": [], "tasks": [], "branches": [],
  "notes_unverified": [], "notes_verified": [],
  "events": [],
  // 各集合带 *_truncated 标记
  "research_v1": { /* research_snapshot 结构，见 §7 */ }
}
```

### ResearchNote（专家意见来源：`kind === "expert_opinion"`）

```jsonc
{
  "note_id": "note-op-1",
  "project_id": "p1",
  "branch_id": "b-soft",
  "hypothesis_id": null,
  "task_id": null,
  "kind": "expert_opinion",       // observation/hypothesis/supporting_evidence/opposing_evidence/dispute/expert_opinion/cross_domain_link
  "actor": { "role": "builder", "instance": 0 },
  "signer": "Dr. Y",               // 仅 expert_opinion 有署名
  "source_refs": [ { "source_id": "...", "kind": "pdf", "identifier": "...", "version": "v3", "license": "CC-BY-4.0", "retrieval": "present", "location": "p.4", "excerpt": "..." } ],
  "text": "倾向软边界方法 A，但未提供独立数据",
  "applicability": {},
  "review_state": "unverified",    // 专家意见恒为 unverified（意见≠事实）
  "references": [],
  "created_at": 0
}
```

---

## 7. `research_snapshot` 返回结构

```jsonc
{
  "policy_version": "research-v1",
  "advisory_only": true,
  "claim_requires_recheck": true,
  "project_id": "p1",
  "exploration_fraction": 0.20,
  "three_axis": {
    "execution": { "succeeded": 3, "failed": 1, "unknown": 0 },
    "hypothesis": { "supported": 2, "refuted": 1, "not_evaluated": 1 },
    "contribution": { "accepted": 3, "proposed": 2, "superseded": 1 }
  },
  "results": [ /* ThreeAxisResult[] */ ],
  "contributions": [ /* ThreeAxisResult[]，contribution=accepted */ ],
  "effective_contributions": [ /* ThreeAxisResult[]，superseded 已标 */ ],
  "corrections": [ /* CorrectionEvent[] */ ],
  "supersessions": [ /* SupersessionEvent[] */ ],
  "trusted_results": [ /* ThreeAxisResult[] */ ],
  "branches": [ /* Branch[]，见 §8 */ ],
  "opportunities": { /* RouteOpportunityPlan，见 §9 */ }
}
```

### ThreeAxisResult

```jsonc
{
  "result_id": "ref:run42",
  "report_id": "rep-42",
  "task_id": "T-13",
  "actor": "w-05",
  "source_ref": "paper v3",
  "provenance": "mock",
  "execution": "succeeded",
  "hypothesis": "supported",
  "contribution": "accepted",
  "asset_id": "a-13",
  "branch_id": null,
  "reviewer": "reviewer-1",
  "at": 1731000120.0,
  "reasons": []
}
```

### 三轴枚举值

| 轴 | 枚举 |
|---|---|
| execution | `not_run` / `running` / `succeeded` / `failed` / `cancelled` / `unknown` |
| hypothesis | `not_evaluated` / `supported` / `refuted` / `inconclusive` / `disputed` |
| contribution | `proposed` / `accepted` / `rejected` / `superseded` |

### CorrectionEvent

```jsonc
{ "event_id": "e-1", "branch_id": "b-hard", "kind": "sleep", "reason": "...", "source_ref": "ref:run39", "actor": "reviewer-1", "at": 0 }
// kind: sleep | downgrade | reopen
```

### SupersessionEvent

```jsonc
{ "event_id": "e-2", "result_id": "ref:run39", "superseded_by": null, "reason": "...", "source_ref": "...", "actor": "...", "at": 0 }
```

---

## 8. `Branch`（`branches[]`）

```jsonc
{
  "branch_id": "b-soft",
  "status": "testing",          // proposed/exploring/testing/supported/disputed/dormant/refuted/archived
  "conditions": {},
  "parent_id": null,
  "authorized": true,
  "supported_by": ["ref:run42"], // 支持的贡献 result_id 列表
  "refuted_by": ["ref:run39"],   // 反驳的贡献 result_id 列表
  "applicability": 1.0,
  "goal_relevance": 1.0,
  "risk": 0.0,
  "known_cost": null
}
```

---

## 9. `RouteOpportunityPlan`（`opportunities`）

```jsonc
{
  "version": "research-v1",
  "exploration_fraction": 0.20,
  "total_share": 1.0,
  "opportunities": [
    {
      "branch_id": "b-soft",
      "eligible": true,
      "share": 0.48,              // 机会份额 [0,1]
      "factors": { "evidence": 1.0, "applicability": 1.0, "goal_relevance": 1.0, "risk": 0.0, "support_count": 1, "refute_count": 0, "exploration_floor": 0.5 },
      "known_cost": null,
      "supported_by": ["ref:run42"],
      "refuted_by": [],
      "reasons": ["eligible"]     // eligible/insufficient_evidence/unknown_cost/refuted_under_conditions/dormant/archived/out_of_scope
    }
  ],
  "reasons": []
}
```

---

## 10. 前端数据层接入约定

前端统一通过一个数据层模块取数（`fetchPackage` / `fetchSnapshot` / `fetchReplay` / `subscribeActivity`），返回结构与本文档逐字段一致。开发期用 mock（JSON 严格对齐本文档字段），接真实后端时只替换数据层实现（指向真实 HTTP 转发），视图组件零改动。

- `fetchPackage()` → §2
- `fetchSnapshot()` → §7
- `fetchReplay(taskId)` → `{ task_id, task, audit[], executions[], observations[], adoption_receipts[] }`（从 package 按 task_id 切片）
- `subscribeActivity(onEvent)` → 订阅活动流（onEvent 收到 `{ at, event, body }`），返回取消函数；真实后端轮询 `task_audit`，开发期 mock 定时器循环播放

### 复合指标口径（前端必须在 UI 小字标注，不得拍脑袋）

| 指标 | 口径 |
|---|---|
| 活跃数 | tasks 中 status ∈ {claimed, submitting} 的数量 |
| 空闲数 | tasks 中 status ∈ {available, partial, handoff} 的数量 |
| 本轮沉淀 | snapshot.contributions 数量 |
| 复用次数 | package.adoption_receipts 数量 |
| 加速 | (沉淀 + 复用) / 沉淀（沉淀为 0 时显示 `—`） |
| 时延 | 本地响应 p95（无真实值显示 `—`） |

---

## 11. live HTTP 端点（`src/env-observatory/server.py`，FastAPI）

数据层 live 实现的同源端点。全部只读（唯一例外：Wayfinder POST）；后端仅调用
`swarm/research/service.py` 的只读方法，不触发 propose/claim/accept/execute/apply。

| 端点 | 方法 | 返回 |
|---|---|---|
| `/api/research/package?project_id=` | GET | §2（`research_package`） |
| `/api/research/snapshot?project_id=` | GET | §7（`research_snapshot`） |
| `/api/research/advisory?project_id=` | GET | §9（`research_advisory`） |
| `/api/research/context?project_id=` | GET | §6（`research_context(overview=true)`） |
| `/api/research/replay/{task_id}?project_id=` | GET | §10 replay 切片（等价前端本地切片语义；observations 取 `context.notes` 按 task_id 过滤，receipts 兼容 `adopting_task_id` 与 `context.task_id` 两种形状） |
| `/api/research/activity?since_seq=&project_id=` | GET | `{ "events": [§5 条目…], "latest_seq": N }` —— sequence > since_seq 的 task_audit 增量，供 `subscribeActivity` 轮询 |
| `/api/wayfinder/ask` | POST | `{ "question": "…" }` → `{ "answer": "…" }`（pi Wayfinder，唯一写入口） |
| `/` 及静态文件 | GET | `env-observatory.html`（`/`）与白名单静态文件 |

`project_id` 可省略（默认 HostConfig 绑定的项目，再缺省 `p1`）。

### 安全约束（与 stdlib 前代一致）

- 非 GET/HEAD（除 `/api/wayfinder/ask` POST）→ **405**
- GET/HEAD 携带请求体 → **413**
- 所有响应带 `X-Content-Type-Options: nosniff`、`X-Frame-Options: DENY`、`Referrer-Policy: no-referrer`
- 未配置 `OBSERVATORY_HOST_CONFIG` → `/api/research/*` 返回 **503**（静态页仍可用，前端回退 mock）

### 前端数据层行为（live 接线版）

- `location.protocol` 为 http(s) 时 fetch 上述端点，成功即在返回对象上标 `source: 'live'`；
- file:// 打开或 fetch 失败 → 回退内联 mock（`buildPackage`/`buildSnapshot`），标 `source: 'mock'`；
- `subscribeActivity`：live 模式轮询 `activity?since_seq=`（基线为 package 中最大 sequence，3.2s 间隔，新事件 `live: true`）；单次轮询失败静默重试，不回退 mock（避免伪 live 事件）；mock 模式保持原定时器循环播放；
- `window.EnvData.getSource()` 返回 `'live' | 'mock'`，供调试面板/控制台确认数据来源。 |

---

## 12. 探测类端点（Agent / Compute，真实执行本机与云端命令）

这三个端点与 §11 的区别在于：它们**真的在本机起子进程**（`nvidia-smi`、`docker`、`wsl`、
`kubectl`、`aliyun`），因此都有 TTL 缓存与超时预算。口径同 §10：拿不到真实值就返回
`null` / `—`，**绝不用 0 或演示数据填充**。

| 端点 | 方法 | 说明 | 缓存 |
|---|---|---|---|
| `/api/health` | GET | 探活：`status` / `pid` / `uptime_s` / `service_ready` / `probe_enabled` / `routes`。**不起子进程、不碰 SQLite**，否则探活本身会成为故障源 | 无 |
| `/api/agents/probe?refresh=` | GET | 遍历 `orchestration.native_agents.registry.REGISTRY`，对每个运行时真实执行 `<cli> --version` 与 `<cli> auth status`。只回显解析出的 argv，**永不回显 auth 的 stdout** | 60s |
| `/api/compute/local?refresh=` | GET | 本机显卡：`nvidia-smi` 优先（型号/总显存/已用/驱动/利用率），Windows 下退回 `Win32_VideoController`（仅型号与驱动） | 30s |
| `/api/compute/providers` | GET | 每个厂商槽位的真实状态：`ready` / `no_gpu` / `probe_failed` / `cli_missing` / `not_configured` / `not_integrated`。**没有"回退到演示数据"这一态** | 无 |
| `/api/compute/aliyun?region=&limit=&families=&refresh=` | GET | 真实 ECS GPU 规格（`DescribeInstanceTypes`）+ 真实 CNY 小时价（`DescribePrice`） | 300s |
| `/api/compute/instances?regions=&refresh=` | GET | **Agent 运行环境**清单，见下 | 180s |

### 12.1 `/api/compute/instances`（Agent 运行环境）

回答"agent 到底能跑在哪台机器上"，覆盖五类真实来源：

| `kind` | 来源 | 探测方式 |
|---|---|---|
| `host` | 本机 | `os` / `platform` + ctypes 物理内存 + 复用 `/api/compute/local` + registry 存在性检查 |
| `container` | Docker | `docker version` 判守护进程，`docker ps -a` 列容器 |
| `wsl` | WSL 发行版 | `wsl -l -v`（输出为 **UTF-16LE**，按字节读取后解码） |
| `k8s` | Kubernetes 上下文 | `kubectl config get-contexts -o name` |
| `cloud-vm` | 阿里云 ECS | `DescribeInstances` 逐地域 |

每个环境条目：

```jsonc
{
  "id": "ecs:i-2ze2nztd89vevmw21wif",
  "kind": "cloud-vm", "provider": "aliyun", "name": "iZ2ze2nztd89vevmw21wifZ",
  "status": "running",            // running / stopped / available / daemon_stopped / no_context …
  "platform": "Ubuntu  24.04 64位",
  "cpu_cores": 4, "memory_gib": 8.0,          // 拿不到就是 null
  "gpu_count": 0, "gpu_model": null, "vram_gib": null,
  "agent_ready": null,                        // 只有本机能确定（查 registry）
  "runtimes": [],
  "detail": {
    "region": "cn-beijing", "zone": "cn-beijing-l", "instance_type": "ecs.c9a.xlarge",
    "charge_type": "PrePaid", "public_ip": "47.93.118.110", "private_ip": "172.31.185.72",
    "expired_time": "2026-10-14T16:00Z", "source": "aliyun ecs DescribeInstances"
  }
}
```

信封：`{ environments[], counts{}, total, runnable, ecs_regions_checked[], ecs_errors[], notes[], source }`，
`source` 为 `live-probe` 或 `probe-disabled`。

**两个实测踩到的坑（改动时不要退回）：**

1. **`DescribeInstances` 的 `TotalCount` 不可信** —— `cn-beijing` 返回 `TotalCount=0`
   但 `Instances.Instance` 里确实有 1 台。只认数组长度。
2. `VpcAttributes.PrivateIpAddress` 是**嵌套两层的** `{"IpAddress": {"IpAddress": [...]}}`，
   而 `PublicIpAddress.IpAddress` 是 `{"IpAddress": [...]}`。取值必须做形状容错。

地域轮询有总时长预算（`OBSERVATORY_ECS_BUDGET`，默认 45s），单地域超时
`OBSERVATORY_ECS_TIMEOUT`（默认 20s）、地域列表 `OBSERVATORY_ECS_REGIONS`。
`DescribePrice` **必须带** `--SystemDisk.Category`，否则报
`InvalidSystemDiskCategory.ValueNotSupported`。

---

## 13. 运行与稳定性（`watchdog.py`）

面板会被长时间开着，而它曾**无声消失**：子进程没有 traceback、日志只有启动横幅 ——
这是被外部终止（机器休眠、父 shell 被回收、OOM）的样子，不是崩溃。所以用看护而不是加更多
`try/except`：

```
python src/env-observatory/watchdog.py --port 8100 --log D:\tmp\watch-server.log
```

- 轮询 `/api/health`（故意做得很轻）；进程死了就拉起，进程活着但连续 `--unhealthy-limit`
  次探活失败则判定卡死并重启；
- 指数退避（`--restart-delay` → `--max-restart-delay`），坏配置不会打满 CPU；
- **端口预检**：端口被别人占着时直接退出并说明，而不是反复 spawn 出一堆绑定失败；
- 自动补 `OBSERVATORY_HOST_CONFIG`（指向同目录 `.state/host-config.json`）与
  `DASHSCOPE_API_KEY`（读 `~/.bailian/config.json`，不覆盖已有值、不打印密钥）；
- `OBSERVATORY_PROBE=0` 可整体关闭外部探测，让面板在零子进程下运行。

直接 `python src/env-observatory/server.py` 仍然可用，看护只是外层包装。

> Windows 上 `.venv\Scripts\python.exe` 是**转发 shim**，它会再拉起真正的 uv 解释器作为
> 子进程。所以 `Popen` 拿到的 pid 是 shim、而真正持有 socket 的是它的子进程 ——
> 看护日志里会同时打印两者（`shim pid X -> socket pid Y`），不要把它误读成两个实例。

