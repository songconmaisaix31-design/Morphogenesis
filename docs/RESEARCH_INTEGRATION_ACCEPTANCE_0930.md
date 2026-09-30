# 科研环境集成：主控独立验收记录

基线 ef77af603577d4539d8dbdf780e1536a369b0d12；计划 6ba12b24781318383454d2e7fb0b132e897b8a8d。Run run_4d81d03a8550 只用于开发协作，不进入产品运行。

## 事实与决定（2026-09-30 初始检查点）

- A Task task_f27c8a6ea322 / ctx_6837a8a3508f，B Task task_7e2b7e735229 / ctx_77f0ab05f391，C Task task_aaa3a884cf72 / ctx_fae36504f1ee。三者实际终端均 GPT-6.1-Sol high，分别在计划指定 worktree。
- 三个首次 Dispatch 在升级提示处 readiness timeout，未注入领域任务；跳过升级，执行只读 cwd/SHA/branch 探针后，同 Task、同终端重试，turn_started observed。保留失败，未新增重复 Owner/Task。
- MCP 入口由 B/A Handoff 收敛为 python -m swarm.research --config ABS_TRUSTED_JSON；宿主绑定身份/权限，工具不提供身份或数据库管理输入。该接口尚未独立运行验收。
- 既有续租函数没有 task_audit 续租事件；B获授权在原事务内增加最少审计。未知执行复用既有 begin_execution/confirm_execution，而非新 Attempt 系统。
- Docker daemon已由C启动；其原restart策略恢复其他项目容器，未修改它们。主控只读测得 host free约0.86GiB、guest available7269MiB。C按guest可用内存与实际峰值评估小型sandbox，不以host free读数单独认定不可运行，不停止他人资源或更改全局设置。
- ORCA源码MIT许可证（Copyright 2026 Lovecast Inc.）已独立读取；OpenSandbox检出089b59ad48af33fc2733de58bd1a39c687c93b0a与Apache-2.0许可证已独立读取。SDK发行版及来源对应关系仍待冻结交付核验。
- 科研正向经验准入固定要求真实执行、可信判据和独立复现。mock/replay观察可以保存，不能因同源模拟记录变为可继承科研经验；旧literal静态资产兼容性保留。此决定已Handoff B。
- 评审关注作者证据提交与独立复现的可达性，以及child继承本地再验证与静态检查；草稿阅读不等于任何验收通过。

## 门禁（未执行不得写通过）

| 门禁 | 当前状态 | 独立验收所需证据 |
|---|---|---|
| 新候选 contract_local | NOT_RUN | 冻结SHA、remote一致、互斥路径、真实账本边界pytest、strict/build/SDK/实际wheel及适用双平台CI |
| Codex原生科研MCP | NOT_RUN | native session/process、真实MCP发现/claim/renew/tool事件、账本身份关联 |
| Claude原生科研MCP | NOT_RUN | native session/process、真实工具事件与同一研究空间的账本记录 |
| OpenSandbox interface_live | NOT_RUN | 官方SDK/service/image版本、实际sandbox生命周期、原始命令/日志/产物及清理 |
| 科学实验与独立复现 | NOT_RUN | 预声明判据/版本，公开数据，独立worker/run/干净sandbox，可信原始结果重算 |
| 经验准入与实际继承 | NOT_RUN | 原资产链晋级、本地条件再验证、后续任务实际应用与AdoptionReceipt，检索/注入不算采用 |
| 中断、接续与旧持有者拒绝 | NOT_RUN | 实际中断前claim/续租、恢复/接续后fencing、旧token合法提交路径拒绝，无未知效果自动重放 |
| 无ORCA产品链 | NOT_RUN | 独立入口、无ORCA argv/env/运行时依赖，原生认证不复制HOME、不绕过权限 |

所有 Owner 自测与主控独立验收分列；最终报告不合并 mock/live 或工程CI/科研 task_live 结论。

## 主控检查点：原失败及冻结候选（2026-09-30）

- A最终648f43c54203f555b1b05827cfe119c8e3dfa622已push，remote/HEAD一致、工作树clean、19个改动路径均在A所有权内。Owner报告75个新contract、11个旧Codex兼容测试、10个严格类型文件及build/wheel通过。主控在同SHA独立运行 `python -m orchestration.native_agents probe`：Codex 0.159.0与Claude Code 2.1.238均版本匹配、官方认证true、版本/认证exit0。此为真实前置探测，不是模型调用、MCP或task_live。A固定Owner保留至集成返修结束。
- B阶段29446a0bf6619310a448599292b9197662425dc9的独立LF archive门禁失败(exit1)：真实TaskLedger调用一次mock backend，backend返回succeeded/exit0但缺effect_state，`assert_execution_confirmed`错误放行。原断言为缺effect必须保留unconfirmed，未改变；修复候选9f20d34a4e4f1e760a6449d029314957e8c9f210已push，待同断言独立复验。不将Owner新增自测代替原失败门禁。
- B同时退回旧Candidate canonical JSON兼容问题及科学计划role/local_path等价问题。完整原计划必须保存；只排除运行角色和本地输入路径，代码/数据/参数/条件/环境仍相同才可复现。旧literal资产身份、报告、批准、consumption、adoption必须用实际ef77持久记录核验。
- C首次live `interface-c-0930-01`（6179d41b336443e915b76d4da87b5267bec5193a）exit1：官方create/status/connect/renew已发生，目录API把0o700转换的448发送到wire而HTTP500，科研command_request_count=0。原result的execution/cleanup/remote effect保持unknown、科学not_evaluated、usage/cost=null。该run不重放，也不事后改绿。
- 同sandbox 96c5f98a-a204-4a69-8830-b5a34a91618c的后续独立只读GET=404、官方DELETE日志204且按ID/标签无残余容器，是后续清理事实，不改变首次失败。C修复SDK wire700/600并保留原失败及官方MockTransport回归；新候选23417b09ffc93fbc432da0f63a7abec2546fd825已远端核验，修复后interface/task尚NOT_RUN。
- C初全库诊断exit1：98 failed、785 passed、69 errors；运行期间SHA曾变化且Node锁依赖未安装，因此不能当不可变候选验收。保留失败及工具截断说明；允许仅npm ci --ignore-scripts补原锁依赖，在新冻结SHA用原测试/阈值作一轮门禁，不修改Node manifests/lock、不跳过失败测试。
- OpenSandbox发行SDK1.1.0官方重试及遥测disabled；公开NumAcc4原CRLF bytes完整性值固定，不把LF归一化数据当原bytes。正式验证通过原始输入和Fraction重算，不信Agent指标、自评或exit0。
- 最终I须使用实际宿主初始化入口和两种原生运行时；只合并与少量胶水，缺案例领域入口退回B/C原Owner。科研mock/replay仍不能批准；所有live门禁尚未通过。
### 当前基础设施限制与额外领域返修

- 主控在B9f20 LF archive的missing-effect/旧基线迁移两个probe均在Python导入阶段遇到OpenBLAS allocation失败exit1；串行设置进程局部OPENBLAS_NUM_THREADS/OMP_NUM_THREADS=1后，PowerShell模块加载仍System.OutOfMemoryException，未抵达原行为断言。这些是基础设施失败，既不算修复通过，也不替代最初真正失败门禁。
- 当前Windows只读资源：free physical约383320KiB，free virtual约9701152KiB；两个已存在Python进程各private约5.9GiB。主控停止启动新的Python并发，Worker已有门禁保留，不停他人容器或修改全局pagefile/Docker。C确认本轮full已用单线程BLAS，guest earlier可用并不能消除Windows此刻限制。
- B9f20科学准入还需对每份author/replication/inheritance可信结果检查effect为已知；仅科学判据通过的unknown效果观察不能跨持有者用于批准。科研claim的plan_id/criteria必须绑定预注册实验计划，不把不同顺序或适用条件虚报为相同。这些只读发现已退回B原Owner。
- C报告exact23417b09的CI36717414791 Ubuntu各门禁success、Windows仍pending；此为Owner自报待独立核验，不能组成完整候选通过，更不能证明科研task_live。
- OpenSandbox release-1.1.0的836b182e208e66c046026fa0f633e089321f1efb是annotated tag对象；独立git peel得到实际源码commit b1a29cf93a823a95913f7943010febb3f29de05c，与C文档一致。

## 接续总控独立检查点（2026-09-30）

- 原 Run 绑定当前 `term_bdbac2dc-861f-4ba9-af30-f44bd35cc2d7`，generation=2；B/C 原终端缺失派发已被运行时结算 failed，原 Task 恢复 ready。原 A 已 succeeded，但其旧终端的两次精确 release 均返回 `release_unknown`；没有广泛关闭或把未知资源写成已释放。B/C 原 settled 资源 release 返回 released/processAction=none。
- 同一原 B/C provider session 已分别恢复到原 worktree。两个 `worker-start --terminal` 均在 agent_readiness 超时，未投递任务；终端实际显示原 Codex 会话 idle 且 agentIdentity=codex，之后以低层 `dispatch --inject` 接续原 Task，当前 B `ctx_108469c068ef`、C `ctx_2a47ef3ebb5e`。实际 transcript 已证实开始工作；这种放置明确为 unsupervised，不冒称 supervised readiness 通过。
- 恢复会话继承原 workspace sandbox/审批配置，当前在读取技能文件的 require_escalated 弹窗等待；主控已请求用户选择开发 Worker 配置，未代按批准或绕过原审批。主控工具自身仍按本会话权限执行独立只读验收；后续依赖 Worker 的返修等待该配置确认。
- C exact `23417b09ffc93fbc432da0f63a7abec2546fd825` 的 CI `36717414791` 已由主控实际读取，Ubuntu/Windows pytest、strict、build、SDK、wheel 安装/分发全部 success。这不抹去 C 本机 full 的真实 `12 failed / 943 passed / 2 warnings`，原失败归档与诊断交回 C。
- B exact `28dc6d0b4ff73edd6da7c27d8ef6f359b95bc126` 的 CI `36719277559` 实际 failure：Ubuntu `4 failed / 955 passed / 1 skipped / 75 warnings`；预注册 plan_id/criteria 两个拒绝用例 DID NOT RAISE，两个 case 初始化用例被 symlink_or_junction 拒绝。原日志 `C:/Users/DW/AppData/Local/Temp/morph-research-B-ci-36719277559.log` 已交 B；不修改保护或删除失败取得绿色结果。
- 主控在原 B `28dc` LF archive 复用了最初 independent missing-effect gate 的相同 backend/真实 TaskLedger/原断言；只更新观察 SHA，进程局部 BLAS 线程为1。实际 backend calls=1、missing_effect_still_unconfirmed=True、exit0。原 `29446a0` 的 exit1 不改写；新门禁只证明缺 effect 不清除 execution_unconfirmed，provenance=mock/contract_local。该 archive 的 service.py blob 与 `28dc:swarm/research/service.py` 均为 `0c85b0dd8b5ca71357b0b1517da59d0297b1caa3`。
- 主控在 clean exact `28dc` 工作树实际运行原 `tests/research/migration_probe.py --baseline-source <ef77 exact LF archive>`，C 锁环境、进程局部 BLAS=1，exit0：实际 ef77 candidate JSON/address/report/approval/consumption/adoption 均保持。此为旧静态资产兼容契约证据，不是科学晋级或 live。
- 上述两个独立 probe 的原日志、真实退出和 missing-effect harness 保留 `C:/Users/DW/AppData/Local/Temp/morph-research-rootaccept-continue-0930/`。科研新候选完整 contract_local、原生 MCP、sandbox 修复后新 live、科学复现及实际科研 adoption 尚未据此放行。
- ORCA 来源独立核对：`.reference` 为下载文件集而不是 Git clone，不能把其中 `git rev-parse` 向上找到的 Morphogenesis HEAD 当上游 SHA。主控重新从官方 raw URL 的固定 `85f8d6b5f507df795cd3cef1cdea08124cf801ee` 读取 LICENSE 和 print-mode-headless-command.ts；以 `git -c core.autocrlf=false diff --no-index` 对照 A 许可与提交的未改动 TS，均 exit0。Node 实际执行原 TS 的11种 print/json/resume/option-terminator 输入，与显式期望相同，exit0；Node 的 MODULE_TYPELESS_PACKAGE_JSON 非致命警告保留。证据与下载原文件在上述主控 TEMP 目录。这只证明明确来源与原模块协议行为，不替代整个上游 Electron/Vitest 或原生 live。
- OpenSandbox 上游目录确为独立 Git clone：主控 `rev-parse --show-toplevel`、HEAD 实测 `C:/Users/DW/AppData/Local/Temp/morph-opensandbox-0930` / `b1a29cf93a823a95913f7943010febb3f29de05c`，已读取 release-1.1.0 的官方 Python SDK pyproject。产品 backend 直接调用 SandboxSync、ConnectionConfigSync、RetryPolicy.disabled、官方文件/命令/状态/interrupt API；没有新增容器运行时。真实修复后 live 仍待统一候选。
- B 两个 plan fixture 失败的源码诊断已交原 Owner：测试用默认 `connection(write=False)` 执行 UPDATE，而既有 context 仅 write=True 时 commit；退出后更新回滚，不能证明生产 guard 缺失。该判断仍为推断，待 B 核实真实持久更新后以原 raises/error/no_reports 断言复验；主控没有修改其实现或测试。

### 用户授权后的执行配置恢复

用户明确授权隔离开发全部权限，解决上述开发 Worker 配置等待。主控只取消两条自有待审批请求；读到两者 Conversation interrupted 后，停止旧低层 Dispatch（processAction=none），再关闭精确自有终端，两个回执均 ptyKilled=true。同一 B/C 原会话在原 worktree 以标准 CLI 参数 `--sandbox danger-full-access --ask-for-approval never` 恢复；不代按原审批，不复制凭据，不把开发权限写成产品能力。

当前 B Dispatch `ctx_e16666128554`、C `ctx_054ccfdf62bf` 均实际 injected=true；领域返修指令分别由 `msg_5b89bc3f5db9`、`msg_e53e560870c8` 持久发送。授权恢复本身不组成测试、科学或 live 通过。原八节任务及八项端到端标准已从历史终端完整读取；新候选与 I live 尚待执行。

- C 仅恢复自有 `morph-research-c-0930-server`，未创建新科研沙箱；主控使用私有 key 路径（未输出内容）独立 GET `/sandboxes`，HTTP200。此为服务可达性，不是修复后的实验通过。
- B `fb280e6a6e2d30c66b45fbe8c693084727b11221` 已 push，Owner 新 focused35/strict98通过。主控读取实际 diff 确认 fixture 只加 write=True，原拒绝断言不变；该阶段解释器 resolve 仍可能把 Linux venv 入口替换为 base executable，已以 `msg_d08c09b2835d`、`msg_40c0fc577caf` 退原 Owner，尚未最终接收。
- I 原标准中的“旧持有者不能提交生效结果”必须在真实公开工具提交路径观察陈旧 token 拒绝；单独 renew 拒绝只能证明续租门禁。中断安排在作者认领/续租后、任何外部实验前，由实际 native/ledger 证据确认；原生取消的未知字段保留，不能据此自动重试外部实验。

### 领域交付与 I 起点

- B `428de06dcaaa780a2e5c617402508ae07179480b` 已 remote 一致、clean；相对源码 `9ad7387c34bd0995df51f2dbb5cba8fc8bb7e7e7` 只有本轨报告变更。Owner在该源码35 focused、strict98、实际锁解释器 MCP 导入/venv prefix/原入口保持、exact archive 离线 C 桥与隔离 sdist/wheel 均 exit0。新 CI `36727919838` / `36728382126` 在交付时 pending，尚未当完整候选通过。真实 live NOT_RUN。
- C `5feb507727c19812edcbcdccfc27c12bf9576899` 已 remote 一致、clean；相对已核验 CI 的 `23417b09ffc93fbc432da0f63a7abec2546fd825` 仅4份文档。主控复核 I_HANDOFF 与 README 均使用 inheritance order=original，不把 reverse 不同条件迁移成正向继承；源码/测试/依赖未更改。原本机失败完整分类，不把所有根因归成 OOM。
- B/C accepted worker_done 后各自精确 worker-release 均为 retained/no_owned_resource/processAction=none，这是 unsupervised 归属结果，不声称开发 PTY 已退出。原 A 旧资源 release_unknown 仍保留。
- I 已在上述固定基线与治理输入启动 `task_afa0f9c81b55` / `ctx_9e1033019bc7`，真实屏幕 Working。主控未写领域代码；合并候选全门禁及科学 live 仍待 I 实际完成。

### 第一个精确合并候选及真实拒收

- I `85a921c49addcdd46c2cb4a307c3515356b3e186` 已 push、remote 一致、clean；主控先在其源码相同的 `12f99ee9cd224d4301599ae6c159ad217109641b` 验证 A/B/C 均为祖先，三份领域树与 Owner 最终提交 diff --exit-code 全为0。`85a921` 相对 `12f99` 仅合并最终治理文档。
- I 自有最终锁 CPython3.13 环境中领域 focused140 passed（73.18s），原 package-lock npm 安装 exit0。完整原 pytest 正在串行运行，不能提前写通过。
- 主控独立读取 exact headSha CI `36728997575`：Ubuntu `1 failed / 1062 passed / 2 skipped / 75 warnings`，388.10s；Windows cancelled，后续 strict/build/SDK/distribution 未完成。首个合并 gate 为 FAILED，原日志由 I 保存 `morph-research-integration-0930-state/ci-36728997575-first-failure.log`。
- 唯一失败 `tests/native_agents/test_process.py::test_unknown_launch_exit_and_mock_cannot_be_live`：CI 没有 Codex，resolve_executable 先抛 FileNotFoundError，未到原 `pytest.raises(ValueError, match="official CLI")` 防伪断言。不是实际 live 放行；不能靠安装/登录 native CLI、删除/跳过或修改原断言取得绿。已退 A 原 Owner，只在外部发现 fixture 边界修确定性，真实 guard 保留。
- A 原会话实际显示既有 completed worker_done 后 final idle，再在原 worktree/分支恢复标准授权配置，创建返修 Task `task_b73e5e520a3e` / Dispatch `ctx_85eecf66ce51` / terminal `term_e24cbaa2-8435-47fb-9e02-9bf97a625886`；injected=true 且 actual Working。原 A 交付及原资源 release_unknown 不改写，不广泛清理。I 独占 Python 窗口，A 先做原 fixture/文档的窄返修，不并发测试。
- I 原无模型权限 probe 被 PowerShell ExecutionPolicy 拒绝，尚未触及目标文件，原失败保留。I 后续报告同一官方 read-only sandbox 的 Node 写 sibling sentinel 实际 EPERM、sentinel 不变；主控要求按本案例实际 read-only 模式记录，不把启动脚本拒绝当文件边界实证。科研 native session 及新外部实验尚未开始。

### 窄返修与原标准范围裁定

A阶段 `f37ada292f61a28899666a84a8c988da5a4c0a40` 已 remote 一致、clean，主控实际 diff：只有原 test_process.py 的外部 resolve_executable fixture 与本轨报告，生产树未变，原 raises 类型/quote、unknown 和禁止 fake live 的断言未变。本机验证尚 NOT_RUN，排在 I 串行 full 后；不把阶段提交当最终验收。I 若 full 在当前 worktree 运行，则退出后才合并，不让变化中的运行冒充不可变 gate。

I审查指出科研资产路径没有生成旧 `metabolism.models.UseRecord`。主控重新核对原终端任务：用户要求沿用现有 adoption、区分检索/注入/实际采用及可追溯继承，没有要求该具体旧类。当前 `ConsumptionExecution` 与 `AdoptionReceipt` 复用既有 adoptions 表，绑定 source/child/context/result/时间；record_adoption 先核验真实 completed fenced task、result 一致和目标 bytes，符合原任务的实际使用记录语义。I spec 中多列 UseRecord 是主控范围假设，已以 `msg_ad610e51738d` 纠正；不得为此追加 Gene/代谢存储或手造 UseRecord。

正向科研验收仍必须核验真实持久 Receipt、ConsumptionExecution、canonical attempt/claim/result/bytes 完整链、源经验与子任务关系及检索/注入/采用的区别；没有放宽科学、文件、fencing 或任何原断言/阈值。若既有真实采用链有缺口仍退 B 原 Owner。此为范围裁定，尚无 live 通过证据。
