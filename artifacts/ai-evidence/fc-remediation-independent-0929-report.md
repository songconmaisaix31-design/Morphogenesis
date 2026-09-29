# D independent FC remediation acceptance, 2026-09-29

Status: **D independent local acceptance complete on the common candidate**.
D final focused 47 passed; all nine semantic mutations failed as expected and
restored green; I's six gates independently read and all actual exits 0.
This closes these five local remediation checks, not FC release/freeze or human/live gates.
No production, Owner test, Schema, plan, TASKS, AGENTS or lock file is edited by D.

## Scope and source authority

Base `3a34ecafe5f48b1a5a7c94c9e063797427817cab`. Reviewed AGENTS, QWEN,
docs/source/README_包内说明.md, FC_ACCEPTANCE, FC_REMEDIATION and FC_CLOSEOUT.
The current dispatched five-fix task overrides old closeout's prohibition on Owner
repairs; D remains acceptance-only. D report branch is
`morph-fc-independent-final-0929`, initially at A `4d1098ed151d6a9859e088f13ea292baeef1acf2`.
Report commits do not redefine the accepted code SHA.

**Only code candidate under review:** `c552250c0d07f5f70f09eb0a5ab3c322195e34ec`,
branch `morph-fc-candidate-0929`, independently remote-matched with
`git ls-remote origin refs/heads/morph-fc-candidate-0929`.
Parents are `5cf2612c04a34dfb17af12af817ebee8c08432dc` and C final below;
first merge parents are A final and B final
`2c6a33ae1950fd6458543618d1c4044dcdd2596f`. B final adds only its report to
the reviewed B production SHA. Common candidate repeats the same old-test AST
result (exit 0). No D evidence commit enters the code candidate.

Preliminary inputs:

- A final `4d1098ed151d6a9859e088f13ea292baeef1acf2`.
- B production `751864580d7043e4187d896bf7036ffc756b5b04` (not final integration).
- C final `e6ac45ffefc171a7215f8db19bc4a28af24ec4fc`.

Production write paths are disjoint. A persists an unconfirmed request before
executor entry and gates both routing/claiming on it, independently of cost;
reads the current reservation for observation cost. B adds token equality to
probe completion and durable recovery time/file position, retaining JSONL.
C lets Worker guard reclaim expired probes atomically and moves both adapters'
5xx classification ahead of body billing/quota interpretation.

## Original tests retained

`fc-remediation-independent-0929-static.py` compares every original test function
AST and its assert/decorator AST against each input. Command: designated read-only
Python, this script, then the three full SHAs above. Exit 0. Each input retains
**464 original test functions, 1,558 assert nodes, and all decorators unchanged**.
Only A changes an existing function body: loss-of-lease test arrange reads the
current renewed lease before real handoff. No assert changes. B adds tests and a
sqlite3 import; C adds files. Original loss-of-lease semantics will also be tested
with D's own success-result/handoff/no-publication probe on the common candidate.

## B original full failure audit (not a passing gate)

Read raw `../morph-fc-breaker-fix-0929/.runtime/full.log`: **47 failed, 656 passed,
2 warnings, 7 errors; exit 1; 578.25s**. All 54 traceback blocks hit an OS TEMP
guard: codex 9, gateway 28, rehearsal 6, runtime 4, gateway_audit setup 7.
Three tracebacks end in regex-mismatch assertions because the premature guard
raises a different message. Representative log lines 34-43 call
`orchestration/codex.py:54`, quote:
`executor requires a dedicated directory under the OS temp root`.
Log lines 1896-1903 call `orchestration/rehearsal.py:130`, quote:
`rehearsal requires a new private root under OS TEMP`.

This supports the layout explanation for observed failures; it does not exclude
deeper failures hidden behind that precondition. Retain this red gate. I must run
full on the common SHA with process-local TEMP/TMP at the isolated state parent,
source/state siblings and unchanged safety checks. D does not promote the 656 subset.

## D independent plan and evidence boundaries

The accompanying focused script reuses baseline fixture construction helpers only;
it does not call Owner tests or Owner mutation drivers. Its own assertions count
real executor/HTTP mock boundaries outside production catches. New OS processes
run real Worker routing against shared durable state. Mock transport does not
intercept live child processes. Fixture token counts are explicit synthetic input;
absent provider usage/price stays unknown.

Independent mutations remove unconfirmed execution persistence, expired
probe routing, recovery-history filtering/equal-time boundary, 5xx priority and
current-reservation cost selection, plus original suspended-transition semantics.
Only ignored exact-source copies may change; original bytes must restore in finally,
then selected tests must return green.

## D execution on the common candidate

All production citations in this section refer to immutable
`c552250c0d07f5f70f09eb0a5ab3c322195e34ec`.

| Requirement | Independently checked behavior | Exact code anchor / verbatim quote |
|---|---|---|
| Known-cost unknown effect | 4 combinations of same/different Worker identity and real lease handoff, each using a fresh OS process; recovered executor count 0, no result; initial reservation settled with 2 synthetic fixture tokens, no unknown hold, budget not sleeping and less than 10% charged; normal confirmed-rejection→success and successful-executor/lease-loss controls | `swarm/worker_loop.py:778` `self.ledger.begin_execution(keeper.current, reservation.request_id)`; `swarm/task_ledger.py:259` `"AND t.unconfirmed_request_id IS NULL "` |
| Expired probe | Before TTL, 0 executor calls; exact TTL boundary produces fresh token via real Worker; stale success and failure have no effect including same owner; two concurrent Workers on separate real task scopes execute exactly once total | `swarm/failure_chain.py:138` `claimed = breaker.try_claim_probe(provider, view.reason, worker_id, now=now)`; `swarm/breaker.py:655` `if not actions or current.probe_token != probe_token:` |
| Recovery history | Same Worker, previously cached peer, and new OS process reobserve retained JSONL; stale pre-success aggregate also reapplied; old bytes unchanged; two new equal-time faults execute, next executor call is blocked, four observations retained | `swarm/breaker.py:662` `recovery_sequence = self._recovery_store.checkpoint()`; `swarm/fault_observations.py:114` `sample.sequence > sequence and sample.occurred_at >= at` |
| Classification priority | Both adapters: status 0, 400, 403, 429, 500, 503, 599 with bilingual account/quota structured bodies; actual EvoMap HTTP mock→executor→Worker sends [1,0] for 5xx, [1,1] for ordinary 4xx; interrupted 400 body sends [1,0]; unknown usage remains null and holds retained | Both adapter files `:34` `if status_code == 0:` (followed by existing comment), `:44` `if status_code >= 500:`; `swarm/evomap_executor.py:112` `if response.error_kind:` |
| Current reservation | With valid usage and no price, cost unknown and 0.2 hold retained with allow_unknown_cost false/true; historical unknown plus current priced settlement records [unknown,settled] while global cost remains unknown | `swarm/worker_loop.py:802` `cost_state = self.budget.reservation_cost_state(reservation)`; `swarm/budget.py:223` `if row["status"] == "settled" and row["cost"] != "unknown":` |

Interpreter for all D Python commands:
`C:/Users/DW/orca/workspaces/Morphogenesis/morph-fc-integration-0927/.venv/Scripts/python.exe`.
D source: `.runtime/candidate-src`; state: sibling `.runtime/test-state` / `.runtime/m2`.
Process PYTHONPATH is the source, TEMP/TMP the relevant state parent, numerical
thread counts 1, PYTHONDONTWRITEBYTECODE=1. No dependency installation or lock change.
Existing `morph-fc-integration-0927/node_modules` SDK 1.14.0 is reused through
an ignored junction after absence/version checks, read-only.
The first external-file pytest invocation created its default root `.pytest_cache`
(creation time matched this run). D relocated only that generated cache to
`.runtime/pytest-cache-retained`, verifying both absolute paths first; final focused
and the delivered mutation command disable cacheprovider. No unrelated file was removed.

Exact export command:
`git -c core.autocrlf=false archive --format=tar --output=.runtime/candidate.tar c552250c0d07f5f70f09eb0a5ab3c322195e34ec`.
Windows tar.exe could not decode four Chinese document paths; extraction was
completed using the designated Python tarfile on the SAME archive. All **346
archived files compared byte-for-byte** against the exported files before tests.
This was an extraction tool failure, not a test result or altered candidate.

Commands from exported source:

```text
python -m pytest ../../artifacts/ai-evidence/fc-remediation-independent-0929-focused.py -q -x --tb=short --basetemp ../test-state/focused-first
```

Result: **46 passed, exit 0, 73.31s** (`.runtime/focused-first.log`). Child process
probes explicitly checked distinct PID and source import within the exported tree.

Final run after all mutation bytes were restored, with history assertions ordered
to test behavior first, and the unchanged original loss-of-lease test added:

```text
python -u -m pytest ../../artifacts/ai-evidence/fc-remediation-independent-0929-focused.py tests/swarm/test_failure_chain_boundaries.py::test_lost_lease_after_successful_execution_prevents_submission -q --tb=short --basetemp ../test-state/final -p no:cacheprovider
```

**47 passed, exit 0, 73.71s**, no skips, deselections or warnings
(`.runtime/focused-final.log`). Durable raw evidence excerpts are preserved in
`fc-remediation-independent-0929-evidence.txt`; the full original ignored state is
retained for inspection. D did not change any Owner source or test assertion.

## Retained D restoration failure and environment correction

The first mutation run's equal-time case correctly failed at executor count **3
versus 2**, exit 1. Its restoration test then failed earlier at successful probe
validation (`quarantined`, not completed), exit 1, 6.97s. This red is retained;
it is not accepted as a restored pass.

Durable ValidationReport in the test's `chain-state/assets/assets.sqlite3` contains
`reasons=["git_operation_failed:worktree"]`. Replaying exactly that failed local
fixture's `git worktree add --detach` gave **exit 128**, stderr:
`fatal: '$GIT_DIR' too big`. Full argv/stdout/stderr are retained in
`.runtime/restore-git-diagnostic.json` and the evidence extract. It only affected
D's ignored fixture, not the code worktree. The sole runtime correction is shorter
temporary directory names: pytest case root 154→120 characters, corresponding
validation worktree 216→182 (Git's internal directory is deeper); no source safety
guard, product timeout, Git global setting, Owner assertion or test was altered.

First unmutated rerun with `--basetemp ../test-state/r1`: **1 passed, 45 deselected,
exit 0, 11.26s**. D also moved the history probe's existing executor-count assertion
before its state assertions, preserving every state assertion, so stale-history
mutation must now fail on actual boundary behavior. Resumed mutations use short
numbered state directories and redo both history cases.

## Independent semantic mutation results

The accompanying D mutation script is written independently of Owner drivers.
Every selected mutation changes exactly one occurrence, verifies original bytes
against candidate Git first, restores in `finally`, compares the restored bytes,
then reruns its selected real behavior tests. Logs are retained in `.runtime/mutations`
and `.runtime/m2`; the final evidence extract includes original reds, restoration
failure, environment diagnostic and subsequent successful pairs.

| D mutation | Actual red assertion / count | Restored result |
|---|---|---|
| Remove begin_execution persistence | 4 cases: restarted executor count 1 instead of 0 | 4 passed, exit 0 |
| Disable expired-probe guard claim | 2 cases: executor count 0 instead of 1 | 2 passed, exit 0 |
| Disable recovered-history filter | after reobserve actual executor count 0 instead of 2 | 1 passed, exit 0 |
| Change equal-time boundary >= to > | new faults ignored; actual executor count 3 instead of 2 | 1 passed, exit 0 |
| Disable DashScope 5xx guard for 503 | 2 actual adapter results confirmed_rejection instead of unknown_effect | 2 passed, exit 0 |
| Disable EvoMap 5xx guard for 503 | real executor/HTTP fallback count [1,1] instead of [1,0] | 1 passed, exit 0 |
| Infer cost from usage/uncertain flag | 2 cases: observation settled instead of unknown with retained unknown hold | 2 passed, exit 0 |
| Infer cost from global snapshot | 2 cases: current settled observation wrongly unknown because prior hold is unknown | 2 passed, exit 0 |
| Change original suspended transition to normal | original preserved test reaches `test_failure_chain_runtime.py:124`, actual executor count 1 instead of 0 | 1 passed, exit 0 |

Each listed red has **exit 1**, each listed restored run **exit 0**. The initial
watermark mutation also failed a state assertion; it was redone after asserting
boundary count first, and only the latter behavior-first pair supports the table.
The initial equal-time restoration red is explained and retained above; its short
path red/restored pair is the accepted pair. No unexpectedly green mutation is
claimed effective. All **346 archived files** were byte-equal to the original Git
archive after the last mutation.

Commands from D report root (absolute Python as above):

```text
python -u artifacts/ai-evidence/fc-remediation-independent-0929-mutations.py .runtime/candidate-src .runtime/mutations c552250c0d07f5f70f09eb0a5ab3c322195e34ec
python -u artifacts/ai-evidence/fc-remediation-independent-0929-mutations.py .runtime/candidate-src .runtime/m2 c552250c0d07f5f70f09eb0a5ab3c322195e34ec 2
```

The first driver stopped with exit 1 at the recorded restoration environment
failure. The resumed driver (case index 2 onwards, including repeat history pair)
exited 0; successful first two pairs remain in the original directory. Focused
deselections in these targeted mutation runs are explicit, not full-gate exclusions.

## I same-candidate gates independently read by D

Raw logs are in sibling `morph-fc-candidate-0929/.runtime/`; this is I execution,
not a D full/strict rerun. D read command, native exit, SHA, cwd and output, plus
source/import preflight and the distribution check implementation.

| Gate | Evidence read | Result |
|---|---|---|
| Focused | `focused.log`, full 14-path pytest command, no skips/deselections | 408 passed, 2 warnings, exit 0, 278.45s |
| Full | `full.log`, `python -u -m pytest -q --basetemp=../test-state/full -p no:cacheprovider` | 862 passed, 2 warnings, exit 0, 589.58s |
| Strict | `strict.log`, `python tools/typecheck.py` (calls mypy --strict) | 87 source files, exit 0 |
| Build | `build.log`, `python -m build --no-isolation --outdir ../dist` | sdist + wheel, exit 0 |
| SDK | `sdk.log`, `node tools/check_sdk.cjs` | schema 1.14.0 valid, ID verified, tampering rejected, published=false, exit 0 |
| Distribution | `distribution.log`, offline --no-deps own-wheel target install; `python -I tools/check_distribution.py --site-dir ../wheel-site --check-node` | install/check exit 0; 13 wheel packages, resources, installed verifier and Node dependency passed |

Build uses existing Poetry backend 2.5.0 from a read-only uv cache path in the build
process only; no installation of third-party dependencies. Distribution isolates
imports to the new wheel target and removes source from sys.path. D additionally
compared **83 Python files in BOTH the wheel ZIP and installed target to candidate
Git blobs**, all equal (`.runtime/wheel-origin-audit.json`). I preflight records all
346 archive files, 23 changed paths and eight relevant production imports exactly
matching this candidate, with tempfile.gettempdir at sibling test-state. Focused
warnings are the existing intentional invalid-model-copy Pydantic cases; none were
suppressed. I full ended at `2026-09-29T11:14:03.0550248Z`, actual exit 0;
same two intentional warnings, no skips/deselections. This is a new common-SHA
full run, not reuse of A/B/C or historical logs.

D independently ran collection only (`python -m pytest --collect-only -q
-p no:cacheprovider`): **862 collected, exit 0**. All **54** node IDs from B's old
failed/error cases remain in this collection. D then compared BOTH I and D archive
contents and post-gate exported files: **346/346 byte-identical**. Thus the collection
and final I full cover the unchanged old failures on this candidate, without skipping
them. The old B red remains historical evidence rather than being relabeled green.

Final D read-only Git verification of I: HEAD and `git ls-remote` both
`c552250c0d07f5f70f09eb0a5ab3c322195e34ec`; status empty. I's final-verification
log also records diff-check exit 0, remote exit 0, zero porcelain lines and post-gate
source verification exit 0. D's own report-only branch is separately committed and
pushed; final report SHA is provided in the delivery, never substituted for code SHA.

DashScope production executor is **NOT_IMPLEMENTED**: code search finds only the
pure adapter; `swarm/evomap_executor.py:139` calls `EvoMapAdapter.interpret`.
Both real adapters can be exercised, while full HTTP/executor/Worker evidence is
EvoMap only. Coordinator confirmed this distinction; D does not fabricate a
DashScope production path. Independent Codex review is not formal DeepSeek FC-E.

## Open / NOT_RUN

No D acceptance work remains for the specified local candidate scope.
H1/H3 human approvals, formal FC-E, T6 three consecutive smoke runs and
entry/rehearsal remain OPEN/NOT_RUN under their separate owners and prerequisites.
Paid live, production merge/tag/freeze/publishing are NOT_RUN.
Local mock evidence never establishes interface_live or task_live.
DashScope full production executor remains NOT_IMPLEMENTED; only its real adapter
was accepted. Windows deep temporary paths retain the demonstrated Git length limit;
the corrected short layout is part of this local evidence. Late uncertain-cost
reconciliation/release, real provider billing and mixed-version deployment are not
established by these gates. D performed no formal DeepSeek review or human sign-off.
