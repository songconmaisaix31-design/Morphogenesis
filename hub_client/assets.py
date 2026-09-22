"""Translate internal contracts, delegating all schema/hash work to the official SDK."""

from pydantic import JsonValue

from bridge_node.assets import NodeAssetBridge
from contracts.resolution import Gene
from hub_client.models import CapsuleEvidence, GenePolicy


class AssetError(ValueError):
    pass


def build_assets(
    gene: Gene, policy: GenePolicy, evidence: CapsuleEvidence, bridge: NodeAssetBridge,
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
    official_gene: dict[str, JsonValue] = {
        "type": "Gene", "schema_version": "1.14.0", "id": gene.ref.gene_id,
        "category": policy.category, "signals_match": list(gene.signals_match),
        "strategy": list(gene.strategy),
        "constraints": {"max_files": policy.max_files, "forbidden_paths": list(policy.forbidden_paths)},
        "validation": list(gene.verification),
        "preconditions": ["Avoid: " + item for item in gene.avoid],
    }
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
    capsule["asset_id"] = bridge.compute_asset_id(capsule)
    assets = [official_gene, capsule]
    validate_bundle(assets, bridge)
    return assets


def validate_bundle(assets: list[dict[str, JsonValue]], bridge: NodeAssetBridge) -> None:
    if len(assets) != 2 or [a.get("type") for a in assets] != ["Gene", "Capsule"]:
        raise AssetError("gene_capsule_bundle_required")
    if assets[1].get("gene") != assets[0].get("asset_id"):
        raise AssetError("capsule_gene_link_mismatch")
    for asset in assets:
        if not bridge.validate_asset(asset).valid:
            raise AssetError("official_asset_validation_failed")
