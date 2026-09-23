# Corrected swarm environment, task ledger and budget

B owns `swarm/{models,task_ledger,pheromone,router,lease,budget}.py` and this report.
Current interface authority is [SWARM_CONTRACTS.md](SWARM_CONTRACTS.md), replacing
all earlier radius, JSON lease, archive-as-decay and account-wide budget claims.
Historical commits through e9a3836 remain intact. No mainline/deployment changes.

## Durable facts and local queries

`TaskLedger(path, swarm_id)` stores immutable task identity/content, scope, module,
dependencies, acceptance policy, attempt observations, result and append-only audit.
Task attempts are plain SQLite records with integer generation, not a new Attempt
framework; existing runtime `AttemptId` remains unchanged. Error observations use
literal normalized evidence keys and merge repeated occurrences into one task.
Failed attempts retain evidence and return available until the attempt limit;
completed and exhausted tasks remain queryable after restart.

Only pheromone/history tables decay. Tasks, dependency edges, attempts, result
acceptance and task audit never decay. JSONL is an explicit export and changes to
an export cannot change authority. Old field/account database layouts fail closed
for explicit migration; no automatic import, deletion, or dropping unknown holds.

Locality requires explicit `authorized_scopes`; empty means no authorization.
Resolved workspace/scope paths, module filters and one-hop dependency neighborhoods
are applied in SQL before task bodies are decoded. Queries use a SQLite B-tree
workspace/scope index, bounded result limit (default 100, max 1000), at most 64
scope/module/dependency filters, and capability filtering before LIMIT. This is
bounded data retrieval, not a constant-complexity or throughput theorem. x/y/radius
remain compatibility display fields without any authority or routing meaning.
Tasks beyond the query limit wait behind older eligible work; this is not a
starvation-free scheduler. Completed dependencies must exist in the same swarm.

## WAL claims and submit-side fencing

All task/lease authorities share one WAL database. Mutations use short
`BEGIN IMMEDIATE` transactions, FULL synchronous writes and bounded lock timeout.
Reads use consistent read transactions. Claim atomically checks authorization,
dependencies, task status, attempt limits and scope overlap, then increments that
task's integer fence and persists owner plus expiry. Parent/child scopes collide;
resolved junction/symlink, dot and Windows case aliases collide. Unrelated siblings
can proceed. Tokens do not reset on expiry or release.

Renew/release/submit validate swarm, task, owner, token, current expiry and TTL.
A stale owner cannot release its successor. The same completed identity/result
replays idempotently; a conflicting result or stale generation is rejected before
an effect. Renewal returns a new expiry identity, so callers retain the latest
lease. Runtime calls, tests, SDK operations, and git snapshot preparation occur
outside write transactions.

For isolated filesystem effects, submit first commits a `submitting` intent. It
then checks fencing inside a short transaction while A publishes only prepared
bytes and checks ownership immediately before each write. Successful callback plus
final TTL check atomically persists `completed` and `effect_applied=true`. A caller's
arbitrary result metadata cannot set that flag. A independently verifies actual
bytes before recording adoption. A no-op callback alone is not proof of useful work.

Crash, expiry or exception after intent leaves `submitting`; it blocks both the
same task and overlapping scopes, including after restart. No replay/reclaim occurs
automatically: partial filesystem effects need manual reconciliation. This is
fail-closed recovery, not a multi-file filesystem transaction or cross-machine
consistency protocol. Trusted same-machine workers must share the database and
use reliable clocks; hostile workers with direct file/DB access are out of scope.

## Decay and actual routing influence

The shared `metabolism.decay.exponential_decay` remains unchanged:
`rho(dt)=1-exp(-dt/tau_seconds)`, default `tau_seconds=86400` and half-life
`tau_seconds*ln(2)`. `metabolism/service.py`'s 0.05 remains archive_threshold.
Reward alpha is independently configurable, default 0.05; tau and alpha persist
per swarm. Reads evaluate from stored anchors and never compound repeated reads.

Failure weakens concentration and increases its future decay multiplier. History
also decays by elapsed time. Reward is zero for failure, otherwise
`0.5 + 0.25*speedup + 0.25*token_saving`; alpha updates
`w_next=(1-alpha)*w+alpha*reward` after elapsed history decay. Initial history is
0.25. Exact exploitation score is
`beta*w_history*concentration*capability_match*effective_urgency`.
Effective urgency is base urgency times `1+min(10,age/aging_seconds)`. Stable
softmax probabilities mix with normalized age weights using exploration (default
0.05). Even fully decayed tasks remain eligible for exploration.

Routing audits preserve authorization/neighborhood constraints, inspected filtered
tasks, status/dependencies/attempt/owner inputs, each concentration/history/match/
urgency/score, normalized exploitation and final probabilities, and selection.
History changes a seeded next selection in the tests. No greedy branch or
Physarum pressure/flow solve is claimed; no paper convergence theorem transfers.

## Budget evidence and admission limits

Budget policy and reservations are swarm-run scoped, not account-wide. WAL short
transactions serialize reserve/settle; policy/start time survive restart. Token
limits, per-worker burn windows, max tasks, global/per-task attempts, max derived
tasks (task ledger), and run duration bound autonomous work. Requests carry an
existing attempt or task/fence identity: a known settled failure permits a new
identity, while pending/uncertain requests prohibit another request for that task.

Persisted evidence labels are `usage_metering=verified|unknown`,
`request_bound=verified|unbounded`, `admission_control=enabled|disabled`, and
`cost=estimated|billed|unknown`. The existing strict gateway usage parser is reused.
Synthetic usage being well-formed proves only contract_local metering behavior.
Explicit prices produce estimates; actual cost stays None, and this adapter never
emits billed. `provider_enforced=True` alone does not establish a verified monetary
upper bound. Verified bounds additionally require an explicit contractual cost
ceiling and trusted executor evidence; no remote provider contract is verified here.

Admission checks settled admission charges plus all pending/unknown holds plus the
new request. Unbounded requests support estimated admission control only; hidden
calls, retries and other account spend are not covered. Without a bill, every
request (verified or unbounded) keeps `max(original_reservation,usage_estimate)`
as a conservative admission debit after usage settlement. Snapshot fields
`admission_charged_usd` and `unreconciled_reservations` expose this commitment;
lower observed usage never restores allowance. Unknown usage/cost retains the full hold, trips the shared breaker and
stops new admission; no expiry, reset or blind retry exists. Disabled admission is
explicitly labeled and makes no ceiling claim. Identical settlement charges once;
conflicting known usage is rejected. Unknown evidence is not overwritten later.

## Read sources, versions, and reuse

Historical provenance carried from the original B implementation: the three full texts were read in that phase. This corrected phase reuses that attribution; it does not claim a new literature review. Papers provide conceptual context; their source code and text were not copied into the package.

| Source | Applicability and boundary |
| --- | --- |
| Huang et al., [The Capacity Constraint Physarum Solver, arXiv:2010.09280v1](https://arxiv.org/html/2010.09280v1), 2020-10-19 | Sections 2–3 couple conductivities to global pressure/flow equations; capacity threshold k modifies the update. Experiments also show sensitivity to stopping tolerance and residual oversaturation. Our leases and preflight reservations are explicit engineering constraints; they are not that solver and inherit no capacity or convergence theorem. |
| Bonifaci et al., [Physarum-Inspired Multi-Commodity Flow Dynamics, arXiv:2009.01498v5](https://arxiv.org/html/2009.01498v5), 2022-02-09 | Uses electrical flows, one/two-norm aggregation, generalized continuous dynamics and a Lyapunov objective. General convergence to a minimizer has additional fixed-point assumptions; mirror-descent results concern a particular continuous variant. Our scalar task reward update and stochastic local sampling do not satisfy those models' premises. |
| Awad et al., [Survey, arXiv:2103.00172v3](https://arxiv.org/html/2103.00172v3), 2021-05-08 | Reviews biology, experiments, flow-conductivity, reaction-diffusion, cellular and multi-agent models, competition and applications. Its environmental memory/competition discussion motivates local sensing and own experience. It does not establish a theorem for this software swarm. Full text was also retrieved through the [ar5iv rendering](https://ar5iv.labs.arxiv.org/html/2103.00172). |
| Marco Dorigo, [Ant colony optimization](https://www.scholarpedia.org/article/Ant_colony_optimization), Scholarpedia 2(3):1461, 2007, revision 90969, DOI 10.4249/scholarpedia.1461 | Primary author describes probabilistic construction, environment pheromone memory, deposit and evaporation. Ant System uses `(1-rho)*tau + sum(delta)`; the task-specified softmax is our discrete heuristic and differs from AS power-law transition probabilities and ACS's greedy branch. The article cites Dorigo/Maniezzo/Colorni 1996, DOI 10.1109/3477.484436. |

The capacity and multi-commodity papers use the [arXiv non-exclusive distribution license](https://arxiv.org/licenses/nonexclusive-distrib/1.0/license.html). The survey's arXiv record links [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). Scholarpedia retains its published copyright terms. Only short formula attribution and independent implementation are used, with no paper figures or substantial prose vendored. No continuum convergence, global optimality, biological fidelity, or measured O(n) performance is claimed.

Implementation reuse: existing repository gateway parser and metabolism behavior from frozen `605cf48` (repository Apache-2.0); locked Pydantic 2.13.5 (MIT); Python 3.12.13 `sqlite3`, `random`, `pathlib`, `contextlib` are stdlib (PSF); SQLite 3.53.1 is public domain. Versions were read from the actual worktree interpreter. No new dependency, lockfile, GEP schema, hashing convention, Attempt system or completion-proof mechanism was introduced.

## Verification scope

Commands use worktree `.venv/Scripts/python.exe`; process-local
`OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=MKL_NUM_THREADS=1` before pytest/type checks.
Current installed versions verified: Python 3.12.13, SQLite 3.53.1, Pydantic 2.13.5.

- Initial corrected domain gate: `python -m pytest tests/swarm/test_ledger.py
  tests/swarm/test_field.py tests/swarm/test_router.py tests/swarm/test_lease.py
  tests/swarm/test_budget.py -q`: 47 passed in 11.14s.
- Final B gate: the same five test files plus `tests/t3/metabolism -q`:
  **60 passed in 21.37s** (47 swarm + 13 legacy metabolism). Two warnings arise
  from deliberately invalid `model_copy` token inputs; both are rejected.
- `python -m mypy --strict swarm/models.py swarm/task_ledger.py swarm/lease.py
  swarm/budget.py swarm/pheromone.py swarm/router.py metabolism`: **11 files clean**.
  The same command with `--platform linux`: **11 files clean**. Linux target type
  checking is not Linux execution evidence.
- Full suite/build/SDK/distribution belong to I and were not run by B.
- Coordinator review added the unbounded-request lower-usage/no-release restart
  regression: `python -m pytest tests/swarm/test_budget.py -q`: **26 passed in
  8.19s**, with the same two expected warnings. Targeted strict models/budget for
  Windows and `--platform linux`: **2 files clean each**. This is a targeted
  follow-up, not a repeated 61-test full gate. B-path `git diff --check` is clean.

These tests execute real local SQLite and subprocess contention, actual terminated
lease owners, Windows junctions and local target writes. Executor usage remains
synthetic; remote Hub/models, provider billing guarantees, Linux process execution,
physical/production evidence and interface_live/task_live remain not_run. All
remote requests, mainline mutations, demo services and global configuration are
outside this delivery. Manual recovery is required for unknown submission effects
or old persisted formats; no migration or deployment was performed.
