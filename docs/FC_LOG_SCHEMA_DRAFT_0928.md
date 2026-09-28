# T8 日志 Schema 1.0.0 冻结版

版本 `1.0.0`。准备人 codex/master-control；基于集成生产 SHA
`73e64cc70116ac658d85591d082c0684a4952c99`。这份文档是 1.0.0 契约，已修复两项校验问题：
count=null/audit缺失错误拒绝；audit对象/count缺失错误放行。现在条件逻辑已正确实现：
1. 当 audit_confirmed_issue_events 为 null 时，issue_audit 也必须为 null（反之亦然）
2. 当 issue_audit 为对象时，audit_confirmed_issue_events 必须为整数（反之亦然）
生产接线未执行。契约冻结不等于已接线采集或生产验收。生成复用当前安装的 Pydantic v2（MIT），
直接导出 FaultObservation 与 RehearsalSnapshot 定义，不复制另一份运行时契约。

## 授权来源与版本策略

本契约版本 1.0.0 由人类队长于 2026-09-28 消息中正式授权冻结，条件逻辑缺陷已修复。
版本规则：可选字段新增为 minor 版本，破坏性修改为 major 版本。
optional → required 会拒绝已有旧日志，属于破坏性变更，需 2.0.0 版本。
可选字段从 optional 保持为 optional 时，即使采集完善，也保持为 minor 版本 1.1。

## 字段及四视图映射

| 字段 | 来源 / 建议语义 | 状态 |
|---|---|---|
| run_id、sequence、task_id、at | TaskLedger.audit 的 sequence/task_id/at；源 run_id 不猜测 | 新统一外壳，未实现转换 |
| duration_seconds | 单次操作实际测量；无可靠起止时为 null，不填 0 | 待事件生产者提供 |
| dag_node | TaskRecord 的 signal.task_id、dependencies、status | 支持 DAG 节点；依赖不能编造 |
| asset_calls | 既有 local_assets 调用/结果的 asset_id、operation、outcome、证据 | 新投影提案；未实现生产接线 |
| routing | swarm/router.py:65–87 的 signals 与 probabilities 按索引对应；selected、beta、exploration | 支持路由权重；此处为任务路由，不能当 provider 选择概率 |
| claim | task_ledger.py:313 的 claimed worker_id/token 与后续实际事件 | 支持认领事件；token 复用既有身份 |
| fault_observation | swarm/fault_observations.py:32 导出全部 14 字段，含 attempt | 不删字段、不改原 JSONL |
| rehearsal | orchestration/rehearsal_models.py:79 的完整 RehearsalSnapshot 导出 | 保留原 provenance/acceptance/results/genes/adoptions |
| drill、provenance、evidence_label | 演练为 true/mock/SIMULATED；真实为 false/live/LIVE；回放为 false/replay/REPLAY | 本提案的显式约束 |
| audit_confirmed_issue_events、issue_audit | 审计确认问题事件数及审计范围/证据；未审计为 null；完整审计确认无问题才可为 0 | 可选字段，未采集可省略或null，随H3批准；配套issue_audit也应允许缺失/null，明确尚未接入采集 |

## 审计确认问题事件数：统计口径提案

新增数值列 `audit_confirmed_issue_events: integer >= 0 | null`（可选、无默认0），配
`issue_audit` 保存 status（partial/complete）、protocol_id、scope、reviewer、
confirmed_issue_ids、evidence_refs。未审计时两字段均为 null；完整审计有证据且无问题
才能写 0。partial 只能报告已确认的正数，必须显示"部分审计"，不能当最终总数。

计数单位为同一 run、同一审计范围内经证据确认的唯一问题事件，不是重试数、失败请求数、
测试失败次数或模型自报。采用既有问题/审计条目 ID 去重，修复后的重跑不重复计数；
真实再次发生的独立事件须有独立证据才计新事件。不新造调度器/Manifest/证明系统。
预期的 SIMULATED 故障注入本身不算问题；若其处理出现经审计确认的缺陷才计数。
drill/mock、live、replay 分范围，不将演练计数混成 live。每行是累计快照，禁止跨行求和。

消费侧还需检查 count == unique(confirmed_issue_ids) 数量，issue 属于声明 scope，
证据可回溯；该跨字段关系不由当前 JSON Schema 自动证明。需要撤销误判时保留审计修订
证据并更新快照，不悄悄删除原问题记录。原始来源没有审计事实时保持 null，不从日志错误码猜数。

参考 [AutoResearch v2 §3.1–3.2 / Figure 2](https://arxiv.org/html/2608.17906v2)：
RSICD 场景在共同任务契约下审计研究工件，公开数字依次为 AutoResearch 5、R&D-Agent 11、
AutoResearchClaw 15、Agent Laboratory 18、The AI Scientist 27。该论文没有给出可直接复用
的细粒度去重字段，本段计数/去重规则是 Morphogenesis 本地提案，不能宣称与论文协议完全等价。
答辩可将数字同框展示，但须同时标注任务、协议、审计范围与完整性；本项目未采集值为“待审计”，
不能预填0或据跨任务原始计数宣称优于这些系统。这里只新增 Schema 草案，明日经 H3 后接线采集。

## 与现有契约的边界

FaultObservation 保留 observation_id/run_id/task_id/request_id/attempt/provider/model/failure_class/
normalized_reason/retry_after_seconds/switched_to/cost_state/occurred_at/evidence_ref 全字段。
`attempt` 为零起始；两个时间均为 UTC Unix 秒。外壳 at 表示观察源事件时间，不强行覆盖
fault_observation.occurred_at。缺失的 switched_to、cost_state、Retry-After、费用/用量保持原未知
语义；不以 0 或人为 null 覆盖已知值。FaultObservation 不进入 Gene/Candidate/发布链。

JSON Schema 可检查结构与 drill/provenance 组合；原 Pydantic model_validator 的跨字段语义
（如 checkpoint 计数、成员选择、源一致性、冷却溢出）不会全部体现在导出中。最终生产接线
必须继续调用原模型校验，并检查外壳 run_id/task_id 与嵌套事实匹配、概率与候选顺序一致。
这里没有宣称结构校验能证明运行行为。schema_version 的变更规则提案为：冻结后任何修改需
bump；兼容新增字段 minor，删除/类型/语义改变 major，纯描述修订 patch，由队长批准规则。

## 变更影响与待拍板

1. 建议新增只读日志投影，在独立演练输出目录写统一 JSONL；保留原故障 JSONL、账本审计、
   RehearsalDocument 不变，禁止把演练写到 live 目录。生产投影代码仍属于 B 类，未实施。
2. GUI 四视图与分析方消费共同 envelope；现有 API/CLI 不受本草案影响。旧日志只有可靠映射
   才转换，不能为补字段制造资产调用、认领、耗时或费用。跨机器时钟排序不能只依赖 at。
3. 本提案只承诺既有故障事实与任务路由快照；provider 候选切换可由 FaultObservation 和已有
   执行证据表达，不把现有任务路由概率错误映射成 provider 权重。是否增独立 provider 快照
   应在冻结前由队长裁定并分配生产 Owner。
4. 队长待确认：字段语义、版本策略、独立演练目录、四视图最小数据、跨字段校验责任。
   审批人/时间/冻结版本：**待填写**。T9 仅在批准后生成样例与两条待发送消息。

## Pydantic 导出的 JSON Schema（含提案外壳）

```json
{
  "$defs": {
    "Acceptance": {
      "additionalProperties": false,
      "properties": {
        "contract_local": {
          "default": "not_run",
          "enum": [
            "not_run",
            "passed",
            "failed",
            "blocked"
          ],
          "title": "Contract Local",
          "type": "string"
        },
        "interface_live": {
          "default": "not_run",
          "enum": [
            "not_run",
            "passed",
            "failed",
            "blocked"
          ],
          "title": "Interface Live",
          "type": "string"
        },
        "task_live": {
          "default": "not_run",
          "enum": [
            "not_run",
            "passed",
            "failed",
            "blocked"
          ],
          "title": "Task Live",
          "type": "string"
        },
        "provenance": {
          "default": "live",
          "enum": [
            "live",
            "replay",
            "mock"
          ],
          "title": "Provenance",
          "type": "string"
        },
        "original_run_uri": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Original Run Uri"
        }
      },
      "title": "Acceptance",
      "type": "object"
    },
    "AgentId": {
      "additionalProperties": false,
      "properties": {
        "role": {
          "enum": [
            "planner",
            "builder",
            "reviewer",
            "aggregator"
          ],
          "title": "Role",
          "type": "string"
        },
        "instance": {
          "minimum": 0,
          "title": "Instance",
          "type": "integer"
        }
      },
      "required": [
        "role",
        "instance"
      ],
      "title": "AgentId",
      "type": "object"
    },
    "AssetCall": {
      "additionalProperties": false,
      "properties": {
        "asset_id": {
          "title": "Asset Id",
          "type": "string"
        },
        "operation": {
          "enum": [
            "lookup",
            "inject",
            "validate",
            "apply",
            "adopt"
          ],
          "title": "Operation",
          "type": "string"
        },
        "worker_id": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "title": "Worker Id"
        },
        "duration_seconds": {
          "anyOf": [
            {
              "minimum": 0,
              "type": "number"
            },
            {
              "type": "null"
            }
          ],
          "title": "Duration Seconds"
        },
        "outcome": {
          "enum": [
            "succeeded",
            "failed",
            "unknown"
          ],
          "title": "Outcome",
          "type": "string"
        },
        "evidence_ref": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "title": "Evidence Ref"
        }
      },
      "required": [
        "asset_id",
        "operation",
        "worker_id",
        "duration_seconds",
        "outcome",
        "evidence_ref"
      ],
      "title": "AssetCall",
      "type": "object"
    },
    "AttemptId": {
      "additionalProperties": false,
      "properties": {
        "task_id": {
          "minLength": 1,
          "title": "Task Id",
          "type": "string"
        },
        "agent": {
          "$ref": "#/$defs/AgentId"
        },
        "attempt": {
          "minimum": 0,
          "title": "Attempt",
          "type": "integer"
        }
      },
      "required": [
        "task_id",
        "agent",
        "attempt"
      ],
      "title": "AttemptId",
      "type": "object"
    },
    "Checkpoint": {
      "additionalProperties": false,
      "properties": {
        "name": {
          "enum": [
            "clamp",
            "mean",
            "unique"
          ],
          "title": "Name",
          "type": "string"
        },
        "passed": {
          "anyOf": [
            {
              "type": "boolean"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Passed"
        }
      },
      "required": [
        "name"
      ],
      "title": "Checkpoint",
      "type": "object"
    },
    "Checkpoints": {
      "additionalProperties": false,
      "properties": {
        "checks": {
          "items": {
            "$ref": "#/$defs/Checkpoint"
          },
          "maxItems": 3,
          "minItems": 3,
          "title": "Checks",
          "type": "array"
        },
        "passed_count": {
          "maximum": 3,
          "minimum": 0,
          "title": "Passed Count",
          "type": "integer"
        },
        "total": {
          "const": 3,
          "default": 3,
          "title": "Total",
          "type": "integer"
        },
        "ratio": {
          "maximum": 1,
          "minimum": 0,
          "title": "Ratio",
          "type": "number"
        },
        "verification": {
          "$ref": "#/$defs/Verification"
        },
        "provenance": {
          "enum": [
            "live",
            "replay",
            "mock"
          ],
          "title": "Provenance",
          "type": "string"
        }
      },
      "required": [
        "checks",
        "passed_count",
        "ratio",
        "verification",
        "provenance"
      ],
      "title": "Checkpoints",
      "type": "object"
    },
    "ClaimEvent": {
      "additionalProperties": false,
      "properties": {
        "task_id": {
          "title": "Task Id",
          "type": "string"
        },
        "worker_id": {
          "title": "Worker Id",
          "type": "string"
        },
        "token": {
          "minimum": 1,
          "title": "Token",
          "type": "integer"
        },
        "outcome": {
          "enum": [
            "claimed",
            "released",
            "lost",
            "submitted"
          ],
          "title": "Outcome",
          "type": "string"
        }
      },
      "required": [
        "task_id",
        "worker_id",
        "token",
        "outcome"
      ],
      "title": "ClaimEvent",
      "type": "object"
    },
    "DagNode": {
      "additionalProperties": false,
      "properties": {
        "task_id": {
          "title": "Task Id",
          "type": "string"
        },
        "dependencies": {
          "items": {
            "type": "string"
          },
          "title": "Dependencies",
          "type": "array"
        },
        "status": {
          "enum": [
            "available",
            "claimed",
            "submitting",
            "partial",
            "handoff",
            "completed",
            "failed",
            "blocked"
          ],
          "title": "Status",
          "type": "string"
        }
      },
      "required": [
        "task_id",
        "dependencies",
        "status"
      ],
      "title": "DagNode",
      "type": "object"
    },
    "FaultObservation": {
      "additionalProperties": false,
      "description": "One request attempt; evidence_ref is FC-A's evidence_hash verbatim.\n\nattempt is zero-based, matching contracts.identity.AttemptId.attempt. Time is\nUTC Unix seconds. Missing switch, cost state and cooldown remain unknown.\nA replay may regenerate observation_id but must retain every other fact.",
      "properties": {
        "observation_id": {
          "minLength": 1,
          "title": "Observation Id",
          "type": "string"
        },
        "run_id": {
          "minLength": 1,
          "title": "Run Id",
          "type": "string"
        },
        "task_id": {
          "minLength": 1,
          "title": "Task Id",
          "type": "string"
        },
        "request_id": {
          "minLength": 1,
          "title": "Request Id",
          "type": "string"
        },
        "attempt": {
          "minimum": 0,
          "title": "Attempt",
          "type": "integer"
        },
        "provider": {
          "minLength": 1,
          "title": "Provider",
          "type": "string"
        },
        "model": {
          "minLength": 1,
          "title": "Model",
          "type": "string"
        },
        "failure_class": {
          "enum": [
            "confirmed_rejection",
            "unknown_effect",
            "budget_exhausted",
            "capability_mismatch"
          ],
          "title": "Failure Class",
          "type": "string"
        },
        "normalized_reason": {
          "minLength": 1,
          "title": "Normalized Reason",
          "type": "string"
        },
        "retry_after_seconds": {
          "anyOf": [
            {
              "minimum": 0,
              "type": "number"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Retry After Seconds"
        },
        "switched_to": {
          "anyOf": [
            {
              "minLength": 1,
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Switched To"
        },
        "cost_state": {
          "anyOf": [
            {
              "enum": [
                "settled",
                "unknown",
                "reserved"
              ],
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Cost State"
        },
        "occurred_at": {
          "minimum": 0,
          "title": "Occurred At",
          "type": "number"
        },
        "evidence_ref": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Evidence Ref"
        }
      },
      "required": [
        "run_id",
        "task_id",
        "request_id",
        "attempt",
        "provider",
        "model",
        "failure_class",
        "normalized_reason",
        "occurred_at"
      ],
      "title": "FaultObservation",
      "type": "object"
    },
    "GeneRef": {
      "additionalProperties": false,
      "properties": {
        "gene_id": {
          "minLength": 1,
          "title": "Gene Id",
          "type": "string"
        },
        "version": {
          "default": 1,
          "minimum": 1,
          "title": "Version",
          "type": "integer"
        },
        "asset_id": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Asset Id"
        }
      },
      "required": [
        "gene_id"
      ],
      "title": "GeneRef",
      "type": "object"
    },
    "GeneView": {
      "additionalProperties": false,
      "properties": {
        "ref": {
          "$ref": "#/$defs/GeneRef"
        },
        "provenance": {
          "enum": [
            "live",
            "replay",
            "mock"
          ],
          "title": "Provenance",
          "type": "string"
        },
        "original_run_uri": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "title": "Original Run Uri"
        },
        "source_attempt": {
          "anyOf": [
            {
              "$ref": "#/$defs/AttemptId"
            },
            {
              "type": "null"
            }
          ]
        },
        "weight": {
          "title": "Weight",
          "type": "number"
        },
        "use_count": {
          "title": "Use Count",
          "type": "integer"
        },
        "injected_count": {
          "title": "Injected Count",
          "type": "integer"
        },
        "created_at": {
          "title": "Created At",
          "type": "number"
        },
        "last_used_at": {
          "anyOf": [
            {
              "type": "number"
            },
            {
              "type": "null"
            }
          ],
          "title": "Last Used At"
        },
        "evaluated_at": {
          "title": "Evaluated At",
          "type": "number"
        },
        "tau_seconds": {
          "title": "Tau Seconds",
          "type": "number"
        },
        "archived_at": {
          "anyOf": [
            {
              "type": "number"
            },
            {
              "type": "null"
            }
          ],
          "title": "Archived At"
        },
        "remote_archive_status": {
          "default": "not_synchronized",
          "title": "Remote Archive Status",
          "type": "string"
        }
      },
      "required": [
        "ref",
        "provenance",
        "original_run_uri",
        "source_attempt",
        "weight",
        "use_count",
        "injected_count",
        "created_at",
        "last_used_at",
        "evaluated_at",
        "tau_seconds",
        "archived_at"
      ],
      "title": "GeneView",
      "type": "object"
    },
    "IssueAudit": {
      "additionalProperties": false,
      "properties": {
        "status": {
          "enum": [
            "partial",
            "complete"
          ],
          "title": "Status",
          "type": "string"
        },
        "protocol_id": {
          "minLength": 1,
          "title": "Protocol Id",
          "type": "string"
        },
        "scope": {
          "description": "Run, evaluated workflow, and trace interval covered",
          "minLength": 1,
          "title": "Scope",
          "type": "string"
        },
        "reviewer": {
          "minLength": 1,
          "title": "Reviewer",
          "type": "string"
        },
        "confirmed_issue_ids": {
          "items": {
            "type": "string",
            "minLength": 1
          },
          "title": "Confirmed Issue Ids",
          "type": "array",
          "uniqueItems": true
        },
        "evidence_refs": {
          "items": {
            "type": "string",
            "minLength": 1
          },
          "minItems": 1,
          "title": "Evidence Refs",
          "type": "array"
        }
      },
      "required": [
        "status",
        "protocol_id",
        "scope",
        "reviewer",
        "confirmed_issue_ids",
        "evidence_refs"
      ],
      "title": "IssueAudit",
      "type": "object"
    },
    "MemberAvailability": {
      "additionalProperties": false,
      "properties": {
        "agent": {
          "$ref": "#/$defs/AgentId"
        },
        "available": {
          "default": true,
          "title": "Available",
          "type": "boolean"
        },
        "changed_at": {
          "minimum": 0,
          "title": "Changed At",
          "type": "number"
        },
        "reason": {
          "default": "fixed logical member",
          "title": "Reason",
          "type": "string"
        }
      },
      "required": [
        "agent",
        "changed_at"
      ],
      "title": "MemberAvailability",
      "type": "object"
    },
    "PipeState": {
      "additionalProperties": false,
      "properties": {
        "src": {
          "$ref": "#/$defs/AgentId"
        },
        "dst": {
          "$ref": "#/$defs/AgentId"
        },
        "weight": {
          "default": 0.0,
          "minimum": 0,
          "title": "Weight",
          "type": "number"
        },
        "flow": {
          "default": 0.0,
          "minimum": 0,
          "title": "Flow",
          "type": "number"
        },
        "success_rate": {
          "default": 0.5,
          "maximum": 1,
          "minimum": 0,
          "title": "Success Rate",
          "type": "number"
        },
        "active": {
          "default": true,
          "title": "Active",
          "type": "boolean"
        }
      },
      "required": [
        "src",
        "dst"
      ],
      "title": "PipeState",
      "type": "object"
    },
    "RehearsalSnapshot": {
      "additionalProperties": false,
      "properties": {
        "executor": {
          "default": "codex",
          "enum": [
            "codex",
            "evomap"
          ],
          "title": "Executor",
          "type": "string"
        },
        "model": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Model"
        },
        "sequence": {
          "minimum": 0,
          "title": "Sequence",
          "type": "integer"
        },
        "stage": {
          "enum": [
            "task_ready",
            "repair_selected",
            "repair_reviewed",
            "gene_generated",
            "awaiting_offline",
            "member_offline",
            "recovery_ready",
            "recovery_selected",
            "recovery_reviewed",
            "gene_adopted",
            "decaying",
            "archived",
            "completed",
            "failed"
          ],
          "title": "Stage",
          "type": "string"
        },
        "at": {
          "description": "Actual Unix wall-clock seconds",
          "minimum": 0,
          "title": "At",
          "type": "number"
        },
        "task_id": {
          "title": "Task Id",
          "type": "string"
        },
        "task_description": {
          "title": "Task Description",
          "type": "string"
        },
        "provenance": {
          "enum": [
            "live",
            "replay",
            "mock"
          ],
          "title": "Provenance",
          "type": "string"
        },
        "acceptance": {
          "$ref": "#/$defs/Acceptance"
        },
        "checkpoints": {
          "anyOf": [
            {
              "$ref": "#/$defs/Checkpoints"
            },
            {
              "type": "null"
            }
          ],
          "default": null
        },
        "members": {
          "items": {
            "$ref": "#/$defs/MemberAvailability"
          },
          "title": "Members",
          "type": "array"
        },
        "pipes": {
          "items": {
            "$ref": "#/$defs/PipeState"
          },
          "title": "Pipes",
          "type": "array"
        },
        "routing": {
          "$ref": "#/$defs/RoutingFact"
        },
        "genes": {
          "items": {
            "$ref": "#/$defs/GeneView"
          },
          "title": "Genes",
          "type": "array"
        },
        "adoptions": {
          "items": {
            "$ref": "#/$defs/UseRecord"
          },
          "title": "Adoptions",
          "type": "array"
        },
        "results": {
          "items": {
            "$ref": "#/$defs/TaskResult"
          },
          "title": "Results",
          "type": "array"
        },
        "retrievable_gene_ids": {
          "items": {
            "type": "string"
          },
          "title": "Retrievable Gene Ids",
          "type": "array"
        },
        "tau_seconds": {
          "exclusiveMinimum": 0,
          "title": "Tau Seconds",
          "type": "number"
        },
        "archive_threshold": {
          "exclusiveMaximum": 1,
          "exclusiveMinimum": 0,
          "title": "Archive Threshold",
          "type": "number"
        },
        "max_model_calls": {
          "const": 2,
          "default": 2,
          "title": "Max Model Calls",
          "type": "integer"
        },
        "model_calls_started": {
          "maximum": 2,
          "minimum": 0,
          "title": "Model Calls Started",
          "type": "integer"
        },
        "cost_usd": {
          "anyOf": [
            {
              "minimum": 0,
              "type": "number"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Cost Usd"
        },
        "message": {
          "default": "",
          "title": "Message",
          "type": "string"
        },
        "failure": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Failure"
        }
      },
      "required": [
        "sequence",
        "stage",
        "at",
        "task_id",
        "task_description",
        "provenance",
        "acceptance",
        "members",
        "pipes",
        "routing",
        "tau_seconds",
        "archive_threshold",
        "model_calls_started"
      ],
      "title": "RehearsalSnapshot",
      "type": "object"
    },
    "RouteCandidate": {
      "additionalProperties": false,
      "properties": {
        "task_id": {
          "title": "Task Id",
          "type": "string"
        },
        "concentration": {
          "title": "Concentration",
          "type": "number"
        },
        "capability_match": {
          "maximum": 1,
          "minimum": 0,
          "title": "Capability Match",
          "type": "number"
        },
        "w_history": {
          "title": "W History",
          "type": "number"
        },
        "urgency": {
          "title": "Urgency",
          "type": "number"
        },
        "base_urgency": {
          "title": "Base Urgency",
          "type": "number"
        },
        "age_weight": {
          "title": "Age Weight",
          "type": "number"
        },
        "score": {
          "title": "Score",
          "type": "number"
        },
        "probability": {
          "maximum": 1,
          "minimum": 0,
          "title": "Probability",
          "type": "number"
        }
      },
      "required": [
        "task_id",
        "concentration",
        "capability_match",
        "w_history",
        "urgency",
        "base_urgency",
        "age_weight",
        "score",
        "probability"
      ],
      "title": "RouteCandidate",
      "type": "object"
    },
    "RouteSnapshot": {
      "additionalProperties": false,
      "properties": {
        "worker_id": {
          "title": "Worker Id",
          "type": "string"
        },
        "selected": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "title": "Selected"
        },
        "candidates": {
          "items": {
            "$ref": "#/$defs/RouteCandidate"
          },
          "title": "Candidates",
          "type": "array"
        },
        "filtered_task_ids": {
          "items": {
            "type": "string"
          },
          "title": "Filtered Task Ids",
          "type": "array"
        },
        "beta": {
          "title": "Beta",
          "type": "number"
        },
        "exploration": {
          "maximum": 1,
          "minimum": 0,
          "title": "Exploration",
          "type": "number"
        }
      },
      "required": [
        "worker_id",
        "selected",
        "candidates",
        "filtered_task_ids",
        "beta",
        "exploration"
      ],
      "title": "RouteSnapshot",
      "type": "object"
    },
    "RoutingFact": {
      "additionalProperties": false,
      "properties": {
        "task_id": {
          "title": "Task Id",
          "type": "string"
        },
        "eligible_members": {
          "items": {
            "$ref": "#/$defs/AgentId"
          },
          "title": "Eligible Members",
          "type": "array"
        },
        "selected_attempt": {
          "anyOf": [
            {
              "$ref": "#/$defs/AttemptId"
            },
            {
              "type": "null"
            }
          ],
          "default": null
        },
        "removed_member": {
          "anyOf": [
            {
              "$ref": "#/$defs/AgentId"
            },
            {
              "type": "null"
            }
          ],
          "default": null
        },
        "removed_at": {
          "anyOf": [
            {
              "type": "number"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Removed At"
        },
        "boundary": {
          "const": "between_tasks",
          "default": "between_tasks",
          "title": "Boundary",
          "type": "string"
        }
      },
      "required": [
        "task_id",
        "eligible_members"
      ],
      "title": "RoutingFact",
      "type": "object"
    },
    "TaskResult": {
      "additionalProperties": false,
      "properties": {
        "run_id": {
          "minLength": 1,
          "title": "Run Id",
          "type": "string"
        },
        "task_id": {
          "minLength": 1,
          "title": "Task Id",
          "type": "string"
        },
        "attempt": {
          "$ref": "#/$defs/AttemptId"
        },
        "status": {
          "enum": [
            "succeeded",
            "failed",
            "interrupted",
            "pending_review",
            "insufficient_evidence"
          ],
          "title": "Status",
          "type": "string"
        },
        "verdict": {
          "$ref": "#/$defs/Verification"
        },
        "artifact_uri": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Artifact Uri"
        },
        "provenance": {
          "default": "live",
          "enum": [
            "live",
            "replay",
            "mock"
          ],
          "title": "Provenance",
          "type": "string"
        },
        "original_run_uri": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Original Run Uri"
        },
        "acceptance": {
          "$ref": "#/$defs/Acceptance"
        },
        "usage": {
          "$ref": "#/$defs/Usage"
        }
      },
      "required": [
        "run_id",
        "task_id",
        "attempt",
        "status"
      ],
      "title": "TaskResult",
      "type": "object"
    },
    "Usage": {
      "additionalProperties": false,
      "description": "None means unreported/unknown, distinct from a measured zero.",
      "properties": {
        "tokens": {
          "anyOf": [
            {
              "minimum": 0,
              "type": "integer"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Tokens"
        },
        "cost_usd": {
          "anyOf": [
            {
              "minimum": 0,
              "type": "number"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Cost Usd"
        }
      },
      "title": "Usage",
      "type": "object"
    },
    "UseRecord": {
      "additionalProperties": false,
      "properties": {
        "run_id": {
          "title": "Run Id",
          "type": "string"
        },
        "attempt": {
          "$ref": "#/$defs/AttemptId"
        },
        "ref": {
          "$ref": "#/$defs/GeneRef"
        },
        "used_at": {
          "title": "Used At",
          "type": "number"
        },
        "provenance": {
          "enum": [
            "live",
            "replay",
            "mock"
          ],
          "title": "Provenance",
          "type": "string"
        }
      },
      "required": [
        "run_id",
        "attempt",
        "ref",
        "used_at",
        "provenance"
      ],
      "title": "UseRecord",
      "type": "object"
    },
    "Verification": {
      "additionalProperties": false,
      "properties": {
        "passed": {
          "anyOf": [
            {
              "type": "boolean"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Passed"
        },
        "reviewer": {
          "anyOf": [
            {
              "$ref": "#/$defs/AgentId"
            },
            {
              "type": "null"
            }
          ],
          "default": null
        },
        "evidence": {
          "items": {
            "type": "string"
          },
          "title": "Evidence",
          "type": "array"
        },
        "command": {
          "items": {
            "type": "string"
          },
          "title": "Command",
          "type": "array"
        },
        "exit_code": {
          "anyOf": [
            {
              "type": "integer"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Exit Code"
        },
        "summary": {
          "default": "Not verified",
          "title": "Summary",
          "type": "string"
        }
      },
      "title": "Verification",
      "type": "object"
    }
  },
  "additionalProperties": false,
  "properties": {
    "schema_version": {
      "const": "1.0.0",
      "title": "Schema Version",
      "type": "string"
    },
    "run_id": {
      "minLength": 1,
      "title": "Run Id",
      "type": "string"
    },
    "sequence": {
      "minimum": 0,
      "title": "Sequence",
      "type": "integer"
    },
    "task_id": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Task Id"
    },
    "at": {
      "description": "UTC Unix seconds; preserve observed source time",
      "minimum": 0,
      "title": "At",
      "type": "number"
    },
    "duration_seconds": {
      "anyOf": [
        {
          "minimum": 0,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "title": "Duration Seconds"
    },
    "drill": {
      "title": "Drill",
      "type": "boolean"
    },
    "provenance": {
      "enum": [
        "live",
        "mock",
        "replay"
      ],
      "title": "Provenance",
      "type": "string"
    },
    "evidence_label": {
      "enum": [
        "LIVE",
        "SIMULATED",
        "REPLAY"
      ],
      "title": "Evidence Label",
      "type": "string"
    },
    "original_run_uri": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Original Run Uri"
    },
    "event": {
      "enum": [
        "task",
        "asset_call",
        "routing",
        "claim",
        "fault_observation",
        "rehearsal"
      ],
      "title": "Event",
      "type": "string"
    },
    "dag_node": {
      "anyOf": [
        {
          "$ref": "#/$defs/DagNode"
        },
        {
          "type": "null"
        }
      ]
    },
    "asset_calls": {
      "items": {
        "$ref": "#/$defs/AssetCall"
      },
      "title": "Asset Calls",
      "type": "array"
    },
    "routing": {
      "anyOf": [
        {
          "$ref": "#/$defs/RouteSnapshot"
        },
        {
          "type": "null"
        }
      ]
    },
    "claim": {
      "anyOf": [
        {
          "$ref": "#/$defs/ClaimEvent"
        },
        {
          "type": "null"
        }
      ]
    },
    "fault_observation": {
      "anyOf": [
        {
          "$ref": "#/$defs/FaultObservation"
        },
        {
          "type": "null"
        }
      ]
    },
    "rehearsal": {
      "anyOf": [
        {
          "$ref": "#/$defs/RehearsalSnapshot"
        },
        {
          "type": "null"
        }
      ]
    },
    "audit_confirmed_issue_events": {
      "anyOf": [
        {
          "minimum": 0,
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "description": "审计确认问题事件数；未审计为null；同一scope累计快照，禁止跨日志行求和",
      "title": "Audit Confirmed Issue Events"
    },
    "issue_audit": {
      "anyOf": [
        {
          "$ref": "#/$defs/IssueAudit"
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "required": [
    "schema_version",
    "run_id",
    "sequence",
    "task_id",
    "at",
    "duration_seconds",
    "drill",
    "provenance",
    "evidence_label",
    "original_run_uri",
    "event",
    "dag_node",
    "asset_calls",
    "routing",
    "claim",
    "fault_observation",
    "rehearsal"
  ],
  "title": "FCLogDraft",
  "type": "object",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "description": "UNFROZEN proposal; generated from existing Pydantic source plus proposed event envelope.",
  "allOf": [
    {
      "if": {
        "properties": {
          "audit_confirmed_issue_events": {
            "type": "integer"
          }
        },
        "required": [
          "audit_confirmed_issue_events"
        ]
      },
      "then": {
        "properties": {
          "issue_audit": {
            "type": "object"
          }
        },
        "required": [
          "issue_audit"
        ]
      }
    },
    {
      "if": {
        "properties": {
          "audit_confirmed_issue_events": {
            "const": null
          }
        },
        "required": [
          "audit_confirmed_issue_events"
        ]
      },
      "then": {
        "properties": {
          "issue_audit": {
            "const": null
          }
        },
        "required": [
          "issue_audit"
        ]
      }
    },
    {
      "if": {
        "properties": {
          "issue_audit": {
            "type": "object"
          }
        },
        "required": [
          "issue_audit"
        ]
      },
      "then": {
        "properties": {
          "audit_confirmed_issue_events": {
            "type": "integer"
          }
        },
        "required": [
          "audit_confirmed_issue_events"
        ]
      }
    },
    {
      "if": {
        "properties": {
          "audit_confirmed_issue_events": {
            "const": 0
          }
        },
        "required": [
          "audit_confirmed_issue_events"
        ]
      },
      "then": {
        "properties": {
          "issue_audit": {
            "properties": {
              "status": {
                "const": "complete"
              },
              "confirmed_issue_ids": {
                "maxItems": 0
              }
            }
          }
        },
        "required": [
          "issue_audit"
        ]
      }
    },
    {
      "if": {
        "properties": {
          "drill": {
            "const": true
          }
        }
      },
      "then": {
        "properties": {
          "provenance": {
            "const": "mock"
          },
          "evidence_label": {
            "const": "SIMULATED"
          }
        }
      }
    },
    {
      "if": {
        "properties": {
          "provenance": {
            "const": "live"
          }
        }
      },
      "then": {
        "properties": {
          "drill": {
            "const": false
          },
          "evidence_label": {
            "const": "LIVE"
          }
        }
      }
    },
    {
      "if": {
        "properties": {
          "provenance": {
            "const": "mock"
          }
        }
      },
      "then": {
        "properties": {
          "evidence_label": {
            "const": "SIMULATED"
          }
        }
      }
    },
    {
      "if": {
        "properties": {
          "provenance": {
            "const": "replay"
          }
        }
      },
      "then": {
        "properties": {
          "drill": {
            "const": false
          },
          "evidence_label": {
            "const": "REPLAY"
          },
          "original_run_uri": {
            "type": "string",
            "minLength": 1
          }
        }
      }
    },
    {
      "if": {
        "properties": {
          "event": {
            "const": "task"
          }
        }
      },
      "then": {
        "properties": {
          "dag_node": {
            "type": "object"
          }
        }
      }
    },
    {
      "if": {
        "properties": {
          "event": {
            "const": "routing"
          }
        }
      },
      "then": {
        "properties": {
          "routing": {
            "type": "object"
          }
        }
      }
    },
    {
      "if": {
        "properties": {
          "event": {
            "const": "claim"
          }
        }
      },
      "then": {
        "properties": {
          "claim": {
            "type": "object"
          }
        }
      }
    },
    {
      "if": {
        "properties": {
          "event": {
            "const": "fault_observation"
          }
        }
      },
      "then": {
        "properties": {
          "fault_observation": {
            "type": "object"
          }
        }
      }
    },
    {
      "if": {
        "properties": {
          "event": {
            "const": "rehearsal"
          }
        }
      },
      "then": {
        "properties": {
          "rehearsal": {
            "type": "object"
          }
        }
      }
    },
    {
      "if": {
        "properties": {
          "event": {
            "const": "asset_call"
          }
        }
      },
      "then": {
        "properties": {
          "asset_calls": {
            "minItems": 1
          }
        }
      }
    },
    {
      "if": {
        "properties": {
          "event": {
            "enum": [
              "task",
              "claim",
              "fault_observation",
              "rehearsal",
              "asset_call"
            ]
          }
        }
      },
      "then": {
        "properties": {
          "task_id": {
            "type": "string",
            "minLength": 1
          }
        }
      }
    }
  ]
}
```
