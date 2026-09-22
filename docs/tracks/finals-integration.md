# Finals independent integration — passed

2026-09-23 Asia/Shanghai. Branch: `morph-finals-integration`. I authored only this report and `tests/integration/check_finals_replay.cjs`; F retained product ownership. Final acceptance is **contract-local / read-only replay**, not live execution.

## Completed scope and lineage

- Normally merged coordinator governance `a186e7b` (includes `54b7981`) and accepted F deliveries: initial `29986331b932df5f865b76f00ba3a55c0410b286` (product `494e31bc833576532c071035f1c9320cf8bb8b8b`), license `cafa875db959d25d25d6430124c9582633ea5183`, motion `b2f61d476fab43dfa0d78c8c84cd83f234169e84`, final **`f99d13988465cd7e56db591ec2cdbbbca2bee553`**. Final product merge: `0d3dd24db57a0a4a007a14de64c31d3e1ef1a257`; subsequent I commit contains final checker/report.
- Actual product scope includes replacement **DOM/JavaScript**, React/TDesign shell, CSS and generated assets under the latest user override; it is not CSS-only. Python backend/contracts and root locks remain unchanged.
- Read upstream Tencent `tdesign-react-starter` package 0.3.1 at `fce97863edd5d5556f766dd4e342aace31a99487` and verified the Board Card/title/count/footer, TopPanel Row/Col composition and AppLayout top layout adaptation against F's sources. The local reference is `C:/Users/DW/AppData/Local/Temp/morph-tdesign-fce97863`. Starter MIT is byte-identical; unrelated template examples were removed. This is an adapted shell, not an unmodified full upstream application.
- All original `tests/integration/*` and `tests/t5/test_adapter.py` remain unchanged; only the new replay checker was added in integration. F replaced its obsolete Stack-specific browser script with a finals-specific one; the original 11 Python tests and original integration assertions were preserved.

## Verification results

| Check | Actual result |
|---|---|
| Original T5 Python tests | **11 passed**, including rerun after motion changed app.js |
| Original Node control tests | **31 passed**; unchanged after motion/license patches, no redundant rerun |
| Clean frontend install/build | `npm --prefix viz/frontend ci` and `npm --prefix viz/frontend run build` passed; generated JS/CSS Git blob hashes equal submitted assets |
| Historical replay | **20 source snapshots, sequence 0–19**, at 1280×720, 1366×768 and 1920×1080: **60 frames, zero failures**; actual source contains 20 entries, not 19 |
| Original read-only layout checker | `check_rehearsal_layout.cjs` ran byte-for-byte unchanged against I's private replay server; exit 0 |
| Geometry | Original readGeometry/assertGeometry imported unchanged; full Gene ledger in first viewport, no chart clipping/node-label overlap, main-panel overlap or internally clipped Gene content; max ledger bottoms **685.59375 / 685.59375 / 745.59375 px** |
| Original stage facts | 0/3→3/3, weight 1.00→1.90 and width 8.6, inactive dashed edge, member online=false, final completed; replay live statuses remain not_run |
| Data correctness | Current-task tokens unknown/911/unknown/1226, actual unarchived count, task round rather than snapshot sequence, real online members, all four Gene states, archive/old-event dimming, real event order/times |
| Empty/error/recovery | Explicitly labelled 503/empty fixtures from populated #11 reset acceptance and statistics; all five statistics restore on replay at all three viewports |
| Browser errors/network | **0 JavaScript exceptions, 0 external requests** |
| Numeric motion | Via actual animationstart events during real history: **9 legitimate value changes per viewport**, each exactly once at **0.3s**; initial render and unchanged polling do not animate; reduced-motion changing all three numbers produces **0 starts**, computed names all none |
| Visual review | All eight final named keyframes (initial, task-in-progress, member-offline, recovery-completed × 1280/1920) inspected; also inspected new/adopted Gene and error/empty frames |
| Original evidence | All **29 files** retain identical SHA-256, size and nanosecond mtime from task start through final package verification; original path below |
| Python distribution | Final isolated sdist/wheel build passed using temporary poetry-core 2.5.0; **85 wheel entries, 84 sdist entries, 15 static resources byte-identical to source**, local index references only |
| Archive boundary | No node_modules or .runtime entries in wheel/sdist; sdist includes frontend lock; all actual bundled dependency licenses present |
| Installed wheel | Original `tools/check_distribution.py --check-node`: **11 packages imported from installed target, resources present, installed verifier passed, Node dependency check true** |

Runtime: Node 24.16.0, Vite 5.4.21, ECharts 6.1.0, Chromium 151.0.7922.34, Python 3.12.13. Final f99d139 changes only licenses/notices relative to b2f61d4, so the final browser artifacts named b2f61d4 validate the exact final DOM/JS/CSS.

## Evidence and commands

Original read-only root: `C:/Users/DW/AppData/Local/Temp/morph-rehearsal-40f04885b37e489fa3ea1a04f61a984d`.

- `.runtime/candidate-b2f61d4/`: final 60 frames, eight named keyframes, per-viewport geometry/statistics/motion, error/empty frames, API history, original-layout stdout and summary; first successful candidate evidence remains `.runtime/candidate-29986331/`.
- `.runtime/replay-preparation/source-before.json` and `.runtime/source-final.json`: matching complete 29-file inventories; each browser run also retains before/after inventories.
- `.runtime/bundled-modules.json`: read-only Vite/Rollup `write:false`, renderedLength>0 audit proves bundled packages **classnames, dayjs, lodash-es, react, react-dom, scheduler, tdesign-react**. Complete installed-package licenses match (normalizing Git CRLF where applicable); starter license matches upstream bytes. Extra tdesign-icons-react license is harmless.
- `.runtime/wheel-resources-f99d139.json`: complete archive entries, resource hashes, local references and license coverage. Final distributions: `.runtime/dist-f99d139/`; installed target: `.runtime/wheel-site-f99d139/`.

```powershell
$py='C:/Users/DW/orca/workspaces/Morphogenesis/morph-onsite-integration/.venv/Scripts/python.exe'
& $py -m pytest tests/t5 -q
node --test tests/integration/test_browser_options.cjs tests/integration/test_observer_control.cjs tests/integration/test_operator_enter.cjs
npm --prefix viz/frontend ci
npm --prefix viz/frontend run build
$env:MORPH_PYTHON=$py
$env:MORPH_PLAYWRIGHT='C:/Users/DW/AppData/Roaming/npm/node_modules/@playwright/cli/node_modules/playwright'
$env:MORPH_CHROMIUM='C:/Users/DW/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe'
node tests/integration/check_finals_replay.cjs C:/Users/DW/AppData/Local/Temp/morph-rehearsal-40f04885b37e489fa3ea1a04f61a984d/rehearsal.json .runtime/candidate-b2f61d4
& $py -m build --outdir .runtime/dist-f99d139
uv pip install --python $py --no-deps --target .runtime/wheel-site-f99d139 .runtime/dist-f99d139/morphogenesis-0.1.0-py3-none-any.whl
& $py -I tools/check_distribution.py --site-dir .runtime/wheel-site-f99d139 --check-node
```

Replay output directories already hold evidence; a rerun requires a new directory. Every I-owned private server exited; 7526/7527 were untouched.

## Failed checks and corrections retained

- Coordinator reported early unaccepted candidates: blank page/process undefined or missing provenance DOM, horizontal overflow, Gene below first viewport. F fixed these; original layout and both full I replay runs subsequently passed without weakening assertions.
- I source review found per-snapshot max normalization hid Gene decay (#4 weight0.9993 and #9 weight0.0136 both full bars). F changed to fixed 0..1 scale before initial acceptance; visible bars now shrink. Review artifact: `.runtime/gene-bar-review.json`.
- Actual bundle audit found lodash-es 4.18.1 missing from cafa875 license copies. F added its complete 47-line license and notices in f99d139; final wheel coverage passed.
- `python -m build --no-isolation` failed: shared environment lacks poetry.core.masonry.api. Standard isolated build succeeded without altering that environment.
- `python -m pip install ...` failed: shared uv environment has no pip. Existing `uv pip --target` installed solely into the artifact directory, then installed-wheel checks passed.
- Initial temporary archive-audit assertion mixed newline-normalized Path.read_text with raw CRLF zip text. Upstream/copy/wheel license bytes proved identical; corrected stronger direct byte comparison passed. This was an audit assumption failure, not a packaging defect.
- Vite's CJS API deprecation notice remains; no build failure. An initial read-only module-audit helper imported the CJS wrapper as named ESM and failed before building; using its actual CJS build API produced the recorded successful module audit.

## Real limits and remaining operations

No in-scope product defect remains. **Original paid live observer NOT_RUN**; no new gateway/model requests, Hub writes, all-suite run, physical witnessing or service switching. Replay cannot establish equivalent live acceptance; interface_live/task_live remain not_run and unknown usage/cost remains unknown. ECharts still uses root lock-installed node_modules and the existing Python vendor route; wheel resource smoke does not establish a standalone Node-free deployment.

Coordinator owns mainline fast-forward, governance acceptance and switching its verified 7527 service. I's final branch/checker/report are committed and pushed; local .runtime evidence stays ignored.
