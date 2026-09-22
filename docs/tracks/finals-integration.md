# Finals independent integration

Owner I, branch `morph-finals-integration`; initial base `38212486a2a859c143d7c5392b2a8e82809cc172`.
Write scope: this report and `tests/integration/check_finals_replay.cjs` only. Product belongs to original F.

## Preparation (2026-09-23 Asia/Shanghai)

- Added a standalone historical replay checker. It launches only `python -m viz.server --rehearsal <temporary copy> --replay` on an OS-selected free loopback port, never 7526/7527, and stops only its own child.
- Source: `C:/Users/DW/AppData/Local/Temp/morph-rehearsal-40f04885b37e489fa3ea1a04f61a984d/rehearsal.json`. Actual history has **20 entries, sequence 0 through 19**, so all 20 will be captured, exceeding the task's stated 19 snapshots without omitting sequence 0.
- Original evidence inventory covers all 29 files; before/after SHA-256, byte size, and nanosecond mtime match. Source files are never written. Temporary working JSON retains historical content; the existing adapter performs replay provenance downgrade.
- Geometry imports original `readGeometry` / `assertGeometry` unchanged, including complete ledger in first viewport, canvas clipping and label/node overlap. Browser mode captures every snapshot at 1280×720, 1366×768 and 1920×1080, waits 650 ms after the observed stage, and saves the four named keyframes at 1280 and 1920.
- Original stage facts remain: 0/3 → 3/3, weight 1.00 → 1.90 with width 8.6, inactive dashed edge, member `online=false`, final completed. Replay must keep `interface_live` and `task_live` at `not_run`.
- `--prepare-only` checks all API snapshots without judging the old frontend against the new design. Result: 20 snapshots, 0 failures, source unchanged, private server exited. Artifacts: `.runtime/replay-preparation/` (ignored).
- Added assertions bound to the new shell's semantic IDs: current-task tokens, actual unarchived Gene count, unique-task round, online membership, and the required black background. Historical token oracle: sequences 0–1 unknown, 2–5 = 911, 6–8 unknown, 9–19 = 1226. Recovery must not inherit 911 or display cumulative 2137. Low weight does not establish archive: only `archived_at` does.
- Separate explicitly labelled 503/empty UI fixtures test acceptance/statistics reset and replay recovery. These start from sequence 11 with two active Genes so an already-zero final count cannot hide stale-state bugs.
- Further browser checks cover main-panel overlap, internally clipped Gene text, all real event sequence/timestamps, four historical Gene states (new #4, decayed #5, adopted #10, archived #18–19), and archived dimming. The unchanged original `check_rehearsal_layout.cjs` also runs against this private replay server.

Coordinator reported an initial, unaccepted candidate failure on port 7528: original `check_rehearsal_layout.cjs` read null `#provenance` after `page.goto` because the React shell had not mounted. This is a reported failed check, not this worker's successful validation; it was returned to F, and the original checker must pass unchanged on the delivered candidate.

Commands executed:

```powershell
npm ci --ignore-scripts
node --check tests/integration/check_finals_replay.cjs
$env:MORPH_PYTHON='C:/Users/DW/orca/workspaces/Morphogenesis/morph-onsite-integration/.venv/Scripts/python.exe'
node tests/integration/check_finals_replay.cjs C:/Users/DW/AppData/Local/Temp/morph-rehearsal-40f04885b37e489fa3ea1a04f61a984d/rehearsal.json .runtime/replay-preparation --prepare-only
```

## Pending acceptance

Await coordinator-accepted exact F SHA before ordinary merge. Coordinator governance `a186e7b` (including `54b7981`) is merged normally. Review actual Tencent TDesign React Starter source/provenance, frontend-only product diff, DOM/JS scope, black/yellow design, current-task tokens, task round, real active Gene counts/four states, archived dimming, current step/events, stale-state reset on API error/empty, and actual screenshots. Run unchanged 11 T5 tests, unchanged 31 Node tests, clean frontend install/build, Python build and installed-wheel resource checks. Preserve original observer and tests.

Full original live observer, new model/gateway execution, remote Hub publishing, and physical screen witnessing are **not run**. Replay/browser evidence cannot establish equivalent live acceptance. No candidate frontend acceptance is claimed by this preparation report.
