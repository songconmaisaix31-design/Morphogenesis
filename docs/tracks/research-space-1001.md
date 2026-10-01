# B 科研空间原 Owner：1001 窄 Handoff

本阶段是正式三角色闭环的准备交付，**prepared，不是 task_live 通过**。

- 原 worktree：`C:/Users/DW/orca/workspaces/Morphogenesis/morph-research-space-0930`。
- 原 branch：`songconmaisaix31-design/morph-research-space-0930`；原 Owner 不变，不创建其它 Agent/Run。
- 已读当前 AGENTS 与 `morph-research-plan-1001/docs/RESEARCH_NEXT_PLAN_1001.md`，clean 后从 `970fc530539c85d25b01096bf5001b5f4262554c` ff-only 到 `c45888f64c1cec60e5f9df45677b6547c4527cac`。
- 写路径仅本文件与 [正式闭环 Handoff](../research/FORMAL_CLOSURE_HANDOFF_1001.md)。领域代码、集成测试/断言、其它轨道文件和旧运行产物不改。
- 薄 Handoff 已发主控转 P/I：`msg_784e9338eee8`；主控授权直接发 P 后，字段交接 `msg_8e55cab278d1` 已送达 P 当前 dispatch。新 dispatch 的定期读信/heartbeat 正常；没有复用旧 Dispatch。

## 已完成

核对全部11公开MCP工具的实际参数、租约/身份边界、canonical `attempt_id` 与当前token、原source/current observation身份区分、复现批准原candidate的流程、第三角色主动检索/一次fresh本地再验证/生成child/静态文件门禁/实际apply/既有ConsumptionExecution及AdoptionReceipt链。完整字段和不可替代的原checker验收点见 Handoff。

读旧唯一案例只用 JSON、SQLite mode=ro/query_only，不手工claim、不修改权威DB、不初始化领域Store/Ledger。确认作者completed/token3、known实验source2/Attempt2、原静态TimeoutExpired报告保留、Claude401未claim、第三NOT_RUN、无approval/consumption/adoption；旧runtime3600已到期。公开claim在过期runtime门禁拒绝，因此不能延长/重置旧窗口补成旧案例通过。建议 A/P/认证就绪后由 I 开明确命名的新完整受限正式案例，保留旧全部红/身份/归档；没有执行新案例。

## 轻量验证

使用锁定 CPython 3.12，进程环境 `OPENBLAS_NUM_THREADS=1/OMP_NUM_THREADS=1`。标准库只读脚本抽取原 checker 的 load/events/native_calls/fraction_check 原函数，不执行 checker.main：

- 原known作者实验Fraction重算所有1001输入/residual通过，exact_mean=50000001/5、exact_variance=1/100；原remote_effect known、cleanup destroyed、usage/cost=null保持。
- 同作者原生UUID四阶段一致；resume旧token renew/合法submit两拒绝都在freshclaim之前；local-completion无实验/发布/批准/应用调用。
- 原author累计602.586241秒/36工具；原runtime3600、attempts3及过期状态、复现/继承尚available的事实核验通过。
- 专项exit0，模型/沙箱调用0；未执行原全checker、全量pytest、模型/Hub、认证变更、沙箱创建或旧实验重跑。

文档检查：`git diff --check` 和 `git diff --cached --check` exit0；57个首引用定位在原源码行范围内，只有两授权路径有变更，原 checker 与 c45888 字节一致。提交/推送完整SHA通过新Handoff回传。提交只含两文档，不宣称新工程门禁或live通过。

引用检查脚本首次使用 Windows 默认 GBK 读取 UTF-8 文档，实际 UnicodeDecodeError，未修改任何业务或运行证据；仅将该只读脚本读取编码明确为 UTF-8 后按原引用/路径/checker 不变断言核验。原失败保留在本条记录及终端输出。

## 真实待完成

P 在新产品正式CLI中承接11工具白名单/只读原生权限/HostConfig/启动归档，冻结核心完整SHA；A完成自有进程树回收修复；主控解决Claude认证身份选择；I冻结后按完整原checker实际执行新三角色、真实中断接续、独立复现和实际继承采用。B后续领域返修仍由本Owner负责，具体源码缺口先Handoff取授权。本阶段未证实需改领域代码的新bug。

## 接续：冻结正式产品独立审核

新Task task_2077dc5da4e7 / Dispatch ctx_c027aae6f986，不复用旧生命周期消息。审核P `9dd4addf4a141a42040574fef3b614ca62b22a57` / core `cbc4dede782eb79b9c007520d96d7958857da0af`；写路径只允许 [正式产品审核](../research/FORMAL_PRODUCT_REVIEW_1001.md) 与本track，所有代码/锁/测试/checker只读。root已明确新正式案例采用现存Claude官方OAuth，此决策更新此前准备阶段的认证待定状态，不假装用户已回答可选偏好；真实OAuth empty-env/currentmodel仍NOT_RUN。

按冻结git show/archive审核实际entry/权限/完整三角色prompt/恢复/TTL/预算/unknown/前序依赖/静态门禁和原adoption链。结论是静态契约及有限本地核验未见必改阻塞，prepared，不签interface_live/task_live；原checker CBC/c458同blob39948d9615bce07b40b96eeaf5dfb263b993c6d3。薄Handoff已向主控msg_46378c646e94和I msg_97d1c07799aa发送，个别近邻行定位在最终报告纠正。

独立4个已有专项 `python -m pytest -q -p no:cacheprovider --basetemp=<B-review>/pytest-bounded <four exact nodes>`：4 passed/1.58s，非全产品/全库；正式installed morph-research version/doctor exit0（仅原SDK本地操作）。只读现有P inspection身份/权限与prepared状态，7条Node原lock记录完全一致；13模块/资源仅archive CRLF与wheel LF差异、Python AST相同。逐字节比较首AssertionError和一次Windows rg wildcard error123保留在报告，未改业务/测试/原checker来消除失败。B没有重新安装/修改P venv，I独立fresh安装与全量core门禁仍归I。

模型/API/沙箱/Hub/EvoMap调用0，旧案例/认证全局状态不动。新research-formal-1001-01等待root release后I正式三角色全原checker；后续领域返修由原Owner经授权负责。文档commit/push及remote/clean完整SHA由本轮Handoff回传。

## 阶段3：受信案例桥接（1002）

当前 Task `task_ee0b6f8ea056` / Dispatch `ctx_12f73e32dbfb`，沿用原 B Owner/worktree/branch。先 READ_ONLY_PREPARE；收到 root `STAGE3_BRIDGE_WRITE_RELEASE` 后才 ff-only 消费 C 固定接口 `789181538c694d8677297b0e0bdfbf879bcc8138`。完整来源、门禁、首红及接续见 [受信案例桥接报告](../research/REGISTERED_CASE_BRIDGE_1002.md)。

元数据 SOURCE `b74fb531df9f3b68686aad9865f780fd78a32bde`；最终领域 SOURCE `5fb0cee3753b5169856f7ea8e0490c2daa2bad4f` 正常 push、remote exact、clean。仅 own case适配/注册案例契约测试，加 root 授权的 Windows Git timeout fixture；TaskLedger、生产 Git helper、C 科学实现、A WindowsJob、锁和原 checker 不变。C 最终08b测试收尾由 I 集成，B 不追逐其它 Owner 源码。

准确5fb归档本地相关范围197PASS/240.99秒，strict8通过；全新copy安装的7文件Git/wheel/site字节一致且nlink1，两installed seed CLI exit0、每例仅3项未claim任务，无实验/批准/adoption。原默认hardlink安装13/14首红与15未发布未测试草稿保留，未放宽no_links。Git fixture保留实际timeout0.2和总<3原断言，计入完整READY准备；复用专属WindowsJob在原断言之后回收实际自有句柄，无附着会话误杀。

root已接受领域SOURCE并放行I消费C08b+B5fb；本报告为prepared/contract_local，原生模型/API/OpenSandbox/Hub/真实科研adoption均NOT_RUN。I负责最终累计冻结、独立安装、完整双平台及root授权的两案例三角色live；旧红/unknown/clock/原checker不改。REPORT仅本文件与桥接报告，准确提交/remote/clean由收尾Handoff回传；后续领域返修仍原Owner负责。
