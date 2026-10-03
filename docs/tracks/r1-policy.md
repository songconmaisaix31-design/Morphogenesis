# R1 C 贡献与研究路线政策（research-v1）

## 2026-10-03 正证据影响后续选择（本次追加收口）

本轨改动及适用验证完成。本次 SOURCE：`e82cae36038c386aec999642289ac1d78c82a9ed`，
已 push 并核对远端 SHA。
分支：`songconmaisaix31-design/morph-r1-policy-1003`。本节是旧阶段之后的追加修复，
以下旧报告与首 RED 均保留；本报告另作 docs-only 后继提交。

按主控计划 `66e2a26f043453a851f4f31ec20700802b90b5d4` 和当前 Spec 的
FR-12/13、AT-10 工作；Spec 的规范 LF SHA256 为
`ab73f60e26af1bc1b44ca5da9b94b2cfdda91a5d4acb25683b9386462dcfb165`。
本 C Windows checkout 的 CRLF 与主控 LF 文本经换行归一化相等。
原 C HEAD `8bc4c282ed4db8e2be0798509b28d984240b3a06` 普通精确快进合入
核心 SOURCE `2c63bc7c9e49edff28e26f5930a22d0415fadd65` 后开发；
核心 REPORT `08b31b39c075571ffd247e2b591d657ce09b6b34` 未再合入，历史由 I 保留。
本次领域变更仅 `swarm/research/policy.py` 和
`tests/research/test_research_policy_opportunities.py`，未改 A/B/P/Q 文件。

### 缺陷、策略语义与实际行为

旧研究候选公式 `(1 + support) / (1 + support + refute)` 在零反证时恒为 1，
所以独立接受正证据只添加引用，无法增加对应机会份额。
本次 `research-v1` 修正为 `(1 + support) / (2 + support + refute)`：
无证据为 0.5，一条支持为 2/3，一条反证为 1/3。它是有界路线偏好，
不解释为科学结论为真的概率。`_value` 和展示因子复用同一 `_evidence`，避免解释与排序分离。
公开 `research-v1` 名称和 DTO 保留，主控 `msg_d1bc90680d07` 已明确同意此候选缺陷修复；
修正语义绑定本次 SOURCE，不回写旧报告或沿用旧 `v0/v0.1` 名称改变其行为。

保持原 80% 价值机会、20% 合法探索和总份额 1；applicability=0 明确不可用，
返回 `eligible=false / share=0 / inapplicable`，不获得探索份额。
负证据继续降低对应路线机会，但可靠反例的贡献仍为 accepted。
原反馈存储负责原始完成记录、独立复核及来源去重，本次未增加反馈表、调度器、预算或证明权威。

新增正式服务对照先完成原执行和独立新任务／运行／sandbox 复核，保持 mock 标记；
随后给三个同等合法分支分别提出工作。在接受前各份额 1/3，未接受结果和作者自评均不增益。
独立接受后，支持分支份额约为 **0.386667**，另两条各约
**0.306667**，总额仍为 1，合法探索下限保持 0.2/3。
`discover` 排序将支持分支移到首位；相同 `seed=4` 的原随机选择从 `alternative`
转到支持分支，实际 `claim` 在原 TaskLedger 写下相同机会及 `result_references=[accepted_result_id]`。
比较的是有证据和无证据的同一批工作，没有 mock 策略、返回值、接受结果或账本。
此单次确定性对照证明机制生效，不宣称统计最优、科研有效性或群体效率优势。

固定 host envelope、持久 BudgetPolicy 和 BudgetSnapshot 在接受／读取／choose／claim
前后相等，未知 tokens / actual_cost_usd 保持 None，未产生采用回执。
重复接受、同原始输出换 task 身份、非匹配条件、越权或无 review 权限、零适用性，
以及 failed/timeout/unknown 执行均不增加科研奖励；unknown 原请求仍拒绝再次执行。

### 调用证据与测试定位（行号按本次 SOURCE）

| 路径 | 调用与意义 |
|---|---|
| `swarm/research/feedback_generated.py:132` | `trusted_generated_feedback` 原 ledger + 资产 + B 原 archive 的可信投影，未另造结果 |
| `swarm/research/feedback.py:179,280,319,398` | `research_feedback → trusted → accept → advisory`，每次重验原事实与独立 Review，只取已接受的适用引用 |
| `swarm/research/policy.py:178,188,193` | `_evidence → _value → opportunities`，一处中性先验公式同时驱动份额和可解释因子 |
| `swarm/research/service.py:1053,1073,124` | 原 `accept_result → research_advisory → discover`，排序实际消费该份额 |
| `swarm/research/service.py:1195,192,1229` | 原 `choose → claim → _record_research_selection`；原 TaskLedger 审计包含选择、token 和已接受结果引用 |
| `tests/research/test_research_policy_opportunities.py:40` | 三合法分支前后份额、同 seed 实际选择、claim 与 SQL 审计、预算不变、重复接受 |
| 同文件 `:108,122` | 反证获得贡献且路线下降；同源复制不再增益 |
| 同文件 `:143,160,171,184` | 条件／scope／适用性／review 权限与 failed/timeout/unknown 负例 |

复用 A 的 `test_dynamic_service` 函数夹具和 B 原 mock 执行器、原 store/ledger，
宿主候选执行和网络由夹具禁止，唯一允许的子进程为固定本地 Git。
A 原测试中正证据 `share == .5` 的旧断言已通过 `msg_d7a0abb9f40a` Handoff 给 A；
A ACK 将收紧为 `> .5` 并保留原源码 RED。C 不越权修改 A 测试或服务。
SOURCE 已通过 `msg_d3fb752441f0` 交 A 允许普通精确 merge。

### 首 RED 与当前验证

本机完整日志目录：`C:/Users/DW/AppData/Local/Temp/morph-r1-c-positive-ctx4b4437/`。
全部新安装指向 C 独有私有解释器
`C:/Users/DW/AppData/Local/Temp/morph-r1-c-recovery-ctx059a/venv/Scripts/python.exe`；
已核实 `sys.prefix` 为该 venv，`swarm.__file__` 来自私有 site-packages。
用 `git archive` 导出基线、`build --wheel --no-isolation`、
`uv pip install --python <private> --offline --link-mode copy --reinstall --no-deps <wheel>`；
首次修复 wheel 使用此导出的代码副本加单一 policy.py 覆盖。
测试 cwd 只有独立测试副本，用 `-I` 加仅测试目录的 bootstrap，不导入活动工作树。
所有进程仅局部设置 `OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=MKL_NUM_THREADS=1`。

| 实际阶段 / 日志 | 结果 |
|---|---|
| 基线 `2c63bc7` 非 editable wheel build/install | PASS |
| `positive-2c63-first-red.txt`，新正式服务正例 | **1 failed，27.09s**；接受后 share 仍为 1/3 |
| `inapplicable-2c63-first-red.txt`，零适用性资格 | **1 failed，2.91s**；旧值 `eligible=True, share=0.1` |
| `opportunities-first-fix.txt`，修复 wheel 上新增全11项 | **11 passed，45.20s** |
| `strict-policy.txt`，`mypy --strict --follow-imports=silent swarm/research/policy.py` | **Success: no issues found in 1 source file** |
| `exact-build.txt` / `exact-install.txt`，最终 SOURCE `git archive` wheel、私有 COPY 安装 | **PASS** |
| `exact-origins.json`，7个实际导入模块与 exact archive 逐字节比较 | **PASS**；非 editable，无全局 site-packages / 活动工作树导入 |
| `exact-dependencies.txt`，私有 `uv pip check` | **104 packages compatible** |
| `exact-c70.txt`，原59 + 新11项 | **70 passed，50.71s** |
| `exact-q45.txt`，Q 原 C 反馈／绑定／generated 安全控制 | **45 passed，11.74s**；原文件和断言不变 |
| `exact-legacy.txt`，旧 `Router` / `policy_score_v01` / `policy_feedback_v01` | **26 passed，42.94s** |

最终 exact-source installed 共 **70 + 45 + 26 = 141 passed**，无 deselect 或断言降级。
全部重进程退出后已通过 `msg_49fae887e9c6` 立即释放串行窗口，报告不触发重跑。
首次修复的11项与最终70项中的新11项是同一套测试，不重复计入141项。

精确 SOURCE wheel 大小 954495，SHA256 为
`3739af7e0447cf932390fcdf32fd3d8b0825469efdd1301cef9b9a56a2b309e5`。
`exact-origins.json` 核对 policy、feedback、feedback_generated、service、dynamic、
TaskLedger 和 BudgetLedger；`direct_url.json` 指向此 wheel，包含 `archive_info`，
不存在 editable `dir_info`，私有 venv 为 `include-system-site-packages=false`。

本次最终 installed 命令（同一中立 tests-only cwd；`$cPython` 为上述私有路径）：

```powershell
& $cPython -I -c 'import sys,pytest; from pathlib import Path; sys.path.insert(0,str(Path.cwd())); raise SystemExit(pytest.main(sys.argv[1:]))' tests/research/test_research_policy_opportunities.py tests/research/test_research_policy_generated.py tests/research/test_research_policy_v1.py -q
$env:R1_SECURITY_SOURCE='<private>/Lib/site-packages'
& $cPython -I -c 'import sys,pytest; from pathlib import Path; sys.path.insert(0,str(Path.cwd())); raise SystemExit(pytest.main(sys.argv[1:]))' tests/integration/r1_security/test_c_feedback_boundaries.py tests/integration/r1_security/test_c_advisory_binding.py tests/integration/r1_security/test_c_generated_trust.py -q
& $cPython -I -c 'import sys,pytest; from pathlib import Path; sys.path.insert(0,str(Path.cwd())); raise SystemExit(pytest.main(sys.argv[1:]))' tests/swarm/test_router.py tests/swarm/test_policy_score_v01.py tests/swarm/test_policy_feedback_v01.py -q
```

首 RED 的可定位原 stdout（后续通过不覆盖）：

```text
_ test_accepted_support_changes_discover_choose_claim_and_preserves_envelope __
>       assert supported["share"] > before[plan.branch_id]["share"]
E       assert 0.3333333333333333 > 0.3333333333333333
tests\research\test_research_policy_opportunities.py:64: AssertionError
1 failed in 27.09s

________ test_inapplicable_route_has_no_exploration_or_evidence_reward ________
>           assert not excluded.eligible and excluded.share == 0
E           AssertionError: assert (not True)
E            +  where True = RouteOpportunity(branch_id='inapplicable', eligible=True, share=0.1, ...).eligible
tests\research\test_research_policy_opportunities.py:166: AssertionError
1 failed in 2.91s
```

完整原日志 SHA256 分别为
`ff6ec9f6f563003ae129f01c12513fd810ec592b04409e6f4b5033a980253e96` 和
`dc36933d9987c45cb397e85e5297c95b7d4d16ab6faed4b498b5cdbdb01ad5b1`。

### 仍有的边界

本轨仅离线／installed mock 的机制证据。基线 A 测试的旧 `share == .5` 正例
须随 A 后继合入其收紧的断言；本次未将该旧断言计为通过，也不改写其历史结果。
完整产品离线回归、正式 installed 输入观察
留给最终 I 组合；本次不代表整体 R1 完成。AT-07 真实隔离探针和 L2 均 **NOT_RUN**，
须后续单独授权。未执行真实模型科研、真实沙箱、云、外部材料获取、Hub 或部署。
旧 FC stdout 首 RED 根因仍 UNKNOWN，未放松原断言或时限，本窄修复不重复 FC 运行。
旧全局 Python 安装残留保持现状；之前清理被自动审批 `blocked by policy` 拒绝，
本轮未重试、卸载或换工具绕过，未知原依赖状态不称已恢复。

## 2026-10-03 恢复后状态（本节覆盖后文旧阶段结论）

**C 领域功能与适用验证已完成，最终 SOURCE 为
`56de8e3f5d2abd1e1ba02218b422f0aba9847ae2`；本报告单独作为 docs-only 后继提交。**
边界为 contract_local / 私有非 editable 安装的 mock；历史首 RED 保留，
全局 editable 清理被自动审批拒绝且未执行，原全局状态 UNKNOWN；不宣称整体 R1 或 L2 完成。

`99cd2997dd024a41c28461228f47a575fef3f9ab` 仅是三轴转换阶段候选；当时
`from_generated_assessment` 未被可信存储消费，不能证明动态研究反馈闭环。
旧 `3161048` / Q22 PASS 只覆盖旧路径，历史结果保留。新的阶段 SOURCE
`d7e561f9b4d6155316f12471de050c09b12471b4` 已 push、远端 SHA 一致，包含普通精确
merge B `d175f7e2f8c3ff41a1ac8a2a4958c68acf57e275` 和
`e8e16a5b9e755a94f8587b76ba9fc288f218b8af`；随后普通合入 B
`d0c834fd381fc292443bf85c5ce1e91043143516` 及
`56b8db589ee04bcc41652bb5e38793a1216f9a1a`。C 后继 SOURCE 为
`38eae47e2961e10e9cf492fe99ea02f418d57dc9`（缺少冻结批准不阻塞其他事实）和
`3cc650b06049d1a714a56a0169de106129ecac10`（host locality），均已 push，远端 SHA 确认。
`535c05ebc8be5e869c828399e6c66e9331364479` 补充原作者同样必须属于 host locality、
原作者与执行任务 workspace 一致；普通后继提交，未改写前三次 SOURCE。
阶段组合 SOURCE `4f83296af908352660ebf71e633e70a111eb2877` 普通精确合入 B 归档重验修复
`2d50d08811aa2337b9c0166dc114513e292bce1f`；push 与远端 SHA 一致。
B 新 `LocalAssetStore(generated_criteria=host_registry)` 用于继承/采用重验；C 生产投影
只读原数据库，显式将同一个 host registry 传给 B 原 reader，未新增存储权威。
最终安装与回归结果见下文；阶段提交和原失败不被最终通过覆盖。

### 精确私有安装准备

普通合入 B 最后兼容修复 `5faafe41b1732c83d165251600b688444186c702` 后，
最终 SOURCE 为 `56de8e3f5d2abd1e1ba02218b422f0aba9847ae2`。
主控 `msg_762cbf9284e0` 授权有界安装准备，完整回归仍等 B 释放窗口。
从 `git archive` 导出的此 exact SHA 构建非 editable wheel，未从活动工作树安装：

```powershell
& '<private>/Scripts/python.exe' -I -m build --wheel --no-isolation --outdir wheels-56de8e3 source-56de8e3
uv pip install --python '<private>/Scripts/python.exe' --link-mode copy --cache-dir uv-cache --no-deps wheels-56de8e3/morphogenesis-0.1.0-py3-none-any.whl
uv pip check --python '<private>/Scripts/python.exe'
```

wheel 大小929336，SHA256
`c96149dba4ee94b9f9d39a872a9dad3b356a4c66b5d7c09f58c025da580a5bdd`；
`wheel-build-56de8e3.txt` / `wheel-install-56de8e3.txt` 均 exit0。
`uv pip check` 为 **104 packages compatible**。隔离 `-I` 导入检查保存在
`installed-import-56de8e3.json`：三个反馈模块均来自本私有
`venv/Lib/site-packages`，`sys.path` 没有活动工作树或全局 site-packages，
`direct_url.json` 为 wheel 的 `archive_info`，无 editable 注册。
锁定 SDK 的工作树依赖文件复制到此私有 site-packages；未改全局 Node 环境。
准备完成时完整 installed pytest / FC / SDK 尚未执行；之后在主控
`msg_d32e1261de70` 授权的串行窗口中得到以下实际结果。

### 最终精确安装验证（SOURCE 56de8e3）

| 日志 / 命令范围 | 结果 |
|---|---|
| `c-installed-final.txt`：`test_research_policy_generated.py` + `test_research_policy_v1.py` | **59 passed，21.35s** |
| `q-installed-final.txt`：Q 原 `test_c_feedback_boundaries.py` / `test_c_advisory_binding.py` / `test_c_generated_trust.py` | **45 passed，10.33s**；含原22控制与实际 generated 正负例 |
| `fc-stdout-installed.txt`：原 `test_process_writers_share_real_sqlite_append_lock` | **1 passed，7.77s**；READY / 120s / 30s 断言均未改 |
| `legacy-installed-final.txt`：FC logging/projection、policy feedback/score、router、field、ledger、lease、budget、旧 policy_entry | **151 passed / 1 deselected / 2 warnings，112.37s** |
| `installed-sdk.txt`：原 `tools/check_sdk.cjs`，官方 SDK1.14.0 | schema / asset ID / tamper rejection PASS，`published=false`、`contract_local` |
| `strict-final.txt`：本轨4个改动模块 | `Success: no issues found in 4 source files` |
| 私有 `uv pip check` | 104 installed packages compatible |
| `git diff --check` | PASS |

legacy 唯一 deselected 是已独立运行通过的 FC stdout 同一测试，避免重复测试；不是取消
失败断言。两项 Pydantic warning 来自旧 budget 的 nan / 字符串输入负例，原样保留。
本次总计四组 **59 + 45 + 1 + 151 = 256 passed**，不代表全仓或最终产品集成验收。

各命令均以私有解释器 `-I` 从不含核心源码的中立 cwd 运行，测试代码为原文件副本。
C/Q 测试的 bootstrap 只把各自测试目录加入 `sys.path`，Q 的 `R1_SECURITY_SOURCE`
显式指向私有 `venv/Lib/site-packages`。旧 FC 的保护目录断言依赖测试相对包的位置，
所以旧套件原测试复制到私有 site-packages/tests 后用 `-I -m pytest --import-mode=importlib`
运行，仍保持测试和断言不变。没有活动 worktree / editable 源码回退。

最终 Q 测试副本的 Git blob（按上述文件顺序）：
`aa793d6c6edab69a007fd2eb11fbd42cc3e7bcf7`、
`fc76df766bde02a12ec3bfdb64502e83d64711b0`、
`5fb378cbfeadde874dcec8b959a83ad59fabf7df`。

实际入口命令形状如下；测试目录分别为证据目录中的 `installed-56de8e3`、
`q-installed`，legacy 目标为私有 site-packages/tests 下的原测试文件：

```powershell
& $python -I -c 'import sys,pytest; from pathlib import Path; sys.path.insert(0,str(Path.cwd())); raise SystemExit(pytest.main(sys.argv[1:]))' tests/research/test_research_policy_generated.py tests/research/test_research_policy_v1.py -q
& $python -I -c 'import sys,pytest; from pathlib import Path; sys.path.insert(0,str(Path.cwd())); raise SystemExit(pytest.main(sys.argv[1:]))' tests/integration/r1_security/test_c_feedback_boundaries.py tests/integration/r1_security/test_c_advisory_binding.py tests/integration/r1_security/test_c_generated_trust.py -q
& $python -I -c 'import sys,pytest; from pathlib import Path; sys.path.insert(0,str(Path.cwd())); raise SystemExit(pytest.main(sys.argv[1:]))' tests/swarm/test_fc_logging.py::test_process_writers_share_real_sqlite_append_lock -q
# legacy 从 site-packages/tests 选上述10个文件，--import-mode=importlib -q
# -k 'not test_process_writers_share_real_sqlite_append_lock'；其单项结果已经单独保存。
```

全部 pytest/Node/build/install 进程结束后已用 `msg_0d25dc91be85` 释放重型窗口给 A。

### 实际持久化消费与独立 Review

- `research_feedback` / `ResearchFeedbackStore.trusted` 读取原 `TaskLedger`、原
  `assets` / `research_reports` 和 B 原始归档；没有新结果表、执行器或证明权威。
  新 `feedback_generated.py` 仅负责只读绑定；B 的 `read_generated_observation`
  重读代码、原始输出、判据、条件、环境和冻结批准，并重新计算科学结论。
- 接受之前核对原 completion audit、已完成 attempt、owner、当前 execution token、
  begin/confirm/research_execution 顺序与确切结果、候选原作者、任务冻结的
  `generated_plan`、project/branch、asset、run、sandbox、已确认效果和清理状态。
  `source_attempt` 是当前执行任务，`Candidate.attempt` 是候选原作者，语义不混用。
- host 注入 `generated_criteria`；批准人独立于候选作者，批准时间先于执行；
  `trusted` / `mode` / `proof_ref` 或传入 `result_id` 本身不授予科学权限。
  crashed、timeout、unknown、replay、无批准、错来源均不获接受。
- 独立复核必须是另一个已完成任务与 actor、另一个 run / sandbox、同一资产、
  条件、项目、provenance 和科学结论；`review_report_id` 与接受事实一同追加保存。
  有效 supported 与 refuted 分别能被接受；inconclusive 保持 proposed。
- `advisory(branches)` 每次重验原始事实和 Review，自动从已接受且未 supersede 的
  事实导出同 branch / conditions 的 `supported_by` / `refuted_by`；调用方空引用
  也会得到真实引用，伪造、复制、换轴、换分支或删除反证引用均不能改变证据。
  有效反证贡献被认可，同时降低对应路线的下一次机会份额。
- A 接线要求的 `locality=host_config.locality()` 复用原 `ledger._local_filter`，
  过滤原结果和复核任务；同项目但外部 scope/workspace/module 的事实不能授权接受或
  影响建议。`advisory["branches"]` 返回相同的已校验引用，供正式 snapshot/discover 使用。
- source 去重复用 B 原输出 artifact 的既有 SHA256 值；未实现新的哈希或证明系统。
  相同原始输出换 task/agent 身份不重复奖励，原论文来源仍在 B 原报告。
  `trusted_facts` 跳过 `generated_plan` 任务，防止动态结果误获旧 v0.1 奖励。

接线使用现有构造器：

```python
store = ResearchFeedbackStore(
    path, ledger, assets_root, reviewer=host_worker_id,
    generated_criteria=host_criteria_registry,
    project_id=project_id, archive_root=archive_root, locality=host_config.locality(),
)
store.trusted()               # actual original records, including inconclusive
store.accept(result_id)      # independent persisted Review required
store.advisory(branches)      # accepted facts resolve the next opportunity refs
```

A 负责正式 `ResearchService.discover` / MCP 组合接线，P 负责产品只读投影；
C 的 store 级通过不代签正式服务、模拟采用或整体 R1 验收。所有新夹具保留 `mock`，
测试禁止候选宿主子进程与网络。夹具仅使用 B 的固定 mock 输出和 FakeBridge；
TaskLedger、发布 API、归档、报告 API、贡献存储和 advisory 实际运行。

A 后续交付 `0bcb320e843839f5f043fccd9f705d9dd9b7299e`（消息
`msg_a554e80b3868`），本 C `4f83296` 是其祖先，已实际读取该 exact 提交测试：
`test_dynamic_service_accepts_only_independent_original_chain_and_changes_opportunities`
参数化 supported/refuted，完成独立 Review 后接受，后续 `discover` 返回同一机会，
`choose/claim` 审计引用原接受结果且费用保持 None。A 报告动态7项 PASS；这属于
**A Owner 报告、C 只读核对代码/祖先关系**，不冒充 C 独立重跑或 installed/live 证据。
A 同时保留旧 SDK 环境24项 RED；其整体 R1/安装/stdio/回归验收当时仍未完成。

### 已保存的检查与失败

本次恢复证据目录（不入库）：
`C:/Users/DW/AppData/Local/Temp/morph-r1-c-recovery-ctx059a/`。

| 检查 | 原始结果 | 后续说明 |
|---|---|---|
| C `generated-first.txt` | 25 failed / 27 passed，27.29s | 新夹具误用不存在的 `TaskLedger.assert_owned`；改用已有 `fenced` context |
| C `generated-second.txt` | 25 failed，14.76s | 原 GEP 桥启动 Node 被测试的子进程禁令拦截；改用 B 惰性 FakeBridge + 原 publish |
| C `generated-third.txt` | 新动态路径 25 passed，9.27s | 原账本、B 归档与报告、独立接受、接受前后同样分支输入实际改变引用 |
| C `generated-fourth.txt` | 27 passed，11.89s | 增加一致伪造 trusted/final/accepted 对原始输出重算拒绝、相同输出换身份去重 |
| C `generated-fifth.txt` | 28 passed，10.37s | 无运行前批准不能事后批准，且不隐藏其他有效结果 |
| C `generated-locality.txt` | 31 passed，11.10s | 外部 scope/workspace/reviewer module 不影响本 host 反馈 |
| C `generated-locality-control.txt` | 3 passed / 28 deselected，2.60s | 补充同授权 scope 的有效接受引用控制 |
| C `generated-locality-origin.txt` | 4 passed / 28 deselected，3.53s | 原始任务 module 也必须属于 host 权限，范围内 Review 不能洗白范围外原始事实 |
| C `c-source-final.txt` on `4f83296` | 59 passed，15.38s | 新动态32 + 旧 research-policy27，实际 B2d 原 writer/reader API |
| C `owner-q81.txt` | collection ERROR，1.63s | C/Q 两个 tests 包同进程冲突，未产生81项测试证据；分开从各测试根运行 |
| Q `q29-source.txt` | 原22 + 新7 = 29 passed，6.34s | 使用 Q 原文件与当前 C SOURCE，无改断言 |
| Q 对旧 `99cd299` 机会绑定 | 6 failed / 1 passed，3.99s | Q `c-99cd299-advisory-first.txt` 原 RED 保留 |
| Q 对 exact `d7e561f` | 首轮40 passed / 1 failed，10.91s | Q 新 fixture 改写报告被原 SQLite immutable trigger 拒绝；Q 修 fixture 前原结果保留，非 C 领域绕过 |
| 私有 `uv pip check` | 103 packages compatible | COPY 安装；不含项目 wheel，后续安装证据另记 |
| 私有 `strict-first.txt` / `strict-origin.txt` | 4 source files no issues | `mypy --strict --follow-imports=silent`，限定 C 改动模块，不代表全仓 strict |

源码验证实际命令（均仅设置进程级 BLAS1）：

```powershell
$python = 'C:/Users/DW/AppData/Local/Temp/morph-r1-c-recovery-ctx059a/venv/Scripts/python.exe'
& $python -m pytest tests/research/test_research_policy_generated.py tests/research/test_research_policy_v1.py -q
& $python -m mypy --strict --follow-imports=silent swarm/research/policy.py swarm/research/feedback.py swarm/research/feedback_generated.py swarm/feedback.py
# Q29 从 Q 工作树运行，R1_SECURITY_SOURCE 为本 C 工作树；不与 C tests 包同进程收集。
& $python -m pytest tests/integration/r1_security/test_c_feedback_boundaries.py tests/integration/r1_security/test_c_advisory_binding.py -q
```

FC stdout 历史首 RED **仍是历史 RED，根因未确认**，不得称作“无关”或凭后续绿认定修复。
最早保存的含 FC 综合命令尾部是 `prt_0fd8bd02a001j76uUI6HoX1XSb-test.json`：
`6 failed / 130 passed / 2 warnings，48.24s`；原命令同时运行 router、policy_score、field、
ledger、lease、budget、fc_logging 与 research_policy，原日志只保留最后8行。
旧 C session 的保留输出包括 `prt_0fd90e70f0012uVJ5G4SnppJB6-test.json`
（1 failed / 33 passed，58.93s），断言为
`future.result(timeout=120).strip() == "READY"`，实际 stdout 为空。
`prt_0fd98a043001XN3x7C02jl77c9-test.json` 为 1 failed / 41 passed，98.90s；
editable 安装后 `prt_0fd9c043b001hMdq6eSufIUuAh-test.json` 仍为
1 failed / 41 passed，84.37s。原输出没有足够 child stderr 定位证据。
原测试、READY 断言、120s / 30s 超时保持原样；最终私有安装单项为1 PASS / 7.77s。
这仅证明当前隔离环境通过，未定位旧环境空 stdout 的根因，也不把历史失败改为通过。

### C 全局 Python 安装事件：事实、残留与人工清理边界

从原 C OpenCode 只读 SQLite session `ses_f0296e348ffent0AfF9jfk7Sdm`
恢复到以下命令和已保留的输出尾部。数据库以 `mode=ro` / `query_only` 读取。
这不是安装前后完整包清单；**安装前全局状态 UNKNOWN，不能宣称已恢复**。

| 原 part | 原命令 | 原输出 |
|---|---|---|
| `prt_0fd9b33f6001WGiRh6Izy8eHOw` | `python -m pip install -e . --no-deps --no-build-isolation 2>&1 \| Select-Object -Last 20` | `Cannot import 'poetry.core.masonry.api'` |
| `prt_0fd9b5da4001dkSpTBsMHO2EQr` | `python -m pip install "poetry-core>=2.0,<3.0" "opensandbox==1.1.0" "opensandbox-code-interpreter==1.1.0" 2>&1 \| Select-Object -Last 15` | 原默认镜像 HTTP 403 |
| `prt_0fd9b7f3e0012NsW454rxZSeQx` | `python -m pip install -i https://pypi.org/simple "poetry-core>=2.0,<3.0" "opensandbox==1.1.0" "opensandbox-code-interpreter==1.1.0" 2>&1 \| Select-Object -Last 15` | `Successfully installed opensandbox-1.1.0 opensandbox-code-interpreter-1.1.0 poetry-core-2.5.0` |
| `prt_0fd9bd0d9001L1dhmlrQW2OMIh` | `python -m pip install -e . --no-deps --no-build-isolation 2>&1 \| Select-Object -Last 10` | `Successfully installed morphogenesis-0.1.0` |

已确认的安装目标是 `C:/Python313`，不是 C 私有环境；成功 editable wheel 大小8912，
SHA256 `dae2592c3b95645f5a4b1c4eb01c30150faa16fc154bc5312021c6f7823bda5d`。
后一次安装约在本地 2026-10-03 01:14:06（UTC 2026-10-02 17:14:06）写入。
`direct_url.json` 原值：

```json
{"dir_info":{"editable":true},"url":"file:///C:/Users/DW/orca/workspaces/Morphogenesis/morph-r1-policy-1003"}
```

`global-registration-readonly.json` 保存11个 RECORD 文件的大小、mtime_ns、SHA256，
全部与当前 RECORD 匹配。精确残留清单：

- `C:/Python313/Scripts/morphogenesis.exe`（108319 bytes）与
  `morphogenesis-swarm.exe`（108315 bytes）。
- `C:/Python313/Lib/site-packages/morphogenesis.pth`（64 bytes），SHA256
  `7d83c607c265723b7a732a6af0a759ed8816b25d15f1e1e51869e607d7ee4615`。
- `C:/Python313/Lib/site-packages/morphogenesis-0.1.0.dist-info/` 下8个文件：
  `INSTALLER`、`METADATA`、`RECORD`、`REQUESTED`、`WHEEL`、`direct_url.json`、
  `entry_points.txt`、`licenses/LICENSE`。RECORD SHA256
  `7a3218626c7c09c07b3eb7eee5e92d3a7a04cd78cd630c31981d28f375efc5fe`。
- 成功安装输出明确列出的 `opensandbox==1.1.0`、
  `opensandbox-code-interpreter==1.1.0`、`poetry-core==2.5.0` 仍留在全局；
  不知道旧环境依赖关系，不卸载这些包，也不声称恢复它们之前的状态。

本轮曾提出只移动本轨 RECORD 精确匹配文件到隔离目录的操作；**自动审批在进程启动前
拒绝，返回 `blocked by policy`**，没有执行清理。已向主控 escalation
`msg_86307680587a`；主控 `msg_1a53956876b8` / `msg_bdefb513f5a2` 明确要求
不绕过、不重试，把残留和人工步骤报告，继续私有环境工作。

最终于 UTC `2026-10-02T18:57:49.886512+00:00` 再次只读复核：11项注册文件的
大小、SHA256 和 mtime_ns 全部与恢复时快照一致，保存在
`global-registration-final-readonly.json`。因此清理仍为 **BLOCKED / 未执行**；
私有环境的通过不能解释为全局恢复，未知旧依赖未被卸载。

人工后续操作（未执行）：先确认没有使用该全局注册的进程，再重新核对上述 direct_url、
RECORD 及11个文件摘要均未变化；只将这些确证文件移到有备份的隔离目录，
仅清理变空的该 dist-info 目录。若任一归属或内容变化即停止，不能批量卸载依赖、
递归删除整个 site-packages 或认定全局回到未知旧状态。

新的私有目录为上述证据目录的 `venv/`，`include-system-site-packages=false`。
使用 `uv pip --python <private>/Scripts/python.exe --link-mode copy --cache-dir <private-cache>`，
本恢复轮未修改锁文件、全局 pip、auth/provider/HOME 或全局环境变量。
仅子进程设置 `OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=MKL_NUM_THREADS=1`。
依赖根据既有 `poetry.lock` 构造，另私有安装构建后端 poetry-core2.5.0；完整日志为
`private-install.txt` / `locked-requirements.txt`，不以全局 editable 提供测试导入。

### 真实剩余限制与未执行操作

本轨 exact-source 私有非 editable 安装、4模块 strict、FC 原断言与上述适用旧路径
已通过。A 已报告正式 discover/choose/claim mock 组合正例；P/UI、正式安装传输与独立 I
整体验收仍由相应 Owner 完成，不由 C 的存储测试替代。全局11项 editable 残留仍待人工
按上述精确核对步骤处理；旧全局状态与历史 FC 空 stdout 根因均 UNKNOWN。
真实模型科研、外部材料、真实沙箱与探针、云、Hub、部署和 L2 仍全部 **NOT_RUN**；
mock 不提升为 interface_live / task_live，未知费用/用量不填零。

## 历史阶段报告（原文保留，不能作为当前完整验收）

**状态：三轴贡献与研究路线政策（research-v1）领域返修完成，新接口 strict + pytest 通过。** 这是独立于既有策略 v0/v0.1 的**新增**层；`swarm/router.py`、`swarm/feedback.py`、`swarm/pheromone.py`、`swarm/worker_loop.py`、`swarm/research/service.py`、`server.py`、`models.py` 的既有语义未被修改。L2 真实科研行动未获运行级授权，全部 **NOT_RUN**。

本轮返修（相对首版 71bfedb）修复验收阻断：贡献持久化接受入口改为从可信持久事实解析并绑定 host 自身审核身份，不再接受调用者 `ThreeAxisResult`/`reviewer` 字符串即奖励；`replace=True` 删除历史已移除，改为追加 supersession；`trusted_refutations` 只把 `purpose=counterexample` 的可信反例当反证；机会建议补齐 spec 七要素。

## 范围与不修改

本轨只写 `swarm/research/policy.py`（新增）、`swarm/research/feedback.py`（新增）、`tests/research/test_research_policy_v1.py`（新增）与本报告。不触碰 A 的 `swarm/research/service.py`/`server.py`/`models.py`/`HostConfig`，不触碰 B 的 `orchestration/experiments/**`/`local_assets/**`/`swarm/research/case.py`，不触碰 P 产品。跨轨接口只通过主控 Handoff。

- **v0/v0.1 原样保留**：`Router` 的 `strategy_version` 仍是 `Literal["v0","v0.1"]`（有测试断言 Router 拒绝 `research-v1`）。`trusted_facts`、`policy_diagnostics`、FC 投影、Worker 续租边界均未改动。
- **closed FC `RouteCandidate` 不放宽**：research-v1 的机会/理由只存在于 `RouteOpportunityPlan`，不新增 FC 路由候选字段，不改 `fc_log_schema.json` 的 `additionalProperties=false`。
- **复用而非新建**：复用 `TaskLedger`/`trusted_facts`/`ResearchObservation`/`Candidate`/`LocalAssetStore` 与标准 `result_id`/`report_id`/`task_id`/`actor(worker_id)`；不新增任务、执行、审计、Hash 或完成证明系统。贡献去重键是 `result_id` + `source_ref`，**不按 Agent 品牌**判断独立。
- **不建平行事实模型**：B 的动态三轴/候选模型在 `orchestration/experiments/generated.py`；本轨只做**政策层结果投影**（spec 5.2 的三轴结果模型），不重复 B 的候选/判据事实。B 安全 Handoff 后由本 Owner 提供薄转换或复用，不各自 pending 归 I。

## FR → 当前代码 → 新契约 → AT 映射

| FR | 旧代码现状 | 新契约（research-v1） | AT |
|---|---|---|---|
| FR-12 贡献与路线分离 | `trusted_facts` 只给正例三类奖励，无三轴 | `ThreeAxisResult(execution, hypothesis, contribution)` 三独立轴；`succeeded/refuted` 可 `accepted`，`crash/timeout/auth/unknown` 无科学条目；有效反证降低该路线未来机会但认可反证贡献 | AT-08, AT-10 |
| FR-13 投入调整 | 无版本化路线政策 | `RouteOpportunityPlan(version="research-v1", exploration_fraction, total_share=1.0)`；`apply_correction`（sleep/downgrade/reopen）追加不擦除；refuted 重开须 `new_condition_branch`；证据改变下一次可解释推荐，claim 仍由原 TaskLedger 权威 | AT-10, AT-11, AT-14 |
| FR-14 探索与多样性 | v0.1 任务级 softmax 保底 | `exploration_fraction`（默认 0.20）作为合法分支探索配额下限；dormant/refuted/archived/越权 `eligible=False` 无执行权；同 `result_id`/同 `source_ref` 去重，不因品牌重奖 | AT-09, AT-11, AT-14, AT-15 |
| FR-24 拓扑可解释 | 无分支机会视图 | `RouteOpportunity.factors`（evidence/insufficient_evidence/applicability/goal_relevance/risk/known_cost）与 `reasons` 逐项可解释；`snapshot()` 输出三轴 + 机会 + 理由 | AT-10, AT-11 |

## 可信贡献接受与审核身份

`ResearchFeedbackStore.accept(result_id)` 是**唯一**持久化接受入口，且**不再接受调用者 `ThreeAxisResult` 或 `reviewer` 字符串**：

- 结果从 `research_feedback(ledger, assets_root)`（可信事实投影）按 `result_id` 解析，不存在的 `result_id` → `untrusted_result`（伪造）。
- `provenance == "replay"` → `replay_not_acceptable`（回放不能建立新接受）。
- reviewer 是**构造时绑定的 host 自身 Agent 身份**（来自 `HostConfig.worker_id`，由 A 的 identity-bound service 提供），不是调用者字符串。`_reviewed` 要求该 host 身份在**可信投影**里有对本候选的独立派生结果（不同 task 的同 asset 的 `supported`/`refuted` 事实，即真实已确认 TaskLedger 运行的 reproduction/counterexample），仅 JSON 宣称 `purpose=reproduction`/`worker_id` 而无 ledger 执行的伪造 observation 不会出现在可信投影，故被拒（`reviewer_not_admitted`）。结果 id 不能提升 authority。
- 跨作者（`reviewer == actor` 由纯策略 `self_approval_rejected` 拒绝）、跨 scope/project（事实绑定本 swarm 账本，跨项目结果根本不在本 store 可信事实内 → `untrusted_result`）。
- 去重按 `result_id` + `source_ref`；纯 `ResearchPolicy.accept` 仅作计算建议，不是持久化权限入口。

历史只追加：贡献按 `result_id` 追加去重；更正按 `event_id` 追加；supersession 按 `event_id` 追加并把有效视图标记 `superseded`，**原贡献记录不删除**。fresh rebuild 建新 destination store，不改原 store。`research_feedback` 纯读投影确定性幂等、读失败不吞。

## 最小可调用接口（供 A/P 接线）

```python
# 纯策略引擎（无 DB、无 Node 桥、无执行器）
from swarm.research.policy import ResearchPolicy, Branch, CorrectionEvent, SupersessionEvent
policy = ResearchPolicy(exploration_fraction=0.20)   # version == "research-v1"
policy.accept(result, reviewer=..., seen=set())       # 纯计算建议，非持久化入口
policy.opportunities([branch, ...])                   # -> RouteOpportunityPlan
policy.apply_correction(branch, event)                # -> Branch (sleep/downgrade/reopen)
policy.new_condition_branch(refuted, new_id, conds)   # -> Branch (不擦旧反证)
policy.snapshot(results, branches)                    # -> dict 三轴视图

# 从可信事实投影三轴（research-v1 反馈）＋ 可信接受入口
from swarm.research.feedback import research_feedback, ResearchFeedbackStore, from_generated_assessment
results = research_feedback(ledger, assets_root)      # -> list[ThreeAxisResult]（正例+可信反证）
store = ResearchFeedbackStore(path, ledger, assets_root, reviewer=host_worker_id)
store.accept(result_id)                               # 唯一持久化接受入口（绑定 host 身份+真实独立审核）
store.record_correction(event)                        # 追加更正事件
store.record_supersession(event)                      # 追加 supersession（不删原记录）
store.contributions() / store.effective_contributions() / store.corrections() / store.snapshot()
store.advisory(branches)                              # A/P 接线：已接受贡献 + 引用贡献的 branch 机会建议

# B 三轴薄转换（不建平行真值/判据）
from swarm.research.feedback import from_generated_assessment
result = from_generated_assessment(assessment, result_id=..., report_id=..., task_id=...,
                                   actor=..., source_ref=..., provenance=..., asset_id=..., at=...)
```

**三轴轴类型复用 B**：`ThreeAxisResult` 的 `execution/hypothesis/contribution` 直接复用 `orchestration.experiments.generated` 的 `ExecutionAxis/HypothesisAxis/ContributionAxis`（spec 5.2 单一三轴结果模型），不建平行判据。`from_generated_assessment` 把 B 的 `GeneratedAssessment` 薄转成 C 的 `ThreeAxisResult`：**忽略 `trusted`/`mode` boolean，`contribution` 恒为 `proposed`**——C 的贡献接受仍来自原 TaskLedger 执行 + 独立审查，不从 backend JSON `trusted` 或 `final` 标签授权，不从 legacy `failed` 推断反证。

**`advisory(branches)`** 是给 A/P 的正式 advisory projection：返回已接受贡献 + `RouteOpportunityPlan`，每个 `RouteOpportunity` 带 `supported_by`/`refuted_by`（真实贡献 `result_id`），所以下一推荐**真引用贡献而非单纯快照**；`advisory_only=True`、`claim_requires_recheck=True`，宿主权限/地方/scope/dependencies/预算过滤与真实 claim 仍走原 `TaskLedger`。默认不改旧 v0/v0.1（`Router` 仍是 v0/v0.1，research-v1 是独立建议层）。

**审核身份权威来源**：host 自身 `HostConfig.worker_id`（A 的 identity-bound service 已绑定）；`_reviewed` 要求该 host 身份在资产库对本候选有真实 `reproduction/counterexample` observation。C 需要 A：接线时把 host 绑定身份传给 `reviewer=`，并把 branch/task/source 关联（`ThreeAxisResult.asset_id/task_id/actor` → branch）暴露给机会/快照；需要 B：可信评价方式（当前 `trusted_facts` 正例 + `ResearchObservation(purpose="counterexample", execution_state="succeeded", scientific_verdict="failed", known_effect)` 作可信反证）。接口未定前，本实现不依赖 A/B 新代码，负例（forge/replay/自批/同源/未审核 actor）先独立成立，后由同一 Owner 持续接线返修。

## 测试与首 RED

`tests/research/test_research_policy_v1.py` 共 23 项全通过（纯策略 + 投影 + 存储，不调用 Node GEP 桥/执行器）。首 RED 保留：先写测试，首次收集 `ModuleNotFoundError: No module named 'swarm.research.policy'`。Q 对 71bfedb 的伪造/未审核 actor RED（`test_c_feedback_boundaries.py` 3 failed/8 passed）已由本轮修复覆盖。

关键断言：有效反证独立接受；crash/unknown 无科学条目；同 actor 自批拒绝；同 result/source 去重；伪造 result_id→`untrusted_result`；replay→`replay_not_acceptable`；未审核/仅 claim 的 known actor→`reviewer_not_admitted`；跨项目→`untrusted_result`；legacy `purpose=original` 的 failed 不是反证；机会总额固定、dormant/refuted/archived/越权不探索、`exploration_fraction` 有界、可信反证降机会、spec 因素与 `unknown_cost` 理由；sleep/downgrade/reopen + refuted 新条件分支；supersession 追加不删原记录；fresh rebuild 不改源；损坏资产库抛 `sqlite3.Error`；Router 拒绝 `research-v1`。

## 验证命令与结果

```text
python -B -m pytest -q tests/research/test_research_policy_v1.py -p no:cacheprovider
# 23 passed

python -m mypy --strict swarm/research/policy.py swarm/research/feedback.py
# Success: no issues found in 2 source files
```

本机环境限制：`tests/swarm/test_policy_feedback_v01.py`、`tests/research/test_policy_entry_v01.py`、`tests/swarm/test_fc_projection_v01.py::test_all_six_existing_fact_kinds...` 依赖 Node GEP SDK（`node_modules` 未装，`bridge_node` 返回 `sdk_process_failed`），属环境前置（`npm ci` 由 B/CI 提供），与本轨无关；改动前已存在，未改这些文件或断言。本轨测试不依赖 Node 桥：直接按 `publish` 输出形状写 `assets` 表。

## 限制与 NOT_RUN

- **L2 实际研究行动未跑，NOT_RUN**：无真实科研模型调用、无外发、无新沙箱探针、无 GPU/云后端、无 Hub/发布授权。
- `research-v1` 是建议层：机会份额只建议 + 已批准容量分配；真实认领仍走原 `TaskLedger` 重查 scope/capabilities/dependencies/lease/fencing/`BudgetLedger` reserve。未知预算不视为 0，branch/run 不重置 envelope。
- A 未接线前，`snapshot`/`research_feedback`/`accept` 是薄接口，不在 `ResearchService` 的 11 个 MCP 工具内（服务接线与 host 绑定身份传递归 A）。
- 三个轴的 `disputed`/`inconclusive` 状态已建模，产生这些状态的独立评审入口由 A 的共同研究层（FR-08/FR-18）接入，本轨仅提供模型、建议机会与接受边界。
