"""Translate internal contracts, delegating all schema/hash work to the official SDK."""

from pydantic import JsonValue

from bridge_node.assets import NodeAssetBridge
from contracts.resolution import Gene
from hub_client.models import CapsuleEvidence, GenePolicy


class AssetError(ValueError):
    pass


def build_assets(
    gene: Gene, policy: GenePolicy, evidence: CapsuleEvidence, bridge: NodeAssetBridge,
    *, for_proxy: bool = False,
) -> list[dict[str, JsonValue]]:
    # Revalidate caller models: frozen Pydantic models still contain mutable lists.
    gene = Gene.model_validate(gene.model_dump())
    evidence = CapsuleEvidence.model_validate(evidence.model_dump())
    policy = GenePolicy.model_validate(policy.model_dump())
    result = evidence.result
    if gene.provenance != result.provenance:
        raise AssetError("gene_result_provenance_mismatch")
    if result.status not in {"succeeded", "failed"}:
        raise AssetError("capsule_requires_observed_terminal_result")
    if for_proxy and (
        not evidence.event_id or not evidence.model_name or not evidence.returned_model_name
        or not evidence.gateway_response_id or evidence.files_changed <= 0
        or evidence.lines_changed <= 0 or evidence.score < 0.7 or result.status != "succeeded"
    ):
        raise AssetError("proxy_bundle_requires_observed_effect_and_model_lineage")
    if for_proxy and (not policy.validation_commands or any(
        not command.startswith(("node ", "npm ", "npx ")) for command in policy.validation_commands
    )):
        raise AssetError("proxy_requires_explicit_node_validation_commands")
    official_gene: dict[str, JsonValue] = {
        "type": "Gene", "schema_version": "1.14.0", "id": gene.ref.gene_id,
        "category": policy.category, "signals_match": list(gene.signals_match),
        "strategy": list(gene.strategy),
        "constraints": {"max_files": policy.max_files, "forbidden_paths": list(policy.forbidden_paths)},
        "validation": list(gene.verification),
        "preconditions": ["Avoid: " + item for item in gene.avoid],
    }
    if for_proxy:
        # The live Hub requires summary although SDK 1.14 permits its absence.
        official_gene["summary"] = evidence.summary
        official_gene["validation"] = list(policy.validation_commands or [])
    official_gene["asset_id"] = bridge.compute_asset_id(official_gene)
    if gene.ref.asset_id is not None and gene.ref.asset_id != official_gene["asset_id"]:
        raise AssetError("gene_reference_asset_id_mismatch")
    capsule: dict[str, JsonValue] = {
        "type": "Capsule", "schema_version": "1.14.0", "id": evidence.capsule_id,
        "gene": official_gene["asset_id"], "trigger": list(gene.signals_match),
        "summary": evidence.summary, "confidence": evidence.confidence,
        "blast_radius": {"files": evidence.files_changed, "lines": evidence.lines_changed},
        "outcome": {"status": "success" if result.status == "succeeded" else "failed", "score": evidence.score},
        "env_fingerprint": evidence.env_fingerprint,
        "content": {
            "details": evidence.content, "source_attempt": result.attempt.model_dump(mode="json"),
            "verification": result.verdict.model_dump(mode="json"), "artifact_uri": result.artifact_uri,
        },
        "cost_tokens": result.usage.tokens, "cost_usd": result.usage.cost_usd,
    }
    if for_proxy:
        # Keep local paths and reviewer evidence in the caller's TaskResult.
        # Only explicitly selected public details leave the workstation.
        capsule["content"] = {
            "details": evidence.content, "source_attempt": result.attempt.model_dump(mode="json"),
            "verification": {"passed": result.verdict.passed, "exit_code": result.verdict.exit_code},
            "local_evidence_redacted": True,
            "model_name": evidence.model_name, "returned_model_name": evidence.returned_model_name,
        }
        capsule["env_fingerprint"] = {**evidence.env_fingerprint, "model_name": evidence.model_name}
        capsule["trigger_context"] = {"agent_model": evidence.model_name}
        # Hub substance checks do not count object-valued evidence metadata.
        capsule["strategy"] = list(gene.strategy)
    capsule["asset_id"] = bridge.compute_asset_id(capsule)
    assets = [official_gene, capsule]
    if for_proxy:
        event: dict[str, JsonValue] = {
            "type": "EvolutionEvent", "schema_version": "1.14.0", "id": evidence.event_id,
            "intent": policy.category, "signals": list(gene.signals_match),
            "genes_used": [official_gene["asset_id"]], "mutation_id": result.task_id,
            "blast_radius": capsule["blast_radius"], "outcome": capsule["outcome"],
            "capsule_id": capsule["asset_id"], "source_type": "generated",
            "meta": {"source_attempt": result.attempt.model_dump(mode="json"),
                     "model_name": evidence.model_name, "returned_model_name": evidence.returned_model_name},
        }
        event["asset_id"] = bridge.compute_asset_id(event)
        assets.append(event)
    validate_bundle(assets, bridge, for_proxy=for_proxy)
    return assets


def validate_bundle(
    assets: list[dict[str, JsonValue]], bridge: NodeAssetBridge, *, for_proxy: bool = False,
) -> None:
    expected = ["Gene", "Capsule", "EvolutionEvent"] if for_proxy else ["Gene", "Capsule"]
    if [a.get("type") for a in assets] != expected:
        raise AssetError("gene_capsule_bundle_required")
    if assets[1].get("gene") != assets[0].get("asset_id"):
        raise AssetError("capsule_gene_link_mismatch")
    for asset in assets:
        if not bridge.validate_asset(asset).valid:
            raise AssetError("official_asset_validation_failed")
    if for_proxy:
        capsule, event = assets[1:]
        if event.get("genes_used") != [assets[0]["asset_id"]] or event.get("capsule_id") != capsule["asset_id"]:
            raise AssetError("event_link_mismatch")
        for item in (capsule, event):
            radius, outcome = item.get("blast_radius"), item.get("outcome")
            if not isinstance(radius, dict) or not isinstance(outcome, dict):
                raise AssetError("proxy_bundle_quality_gate_failed")
            files, lines, score = radius.get("files"), radius.get("lines"), outcome.get("score")
            if (not isinstance(files, int) or files <= 0
                or not isinstance(lines, int) or lines <= 0
                or not isinstance(score, (float, int)) or score < 0.7
                or outcome.get("status") != "success"):
                raise AssetError("proxy_bundle_quality_gate_failed")
