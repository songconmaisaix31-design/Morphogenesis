# Windows TTL=2 renewal timing repair, 2026-10-03

Scope: `decentralized-swarm`, starting at
`ef77af603577d4539d8dbdf780e1536a369b0d12`. Only renewal scheduling,
new regression coverage and this report change. `swarm/lease.py`, TaskLedger,
the original `test_lease.py` and `test_worker_runtime.py`, TTLs, fencing tokens,
expiry checks, safety assertions and submission/recovery ordering are unchanged.

Validated SOURCE commit: `3c079cc85eef333351835c0cb47e3849f8c16f7d`.
The final branch HEAD adds only this report. The tested COPY and installed
wheel's renewal source were compared byte-for-byte with the committed blob.

## Historical RED remains historical

The original Windows CI run `35889933044` at
`d4808870bf5b196babf40ebf3f82503365fe9074` reported 1 failed / 466 passed;
its truncated assertion did not establish the cause. The separate 09-24
counterexample delayed the `submitting` status write by 2.5 seconds with TTL=2:
9 renewals preceded `LeaseLost` at submit. That demonstrated the old ordering
gap (stop renewal, then persist status), not the cause of every CI failure.
The status-before-handoff repair is already present in this task's starting SHA.

Neither original evidence nor its interpretation is overwritten:
`docs/SWARM_RUNTIME.md`, section "Submission handoff investigation, 2026-09-24";
`.runtime/swarm-integration-20260924/ci-windows.log`;
`.runtime/swarm-integration-20260924/c-status-gap-before.log`.

## Remaining defect and bounded fix

The renewal loop still waited a full `min(1, TTL/3)` **after** each renewal
returned. SQLite establishes the renewed expiry before transaction completion
and returning to the caller. Thus 1.5 seconds of completion latency plus the
next 0.667-second wait exceeds TTL=2 even though the lease was still valid when
renewal returned. Both controlled-time and Windows real-wall-clock regressions
reproduce this on the starting implementation.

`_Renewal._run` now subtracts monotonic elapsed renewal/lock time from the next
wait, retaining the existing interval and 1 ms lower bound. There is no retry on
rejection or I/O error. The existing handoff still joins the thread, renews once
with the configured TTL and immediately submits the exact lease. A stall past
expiry still fails closed; this does not provide a real-time guarantee.

The related repair in this repository at
`5e24715c7002d254dd908aea53ce82e86c12ebf3` was inspected and reused narrowly;
its regression concept is adapted to this branch's ledger (which has no
`renewed` audit event), with an additional real-wall-clock completion-delay
case. No unrelated branch changes are merged or cherry-picked.

## Local Windows evidence (completed 2026-10-04 CST)

Interpreter: existing worktree `.venv/Scripts/python.exe`, Python 3.12.13.
Tests execute a Git archive COPY under `.runtime/lr1003/src`, with the changed
files copied from the worktree (normalized to exact staged Git blob bytes for
the final full run). State, pytest basetemp and logs
are siblings of that source COPY under `.runtime/lr1003`; TEMP/TMP must name
`.runtime/lr1003` itself so the older gateway fixtures remain below OS temp.
This keeps
all writes in the authorized worktree without weakening source-path guards.
BLAS/OMP/MKL thread counts are process-local and set to 1; no dependencies,
global settings or credentials change. The COPY also contains the existing
local `@evomap/gep-mcp-server` 1.7.0 package, required at a source-relative path;
its remaining Node dependencies resolve from the existing worktree installation.

| Gate | Result | Preserved log |
| --- | --- | --- |
| Starting SHA: original lease + worker_runtime | 37 passed / 154.37s / exit 0 | `logs/01-baseline.txt` |
| New regressions against starting implementation | **2 failed, 3 passed / 9.24s / exit 1** | `logs/02-renewal-red.txt` |
| Fixed renewal + lease + worker_runtime | 42 passed / 80.24s / exit 0 | `logs/03-focused.txt` |
| First full pytest: incorrect TEMP layout and missing COPY-local MCP package | **63 failed, 857 passed, 10 errors, 2 warnings / 600.48s / exit 1** | `logs/04-full.txt` |
| Correct TEMP layout: gateway audit retest | 7 passed / 2.53s / exit 0 | `logs/04a-temp-layout-retest.txt` |
| Existing MCP package supplied to COPY: MCP tests | 5 passed / 14.01s / exit 0 | `logs/04c-mcp-layout-retest.txt` |
| Full pytest with correct TEMP layout | **930 passed, 2 warnings / 930.46s / exit 0** | `logs/04b-full.txt` |
| Strict | 89 source files, no issues / exit 0 | `logs/05-strict.txt` |
| Offline build | sdist + wheel built / exit 0 | `logs/06-build.txt` |
| Official SDK check | contract_local checks passed / exit 0 | `logs/07-sdk.txt` |
| Offline wheel install and distribution check | 13 packages, resources, verifier and Node dependency passed / exit 0 | `logs/08-wheel-install.txt`, `logs/09-distribution.txt` |

The full-run warnings are the existing Pydantic serialization warnings from
budget rejection cases with `input_tokens=nan` and `input_tokens="1"`.
Build used `--no-isolation` with an unchanged copy of the already installed
pure-Python `poetry-core` 2.5.0 in `.runtime/lr1003/build-deps`, exposed only
through that build process's PYTHONPATH. No package download or global install
was performed. The wheel target and uv cache are also private to this worktree.

All log paths above are relative to `.runtime/lr1003` and remain local ignored
artifacts. The new RED is a separate retained run; later green evidence does
not replace either it or the original 09-24 RED.

Commands from the source COPY, using the interpreter above:

```text
python -u -m pytest -q tests/swarm/test_worker_renewal.py tests/swarm/test_lease.py tests/swarm/test_worker_runtime.py --basetemp=../focused-tmp
python -u -m pytest -q --basetemp=../full2-tmp
python tools/typecheck.py
python -m build --no-isolation
npm run check:sdk
uv pip install --offline --no-deps --python ../../../.venv/Scripts/python.exe --target ../wheel-site --cache-dir ../uv-cache --link-mode copy dist/morphogenesis-0.1.0-py3-none-any.whl
python -I tools/check_distribution.py --site-dir ../wheel-site --check-node
```

Evidence is `contract_local`: real Windows threads, clocks, SQLite and local
fixture effects. No model, paid API, real Hub, sandbox, science execution or
deployment is run. Original-CI causation beyond the proven counterexamples and
new exact-SHA remote CI acceptance are not claimed.

## Lifecycle limitation

This user-started session has no injected Task/Dispatch preamble and no
`ORCA_TERMINAL_HANDLE`. `orca orchestration run-current --json` returned
`no_active_sender_terminal`. The missing original dispatch context was requested
while implementation continued. A `worker_done` delivery cannot be claimed
without an accepted receipt from this session's authorized sender; another
terminal or historical dispatch must not be substituted.
