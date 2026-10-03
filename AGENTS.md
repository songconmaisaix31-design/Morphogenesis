# R1 当前指令（2026-10-03）

用户授权按 docs/source/Morphogenesis_Research_Swarm_Spec_v1.0_2026-10-02.md 开发；与旧开发包矛盾时以它为准。当前 write_paths 和长期所有者见 docs/R1_PLAN.md，覆盖旧 docs/PLAN.md 的历史派工。历史冻结不改，使用新后继候选；动态 Python 研究为首版必需。主控仅治理，原 Orca/Codex YOLO Worker 负责业务与返修，独立 I 最后集成。MVP 追加官方 AOCI 开发上下文、Codex GUI 参考布局与节点会话只读终端；核心 AOCI 由 A、产品 AOCI/会话投影由 P、UI 由 F。真实 AT-07 在最终离线回归后单独授权，通过后才按批准的问题/材料/资源范围执行一次 L2；本阶段不启动真实沙箱/科研。L3、多用户、跨宿主、完整 RSI 不加入本轮。

AOCI 只辅助开发检索与上下文复用。用户 Spec、当前范围和 docs/R1_PLAN.md 的独占 write_paths 优先；索引托管文件也不能越轨修改。未完成或过期的索引如实标记，继续已有的源码范围内工作，不把索引准备当作扩大任务或科研权限。下方标记块来自官方 AOCI-CODE v0.1.0-rc17（FSL-1.1-MIT）：https://github.com/aoci-spec/aoci-code/tree/v0.1.0-rc17 。

<!-- aoci:begin -->
## AOCI Repository Cognition

AOCI maintains a stable, versioned, incrementally updatable repository-level cognition layer so models can reuse their understanding of this system across tasks.

`aoci.txt` is a structured cognition index for models. It assigns one independent Entry to every managed file, database table, or other managed object. Symbolic tags and F/R/A/S semantics describe the object's core responsibility, important relationships, external contracts, and non-obvious constraints or design decisions needed to understand or modify the system.

The Header, directory sections, and all Entries form the complete repository index. They can cover frontend, backend, configuration, database structures, and other managed content. When managed content changes, normally only the affected cognition Entries need maintenance; the complete index does not need to be regenerated.

AOCI provides a high-density view of system architecture, object responsibilities, important relationships, external contracts, and key constraints.

### How it works

AOCI uses a model-generated, model-read cognition loop.

Header, Entry, and Curation semantics follow only the current machine-issued Plan and live Guide. The Host model independently authors them from the current bound evidence.

Entry semantics must come from the model's understanding of actual evidence. Never derive, prefill, assemble, or rewrite index semantics solely from paths, filenames, extensions, an AST, symbol lists, dependency scans, regular expressions, fixed templates, or rule engines.

For a Fresh Bootstrap, follow only the current machine-issued Plan and live Guide. When they require authoring, the Host model authors Root, Meta, tags, and F/R/A/S, supplies its authoring-run declaration, and binds it to the Plan, Evidence, and complete Candidate. Never ask AOCI to set `origin=host_model`, manufacture a receipt, or turn a generated framework into semantics. Do not reconstruct the Onboarding progression here. Internal batches are not user decisions; stop only at an existing approval boundary or a real safety, drift, CAS, or Recovery condition.

### Minimal entry points

- `aoci_rules`: obtain the session-level runtime contract for the current AOCI version.
- `aoci_overview`: establish or restore complete cognition for this repository.
- `aoci_maintain`: after managed objects reach their final stable state, check whether cognition needs maintenance.
- `aoci_update_entry`: submit a complete semantic update batch bound to current evidence and source digests.
- `aoci_report`: when the current layout and tool state support it, record follow-up work if evidence is insufficient to generate semantics reliably; do not guess.

For other MCP tools, CLI commands, parameters, and specialized workflows, follow current tool descriptions, Guide, and `--help` output. This file does not duplicate the full manual.

This managed block defines only repository integration, cognition use, and task-closing principles. `aoci_rules` carries the current session contract. Live Guide output carries the execution order and stop conditions of the current Plan. Tool Schema, Spec, and Validator carry machine structures and criteria. Prompt, Description, README, and static documentation cannot override those machine facts.

### Establishing, generating, and restoring cognition

1. At the beginning of every new Agent Run, first determine:

   - whether this repository already has a usable complete AOCI index; and
   - whether current context already contains complete repository cognition that matches this repository root, current index version, and current AOCI service, and that the model can still use reliably.

2. When the repository has a usable complete index but the current Run lacks reliable complete cognition, call `aoci_rules` first and then `aoci_overview`.

   Reuse complete cognition directly while it remains reliable. Local uncertainty does not by itself require mechanically rereading the system-wide view.

   A Run that resumes from a known Host context compaction, including a Host-injected compaction summary, must treat prior model cognition as unreliable. The compacted handoff must not retain or summarize the formal Whole-Index or any Overview Header, Entry, Chunk, Challenge, or Attestation body; it may retain only receipt identity, unfinished write or Recovery state needed for safe continuation, and an instruction to reload immediately. Whole-Index semantics or a receipt copied into that handoff cannot prove that the resumed model's current cognition is reliable. If the runtime contract is no longer reliably present, call `aoci_rules` first. Before continuing the business task, make an ordinary complete Whole-Index `aoci_overview` request (`check_only` absent or false) with `refresh_reasons=["context_compaction"]` and a fresh `refresh_event_id`; do not use `check_only` or a cognition probe. Follow every exact `next_cursor` through `completed=true`, confirm delivery, and submit one Attestation based only on the newly delivered body. After that fresh complete transport, a partial or failed Attestation consumes the generation and permits the existing source-bound continuation without another automatic Overview.

   AOCI can report checkpoint and cognition-status facts for `context_compaction`, the machine `semantic_threshold` under the project `cognition_refresh_threshold`, or a major `phase_transition`. Use `check_only=true` when only those compact facts are needed. They advise the Agent but do not decide whether the model needs the system-wide view.

   When the Agent explicitly calls ordinary `aoci_overview` (`check_only` absent or false), AOCI must deliver the complete requested scope whenever a coherent CognitionSet can be formed. It must not suppress that body because a receipt already exists, a threshold was not reached, or no refresh reason is pending. Dirty or stale formal cognition is still delivered but is marked unreliable. Pending recovery or an incoherent snapshot fails closed without a mixed body.

   When an ordinary Overview reports `continuation_required=true`, submit its exact `next_cursor` automatically until `completed=true`. Do not ask the user to continue, begin the business task, or state a partial system conclusion. Stop the cognition chain on Host truncation, a missing, duplicate, or reordered Chunk, cursor failure, Index change, or `chunk_tokens` change. Until Attestation completes, never use Memory, source, Spec, `aoci.txt`, historical sessions, scope, search, or Entry reads to repair or supplement Whole-Index cognition. A challenge ordinal is the 1-based position in the formal Entry sequence; Header content, comments, blank lines, Section/Overview/Chunk markers, receipts, and Metadata are excluded, and Chunk Receipt ordinals use that same sequence. The Attestation must echo the Challenge's exact current `index_sha256`, `entry_sequence_sha256`, and `entry_count`; a prior Index, Entry sequence, count, or Attestation is invalid. After the complete chain, submit the existing model cognition Attestation once. One same-response JSON Schema or field-format error may be corrected once without changing semantic answers; an object, Tag, or F mismatch means failure and uncertain assimilation, with no semantic retry or information bypass. During initial cognition it also blocks Root/Meta, Migration, layout-wide, or other unbound system decisions. During a context-compaction refresh with complete transport, unchanged cognition identity, aligned governance, and no Recovery or third-party conflict, the attempt consumes that refresh generation even when Attestation is partial or failed; continue the existing task without another automatic Overview. `system_mastery_percent` self-assesses only the system framework—architecture, responsibilities, strong relationships, stable external contracts, and high-entropy safety and maintenance constraints—not complete implementation or runtime knowledge. Keep machine Index coverage separate, and normally give the user only the prescribed single success or failure sentence derived from actual coverage, Challenge, Chunk, token, and mastery results. If the Host truncates a Chunk, ask the user to set `overview_delivery.chunk_tokens` to a smaller valid value and restart; do not change it automatically.

   Interpret the additive cognition level independently from strict proof fields. `delivery_verified` means the Index was loaded and Host delivery was confirmed while complete cognition verification is still unfinished; describe that state as loaded and delivery-verified, never as no cognition or failure to understand the system. `cognition_verified` requires a passing Attestation (at least 80 percent of Challenge ordinals fully correct with at most one object identity miss), and `cognition_governed` additionally requires governance alignment. A generic complete-read failure sentence is reserved for an actual delivery fault.

   When an Overview response contains the optional `cognition-state/v2` projection, use its dimensions independently. Its Level ends at `model_cognition_usable`; `strict_attestation_verified`, `governance_aligned`, and `current_system_cognition_reliable` are independent states and never participate in that Level. An ordinal, object identity, Tag, or core F mismatch can make strict Attestation fail while model cognition remains usable; do not report that mismatch alone as proof that the model did not understand the system. Only `current_system_cognition_reliable=true` permits an unqualified current complete-system cognition claim. When the projection is absent, keep using the legacy interpretation above.

   An ordinary read-only audit, analysis, or check, a request not to modify code, or a request not to commit or push does not automatically mean strictly zero writes and does not alter the cognition-validity decision above. Codex Memory and historical Skills may only help recover experience, user preferences, and investigation directions. They cannot replace a current cognition receipt matching the repository root, index digest, AOCI service identity, and cognition scope. Project AGENTS and current AOCI identity take precedence over historical Memory for AOCI state.

   Treat a task as strictly zero-write only when the user explicitly prohibits Ledger, metadata, `.aoci` runtime assets, and every filesystem write. If necessary cognition establishment conflicts with that boundary, report the conflict and ask the user to decide or recommend an isolated copy. Never silently substitute Memory for current repository cognition.

3. If the repository has no usable complete index, or has only a minimal skeleton, an incomplete Header, unfinished Entries, or undecided required Curation, obtain `aoci_rules` and enter the current AOCI Guide when a formal complete AOCI index is required. Let Guide choose the next phase from actual repository state and complete the required safety steps.

   `aoci_maintain` does not replace the index-establishment workflow.

   Do not reconstruct or hard-code the full-index generation state machine in this file.

4. During a long-running task, the model is responsible for preserving the current cognition receipt and using the refresh gate correctly:

   - when the Host reports context compaction or the model knows the system-wide view was lost, follow the mandatory `context_compaction` reload rule above; AOCI cannot infer the Host event;
   - when entering a genuinely major phase, declare `phase_transition`, not a function, test run, or small step;
   - at a plausible stable checkpoint, use `check_only=true` to obtain the machine semantic count when that fact is useful;
   - except for the mandatory known-compaction reload, decide whether the current task needs another explicit scoped or complete Overview; and
   - keep the Dirty or Stale reliability state reported by AOCI until maintenance and alignment complete.

### Task closing and cognition maintenance

5. A purely read-only question, analysis, version check, or task that changes no AOCI-managed object does not require a maintenance-tool call. The AOCI version in use is `cognition_receipt.mcp_service_version` in any `aoci_overview` check_only or `aoci_maintain` response; the binary path is the `command` in the project's `.mcp.json`, and the CLI need not be on PATH.

6. When AOCI-managed objects change, call `aoci_maintain` once after they reach the task's final stable state. Do not maintain files individually after each intermediate edit.

7. If maintenance returns actual semantic candidates, the Host model must independently author the complete tag and F/R/A/S updates from each candidate's bound object and necessary evidence. Submit the complete candidate set for that current machine-issued batch in one `aoci_update_entry` call while preserving each `source_sha256`, `candidate_id`, and domain batch identity. `max_entries` limits one request and atomic transaction, not the logical plan, Whole-Index, or Managed Scope. When `remaining` is nonzero, call Maintain again after the successful Apply and continue from the new preimage; never shrink Index coverage or slice a returned batch to satisfy transport limits.

   When evidence is insufficient and the current layout supports `aoci_report`, use it instead of guessing, applying a template, or generating unsupported cognition merely to eliminate follow-up work.

8. Obey structured tool states and safety boundaries:

   - `repair_required`: repair only the explicitly identified candidates, then resubmit the complete current machine-issued batch;
   - `stopped`: end that write attempt and inspect `failed_step`, error, formal-write evidence, and Recovery. In auto mode, a proven zero-write closure is followed by a fresh Plan; a complete Intent with provable postimage is resumed; a policy-selected Rollback with exact preimage is completed and replanned. Stop the user task only when proof is unavailable, third-party bytes conflict, approval or external action is required, or another real safety boundary applies;
   - never ignore conflicts, approvals, human decisions, permissions, or safety signals; and
   - after alignment, do not repeat maintenance or writes; `refresh_ready_for_overview` is a checkpoint fact, and the Agent decides whether to request an ordinary complete Overview for its next phase.

   If any managed object changes after maintenance completes, the previous result is invalid. Complete closing again from the new final stable state.

9. When the user limits only business-file scope and does not explicitly forbid repository-managed assets, AOCI-managed assets may be updated during closing to preserve cognition consistency. Distinguish them from business files in audits and commits.

   When the user explicitly forbids changes to `aoci.txt`, `.aoci`, metadata, or any additional file, obey that restriction, do not write, and report any remaining inconsistency accurately.

### Specialized workflows

Initialization, complete-index generation, Header generation, Entries generation, database-structure indexing, Curation, human review, and failure recovery must follow only the instructions, commands, and safety stops returned by the current AOCI Guide or tool at the corresponding stage.

Do not preload, guess, or reconstruct these specialized workflows. The relevant Guide, tool descriptions, model Prompt, and CLI help provide platform invocation, request format, batch limits, approval rules, index-format details, and recovery steps as needed.
<!-- aoci:end -->

# Morphogenesis 执行约定

用户当前指令优先于开发包。业务事实源为 `docs/source/README_包内说明.md` 列出的现行文档；v1 仅存档。

- 核心原则：官方实现优先、成熟开源依赖优先，只自研差异化机制和必要适配。引用或复制代码记录来源、版本、许可证；不自行重写调度器、Attempt 系统、Manifest、哈希或完成证明系统。文档所需 AttemptId 只是数据身份，使用 Pydantic，不扩建基础设施。
- 当前一页计划和文件所有权见 `docs/PLAN.md`。每条轨道固定一个 Agent、一个 Orca worktree、一个分支。只能修改该轨 write_paths；跨轨请求通过 Handoff。
- 主 Agent 只维护计划、状态、决策和验收。开发、测试、文档、返修由原 Worker 完成；最后由集成 Agent 合并，只改少量导入、配置、类型和路由胶水，领域问题退回原 Worker。
- 优先复用既定 Python / LangGraph / Pydantic / SQLModel / SQLite / httpx / MCP / 官方 GEP SDK / ECharts 技术栈，不为并行改目录。锁文件由 T0 独占。
- 每阶段 commit，完成 push。禁止 force push、覆盖历史、丢弃其他贡献。秘密与本地运行产物不得入库。
- contract_local、interface_live、task_live 分开；模拟、回放、生成代码、单测通过均不可冒充真实运行验收。未知远端效果不自动重试。
- Hub 沙箱信息未提供：只联调本地隔离 stub，显示待发布。ORCA 运行时供给接口未提供：使用固定规模蜂群。T4 可选进化不进入当前核心闭环。
- 最终仅报告完成内容、分支和 SHA、验证命令与结果、真实限制、未执行或人工操作。
