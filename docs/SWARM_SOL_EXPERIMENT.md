# EvoMap Swarm Scale Experiment

This track evaluates the existing decentralized Worker, SQLite task ledger, lease fencing,
budget ledger, asset approval, and router. It does not replace scheduling, Attempt identity,
hashing, Manifest, completion proof, or the asset system.

## Configured Scales

The CLI accepts only the controlled shapes `3 workers / 6 tasks`, `8 / 48`, and `16 / 96`.
Tasks are deterministic but diversified integer/string data operations. Every task has one
attempt, no derived task, and an immutable standard-library oracle in its acceptance policy.
Workers receive overlapping authorized neighborhoods, so claims contend through the existing
SQLite lease checks rather than using fixed per-worker assignment. The final task depends on
`data-0` and can complete only through the existing approved asset consumption/adoption path.

## Evidence

Each run reports independent process exit codes and PIDs, unique completed task IDs, worker
participation, adoption source/target lineage, router probabilities and history in the existing
routing audit, elapsed request latency, parsed token usage, estimated/billed/unknown cost, and
stop reasons. The report is finite execution evidence for these bounded data tasks, not a
convergence, optimality, throughput, or general coding-agent claim.

Mechanism comparisons use the existing router/field APIs: retained history versus a fresh field,
and member replacement with a new worker identity. Replacement does not inherit identity-local
history automatically; approved assets and task facts remain shared independently.

## Live Gate and Cost

Each worker can be pinned before launch to one of the seven authenticated text model IDs in
`EvoMapTextModel`; no failed task switches model or retries. The first smoke uses three distinct
families, while benchmark runs may represent all seven. Requests go through
`https://api.evomap.ai/v1` using the existing HTTP child. The parent passes only the private
credential-file path and never reads or prints the key. OpenAI rates are not EvoMap evidence.

Live admission remains `request_bound=unbounded`, `provider_enforced=false`, with an explicit
operator allowance only. The default policy still trips the `unknown_cost` breaker. The finite
experiment explicitly enables `allow_unknown_cost`: known valid provider usage may proceed while
cost remains unknown and billed cost remains null, and every full admission hold remains charged
against capacity. Unknown usage, ambiguous remote effect, bound violations, allowance exhaustion,
or provider refusal stop the run. There is no retry, run reset, fallback model, Hub call, or publish.

The synthetic tasks are smoke and contention evidence, not benchmark evidence. Official GSM8K
test and BIG-Bench Hard subsets are separately pinned, sampled, and scored on the same tasks for
homogeneous and heterogeneous pools; the duplicate asset-reuse probe is excluded from accuracy.

Runtime roots and immutable outputs belong under `C:/Users/DW/AppData/Local/Temp/` and are not
committed. Set `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`, and `MKL_NUM_THREADS=1`.
