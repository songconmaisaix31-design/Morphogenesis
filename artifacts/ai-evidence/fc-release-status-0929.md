# FC 发布预检与 T10 状态登记（G，2026-09-29）

本次完成窄治理登记；**E 预检已交付，T10 实际失败，dsh 新评审 NOT_RUN，H1/H3 pending，FC BLOCKED、未冻结。** 只读接收证据，不执行产品测试、模型调用、安装或依赖动作，不代理人工结论。

## 身份与证据入口

| 对象 | 精确身份 / 来源 | 本轮接收边界 |
|---|---|---|
| G 本次 | `morph-fc-governance-final-0929`；基线 `669b191bf41d3fa42e2ab34a2c1fa68d53498f49`；`task_9830b76675be / ctx_9cd98d874e99` | 只改 TASKS 本轮附录、发布计划、本文；桌面 0929 只追加 |
| 共同受测代码 | `morph-fc-candidate-0929@c552250c0d07f5f70f09eb0a5ab3c322195e34ec` | I focused408/full862/strict87/build/SDK/分发六门禁是该 SHA 实跑；D `9a6705c7aeae9c812329c015f13e440842beff17` 的 47 focused / 九组 mutation 身份保留，G 本轮不重跑、不转贴为治理 SHA 结果 |
| E 已验收交付 | `morph-fc-release-preflight-0929@7347f5c1a7eaf0f5a3279c2db0ffb751a730792c`，父 `c1107b63911e44269b586a1252cb84836cdeacf3` | [预检与完整六阶段任务单](https://github.com/songconmaisaix31-design/Morphogenesis/blob/7347f5c1a7eaf0f5a3279c2db0ffb751a730792c/docs/FC_RELEASE_PREFLIGHT_0929.md)、[材料检查](https://github.com/songconmaisaix31-design/Morphogenesis/blob/7347f5c1a7eaf0f5a3279c2db0ffb751a730792c/artifacts/ai-evidence/fc-release-preflight-0929-validation.json)；G 用 git show 读取，远端 exact |
| G 原 dsh 预检 | `669b191bf41d3fa42e2ab34a2c1fa68d53498f49` | [原报告](https://github.com/songconmaisaix31-design/Morphogenesis/blob/669b191bf41d3fa42e2ab34a2c1fa68d53498f49/artifacts/ai-evidence/review-0929-v41flash-report.md)：认证 BLOCKED、请求 0、submitted=false、实际返回模型/usage/cost=null、review NOT_RUN、FC-E OPEN；旧 R1 REJECTED 不改 |
| T10 原生宿主 | `task_5a07cc5ef0f5 / ctx_f5dfba4a52b3`；主控结算消息 `msg_907887d81683` | 主控已验收失败并 release；下列本地证据由 G 只读核对，不复制或提交原生运行产物 |

E 在原预检时记录：真正 FC 目标为 `decentralized-swarm@73798cd6f05210f2bd9b1eebfd6f9f0dd6e842db`，目标到 C552 可快进（0/44）；本地/远端无 demo-build tag；两次只读 merge-tree 无文本冲突。11 份旧回放解析为 replay、interface_live/task_live=not_run，59 树及 refs 当时未发现 T10。G 引用该快照，未重新盘点；主控一次 remote TLS 失败后只读重试成功，原失败不改绿。E 没有运行三连、正式演练或 live。

## T10 失败事实及授权边界

前一次 Orca `--agent qwen` 前置拒绝 `agent_unconfigured`，无 Task/树/终端；之后单独建立原生 Qwen CLI 宿主，Codex 只负责启动和核验。当前树 `C:/Users/DW/orca/workspaces/Morphogenesis/morph-fault-drill-0929` 已普通改名到 `feat/fault-drill`，HEAD 仍 C552、工作树 clean；这不是新的实现提交，也没有 push。

只读证据：[宿主报告](C:/Users/DW/orca/workspaces/Morphogenesis/morph-fault-drill-0929/.runtime/fault-drill/report.md)、[原生退出码](C:/Users/DW/orca/workspaces/Morphogenesis/morph-fault-drill-0929/.runtime/fault-drill/qwen-native.exit.json)、[原生 JSONL](C:/Users/DW/orca/workspaces/Morphogenesis/morph-fault-drill-0929/.runtime/fault-drill/qwen-native.stdout.jsonl)、[结束检查](C:/Users/DW/orca/workspaces/Morphogenesis/morph-fault-drill-0929/.runtime/fault-drill/final-checks.json)。这些是本机 ignored 证据路径，不是 GitHub 可下载附件。

| 原生事实 | 结果 |
|---|---|
| CLI / 唯一 session | Qwen `0.24.6` / `45763f00-a28a-4a98-a800-06b82fba27bb` |
| UTC 开始 / 结束 | `2026-09-29T12:39:06.9704879Z` / `2026-09-29T12:39:13.0913945Z` |
| 原生 exit / 错误 | **1 / No auth type is selected**；`error_during_execution`、`is_error=true` |
| 原生 CLI 元数据 | `num_turns=0 / duration_api_ms=0`；不把 CLI token=0 记作 provider 实测 usage 或零费用 |
| 认证 / 模型 | 宿主报告标准用户/本树 Qwen settings 均不存在；没有认证，默认/实际生成模型未证实，provider usage/cost 均 unknown/null |
| 产品文件 / 测试 | `demo/fault_drill.py`、`tests/swarm/test_fault_drill.py` 均未生成；实现、focused、typecheck、完整序列 CLI、`test_stigmergy_avoidance`、mutation **全 NOT_RUN** |

产品代码必须由已指定 Qwen 生成；本次 Codex 没有代写、安装、自动重试或静默替换模型。用户“继续”已授权隔离开发自验，开发无需等待 H1/H3；本次实际阻塞为 Qwen 原生认证。主控关于是否改派 Codex 的问题尚无回复，本轮不等待或推定同意，正式 dsh Flash 评审要求不变。后续仍以 E 精确 SHA 的六阶段任务单为需求，不能把该任务单当已实现证据。

## 人工项与 NOT_RUN

主控已请求 H1 本人的预算 A/B、breaker 六点及姓名结论，H3 optional+nullable **1.0.0 candidate** 的采集/准入/冻结拍板，dsh 原生 profile/认证路径；目前均 pending。一般“继续”不是签名，不补人工结论、不冻结 Schema。正式 T10 演练验收和发布仍等原三锁（代码门禁、可接受 FC-E、H1 签字），H3 保持独立人工条件。

本轮未执行 merge/tag/三连/课题/正式演练/live；业务 contract_local 仅继承精确 C552 旧证据，interface_live/task_live 没有新增通过。旧 R1 拒收、dsh verifier exit 2/旧样本 exit 1、历史产品失败及 T10 exit 1 全部保留，不因材料交付成功变绿。

## 本轮材料校验与交付

仅检查授权路径、精确链接/对象、历史保留和 diff；不额外运行产品测试。已执行的材料核查如下，均不构成产品或发布门禁通过：

| 实际检查 | 结果 |
|---|---|
| `git show` E 精确 SHA 的报告、validation 与父提交；G 原报告；T10 本机 report/JSONL/exit/final-checks | 已只读核对；E 父为 c1107，T10 原生 exit 1 与失败结算一致 |
| `git ls-remote origin refs/heads/morph-fc-governance-final-0929 refs/heads/morph-fc-release-preflight-0929` | exit 0；开工 G=669b191、E=7347f5c1 精确一致；不是最终推送回执 |
| `git diff --name-only 669b191...` + `git ls-files --others --exclude-standard` 授权集合检查 | exit 0；恰好 3 个本轮仓内路径，无生产/测试/Schema/签字/源 TODO/AGENTS/SWARM/锁/旧报告变化 |
| PowerShell 历史前缀与新链接检查；GitHub blob 使用 `git cat-file -e <SHA>:<path>`，本地链接使用 `Test-Path` | exit 0；TASKS、计划两份 Git 文本历史前缀完整保留（统一换行比较）；15 个新增链接中 5 个精确 Git 对象、10 个本地文件均存在，未以网络页面可用性替代对象核查 |
| `git diff --check 669b191...` 与 `git diff --numstat` | exit 0；TASKS +11/-0、计划 +18/-0，旧历史无删除；新报告另增。Git 给出仓库既有 LF→CRLF 提示，未改全局换行配置 |
| 桌面追加前身份 | 17893 bytes，SHA256 `C6E1B55DEC14DE8AAB6BC0BF450F3707E6788E3823C10970AEDA0FAA9104CCF0`；追加后再比较此前完整字节前缀 |

首次读取本文时文件尚不存在，`Get-Content` 报路径不存在；随后按本轮写权新建，不是产品测试失败或可补绿的门禁。没有重跑产品/可选测试，也没有创建材料测试框架。

最终普通 commit/push、remote exact/clean、桌面追加后的字节保留结果，由实际完成后的桌面最终回执与 worker_done 登记。本文交付 SHA 由最终 Git 提交定位，不把准备中的材料预写为推送成功。

入口：[TASKS 最新附录](../../TASKS.md)、[发布计划最新续接](../../docs/FC_RELEASE_PLAN_0929.md)。
