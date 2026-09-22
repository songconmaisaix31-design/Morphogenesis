from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from pydantic import JsonValue

from bridge_node import BridgeError, NodeAssetBridge


def test_sdk_roundtrip_and_canonicalization(
    bridge: NodeAssetBridge, gene: dict[str, JsonValue], capsule: dict[str, JsonValue],
) -> None:
    assert bridge.canonicalize({"z": [True, None], "a": {"中文": "正文", "b": 1}}) == (
        '{"a":{"b":1,"中文":"正文"},"z":[true,null]}'
    )
    for asset in (gene, capsule):
        assert bridge.compute_asset_id(asset) == asset["asset_id"]
        assert bridge.verify_asset_id(asset)
        result = bridge.validate_asset(asset)
        assert result.valid and result.schema_valid and result.asset_id_valid
        assert result.schema_version == "1.14.0"
        assert not result.errors


def test_schema_validation_is_distinct_from_hash(
    bridge: NodeAssetBridge, gene: dict[str, JsonValue],
) -> None:
    tampered: dict[str, JsonValue] = {**gene, "strategy": ["Modified content"]}
    result = bridge.validate_asset(tampered)
    assert result.schema_valid and not result.asset_id_valid and not result.valid
    invalid: dict[str, JsonValue] = {**gene, "constraints": {"max_files": "1", "forbidden_paths": []}}
    invalid["asset_id"] = bridge.compute_asset_id(invalid)
    result = bridge.validate_asset(invalid)
    assert not result.schema_valid and result.asset_id_valid and not result.valid
    assert {issue.keyword for issue in result.errors} >= {"type", "minItems"}
    assert not bridge.verify_asset_id({"asset_id": "sha256:" + "0" * 64})


def test_complete_body_required(bridge: NodeAssetBridge, capsule: dict[str, JsonValue]) -> None:
    del capsule["summary"]
    capsule["asset_id"] = bridge.compute_asset_id(capsule)
    assert not bridge.validate_asset(capsule).schema_valid
    with pytest.raises(BridgeError, match="unsupported_asset_type"):
        bridge.validate_asset({"type": "SomethingElse"})


def test_ambient_credentials_and_node_options_not_inherited(
    bridge: NodeAssetBridge, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NODE_OPTIONS", "--require=/nonexistent/do-not-run.js")
    monkeypatch.setenv("EVOMAP_API_KEY", "sensitive-test-value")
    assert bridge.canonicalize({"ok": True}) == '{"ok":true}'


@pytest.mark.parametrize("value", [float("nan"), float("inf")])
def test_non_json_numbers_rejected(bridge: NodeAssetBridge, value: float) -> None:
    with pytest.raises(BridgeError, match="invalid_json_value"):
        bridge.canonicalize(value)


def test_missing_node_is_not_python_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda _: None)
    with pytest.raises(BridgeError, match="node_unavailable"):
        NodeAssetBridge().compute_asset_id({"a": 1})


@pytest.mark.parametrize(
    ("source", "error"),
    [
        ("process.stdout.write('garbled');", "sdk_invalid_response"),
        ("process.stderr.write('secret-child-data'); process.exit(3);", "sdk_process_failed"),
        ("setTimeout(() => {}, 60000);", "sdk_timeout"),
        ("console.log(JSON.stringify({ok:true,result:123}));", "sdk_invalid_response"),
    ],
)
def test_real_child_failures_are_bounded_and_redacted(tmp_path: Path, source: str, error: str) -> None:
    script = tmp_path / "fake.mjs"
    script.write_text(source, encoding="utf-8")
    client = NodeAssetBridge(timeout_seconds=0.5)
    client._script = script
    with pytest.raises(BridgeError) as caught:
        client.canonicalize({"secret": "secret-request-data"})
    assert caught.value.code == error
    assert "secret" not in str(caught.value)


def test_node_structured_stdin_error() -> None:
    node = shutil.which("node")
    assert node is not None
    script = Path(__file__).resolve().parents[3] / "bridge_node" / "asset_bridge.mjs"
    result = subprocess.run(
        [node, str(script)], input=b"{broken", capture_output=True,
        timeout=10, shell=False, check=False,
    )
    assert result.returncode == 1
    assert json.loads(result.stdout) == {"ok": False, "error": "invalid_json"}
