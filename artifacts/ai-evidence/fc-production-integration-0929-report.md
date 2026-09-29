# FC production integration and independent acceptance — 2026-09-30

LOCAL INTEGRATION AND INDEPENDENT ACCEPTANCE COMPLETE; RELEASE BLOCKED.
All six required local gates ran on the fixed final candidate and passed, with
first-run failures preserved below. This is not a release, human signature,
formal FC-E review, or live acceptance. No post-test report commit
will be appended to the code candidate. Raw logs and per-command metadata are beside
this report; metadata includes full argv, cwd, interpreter, UTC times and native exit.

## Immutable candidate

- Branch: `morph-fc-production-integration-0929`.
- Final candidate: `8c76af727cf8a669c0b22b65586c2a0a70577e72`.
- Parents: `35016ffff836635b23f94c74121a7ca1f2407926` and
  `1d7753957a982f1f67f29ffa02e8f064d4f67a41`.
- Base: H3 `be4fb7a685e951c9e42d8dc0c7eeb900cb5518f1`.
- Serial ordinary no-ff merges: A `cb0902395d4e1fa89390c67c1cdfb6cec1607b72`
  -> `be27d3c7ad821faf5303de92cef2a201890e43ba`; B
  `cbec0b31fc1e27bfee1b83bd84e1f34097c19a19` ->
  `35016ffff836635b23f94c74121a7ca1f2407926`; C
  `1d7753957a982f1f67f29ffa02e8f064d4f67a41` -> final candidate.
- Each merge contains `Swarm-Agent: codex`. Git author identity is inherited;
  the executing Worker is Codex. No history rewrite, cherry-pick or domain fix.
- Ordinary push succeeded and `git ls-remote origin
  refs/heads/morph-fc-production-integration-0929` matched the full SHA.
  `identity.json`, `push.log`, `remote-candidate.*` retain evidence.
- Exact whole-tree composition verified: C552 plus the three authorized deltas,
  with only the frozen H3 document selected from be4. 99 paths differ from the
  be4 creation base; 33 differ from C552. Complete paths and lineage are in
  `identity.json`, including the inherited historical FC changes.
- The only merge conflict was `docs/FC_LOG_SCHEMA_DRAFT_0928.md`, resolved by
  the explicitly authorized complete be4 blob
  `61af30bde619af296afdf1b68e029c119e95c7a3`. Its fenced JSON is byte-identical
  to packaged `orchestration/fc_log_schema.json`.
- All original tests are retained. The only existing test changed by A,
  `tests/t2/test_rehearsal.py`, preserves every original assertion and decorator
  in all four original test functions (independent AST comparison).

## Source and environment

Worktree: `C:/Users/DW/orca/workspaces/Morphogenesis/morph-fc-production-integration-0929`.
Source: its ignored `.runtime/candidate-src`, exported with
`git -c core.autocrlf=false archive --format=zip --output=.runtime/candidate.zip <final-sha>`.
All 375 archived files verified byte-for-byte. Tests use source imports from this
archive, never an Owner's mutable tree. State is outside source in this report's
`state/`; process TEMP/TMP point there. `gate-env.ps1` records the complete layout.

Python is the newly created worktree `.venv/Scripts/python.exe`, CPython 3.12.13,
created by `uv tool run poetry install --no-root --no-interaction` from unchanged
`poetry.lock`. All 88 current-platform active lock packages match installed versions;
the Emscripten-only package is not an active dependency. Ten actual production
module `__file__` paths resolve inside the archive (`environment.json`). Bootstrap
archive extraction / initial Git-only identity used B's read-only interpreter,
not the interpreter used for product gates. Node dependencies were independently
installed from the unchanged package-lock using `npm ci --ignore-scripts --no-audit
--no-fund` in the archive (99 packages).

Build uses the worktree Python and `-m build --installer uv`, command-local official
PyPI, isolated declared backend `poetry-core 2.5.0`. A separate new deployment venv
and Node installation are used for installed-wheel validation. No global TLS/index
configuration, project lock or dependency declaration is changed.

## Recorded local results

- Complete focused second pass: 452 passed / 2 original warnings / 837.19s,
  native exit 0. `focused-2.meta.json` contains the exact original selection and
  unchanged thresholds. First-pass failures remain separate below.
- Complete full second pass: 899 passed / 2 original warnings / 600.17s,
  native exit 0, 2026-09-29 16:44:14.4084865Z to 16:54:16.6167497Z.
  `full-2.log`, `full-2.exit`, and `full-2.meta.json` agree. All 899 tests were
  collected and run with unchanged assertions, timeouts and no deselections.
- Strict: exit 0, 89 source files, including new logger and drill.
- Build: exit 0, new sdist and wheel built from this final archive.
- Official SDK: exit 0, package 1.14.0, schema_version 1.14.0, schema valid / asset ID verified / tampering rejected,
  `published=false`, `contract_local`.
- Schema: original 12/12, expanded 24/24, controls 13/13, exit 0. Original illegal
  controls remain illegal. Count null without issue_audit is VALID. FaultObservation
  remains exactly 14 fields, matching its model schema. No implicit audit zero.
  The reused JSON-Schema-only tool retains historical `NOT_IMPLEMENTED` text for
  arbitrary count-versus-array-length comparisons; this is not the new logger's
  runtime status. The new consumer checks that relation in `fc_logging.py:83-87`
  and its existing semantic negative tests are retained.
- Independent five-P0 probe: 47 passed in 95.14s, native exit 0. Reused exact D
  probe blob from `9a6705c7aeae9c812329c015f13e440842beff17`, run anew against this
  final SHA, plus the original loss-of-lease test. This is not reused old evidence.
- Source six-stage CLI: exit 0, run
  `fault-drill-8ffcbb59207b4973a086af8efca4f05d`, 21 actual validated JSONL rows,
  failure_count 0. A observation `5cbaf6ab75124442a3a1cdfe4fa0f3b0` is present in
  B's actual store reads; B executor calls alpha=0/beta=1. After cooldown, actual
  token 1 and alpha=1/beta=0; original history retained, same/other/restarted
  instances remain normal. D's independent probe additionally uses real OS process
  restarts. All five 0.2 reservations remain uncertain/full-held (total 1.0), usage
  and cost null. These are SIMULATED/mock facts, not billing or live evidence.
- Fresh installed distribution: `tools/check_distribution.py --site-dir
  <deployment/.venv/Lib/site-packages> --check-node`, under that environment's
  `python.exe -I`, exited 0. All 13 packages import from installed wheel resources;
  installed fixed verifier and Node dependency check pass. `installed-fc` exits 0:
  actual module paths are inside that new site-packages, packaged logger / schema /
  rehearsal / Worker / drill bytes equal the final archive and generated wheel,
  schema has 14 FaultObservation fields, real unknown-audit emit validates with
  failure_count 0, and the wheel requires no docs tree.
- Mixed provenance/origin regression is included in both complete successful
  pytest runs: `tests/swarm/test_fc_logging.py:256` exercises a real Worker whose
  final admitted candidate changes to replay, with two distinct origin forms.
  Its task projection matches the admitted candidate and retains origin/failure
  count semantics. Worker audit/source sequence and rehearsal snapshot/event
  assertions run through actual product objects with fixture transports.
- Installed `python -I -m demo.fault_drill` also actually executes all six stages,
  exit 0, run `fault-drill-cd1cd199ea94413baf20ca442967862e`. Independent row inspection
  uses that same installed interpreter with `-I`. It reports 21 actual legal rows,
  failure_count 0, B actual reads/calls, restored probe state and five retained
  0.2 holds, cost/usage null. This is a separate installed mock run, not live.
- New deployment package check: all 89 installed packages compatible (88 locked
  dependencies + this wheel); all 88 active versions match the lock exactly.
  Node dependencies were also installed separately from the same lock, 99 packages.

## Independent semantic coverage and mutations

All references here are to the final candidate. The unchanged D probe tests
known-usage/known-price unknown effects across same/different Workers and actual
OS-process restart/handoff; the persistent fence is at `worker_loop.py:858` /
`task_ledger.py:259`. It checks TTL-expired claims through real Worker routing
(`failure_chain.py:138`), old success/failure tokens, and single-winner competition.
Recovery tests retain and reread original fault history in the same Worker, a
cached peer, and a fresh OS process; equal-time new observations still count
(`breaker.py:662`, `fault_observations.py:114`). Both adapters' 5xx account bodies
stay unknown with 4xx controls, including the real mock HTTP-to-Worker request
count path. Current reservation cost is selected at `worker_loop.py:882` /
`budget.py:213`, retaining unknown holds and distinguishing old unknown aggregate
cost from a new priced reservation.

Reused D mutation driver retains all nine original semantic changes, adding only
three explicit selections for B routing, Worker flush and rehearsal emit. All
12 mutated runs have native exit 1 with actual behavioral failures; all 12
restored runs have native exit 0. Each restores exact original bytes in finally
before its green run. Driver exit 0. Commands, source SHA, timestamps, interpreter,
actual red and restored output are in the worktree's ignored
`.runtime/mutations/.runtime/state/<case>-{red,restored}.{log,meta.json}`;
`mutation-summary.json` is the copied actual result table.

| Mutation | Observed failure caught; restored behavior |
|---|---|
| effect-persistence | Unknown-effect task sends again after restart (4 failures); 4 restored passes |
| ttl-worker-guard | New expired-TTL Worker cannot execute (2 failures); 2 restored passes |
| history-watermark | Historical faults block legitimate new executions; restored test passes |
| equal-time-new-fault | Equal-time newer facts are missed; restored test passes |
| dashscope-5xx | 503 account text loses unknown priority; restored test passes |
| evomap-5xx | Real request-count control changes after 503; restored test passes |
| cost-from-usage | Usage-known/no-price is mislabeled settled (2 failures); 2 restored passes |
| cost-from-global | New priced reservation is mislabeled from historical unknown aggregate; restored test passes |
| original-suspended-transition | Original Worker observation/suspension behavior changes; restored test passes |
| drill-real-peer-routing | Actual B calls alpha=1/beta=0, caught outside Worker catches; restored alpha=0/beta=1 |
| worker-projection | Real Worker finishes but expected projected events disappear (3 failures); 3 restored passes |
| rehearsal-projection | Real published rehearsal loses events/diagnostic (3 failures); 3 restored passes |

`mutation-restoration.log` independently compares all 375 archived files in BOTH
the ordinary source and mutation source with the original final archive: exact,
candidate HEAD unchanged, worktree clean, frozen H3 unchanged. No variant bytes
entered the code candidate. Focused/full have no test selection exclusions;
mutation deselections are explicit narrow semantic probes, not replacements for
the complete gates.

Five real entrypoint helps (`orchestration.rehearsal`, `swarm.cli`, `viz.server`,
`orchestration.acceptance`, `demo.fault_drill`) each exited 0. The PowerShell
launcher parsed with zero errors; no standalone viewer/live launcher was started.
The full-suite fixture's private local listener is a test boundary, not a live
rehearsal or reused user listener.

## Failures retained during this run

- Initial broad `git diff --cached --check` against be4 found existing whitespace
  in the inherited FC history. No readonly source was reformatted. The intended
  new delta relative to C552 passed diff-check; exact composition was separately
  verified. B/C merge commands issued before the A merge commit consequently
  returned MERGE_HEAD/128; their original logs remain. After committing A, ordinary
  B/C merges succeeded without conflict. No candidate history was rewritten.
- Fresh-environment import was initially slow. One diagnostic importtime run
  preserved timed stack output and then exited 0; `source-environment` also exited
  0. No repeated heavy import diagnostic or source safety bypass was used.
- First focused and full failures are both retained. Focused native exit 1:
  6 failed / 446 passed / 2 warnings / 607.15s. Every failure is an existing mock
  `swarm.evomap_executor --request-child` subprocess exceeding its unchanged 30s
  timeout. The six failure names and all tracebacks remain in `focused.log`.
  Only dependencies in this worktree's own venv were precompiled (exit 0).
  Same-source worker importtime decreased from 55.565204s to 2.969729s; that
  supports an environment/cold-import/load explanation, not a uniquely proven
  cache root cause. Second focused keeps the original 452 tests/thresholds and a
  new state directory. No green subset supersedes the retained first failure.
- First full: 899 collected, 1 failed / 898 passed / 2 warnings / 1166.70s,
  native exit 1. Only `test_demo_excludes_sentinel_from_viewer_and_passes_executor_args`
  failed: its local fixture PowerShell invocation exceeded unchanged 30s while
  waiting for stdout reader closure; traceback shows Popen returncode 0. Retained
  fixture viewer record has key_present=false, executor record key_present=true
  and correct arguments. Those records do not turn the timeout green. No gateway
  call occurred: the test created local fixture modules. One unchanged complete
  second run after other test work subsided passed all 899 in 600.17s. The first
  timeout remains a real failed invocation; no third full retry was performed.
- First deployment dependency download was stopped after verified ownership of
  uv PID 40976 and prolonged download delay; native exit -1 is retained in
  `deploy-dependencies.*`. Only that task-owned process was stopped. Second network
  attempt used command-local official PyPI plus NO_PROXY; it completed three large
  packages but was still waiting for SciPy. Under coordinator cache-reuse guidance
  `msg_b8534eb3f69c`, verified the cached Poetry wheel
  `scipy-1.18.1-cp312-cp312-win_amd64.whl` (36,658,278 bytes) against poetry.lock:
  SHA256 `5e4d44984abc0020154ea81b247adeddcc3ac5527b975ff798bd1ba0adc513c2`.
  Only verified task-owned uv PID 5652 was stopped; second native exit -1 retained
  in `deploy-dependencies-direct.*`. The deterministic cache path then succeeded:
  `uv pip sync --offline --find-links <verified-Poetry-wheel-directory> --python
  <new-deployment-python> locked-requirements.txt`, native exit 0. Actual wheel
  install, imports, dependency versions and CLI are independently verified above.
  No third blind network retry, site-packages copy, shared environment mutation,
  added dependency or TLS weakening was used.
- Offline review preparation first ran from the nested exported source, causing
  Git's relative `ls-tree` scope to appear empty (native exit 2, `review-packet.*`).
  Retried once using the supported explicit `--repo` set to this worktree and the
  unchanged final SHA: exit 0. No `--preparation-control` or script edit was used.
  An independent TEMP-only config reader initially used the Windows GBK default
  and failed to decode UTF-8 (exit 1, `review-config-check.*`); specifying UTF-8
  fixed that reader (exit 0). C's committed scripts remained byte-identical.

## Prepared final-SHA FC-E packet and H1 handoff

Only offline preparation was requested and performed. Existing C scripts produced
`fc-e-packet/review-0929-release-v41flash-input.json` (748,088 content UTF-8 bytes,
tokens unknown), `review-0929-release-v41flash-input-check.json`, and
`review-0929-release-v41flash-coverage.json`. All bind the full final SHA, contain
no missing paths, use `preparation_control=false`, and record `submitted=false`.
The 40 dimensions are requirements (original 37 plus production logging,
six-stage drill and live entry); they are NOT model-verified coverage.

`fc-e-native/overlay.json`, `composed.yml`, `native-prepare.json`, `dump.exit` and
`dump.stderr.log` are the new native dsh packet. The invocation only used
`dsh --profile headless --patch <overlay> --dump-config` (native exit 0).
Reusing exactly the existing seven config assertions confirms full task bytes,
no startup dependency, requested disabled plugins, retry 0, finite 16384 output,
and the official configured route. No runner boot or model request occurred:
model_requests=0; returned_model, usage and cost remain null. Configured catalog
name DeepSeek-V41-Flash / deepseek-official/deepseek-flash is not an observed
provider-returned model. A future authorized actual invocation must use the
packet's independent DSH_HOME and preserve its original response for the existing
byte/line/SHA verifier; this report does not supply FC-E approval.

H1 locations, reread against `8c76af727cf8a669c0b22b65586c2a0a70577e72`:

- Source TODOs: `swarm/breaker.py:202`, `:592`, `:672`, unchanged and unsigned.
- Human worksheets in this candidate: `docs/FC_HUMAN_REVIEW_0928.md:32` (budget A),
  `:47` (budget B), `:67` (budget signature/conclusion slots), `:81` (matrix),
  `:169` (six conclusions/signature/authority). Their old 73e64cc line references
  remain historical; they cannot be signed as this final SHA without rebinding.
- Current preflight checklist: `docs/FC_RELEASE_PREFLIGHT_0929.md:208-223`.
  Budget A final source is `swarm/budget.py:179-203,230-251`; actual Worker
  reserve/request/call is `swarm/worker_loop.py:810-859`, with settlement and
  per-reservation cost at `:874-904`. Budget B is `swarm/budget.py:77-101,192-203,
  259-313`. Breaker review anchors remain `breaker.py:163-251,477-521,569-695`.
- More recent human material is OUTSIDE this candidate: immutable governance
  `40577cb841e8d89c08e1336d7254c4ca7bb3984e:docs/FC_HUMAN_REVIEW_0929.md:40,66`
  and its `artifacts/ai-evidence/fc-remediation-governance-0929-h1-quotes.md/json`.
  Read directly via `git show`; its source target is C552 and its pending slots
  are not final-SHA signatures. Its historical H3 unsigned text is superseded by
  the complete be4 frozen H3 document retained here. No governance tree was merged.

H1 needs the person's final-SHA A/B conclusions with premises, six breaker
conclusions, name/time/signature, and explicit authority if the original Owner is
to replace the three TODO comments. This Worker supplies source locations only.

## Release and live restrictions

H3 is the supplied David-frozen Schema 1.0.0 fact. H1 still lacks the budget A/B
and six breaker conclusions / signature; source TODOs remain at breaker.py
202, 592 and 672. Formal native dsh DeepSeek-V41-Flash review lacks authentication
and a final acceptable report. The user has not supplied the live target, budget,
route or single-task versus auto-recovery decision. No AI signature is substituted.

Rehearsal still permits recovery when token usage is known but cost is unknown
(`orchestration/rehearsal.py:306-310`, recovery call at 346); MaxCostUsd is not a
cumulative upstream hard billing cap. Domain behavior is unchanged. Unknown
remote effects are not retried; unknown holds are not released.

Mainline merge, tag, formal FC-E invocation, three live smokes, paid/provider calls,
real task/field acceptance, Desktop and TASKS updates: NOT_RUN by this Worker.
All executed behavior is local contract / mock; interface_live and task_live
remain NOT_RUN. Log source sequences / JSONL positions are not global request IDs
or audit counts. Best-effort logs can be missing after crashes or I/O failures,
and sequence values can repeat across restarts; logs do not drive remote decisions.

## Native command and evidence index

All entries below ran against the fixed final SHA. Times are UTC; raw logs preserve
the actual output. The source/environment section identifies dependency and import
origins. Mutation driver rows point onward to each native red/restored child log.

| Gate | Result | Native exit | UTC start / end | Raw evidence |
|---|---|---|---|---|
| focused-2 | 452 passed; 2 warnings | 0 | 2026-09-29T16:29:51.1703726Z / 2026-09-29T16:43:51.8042176Z | [focused-2.log](focused-2.log), [metadata](focused-2.meta.json) |
| full-2 | 899 passed; 2 warnings | 0 | 2026-09-29T16:44:14.4084865Z / 2026-09-29T16:54:16.6167497Z | [full-2.log](full-2.log), [metadata](full-2.meta.json) |
| strict | 89 files | 0 | 2026-09-29T16:16:42.0816278Z / 2026-09-29T16:20:01.9974041Z | [strict.log](strict.log), [metadata](strict.meta.json) |
| build | sdist and wheel | 0 | 2026-09-29T16:18:51.3060334Z / 2026-09-29T16:19:34.7895441Z | [build.log](build.log), [metadata](build.meta.json) |
| sdk | official SDK 1.14.0; schema_version 1.14.0; local | 0 | 2026-09-29T16:19:28.5725261Z / 2026-09-29T16:19:39.1060728Z | [sdk.log](sdk.log), [metadata](sdk.meta.json) |
| distribution | fresh installed 13 packages + Node | 0 | 2026-09-29T16:48:26.3132351Z / 2026-09-29T16:48:34.9940445Z | [distribution.log](distribution.log), [metadata](distribution.meta.json) |
| installed-fc | installed schema/logger/Worker/rehearsal/drill imports and real emit | 0 | 2026-09-29T16:48:26.7489437Z / 2026-09-29T16:48:36.9897018Z | [installed-fc.log](installed-fc.log), [metadata](installed-fc.meta.json) |
| installed-drill-cli | installed six-stage mock CLI | 0 | 2026-09-29T16:48:26.5190236Z / 2026-09-29T16:49:12.7742780Z | [installed-drill-cli.log](installed-drill-cli.log), [metadata](installed-drill-cli.meta.json) |
| installed-drill-inspection | 21 legal rows, no logger failures | 0 | 2026-09-29T16:49:42.8819629Z / 2026-09-29T16:49:44.5478701Z | [installed-drill-inspection.log](installed-drill-inspection.log), [metadata](installed-drill-inspection.meta.json) |
| independent-p0 | 47 passed | 0 | 2026-09-29T16:21:38.7302468Z / 2026-09-29T16:23:16.8148854Z | [independent-p0.log](independent-p0.log), [metadata](independent-p0.meta.json) |
| schema | original 12, expanded 24, controls 13 | 0 | 2026-09-29T16:19:26.7472111Z / 2026-09-29T16:19:34.8458835Z | [schema.log](schema.log), [metadata](schema.meta.json) |
| mutations | 12 red / 12 restored green | 0 | 2026-09-29T16:29:50.9445299Z / 2026-09-29T16:43:27.2115762Z | [mutations.log](mutations.log), [metadata](mutations.meta.json) |
| final-source | 375 exact files in each source; clean | 0 | 2026-09-29T16:55:41.9681521Z / 2026-09-29T16:55:43.1143784Z | [final-source.log](final-source.log), [metadata](final-source.meta.json) |
| review-packet-2 | 748088 bytes / 40 required dimensions / 0 model calls | 0 | 2026-09-29T16:56:22.9362614Z / 2026-09-29T16:56:29.3301531Z | [review-packet-2.log](review-packet-2.log), [metadata](review-packet-2.meta.json) |
| review-native-dump | config dump only | 0 | 2026-09-29T16:56:29.3422900Z / 2026-09-29T16:56:31.2609925Z | [review-native-dump.log](review-native-dump.log), [metadata](review-native-dump.meta.json) |
| review-config-check-2 | 7 configuration checks | 0 | 2026-09-29T16:57:16.7502587Z / 2026-09-29T16:57:17.4877092Z | [review-config-check-2.log](review-config-check-2.log), [metadata](review-config-check-2.meta.json) |

Exact six-gate commands (PowerShell notation; no abbreviated argv):

focused-2:

```powershell
Set-Location -LiteralPath 'C:\Users\DW\orca\workspaces\Morphogenesis\morph-fc-production-integration-0929\.runtime\candidate-src'
& 'C:\Users\DW\orca\workspaces\Morphogenesis\morph-fc-production-integration-0929\.venv\Scripts\python.exe' '-B' '-u' '-m' 'pytest' '-q' 'tests/orchestration' 'tests/swarm/test_unknown_effect_recovery.py' 'tests/swarm/test_reservation_cost_state.py' 'tests/swarm/test_probe_lifecycle_recovery.py' 'tests/swarm/test_rejection_runtime_boundaries.py' 'tests/swarm/test_failure_chain_boundaries.py' 'tests/swarm/test_failure_chain_runtime.py' 'tests/swarm/test_breaker.py' 'tests/swarm/test_fault_observations.py' 'tests/swarm/test_budget.py' 'tests/swarm/test_budget_evomap.py' 'tests/swarm/test_worker_runtime.py' 'tests/swarm/test_ledger.py' 'tests/swarm/test_lease.py' 'tests/swarm/test_fc_logging.py' 'tests/swarm/test_fault_drill.py' 'tests/t2/test_rehearsal.py' '--basetemp' 'C:\Users\DW\AppData\Local\Temp\morph-fc-production-integration-ctx-af144abe21c7\state\focused-2' '-p' 'no:cacheprovider'
```

full-2:

```powershell
Set-Location -LiteralPath 'C:\Users\DW\orca\workspaces\Morphogenesis\morph-fc-production-integration-0929\.runtime\candidate-src'
& 'C:\Users\DW\orca\workspaces\Morphogenesis\morph-fc-production-integration-0929\.venv\Scripts\python.exe' '-B' '-u' '-m' 'pytest' '-q' '--basetemp' 'C:\Users\DW\AppData\Local\Temp\morph-fc-production-integration-ctx-af144abe21c7\state\full-2' '-p' 'no:cacheprovider'
```

strict:

```powershell
Set-Location -LiteralPath 'C:\Users\DW\orca\workspaces\Morphogenesis\morph-fc-production-integration-0929\.runtime\candidate-src'
& 'C:\Users\DW\orca\workspaces\Morphogenesis\morph-fc-production-integration-0929\.venv\Scripts\python.exe' '-B' 'tools/typecheck.py'
```

build:

```powershell
Set-Location -LiteralPath 'C:\Users\DW\orca\workspaces\Morphogenesis\morph-fc-production-integration-0929\.runtime\candidate-src'
& 'C:\Users\DW\orca\workspaces\Morphogenesis\morph-fc-production-integration-0929\.venv\Scripts\python.exe' '-B' '-u' '-m' 'build' '--installer' 'uv' '--outdir' 'C:\Users\DW\AppData\Local\Temp\morph-fc-production-integration-ctx-af144abe21c7\dist'
```

sdk:

```powershell
Set-Location -LiteralPath 'C:\Users\DW\orca\workspaces\Morphogenesis\morph-fc-production-integration-0929\.runtime\candidate-src'
& 'node' 'tools/check_sdk.cjs'
```

distribution:

```powershell
Set-Location -LiteralPath 'C:\Users\DW\AppData\Local\Temp\morph-fc-production-integration-ctx-af144abe21c7\deployment'
& 'C:\Users\DW\AppData\Local\Temp\morph-fc-production-integration-ctx-af144abe21c7\deployment\.venv\Scripts\python.exe' '-I' 'C:\Users\DW\orca\workspaces\Morphogenesis\morph-fc-production-integration-0929\.runtime\candidate-src\tools\check_distribution.py' '--site-dir' 'C:\Users\DW\AppData\Local\Temp\morph-fc-production-integration-ctx-af144abe21c7\deployment\.venv\Lib\site-packages' '--check-node'
```

## Final identity and closeout

`final-remote.log` freshly confirms remote candidate
`8c76af727cf8a669c0b22b65586c2a0a70577e72` and release target
`be4fb7a685e951c9e42d8dc0c7eeb900cb5518f1`. `final-target-status.log` is empty;
`final-target-sha.log` confirms be4. `final-diff-check` exits 0 relative to C552.
The candidate remains clean, with the two parents listed at the top, and all
archived/mutation files and H3 bytes restored. No report, packet, dependency,
local state or post-test commit entered this candidate.

The first-generation root is still
`2957b408ce922369a595a8acd43a882eb85897d3`, with its preexisting
` M docs/SWARM_SOL_PLAN.md` WIP retained (`final-root-status.log`). It is not claimed
clean. Neither target/root tree, tags, user/peer ports nor their processes were
modified. `final-processes.json` retains the closing process-path inspection;
no task test/build/model child remained to terminate. The two earlier explicitly
owned downloader stops are recorded above. Mere peer command-line references to
this report were not treated as ownership.

This completes the authorized isolated merge and local independent acceptance
phase. Release remains BLOCKED by H1 / acceptable formal FC-E and the separate
live target-route-budget/auto decision. Mainline merge, tag, three live smokes,
paid calls, field/browser acceptance remain NOT_RUN; no pass is prewritten.
The coordinator/material Owner can register this TEMP report and raw evidence
without advancing the immutable code candidate.
