# Formal v2 input index

Candidate: `c552250c0d07f5f70f09eb0a5ab3c322195e34ec`.

The exact submitted text is the `content` string in [input.json](review-0929-formal-v2-input.json), decoded once by the existing SDK request script. JSON escaping preserves every source-space and diff line; it is not source normalization. The original raw Markdown representation triggered `git diff --check` on inherited trailing whitespace in copied code/diff. That check failure is retained in the governance report; JSON transport avoids editing source quotations merely for a documentation whitespace gate.

Actual input: 288865 UTF-8 bytes / 288741 Unicode characters. Exact tokens unknown. Byte guard 300000 is NOT a token count. Provider max input=98304 tokens, context=131072, max output=16384.

Included: complete `348cf8d..73e64cc` swarm/orchestration production diff, complete `73e64cc..c552250` production increment, numbered final core excerpts, full three adapters and lease, and seven full tests: unknown_effect_recovery, reservation_cost_state, probe_lifecycle_recovery, rejection_classification_boundaries, rejection_runtime_boundaries, failure_chain_boundaries, failure_chain_runtime. Both complete diff strings were compared directly with git output; see [input check](review-0929-formal-v2-input-check.json).

Excluded: other full test files, unselected unchanged source, documentation/lock/frontend contents. Changed-file lists for both ranges and exact included file:line ranges are part of the decoded input. This is not a full repository or live review. The former 95000-byte partial packet was withdrawn before any model call.
