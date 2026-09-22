# 验收矩阵

## 当前新增验收：固定完整彩排（进行中）

旧版三次单任务测试不计入本轮三次完整彩排。每轮必须在独立 TEMP 根按顺序观察：真实固定 bug/checkpoint 初始失败 → 模型修复并外部复核 → 管道实际权重变化 → 两任务间下线获胜成员 → 另一成员被选中且完成新任务 → 真实 Gene 生成/采用/墙钟衰减/归档后不可检索。每轮最多两个新任务，未知执行不重试。

| 本轮项目 | 状态 |
|---|---|
| R 运行 / V 展示实现与集成 | 开发中，最小快照契约 e3fe21d 已交付 |
| 完整软件彩排 1 / 2 / 3 | NOT_RUN；不能用旧单任务证据或 fixture 替代 |
| 用户新凭据 API 测试 | NOT_RUN；Base URL / 模型或 Hub 用途待用户确认，凭据未发送 |
| 真实投影接线 / 实际场地彩排 | NOT_RUN；当前仅检测到一个活动显示屏 |

以下为上一阶段已完成基线的证据，保留精确范围。

协调者核对命令、日志、真实任务产物与最终浏览器截图后记录；AI 生成、Mock 展示和本地测试不替代真实外部验收。详细证据见 [集成报告](tracks/integration.md)。

| 检查 | 结果与边界 |
|---|---|
| 可复现环境 | Poetry / npm 锁安装通过；Python 3.12.13、Node 24.16.0；sdist / wheel 构建通过，11 包及资源安装后检查通过 |
| G1 契约冻结 | 通过：真实调用方与实现方联通；Pydantic / SQLModel / Runtime / Metabolism 语义检查；全实现 strict 50 文件无错误 |
| G2 轨道集成 | 通过：八个功能轨合入，完整 pytest 149 passed |
| 权重影响选择 | 真实 reuse：初始权重 1/1.5，载入前次真实复核反馈后 builder1→builder0，实际执行 builder0 |
| 重复反馈 | 拓扑与代谢测试通过；重复反馈不重复奖励/计次，最终已完成检查点在副本上重复恢复两次也不增加事件或采用记录 |
| 经验使用 | 前次 normal 成功经验正文进入 reuse 执行输入，模型显式报告采用，持久 UseRecord=1；绑定实际 attempt，注入/使用计数各 1 |
| 归档一致性 | 本地 SQLite 事务、检索/缓存及重启测试通过；未证明远端归档同步 |
| 接续 | 真实执行后暂停，新进程恢复复核，总 CLI 调用仍为 1；最终代码另在三个完成检查点副本上各恢复两次，执行器/复核器均未被再次调用 |
| 独立复核 | normal/resume/reuse 均通过外置三个函数测试；最终代码再次复核三个保留候选通过 |
| 受控运行 | 单次调用、超时、停止、路径白名单、发布批准拒绝与 UNKNOWN 不重试通过；单次硬费用/token 上限受公开 CLI 能力限制 |
| SDK 本地接口 | Python→Node 官方 GEP SDK/Ajv 的 schema/hash/tamper 检查通过，published=false |
| MCP 本地接口 | 官方 MCP 客户端与 Server 握手、工具调用通过；输入合成，证据为 contract_local |
| Hub 远端接口 | 未运行。实现当前仅允许 literal loopback，本地 stub 联调不证明正式沙箱接口或发布成功 |
| 模型任务 live | 三次真实任务通过，合计 3 次调用 / 43,166 tokens；费用未知；集成复核新增调用 0 |
| 可视化 | Chromium 真实渲染既有 reuse 导出：5 条消息边、1 Gene、1 来源边、1 采用边，两个 Canvas，三态独立；本地 ECharts 6.1.0；网络/控制台检查通过，截图已查看 |
| Git 交付 | 八轨及独立集成分支已 commit + push；主线接收集成结果并提交验收记录，保留完整历史 |

## 门禁结论

G1 / G2 已通过。G0 的单次调用硬预算仍有限制；G3 / G4 仅完成本地官方接口与固定样例真实任务部分，Hub 外部链路未通过，不能标整体通过。G5 按统一对齐文件指代码冻结/现场演示，现场尚未执行。T4 配置进化是独立可选项，本次未开发。

实际 Orca CLI 多 Worker 属于开发流程；产品运行时供给仍是固定规模逻辑成员 fallback，不能以开发多开冒充运行时动态供给验收。三次固定样例不证明性能提升、最优拓扑或通用自主修复能力。

## 验证命令

命令在集成 worktree 的锁定环境运行，主线使用相同实现。最终报告记录各次检查对应提交。

| 命令 | 结果 |
|---|---|
| `uv tool run poetry check --lock` / `uv tool run poetry install --no-interaction` | 通过，项目独立 .venv |
| `npm ci --no-audit --no-fund` | 通过，锁文件未改 |
| `uv tool run poetry run python -m pytest -q` | 149 passed |
| `uv tool run poetry run python tools/typecheck.py` | 50 source files，0 errors |
| `node --check bridge_node/asset_bridge.mjs`、`node --check tools/check_sdk.cjs`、`node --check viz/static/app.js` | 通过 |
| `npm run check:sdk` | schema_valid / asset_id_verified / tampering_rejected=true |
| `uv tool run poetry run python -m build` | sdist / wheel 通过 |
| 安装 wheel 后 `python -I tools/check_distribution.py --site-dir tools/.wheel-site --check-node` | 11 包、资源、独立验证器、Node 桥通过 |
| `node .runtime/integration/browser.cjs` | 真实 DOM/Canvas/网络/截图通过；无页面或控制台错误 |

wheel 检查复用锁定依赖，目标位于源码目录下，Node 能向上找到源码 node_modules；不代表任意 site-packages 中 Python wheel 单独运行 Node/MCP。完整使用仍需源码 `npm ci`、Node、Codex CLI 和账号。

GitHub Actions 双平台结果：[run 35682995743](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/35682995743) 在精确集成提交 `b6bb49c3112a12f3c0bdcddbddbf2dde453be2e6` 上 **Ubuntu / Windows 均 success**，覆盖锁安装、149 tests、strict、构建、SDK 和安装后分发检查。主线后续只修改本验收、状态、计划与决策文档，业务实现相同。

## 三次真实任务（2026-09-22）

协调者核对了 `%TEMP%/morph-t2-{normal,resume,reuse}-20260922/` 的 summary/result/events/genes/adoption、独立复核输出、实际 CLI 提案及 resume-observation。原始日志和工作目录保留本机临时目录，不提交 Git。

| 场景 | 独立复核 | CLI 调用 | tokens | 费用 |
|---|---|---|---|---|
| normal | 通过 | 1 | 14,327 | 未知/null |
| resume（暂停后新进程接续） | 通过 | 合计 1 | 14,330 | 未知/null |
| reuse（前次真实经验） | 通过，采用记录 1 | 1 | 14,509 | 未知/null |

合计 43,166 tokens 不含开发 Worker 的消耗。使用 gpt-5.6-luna / Codex CLI 0.155.1。单轮结束不自动启动下一轮。

集成恢复复核先复制数据库与 sidecars，再在副本操作。调试首版只读 SQLite backup 曾使 normal/checkpoints.db-shm 的 mtime 改变，bytes 未变；最终副本方案全部原文件 bytes/mtime 断言通过。不能声称整个集成期间所有辅助文件的 mtime 从未变化。CLI 产物、sample.py 和业务证据未因接续重复写入。

## 真实剩余限制与人工项

- 尚无 Hub 正式沙箱地址、凭据及对接契约；接入前需替换当前 loopback 限制为经核验的正式适配，并执行受控发布/发现性验收。未进行生产发布。
- ORCA 产品运行时供给契约未提供，当前固定逻辑成员 fallback；动态供给未验收。
- 公开 CLI 无单次模型调用硬 token/美元封顶。实现仅有限调用、超时、完成后检查 token、未知费用不自动续跑；不能把未知费用记为 0。
- sklearn 字符词法向量 + FAISS 不是语义 embedding；本地经验归档不证明 Hub/Evolver 远端原子同步。
- Orca 内嵌浏览器 helper 返回 browser_owner_unavailable，未修复该全局能力。已用现有外部 Playwright/Chromium 完成页面验证，不等于内嵌浏览器通过。
- T4 可选进化与 G5 正式现场演示未执行；独立测试/语法门也不等于通用敌对代码沙箱。
