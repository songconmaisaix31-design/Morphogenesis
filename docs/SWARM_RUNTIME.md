# Swarm v0.2 runtime, observation and packaging

Worker C owns M5/M7 and the packaging changes in this document. Business scope is [SWARM_TASK.md](SWARM_TASK.md); field, lease and budget contracts are [SWARM_ENVIRONMENT.md](SWARM_ENVIRONMENT.md), and candidate validation/promotion is [SWARM_ASSETS.md](SWARM_ASSETS.md). Baseline is `605cf48b8b05baf86fd68e5d63f495ba3e5d7e69`; the existing official direct Hub adapter originates at `4938bb9`. The old dispatcher and gateway implementation remain unchanged.

## Executable local mode

Both `python -m swarm` and the installed `morphogenesis-swarm` entry point expose `demo`, `seed-demo`, `worker`, and `observe`. Run from the source checkout with its locked Python environment and existing `node_modules`. All runtime artifacts belong outside this repository and the frozen mainline. Example PowerShell commands (use a new directory for the first command):

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
./.venv/Scripts/python.exe -m swarm demo --directory C:/Users/DW/AppData/Local/Temp/swarm-v02-demo --max-cost-usd 0.01
./.venv/Scripts/python.exe -m swarm observe --state C:/Users/DW/AppData/Local/Temp/swarm-v02-demo/state
./.venv/Scripts/python.exe -m swarm demo --directory C:/Users/DW/AppData/Local/Temp/swarm-v02-demo --max-cost-usd 0.01 --resume
```

`demo` seeds six broken Python functions as environmental observations, then starts three independent OS processes. Their fixed local neighborhoods contain two observations each. The parent starts and joins processes; it sends no task IDs, assignments, completion callbacks, or worker messages. Each process samples its neighborhood itself. The command exits successfully only when all three processes exit successfully and at least six promotion audit records exist. `--resume` preserves the field, leases, reports, budget holds and remaining energy; it does not reset cost limits or retry tasks.

For separate terminals, first run `seed-demo --directory <new-absolute-directory>`, then start `worker` independently with `--state`, `--target`, `--instance`, local `--x/--y/--radius`, `--max-cost-usd`, `--executor fixture`, and `--validation-json <operator-owned-file>`. The validation JSON contains argv arrays, for example `[["C:/absolute/path/to/python.exe","-B","{scope}"]]`; it is trusted operator configuration, not signal-selected shell text. Use three instances at x=0,10,20 and radius=1 for the supplied fixture. `--energy` defaults to 20 and `--max-tokens` to 20000. The programmatic `WorkerConfig` also bounds idle counts, sleep durations, lease TTL, and validation deadlines.

This executable uses a **fixture executor**: it applies explicitly supplied code edits and executes real validation commands. It never calls a model. Usage is labeled `fixture_mock`; two synthetic token units per fixture operation are charged against explicit local test prices of USD 1 per million input and output units. Cost fields are estimates, and actual cost stays `null`. This is `contract_local` evidence; `interface_live` and `task_live` remain `not_run`.

## Independent worker path

1. Restore only this worker's durable counters and any interrupted reservation, acquire a worker identity lease, and check its shared account budget.
2. Use B's indexed local `sense` and weighted router. Inputs are the local observations, this worker's capability map and its own pipe history. No global observer view or complete field snapshot participates.
3. Acquire the observation's file/directory scope lease. Re-sense locally to avoid executing an observation retired while waiting. Lease competition consumes bounded energy and sleeps.
4. Attest a real execution bound, reserve atomically against the common account, persist the reservation, and capture A's native scoped Git snapshot under `LeaseManager.guard`. The helper uses an alternate Git index and an unreferenced commit; it does not update target HEAD, refs, or the user's index. Only the leased scope's WIP is overlaid on HEAD.
5. Execute in a separate detached worktree. Settle usage immediately, including a known failed result, before any validation. Missing, malformed or uncertain usage retains the hold and stops autonomous spending; there is no execution retry. A trusted adapter must actually enforce its declared input/output bounds, not merely set a boolean.
6. Publish the candidate through the official SDK-backed local store. A validates syntax, hazards and exact change bounds, then runs the configured commands in a second retained worktree. Reports bind the original candidate, Pydantic AttemptId and environment fingerprint.
7. Under a valid scope guard, promote only a passed report into the explicit nonprotected local workspace. The same guard fences positive/negative pheromone feedback, local pipe reinforcement, retirement and success/quarantine audit. Expired or replaced holders cannot create a success audit or promote. Finally release the scope lease on every normal/error path.

The default metadata-lock wait is 30 seconds in this runtime, using B's bounded OS-lock option; execution and validation do not hold that metadata lock. Timeout causes bounded sleep/exit, never execution retry. If release itself times out, the durable lease is left for TTL recovery. Worker identity contention cannot overwrite another copy's saved counters. Energy is decremented for each loop, including empty and contended iterations. A sleeping process saves its state, sleeps once for a bounded interval, and returns; a supervisor is not silently created.

Every audit includes worker and OS process IDs, AttemptId, signal ID, lease identity, candidate/report IDs, execution and validation workspace paths, environment fingerprint, outcome and provenance. Only the existing gateway parser's whitelisted usage result is saved; raw model responses and exception text are excluded. Executor/result provenance must agree, and replay requires its original run URI. The CLI enables no remote executor. The local asset fixture evidence remains mock; a future live adapter and its asset-evidence mapping need separate verification before live acceptance.

Restart never turns unknown into zero or retries the task. A crash between account reservation and worker-status persistence leaves B's pending hold and duplicate-task fence intact; it is not a completed or free task. A crash after candidate promotion and before audit/feedback can leave partial evidence, requiring inspection of the immutable report and promotion receipt. No multi-file crash transaction or automatic recovery of ambiguous promotion effects is claimed. Git worktrees isolate ordinary file changes, **not** hostile execution as an OS sandbox. Retained worktrees and Git objects require explicit operator retention/cleanup.

## Read-only observer and optional mirror

The observer reads existing field/budget/asset SQLite files using `mode=ro&immutable=1` and `query_only`, and reads lease/audit/worker JSON directly. It never constructs a field, store, ledger or lease manager; never creates missing paths, tables or SQLite sidecars; and never expires leases or updates decay. Active WAL/journals or a changed file stamp produce `busy`/partial health instead of pretending to provide a current snapshot. Views have bounded row/record limits and do not prove cross-file atomicity or acceptance. Raw record provenance remains available within the view; the view itself is not live evidence.

`HubMirror` is disabled by default. Enqueue only performs bounded in-memory operations; one optional daemon thread handles SDK checks and transport, with queue capacity 8 (maximum 64), client timeout at most 10 seconds and close wait at most 1 second. Only locally promoted assets qualify. Artifact directories reject protected paths. Mirror exceptions never change a local result and their text is not logged.

Callers explicitly supply the existing `HubClient` and exact payload-bound `PublishApproval`. For `evolver_proxy`, they also supply a `PublicationRecord` containing the official Gene/Capsule/EvolutionEvent bundle and original model/event lineage. The mirror validates the official schema/addresses, preserves the exact local Gene, binds candidate AttemptId and passing report, and defers missing lineage; it does not invent model names. This supports the existing adapter's `/asset/submit?mode=sync` path. No production call is enabled by the CLI or tests. Mock publication cannot become live evidence through a live transport.

The existing direct adapter writes unknown before an uncertain request and contains credentials. Mirror artifact creation is exclusive and per asset: an existing pending, unknown, rejected or received artifact prevents all later sends, including across restart. A connect failure remains pending and still receives no automatic retry. Queued but unsent entries are not a durable delivery guarantee; process exit can drop them. Local promotion remains usable offline.

## Read sources and exact reuse

The three task-specified full papers, including their equations, results and conclusions, were read on 2026-09-23. The ACO author report was also read through its concluding section and bibliography. These are conceptual references; no paper implementation, figure or substantial text is copied into the package.

| Source/version | Runtime interpretation and limit | Publication license |
|---|---|---|
| Huang et al., [The Capacity Constraint Physarum Solver, arXiv:2010.09280v1](https://arxiv.org/html/2010.09280v1), 2020-10-19 | Flow/pressure systems and capacity-dependent conductivity updates motivate bounded resources. Account reservations and file leases are engineering gates, not this solver; its numerical experiments do not prove our remote cost ceiling. | [arXiv non-exclusive distribution license](https://arxiv.org/licenses/nonexclusive-distrib/1.0/license.html), not an open-source software license |
| Bonifaci et al., [Physarum-Inspired Multi-Commodity Flow Dynamics, arXiv:2009.01498v5](https://arxiv.org/html/2009.01498v5), 2022-02-09 | Continuous electrical flows, Lyapunov cost/energy and conditional convergence results require assumptions absent from discrete task sampling. Runtime feedback inherits no convergence or global-optimality theorem. | arXiv non-exclusive distribution license |
| Awad et al., [A Survey on Physarum Polycephalum Intelligent Foraging Behaviour and Bio-Inspired Applications, arXiv:2103.00172v3](https://arxiv.org/html/2103.00172v3), 2021-05-08 | Local sensing, external environmental memory and adaptive foraging motivate persistent local signals. Biological, reaction-diffusion and multi-agent models are distinguished; this implementation is not a biological simulation. | [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) as linked by the arXiv record |
| Dorigo and Socha, [An Introduction to Ant Colony Optimization, TR/IRIDIA/2006-010.003](https://www.researchgate.net/publication/228388768_An_Introduction_to_Ant_Colony_Optimization), 2007-04-30 author-uploaded full text; [author bibliography](https://iridia.ulb.ac.be/~mdorigo/ACO/publications.html) | Sections 25.2–25.4 describe local stigmergic state, probabilistic construction and deposition/evaporation. We use task-specified softmax and asynchronous completion, not the report's power-law Ant System rule, optional global daemon actions or best-ant aggregation. | Copyright retained; no open redistribution license established, no text/code vendored |

There is no runtime O(n) benchmark, throughput guarantee, convergence claim or continuous Physarum solver in this delivery. A shared filesystem/SQLite account does not establish distributed-host correctness. The `random.choices` operation, existing shared exponential-decay helper, Git plumbing, SDK, SQLite and OS file locks supply the established mechanisms; no scheduler, custom hashing, Manifest, Attempt infrastructure or completion-proof system was added.

| Reused implementation | Verified version/source | License/use |
|---|---|---|
| Pydantic | 2.13.5, [pydantic](https://github.com/pydantic/pydantic), locked environment | MIT; existing AgentId/AttemptId and typed contracts |
| Python standard library | 3.12.13, [CPython](https://github.com/python/cpython) | PSF; multiprocessing, random sampling, queue/thread, pathlib, JSON, SQLite access |
| SQLite | 3.53.1 in the worktree interpreter, [SQLite](https://sqlite.org/copyright.html) | Public domain; existing B/A persistent storage |
| Git | 2.47.0.windows.1, [Git for Windows](https://github.com/git-for-windows/git) | GPL-2.0; external worktree and native scoped snapshot commands, no Git source copied |
| Official GEP SDK | `@evomap/gep-sdk` 1.14.0, [gep-sdk-js](https://github.com/EvoMap/gep-sdk-js) | Apache-2.0 code, CC BY 4.0 specification; existing bridge schema and asset address calls |
| Existing direct Hub adapter | repository `4938bb9`, retained at baseline `605cf48` | Repository Apache-2.0; authorization, unknown state, official Evolver transport and no retries |
| httpx | 0.28.1, [httpx](https://github.com/encode/httpx) | BSD-3-Clause; existing adapter transport and offline MockTransport tests |
| Gateway usage parser / identity contracts | repository baseline `605cf48` | Repository Apache-2.0; called directly without changing dispatcher or execution logic |

No dependency, lockfile or SDK schema changed. Existing [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) contains package notice text.

## Verification and remaining acceptance

Domain acceptance uses real spawned processes, Git worktrees, SQLite, file leases, actual fixture execution and actual promotions. `test_selfgrowth.py` blocks Python socket connections/DNS and old controller imports in each worker, and makes global field/observer access fail. Its barrier starts the processes only. All three must contribute to six promoted fixes. This is not an OS-level network sandbox for every possible child binary; the trusted fixture children perform local operations only.

Other cases cover two generations on the same file with WIP/index/HEAD preservation, persistent restart, crash/TTL and stale-holder behavior, unknown usage, reservation denial before execution, settlement before failed validation, negative feedback, read-only observation, fake high usage stopping all three workers, disabled/offline/nonblocking mirrors, official proxy payloads via MockTransport, and no repeat unknown writes. Artificial high consumption and mock transport are explicitly non-live tests.

Packaging adds `swarm` and `local_assets` to Poetry and full-file strict type checking. Distribution validation imports their concrete modules from the installed wheel, including the native snapshot helper. Existing `foundation` CI already runs pytest, strict checking, build, SDK and wheel validation on Ubuntu/Windows with Python 3.13 and Node 24; this Windows local Python 3.12 run cannot substitute for those jobs. Source `node_modules` is still required for the existing Node bridge dependency resolution; a Python wheel alone does not bundle the SDK.

Completed checks on 2026-09-23, Windows local Python 3.12.13, with all three BLAS thread variables set to 1:

| Command | Result |
|---|---|
| `python -m pytest tests/swarm/test_worker_runtime.py tests/swarm/test_selfgrowth.py tests/swarm/test_mirror.py tests/swarm/test_observer.py -q` | 19 passed in 156.28s, before the additional protected mirror path case |
| `python -m pytest tests/swarm/test_mirror.py::test_enabled_mirror_rejects_protected_artifact_directory -q` | 1 passed in 20.09s; a targeted follow-up, not another full domain run |
| `python tools/typecheck.py` | All 74 source files pass strict checking |
| `python -m build` | Wheel and source distribution built successfully with isolated poetry-core 2.5.0 |
| `npm run check:sdk` | SDK schema 1.14.0 valid; official asset address verified; tampering rejected; published=false |
| `uv pip install --python .venv/Scripts/python.exe --no-deps --target tools/.wheel-site dist/morphogenesis-0.1.0-py3-none-any.whl` then `python -I tools/check_distribution.py --site-dir tools/.wheel-site --check-node` | 13 packages imported from installed wheel, all checked resources present, installed verifier and Node dependency check passed |
| `python -m swarm demo --directory C:/Users/DW/AppData/Local/Temp/swarm-v02-c-20260923-1510 --max-cost-usd 0.01`, then the same with `--resume` | Both exit 0; three process exit codes 0; six completed tasks and observer health ok before and after resume, with no extra promotion |

Installed metadata contains `morphogenesis-swarm = swarm.cli:main`, and the wheel contains `local_assets/snapshot.py`. CLI JSON evidence is retained in the matching `...-result.json` and `...-resumed.json` files under the local temp directory. The high-consumption domain run saved all three worker states as `sleeping` with `budget_or_uncertain_execution`; its per-worker audits show `account_cost_estimate_exhausted`, `budget_stopped`, `account_cost_estimate_exhausted`, confirming account breaker behavior rather than metadata-lock timeout. The accumulated suite also rejects metadata-timeout-only sleeping as breaker evidence.

Source checkpoint at 2026-09-23 23:20 CST: the accumulated 398-case full pytest run is still in progress beyond 54%; all newly added Swarm cases have passed in collection order, but two legacy failure markers exist (launcher environment and official MCP integration positions). Exact final tracebacks and isolated retests are pending; this checkpoint does **not** claim a green full suite or overall acceptance. Recent raw stdout is retained at `C:/Users/DW/AppData/Local/Temp/swarm-v02-c-full-pytest-tail.log`; the final traceback/summary will be appended there. Pending external steps are exact candidate SHA Ubuntu/Windows CI, independent integration review, and any explicitly authorized live executor/Hub acceptance. Frozen mainline remains untouched.

A corrected negative test briefly created `C:/Users/DW/orca/workspaces/Morphogenesis/forbidden-runtime-state` (two directories and three empty-schema runtime SQLite files). Automatic approval review rejected cleanup with `blocked by policy`; the coordinator confirmed it and instructed no retry. These generated files remain for manual cleanup, outside the repository and frozen mainline.
