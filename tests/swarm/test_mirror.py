from __future__ import annotations

import json
from pathlib import Path
import sys
from threading import Event
import time

import httpx
from pydantic import SecretStr
import pytest

from contracts.identity import AgentId, AttemptId
from contracts.provenance import Acceptance
from contracts.resolution import Gene, GeneRef
from contracts.results import TaskResult, Verification
from hub_client import CapsuleEvidence, GenePolicy, HubClient, HubConfig, PublicationRecord, PublishApproval
from hub_client.assets import build_assets
from local_assets import AssetPromoter, AssetValidator, Candidate, FileChange, LocalAssetStore
from local_assets.models import FileExpectation, ValidationPolicy
from local_assets.paths import git
from swarm.hub_mirror import HubMirror


@pytest.fixture(scope="module")
def promoted(tmp_path_factory):
    root = tmp_path_factory.mktemp("mirror-promoted")
    target = root / "target"
    target.mkdir()
    git(target, "init", "-b", "mirror-fixture")
    (target / "example.py").write_bytes(b"answer = 1\n")
    git(target, "add", "example.py")
    git(target, "-c", "user.name=Fixture", "-c", "user.email=fixture@localhost", "commit", "-m", "fixture")
    candidate = Candidate(attempt=AttemptId(task_id="mirror", agent=AgentId(role="builder", instance=0), attempt=0),
                          base_revision=git(target, "rev-parse", "HEAD").decode().strip(),
                          changes=(FileChange(path="example.py", before="answer = 1\n", after="answer = 2\n"),),
                          declared_files=1, declared_lines=2)
    store = LocalAssetStore(root / "assets")
    asset_id = store.publish(candidate)
    policy = ValidationPolicy(version="mirror-fixture-v1", expectations=(
        FileExpectation(path="example.py", content="answer = 2\n"),))
    report = AssetValidator(store, target, policy=policy).validate(asset_id)
    assert report.passed, report.reasons
    AssetPromoter(store, policy_version=policy.version).promote(asset_id, report.report_id)
    assert (target / "example.py").read_bytes() == b"answer = 1\n"
    return store, asset_id, report


def approved(record, client):
    return PublishApproval(approved_by="explicit-contract-fixture", payload_json=record.payload_json,
                           provenance=record.provenance, original_run_uri=record.original_run_uri,
                           sender_id=client.config.sender_id, hub_url=client.config.base_url)


def local_record(store, asset_id):
    return PublicationRecord(payload_json=store.bridge.canonicalize({"assets": store.promoted_bundle(asset_id)}),
                             provenance="mock", acceptance=Acceptance(provenance="mock"))


def drain(mirror):
    deadline = time.monotonic() + 40
    while mirror._queue.unfinished_tasks and time.monotonic() < deadline:
        time.sleep(0.02)
    assert mirror._queue.unfinished_tasks == 0


def test_mirror_default_disabled_does_not_create_artifacts(promoted, tmp_path):
    store, asset_id, _ = promoted
    mirror = HubMirror(store, tmp_path / "disabled")
    assert mirror.enqueue(asset_id) is False
    assert not (tmp_path / "disabled").exists()
    assert mirror._thread is None


def test_enabled_mirror_rejects_protected_artifact_directory(promoted):
    store, _, _ = promoted
    client = HubClient(HubConfig(base_url="http://127.0.0.1:9"))
    try:
        with pytest.raises(ValueError, match="protected_mirror_state"):
            HubMirror(store, Path(__file__).resolve().parents[2] / "forbidden-mirror",
                      enabled=True, client=client)
    finally:
        client.close()


def test_offline_mirror_enqueue_nonblocking_unknown_never_retried(promoted, tmp_path):
    store, asset_id, _ = promoted
    entered, release = Event(), Event()
    calls = []
    def transport(request):
        calls.append(request)
        entered.set()
        release.wait(10)
        raise httpx.ReadError("credential-not-for-logs", request=request)
    client = HubClient(HubConfig(base_url="http://127.0.0.1:9", node_secret=SecretStr("credential-not-for-logs")),
                       transport=httpx.MockTransport(transport))
    record = local_record(store, asset_id)
    approval = approved(record, client)
    mirror = HubMirror(store, tmp_path / "mirror", enabled=True, client=client, max_pending=1)
    try:
        before = time.monotonic()
        assert mirror.enqueue(asset_id, approval=approval)
        assert time.monotonic() - before < 0.5
        assert entered.wait(40)
        assert store.state(asset_id) == "approved"
        # One waiting item fills the bounded queue while the first HTTP call waits.
        assert mirror.enqueue(asset_id, approval=approval)
        assert not mirror.enqueue(asset_id, approval=approval)
        release.set()
        drain(mirror)
        path = next((tmp_path / "mirror").glob("*.json"))
        assert json.loads(path.read_bytes())["state"] == "unknown"
        assert "credential-not-for-logs" not in path.read_text()
        assert len(calls) == 1
        mirror.close(wait_seconds=1)
        restarted = HubMirror(store, tmp_path / "mirror", enabled=True, client=client)
        try:
            assert restarted.enqueue(asset_id, approval=approval)
            drain(restarted)
            assert len(calls) == 1
        finally:
            restarted.close(wait_seconds=1)
    finally:
        release.set()
        mirror.close(wait_seconds=1)
        client.close()


def proxy_record(store, asset_id, report):
    candidate = store.fetch(asset_id)
    result = TaskResult(run_id="mirror-fixture", task_id=candidate.attempt.task_id,
                        attempt=candidate.attempt, status="succeeded", provenance="mock",
                        artifact_uri=report.worktree_path,
                        acceptance=Acceptance(provenance="mock"),
                        verdict=Verification(passed=True, reviewer=AgentId(role="reviewer", instance=1),
                                             exit_code=0, evidence=[report.report_id]))
    assets = build_assets(
        Gene(ref=GeneRef(gene_id="fixture-mirror"), signals_match=["local_candidate"],
             strategy=[candidate.summary], verification=["node --check fixture.js"], provenance="mock"),
        GenePolicy(category="repair", max_files=1, forbidden_paths=[".git/**"],
                   validation_commands=["node --check fixture.js"]),
        CapsuleEvidence(capsule_id="mirror_fixture", summary="Local fixture only", confidence=1,
                        files_changed=1, lines_changed=2, score=1, result=result,
                        env_fingerprint=report.env_fingerprint.model_dump(mode="json"),
                        content={"candidate_asset_id": asset_id, "report_id": report.report_id},
                        model_name="fixture-not-live", returned_model_name="fixture-not-live",
                        gateway_response_id="fixture-not-live", event_id="fixture-not-live"),
        store.bridge, for_proxy=True)
    # Test caller explicitly binds the official bundle to the original local Gene.
    assets[0] = store.fetch_asset(asset_id)
    assets[1]["gene"] = asset_id
    assets[1]["asset_id"] = store.bridge.compute_asset_id(assets[1])
    assets[2]["genes_used"] = [asset_id]
    assets[2]["capsule_id"] = assets[1]["asset_id"]
    assets[2]["asset_id"] = store.bridge.compute_asset_id(assets[2])
    return PublicationRecord(payload_json=store.bridge.canonicalize({"assets": assets}), provenance="mock",
                             source="evolver_proxy", acceptance=Acceptance(provenance="mock"))


def test_official_proxy_mirror_preserves_ids_and_requires_supplied_lineage(promoted, tmp_path):
    store, asset_id, report = promoted
    calls = []
    def transport(request):
        calls.append(request)
        assert request.url.path == "/asset/submit" and request.url.params["mode"] == "sync"
        body = json.loads(request.content)
        assert body["assets"][0]["asset_id"] == asset_id
        return httpx.Response(200, json={"publish_status": "accepted", "queued": False,
                             "status": "accepted", "receiptId": "mock-receipt",
                             "assetIds": [asset["asset_id"] for asset in body["assets"]]})
    client = HubClient(HubConfig(base_url="http://127.0.0.1:19820", source="evolver_proxy",
                                proxy_token=SecretStr("fake-token")), transport=httpx.MockTransport(transport))
    mirror = HubMirror(store, tmp_path / "proxy", enabled=True, client=client)
    record = proxy_record(store, asset_id, report)
    try:
        assert not mirror.enqueue(asset_id, approval=approved(record, client))
        assert mirror.enqueue(asset_id, approval=approved(record, client), publication=record)
        drain(mirror)
        assert len(calls) == 1
        receipt = json.loads(next((tmp_path / "proxy").glob("*.json")).read_bytes())
        assert receipt["state"] == "received" and receipt["source"] == "evolver_proxy"
        assert receipt["acceptance"]["provenance"] == "mock"
        assert receipt["acceptance"]["interface_live"] == "not_run"
    finally:
        mirror.close(wait_seconds=1)
        client.close()


def test_unpromoted_asset_and_mock_to_live_do_not_send(promoted, tmp_path):
    store, asset_id, report = promoted
    calls = []
    client = HubClient(HubConfig(base_url="http://127.0.0.1:19820", source="evolver_proxy",
                                transport_provenance="live", proxy_token=SecretStr("fake-token")),
                       transport=httpx.MockTransport(lambda request: calls.append(request)))
    mirror = HubMirror(store, tmp_path / "denied", enabled=True, client=client)
    record = proxy_record(store, asset_id, report)
    try:
        assert mirror.enqueue("sha256:" + "f" * 64, approval=approved(record, client), publication=record)
        assert mirror.enqueue(asset_id, approval=approved(record, client), publication=record)
        drain(mirror)
        assert calls == []
    finally:
        mirror.close(wait_seconds=1)
        client.close()
