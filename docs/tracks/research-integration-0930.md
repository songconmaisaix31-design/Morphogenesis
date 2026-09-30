# Research integration I — 2026-09-30

## Frozen integration and evidence classes

Branch: `morph-research-integration-0930`. Current code candidate: `bc4d017924d8d08454b97e6d0c1b5a84d4064fd6`. Exact A/B/C and governance commits were merged with their complete histories; no cherry-pick, force push, main/tag/Hub modification, or domain-source edit by I. Ownership was checked against common plan `6ba12b24781318383454d2e7fb0b132e897b8a8d`.

This is a checkpoint, not completed acceptance. Engineering/contract evidence, interface_live and task_live remain separate. Persistent local evidence root is `C:/Users/DW/orca/workspaces/Morphogenesis/morph-research-integration-0930-state`; raw native output, sandbox archives and logs remain outside Git. No service secret is included in this report.

## Engineering checks

I installed the final Poetry lock into a separate CPython 3.13 environment under that sibling root. Python checks use one local verification window and process-local BLAS thread limits of one. Node dependencies use the original lock and `npm ci --ignore-scripts`.

| Candidate / command | Actual result | Local evidence |
|---|---|---|
| `85a921c49addcdd46c2cb4a307c3515356b3e186`, applicable four-module pytest | 140 passed, 73.18s | `focused-85a921.log` |
| same candidate, `python -m pytest -q --tb=short` | 1065 passed, 75 warnings, 763.09s | `full-85a921-first.log` |
| same candidate, first exact-head CI `36728997575` | Ubuntu 1 failed / 1062 passed / 2 skipped; Windows cancelled | `ci-36728997575-first-failure.log` |
| `ea2072db5c9d21ed40c08fd729e99cf66ff2806f`, exact-head CI `36731765767` | Ubuntu strict failed: 11 platform attribute errors in Windows Job binding, 116 files checked | `ci-36731765767-first-failure.log` |
| current code candidate, `python -m pytest tests/native_agents -q --tb=short` | 75 passed, 9.84s | `native-final.log` |
| current, `python tools/typecheck.py` | passed, 116 files | `strict-final.log` |
| current, `python -m mypy --strict --platform linux orchestration/native_agents` | passed, 10 files | `strict-native-linux-final.log` |
| current, `python -m build` | actual sdist and wheel built | `build-bc4.log`, `dist-bc4/` |
| current wheel, `python -I tools/check_distribution.py --site-dir … --check-node` | 13 packages from installed wheel, resources / verifier / Node passed | `distribution-bc4.log` |
| current wheel, isolated new research/native/experiment imports | four modules imported from installed wheel target | `wheel-research-imports-bc4.log` |
| exact LF current archive, B `bridge_probe.py --c-source` exact C archive | passed; mock scientific evidence remains quarantined, no adoption | `bridge-bc4.log` |
| exact LF current archive, B `migration_probe.py --baseline-source` exact ef77 archive | passed; original candidate/address/report/approval/consumption/adoption unchanged | `migration-bc4.log` |
| original missing-effect harness, only source-root and observed SHA updated | original assertion passed: one backend call, missing effect still unconfirmed | `missing-effect-bc4.py`, `missing-effect-bc4.log` |
| exact-head CI `36733427101` | Ubuntu original pytest/strict/build/SDK/wheel/distribution steps SUCCESS; Windows pending at checkpoint | GitHub run and exact headSha recorded separately |

Original failures remain failures. A Owner repaired the portable fixture in `f37ada292f61a28899666a84a8c988da5a4c0a40` and platform binding in `2f4b51587e53ecd31dfaf070957f638deed77d4a`; I merged those exact commits and ran the original applicable gates. No original assertions or thresholds were removed or relaxed.

## Official provenance and permissions

ORCA shared protocol reference is fixed at `85f8d6b5f507df795cd3cef1cdea08124cf801ee`, MIT. `.reference` is a downloaded file collection, not a Git clone. The official LICENSE and unchanged TS match the exact LF Git archive byte-for-byte. Eleven actual Node oracle inputs passed; the original MODULE_TYPELESS_PACKAGE_JSON warning is retained in local stderr. Referenced neighboring shared module imports were read; this does not claim a complete upstream Electron/Vitest build.

OpenSandbox official source is fixed at release commit `b1a29cf93a823a95913f7943010febb3f29de05c`; both installed official SDKs are 1.1.0, with disabled automatic retries and telemetry. C calls the official SDK APIs. No replacement container runtime was introduced.

Official runtime probes show Codex CLI 0.159.0 and Claude Code 2.1.238, matching versions and existing authenticated accounts. These probes are prerequisites, not research sessions. The native child environment contains no Orca authority keys. Codex's original read-only permission profile actually rejected a Node filesystem write with EPERM and left the protected sentinel unchanged; the original launch/syntax failures before that valid filesystem probe remain in local evidence. Claude's planned operator launch uses official dontAsk plus the exact eleven allowed research MCP tools, strict MCP configuration and no built-in tools. No HOME copy, auth replacement or permission bypass is used.

## interface_live first I run — FAILED

New run `interface-i-0930-bc4-01` used the protected persistent `interface-live/` archive and the owned `morph-research-c-0930-server` service on 127.0.0.1:8097. Create, get-info, attached connect, attached-destroy rejection, renewal and binary roundtrip succeeded. The first cgroup inspection command failed at the official command endpoint with `INVALID_REQUEST_BODY`: `RunCommandRequest.Command` failed its required validation, request ID `cf19659930344f89b642c9ff2622449b`.

The authoritative original result is unchanged: execution/cleanup/remote effect unknown, science not_evaluated, usage/cost null. The created sandbox ID occurs in raw `interface.json`: `d96ce63e-c418-40e0-82b5-b483b356af6e`; it was not returned in the failed executor result. Subsequent independent read-only GET returned 404 at 15:09:54Z, and no matching morph-run container was observed. This is subsequent cleanup evidence, not a rewrite of the failed result.

Evidence: `interface-i-0930-bc4-01.log`, `interface-live/interface-i-0930-bc4-01/{interface.json,result.json,summary.json}`, and `interface-i-0930-bc4-01-subsequent-cleanup.json`. C domain Handoff was sent to coordinator as `msg_f312b21928c0`; adapter commands.run receives argv lists at backend lines 87/97, for original C Owner diagnosis. This run is never replayed. No dependent native research session has started.

Original C `interface-c-0930-01` remains FAILED and is not replayed; its directory-mode failure, unknown result and later separate cleanup evidence remain in the original C/governance record.

## Remaining acceptance

task_live, actual author interruption / same-session resume / stale renew and legitimate stale submit rejection, independent clean reproduction, local inheritance validation and actual adoption are NOT_RUN. New code from original C must pass applicable gates before a new unique live run; an unknown experiment is never replayed. At most three original native research identities remain authorized, with each identity's cumulative wall and observed tool limits preserved.

Actual research adoption must use existing ConsumptionExecution and AdoptionReceipt plus canonical claim/attempt/result/target-bytes lineage. Coordinator clarified `msg_ad610e51738d` that the original user task did not require the unrelated `metabolism.models.UseRecord` class; do not introduce a second adoption store or manufacture that record. Search, injection, application and actual adoption remain distinct.

Linux/WSL actual native execution, additional Agent/SDK vendors, notebook/Jupyter/CodeInterpreter, persistent volumes and GPU have no live evidence and remain NOT_RUN. Two-platform final CI success and the full actual native scientific chain are still required before declaring completion.
