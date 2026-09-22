# 开发状态

## 最新结果：真实 EvoMap 免费 Gene 获取与审查完成（2026-09-22）

首次注册及绑定已由 HTTP 200 / claimed=true 核验。用户确认具体免费 repair Gene 后，仅一次 authenticated A2A fetch 返回 1 条资产，扣费 0 credits。Gene `sha256:c9ed1efef4529b9d43ac5738c27bb76735decf483aad5ddcabb974f53a252ae2` 通过现有官方 SDK schema 与哈希校验，可作为修复策略参考。

响应附带 Capsule 未通过 schema/哈希，现有 `validate_bundle` 以 `official_asset_validation_failed` 拒绝。未运行资产命令、安装到 Gene 池、注入模型任务或发布；不能把通用策略和文本验证声明算作项目修复验收。本次证明直接 Hub 定向获取可用，不证明 Evolver 插件/Proxy 已接通，既有插件阻塞仍保留。节点凭据仅在临时会话内，未持久保存或开启心跳循环。详见 [验收记录](ACCEPTANCE.md)。

## 最新评估：Evolver 插件部分可复用，尚不满足直接接入（2026-09-22）

按用户要求实测已安装并 enabled 的 `evolver@evomap` 0.2.0。17 个适配检查 **13 通过、4 不满足**：Windows 默认 MCP command 是 macOS 绝对路径；不能直接替换 8 个既有 `gep_*` 工具；缺失必填 signals 仍被桥转发；模拟提交已接收但响应断连时默认自动重发，单次调用出现 2 POST。手动采用本机 Node 的标准 MCP 握手、9 工具发现及 7 条隔离 stub 路由通过，关闭 autostart 后断连仅 1 POST 且明确失败。测试只运行本地合成服务，无真实 Hub 发布和模型调用。

本机 CLI / Proxy 尚未就绪，当前 Codex 会话未加载插件 MCP；默认宿主接入不通过，网络检索、实际记忆写入和任务采用 NOT_RUN。项目既有官方 GEP MCP 的安装/选择/记录/召回/导出/隔离对照复验 **1 passed / 4.59s**。保留现有网关、GEP 桥、metabolism、Hub 发布门与演示实现；不因插件 installed 状态替换主链。完整问题、来源、命令与证据见 [验收记录](ACCEPTANCE.md)。

## 最新结果：7527 本机单屏第五轮网关真跑通过（2026-09-22）

用户明确改为本机单屏、无需外接投影，并授权立即启动 7527。协调者在干净的 I 分支 `songconmaisaix31-design/morph-onsite-integration` / `bcd81beac5b9f73ac9f8267ccbc3f571e4faf738` 运行一次已集成入口；首幕至末幕北京时间 **17:48:48–17:50:14**，观察器 summary 的 demo exitCode=0、failure=null。恰好 2 次 EvoMap POST / HTTP 200，两个新样例各 0/3→3/3，builder#0 两任务间下线后 builder#1 完成后续任务并采用前次 Gene；2 Gene 衰减归档、21 个墙钟采样和归档后不可检索通过。共 **2,137 tokens**，费用未知/null。

`--operator-enter` 的 TTY 门已实跑：两视口及原运行根确认 awaiting_offline 后，协调者于 17:49:33 发送一次 Enter；这是工具操作，不是用户亲手按键或物理投影见证。1366×768 / 1920×1080 各记录全部 20 幕，共 40 张阶段图加 2 张等待图，页面错误 0。只读审计通过，29 原文件 bytes/mtime 未变，31 份文本扫描无凭据样式命中。证据路径及命令见 [验收记录](ACCEPTANCE.md)。

7527 保留本次 live 数据的 completed 页面（验收时 launcher 58304 → listener 25412），没有自动启动下一轮；7526 旧回放 listener 26576 未操作。viewer 存活使观察器父会话仍保留输出句柄，不能把 demo exitCode=0 写成整个终端已退出；未来停止前重核 PID、命令行和运行根。自动审批拒绝 `Start-Process` 打开桌面浏览器，理由 blocked by policy，未绕过；用户可直接访问 http://127.0.0.1:7527/ 。外接投影已取消为验收前置；桌面人工观看/全屏未见证，截图属于真实浏览器软件证据。

## 当前并行工作：现场展示与人工确认（2026-09-22）

用户要求继续多 Agent 并行开发。Orca Run `run_777080c220e3` 从计划基线 `9e4b432` 发出互斥的展示轨 V（`morph-onsite-viz` / `ctx_151a78289685`，有效模型 gpt-5.6-terra high）和人工证据轨 O（`morph-onsite-observer` / `ctx_b8f099cf5355`，有效模型 gpt-6-astra high）。V `1b2e335af52bd2e7de780d65fc14246a50bd2fd9` 与 O `26a5cf1e417813244809807de44c44e917993713` 已各自推送，31 项 Node 测试与 V 的 11 项展示测试通过。I 原派发 `ctx_af2da0cde34f` 普通合并后发现旧 Python fixture 固定绑定 7526，与常驻回放冲突；首次全套为 199 passed / 1 failed，错误原样保留。

O 原 Codex 会话在同一 worktree/branch 续接 `ctx_3169ef5e1e9a`，提交推送 `3d05f4e941ffe350270ddb9d55933a5065887665`，用系统分配的独立端口修复 fixture；原失败项定向 1 passed。I 收到精确 SHA 后合并，最终分支 `songconmaisaix31-design/morph-onsite-integration` / `bcd81beac5b9f73ac9f8267ccbc3f571e4faf738` 已推送并由主线 fast-forward 接收。31 Node、strict 53 文件、构建/SDK/11 包 wheel、双尺寸只读回放及 29 原件不变性检查通过；最终 SHA 完整 200 项未本地重跑，精确候选 [CI 35709392862](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/35709392862) 的 Ubuntu / Windows 两 job 均 success，run completed/success。四个派发均 succeeded，I/V 已 worker-release 关闭 agent terminal，O 恢复自既有外部会话，release 返回 retained / external_terminal。可回收派发列表为 0。详细命令与边界见 [I 报告](tracks/onsite-integration.md)。

今晚演示主执行器为 EvoMap 网关；OpenCode 仅为备选开发路径，其工具调用与流式今晚不测。原 17:30–18:00 物理投影计划被用户最新本机单屏指令替代；7527 新真跑已通过，见上节。Hub 保持本地 stub / 待发布；在途进程强杀恢复范围外。路演仅承诺“成员下线后，后续任务自动重新选路”。

## 当前结果：网关第四轮与原 R/I 交付已通过

第四轮真实软件彩排在 I 精确入口 `7c0bb6a2f7b39a7eb524c0c71bc31c7a110f883c` 完成：两个 HTTP 200，新坏样例各 0/3→3/3，builder#0 两任务间下线、builder#1 执行并采用 Gene，τ=10 秒衰减与归档不可检索通过；合计 2,235 tokens，费用未知。双视口全部 20 幕、29 原件不变性与 21 个衰减采样审计通过。200 tests / strict53 / 构建分发及 7c0bb6a 精确双平台 CI35703445239 通过。项目 OpenCode 配置已加入 7 个备用代码模型并通过隔离解析/枚举，真实开发工具调用仍未验收。

原 R 分支 `songconmaisaix31-design/morph-rehearsal-runtime` 的 `94b70816784fcd46ce4f74b8e205bd009b789cc3` 已推送，无领域返修；I 分支 `songconmaisaix31-design/morph-rehearsal-integration` 最终报告 `61784b73be6b2a47a3a45f8e206678d4f932ae59` 已推送，协调者以 fast-forward 接收，保留完整历史。后续主线仅补治理验收记录，业务源码与双平台 CI 通过的 `7c0bb6a` 相同。原 live 7526 viewer 已核验关闭，观察父进程 exit0；新 7526 由协调者运行明确 replay 的只读回放，未来清理须重核身份。此前原三轮和第一轮 7525 回放未重跑或修改。详见 [验收记录](ACCEPTANCE.md)。

R 当前派发 `ctx_232e8907f456` 与 I 当前派发 `ctx_3dc412a2eeef` 均已 succeeded。验明交付后分别 worker-release，均返回 retained / external_terminal / processAction=none，随后 ACK；保留原会话，不强关用户终端。

### 本轮恢复与准备过程（历史）

用户本轮已明确批准提交推送、集成复验和第四轮彩排，解除下文历史“待授权”阻塞。R 原 Task 重试派发为 `ctx_232e8907f456`，terminal 仍为 `term_52058249-adb8-426c-a996-5849cc5afa5d`。I 原 Codex 会话 `01a0c788-7734-7993-ba6c-77dd6f208d20` 已通过官方 resume 恢复，新 terminal `term_ca34dd06-6100-49c6-a43c-0511245b1852`，正式任务 `task_7cd7ff6071f2 / ctx_3dc412a2eeef`；旧终端确认 Codex 已退出至 PowerShell 后仅清理空闲 shell。分支、工作树和所有候选未替换；必要命令逐次按用户授权处理，不写永久允许规则。

R 已交付 `94b70816784fcd46ce4f74b8e205bd009b789cc3`，原分支已推送且工作区 clean，71 项回归通过；精确提交的 Ubuntu / Windows CI 35701298167 均 success。I 已收到精确 Handoff，继续集成审计/观察器/启动配置及项目 `opencode.evomap.json`；本轮真实网关 POST 仍为 0，等待完整集成复验后执行。R 保留领域返修所有权。

### 以下为授权前的历史阻塞（已解除，不代表当前状态）

用户已明确要求切换至 EvoMap 网关并继续第四轮；当前范围与文件所有权以 PLAN 的网关章节为准，替代此前仅整理未提交草稿的阶段限制。原 R 会话已复用为 `task_da11b736e4e5 / ctx_71b6412cc572`，terminal `term_52058249-adb8-426c-a996-5849cc5afa5d`，原 worktree/branch 不变。旧草稿任务按未完成如实结算；没有把旧证据或一次网关连通请求计为第四轮。

R 已通过本轨私有 TEMP/TMP 与独立 pytest basetemp 运行时间竞态测试：7 passed；网关定向测试 33 passed，相关 11 文件与全包 53 文件 strict 通过。T2/固定验证器/拓扑回归为 69 passed / 2 failed：旧 Codex 停止测试的 taskkill 被受限沙箱拒绝，最小自有子进程诊断亦为 exit 1 / Access denied，不能记整体通过。未因此修改旧业务停止策略。

原 I 的同一 Orca 二进制绝对路径访问也返回 Access denied，正式集成尚未开始。已向用户询问本项目必要命令权限，尚未收到明确答复；没有保存前缀允许规则或修改全局权限、账号配置。第四轮新增真实请求仍为 0，尚未运行，不能用旧三轮或 MockTransport 测试替代。

R 正常 `git add` 也被拒绝创建 `.git/worktrees/morph-rehearsal-runtime/index.lock`，退出 1 / Permission denied。六文件候选尚未暂存、提交或推送；原 R 分支仍指向 `652e3199d626f60b414b70ee523b5f9703d1e539`，这不是网关候选 SHA。代码、测试和精确命令结果保留在原 worktree 的 [R 报告](../../workspaces/Morphogenesis/morph-rehearsal-runtime/docs/tracks/rehearsal-runtime.md)。

I 旧任务的提权请求由协调者以 Escape 取消，未批准，不代表用户拒绝授权。终端与 transcript 均确认该回合已 interrupted 且未发送 worker_done；随后公开 `worker-abandon ctx_44c3b8728ee5` 返回 abandoned / processAction=none，保留原会话、分支与报告草稿。没有按陈旧状态强关进程，也未把无法结算的旧任务报告为成功。后续获准后仍使用原 R/I 所有者。

R 于北京时间约 15:24 以 `worker_done / failed` 如实结算 `ctx_71b6412cc572`；协调者验明六文件候选与报告后执行 worker-release，返回 retained / external_terminal / processAction=none。消息已处理后 ACK，reclaimable 查询为空。R 会话与未提交文件保留，不把未交付候选或关闭的派发当作项目完成；后续仍需有限项目命令权限、原所有者提交/推送、原 I 集成复验及第四轮真实软件彩排。

## 本轮结果：三次完整软件彩排已通过

收尾复核：主线 `c1542b2` 的 Windows/Ubuntu CI 35691937011 均 success，但较早候选 `e83a816` 的 Windows CI 35691719303 暴露 `tests/t2/test_rehearsal.py:81` 的时间竞态；后续偶然通过不消除该问题。原 R/I 会话通过 Orca terminal 内 `codex resume --last` 恢复到原 worktree/branch，任务分别为 `task_78d3e30ecafd / ctx_76c264a284f2`、`task_0abdacc8d0ba / ctx_44c3b8728ee5`。恢复时 CLI 使用受限沙箱，Orca 通信与共享 Git 元数据访问需确认；当前仅授权范围内准备返修，未将新修改宣称为已验证或推送。

2026-09-22 用户新增固定演示全链和至少三次完整彩排，旧三次单任务证据不计入本轮。主线已接收并验收集成 `e83a8168a066a0c687a15a7d28c15739bab13ad6`。北京时间 13:23–13:30 顺序完成 manual / auto / auto，共 6 次真实 CLI / 87,133 tokens，费用未知。每轮两个新任务 3/3、下线改道、Gene 生成/采用/墙钟衰减/归档全部通过。Orca Run `run_2cdbc98915f7`，协调 terminal 沿用原身份。

| 轨 | worktree / branch 后缀 | 实际模型 | Task / Dispatch | terminal |
|---|---|---|---|---|
| R | morph-rehearsal-runtime | gpt-6-astra / xhigh | task_3ca8b0ded0ae / ctx_bee3929001e7 | term_1fa7a0dc-6e17-4c96-9835-0428cf455e07 |
| V | morph-rehearsal-viz | gpt-5.6-terra / high | task_d91042ca5a85 / ctx_e028b3a23be7 | term_ffa1e302-b8ed-43c0-bae6-fcc662233d0c |
| I | morph-rehearsal-integration | gpt-6-astra / high | task_6bf332fa1437 / ctx_0887e4fb6588 | term_1eee9d49-ded9-441b-b7c8-406b5692b797 |

R/V worktree 从 `791d3cf` 建立；最终领域提交为 R `652e3199d626f60b414b70ee523b5f9703d1e539`、V `80220c5481e64fa197a679a7ec2ea466b6306af6`，集成 I 从 `501c491` 建立，最终为 `e83a8168a066a0c687a15a7d28c15739bab13ad6`。全部 commit + push，三个模型均经 effective 回执确认。主 Agent 只合入候选和维护治理文档，所有显示/类型返修都由原 V 完成。

158 tests、全包 strict 52 文件、SDK、构建与安装后资源检查通过；三轮实时双视口截图和最终 UI 明确 replay 的实际绘制边界检查通过。最终显示修复没有重复模型调用或替换旧 live 图片，证据边界见 [本轮集成报告](tracks/rehearsal-integration.md)。用户补充模型提供方与清单后，约 14:12 完成 EvoMap Gateway `https://api.evomap.ai/v1` 的鉴权和 Luna 一次真实短文本测试：均 HTTP 200，返回 OK / 15 tokens / 4813 ms。模型目录共十项，含额外的 Terra；完整 ID 与证据边界见 ACCEPTANCE。凭据未进入代码、命令参数、验收记录或 Worker prompt；尚未改演示执行器，物理投影接线仍 NOT_RUN。

第一轮 R、V、I 均已 worker_done / succeeded；三个 worker-release 均返回 released / closed_agent_terminal，transcript captured。三个无任务启动 PowerShell 已单独核对关闭。集成自有 7520–7524 服务和临时页面已清理，独立浏览器均正常关闭。原 7525 服务实际随 I 的 release 退出，原先“独立隐藏进程可保留”的判断已被否定。协调者已重新启动 [7525 只读回放](http://127.0.0.1:7525/)，核验 launcher 65808 → listener 57100，HTTP 200、mode/provenance=replay、current.stage=completed、task_live=not_run；日志位于 `%TEMP%/morph-replay-coordinator-983d9f27fa08480a9c1836c25c9dbb64/`。这不是新 live，也不承诺跨 Orca/系统退出常驻；端口空闲后按报告中的 replay 命令重启。原始 TEMP 证据、分支和 worktree 保留。

## 已完成的核心原型基线

八个功能轨及一个独立集成轨已交付核心原型。通过 Orca CLI 多开，按难度分配 Astra / Terra / Luna；领域返修仍由原 Worker 完成。主 Agent 只维护计划、状态、决策与验收，接收集成结果，不写业务代码。

- 主线：`codex/morphogenesis-mainline`，已接收集成候选 `b6bb49c3112a12f3c0bdcddbddbf2dde453be2e6`，最终状态/验收记录随主线提交推送。
- 初始仓库 `117fdde` 仅 LICENSE；用户 ZIP 原文在 `docs/source/`，保留 Apache-2.0。
- 功能：LangGraph 执行/独立复核/接续；反馈拓扑选路；经验正文注入、采用、衰减和本地归档；官方 GEP SDK/MCP 桥；受控本地 Hub 适配；ECharts 实际事件展示。
- 最终验证：149 tests、50 文件 strict、sdist/wheel 与 11 包安装检查、真实 Chromium 页面检查通过；Windows / Ubuntu CI 见 [验收矩阵](ACCEPTANCE.md)。
- 三次真实模型任务通过：正常/接续/复用，3 次 CLI / 43,166 tokens，费用未知。远端 Hub、动态供给、硬单次模型费用上限与正式现场演示仍有限制，不能宣称 G0–G5 整体通过。

## 分轨提交与身份

worktree 根目录 `C:/Users/DW/orca/workspaces/Morphogenesis/`；以下后缀同时是目录名和分支后缀，分支前缀为 `songconmaisaix31-design/`。所有精确领域提交已合入并推送，历史保留。

| 轨 | worktree / branch 后缀 | 实际模型 | 最终领域提交 |
|---|---|---|---|
| T0 地基 | morph-t0-foundation | gpt-6-astra（继承） | cdc8972ba0a711cb3b06bd36bdea516807430a8e |
| T1 协议桥 | morph-t1-adapters | gpt-6-astra（继承） | adca7f69183669f70135ead9e043aa5b70a8b876 |
| H Hub | morph-hub | gpt-6-astra / high | 07636c17f95a24dd0fbd37dbdf050cb6a26ca496 |
| P 供给 | morph-provision | gpt-5.6-luna / high | 1c4e5e9013ef08bbb50cbf20c11eb0119960c42e |
| T2 执行 | morph-t2-runtime | gpt-6-astra / xhigh | 33ed929d2065db8a00d46f679d27ba09d950d13a |
| T3T 拓扑 | morph-t3-topology | gpt-5.6-terra / high | a12d288a6505c1c098d85cbfd231a708e9b59342 |
| T3M 代谢 | morph-t3-metabolism | gpt-6-astra / high | 240aaf0f985ec3d374e07a25b3969650698d0aee |
| T5 展示 | morph-t5-viz | gpt-5.6-terra / high | 9ae01cf6428d04ed365ad778f4b3436d35d536ba |
| I 集成 | morph-integration | gpt-6-astra / high | b6bb49c3112a12f3c0bdcddbddbf2dde453be2e6 |

Orca Run：`run_3cac02602e7c`；协调 terminal：`term_263319ac-dfa1-4ff3-8463-7fe200fad470`。

| 轨 | Task | Dispatch |
|---|---|---|
| T0 | task_3bdb79633de5 | ctx_177ee63228f3 |
| T1 | task_b92657a452bc | ctx_c6e4d813fcc6 |
| T2 | task_c03f393208dd | ctx_0f54173a063d |
| T3T | task_9c35a6fd3bee | ctx_ed1ee9f3817e |
| T3M | task_beb94df50bac | ctx_31f926047197 |
| T5 | task_f37cacf4910a | ctx_101b31af0af0 |
| H | task_89da8e623a87 | ctx_a2be7a533175 |
| P | task_9ae1f6f71a6d | ctx_a408002966fe |
| I | task_c465399ce327 | ctx_90a1c3ad0fa9 |

P 最初 Task `task_509a8b88e115` / Dispatch `ctx_8e1f19911c90` 在原 terminal 立即续接返修，最终以表内 dispatch 结束。集成 terminal 为 `term_81b5bbf7-efd6-4285-8269-8e98919eb912`。

## 结束与资源处置

九个最终 Worker 均已发送 worker_done / succeeded。P、H、T2、T3T、T3M、T5、I 的 worker-release 均返回 released / closed_agent_terminal，输出归档 captured。T0 / T1 的 worker-release 返回 retained / external_terminal / processAction=none；这是 Orca 的外部 terminal 所有权限制，未绕过该限制强关。

T5 与集成 Worker 已逐一核对并清理自有预览进程；协调者复查 7500 / 7501 / 7502 / 7510 均无监听。浏览器截图及本地日志保留。

未重启 Orca 或操作其他项目进程；Git 分支、worktree、原始真实任务和本地验收产物保留。集成没有新增模型调用或外部 Hub 发布。详细命令、早期失败与修复及证据边界见 [集成报告](tracks/integration.md)。
