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

## Exact host, SDK and generated-feedback stage verification

Coordinator `msg_6e9cb55ceec4` allows sequential Q pure-fixture sets of at most
100 tests in the existing private environment. Process-only BLAS limits remain
one; the autouse process/socket guards remain active. The following independent
checks use exact archives, not Owner working files. SOURCE
`71c46424d569f2967901684fa2c1c3c58dc71e33` preserves all raw outcomes and tests.

| Exact source | Q pytest files | Result |
| --- | --- | --- |
| A `8fc90a9a34d3b47ced952510ea53ce2412dc38ca` | `test_a_host_boundaries.py test_a_research_policy_boundaries.py test_a_project_budget_boundaries.py` | First **35 passed / 2 failed**, 10.95s; bound legitimate fixtures **37 passed**, 13.49s |
| B `e8e16a5b9e755a94f8587b76ba9fc288f218b8af` | `test_b_generated_boundaries.py test_b_successor_authority.py test_b_sdk_configuration.py test_b_probe_configuration.py test_b_input_binding.py test_b_configured_sdk_boundary.py` | **52 passed**, 2.41s |
| C `d7e561f9b4d6155316f12471de050c09b12471b4` | `test_c_feedback_boundaries.py test_c_advisory_binding.py test_c_generated_trust.py` | First **40 passed / 1 failed**, 10.91s; generated12 after explicit immutable-write assertion **12 passed**, 5.61s |

Commands use `.venv-q/Scripts/python.exe -m pytest` with the paths above under
`tests/integration/r1_security/`, followed by `-q --tb=short`, and the matching
`R1_SECURITY_SOURCE` archive. No failed output was replaced.

A's two first failures identify Q legitimate-fixture gaps under its stronger
contract: the authorized MCP task lacked a project payload and the sleep/reopen
positive cited nonexistent notes. Q adds the actual project identity and first
persists the two notes through `submit_note`; every prior business assertion is
unchanged. Six project-budget cases independently pass, including a real
BudgetLedger hold after reserve/begin interruption, unknown effects and worker,
branch, task or database replacement. These are inert boundary calls, not paid
or scientific executions.

B now passes all historical29, data/candidate-binding8 and configured-SDK15.
The SDK positive captures one actual supported `SandboxSync.create` request
with its effective image, resource and network policy, stopping at the injected
boundary; twelve configuration substitutions and two post-prepare mutations
refuse before SDK creation. This closes the bounded d175 first RED cases, not
live OpenSandbox acceptance.

C's generated positives bind actual original TaskLedger tasks, claims, fenced
execution audit, original report rows, frozen host criteria and deterministic
raw archives. Both supported and refuted results require a separate review
task/actor/run/sandbox, contribute once, change advice and survive reopen.
Crashes, unknown execution/effect, same reviewer/sandbox, absent review and late
criteria are refused. Raw-output/evaluation tampering cannot obtain credit.
The last initial failure was SQLite rejecting Q's attempted reviewer substitution
with `immutable_local_evidence`; Q now asserts that rejection and unchanged
original row/trust, instead of assuming the protected write succeeds. Original
Handoff `msg_4e0faa41eb69` and coordinator result `msg_da85c55e6dc5` preserve
the distinction between fixture repair and domain failure.

This stage is contract_local. B's newly delivered mock inheritance/adoption
SOURCE `d0c834fd381fc292443bf85c5ce1e91043143516`, A's complete generated
formal service chain, P's configured factory and final combined exact candidate
remain to be independently checked. L2/L3 and external materials remain NOT_RUN.

## Original mock adoption and product material first RED

Q SOURCE `5fc892c` adds `test_b_mock_adoption.py` and
`test_p_material_identity.py` with preserved raw evidence. All runs are sequential
private-environment `python -m pytest <file> -q --tb=short` under the same
process/network-deny fixtures and BLAS1 settings.

* B exact `56b8db589ee04bcc41652bb5e38793a1216f9a1a`, mock12 first:
  **8 failed / 4 passed**, 6.27s. The Q fixture left the approval lease active;
  the original TaskLedger correctly refused later same-scope claims. Q now
  performs the real approval and releases that lease before original/review
  tasks. Failed/unknown review eligibility is checked directly at fetch, leaving
  its unknown ledger hold intact. No domain assertion or guard was weakened.
* The same B exact candidate with corrected fixture: **9 passed / 3 failed**,
  6.44s. The true failures are original archived output, evaluation and
  environment changes still allowing `AssetConsumer.inject/execute` to produce
  an inherited candidate. Prior original/review and approved-asset positive
  controls pass before each change. Handoff `msg_c386db7350f8`; Owner confirmed
  the cached eligibility gap and is adding original-reader rechecks with the
  host criteria registry.
* P exact `cedbf3bc52eaabd4814e43068428e89a49ab5cf9`, material9:
  **7 failed / 2 passed**, 2.65s. Same-locator changed source version, digest or
  extraction outcome is discarded. Same-source/text expert opinions with a
  different applicability, domain, time or dispute status are also discarded.
  Both unchanged retry controls deduplicate. Handoff `msg_c44d4c988955` asks for
  append-only history and the new receipt-selected identity at the HTTP route.

The B positive uses the installed `GeneratedFixtureBackend` and original
observation writer, actual original/review tasks, `AssetConsumer`, child local
revalidation, `AssetApplicator.prepare`, `TaskLedger.submit(apply)`, real inert
file writes and the original `AdoptionReceipt`. Receipt provenance is `mock`,
replay is idempotent and reopen preserves it. Default-live refusal, both mode
switch directions, root binding, mixed provenance, failed/timeout/unknown
review and using the fixture identity with the real SDK adapter all pass.
GEP and read-only Git plumbing are deterministic Q boundaries; Node/Git
subprocess adapter coverage is not claimed. The fixture backend visibly retains
`isolation.verified=false`, `probe=not_run`, and never executes candidate bytes.

The new failing cases are unresolved at this evidence checkpoint. The corrected
exact Owner successor, combined formal service chain and configured product
factory remain pending; none of these local results claims L2/L3.

## Exact archive repair and scoped-feedback rechecks

Q SOURCE `fff315b` preserves the repaired-fixture checks and new raw logs:

| Exact source combination | Own Q suite | Result |
| --- | --- | --- |
| B `2d50d08811aa2337b9c0166dc114513e292bce1f` | Historical52 plus `test_b_mock_adoption.py`16 | **68 passed**, 10.28s |
| C `4f83296af908352660ebf71e633e70a111eb2877` (contains B2d) | Original22, advisory7, generated16 | **45 passed**, 11.80s |
| P `f00631e6a11eee776574f8d1ff4319b318fd879a` plus A8fc | Host12 plus material9 | **21 passed**, 4.33s |

All use the same `python -m pytest <owned files> -q --tb=short` command and
exact archive environment selection as above. B fixture now passes the same
original host `TrustedCriteriaRegistry` to the store, executor and reopen.
Original assertions remain; the three B archive first REDs and seven P identity
first REDs remain in their earlier logs and commits. B additionally refuses
missing or substituted host criteria on reopen and rechecks original evidence
before apply and after actual file writes. Post-write corruption rolls back the
inert file, leaves the ledger task uncompleted and records no adoption.

C's four new locality controls first establish a real accepted contribution.
The matching host can still read it; a foreign scope or workspace sees neither
trusted results nor historical credit. A separate review workspace cannot
launder the original result into a contribution. Existing support/refutation,
correction, deduplication and archive checks still pass on the combined C/B SHA.

Handoffs: B `msg_c012fd30895e`, P `msg_677d9ae14b7c`, A
`msg_3b158e841bcf`. A's complete generated service/official MCP chain and the
final installed product combination remain pending exact delivery. These
bounded results do not substitute for final integration or real execution.

## Actual combined generated service through official FastMCP

Exact A SOURCE `0bcb320e843839f5f043fccd9f705d9dd9b7299e` includes B2d and
C4f by ordinary merges. Q `test_a_dynamic_mcp.py` invokes the actual official
FastMCP tool manager and original `ResearchService`, with the installed fixed
output fixture backend selected from HostConfig. No Owner helper is imported.

First `python -m pytest tests/integration/r1_security/test_a_dynamic_mcp.py -q
--tb=short`: **14 passed / 1 failed**, 19.17s. The adoption positive reached the
original service snapshot query, which Q's process guard refused. No process
was launched. Q supplies the same bounded Git/snapshot fixture at that second
native-plumbing import; all original business assertions and process/network
denies remain. Repeat: **15 passed**, 20.01s. Both raw outputs are preserved.

Nonempty positives cover proposed/chosen/claimed work, frozen candidate plan,
actual fixed-output execution, source-bound observation, completed original and
independent review, accepted support/refutation, future opportunity references,
reopen and a three-member inheritance sequence through original validation,
approval, fenced apply and `AdoptionReceipt(provenance=mock)`. The inert candidate
file is actually written only in the apply positive. Usage and actual cost stay
unknown, never zero; mere contribution does not create an adoption receipt.

Negatives refuse cross-project/branch/authorization, changed environment or
resources, self-approved changed evaluation, unapproved data and stale token
before execution. Failed/timeout/unknown outcomes cannot become refutation or
credit; the unknown run cannot resend after reopen. A different plan under the
same frozen task is rejected while the original acceptance remains intact.
Handoffs `msg_47efa881acbc` and `msg_af9c2ec5391e` preserve the first fixture
failure and exact subsequent result. Native Git/GEP adapter verification and
the final installed A/P combination remain outside this fixture result.

## One exact combined core and HTTP identity first RED

All three Q slices below use the same exact A SOURCE
`4afe462b08867b4662a0bd01ee89833e56ffb32b`, including final B SOURCE
`5faafe41b1732c83d165251600b688444186c702` and C4f. They run sequentially in
the existing private environment, with no process/socket guard exceptions:

| Owned pytest slice | Result |
| --- | --- |
| A host26 + policy5 + project-budget6 + dynamic MCP/artifact20 | **57 passed**, 38.28s |
| B generated/configuration/input52 + mock adoption16 | **68 passed**, 9.87s |
| C original22 + advisory7 + generated/locality16 | **45 passed**, 10.91s |

Thus **170 checks pass on one exact combined core**. Five new artifact controls
first retrieve the actual archived output, then cover input-file requests, path
escape, size limit and changed output. The public export contains original
execution and generated-validation facts, keeps `completion_claim=false` and
does not invent adoption. Native Git/GEP remain deterministic test boundaries.

Coordinator `msg_98a5be1b9b55` requested independent reproduction of P's
URL-selected member issue. Exact P `f00631e6a11eee776574f8d1ff4319b318fd879a`
with the same A4afe core runs `test_p_member_credentials.py`: **4 failed /
1 passed**, 3.83s. Absent, wrong, other-member and duplicate Authorization
headers all reach the reviewer backend. The tool is the actual official MCP
`submit_research_note`, and the valid-path control persists an unverified note
under the reviewer HostConfig identity. This is a real route-boundary failure,
not a comparison-helper test. Handoff `msg_43a6f3e41fb2`; raw
`p-f00631e-member5-first.txt` retains pytest's original whitespace diff lines.

Q SOURCE `0f7a609` also prepares currently **NOT_RUN** native19 and installed
factory4 checks. Native tests use real protected HostConfig files and original
project/budget stores, with only planner/probe/native-process boundaries mocked.
They cover explicit native authorization, provider-bound observer limits,
original pending/uncertain holds, no fabricated usage, forbidden tool events and
nine closed project/member/runtime/provider/model/scope/data-category egress
grant negatives. No actual CLI, auth probe or model invocation is authorized.

Installed factory tests keep the original `installed_core` VCS-pin check and
require actual noneditable site-packages for both packages. They exercise the
actual protected ConfiguredResearch constructor and handler-to-MCP call path,
source version links and restart/rebind boundaries, without creating a socket
server. `R1_SECURITY_INSTALLED=1` only prioritizes that environment's installed
packages over Q's checkout; it does not alter package metadata or the pin check.
Exact repaired P delivery and the serialized install window are still required.

## Product credential repair and native metering first RED

Exact P SOURCE `f942de2ed2a22fa8bd8c418c6b4bf2b7d59e83bf` with the same
A4afe core runs native22, member5, host12 and material9 sequentially in one
guarded pytest process: **47 passed / 1 failed**, 10.59s. Q SOURCE
`fc18b24e22e4671285d7e0afcfff56e99d169733` preserves the unchanged first output
in `p-f942de2-boundaries48-first.txt`.

All five actual member-handler controls now pass. Missing, wrong, other-member
and duplicate credentials stop before backend selection; the valid credential
still writes an unverified note through the original official MCP tool. Nine
host egress grant negatives and original pending/unknown budget holds also
pass. Native launch, CLI/auth probes and model execution remain inert fixtures.

Pre-test Handoff `msg_683bb63a3763` identified an original API mismatch: the
native observer returns bare token fields, whereas original `BudgetLedger`
parses a `usage` envelope. The new nonempty matching-event control confirms
this: observed input3/output2 is returned by the inert native adapter, but
original persisted budget tokens remain `None`, failing expected5. Missing or
mismatched event counts correctly remain unknown. Actual cost is still unknown
and no science contribution/adoption is inferred. Post-test Handoff
`msg_78e63bbf7105` sends this first RED to P for its own repair.

A final SOURCE `cc2e7227e1b423924c99113c9676ef8cc310e92b` was delivered.
Independent Git diff against tested A4afe contains only six owner stdio test
lines. Final C SOURCE `56de8e3f5d2abd1e1ba02218b422f0aba9847ae2` has no domain
diff against that A final in C feedback/policy, local assets or experiments.
This source comparison is not a substitute for the still-pending exact final
installed product/core combination gate.

## Native resume identity first RED

Coordinator review `msg_92372fc12bec` requested original-record resume scope
checks. Exact P f942/A4afe runs `test_p_resume_boundaries.py`: **8 failed /
1 passed**, 4.79s. Same-project/member completed records prepare a resume without
launching anything. Changed observation project/member/runtime, request
runtime/model/workspace, reservation member and missing request all reach
native planning instead of refusing. Raw `p-f942de2-resume9-first.txt` preserves
the first result; Handoff `msg_16407ecd2556` sends all eight failures to P.

The fixture uses actual protected HostConfig, core service factory, official
MCP catalogue and original BudgetLedger reservation/settlement. The saved
request and observation use original `LaunchRequest` and `NativeOutcome`
structures. Source mode substitutes the package-origin admission and native
launch planner only; this does not validate installation. Installed mode keeps
the original package-origin check. Neither mode reads auth configuration or
launches a native process, model or candidate. No new session proof mechanism
or business code is introduced by Q.

## Product repairs and public export contract

Corrected legitimate fixture inputs use original `forbidden=false`, the exact
closed host egress grant, and typed `ProbeResult`/`LaunchPlan`. No refusal or
budget assertion changed. Exact f942 native22/resume9 still gives **22 passed /
9 failed**, 9.05s, independently retaining all one-metering/eight-resume REDs.

Exact P `08afdb8ddb10721ce008fd91d88be1d38a15d3fc` with A4afe passes all 57
native/resume/member/host/material checks. Adding the older product-authority
file yields first **58 passed / 5 failed / 3 skipped**, 14.93s: five older tests
expect scientific fields on the input-only `R1Store.export_package`. Coordinator
`msg_a5ae6b6b6e6a` and owner `msg_f721f29e5636` confirm that public
`web.r1.export_view` now projects original core scientific rows.

The same five no-fabrication/no-authority assertions now exercise that actual
public export over original `R1Spaces`/`R1Store`; they are neither deleted nor
skipped. Empty scientific rows, unknown core identity, no authorization/route,
unchanged original TaskLedger, and retained untrusted event inputs are required.
A new fixture expectation that approval would echo true first fails; actual
store approval correctly remains false. That failure is retained, and the test
now asserts false authority plus the original declared input in its event.
Repeat: **6 passed / 3 historical skips**, 2.58s. The three skips concern the
withdrawn unsafe parallel loop and do not count as present functionality.

## Exact installed pair and independent SQLite race

Q SOURCE `7aa8d0632a86a162764031b14a62af352f582d4e` records this stage.
Coordinator `msg_30e76c42ea75` grants private dependency/install work. Initial
`uv pip check --python .venv-q/Scripts/python.exe` finds two checkpoint version
incompatibilities. Only this private environment's `langgraph-checkpoint` is
updated from3.0.1 to4.2.0; repeat83-package check passes. Initial and repair logs
remain separate.

Exact installed SOURCE pair:

- core `cc2e7227e1b423924c99113c9676ef8cc310e92b`;
- product `24f02a169a696afd1f4eb769a8c0dbb8ca052f95`.

`uv pip install --python .venv-q/Scripts/python.exe --link-mode copy` uses each
canonical HTTPS Git URL with its full revision; product installation adds
`--no-deps` after core dependencies and `pypdf==6.19.0` are resolved. The initial
Windows local-file Git URL parser error is retained, not recast as a product
failure. `python -I` checks real distribution `direct_url.json`, noneditable
origins and site-packages modules for both packages; unmodified `installed_core`
accepts the exact core pin. Final `uv pip check` passes all95 packages. No
installed source byte or package metadata is patched.

With `R1_SECURITY_INSTALLED=1`, process-local BLAS1 and all existing process/
socket denies, `python -m pytest <owned slice> -q --tb=short` gives:

| Installed slice | Result |
| --- | --- |
| Protected ConfiguredResearch and actual handler/MCP factory4 | **4 passed**, 4.51s |
| A host/policy/project budget/dynamic MCP57 | **57 passed**, 36.80s |
| B generated/configuration/adoption68 | **68 passed**, 9.48s |
| C original/advisory/generated45 | **45 passed**, 11.29s |
| P native/resume/member/host/material/public authority66 | **63 passed / 3 historical skips**, 15.33s |

Thus this exact pair has **237 passed and 3 historical skips** for the existing
owned gate. Factory checks use real protected config, member credentials,
shared authorities, actual HTTP handler-to-official MCP, claim/fenced release,
material version links, stable restart and refused rebind. The HTTP transport
stays in process; no socket server or native model process is started.

Coordinator `msg_9ac5dd5cb6c3` reports a separate Windows CI store initialization
race and returns it to B. Q independently reproduces it on installed cc2:
**4 failed**, 1.85s, all exposing `asset_store_settings.name` UNIQUE collisions.
Two real SQLite connections synchronize their original unprotected read; no
SQL results or data are mocked. Same live/mock configuration must admit both
workers; conflicting provenance/fixture roots must yield one domain refusal,
one intact two-field binding and unchanged immutable triggers.

Exact B successor `230d283848c0879ff9c349096548d3810c4b1954` adds only original
`BEGIN IMMEDIATE` and comments before settings reads. Independent archive run
of the unchanged four new checks plus previous68: **72 passed**, 10.05s.
Handoff `msg_9457a6b8eaf6` sends the no-interface-change result to the controller.
The old installed cc2/24f bytes remain unchanged; final repaired merge/pin and
installation still need verification. Additional coordinator-requested native
provider-destination binding review is ongoing. This is bounded local/mock
evidence, not real science/model/probe/sandbox/Hub/deployment or L2/L3 acceptance.

## Selected native provider authorization first RED

Coordinator `msg_a423817c5f54` requests checking actual selected provider binding.
Read-only review finds only grant/provider versus declared bound/provider
comparison. The original planner forwards the model and inherits native
selection; its configuration reads retain only MCP names. The original probe
reports version/authentication, with no provider-destination fact.

On the unchanged installed cc2/24f pair, `test_p_provider_binding.py` gives
**1 passed / 1 failed**, 2.34s. The fixture uses the actual protected HostConfig,
installed-core admission, service factory, original planner and BudgetLedger.
Its only native config is a credential-free temporary TOML file: approved
provider `q-mock` maps to `https://authorized.invalid/v1`; `foreign` maps to
`https://foreign.invalid/v1`. Matching selection passes. Changing the selected
provider to `foreign` while retaining the old host grant still reaches the
inert native boundary and returns success, failing the refusal assertion.

Only config-path discovery, executable resolution, version/auth probe and
headless execution are fixtures; no actual user configuration, auth material,
native process, model or network is accessed. This proves an admission gap,
not an observed data transfer. Raw `installed-cc2e722-24f02a1-provider2-first.txt`
is preserved. Handoffs `msg_09f3fb3344df` and `msg_05549e7614da` send the result to
P and the controller; P confirms the gap in `msg_eae6e4975a15` and owns repair.
The final safety gate remains open for that repair and the B concurrency merge.

## Actual provider binding repair, with nonempty native positives

P delivers SOURCE `5b1f076cb18d181037f4c5f052b6006705121c84`. Legitimate fixtures
add the existing frozen `data_bounds.native_provider_bindings` grant with exactly
`runtime/provider/base_url`, and the original request record's matching
`provider_binding`. Original refusal assertions remain intact. No current
configuration, credential, native executable or actual provider is accessed.

Independent exact P5b1/corecc2 archive run of native22, resume13, Codex provider10
and Claude gateway5: **50 passed**, 15.31s. Codex custom-provider and Claude
gateway positives traverse the actual service factory/planner and settle original
budget tokens5 while actual cost stays unknown. The same authorized non-secret
provider/destination is frozen in the invocation arguments. Native/probe/binary
boundaries remain inert, and source-mode package admission is explicitly a fixture.

Negative controls cover selected provider changes, same-provider endpoint drift,
missing/foreign/extra grant fields, active profile, managed/conflicting metadata,
Claude cloud route, and altered or absent original resume destination binding.
All reject before the relevant probe/reservation/native effect. Earlier unknown,
pending hold, exact usage, closed egress, member and resume checks retain their
assertions. Handoffs `msg_a1fa7aa9ba02` and `msg_0437d2f456e9` report this result.

FR-09 scope is bounded preparation/admission via original adapters, not universal
readiness of already selected accounts. Exact code requires an unambiguous
explicit custom Codex provider and rejects every nonempty `profile`/`profiles`,
managed route and listed built-in provider ID, including one with an explicit URL.
Q covers Claude gateway; the actual OAuth status path is not exercised here.
Unknown managed/cloud/socket routes remain refused. These limits are compatible
with fail-closed AT15 admission, but cannot be represented as live authentication,
native isolation, or support for all existing native configurations.

Old installed cc2/24f bytes and their first failures are untouched. Final merged
core/provider-fixed product installation remains pending. The B owner additionally
reports a separate original-worker deadline failure with unresolved cause; Q's
SQLite72 result neither explains nor overrides that owner evidence.

## Cloud route and case-equivalent metadata independent controls

Read-only review of P SOURCE `7a155c59672cc030b3d7916de04e47c71ec6c124`
adds five black-box admission controls to the same protected service/planner
fixtures. Codex selected custom-provider metadata must refuse cloud names
`Amazon Bedrock` / `Amazon Bedrock Runtime` and an `aws` route even when its
ordinary provider ID and URL match the prior grant. Claude must refuse a
lower-case cloud flag and conflicting case-equivalent destination keys.
Review Handoff `msg_a29a0146c076` precedes the test additions.

On exact previous P5b1/corecc2 archives these five refusal assertions give
**5 failed**, 3.48s. The same assertions plus the previous native/resume/provider
controls on exact P7a/corecc2 give **55 passed**, 14.97s. Raw
`p-5b1f076-cloud-route5-first.txt` and
`p-7a155c5-native-provider55-first.txt` preserve both outcomes. Legitimate Codex
and Claude gateway positives remain nonempty; probe/native/process/network
boundaries remain inert or denied. No real metadata or credential is read.
Handoffs `msg_94d1a18473f6` and `msg_4db908e3f9e4` deliver this bounded result.

A delivers merged core SOURCE `d85aa95e8da406d598f3658492e3d615bba8a28f`.
Q read-only diff against cc2 confirms the sole production change is B's original
SQLite `BEGIN IMMEDIATE` and comments; B/C exact source/report ancestry remains.
B separately reports SOURCE230 CI37059454013 attempt1 success, Windows1295
passed/5 skipped and Linux1294 passed/6 skipped, plus its final REPORT
`387338f49045f7be7a184b868f48f325cebd9cbd`. These are owner-reported CI results,
not Q's independently run checks; the earlier local worker timeout remains
unexplained. Final P repin and the exact merged installed Q gate are pending.

## Merged core cross-module archive check

Before the final product installation window, Q checks the interaction of B's
new initialization transaction with A/C's existing dynamic and trusted-feedback
paths on exact core `d85aa95e8da406d598f3658492e3d615bba8a28f`. A new archive
uses process-local `git -c core.autocrlf=false archive`; no global Git setting
changes. Dynamic MCP20, project/budget6 and all C45 checks give **71 passed**,
40.64s, with the unchanged deny fixture and BLAS1. Raw
`a-d85aa95-ac-integration71-first.txt` is retained. This checks the merged source
interaction, not final installed product acceptance. P's early fd7 pin is
explicitly not the final combined product candidate; that delivery and the
coordinated installation window remain pending.

## d85/fd7 actual installation preparation and later transport delta

Coordinator `msg_9fb72a8763e3` grants a bounded installation while F's observer
finishes. Q installs exact core `d85aa95e8da406d598f3658492e3d615bba8a28f` and
product `fd7a79eafbf4aa296ef1348aa001457aaea5cf97` into the same private venv.
Each canonical VCS installation uses `uv pip install --python
.venv-q/Scripts/python.exe --no-deps --reinstall --link-mode copy`, a fresh
Q-only cache, one build/install worker and process-local `core.autocrlf=false`.
The prior 95-package dependency set is unchanged; no installed bytes are patched.

Isolated `python -I` verifies both actual noneditable `direct_url.json` revisions,
private site-packages origins and the unmodified product `installed_core` gate.
Direct `git cat-file --batch` original blobs equal every packaged core129 and
product34 Python file byte for byte, with no newline normalization. `uv pip check`
reports all95 compatible. Four `installed-d85aa95-fd7a79e-*-first.txt` logs retain
the installation, original-byte and dependency evidence.

P subsequently delivers production SOURCE
`fd0ec1e13aff0ea37fe79f601a865040d1c5b604`, catching actual response header/body
connection errors so a reply loss cannot be recast as another source-failure
status. Therefore the fd7 installation is preparation, not final combination
acceptance. Review Handoff `msg_d47010ce453e` precedes Q's seven new installed
factory controls: a delivered positive and header/body failures for three
connection exceptions, retaining the actual outer handler, official MCP,
original durable proposal/task and same-proposal recovery after reopen.
These new checks are **NOT_RUN** at this checkpoint: P owns the full baseline
window. Q keeps the actual fd7 installation for first outcomes, then will
install the authoritative successor and run the final owned slices.

## Actual installed response-loss first RED and fbe72 successor

Coordinator `msg_0c73ccf3c56e` authorizes the bounded first seven checks during
P's full baseline. Actual installed d85/fd7 gives **1 passed / 6 failed**, 6.16s.
All six failing cases first confirm one accepted original proposal/task,
successful same-proposal recovery after reopening ConfiguredResearch, no
duplicate task and no fabricated adoption/contribution. They then fail the
unchanged status assertion: the real outer HTTP handler emits `[200, 503]`
after response header/body loss. The normal delivered-response positive passes.
No real socket is used. Raw
`installed-d85aa95-fd7a79e-disconnect7-first.txt` retains the first failures;
Handoffs `msg_8ced7ade0cda` and `msg_4cf2cd43a4e8` deliver them to P/controller.

P's authoritative successor is
`fbe72c519a3809ffbd439ecba9b65b0441726585`, pinned to the same d85 core.
Read-only diff confirms only the reviewed reply-disconnect handling changes
production Python since fd7. Q updates only the product via exact VCS COPY,
with no dependency or installed-source edits. Actual noneditable origins,
the original pin gate, all core129/product34 Python Git blob comparisons and
`uv pip check`95 pass again; three new `installed-d85aa95-fbe72c5-*-first.txt`
logs retain this result. Final owned pytest slices await P's baseline exit;
neither this package verification nor P's ongoing baseline is counted as Q
final acceptance.

## Complete Q installed gate on exact fbe72/d85

Coordinator `msg_c80c845dae24` grants the final sequential slices. Exact tested
noneditable product `fbe72c519a3809ffbd439ecba9b65b0441726585` and core
`d85aa95e8da406d598f3658492e3d615bba8a28f` remain unchanged throughout.
Each command uses `R1_SECURITY_INSTALLED=1`, process-local BLAS1 and
`.venv-q/Scripts/python.exe -m pytest <owned slice> -q --tb=short`; the P slice
also uses `-rs`. Original process/socket denies and protected pin admission
remain active. All raw first outputs are retained under
`installed-d85aa95-fbe72c5-{factory11,a57,b72,c45,p90}-first.txt`.

| Owned slice | First result |
| --- | --- |
| Actual protected factory, HTTP/MCP and response recovery11 | **11 passed**, 7.81s |
| All A host/project/policy/dynamic checks57 | **57 passed**, 39.30s |
| All B generated/configuration/adoption/concurrency checks72 | **72 passed**, 4314.57s |
| All C original/advisory/generated-trust checks45 | **45 passed**, 11.62s |
| Other P native/resume/provider/member/material/public checks90 | **87 passed / 3 historical skips**, 21.74s |

Total: **272 passed / 3 historical skips**. The three skips retain earlier tests
for the removed unsafe product loop; present public authority and real configured
core boundaries are separately exercised. Unchanged response-loss controls now
pass, retaining one durable task across reopened same-proposal admission and no
second503 or fabricated adoption/contribution. All earlier first failures remain.

B's original command returned after an approximately72-minute tool-return gap;
the original pytest session completed successfully with the actual duration above.
No duplicate execution or replacement log was created. Cause is **UNKNOWN**;
this run provides no latency/performance assurance. The controller reports a
similar observed gap separately. All Q pytest processes exit before releasing
the window in Handoff `msg_b0d6abadad24`.

This is Q's complete bounded local/mock gate for **fbe72/d85**, not all R1 or
live acceptance. Native processes, real candidate execution, real model/science,
sandbox/probe, external materials, Hub and deployment remain NOT_RUN. The
controller separately reports P's full baseline221 passed/3 legacy compatibility
failures and core CI success; neither is Q's own execution result. Later legacy
MCP compatibility changes require additional original HostBinding, workspace and
tool-surface verification before acceptance; they do not inherit this result.

## Final related successor gate and Q handoff

Q SOURCE `953e5cf01f06dd2ed3c77f4cebb0f1c1a9bf1b6f` contains the owned final
checks and immutable outputs. The complete fbe/d85 gate above remains attributed
to that exact pair. Coordinator `msg_4f4344b03d13` authorizes the final related
successor checks and asks Q to stop after completing this scope.

The canonical core launch contract validates an absolute host configuration and
matching workspace and derives HostBinding only for its original MCP module.
Read-only Handoff `msg_925411d7f690` precedes Q's new both-runtime controls for
registered, choice and R1 launches. Separate Handoffs `msg_777f341a59da` and
`msg_a167c3da1ae9` identify the real legacy sentinel: d85 HostConfig defaults to
the empty string, whereas the first product adapter incorrectly tested None.
No invalid HostConfig model_copy(None) is used to manufacture a positive.

| Exact product source with d85 core | Q archive result |
| --- | --- |
| `66744c4e005f6b5289bbb370bc7bc54005594155` | **12 failed / 9 passed**, 3.08s: missing original bindings, relative/workspace bypasses and legal legacy refusal |
| `0dfaceb8af5cc220e555cd3ad4033f02f4ec44cc` | **2 failed / 19 passed**, 2.58s: both valid legacy factories still refused |
| `0da6273f54281f5e86231e31234f682598f68ba2`, initial positive fixture | **2 failed / 19 passed**, 2.82s: Q fixture used the wrong row key and only one candidate |
| Same0da, fixture corrected to original contract | **21 passed**, 2.54s |
| Same0d, corrected valid legacy positives | **2 failed / 19 deselected**, 2.17s, preserving the actual product refusal |

The only fixture correction supplies the original required two legal candidates
and reads their original `signal.task_id`. Safety, identity, rejection and
catalogue assertions remain. All first outputs, including Q's fixture failures,
are preserved. The successful catalogue checks retain every original legacy11
schema/handler, discover both real ledger tasks, reject direct removed R1 calls,
retain Choice's science refusal, reject nonempty R1 hosts in the legacy factory,
and compare the complete original R1 surface before and after narrowing.

Final actual installed pair:

- product `0da6273f54281f5e86231e31234f682598f68ba2`;
- core `d85aa95e8da406d598f3658492e3d615bba8a28f`.

Q updates only its private product package using exact VCS COPY, the same isolated
cache and process-local LF Git configuration. Both actual noneditable origins,
the unmodified installed_core pin gate, core129/product35 original Python blobs
and all95 installed dependencies pass. All164 Python comparisons use original
`git cat-file` bytes without normalization; no installed metadata/source is edited.
The diff since fbe changes only choice_mcp.py, permissions.py, registered_mcp.py
and F's static product.js. Q does not claim independent browser acceptance.

With `R1_SECURITY_INSTALLED=1`, BLAS1 and the unchanged process/socket denies,
`.venv-q/Scripts/python.exe -m pytest` on registered21, native22, resume13,
Codex provider13, Claude7 and actual factory11 (`-q --tb=short`) gives
**87 passed**, 21.74s. Raw `installed-d85aa95-0da6273-related87-first.txt` and
the matching install/origins/dependencies logs retain this actual installed
result. It is a focused successor verification, not an unrun full275 claim.

Q's authorized safety work is complete: own tests/report only, original owner
repairs, first failures retained and exact installed results separated. All Q
test/install processes have exited. Independent I's final merges, final combined
build/acceptance and human run-level approval remain outside this Q task.
No candidate or native model process, real scientific execution, sandbox/probe,
external material acquisition, Hub or deployment ran; L2/L3 remain NOT_RUN.
Original unknown effects/costs stay unknown, and the earlier unexplained long
tool-return duration is retained without a latency assurance.

## 2026-10-03 Q successor: explicit Docker freeze/export, offline only

Successor task `task_f1ef0047b01a`, dispatch `ctx_a1965382b7ea`, reuses the original
Q worker/worktree/branch. The previous task and its completion stay settled.
This section records only Q's affected-boundary work; it does not accept MVP/R1,
AT07, L2, or L3. Only Q tests/evidence and this report were authored. Domain,
governance and owner reports below entered through authorized ordinary exact
merges; Q authored no domain, AOCI, dependency, deployment or original B-test file.

### Exact subjects and publication checkpoint

| Subject | Full immutable identity |
| --- | --- |
| Starting Q report | `793661391738f5dadb2412af32c7188a60915c7d` |
| Governance | `de242031cb3cb029191ea7754475bf5d23ebba95` |
| B runtime SOURCE | `5769005b09f1b756c94fdad0649a6b74690c0ca9` |
| B docs-only REPORT, direct child of SOURCE | `5aebd2eb7af774b3dc496ad9620548f6e7852e09` |
| A configuration SOURCE, including the exact B subject | `aec86c98ffe8fc3c3a922da5a6e281d553820d05` |
| Q ordinary merge of A configuration SOURCE | `d0b9e288942a1491ed2515681c96ccb35fab3ef0` |
| Q tests and initial raw evidence SOURCE | `b8f7a8a5ae5ab62e8c84fdec85557a88d06d273f` |
| Q source push first-failure receipt commit | `76de0b577913b947b298573628eb0d2dbefe5e65` |
| Q latest SOURCE with failed read-only reconciliation receipts | `88d0cc28d1fdb3d89d62cdb1f1312078fc3c22b0` |

Branch: `songconmaisaix31-design/morph-r1-boundaries-1003`. At this local-report
checkpoint, SOURCE is committed locally, first push and two read-only Git remote
queries failed, and both SOURCE/REPORT publication are pending. The first push's ref effect
was UNKNOWN; root's existing GitHub API lookup and Q's independent lookup at
05:25 UTC both return the original report `793661391738f5dadb2412af32c7188a60915c7d`.
No successor publication is established. Q has not sent worker_done or asserted
remote publication closeout. Root's reply to the durable Orca ask explicitly
permits saving a local docs-only REPORT with SOURCE88 as its direct parent while
publication is blocked. This adjusts local saving order only, not acceptance.
Root reports SSH443 read-only authentication refusal, not a usable channel;
neither root nor Q changes auth/network configuration. Unconditional push and
network polling stop until actual network conditions change. SOURCE must publish
before the docs-only REPORT push; no completed test is rerun for this blocker.

The final actual private noneditable distribution is A configuration SOURCE
`aec86c98ffe8fc3c3a922da5a6e281d553820d05`, not a floating owner HEAD or AOCI WIP.
No `orchestration/experiments/**` or `local_assets/**` difference exists between
B576 and this exact A source. A's other inherited local-context/native changes
are outside this test slice. No unchanged 293-test or product-wide suite ran.

### Preserved first results and actual installation

All raw files below live in `tests/integration/r1_security/evidence/` and are new
immutable evidence. Prior owner/Q REDs, the 296ec298/7a6c509 refusal stage and all
historical installed results remain unchanged.

| Actual subject/check | First outcome | Raw evidence filename |
| --- | --- | --- |
| B576, unchanged original configured15 | **3 FAIL / 12 PASS**, 2.29s | `b-5769005-original-configured15-first.txt` |
| B576, first identity script | **FAIL**, checkout module import asserted | `b-5769005-private-origins-blobs-first.txt` |
| B576, identity script with private purelib first | **PASS**, 136 original Python blobs | `b-5769005-private-origins-blobs-import-corrected.txt` |
| B576, explicit fixture + original15 + new frozen39 | **54 PASS**, 0.66s | `b-5769005-explicit-frozen54-first.txt` |
| Aaec, final affected slice: original15 + frozen45 + A config5 | **65 PASS**, 24.98s | `a-aec86c9-installed-affected65-first.txt` |
| Aaec, actual origin/private imports/original blobs | **PASS**, 136 original Python blobs | `a-aec86c9-private-origins-blobs-first.txt` |
| Aaec, `uv pip check` | **PASS**, 96 compatible packages | `a-aec86c9-private-dependencies-first.txt` |
| Additional fixed Moby archive read | **UNKNOWN / incomplete**, TaskCanceledException | `q-fixed-moby-archive-read-first.txt` |
| Q initial SOURCE push | **FAIL**, exit128 connection reset; remote effect unknown | `q-docker-source-push-first.txt` |
| Q first `ls-remote origin` | **FAIL**, exit1 connection reset | `q-docker-remote-ref-first.txt` |
| Q canonical same-repository `.git` `ls-remote` | **FAIL**, exit1 unable to connect after32103ms | `q-docker-remote-ref-canonical.txt` |

Successful independent read-only reconciliation command:
`gh api repos/songconmaisaix31-design/Morphogenesis/git/ref/heads/songconmaisaix31-design/morph-r1-boundaries-1003 --jq .object.sha`.
It returns `793661391738f5dadb2412af32c7188a60915c7d`, matching root's prior
observation; it does not retroactively turn the first failed push into success.

The original three tests failed before their intended positive/mutation
boundaries: the old fixture had `docker_export=None`. That refusal is the new
default fail-closed contract, not evidence that the explicit adapter failed.
Q changes only the positive fixture's explicit DockerExportConfiguration and
full server ID, and stubs the HTTP/SDK I/O boundary. Every original security
assertion is retained; a pre-create read-only route assertion is added.
Neither `ATOMIC_EXPORT_SCOPE_SUPPORTED` nor `declared_capability`, verification,
FrozenDockerExport, or the production admission/path/tar/lifecycle checks are
monkeypatched. Separate tests require old None configuration and old/hand-filled
passed probes to remain unverified and unable to admit/create.

The first identity-script failure was Q verification plumbing: imports occurred
before placing private purelib first. The corrected script preserves that first
failure, places purelib first like the unchanged installed-mode conftest, and
compares all packaged Python files to original `git cat-file --batch` blobs.
There is no normalization or installed source/metadata repair. Both installs
validate canonical Git origin and full `commit_id`/`requested_revision`; imports
resolve under Q `.venv-q/Lib/site-packages`, with Docker SDK **7.2.0**.

Installation uses the existing private `.venv-q`, COPY link mode and exclusive
TEMP cache `morph-q-r1-1003/q-uv-b576-20261003`. The only added runtime package is
official `docker==7.2.0`. Process-local `core.autocrlf=false`,
`GIT_NO_LAZY_FETCH=1` and UV concurrency1 apply; no global auth/provider/HOME,
system Python, other Owner environment or cleanup changes occurred. Raw installs
and dependency checks retain their `b-5769005-*` / `a-aec86c9-*` identities.
The product's installed_core guard is untouched; no product acceptance is inferred
from changing Q's private core distribution.

### Independent boundaries and real domain calls

- **Configuration authority:** actual LocalCpuSandboxBackend, prepare/admit and
  direct create refuse None export, missing/old configuration and a changed
  daemon/socket with the previous probe. Closed plan/backend/environment schemas
  reject candidate-supplied docker_export. Actual daemon/version/service-port/
  full-server-ID mismatches refuse before the captured official SDK create.
- **Nonvacuous positive:** original15's legitimate host/probe fixture reaches the
  original SDK request once after actual FrozenDockerExport preflight. Image,
  resource, deny-network, duration, task/fence and original prepare-mutation
  assertions remain. Probe records are trusted deterministic fixtures only;
  they do not claim a real harmless probe or authorize live execution.
- **Owned writers and range:** the actual OpenSandboxSession/FrozenDockerExport
  path checks full main/egress identities, exact image/resources, security,
  runtime volume driver/options and exclusive users. Third writer, export-root
  mount, host PID or changed resource/image refuse. Positive metadata models
  the upstream **RW** runtime volume outside the export tree, shared only by the
  owned pair. Both must be paused throughout every HEAD/GET. Positive requests
  visit `/tmp`, export root, nested ancestor and leaf, close all HTTP replies,
  then resume the same session; the second file performs a second pause/resume.
- **Untrusted file bytes:** representative ancestor/leaf symlink, oversize stat,
  tar hardlink/FIFO, traversal, extra member, PAX path, compression, truncation
  and stream overflow refuse. TarFile.extract/extractall are denied during these
  tests; only bounded bytes from the actual parser can leave the read boundary.
- **Unknown effects and original cleanup:** pause timeout before/after effect,
  a partially paused pair, lost/foreign resume connection, stream disconnect,
  late read and changed GET metadata do not redeliver pause or later work.
  Read-only reconciliation may permit one same-session resume when both writers
  are confirmed paused, while the original unknown remains. A foreign resumed
  connection is closed, never killed. Actual original finalize_session persists
  unknown cleanup and closes owned handles; borrowed sessions never kill.
  Actual executor create timeout persists unknown, original archive reread grants
  no science/contribution, and the same run cannot recreate the SDK request.
- **A handoff:** actual HostConfig→GeneratedHostSettings→ResearchService factory
  roundtrips absent/explicit export, with ambient Docker settings unable to fill
  it. No probe means no admission. Changing/disabling export cannot rebind the
  existing frozen project, whose context/audit facts remain unchanged. A real
  official FastMCP call over the original ledger rejects a candidate control
  field before plan persistence; the tool catalogue exposes no such host field.
- **Official transport construction:** on this private Python3.13 environment,
  actual Docker7.2.0 UnixHTTPAdapter and NpipeHTTPAdapter constructors work with
  the configured local endpoint, `trust_env=False` and no APIClient auth config.
  No adapter connects to an Engine. Inert HTTP responses are supplied only for
  the explicit fixture, not through a fake export-capability declaration.

Final test command (PowerShell process-local `R1_SECURITY_INSTALLED=1` and
OPENBLAS/OMP/MKL_NUM_THREADS=1):

```text
.venv-q/Scripts/python.exe -m pytest tests/integration/r1_security/test_b_configured_sdk_boundary.py tests/integration/r1_security/test_b_frozen_export_boundary.py tests/integration/r1_security/test_a_docker_export_handoff.py -q --tb=short
uv pip check --python .venv-q/Scripts/python.exe
```

The unchanged conftest denies subprocess.Popen, os.system, socket connect and
connect_ex for every test/tool call after creating its trusted stdlib loop.
No original B tests/helpers are imported or run. All test/install processes
exited. Q released the serialized window in Orca message `msg_f36d690920ab`.
Review Handoffs preceded new tests; the inactive settled B mailbox was explicitly
rejected by Orca and forwarded through root. No domain defect was found in this
affected deterministic slice and no Q domain patch was made.

### Primary-source checks and remaining limits

With `GIT_NO_LAZY_FETCH=1`, Q read the already-present OpenSandbox clone's exact
`b1a29cf93a823a95913f7943010febb3f29de05c` lifecycle/networking code: main and
egress pause/resume, rollback handling, and the runtime RW/NET_ADMIN sidecar
configuration. The local private official Docker7.2.0 API/transport code confirms
archive path/stat header handling, APIClient auth loading, the high-level stream
timeout removal, and npipe overlapped timeout/cancellation; Q's actual adapter
constructors were independently tested. The fixed Moby Stat source was read via
the official raw endpoint. Further web reads were terminated without completed
results, and a separate bounded archive fetch failed; its incomplete review is
not presented as a successful whole-file/schema verification.

Primary references: [fixed OpenSandbox lifecycle](https://github.com/opensandbox-group/OpenSandbox/blob/b1a29cf93a823a95913f7943010febb3f29de05c/server/opensandbox_server/services/docker/docker_service.py),
[fixed Moby Stat](https://github.com/moby/moby/blob/285b47192d4b2f183aba5dd360a92cd52d723004/daemon/containerfs_linux.go),
[Docker SDK7.2.0 API client](https://github.com/docker/docker-py/blob/5ad5327fba623897ee9a527d7eee1b01703e0726/docker/api/client.py),
and the [Engine API1.52 reference](https://docs.docker.com/reference/api/engine/version/v1.52.yaml).
The last schema link is a reference, not a claim that its full content was
independently downloaded successfully during this successor.

Actual Engine29.5.3/API1.52 and daemon ID remain **UNKNOWN / unmeasured**.
No Docker/WSL service, container, candidate, model/science or real isolation
probe was started. All passed probe records/HTTP replies/SDK effects are inert
contract-local fixtures. Mock PASS does not prove isolation or a usable live
backend. Fixed version metadata/source review does not prove actual deployment.

The approved scope excludes shared mounts from the export tree, checks every
ancestor/leaf and limits ordinary file bytes/time while both writers are frozen.
PathStat exposes no nlink; rejecting tar link members does **not** rule out all
inode aliases outside the tree. That unpromised condition is not added as a new
exit gate. This implementation resumes after each file, with no promise of one
atomic snapshot across multiple files. A blocked underlying read can consume an
additional request timeout; SDK pause/resume is separate, not a hard real-time
guarantee. Unknown SDK create has no owned returned identity to blindly clean up.

Independent I's final exact combination, product pin/interface/build regression,
real deployment safety checks and separately authorized AT07 remain pending.
L2 must follow actual AT07 acceptance and specific user authorization; L3 and
MVP/R1 overall acceptance are outside this Q task. AOCI is A's separate work;
Q has neither authored nor claimed its receipt. No C policy-blocked cleanup was
retried. These focused results do not replace prior failures, owner reports or
unrun live/human acceptance.

### 2026-10-03 16:32 CST publication recovery, docs-only successor

Recovery dispatch `ctx_ff36f31b0819` retains task `task_f1ef0047b01a`, the
original Q worker/worktree/branch and the completed affected-boundary evidence.
The earlier publication checkpoint above remains the historical state when
REPORT `09a62370498e40d54d8e956ce6b2c941e16f7515` was authored; its direct parent
is SOURCE `88d0cc28d1fdb3d89d62cdb1f1312078fc3c22b0`. The first failed push and
failed remote queries remain in that SOURCE, with their original outcomes.
Root's 16:29 CST successful HTTP/1.1 remote read supplied evidence of changed
network conditions and authorized the single ordinary publication recovery.

Q independently completed these commands in order, with process-local
`GIT_NO_LAZY_FETCH=1` and `GIT_TERMINAL_PROMPT=0`:

```text
git -c http.version=HTTP/1.1 push origin 88d0cc28d1fdb3d89d62cdb1f1312078fc3c22b0:refs/heads/songconmaisaix31-design/morph-r1-boundaries-1003
git -c http.version=HTTP/1.1 ls-remote origin refs/heads/songconmaisaix31-design/morph-r1-boundaries-1003
git -c http.version=HTTP/1.1 push origin 09a62370498e40d54d8e956ce6b2c941e16f7515:refs/heads/songconmaisaix31-design/morph-r1-boundaries-1003
git -c http.version=HTTP/1.1 ls-remote origin refs/heads/songconmaisaix31-design/morph-r1-boundaries-1003
git status --porcelain=v1
```

All five commands exited 0. The first push advanced the original remote ref
`793661391738f5dadb2412af32c7188a60915c7d` to SOURCE88; its immediately following
remote read returned the full SOURCE88 SHA. Only after that verification did
the second push advance SOURCE88 to REPORT09; the next remote read returned
`09a62370498e40d54d8e956ce6b2c941e16f7515`. The worktree was clean at
`2026-10-03T16:32:47.8439736+08:00`, before this report-only addition.
Both original SOURCE and REPORT are now independently confirmed published;
the new success does not change any earlier failure or unknown-effect record.

This successor changes only `docs/tracks/r1-boundaries.md`; SOURCE88's tests,
raw evidence and domain bytes remain unchanged. No completed test or install
was rerun, no new boundary module was added, and the previously released
serialized installation/test window remains released. No AOCI file or receipt
was changed or claimed. No force push, cherry-pick, API Git-object reconstruction,
global auth/proxy/SSH change, Docker/WSL action or C cleanup retry occurred.
The final docs-only successor SHA and its successful ordinary push/remote-read
receipt will be handed to root through the current live Dispatch.

The retained result is the existing private noneditable Aaec/B576 affected
slice: 65 PASS in 24.98s, 136 original Python blobs and 96 compatible packages.
Actual Engine29.5.3/API1.52, daemon identity and isolation remain unmeasured;
AT07 and L2 remain NOT_RUN. Independent I's final offline combination and
separate user authorization are still required before real AT07, followed by
L2 only after actual AT07 acceptance and its approved problem/material/resource
scope. This publication closeout grants no MVP/R1 overall acceptance.

## 2026-10-03 Q scoped Docker transport portability repair

Task `task_7517d7a2997a`, dispatch `ctx_246835450dd3`, continues the original Q
worktree/branch from clean `6ce5a23ea256affdf9fe8a71bbaabb66695f3631`.
The failed integration subject remains SOURCE
`3a6a7e5fecd5bbead9d234fa22ae0735bed19beb`: original CI
`37113441786`, attempt1, Linux **2 FAIL / 1742 PASS / 16 SKIP in 540.91s**;
Windows was cancelled by the matrix. Both original failing endpoint cases
raise ImportError at Q test line123's unconditional NpipeHTTPAdapter import.
Q read I's preserved `C:/r1i/i1003-core-1732/logs/ci-first-failure-excerpt.txt`;
the original full log and first-result files remain unchanged in I's directory.
Prior Q **65 PASS / 24.98s** remains historical evidence, not a replacement
for this first CI failure or a result rerun during this repair.

### Minimal change and official platform behavior

Fixed private official `docker==7.2.0` source exports UnixHTTPAdapter
unconditionally, but catches ImportError around npipeconn/npipesocket;
npipesocket requires pywintypes and win32 modules. Therefore importing both
adapters before choosing an endpoint also broke the Linux UNIX case. The Q
test now imports the transport module and accesses only the appropriate adapter.
On a non-Windows host the NPIPE case explicitly asserts the official adapter
is unavailable and the actual production `_transport(endpoint)` raises
AttributeError naming NpipeHTTPAdapter. This is rejection evidence, not NPIPE
construction success; the UNIX case continues actual construction. There is
no blanket or platform skip, fake adapter, platform monkeypatch or new dependency.

On Windows, actual UNIX and NPIPE constructors remain required. Original
DOCKER_HOST/DOCKER_CONTEXT/HTTP_PROXY poison, adapter type, trust_env=False,
auth=None, close and process/socket guards remain. The earlier alternative
base membership assertion is strengthened to the exact per-endpoint base;
actual adapter socket_path/npipe_path must match the explicitly supplied endpoint.
No adapter connects to an Engine. No B production failure is established by
the original import error, and no domain/dependency/workflow/guard file changed.

### Exact private installation and targeted validation

Reused only Q's existing private noneditable Python3.13.13 environment after
fresh verification of canonical direct_url commit_id/requested_revision
`aec86c98ffe8fc3c3a922da5a6e281d553820d05`, private purelib import origins and
all **136 installed Python files byte-equal to raw Git blobs**. Process-local
`GIT_NO_LAZY_FETCH=1` applied; `git cat-file --batch` supplied original bytes,
without line-ending normalization. `git diff --exit-code` confirms no
orchestration/experiments or local_assets changes between exact B
`5769005b09f1b756c94fdad0649a6b74690c0ca9` and that A subject. Official Docker
7.2.0 resolves from the same private purelib. New immutable identity evidence:
`tests/integration/r1_security/evidence/q-transport-portability-private-identity-first.txt`.

Actual Windows command, with process-local R1_SECURITY_INSTALLED=1,
PYTHONDONTWRITEBYTECODE=1 and OPENBLAS/OMP/MKL_NUM_THREADS=1:

```text
.venv-q/Scripts/python.exe -m pytest tests/integration/r1_security/test_b_frozen_export_boundary.py::test_official_local_transport_constructs_without_environment_or_engine_connection -q -rA --tb=short
```

**2 PASS, 0 SKIP, 0.45s, exit0**; both original parameterized endpoint cases
constructed actual official adapters. Raw result:
`tests/integration/r1_security/evidence/q-transport-portability-windows2-first.txt`.
The original unchanged conftest denies subprocess.Popen, os.system and socket
connect/connect_ex throughout both test calls. No Linux host was available:
root confirmed this in `msg_746e3444b417`; actual Linux UNIX construction and
NPIPE rejection execution await I's authorized combined successor CI. No WSL,
Docker, new host/environment, full65/293/core/product run or reinstall was used.
The short private verification/test processes exited and the window is released.

### Frozen SOURCE, publication and remaining gates

SOURCE `acb26f4af3535ff6b4136dcb5ef0f7fde526e2a3` changes only the owned test
function and two small new evidence files. `git diff --check` passed. Ordinary
publication and immediate remote verification both exited0:

```text
git -c http.version=HTTP/1.1 push origin acb26f4af3535ff6b4136dcb5ef0f7fde526e2a3:refs/heads/songconmaisaix31-design/morph-r1-boundaries-1003
git -c http.version=HTTP/1.1 ls-remote origin refs/heads/songconmaisaix31-design/morph-r1-boundaries-1003
```

The remote returned full SOURCEacb and the worktree was clean. Early frozen
Handoff `msg_632d3b82ce80` routes this exact source through root to original I
`ctx_eceee077723b`; root owns merge and successor CI authorization. This
docs-only REPORT follows SOURCE; its commit uses `[skip ci]` per root's guidance.

The new skip-ci follow-ups were first consumed after SOURCE was already pushed,
so its published commit message lacks `[skip ci]`. Q preserves that immutable
published history. A read-only `gh run list --branch
songconmaisaix31-design/morph-r1-boundaries-1003 --commit
acb26f4af3535ff6b4136dcb5ef0f7fde526e2a3 --limit 3 --json
databaseId,headSha,status,conclusion,event,url` observed automatic push run
`37114202636` in_progress, with no conclusion. Q immediately escalated through
`msg_368a6bf2b50a` and `msg_c851857bf49a` for coordinator handling of that extra
run. Q issued no CI dispatch, rerun or cancellation; this automatic run is not
presented as acceptance or as the unique I combined gate.

Linux validation and I's final combined gate remain pending. Actual daemon/API/
Engine/isolation are still unmeasured; AT07/L2 remain NOT_RUN and require their
separate authorization sequence. No native/model/science execution, C cleanup,
OpenCode, AOCI write, global Python install or auth/provider change occurred.
This repair/report closes only the scoped Q portability phase, not MVP/R1.

Publication closeout: docs-only REPORT
`76af665511cb4b31662df0f698fcf631bb96419e`, direct child of SOURCEacb, was
ordinarily pushed and independently read back with the full matching remote
SHA; the worktree was clean and the SOURCE-to-REPORT difference is exclusively
this report. Both the push and remote read exited0. Root's
`msg_b0939dec24b7` accepts the minimal platform repair for I integration and
reports a single cancellation request for the extra Q run, with its initial
unconfirmed state retained. A subsequent Q read-only command
`gh run view 37114202636 --json databaseId,headSha,status,conclusion,url`
returned exact SOURCEacb, status `completed`, conclusion `cancelled`.
This confirms cancellation only, not a passing Linux run. This final docs-only
successor records that confirmed result, also uses `[skip ci]`, and preserves
SOURCEacb and REPORT76 without amendment or forced history changes.

## 2026-10-03 Q: exact AT07 observation route boundary acceptance

Completed only the Q19:44 scope from root governance
`86199ed6f2df1413b8b2b9a81e0a65988cb1a6f0`: the independent new
`tests/boundary_review/test_at07_route_boundary.py` and this appended report.
Spec AT-07 still requires a separately authorized real harmless sandbox probe;
this acceptance is **contract_local mock I/O**, not AT-07, L2 or isolation proof.
Q resumed branch `songconmaisaix31-design/morph-r1-boundaries-1003` at historical
REPORT `49c0b3ad49f9fa1b5ad7b493ec05187e5b148503`, initially clean. No B dirty
tree, other owner's environment, source, tests, lock, AOCI assets or old evidence
was modified. The original Linux/NPIPE first failure and all prior reports remain.

### Exact sources and private installation

- Actual baseline core: `b480fca1b10a0b6a9c93f0d1801d38f267662461`.
- Actual new core under test, supplied by root: B SOURCE
  `fc866465aa52a3f09773bc79a0fab95bceedc3d9`. Q read this immutable Git object;
  B docs-only REPORT `f008e281e15d25c8950d7ddd05450fbe398653f1` was not used as
  the tested code pin.
- Initial Q test SOURCE: `8b1b9d4b1da40eb3c2d544aa875ad65d7e596733`.
- Final Q test SOURCE: `f2b81cd9c0e0623c224b0501580a19e3fc1d37da`; its small
  successor completes a synthetic export observation and strengthens the
  injected TimeoutError assertion. Original route/log/unknown/replay assertions
  remain. Both SOURCE commits use `[skip ci]` and were ordinarily pushed;
  `ls-remote` returned their full exact SHAs, with clean worktrees at publication.
  Root received final SOURCE before this separate docs-only REPORT.

Private root: `C:/research-private/q-at07-ctx345f-20261003`. Baseline and new
SOURCE used separate fresh noneditable GitHub VCS COPY installs, venvs and caches,
`uv pip install --link-mode copy`, Python 3.13.13; no global pip or I/P/B environment
was used. The accepted new environment is `source-lf-venv`, with `source-lf-cache`.
The URL is `git+https://github.com/songconmaisaix31-design/Morphogenesis.git@`
followed by the full tested SHA; `direct_url.json` has that same full commit ID
and requested revision, with no editable flag. Actual imports of `at07_live`,
`at07`, `frozen_export` and `generated` are inside this venv's site-packages.

Raw identity verification passed **133/133 Python objects, all nlink=1**. This
set consists of Git-tracked `.py` paths actually present in the noneditable
distribution, excluding `tests/`, `tools/` and `demo/`; it is not all repository
files or an assertion about distribution completeness. Each installed object
was compared byte-for-byte with the exact source Git blob, without normalization
or installed-file edits. A read-only `git cat-file --batch` preserved that same
comparison while avoiding per-object subprocess overhead. Raw identity and
import paths: `source-lf-identity-batch.txt`; baseline: `baseline-identity-first.json`.
`source-lf-pip-check.txt` records `uv pip check`: **98 packages compatible, exit0**.

### Independent cases and first evidence

The 54 cases intercept original subprocess argv/env and original
`frozen_export._transport` I/O; they run original `FrozenDockerExport.preflight`,
the execute/create/finish call chain and original diagnostic review. Real
process creation, network connect/connect_ex/sendto, os.system, transport and
SDK create are denied unless the individual test replaces that seam with an
explicit synthetic capture. No Docker executable or Engine was invoked. Synthetic
key reads and captured SDK calls are not real key access or real sandbox creation.

Coverage includes both allowed endpoints; uppercase/mixed-case Docker context,
host/config/certs/TLS/API/auth and proxy/HOME poisoning; explicit host/config,
minimal canonical process environment, shell=False and 10-second deadline;
route arguments and secret inspect-format bypasses; mutation and arbitrary exec
refusal; exact fixed cat/nft forms; incomplete/invalid/conflicting configuration
before CLI/key/create; original daemon/Engine/OS and actual API mismatch rejection;
absent/unknown/nonempty/symlink/junction private paths; preexisting directory
refusal and preservation of unexpected files without recursive deletion;
bounded secret-free exit/OSError/timeout/oversized failures with no retry; all
pre/post inspect, inventory, fixedexec and log observations on the same endpoint;
unknown SDK/observation effects and durable refusal of a second create request.
Junction metadata and both transports are mocked, not real platform acceptance.

Preserved evidence, in order:

1. Installed baseline `b480`: independent unbound-observation test **1 FAIL,
   15.41s, exit1**, because `docker_read` without a trusted binding did not reject
   the intercepted CLI call. The test was WIP on parent Q49 at that time; its
   refusal assertion remains in both published Q sources. Raw:
   `baseline-route-first-red.txt`; this is the actual old-code counterexample.
2. First fc866 install identity **FAIL** on `bootstrap/__init__.py`: installed
   63B with CRLF versus Git 62B LF. `source-identity-first.json` is unchanged.
   System Git `core.autocrlf=true` was diagnosed; normalization was used only
   to identify the cause, never for acceptance. A new venv/cache was installed
   with process-local `GIT_CONFIG_COUNT=1`, key `core.autocrlf`, value `false`.
   No global configuration or installed bytes were patched.
3. A long-running identity import was stopped only after confirming its exact
   private command, PID68432 and creation time `2026-10-03 19:54:17`.
   `identity-import-interruption.json` preserves ownership. Pytest had not started;
   this interrupted verification was not a pass. Its empty original output is
   retained as `source-lf-identity.json`. Subsequent verification sets BLAS/OMP/MKL
   thread limits to 1 before import and performs the same raw checks in a batch.
4. Q SOURCE8b1 on identity-verified installed fc866: **52 PASS / 2 FAIL,
   2.11s, exit1**, raw `source-boundary-first.txt`. The two postcreate route cases
   stopped at the original export review: Q's synthetic export observation lacked
   required `frozen_export=true`, leaving export unknown before the logs stage.
   Private `source-first-tmp/test_execute_keeps_every_obser2/q-route/result.json`
   and `review.json` preserve that reason. No B defect was inferred from this
   incomplete fixture; only Q's synthetic observation was completed, with a
   stronger TimeoutError reason assertion. No route assertion was weakened.
5. Final Q SOURCEf2 on the same installed fc866: **54 PASS / 0 SKIP,
   4.54s, exit0**, raw `source-boundary-final.txt`; root accepted this narrow gate.
6. Closing input audit additionally found Q's unchanged checked-out TOML fixture
   had CRLF (1049B) versus fc866 Git LF (1013B), while the Q test source itself
   matched Git exactly. `final-test-and-profile-identity.json` preserves that
   first audit assertion failure. The already-passing core's 133-byte checks were
   unaffected. Via the existing `Q_AT07_SERVER_CONFIG` fixture input, a new private
   `source-at07.config.toml` was copied from the exact fc866 Git blob, nlink1 and
   byte equality checked. No code mirror or installed object was changed.
   `bound-test-and-profile-identity.txt` records original diagnosis and final input
   identity; final test SHA256 is
   `36f002b60310ddfd84f2ec160948532d3a9ea918d5a3e7c488e9d29dd428a192` and
   profile SHA256 is `438fe04be51d07188b6bc4b26fbd85c2e7ce28dc02e31ed3af2a4cf27f3c0b79`.
   With that exact profile input, the unchanged Q SOURCEf2 and installed fc866
   passed **54 PASS / 0 SKIP, 1.71s, exit0**, raw `source-bound-input-final.txt`.
   This new evidence does not overwrite the earlier green or any first failure.

### Commands and remaining limits

From the private root, using process-local `PYTHONDONTWRITEBYTECODE=1` and
`OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=MKL_NUM_THREADS=1`, the baseline selector was
`test_unbound_observation_cannot_reach_cli` with `baseline-venv/Scripts/python.exe`.
The final new-file command was:

```text
source-lf-venv/Scripts/python.exe -I -m pytest C:/Users/DW/orca/workspaces/Morphogenesis/morph-r1-boundaries-1003/tests/boundary_review/test_at07_route_boundary.py --import-mode=importlib -q -rA --tb=short -p no:cacheprovider --basetemp C:/research-private/q-at07-ctx345f-20261003/source-bound-input-tmp
```

The final invocation additionally set `Q_AT07_SERVER_CONFIG` to the absolute
private `source-at07.config.toml` path. Identity used
`source-lf-venv/Scripts/python.exe -I verify_install_batch.py <absolute-Q-repo> fc866465aa52a3f09773bc79a0fab95bceedc3d9`;
package compatibility used `uv pip check --python source-lf-venv/Scripts/python.exe
--cache-dir source-lf-cache`. Paths here denote this task's private root only.
`git diff --check` passed; publication uses ordinary
`git -c http.version=HTTP/1.1 push origin HEAD:refs/heads/songconmaisaix31-design/morph-r1-boundaries-1003`
and `git -c http.version=HTTP/1.1 ls-remote origin refs/heads/songconmaisaix31-design/morph-r1-boundaries-1003`.
Q changed tests only; no production type change required another strict gate.

The earlier I combination `b480` + product
`2b9bf73c93e732771ed3582f3bc7745ea8158b68` / REPORT
`a67c0af1e27bea08a8e2ce426337f0608e62f216` remains prior-combination evidence,
not acceptance of a product repinned to fc866. Q did not repeat old 293/65/platform2,
core/product/UI gates or create a new integration owner. Root received first
failures, the final consumable SOURCE and all input distinctions via Orca CLI;
the settled original B Dispatch refused further mailbox delivery, so any domain
repair would have gone through root to the same Owner. None was required here.
After consuming root's docs-only closeout instruction, no further test runs occur.

Real Engine/daemon/API/isolation, official CLI binary identity, real cleanup,
AT-07, candidate execution, native/model/science, L2 and final integrated product
acceptance remain **NOT_RUN**. Capture of the `docker` argv is not verification
of a host executable. No usable AOCI index/service entry was present in this Q
checkout; no formal cognition or maintenance claim is made, and all AOCI assets
remain untouched as required. The task's private test/import processes exited;
private caches, venvs and all first evidence are retained. Main/tag/deploy,
Engine startup/pulls and human acceptance were not performed. Token usage, cost
and savings are **UNKNOWN**. Only the original I may subsequently merge these
exact B/Q sources and perform the applicable cumulative integration gate.

## 2026-10-03 Q successor: Linux junction fixture portability repair

Task `task_33fe99de98b4`, Dispatch `ctx_cc395fc66dbc`, parent
`task_7799a761b32c`, same Q Owner/worktree/branch/terminal. Q read root's current
20:31 plan and retained the previous SOURCE/REPORT and Windows-only 54-case
evidence. This successor changes only the junction fixture in
`tests/boundary_review/test_at07_route_boundary.py` and this appended report.

### Preserved CI and local first RED

Read-only `gh run view 37122569886 --json headSha,attempt,status,conclusion,jobs`
and `gh run view 37122569886 --log-failed` confirmed attempt1, exact integrated
SOURCE `e635b8ab3e79529403b527892e75ffb29674af0a`, completed/failure:
Linux **1823 PASS / 1 FAIL / 16 SKIP, 425.33s**, Windows **CANCELLED**.
The failing case was
`test_untrusted_private_config_directory_cannot_reach_cli[junction]`:
the fixture simulated `asset_paths.sys.platform=win32`, but Linux's stat module
had no `IO_REPARSE_TAG_MOUNT_POINT`. The real `local_assets/paths.py:61` raised
AttributeError before the original expected refusal/CLI-zero assertion finished.
Linux's later type/build/SDK/wheel steps were skipped. The old installed Windows
54 PASS does not establish this Linux fixture or the integrated gate as passing.

New private evidence root:
`C:/research-private/q-at07-linux-junction-ctxcc395-20261003`.
`ci37122569886-attempt1-failed.log` and `ci37122569886-attempt1-status.json`
preserve the original CI observation without rerunning or cancelling that run.
The private `run_case.py` child used the original Q-owned
`C:/research-private/q-at07-ctx345f-20261003/source-lf-venv/Scripts/python.exe`.
Its actual noneditable `direct_url` remained B SOURCE
`fc866465aa52a3f09773bc79a0fab95bceedc3d9`; imported `at07_live.py` and
`local_assets/paths.py` were inside that venv, nlink1, and their bytes equalled
both fc866 and integrated e635 Git blobs. This was a two-object identity check,
not a new whole-install acceptance or a claim of installing e635.

Before editing, the isolated child removed the stat symbol and ran the unchanged
junction selector against Q parent REPORT
`f261c78a8181a4ce82a74bb41395cb35ee1e7b21`:
**1 FAIL, 1 warning, 0.26s, exit1** with the same production-line AttributeError.
Raw `local-junction-first-red.txt` records symbol absence, imports/pin, failure
and fixture restoration. The symbol deletion affected only that child process;
the child restored its original value in finally before exiting.

### Minimal SOURCE and scoped verification

SOURCE `3aa95d94828449fd92e6bb4fe6385178f3dac971`, direct child of Q REPORTf261,
adds only a comment and, inside the existing junction-only fixture branch:

```python
monkeypatch.setattr(asset_paths.stat, "IO_REPARSE_TAG_MOUNT_POINT", 0xA0000003, raising=False)
```

This supplies the original Windows constant alongside the already-simulated
Windows platform and reparse metadata. The actual `no_links` function, comparison
and invocation remain unchanged. Original expected refusal exceptions, symlink/
junction metadata, `capture_cli` zero-call assertion and file-preservation checks
remain unchanged. No skip, AttributeError allowance, stub of `no_links`, production
edit, lock/workflow/profile change or new transport was introduced.

With process-local `PYTHONDONTWRITEBYTECODE=1` and BLAS/OMP/MKL thread limits1,
from the new private evidence root, the exact child command pattern was:

```text
C:/research-private/q-at07-ctx345f-20261003/source-lf-venv/Scripts/python.exe -I C:/research-private/q-at07-linux-junction-ctxcc395-20261003/run_case.py MODE SCOPE PHASE
```

The helper calls pytest only for the original private-config test function, with
`--import-mode=importlib -q -rA --tb=short -p no:cacheprovider` and a distinct
private basetemp for each phase. Actual arguments/results:

| MODE / SCOPE / PHASE | Result | Raw file |
|---|---|---|
| `missing junction first-red` | 1 FAIL / 0.26s / exit1 | `local-junction-first-red.txt` |
| `missing junction missing-fixed` | 1 PASS / 0.03s / exit0 | `local-junction-fixed.txt` |
| `native five native-five-fixed` | 5 PASS / 0.05s / exit0 | `private-config-five-fixed.txt` |

The five states are absent, nonempty, unknown, symlink and junction. All three
runs record that `Path.lstat`, `asset_paths.sys` and stat-symbol presence/value
were restored after pytest teardown. In the missing-symbol run, fixture teardown
restored absence rather than leaving a fabricated constant behind. Each run
retains one `PytestAssertRewriteWarning` for already-imported anyio; no case was
skipped. These are Windows-host isolated simulations, not a real Linux CI run.

`git diff --check` passed. SOURCE was ordinarily committed/pushed with `[skip ci]`;
`git -c http.version=HTTP/1.1 ls-remote origin refs/heads/songconmaisaix31-design/morph-r1-boundaries-1003`
returned full SOURCE3aa and the worktree was clean. Handoff `msg_5d2ccf50e94e`
included full SHA/diff/raw/pin. Root `msg_0107cbb70087` independently accepted the
exact two-line fixture repair and handed it to the same I; this separate
docs-only REPORT follows that acceptance and also uses `[skip ci]`.

No 54-case, old install/full-core/product/UI/type gate was repeated, no package
was installed, and Q did not dispatch/retry CI. Original I must ordinarily merge
the exact Q SOURCE and publish a new cumulative SOURCE before its necessary new
CI. Original e635 failure, Windows cancellation and all earlier Q/B/history
remain unchanged. That new integrated Linux/Windows gate is still pending here.
No global pip/auth/HOME/configuration or AOCI assets changed; child processes
exited, and private first evidence remains. Real Engine/key/probe/SDK create,
science, AT-07, L2, main/tag/deployment remain NOT_RUN. Token usage/cost/savings
remain UNKNOWN. This closes only Q's fixture repair.

## 2026-10-03 Q: dynamic-port prerequisite review and unapplied host packet

Owner Q, task `task_90f7d319dd74`, dispatch `ctx_9d2d8cbf6ca9`, continues
completed task33fe in the same tree/branch/terminal. Governance read was root
`ac861af727bcf3420b3e150cac72438a6cec3aa6` (21:57 plan). This is a docs-only
REPORT: Q production, tests, profile, dependency/lock and AOCI assets have no
delta. Original approved AT07 attempt stopped before key/deploy/create, SDK0,
and its 600s window ended; that first STOP and all prior RED/green/CI history
remain. This review does not replay it or declare actual AT07/review PASS.

**Finding: approved-address-only reachability is UNKNOWN; pre-create STOP.**
Static rules do not establish actual inbound reachability or prove future
Docker-published ports are isolated. Private raw evidence is at
`C:/research-private/q-at07-firewall-ctx9d2d-20261003`; observations began
2026-10-03T14:00:59Z. No listener, firewall mutation, Engine mutation, SDK
create, probe, key access or science was performed. Desktop was already
running from B's separately recorded start; Q made bounded read-only queries.

### ActiveStore and effective matching facts

`read_firewall.ps1` uses `Get-NetFirewallRule -PolicyStore ActiveStore
-DisplayName 'Docker Desktop Backend','codex_sandbox_offline_block*'` and the
associated application/service/port/address/interface/interface-type/security
filters. Only six relevant rules and bounded port/WSL queries were emitted.
`related-rule-filters.json` and `read-firewall-first.log` retain raw values.

| Relevant rule | Direction/action/profile | Matching filters and limitation |
|---|---|---|
| Docker Backend TCP / UDP Query User rules | Enabled, inbound ALLOW, Public; direct ActiveStore reads Enforced | Exact `C:\Program Files\Docker\Docker\resources\com.docker.backend.exe`; service Any; respective TCP/UDP; local/remote ports and addresses Any; interface/type Any; local/remote users and machines Any; authentication/encryption NotRequired; OverrideBlockRules false; edge traversal Allow |
| Codex nonloopback inbound / outbound | Enabled BLOCK, profiles Any | Program/service/protocol/ports/interface Any; local address Any; remote IPv4 excludes 127/8, remote IPv6 excludes only ::1; security LocalUser is SID ending1007, not Any; authentication/encryption NotRequired, OverrideBlockRules false |
| Codex loopback TCP / UDP outbound | Enabled BLOCK, profiles Any | Same local-user SID1007; remote127/8 and ::/127; TCP remote1-65535 or UDP Any. This outbound match cannot by itself block Backend inbound publication |

Two existing Backend processes, PID69744 and72724, have the exact executable
path above and owner SID ending1005; creation times are privately retained in
`backend-identity-first.json` and `backend-owner-sids.json`. This establishes
that the observed SID1007 restrictions do not match those Backend owners.
Microsoft documents that LocalUser filters match traffic to/from the listed
principals, rather than all applications/users.
[Security-filter contract](https://learn.microsoft.com/en-us/powershell/module/netsecurity/get-netfirewallsecurityfilter?view=windowsserver2025-ps).

WLAN and Mihomo are Public. WLAN has IPv4 and IPv6 Internet connectivity;
Mihomo has IPv4 Internet and IPv6 local connectivity. No SSID/account name is
published here. All three ActiveStore profiles have firewall enabled, inbound
default Block, outbound default Allow, inbound/local firewall rules allowed,
and no disabled-interface alias. MpsSvc is Running/Automatic. The current Q
principal is **not administrator** (`firewall-authority-prerequisites.json`),
so this session has not established permission to apply rules.

An application-filter association lookup returned the same two Backend rule
IDs but `NotApplicable`, including when ActiveStore was specified. The original
direct rule query and a final exact-Name ActiveStore query both returned
`Enforced`; all three outputs remain, including this projection discrepancy.
Use direct effective-rule reads for the recorded status, not a silently
normalized association status. Other providers/exception rules were not
exhaustively dumped and are not declared absent.

Explicit matching Windows Firewall BLOCK takes precedence over conflicting
ALLOW, while an explicit ALLOW beats the default inbound Block. Consequently,
a narrow new ALLOW cannot restrict the existing broad ALLOW, and an Any BLOCK
cannot be repaired with an ordinary ALLOW exception.
[Rule precedence](https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/rules).
These are matching-rule conclusions. WFP also arbitrates providers, layers
and action-override rights; this review neither enumerates every WFP provider
nor substitutes rule text for a packet traversing the relevant layers.
[WFP arbitration](https://learn.microsoft.com/en-us/windows/win32/fwp/filter-arbitration).

### Docker forwarding, IPv6 and frozen-version limits

Read-only official CLI queries used the absolute Docker executable, explicit
`--host npipe:////./pipe/dockerDesktopLinuxEngine`, a newly owned empty
`--config` directory, shellFalse, timeout10s, and only PATH/SYSTEMROOT/WINDIR.
`read_docker.py` retains argv/env names/raw results and executable SHA256;
no Docker context/auth/HOME/proxy variables were inherited. No Config.Env,
container auth labels, key or expanded Compose output was read.

| Read | Actual result |
|---|---|
| `version --format` selected server data; `info --format` ID/version/OS | Desktop4.77.0; Engine29.5.3, API1.54, MinAPI1.40, Linux/amd64, WSL2 kernel; daemon `6cc73c96-c021-4a82-ade6-2fc9ae693fff`; exit0 |
| `network inspect bridge --format` selected networking fields | driver bridge, subnet172.17.0.0/16, gateway172.17.0.1, EnableIPv6=false, Internal=false; exit0 |
| `ps -a --format` Ports only; `Get-NetTCPConnection` Listen / `Get-NetUDPEndpoint` local47400..47410 | No current publication/listener record for this range. No existing resources were altered |
| `Get-NetNat` selected fields | Empty. This does not prove absence of Docker Desktop's VM/backend forwarding |
| WSL creator Hyper-V VM settings and rules in ActiveStore | Enabled, default inbound Block/outbound Allow, LoopbackEnabled and AllowHostPolicyMerge true; selected rules include profile defaults/ICMP/mDNS, no47400..47410 exception. No proven mapping of the future Backend relay through this layer |
| Exact `container inspect morph-r1-at07-server` selected networking fields | First exit1, `No such container`; no actual service-proxy address can be read before this service exists |
| Fixed `image inspect ...server:release-1.1.0@sha256:68ca...` | First template exit1 because Labels field absent; corrected safe-index read exit0, exact imageId/RepoDigest68ca, Labels=null. Image revision and packaged source contents remain UNKNOWN |

Docker documents that Windows/WSL2 published ports pass through
`com.docker.backend.exe`, which listens on host ports and forwards into the
Linux VM; default publication uses all interfaces. Host firewall rules may
filter that executable. This is the relevant architecture, rather than an
inference that Windows Get-NetNat or Linux host iptables shows the whole path.
[Docker Desktop networking](https://docs.docker.com/desktop/features/networking/).
The observed Hyper-V settings describe WSL policy; loopback enablement and
policy merge alone do not prove the specific Desktop publication boundary.
[Hyper-V firewall](https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/hyper-v-firewall).
Bridge/egress IPv6 disabled does not demonstrate that the Windows host's
IPv6-facing Backend sockets cannot accept inbound connections.

The original profile's Git bytes remain1013B, SHA256
`438fe04be51d07188b6bc4b26fbd85c2e7ce28dc02e31ed3af2a4cf27f3c0b79`,
read from core15de. It declares upstream
`b1a29cf93a823a95913f7943010febb3f29de05c`. Official GitHub blobs for that exact
revision were fetched privately and their Git blob bytes checked, without
installing/importing upstream code: configuration.md/config.py/networking.py/
docker_service.py have no publish_host; port_allocator.py defines
DOCKER_PUBLISH_HOST=0.0.0.0, and sidecar execd/http bindings also use0.0.0.0.
host_ip controls endpoint resolution, not publication binding.
[Declared-version configuration](https://github.com/opensandbox-group/OpenSandbox/blob/b1a29cf93a823a95913f7943010febb3f29de05c/server/opensandbox_server/config.py),
[allocator](https://github.com/opensandbox-group/OpenSandbox/blob/b1a29cf93a823a95913f7943010febb3f29de05c/server/opensandbox_server/services/docker/port_allocator.py).
This source evidence does not establish image/source correspondence when the
image has no revision label. No main-branch field, version upgrade, host_ip
change or unverified profile switch is proposed as current support.

### Concrete minimal host packet: proposed, NOT applied or authorized

Root message `msg_c185348001a5` selected proposed permitted origins **127.0.0.0/8
and ::1 only**, excluding guessed private CIDRs/gateways. It did not authorize
firewall modification. Private `firewall-change-packet.ps1` contains one
uninvoked review function with exactly two New-NetFirewallRule calls; its
proposed parameters are:

| Field | Exact proposed value |
|---|---|
| Names | `Morph-R1-AT07-Q-ctx9d2d8cbf6ca9-TCP-NonLoopback`, `Morph-R1-AT07-Q-ctx9d2d8cbf6ca9-UDP-NonLoopback` |
| Store/group | PersistentStore / `Morph-R1-AT07-Q-ctx9d2d8cbf6ca9`; fresh unique owner names, no edit of existing rules |
| Direction/action/enabled | Inbound / Block / True |
| Program/service/users | Exact official Backend absolute path above; Service Any; LocalUser/RemoteUser/RemoteMachine Any, covering actual Backend SID1005 |
| Protocol and ports | One TCP and one UDP rule; LocalPort47400-47410, RemotePortAny |
| IPv4 nonloopback remote complement | `0.0.0.0-126.255.255.255`, `128.0.0.0-255.255.255.255` |
| IPv6 remote complement of ::1 | `::`, `::2-ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff` |
| Remaining match/security | ProfileAny, LocalAddressAny, InterfaceAlias/InterfaceTypeAny; Authentication/EncryptionNotRequired; OverrideBlockRulesfalse; EdgeTraversalBlock |

Both exact proposed names were absent in the read-only preapply lookup at
14:11:19Z; this is not a reservation or proof of later absence. It must be
rechecked in both PersistentStore and ActiveStore immediately before any
authorized attempt. Require separately approved scope and an elevated original
owner, current Backend path/process identity, MpsSvc Running, enabled effective
profiles/local-policy merge, and stable relevant rules/interfaces. Do not
change service, default policy, old Docker/Codex rules, profile438, daemon or
other ports. This packet affects this Backend port range regardless of local
user and must not be treated as permission to reuse another workload's ports.

If later authorized, record each create response once; if one rule creation
fails/is unknown, STOP before SDK and inspect only those exact names instead
of blindly reissuing the mutation. Before admission, retrieve both names by
direct ActiveStore query plus all associated filters and compare every field
above, enforcement and policy-store source. Recheck the existing Backend
ALLOW/security exceptions and current interfaces; any missing/overridden/
conflicting field, projection ambiguity or unapplied local policy stays STOP.
An absent listener or default Block is not a replacement for these checks.

Only exact owned-name rules whose full filters/store still equal the recorded
proposal may be removed by a separately authorized original owner. No wildcard
removal, foreign-rule deletion, default-policy restoration or automatic retry.
Unknown cleanup is preserved and handled by exact read-only inspection.
Removing rules invalidates this boundary for later same-ID L2 service use;
re-evaluate effective policy and reachability then, without inheriting old
probe authority across a changed host boundary.

Actual service-to-host.docker.internal forwarding may arrive with a
nonloopback source. The observed bridge gateway is not that source identity.
Under this proposed loopback-only approval, failure of the service proxy is a
pre-create STOP; do not widen the packet to gateway/private CIDR automatically.
If a future harmless control is separately approved, a bounded pre-SDK option
is one short-lived owned inert container from the already pinned Python image,
no volume/network creation or pull, publishing TCP+UDP at a freshly free port
inside this range. Use only owned local canary clients and the subsequently
approved service proxy to observe the actual connection/source, then remove
that exact control container before the original AT07 resource set (at most
five objects) and at most one SDK create. No control is implemented/run here.
Local self-connect checks cannot establish cross-host reachability; cross-host
testing remains outside this authorization. A denied/missing proxy control or
missing external-ingress evidence remains UNKNOWN/STOP, not a reason to retry
SDK create, relax the allowlist, or declare AT07 PASS.

### B API SOURCE review and closing limits

Root supplied B SOURCE `c3a905eaf79a869dffb5960da9c4afee1dc63c3e` in
`msg_5c09cad1eda0`. Q read its exact Git blobs and diff privately, without
merging, installing or testing it. Production delta is only generated.py's
Literal[1.52,1.54], retaining default1.52. The existing execute call chain
validates complete configuration, preflights the same FrozenDockerExport,
checks actual /version.ApiVersion equality, and passes the same bound config
to its CLI reader before _execute/key/SDK. Frozen request URLs use that
configuration's api_version. Direct backend admission still compares full
probe configuration and preflights before its unique SDK create.

The existing three test files add both-direction supported-API mismatch
zero-CLI/SDK assertions, explicit closed-schema/legacy-default cases,
unsupported API refusal, reverse probe conflict and /v1.54 archive assertions;
old substantive assertions remain. This bounded static review found no new
binding regression. It is not an independent installed/live PASS; no Q test
path was requested and no old54/full-core/product/UI/CI/type gate was rerun.
An initially guessed nonexistent adapter path produced Git exit128 and was
preserved; corrected sandbox_adapter.py raw identity was subsequently checked.

Handoffs `msg_9ecd716aed27`, `msg_8fed36a5d91d`, `msg_d8bb22339533` delivered
the first policy/identity gap, frozen-source/image limits and exact API review.
No Q business SOURCE was created. This ordinary docs-only commit/push uses
[skip ci]; root/original owners decide host permission and continuation, and
the same I owns any necessary later integration. Actual dynamic ingress,
service-proxy/NAT source and image revision remain UNKNOWN; actual AT07 and
L2 remain NOT_RUN. Token usage, cost and savings remain UNKNOWN.

## 2026-10-03 Q: guarded administrator preparation, execution NOT_RUN

Same Q owner/tree/branch/terminal, task `task_1c2ec01e428a`, dispatch
`ctx_8cb7185eb67f`, continues completed task90f7. Root read was
`7ef9ff73b578ce9e21cca08b297ca0db7e1bed9a` / 22:16 plan; the later explicit
TASK narrows this work to an administrator preparation packet. This docs-only
REPORT changes no production/tests/profile/locks/AOCI assets. REPORT04ad,
all first failures/unknowns and the original expired600s/SDK0 attempt remain.

Prepared standalone operator script:
`C:/research-private/q-at07-admin-ctx8cb7185-20261003/at07-firewall-operator.ps1`.
Reviewed SHA256:
`E2C23FF1A0CE3C84F80E02A101A1DDB235595A623F87C1CAE1F3066ACA51911F`.
It retains the original two rule IDs, exact official Backend path and original
TCP/UDP47400..47410 dual-stack nonloopback complement packet. No old rule,
default policy, profile438, daemon or other port is modified by its design.
This private file is a local operator aid, not a new repository module,
scheduler, registry, Manifest or scientific proof system.

Only standalone read-only file identity was observed at14:22:24Z, recorded in
`preparation-identity.json`: Backend Authenticode status Valid, Docker Inc
signer thumbprint `CACB4F507942C182C47EF14E7B9050CBDE780EB9`, executable SHA256
`3CB1FBA716D63EBBDB28CAC038ED98AA50CC07B91CB366F9A191CD9BDFBFC03E`, current
principal SID ending1005, IsAdministrator=false. These pins are guard inputs;
changed signed bytes/process owner cause STOP, not silent pin replacement.
[Official signature interface](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.security/get-authenticodesignature?view=powershell-7.5).

The script itself was **not invoked in any mode**, including Inspect. Apply,
Cleanup, UAC, Engine/listener/probe/SDK/key/science actions were NOT_RUN. Its
proposed runtime behavior is therefore untested, not a successful safety run:

| Mode / guard | Intended behavior, requiring actual future evidence |
|---|---|
| Default Inspect | New private output directory; read exact rule names in PersistentStore and ActiveStore, signed Backend identity/process owner, unused47400..47410 TCP/UDP listeners, MpsSvc, three effective profiles/local-rule merge, current interface categories, SID and IsAdmin. Query failure/conflict is recorded, not swallowed as absence |
| Nonadministrator, any mode | Record needs_admin and exit20 without calling either firewall mutator. A failed read remains in its separate first-error receipt |
| Apply | Require elevated SID1005, explicit `AuthorizeRuleChanges`, a non-secret rule-scope `AuthorizationRef` and exact `ReviewedScriptSha256`; require all preconditions and exact-name absence. One New-NetFirewallRule call per TCP/UDP, not a Set/update/overwrite |
| Effective readback | Direct exact-name ActiveStore reads, all seven associated filters, local/remote users/machines, source/type and enforcement. Require full expected fields and local PersistentStore source; Enforced must be present, only additional ProfileInactive is accepted. Missing/NotApplicable/other projection or enforcement is STOP |
| Override review | Save only named Docker/Codex related filters and bounded authenticated-bypass candidates. Potential applicable override, missing association or over-limit ambiguity stops. Other WFP providers and packet traversal remain UNKNOWN; no global rule dump is a proof |
| Cleanup | Separate authorization and fresh output, original Apply identity/created receipts required. Validate every intended removal's two-store complete saved snapshot first, recheck immediately before each exact Remove. No original returned/confirmed receipt, changed fields/store, absent/ambiguous rule or prior remove intent means STOP, not ownership by name alone |

Output is secret-free rule/process metadata, non-secret approval references,
UTC, raw returned CIM/error XML and JSON filters. Native command exit codes
are not fabricated for PowerShell cmdlets: receipts say ReturnedWithoutError
and NativeExit=NOT_APPLICABLE; the script result carries its actual intended
process exit0/20/21/22/23/30. Every result has Admission=STOP and retains
ServiceProxySource/ExternalIngress=UNKNOWN and AT07=NOT_RUN, even when rule
creation/readback or owned cleanup succeeds.

Receipts use FileMode.CreateNew plus flush, preserving first bytes. After
authorization/preconditions, one append-only apply intent in this packet
directory prevents a different output directory from replaying this Apply.
Each removal additionally appends one once-intent in the original Apply
receipt directory, without rewriting its first evidence. Failure/unknown
enters only exact-name inspection; there is no automatic retry, rollback,
cleanup, wildcard delete or recursive directory removal. Partial/unknown
creation without confirmed full readback cannot obtain cleanup authority.
Manual recovery from such unknowns needs original-owner review, not repeated
script invocation. The files are ordinary command receipts, not authority for
host isolation or science.

For operator review, the invocation shape is `powershell.exe -NoProfile -File`
the exact script path, with `-Mode Apply`, a fresh absolute `-OutputDirectory`
directly under this packet directory, `-AuthorizeRuleChanges`, the actual
new rule-scope approval reference and the reviewed SHA above. Cleanup uses
`-Mode Cleanup`, another fresh output child and `-ApplyReceiptDirectory` for
the original Apply receipts, plus its separate explicit authorization and
the same reviewed SHA. These are instructions, not commands Q executed.
No Start-Process/RunAs, execution-policy bypass/change, auth/HOME/env dump,
Docker command or listener launch is included. An existing OS/policy refusal
is another STOP; do not alter policy automatically.

Windows admin rights are a real OS requirement for modifying firewall rules;
the already accepted general AT07 approval does not make the current process
elevated. Root/operator may review the fixed path, scope and bytes, then choose
one accurate separately authorized elevated invocation using the normal
Windows UAC interaction. Q neither requested another generic AT07 approval
nor initiated UAC. Future root/original-owner actual execution must preserve
its own fresh full receipts and exact effective readback; a prepared script
does not demonstrate that Windows will apply these rules.
[Official create interface](https://learn.microsoft.com/en-us/powershell/module/netsecurity/new-netfirewallrule?view=windowsserver2025-ps),
[effective rule reads](https://learn.microsoft.com/en-us/powershell/module/netsecurity/get-netfirewallrule?view=windowsserver2025-ps).

`Parser::ParseFile` and installed Get-Command parameter metadata were used
without invoking the guarded script. `static-first.json` preserves the first
331-line preparation result; final356-line `static-final.json` records zero
parse errors, zero unknown literal/splatted cmdlet parameters, and exactly
one New and one Remove syntax site inside separate guarded branches. This
validates syntax/parameter names only, not parameter-binding side effects,
permissions, rule semantics or execution safety. No tests, green old gate,
package install or Engine operation was repeated.

Correction/limit for REPORT04ad's optional inert-container suggestion: **the
<=5 resource limit is cumulative, not merely simultaneous**. Deleting a
control then creating another does not reset it. No sixth cumulative
container/control is proposed as an executable route here. Any harmless
control path must be submitted by original B within the approved original
<=5 cumulative resources and at most one SDK create; it is not authorized
or implemented by this preparation. Actual service-proxy/NAT source and
external reachability remain UNKNOWN/STOP. Removing rules also invalidates
this boundary for future same-ID service/L2 reuse; no old probe authority
may silently survive that host-policy change.

Ready packet was handed to root before closing, for review and operation
selection. Only this appended own REPORT is ordinarily committed/pushed
with [skip ci], remote exact/clean checked; there is no new Q business SOURCE.
Actual apply/cleanup, complete network evidence, AT07 and L2 remain NOT_RUN.
Token usage, cost and savings remain UNKNOWN.

## 2026-10-03 Q: independent pre-SDK packet review, no execution

Task `task_6735e8f955e0`, Dispatch `ctx_7b3806335d93`, same Q owner/tree/branch.
Read B docs-only REPORT `6ea5e5dd81bdf53e33f46beed74f7382a804efaf` and
`C:/research-private/b-at07-pre-sdk-ctx_78a8eebd6960/control-proposal.json`,
root plan `09c52988390ba4eace08f2eb4e3592682c8b15a2`, Spec sections 10.1/14.3
and the original AT07 authorization. Later direct Task/status messages govern
where that plan snapshot is older. Private evidence is retained at
`C:/research-private/q-at07-presdk-review-ctx_7b3806335d93/`.
Reviewed production objects are core `82201af4d3b369da827f6f22ff1d9c6b608c0108`
and product `d5d387a6f5c1778dffdd860986843826420edf5e`; neither was executed here.

B's minimum proposal reuses the same server and target, adding only server
`0.0.0.0:47410:8090/tcp` and target `0.0.0.0:47410:9053/udp`, retaining the
original loopback publications. Fixed stdlib health/DNS positive controls use
the actual server ID/interpreter, typed official CLI, bound host/owned empty
config, shell=False, minimal three-variable child environment and outer 10s.
The declared interpreter path still needs actual confirmation; no new binary
revision, fake-label or complete pre-SDK sandbox-proxy gate is introduced.
Complete proxy testing belongs after the sole harmless SDK create. Original
preflight accepts any loopback8099 entry, not a unique mapping; B's first
misinterpretation and correction remain preserved. Actual HostConfig/Ports,
loaded configuration, same full IDs, cache ownership/destruction and effective
host filters must be recorded, not inferred from this static proposal.

The cumulative cap remains five containers (including transient cache), one
owned volume, zero new networks, one harmless SDK create and one 600s window.
Removing/recreating controls does not reset counts. Windows TCP47410 collision
with the server namespace allocator remains possible; failure is STOP, not a
second create or range change. Remaining >=420s before SDK is a conditional
planning threshold: core822 checks the 210s step limit between steps and the
240s expiry loop before each iteration; bounded CLI work and finish/inventory
still follow. It is not a hard 240s total runner deadline. Actual elapsed time
and the absolute 600s stop remain necessary; speed is not a new success gate.

Current read-only NetSecurity evidence (`current-exact-related-filters.json`)
contains only six previously identified related rules and their application,
service, port, address, interface/type and security filters. Backend inbound
TCP/UDP still allow Any port/remote address; Codex blocks have different local
security identity constraints, so they cannot stand in for Backend protection.
The two exact owned Q names returned zero matches in PersistentStore/ActiveStore.
All three ActiveStore profiles are enabled and allow local-rule merging; their
LogAllowed/LogBlocked are disabled. Interface/profile facts are recorded
separately from packet behavior. SID1005 is still nonadmin. Q operator SHA
`E2C23FF1A0CE3C84F80E02A101A1DDB235595A623F87C1CAE1F3066ACA51911F`
is unchanged, every mode NOT_RUN. No UAC, policy/logging/WFP change or packet
execution occurred. Windows admin is an OS requirement, not another request
for the already accepted AT07 authorization.

Spec AT-07 requires real harmless file/network/resource refusal; the original
authorization requires approved dynamic-port reachability before SDK creation.
The proposed health/DNS successes establish only their positive route. Static
rules, an enabled profile or local loopback failure cannot prove external denial.
Within one host, legitimate future evidence is the original operator's exact
rule/store/filter readback, actual publications and interface/profile, plus an
already available bounded WFP/drop record tying the actual nonloopback source,
destination port/protocol, application and deny decision to that path. A client
in already-budgeted infrastructure is useful only if host-visible source and
filter traversal are established; NAT/self-route assumptions are insufficient.
No extra listener/container, cross-host requirement or logging reconfiguration
is added here. Such packet/source attribution is absent now: external ingress
and service-proxy/NAT source remain UNKNOWN/STOP, not risk-accepted PASS.
This is an existing admission limitation, not a new requirement to test the
nonexistent sandbox's complete proxy before its sole authorized creation.
Official context: [Docker Desktop networking](https://docs.docker.com/desktop/features/networking/),
[Windows rule precedence](https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/rules)
and [firewall logging](https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/configure-logging).

Old background identity is now narrowed to exec session19099: Python PID68432,
parent64640, CreationDate `2026-10-03T19:54:17.771131+08:00`, private
`source-lf-venv/Scripts/python.exe -I .../verify_install.py ... fc866465aa52a3f09773bc79a0fab95bceedc3d9`.
Historical call at 11:58:46.963Z matched PID/creation/command before stopping
only that owned import; its stop-command receipt is exit0, chunk49c7d4.
This is not the original exec's exit code. Current exact PID/path queries find
no matching process, but an empty poll still returns session19099 without an
exit code (chunk1b1d38). Exec retirement/all-background cleanup is therefore
NOT_ESTABLISHED; no current kill/CtrlC was sent. The earlier report's blanket
private-process-exited sentence is qualified by this distinction, not erased.
Original interruption ownership and this unresolved session state are retained.
The first history-reader sharing failure is also preserved before the successful
FileShare.ReadWrite read of this exact own session; no empty history was inferred.

Root received the concrete checkpoint and handoff, including the unresolved
exec, external evidence gap and budget qualification. Current Task reports core
CI Win1839/15SKIP, Linux1838/16SKIP, strict140 and SDK wheel green; product
whole254PASS/2FAIL and P test-only c0dd targeted/I follow-up remain pending.
Those are coordinator facts, not Q reruns or whole-engineering acceptance.
Verification here is read-only Git/source/NetSecurity/process inspection and
`git diff --check`, followed by ordinary docs-only `[skip ci]` publication with
remote exact/clean checks. Production/tests/locks/profile/compose/AOCI and the
original operator are unchanged. All first REDs, the original 600s STOP/SDK0,
the B first misread and prior reports remain. Actual controls, apply/cleanup,
SDK, real AT07, isolation, candidate/L2/science remain NOT_RUN; this review is
complete but is not runtime reviewPASS. Token usage/cost/savings remain UNKNOWN.
