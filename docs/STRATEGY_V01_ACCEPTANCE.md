# 策略 v0.1 验收

**当前状态：NOT_RUN（累计版本正式入口、独立安装与完整工程验收）。**
本页是本轮候选验收范围与待填的事实，不以旧科研 PASS 或 D 的定点测试签署新版本。
A/B/C 冻结输入、最终核心 SOURCE 和独立 I 结果尚待交接；新增科研运行与 main 发布等待用户明确范围。

## 版本与现有证据

| 对象 | 身份 / 当前用途 |
|---|---|
| 历史科研核心 | SOURCE `bf67c1a4134a25d009cff2acccbfab027999bea6`；REPORT `7b66f0dd0a285c1b6cf789aa3c5a41d22d655993`，本轮开发基线 |
| 历史私库产品 | REPORT `e9a68668ac1e15038faaa3b04a34e2a5aa0c9f4a`；既有产品固定核心 bf67，不能表示本轮安装已更新 |
| 本轮核心 / 产品 / 策略 | 待四轨与独立 I 的精确冻结身份；产品最终 pin 必须等累计核心 SOURCE，报告 SHA 与业务 SOURCE 分列 |
| D 投影领域输入 | SOURCE `69f586e79adb23cae5d6bb21f3c46e22b0cc850e`，仅领域 contract_local；不代替累计核心或正式产品 pin |
| NIST 原完整检查器 | `tests/integration/check_research_live.py`，Git blob `39948d9615bce07b40b96eeaf5dfb263b993c6d3`，原断言不改 |
| synthetic 原完整检查器 | `tests/integration/check_research_case_live.py`，Git blob `538f6b1852ccbba3f1cef6d09ad16b2a6fe8d4f5`，原断言不改 |

独立 I 使用安装分发元数据、`direct_url.json` 和真实 Git 对象核对核心 / 产品 / 策略版本，复用产品已有 `morph-research audit` 清单，不建立另一套 Manifest、哈希索引或完成证明。`logs/10-source-provenance.json` 的 `case_checkers[case_id]` 必须绑定真实 SOURCE、固定检查器路径与 Git blob；不制造自引用提交身份。

现有清单已区分 `subject` 与 `generated_by`：前者是历史案例实际执行的核心、产品与检查器，后者是当前安装的审查生成器。旧 NIST / synthetic 档案可以在只读条件下核对，但应保持 `historical_readonly_reverification` / `new_task_live=not_run`；旧执行不能归到本轮新 SOURCE。

## 五项停止条件

| 条件 | 需要的实际证据 | 当前本轮状态 |
|---|---|---|
| 正式入口共享策略 | 安装后原 MCP 路径的策略版本、合法候选、推荐、实际认领与主动覆盖可关联；不是仅 Router 单测 | NOT_RUN，等 A/C/I |
| 可信反馈改变偏好 | 至少两个合法候选；同一可信结果反馈前后概率或推荐变化可解释，固定种子和衰减事实单列 | NOT_RUN，等 B/C/I |
| 安全硬约束保持 | 依赖、能力、scope、当前租约、预算与未知效果拒绝仍由原账本/执行边界决定；评分不赋执行权 | NOT_RUN，等累计核心验收 |
| 恢复不双学习、不重放 | 同事实同类学习幂等；崩溃/投影重建不执行模型/实验；未知学习状态保持 incomplete | NOT_RUN，D 只覆盖投影侧，C/I 覆盖可信反馈 |
| 版本、安装与工程一致 | 累计 SOURCE 原完整 Windows/Linux 流程、正式产品精确 pin 与独立非 editable 安装、检查器与清单实际绑定 | NOT_RUN，等独立 I |

五项全部具备即停止 v0.1，不扩展 Agent、案例、全局调度或外部平台。contract_local、interface_live、task_live 分列；首次 RED、NOT_RUN、unknown 与 null 费用原样保留。

## 首版候选窗口

原 TaskLedger 默认 `candidates(limit=100)` 按 `created_at, task_id` 排序；Router 在该有界窗口及既有合法性过滤内计算 softmax / 探索概率。窗口外任务当轮不参加评分或探索，不能宣称全任务覆盖、公平轮转或全局最优。只记录此支持范围，本轮不实现分页或轮转。

## 投影检查与显式恢复

FC JSONL 是 side-channel，原账本与可信实验/文件/采用档案才是执行事实。`FCLogWriter.projection_status()` 为 Worker 提供有界、secret-free 只读状态，`available` 仅指当前可读的有限 FC 记录，不表示完整执行或采用证明。写入/读取故障、半截记录、变化快照或未读完窗口必须显示 `incomplete`。

账本投影写入失败时停止后续自动投影，游标不越过失败源行；fsync 失败可能已留下字节，不能以再调用投影自动重发。显式 `rebuild_projection` 仅从调用方提供的可信日志和原账本 routing/claim 事实写全新目标：不覆盖半截原日志、不改账本、不学习、不调用 Executor。可保留的六类 FC 事实、原序号和 unknown/null 字段原样复制；缺失的资产/故障/彩排事实不能从任务 completed 推造。源日志不完整时重建结果仍为 incomplete，语法可读的新文件不能清除旧失败。

## 紧凑验收清单

只引用现有安装与产品 audit 清单、原始记录位置，不复制秘密或大段 journal：

- 核心/产品 SOURCE 与各 docs-only REPORT、策略版本、两检查器实际 Git blob、安装主体与审查生成器身份。
- 推荐候选及过滤条件、实际当前-token 选择/覆盖、可信结果来源与学习幂等事实；两候选概率变化与窗口范围。
- 原生三角色、实际实验/沙箱与 known/cleanup、源/子资产及唯一 AdoptionReceipt / ConsumptionExecution / ledger result 绑定；历史与新增执行分开。
- 首命令、stdout/stderr/exit、原始证据引用、RED/NOT_RUN/unknown、权限与人工步骤；原真实费用未知保持 null。
- 投影 status / 显式新目标重建结果，完整工程与独立安装原始结果；旧 task_live 不充当新版本 task_live。
