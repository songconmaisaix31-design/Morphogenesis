# 验收矩阵

本文件由协调者根据实际命令和产物填写，不由模型生成内容本身决定是否通过。

| 检查 | 所需证据 | 当前状态 |
|---|---|---|
| 可复现环境 | Python/Node 锁安装、包构建、导入 | T0 `32c897a` 分轨通过；最终集成包待验 |
| G1 契约 | caller 与 implementation 真调用、语义拒绝测试、strict 类型检查 | T0 持久化/独立复核调用通过；其他实现对接待验 |
| G2 各轨 | 分轨测试及集成测试 | 未运行 |
| 权重影响选择 | 反馈前后不同实例被选中，执行入口消费该选择 | 未运行 |
| 重复反馈 | 重复 msg_id/AttemptId 不增加奖励/采用次数 | 未运行 |
| 经验使用 | 正文注入执行输入，执行者报告采用，绑定实际 attempt | 未运行 |
| 归档一致性 | 归档后缓存/检索均不可返回；重启也一致 | 未运行 |
| 接续 | 执行后中断，再恢复进入复核；工具调用与文件副作用无重复 | 未运行 |
| 独立复核 | 固定外部测试运行通过，执行者不能修改测试 | 未运行 |
| 受控运行 | 预算/超时/停止/路径限制/发布批准拒绝用例 | 未运行 |
| SDK 本地接口 | Python→Node 调用官方 SDK schema/hash | T0 官方 Node SDK schema/id/tamper 检查通过；Python桥成功路径待验 |
| MCP 本地接口 | 官方 MCP Server 握手和实际工具调用 | 未运行；与远端 Hub 分开 |
| Hub 远端接口 | 官方沙箱凭据、受控发布回执和可发现性 | 未提供沙箱配置，未执行 |
| 模型任务 live | 当前入口真实模型调用，真实产物和独立验收 | 未运行 |
| 可视化 | 真实事件输入，来源/三态独立展示，浏览器验证 | 未运行 |
| Git 交付 | 每轨 commit+push、集成分支 push、干净工作树 | 计划提交已推送，业务未完成 |

G0/G3/G4/G5 暂不宣称通过。本地 SDK/MCP 接口、mock/stub 联调、真实模型任务、Hub 远端发布是不同证据。

T0 分轨证据（Worker 已提交并推送，协调者已核对提交内报告，集成时重新执行必要全套检查）：

- `uv tool run poetry run python tools/contracts_check.py`：20 passed。
- `uv tool run poetry run mypy`：18 个源文件通过。
- `uv tool run poetry run python -m build`：sdist/wheel 通过，含固定验收资源。
- `uv tool run poetry check --lock`、`npm ci --ignore-scripts`、`npm run check:sdk`：exit 0。
- 实际环境 Python 3.12.13 / Node 24.16.0；FAISS Windows 原生索引/查询与 LangGraph SQLite 重开检查通过。

预算边界：T2 核查当前 Codex CLI 没有公开的单次调用硬 token/美元封顶参数。实现限制为有限单次调用、无自动重试、缺失 usage 后停止进一步消费；此能力不可写成硬费用上限已实现，G0 预算项保留限制。
