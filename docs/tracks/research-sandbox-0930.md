# C / OpenSandbox 科研执行与 T0

基线 `ef77af603577d4539d8dbdf780e1536a369b0d12`；计划 `6ba12b24781318383454d2e7fb0b132e897b8a8d`。
本轨仅修改指定所有权路径，无新 Agent/Run，产品执行不调用 Orca。

## 已交付接口与独立原始指标

`orchestration.experiments` 导出 `ExperimentPlan`、`ExperimentContext`、`ExperimentResult`、
`ExperimentExecutor`、`OpenSandboxBackend`、`read_result`。
同步 `ExperimentExecutor(backend).execute(plan, context, archive_root)`；B 可以 `asyncio.to_thread`。
`read_result(archive_root, run_id, *, expected_plan=None, expected_context=None)` 重新读取原始文件、
比较输入/输出 SHA256、计划/宿主身份、真实 command 结果和 Python 环境，并独立计算科学判据。
B 必须传入预注册 plan/context 并通过现有账本强制 fencing；本轨不创建账本或新调度系统。

案例为 NIST StRD NumAcc4；代码调用 CPython `statistics.variance`，对照朴素方差相消公式。
数据原样保存，独立 host 使用 Fraction 从十进制输入计算精确方差，并逐项核验输出残差。
固定样本方差 0.01，绝对误差上限 1e-9；参数只有 original/reverse，seed=0。
候选代码须与本次实际执行的 code SHA/内容一致；成功不能转移给无关补丁。

## 已运行验证与原失败

- 首次 strict：exit 1，8 个错误（浮点 Literal、1.1.0 无 interpreter.close、SDK alias 类型、局部变量类型）；未修改阈值，按发行 API 修复。
- 修复后 `python -m mypy --strict orchestration/experiments`：6 files，exit 0。
- 早期 `python -m pytest tests/experiments -q`：12 passed，后续补齐失败/timeout/unknown/缺产物/身份绑定/官方SDK wire等契约测试；固定候选 full 的失败清单没有实验模块失败，同 SHA CI 全仓通过。包含真实公共脚本在 pytest 临时目录运行，不能视为 OS 沙箱或 live。
- Poetry 2.3.2 / Python 3.12.13：lock/install 成功；14 个新增包，原锁中依赖版本均保持不变。
- `docker compose ... up -d` 容器创建成功；实际官方服务首次 startup 拒绝无 API key，原日志保存在 `C:/Users/DW/AppData/Local/Temp/morph-sandbox-live-0930/service-first-start.log`，这不是服务通过。
  后续配置强制独立私有服务 key，不能跳过官方认证检查。

## 固定候选、完整 gate 与交接

分支 `songconmaisaix31-design/morph-research-sandbox-0930`；实现候选
`23417b09ffc93fbc432da0f63a7abec2546fd825` 已 push 并远端核验。
后续本次收口仅修改文档，不把候选测试移称为文档 SHA 的重新验收。

- 官方 release-1.1.0 源 commit `b1a29cf93a823a95913f7943010febb3f29de05c`；两个 SDK 1.1.0、nbclient0.10.4、nbformat5.10.4；初始研究 SHA、许可证和 API 差异见 `docs/experiments/upstream.md`。选择性官方 upstream API tests 33 passed，不是全上游测试通过。
- 本机固定候选 `python tools/typecheck.py`：97 files、exit0；此前本机 Poetry lock/check/build和wheel导入均通过（build在22c21e8阶段），固定23417的完整build/wheel由CI实测。
- 固定候选本机 `python -m pytest -q`：**12 failed / 943 passed / 2 warnings，exit1**，进程局部 BLAS/OMP threads=1，原日志/原断言均未修改，没有再跑full。
- 同候选 [CI36717414791](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/36717414791)：Ubuntu954 passed/1 skipped、Windows955 passed；strict97、build、SDK、独立wheel资源/Node检查全部success。CI Python3.13，和本机Python3.12.13环境不同；不能覆盖本机失败。
- 逐项12失败与四个原始audit的事实/推断边界见 `docs/experiments/full-gate-23417b09.md`。存在明确WinError1455/DLL pagefile错误；Node/Git/snapshot/SQLite锁的残余根因不全部归为内存，没有改他人领域代码、调阈值或删测试。
- 首次官方 smoke `interface-c-0930-01` 在候选6179d41b上 **interface_live=FAILED / provenance=live / task_live=NOT_RUN**。create/connect/renew/附着拒杀真实完成后，目录权限wire448 HTTP500；原unknown result不改，原退出/用量/成本null，未执行科学命令。SDK wire修复700/600并验证官方SDK JSON/multipart；原自有sandbox已DELETE204，后续只读404补充留存，未重放。详见 `docs/experiments/interface-c-0930-01.md`。
- 自有service曾exited255（非OOMKilled，退出根因unknown）；授权只恢复同容器，14:12:16Z认证只读HTTP200，无新sandbox/live。service/私有key路径、可信配置、运行命令、B宿主CPUplan接口和归档归属见 `docs/experiments/I_HANDOFF.md`；主控要求I接续自己的独立新案例。

## 真实限制与未执行操作

修复后新 interface_live 尚未运行；历史 interface_live 失败保持失败，原生两 Agent task_live NOT_RUN。
codeinterpreter、nbclient/Jupyter 和持久卷是显式可选能力，默认未启用，未实测不得宣称支持。
执行失败/超时/unknown/unsupported/缺产物与科学负结果分开；未知退出、用量、成本和远端效果不补零、不重放。
Docker Desktop 已启动一次（`Start-Process -WindowStyle Hidden`），既有 restart 策略自动恢复其他项目容器；未改设置或停其他资源。
宿主空闲内存约1GiB曾触发阻塞报告，guest available约7GiB是当时快照；之后Windows页面文件压力确证，不能把guest cache充足当成Windows进程启动充足。

正式CPU命令/二进制/cgroup/cancel在首次烟测前置失败后NOT_RUN；由I在固定集成SHA上做独立新run。
Notebook Dockerfile 未build/run，Code Interpreter/持久卷未实测，GPU不在范围。
服务HTTP200不等于实验通过，CI/mock/宿主脚本不等于原生Agent验收；不存在本轨“开发全部完成”或生产结论。
本轨实现/失败留存/文档移交完成，后续接入领域问题仍退回同一Owner；I合并少量胶水并负责独立live与原生session验收。
