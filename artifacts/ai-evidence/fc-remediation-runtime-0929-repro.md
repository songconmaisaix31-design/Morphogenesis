# Track A original failures (2026-09-29)

Base: `3a34ecafe5f48b1a5a7c94c9e063797427817cab`.
Production files used for this reproduction are the unchanged base, exported with
`git -c core.autocrlf=false archive --format=zip --output=.runtime/baseline.zip HEAD`.
The two new regression files are overlaid into `.runtime/candidate-src/tests/swarm`.
No original tests were edited. Only the executor boundary uses local fixtures;
the restart cases spawn real Python processes running `Worker.run` with persistent
SQLite state and the actual router/lease manager. No live subprocess is mocked.

Python (read-only reuse):
`C:/Users/DW/orca/workspaces/Morphogenesis/morph-fc-integration-0927/.venv/Scripts/python.exe`
(3.12.13). `PYTHONPATH` is the absolute `.runtime/candidate-src`, verified by
`swarm.worker_loop.__file__`. SDK dependency is an ignored `node_modules` junction
under the export to the existing integration installation (`@evomap/gep-sdk` 1.14.0,
matching package.json); the destination was absent before creation. No installs.

Command from `.runtime/candidate-src`:

```text
<python> -m pytest -q tests/swarm/test_unknown_effect_recovery.py tests/swarm/test_reservation_cost_state.py --basetemp=../test-state/original-scoped -p no:cacheprovider
```

Actual result: **5 failed, 2 passed / exit 1 / 25.48s**.
Raw output: `.runtime/original-scoped-red.log` (ignored, retained locally).

- Same Worker identity in a new process: `recovered["calls"] == 0` fails with
  `assert 1 == 0`. The original request has two known fixture tokens, a settled
  estimated cost, zero remaining reservation hold and available budget.
- Different Worker identity in a new process: same `assert 1 == 0` failure;
  this is an actual new executor call, not only a candidate-loop assertion.
- Real `LeaseManager.handoff` during the request: successor `Worker.run` calls
  its executor once despite the returned unknown effect and settled cost.
- Known usage, no prices: both `allow_unknown_cost=False` and `True` fail with
  `fact.cost_state == "unknown"` versus actual `settled`; SQLite retains a .2 hold,
  `cost=unknown`, `estimate_usd=NULL`, `usage_metering=verified`, `tokens=2`.
- Controls pass: confirmed rejection switches to a successful fixture and
  completed tasks stay completed; an earlier unknown hold does not change a
  current genuinely settled reservation into unknown.

Earlier attempts are retained, not superseded as green: `.runtime/original-setup-error.log`
has six setup errors / exit 1 because the basetemp parent did not yet exist.
After creating that parent, `.runtime/original-red.log` has 5 failed, 1 passed /
exit 1 / 34.74s, including a new test's success control incorrectly admitting
the fixture's other task. The final reproduction narrows only these new recovery
tests through the existing `Locality.dependency_of=("fixture-0",)` filter, and adds
the real handoff case. The two production bugs remain red as listed above.

This is Owner `contract_local` evidence only. H1/H3, formal FC-E,
`interface_live` and `task_live` are not closed by these tests.

## Supplemental unknown-effect candidate counterexample

The final additional test also runs against the three production files restored
byte-for-byte from `baseline.zip` (all other production files were already base).
Command: `<python> -m pytest -q tests/swarm/test_unknown_effect_recovery.py::test_unknown_effect_candidate_is_not_published_or_retried --basetemp=../test-state/original-candidate -p no:cacheprovider`.
Result: **1 failed / exit 1 / 7.68s**, retained in
`.runtime/original-candidate-red.log`: `assert 'completed' == 'sleeping'`.
This exposes the original candidate-success branch taking precedence over an
explicit `unknown_effect` classification. The fixed Worker gives the unknown
effect precedence and leaves the candidate unpublished and task unretryable.
