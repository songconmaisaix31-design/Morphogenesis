# R1 MVP 当前一页执行计划（2026-10-03 22:16）

业务事实源：用户Spec v1.0_2026-10-02（Downloads原件SHA AB73F60E26AF1BC1B44CA5DA9B94B2CFDDA91A5D4ACB25683B9386462DCFB165）与当前用户收窄指令优先。目标：三项Spec行为证据 → 固定离线组合 → 独立真实AT07 → 一次L2开放切片。当前没有完整MVP/R1/task_live成功声明。只用原Python/LangGraph/Pydantic/SQLModel/SQLite/httpx/MCP/GEP/ECharts技术栈和既有TaskLedger/registry/归档链，不造调度/Attempt/Manifest/proof框架。

## 当前轨道和互斥所有权

| 轨 | 原树 / 分支尾名 | 当前身份与唯一write_paths | 本轮交付 |
|---|---|---|---|
| B 原领域Owner | morph-r1-experiments-1003 | 原term_4ffcdc70；API Task8ecc/ctx370已done。仅generated.py、tests/experiments/{test_at07,test_frozen_export,test_generated_configuration}.py与own两docs已交；下一准备阶段仅docs/experiments/at07-authorization.md、docs/tracks/r1-experiments.md、新B私有证据 | API SOURCE c3a905eaf79a869dffb5960da9c4afee1dc63c3e；docs REPORT08f2315dbc6a2396c4b55dd07a6d60f6fd115dfa。下一仅原固定egress补齐 |
| Q 原独立审查Owner | morph-r1-boundaries-1003 | term_977c62ef，task_90f7d319dd74/ctx_9d2d8cbf6ca9；只docs/tracks/r1-boundaries.md与新Q私有证据 | 只读现有有效FW/NAT与API绑定、最小双栈端口packet；当前UNKNOWN/STOP |
| I 唯一集成Owner | morph-r1-integration-1003 | 原会话01a10119-cd06-7f40-a9fc-f6e46af64e7f已resume至term_cc6a6c31；task_6d13ed8377e3/ctx34ec首agent_readiness timeout未注入，短只读恢复实际Working后按同Task retry-of接续；只own docs/tracks/r1-integration.md、新C:/r1i/私有验收与必要少量导入/路由/类型/SDK胶水 | 普通合精确B SOURCE/REPORT与root治理，尽早发布唯一累计SOURCE；一次新SOURCE原CI，等精确P最终pin后一次新组合全产品offline与installed |
| P 原产品Owner | research-r1-product-1003 | 原会话01a10165-8eb4-7370-bb7d-da99cd19c66b待需要时resume；仅pyproject.toml、uv.lock、src/morph_research/__init__.py、own docs/tracks/r1-product.md | 只收到root接纳的I完整SOURCE才repin，不从REPORT取pin，不再安装/重复绿测试 |
| 主控 | morph-r1-control-1003 / research-r1-control-1003 | 仅计划/状态/决策/验收；不写业务代码。C用户协调会话只读跟进 | 分配原Owner、验收原始结果、保护历史和边界 |

分支均songconmaisaix31-design/<尾名>；仅上述原树，跨轨只Handoff。Codex GPT-6.1-Sol high YOLO；OpenCode余额阻塞不重试/改配置。普通merge/push，不cherry-pick/force/覆盖贡献；领域退原Owner。避免新增idle Agent、全局pip/auth/HOME/provider或大范围进程/文件清理。

## 已有工程基线与新差异

原离线接受业务core15de4959646df264530b978dfde9152552b9a76b + productc84e49bd8e926f50d2c057793e8789cf137b310a；TESTSOURCE756d5069e7739089f0e5ba1c33eebfb2657b03f0，I REPORTc5cdfc89e5a1e43ab49f9afc33a05a53d887e8ab，P REPORTeca3fd48c33fc602f1ddb3f45d91bd88e17b941b。原CI37123370202 attempt1：Win1825/15skip、Linux1824/16skip、strict140/build/SDK1.14/wheel通过；原全产品255PASS/1FAIL保留，test-only修后P及I各仅单nodePASS，不写whole256green。适用types30PASS、整包10原errors保留。UI126/8skip只按原范围沿用，人工未验。

B新差异：generated.py仅Literal1.52/1.54且默认1.52；三既有测试正负控制，旧98assert及at07_live/frozen_export/registry/锁/profile/compose原blob未变。B首6FAIL/29PASS/97deselected、修后131PASS/1FAIL（新mock漏provenance）、修该项1PASS、strict1source分别保留；不冒称132全重跑。I新累计SOURCE/pin/installed/全产品/原双平台CI尚待实际结果，旧SOURCE绿门不rerun。新组合生产UI零delta可沿用，但新installed原bytes/import/direct_url/锁与受影响API调用必须核实。新fixture/env/cache独立，第一失败/原报告不可改写。

三项已定位行为已有原Owner调用/测试证据：正证据路线作用、正式envelope跨片段接续、局部相关性在ResearchService.research_context完成；不重复造模块。只读Agent节点会话右击/键盘、输出轮询和当前上下文已实现，complete仅输出窗口读完。AOCI官方portable配置已交；15语义entries/维护与实际Token费用节省NOT_VERIFIED/UNKNOWN，非新增MVP业务门。

## 当前运行事实与必要准备

用户直接“我现在批准AT-07，继续开发”由root读C实际提交stream核实，原专项批准已接纳，不再重复问同一权限。原600s尝试UTC13:29:15–13:39:15已封存：Desktop一次Hidden启动；首Composeexit125/stderr内容MISSING；创建前STOP，SDKcreate0/infra0/registry0/其他项目启动影响NOT_ASSESSED。不reset/replay该尝试。

独立只读诊断：Compose5.1.4（仅加固定ProgramFiles locator）；LinuxEngine29.5.3/API1.54/min1.40/daemon6cc73c96-c021-4a82-ade6-2fc9ae693fff。固定server68ca/execd6cf7/python229a存在，egress原db7345缺失；公开OCI index/amd64manifest摘要一致，压缩layers+config132032785bytes，解压磁盘/增量UNKNOWN。

**主控现在明确授权单独镜像准备，基于用户授予的全开发权限与已审阅B08f packet：** 只原官方绝对DockerCLI、同npipe、全新核identity空ownedconfig、typed argv/shellFalse、仅三system childenv，一次image pull --platform linux/amd64 原opensandbox/egress:v1.1.7@sha256:db7345d567b0970f384b8e3fa7a93a71b7f43d4b16bb2009de34096e9a87b3b5，独立180s cap；先fresh同Engine/CLI/disk资源只读，缺必要条件STOP。完整exit/时点/secret-free原stdout-stderr分档，timeout/断连效果UNKNOWN不第二pull/重试，不prune/shared层清理/切源/tag/build/升级/auth代理修改/Desktop重启。只读核实际RepoDigest/linuxamd64；只同identity且仍空的ownedconfig精确rmdir。该准备不创建容器卷网/SDK、不是恢复旧probe窗口或科学执行。

Q现状：Backend宽ALLOW的实际用户SID1005与既有Codex BLOCK1007不同；声明旧server源码没有publish_host，固定镜像Labelsnull/revision UNKNOWN。当前动态0.0.0.0:47400..47410有效边界未证。只准备仅backend+InboundTCP/UDP+该range+双栈nonloopback补集BLOCK；拟允许127/8与::1，不猜gateway/privateCIDR/NAT源，不实际改FW/hostlistener/globaldaemon。原Q必须交exactruleIDs/apply有效核对/权限/未知与回收packet，静态方案不得称真实隔离PASS。服务proxy需要未批准源即STOP，不自动放宽。

## 下一验收顺序

1. 原I普通精确合入 → root接受完整累计SOURCE → 原P仅repin → 原I新私有noneditable固定组合一次完整产品offline、必要类型/affectedinstalled + 一次该新SOURCE原CI/buildSDKwheel；新RED退原Owner，旧绿不为blocker重跑。
2. 镜像准备与Q具体端口方案可并行；真实AT07仍待新工程与有效前提核验。每项变动/实际授权范围另记录，不默默继承原结束窗口，不以风险接受代PASS。
3. 一次专用无害真实AT07沿原SDK pause→只读EngineHEAD/GET→SDKresume，原5容器/1卷/0新network/一次SDKcreate/600s和fixed512MiB/128pids/30s/180s/1MiB范围。unknown不replay/第二POST；全部PASS与Q独立raw审阅、归属/cleanup/fullconfig接纳后才可注册probe与准入候选。仅条件已核的同64IDserver停止保留，删/重建/配置变化不继承。
4. 然后一次L2：问题和原材料给Agent，不给完整候选代码；记录实际新分支/代码版本/实验/独立复核/证据后续行动与至少一次实际使用；负结论可以。现阶段L2/native付费/外发/真实候选未授权执行。L3/大规模对照/多用户/跨宿主/完整RSI/新学科品牌语言评分/main/tag/deploy均不加入。性能实测照实记录，不变最优成绩收口条件；人工可配真实页面。

历史计划与所有首失败保持Git快照和STATUS/ACCEPTANCE/Owner原报告、私有raw，不再把全量历史塞进每次Worker读取：
[完整计划历史冻结于ab663f6](https://github.com/songconmaisaix31-design/Morphogenesis/blob/ab663f6/docs/R1_PLAN.md)；[当前状态](R1_STATUS.md)；[验收记录](R1_ACCEPTANCE.md)。
