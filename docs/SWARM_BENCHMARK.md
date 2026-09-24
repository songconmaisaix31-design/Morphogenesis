# Common-Benchmark Swarm Protocol

This track compares homogeneous and heterogeneous worker pools using original public benchmarks. It is not evidence of a single-agent capability result, a causal routing advantage, a general algorithm advantage, or a reproduction of a full official leaderboard.

## Sources and Selection

| Source | Immutable revision | Files | License |
| --- | --- | --- | --- |
| GSM8K, OpenAI grade-school-math | `3101c7d5072418e28b9008a6636bde82a006892c` | `grade_school_math/data/test.jsonl` | MIT |
| BIG-Bench Hard, suzgunmirac/BIG-Bench-Hard | `9ee07bd481feebf959a6b59d61ea57bdcf30964d` | `bbh/logical_deduction_three_objects.json`, `bbh/multistep_arithmetic_two.json`, `bbh/boolean_expressions.json` | MIT |

`tools/run_swarm_benchmark.py --download` obtains these exact commits into a task-specific directory outside Git, then verifies each checkout with `git rev-parse HEAD` and rejects any dirty or untracked source files. The default fixed seed is `20260924`. The initial 48-item stratified subset contains 24 GSM8K test rows and 8 rows from each confirmed BBH file; its public manifest records only source revisions, seed, count, and sample IDs, never questions or gold answers.

The 16-member extension contains the original 48 plus 48 new, non-overlapping examples selected with the same seeded procedure and explicitly reports the overlap. The complete per-run selection, question order, prompt, and output limit are identical between conditions. Dataset questions and immutable gold answers are loaded only for task payload seeding and independent acceptance policy; gold never enters a model prompt, model payload, request artifact, or public manifest.

## Conditions

The first approved experiment has eight members and 48 tasks:

| Condition | Worker models |
| --- | --- |
| Homogeneous baseline | Eight fixed `evomap-gpt-5.6-sol` members |
| Heterogeneous pool | Eight fixed members covering DeepSeek V4 Flash, Gemini 3.1 Pro Preview, GLM 5.1, GLM 5.2, GPT 5.6 Luna, Sol, and Terra; one selected model repeats |

The permitted extension is 16 members and 96 tasks, covering all seven available text models. Each member has a fixed requested model before the run; record both requested and returned model per request. Do not silently fall back, automatically retry, replace a rejected model, or rerun a condition to hide failures. Generic swarm behavior, fixed worker/task scale, budget reservations, state reset, worker history, replacement evidence, and smoke gating remain owned by the generic runtime track.

The execution payload asks for exactly `{"answer":"...","adopted_asset_ids":[]}` to satisfy the existing executor schema while explicitly forbidding benchmark-task adoption. The pool comparison remains decentralized: assignments can be unequal, so per-model accuracy is descriptive only. Any exact-answer reuse probe is a separately labelled experiment and is excluded from the benchmark denominator.

## Scoring and Reporting

GSM8K gold is extracted only from the official final `####` marker and scored with finite numeric normalization (`Decimal`, allowing commas, dollar markers, and equivalent numeric notation). BBH compares the whitespace-trimmed answer against the exact case-sensitive official target. The constrained response contract is strictly a JSON object with the string field `answer` and an empty `adopted_asset_ids` array; malformed JSON, extra fields, non-string answers, nonempty reuse declarations, and missing responses fail that contract.

Report standard normalized correctness and strict JSON-contract compliance separately when relevant. Accuracy always uses every requested sample as denominator: correct, incorrect, malformed, missing, and duplicate responses are distinct counts. Do not report completed-only accuracy. Request IDs are deduplicated before aggregation; report requested/returned model, HTTP status, latency, stop reason, token total when known plus known subtotal otherwise, and billed cost as `null` when unavailable. Preserve unknown usage and cost as unknown rather than zero.

The protocol is a zero-shot, JSON-constrained subset and therefore differs from original GSM8K/BBH papers and leaderboard protocols. A runtime acceptance rule that requires cross-member asset adoption can be blocked for independently scored benchmark tasks; benchmark accuracy must still be reported independently and must not fake adoption.

## Executed 8x48 Evidence

On 2026-09-24, after the bounded live interface had been authorized, two fresh 8-worker, 48-task, one-attempt conditions ran against the pinned 48-item selection. Both used `allow_unknown_cost=true`, explicit unbounded reservation admission, the same private credential-file route, no retries, no model fallback, and no task adoption. All eight worker processes exited `0` in each condition. The source state and aggregate results are retained outside Git; the paths below contain request/response evidence, audit records, and immutable acceptance records, including the gold values that must not be published.

| Condition | Correct | Incorrect | Malformed | Missing | Duplicate | Accuracy | Strict JSON rate | Requests | Known provider tokens | Billed cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Eight fixed Sol workers | 25 | 21 | 0 | 2 | 0 | 52.08% | 95.83% | 48 | 12,304 of 46 known-usage requests | `null` / unknown |
| Eight fixed heterogeneous workers | 30 | 15 | 2 | 1 | 0 | 62.50% | 93.75% | 48 | 18,454 of 48 requests | `null` / unknown |

The heterogeneous pool used DeepSeek V4 Flash, Gemini 3.1 Pro Preview, GLM 5.1, GLM 5.2, GPT 5.6 Luna, Sol, Terra, and a second fixed Sol worker. Assignment is decentralized and unequal, so these rows are descriptive rather than a balanced model comparison. Names below are the returned provider model identifiers when available.

| Returned model | Requested samples | Correct | Incorrect | Malformed | Missing | Accuracy | Strict JSON rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `deepseek-v4-flash-0731` | 6 | 3 | 2 | 0 | 1 | 50.00% | 83.33% |
| `gemini-3.1-pro-preview` | 5 | 5 | 0 | 0 | 0 | 100.00% | 100.00% |
| `glm-5.1` | 5 | 3 | 0 | 2 | 0 | 60.00% | 60.00% |
| `glm-5.2` | 5 | 5 | 0 | 0 | 0 | 100.00% | 100.00% |
| `gpt-5.6-luna` | 7 | 6 | 1 | 0 | 0 | 85.71% | 100.00% |
| `gpt-5.6-sol` | 14 | 5 | 9 | 0 | 0 | 35.71% | 100.00% |
| `gpt-5.6-terra` | 6 | 3 | 3 | 0 | 0 | 50.00% | 100.00% |

The two malformed heterogeneous responses came from `glm-5.1`; they remain malformed under the strict response contract and were not repaired or retried. The Sol condition's two missing responses had no returned model or provider usage, so they remain in its full 48-sample denominator rather than in the 46 returned-Sol descriptive rows. No provider billed-cost field was supplied, so cost is retained as unknown rather than estimated or zero.

Aggregate outputs and state roots are:

| Condition | Aggregate output | State root |
| --- | --- | --- |
| Eight fixed Sol workers | `C:/Users/DW/AppData/Local/Temp/morph-benchmark-8x48-sol-result.json` | `C:/Users/DW/AppData/Local/Temp/morph-benchmark-8x48-sol/state` |
| Eight fixed heterogeneous workers | `C:/Users/DW/AppData/Local/Temp/morph-benchmark-8x48-hetero-result.json` | `C:/Users/DW/AppData/Local/Temp/morph-benchmark-8x48-hetero/state` |

The first direct invocation stopped before configuration parsing or any provider request because the workspace was absent from `PYTHONPATH` (`ModuleNotFoundError: swarm`). The authorized live invocations were then run once with `PYTHONPATH` explicitly set to the workspace. This was a local launch correction, not a remote retry; the two reported conditions are the only paid benchmark executions. The optional 16x96 extension was not run.
