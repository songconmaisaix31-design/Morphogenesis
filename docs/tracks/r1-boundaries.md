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

## Exact repair candidate checks

- C `40011761c3cce6513bbeef776543740f60d1d03e`, coordinator-delivered pushed SHA:
  exact git archive, Q suite **13 passed / 1 failed**, exit 1. **NOT_ACCEPTED**.
  A forged reproduction observation has no matching ledger task/run but still
  authorizes contribution acceptance; the raw reviewer/purpose strings remain
  an authority bypass. Full output `c-4001176-first-red.txt`. The constructor
  and result-ID call adaptation preserves the same invariant and does not
  count a TypeError as PASS. B WIP 13 pass is diagnostic only.

## Additional P scope

Coordinator `msg_b08511c45c19` added read-only P loop review. P source baseline
is `9eada755eddb71d53d461577f6054dc34fce96cf`; loop/backend files were uncommitted
WIP and no P exact candidate has been accepted. Q writes only its own tests.

`test_p_loop_boundaries.py` requires explicit `R1_PRODUCT_SOURCE` and uses real
R1Store plus actual HostConfig-bound ResearchService/TaskLedger read-only context.
First P WIP result **2 failed / 1 passed**, exit 1, `p-wip-first-loop-red.txt`:
mock-labeled unknown/refused effect permits another phase/retry; known core
context is blocked solely because its provenance is non-mock. Unapproved
envelope blocks backend calls. Handoff `msg_8393a49aef40` to original P.
There is no fake eight-stage mock completion and no model/candidate execution.

## Additional authority coverage

C4001176's authoritative source projection rejects actual submitted records for
crash, timeout, unknown execution, and succeeded execution with unknown effect:
**4 passed**, exit 0 (`c-4001176-unknown-projection.txt`). This strengthens the
earlier caller-object negative; it does not accept the still-failing reviewer path.

B successor WIP: full bound-output recomputation discards caller score/reward,
and 14 generated cases pass. Two new probe-reference cases fail: a host fixture
record with probe_id=host-probe authorizes IsolationReport proof_ref=null or
invented-probe. `verify_isolation` does not bind the claimed reference to the
registered record. First diagnostic **2 failed / 14 passed**, exit 1; Handoff
`msg_de80b96316bc`. This is deterministic host-authority input, not a live probe
or scientific result; the final host construction path still needs Owner Handoff.

## Latest immutable checkpoints

| Candidate | Q result | Disposition |
| --- | --- | --- |
| B `a322cfd53f5c330654e19a6add8438a3f8c5fab4` | exact archive, 14 pass / 2 fail, exit 1 (`b-a322-first-red.txt`) | NOT_ACCEPTED: probe_ref missing/different still authorizes |
| P `f4799298e530f47fbdac99afc795e6b40969e4eb` + A48ee source for core read fixtures | exact archives, 6 pass / 3 skip, exit 0 (`p-f479-corrected-boundary.txt`) | narrow boundary check only; deleted incorrect loop, core wiring NOT_RUN |

P removed loop/backend and record_loop/loop_position, so the three legacy loop
tests now explicitly skip with the unmet native integration reason. Six new
tests prove removal of parallel authority, envelope approval cannot certify
science, and mock/replay/contract_local product event labels cannot change a real
core task's owner/status. These do not establish P end-to-end or R1 capability.
The first P archive command exited 1 with no captured stdout; Tee-Object did not
create the intended `p-f479-exact-boundary.txt`. A verbose retry found a Q test-placement mistake:
3 failed / 3 passed / 3 skipped (legacy block appended to a new test). Q corrected
the placement, preserving this history and the original WIP RED. No domain
threshold changed. B exact RED coordinator Handoff `msg_04a4509540cd`.

## Independent review and generated admission follow-up

C `40011761c3cce6513bbeef776543740f60d1d03e`: a positive independent
counterexample uses distinct real local ledger claim/begin/confirm/submit and
store observation identities. It is accepted once, survives reopening, and
supersession appends history. **1 passed / 3 failed**, exit 1
(`c-4001176-review-effect-red.txt`): a review with failed execution, unknown
execution, or unknown effect still authorizes the original contribution.
Handoff `msg_ef17d21d6bfc` goes to the original C owner. These ledger fixtures
are contract_local facts; no experiment or candidate executes.

B `a322cfd53f5c330654e19a6add8438a3f8c5fab4`: initial additional validation
tests hit Q's subprocess guard when the trusted GEP bridge tried to run Node;
**2 failed**, preserved in `b-a322-approval-and-manifest-red.txt`. Q then
supplied an injected bridge which admits only the exact inert, seeded Gene
dictionary by equality. This fixture does not verify production SDK asset
validation; the approval, validation and persistent store functions are real.
The actual domain check is **2 failed**, exit 1
(`b-a322-approval-manifest-domain.txt`): caller-modified `passed=True` approves
a persisted failed report with invented proof_ref/default no-op fencing;
changed source bytes outside the frozen manifest still pass validation.
Handoff `msg_4e104efa3e61` to current B and `msg_99d8adbdf960` to coordinator.
All child processes and network remain denied during test calls.

B a322 SDK configuration tests: **3 failed**, exit 1
(`b-a322-sdk-configuration-first-red.txt`). A replaced SDK create function
captures arguments and returns only an inert fixture ID; no sandbox or SDK
network request occurs. Actual adapter configuration omits network_policy,
sends the bare image digest without its repository, and allows direct create
without verified process-limit/isolation instance authority. Unsupported
controls must refuse before create; declaring network/process booleans is not
enforcement. Source inspection additionally finds registry matching only a
backend name/capability set, without endpoint/runtime/environment/configuration
binding. Review Handoff `msg_568c2c09267c`, exact reproduction
`msg_ad45f34519ca`, coordinator `msg_f4c22f417513`.

## C trusted-review repair checkpoint

Coordinator `msg_aaae8ebffdc7` confirms original C owner delivery
`msg_b8ccbbbec65b`: pushed stage candidate
`3161048c463b3aa4f434054755afc9787bbda989`. Q used a fresh exact git archive,
set `R1_SECURITY_SOURCE` to that archive, and ran
`.venv-q/Scripts/python.exe -m pytest tests/integration/r1_security/test_c_feedback_boundaries.py -q --tb=short`:
**22 passed**, exit 0, 5.11 seconds. Raw output
`c-3161048-exact-boundary.txt`. All prior negative assertions and the valid
distinct-review/history positive control pass. C71bf/C4001176 RED remains
historical evidence. This is acceptance of the covered counterexample/review
boundary on this stage candidate only; B generated projection and the merged
installed native research chain remain pending, not R1 or live science PASS.

## Integration checklist and limits

Before I accepts the successor, the exact merged source must expose the dynamic
generated plan through the HostConfig-bound formal MCP/service path and bind
the three scientific axes to the original ledger/store and independent review
facts. A's read-only current service/server/experiments scan has no
GeneratedExperimentPlan or ScientificContributionStore wiring yet; owner WIP
and future integration glue are not evidence of that capability. P's removal
repair alone is not a native dynamic research loop. Verify the final installed
core/product combination separately; Q's source imports and local dependency
environment are not installed-wheel acceptance.

Q's deterministic crash injection covers proposal-put/enqueue/bind recovery,
not operating-system process kills or a real remote unknown effect. Task-count
persistence across branch/member reopening is covered; model/fee/data export
and sandbox resource enforcement across product runs remain NOT_RUN. Official
MCP tool tests are in-process, without a live transport. AT07 real isolation
probe, L2/L3, interface_live and task_live remain NOT_RUN. No candidate, model
research, new sandbox, probe, paid backend or external data operation was run.

## Expanded host/configuration scope

Coordinator `msg_b8c6b6c41499` adds P material-root and service read/provenance
boundaries and B's actual probe configuration, without expanding Q write paths.
Orca ask `msg_032ac8a3f5c1`, answer `msg_809961677e5c`, requires this dispatch
to wait for final receipts. A stage candidate
`7fc1e80845128080dfbcd5899aa9a09e37128753` is archived but Q26 run awaits the
main-controlled resource window. Formal dynamic integration remains separate.

B current WIP, eight prepare/admit-only tests in
`test_b_probe_configuration.py`: **7 failed / 1 passed**, exit 1, 6.29 seconds;
`b-wip-probe-configuration-first-diagnostic.txt`. Conflicting duplicate probe ID
silently replaces evidence; effective image, CPU, memory, process limit, endpoint
and network changes consume unchanged probe identity/capability claims. Exact
duplicate record construction is retained as a positive control. This is a WIP
diagnostic, not immutable acceptance or a valid isolation-probe claim. The
current API cannot bind the full configuration; an incomplete host record must
refuse. Full correctly configured admission needs the owner's actual new schema
and a separate positive control before acceptance. No create/execute/SDK call.
Original B Handoffs `msg_871e5db6f626`, `msg_4a37a68adc04`.

P exact `76b02298355241e1366cdd4ce1ffbadc6ce69d9f` is archived. New nine tests
in `test_p_host_boundaries.py` are **NOT_RUN pending resource window**: deny empty
host roots, retain explicit allowed-root import, deny parent traversal, prevent
caller envelope (including approved boolean) from widening handler roots, deny
foreign project callbacks, retain valid project read, and do not invent live
provenance from local service connection. Fixtures use Q-created inert text
only; there is no user/private file, server socket or scientific result callback.
Review Handoff `msg_91f820239256`. Owner WIP is not final evidence.

Coordinator `msg_a0775d2500d7` delivers exact B stage
`d175f7e2f8c3ff41a1ac8a2a4958c68acf57e275`. Fresh archive, single-process
`.venv-q/Scripts/python.exe -m pytest` on all four `test_b_*.py` files,
`-q --tb=short`: **21 passed / 8 failed**, exit 1, 20.45 seconds;
`b-d175f7e-exact-first.txt`, **NOT_ACCEPTED**. Generated14/successor4 pass:
failed-report forgery and manifest byte substitution are now refused. Two SDK
configuration cases refuse before create on inconsistent image, which does not
prove correctly configured SDK admission. Unverified direct backend creation
and all seven conflicting-probe/configuration negatives remain RED. Original
B `msg_6497a8e52900`, coordinator `msg_81d03bd42507`.

Coordinator `msg_be9c1eb32b1e` delivers P stage
`550e1d43b43a9b668d5255fd8f01d0a67c763c49`, archived but Q9 still awaits window.
Source uses host roots and provenance defaults to unknown. Callback API now
receives project_id; Q sentinel accepts that argument while preserving zero
callback reads on foreign project and one read on valid project. Forwarding an
ID alone does not authorize it; the stage still lacks host project validation
before projection. Read-only Handoff `msg_a8f584b0b3e7`; no TypeError is counted
as a safety PASS. Full configured product/PDF/native integration stays pending.

P material subset runs use lazy core imports so they do not construct the actual
research service or an HTTP server. Both commands select the explicit exact P
archive plus A7fc1 source, run `test_p_host_boundaries.py -q --tb=short -k
'host_roots or host_root or parent_traversal or caller_envelope'`:

- P76b0229: **3 failed / 2 passed / 4 deselected**, exit 1, 2.37 seconds;
  `p-76b0229-material-first.txt`. Empty roots authorize an arbitrary local file;
  both False/True caller envelope booleans widen the handler's host roots.
- P550e1d4: **5 passed / 4 deselected**, exit 0, 2.58 seconds;
  `p-550e1d4-material-exact.txt`. Trusted positive import retained; all root
  negatives refuse before any read of the own inert outside fixture.

Original P Handoff `msg_24b038c0f466`. First RED is unchanged. Only Q-created
text is read; UI view formatting is a deterministic fixture while actual
handler routing/parser/persistent store authorize the operation. Four service
project/provenance cases still await the resource window. This subset is no
claim of configured product, PDF, installed/native science or R1 acceptance.

## Runtime recovery and exact A/P service checkpoints

Q resumed the same branch/task at `dc8a81c507d1f99674f1341c56f284f57f8c4608`
after the Orca restart, under replacement dispatch `ctx_e8614b81faa5`. Two
pre-restart outputs were already durable but untracked; they are preserved in
the evidence commit together with the separate recovery repeats. No original
file was overwritten. First retained outcomes: A7fc **26 passed** in 7.11s;
P550 service **2 failed / 2 passed / 5 deselected** in 2.92s.

The explicitly granted sequential short window reran exact A
`7fc1e80845128080dfbcd5899aa9a09e37128753` and exact P
`550e1d43b43a9b668d5255fd8f01d0a67c763c49` from existing private archives,
using `.venv-q/Scripts/python.exe -m pytest`, `-q --tb=short` and process-only
OPENBLAS/OMP/MKL thread limits of 1. All Q process/network guards remained on.

- `test_a_host_boundaries.py`: **26 passed**, exit 0, 17.64s;
  `a-7fc1e80-recovery-repeat.txt`.
- `test_p_host_boundaries.py -k 'foreign_project or authorized_project or connected_local'`:
  **2 failed / 2 passed / 5 deselected**, exit 1, 4.31s;
  `p-550e1d4-service-recovery-repeat.txt`. Both three_axis and route_opportunities
  invoked the trusted callback for p2 under a p1-bound ResearchService. Merely
  forwarding project_id to a callback is not authorization.

The window was released by `msg_07f1ab25225c`; original P repair Handoff
`msg_a266bfb8d5b0`. Coordinator `msg_3de398c9a49f` accepts only these exact
bounded results. P WIP now checks service.project before callbacks; this is
not yet Q-tested or an immutable accepted candidate. Raw results were pushed
in evidence SOURCE commit `967c75a`.

Read-only follow-up Handoffs (new tests are NOT_RUN pending the next serialized
window): B `msg_0491bb0a84a6` covers candidate identity/revision/byte substitution
and data/code/runner collisions; C `msg_9fd970eb497b` covers advisory references
that must resolve to effective accepted original facts; A `msg_310b7bc28009`
covers newly exposed correction, supersession, project/scope and future-advice
boundaries. New positive controls retain legitimate data, persisted candidate,
independent refutation and legal sleep/reopen. The original assertions remain.

The actual generated persisted-trust projection, project-wide budget reservation
across new task/branch/run and unknown effect, configured P factory and final
exact core/product combination still require original Owner source delivery and
Q verification. L2/L3, real probes, scientific execution and external materials
remain NOT_RUN; no new worker or global environment changes were made.

## Input and advisory first RED after recovery

Coordinator `msg_039c88daa1db` granted only two sequential pure-fixture checks
in the existing private environment while B installed its private dependencies.
No Node/native process, candidate, sandbox or network call occurred.

| Exact archive | Q command (after private python -m pytest) | First result |
| --- | --- | --- |
| B `d175f7e2f8c3ff41a1ac8a2a4958c68acf57e275` | `tests/integration/r1_security/test_b_input_binding.py -q --tb=short` | **7 failed / 1 passed**, exit 1, 2.35s |
| C `99cd2997dd024a41c28461228f47a575fef3f9ab` | `tests/integration/r1_security/test_c_advisory_binding.py -q --tb=short` | **6 failed / 1 passed**, exit 1, 3.99s |

B's data may overwrite the candidate path, conflict with the runner, repeat a
manifest name or exceed the aggregate input bound without failing preparation.
Its validation also certifies an unrelated asset ID, revision or stored byte
payload. Each asset negative first proves the unchanged persisted candidate is
valid under the same host fixture authority. The disjoint inert-data positive
also passes. Original B Handoff `msg_1e2cc212b1e7`.

C's advisory retains invented supported/refuted IDs and reuses a real result
on a foreign branch, under the wrong hypothesis axis, repeatedly, and after
supersession. Its nonempty positive builds independent original ledger/store
executions and accepts a refutation once; that real result lowers the linked
branch opportunity. Original C Handoff `msg_7c0bfd1ca735`.

SOURCE `e7e1805c9f34351a6139de54732cff51d00591b0` preserves tests and raw logs
`b-d175f7e-input-binding-first.txt` / `c-99cd299-advisory-first.txt`. The latter
retains pytest's original whitespace-only diff line, so the evidence-inclusive
`git diff --check` reported that line; source assertions were not changed.
The older C fixture gains an optional branch_id (default absent) and copies
the original task payload into its independent review signal. This adds lineage
for new advice tests without changing the old tests' data or assertions.

Window released by `msg_a44c9f8e4b51`. A new policy/correction tests remain
NOT_RUN. Read-only review of new generated report code found B requiring the
candidate author's source_attempt while C requires the current review execution
attempt; Handoffs `msg_ebc5bf6469cc` and `msg_393526310efc` request one consistent
original execution lineage and a nonempty independently reviewed positive.
These repair checkpoints are neither final Owner acceptance nor R1 PASS.

## P host repair and successor configuration controls

P delivered SOURCE `cedbf3bc52eaabd4814e43068428e89a49ab5cf9`; coordinator
`msg_704adcdf4f64` granted the exact Q12 window. A fresh P archive with unchanged
A7fc and private BLAS1 environment ran `test_p_host_boundaries.py -q --tb=short`:
**12 passed**, exit 0, 3.17s. `p-cedbf3b-host-first.txt` preserves this first
candidate outcome. Original material-root and callback negatives pass; three
additional tests reject a private-scope task and a same-scope foreign-project
task while preserving a real permitted note read. This uses the actual public
ServiceBackend and original stores, without constructing a socket server.
Window release `msg_d9eb7509a234`, original P receipt `msg_1a5306edc854`.

Q SOURCE `63fe5ead51e05fc2f718ebcfe942942d82d90abf` also adds currently NOT_RUN
tests for fully configured SDK request capture (one nonempty positive, twelve
effective-setting substitutions, two prepare/admit mutations) and actual service
BudgetLedger admission (six cases covering known allowance, unknown/crash,
reserve/begin interruption and replacement run/database). B's new full
IsolationConfiguration fixture uses the same canonical image, resource profile,
endpoint, deployment and process limit on the host record and report; candidate
seeding takes that same frozen plan. No assertion or threshold changed; the
historical unbound-fixture first RED remains in `e7e1805` and its raw log.

B has delivered stage `e8e16a5b9e755a94f8587b76ba9fc288f218b8af`, now archived.
Owner test reports are not Q acceptance. The real generated observation reader,
trusted three-axis projection and original consumption/adoption remain under
review. Coordinator `msg_d7c25aad3900` permits explicit isolated mock L1 adoption
only through the existing chain, requiring provenance retention and default-live,
mixed-mode and reopen refusal checks. No real science or probe was authorized.
