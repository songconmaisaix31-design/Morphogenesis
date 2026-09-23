# Common-Benchmark Swarm Protocol

This track compares homogeneous and heterogeneous worker pools using original public benchmarks. It is not evidence of a single-agent capability result, a causal routing advantage, a general algorithm advantage, or a reproduction of a full official leaderboard.

## Sources and Selection

| Source | Immutable revision | Files | License |
| --- | --- | --- | --- |
| GSM8K, OpenAI grade-school-math | `3101c7d5072418e28b9008a6636bde82a006892c` | `grade_school_math/data/test.jsonl` | MIT |
| BIG-Bench Hard, suzgunmirac/BIG-Bench-Hard | `9ee07bd481feebf959a6b59d61ea57bdcf30964d` | `bbh/logical_deduction_three_objects.json`, `bbh/multistep_arithmetic_two.json`, `bbh/boolean_expressions.json` | MIT |

`tools/run_swarm_benchmark.py --download` obtains these exact commits into a task-specific directory outside Git, then verifies each checkout with `git rev-parse HEAD`. The default fixed seed is `20260924`. The initial 48-item stratified subset contains 24 GSM8K test rows and 8 rows from each confirmed BBH file; its public manifest records only source revisions, seed, count, and sample IDs, never questions or gold answers.

The 16-member extension contains the original 48 plus 48 new, non-overlapping examples selected with the same seeded procedure and explicitly reports the overlap. The complete per-run selection, question order, prompt, and output limit are identical between conditions. Dataset questions and immutable gold answers are loaded only for task payload seeding and independent acceptance policy; gold never enters a model prompt, model payload, request artifact, or public manifest.

## Conditions

The first approved experiment has eight members and 48 tasks:

| Condition | Worker models |
| --- | --- |
| Homogeneous baseline | Eight fixed `evomap-gpt-5.6-sol` members |
| Heterogeneous pool | Eight fixed members covering DeepSeek V4 Flash, Gemini 3.1 Pro Preview, GLM 5.1, GLM 5.2, GPT 5.6 Luna, Sol, and Terra; one selected model repeats |

The permitted extension is 16 members and 96 tasks, covering all seven available text models. Each member has a fixed requested model before the run; record both requested and returned model per request. Do not silently fall back, automatically retry, replace a rejected model, or rerun a condition to hide failures. Generic swarm behavior, fixed worker/task scale, budget reservations, state reset, worker history, replacement evidence, and smoke gating remain owned by the generic runtime track.

The execution payload asks for exactly `{"answer":"..."}`. The pool comparison remains decentralized: assignments can be unequal, so per-model accuracy is descriptive only. Any exact-answer reuse probe is a separately labelled experiment and is excluded from the benchmark denominator.

## Scoring and Reporting

GSM8K gold is extracted only from the official final `####` marker and scored with numeric normalization (`Decimal`, allowing commas, dollar markers, and equivalent numeric notation). BBH compares the whitespace-trimmed answer against the exact case-sensitive official target. The constrained response contract is strictly a JSON object with exactly one string field, `answer`; malformed JSON, extra fields, non-string answers, and missing responses fail that contract.

Report standard normalized correctness and strict JSON-contract compliance separately when relevant. Accuracy always uses every requested sample as denominator: correct, incorrect, malformed, missing, and duplicate responses are distinct counts. Do not report completed-only accuracy. Request IDs are deduplicated before aggregation; report requested/returned model, HTTP status, latency, stop reason, token total when known plus known subtotal otherwise, and billed cost as `null` when unavailable. Preserve unknown usage and cost as unknown rather than zero.

The protocol is a zero-shot, JSON-constrained subset and therefore differs from original GSM8K/BBH papers and leaderboard protocols. A runtime acceptance rule that requires cross-member asset adoption can be blocked for independently scored benchmark tasks; benchmark accuracy must still be reported independently and must not fake adoption.
