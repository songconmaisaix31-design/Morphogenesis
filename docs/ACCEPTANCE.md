# 验收矩阵

本文件由协调者根据实际命令和产物填写，不由模型生成内容本身决定是否通过。

| 检查 | 所需证据 | 当前状态 |
|---|---|---|
| 可复现环境 | Python/Node 锁安装、包构建、导入 | 各轨锁安装通过；11 包分发配置及最终集成待验 |
| G1 契约 | caller 与 implementation 真调用、语义拒绝测试、strict 类型检查 | SQLModel/Verifier/Runtime/Metabolism 等调用通过；全包 strict 收尾 |
| G2 各轨 | 分轨测试及集成测试 | 多轨分测通过，最终合并测试尚未运行 |
| 权重影响选择 | 反馈前后不同实例被选中，执行入口消费该选择 | 真实 reuse：声明初始权重 1/1.5，载入前次真实复核后选择 builder1→builder0，实际执行 builder0 |
| 重复反馈 | 重复 msg_id/AttemptId 不增加奖励/采用次数 | 拓扑/代谢合同级测试通过；最终集成复验待运行 |
| 经验使用 | 正文注入执行输入，执行者报告采用，绑定实际 attempt | 真实 reuse 通过，持久 UseRecord=1，源自 normal 的实际成功任务 |
| 归档一致性 | 归档后缓存/检索均不可返回；重启也一致 | 代谢本地事务与重启测试通过；远端归档未同步 |
| 接续 | 执行后中断，再恢复进入复核；工具调用与文件副作用无重复 | 真实新进程恢复通过，总调用仍为 1，源码/CLI 产物 bytes 与 mtime 不变 |
| 独立复核 | 固定外部测试运行通过，执行者不能修改测试 | normal/resume/reuse 均通过外置三个函数测试 |
| 受控运行 | 预算/超时/停止/路径限制/发布批准拒绝用例 | 分轨用例通过；公开 CLI 单次硬费用/Token 封顶不可实现，见下述限制 |
| SDK 本地接口 | Python→Node 调用官方 SDK schema/hash | `adca7f6` 真实 Node SDK/Ajv 桥测试通过 |
| MCP 本地接口 | 官方 MCP Server 握手和实际工具调用 | 官方 MCP initialize/list/install/evolve/record/recall/export 本地运行通过；输入为合成数据，仅 contract_local |
| Hub 远端接口 | 官方沙箱凭据、受控发布回执和可发现性 | 未提供沙箱配置，未执行 |
| 模型任务 live | 当前入口真实模型调用，真实产物和独立验收 | 三次真实任务通过；代码最终提交/集成仍待完成 |
| 可视化 | 真实事件输入，来源/三态独立展示，浏览器验证 | 初版 mock 浏览器通过；真实导出接线/浏览器正在补齐 |
| Git 交付 | 每轨 commit+push、集成分支 push、干净工作树 | 六轨候选已推送，T2/T5/全包收尾与最终集成未完成 |

G0/G3/G4/G5 暂不宣称整体通过。本地 SDK/MCP 接口、mock/stub 联调、真实模型任务、Hub 远端发布是不同证据。G5 依统一对齐文件指代码冻结/现场稳定；T4 配置进化为可选未开发项。

## 三次真实任务证据（2026-09-22）

协调者直接核对了 `%TEMP%/morph-t2-{normal,resume,reuse}-20260922/` 的 `summary.json`、独立复核输出、`resume-observation.json`、`genes.json` 与 `adoption.json`。原始 CLI 输出及工作目录保留在本机临时目录，不提交 Git。

| 场景 | 独立复核 | CLI 调用 | tokens | 费用 |
|---|---|---|---|---|
| normal | 通过 | 1 | 14,327 | 未知/null |
| resume（暂停后新进程接续） | 通过 | 合计 1 | 14,330 | 未知/null |
| reuse（前次真实经验） | 通过，采用记录 1 | 1 | 14,509 | 未知/null |

三个样例合计 43,166 tokens；不含开发 Worker 的消耗。这里证明固定修复样例的真实执行、接续和经验采用，不代表性能提升或最优拓扑。单轮结束不自动启动下一轮。

T0 分轨证据（Worker 已提交并推送，协调者已核对提交内报告，集成时重新执行必要全套检查）：

- `uv tool run poetry run python tools/contracts_check.py`：20 passed。
- `uv tool run poetry run mypy`：18 个源文件通过。
- `uv tool run poetry run python -m build`：sdist/wheel 通过，含固定验收资源。
- `uv tool run poetry check --lock`、`npm ci --ignore-scripts`、`npm run check:sdk`：exit 0。
- 实际环境 Python 3.12.13 / Node 24.16.0；FAISS Windows 原生索引/查询与 LangGraph SQLite 重开检查通过。

预算边界：T2 核查当前 Codex CLI 没有公开的单次调用硬 token/美元封顶参数。实现限制为有限单次调用、无自动重试、缺失 usage 后停止进一步消费；此能力不可写成硬费用上限已实现，G0 预算项保留限制。
