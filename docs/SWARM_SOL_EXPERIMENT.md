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

## Heterogeneous Smoke Result

Two immutable `3 workers / 6 tasks` live smokes used fixed DeepSeek v4 Flash, Gemini 3.1 Pro
Preview, and GLM 5.1 workers. Both runs passed the live interface gate but blocked the task-live
gate with four promoted tasks. They are structured-output compliance findings, not benchmark
accuracy results. Neither run retried, changed a worker's model, reset state, called Hub, or
published an asset.

The first run recorded five audited requests and 2,176 provider-reported tokens. GLM 5.1 returned
HTTP 200 and a semantically valid `DataProposal` wrapped in a complete Markdown `json` fence. The
then-current bare-JSON parser rejected it as `data_proposal_rejected` / `candidate_missing`, so
`data-4` failed after its only attempt and dependent reuse task `data-5` remained unavailable.
The result was 4/6 promotions, process exit codes `[0, 0, 1]`, and no adoption. Its state is:

`C:/Users/DW/AppData/Local/Temp/morph-hetero-smoke-20260924/state`

Commit `b60d507` accepts only a complete fenced JSON document, with an optional `json` tag and no
surrounding prose. It does not extract arbitrary substrings. The authorized patched smoke then
recorded five audited requests and 1,659 provider-reported tokens. The fence case passed, but
DeepSeek v4 Flash returned HTTP 200 with three concatenated JSON values: a valid `DataProposal`,
an empty array, and the same `DataProposal` again. The exactly-one-document parser correctly
rejected this ambiguous output as `data_proposal_rejected` / `candidate_missing`; `data-0` failed
after its only attempt and dependent `data-5` did not run. The final result was 4/6 promotions,
process exit codes `[1, 0, 0]`, participation by all three worker PIDs, and no adoption. Its state
is:

`C:/Users/DW/AppData/Local/Temp/morph-hetero-smoke-patched-20260924/state`

The accepted conclusion is to retain this second 4/6 result as the honest heterogeneous-model
structured-output compliance finding. Selecting one value from concatenated documents could hide
conflicting outputs and would weaken the exact `DataProposal` boundary. No further paid smoke is
part of this track.

Commit `05175d8` contains the optional validated `capability_names` override and effective-model
price binding. Mixed-model runs cannot apply the configured model's prices to different effective
worker models; without verified per-model EvoMap prices they require explicit unknown-cost
authorization and retain every financial admission hold.

Runtime roots and immutable outputs belong under `C:/Users/DW/AppData/Local/Temp/` and are not
committed. Set `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`, and `MKL_NUM_THREADS=1`.
