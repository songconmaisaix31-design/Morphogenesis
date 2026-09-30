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