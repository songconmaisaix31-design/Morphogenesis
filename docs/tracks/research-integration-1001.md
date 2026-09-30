# I1001 independent integration and acceptance

Engineering and installed-product local gates passed. **New formal task_live is NOT_RUN; the original full live checker has not passed.** This is the engineering checkpoint before the coordinator's explicit formal launch release, not completion of the original research task.

## Immutable inputs and ownership

Existing integration branch: `morph-research-integration-0930`. Clean starting HEAD: `c45888f64c1cec60e5f9df45677b6547c4527cac`. Ordinary merges preserve A source `0a192c6b037df0e70cedb17e8d2e8bfa28f0dd09`, A report `46a1282b148fd8e03e2df85cb80de90957d64921`, B contract `a060564dee6d7fa790b64583fd76301e95eadb54` and governance `5415ee9e0cf22aaaa34bb21764249456c03d7601`.

Frozen, pushed, remote-verified core dependency/code candidate: **`cbc4dede782eb79b9c007520d96d7958857da0af`**. All core gates below used this exact source. Product input: private Morphogenesis-Research **`9dd4addf4a141a42040574fef3b614ca62b22a57`**, branch `songconmaisaix31-design/research-product-1001`; its actual installed core VCS origin is CBC. No product glue was necessary; the coordinator explicitly directed immutable installation instead of another checkout.

After the frozen gates exited, ordinary document-only merges incorporated D `8530b1bb8df1c8f5272ff19e8b731c6eea62289a`, B review `c4d46b9325884687571166fa0227ca1214d8c0d9` and governance `e969babf4209df4db06b1c81494c159cfcb3e1cb`. These are evidence/governance inputs, not a replacement core code candidate. The resulting evidence SHA is supplied in the commit/push Handoff; non-document tree differences from CBC are empty.

Original full checker blob remains **`39948d9615bce07b40b96eeaf5dfb263b993c6d3`**. WindowsJob, `_windows_exec.py`, original `test_process.py`, both core locks and the checker are unchanged from c458. I edited no domain source, domain test, model catalogue, account configuration or root WIP. No cherry-pick, force push, main/tag/Hub/EvoMap change or new agent/run.

## Environments and durable evidence

`S` = `C:/Users/DW/orca/workspaces/Morphogenesis/morph-research-integration-1001-state`, outside Git and model workspaces. Original raw logs, exits, exact command arguments and wall timestamps remain in `S`; no key or signed download URL is copied into Git. Each gate has its named `.log`, `.exit` and `.command.json` unless explicitly identified as a launcher diagnostic.

Core Windows: new final-Poetry-lock environment `S/envs/morphogenesis-aDl55zGp-py3.13`, CPython3.13.13, imports from this integration checkout, official OpenSandbox SDKs both1.1.0. WSL: Ubuntu/Python3.12.3, separate `S/envs/linux312`, dependencies constrained to core lock versions, native Linux runtime temp/cache `/var/tmp/morph-i1001-cbc4dede`. Product: new `S/envs/product-9dd4add`, CPython3.13.13; wheel built from exact LF product Git archive and installed with its frozen uv requirements, including development dependencies, **95 distributions**. This is distinct from P's earlier88-runtime-only installation.

Caches and state are exclusive to I. BLAS/OpenMP/MKL/NumExpr thread limits are process-local1; no global PATH/index/config change. Original core `npm ci --ignore-scripts` installed99 packages in the exact LF CBC archive. Product Node dependencies were installed by its formal `setup-assets`, not NODE_PATH or source node_modules injection.

## Core local and CI results

| Host / original command | Actual result | Evidence in S |
|---|---|---|
| Windows `python -m pytest tests/native_agents -q` | 89 passed / 5 POSIX skipped,8.51s | `native-windows` |
| Actual WSL `python -m pytest tests/native_agents/test_posix_process.py -q` | Original5 passed,13.79s | `posix-parent-first-native-temp` |
| Actual WSL `python -m pytest tests/native_agents -q` | 92 passed / 2 skipped,19.79s; WindowsJob and unavailable Linux Node oracle | `native-linux` |
| WSL `python -m mypy --strict orchestration/native_agents` | 10 source files passed | `strict-native-linux` |
| Windows original focused research/experiments/local_assets/swarm command | After justified process-temp correction:542 passed / 2 warnings,556.30s | `focused-windows-corrected`; first RED below |
| Windows original `python -m pytest -q` | **1104 passed / 5 skipped / 75 warnings,662.09s**, exit0 | `full-core-windows` |
| `python tools/typecheck.py` | 116 source files passed | `strict-core` |
| Original `python -m build` | sdist and wheel built; poetry-core2.5.0, isolated build | `build-cbc4dede-official-index`; first403 below |
| `npm run check:sdk` | SDK/schema1.14.0, canonical asset verified, tampering rejected, published=false | `sdk-cbc4dede` |
| Actual wheel install then original `python -I tools/check_distribution.py --check-node` | 13 installed packages, resources, verifier and Node passed | `wheel-install-cbc4dede`, `distribution-cbc4dede` |
| Installed native/experiment/research/case imports and MIT bytes | Four modules from actual wheel target; MIT byte equality | `wheel-research-imports` |
| Original B `bridge_probe.py --c-source <exact b4b403 archive>` | passed; mock remains quarantined, no scientific/live claim | `bridge-cbc4dede` |
| Original B `migration_probe.py --baseline-source <exact ef77 archive>` | actual old candidate/address/report/approval/consumption/adoption unchanged | `migration-cbc4dede` |

The two original missing/unrecognised-effect tests remain intact in the542 focused tests: one backend call, second execution rejected as unconfirmed, release leaves blocked. Other original stale/missing-artifact/execution/science/condition/unknown/native/attached/legacy guards were not removed or relaxed.

Independent exact-head CI **[36762330605](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/36762330605)**: headSha=CBC, run=success, both jobs=success, each original8 shell commands passed (install/npm/pytest/strict/build/SDK/wheel install/wheel checker).

| Actual CI job | Original full test result | Remaining original gates |
|---|---|---|
| Ubuntu110047766591 | 1106 passed / 3 skipped / 75 warnings,483.27s | strict116/build/SDK/wheel13+Node passed |
| Windows110047766654 | 1104 passed / 5 skipped / 75 warnings,1364.83s | strict116/build/SDK/wheel13+Node passed |

Actual status/steps are retained as `ci-cbc4-status.json` and `ci-cbc4-verified-summary.json`; raw logs are `ci-cbc4-ubuntu.log` and `ci-cbc4-windows-powershell.log`. No old single-owner or prior-CI green was substituted, and no CI was rerun.

Fixed ORCA source85f8d6/MIT was independently rechecked against the existing downloaded reference (not a clone): registry43/43, no missing/extra rows; the actually reused TS module and packaged MIT match exact LF Git archive bytes (`upstream-source-matrix-corrected`). Windows native tests executed the existing11-input Node oracle. Inventory43 does not mean43 implemented runtimes: core still implements Codex/Claude CLI, and SDK/WSL model live claims remain NOT_RUN.

## First failures retained

- First focused command: **13 failed / 526 passed / 3 errors,557.04s**. Every failure/setup error traced to unchanged `demo/fault_drill.py:58` OS-temp enforcement (or its dependent expected-error assertion). I initially placed `--basetemp=S/pytest-focused` outside process `TEMP=S/temp`. Only process-local TEMP/TMP became S; source, SHA, command and assertions stayed unchanged. First logs/exits/arguments remain `focused-windows.*`, and first fixture tree was safely moved within S to `pytest-focused-first-red` before the one justified rerun.
- First WSL helper invocation consumed `-d` as PowerShell's common Debug parameter: exit127, no pytest. Explicit native argument arrays corrected the launcher. First actual pytest then ran no tests because DrvFS TemporaryFile.truncate raised FileNotFoundError. `linux-temp-diagnosis.log` reproduces mounted-path truncate failure and own Linux-temp success. Original errors remain `posix-parent-first.*` and `posix-parent-first-launched.*`; original5 assertions/thresholds then passed on Linux-native temp.
- First build failed before backend execution: inherited Tsinghua pip index returned403 for official poetry-core2.5.0. `build-cbc4dede.*` retained; exact same SHA/command passed with only that process's index set to official PyPI. A separate PowerShell `-I` argument-binding failure occurred before the wheel checker; `distribution-launcher-first.*` retained, named argument array then ran the actual original checker.
- Source inventory helper initially expected an un-packaged neighboring TS file and got ENOENT. First helper/log retained; actual package contents were inspected, and only the truly reused module was compared. No product/domain assertion was changed.
- One GitHub status read timed out; two Go-client Windows log downloads returned EOF. Both signed error logs remain private. A bounded different-client GET of the same authorized immutable job log succeeded; the signed URI stayed process-local and out of arguments/Git. These transport failures do not alter CI verdicts.

Older C/B/local/CI failures, previous expired research-host-7d04, Claude401, unknown effects/null usage, failed author static report and absent adoption remain unchanged in the0930 records. No old sandbox experiment or model request was replayed.

## Independent installed product

Exact P wheel, frozen requirements, install, source identity and logs are `product-9dd4add/`, `product-dist-9dd4add/`, `product-locked-requirements.txt`, `product-install.log` and `product-version.*`. Formal version verified the installed core VCS CBC; installed NumAcc4 bytes equal the exact core archive.

- Original P tests against the installed wheel: **20 passed,9.96s** (`product-tests-installed`). No source imports or permission/argv patches by I.
- Formal `version`, `setup-assets`, `doctor`: exit0, actual installed official SDK canonicalization and invalid-asset rejection, ready_local/schema1.14.0; no model/experiment/Hub calls.
- Separate explicitly offline `offline-i1001-installed-01` fixture: formal `init`, Codex/Claude `inspect` and read-only `observe` passed. Three tasks remain available/attempts0, only creation audit; no native observations or experiments. Request/argv/HostBinding come from the installed product. Auth is pending, not alleged ready.
- Its formal `run --phase replication` rejected exit2 with `explicit_operator_auth_selection_required`, before probe/model/experiment. This auth rejection is not misreported as the separate dependency rejection documented in P's selected-auth fixture.

Product owns permissions and role prompts. Original accepted boundary is11 permitted MCP calls, original exact argv/permissions and no outside calls. Codex0.159 automatically exposes resource helpers/model-selected apply_patch; total catalogue=11 is unsupported. Original checker is unchanged. A raw/normalized outside-tool attempt must remain RED; observation cancellation is not a pre-effect guarantee.

## Formal live checkpoint

New `research-formal-1001-01` project/state and runtime clock have **not** been created. No model, auth probe, scientific sandbox or service request was made in this phase. Existing owned service remains stopped; its name/full ID/owner label must be checked before any coordinator-released restart. No other Docker resource is managed.

The coordinator selected existing Claude first-party OAuth for the new named case, implemented only by P's trusted process-local profile exclusion of the two gateway variables, with original model/account/home retained. Actual OAuth/current-model compatibility remains NOT_RUN. This is not authorization to substitute a model/provider/account or patch test environment/argv.

After explicit launch release, the installed formal CLI must initialize a new disjoint project/state and prove the original full path: three native UUIDs/two brands; author owned interruption before experiment, real TTL, same UUID resume and legal stale renew+submit rejection; each role900s/64 observed tools, runtime3600/attempts3, ONE actual sandbox execution per task; author candidate/original verify/evidence completion; independent reproduction and source file validate/approve/apply; active search, third fresh local validation, inherit child/file validate/approve/apply and actual unique existing AdoptionReceipt/ConsumptionExecution. Then execute the **original byte-unchanged** `tests/integration/check_research_live.py --state <formal-state>` and retain its actual result.

Linux/WSL model live, other Agent runtimes/SDKs, Notebook/Jupyter/Code Interpreter/GPU/volumes, second-case abstraction and Hub/EvoMap remain NOT_RUN. No success of an author-only check, terminal exit, offline fixture or engineering CI substitutes for full task_live.
