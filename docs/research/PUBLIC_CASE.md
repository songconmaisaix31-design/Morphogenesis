# 最终 I 的可运行公开案例

本入口属于 B 领域实现；I 仅合并冻结 A/B/C 后接线。初始化只产生真实任务上下文、预声明计划、固定文件policy和三份宿主配置，**不认领、不运行、不批准、不记录采用**。只用C唯一公共NumAcc4 factory，B没有第二实验执行器。

在最终集成源码和锁环境中，选择不存在的绝对项目/状态目录，状态必须在Agent可写项目之外。先由宿主建立操作系统访问边界和受保护OpenSandbox服务key环境变量，再执行（PowerShell示意，替换成真实已核验路径；不要在参数中放密钥）：

```powershell
python -m swarm.research.case --project C:/research-demo/project --state C:/research-demo/host-state --python C:/locked-env/Scripts/python.exe --case-directory C:/integrated-morph/demo/research_case --swarm-id nist-live-0930 --domain 127.0.0.1:8097 --api-key-env MORPH_OPENSANDBOX_API_KEY
```

入口拒绝已存在目录、软/硬链接、项目与状态嵌套及受保护源码目录；不覆盖WIP，不复制HOME、不改原生认证。输出三份配置的绝对路径、原仓基线revision及解释器路径。配置只存key的环境变量名。首次创建失败的部分状态保留，不能复用同一root静默重跑。

任务固定 `author → replication → inheritance`，通过既有TaskLedger dependencies发现可认领项；角色资格为 `research.author` / `research.replication` / `research.inheritance`，宿主绑定不同worker/AgentId。副本可以在相同授权scope阅读前置科研上下文，但无法认领不合资格的任务。每个任务最多一次外部实验（未知也计入，绝不自动重放），正常claim还受原RunLimits/attempt预算约束。

A的已冻结原生入口接三份 `HostConfig`，每份MCP形状均为 `command=<绝对python>`, `args=["-m","swarm.research","--config",<对应配置绝对路径>]`。原生运行分别使用Codex作者、Claude复现者、Codex继承者（或交换品牌，仍须至少两种且不同worker）。最多三个研究session；I调用前检查原生权限、工具轮次/时长及预算授权，未知token/cost保留unknown。具体A argv/启动规范来自其领域入口，不经Orca产品运行时。

给三者的统一bootstrap：读取MCP metadata，主动 `discover_tasks`，`lease_task(action=claim)`；读 `project_context` 的task acceptance/payload和 `dependency_results`；按上下文中的instructions工作。claim返回原Lease和canonical `attempt_id`，提交candidate把该attempt_id放入既有Candidate.attempt，不能自己换身份。

| 会话 | 可运行顺序 | 真实完成事实 |
|---|---|---|
| 作者 | claim/renew → research_experiment request/run → research_candidate submit（payload.candidate_template + claim返回attempt_id）→ verify_research purpose=original → complete_research_task | 候选仍quarantined；作者task.completed/effect_applied=false仅表示证据工作完成，允许不同worker主动发现replication |
| 复现者 | 从dependency_results读取author.result.asset_id → fresh run → verify_research purpose=reproduction → research_candidate validate_files → approve_candidate → apply_candidate原候选 | 两份可信raw证据科学内容一致、不同worker/run/sandbox，原静态安全通过；受账本fence写science/experiment.py；replication.completed实际effect_applied=true |
| 继承者 | 同一来源asset → fresh local run → verify_research purpose=inheritance → inherit_experience（map science/experiment.py→science/reused.py、preimage null、payload.base_revision）→ validate_files child → approve child → apply child及execution_id | 条件匹配和本地再验证；child走原ConsumptionExecution关联parent；新静态门禁及真实目标bytes/ledger/result一致后才有原AdoptionReceipt |

操作每步均以实际返回为事实源：获取本次 run_id、report_id、child candidate_asset_id、execution_id、result_id，不预填expected ID或通过。反例/失败复现使经验不可继承；missingartifact、failedcriterion、infrastructurefailure、unknown分开，不用exit0代替科学通过。任何unknown停止该live路径，不换mock或手造approved/adoption补齐故事。

三份计划科学条件一致，只变role；继承任务不偷偷改为reverse顺序。报告的plan/判据必须对应预注册claim，各原始结果必须已知effect；科学达标与远端效果确认分别保留。继承输入payload.base_revision作为HEAD锚点，服务复用现有scope快照纳入复现者先前apply的science/experiment.py，再生成science/reused.py child，防止沿用旧scope树造成snapshot_target_changed。

中断/接续安排在作者**claim/renew之后、execute之前**：I根据真实原生日志确定尚无execution_unconfirmed，再只中断自己创建的原生进程；等真实TTL过期，在同一个原生session_id/同一HostConfig恢复。先用原token证明renew拒绝，再主动claim取得更高token并继续作者任务。该安排仍只有三种研究session身份，不新增第四个研究者，也不误杀附着会话。若已越过实验边界或日志无法确认，保留unknown并停止，不能据此声称接续通过；I单独记录 NOT_RUN。

完整live正向链、原生工具调用/认证/会话、干净sandbox及真实adoption由I实际验收。B离线probe明确mock且科研quarantine，只证明接线/失败门禁；初始化输出和固定计划都不等于运行通过。
