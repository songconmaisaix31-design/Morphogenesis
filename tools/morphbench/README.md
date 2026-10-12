# Local MorphBench observer

These scripts observe the operator-supplied MorphBench suite and an installed
Morphogenesis 0.2.1. They do not contain the suite, whose source provenance and
redistribution permission were not supplied. Reproduction requires the same
private snapshot at `C:/Users/DW/orca/mb021-1007/suite`; there is no claim that a
public checkout alone reproduces this experiment. No external service is called.

The measured product source is `50396909c3fbaa510e755b8e2361e05d84afdfaa`.
Use a noneditable installation, lock-aligned Python dependencies, Node, and the
locked root npm dependencies in an ancestor searchable from the installed
`bridge_node` scripts. In this run Q owns that environment; M only reads it.
`environment.json` checks site-packages imports and noneditable metadata;
independent source-byte comparison belongs to Q and is not inferred from version.

Run from an output directory outside the source checkout. Fresh output names are
required; scripts refuse to overwrite evidence. PowerShell example:

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONDONTWRITEBYTECODE='1'
Set-Location C:/Users/DW/orca/mb021-1007/eval
& C:/Users/DW/orca/mb021-1007/verify/venv/Scripts/python.exe C:/Users/DW/orca/workspaces/Morphogenesis/morphbench-eval-1007/tools/morphbench/run_local.py --suite C:/Users/DW/orca/mb021-1007/suite --output C:/Users/DW/orca/mb021-1007/eval/matrix-new --budget 8 --seeds 0 1 2 3 4 --measurement-window Q_quiet_window
& C:/Users/DW/orca/mb021-1007/verify/venv/Scripts/python.exe C:/Users/DW/orca/workspaces/Morphogenesis/morphbench-eval-1007/tools/morphbench/summarize.py C:/Users/DW/orca/mb021-1007/eval/matrix-new --output C:/Users/DW/orca/mb021-1007/eval/summary-new
& C:/Users/DW/orca/mb021-1007/verify/venv/Scripts/python.exe C:/Users/DW/orca/workspaces/Morphogenesis/morphbench-eval-1007/tools/morphbench/mechanisms.py --suite C:/Users/DW/orca/mb021-1007/suite --matrix C:/Users/DW/orca/mb021-1007/eval/matrix-new --output C:/Users/DW/orca/mb021-1007/eval/mechanisms-new --measurement-window Q_quiet_window
```

`run_local.py` reuses the suite's tasks, serial baselines, executor, and immutable
acceptance seeding. Three spawned processes run the installed product's
`Worker.run()` independently. The only policy overrides are existing run limits
(`max_attempts=8`), a **total** energy of eight split 3/3/2, and actual worker RNG
seeds `1000 * trial_seed + worker_index`. No product code, assertion, or validation
threshold is changed. A contended sensing cycle can consume energy without a fit;
such a trial remains incomplete, and no extra worker or retry fills the budget.
Concurrent scheduling, task IDs, and wall-clock decay are not seed-deterministic.

Every search evaluation is logged at start and finish. Successful Worker scores
come from applied result files and are cross-checked against executor observations.
Final configuration selection uses these observations without searching the whole
space again. Precomputation of **every** acceptance config remains an extra cost:
BM-01/02/03/04/05 have 13/9/12/11/60 configs. Each successful trial also performs one
held-out evaluation. Thus budget eight means the search allowance only; total
compute is not matched across the three systems. BM-05 evaluates a mathematical
function, with a per-task cache; it does not fit or train any model.

All dataset and sklearn model seeds remain fixed by the private suite. Trial seeds
vary only allocation. Five trials quantify local allocation variability, not
uncertainty across datasets or research problems. Paired percentile bootstrap uses
10,000 resamples and RNG seed 20261007. Exact two-sided sign-flip p values and BH
adjustment of the ten task/baseline contrasts are exploratory; five pairs cannot
yield p < 0.05 in that test. Sequential testing was not preregistered or executed.
Incomplete trials are preserved and excluded from matched-search-budget contrasts.
Separate fixed-allowance contrasts include observable partial endpoints, with
explicit unequal execution counts. Complete-only comparisons can have selection
bias. Coverage enumerates all planned task/seed/system combinations, including
missing and failed-without-result trials. BM-05's final evaluation uses the same
mathematical objective and has no independent held-out test set.

The executor and all token/cost accounting retain `provenance=mock` and
`usage_source=fixture_mock`. Actual cost is unknown (`null`). Real CPU fitting,
installed Worker execution, and mock provider usage are separate facts. These are
local synthetic tests, not an authorized scientific sandbox or live model run.

`mechanisms.py` keeps the existing SB-01 alive-list adapter visible as an adapter
observation; Q supplies independent process-kill/lease evidence. SB-02 reuses the
suite's field-transfer adapter on a perturbed mathematical objective and reports
negative gains and unreachable targets without clipping or imputation. It executes
four full budgets per seed (reference, training, cold, warm), even if a target was
reached early. This is not research-feedback transfer through real Workers.
SB-03 replays exactly the BM-01 Worker configurations serially and reports the
measured pipeline wall increment; spawning, Git, SDK and validation contribute,
and this cannot isolate coordination time. SB-04 counts repeated configurations
within a task/seed search, with acceptance/test refits separately charged.

Formal BioML/ProteinGym/TDC/Polaris/Open Problems/Kaggle/nanochat datasets and
official scoring are not connected. Tier C's keyword judge is not used as an LLM
or expert review. No official percentile, ranking, research quality, or comparison
with named external products follows from these results.
