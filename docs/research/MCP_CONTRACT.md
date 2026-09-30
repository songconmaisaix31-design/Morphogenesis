# 科研 MCP 宿主契约

启动：`python -m swarm.research --config ABS_TRUSTED_JSON`。官方 MCP Python SDK v1 `FastMCP`，stdio；运行不导入或调用 Orca。A 使用每次启动的原生 MCP 配置，不改 HOME、账号或全局设置。

宿主 JSON 必需字段：`ledger_path`, `swarm_id`, `workspace`, `worker_id`, `agent`（既有 role/instance）, `authorized_scopes`, `capabilities`, `assets_root`, `evidence_root`。路径均绝对路径；可选 `project_context` 与 `experiment_backend`。配置、账本、资产数据库及原始实验归档必须由宿主保护，放在模型可写项目目录之外。MCP 是工具参数边界，并不防止同一操作系统用户绕过工具直接写 SQLite；原生权限/沙箱负责这一边界。

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

工具无 worker/agent 身份、数据库路径、任意验收脚本或 passing/approved/metric 输入。`discover_tasks` 仅查询可认领任务；`claim_task` 显式主动认领。context/search 是发现和检索，不能据此记录采用。renew/release/handoff 使用绑定身份和当前 fencing token；handoff 不自动派给下一位。

科研任务通过宿主预先 `TaskLedger.enqueue` 注册 `acceptance.experiment_plan`（C 的 ExperimentPlan）、`research_claim`（plan_id/criterion_version/conditions/sources）、`file_policy`（既有 ValidationPolicy）。MCP 工具不能修改这些事实源。论文源引用放 task payload 或 claim.sources；正文与经验放既有候选资产，不新建经验池。

流程：发现 → claim → request environment → execute → 读取持久结果 → submit candidate（quarantine）→ verify research → complete research task（释放 scope，批准仍待复现）→ 不同 worker 在新 task/新 sandbox/run 复现 → 静态验证 + 科研准入 → 后续 task 本地 revalidation → inherit experience（原有 consumption）→ child 静态验证 + 准入 → apply（原有 ledger fence）→ 实际 AdoptionReceipt。

外部 execute 前使用既有 begin_execution 持久未确认请求；外部调用不持 SQLite 写事务。未知退出/远端效果/异常/失去租约不自动重做，成本/用量未知保留 unknown/null。耗时执行期间另一 MCP renew 可以继续；所有提交、批准和应用重新校验当前身份/权限/租约。

科学通过由 C 可信读取器重读原始归档计算；exit 0 和 Agent 报告的 metric 均不能替代判据。独立复现要求不同 worker/run/sandbox，以及相同科学计划/条件。静态验证仍调用原 AssetValidator；不把科研报告伪装为 literal-files-v1。反例与失败复现保留，不覆盖历史；失效经验不可注入或采用。

官方来源：MCP v1 [Python SDK](https://github.com/modelcontextprotocol/python-sdk/blob/v1.x/README.md)，MIT，当前机器实测 mcp 1.28.1；锁版本由 C 管理。唯一公开 CPU 案例由 C 固定 [NIST NumAcc4](https://www.itl.nist.gov/div898/strd/univ/data/NumAcc4.dat)。接口与科研任务 live 尚待最终 I，配置存在不是验收。
