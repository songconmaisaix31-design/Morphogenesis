# Morphogenesis 今日首批三轨收口与下一步 · 2026-09-29

**今日首批 A+B 隔离候选完成标准合并及适用组合门禁；C 保持独立候选。FC 整体仍 BLOCKED、未冻结。** 不代表原 T1–T11 或今日全部开发完成。本轮无生产/测试手改、跨代前端合并、生产分支更新、tag、发布、模型或付费调用；D/Codex 不替代正式 deepseek FC-E 或真人 H1/H3。

| 输入 / 交付 | 分支与不可变 SHA |
|---|---|
| A 最终；全量测试证据所绑定提交 | `morph-fc-tests-0929@3d8bb856efadbb1bee4a69bc37c56d3ef4d24cfd`；测试 `f4779d45a1b1417ffa6bce37708e9a68d46cf4e5` |
| B 最终材料；D 已验收 Schema | `morph-schema-closeout-0929@092cadaf497482e00518dfd86d958a81c876a7bd`；Schema `318dd4f26f27cda25e4278772bcce6b508023c26` |
| D 报告单文件来源 | `morph-closeout-acceptance-0929@969d3274622538a36ac8a60e09c41be86bea9c60`；blob `bf3e8a8a06cd8b890558b3aa35120bea12baa6cd` |
| FC 组合候选 / 本次门禁 SHA | `morph-closeout-integration-0929@4c3dc46e7c0459680a7567ff6d91ba44301c3819`；父提交依次为 A、B；后续材料提交见交付回执 |
| 第一代只读应用独立候选 | `morph-readonly-app-0929@621f588988899bdbc7c7a83e893369c4145d89b3` |

所有输入已实际 `git ls-remote origin` 核对；origin 为 `https://github.com/songconmaisaix31-design/Morphogenesis`。A/B 共同祖先 `f159f1e698101a48579822a6ad0ee3e13e412bcd`，两侧 changed paths 交集为空，标准 `git merge --no-ff 092cadaf...` 无冲突。B 从 318dd 到最终 SHA 只增加/修改 CLOSEOUT、TASKS、PLAN、DAY_PLAN 四治理文档，Schema/H1 原文逐字节不变。合并相对 A 仅文档与证据；全部生产源码、全部测试（含 A 两文件）、AGENTS、docs/SWARM_*、锁与依赖声明的 Git blobs 不变。D 仅引入报告原 blob，未合并其旧测试基树。

门禁环境：`P=C:/Users/DW/orca/workspaces/Morphogenesis/morph-fc-integration-0927/.venv/Scripts/python.exe`，Python 3.12.13、jsonschema 4.26.0、Pydantic 2.13.5；未安装依赖。Python/Node 锁与现成环境逐字节一致；按主控授权只在 I ignored node_modules 建立指向 integration 现成依赖的 junction，SDK 1.14.0，目标未写。每条 Python 命令设置 OPENBLAS_NUM_THREADS/OMP_NUM_THREADS/MKL_NUM_THREADS=1、PYTHONDONTWRITEBYTECODE=1。

令 `L=.runtime/integration-0929`（相对 I 工作树），`M=4c3dc46e7c0459680a7567ff6d91ba44301c3819`。使用 `git -c core.autocrlf=false archive --format=zip M` 导出到 `L/candidate-src`；正式 focused 的 cwd 和实际 `swarm.worker_loop.__file__` 均为该精确候选导出，状态目录与源码平级。Schema 脚本复用 B 已提交的 jsonschema 命令，production-root 为同一 M 的 swarm 原字节导出 `L/schema-src`，FaultObservation 14 字段精确匹配；未新增验证框架。

| 实际命令 / 范围 | 退出与原始证据 |
|---|---|
| I 根：`P -B -m pytest -q tests/swarm/test_failure_chain_boundaries.py tests/swarm/test_failure_chain_runtime.py -o cache_dir=L/pytest-cache --basetemp L/focused` | **exit 1，18 failed / 2 passed，2.08s**。L/focused.log/.exit；状态在源码树内，既有 `worker_loop.py:236` 的 protected_runtime_state 拒绝。已上报，未改/绕过保护、未改 seed_demo |
| `L/candidate-src`：`P -B -m pytest -q tests/swarm/test_failure_chain_boundaries.py tests/swarm/test_failure_chain_runtime.py -o cache_dir=../candidate-pytest-cache --basetemp ../focused-candidate` | **exit 0，20 passed，43.60s**。L/focused-candidate.log/.exit、candidate-import.log；主控确认的一次目录布局纠正 |
| I 根：`P -B artifacts/ai-evidence/schema-0929-validate.py --revision M --production-root L/schema-src --output L/schema.json` | **exit 0，原 12/12（扩展的子集）、扩展 24/24、控制 13/13**。L/schema.log/.exit/.json；缺失/null、0/正数与 audit、非法值、孤立 audit、来源与非 audit 边界均保留 |
| A 原 `P -m pytest -q` / `P tools/typecheck.py` | **复用** f477 原日志：699 passed / 2 warnings / 450.96s，strict 87 文件，均 exit 0；本 merge SHA **未重跑全量/strict/build/SDK**。生产/测试无差异，无需追加这些门禁 |
| Git 范围 / 材料检查 | `git diff --check`、精确 blob/父提交/trailer、最终 clean 与 `git ls-remote` 对照；以本次材料提交和 push 回执封存，trailer `Swarm-Agent: codex` |

复用证据：[A 报告](fc-tests-0929-report.md)、[full699 原日志](fc-tests-0929-pytest-full.log)、[strict87 原日志](fc-tests-0929-typecheck.log)、[D 独立报告](acceptance-0929-closeout.md)。D 独立 A focused20/语义 mutation 红后恢复绿、B 44/44 已通过；C 独立 53 T5、build 两 bundle 字节一致、3 份历史 replay 的真实 HTTP→DOM 通过，本轮未重复 C 验收。证据分别限定于 mock 本地机制和历史 replay，interface_live/task_live 均 not_run。C 与 FC 从 `605cf48b8b05baf86fd68e5d63f495ba3e5d7e69` 分叉，Backend.jsx 与两个 bundle 确有冲突，本轮不强合。

**真实未解：** F=`73e64cc70116ac658d85591d082c0684a4952c99` 的 `swarm/worker_loop.py:839` 将有 usage、无价格的 observation.cost_state 写为 settled，账本仍为 unknown/full hold；A/D 语义检查 **exit 1** 保留，非预算释放/超支证据，最小生产修复待队长确认。`swarm/budget.py:253–257` 无 uncertain→settled 晚到结算，unknown hold 长期占额度；本地 allowance 不等于上游账单硬上限。Schema 仍 1.0.0 candidate，正数与 unique issue IDs 数量、scope、证据追溯依赖未实现的生产消费者。C 越契约 `adoptions=[null]` 导致旧 app.js 错误的 exit 1 仍保留，合法数据验收通过不表示该样本修复。

**下一步与人工项：** 队长确认 cost_state 最小元数据修复，由原 Owner 修复并交独立复验；真人 H1 复核四态/并发/fencing/预算限制，真人 H3 审批 Schema；恢复原有已授权 v2 正式 deepseek FC-E 范围，先核实原隔离 profile/launcher、工具通道及适用调用上限，不能替代引擎或制造报告。B 仅证实 CLI help 可用，原通道未定位；本轮无模型调用。发布三锁未齐，生产 merge/tag、Schema 冻结、依赖 H3 的 T9 生产日志接线、T10 演练、长期运行与新 live 均 **NOT_RUN**。继承待办未清空；benchmark 的 BENCHMARK_POLL_MS 风险本轮 **未核验**，不替其他活跃工作树断言修复状态。

入口：[今日计划](../../docs/FC_DAY_PLAN_0929.md)、[审批与下一步包](../../docs/FC_CLOSEOUT_0929.md)、[今日台账](../../TASKS.md)。系统实际 Desktop 为 `C:/Users/DW/Desktop`，新建同内容简明汇总并附绝对链接；0928 旧文件原字节保留，不覆盖同名文件、不生成 Word/PDF、不公开分享。
