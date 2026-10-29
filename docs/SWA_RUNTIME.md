# Morphogenesis + Swarm CLI

每个 Morphogenesis Worker 独立读取共享任务环境，按能力与反馈选任务、竞争认领、续租、验证结果并更新反馈。Swarm CLI 负责调用该 Worker 配置的原生 Agent 和模型。观察者读取状态；启动器只创建进程和汇总结果，不选择任务。

| 组件 | 复用内容 |
| --- | --- |
| Morphogenesis Worker | `Worker`、`TaskLedger`、`Router`、`PheromoneField`、预算和候选验证 |
| SWA 执行适配器 | `swarm/swa_executor.py`，把已认领任务送入独立 SWA Run |
| 多成员入口 | `swarm/swa_runtime.py`，从配置创建独立进程 |
| 项目状态 | 共享任务、租约、预算、资产与反馈；成员身份分别保存 |

这是同机共享持久化、各成员独立决策的系统。SQLite WAL 提供同机并发协调；跨机器状态复制、网络分区与故障切换不在本次实现内。

## 当前接入范围

适配器接收已有 `DataTask`，要求模型返回 `{"answer": <JSON>, "adopted_asset_ids": []}`。结果通过既有 `DataProposal`、候选物化和任务的 `ValidationPolicy` 检查后提交。适配器不执行模型生成的代码，模型退出或 SWA Run 完成不代替 Morphogenesis 的结果验证。

代码接口固定参考 SWA [PR #10](https://github.com/songconmaisaix31-design/swarm-anything/pull/10) 的 [733ee08fb694fe8d8719693ca6b6e05432e005b2](https://github.com/songconmaisaix31-design/swarm-anything/tree/733ee08fb694fe8d8719693ca6b6e05432e005b2)：

1. `swa run --strict` 启动单个原生 Worker，并等待同一 Run 的完成与资源释放。
2. `swa task result` 取得匹配 Dispatch 的完整原生最终文本。
3. `swa controller close` 关闭本次控制端。

实际命令及返回结构依据 `cmd/swa/run_flow.go`、`runtime/swa-orca/src/run-view.ts`、`run-settlement.ts` 和 `controller-runtime.ts`。SWA 当前 `main` 及独立 Windows PR #12 不据此获得兼容性结论；部署时选择具有本接口且实际验证通过的安装版本。

当前 SWA 原生策略没有外部 MCP 传入路径，因此这里由 Morphogenesis Worker 程序决定任务，原生 LLM 完成指定任务。原有 `python -m swarm.research --config ...` 科研 MCP、实验、复现与继承能力继续保留，直接交给 SWA 托管 Agent 使用还需要受控工具桥。本适配器的 JSON 任务验收不代表科研闭环验收。

## 运行条件

- 安装本分支 Morphogenesis 的 Python 与根 Node 依赖，使用仓库声明的版本范围及锁文件。
- 已安装带上述 `run` 协议的 SWA，后台可访问；已取得对应项目的 `SWA_PROJECT_TOKEN`，通过环境变量传入，不放进配置或仓库。
- SWA 项目已批准专用工作目录、指定 Agent 与模型。专用工作目录与 Morphogenesis 源码、目标仓库、状态目录分别存放。
- 使用新建目标 Git 分支和新状态目录。所有 Worker 共享 `swarm_id`、目标、状态与预算，但具有不同 `agent.instance`；每个成员可以选择不同 CLI/模型。

SWA 原生 usage 记录格式尚未统一，适配器保留 `usage=null` 和实际结果证据，不从累计记录推算账单。默认 `allow_unknown_usage=false` 会阻止本次结果完成后的晋级。运营者若明确接受有限运行中的未知计量，可在运行前设置 `allow_unknown_usage=true`；`allow_unknown_cost` 同样必须显式选择。预算预留额度属于本地准入，不是提供商强制费用上限。程序不会自动改变这些字段。

## 创建可复用的运行配置

下面脚本只创建两项可独立验证的 JSON 任务与两个成员配置，不调用模型。将其保存为目标源码目录之外的 `seed_swa.py`，填写真实路径、SWA 项目 ID、已批准的 Agent 和模型；从 Morphogenesis 已安装的 Python 环境运行。`root` 必须不存在。

```python
import json
from pathlib import Path

from contracts.identity import AgentId
from local_assets.models import FileExpectation, ValidationPolicy
from local_assets.paths import git
from swarm.evomap_executor import canonical_answer
from swarm.models import BudgetPolicy, Locality, RunLimits, Signal
from swarm.pheromone import PheromoneField
from swarm.swa_executor import SwaConfig
from swarm.swa_runtime import WorkerEntry
from swarm.task_ledger import TaskLedger
from swarm.worker_loop import WorkerConfig

root = Path("/absolute/new-morph-run")
swa_binary = Path("/absolute/installed/swa")
swa_workdir = Path("/absolute/approved-swa-workdir")
swa_project = "REPLACE_WITH_APPROVED_PROJECT_ID"
endpoint = "http://127.0.0.1:8787"
members = [("opencode", "REPLACE_WITH_PROVIDER/MODEL"),
           ("pi", "REPLACE_WITH_PROVIDER/MODEL")]

root.mkdir(parents=True, exist_ok=False)
target, state = root / "target", root / "state"
target.mkdir()
git(target, "init", "-b", "morph-swa-data")
for scope in ("sum", "sort"):
    (target / scope).mkdir()
    (target / scope / "answer.json").write_text("null\n", encoding="utf-8")
git(target, "add", ".")
git(target, "-c", "user.name=Morphogenesis", "-c", "user.email=local@example.invalid",
    "commit", "-m", "Initialize bounded JSON task workspace")
limits = RunLimits(max_tasks=2, max_attempts=2, max_attempts_per_task=1,
                   max_derived_tasks=0, max_runtime_seconds=600.0)
budget = BudgetPolicy(max_cost_usd=1.0, unbounded_reservation_usd=0.25,
                      limits=limits, allow_unknown_usage=False, allow_unknown_cost=False)
ledger = TaskLedger(state / "tasks.sqlite3", "swa-data-example", limits=limits)
field = PheromoneField(state / "field.sqlite3", ledger=ledger)
for name, instruction, incoming, expected in [
    ("sum", "Return the sum as a JSON integer.", [2, 3, 5], 10),
    ("sort", "Sort ascending, preserving duplicates.", [3, 1, 3, 2], [1, 2, 3, 3]),
]:
    path = name + "/answer.json"
    signal = Signal(task_id=name, signal_id=name, workspace=str(target), scope=name,
                    module=name, kind="opportunity", required_capability="json",
                    payload={"instruction": instruction, "input": incoming, "output_path": path})
    policy = ValidationPolicy(version="swa-example-v1", expectations=(
        FileExpectation(path=path, content=canonical_answer(expected)),))
    ledger.enqueue(signal, acceptance={"validation_policy": policy.model_dump(mode="json")})
    field.deposit(signal)
entries = []
for instance, (cli, model) in enumerate(members):
    worker = WorkerConfig(state=state, target=target, swarm_id="swa-data-example",
        agent=AgentId(role="builder", instance=instance), budget=budget,
        locality=Locality(workspace=str(target), authorized_scopes=("sum", "sort")),
        capabilities={"json": 1.0}, energy_policy="claim", routing_strategy="v0.1",
        max_idle=100, idle_seconds=0.5, seed=instance)
    swa = SwaConfig(executable=swa_binary, endpoint=endpoint, project=swa_project,
                    workdir=swa_workdir, agent=cli, model=model)
    entries.append(WorkerEntry(worker=worker, swa=swa).model_dump(mode="json"))
(root / "members.json").write_text(json.dumps(entries, indent=2), encoding="utf-8")
print(root / "members.json")
```

两个成员都能看见并认领这两项任务，实际归属由各自选择与原子认领决定。不同 scope 允许并行；成员数量不保证负载平均。替换问题、数据、能力、范围和可信验证条件即可复用同一执行方式。此例是工程验收数据，不表示科研发现。

检查并按实际授权设置生成配置中的预算策略后运行：

```bash
python -m swarm.swa_runtime --config /absolute/new-morph-run/members.json
```

入口输出每个进程的实际状态及共享账本的任务计数。只有所有进程正常结束且全部已登记任务完成时退出 0；等待、预算停止、任务未完成或未知效果退出非零。这里的完成指既有 JSON 验证流程，不代表科学结论成立。

## 失败与后续验收

每次调用前保存原始请求 ID。超时、取消、结果不完整或身份不匹配均保留未知效果，不自动重新派发。根据专用 SWA 工作目录中的 `morph-*/invocation.json`，使用原项目和请求 ID 执行 `swa request show`；有原控制端身份时按 SWA 原命令检查该 Run。Ctrl+C 结束本启动器的进程后，外部 SWA 任务仍须按原身份核对，不能以本地退出推断原生任务已停止。

本次验证范围为本地协议、候选与预算行为；真实 SWA 服务和异构模型尚未通过本适配器验收。后续使用同一安装完成：两个实际 Worker 独立认领、完整成果取得、指定停止、原请求恢复查询、重复认领拒绝及旧租约拒绝，再记录安装版本、原生 Agent、模型和实际结果。无需重新编写路由、租约或账本。
