# B 阶段3：受信案例与科研协作桥接

结论：本 Owner 的授权领域适配、相关 Windows 本地测试及独立 copy 安装检查通过，交付层级为 **prepared / contract_local**。没有执行真实原生三角色、模型/API、OpenSandbox、Hub 或实际科研 adoption；本报告不签署 interface_live/task_live。

## 冻结来源与所有权

- Task `task_ee0b6f8ea056`，Dispatch `ctx_12f73e32dbfb`；固定原 B Owner、worktree 与 branch `songconmaisaix31-design/morph-research-space-0930`。
- 初始 `c4d46b9325884687571166fa0227ca1214d8c0d9` clean。收到 root `STAGE3_BRIDGE_WRITE_RELEASE` / `msg_7fdc88bf1d50` 后，核验远端准确 C 接口并 ff-only 到 `789181538c694d8677297b0e0bdfbf879bcc8138`，没有提前写入或追逐 mutable 源码。
- 元数据适配 SOURCE `b74fb531df9f3b68686aad9865f780fd78a32bde`；最终领域 SOURCE **`5fb0cee3753b5169856f7ea8e0490c2daa2bad4f`**。两次正常 push；最终 SOURCE 与 origin 同名分支完整 SHA 一致、worktree clean。
- C 后续 `08b37827e6e6b48db93962611b1a79a230b1f2c1` 仅 C 测试收尾，由 I 集成；B 的实际消费接口仍是固定 `789181…`，没有替 C 修改测试或报告。
- SOURCE 相对接口基线仅改 `swarm/research/case.py`、`tests/research/test_registered_cases.py`，以及 root 另行授权的 `tests/local_assets/test_git_timeout.py`。本次 REPORT 只改本文件与 `docs/tracks/research-space-1001.md`，报告提交 SHA 由推送后 Handoff 回传。
- TaskLedger、C 科学代码/数据/judge、A WindowsJob、生产 Git helper、MCP 底层、锁文件、pyproject、tools、其它 Owner 报告均未修改。原 `tests/research/test_case.py` 字节保留；原完整 checker blob 仍为 `39948d9615bce07b40b96eeaf5dfb263b993c6d3`。

## 适配与接口 Handoff

| 位置（SOURCE 5fb0cee） | 实际接口与边界 |
| --- | --- |
| `swarm/research/case.py:26` | 原 `seed_case(...)` 签名保留，P 原调用无需注入新权限参数或更换执行器。 |
| `swarm/research/case.py:58` | `definition = get_case(case_id)`，case_id 来自受信 operator 提供 plan 的 `criteria.version`；未知案例在建目录/ledger 前拒绝。 |
| `swarm/research/case.py:63` | 完整生产 plan 经 C `ExperimentPlan` 校验；固定 claim、判据、输入身份与注册输入由 C 负责。保留原简化 NIST 离线 seed 契约。 |
| `swarm/research/case.py:69` | 原 `no_links(path)` 不变：输入链接、hardlink、多余路径或缺失输入不能绕过门禁。 |
| `swarm/research/case.py:76` | `definition.validate_inputs(registered, inputs[0], inputs[1])`；候选正文必须等于实际 plan.code 输入 UTF-8 字节。B 未复制 CSV、候选程序或科学公式。 |
| `swarm/research/case.py:98` | C `file_policy_prefix` 生成角色静态文件策略版本。旧 NIST 三角色版本仍与原契约相同。 |
| `swarm/research/case.py:116`、`:123` | 任务问题与候选 summary 分别读取 `definition.problem` / `definition.template_summary`，移除桥接中的 NIST 专用正文。 |
| `swarm/research/case.py:146`、`:156`、`:157` | 受信 CLI `--case-id` 默认旧 `nist-numacc4-v1`；调用 C `build_plan(role="author", order="original", directory=...)`，读取实际 `plan.code.local_path`。不提供目录时定位 installed 输入。 |

第二案例 `synthetic-linear-regression-v1` 只由 C 改变数据、候选程序和可信科学判定。案例选择发生在 operator seed 入口，不增加外部 Agent 科学选择工具、动态 validator shell/import 或新协议。真实科研 MCP 仍为原11工具。

原 scope `science`、`science/experiment.py → science/reused.py`、changes/preimage/base_revision、canonical attempt/current fence、角色依赖、预算及未知停止语义继续复用。两个案例走相同 TaskLedger / ResearchHost / OfficialExperiments 桥接与文件验证路径；未加入自动 claim/renew/批准/adopt、环境派单或 Observer 推进。

`tests/research/test_registered_cases.py:26` 两案例参数化契约使用真实 ledger、不同 worker/AgentId、显式合法 claim/renew、canonical 发布及 C 官方桥接。C LocalContractBackend 实际运行小型 CPU fixture，但 provenance 为 mock，所有研究结果保留 quarantine：独立复现批准门禁拒绝 mock，未批准 apply 拒绝，重复实验被 once 门禁拒绝，第三角色前序未完成不能 claim/inherit。没有捏造 UseRecord、批准或 AdoptionReceipt。已有通用资产测试覆盖实际文件 apply 与 adoption 机制；它们不能替代本研究案例的真实三角色闭环。

`tests/research/test_registered_cases.py:104` 六种错误种子（未知 case、错 claim、错判据、程序/数据身份或候选正文不匹配）在项目/权威 DB 创建前拒绝，不启动 backend/模型。`:126` 核对第二案例 CLI 无 case-directory 时使用 C 提供输入。

## Windows Git 原行为回归

真实缺口发生在测试 fixture：原 0.2 秒 communicate 在冷启动时可能先结束 wrapper，尚未建立继承 stdout/stderr 的真实 descendant；不能把这种结果当作 EOF 回归证据。生产 `local_assets/paths.py` 不改。

`tests/local_assets/test_git_timeout.py:35` 保留真实 Popen/native_run/Windows 句柄，仅对新建自有 fixture 设置就绪阶段。两个纯标准库子进程使用官方 CPython `-I -S`；新 wrapper 在已有 A `WindowsJob` 成功赋予所有权后才创建 descendant。测试持有实际 descendant handle，确认 communicate 前仍存活。A 源码不变。

原始五条断言、实际 `git(..., timeout=0.2)` 和单一总计时起点全部保留：`:89` 起表位于 Git 调用前，fixture 启动/Job/READY 都计入原 **总耗时 <3秒**；没有 READY 后重置时钟或提高通信超时。真实 stdout/stderr、READY、Git argv 与0.2秒参数仍逐项验证。`:99` finally 在原 EOF/耗时断言之后回收新建专属 Job，不能靠提前杀 descendant 使断言通过；`:114` 等待持有的实际句柄退出，无按名字/全局子树误杀或附着会话终止。

`10-git-diagnostics.txt` 对应的原始 fixture.log：root PID61120、descendant PID75388；Popen进入0.265161秒、Job赋权0.266202、READY0.747966、实际TimeoutExpired0.956122、原断言结束0.956428、清理结束0.958646。两实际退出码均1，后续只读精确自有 fixture CIM 查找 count0。退出码是 fixture 清理事实，不是科学结果。`:129` 保留原始本地诊断日志，不生成完成证明体系。

## 冻结验证与安装来源

私有 sibling：`C:/Users/DW/orca/workspaces/Morphogenesis/morph-research-bridge-cases-1002-state-12f73e32`。首次环境、冻结归档以及后续 copy 环境分别新建；未复制旧 venv、node_modules 或运行产物，允许下载缓存。依赖导出来自原 poetry.lock，hash 校验安装；进程 BLAS/OMP=1。源码通过准确 Git archive，wheel 非 editable；Node 原锁 `npm ci --ignore-scripts`，不设置 NODE_PATH。没有修改 global HOME/auth/model/tier/凭证内容。

| 命令 / 原始日志 | 实际结果 |
| --- | --- |
| 冻结 SOURCE 的 `python -m mypy --strict swarm/research local_assets/research.py`；`11-frozen-strict.txt` | 8 source files，无错误。 |
| 冻结 SOURCE 的 `python -m pytest tests/research tests/local_assets tests/experiments tests/swarm/test_assets.py tests/t1/bridge/test_assets.py -q --junitxml=<private>/12-frozen-related.xml`；`12-frozen-related.txt` | **197 passed /240.99秒**；本次 Windows 范围无 skip。包含真实 ledger stale holder、缺失产物、判据失败、条件不符、unknown 和原资产门禁。不是全仓或双平台门禁。 |
| 准确5fb归档 `uv build --wheel`，独立 `copy-venv`；依赖 `uv pip install --require-hashes --link-mode copy`，wheel `--no-deps --link-mode copy` | 锁定依赖与非 editable wheel 安装；Python3.13.13、Node24.16.0。保留 nlink=1 门禁。 |
| `16-copy-installed.txt`：7项 GitZIP/wheel/site 原字节比较，实际 stat/no-links | B case、C case、Node bridge、两案例代码/数据全部一致、nlink=1、非 symlink。 |
| installed Node 官方 SDK 本地 canonicalize | 输出 `{"case":"local","tier":"contract_local"}`；纯本地操作。 |
| copy-venv 的 `python -I -m swarm.research.case --project <fresh> --state <fresh> --python <copy-python>`；默认 NIST 与显式 `--case-id synthetic-linear-regression-v1` | 两 CLI 均 exit0；无 case-directory，代码来自 installed site-packages。每例仅3个未认领任务，owner/result为空、attempts0，experiment NOT_RUN，无批准/adoption。 |

7项来源分别为 `swarm/research/case.py`、`orchestration/experiments/case.py`、`bridge_node/asset_bridge.mjs`、`demo/research_case/{experiment.py,NumAcc4.dat}` 和 `demo/research_cases/synthetic_linear_regression/{linear_regression.py,data.csv}`。`direct_url.json` 指向私有 `frozen-wheels/morphogenesis-0.1.0-py3-none-any.whl`，没有 editable 标记。完整 stdout/stderr 在 `16-cli-<case-id>.*`，未重用已有案例路径。

## 首红、诊断与未发布草稿

后续通过都是新来源/新检查证据，不覆盖以下原红：

| 记录 | 保留结果与解释 |
| --- | --- |
| C 原789相关范围 | 116PASS/1FAIL，618.16秒；Git fixture 未达到 descendant READY，原输出仍归 C。其遗留自有进程由 C 正确认领并单独清理，B 不假定 sleep 已退出。 |
| `01-baseline-red.txt` | 旧789种子对第二案例原拒绝 `official_public_case_plan_required`，1FAIL/8deselected、93.74秒；受控旧行为回归。 |
| `02-strict.txt` | 首次 str 类型收窄错误1项；修改 B 自有 case_id 绑定后04/11严格检查通过。 |
| `05-final-pair.txt` | 复制快照路径误指向自身，PowerShell 首错保留；随后2PASS属于先前快照，不能代签最终新增断言。绝对路径正确复制后的06为2PASS/62.73秒。 |
| `07-git-ready.txt` | 首次 B READY fixture 实际总耗时3.0680564秒，原<3断言失败，1FAIL/14.92秒；未改阈值。官方-I/-S的08、专属清理09、诊断10分别是后续版本1PASS。 |
| `13-installed.txt` | UV默认安装首次 CLI exit1；首 CalledProcessError 未打印原 stderr，不能补写原因冒充已捕获。原项目/状态不存在。 |
| `14-installed-diagnosis.txt` 及 stdout/stderr | 另开新路径采集完整错误：installed 输入 nlink=2，原 no_links 报 hardlinked_path，创建项目/ledger 前拒绝。是安装方法不符合正式 nlink=1，不是应放宽的业务门禁。 |
| `15-unreleased-hardlink-compat.patch` | root 未授权的 hardlink 兼容草稿，仅私有保存，**未执行测试、未提交、未发布**；已恢复 own 两文件到准确5fb。最终代码仍保留 no_links，16采用全新copy安装通过。 |

最初 C 远端无前缀 ref 查询 exit0但无匹配，随后用正确完整分支核验；root 最终验 ref 首EOF/TLS错误后另次读取准确5fb，首网络失败保留。没有 force push、丢弃他人 WIP 或修改全局 Git 配置。

## 接续与真实限制

root `msg_e5f510f482e4` 已实际读16/12/11并接受 B 冻结领域门，放行 I 消费准确 C08b+B5fb；本 Owner 只做 doc-only 收尾。SOURCE 不需要新领域修补。

I 仍须在最终累计 core/product/checker 精确冻结、独立安装之后，核验完整双平台工程门并按 root release 运行真实 Case1/Case2：独立品牌/UUID、有效显式 renew、一次 fresh sandbox、可信科学复现、原 candidate 的文件验证/批准/apply、第三角色主动 search/本地再验证/inherit child/文件验证/apply(execution_id)/实际唯一 AdoptionReceipt。B 本轮这些 live 动作为 **NOT_RUN**；mock quarantine 拒绝不能代签真实继承完成。

原11工具权限、runtime3600/attempts3/每任务一次实验、unknown停止、原全 checker 字节与断言保持。旧case06原checker PASS但有效续租新标准 NOT_SATISFIED，旧expired research-host7d04、原认证401及未知效果档案均只读保留，不重置 clock、不拼接作者证据或自动重跑旧实验。后续具体领域返修仍由本 Owner 经 root 授权处理。
