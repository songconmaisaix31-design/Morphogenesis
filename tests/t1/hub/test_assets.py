import json
from pathlib import Path

import pytest
from bridge_node import NodeAssetBridge
from contracts.resolution import Gene
from hub_client import AssetError, CapsuleEvidence, GenePolicy, HubClient, PublicationRecord, build_assets


def test_official_bundle_and_observed_evidence(record: PublicationRecord, bridge: NodeAssetBridge) -> None:
    gene, capsule = json.loads(record.payload_json)["assets"]
    assert bridge.validate_asset(gene).valid
    assert bridge.validate_asset(capsule).valid
    assert capsule["gene"] == gene["asset_id"]
    assert capsule["outcome"] == {"status": "success", "score": 0.8}
    assert capsule["cost_tokens"] is None and capsule["cost_usd"] is None
    assert capsule["content"]["verification"]["evidence"] == ["fixture://verification"]
    assert record.acceptance.interface_live == "not_run"
    assert record.provenance == "mock"


def test_sdk_rejects_tamper_and_empty_validation(
    gene: Gene, policy: GenePolicy, evidence: CapsuleEvidence, bridge: NodeAssetBridge,
    record: PublicationRecord,
) -> None:
    asset = json.loads(record.payload_json)["assets"][0]
    asset["strategy"] = ["tampered"]
    assert not bridge.validate_asset(asset).valid
    changed = gene.model_dump()
    changed["verification"] = []
    with pytest.raises(AssetError, match="official_asset_validation_failed"):
        build_assets(Gene.model_validate(changed), policy, evidence, bridge)


@pytest.mark.parametrize("change", ["provenance", "unfinished", "reference"])
def test_assembler_rejects_false_claims(
    change: str, gene: Gene, policy: GenePolicy, evidence: CapsuleEvidence, bridge: NodeAssetBridge,
) -> None:
    gene_data = gene.model_dump()
    evidence_data = evidence.model_dump()
    if change == "provenance":
        gene_data["provenance"] = "live"
    elif change == "unfinished":
        evidence_data["result"]["status"] = "pending_review"
    else:
        gene_data["ref"]["asset_id"] = "sha256:" + "0" * 64
    with pytest.raises(AssetError):
        build_assets(Gene.model_validate(gene_data), policy, CapsuleEvidence.model_validate(evidence_data), bridge)


def test_failed_capsule_remains_failed(
    gene: Gene, policy: GenePolicy, evidence: CapsuleEvidence, bridge: NodeAssetBridge,
) -> None:
    data = evidence.model_dump()
    data["result"]["status"] = "failed"
    data["result"]["verdict"].update(passed=False, exit_code=1)
    capsule = build_assets(gene, policy, CapsuleEvidence.model_validate(data), bridge)[1]
    assert capsule["outcome"] == {"status": "failed", "score": 0.8}


def test_prepare_never_overwrites_existing_publication(
    gene: Gene, policy: GenePolicy, evidence: CapsuleEvidence, publication: Path,
) -> None:
    before = publication.read_bytes()
    client = HubClient()
    try:
        with pytest.raises(FileExistsError):
            client.prepare(gene, policy, evidence, artifact_path=publication)
    finally:
        client.close()
    assert publication.read_bytes() == before
