# 科研执行接口

产品直接调用官方 Python SDK；Docker Desktop/Orca 仅本次开发环境，本模块不调用 Orca。
同步接口供 B 在官方 MCP 处理器中 `asyncio.to_thread` 调用。身份、发现认领、续租、fencing、
预算与 begin_execution 仍由已有 TaskLedger/Worker/B 提供。

```python
from orchestration.experiments import ExperimentContext, ExperimentExecutor, OpenSandboxBackend, read_result
from orchestration.experiments.case import public_case

plan = public_case(case_dir, role="author", order="original")
# 以下身份必须来自宿主已获准的账本操作，不能信任 Agent 自报。
context = ExperimentContext(run_id=run_id, task_id=task_id,
                            worker_id=worker_id, fencing_token=token)
backend = OpenSandboxBackend(domain="127.0.0.1:8097", api_key=private_service_key)
result = ExperimentExecutor(backend).execute(plan, context, protected_evidence_root)
verified = read_result(protected_evidence_root, run_id,
                       expected_plan=plan, expected_context=context)
```

每个 `run_id` 创建新目录，先存计划和保守 unknown 状态，之后只 create 一次新沙箱。
同 `run_id` 再 execute 会拒绝，不会自动恢复或重放；异常、HTTP timeout、缺退出信息保持 unknown。
正式复现必须用不同 worker/run/sandbox；脚本是新 Python 进程。作者结果、独立复现和继承再验证
各自实际运行，本轮 B 正向准入三次科学计划只变 role，order 均为 original。
reverse 是显式不同条件，只能作等价继承拒绝对照或新的预注册实验；不能把先前 original 通过迁移过去。
C 的接口烟测不能代替两个原生 Agent 的任务验收。

计划固定 code/data SHA、镜像、Python版本、参数、seed、判据、CPU/内存/最长生命周期/command timeout。
`public_case` 只生成计划，不生成通过结论。候选内容必须逐字匹配被执行并归档的 code，
不同 code/env/data/参数或条件下的历史通过不能迁移。B 必须将 read_result 的原始科学判据与旧静态门禁共同准入。
缺少完整可信证据或 `provenance != live` 不可准入 live 科研经验。

`archive_root/run_id` 保存 plan/result JSON、只读原始 inputs、runtime、SDK execution/logs 和 outputs。
result 路径/常规 SHA 仅用于完整性，不是远端执行完成证明；root必须由宿主保护。
read_result 比对期望计划/身份、常规文件 SHA、真实 SDK completion/exit、环境，再用 host Fraction
独立从 NIST 原始十进制输入计算精确值及逐项残差，重算 verdict，不信任存储JSON里的自报metric。
原生凭证、HTTP认证headers和秘密不能进入计划、代码或产物。错误摘要只记录异常类型；
私有 root 的原始 SDK/服务日志仍须在公开前检查脱敏。大文件走 SDK bytes/stream 或外部 storage，MCP仅返回引用。

## 能力与真实边界

| 能力 | 实现/API | 当前运行证据 |
|---|---|---|
| create/status/connect/renew | `SandboxSync` 官方生命周期 | 首次烟测实际完成，随后失败；不算整体通过 |
| attached保护 | connect仅借用；拒绝run/upload/renew/cancel/destroy，close仅释放本地连接 | mock契约与首次live拒杀 |
| argv/logs/exit/server timeout | 官方 commands.run + RunCommandOpts | 官方1.1.0 contract测试；科研live未执行 |
| background/status/logs/cancel | 官方后台run、get_command_status/logs、interrupt；只允许自有command ID | contract；首次live在此前失败，NOT_RUN |
| binary upload/download | 官方 filesystem write/read_bytes_stream，限产物大小 | 首次目录权限 wire 参数失败；修复700/600并补官方wire测试，修复后live NOT_RUN |
| persistent volume | 官方 Volume/PVC 指向预先创建的卷，`volumes=True`显式开启 | 本轨没有建卷，不删除外部卷；NOT_RUN |
| Code Interpreter | `codeinterpreter=True`，官方SDK create_context新内核，固定官方入口 | 默认unsupported；镜像未拉/未跑，NOT_RUN |
| Jupyter notebook | `notebook=True`，固定runner调用nbclient的新kernel，保存executed notebook/kernel ID | 默认unsupported；可选Dockerfile.notebook未build/run，NOT_RUN |
| CPU/memory/duration | 官方resource/timeout映射，smoke原始cgroup读取准备就绪 | 原live在读取前失败；实际enforcement=unknown，不把配置当验证 |
| GPU | 无本轮支持 | 请求不能静默降级；不需要GPU，不扩围 |

官方SDK重试设为disabled，遥测disabled。command超时由官方execd强制；Code Interpreter流的网络超时
只说明传输未完成，远端执行仍unknown，最长sandbox生命周期兜底，不能重复run。
科学负结果是execution succeeded / scientific failed；执行失败、缺产物等不计算科学通过。
即使科学判据通过，cleanup/effect unknown也不应进入B准入。

## 开发服务与人工操作

先只读检查资源、现有容器和端口。固定镜像digest见 `deploy/opensandbox/compose.yaml`、`config.toml` 和 case.py。
设置进程环境 `OPENSANDBOX_SERVER_API_KEY` 为私有本地服务key后：

```text
docker compose -f deploy/opensandbox/compose.yaml config --quiet
docker compose -f deploy/opensandbox/compose.yaml up -d
python -m orchestration.experiments.smoke --case-dir demo/research_case --archive-root <private-absolute-path> --run-id <new-approved-run>
```

首次运行 `interface-c-0930-01` 已失败并留痕；不得重放它。修复后的live由I在冻结SHA另作独立案例。
服务通过loopback8097+原生key认证；server和sandbox在默认bridge，SDK走server代理。
发行1.1.0的sandbox桥接端口会动态发布到宿主，不能声称是网络强隔离；本配置只供受控本地公开CPU输入。
服务拥有Docker socket权限，不能提供生产或不可信公开入口。认证/设置仅本次私有服务，不复制Agent HOME或原生登录凭据。
收尾仅停止本轮自有服务/沙箱，不停他人容器，不清理未知资源或全局Docker设置。
