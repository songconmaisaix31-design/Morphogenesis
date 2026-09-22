from __future__ import annotations

import pytest
from pydantic import JsonValue

from bridge_node import NodeAssetBridge


@pytest.fixture
def bridge() -> NodeAssetBridge:
    return NodeAssetBridge()


@pytest.fixture
def gene(bridge: NodeAssetBridge) -> dict[str, JsonValue]:
    # Synthetic body, confined to local contract tests; not a publishing fixture.
    asset: dict[str, JsonValue] = {
        "type": "Gene", "schema_version": "1.14.0", "id": "gene_local_fixture",
        "category": "repair", "signals_match": ["log_error"],
        "strategy": ["Inspect the failing fixture", "Correct its bounded behavior"],
        "constraints": {"max_files": 1, "forbidden_paths": [".git"]},
        "validation": ["python -m pytest"], "summary": "Local bridge test only",
    }
    asset["asset_id"] = bridge.compute_asset_id(asset)
    return asset


@pytest.fixture
def capsule(bridge: NodeAssetBridge, gene: dict[str, JsonValue]) -> dict[str, JsonValue]:
    asset: dict[str, JsonValue] = {
        "type": "Capsule", "schema_version": "1.14.0", "id": "capsule_local_fixture",
        "trigger": ["log_error"], "gene": gene["id"],
        "summary": "Synthetic local SDK boundary fixture, never published",
        "confidence": 0.5, "blast_radius": {"files": 1, "lines": 2},
        "outcome": {"status": "success", "score": 0.5},
    }
    asset["asset_id"] = bridge.compute_asset_id(asset)
    return asset
