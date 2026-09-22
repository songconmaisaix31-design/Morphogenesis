import json
from pathlib import Path

import httpx
import pytest
from pydantic import JsonValue, SecretStr, ValidationError

from hub_client import HubClient, HubConfig, HubError, PublicationRecord, PublishApproval

ORIGIN = "http://127.0.0.1:7102"
FIXTURE_SECRET = "fixture-only-secret-not-a-credential"


def config() -> HubConfig:
    return HubConfig(base_url=ORIGIN, node_secret=SecretStr(FIXTURE_SECRET))


def approve(record: PublicationRecord, *, origin: str = ORIGIN) -> PublishApproval:
    return PublishApproval(
        approved_by="contract-test", payload_json=record.payload_json,
        provenance=record.provenance, original_run_uri=record.original_run_uri,
        sender_id=config().sender_id, hub_url=origin,
    )


@pytest.mark.parametrize("url", ["https://evomap.ai", "http://localhost:7102", "http://127.0.0.1.evil", "http://127.0.0.1/a2a", "http://x:secret@127.0.0.1", "http://127.0.0.1?x=y"])
def test_only_literal_local_stub_allowed(url: str) -> None:
    with pytest.raises(ValidationError):
        HubConfig(base_url=url)


def test_missing_config_keeps_local_artifact(publication: Path) -> None:
    def no_network(request: httpx.Request) -> httpx.Response:
        pytest.fail("unconfigured adapter must not send")
    client = HubClient(transport=httpx.MockTransport(no_network))
    try:
        before = publication.read_bytes()
        assert client.hello(env_fingerprint={}).state == "pending"
        assert client.fetch(signals=[]).state == "pending"
        assert client.publish(publication).state == "pending"
        assert publication.read_bytes() == before
    finally:
        client.close()


def test_hello_envelope_and_secret_retention() -> None:
    requests: list[httpx.Request] = []
    def stub(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        reply: dict[str, JsonValue] = {"status": "acknowledged", "your_node_id": config().sender_id}
        if len(requests) == 1:
            reply["node_secret"] = "new-fixture-secret"
        return httpx.Response(200, json={"payload": reply})
    client = HubClient(config(), transport=httpx.MockTransport(stub))
    try:
        assert client.hello(env_fingerprint={"platform": "fixture"}).secret_updated
        receipt = client.hello(env_fingerprint={})
        assert not receipt.secret_updated
        assert client.node_secret == SecretStr("new-fixture-secret")
        assert requests[1].headers["Authorization"] == "Bearer new-fixture-secret"
        first, second = [json.loads(r.content) for r in requests]
        assert set(first) == {"protocol", "protocol_version", "message_type", "message_id", "sender_id", "timestamp", "payload"}
        assert first["protocol"] == "gep-a2a" and first["protocol_version"] == "1.0.0"
        assert first["message_id"] != second["message_id"]
        assert first["timestamp"].endswith("Z")
        assert "new-fixture-secret" not in repr(receipt)
        assert FIXTURE_SECRET not in repr(config()) + config().model_dump_json()
        assert receipt.acceptance.interface_live == "not_run"
    finally:
        client.close()


def test_hello_wrong_identity_does_not_rotate_secret() -> None:
    client = HubClient(config(), transport=httpx.MockTransport(lambda r: httpx.Response(200, json={
        "status": "acknowledged", "your_node_id": "hub_wrong", "node_secret": "bad-secret",
    })))
    try:
        assert client.hello(env_fingerprint={}).state == "failed"
        assert client.node_secret == SecretStr(FIXTURE_SECRET)
    finally:
        client.close()


@pytest.mark.parametrize("approval_kind", ["absent", "content", "destination", "sender", "provenance"])
def test_approval_binds_content_identity_and_destination(
    approval_kind: str, publication: Path, record: PublicationRecord,
) -> None:
    def no_network(request: httpx.Request) -> httpx.Response:
        pytest.fail("unapproved payload must not send")
    client = HubClient(config(), transport=httpx.MockTransport(no_network))
    approval = approve(record)
    changes = approval.model_dump()
    changes.update({
        "content": {"payload_json": "{}"}, "destination": {"hub_url": "http://127.0.0.1:7999"},
        "sender": {"sender_id": "node_other"}, "provenance": {"provenance": "live"},
    }.get(approval_kind, {}))
    try:
        if approval_kind == "absent":
            assert client.publish(publication).state == "pending"
        else:
            with pytest.raises(HubError, match="approval_does_not_match_publication"):
                client.publish(publication, approval=PublishApproval.model_validate(changes))
        assert client.read_publication(publication).state == "pending"
    finally:
        client.close()


@pytest.mark.parametrize("reply,expected", [
    ({"status": "received"}, "received"), ({"status": "candidate"}, "candidate"),
    ({"decision": "accepted"}, "candidate"), ({"status": "promoted"}, "promoted"),
    ({"status": "rejected"}, "rejected"), ({}, "unknown"), ({"status": []}, "unknown"),
])
def test_publish_lifecycle_is_not_http_success(
    reply: dict[str, JsonValue], expected: str, publication: Path, record: PublicationRecord,
) -> None:
    calls = 0
    def stub(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert HubClient.read_publication(publication).state == "unknown"
        assert json.loads(request.content)["payload"] == json.loads(record.payload_json)
        return httpx.Response(200, json={"payload": reply})
    client = HubClient(config(), transport=httpx.MockTransport(stub))
    try:
        receipt = client.publish(publication, approval=approve(record))
        assert receipt.state == expected
        assert receipt.provenance == "mock"
        assert receipt.acceptance.provenance == "mock"
        assert receipt.acceptance.interface_live == receipt.acceptance.task_live == "not_run"
        assert client.publish(publication, approval=approve(record)).state == expected
        assert calls == 1
    finally:
        client.close()


@pytest.mark.parametrize("failure,expected", [("read", "unknown"), ("write", "unknown"), ("connect", "pending"), ("500", "unknown"), ("403", "rejected"), ("redirect", "unknown"), ("malformed", "unknown")])
def test_network_failures_are_bounded_and_sanitized(
    failure: str, expected: str, publication: Path, record: PublicationRecord,
) -> None:
    calls = 0
    def stub(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if failure == "read":
            raise httpx.ReadTimeout(FIXTURE_SECRET, request=request)
        if failure == "write":
            raise httpx.WriteError(FIXTURE_SECRET, request=request)
        if failure == "connect":
            raise httpx.ConnectError(FIXTURE_SECRET, request=request)
        if failure == "redirect":
            return httpx.Response(307, headers={"Location": "https://evomap.ai/a2a/publish"})
        if failure == "malformed":
            return httpx.Response(200, content=b"not-json")
        return httpx.Response(int(failure), json={"secret": FIXTURE_SECRET})
    client = HubClient(config(), transport=httpx.MockTransport(stub))
    try:
        receipt = client.publish(publication, approval=approve(record))
        assert receipt.state == expected and calls == 1
        assert FIXTURE_SECRET not in receipt.model_dump_json() + publication.read_text()
    finally:
        client.close()
    if expected == "unknown":
        restarted = HubClient(config(), transport=httpx.MockTransport(stub))
        try:
            assert restarted.publish(publication, approval=approve(record)).state == "unknown"
            assert calls == 1
        finally:
            restarted.close()


def test_publication_lock_blocks_duplicate_send(publication: Path, record: PublicationRecord) -> None:
    publication.with_name(publication.name + ".publish.lock").touch()
    client = HubClient(config())
    try:
        with pytest.raises(HubError, match="publication_locked"):
            client.publish(publication, approval=approve(record))
    finally:
        client.close()


def test_corrupted_approved_bundle_fails_before_send(publication: Path, record: PublicationRecord) -> None:
    payload = json.loads(record.payload_json)
    payload["assets"][1]["summary"] = "edited without recomputing ID"
    data = record.model_dump()
    data["payload_json"] = json.dumps(payload)
    corrupted = PublicationRecord.model_validate(data)
    publication.write_text(corrupted.model_dump_json(), encoding="utf-8")
    def no_network(request: httpx.Request) -> httpx.Response:
        pytest.fail("corrupted assets must not send even with approval")
    client = HubClient(config(), transport=httpx.MockTransport(no_network))
    try:
        with pytest.raises(HubError, match="publication_validation_failed"):
            client.publish(publication, approval=approve(corrupted))
        assert client.read_publication(publication).state == "pending"
    finally:
        client.close()


def test_absent_credentials_do_not_send(publication: Path, record: PublicationRecord) -> None:
    def no_network(request: httpx.Request) -> httpx.Response:
        pytest.fail("missing credentials must not send")
    client = HubClient(HubConfig(base_url=ORIGIN), transport=httpx.MockTransport(no_network))
    try:
        assert client.publish(publication, approval=approve(record)).state == "pending"
        assert client.fetch(signals=[]).reason == "node_secret_required"
    finally:
        client.close()


def test_fetch_top_level_rejection_cannot_hide_behind_payload(record: PublicationRecord) -> None:
    client = HubClient(config(), transport=httpx.MockTransport(lambda r: httpx.Response(
        200, json={"error": "denied", "payload": json.loads(record.payload_json)},
    )))
    try:
        result = client.fetch(signals=[])
        assert result.state == "failed" and result.assets == []
    finally:
        client.close()


@pytest.mark.parametrize("kind,expected", [("empty", "empty"), ("missing", "failed"), ("wrong_shape", "failed"), ("tampered", "failed"), ("full", "discovered"), ("wrapped", "discovered")])
def test_fetch_requires_actual_valid_assets(kind: str, expected: str, record: PublicationRecord) -> None:
    assets = json.loads(record.payload_json)["assets"]
    if kind == "tampered":
        assets[0]["strategy"] = ["changed"]
    reply = {
        "empty": {"assets": []}, "missing": {"ok": True}, "wrong_shape": {"assets": {}},
        "tampered": {"assets": assets}, "full": {"assets": assets},
        "wrapped": {"results": [{"payload": a} for a in assets]},
    }[kind]
    client = HubClient(config(), transport=httpx.MockTransport(lambda r: httpx.Response(200, json=reply)))
    try:
        result = client.fetch(signals=["fixture_error"])
        assert result.state == expected
        assert result.acceptance.interface_live == "not_run"
        if expected == "failed":
            assert result.assets == []
    finally:
        client.close()
