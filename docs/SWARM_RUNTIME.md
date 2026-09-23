# Decentralized Swarm corrected v0.2 runtime

Worker C owns runtime, CLI, observation, optional mirror and package coverage. The current facts are [SWARM_TASK](SWARM_TASK.md), [SWARM_PLAN](SWARM_PLAN.md), [SWARM_CONTRACTS](SWARM_CONTRACTS.md) and [SWARM_ASSETS](SWARM_ASSETS.md). The frozen baseline is `605cf48b8b05baf86fd68e5d63f495ba3e5d7e69`; development stays on `decentralized-swarm`. Prior runtime and its historical acceptance are preserved at `e9a3836`; those results do not validate this revision.

## Reproduce the local fixture

Use the existing locked environment and SDK installation. Pick a new directory outside this repository and the frozen mainline:

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
./.venv/Scripts/python.exe -m swarm demo --directory C:/Users/DW/AppData/Local/Temp/swarm-corrected-v02 --max-cost-usd 0.01
./.venv/Scripts/python.exe -m swarm observe --state C:/Users/DW/AppData/Local/Temp/swarm-corrected-v02/state
./.venv/Scripts/python.exe -m swarm demo --directory C:/Users/DW/AppData/Local/Temp/swarm-corrected-v02 --max-cost-usd 0.01 --resume
```

`python -m swarm` and installed `morphogenesis-swarm` provide `demo`, `seed-demo`, `worker`, and `observe`. `seed-demo --directory <new directory>` creates six broken functions in three actual modules. It seeds immutable acceptance policies independently of future candidate output. `demo` launches three independent processes with module permissions, then joins them; it sends no task assignments, callbacks, results or worker messages. Workers query and sample their own neighborhoods. CLI success requires all three child exit codes to be zero and six completed finalization audit records. Both the direct worker CLI and demo child return exit 1 for `stopped` or `needs_review`.

Separate terminals can start workers after `seed-demo`:

```powershell
./.venv/Scripts/python.exe -m swarm worker --state <state> --target <local-workspace> --instance 0 --scope module_0 --module module_0 --max-cost-usd 0.01 --executor fixture
```

Use distinct instance IDs and corresponding module permissions for the other workers. `--scope` is repeatable, is relative to the target, and must be explicit. Coordinates no longer affect authorization or routing. `--max-tokens` defaults to 20000, `--energy` to 20, and `--swarm-id` to `local-fixture`. Run-wide task, attempt, derived-task and time limits come from B's persisted `RunLimits`; changing a durable policy is rejected.

The fixture changes real files in retained isolated Git worktrees. Validation compares exact files against the trusted task policy and parses supported syntax; it never evaluates candidate code. Arbitrary validation commands fail closed because a worktree is not an operating-system sandbox. This bounded literal-file mode does not claim general model-driven coding or arbitrary-code execution acceptance. Test-only behavior checks execute only the explicitly known fixtures.

Synthetic usage is two units per transformation, with local test prices of USD 1 per million input/output units and an explicit fixture monetary admission bound of USD 0.000002. This is a contract-local simulation, not an upstream billing promise; actual billed cost stays `null`. No remote model or production Hub request is made. `interface_live` and `task_live` remain `not_run`.

## Worker path and recovery

1. Query B's swarm/owner-scoped pending reservations before reading status JSON and mark interrupted holds uncertain, including a crash between reserve commit and status writing. Restore the worker's durable counters and interrupted finalization, then check the shared swarm-run breaker, remaining energy and runtime bounds.
2. Query B's authorized local ledger and weighted router. Historical weights actually enter the softmax score; B persists signals, exclusions and probabilities. Global observer/field snapshots are never decision inputs.
3. If a task explicitly consumes a completed dependency whose asset is not approved yet, wait with bounded exponential backoff and jitter before claiming or reserving. This approval window creates no attempts or charges.
4. Atomically claim through B's SQLite ledger. The lease binds task, swarm, owner, integer fencing token and current expiry. A bounded renewal thread maintains this lease during snapshot, SDK and validation operations; it neither selects nor assigns tasks.
5. Reserve budget using the existing `task_id:lease.token` identity before execution. Persist the hold in worker state. B conservatively retains the original admission debit after settlement; unknown usage or uncertain execution preserves the hold and stops new autonomous spending. No transport retry occurs.
6. Snapshot only the leased scope through A's native Git helper. Execute the fixture in a separate worktree. For reuse, FETCH the explicit approved dependency asset, check applicability, inject it with swarm/task/worker/token/input/execution context, and derive the new candidate from its exact addressed bytes. Mapped destinations are checked against scope and the 256 KiB preimage limit before reading them.
7. Settle usage immediately, including known failure, before validation. A known valid request using the final allowance still validates and completes; exhausted admission prevents the next request. Unknown usage and provider-bound violations cannot finalize. The existing gateway parser whitelists numeric usage; raw responses and exception text are excluded from durable runtime records. Failure leaves task facts and negative evidence intact.
8. Validate using immutable operator-seeded task acceptance. Prepare A's target application outside a SQLite write transaction. Stop renewal, verify the exact lease, and call B's `submit` with a short prepared callback. No model, SDK, Git command or test runs inside that transaction. The callback checks the submit-side fence immediately before each target write.
9. Only an accepted `completed` result with authoritative `effect_applied` permits local index approval and actual adoption recording. Local approval does not apply the patch itself. Deposit positive feedback, save provenance audit and optionally enqueue the off-by-default mirror. Finally release by exact token; old holders cannot release newer leases.

Execution outcomes and authoritative task history remain in SQLite; JSON is status/evidence export. Every finalization audit includes OS PID, worker/swarm/task/attempt identity, lease token, result/asset/report IDs, policy, usage provenance and separate execution/validation workspaces. Runtime state and targets reject links and protected repository paths. Target HEAD, index and unrelated WIP are preserved.

A killed worker that has only claimed a lease can expire and be replaced with a higher token. A pending/uncertain budget request is never treated as a free retry. A crash after B's durable `submitting` intent leaves an ambiguous filesystem publication: the scope remains blocked for manual recovery. No cross-database or multi-file transaction is claimed.

Existing worker state saves pending finalization before submit. On restart, a matching completed task can recover idempotent approval/adoption and audit without executing or applying again. A mismatched result, uncompleted intent, expired approval evidence, or interrupted feedback pair returns `needs_review`. `feedback_started` is saved before deposition; if completion was not saved, feedback is not replayed and no completed CLI audit is fabricated. This avoids duplicate reward while keeping the incomplete evidence visible. A process restart does not reset its energy or shared budget. Unique worker instance IDs are an operator configuration requirement.

## Observation and optional mirror

The observer imports no ledger, worker, router or lease manager. It directly reads existing SQLite files and existing JSON evidence with bounded limits. It neither creates tasks/tables nor claims, expires, refreshes, settles or checkpoints them. Existing hot WAL is read in a `mode=ro`, `query_only` read transaction; SQLite SHM reader marks/locks may change. This bookkeeping exception was explicitly agreed after a byte-level test demonstrated that SQLite read-only WAL access changes SHM. Database/WAL payloads and business rows remain unchanged. Missing state creates nothing. A missing SHM for a hot WAL or a recovery journal produces `busy`, and checkpointed files use immutable mode to avoid creating sidecars. Views are per-file snapshots, not cross-file transactions.

`HubMirror` remains disabled by default and uses the existing official direct `HubClient` from `4938bb9`. Only locally `approved` assets qualify. Enqueue does bounded in-memory work; a daemon thread performs SDK/transport work with queue size 8 (maximum 64), client timeout at most 10 seconds and close wait at most 1 second. Caller supplies payload-bound `PublishApproval`; official proxy publication also requires the exact caller-supplied Gene/Capsule/EvolutionEvent lineage. There are no fabricated model names, credential searches or exception-text logs.

Mirror receipt files are exclusively created per asset. Existing pending/unknown/rejected/received records prevent repeat sends, including across restart. The observer projects adapter states into `pending`, `confirmed`, `rejected`, `unknown`, retaining the original adapter state. `confirmed` means acknowledged transport, not Hub promotion. Queued unsent items can be lost when the process exits; this optional mirror is not a durable delivery service. Offline mirror failures never change local outcomes.

## Sources and reuse boundaries

The referenced papers are read as conceptual sources, including equations, case studies, proofs/discussion and conclusions. No paper code, figure or substantial text is vendored. The implementation is local reward routing inspired by environmental memory and tube adaptation; it is not a discretization of the papers' flow solver.

| Source/version | Relevant boundary | License |
|---|---|---|
| Huang et al., [The Capacity Constraint Physarum Solver, arXiv:2010.09280v1](https://arxiv.org/html/2010.09280v1), 2020-10-19 | `Qij = Dij/Lij * (pi-pj)` defines flow; adaptation changes `D`, not `Q`. Capacity regulation and empirical stopping thresholds do not establish a billing guarantee. | arXiv non-exclusive distribution license; not a software license |
| Bonifaci et al., [Physarum-Inspired Multi-Commodity Flow Dynamics, arXiv:2009.01498v5](https://arxiv.org/html/2009.01498v5), 2022-02-09 | Electrical flows, Lyapunov energy/cost and convergence assumptions differ from discrete task sampling. Its convergence results are not inherited here. | arXiv non-exclusive distribution license |
| Awad et al., [A Survey on Physarum Polycephalum Intelligent Foraging Behaviour and Bio-Inspired Applications, arXiv:2103.00172v3](https://arxiv.org/html/2103.00172v3), 2021-05-08 | Distinguishes biological experiments, flow, reaction-diffusion, cellular and agent models. Environmental memory is an analogy; backend scope is not a biological or frontend coordinate. | CC BY-NC-SA 4.0; reference only |

Historical ACO reading/provenance is preserved in `git show e9a3836:docs/SWARM_RUNTIME.md`; no ACO implementation is copied. B's independent reward alpha and `tau_seconds=86400` implement the task contract; `rho(dt)=1-exp(-dt/tau)`, half-life `tau*ln(2)`. There is no convergence, optimality, O(n) coordination or throughput benchmark claim. SQLite WAL supports this same-machine trusted-process design, not cross-machine consensus.

| Reused implementation | Exact version/source | License and use |
|---|---|---|
| Python standard library | 3.12.13, [CPython](https://github.com/python/cpython) | PSF; multiprocessing, random sampling, threading, queues, SQLite, JSON and pathlib |
| Pydantic | 2.13.5, [Pydantic](https://github.com/pydantic/pydantic) | MIT; existing AgentId/AttemptId and data models |
| SQLite | 3.53.1 in the locked interpreter, [SQLite](https://sqlite.org/copyright.html) | Public domain; authoritative task/lease/budget transactions |
| Git | 2.47.0.windows.1, [Git for Windows](https://github.com/git-for-windows/git) | GPL-2.0; external native worktree/snapshot plumbing |
| Official GEP SDK | `@evomap/gep-sdk` 1.14.0, [gep-sdk-js](https://github.com/EvoMap/gep-sdk-js) | Apache-2.0 code, CC BY 4.0 specification; existing NodeAssetBridge schema/address verification |
| Official direct Hub adapter | repository `4938bb9`, baseline `605cf48` | Repository Apache-2.0; existing authorization and no-retry uncertain-write handling |
| httpx | 0.28.1, [httpx](https://github.com/encode/httpx) | BSD-3-Clause; existing transport and explicit MockTransport tests |
| Identity and usage parser | repository baseline `605cf48` | Apache-2.0; direct reuse, old dispatcher unchanged |

No dependencies, lockfiles or SDK schemas change. Existing notices remain in [THIRD_PARTY_NOTICES](../THIRD_PARTY_NOTICES.md). Package declarations and full-file strict checks already include `swarm`/`local_assets`; installed-wheel checks now include the new concrete task ledger, application and consumption modules. Existing CI matrix remains authoritative. The wheel alone does not install the Node SDK; the existing source `node_modules` boundary remains.

## Current verification

Windows local Python 3.12.13, BLAS/OMP/MKL threads set to 1; verified 2026-09-24 Asia/Shanghai:

| Command after `./.venv/Scripts/python.exe` | Result |
|---|---|
| `-m pytest tests/swarm/test_worker_runtime.py tests/swarm/test_selfgrowth.py tests/swarm/test_observer.py tests/swarm/test_mirror.py -q` | **30 passed in 207.79s**, including both budget regressions |
| `-m pytest tests/swarm/test_worker_cli.py -q` | **4 passed in 1.21s** |
| `-m mypy --strict swarm/worker_loop.py swarm/observer.py swarm/hub_mirror.py swarm/cli.py swarm/__main__.py tools/check_distribution.py` | **6 source files clean** |
| Same strict command with `--platform linux` | **6 source files clean**; static platform target, not Linux runtime evidence |

The subsequent CLI exit-code correction also passed strict Windows/Linux checks. Initial runs were observer/mirror **9 passed in 18.55s** and runtime/selfgrowth **19 passed in 183.28s**. Full pytest, full strict, build, SDK and distribution validation belong to independent I after A/B/C settle, per the corrected plan.

Fresh CLI demonstration: `-m swarm demo --directory C:/Users/DW/AppData/Local/Temp/swarm-c-v02-20260924-0011 --max-cost-usd 0.01`, then the same command with `--resume`; both returned exit 0, child exit codes `[0,0,0]`, and six completed tasks. Initial worker PIDs were 32744, 4940 and 6564, each with two completions. Audit/report counts were six; resume kept six audits. Full observer output is retained in the adjacent `swarm-c-v02-20260924-0011-initial.json` and `-resume.json` files outside the repository.

Before correction, the two recovery/final-credit regressions failed in **6.64s** under `pytest-116`: the reserve-before-status case observed `snapshot.reason is None` instead of `unknown_usage`, and the final-credit case observed `completed=0` instead of 1. Both tests remain in `test_worker_runtime.py`; no failing artifact was deleted. This evidence led to B's owner-scoped pending lookup and stronger breaker precedence, then the runtime corrections described above.

Acceptance includes three independent offline processes performing six actual fixture transformations, each contributing two; process start barrier only; disabled controller imports, socket/DNS calls and global decision views; real killed-worker TTL recovery; stale submit rejection; unknown request persistence; fake high consumption stopping all workers; quarantine; renewal; target/WIP preservation; cross-member content adoption; readiness without attempts; restart between accepted effect and approval; incomplete feedback without replay; source-read boundaries; read-only WAL observations and offline mirror behavior.

All fixture/model/metering and HTTP mock evidence is `contract_local`. Python socket blocking is not an OS sandbox for arbitrary child binaries; arbitrary candidates are never executed. Real model-gateway availability while Hub is offline, production Hub, billed cost reconciliation, arbitrary-code sandbox execution, physical operation, exact candidate CI and merging into mainline are **not run**. No mainline merge, deployment or demo-process mutation is authorized. Existing temporary artifacts from historical runs are retained; no unrelated cleanup is performed.

The coordinator relayed a subsequent requirement at 2026-09-24 00:11 Asia/Shanghai: algorithm attempts must use the EvoMap API. The local checkpoint `bc1827a046f0b65beb643726257c7c7c4f20deb7` (2026-09-24 00:14:13 +08:00) is retained as deterministic regression evidence. The API phase below extends it; a concrete credential path and admission configuration remain unavailable for real execution.

## EvoMap data algorithm entry

`python -m swarm evomap --config <operator-config.json>` starts three independent workers; `--resume` uses the same persisted run. All six algorithm tasks use the existing EvoMap Chat Completions endpoint and the configured model. The six tasks are integer sorting, order-preserving string deduplication, three-smallest selection, integer sum, string frequencies, and a second member reusing the first sorting result. Python `sorted`, `dict.fromkeys`, `heapq.nsmallest`, `sum` and `collections.Counter` create fixed oracles at seeding time. Oracles stay in task acceptance and never enter the signal payload or model context.

Workers receive backend scope permissions and module membership only. Builder 2 may access `module_0` for the `reuse` module while its own independent task stays in `module_2`; builder 0 selects only `module_0` tasks. The source and consuming tasks therefore share a real scope and its exclusive lease, satisfying A's existing applicability rule. Approved content enters the actual consuming model request. Only a returned answer with the exact source bytes and the supplied asset ID can bind A's existing consumption/adoption receipt; injection or a local copy alone is insufficient.

The model returns JSON data, normalized to a JSON file candidate. A's independent literal-file policy validates the exact expected result. No model code is imported, evaluated or executed. These tasks can support limited data-task acceptance; they do not establish general coding-agent or operating-system sandbox acceptance.

Example configuration structure below uses **operator admission allowances**, not provider prices or a billed-cost ceiling. Choose an unused experiment directory and a private credential file outside every repository, task, state, execution and validation directory. This example is not evidence of a configured or completed live run:

```json
{
  "directory": "C:/Users/DW/AppData/Local/Temp/swarm-evomap-operator-run",
  "swarm_id": "evomap-data-v02",
  "api": {
    "model": "evomap-gpt-5.6-luna",
    "credential_file": "C:/Users/DW/private/evomap-api-key.txt",
    "max_input_bytes": 12000,
    "max_output_tokens": 1024,
    "timeout_seconds": 60
  },
  "budget": {
    "max_tokens": 20000,
    "max_cost_usd": 0.06,
    "unbounded_reservation_usd": 0.01,
    "prices": null,
    "limits": {
      "max_tasks": 6,
      "max_attempts": 6,
      "max_attempts_per_task": 1,
      "max_derived_tasks": 0,
      "max_runtime_seconds": 300
    }
  }
}
```

`request_bound=unbounded` and `provider_enforced=false` are intentional. The explicit positive `unbounded_reservation_usd` enables B's admission policy; its default is denial. Without real matching price configuration, valid reported tokens remain known but costs remain `null`, the full reservation is retained, and `unknown_cost` blocks subsequent requests. Known valid in-flight responses may still finish fixed validation and fenced submission. Thus a price-less run cannot promise six requests/completions. Missing usage, unknown transport effects and token-limit violations reject effects and stop further admission. There are no retries, fallback providers, new-run retries or automatic paid tests.

The file path is the only credential reference passed to workers. An HTTP-only child reads its content; the parent does not. Inherited `MORPH_EVOMAP_API_KEY` is rejected before Git, SDK or validator launch, so configure the file route and clear that inherited variable. Linked or overlapping credential paths are rejected before snapshots or preimage reads. The child has a bounded lifetime, bounded response and no further child process. The extracted `orchestration.gateway_transport.single_request` retains the original httpx no-retry, no-redirect and no-environment-proxy lifecycle. The original `GatewayExecutor` remains restricted to its existing sample/TASK exercise and retains its STOP, usage, secret-redaction and path checks.

Durable request evidence records identity/model/limits/input byte count, with no raw prompt or credential path. Task inputs and routing probabilities remain reproducible from the immutable task and routing ledger. Response evidence contains only parsed, credential-screened content and numeric usage; exception strings, headers and raw error bodies are excluded. Each final audit/result binds requested/returned model, local/provider request IDs, HTTP status, elapsed time, actual cost `null`, execution evidence URI and adoption lineage. Missing provider IDs/models stay `null`.

The experiment summary requires at least five distinct accepted tasks, all three member IDs, three independent OS PIDs and an authoritative cross-member adoption receipt before its `task_live` scenario passes; six completions plus zero child failures are required for CLI exit 0. A 200 status alone never passes `interface_live`. Mock transport and simulated IPC remain `mock`/`contract_local`. Local terminal tasks allow bounded early exit; otherwise dependency waits use exponential backoff within energy/time limits.

## API-phase regression and CI limits

The extracted transport passed the **33 original gateway tests in 5.78s**. API negative/credential/unknown-cost checks passed **13 tests in 28.16s**; the corrected three-process API-path test passed **1 test in 108.47s**, making exactly six MockTransport requests (two per member), applying six oracle-checked JSON results and persisting one exact cross-member adoption. These are offline contract tests, not actual EvoMap calls.

Final combined C domain gate, 2026-09-24 00:34 +08:00, with all BLAS thread variables at 1:

```powershell
./.venv/Scripts/python.exe -m pytest tests/swarm/test_worker_runtime.py tests/swarm/test_selfgrowth.py tests/swarm/test_observer.py tests/swarm/test_mirror.py tests/swarm/test_worker_cli.py tests/swarm/test_worker_evomap.py tests/t2/test_gateway.py -q
# 84 passed in 156.61s
./.venv/Scripts/python.exe -m mypy --strict swarm/worker_loop.py swarm/evomap_executor.py swarm/observer.py swarm/hub_mirror.py swarm/cli.py swarm/__main__.py orchestration/gateway.py orchestration/gateway_transport.py tools/check_distribution.py
# 9 source files clean; same command with --platform linux also clean
./.venv/Scripts/python.exe -m swarm evomap --help
# exit 0; explicit --config and --resume entry available
```

The gate includes the additional aggregate-live acceptance negative cases, deterministic and real-wall-clock renewal cases, and bounded Windows sharing-conflict test. Full pytest/build/SDK/distribution and exact-SHA cross-platform CI remain independent I's responsibility; they were not substituted by this domain run.

Original CI [run 35887345947](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/35887345947) at `bc1827a` had **2 failed, 433 passed, 1 skipped** on Ubuntu; Windows was cancelled. The process test lost its temporary Barrier's POSIX semaphore before child unpickling; it now retains a parent reference until join. The old 0.25s wall-clock renewal failure reported only `stopped`, so its specific failure cause remains unknown. Replacement protocol coverage advances a controlled ledger clock across three persisted real-thread renewals; separate wall-clock coverage uses a 2s TTL, execution longer than that TTL, and checks actual renewal count. Neither Windows success nor Linux-target type checking proves the next Linux CI run passed.

The first new API concurrency run under `pytest-123` failed in **182.80s** with zero admitted requests: new `opportunity` signals defaulted to `innovation`, while workers advertised `repair`. The data task and worker capabilities are now explicitly `data`. A diagnostic Windows file read also exposed a transient `WinError 5` on status replacement. Status export now permits at most three local rename attempts for that known failed sharing operation, preserving the old file on persistent failure; this does not repeat model/API work. Original failure artifacts remain retained. No real EvoMap request, actual billed-cost reconciliation, production Hub publish, mainline merge or deployment has occurred in this phase.
