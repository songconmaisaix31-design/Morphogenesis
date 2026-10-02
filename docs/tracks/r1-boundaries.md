# Q independent R1 boundary acceptance

Scope: Q owns only `tests/integration/r1_security/**` and this report.
Domain repair belongs to original A/B/C owners. No owner helper imports,
candidate execution, scientific model calls, paid sandbox, or external network.
All results here are `contract_local`; interface/task live and L2/L3 are NOT_RUN.

## First observations (preserved)

| Owner | Exact observed source | First command/result |
| --- | --- | --- |
| A | `48eeebd6c7fcfaf797d297ea5d73eb0673bddb46`, initially clean | `.venv-q/Scripts/python.exe -m pytest tests/integration/r1_security/test_a_host_boundaries.py -q --tb=short`; collection ERROR, exit 1, `ModuleNotFoundError: No module named 'faiss'` |
| C | `71bfedbfd0cf4b6581f36cfdc70281bc877f71c8`, initially clean | Same command with `test_c_feedback_boundaries.py`; collection ERROR, exit 1, missing faiss |
| B | `fbee1e5edee5f5d0cb72141f511fdfc724633f69`, clean | Same command with `test_b_generated_boundaries.py`; **6 failed, 6 passed**, exit 1 |

Each command selects the source via `R1_SECURITY_SOURCE`; dependencies were
installed only in Q's `.venv-q`. Initial unconstrained install selected MCP 2.2.0
and checkpoint 4.2.0; these were corrected to MCP <2 and checkpoint <4 before any
tests. Missing faiss was then installed with declared numpy/scikit-learn ranges.
These environment collection errors remain historical evidence, not domain failures.

B first RED assertions (2026-10-03 local):

- Mock `verified=True`, `probe=passed`, and all capability booleans reached
  `backend.create` (call count 1, expected 0). That method is a raising sentinel;
  no sandbox or candidate code was executed.
- Caller-supplied `approved=True`, `approved_by=invented`, and
  `reviewer_independent=True` returned `mode=final`, expected diagnostic.
- For each `unknown`, `failed`, `timeout`, the durable archive reader retained
  a caller-written assessment with trusted=True and contribution=accepted.
- Succeeded execution with unknown remote effect/cleanup returned final science.

Initial review Handoff `msg_2ebc81913dc4`; B first RED Handoff `msg_76bac0647ec8`.
After dependency installation, exact archive A produced **14 failed / 4 passed**
and C **3 failed / 8 passed**, both exit 1. A's `after_enqueue` recovery returned
blocked, rather than accepted, after reopening both persistent stores; the other
A failures were authorization and payload collision assertions. C's fabricated
supported/refuted contributions and accepted-label synchronization persisted
without any ledger task/report. Handoffs: A `msg_6f9f033fb5a7`, C
`msg_590b78b735b8`, coordinator `msg_99576b750b1b`.

The verbatim domain outputs are in `tests/integration/r1_security/evidence/`.
B's saved output is explicitly a repeat of its first RED using an exact archive;
it is not relabeled as the first invocation. Original first counts/assertions are
above. A/C saved outputs are their first collected domain test executions.
Coordinator authorized exact ordinary merges only for read-only test source,
but Q initially uses exact git archives to avoid owner WIP and helper collection.

## Verification map

| Boundary | Q black-box entry | Spec / acceptance |
| --- | --- | --- |
| Host project/authorization; cross-project branch/derived task | ResearchService / ResearchKnowledge | FR01-11, AT01-04,09,14-15 |
| Scope/capability; durable proposal put/enqueue/bind recovery; identity collision | ResearchService plus persisted reopen | FR06-07, AT03-04,14-15 |
| No host execution; untrusted isolation/approval labels; full plan binding | GeneratedExperimentExecutor / archive reader / evaluator | FR15-20, AT05-07,12-15,17-18 |
| No fabricated contribution; failed/unknown no reward; corrections preserve history | ResearchFeedbackStore / research_feedback / policy | FR12-14,24, AT08-11,14-15 |

## Current disposition

Independent acceptance is in progress. First RED remains unaccepted; original
owners must return exact pushed repair SHAs before final verification. This report
does not approve R1 or live science. Budget envelope resets, native process
containment, and real isolation capability probes need separate evidence.

## Expanded negatives and preserved results

- A48ee: authorized voluntary claim, scope/capability/dependency claim denial,
  and persistent max_tasks across branch/member reopen passed (5 cases).
  A private task linked from a note was accepted: 1 new RED.
  Handoff `msg_811c8b65115c`.
- Bfbee: succeeded archive without output digest/size binding was accepted:
  1 new RED. Handoff `msg_b6976c3faaef`.
- C71bf: a deterministic known-effect submitted counterexample is projected by
  the original trusted ledger/store chain. Nominating an unknown reviewer or an
  actor who only claimed an unrelated task both grants acceptance: 2 new RED.
  The fixture writes existing contracts only and never executes candidate code.
- C successor changes the store constructor to bind assets_root and removes
  synchronize. Q's helper recognizes that constructor; removal of the unsafe
  import entry still requires an empty contribution store. No original
  assertion/threshold has been loosened; original first RED remains in commit
  `6ceb2e2` and logs. A successor result-ID acceptance API is exercised directly
  by the result-bound reviewer negative.

All additional raw results are in the same evidence directory. Task-count
envelope checks establish only persistent TaskLedger limits, not financial,
model, data-export, or sandbox runtime enforcement.

## Review checkpoints (not final acceptance)

- Official in-process FastMCP tests initially hit Q's network guard while
  Windows asyncio created a stdlib self-pipe: 2 failures, no tool invocation.
  Saved in `a-48ee-mcp-negative.txt`. The fixture now creates the trusted stdlib
  loop before guarding all test/tool calls; network/process denial remains active.
  The actual A48ee tool run produced 1 pass (host impersonation denied/ignored)
  and 1 RED (cross-project read), in `a-48ee-mcp-domain.txt`.
- A WIP diagnostic: 25 pass / 1 RED (authorization_ref), not tied to a final SHA.
  Q's original exception-only assertion is preserved in `6ceb2e2`. Coordinator
  `msg_1b36908dd46e` required the actual invariant: reject OR retain host authority.
  The successor test reopens storage and checks persisted HostConfig authority;
  old source still fails because it persists the caller's reference.
- C WIP first interface check failed 12 / passed 1 because the new constructor
  requires a host-bound reviewer. Q adapted that API without changing safety
  assertions. A subsequent diagnostic passed 13 / failed 1: an invented review
  observation with no ledger task/lease/run granted acceptance. Handoff
  `msg_4c450a93c76a` requests validation of the review's authoritative lineage.

WIP counts are repair diagnostics only. No immutable owner candidate is accepted
by these checkpoints, and later green results cannot rewrite first RED.
