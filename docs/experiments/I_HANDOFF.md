# C → I：可信配置、证据与自有资源交接

代码候选 `23417b09ffc93fbc432da0f63a7abec2546fd825` 已 push；本次收口只增加/更新文档。
集成后 I 需固定自己的完整集成 SHA 重新验证，不复用 C 作为集成通过。
本轨依赖唯一 Owner 的改动是 `pyproject.toml` / `poetry.lock`；锁中原有版本均未升级。
版本、来源、许可证见 [upstream.md](upstream.md)，接口与支持矩阵见 [README.md](README.md)。

## 固定环境与信任来源

- 项目沿用 Python 3.12（本机 3.12.13）、Poetry 锁；opensandbox 与 opensandbox-code-interpreter 均 **1.1.0**，nbclient 0.10.4、nbformat 5.10.4。
- 官方初始研究 SHA `089b59ad48af33fc2733de58bd1a39c687c93b0a`；实际 SDK/service release 源 commit **`b1a29cf93a823a95913f7943010febb3f29de05c`**。`836b182e208e66c046026fa0f633e089321f1efb` 是 annotated tag object，不能当源 commit。
- `deploy/opensandbox/compose.yaml` 和 config.toml 为宿主可信配置；固定 server/execd/image digest，不接受 Agent 提交的 service host、key、archive root 或资源扩大请求。
- API `127.0.0.1:8097`，官方 `OPEN-SANDBOX-API-KEY` 认证。私有本地 key 文件 **`C:/Users/DW/AppData/Local/Temp/morph-sandbox-live-0930/service-key`**，当前用户 ACL；只传路径，从文件直接读，不打印、不送 MCP、不复制 HOME/原生 Agent 凭据。
- 本机 C Poetry 环境位于 `C:/Users/DW/AppData/Local/Temp/morph-c-poetry-0930`，只供已授权本机只读使用。I 应从最终集成锁建立自己的环境；不能由 C 的 editable 路径误导为集成源码。

## 当前服务与资源归属

只归本轮所有的 compose project `morph-research-c-0930`、container
`morph-research-c-0930-server`，label `morph.owner=research-c-0930`，ID `eb6152fbdee0`。
配置 server 1 CPU / 512MiB / 128 pids、restart=no、loopback 生命周期端口。
2026-09-30 14:11 UTC 恢复前独立观察：该容器 exited255，finished13:09:36Z，
OOMKilled=false，Error空；退出根因 unknown，不能认定是 OOM。
当时 guest available7458MiB，host free physical1926896KiB / virtual23357448KiB；这是当时快照，运行前须再次核验。
按主控授权只启动同一自有 service，未启动新 sandbox；14:12:16Z 原生认证 GET /sandboxes HTTP200。
`service-handoff-status.json`、`service-handoff.log` 保存磁盘证据。HTTP200 仅说明生命周期服务可读，不能算新实验通过。

主控已要求交由 I 接续独立案例。I 负责自己的新 sandbox 与归档，并在收尾仅停止本轮 service/自己创建的 sandbox。
Docker Desktop、其余约60个容器、外部卷和已有设置不属于本轮，不停、不删、不改。
发行1.1.0 sandbox 会发布动态 bridge 端口；默认 Docker runtime 无 secure runtime，
只允许当前授权的公开 CPU 输入，不能称为网络强隔离/生产环境。

在集成仓库根目录，必要时可使用以下现有配置启动**自有 service**：

```powershell
$taskServiceKey = 'C:/Users/DW/AppData/Local/Temp/morph-sandbox-live-0930/service-key'
$env:OPENSANDBOX_SERVER_API_KEY = [IO.File]::ReadAllText($taskServiceKey).Trim()
try {
  docker compose -f deploy/opensandbox/compose.yaml config --quiet
  if ($LASTEXITCODE -ne 0) { throw 'Owned compose validation failed' }
  docker compose -f deploy/opensandbox/compose.yaml up -d server
  if ($LASTEXITCODE -ne 0) { throw 'Owned service startup failed' }
} finally {
  Remove-Item Env:OPENSANDBOX_SERVER_API_KEY -ErrorAction SilentlyContinue
}
```

不要输出 `docker compose config` / inspect 的 Env 内容；不要把 key 放在 shell 参数里。

## 新 CPU 接口案例与宿主计划

C 原唯一 live `interface-c-0930-01` **FAILED**，见 [原失败](interface-c-0930-01.md)。
原目录/result 不改，禁止重复这个 run 或在 unknown 后自动重建。
I 在已批准的完整集成 SHA 上自行选择全新唯一 run_id（以下只是说明，不应直接复制占用名称）：

```text
python -m orchestration.experiments.smoke --case-dir demo/research_case --archive-root <host-protected-absolute-path> --run-id <new-approved-unique-run-id> --domain 127.0.0.1:8097
```

运行时进程环境同样从上述文件读 `OPENSANDBOX_SERVER_API_KEY`，结束后删除环境变量；不要输出秘密。
smoke 是 SDK 接口 CPU 案例，不是 NativeAgent task_live。它包含创建/附着拒杀/续期/二进制往返/
实际 cgroup CPU-memory/命令取消/正式脚本/独立判据/关闭；必须检查实际结果，不能预写通过。
固定计划默认1 CPU、512MiB、180s生命周期、30s命令；GPU请求或不可用能力显式unsupported。

B 的宿主业务入口：

```python
from orchestration.experiments import ExperimentContext, ExperimentExecutor, OpenSandboxBackend, read_result
from orchestration.experiments.case import public_case

# case_dir、service_key、protected_root 是宿主配置；身份来自既有账本。
plan = public_case(case_dir, role="author", order="original")
context = ExperimentContext(run_id=run_id, task_id=task_id,
                            worker_id=worker_id, fencing_token=token)
backend = OpenSandboxBackend(domain="127.0.0.1:8097", api_key=service_key)
result = ExperimentExecutor(backend).execute(plan, context, protected_root)
verified = read_result(protected_root, run_id,
                       expected_plan=plan, expected_context=context)
```

同步 execute 可以 `asyncio.to_thread`。必须由 B 的既有账本/宿主保留 begin_execution/fencing/预算约束，
每个 run 只执行一次；A 原生工具通过 B 调用 C，C 不提供 Agent 调度器。
独立复现 `public_case(..., role="replication", order="original")` 与继承再验证
`public_case(..., role="inheritance", order="original")` 各自必须不同 worker/run/sandbox、重新实际运行。
本轮 B 的正向科研经验准入要求三次科学计划等价（只改变 role），包括 parameters.order；
`reverse` 是显式不同实验条件，只能用于拒绝等价继承的对照或新的预注册实验，不能用于本轮正向继承。
三种角色只是预注册计划元数据，不是三个已经通过的案例；付费/原生 session 仍由 I 统一掌握原生认证和权限。
科学判据只针对 NIST NumAcc4 的均值/样本方差/全部原始残差，host Fraction 独立重算；候选 code 必须匹配实际 archive。
read_result 的普通 SHA/绑定只防输入输出错配，不是远端完成证明；protected_root 必须由宿主管理。

## 关闭后原始证据与剩余能力

`archive_root/run_id` 中 plan、raw inputs、runtime、SDK execution/logs、outputs、result/summary 在 sandbox 销毁后仍保留。
失败/timeout/unknown/缺产物/unsupported 与科学负结果不同；exit/usage/cost/远端效果未知保持 null/unknown，
禁止自动重放。二进制用官方 filesystem stream/storage，MCP仅传引用，不把大产物或秘密塞文本。
当前既有 private archive 是 `C:/Users/DW/AppData/Local/Temp/morph-sandbox-live-0930`，
C 不自动清理；TEMP 是本机磁盘证据，不是长期备份保证，I 要将需要长期保存的脱敏证据移入宿主管理的持久 root。

Script 已实现；connect 仅借用、禁止远端修改/续期/取消/销毁，close仅释放本地传输。
持久卷、Code Interpreter、新 Jupyter kernel 是显式 opt-in 且本轮 **NOT_RUN**，默认unsupported。
Notebook Dockerfile 未 build/run，不能宣称已可用；正式复现需固定镜像、全新 kernel/context 与完整产物。
原烟测在目录权限 wire 失败前未发送 binary/cgroup/cancel/科研 command；700/600已修复且官方 SDK wire contract 测试通过，
修复后上述 live 能力仍待 I 独立新案例。原生两个 Agent task_live **NOT_RUN**。

完整本机12失败与同 SHA CI结果见 [full gate](full-gate-23417b09.md)；文档提交不把它们改为通过。
