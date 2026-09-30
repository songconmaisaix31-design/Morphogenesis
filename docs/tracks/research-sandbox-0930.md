# C / OpenSandbox 科研执行与 T0

基线 `ef77af603577d4539d8dbdf780e1536a369b0d12`；计划 `6ba12b24781318383454d2e7fb0b132e897b8a8d`。
本轨仅修改指定所有权路径，无新 Agent/Run，产品执行不调用 Orca。

## 阶段一：接口与独立原始指标

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
- `python -m pytest tests/experiments -q`：12 passed，exit 0，全部 `contract_local / mock`，包含真实公共脚本在 pytest 临时目录运行，不能视为 OS 沙箱或 live。
- Poetry 2.3.2 / Python 3.12.13：lock/install 成功；14 个新增包，原锁中依赖版本均保持不变。
- `docker compose ... up -d` 容器创建成功；实际官方服务首次 startup 拒绝无 API key，原日志保存在 `C:/Users/DW/AppData/Local/Temp/morph-sandbox-live-0930/service-first-start.log`，这不是服务通过。
  后续配置强制独立私有服务 key，不能跳过官方认证检查。

## 当前限制

本阶段 interface_live 与 task_live 均 NOT_RUN；尚无原生两 Agent task_live。
codeinterpreter、nbclient/Jupyter 和持久卷是显式可选能力，默认未启用，未实测不得宣称支持。
执行失败/超时/unknown/unsupported/缺产物与科学负结果分开；未知退出、用量、成本和远端效果不补零、不重放。
Docker Desktop 已启动一次（`Start-Process -WindowStyle Hidden`），既有 restart 策略自动恢复其他项目容器；未改设置或停其他资源。
宿主空闲内存约1GiB曾触发阻塞报告，主控补充 guest available 约7GiB后改用小型512MiB/1CPU沙箱。

后续继续由同一 Owner 完成 SDK 契约验证、一次正式 CPU 接口烟测、docs/build/full strict 和阶段 commit/push。
