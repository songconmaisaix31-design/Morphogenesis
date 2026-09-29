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
from swarm.observer import read_mirror


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


@pytest.mark.parametrize("fault", ["store", "sdk"])
def test_accepted_store_failure_is_observable_without_send(promoted, tmp_path, monkeypatch, fault):
    store, asset_id, _ = promoted
    calls = []
    client = HubClient(HubConfig(base_url="http://127.0.0.1:9"),
                       transport=httpx.MockTransport(lambda request: calls.append(request)))
    record = local_record(store, asset_id)
    mirror = HubMirror(store, tmp_path / "mirror", enabled=True, client=client)
    failures = []
    def broken_state(_asset_id):
        failures.append(fault)
        raise RuntimeError("private-store-exception-do-not-log")
    monkeypatch.setattr(store if fault == "store" else client.bridge,
                        "state" if fault == "store" else "canonicalize", broken_state)
    try:
        assert mirror.enqueue(asset_id, approval=approved(record, client))
        drain(mirror)
        view = read_mirror(tmp_path / "mirror")
        assert view["state"] == "ok" and len(view["records"]) == 1, view
        assert view["records"][0]["state"] == "unknown"
        assert calls == []
        assert "private-store-exception-do-not-log" not in json.dumps(view)
        assert all("private-store-exception-do-not-log" not in path.read_text()
                   for path in (tmp_path / "mirror").glob("*.json"))
        before = {p.name: p.read_bytes() for p in mirror.directory.glob("*.json")}
        restarted = HubMirror(store, mirror.directory, enabled=True, client=client)
        try:
            assert restarted.enqueue(asset_id, approval=approved(record, client))
            drain(restarted)
            assert failures == [fault] and calls == []
            assert {p.name: p.read_bytes() for p in mirror.directory.glob("*.json")} == before
        finally:
            restarted.close(wait_seconds=1)
    finally:
        mirror.close(wait_seconds=1)
        client.close()


def test_pending_is_visible_before_store_preparation(promoted, tmp_path, monkeypatch):
    store, asset_id, _ = promoted
    client = HubClient(HubConfig(base_url="http://127.0.0.1:9"), transport=httpx.MockTransport(
        lambda request: pytest.fail("unconfigured mirror must not send")))
    record = local_record(store, asset_id)
    entered, release = Event(), Event()
    original = store.state
    def paused(value):
        entered.set()
        assert release.wait(10)
        return original(value)
    monkeypatch.setattr(store, "state", paused)
    mirror = HubMirror(store, tmp_path / "mirror", enabled=True, client=client)
    try:
        before = time.monotonic()
        assert mirror.enqueue(asset_id, approval=approved(record, client))
        assert time.monotonic() - before < 0.5 and entered.wait(10)
        view = read_mirror(mirror.directory)["records"][0]
        assert view["state"] == "pending" and view["reason"] == "mirror_preparation_pending"
        assert not view["hub_promoted"] and view["acceptance"]["interface_live"] == "not_run"
        assert json.loads(next(mirror.directory.glob("*.json")).read_bytes())["payload_json"] == "{}"
        release.set()
        drain(mirror)
    finally:
        release.set()
        mirror.close(wait_seconds=1)
        client.close()


@pytest.mark.parametrize("mismatch", ["approval", "publication", "quarantined"])
def test_preflight_rejections_are_visible_without_payload(promoted, tmp_path, mismatch):
    store, asset_id, _ = promoted
    client = HubClient(HubConfig(base_url="http://127.0.0.1:9"), transport=httpx.MockTransport(
        lambda request: pytest.fail("preflight rejection must not send")))
    record = local_record(store, asset_id)
    approval = approved(record, client)
    if mismatch == "approval":
        approval = approval.model_copy(update={"payload_json": "private-rejected-payload"})
    elif mismatch == "publication":
        record = record.model_copy(update={"state": "unknown", "payload_json": "private-rejected-payload"})
    else:
        candidate = store.fetch(asset_id).model_copy(update={"changes": (
            FileChange(path="example.py", before="answer = 1\n", after="answer = 3\n"),)})
        asset_id = store.publish(candidate)
    mirror = HubMirror(store, tmp_path / "mirror", enabled=True, client=client)
    try:
        assert mirror.enqueue(asset_id, approval=approval, publication=record)
        drain(mirror)
        view = read_mirror(mirror.directory)["records"][0]
        assert view["state"] == "rejected" and not view["hub_promoted"]
        assert view["reason"] == {"approval": "mirror_approval_mismatch",
                                  "publication": "mirror_publication_state_or_source_mismatch",
                                  "quarantined": "mirror_local_asset_not_approved"}[mismatch]
        assert all("private-rejected-payload" not in p.read_text() for p in mirror.directory.glob("*.json"))
    finally:
        mirror.close(wait_seconds=1)
        client.close()


@pytest.mark.parametrize("state", ["pending", "unknown", "received", "rejected"])
def test_existing_receipt_is_unchanged_and_skips_preparation(promoted, tmp_path, monkeypatch, state):
    store, asset_id, _ = promoted
    client = HubClient(HubConfig(base_url="http://127.0.0.1:9"))
    record = local_record(store, asset_id)
    mirror = HubMirror(store, tmp_path / "mirror", enabled=True, client=client)
    mirror.directory.mkdir()
    path = mirror.directory / (asset_id[7:] + ".json")
    path.write_text(record.model_copy(update={"state": state}).model_dump_json(), encoding="utf-8")
    before = path.read_bytes(), path.stat().st_mtime_ns
    monkeypatch.setattr(store, "state", lambda value: pytest.fail("existing receipt must skip preparation"))
    try:
        assert mirror.enqueue(asset_id, approval=approved(record, client))
        drain(mirror)
        assert (path.read_bytes(), path.stat().st_mtime_ns) == before
        assert mirror.last_error is None
    finally:
        mirror.close(wait_seconds=1)
        client.close()


@pytest.mark.parametrize("state", ["unknown", "received"])
def test_preparation_does_not_overwrite_an_observed_outcome(promoted, tmp_path, monkeypatch, state):
    store, asset_id, _ = promoted
    client = HubClient(HubConfig(base_url="http://127.0.0.1:9"))
    record = local_record(store, asset_id)
    mirror = HubMirror(store, tmp_path / "mirror", enabled=True, client=client)
    def changed(value):
        path = mirror.directory / (value[7:] + ".json")
        client._save(path, client.read_publication(path), state, "fixture_known_outcome")
        return "approved"
    monkeypatch.setattr(store, "state", changed)
    monkeypatch.setattr(client, "publish", lambda *args, **kwargs: pytest.fail("outcome must not be resent"))
    try:
        assert mirror.enqueue(asset_id, approval=approved(record, client))
        drain(mirror)
        saved = client.read_publication(next(mirror.directory.glob("*.json")))
        assert saved.state == state and saved.reason == "fixture_known_outcome"
    finally:
        mirror.close(wait_seconds=1)
        client.close()


def test_unwritable_record_has_bounded_process_local_diagnostic(promoted, tmp_path):
    store, asset_id, _ = promoted
    client = HubClient(HubConfig(base_url="http://127.0.0.1:9"))
    record = local_record(store, asset_id)
    directory = tmp_path / "not-a-directory"
    directory.write_text("preserve original", encoding="utf-8")
    mirror = HubMirror(store, directory, enabled=True, client=client)
    try:
        assert mirror.enqueue(asset_id, approval=approved(record, client))
        drain(mirror)
        assert mirror.last_error == "mirror_record_unavailable"
        assert directory.read_text() == "preserve original"
        assert read_mirror(directory)["records"] == []  # Cannot claim durable visibility.
    finally:
        mirror.close(wait_seconds=1)
        client.close()


def test_unaccepted_invalid_and_closed_offers_create_nothing(promoted, tmp_path):
    store, asset_id, _ = promoted
    client = HubClient(HubConfig(base_url="http://127.0.0.1:9"))
    record = local_record(store, asset_id)
    mirror = HubMirror(store, tmp_path / "mirror", enabled=True, client=client)
    try:
        assert not mirror.enqueue(asset_id)  # No approval.
        assert not mirror.enqueue("invalid", approval=approved(record, client))
        mirror.close()
        assert not mirror.enqueue(asset_id, approval=approved(record, client))
        assert not mirror.directory.exists() and mirror._thread is None
    finally:
        client.close()


@pytest.mark.parametrize("persisted", [None, "unknown", "received"])
def test_adapter_exception_keeps_outcome_or_marks_unknown(promoted, tmp_path, monkeypatch, persisted):
    store, asset_id, _ = promoted
    client = HubClient(HubConfig(base_url="http://127.0.0.1:9"))
    record = local_record(store, asset_id)
    mirror = HubMirror(store, tmp_path / "mirror", enabled=True, client=client)
    def failed_publish(path, **kwargs):
        if persisted:
            client._save(path, client.read_publication(path), persisted, "fixture_preserved_outcome")
        raise RuntimeError("private-adapter-error")
    monkeypatch.setattr(client, "publish", failed_publish)
    try:
        assert mirror.enqueue(asset_id, approval=approved(record, client))
        drain(mirror)
        path = next(mirror.directory.glob("*.json"))
        saved = client.read_publication(path)
        assert saved.state == (persisted or "unknown")
        assert saved.reason == ("fixture_preserved_outcome" if persisted else "mirror_adapter_failed")
        assert "private-adapter-error" not in path.read_text()
        assert mirror.last_error is None
    finally:
        mirror.close(wait_seconds=1)
        client.close()


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
        view = read_mirror(mirror.directory)["records"][0]
        assert view["state"] == "confirmed" and not view["hub_promoted"]
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
        view = read_mirror(mirror.directory)
        assert len(view["records"]) == 2
        # An absent asset makes A's state lookup raise; it is an unknown local
        # preparation failure, distinct from a known quarantined asset above.
        assert {(row["state"], row["reason"]) for row in view["records"]} == {
            ("unknown", "mirror_preparation_failed"), ("rejected", "mirror_provenance_mismatch")}
    finally:
        mirror.close(wait_seconds=1)
        client.close()
