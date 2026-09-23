# Swarm corrected v0.2 contracts

Owner B; proposal accepted by coordinator and A on 2026-09-23 and delivered to C
before runtime execution. C acknowledges via mailbox. This replaces the old
radius/file-lock/account contract, while preserving the historical implementation.

## Task authority and locality

- `TaskLedger(path, swarm_id, *, limits=RunLimits(), clock=time.time, timeout_seconds=10)`:
  one SQLite WAL database for tasks, dependencies, attempts, claims, result intents,
  result acceptance and append-only audit. All participants use the same database
  and swarm ID. JSONL is an explicit audit export, never an authority.
- `enqueue(signal: Signal, *, dependencies: tuple[str, ...]=(), acceptance:
  dict[str, JsonValue] | None=None, evidence_key: str | None=None,
  derived_from: str | None=None) -> TaskRecord`. Identity and task content are
  immutable; duplicate evidence keys merge into the existing task without a new
  attempt/task or stronger pheromone. Dependencies must already exist.
- `get(task_id) -> TaskRecord`; `candidates(locality, *, limit=100,
  include_blocked=False, capabilities: tuple[str,...] | None=None) -> list[TaskRecord]`;
  `snapshot(*, limit=100) -> list[TaskRecord]`; `audit(*, limit=100) -> list[dict]`.
- `Locality(workspace, authorized_scopes=(), modules=(), dependency_of=())`.
  Empty scope authorization returns no candidates. Scopes are resolved backend
  paths within workspace, including symlink/case normalization. Module/dependency
  neighborhood further narrows authorization. Legacy x/y/radius fields carry no
  routing or authority semantics. Bounded SQL filters precede reading task bodies.
- `RunLimits(max_tasks=1000, max_attempts=10000, max_attempts_per_task=3,
  max_derived_tasks=100, max_runtime_seconds=3600)` is immutable per swarm.

## Claims and publication

- `LeaseManager(ledger: TaskLedger)` delegates `acquire(task_id, worker_id, *,
  ttl_seconds=30, locality: Locality) -> Lease | None`, `renew(lease, *,
  ttl_seconds=30) -> Lease | None`, `release(lease) -> bool`, `is_valid(lease) -> bool`,
  `snapshot() -> list[Lease]` and `submit` below. `TaskLedger.claim` is the same
  acquire implementation. Worker capabilities must be filtered by the router;
  authorization, dependencies, status and scope overlap are checked atomically.
- `Lease(task_id, swarm_id, scope, worker_id, token: int, expires_at)`: token grows
  monotonically per task and never resets on release/expiry. Renew/release validate
  the persisted owner, token, exact current expiry and live TTL. Sibling scopes may
  run concurrently; parent/child and aliases conflict.
- `submit(lease, result_id: str, result: dict[str, JsonValue], *,
  apply: Callable[[Callable[[], None]], None] | None=None) -> TaskRecord`.
  Same completed owner/token/result is idempotent; conflicting results and stale
  generations reject before invoking apply. Without an effect, completion is one
  short transaction. With an effect, persist a `submitting` intent first, then
  fence a short prepared publication in a second transaction. A's callback receives
  `assert_owned()` and checks it immediately before each isolated-target write.
  Callback preparation, model calls, tests and git operations occur outside this
  transaction. Callback returns None; prepared result metadata is supplied up front.
  Crash/exception after intent leaves `submitting`, blocks overlapping scope and
  automatic reclaim/replay, and requires manual recovery of potentially partial
  filesystem effects. SQLite does not provide a multi-file filesystem transaction.
  `TaskRecord.effect_applied` is authoritative: false without a callback, true only
  after the callback and final ownership check succeed. Arbitrary `result.applied`
  metadata cannot set it. A additionally verifies target bytes before adoption.
- `fail(lease, evidence: dict[str, JsonValue]) -> TaskRecord` preserves an attempt
  outcome and releases to available (or failed at attempt limit); it never completes
  or deletes the task. Result acceptance is an explicit submitted fact.

## Field and router

- `PheromoneField(path, *, ledger: TaskLedger, tau_seconds=86400, alpha=0.05,
  clock=time.time)`. Decay is `rho(dt)=1-exp(-dt/tau)`; alpha is independent.
  Existing deposit/feedback/history interfaces remain. `deposit` enqueues through
  the ledger; `sense` uses ledger locality; only fenced `submit` completes a task.
  `complete` is removed. Task facts never decay.
- `Router(field, *, beta=1, rng=None, exploration=0.05, aging_seconds=86400)`;
  `choose(worker_id, locality, capabilities) -> Signal | None`;
  `reinforce(worker_id, signal, *, success, speedup=0, token_saving=0)`.
  Exact exploitation score is `beta*w_history*concentration*match*urgency`.
  Urgency includes bounded age; exploration mixes normalized age weights with the
  normalized softmax. Persist filter reasons, history, signals, both probabilities
  and final selection as a routing audit. All local inputs are bounded.

## Budget

- `BudgetLedger(path, swarm_id, policy: BudgetPolicy, *, clock=time.time)`;
  `reserve(worker_id, task_id, bound: ExecutionBound, *, request_id: str | None=None)
  -> Reservation`;
  `settle(reservation, usage: JsonValue) -> BudgetSnapshot`;
  `mark_uncertain(reservation)`; `snapshot(worker_id=None)`;
  `pending(worker_id: str, *, limit=100) -> list[Reservation]` (max 1000).
  Reservations and breakers are swarm-run scoped, never account-wide guarantees.
  `pending` reads authoritative in-flight holds without changing them, including
  the crash window after reserve commit and before any worker status file. C calls
  it on proven owner recovery and marks those holds uncertain; it does not mark a
  live owner's requests merely because they are observed.
  Use existing AttemptId or task ID plus integer fence for request identity. A new
  identity is allowed after a known settled failure; the same request is never
  reserved again. A pending/uncertain request for that task blocks a new identity.
- `BudgetPolicy` retains explicit prices, token and burn limits, adds `limits:
  RunLimits` and `admission_control: enabled|disabled` (default enabled).
- `ExecutionBound` retains token fields; adds `request_bound: verified|unbounded`
  (default unbounded), `max_cost_usd: float | None`, `bound_evidence: str | None`.
  A verified request bound requires explicit trusted executor evidence and a
  contractual monetary upper bound, not just `provider_enforced=True` or prices.
  Unbounded requests can only make an estimated admission-control claim.
- Persist and expose `usage_metering: verified|unknown`, `request_bound:
  verified|unbounded`, `admission_control: enabled|disabled`, `cost:
  estimated|billed|unknown`. Parsed synthetic usage is contract-local evidence;
  estimated costs are never invoices. Missing/malformed usage retains its full
  reservation and trips the shared breaker; unknown holds never expire/retry.
  Settled usage plus pending/unknown reservation plus a new reservation must fit
  the configured admission ceiling. Limits persist across restarts.
  Without a bill, every request retains `max(original_reservation, usage_estimate)`
  as its conservative admission debit, including unbounded requests. Snapshot
  `admission_charged_usd` and `unreconciled_reservations` expose this separately from
  pending holds and measured usage estimates. A lower estimate never creates new
  allowance. The current adapter never emits `billed` or a non-null actual cost.
  Breaker priority is unknown usage, then request-bound violation, then admission
  exhaustion. A known valid final-credit request may complete its fenced result;
  a simultaneous/later bound violation is never hidden behind exhaustion.

## A/C integration agreement

A's `AssetApplicator.prepare` runs before submit; `PreparedApplication.apply` runs
in the submit callback and C checks its scope is contained in the task lease.
Approval runs only after completed submission; adoption additionally reads
`TaskLedger.get` and checks `effect_applied`, swarm/task/owner/token/result ID and
target bytes. `ConsumptionContext` carries `swarm_id=lease.swarm_id`, `task_id`,
`worker_id`, `fencing_token`, `execution_id`, `scope`, `capabilities`,
`completed_dependencies`, and `input_context` (A owns exact asset model types).

Legacy field/account databases are rejected for explicit migration, preserving
historical data and unknown holds; they are not silently reset or reinterpreted.
New fixture runs use an explicitly separate state directory and swarm identity.

Evidence remains contract_local unless separately measured; no remote model or Hub
calls are authorized for B. A/C own their respective filesystem/runtime boundaries.
