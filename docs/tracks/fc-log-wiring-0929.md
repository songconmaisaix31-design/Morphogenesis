# FC 日志生产接线 Owner 记录（2026-09-29）

Owner / Swarm-Agent: codex；分支 `morph-fc-log-wiring-0929`。
基线 `c552250c0d07f5f70f09eb0a5ab3c322195e34ec`，开工 HEAD exact / clean。
本轨仅生产接线及自身验证；不发布、不合主线、不打 tag、不作 H1/FC-E 签字。

## 范围与接口

按限定七个 write_paths 开发；冻结 H3 只读消费
`be4fb7a685e951c9e42d8dc0c7eeb900cb5518f1:docs/FC_LOG_SCHEMA_DRAFT_0928.md`。
原文档由集成 Agent 引入。本轨打包其 fenced JSON 至
`orchestration/fc_log_schema.json`，运行时通过 `importlib.resources` 加载，不依赖文档或 Git。
复用 Pydantic 2.13.5 / jsonschema 4.26.0（均 MIT，现有锁 main 依赖）、原 FaultObservation /
RehearsalSnapshot、既有 SQLite bounded connection / fsync / no_links 路径保护。

```python
from orchestration.fc_logging import FCLogWriter

writer = FCLogWriter(drill_root, config.swarm_id, provenance="mock", drill=True)
worker = Worker(config, executor, candidates=candidates, fc_log=writer)
# 独立投影：writer.emit(event, task_id=..., at=..., sequence=...,
#                     duration_seconds=None, fault_observation=existing_model)
```

支持 `task / asset_call / routing / claim / fault_observation / rehearsal`。
`append` 严格校验并抛错，供验证工具使用；生产使用 `emit`，失败返回 False 且只记录常量诊断
`fc_log_projection_failed`，返回值不参与执行决策。`writer.path` 为输出文件。
公开 `validate_event(value: object) -> dict[str, JsonValue]` 可逐行验证；
`writer.failure_count` 计量该实例实际投影失败次数，供演练收尾验收检查，绝不是审计问题计数。

- 演练：`root/fc-logs/drill/mock/events.jsonl`；禁止 drill 的 live/replay executor。
- 普通运行：`root/fc-logs/runtime/{live,mock,replay}/events.jsonl`，各 provenance 硬隔离。
- Worker 自动接线五类（rehearsal 除外），路由概率按源数组索引对应，认领复用真实 token。
  资产仅投影实际 inject/validate/apply/adopt 调用；未调用不造数据。
  故障保留全部 14 字段和源时间、switched_to/cost_state/evidence_ref。
- Worker 先缓存资产/故障观察，执行、预算结算、租约清理之后再写旁路文件；不增加请求重试，
  不改变预算、breaker、路由决策、租约控制和旧 `fault_observations.jsonl`。
- Rehearsal 在旧 `rehearsal.json` 原子发布之后投影完整快照；read_rehearsal 仍完全只读。
  可将其返回的 replay 快照交给单独 replay writer，保持原 URI，不能冒充 live。
- `sequence` 在有源序号时保留源值，否则为 JSONL 行位置；跨类型不是全局唯一 ID。
  `at` 为源事实时间，耗时只用本次实际 monotonic 测量；故障耗时未知为 null。
  审计计数/issue_audit 默认省略，显式 null 合法，不生成假 0。

## 不可变接口与验证记录

接口提交 `6a04d7fe7f974305d57fec06bfad26d53cf8716f`；parent 为上述基线，已 push、
`git ls-remote origin refs/heads/morph-fc-log-wiring-0929` exact，提交后 clean。
最终生产修复提交 `1516d67b9b7d9316025533949b105fff36bc37c3`，parent 为 `6a04d7fe...`；
相对里程碑只改 `swarm/worker_loop.py` 与 `tests/swarm/test_fc_logging.py`（40 insertions / 4 deletions）。
修复只让 task 快照继承最后实际 admitted 候选的 provenance/origin，并在新任务开始重置观察来源；
未改候选选择、准入、预算或执行控制，公共 API 不变。后续交付提交只更新本报告。
七个实际 changed paths 为本报告、fc_logging.py、fc_log_schema.json、rehearsal.py、
worker_loop.py、test_fc_logging.py、test_rehearsal.py，均在写权内。

冻结源文档 blob `61af30bde619af296afdf1b68e029c119e95c7a3`，打包 JSON blob
`eecff835ba947869c93a4a072c701f7675c33d2e`；用两个 immutable Git blob 实测 fenced JSON
逐字节相同，SHA256 `1b4fc1f2dfe603a691b7a4d0dfe977a36bc99aebbfc40e37a0418f0e6355bffc`。

本树原无 `.venv`。参考 `morph-fc-integration-0927/.venv` 只读核版本：Python 3.12.13、
Pydantic 2.13.5、pytest 9.1.1、mypy 1.20.2、jsonschema 4.26.0。
本树大包下载尚未完成后由本 Owner 停止（两次联网安装终止均 exit 1）。主控消息
`msg_eee02d6cb691` 明确允许只读使用参考解释器执行本轨源码验证，未改共享环境。
当前正式验证解释器是上述参考 `.venv/Scripts/python.exe`，cwd 为本轨，
`swarm.worker_loop.__file__` / `orchestration.fc_logging.__file__` 均核为本轨绝对路径。
核所有当前平台生效依赖与本树锁版本一致，无缺失；`httpx2-jsfetch` 为 Emscripten 非生效项。
首次无条件核 89 包的脚本因该非生效项 exit 1，按锁 marker 核后 exit 0。

- 按 `poetry.lock` 生成 OS TEMP 固定版本 requirements；`uv venv .venv --python <参考解释器> --offline`
  exit 0；首次 `uv pip sync --offline` exit 1，cachetools 7.2.0 cache miss。
- 主控允许仅联网安装锁内依赖，不改锁/全局配置。第一次联网大包下载慢，停止本任务 uv 进程，
  原进程 exit 1；只为后续安装命令设置 NO_PROXY，继续同一锁定安装。
- `npm ci --ignore-scripts --no-audit --no-fund` exit 0，99 packages，保留锁不变。
- 本树 Python `compileall` 本轨源码/测试 exit 0。
- 参考 Python `-m pytest -q tests/swarm/test_fc_logging.py tests/t2/test_rehearsal.py`
  （OS TEMP 独立 basetemp）：首轮 29 passed / 4 failed，exit 1；次轮 33 passed，74.22s，exit 0。
  原失败未删：源 FailureObservationFact 少 observation_id，改为回读原故障文件的真实 14 字段；
  Windows monotonic 15.625ms 分辨率导致测量 0，新观察测时改 perf_counter 100ns，不改控制计时或弱化断言。
- `tools/typecheck.py` 首轮两处本轨类型错误 exit 1；修正后两次 strict 88 文件 exit 0。
- `-m build --no-isolation` exit 1：参考环境缺声明的构建后端 poetry-core；未安装到共享环境。
  默认隔离 build 第二次 exit 1：既有 pip 清华镜像下载 poetry-core HTTP 403，仍在 bootstrap。
  按两红规则保留失败并上报，主控 `msg_16f339f6a0d9` 批准只恢复既有构建器，不改验收标准。
- `UV_INDEX_URL=https://pypi.org/simple` 仅命令级；参考 Python `-m build --installer uv`
  在 OS TEMP 隔离安装既有声明后端 poetry-core 2.5.0，sdist + wheel exit 0。
- `uv pip install --python .venv/Scripts/python.exe --target <TEMP>/wheel-site --no-deps --offline
  dist/morphogenesis-0.1.0-py3-none-any.whl` exit 0；参考 Python `-I` 从 wheel-site 实际导入，
  检查 wheel 无 docs、包含原封冻结 JSON、真实 emit + validate_event 成功、failure_count=0，exit 0。
- `npm run check:sdk` exit 0：官方 SDK 1.14.0，schema_valid/asset_id_verified/tampering_rejected=true，
  published=false / contract_local。
- 语义 mutation：仅将 Worker finally 的 `_fc_flush` 替换为 pass，既有新测试 2 failed / 6.53s / exit 1；
  恢复后仅禁用 rehearsal 新 emit，2 failed / 15.34s / exit 1。两者均在真实入口已执行后因缺事件而红，
  不是收集错误。逐字节恢复源文件后联合 4 passed / 21.53s / exit 0，`git diff --exit-code` 为 0。
- **仅里程碑 6a04d7fe 源码的全量**：参考 Python `-m pytest -q --basetemp
  <TEMP>/fc-log-wiring-0929-evidence/full-state`：888 passed / 2 原有 Pydantic serializer warnings，
  799.36s，native exit 0。主控发停止指令时进程恰已自然退出，未执行 terminate；不能虚记中断，
  更不能将这份日志当作 1516d67 或最终集成 SHA 的全量。
- 混合 provenance 自审独立复现（`provenance-before.log`）：6a 账本结果为 replay，task 日志为
  mock/origin=null，native exit 1。主控 `msg_3d86a95932f0` 确认最小修复范围，并将最终全量交给 I。
- **最终生产修复 1516d67 的自验**：参考 Python `-m pytest -q tests/swarm/test_fc_logging.py
  tests/t2/test_rehearsal.py tests/swarm/test_failure_chain_runtime.py tests/swarm/test_failure_chain_boundaries.py
  --basetemp <TEMP>/fc-log-wiring-0929-evidence/final-focused-state`：55 passed / 105.48s / native exit 0，
  包含两个新增混合来源/不同原 URI 回归与原 20 项执行链测试；原测试内容没有改动。
- 最终 `tools/typecheck.py`：88 源文件通过 / native exit 0；最终 `-m build --installer uv`：
  sdist + wheel 通过 / native exit 0。新 wheel-site-final 安装及实际导入/emit 验证 exit 0，
  wheel 中 worker_loop 字节与最终源码一致、Schema 与冻结 fence 一致、无 docs 依赖。
- 冻结 JSON/原 P0 两测试/budget/breaker/lease/adapters/锁文件 diff 核对：除新增 JSON 外，
  原文件相对基线无改动；语义 mutation 归属 6a，最终来源修复是独立实际缺陷红→修复回归绿证据。

原始证据目录为 `C:/Users/DW/AppData/Local/Temp/fc-log-wiring-0929-evidence/`：
`focused-1.log` / `focused-2.log`、`typecheck-1.log` / `typecheck-2.log` / `typecheck-3.log`、
`build.log` / `build-isolated.log` / `build-uv.log`、`mutation-worker.log` / `mutation-rehearsal.log` /
`mutation-restored.log` / `mutation-results.json`、`full-1.log`、`provenance-before.log`、
`final-focused.log` / `final-typecheck.log` / `final-build.log` / `final-wheel-install.log` /
`final-wheel-smoke.log`。测试状态也全部在该 OS TEMP 根下，
没有触发或放宽源码路径保护。wheel 与 sdist 在 ignored `dist/`，安装验证与真实 JSONL 在 TEMP。

## 真实限制

Owner 自验不替代独立验收。所有行为测试使用现有 mock executor 边界和真实 Worker/
LangGraph 本地路径，未运行任何 live 模型调用；interface_live/task_live 为 NOT_RUN。
原 P0 / 五不变量测试保留且最终 focused 中通过；最终生产修复/最终共同候选的全量 NOT_RUN，
按主控安排由 I 对准确共同 SHA、LF archive 与源码旁独立状态重跑六门禁，不复用旧 SHA 全量。
本树 `.venv` 仅解释器就绪，完整依赖安装未完成；所有上述测试实际使用已授权的只读参考环境，
不宣称新部署环境已验收。生产合并/tag、三连冒烟、live 验收、H1/FC-E 均未由本 Owner 执行。
日志是尽力旁路：进程崩溃或 IO 故障可缺行；重启可能重复源序号，不能拿行数当请求数或审计问题数。
不建立第二套去重/完成证明系统，不用观察日志恢复或驱动远端执行。
敏感凭据模式导致整条旁路投影拒绝，以免改写嵌套事实；只输出固定诊断，不输出异常文本。
scope 的审计归属和人工证据真实性仍需审计人确认，Schema 不能代签。
