# Qwen / 阿里云科研协同路线

本轮交付是定位与实施路线，只修改文档。Qwen 接入、本地 GPU 科研、阿里云计算执行、跨机器协作和加速收益均为 **NOT_RUN**。当前 main 基线为 `0e7826819c6780f637ff4049adfc61e8069638d9`；本次文档变更没有增加科研执行能力。

## 可复用的冻结基础

CaseDefinition 将科学定义与执行平台分开，声明程序、数据、条件与判据；可信执行器保存原始证据并独立判定。TaskLedger 负责认领、续租、fencing 与预算，科研 MCP 提供受限工具，官方 OpenSandbox SDK 执行注册实验。文件验证、批准、应用与继承继续使用既有资产消费链。

| 固定版本 | 可核对来源 |
|---|---|
| CORE `bf67c1a4134a25d009cff2acccbfab027999bea6` | [CaseDefinition](https://github.com/songconmaisaix31-design/Morphogenesis/blob/bf67c1a4134a25d009cff2acccbfab027999bea6/orchestration/experiments/case.py)、[执行器与可信读取](https://github.com/songconmaisaix31-design/Morphogenesis/blob/bf67c1a4134a25d009cff2acccbfab027999bea6/orchestration/experiments/executor.py)、[科研 MCP](https://github.com/songconmaisaix31-design/Morphogenesis/tree/bf67c1a4134a25d009cff2acccbfab027999bea6/swarm/research) |
| PRODUCT `dfbc88cbc5fb90f41f6ba01a0f5d16a5a59294fa` | 源码位于私有独立产品仓库 `songconmaisaix31-design/Morphogenesis-Research`；需要仓库访问权限，由有权限的审查者按此完整 SOURCE 核对 CLI 与权限配置。公共验收入口见下行 REPORT |
| REPORT `7b66f0dd0a285c1b6cf789aa3c5a41d22d655993` | [公开实际运行、检查器与继承回执](https://github.com/songconmaisaix31-design/Morphogenesis/blob/7b66f0dd0a285c1b6cf789aa3c5a41d22d655993/docs/tracks/research-integration-cases-1002.md) |

| 科学案例 | 科学差别 | 共用路径 |
|---|---|---|
| NIST NumAcc4 | 1001 行公开数值数据；验证均值、样本方差与残差，独立 Fraction 重算 | 三角色各一次 fresh CPU 实验、可信结果、文件验证批准应用、第三角色本地再验证与真实 adoption |
| synthetic 线性回归 | 项目自有七行确定性数据，明确为 synthetic；独立有理数判定斜率、截距与 SSE | 同一执行与继承链，使用自身程序、数据和 ScientificAssessment，不套 NIST 公式 |

冻结版本使用 Codex 与 Claude 原生 CLI；Claude 实际 provider/model 为 StepFun/step-3.5-flash。它证明案例复用同一协作链，不证明 Qwen、云 GPU、跨机器调度或科研加速。业务 SOURCE 与报告 SHA 分列；此代码与独立产品没有由本轮合入 main。

## 协同数据流与执行边界

1. 操作者在本地选择 CaseDefinition，固定输入、程序、判据、执行模式与资源，创建隔离项目和保护状态。原始数据默认不离开本机。
2. 云端 Qwen 只获得已允许发送的任务摘要、工具 schema 与必要结果摘要，返回候选建议或工具请求。原始数据片段上传须由操作者按数据边界决定；凭据、权威 SQLite 和完整私有目录不进入模型上下文。
3. 既有宿主核验工具名、参数、scope、身份、当前 token、有效租约与预算。模型请求不是执行授权，也不直接写 approved/result/adoption。
4. 执行 MCP 将注册程序和数据交给本地后端；CPU/GPU由已批准配置选择。已验证案例是 CPU；GPU还需验证设备、驱动、镜像与数值条件。
5. 如需阿里云计算，操作者明确指定一个后端与资源配额，只传入允许上传的实验输入。复用执行接口和官方 SDK，不复制到未批准地域，不新建跨机分发系统。
6. 后端返回原始输出、日志、执行身份与清理状态，本地 trusted read_result 核验计划与上下文，科学规则独立判定。不同 worker 在干净环境复现后才文件验证、批准应用；后续任务仍需自己本地再验证，实际文件、账本与消费回执一致才算继承。

| 配置层 | 必须显式选择 | 尚未证明 |
|---|---|---|
| 云推理 | 百炼地域/业务空间、官方端点、明确模型 ID、凭据来源、输出限制、工具能力与 usage | 此仓 Qwen 适配、实际工具循环、账户额度及在途硬费用封顶 |
| 本地计算 | 数据目录、案例、CPU/内存/时限；GPU设备与软件环境 | GPU科学结果与性能收益；宿主资源请求不是客体 cgroup/设备隔离证明 |
| 云计算 | 指定后端、镜像、地域、上传清单、资源上限、结果回收与销毁 | 实际云实验、失败远端状态、跨机续接与计算费用 |

云推理 token/延迟与云计算 CPU/GPU 时间、传输和存储费用分开记录。没有可信用量时保留 unknown/null，CLI估费不能当作已结算费用。未知远端效果停止后续执行，不自动重试或用新身份绕过。

## 最小实施阶段与验收

| 阶段 | 最少工作 | 独立验收 |
|---|---|---|
| 1 · Qwen 独立接口契约 | 在既有 provider 边界接入官方 SDK 或兼容接口；显式地域/模型、请求/返回/流式工具/usage映射及凭据隔离 | 先 contract_local：参数、权限、无副作用拒绝、错误/取消/缺usage；后在授权账户与预算下 interface_live，核对请求和实际模型及工具返回。HTTP 200 或文本回复不算科学通过 |
| 2 · 云推理 + 本地科学闭环 | 正式产品消费适配器，复用三角色与 lease/budget/once/approval/inheritance，不改判据 | 精确新冻结 SOURCE、新非editable安装、原完整双平台工程；两个新案例独立执行/复现/继承、当前token有效续租、真实中断与TTL同会话恢复及合法stale拒绝；完整原检查器和audit通过才签 task_live |
| 3 · 可选指定云计算后端 | 本机资源不足时适配一个成熟官方计算服务，同计划接口与受控输入、回收及清理 | 新唯一实验核对镜像/数据/条件/实际资源、科学结果与销毁；与本地同条件比较，记录传输和端到端时间后再讨论加速。未知effect禁止重放 |

三阶段当前均 **NOT_RUN**。本轮不实现适配，不新增几十个 Agent、大量算法对照或另一套调度/Attempt/Manifest/完成证明系统。MCP、TaskLedger、OpenSandbox 与继承继续复用；权限与关键启动参数归正式产品，不由观察脚本补齐。

## 官方接口依据与选择原则

2026-10-02 仅浏览官方文档，没有调用模型、API、账户或云资源：

- [百炼 OpenAI 兼容 Chat](https://www.alibabacloud.com/help/en/model-studio/compatibility-of-openai-with-dashscope)：Qwen 支持官方兼容接口；API Key 与端点地域需匹配。地域/业务空间端点在实施时按官方文档和所选账户确认，本路线不固定未经核验的最新模型。
- [官方 Function Calling](https://www.alibabacloud.com/help/en/model-studio/qwen-function-calling)：适配需验证工具选择、参数和多轮结果回传；云模型提出调用不等于本地工具已执行。API兼容名称不能替代权限与真实循环验收。
- [官方 API Key 管理](https://help.aliyun.com/zh/model-studio/get-api-key)：凭据由受控宿主进程局部使用，不写源码、prompt、命令行或证据清单，不改变全局 HOME/auth/provider/model/tier。

本仓安装与当前入口见 [README](../README.md)，文件所有权见 [PLAN](PLAN.md)。冻结代码、报告与历史失败保持原样；下一步实际实现范围由用户决定，再按对应阶段验收。
