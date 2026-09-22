# R 固定彩排运行链路

基线：`791d3cf`。所有修改限于 R 轨 write_paths；真实模型调用留给 I，总计最多六次，本轨不调用模型或外部 API。

## V 消费契约（第一阶段）

直接导入 `orchestration.rehearsal_models.RehearsalDocument`；不复制类型。运行目录下的 `rehearsal.json` 为该模型序列化，`current` 是 `history[-1]`。读取端用 `model_validate_json`。

- 每幕包含 `stage / sequence / at / task_id / task_description`。
- `checkpoints.checks` 为 clamp / mean / unique 的独立 unittest 真判定；未知是 null。`passed_count / total / ratio` 验证一致，3/3 必须有通过的独立验证证据。
- `members` 为具体 AgentId 可用性；`pipes` 直接复用 `PipeState[]`。不可用成员的管道只在展示快照设 inactive，不修改拓扑正常策略。
- `routing` 给出有效成员、实际 selected_attempt、removed_member/removed_at；`boundary=between_tasks`。
- `genes` 直接复用 `GeneView[]`，`adoptions` 复用 `UseRecord[]`，`results` 为每个任务原有 TaskResult；`retrievable_gene_ids` 来自实际 resolve。
- `tau_seconds / archive_threshold / at` 显式披露墙钟演示参数；不加速或伪造时钟。
- `mode / provenance / acceptance` 严格区分 live/mock/replay 及 contract_local/interface_live/task_live；`cost_usd=null` 是费用未知，不能显示为零。
- `scope=fixed_pool_between_tasks` 仅证明固定逻辑成员在新任务分配前移除后的选路恢复，不证明杀死在途 CLI 后恢复。没有 PID 死亡/进程心跳模拟。Hub 始终 `pending_publish`。

约定入口：`python -m orchestration.rehearsal --root <新空TEMP目录> --mode auto|manual --model gpt-5.6-luna --tau-seconds 10 --stage-delay 2`。manual 在两任务之间提示操作员按 Enter 下线获胜 builder；auto 使用同一顺序。`--replay <已有rehearsal.json>` 只读、明确 replay，不调用模型。运行入口正在下一阶段实现；此提交仅交契约。
