# 2026-10-01 Agent 协议与正式科研产品：一页执行计划

事实源为本轮用户任务及 docs/source/README_包内说明.md；用户最新指令将本轮限定为“最终正式版本上的两品牌、三角色、一次真实成果继承”。扩大Agent兼容范围和抽离通用科研案例须在完成后另行决定，不因检查通过自动启动。EvoMap协议开发继续后置。原冻结交付 c45888f64c1cec60e5f9df45677b6547c4527cac，业务代码 bde3412d2257fd1581ce1d7f88b254fb0c13a269。主控只分发、决策、读取证据和独立校验，不写业务代码。

当前冻结核心CBC（cbc4dede782eb79b9c007520d96d7958857da0af）及产品4428fdadfb0a5dfe8adc9e04c7fd881784f2807e的工程/独立安装门禁通过。case04作者科学通过但Claude正式OAuth未登录、无Orca已选Claude账户；原完整checker仍RED，产品新冻结三角色尚NOT_RUN。只等待官方用户登录及准确新案例处置；不得提前放行阶段4或冒称原任务完成。详情见本轮验收记录。

## 原始任务与顺序

1. 继续复用 ORCA 各 Agent 接入的全部接口；盘点固定上游源码、版本和许可证，按真实支持情况逐项映射，不搬入桌面基础设施。
2. 先修进程清理：补父进程先退出的真实 POSIX 回归。科研权限、窄工具集、正式启动参数放入新产品仓库 Morphogenesis-Research；验收从安装后的正式入口运行，测试脚本只观察，不补关键权限/启动参数。
3. 冻结新核心和产品代码后完成现有作者→独立复现→文件验证/批准/应用→第三角色本地再验证→真实继承/adoption完整闭环，并运行原 tests/integration/check_research_live.py，不能以作者检查代替。
4. 历史后续方向为抽离案例数据、科学判定和候选模板、以第二类任务证明扩展，再扩更多Agent。最新用户指令将这些排除出本轮执行范围：第3项真实通过后先报告结果，等待用户另行决定；不自动派发C或D扩展任务。当前不做大量算法对照实验，不开发EvoMap协议。

## 互斥长期轨道

| 轨道 | Agent / Worktree / Branch | write_paths 与当前阶段 |
|---|---|---|
| A 进程清理 | 原 A / morph-research-agents-0930 / 原分支 | orchestration/native_agents/process.py、windows_job.py、_windows_exec.py；tests/native_agents/test_process.py、test_posix_process.py；docs/tracks/research-process-1001.md。先真实 POSIX 父进程退出/存活子进程回归，Windows Job/附着保护不退化。 |
| D ORCA 全接口 | 原 D / morph-agent-protocols-1001 / 原分支 | docs/agents/ORCA_PROTOCOL_MATRIX_1001.md、docs/tracks/agent-protocols-1001.md；现有盘点已完成，本轮不新增运行时兼容。若闭环出现实际协议阻塞，才由原Owner做窄诊断与Handoff。 |
| B 科研闭环 | 原 B / morph-research-space-0930 / 原分支 | swarm/research/**、local_assets/**、tests/research/**、tests/local_assets/**、docs/research/**、docs/tracks/research-space-1001.md；swarm/task_ledger.py仅具体必要修复另行批准。当前读现有链并给P/I窄Handoff，不运行native或实验，不自行开发案例抽象。 |
| P 产品入口 | 新 P / 新仓库 Morphogenesis-Research 的 research-product-1001 worktree/branch | 新仓库业务、测试、锁和产品文档；AGENTS.md、docs/PLAN.md、docs/DECISIONS.md、docs/ACCEPTANCE.md由主控独占。正式CLI依赖现有核心固定SHA，产品层拥有科研权限和角色流程，无第二套账本/调度器。 |
| C 案例扩展 | 原 C / morph-research-sandbox-0930 / 原分支 | 本轮不派发、不授权修改。闭环完成后是否抽离案例及验证第二类任务，由用户另行决定。 |

主控仅 docs/PLAN.md、本计划、docs/RESEARCH_NEXT_ACCEPTANCE_1001.md；独立 I 在 A/P/B 输入冻结后接续原 morph-research-integration-0930，拥有 tests/integration/**和自身报告、精确合并及最少配置胶水。I不得改原完整检查器的断言或让测试脚本补权限；领域问题退原Owner。产品最终集成使用独立branch，不覆盖公共历史。

## 运行、证据与资源

- 先启动A/D/B/P独立波；源码互斥、各自环境和sibling state，轻量专项可并行，BLAS进程局部1。全量工程验证及同一真实科研案例由I独占；所有跨轨修改走Handoff。
- 所有轨道先小型接口Handoff，再开发/测试/文档/返修持续同Owner，阶段commit+push。未知用量/费用保持null，未知远端效果不重试，secret及运行state不入库。
- 上一轮Claude实测DeepSeek gateway401；本轮用户全部授权下已明确选择正式产品Claude OAuth profile（治理3c859ff阶段），仅产品子进程屏蔽旧gateway两键并恢复，不修改全局账号/HOME/current model、不复制凭据，旧401保留。Codex继承既有选中身份及模型。已有案例到期或入口失败的原红和账本保留；新的正式验收窗口须明确新案例命名，不能重置旧案例来冒充通过。原角色、科学阈值、中断/同UUID恢复/真实TTL/合法陈旧提交拒绝及完整checker标准全部保留。
- 新仓库使用Python/Pydantic及既有官方依赖，固定核心依赖提交，private远端；保留根仓docs/SWARM_SOL_PLAN.md WIP。无main/tag/Hub发布、批量删除或全局配置/认证修改。
- 原完整checker及适用核心/产品门禁真实通过，只证明本轮闭环完成，不自动授权C抽象或D新增运行时；没有真实账号的接口明确NOT_RUN，不以几十个外围测试替代科研闭环。
