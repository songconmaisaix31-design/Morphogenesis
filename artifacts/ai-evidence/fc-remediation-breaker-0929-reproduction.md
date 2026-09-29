# B original implementation reproduction

Base: `3a34ecafe5f48b1a5a7c94c9e063797427817cab`.
Worktree: `C:/Users/DW/orca/workspaces/Morphogenesis/morph-fc-breaker-fix-0929`.
Production code was unchanged for this reproduction. Only the new regression
file was overlaid on a `git -c core.autocrlf=false archive --format=zip` export
in ignored `.runtime/candidate-src`; state is its sibling `.runtime/test-state`.
Read-only Python: `C:/Users/DW/orca/workspaces/Morphogenesis/morph-fc-integration-0927/.venv/Scripts/python.exe`.
Official Node dependency reuse: ignored candidate-src/node_modules junction to
the same integration worktree; original link path absent, SDK 1.14.0 matches
package.json. No dependencies installed or locks changed.

Command from exported source, with PYTHONPATH set to that exact directory:

```text
python.exe -m pytest -q tests/swarm/test_probe_lifecycle_recovery.py --basetemp=../test-state/baseline-2
```

Result: **6 failed, exit 1, 36.49s**. Full original output is retained locally
at `.runtime/baseline-red-2.log`.

- TTL guard same-owner and different-owner cases: expected executor call 1,
  actual 0. Real Worker never reaches the probe executor after expired owner.
- Concurrent expired-probe Workers: expected call counts `[0, 1]`, actual
  `[0, 0]`; neither can reclaim through the production route.
- History replay same Worker / other Worker / restarted Worker: a successful
  real Worker probe reaches normal, then real observe returns suspended solely
  from the two retained pre-recovery failures.

Earlier setup run: **6 errors, exit 1**, because the sibling test-state parent
directory did not yet exist. `.runtime/baseline-red.log` is retained. Creating
that missing parent fixed test setup; it did not change source or assertions.

Root causes: base `swarm/failure_chain.py:143` never tries reclaim when
probing_recovery is ineligible (C-owner handoff sent); base
`swarm/breaker.py:651` only resets the local TTL cache and stores no persistent
recovery boundary. No production fix was included in this stage. These are
contract_local executor-boundary tests, not interface_live or task_live proof.
