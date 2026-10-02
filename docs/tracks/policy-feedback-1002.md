# 可信反馈与恢复 v0.1（C，1002）

状态：C 领域代码与定点验证完成，最终 SOURCE `9796d23c1f978b96baec5b8625ced55aa98816ea` 已普通推送并核对远端 exact。仅离线 contract_local，不签科研 task_live 或五项总验收；最终组合完整工程、新安装与原完整 checker 由独立 I 验收。

## 归属与来源

Task `task_0bdb64a48b89`：原 Dispatch `ctx_72737f3d2607` 在 Orca 重启后由主控撤销，当前唯一恢复 Dispatch `ctx_fe917d7d319e`。主控更正 placement 后使用原 agents worktree 与新分支 `songconmaisaix31-design/morph-policy-feedback-v01-1002`；sandbox worktree 仅核对，保持 clean、原 `dcb23d993ce3562993c20f5118209bc49ccae234`，无修改。原 agents 分支 `1532cdbcf549c3050b3e9617d8d44793f6f16834` 保留。恢复时 HEAD `51f81845b4ad831b58be0c66bd182e05efcb517c` 与全部四项 WIP 保留并由同 Owner 收口，没有新增 Agent、分支或 worktree。

从科研冻结 `7b66f0dd0a285c1b6cf789aa3c5a41d22d655993` 普通合入治理 `5a4fe1d2f5bdaf941493e9c195188c9a7dee408c`。C 先验接口独立 SOURCE `7844cf21b32145c55f714b12848e878e332f70c5` 已正常推送并核对 remote exact。精确消费 B 最终代码 `4ed6561504c56288e2335d88da72bd172b1c2a7f`、D helper `69f586e79adb23cae5d6bb21f3c46e22b0cc850e`，未跨轨修改源码。复用原 SQLite/Pydantic/标准库与原 TaskLedger、资产、科学报告、采用回执；没有新调度器、任务副本、Attempt/Manifest/hash/采用证明。

## 学习事实与恢复

`swarm.feedback.trusted_facts` 只接受原账本 completed authority：结果 ID、唯一 completed 审计 token/时间、原 task_attempts worker/outcome 与原结果一致，无未确认 execution。文件候选必须关联同一不可变验证报告、候选/资产、范围、策略、原应用层接受时的有效期和真实 applied 效果。普通 Worker 原 AttemptId 是 claim 前零基计数，研究入口为 claim 后计数；两者分别核对，均不替代 fencing token。

科研结果还必须有当前 task/worker/token/run 对应的原 ResearchObservation、预注册 plan/claim/条件、succeeded/passed、known/confirmed effect、原 research_execution 与 execution_confirmed lineage。恢复来源 token、attempt、swarm 不能错配。文件验证 passed 本身不能奖励科学。继承时科学报告可在源资产上，静态报告在新 applied candidate 上；实际 consumption/adoption 回执须同时匹配权威结果、候选、输入上下文、worker/token/scope 与 source asset。

最终窄修补充核对科学报告字段、报告内原 evaluated result 及持久 research_execution 的 verdict/provenance 一致性；调用者 passed 或相互冲突的原执行结果不能奖励。静态文件报告只核对自身时间区间有效，原应用层已接受的历史完成结果不与账本受控时钟跨域比较；研究报告与账本的原时间来源核对保留。

分类为 `validated_completion`、`scientific_result`、`scientific_adoption`，保留各自 live/replay/mock/contract_local provenance。每个原完成结果只能属于一种类别；报告及实际 adoption ID 是同一结果的来源限定，不是额外两个奖励。未知效果、未验证/错身份/错来源事实没有科研正奖励；mock 科研报告仍是 mock 合约证据，不能成为真实科学验收。

派生 `learning_facts` 去重键是原 result ID + kind。原事实保持只读，派生信号/history 在既有 SQLite 短事务中一起重建，以 `(原完成 at, result ID, kind)` 排序。使用原信号 created_at 和原事实时间作衰减锚点，不以重建当前时间刷新旧奖励。新增 keyword `prior=None` 保留原零中心 history；v0.1 显式 .25 居中读取与 reinforce，alpha/tau 不变，数学由 B 所有。

Worker 的原 `feedback_started`/`feedback_complete` 状态边界保留。原两次 feedback/reinforce 调用在成功 pair 后才一次提交派生索引；中途异常没有半个学习写入。持久 started 且未 complete 仍为 `feedback_incomplete_requires_review`，不会自动重放 Executor/模型/实验。明确的派生重建只读可信事实，不能补写 Worker 完成标记、科学状态或采用回执。原未验证 rejection 仍为原非科学负反馈路径，不把其异常/未知效果升级为科学成功。

## 正式入口与只读 API

原 11 MCP 名称及参数不变。`ResearchService.discover` 使用共享 Router 的显式 v0.1，并记录一条原 routing 审计。原 list 首项 `policy_recommendation` 是完整建议，其余项只含 `routing_sequence/policy_version/selected/reference_only`；不重复复制全轮候选。100 候选窗口仍按 created_at/task_id，窗口外没有参与 softmax/探索。

Agent 自主 lease_task claim。原账本重新裁决资格，成功后 `policy_selection` 记录实际 task/token、建议或覆盖、同一原 routing sequence、policy version、完整候选条件、反馈来源。关联验证同 worker、完整 locality、版本，以及权威 TaskRecord 的 workspace/scope/module/capability/dependencies；消费过的建议不再次关联。无建议时字段保持 null，不宣称遵从。推荐不检查模型 budget admission，不授权跳过依赖/能力/租约/未知效果或自动认领。claim 与附加 selection 审计是两个原短事务；中间进程崩溃只能保留 claim 而缺选择观察，不能推断 Agent 遵从或自动重试 claim。

产品支持的核心函数：

```python
swarm.feedback.policy_diagnostics(
    config: HostConfig, *, rebuild_to: Path | None = None,
    seed: int = 0, limit: int = 100,
) -> dict[str, JsonValue]
```

返回 `policy`（共享 B recommend，去掉 payload）、`feedback`（原来源 ID/种类/原 at/provenance）、`source=existing_authoritative_facts`、`rebuild`、`evidence_class=contract_local`、`execution_invoked=False`。默认没有 TaskLedger/AssetStore/Field 写初始化，没有 auth/backend/Executor 调用。seed 只控制共享标准库抽样，不修改评分公式。

默认档案读取是 `mode=ro/query_only`，只对已经 checkpoint、没有非空 WAL 的档案使用 immutable。非空 WAL 或读取期间改变明确拒绝；不丢失未 checkpoint 页、不 checkpoint 原档案、不创建新辅助文件。正式运行中的 Worker/ResearchService 已拥有其可写 runtime，使用原 SQLite read transaction 读取事实的一致快照；这不用于操作员的只读档案入口。

显式 rebuild_to 必须为不存在的绝对独立派生文件，位于 workspace、ledger 父根、assets、evidence、安装包之外。只重建该偏好库，不修改科学源。实际科研/采用仍由原判定；偏好可再生但不能作为科学证明。

同 author capability 的两合法候选可以保持原角色绑定，使用不同原信号坐标（如 concentration 1 与 2）。同 pipe 的可信历史 .25→.2625 通过 B 既有 softmax 改变两候选概率；不把 completed source 再开放为新任务，也不改角色调度或阈值。这个结果是离线策略行为，不表示模型实际改变选择。

D 的 `projection_status()` 仅加到 Worker status/audit 观察字段。missing/available/incomplete、failure count/cursor/reasons 不控制执行或奖励；available 不证明 FC 覆盖完整决策，完整策略仍在原 routing 审计 policy_candidates。

## 环境、首结果与验证

新私有状态根 `C:/Users/DW/orca/workspaces/Morphogenesis/morph-policy-feedback-v01-1002-state-ctx72737f3d2607`，fresh CPython 3.13.13 copy venv、冻结 Poetry export、非 editable wheel 安装，103 原依赖；只复用自身官方同锁下载 cache。Node 在本 venv site-packages 按原 package-lock npm ci 安装。BLAS/OMP/MKL 局部 1，未复制旧 venv/node_modules/test artifact，未改 global HOME/auth/provider/model/network。

Windows Git worktree 需要短 private test 根，因此新增独占 `C:/Users/DW/orca/workspaces/Morphogenesis/pf72737-state/t`。所有新 basetemp 在该 TEMP/TMP 根内。不得把最初长路径失败改为通过。

| 保留证据 | 实际结果 |
| --- | --- |
| 05-prior-first-red.log | 原安装接口不支持 prior，1 FAIL/TypeError |
| 08-prior-pass.log / 09-prior-strict.log | 新先验+原 field 6 PASS/7.55s，strict1 PASS |
| 14-feedback-first.log/xml | 5 FAIL/1 PASS；长路径 Git worktree、FC 路由 schema、MCP 包装及 SQLite sidecar 首失败 |
| 17-feedback2.log/xml | 2 FAIL/4 PASS；真实 Worker 零基 AttemptId 与新 reader 的不匹配；原 incomplete 安全测试通过 |
| 21-feedback3.log/xml | 2 FAIL/10 PASS；测试 sqlite context 未 close，真实 WAL 拒绝；原断言保持，fixture 显式 close |
| 24-feedback4.log/xml | 60 PASS/2 FAIL，412.67s；两个原 SDK 10s timeout，不调阈值，整体仍 RED |
| 25/26-candidate-*-strict.log | 首类型缩窄错误保留，待修后专项 |
| 29-candidate5.log/xml | 17 PASS/2 FAIL，476.19s；跨成员恢复的子进程误导入工作树、另一个原 SDK timeout；整体仍 RED |
| 33-source-win-strict.log | responses 类型注解首 RED，后续补显式类型 |
| 34/35-final-*-strict.log | Windows/Linux strict 各 4 files PASS；尚待最终时间域修复后增量检查 |
| 36-ci-ubuntu-first.log | SOURCE51f CI36915351295：Linux 1190 PASS/1 FAIL/6 SKIP/75 warnings，461.93s；Windows cancelled，下游 SKIP |
| 30-serial-control.txt | 按主控要求取消自己拥有的并发 mypy，NOT_RUN；未动附着/其他进程 |
| 37/38-feedback6-*.log、39-installed-origin.log | feedback6 wheel build/install 成功，非 editable，bridge/feedback origin 均为私有 venv site-packages；恢复时四个反馈核心文件与 WIP 内容相同 |
| 40-final-focused.log | 重启后为空且无对应 Python 测试进程，没有终止或通过结果，保持 NOT_RUN |
| 41-resumed-focused.log/xml/exit | 新恢复 Dispatch，neutral cwd 安装环境串行 17 PASS / 87.25s / exit0：新反馈与入口14项、原 renewal、feedback incomplete、cross-member adoption restart 三项 |
| 42-resumed-sdk.log/xml/exit | 原 negative original observation/recovery [True] 定点 1 PASS / 7.17s / exit0；SDK 10s 原阈值保持 |
| 43-resumed-unknown.log/xml/exit | 原 successful science/unknown effect [original-unknown] 定点 1 PASS / 2.98s / exit0 |
| 44/45-resumed-*-strict.log/exit | Windows/Linux strict 各 4 source files PASS / exit0；平台选项类型检查，不冒称两操作系统实际运行测试 |

CI 唯一失败为原 `test_renewal_keeps_slow_local_execution_owned`：应用与账本完成已有权威证据，但新学习 reader 将静态报告的系统时间与受控账本时间比较，错误拒绝合法事实，触发原 finalize 的 AssetSafetyError。最小修复不再跨时间域比较；原应用层 expiry guard、原续租时钟和断言均不改变。报告自身 expires_at 必须晚于 created_at；原科研报告与账本共享时间域的来源条件保持。此次 CI firstRED 不回写或改绿。

网络首失败：猜测 D 的 remote ref 不存在，git fetch exit1 原样记录；随后以主控已推精确 SHA 普通合入。向已 settled D Dispatch 发送 Handoff 被 CLI 拒绝，改交主控；FC 边界最终由原 B 修其 routing 审计，不改 D/schema。

最终验证命令：私有 `venv/Scripts/python.exe -I -m pytest`，从中立状态根运行，`--import-mode=importlib` 沿用仓库配置，`-p no:cacheprovider`、独占短 `--basetemp`、独占 XML，41 选上述两份新测试文件与三项原 Worker/restart 用例，42/43 选两项原 SDK 首失败用例。私有 `python -I -m mypy --strict --platform win32` 与 `--platform linux` 串行检查 `swarm/feedback.py swarm/pheromone.py swarm/worker_loop.py swarm/research/service.py`，各自新 cache；`git diff --check` exit0。恢复后没有新增领域逻辑或改动原测试，只提交保留的 WIP 窄修，SOURCE 普通 commit/push，远端 `ls-remote` 等于上述完整 SHA。

这些是当前安装候选的定点领域证据，不能替代完整工程，原首 RED 及 40 NOT_RUN 均保持。报告独立 docs-only commit；其实际 REPORT SHA 见最终交接/远端 branch head，不在文档中自引用。完整工程、产品新安装、原科学 checker 与五项总门由独立 I 验；本轨不签 task_live，不执行新科研/模型/API/登录或修改旧案例/时钟/checker，也不变更 main/tag/生产 pin。A 已收到新恢复 ctx 的稳定 API Handoff，正式核心 pin 等待 I 最终冻结。

