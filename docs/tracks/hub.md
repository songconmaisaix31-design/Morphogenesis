# H Hub adapter handoff

Owner/write paths: `hub_client/**`, `tests/t1/hub/**`, this document. Dependencies merged from T0 `d0f5ac9` / `32c897a` and T1 bridge `32586be`. No shared contract, lock, bridge, or other worker implementation was edited by H.

## Behavior and API

`HubClient` owns a synchronous httpx client with finite timeouts, no redirects, no inherited proxies, and **one request attempt per operation**. `HubConfig()` defaults to no destination. Configured origins currently accept only literal `127.0.0.1` or `::1`, so no production or external sandbox calls are enabled. `close()` releases its HTTP resources. There is no autonomous registration, heartbeat, task worker, or publishing loop.

- `hello(env_fingerprint=...) -> HelloResult` sends the seven-field `gep-a2a` 1.0.0 envelope. Identity must echo the configured node, not the Hub node. A valid newly returned secret replaces the in-memory `SecretStr`; absent/null secret preserves the old value. Responses expose only a sanitized receipt. `node_secret` returns `SecretStr` for a separately authorized secure-storage caller. The adapter never reads ambient user credentials or writes secrets to disk.
- `build_assets(gene, policy, evidence, bridge)` maps the **full** internal `Gene` to official Gene+Capsule. `GenePolicy` requires category, maximum file count and forbidden paths. `CapsuleEvidence` requires capsule identity, summary, confidence, changed file/line counts, score, `TaskResult`, environment and content. Nonterminal results and mismatched provenance fail. Independent successful verification comes from T0's revalidated `TaskResult`; missing cost remains null. Actual verification, attempt and artifact references are embedded in Capsule content. Gene signals, strategy and validation commands are preserved; `avoid` becomes explicit avoidance preconditions. An existing GeneRef asset ID must match the official assembled body.
- `prepare(gene, policy, evidence, artifact_path=Path(...)) -> PublicationRecord` invokes the real Node bridge for IDs/schema checks and canonicalization, then creates a local JSON record exclusively. It refuses to overwrite any existing record. The caller chooses an isolated, ignored runtime directory; `.runtime/hub/<run>/publication.json` is suitable. SDK failures fail closed; there is no Python schema/hash fallback.
- `PublishApproval(approved_by=..., payload_json=record.payload_json, provenance=record.provenance, original_run_uri=record.original_run_uri, sender_id=config.sender_id, hub_url=config.base_url)` represents the application's explicit approval of this exact stored content, source, identity and destination. **The application owns approval authority and may create this only after its human/automatic gate succeeds**; this data class does not authenticate an approver. There is deliberately no automatic approve-and-publish helper.
- `publish(artifact_path, approval=...) -> PublicationRecord` stays pending without configuration, approval, or secret. Approval mismatch or failed official revalidation sends nothing. A per-file exclusive lock excludes concurrent sends. The record is atomically changed to unknown **before** sending; restart or another call cannot resend a nonpending record. Connect failure returns pending with no automatic retry. Read/write failure, malformed/ambiguous response, redirects and 5xx remain unknown. Explicit rejection becomes rejected. Only explicit receipt status produces received/candidate/promoted; `decision=accepted` means candidate, never promoted. A crash lock needs manual reconciliation; do not remove it or reset unknown without investigating the effect.
- `fetch(signals=..., asset_ids=None) -> FetchResult` accepts complete official assets directly in `assets` or wrapped under `results[].payload`, validates every returned body with the real bridge, and rejects wrong requested IDs. Empty is explicitly empty; malformed/missing/tampered assets fail with no invented results. Discovered means retrieved and locally validated, not locally executed, adopted, or promoted. It does not mutate a prior publication receipt.

The publication record retains the original asset provenance. All network receipts in this version have `Acceptance(provenance="mock", contract_local="passed")`; interface_live/task_live remain not_run even over a real loopback socket. Prepare's local schema evidence also never upgrades live acceptance. No endpoint/credential test against a public Hub occurred.

## Sources, versions and license

Read-only protocol research: [official A2A reference](https://evomap.ai/wiki/05-a2a-protocol), accessed 2026-09-22. The adapter uses the seven envelope fields, hello credential semantics, bundle `payload.assets`, fetch signals/asset_ids, and distinct candidate/promotion lifecycle described there. No documentation or implementation was copied wholesale.

The exact SDK artifact is [`@evomap/gep-sdk` 1.14.0](https://registry.npmjs.org/@evomap/gep-sdk/1.14.0); official source is [EvoMap/gep-sdk-js](https://github.com/EvoMap/gep-sdk-js). Its npm `LICENSE`/`NOTICE` identify code and schemas as **Apache-2.0**, human-readable specification as **CC-BY-4.0**. `NodeAssetBridge` invokes that package and Ajv; H neither copies schemas nor rewrites hash/canonicalization algorithms. Package/lock ownership stays T0.

The locked [`@evomap/gep-mcp-server` 1.7.0](https://registry.npmjs.org/@evomap/gep-mcp-server/1.7.0) `src/protocol.js` documents Capsule outcome normalization to only `status`/`score` before Hub hashing. H verified that installed source and emits exactly those fields; additional narrative/evidence goes in content. MCP is not the Hub HTTP path: bridge owns local official SDK/MCP operations, H owns httpx A2A.

httpx 0.28.1 is BSD-3-Clause; Pydantic 2.13.5 is MIT (T0 locked environment). Only dependency invocation and necessary mapping/HTTP glue are implemented here.

## Verification

Tests use actual locked Node SDK/Ajv schema and hash checks. HTTP fault cases use httpx MockTransport; the end-to-end transport test starts a real ephemeral loopback HTTPServer with fixture data and a fabricated server receipt. This is intentionally **contract_local**, not remote authentication, discoverability, or task acceptance.

Verified on Windows, Python 3.12.13, Node 24.16.0, locked httpx 0.28.1 / Pydantic 2.13.5:

```powershell
npm ci --ignore-scripts
uv tool run poetry install
uv tool run poetry run python -m pytest tests/t1/hub -q
uv tool run poetry run mypy --strict hub_client tests/t1/hub
git diff --check
```

- Node frozen install and Poetry locked install: exit 0.
- Hub tests: **46 passed**, including real SDK positive/negative validation and real loopback hello → publish → fetch. All network data is mock; no live dimension passed.
- Strict mypy over Hub implementation and tests: **8 source files, no issues**.
- Diff whitespace check: exit 0. T0's packaging ownership remains unchanged; package-wide build is handled by T0/integration after registering track packages.

## Remaining limits / integration

- Sandbox URL/credentials are unavailable. External origins intentionally remain disabled; public Hub received/candidate/promoted/discovered and interface_live are **NOT_RUN**.
- Official Hub policy documents validation commands beginning with node/npm/npx, whereas SDK JSON Schema accepts string commands and the internal project uses Python. H preserves actual commands and does not fabricate a Node success command. Passing SDK validation is therefore not a promise of remote policy acceptance; any future sandbox policy adaptation needs explicit evidence.
- Publication state prevents retries **per retained local artifact**; callers must retain that path and must not duplicate unknown publications into fresh pending files. No global scheduler, dedup registry, custom manifest, or completion-proof infrastructure was added.
- Evidence models validate structure and internal consistency, not truth of arbitrary caller assertions. The caller owns actual measurements and the approval gate. File/lock state is intended for trusted local application storage, not adversarial multi-user access.
- T0 must include `hub_client` in packaging/configured mypy scope; dependency handoff sent. The adapter itself requires no new third-party dependency.
