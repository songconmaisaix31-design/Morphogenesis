# 1001主控状态与独立验收

Run run_e54c8f113bfd，主控term_bdbac2dc-861f-4ba9-af30-f44bd35cc2d7。只分发/校验，领域代码由固定Owner负责。A进程轨contract_local已交付并独立核对，B闭环契约prepared已交付；新累计工程与完整task_live仍未通过。

| 轨道 | Task / 当前Dispatch | 实际启动状态 |
|---|---|---|
| A原进程Owner | task_45acb7d726b1 / ctx_500e88b29bfb | 初始turn_start_unobserved保留；实际屏幕Working、live projection及合法薄Handoff正面证明正在工作，未重复派发。 |
| B原科研Owner | task_5790e2dea18a / ctx_3fabb5007d5f | ready/turn_started，旧Owner同worktree/branch接续，ff-only到c458；当前只做闭环领域Handoff。 |
| D协议盘点 | task_a8f3a68a0da7 / ctx_2ef7076320c0 | 前两次agent_readiness timeout、一次agent_unconfigured预检保留。原终端完成三个只读命令后，实际idle=true；同Task/同终端第三次ready/turn_started，未重复创建Agent。 |
| P新产品 | task_5bf5e462e8dc / ctx_a3726e1bd9d3 | 前两次agent_readiness timeout保留；完成只读诊断和idle=true后同Task/同终端ready/turn_started。 |
| I原独立集成Owner | task_461afacb0c18 / ctx_c6bb0ebb6ad6 | 原终端实际idle=true后接续ready/turn_started；核心工程验证与正式产品集成持续同Owner。 |

新private远端 https://github.com/songconmaisaix31-design/Morphogenesis-Research 已创建/推送bootstrap6c1451f5269ce8d7e2f92c8a794a691b41d8145c；仅AGENTS/计划/Apache许可证，没有主控业务代码。Orca repo27a06ff8-8398-4829-8e66-1aee6c5b89dc，P worktree C:/Users/DW/orca/workspaces/Morphogenesis-Research/research-product-1001 / branch songconmaisaix31-design/research-product-1001。

A运行源码0a192c6b037df0e70cedb17e8d2e8bfa28f0dd09，最终报告46a1282b148fd8e03e2df85cb80de90957d64921；主控实际ls-remote一致、clean、两提交生产/测试树diff0及相对c458仅3授权文件。真实Ubuntu WSL2/Linux6.6.114.1/Python3.12.3原5RED1.99s、同断言5PASS13.12s及4秒边界未放宽，主控读取原日志而非仅报告；Linux原native92pass/2skip、Windows原native89pass/5POSIXskip，strict两平台10文件通过。原WindowsJob/_windows_exec及其它领域未改。OwnedProcess仅新增兼容可选private_group，run_headless API保持，强制清理后代时usage/effect保守unknown/null；只私有组归属，脱离组daemon及OS孤儿收尸不冒充已清理。A合法worker_done succeeded已结算；release返回external_terminal/retained/processAction=none，供原Owner后续返修，未重派初始unknown启动。I独立门禁待结果，源码CI未先标绿。

B薄Handoff实际引用现有11工具链：独立复现verify→原候选validate/approve/apply；第三角色search→ONE fresh run→verify(inheritance)→inherit→child validate/approve/apply→既有Receipt。不同nativebrand由原完整checker负责核验；旧runtime3600已过期阻断claim，不能重置旧clock或移植audit来冒充同案例通过。已转交P，精确字段与可行正式验收方案待B最终文档。

B最终a060564dee6d7fa790b64583fd76301e95eadb54已remote一致/clean；主控实际相对c458只有两授权文档并读取FORMAL_CLOSURE_HANDOFF_1001完整公开工具字段/原checker要求/旧窗口只读结论。prepared只读专项不是完整live；模型/实验调用0。合法worker_done succeeded后release返回external_terminal/retained/processAction=none。领域真实缺口仍退B；新命名完整案例须先冻结产品/core并解决认证，保持原限制/角色/中断恢复/科学及adoption标准。

主控许可决策msg_3b4a8a9ba3be及对D/I同文：D固定官方rust-v0.159.0源码发现MCP resource helpers自动注册、apply_patch按模型能力注册；公开headless CLI/TS SDK没有可隐藏全部目录的allowedTools开关。保留这个曝光限制，不宣称总工具目录exact11、不改catalog/runtime/provider。主控实际读取原checker140–161：核验实际工具调用属于11科研工具、原read-only/never/per11approve/defaultprompt及Claude严格allowed11/tools-empty，没有模型目录总数断言。P继续正式入口，保留全部官方可用的禁用开关和单MCP权限；缺必要权限或任何真实越界工具尝试必须失败/停止并保留原红，不能隐藏/丢弃raw事件。此决策纠正未获支持的曝光声明，不修改原完整checker、权限、调用与效果标准；全部科研live尚未放行。

用户最新边界：EvoMap协议开发后置；并行按互斥文件路径提高效率，主控上下文以薄Handoff/精确SHA/原结果管理。原Claude401的认证身份选择已通过异步问题提出，尚无回答；不得据经过时间/默认选项切换账号/provider/model。完整三角色检查器和各阶段顺序均保留，当前native/实验尚NOT_RUN。
