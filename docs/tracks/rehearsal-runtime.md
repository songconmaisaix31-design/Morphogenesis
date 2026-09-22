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

## 已实现入口和操作顺序

```powershell
# 仅 I / 操作员执行：明确授权两次不同的新任务，每个任务一次调用。
python -m orchestration.rehearsal --root "$env:TEMP/morph-rehearsal-new-1" --mode auto --authorize-task repair --authorize-task recovery --model gpt-5.6-luna --tau-seconds 10 --stage-delay 2 --timeout 180
# 手动模式：同样参数改成 --mode manual，在 awaiting_offline 按 Enter。
# 只读回放：输出 JSON 至 stdout，不创建目录、不改原始证据、不调用模型。
python -m orchestration.rehearsal --replay "$env:TEMP/morph-rehearsal-new-1/rehearsal.json"
```

`--root` 省略时创建新的空 TEMP 根。已有非空根一律拒绝再次运行；读回放不接受任何执行授权。默认模型 gpt-5.6-luna；不改变账号/认证配置。可调整 `--tick-seconds`（默认 1）、`--archive-threshold`（默认 0.2）、`--max-tokens`（每任务默认 20000）、`--max-cost-usd`（每任务申明默认 1）。现有 CLI 不提供调用中美元硬上限，不能将该参数或 token 数称作费用证明。

两次调用以 `--authorize-task repair --authorize-task recovery` 明确授权；第二次为新 TaskId、新工作目录里的坏样例，绝非重试。第一次失败、执行未知、token usage 缺失时停止，不进入第二次；第二次失败也不重试。费用未知保留 null；旧 Runtime 的 unknown_usage 语义不改，第二次调用依赖独立的新任务授权。三次彩排总计最多六次真实调用，R 无真实调用，I 必须跨三个根累计预算，不能在失败后换根变相重试。

顺序：

1. task_ready：外部固定 unittest 对坏样例产生真实 0/3。
2. repair_selected：Runtime 选中第一名 builder；唯一 execute_intent 进入现有执行器。
3. repair_reviewed：外部独立 reviewer 给出真实结果；先保存复核，再保存反馈后的管道权重，成功管道从 1.0 增至 1.9。
4. gene_generated：仅从本次已通过独立验收的 proposal.summary/content、verdict 和 source_attempt 生成本地 Gene。
5. awaiting_offline → member_offline：auto 按顺序执行，manual 等待 Enter；移除获胜 builder 后展示原管道 inactive。底层拓扑策略/权重不受展示覆盖影响。
6. recovery_ready → recovery_selected → recovery_reviewed：新空工作目录的新任务；有效列表只剩另一名 builder，实际执行后独立复核。
7. gene_adopted：只有 executor 明确声明采用已注入 Gene 且独立复核成功，原有 LocalMetabolism.mark_used 才增加采用记录并刷新权重。未声明采用则不能完成彩排；不会补造采用事实。第二次成功也生成自己的 Gene。
8. decaying → archived → completed：真实 time.time() 墙钟计算 exp(-elapsed/tau)，逐幕记录；低于阈值调用原有本地 archive，再对每个 Gene 调用 resolve，全部不可检索才完成。远端 Hub 不发布、不同步。

所有阶段均原子更新 `root/rehearsal.json`，其中 current/history 有完整前后快照。每次任务的 config/result/gene/events/CLI 原始证据/外部 verification 文本和 JSON 保存在 `root/repair`、`root/recovery`；元数据与 LangGraph 检查点使用原有 SQLiteStore/SqliteSaver。失败保存 stage=failed、failure 和已知结果，UNKNOWN 为 blocked 或 not_run，不伪称已知修复失败。`root/STOP` 可阻止继续；现有执行器负责自己的调用超时，不用进程死亡制造恢复故事。

V 可先启动只读 HTTP viewer，再在前台运行 CLI；初次独立验证完成前文件短暂不存在，应显示等待。live 轮询 `read_rehearsal(path)`；回放用 `read_rehearsal(path, replay=True)`，返回数据所有来源为 replay，interface_live/task_live 降为 not_run，保留原始证据 URI、时间、结果和未知费用，message 标注原始来源。`--replay` 仅输出至 stdout，不覆盖传入源文件；V 持续读取原 `--rehearsal` 路径即可。已与 V 确认显式授权和只读回放入口。

## 验证与剩余限制

复用 `../morph-integration/.venv/Scripts/python.exe` 的锁环境，仅执行工具、不改该 worktree；无全局安装、无模型/API 调用。

- `python -m pytest tests/t2 tests/t0/test_bootstrap.py tests/t3/topology -q`：37 passed，包括完整 fixture 流程和真实外部 unittest 子进程。fixture 的所有任务/Gene/快照均 mock，interface_live/task_live 保持 not_run。
- `python tools/typecheck.py`：52 source files strict clean。
- `uv tool run --offline poetry check --lock`：锁一致（仅元数据弃用提示）。
- `uv tool run --offline poetry build --output "$env:TEMP/morph-rehearsal-runtime-dist"`：sdist/wheel 成功；wheel 内含新入口、共享模型、固定 runner 和 fixture。直接 `python -m build --no-isolation` 曾因复用环境未装 poetry-core 报 BackendUnavailable，改用已有离线 Poetry 构建成功，未安装全局工具或修改其他 worktree。
- 真实模型调用、真实 Gene、三次真实全流程、页面浏览器证据由 I 验证；本轨测试不能代替。真实投影接线仍需人工完成，固定成员池下线不证明在途 CLI 被杀后的恢复。

契约首交提交：`e3fe21d`。完成提交与最终 SHA 见本轨交付消息；开发和返修仍由 R 负责，待协调者明确放行后才发 worker_done。
