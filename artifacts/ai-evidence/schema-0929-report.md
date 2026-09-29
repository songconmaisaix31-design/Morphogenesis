# B 轨 Schema nullable 收口 · 2026-09-29

**Owner 自验通过；仍为 1.0.0 candidate，待独立验收与人工 H3，FC 未冻结。** 仅删除 `docs/FC_LOG_SCHEMA_DRAFT_0928.md` 的 `allOf[1].then.required`，使 count 显式 null 时允许 audit 缺失；其 properties/const:null 仍拒绝孤立对象。数值要求审计、审计对象要求数值、0 要求 complete/无问题 ID/非空证据，以及其余 Schema 全部保留。

## 版本与范围

- 开工分支 `morph-schema-closeout-0929`，HEAD/base `73798cd6f05210f2bd9b1eebfd6f9f0dd6e842db`；开工 status clean，`git ls-remote` 确认 origin/decentralized-swarm 同 SHA。
- remote：`https://github.com/songconmaisaix31-design/Morphogenesis`。计划阶段 `b27a2ec16ce31b28d1b1ae60cd580288792fdcc9` 已 push，远端一致。
- FaultObservation 源固定 `73e64cc70116ac658d85591d082c0684a4952c99`。治理树不包含 FC 实现，不把跨分支能力混算。
- 修改只在 B write_paths：新一页日计划、PLAN 今日附录、TASKS 今日台账、Schema audit 条件及相应说明、本组 `schema-0929-*` 证据。未修改生产源码、测试目录、锁文件、AGENTS、SWARM 文档或他人工作树。旧 PLAN 和旧 TASKS 原文保留。
- 两份今晨审查已读，日计划登记 A/B/C 基线、排他写权、Dispatch、主控转发进展及三锁。C 前端是已批准的生产写权例外；A/B 无生产写权。主控转发 A cost_state 语义 exit 1，仍待决策/修复，不被本轨通过覆盖。

## 复用、命令与真实结果

本轨 [schema-0929-validate.py](schema-0929-validate.py) 沿用昨夜独立验收脚本的合法外壳、12 例和 9 控制，扩为 24 例和 13 控制。原脚本位于 `../morph-fc-acceptance-0928-final/.runtime/acceptance-0928/validate_schema.py`，历史报告 SHA `4409a60e278ce328fd76588d680e3c4438bdaa84`；项目 Apache-2.0。使用既有 integration `.venv/Scripts/python.exe`，Python 3.12.13、jsonschema 4.26.0（MIT）、Pydantic 2.13.5（MIT），未安装任何依赖。不新建 Schema 库、调度器或证明系统。

从 `git show 73e64cc…:swarm/{__init__,fault_observations,task_ledger,models}.py` 用 `subprocess.check_output` 原字节提取到本轨 ignored `.runtime/schema-0929/production/`。验证器逐个核对四个实际导入文件与精确 Git blob，再对 FaultObservation 的 14 字段完整 `model_json_schema()` 比较。使用 stdlib/jsonschema 执行，不涉及账本写入、网络或模型。

在本工作树执行（PowerShell；输出和 `$LASTEXITCODE` 分别保存在同前缀 `.log/.exit`）：

```powershell
& '../morph-fc-integration-0927/.venv/Scripts/python.exe' -B artifacts/ai-evidence/schema-0929-validate.py --revision 73798cd6f05210f2bd9b1eebfd6f9f0dd6e842db --production-root .runtime/schema-0929/production --output artifacts/ai-evidence/schema-0929-before.json
& '../morph-fc-integration-0927/.venv/Scripts/python.exe' -B artifacts/ai-evidence/schema-0929-validate.py --revision WORKTREE --production-root .runtime/schema-0929/production --output artifacts/ai-evidence/schema-0929-after.json
git diff --check
```

| 门禁 | 修前 | 修后 Owner 自验 |
|---|---|---|
| 原独立矩阵 12 例 | **11/12，exit 1** | **12/12，exit 0** |
| 扩展 audit 24 例 | **23/24** | **24/24** |
| 控制 13 例（含原 9 例） | 13/13 | 13/13 |
| `Draft202012Validator.check_schema` | 通过 | 通过 |
| FaultObservation 完整导出 / 非 audit | 14 字段一致 / 未变 | 14 字段一致 / 未变 |
| optional / 无 default / 输入不被填充 | 保留 | 保留 |

原 12 例含：两项真缺失、两项显式 null、仅 count null、仅 audit null、0 complete、0 partial、负数、数值无 audit、孤立 audit、数值配 null audit、null 配对象、正数 partial。扩展含：正数 complete、空证据、0 无/null audit、0 搭非空 ID、不接受小数/布尔/字符串、空 audit、重复 ID、额外字段及孤立 partial audit。控制含非法 live/mock 标签、drill、replay 缺来源、事件缺内容、空 task、额外字段、负耗时/attempt、非法 cost_state 与合法未知字段。

修前唯一失败路径仍为 `allOf/1/then/required`，`'issue_audit' is a required property`；修后只移除该要求。验证器断言完整解析 Schema 只能等于基线或“仅该 required 删除”的版本，故非 audit、其他 audit 条件和全部 `$defs` 均受保护。完整输出见 [before](schema-0929-before.json)、[after](schema-0929-after.json) 及相应日志。历史 8/9、11/12、exit 1 未被覆写。

初次证据环境检查 **exit 1**（[日志](schema-0929-environment-check.log)）：历史生产提取 `swarm/__init__.py` 为 CRLF 71 字节、Git blob 为 LF 70 字节，换行归一后相等；未进入矩阵。随后只在本轨 `.runtime` 从 Git 提取精确字节，字节检查成功；这是取证环境修正，不是产品修复轮次。修前已知红项为复现，修复后首轮通过，没有进行连续失败返修或越界安装。

## 真实限制与未执行

- 两个额外不一致样本（正数1配空ID、正数2配单ID）仍被 Schema 接受。文档既有责任要求消费侧验证 `count == len(unique(ids))`、scope 归属和证据可追溯；本次仅记录差异，**未实现生产消费者**，不宣称完整语义验证。0 配非空 ID、重复 ID 等现有可表达约束仍实际拒绝。
- `contract_local` 仅指候选 Schema 的 Owner 自验；`interface_live/task_live=NOT_RUN`，夹具不是真实日志采集。缺失/null 未补 0，任何数值都不能由本脚本推导成项目真实审计数量。
- 可选字段新增为 minor；optional→required 破坏兼容，需 major/2.0.0。当前候选纠错不提升到所谓“1.1 必填版”。
- 独立验收、人工 H3、H1、有效 FC-E 正式 deepseek v2 报告仍未完成；三锁未齐，不生产 merge/tag，不代签、不冻结。
- 未运行全项目 pytest/strict/build/SDK（本轨只改候选 Schema/治理/证据，生产模块未变；适用 Schema 行为与范围校验已运行）；新集成组合的门禁由独立验收/集成执行。未执行预算事后对账、生产接线、正式日志写入、T9/T10、付费 live 或长期运行。
