# MorphBench 真实调用测评：B领域记录

当前状态：**准备中 / 正式调用 NOT_RUN**。本页为执行中的领域记录，不是最终验收报告。唯一最终汇总由 I 负责；本页不能用来声称算法优势、真实科研或完整故障覆盖。

产品原件 `50396909c3fbaa510e755b8e2361e05d84afdfaa` 与旧报告 `47f089ad92e0c459b2deeadab65109246d64ae9a`、`C:/Users/DW/orca/mb021-1007` 未改。新输出独占根 `C:/Users/DW/orca/mb-live-1007/eval`。当前请求数 **0**，无读取/打印/保存密钥本体，实际账单 `null`。

## 版本与范围

- 本轨分支 `songconmaisaix31-design/morphbench-eval-1007`。
- 治理 `445aad4e3066e7cbfc0123adc1779d24d0c74cd4` 已普通合并。
- 协议阶段 SOURCE `254989b07541f5b504dcf3815d70543a8d541ae4` 已push；主控认可设计，未授权正式运行窗口。
- A代码候选 `948252311018a433cb4b4c905d8c5364a11d678f`、HTTP trace后继 `d5cb717f734eb34cb17855d3075c4f37c43667ca` 均普通合并；最终安装及门验证待计算窗口。
- 基准是三函数、六缺陷的 local code-defect benchmark；统一新executor上的old/new策略及Single/Central机制消融。不是纯0.2.1端到端横比、SWE-bench或科研排行榜。

完整预注册判据、预算、模型、四类矩阵见 [协议](morphbench-live-protocol-1007.md)。主控消息 `msg_7b0684d34186` 在正式前批准before_commit独立1槽：233已分配+7保留=240≤256，每请求hold CNY0.1，全流程hold CNY24≤30。单独preflight计划不执行。

## 首失败与已完成检查

| 检查 | 真实结果 | 原始证据 |
|---|---|---|
| 初版矩阵/同额度/输入隔离单测 | 3 PASS | 阶段254989b；后继增加故障槽后待重测 |
| 6个原始buggy seed独立安装版负控 | 6/6均被固定测试判失败，负控PASS | `eval/offline-v1/result.json`、各子目录stdout/stderr |
| 新环境依赖 | 从旧只读已核验清单复制安装，不改旧venv | `eval/dependencies.txt`、`dependencies-install.log` |
| Node prerequisites | npm ci --ignore-scripts，99 packages | `eval/node-install.log`、冻结package-lock |
| 基线50396909非editable安装 | 成功 | `eval/baseline-install.log`、`baseline-50396909.zip` |
| A9482523第一次安装 | **RED 0xc000012d**，安装失败，不声称精确环境就绪 | `eval/install-9482523.log`；source/zip保留 |
| 初次本轨mypy调用 | **RED No module named mypy** | `eval/type-tools-first.log` |
| 安装锁内mypy工具 | mypy1.20.2、extensions1.1.0、pathspec1.1.1、librt0.15.0 | `eval/dev-type-install.log` |
| 旧3文件strict类型债 | 已修37项；原首RED由A保留，另1项frozen_export越轨交I | `core/type-full-first.log`；`eval/type-tools-second.log` |
| 新工具strict检查后继 | 12 files PASS | `eval/type-all-tools-fifth.log`；中间RED日志逐次保留 |
| 新四类完整离线Worker验证 | **NOT_RUN**，等A释放独占计算窗口 | 尚无正式或离线分数 |

宿主Orca重启后已换新dispatch；原 `ctx_d497608881ae` 被围栏，续接 `ctx_d4bfb6a05b88`。安装首OOM没有重写成成功。主控将A重回归、B安装/实跑、F浏览器及I最终门串行安排，不改全局pagefile，不杀未知进程。

## 真实剩余限制

正式预算、请求id/返回model、input/output/cache usage、原始费用总账与逐cell结果均尚未产生，保持NOT_RUN/null。离线Mock HTTP仅验证工程通路，不能转为task_live分数。拟用独立固定测试作为裁决；提示配置反转如果没有实测能力分离，要报告不可辨识。

原始固定测试只对本次模型输入隐藏，公开仓库可能进入训练数据；`-I -S`加纯函数AST白名单不是操作系统沙箱，也不支持一般工程仓库任意代码。正确经验必须真实生成、验证并沿合法链采用；错误经验若被审核拒绝，只能证明拒绝，不能声称模型在上下文中战胜错误经验。

before_commit预计needs_review/BLOCKED且0重发；after_commit才检查已提交effect的安全finalization恢复。inflight实际send-entry仍不等于供应商收到请求；未知请求不重试，账单未知保留null。最终结论必须在完成固定批次或明确协议停止后基于保留的原件补全。
