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
