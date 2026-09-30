# 科研 MCP 宿主契约

启动：`python -m swarm.research --config ABS_TRUSTED_JSON`。官方 MCP Python SDK v1 `FastMCP`，stdio；运行不导入或调用 Orca。A 使用每次启动的原生 MCP 配置，不改 HOME、账号或全局设置。

宿主 JSON 必需字段：`ledger_path`, `swarm_id`, `workspace`, `worker_id`, `agent`（既有 role/instance）, `authorized_scopes`, `capabilities`, `assets_root`, `evidence_root`。路径均绝对路径；可选 `project_context` 与 `experiment_backend`。配置、账本、资产数据库及原始实验归档必须由宿主保护，放在模型可写项目目录之外。MCP 是工具参数边界，并不防止同一操作系统用户绕过工具直接写 SQLite；原生权限/沙箱负责这一边界。

`experiment_backend` 可配置 `domain`（默认127.0.0.1:8097）、`protocol`（http/https）、`api_key_env`（受保护环境变量名，不写secret文本）、`use_server_proxy`、`codeinterpreter`、`notebook`、`volumes`（开关须字符串true/false）。后端为 C `ExperimentExecutor(OpenSandboxBackend(...))`，用 `asyncio.to_thread` 执行，用 `read_result(..., expected_plan=..., expected_context=...)` 重新读取。`max_experiments_per_task` 默认1、最大10，由宿主配置；计数使用原task_audit，在 begin_execution 原事务中检查，不能并发越过，也不是新Attempt系统。

claim回包保留原Lease字段，并加既有 `AttemptId` 的 `attempt_id`，其中 agent 来自宿主、attempt 来自原TaskLedger.attempts。A保留原native会话日志并绑定该回包，缺失native session/usage/cost保持unknown。

```json
{
  "ledger_path": "C:/research-state/tasks.sqlite3",
  "swarm_id": "research-demo",
  "workspace": "C:/research-project",
  "worker_id": "native-author",
  "agent": {"role": "builder", "instance": 0},
  "authorized_scopes": ["science"],
  "capabilities": ["research"],
  "assets_root": "C:/research-state/assets",
  "evidence_root": "C:/research-state/experiments",
  "project_context": "NIST NumAcc4 sample variance experiment"
}
```

最终11个工具按协作契约收敛：`discover_tasks`、`project_context`、`lease_task(action=claim|renew|release|handoff)`、`search_evidence`、`research_experiment(action=request|run|result)`、`research_candidate(action=submit|validate_files)`、`verify_research`、`complete_research_task`、`approve_candidate`、`inherit_experience`、`apply_candidate`。action只允许其对应字段，跨action参数拒绝；通过官方metadata读取当前形状。科研验证、准入和实际采用保留独立工具，避免将多种科学事实混成一个布尔结果。

工具无 worker/agent 身份、数据库路径、任意验收脚本或 passing/approved/metric 输入。`discover_tasks` 仅查询可认领任务；`lease_task(action=claim)` 显式主动认领。context/search 是发现和检索，不能据此记录采用。renew/release/handoff 使用绑定身份和当前 fencing token；handoff 不自动派给下一位。

科研任务通过宿主预先 `TaskLedger.enqueue` 注册 `acceptance.experiment_plan`（C 的 ExperimentPlan）、`research_claim`（plan_id/criterion_version/conditions/sources）、`file_policy`（既有 ValidationPolicy）。MCP 工具不能修改这些事实源。论文源引用放 task payload 或 claim.sources；正文与经验放既有候选资产，不新建经验池。

流程：发现 → claim → request environment → execute → 读取持久结果 → submit candidate（quarantine）→ verify research → complete research task（释放 scope，批准仍待复现）→ 不同 worker 在新 task/新 sandbox/run 复现 → 静态验证 + 科研准入 → 后续 task 本地 revalidation → inherit experience（原有 consumption）→ child 静态验证 + 准入 → apply（原有 ledger fence）→ 实际 AdoptionReceipt。

外部 execute 前使用既有 begin_execution 持久未确认请求；外部调用不持 SQLite 写事务。未知退出/远端效果/异常/失去租约不自动重做，成本/用量未知保留 unknown/null。耗时执行期间另一 MCP renew 可以继续；所有提交、批准和应用重新校验当前身份/权限/租约。

科学通过由 C 可信读取器重读原始归档计算；exit 0 和 Agent 报告的 metric 均不能替代判据。独立复现要求不同 worker/run/sandbox，以及相同科学计划/条件。静态验证仍调用原 AssetValidator；不把科研报告伪装为 literal-files-v1。反例与失败复现保留，不覆盖历史；失效经验不可注入或采用。

当前可准入案例限定单个静态安全 Python script：Candidate唯一FileChange.after须逐字节对应被C执行并归档的代码。多文件/Notebook研究资产准入尚不支持（C的Notebook执行能力另行验收），不绕过已有静态语言限制。作者/复现计划比较保留code/data官方完整性值、环境、判据、参数、seed、资源和模式，仅排除role与本地输入路径。inheritance必须明确匹配预注册条件并重验，child通过既有ConsumptionExecution关联parent；child仍须自身静态门禁。mock/replay观察可留痕，但不能approve或继承科研经验；完整正向科研链等待I真实OpenSandbox case，B不伪造live数据取得绿色测试。

每份原作者、复现者及本地再验证的可信结果还必须明确 `effect_state=known|confirmed`；科学passed但cleanup/effect未知仍是原始观察，不能晋级或继承，不把unknown改写known。报告写入前核对预注册plan_id与criteria.version对应claim；继承的完整科学plan也须与原作者相同。`inherit_experience` 的base_revision/base_head是当前目标HEAD锚点，服务在有效租约下复用既有 `snapshot_revision` 捕获当前scope（包含上一任务已apply的bytes），生成child基线；不创建新的哈希或快照系统。昂贵Git操作在账本写事务外，消费完成后再次检查fencing。

官方来源：MCP v1 [Python SDK](https://github.com/modelcontextprotocol/python-sdk/blob/v1.x/README.md)，MIT，当前机器实测 mcp 1.28.1；锁版本由 C 管理。唯一公开 CPU 案例由 C 固定 [NIST NumAcc4](https://www.itl.nist.gov/div898/strd/univ/data/NumAcc4.dat)。接口与科研任务 live 尚待最终 I，配置存在不是验收。
