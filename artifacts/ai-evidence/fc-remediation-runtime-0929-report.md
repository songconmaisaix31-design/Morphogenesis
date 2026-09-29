# Track A: execution persistence and reservation cost state

Owner evidence, 2026-09-29. **Scoped contract_local gates passed; no independent
acceptance, H1/H3 sign-off, formal FC-E or live acceptance is claimed.**

- Worktree: `C:/Users/DW/orca/workspaces/Morphogenesis/morph-fc-runtime-fix-0929`.
- Branch: `morph-fc-runtime-fix-0929`.
- Base: `3a34ecafe5f48b1a5a7c94c9e063797427817cab`.
- Reproduction commit: `58cec571dd209b01ba6fc9e354288ab06a77acab`.
- Tested production/test commit: `f2be38864c87632ca8a41d0471b4b4bfcfef1d74`.
- Remote: `https://github.com/songconmaisaix31-design/Morphogenesis` (`origin`).
- The final evidence-only tip, remote comparison and clean status are supplied in
  the delivery message. Production and tests remain byte-identical to `f2be388...`.

## Changes and exact data flow

All line references below refer to the tested commit above.

**Task 1.** `swarm/worker_loop.py:778` calls `TaskLedger.begin_execution` immediately
before the real executor boundary. `swarm/task_ledger.py:358` stores the existing
reservation's request ID in the existing task row as `unconfirmed_request_id`
and appends an existing task audit event. This is a task fact, independent of the
budget. No scheduler, Attempt lifecycle, Manifest or hashing infrastructure was
introduced. The additive SQLite column is installed at `task_ledger.py:104`.

`task_ledger.py:259` excludes unconfirmed tasks from both normal candidate routing
and atomic lease claims, including expired claims and voluntary handoffs. The
owned release path at `task_ledger.py:387` leaves such a task `blocked`, instead of
making it available. An already handed-off task retains its handoff status but
the durable unconfirmed marker still excludes it from routing and claiming.

`worker_loop.py:812` clears only a confirmed effect, with the current fenced lease
and matching request ID (`task_ledger.py:374`). Unknown effects keep the marker
even when usage and prices are known and their reservation is genuinely settled.
An unknown-effect classification also takes precedence over candidate presence
(`worker_loop.py:840`). `keeper.lock` covers only the short begin/confirm ledger
transactions; executor/model calls occur outside the lock and SQLite transaction.

The recovery tests use real `Worker.run`/`_process`, SQLite, router and leases.
Same-identity restart and different-identity recovery run in new spawned Python
processes. Another case performs actual `LeaseManager.handoff` inside the external
executor boundary. Each asserts no new executor invocation or reservation with
zero outstanding hold, settled known fixture usage/cost and available budget.
Confirmed-rejection switching, successful task completion, and completed-task
recovery remain positive controls. Fixture provenance is `mock`; no live child
process is mocked and no paid request occurs.

**Task 5.** The exact `Reservation` returned by `reserve` is passed to
`BudgetLedger.reservation_cost_state` after settlement (`worker_loop.py:802`).
`budget.py:213` reads that durable row through the existing `_stored` identity
check. Pending maps to `reserved`; settled with observed estimate maps to
`settled`; uncertain/unknown-cost-allowed maps to `unknown`. This value flows
through `worker_loop.py:824,861` to `FailureObservationFact` and the real append-only
FaultObservation store, keyed by the same request ID. It never reads aggregate
cost to infer a single reservation's status. `settled` means the existing ledger's
local estimate settlement, not an observed provider bill.

Tests cover both `allow_unknown_cost` values for known usage without prices:
`tokens=2`, `usage_metering=verified`, `cost=unknown`, `estimate_usd=NULL`, full
`.2` hold retained, observation `cost_state=unknown`. A prior unknown rejection
hold followed by a currently settled reservation proves aggregate unknown cost
does not mislabel the current observation. No fabricated zero or released unknown
hold is introduced.

## Failures retained and applicable gates

Commands use the read-only existing Python at
`C:/Users/DW/orca/workspaces/Morphogenesis/morph-fc-integration-0927/.venv/Scripts/python.exe`.
See [original reproduction](fc-remediation-runtime-0929-repro.md) for the complete
original-failure sequence, including setup and test-scoping errors.

| Evidence | Result / actual exit | Local raw log under `.runtime/` |
| --- | --- | --- |
| First reproduction setup | 6 setup errors / 1 | `original-setup-error.log` |
| Initial new-test run before narrowing the success control | 5 failed, 1 passed / 1 | `original-red.log` |
| Original production, correctly scoped restart/handoff and cost regressions | 5 failed, 2 passed / 1 / 25.48s | `original-scoped-red.log` |
| Original production, unknown effect carrying a candidate | 1 failed / 1 / 7.68s | `original-candidate-red.log` |
| First fix gate, WIP overlay | 1 failed, 117 passed, 2 warnings / 1 / 278.18s | `fix-r1.log` |
| Second fix gate, exact LF `f2be388...` archive | **119 passed, 2 warnings / 0 / 172.21s** | `fix-r2.log` |
| Scoped strict typing, three changed production files | **3 files, no issues / 0** | `types-scoped.log` |

The first fix gate's actual failure was
`test_lost_lease_after_successful_execution_prevents_submission`: `len(results)=1`
but `len(handoffs)=0`. Its callback used the original claim's expiry after real
renewal changed the persisted expiry; it raised `LeaseLost` before performing the
handoff. Only the arrange line was corrected to read the current persistent lease.
No TTL was lengthened, keeper bypassed, test skipped, or assertion relaxed.
All original assertions in the four permitted existing test files were compared
as ASTs to base: boundaries **61**, runtime **50**, budget **67**, budget_evomap
**21**, all identical. The other three files have no diff.

Exact second-gate source export:

```text
git -c core.autocrlf=false archive --format=zip --output=.runtime/fixed.zip f2be38864c87632ca8a41d0471b4b4bfcfef1d74
```

The ZIP was extracted to `.runtime/fixed-src`; `PYTHONPATH` points there and
`swarm.worker_loop.__file__` was checked. Production source has LF line endings.
State lives in sibling `.runtime/test-state`, never beneath the tested source.
The ignored SDK junction reuses the existing 1.14.0 installation after checking
the destination was absent and package version matched; no dependency install.

Commands from `.runtime/fixed-src` (`<python>` is the absolute executable above):

```text
<python> -m pytest -q tests/swarm/test_unknown_effect_recovery.py tests/swarm/test_reservation_cost_state.py tests/swarm/test_failure_chain_boundaries.py tests/swarm/test_failure_chain_runtime.py tests/swarm/test_budget.py tests/swarm/test_budget_evomap.py tests/swarm/test_worker_runtime.py tests/swarm/test_ledger.py tests/swarm/test_lease.py --basetemp=../test-state/fix-r2 -p no:cacheprovider
<python> -m mypy --strict --follow-imports=silent --cache-dir=../mypy-scoped swarm/worker_loop.py swarm/budget.py swarm/task_ledger.py
```

The two warnings are the unchanged deliberate Pydantic invalid-model-copy cases.
This is not a full-suite or full-repository strict rerun.

## Semantic mutations and restoration

Command from the worktree root (overall exit **0**):

```text
<python> artifacts/ai-evidence/fc-remediation-runtime-0929-mutations.py .runtime/fixed-src
```

| Mutation | Actual failing behavior / red exit | Restored check / exit |
| --- | --- | --- |
| Omit `begin_execution` | Same/new Worker restart and handoff each resend: `1 != 0`; 3 failed / 1 | 9 passed / 0 / 36.09s |
| Reinstate usage-only cost inference | Both no-price policies report settled instead of unknown; 2 failed / 1 | 9 passed / 0 / 26.76s |
| Infer current cost from aggregate | Prior unknown hold makes current settled observation unknown; 1 failed / 1 | 9 passed / 0 / 26.82s |
| Make real ledger handoff a no-op | Existing loss-of-lease test observes `completed` instead of `failed`; 1 failed / 1 | 9 passed / 0 / 26.11s |

The handoff mutation proves the corrected arrange still depends on real lease
loss. All assertions run outside Worker exception handlers. Every mutation uses
`finally` to restore original bytes, verifies byte equality and SHA-256, and then
runs the eight new cases plus the original loss-of-lease test. Exact commands,
exits and local log paths are in `.runtime/mutation-results.json`;
logs use `mutation-<name>.log` and `restored-<name>.log`.

Restored bytes were also compared directly with `fixed.zip`:

- `swarm/worker_loop.py`: `cab098cb5cbb39bd8fedc25dd08c88c0430a5f121bf880ae863d64bd75c33442`.
- `swarm/task_ledger.py`: `5016de95bf73da51b0f1d236a78f1462f7dc063b516fee135bcb4a239f26e698`.
- `swarm/budget.py`: `7f9e7a2fa38d1c45b0da0ad6a74f5d940f5b94a2538d14308b98d7ba7814b710`.

## Diff scope and remaining acceptance

Changed paths: `swarm/worker_loop.py`, `swarm/budget.py`, `swarm/task_ledger.py`,
`tests/swarm/test_failure_chain_boundaries.py`, new
`tests/swarm/test_unknown_effect_recovery.py`, new
`tests/swarm/test_reservation_cost_state.py`, and the three
`artifacts/ai-evidence/fc-remediation-runtime-0929-*` evidence files.
Protected governance, SWARM contracts, locks, plans and TASKS have no diff.
B confirmed no Worker guard glue was required; no cross-track source was edited.

Unknown-effect tasks remain isolated pending verified reconciliation; this patch
adds no automatic retry, unblocking API or late uncertain-to-settled reconciliation.
Existing unknown fee holds continue to occupy capacity. There is no provider bill
claim. Mixed-version deployment and recovery of historical pre-fix state were not
validated; no production state was migrated in this task.

Integration must run the merged candidate's full tests, full strict, build, SDK
and distribution gates. H1/H3 and formal FC-E remain open; independent acceptance,
`interface_live`, `task_live`, paid live calls, production merge, tag and release
are **NOT_RUN** here. Passing this Owner subset does not freeze or sign off FC.
