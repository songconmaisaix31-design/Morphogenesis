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

## 后续候选与部分 L1（01:28 追加）

Q 精确 B `a322cfd53f5c330654e19a6add8438a3f8c5fab4` 首批 16 项为 14 passed / 2 failed：缺失或杜撰 probe proof_ref 可复用无关探针。随后独立新增 2 项审批 passed 与冻结 manifest 字节篡改、3 项 SDK 网络策略/合法镜像/direct-create 负例均 RED；均退回 B，不赋予隔离或实验可信 PASS。SDK 测试在调用前使用 sentinel 截断，未访问真实沙箱。

Q 精确 C `40011761c3cce6513bbeef776543740f60d1d03e` 首批 13 passed / 1 failed：假 observation 缺原 ledger 执行仍被当独立复核。新增 failed/unknown/unknown-effect 复核 3 项 RED；有效独立复核正例通过。Owner 新交付 `3161048c463b3aa4f434054755afc9787bbda989` 待 Q 归档重验；B 动态可信结果到 C 的薄转换和 A 实际下一推荐尚未验收。

F 源码 `124a71af513cfadf096c6e7f55b7be1be2f913ac` / 报告 `bc2a8ec4c505a680a847221b3950b22609e19cb5` Owner 已推送：当前三页旧+R1 回归 88 passed / 2 installed skipped，另以 fresh 非 editable 私有安装运行同源真实本机 HTTP 页面 2 passed；现有输入 HTTP 6 passed。未截获接口伪装真实 HTTP，执行后端仍明确为 mock。首次 hardlinked_path 拒绝、错误 selector、mock 时序失败、Node OOM 均保留，修复使用 COPY 私有安装及正确 selector，不弱化安装/业务不变量。该证据仅覆盖现有产品输入及安全状态显示；动态任务分支、候选冻结评价、复核和贡献关系尚待核心 DTO，AT16 总体仍未通过。

P 撤回八阶段新调度/伪造 mock accepted 的 WIP 只证明错误方案已移除；不能据此标 native 自主闭环完成。A 修复诊断和 P 局部输入通过均须对应最终交付重新验收。全 R1、最终安装组合、实际隔离探针及 L2/L3 科研仍未通过/NOT_RUN。

01:29 Q 交付 C `3161048c463b3aa4f434054755afc9787bbda989` 精确 git archive：`.venv-q/Scripts/python.exe -m pytest tests/integration/r1_security/test_c_feedback_boundaries.py -q --tb=short`，exit 0，22 passed / 5.11s。原伪造结果/复核、unknown、历史与 TaskLedger 负例，以及有效独立复核正例均保留并通过；原始输出 `tests/integration/r1_security/evidence/c-3161048-exact-boundary.txt`。仅接纳该阶段被测贡献边界，B 动态结果投影、实际下一行动与最终组合仍待验收。此前 C 首次 RED 不覆盖。

## 精确边界复验与接续（02:12 追加）

Q SOURCE `967c75a75196b3e4b8ec972ee504e658ff290b49` / REPORT `7ab8c4cf0bb3e24a4196b9847b850f6b5a330293` 已推送且远端核实。使用 Q 自有环境和 owner 精确 archive；原 conftest 禁止宿主启动候选及外网请求，保留有效输入正例。

| 源码与边界 | 实际结果 | 接纳范围 |
|---|---|---|
| A `7fc1e80845128080dfbcd5899aa9a09e37128753`；`test_a_host_boundaries.py -q --tb=short` | 26 passed，exit 0；重启前日志及恢复后复验均保留 | 项目/权限/来源/提议幂等与中断恢复的该阶段边界；不涵盖尚在开发的 generated/budget/advisory 接线 |
| B `d175f7e2f8c3ff41a1ac8a2a4958c68acf57e275`；原四个 `test_b_*.py -q --tb=short` | 21 passed / 8 failed，exit 1，20.45s | NOT_ACCEPTED；有效配置绑定、冲突 probe 和 direct create 仍失败；合法 SDK 配置正例待证实 |
| P `550e1d43b43a9b668d5255fd8f01d0a67c763c49`；`test_p_host_boundaries.py` 材料子集 | 5 passed / 4 deselected，exit 0 | 宿主允许目录、空拒绝、父目录和调用者 envelope 无法放大范围 |
| 同 P550；项目/来源服务子集 | 2 failed / 2 passed / 5 deselected，exit 1 | NOT_ACCEPTED；外项目仍可触达两个可信 callback，已退原 P，恢复后同断言仍 RED |

F SOURCE `36b8c0c9dfa400b3574af37a47508796dd5461d6` / REPORT `a1aee14f0b87e4cf1b0cce854f2d77ad23e72539` Owner 交付两视窗 24/24，加视觉修正后适用 2/2；该版动态候选、完整冻评价/复核/采用和实际安装 HTTP L1 仍待。旧 SOURCE124a 的 installed 2 PASS 不转移到新 SOURCE36b。

新增接线门槛：A/P 必须实际复用原 BudgetLedger 在稳定项目命名空间准入，跨 branch/run/resume 不重置，未知效果保留预留；C 只能从原账本/资产/归档与独立复核产生贡献及机会，不信任直接填入的 branch refs；FR02 本地代码快照须有界读取内容并提供行定位，metadata-only 不算完成。Owner 正在实现，不能以 schema/docstring/局部通过代替最终固定组合。

C 系统 Python editable 清理被自动审批在进程启动前拒绝（仅返回 `blocked by policy`），没有发生清理；主控明确禁止换工具绕过。C 用私有环境继续，原安装日志与只读 RECORD 清单、人工恢复步骤由 C 报告；未知旧依赖保留，不声称全局环境恢复。该操作限制与科研 L2 NOT_RUN 分开。

## 动态契约复验进展（02:29 追加）

Q 回执：exact B `e8e16a5b9e755a94f8587b76ba9fc288f218b8af` 的原29、输入/候选绑定8、合法SDK配置15，共52 passed / 2.41s。SDK正例捕获一次 SandboxSync.create 调用，未访问真实后端或执行候选；不证明隔离实测。B 后继 d0c834f 的 host mock 原采用链尚待独立重验。

exact P `cedbf3bc52eaabd4814e43068428e89a49ab5cf9` 独立12 passed / 3.17s（原材料/项目/回调/笔记边界与合法正例），证据在 Q SOURCE63fe5ea/REPORT29cb3f0。Owner 的材料18通过另计；此处不证明正式factory、PDF实际安装、native或动态实验闭环。

exact A8fc 新37项首结果35 passed / 2 failed：旧合法MCP任务缺 project payload、休眠重开fixture引用不存在note；Q将绑定实际持久项目/来源再跑，首失败保留，原业务断言不削弱。C99cd旧advisory新增7项首6 failed / 1 passed（杜撰/外分支/错误轴/重复/更正后来源）；C d7e561f Owner29通过，独立复验待。B d175输入8项首7 failed / 1 passed 同样保留，不能用后续52 PASS擦除。

F8e93738 的 build 3906 modules / 15.66s，聚焦两视窗8 passed / 9.2s；Owner实际查看1366x900和390x844截图。只接纳被后端返回的来源定位/多版本/缺失状态展示，不推定 P 真实导入已支持多版本；P import_source按kind+identifier吞并新版本和意见不同适用条件问题已退原 P 并交 Q。新 F8e 的 installed HTTP L1尚未运行。

剩余验收重点是同一组合的正式 configured product/身份MCP/native发现认领、生成候选到可信评价与独立复核、接受证据改变下一实际选择、原消费与采用、完整成果包与三页真实HTTP。所有Owner/独立Q/最终I各自证据须标来源和范围；AT07真实隔离探针、L2研究及L3效果研究仍NOT_RUN。

## 完整候选与归档继承返修（02:46 追加）

Q SOURCE71c4642 / REPORTac4b150精确阶段结果：A8fc的37项在仅修合法项目/note fixture后37 passed /13.49s；首35/2保留。B e8 52通过；C d7e原29及新generated12通过，首40 passed /1 failed为fixture试图写不可变SQLite而提前拒绝，修为断言拒绝后12通过，原失败保留。

Q SOURCE5fc892c6af5a749f8d7356fda613f98c2005846a / REPORT211c50422ec381a057773f15e1dc84d8986d3c86保存真实缺陷：B56的原mock消费/apply/adoption正例通过，但原output/evaluation/environment篡改后仍可继承的3个负例失败；Pced资料版本/内容/解析与意见适用条件9项为7 failed /2 passed。各Owner返修，旧日志不覆盖。

Q 最新SOURCEfff315b / REPORTbf5be87精确验收：B2d 68 passed /10.28s（含原始证据复查、host判据重开、应用前后回滚）；C4f 45 passed /11.80s（含原始来源与review locality、真实有效独立复核）；Pf006 + A8fc 21 passed /4.33s（原12访问边界+9资料/意见身份）。均为受控fixture边界，不执行候选、真实SDK沙箱或模型。当前B5faa后继与A0bcb完整正式入口须进一步验收。

P f006+A8fc 的私有非editable安装37通过只涵盖配置/HTTP/MCP/资料阶段。B静态危险输入compat首244 passed /1 failed、A缺Node依赖首51 passed /24 failed及P安装源码比较器的旧root布局误判都作为原始结果保留；后续新结果分别记录。未完成的安装/stdio/完整研究DTO/三页与最终I检查仍不赋予PASS。
