# B 有界评分 v0.1（2026-10-02）

当前状态：B 有界交付完成，最终 SOURCE `b0f3b2ada4b41839c4472cb2ce208a0db93b591e` 已正常推送；83 项相关回归与 Windows/Linux 的 Swarm 23 文件 strict 通过，首 RED 保留。评分与只读推荐属于 `contract_local`。已精确消费 C 先验接口 SOURCE `7844cf21b32145c55f714b12848e878e332f70c5`，B 未修改 C 文件；本文件为随后单独提交的报告。安装后正式产品接线、可信反馈来源及五项整体停止条件由 C/A/独立 I 验收，本报告不代签整体策略冻结。

本轮从科研冻结 `7b66f0dd0a285c1b6cf789aa3c5a41d22d655993` 建立 `songconmaisaix31-design/morph-policy-score-v01-1002`，普通合入治理 `5a4fe1d2f5bdaf941493e9c195188c9a7dee408c`。原文档 I 分支 `1cb2d9685fa67fdfc578d25674e7b61fb2819d7b`、原科研 B 分支 `d228d43e9c12ca9743a362a7f1187cda4d8218ee` 保留；未操作公开 main 或用户根工作区 WIP。B 仅写 Router、新的局部测试及本报告；C 拥有信息素、可信反馈、Worker 与科研接口。

## 一次校准的含义

保留稳定 softmax、年龄加权探索、浓度衰减和原学习率。本策略是局部离散启发式，不宣称最优、收敛或未经测量的性能提升。两个原循环中的分母求和各外提一次，未做性能实验。

设 `h` 是 worker/pipe 历史，`c` 是已衰减浓度，`u` 是原紧迫度，`m` 是 `[0,1]` 能力匹配，`a=1+min(10,age/aging_seconds)`。参数与版本如下：

| 项 | v0（兼容默认） | v0.1（正式新入口显式选择） |
|---|---|---|
| 评分 | `beta*h*c*m*u*a` | `beta*h*(2c/(1+c))*m*(2u/(1+u))*a` |
| 浓度/紧迫度尺度 | 原单位乘积 | 固定单位尺度 1，两个因子各在 `[0,2)` |
| 单位输入 `c=u=1` | 原尺度 | 保留原尺度；并非所有旧输入都等价 |
| 极大 `c/u` | 乘积可使偏好饱和 | 有界因子保留历史相对影响，评分不超过 `44*beta` |
| 历史读取/反馈 | 保留原零中心衰减 | 使用 C 显式 `prior=.25` 的居中衰减读写 |
| `beta` | 默认 1，允许 `[0,1e6]` | 同左；大 beta 仍可使 softmax 饱和 |
| 探索 `epsilon` | 默认 `.05`，允许 `[0,1]` | 同左；显式 0 关闭探索保底 |
| 时间/学习 | `tau=86400s`、`alpha=.05`、`aging_seconds=86400s` | 同左；tau 是时间常数，非半衰期，alpha 是奖励学习率 |

`p_i=(1-epsilon)*softmax_i+epsilon*a_i/sum(a)`，softmax 先减最大评分。默认非零探索下，窗口内每个合法候选至少得到 `epsilon*a_i/sum(a)`；该保底不授予非法候选资格。单位输入的常规成功奖励仍为 `.5`，历史第一步 `.25→.2625`，失败奖励仍为 0；不改变科学判定或成本/用量语义。

选择有界因子的理由是单位输入兼容、零浓度仍为零、随浓度和紧迫度单调、极大输入不再无界相乘。没有搜索参数或与其他算法排名比较。源代码确认旧历史记录衰减到 0，而从未见过的历史为 `.25`；已消费的 C 窄契约为 `prior+(stored_h-prior)*exp(-dt/tau)`，旧 `prior=None` 继续原式。反馈以同一 prior 读取再原 alpha 更新，没有只改展示值或重写旧时间锚。原始成功/失败样本、更新时间、次数均保留；衰减影响派生偏好，不改原任务或科学证据。

## 共享推荐接口与边界

`Router(field, strategy_version="v0.1", rng=random.Random(seed))`；`choose(worker_id, locality, capabilities)->Signal|None` 的签名与默认 v0 保持兼容。两个公开入口共用一个候选、评分、探索和采样实现，不复制公式。

`recommend(worker_id, locality, capabilities, *, limit=100, record_audit=True)->dict[str, JsonValue]` 返回：

- `policy_version` / `strategy_version`：同一显式版本；`selected` 是建议 task ID 或 null；`recommendation` 是该候选的 scope、task_kind、payload。
- `signals`：task ID、scope、module、required_capability、dependencies、status、created_at、原浓度/紧迫度、历史、匹配、年龄、尺度因子与评分；`softmax` / `probabilities` 同顺序。
- `authorized_scopes` / `modules` / `dependency_of`、`filtered`、`constraints`、`query_limit`、`window_order` 和实际参数。filtered 只描述可见局部窗口，不泄露 scope 外任务，也不是全库排除清单。
- `history_prior` 明确是 `.25` 或旧版 null；`advisory_only=True`、`claim_requires_recheck=True`、`budget_admission="not_evaluated_by_router"` 不把建议误报为预算许可。
- `routing_sequence` / `audited`：默认在原 TaskLedger 短事务中写一条 `routing`，同连接取得既有 `task_audit.sequence`；不建新 ID、表或调度状态。返回的行号对应审计行元数据，未循环查询最新行猜测关联。

窗口是在账本局部资格过滤后，按 `created_at,task_id` 排序的前 `limit` 个，`limit` 只能是 1–100。窗口外本轮不参加 softmax 或探索；不分页、轮转或承诺全局最优。TaskLedger 继续过滤依赖未完成、能力、scope/module/邻域、活跃重叠租约、尝试上限和未确认效果。推荐快照与后续 claim 间可能变化，claim 仍须由原账本重新裁决，预算/租约/科学权限不能由评分授予。

`record_audit=False` 只供宿主只读诊断，复用相同算法但不调用写事务；明确返回 `routing_sequence=None, audited=False`。正式 discover 固定 True，不能把此选项开放为 Agent MCP 参数。C 可用原 routing 行号记录成功 claim 的实际选择、是否覆盖和版本/候选条件；选中建议本身不是实际选择、执行或完成。A 从 C 的原 11 MCP 工具消费，不复制算法。

## 已执行验证与当前限制

私有环境：`C:/Users/DW/AppData/Local/Temp/morph-policy-score-1002-484a581deed8/.venv`，Python 3.13；官方 Poetry 2.3.2 导出本仓锁文件，uv `pip sync --require-hashes` 安装 102 个锁定依赖；未复用旧 venv。BLAS/OMP/MKL 仅本次子进程设为 1。无需 Node/模型/沙箱/Hub 服务。

首 RED：`02-first-red.txt` 中新 API 在原 Router 上因未知 `strategy_version` 参数失败（1 failed，exit 1），原样保留。后续通过是新增证据，未覆盖首失败。

先验实际首 RED：`10-prior-first-red.txt` 用真实偏好库的失败样本经过 `100*tau` 后，已见历史为 `8.835180443049486e-45`，未见历史为 `.25`，原 `[.25,.25]` 断言失败。保留该记录，用它验证 C 接口消费前后的行为差异；不得放宽断言或仅改推荐展示。

- `03-score-tests.txt`：旧 Router 与初版新行为 15 passed；`04-router-strict.txt`：Router strict 通过。
- `05-early-regression.txt`：Router、新评分、field、ledger、lease、budget、unknown-effect recovery 七个测试文件 76 passed；两个原 Pydantic 非法输入告警保留。
- `07-readonly-api.txt`：新增只读事务拒绝测试后，旧 Router 与新行为 16 passed；`08-readonly-strict.txt`：Router strict 通过。
- `09-swarm-strict.txt`：Swarm 全部 23 个源码文件 strict 通过（薄接口阶段）。
- `11-final-regression.txt`：消费 C SOURCE 并完成全部 B 源码后，八文件 83 passed / 2 个原非法输入告警 / 53.46s，exit 0。
- `12-final-windows-strict.txt`、`13-final-linux-strict.txt`：同一最终源码 Swarm 23 文件 Windows/Linux strict 均 exit 0。
- `git diff --check` 通过；`14-source-push.txt` 保存正常推送，实际 `git ls-remote` 核对最终 SOURCE 精确；源文件均已提交，报告单独收尾。

测试使用真实 SQLite 账本与偏好库，种子 17、两个合法候选验证共享 choose/recommend 的一致性及成功/失败反馈概率方向；直接反馈是离线合成输入，不能冒称科学可信证据。极值包含 beta 0/1e6、浓度 0/1e12、紧迫度 0/1e6、近零匹配、历史 0/1 和长年龄及近零 aging 常数；高分缺能力、scope 外、依赖未完成和过期但效果未确认任务不能入选；第 101 个高分候选不进入窗口。只读推荐明确禁止调用 transaction，并核查审计和任务状态不变。建议返回后另一 worker 仍能合法取得租约，原建议方不能凭建议抢占，下一次推荐排除该任务。

过期历史原 `[.25,.25]` 断言现通过：成功/失败样本在 100*tau 后回到先验，读取前后旧库 weight/samples/anchor 相同，旧版对同一记录仍趋近 0，晚到常规成功以同 prior 更新为 `.2625`，样本数递增到 2。无需修改原 Router 测试或科学 checker。

最终复验命令（均在本轮私有环境，`--basetemp` / mypy cache 指向上述 Temp，不使用旧产物）：

```text
python -B -m pytest -q tests/swarm/test_router.py tests/swarm/test_policy_score_v01.py tests/swarm/test_field.py tests/swarm/test_policy_feedback_v01.py tests/swarm/test_ledger.py tests/swarm/test_lease.py tests/swarm/test_budget.py tests/swarm/test_unknown_effect_recovery.py -p no:cacheprovider --basetemp <private Temp>/final-regression
python -B -m mypy --strict --cache-dir <private Temp>/mypy-swarm-cache swarm
python -B -m mypy --strict --platform linux --cache-dir <private Temp>/mypy-linux-cache swarm
git diff --check
git push origin HEAD:refs/heads/songconmaisaix31-design/morph-policy-score-v01-1002
git ls-remote origin refs/heads/songconmaisaix31-design/morph-policy-score-v01-1002
```

实现位置：[共享 Router](../../swarm/router.py)，行为验收：[本轨新测试](../../tests/swarm/test_policy_score_v01.py)。薄 API SOURCE `17c3bbfd9c0084b17482e6bba796de86555c4641` 是历史阶段，最终算法 SOURCE 为首页 b0f3；C 的原提交保留在 ancestry，不能把它归为 B 自行改动。

完整工程、独立安装、正式入口 trace 和五项整体条件：由独立 I 后续验收，当前本轨不宣称已满足。没有全量 pytest、安装后产品或新科学/模型/付费验收，没有账户或全局 HOME 配置变化，所有 live 仍未由本轨新增。本次只推候选分支，不发布 main。
