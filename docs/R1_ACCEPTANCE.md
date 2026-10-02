# R1 验收登记（2026-10-03，开发开始）

最新Spec第14节为验收事实源。本登记未赋予任何PASS；依据各最终候选源码与实际证据追加结果。首次失败记录在docs/R1_STATUS.md。

| AT | 验收对象 | Owner | 当前状态 / 所需证据 |
|---|---|---|---|
| 01 | 来源定位与回链、解析缺失 | A/P | NOT_RUN；原文页/段/行可到达，解析失败/摘要不伪全文 |
| 02 | 新成员有界上下文与接续 | A/P | NOT_RUN；真实正式入口重建共享背景，L2实例单列 |
| 03 | 发现/讨论产生新任务分支 | A | L0待测，L2未授权；非全部启动前写死 |
| 04 | 自主选择与可替换规划职责 | A/C/P | NOT_RUN；多个合法候选、覆盖理由、原TaskLedger最终认领 |
| 05 | 新候选版本非注册程序 | B/A/P | NOT_RUN；来源/修订真实，宿主没有执行候选 |
| 06 | 评价独立且冻结 | B | NOT_RUN；自报分数/阈值修改/隐藏数据/自批攻击拒绝 |
| 07 | 隔离有效 | B/I | 真实探针NOT_RUN/未授权；文件/网络/资源无害拒绝及自有清理证据，mock不算 |
| 08 | 有效反证获得贡献 | C/B | NOT_RUN；succeeded/refuted/accepted；crash/timeout/auth不反证 |
| 09 | 意见非事实、同源去重 | A/C/P | NOT_RUN；意见触发检查且不批准，重复来源不计独立贡献 |
| 10 | 可信反馈改变下一行动 | C/A/P | L0待测，L2未授权；解释下一推荐，实际研究行动引用证据 |
| 11 | 有界探索、休眠、重开 | C/A | NOT_RUN；越权/休眠无探索，历史保留，原因条件明确 |
| 12 | 独立复核 | B/A/P | L0/L1路径待测，L2未授权；不同成员、新run/sandbox与方法独立性 |
| 13 | 实际继承 | B/A/P | L0/L1消费链待测，L2未授权；新task再验证并真实使用，原adoption receipts |
| 14 | 故障与幂等 | A/B/C/P/I | NOT_RUN；迟到token、unknown、重复POST、反馈重读、进程/写入中断与重建 |
| 15 | 授权和数据边界 | A/B/C/P/I | NOT_RUN；项目总envelope跨branch/run不重置，支出/外发/新backend拒绝 |
| 16 | 三页可理解 | F/P/I | NOT_RUN；两视窗真实产品HTTP，keyboard/reduced-motion，三轴/采用与来源 |
| 17 | 来源与兼容回归 | 全轨/I | NOT_RUN；精确SHA/安装/依赖/报告，旧两例/v0.1/literal validator，历史快照保护 |
| 18 | 可追溯成果包 | A/B/P/I | L1待测，L2未授权；目标/来源/代码/环境/结果/复核/继承/负结论/局限 |

验收层分开：L0=确定性schema/权限/边界测试；L1=真实本机HTTP/MCP/安装/页面与可替换backend（mock注明）；L2=固定最终组合的授权真实研究；L3=同条件效果对照。本轮没有L2/L3结果，未参与实现的人工观察未测。

必须拒绝：按LLM文本/专家身份制造可信科学结论；候选作者自批；读取旧fixture充当新研究；因unknown改run/token重试；删除原等值安全检查启用动态；宿主运行候选或未经批准评价器；源资产PASS随条件变化继承；把查找/注入/释放写成adoption；把token限额标提供方账单硬封顶。

原固定阶段通过仍属于对应旧subject，新Spec不改写历史。旧类型错误只按基线身份登记，新schema/MCP/安全边界必须验证，不增加豁免。只据最终源码及实际回执标通过；阶段源码更新后适用重验，docs-only不触发收费科研。

## 首次独立安全验收（保留 RED）

Q 测试与原始证据提交 `6ceb2e2752979259be91415cf5a116df94e6aebd`，远端已核实。测试从明确 owner 精确 archive 导入业务代码；未导入或运行 B 的宿主候选 helper。可信 fixture 为预制输出，backend.create 用抛出异常的 sentinel；测试阻断宿主进程启动与外网连接。

| 待测源码 | 命令主体（Q 专属环境） | 首结果 | 处置 |
|---|---|---|---|
| A `48eeebd6c7fcfaf797d297ea5d73eb0673bddb46` | pytest tests/integration/r1_security/test_a_host_boundaries.py -q --tb=short | 14 failed / 4 passed，exit 1 | 项目越权/跨域关联/中断后 enqueue-bind 恢复等退回 A |
| B `fbee1e5edee5f5d0cb72141f511fdfc724633f69` | pytest tests/integration/r1_security/test_b_generated_boundaries.py -q --tb=short | 6 failed / 6 passed，exit 1 | 可伪造隔离/审批、unknown/failed/timeout 被信任等退回 B |
| C `71bfedbfd0cf4b6581f36cfdc70281bc877f71c8` | pytest tests/integration/r1_security/test_c_feedback_boundaries.py -q --tb=short | 3 failed / 8 passed，exit 1 | 无原 ledger/report 的任意结果和 reviewer 被接受、历史删除等退回 C |

Q 此后新增 B 成功 archive 缺 output.json size/digest 绑定的单项负例，也在同首版 SHA 失败；扩展测试尚未全组合重验，不能将其计为最终结果。Q 首次依赖缺失（faiss）collection RED 另存原报告。修复后的新结果将追加，不能覆盖此处。

P 首版 backend `80ed5e13351a9eab8b36ba03c710e98fd7544fcf` 为产品输入与未接入核心状态投影，尚非科研闭环：Owner 原基线 133 passed / 27 环境失败，仍需独立安装及完整适用回归。UI WIP `44353e35bc745b7542625b85376791b5ac68aa4f` 未 build/未 Playwright，已保留并移交 F；不赋予 AT16 PASS。L2/L3 和真实隔离探针仍 NOT_RUN。
