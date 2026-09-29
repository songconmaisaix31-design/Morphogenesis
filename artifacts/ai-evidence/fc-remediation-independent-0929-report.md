# D independent FC remediation acceptance, 2026-09-29

Status: static review complete; common candidate and final behavioral gates pending.
No production, Owner test, Schema, plan, TASKS, AGENTS or lock file is edited by D.

## Scope and source authority

Base `3a34ecafe5f48b1a5a7c94c9e063797427817cab`. Reviewed AGENTS, QWEN,
docs/source/README_包内说明.md, FC_ACCEPTANCE, FC_REMEDIATION and FC_CLOSEOUT.
The current dispatched five-fix task overrides old closeout's prohibition on Owner
repairs; D remains acceptance-only. D report branch is
`morph-fc-independent-final-0929`, initially at A `4d1098ed151d6a9859e088f13ea292baeef1acf2`.
Report commits do not redefine the accepted code SHA.

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

Planned mutations independently remove unconfirmed execution persistence, expired
probe routing, recovery-history filtering/equal-time boundary, 5xx priority and
current-reservation cost selection, plus original suspended-transition semantics.
Only ignored exact-source copies may change; original bytes must restore in finally,
then selected tests must return green.

DashScope production executor is **NOT_IMPLEMENTED**: code search finds only the
pure adapter; `swarm/evomap_executor.py:139` calls `EvoMapAdapter.interpret`.
Both real adapters can be exercised, while full HTTP/executor/Worker evidence is
EvoMap only. Coordinator confirmed this distinction; D does not fabricate a
DashScope production path. Independent Codex review is not formal DeepSeek FC-E.

## Open / NOT_RUN

Common candidate focused/mutations and I six-gate evidence: pending.
H1/H3 human approvals, formal FC-E, entry/rehearsal remain OPEN.
Paid live, production merge/tag/freeze/publishing are NOT_RUN.
Local mock evidence never establishes interface_live or task_live.
