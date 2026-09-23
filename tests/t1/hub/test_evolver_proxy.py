import json
import time
from pathlib import Path

import httpx
import pytest
from pydantic import SecretStr, ValidationError

from hub_client import CapsuleEvidence, HubClient, HubConfig, HubError, PublishApproval
from hub_client.assets import AssetError
from contracts.resolution import GeneRef
from metabolism.models import UseRecord

ORIGIN = "http://127.0.0.1:19820"
TOKEN = "local-fixture-ipc-token"


def proxy_config(**changes):
    return HubConfig(base_url=ORIGIN, source="evolver_proxy", proxy_token=SecretStr(TOKEN), **changes)


def proxy_evidence(evidence):
    return evidence.model_copy(update={"event_id": "event_fixture", "model_name": "requested-model-fixture",
                                       "returned_model_name": "returned-model-fixture", "gateway_response_id": "response-fixture"})


def proxy_policy(policy):
    # Schema fixture only; no execution claim is made by these MockTransport tests.
    return policy.model_copy(update={"validation_commands": ["node --check sample.js"]})


def approval(record, config):
    return PublishApproval(approved_by="contract-fixture", payload_json=record.payload_json,
                           provenance=record.provenance, original_run_uri=record.original_run_uri,
                           sender_id=config.sender_id, hub_url=config.base_url)


def test_proxy_keeps_literal_loopback_and_separates_credentials():
    with pytest.raises(ValidationError):
        proxy_config(node_secret=SecretStr("not-an-ipc-token"))
    with pytest.raises(ValidationError):
        HubConfig(base_url="https://evomap.ai", source="evolver_proxy")
    with pytest.raises(ValidationError):
        HubConfig(transport_provenance="live")
    assert TOKEN not in proxy_config().model_dump_json()


@pytest.mark.parametrize("commands", [None, ["Fixed sample acceptance passed"], ["python -m pytest"]])
def test_proxy_does_not_treat_descriptive_verification_as_commands(commands, gene, policy, evidence, tmp_path):
    client = HubClient(proxy_config())
    try:
        with pytest.raises(AssetError, match="explicit_node_validation_commands"):
            client.prepare(gene, policy.model_copy(update={"validation_commands": commands}),
                           proxy_evidence(evidence), artifact_path=tmp_path / "invalid.json")
        assert not (tmp_path / "invalid.json").exists()
    finally:
        client.close()


def test_proxy_hello_checks_existing_status_without_remote_registration():
    seen = []
    config = proxy_config()
    def transport(request):
        seen.append(request)
        assert request.method == "GET" and request.url.path == "/proxy/status"
        assert request.headers["authorization"] == "Bearer " + TOKEN
        assert request.headers["x-evomap-expected-hub-mode"] == "public"
        return httpx.Response(200, json={"running": True, "node_id": config.sender_id,
                                        "hub_mode": "public", "hub_auth_status": "ok"})
    client = HubClient(config, transport=httpx.MockTransport(transport))
    try:
        result = client.hello(env_fingerprint={})
        assert result.state == "acknowledged" and result.source == "evolver_proxy"
        assert result.acceptance.provenance == "mock"
        assert result.acceptance.interface_live == "not_run"
        assert client.node_secret is None and len(seen) == 1
    finally:
        client.close()


def test_proxy_bundle_uses_official_event_schema_and_excludes_local_paths(gene, policy, evidence, bridge, tmp_path):
    client = HubClient(proxy_config(), bridge=bridge)
    try:
        result = client.prepare(gene, proxy_policy(policy), proxy_evidence(evidence), artifact_path=tmp_path / "bundle.json")
    finally:
        client.close()
    assets = json.loads(result.payload_json)["assets"]
    assert [a["type"] for a in assets] == ["Gene", "Capsule", "EvolutionEvent"]
    assert all(bridge.validate_asset(a).valid for a in assets)
    assert assets[0]["summary"] == evidence.summary
    assert assets[0]["validation"] == ["node --check sample.js"]
    assert assets[2]["capsule_id"] == assets[1]["asset_id"]
    assert assets[2]["genes_used"] == [assets[0]["asset_id"]]
    assert assets[1]["content"]["model_name"] == "requested-model-fixture"
    assert assets[1]["content"]["returned_model_name"] == "returned-model-fixture"
    assert assets[1]["strategy"] == list(gene.strategy)
    assert "artifact_uri" not in assets[1]["content"]
    assert "response-fixture" not in result.payload_json
    assert "fixture://verification" not in result.payload_json
    assert result.source == "evolver_proxy"


@pytest.mark.parametrize("reply", ["accepted", "queued", "missing-id", "wrong-id", "disconnect", "rejected", "quarantine"])
def test_proxy_publication_single_send_and_receipts(reply, gene, policy, evidence, tmp_path):
    seen = []
    def transport(request):
        seen.append(request)
        assert request.url.path == "/asset/submit" and request.url.params["mode"] == "sync"
        payload = json.loads(request.content)
        assert payload["compose_recipe"] is False
        assert "protocol" not in payload
        if reply == "disconnect":
            raise httpx.ReadError(TOKEN, request=request)
        if reply == "rejected":
            return httpx.Response(402, json={"error": "credit_shortage"})
        body = {"publish_status": "accepted", "queued": False, "status": "accepted", "receiptId": "fixture-receipt",
                "assetIds": [a["asset_id"] for a in payload["assets"]]}
        if reply == "queued":
            body.update(publish_status="pending", queued=True)
        elif reply == "missing-id":
            del body["receiptId"]
        elif reply == "wrong-id":
            body["assetIds"] = ["sha256:" + "0" * 64]
        elif reply == "quarantine":
            body["decision"] = "quarantine"
        return httpx.Response(202 if reply == "queued" else 200, json=body)
    config = proxy_config()
    client = HubClient(config, transport=httpx.MockTransport(transport))
    path = tmp_path / "publish.json"
    try:
        record = client.prepare(gene, proxy_policy(policy), proxy_evidence(evidence), artifact_path=path)
        result = client.publish(path, approval=approval(record, config))
        expected = "received" if reply == "accepted" else "rejected" if reply in {"rejected", "quarantine"} else "unknown"
        assert result.state == expected
        assert result.source == "evolver_proxy"
        assert result.acceptance.provenance == "mock" and result.acceptance.interface_live == "not_run"
        assert client.publish(path, approval=approval(record, config)) == result
        assert len(seen) == 1 and TOKEN not in path.read_text()
    finally:
        client.close()


def test_proxy_fetch_requires_id_and_cannot_label_cache_as_remote(record):
    asset = json.loads(record.payload_json)["assets"][0]
    calls = []
    def transport(request):
        calls.append(request)
        assert request.url.path == "/asset/fetch"
        assert json.loads(request.content) == {"asset_ids": [asset["asset_id"]]}
        return httpx.Response(200, json={"assets": [asset], "missing": []})
    client = HubClient(proxy_config(transport_provenance="live"), transport=httpx.MockTransport(transport))
    try:
        assert client.fetch(signals=[]).state == "failed"
        result = client.fetch(signals=[], asset_ids=[asset["asset_id"]])
        assert result.state == "discovered" and result.source == "evolver_proxy"
        assert result.acceptance.interface_live == "not_run"
        assert result.acceptance.task_live == "not_run" and len(calls) == 1
    finally:
        client.close()


@pytest.mark.parametrize("reply", [True, False, "disconnect", "missing-id", "empty-id"])
def test_proxy_report_requires_effect_and_never_retries_unknown(reply, evidence, record, tmp_path):
    calls = []
    path = tmp_path / "use-report.json"
    asset = json.loads(record.payload_json)["assets"][0]
    asset_id = asset["asset_id"]
    def transport(request):
        if request.url.path == "/asset/fetch":
            return httpx.Response(200, json={"assets": [asset]})
        calls.append(request)
        assert request.url.path == "/asset/reuse-result"
        assert json.loads(path.read_text())["state"] == "unknown"
        payload = json.loads(request.content)
        assert payload["asset_id"] == asset_id and payload["outcome"] == "success"
        assert "time_saved_seconds" not in payload and "tokens_saved" not in payload
        if reply == "disconnect":
            raise httpx.ReadTimeout(TOKEN, request=request)
        if reply == "missing-id":
            return httpx.Response(200, json={"recorded": True})
        if reply == "empty-id":
            return httpx.Response(200, json={"recorded": True, "id": "  "})
        return httpx.Response(200, json={"recorded": reply, "id": "fixture-use"})
    client = HubClient(proxy_config(), transport=httpx.MockTransport(transport))
    try:
        with pytest.raises(HubError, match="fetched_asset_and_adoption"):
            client.report_use(asset_id, evidence.result, artifact_path=path, approved=True)
        assert client.fetch(signals=[], asset_ids=[asset_id]).state == "discovered"
        use = UseRecord(run_id=evidence.result.run_id, attempt=evidence.result.attempt,
                        ref=GeneRef(gene_id=asset["id"], asset_id=asset_id), used_at=time.time(), provenance="mock")
        wrong = use.model_copy(update={"ref": GeneRef(gene_id="unrelated", asset_id="sha256:" + "0" * 64)})
        with pytest.raises(HubError, match="adoption_mismatch"):
            client.report_use(asset_id, evidence.result, artifact_path=path, approved=True, use=wrong)
        pending = client.report_use(asset_id, evidence.result, artifact_path=path, use=use)
        assert pending.state == "pending" and not calls
        result = client.report_use(asset_id, evidence.result, artifact_path=path, approved=True, use=use)
        assert result.state == ("recorded" if reply is True else "unknown")
        if result.state == "unknown":
            assert result.acceptance.interface_live == "not_run" and result.receipt_id is None
        assert client.report_use(asset_id, evidence.result, artifact_path=path, approved=True, use=use) == result
        assert len(calls) == 1 and TOKEN not in path.read_text()
    finally:
        client.close()


def test_mock_evidence_cannot_report_live_effect(evidence, tmp_path):
    client = HubClient(proxy_config(transport_provenance="live"))
    try:
        with pytest.raises(HubError, match="mock_or_replay"):
            client.report_use("sha256:" + "1" * 64, evidence.result, artifact_path=tmp_path / "no.json", approved=True)
    finally:
        client.close()
