# FC five-remediation integration: candidate gate evidence

Status: SIX REQUIRED LOCAL GATES PASSED on `c552250c0d07f5f70f09eb0a5ab3c322195e34ec`. Final verification completed at 2026-09-29T11:14:33Z. This file is ignored local evidence; it is not a commit, human approval, release, or freeze. Governance G registers the final results on its separate branch. No further tracked changes were made to this code candidate.

## Immutable candidate and merge lineage

- Worktree / branch: `C:/Users/DW/orca/workspaces/Morphogenesis/morph-fc-candidate-0929` / `morph-fc-candidate-0929`.
- Common base: `3a34ecafe5f48b1a5a7c94c9e063797427817cab`.
- A start / final: `4d1098ed151d6a9859e088f13ea292baeef1acf2` (production source `f2be38864c87632ca8a41d0471b4b4bfcfef1d74`).
- B final: `2c6a33ae1950fd6458543618d1c4044dcdd2596f` (production source `751864580d7043e4187d896bf7036ffc756b5b04`).
- First ordinary no-ff merge: `5cf2612c04a34dfb17af12af817ebee8c08432dc`, parents A final and B final in that order.
- C final: `e6ac45ffefc171a7215f8db19bc4a28af24ec4fc` (production source `36aa0e7ec7b355ad0c8e2eacfc5489df9d577ad4`).
- Final ordinary no-ff merge / code candidate / all six gates: **`c552250c0d07f5f70f09eb0a5ab3c322195e34ec`**, parents first merge and C final in that order.
- Both merge commits contain `Swarm-Agent: codex`. No conflict resolution or integration glue was needed.
- Origin: `https://github.com/songconmaisaix31-design/Morphogenesis`; ordinary push to `refs/heads/morph-fc-candidate-0929` completed, then `git ls-remote` matched the candidate. Main, tags, public history and protected governance/lock files were not changed.
- Base ancestry and full changed-path intersections were checked: A=9, B=7, C=7 paths, all pairwise intersections empty. The candidate includes B's breaker and C's dependent guard together. A/B/C final deltas from their source SHAs are only their evidence/plan material.
- `merge-lineage.log` retains the first read-only GitHub TLS failure (`SSL_ERROR_SYSCALL`, exit 1), the successful subsequent remote read, both actual merges and the push. No TLS policy or global Git setting was changed.

## Exact source and isolated environment

All paths below are relative to this ignored `.runtime/` unless specified. `gate-env.ps1` records the process-local environment. The tested source is `candidate-src`; all state, caches, wheel output and installed-wheel target are siblings, outside that source directory.

```text
git -c core.autocrlf=false archive --format=zip --output=.runtime/candidate.zip c552250c0d07f5f70f09eb0a5ab3c322195e34ec
C:/Users/DW/orca/workspaces/Morphogenesis/morph-fc-integration-0927/.venv/Scripts/python.exe -m zipfile -e .runtime/candidate.zip .runtime/candidate-src
```

The existing read-only interpreter is Python 3.12.13. Before starting Python, `.runtime/test-state` was created and process `TEMP` and `TMP` set to that absolute directory. `PYTHONPATH` points to the absolute `candidate-src`; `PYTHONDONTWRITEBYTECODE=1`; OPENBLAS/OMP/MKL thread counts are each 1. Mypy/Hypothesis/uv caches are sibling directories. No production safety guard was changed or bypassed.

`source-preflight.log`: 346 archived files byte-equal to the export, all 23 changed paths byte-equal to candidate Git blobs; eight production module imports (`worker_loop`, `task_ledger`, `budget`, `breaker`, `fault_observations`, `failure_chain`, two provider adapters) resolved within this export and byte-equal to Git. `tempfile.gettempdir()` matched the isolated state parent. Exit 0.

`temp-preflight.log`: `python -m pytest -q tests/integration/test_gateway_audit.py --basetemp=../test-state/preflight -p no:cacheprovider`, 7 passed in 2.35s, exit 0. This preflight is separate from and does not replace the full gate.

Existing SDK dependency reuse: before creating junctions, destinations were absent and ignored; target `morph-fc-integration-0927/node_modules` SDK version 1.14.0 matched candidate `package.json`. `candidate-src/node_modules` supports source SDK checks; sibling `.runtime/node_modules` supports the installed wheel's Node import resolution. Both are read-only reuse, with no npm installation. Node v24.16.0; uv 0.11.26. See `export-preflight.log`.

Build-only backend reuse: existing `C:/Users/DW/AppData/Local/uv/cache/archive-v0/8IuHKNOGrMpTxzu6/Lib/site-packages` was appended to PYTHONPATH only in the build subprocess. Actual imported Poetry backend version 2.5.0 satisfies `poetry-core>=2.0,<3.0` from candidate pyproject (`backend-preflight.log`, exit 0). Test/type/distribution processes did not receive that extra path. No dependency or lock change, and no new third-party install.

## Six required gates on the same candidate

Working directory for every gate: `.runtime/candidate-src`. `python` below means the absolute existing interpreter above, not PATH Python. Logs retain exact command, candidate SHA, output, actual native exit code and start/end times. No prior Owner or historical full result is substituted.

| Gate | Actual result | Raw log |
|---|---|---|
| Focused | PASS, 408 passed, 2 warnings / 278.45s, exit 0 | `focused.log` |
| Full pytest | PASS, 862 passed, 2 warnings / 589.58s, exit 0 | `full.log` |
| Strict via project tool | PASS, 87 source files, no issues, exit 0 | `strict.log` |
| Build sdist and wheel | PASS, exit 0 | `build.log` |
| Official SDK | PASS, exit 0 | `sdk.log` |
| Fresh wheel distribution | PASS, install exit 0, checker exit 0 | `distribution.log` |

Focused includes all five new regression areas and the existing provider, two failure_chain, breaker, fault, budget, Worker, ledger and lease coverage:

```text
python -u -m pytest -q tests/orchestration tests/swarm/test_unknown_effect_recovery.py tests/swarm/test_reservation_cost_state.py tests/swarm/test_probe_lifecycle_recovery.py tests/swarm/test_rejection_runtime_boundaries.py tests/swarm/test_failure_chain_boundaries.py tests/swarm/test_failure_chain_runtime.py tests/swarm/test_breaker.py tests/swarm/test_fault_observations.py tests/swarm/test_budget.py tests/swarm/test_budget_evomap.py tests/swarm/test_worker_runtime.py tests/swarm/test_ledger.py tests/swarm/test_lease.py --basetemp=../test-state/focused -p no:cacheprovider
python -u -m pytest -q --basetemp=../test-state/full -p no:cacheprovider
python tools/typecheck.py
python -m build --no-isolation --outdir ../dist
node tools/check_sdk.cjs
uv pip install --python C:/Users/DW/orca/workspaces/Morphogenesis/morph-fc-integration-0927/.venv/Scripts/python.exe --offline --no-deps --target ../wheel-site ../dist/morphogenesis-0.1.0-py3-none-any.whl
python -I tools/check_distribution.py --site-dir ../wheel-site --check-node
```

Build generated new `dist/morphogenesis-0.1.0.tar.gz` and `dist/morphogenesis-0.1.0-py3-none-any.whl` from this candidate; dist was absent before running. Distribution installed only this wheel into previously absent `wheel-site` (user-authorized own-wheel install, offline/no-deps). Checker confirmed all 13 packages import from the installed target, resources exist, installed verifier passed, and Node dependency check passed. SDK output: `scope=contract_local`, schema 1.14.0, schema valid, asset ID verified, tampering rejected, `published=false`. These three gate outputs contain no warnings.

Focused and full each report the same two existing intentional invalid-model-copy cases in `tests/swarm/test_budget.py::test_model_copy_cannot_bypass_preflight_validation[nan]` and `[1]`: Pydantic warns that `input_tokens` expects int but receives float nan / string '1'. The warnings were not filtered or suppressed. Both runs have no skips or deselections. Full ran every collected test with no path subset or selection filter. Strict/build/SDK/distribution outputs contain no warnings. There were no failed integration gate rounds on this candidate.

## Retained earlier failures and independent acceptance boundary

- B original full remains **47 failed / 656 passed / 2 warnings / 7 errors / exit 1 / 578.25s** at `C:/Users/DW/orca/workspaces/Morphogenesis/morph-fc-breaker-fix-0929/.runtime/full.log`. B ran custom basetemp outside its then-current OS TEMP. The coordinator relayed D's independent review of all 54 tracebacks: all hit OS TEMP guards, but those guards could mask deeper failures. This candidate's full rerun now passed 862 tests under the corrected isolated TEMP/TMP; the earlier failed gate is never relabeled green.
- B `build-final` and C `build.log` each retain exit 1 for the shared interpreter's missing Poetry backend. This candidate's process-local existing-backend build is a new execution, not a rewrite of their failures.
- All earlier Owner red/green/mutation evidence remains in the merged three `artifacts/ai-evidence/fc-remediation-*-0929-report.md` reports, with original local log locations. A's earlier fix-round failure and its handoff fixture correction, B's composition failures, and C's fixture setup failures are retained there.
- Independent D `ctx_dec883ee43f2` and governance G `ctx_a3637ec3a0c7` received the exact pushed candidate immediately. Their results are separate evidence. D's focused/mutations never replace these six integration gates; I performs no mutation on candidate-src.
- The coordinator relayed D's existing-test AST check (464 baseline test functions, 1558 asserts, all decorators preserved; only A handoff arrange changed). I made no test/source edits, exclusions, skip marks, or relaxed assertions.

## Remaining limitations / NOT_RUN

These are local contract gates, with explicit mock/fixture or subprocess test provenance. They are not interface_live or task_live acceptance. No paid live requests, unknown-effect retry, fee confirmation, human signature or provider bill claim occurred.

H1/H3 human review/signatures remain open; I cannot sign them. Formal deepseek FC-E is G's separate track, not this integration's result. T6 three consecutive smoke runs, formal entry and rehearsal remain NOT_RUN under the original human lock and its prerequisites; no unit-test result substitutes for them. Main merge, tag, freeze, release, and production deployment remain NOT_RUN. No new reconciliation API, unknown hold release, migration exercise, or mixed-version deployment is added by integration.

## Final post-gate verification

`final-verification.log`, actual command exit 0:

- `git rev-parse HEAD` remains `c552250c0d07f5f70f09eb0a5ab3c322195e34ec`.
- `git status --porcelain` returned zero lines; `git diff --check 3a34ecafe5f48b1a5a7c94c9e063797427817cab HEAD` exited 0.
- `git ls-remote --heads origin refs/heads/morph-fc-candidate-0929` exited 0 and returned that exact SHA.
- All 346 exported files still match `candidate.zip` byte for byte after all six gates. All 23 A/B/C changed paths in both export and candidate Git blobs also match the exact respective Owner final blobs. There are no leftover mutation bytes; integration performed no mutation.
- Report and all six raw gate logs were verified ignored. No report/governance commit was added after the tested candidate; no G material was merged into it.

The six results above are this integration Worker's executions. Independent D acceptance, G's formal heterogeneous review and human sign-offs retain their own authority and status.
