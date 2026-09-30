# Research integration I — 2026-10-01

## Current result: full acceptance not passed

Branch `morph-research-integration-0930`; final engineering code candidate **`bde3412d2257fd1581ce1d7f88b254fb0c13a269`**, pushed and remote exact/clean verified before gates. Engineering original gates passed locally and on both CI platforms. **Original complete research acceptance remains AUTH_BLOCKED**, with inheritance NOT_RUN and no actual adoption. Subsequent evidence revisions merge documentation only; their full SHA is recorded in the final CLI handoff, separately from this code candidate. Actual interrupted/resumed author turns ran at dec5798 and local completion at `363cac52f515f5e810de2e3a65fa83bc8c7b859e`; no new live was run on bde.

Complete histories include original A/B/C, A portable/platform fixes and final API-error accounting repair `3c4bc28e19abff7863007a2452b331762d10802e`, C command-wire repair `b4b403cd098df5cf2194e32377f7bd9f18a54ade`, and B bounded validation/known-result continuation `970fc530539c85d25b01096bf5001b5f4262554c`. Final A documentation `b2199c2fcc03a41389f69c3a8ac20e69ec7eb87c` changes only its track report. I changed only integration observers/checkers and this report. No domain source, original assertions, run limits, main/tag/Hub or root WIP was changed by I.

Final governance `e7d235a90f998fbb2015bc57d867592ec6988c96` was exact remote-verified and merged with full history after all frozen code gates settled. `git diff bde3412… HEAD` contains only authorized documentation; A3c4 native source/tests, B970 research/assets source/tests and Cbb2 experiment source/tests remain mechanically identical to their exact Owner commits. Final evidence publication does not rerun CI or relabel the failed original case.

Persistent evidence root, `S`: `C:/Users/DW/orca/workspaces/Morphogenesis/morph-research-integration-0930-state`. Protected case state is `S/research-host-7d04`, outside model workspace `S/research-project-7d04`. Actual raw/native/SQLite/scientific archives remain outside Git; no secret is included here.

| Exact candidate / gate | Actual result | Evidence under S |
|---|---|---|
| bc4, CI `36733427101` | Both platforms passed: Ubuntu 1063 passed / 2 skipped; Windows 1065 passed; strict/build/SDK/wheel passed | `ci-bc4-all.log`, `ci-bc4-final.json` |
| `7d04d9c4759a14c91dd75aff2aa9162a84b4c397`, local applicable pytest | 150 passed, 47.44s; strict116/build/SDK/wheel passed | original 7d04 logs |
| same SHA, CI `36736123569` | Both platforms passed: Ubuntu 1073 passed / 2 skipped; Windows 1075 passed; all original remaining gates passed | `ci-7d04-all.log`, `ci-7d04-final.json` |
| `dec579889af7c3853c9a7f76ba1fe5d835299716`, CI `36738222386` | Both platforms passed: Ubuntu 1073 passed / 2 skipped; Windows 1075 passed; strict/build/SDK/wheel passed | `ci-dec5798-all.log`, `ci-dec5798-final.json` |
| 363cac5, `python -m pytest tests/native_agents tests/research tests/local_assets tests/experiments -q --tb=short` | 165 passed, 55.40s | `focused-continuation.log/.exit` |
| same SHA, `python tools/typecheck.py` / `python -m build` | strict116 passed; sdist/wheel built | `strict-continuation.log`, `build-continuation.log`, `dist-363cac5/` |
| same wheel, `python -I tools/check_distribution.py --site-dir … --check-node` | First target `S/wheel-363cac5` lacked parent Node `ajv` dependency; bounded diagnosis confirmed ERR_MODULE_NOT_FOUND. Same wheel at `S/merged-7d04/tools/.wheel-site-363cac5` with unchanged original-lock dependencies passed 13 packages/resources/verifier/Node | Both targets retained; first terminal error retained |
| same SHA, `npm run check:sdk` | schema1.14 valid, address verified, tampering rejected, not published | actual command output |
| same exact LF archive, B bridge/migration/original missing-effect probes | Mock stays quarantined; actual ef77 legacy asset/approval/consumption/adoption unchanged; one missing-effect call remains unconfirmed | `bridge-363cac5`, `migration-363cac5`, `missing-effect-363cac5` logs and exits |
| same SHA, CI `36743307157` | Ubuntu 1087 passed /3 skipped /75 warnings,397.95s, all remaining gates success. Windows first red: existing FC concurrent logging test failed SQLite database locked; 1 failed /1089 passed /75 warnings,2094.27s. Original timeout0.05 and assertions untouched; FC logger/test diff vs ef77 is0 | `ci-363cac5-final.json`, `ci-363cac5-all-final.log`, `ci-363cac5-first-windows-failure.log` |
| final bde, original `python -m pytest -q --tb=short` | 1104 passed /75 warnings,1708.98s, exit0; not rerun | `full-final-A3c4-first.log/.exit` |
| final bde, `python tools/typecheck.py` / `python -m mypy --strict --platform linux orchestration/native_agents` | 116 /10 files passed | `strict-bde3412`, `strict-native-linux-bde3412` logs/exits |
| final bde, `python -m build`, actual wheel install then `python -I tools/check_distribution.py --site-dir … --check-node` | sdist/wheel built; 13 packages from wheel, resources/verifier/Node passed. Four research/native/experiment modules and packaged ORCA MIT license verified from installed target | `build-bde3412.log`, `dist-bde3412/`, `wheel-install-bde3412.log`, `distribution-bde3412.log`, `wheel-research-imports-bde3412.log` |
| final exact bde archive, original SDK/bridge/migration/missing-effect gates | SDK1.14 valid/tampering rejected/not published; mock quarantine preserved; actual ef77 assets/report/approval/consumption/adoption unchanged; one absent-effect call remains unconfirmed. All exit0 | `sdk-bde3412`, `bridge-bde3412`, `migration-bde3412`, `missing-effect-bde3412` logs/exits |
| final bde, archived actual Claude API-error normalization | replay/contract_local only, no model or research tool invocation: failed terminal, tokens/cost null; original raw and old zero-valued observation unchanged | `claude-error-replay-bde3412.json/.exit`, `S/replay-claude-error-usage.py` |
| final bde, CI `36746045909` | Exact headSha, both jobs/all original steps SUCCESS: Ubuntu1101 passed /3 skipped /75 warnings,399.83s; Windows1104 passed /75 warnings,1481.75s. Both strict116/build/SDK/wheel13+Node success | `ci-bde3412-final.json`, `ci-36746045909-root-verified.log` |

First failures below, original C 12 failed / 943 passed and old B first-red gates remain historical failures. No thresholds were relaxed. I helper's first nonexistent TaskRecord hold attribute error was corrected before native launch to a read-only query of the existing authoritative column. Pinned Codex0.159 config-schema/official exact11 approvals/default prompt/read-only/disabled built-ins and other MCP/same UUID/source token2/cumulative-budget checks then passed. Actual subsequent MCP calls establish effective access. Official per-tool policy follows pinned upstream [mcp_tool_call.rs](https://raw.githubusercontent.com/openai/codex/rust-v0.159.0/codex-rs/core/src/mcp_tool_call.rs); no general permission bypass was introduced.

## Later real interface_live: passed unique new run

After C repair and merged gates, new `interface-i-0930-7d04-02` passed official create/attach/attached-destroy rejection/renew/binary/cgroup/log/cancel/destroy and persisted raw checks. Sandbox `78189de1-196d-469e-9f00-1e552634bada`; effect known, science passed, cleanup destroyed, usage/cost null. Actual CPU `100000 100000`, memory `536870912`, cancelled command not running. Independent trusted reader plus Fraction checked all1001 residuals, exact mean `50000001/5`, variance `1/100`, float variance error `1.1175871e-10` within original1e-9. Evidence `interface-live/interface-i-0930-7d04-02/`, `interface-i-0930-7d04-02-independent.json`. Original failed interface runs below were never replayed or rewritten by later GET404 cleanup.

## Actual research case: author evidence passed; full chain AUTH_BLOCKED

Case `nist-i-0930-7d04` was seeded once through B official entry; registered roles use original order and distinct host worker/AgentId/scope bindings. Base workspace revision `4c5dab85c7107b94b3f0819b1a634aeec05021a2`. Author UUID `01a0f2ee-ae2a-7ce3-9470-e485066fb8d2` remained the same across all turns:

| Phase | Actual result | Wall / tools |
|---|---|---|
| interrupt,7d04 | Initial MCP approval denied; natural exit0; available/no claim/no experiment; interruption NOT_RUN | 51.9734652s /1 |
| interrupt-recovery,dec5798 | Actual native discover/claim/renew, host cancelled only Owned Windows Job after renewal, exit1, no experiment; real TTL expired | 53.1386115s /5 |
| resume,dec5798 | Old token1 renew AND legal exact canonical candidate submit rejected before fresh claim2. One real experiment and original candidate submission; optional static check then timed out; no completion in that turn | 412.4825349s /18 |
| local-completion,363cac5 | Native fresh claim3/renew, original token2 trusted verification, quarantined evidence completion; no new experiment/candidate/static/approval/apply | 84.9916294s /12 |

Author cumulative602.586241s /36tools remains within900s /64 observer limits. These are not hard token/cost caps. Interrupted/unknown accounting stays unknown; partial reported native usage remains raw evidence.

Actual author run `a79578f21ff148c6a86708bddd9f611b`, sandbox `14580dc2-65ee-4c0c-b724-9e70fb4f04dd`: succeeded/science passed/effect known/destroyed. Original candidate `sha256:ddd070985e6ee0d895d0c8a3270a4688208c4d4051907a4c79711b40c97b90f5` retains canonical attempt2, builder0 and actual883 code bytes. Failed static report `a9b79ce344fe4a24ac8547efcd69c320`, passed=false/TimeoutExpired, remains unchanged. B fixed shared Git inherited-pipe timeout and event-loop blocking after real bounded red probes; the live Git root cause itself remains unproven.

Trusted original report `7efcf571d7c7434591d975e0cc149b9a` records source swarm/source token2/source attempt2, current observation fence3. Completion preserves original source identity plus observation_fencing_token3; stage evidence_submitted, approved=false, effect_applied=false, source quarantined. Original execution token is immutable data identity, never old-holder write authority. Read-only independent verification checked actual native fencing/TTL/stale paths, unchanged failed report, trusted raw/digests/code and all1001 Fraction residuals: `research-host-7d04/partial-independent-verification.json`, `S/check-author-partial.py`.

Claude replication UUID `5c787eb6-602b-4e03-9fea-313af2b5c826` launched once using existing official authentication and exact narrow trusted tools. Actual API returned401 authentication_failed through10 official retries, then naturally exited1 in186.5831312s /0tools. No MCP call, claim or experiment occurred; replication remains available. Stop identity guard found the owned barrier already absent, refused termination, and no process was killed or interruption claimed. Auth-status logged-in is not successful API authentication. Coordinator performed read-only existing-auth-source diagnosis and requested user identity selection; no credential value/provider/model/account/auth source was changed by I.

The native API-error result contains synthetic zero usage/cost; original raw and first normalized observation remain unchanged, but billing usage/cost are null/unknown. Original A repaired error-accounting normalization at3c4; final bde's read-only replay of this exact real error yields failed/null while preserving raw fields. This is replay evidence, not new live, and no further model calls are authorized.

Original swarm_runs started_at1790782122.151175, max_attempts_per_task3 and runtime3600 give deadline **2026-09-30T16:28:42.151175Z**, now expired unchanged. No clock/run/claim budget reset. Inheritance is NOT_RUN; third identity was not launched. Independent reproduction, original static approval/application, local inheritance validation and actual adoption are absent; actual adoption count0, no AdoptionReceipt/ConsumptionExecution/UseRecord was fabricated.

Full `python tests/integration/check_research_live.py --state S/research-host-7d04` ran unchanged and failed exit1 on absent inheritance-observation.json (`full-live-checker-363cac5-first.log/.exit`). Author-only check explicitly reports AUTH_BLOCKED and does not substitute for full acceptance.

## Independent read-only acceptance, cleanup and remaining limits

Engineering is verified at final bde; the sole Python window was released for coordinator's independent acceptance. Coordinator's stdlib-only SQLite mode=ro/query_only check passed original identity/budget/fence/one-experiment/failed-report/no-adoption/expired-limit assertions, with zero model/experiment calls. Its first incorrect GEP envelope assumption produced KeyError and exit1, both retained; corrected extraction uses existing strategy[1].local_candidate_json, retaining all original assertions. Actual corrected output and exit0 were read from `C:/Users/DW/orca/workspaces/Morphogenesis/morph-research-plan-0930-state/original-case-readonly-schema-corrected.log/.exit`; it explicitly reports full_task_live not_passed.

Coordinator cleanup at2026-09-30T17:22:07Z verified full container ID `eb6152fbdee01a0044cc1fdd881cf05c00dbbf3905411bc6c5a480f6a7141ec6`, exact name `/morph-research-c-0930-server`, owner research-c-0930 and compose project morph-research-c-0930, then stopped only that service, exit0, running→exited. Container, private key and all archives were retained; other resources unchanged. Actual `morph-research-plan-0930-state/owned-service-cleanup.json` remains separate cleanup evidence; no historical unknown result was rewritten. Main, old demo tag, production Hub and root WIP remain untouched.

User authentication identity selection remains pending; elapsed time is not approval, and the expired original run cannot be silently reset or a fourth identity created. Actual independent reproduction, original static approval/application, inheritance local validation and real consumption/adoption remain absent. Linux/WSL actual native, other Agent/SDK vendors, Notebook/Jupyter/CodeInterpreter/volumes/GPU remain NOT_RUN. Full original scientific research/adoption standard is unmet; overall dispatched outcome is failed/AUTH_BLOCKED, engineering passes separately.

## Archived bc4 checkpoint — superseded status, preserved evidence

All "current"/candidate references in the following archived sections describe the original bc4 checkpoint only; final status and exact engineering candidate are above. First failures remain their original outcomes.

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

## Archived remaining acceptance at bc4

At the archived bc4 checkpoint, author interruption / same-session resume / stale renew and legal stale submit rejection had not run; those author behaviors now have the actual evidence listed above. Independent clean reproduction failed before tools because of authentication, inheritance is NOT_RUN, and actual adoption remains absent. The original failed interface records remain failed, and no unknown experiment was replayed. Native identity wall/tool budgets and the original expired run limits were preserved.

Actual research adoption must use existing ConsumptionExecution and AdoptionReceipt plus canonical claim/attempt/result/target-bytes lineage. Coordinator clarified `msg_ad610e51738d` that the original user task did not require the unrelated `metabolism.models.UseRecord` class; do not introduce a second adoption store or manufacture that record. Search, injection, application and actual adoption remain distinct.

Linux/WSL actual native execution, additional Agent/SDK vendors, notebook/Jupyter/CodeInterpreter, persistent volumes and GPU have no live evidence and remain NOT_RUN. Two-platform final CI success and the full actual native scientific chain are still required before declaring completion.
