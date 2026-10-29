# SWA 原生 Agent 自行调用 Morph 研究工具

这条桥把现有 `swarm.research` 官方 MCP stdio 服务交给 SWA 的 Pi 固定扩展。Pi 调用 `morph_list_tools {}` 读取真实 schema，再调用 `morph_call_tool {"name": "工具名", "arguments": {...}}`。研究任务的发现、选择、认领、续租和提交由原生 Agent 发起；Morph 的既有 HostConfig、TaskLedger、fencing、验证和资产流程继续约束每次操作。

| 职责 | 实现 |
|---|---|
| 原生模型会话、工具调用、会话结果和清理 | 支持 `--morph-config` 的 SWA Pi 运行时 |
| 身份、能力、scope、任务依赖与租约 | `swarm/research/models.py`、`service.py` 和 `swarm/task_ledger.py` |
| MCP 工具 schema 与 action 检查 | `swarm/research/server.py:create_server` |
| 注册实验、可信原始结果、复现与采用 | 现有 OfficialExperiments / OpenSandbox / local_assets |
| 准备材料与无模型 stdio 自检 | `demo/swa_research_bridge.py` |

这仍是同一宿主上的独立决策与共享账本，不是跨宿主共识。SWA 的 run 完成只代表原生会话结束，不能代替 Morph 科研证据或采用回执。

## 1. 准备三个研究身份

在安装好项目依赖的 Morphogenesis checkout 根目录执行。所有路径用绝对路径；项目目录和状态目录必须不存在、互不嵌套，并位于源码之外。以下示例的 `/abs/...` 均替换为本机路径。

```bash
/abs/morph-env/bin/python -m demo.swa_research_bridge prepare \
  --project /abs/nist-demo/project \
  --state /abs/nist-demo/host-state \
  --python /abs/morph-env/bin/python \
  --swarm-id nist-swa-demo \
  --domain 127.0.0.1:8097 \
  --api-key-env MORPH_OPENSANDBOX_API_KEY
```

此命令复用 `seed_case`，生成注册 NIST NumAcc4 计划、三项有依赖的任务、三份 HostConfig，并打印所有路径。每个角色另有：

- `author.morph.json` / `replication.morph.json` / `inheritance.morph.json`：SWA descriptor。
- 科学项目 `swa-inputs/` 内对应的 `.task.json`：SWA run spec，单个原生 Worker。
- 科学项目 `swa-inputs/` 内对应的 `.input.txt`：要求 Agent 自主发现和认领的操作说明。

descriptor 只含三个绝对路径，例如：

```json
{
  "python": "/abs/morph-env/bin/python",
  "cwd": "/abs/Morphogenesis",
  "host_config": "/abs/nist-demo/host-state/author-host.json"
}
```

`cwd` 是 Python 模块所在的 Morph 源码目录；`HostConfig.workspace` 和 SWA `--workdir` 必须一致，都指向生成的科学项目。descriptor、HostConfig、解释器和 Morph 源码都在科学项目之外；SWA 从已批准的项目路径读取 spec/input，因此它们放在项目内的 `swa-inputs/`，与 `science/` 研究 scope 分开。保留 venv 的启动路径，不要改成其符号链接的系统 Python 目标。

准备命令不会调用模型、认领任务、运行实验、批准候选或生成科研结果；失败后保留现场，另选新目录再准备。API key 仅由宿主环境提供，配置只记录环境变量名，不能把 key 写入 descriptor、prompt 或 spec。

## 2. 先跑真实 stdio 自检

```bash
/abs/morph-env/bin/python -m demo.swa_research_bridge selfcheck \
  --root /abs/nist-stdio-checks \
  --python /abs/morph-env/bin/python
```

每次在 `--root` 下新建独立目录，可以重复执行，不会消耗待演示科研项目的 attempt。它使用官方 MCP SDK 启动两个真正的 `python -m swarm.research` 子进程：

1. 两个不同身份、相同资格的客户端发现同一 author 任务。
2. 并发认领，验证只有一个赢家，并核对真实 ledger 的 owner。
3. 赢家续租、释放；另一身份认领取得更高 fencing token。
4. 旧持有者续租被拒，现持有者仍不变；最后释放任务。
5. 官方 stdio 上下文关闭，验证三任务都没有 owner 或结果，候选文件保持初始内容。

stdout 和打印出的 `selfcheck-result.json` 提供实际结果；SDK stderr 留在相邻日志中。实测范围是本地 MCP/租约接线：`status=passed`、`validation=contract_local`、`model_invoked=false`、`experiment_invoked=false`。测试命令：

```bash
/abs/morph-env/bin/python -m pytest -q tests/research/test_swa_bridge.py
```

## 3. 通过 SWA 启动真实 Pi

使用 SWA [PR #14](https://github.com/songconmaisaix31-design/swarm-anything/pull/14)（基于 PR #10）的固定源码 [777e538aa6e6a8f30a67aac961f2425d9253b005](https://github.com/songconmaisaix31-design/swarm-anything/tree/777e538aa6e6a8f30a67aac961f2425d9253b005) 构建，其中包含 Pi Morph 扩展和 `--morph-config` 参数。旧的 `733ee08f` 只有运行生命周期，不能运行本工具桥。真实 SWA 项目授权和 Pi 模型认证由 SWA 正常配置提供。调用 CLI 的环境需要 `SWA_PROJECT_TOKEN`。若 OpenSandbox 要求认证，须在启动 **`swa serve` 的宿主环境**中提供上文指定的 `MORPH_OPENSANDBOX_API_KEY`；仅在调用 CLI 的终端设置它不会传入已运行的 daemon。SWA 从固定 HostConfig 的 `experiment_backend.api_key_env` 精确读取该变量并传给 MCP 子进程，不继承整个宿主环境。不要把密钥放到命令行或演示画面中。

SWA 项目的 `AllowedTools` 必须包含 `morph_list_tools` 和 `morph_call_tool`，并批准科学工作目录。以下命令使用该项目 ID、实际 endpoint、实际 Pi `PROVIDER/MODEL` 和新 UUID；保存该 UUID 与输出，遇到中断查询原请求，不重新提交同一实验。

```bash
swa run \
  --project REAL_SWA_PROJECT \
  --endpoint http://127.0.0.1:REAL_PORT \
  --workdir /abs/nist-demo/project \
  --spec-file /abs/nist-demo/project/swa-inputs/author.task.json \
  --input-file /abs/nist-demo/project/swa-inputs/author.input.txt \
  --agent pi --model PROVIDER/MODEL --name morph-author \
  --morph-config /abs/nist-demo/host-state/author.morph.json \
  --request-id NEW_UUID \
  --strict --timeout 15m --on-input exit \
  --question-mode disabled --delegation-mode disabled --development-mode disabled \
  --json
```

当前桥只用于 Pi，不能与 role、handoff 或其他启用的工具模式混用。首次应观察 Pi 真实调用 `morph_list_tools` 和 `morph_call_tool`，而非只在 final text 描述操作。Morph MCP schema 是参数事实源：模型不能自行指定 worker_id、ledger 路径、科学指标或通过标志。

成功后用返回的 controller/task ID 导出原生结果，再关闭该 controller；下面的占位 ID 必须取自原输出，导出目录必须不存在：

```bash
swa task result --project REAL_SWA_PROJECT --endpoint http://127.0.0.1:REAL_PORT \
  --controller RETURNED_CONTROLLER --task RETURNED_TASK_ID \
  --output-dir /abs/nist-demo/author-native-result --json
swa controller close --project REAL_SWA_PROJECT --endpoint http://127.0.0.1:REAL_PORT \
  --controller RETURNED_CONTROLLER --request-id NEW_CLOSE_UUID --json
```

超时仅停止等待，不保证原生 Worker 停止。使用 `swa request show --project REAL_SWA_PROJECT --endpoint http://127.0.0.1:REAL_PORT --request-id ORIGINAL_UUID --json` 查询原请求；按 SWA 返回的同一 run/controller 恢复观察。外部效果未知时停止，不重发 `research_experiment(action=run)`。

## 4. 有 OpenSandbox 时完成科研链

准备中的 `--domain` 必须对应可用 OpenSandbox 服务，具有注册计划要求的镜像及隔离能力。三角色依次启动，每次替换命令中的 spec、input、descriptor、name 和 request UUID；下一角色依据 Morph 的真实依赖状态发现任务。

| 原生身份 | Agent 通过 MCP 自主执行 | 可验收的实际结果 |
|---|---|---|
| author | discover → claim/renew → context → experiment request/run → candidate submit（template 加 claim 返回的 attempt_id）→ verify original → complete | 作者证据提交；候选仍 quarantined，未批准或采用 |
| replication | discover → claim/renew → dependency asset → 新 sandbox run → verify reproduction → validate_files → approve → apply 原候选 | 不同 Worker/run/sandbox 的复现通过，原文件实际应用 |
| inheritance | discover → claim/renew → 来源 asset → 新 run → verify inheritance → inherit_experience → validate/approve child → apply child 与 execution_id | `science/reused.py` 的实际字节、ledger result 和 AdoptionReceipt 一致 |

精确作用域、候选模板、路径映射、base_revision 与步骤来自 `project_context`。科学判据、效果确认、清理和采用是不同事实。失败/未知结果保留原状态，不换 mock 或伪造成功。完整背景见 [PUBLIC_CASE.md](research/PUBLIC_CASE.md)。

`seed_case` 生成的是既有注册案例配置，默认不含研究项目 envelope、模型费用授权或 `native_invocation`。这个 helper 不增加、删除或绕过预算门禁，也不自动批准模型开支。若使用已有受预算约束的研究项目，把 descriptor 指向宿主已批准的原 HostConfig，沿用其 admission、binding、结算和 unknown 处理；不能为让演示通过而删掉这些字段。现有研究预算的 pending hold 按项目检查，本说明只验证顺序三阶段，不宣称其多模型并发预算已验收。未知 usage/cost 保留 null。

交件时分别展示本地 stdio 检查、SWA 原生工具调用记录、Morph task audit、三个真实实验归档以及采用回执。准备输出、单测通过或模型自然语言结论均不能替代真实科研证据。
