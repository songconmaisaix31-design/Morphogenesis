# MorphBench DashScope A core successor, 2026-10-07

Task `task_5cc873bc4e7e`, dispatch `ctx_e283b709decc`; owner branch
`songconmaisaix31-design/morphbench-live-core-1007`, base
`445aad4e3066e7cbfc0123adc1779d24d0c74cd4`. Scope is the last execution page of
`docs/PLAN.md`. Prior report `morphbench-final-1007.md` stays historical and
unchanged. Runtime evidence: `C:/Users/DW/orca/mb-live-1007/core`.
After the host OOM/restart the coordinator fenced that dispatch and resumed the
same task/worktree as `ctx_2a60f63e70e5` on 2026-10-08. Historical results below
remain attached to their original runs; the recovery does not erase them.

Final SOURCE: **`d5bd40cea91b09ddf669be5e063e726186191fc4`**. It is pushed and
the remote branch was verified equal before the documentation-only REPORT
commit. Relative to the completed broad-regression SOURCE below, its only
changes are `swarm/budget.py`, `swarm/worker_loop.py` and
`tests/swarm/test_code_executor.py`: the two B-reported audit/HTTP stop defects
and their tests. The exact REPORT SHA is sent through the coordinator handoff
after this file is committed and pushed. A has released the heavy test/build
window; no paid calls or user-credential reads were made by A.

Completed broad-regression SOURCE: `d5cb717f734eb34cb17855d3075c4f37c43667ca`, following the first
core candidate `948252311018a433cb4b4c905d8c5364a11d678f`. The latter contains
the policy, executor, validation and consumption changes; the successor adds
bounded HTTP phase observations and their regression test. Both are ordinary
commits on the owner branch. Source commits exclude this report; its eventual
documentation commit is REPORT, not a replacement source pin.

The first push of the trace successor failed with `SSL_ERROR_SYSCALL`.
`ls-remote` still showed the earlier candidate before one ordinary retry
succeeded; the observed remote then equalled the frozen SOURCE. Original and
retry outputs are separate `push-trace-source*` evidence files. No force push.

## Change and causal scope

One new scheduling policy is opt-in: `WorkerConfig.energy_policy="claim"`
charges every acquired lease, including rejected execution, instead of every
sensing cycle. `"cycle"` remains the default. Previous 192/200 completion and
the cycle decrement before selection motivated the controlled hypothesis that
lost claims can consume otherwise usable local execution allowance. This is
not proof of the cause of any particular historical incomplete trial.

`max_senses` bounds the entire worker identity's persisted sensing count,
including no candidates, dependency waits and contention. Runtime, idle,
shared RunLimits, reservations, unknown usage and fencing still independently
stop work. Restart does not replenish energy or senses; changing the stored
energy/routing policy is rejected. This is not success-only charging.
`stop_when_local_terminal=False` optionally waits for future arrivals under the
same idle/sense/runtime limits; the default keeps the existing terminal exit.

`routing_strategy="v0"|"v0.1"` exposes the existing Router policies through
WorkerConfig. Default remains v0. No new routing algorithm, field projection,
feedback reward, scheduler, ledger, hash or proof mechanism was added. Comparing
claim+v0.1 against cycle+v0 is a combined intervention, not isolated routing
causality. Formal task-live results belong to B's frozen protocol and run.

## Fixed code contract

The existing data-only executor still only produces JSON data. The separate
`swarm.code_executor.DashScopeCodeExecutor` accepts `DashScopeCodeConfig` and
one `CodeTask` payload:

```python
api = DashScopeCodeConfig(
    model="qwen-plus-2025-12-01", max_input_bytes=12000,
    max_output_tokens=1536, temperature=0.2, seed=1234,
    prompt_profile="Check boundaries.",
    phase_profiles={"0": "Check boundaries.", "1": "Check order.", "2": "Check boundaries."},
)
payload = {"instruction": "Public repair specification", "output_path": "task/sample.py", "phase": "0"}
policy = SampleValidationPolicy(version="sample-tests-v1", path="task/sample.py")
# ledger.enqueue(signal, acceptance={"validation_policy": policy.model_dump(mode="json")})
# worker = Worker(config, DashScopeCodeExecutor(api))  # Only B may invoke live.
```

The reply is JSON `{changes:[{path,before,after}],adopted_asset_ids:[]}`.
`SamplePatch` and `candidate_from_patch` bind this data to host-owned attempt,
scope and snapshot identities. One existing `sample.py`, at most 16 KiB of
source, may change. Source preimage must match. Tests, arbitrary scripts,
commands, imports and other runtime capabilities are rejected. Model context
contains the public instruction, buggy source and explicitly supplied experience;
no acceptance policy, expected source or fixed tests are sent.

`SampleValidationPolicy.executor="fixed-sample-v1"` is a separate operator
selection. `literal-files-v1` retains its original byte-equality semantics.
The new policy reuses `orchestration.sample_policy.validate_sample` and
`bootstrap.acceptance_runner` for the fixed clamp/mean/unique exercise. A
trusted runner outside the candidate tree checks three function suites in a
private copy with Python `-I -S`, a cleared child environment and timeout.
Only the existing pure-function allowlist is admitted. This is **not an OS
sandbox, arbitrary Python execution, generated research admission or AT-07**.
Explicit arbitrary validation commands remain rejected. Reports identify
`fixed_pure_sample_subprocess`; approval checks the policy and report identity.

## Request and budget boundary

No A-run paid calls or credential reads. Production execution is B-owned and
requires coordinator approval of exact SOURCE and budget. The credential is
obtained only inside the HTTP child through the fixed .NET
`Environment.GetEnvironmentVariable('DASHSCOPE_API_KEY','User')` entry via
PowerShell and a private captured pipe. It never goes to the parent Worker,
patch process, inherited environment, command arguments or evidence files.
The parent refuses an inherited DASHSCOPE_API_KEY. HTTP uses the existing
single-request transport and provider classification; no retries or redirects.

Requests fix the model snapshot, nonthinking mode, output cap, temperature and
seed. Operator-owned phase profiles are selected by payload phase 0/1/2; they
never inject success rates or winners. Request/response evidence records
provider/model/request IDs, settings, input/source/experience, usage, cached
input when supplied, elapsed time and uncertainty. Missing usage stops the
branch without replay. Actual billing remains null. Cache usage is an additive
observation on the shared Reply and does not discount the conservative budget.
The HTTP child also records `http-trace.jsonl` with send-entry, response-header
and transport-return observations, PID, epoch and monotonic times. Its
`child_entered_at` is an application timestamp, not OS process CreationDate.
Send-entry alone is not proof of a transmitted packet or server receipt. The
fault harness must separately observe process identity and preserve unknown
outcomes when no response has returned; the trace never authorizes a retry.

`ExecutionBound` is explicitly unbounded/provider_enforced=False: token and
cost estimates are local admission accounting, not provider billing guarantees.
Existing ModelPrices/BudgetPolicy USD fields retain their semantics. B declared
6 CNY per USD as a fixed accounting conversion assumption, not a market quote;
convert CNY published prices/allowances before supplying USD fields and report
CNY estimates separately. Shared request/attempt caps and non-transferable
trial allocations must enforce the aggregate approved ceiling.

## Cross-session experience

Keep the original same-swarm state/ledger/assets, create a fresh Git workspace,
new worker identity and process. A new task declares the completed source task
dependency and `reuse_task_id`/`path_map`. Source scope/capability/dependency
checks and approved content fetch still run. The exact fetched content enters
the request. Claimed IDs must be in the provided set.

For a transformed code reply, `AssetConsumer.derive` appends a consumption
linked to the original execution, retaining source/preimage/attempt/scope and
the actual returned patch. The literal consumption is not rewritten. The
returned patch still needs fixed independent validation, approval and a
completed fenced target effect before the existing adoption path records it.
The final result names the derived execution ID. Distinguish context supplied,
model-declared use, validated/applied adoption, and causal benefit. None alone
proves general scientific usefulness.

An incorrect source rejected by fixed tests stays quarantined. Existing
AssetConsumer refuses it; it cannot be approved with a substitute literal
policy just to populate the control. The wrong-experience control therefore
measures refusal/no adoption, not model exposure to unsafe unapproved content.

## Validation and limits

First focused run: **13 PASS / 1 FAIL**, `focused-first.log`/XML/exit. New test
had incorrectly marked a root Git commit as a scope snapshot; successor uses
the real snapshot function. Original assertion and failure are retained.
First scoped strict run: two missing generic annotations; repaired. Second
scoped strict: **9 source files PASS**. First SDK check: **PASS**, official
GEP 1.14.0 schema/address/tampering checks, contract_local, not publication.
First full strict: **38 errors in 4 unchanged files**, 162 checked files: 37 in
three tools/morphbench files handed off to B, one redundant cast in
orchestration/experiments/frozen_export.py handed off to the coordinator/I,
all outside A write_paths. No exclusion or weakened type assertion was added.
These historical cross-owner errors remain RED on this branch; focused type
success does not imply a clean whole-repository result.

Second focused run: **16 PASS / 2 FAIL**, retained in `focused-second.*`.
Transformed consumption initially left the original execution ID in the task
result, so final adoption failed; fixed by binding the derived execution ID.
Unknown usage on a worker with zero remaining energy originally resumed as
`exhausted`; the durable uncertainty now takes precedence and remains sleeping.
Third focused run: **20 PASS**, including the actual fresh-process/fresh-target
reuse, unchanged assertions, wrong-code rejection and no replay of unknown use.

First isolated build failed fetching poetry-core from the configured mirror
with HTTP 403. Second isolated build used uv's cached declared poetry-core
2.5.0 and successfully built wheel and sdist. First attempted exact VCS install
was rejected by uv's Windows file URL parser before installation; existing
dependency installation is separate and does not prove source installation.

The first full core/assets regression collected 575 tests but was interrupted
near 14 percent during the host OOM. Passing observations, FAIL/ERROR rows and
the lack of final XML/exit remain in `core-regression-first.log`. The terminal
also observed Node `ERR_MEMORY_ALLOCATION_FAILED`; individual incomplete test
failures are not relabelled as passing or presumed harmless. No owned Python,
uv or Git processes remained at the recovery checkpoint. Recovery is performed
in A's exclusive serial test window with BLAS/OMP threads limited to one and
without changing global pagefile or Docker settings.
The original regression parent started before the trace successor was edited;
later subprocess import bytes could differ. That interrupted run therefore
does not establish a single exact-source full regression. The recovery freezes
production and test bytes for the entire run and collects 576 tests.

Recovery trace test: **1 PASS**, 45.26 seconds, `trace-recovery.log` and exit 0.
Recovery scoped strict typing: **10 changed production files PASS**,
`type-trace-recovery.log` and exit 0. The frozen regression starts with all
tracked production/test bytes matching SOURCE; only this report is modified.
Its elapsed time is a correctness-check observation under a shared host, not
a MorphBench performance score.

Completed recovery: **576 PASS, 2 warnings**, 1053.47 seconds, exit 0, on
`d5cb717f734eb34cb17855d3075c4f37c43667ca`. Evidence is
`core-regression-recovery.log`, `.xml` and `.exit.txt`. The two Pydantic
serialization warnings originate in the invalid-input regression; they are
retained in the log. No full suite result is inferred for a later SOURCE.

B then identified a narrow audit-label gap: successful fixed code tasks still
retained `task_live=not_run` because the existing branch only recognized
`bounded_json`. A new test first reproduced **1 FAIL**, 16.29 seconds, exit 1,
in `audit-label-first.*`. The successor recognizes `fixed_sample_patch` only
with live provenance, passed interface, `promoted`, and a passed independent
report with `fixed_pure_sample_subprocess` isolation. Only `_finalize` emits
`promoted`; it first requires completed ledger state, matching owner, fencing
token, result, swarm and scope, and `effect_applied`. Approval or validation
alone cannot grant the label. This labels the fixed local repair task, not
general research, OS containment, AT-07 or a human acceptance decision.
Existing immutable audit artifacts are not rewritten or retrospectively graded.

The audit test uses a real mock-produced, independently validated/applied
repair, then tests synthetic projection inputs without any live request.
Mock, failed/unknown interface, rejection, missing/failed/wrong-isolation
report and unregistered task kinds stay `not_run`. A missing target effect,
pending task or stale token cannot emit a completed audit. These test rows
are contract-local evidence, not real provider or task-live observations.
Audit successor validation: **8 PASS**, 112.47 seconds, exit 0,
`audit-label-successor.*`; this includes the actual Worker kill/TTL/stale-submit
and expired-scope rejection cases, plus the code executor and projection matrix.
It ran on the audit-label delta above the completed broad-regression SOURCE.

B also identified that `continue_on_rejection=True` could continue after a
confirmed HTTP 401, because the existing generic chain intentionally admits a
bounded switch under an unknown rejection hold. The new fixed-model protocol
requires stopping instead. `http-stop-first.*` retains **2 FAIL / 1 PASS**,
30.33 seconds, exit 1: both known-usage and missing-usage 401s continued to
energy exhaustion; the independent validation-failure continuation control
already passed.

The successor reuses `BudgetLedger.settle(..., stop_on_provider_error=True)`
only for fixed code HTTP errors (`http_status >= 400`). The new argument is
false by default, preserving the generic/data-only chain. The existing shared
budget breaker is set in the settlement transaction; later reservations by
peers or restarts are refused. Observed usage is settled faithfully, absent
usage retains its unknown hold, and already admitted work can settle its
original result without clearing the stop. It does not retract in-flight
requests or claim zero concurrent outbound work. Provider failure classification
is retained separately, so a server error does not become a confirmed rejection.
Local fixed-validation failure can still continue under the existing option.

Final checkpoint on SOURCE `d5bd40cea91b09ddf669be5e063e726186191fc4`:

| Check | Result | Runtime evidence |
| --- | --- | --- |
| Code executor, all budget and failure-chain tests | 79 PASS, 2 retained warnings, 68.38 seconds; exit 0 | `final-boundaries.log`, `.xml`, `.exit.txt` |
| Strict mypy, all 11 changed production files | PASS; exit 0 | `type-final-boundaries.log`, `.exit.txt` |
| Isolated wheel and sdist with cached poetry-core 2.5.0 | PASS; exit 0 | `build-frozen.log`, `.exit.txt`, `dist-frozen/` |
| Ordinary source push and remote readback | PASS; remote matched SOURCE | `push-final-source.log`, `.exit.txt` and coordinator handoff |

The final 79 tests include known/missing-usage 401 stopping, peer/restart
admission refusal, settlement of an already admitted peer, validation-failure
continuation, the audit matrix, actual cross-process experience reuse, and the
unchanged data-only budget/failure-chain assertions. The preceding 576 result
belongs to d5cb717; the final delta was checked by these applicable 79 tests.

Validation interpreter is
`C:/Users/DW/orca/mb-live-1007/core/venv/Scripts/python.exe`, with a private
editable development install of this worktree. This is not independent
installed-package acceptance. B/I retains the final exact noneditable COPY
installation and distribution/import provenance checks. No paid request or
actual Windows user-credential read occurred in A's development checks.

Recorded commands, from the owner checkout with that interpreter (use a fresh
evidence path for any successor, preserving the paths recorded here):

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
python -m pytest -vv tests/swarm tests/local_assets --junitxml=C:/Users/DW/orca/mb-live-1007/core/core-regression-recovery.xml
python -m pytest -vv tests/swarm/test_code_executor.py tests/swarm/test_budget.py tests/swarm/test_budget_evomap.py tests/swarm/test_failure_chain_runtime.py tests/swarm/test_failure_chain_boundaries.py --junitxml=C:/Users/DW/orca/mb-live-1007/core/final-boundaries.xml
python -m mypy --strict local_assets/consume.py local_assets/models.py local_assets/promote.py local_assets/sample_validation.py local_assets/validate.py orchestration/gateway_transport.py swarm/budget.py swarm/code_executor.py swarm/code_patch.py swarm/evomap_executor.py swarm/worker_loop.py
python tools/typecheck.py
$env:UV_OFFLINE='true'
python -m build --installer uv --outdir C:/Users/DW/orca/mb-live-1007/core/dist-frozen
npm run check:sdk
```

The first successful build and SDK check were on the first core candidate;
the isolated build was repeated successfully on final SOURCE. SDK code,
dependencies and locks did not change afterward, so its original successful
evidence is retained without an unnecessary repeat. Full strict typing remains
the cross-owner RED described above. B/I must finish the independent noneditable
installation, aggregate type repair and exact integration acceptance. Real
DashScope runs still require coordinator protocol/source/budget freeze and the
sole API owner B; A's local/mock checks provide no task-live performance result.

AOCI tools are not exposed and this worktree has no `.mcp.json`. AOCI volumes
exist, but no current complete cognition/maintenance receipt was obtainable.
Work remains source-bound; index assets were not modified and are not claimed
current. No product frontend, lock files, prior runtime evidence, arbitrary
research sandbox, provider credentials or original baseline results were changed.
