"""A deliberately local-only A2A adapter with durable, content-bound publication."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import httpx
from pydantic import JsonValue, SecretStr, TypeAdapter, ValidationError

from bridge_node.assets import BridgeError, NodeAssetBridge
from contracts.provenance import Acceptance
from contracts.resolution import Gene
from hub_client.assets import AssetError, build_assets, validate_bundle
from hub_client.models import (
    CapsuleEvidence, FetchResult, GenePolicy, HelloResult, HubConfig,
    PublicationRecord, PublicationState, PublishApproval,
)

_OBJECT = TypeAdapter(dict[str, JsonValue])
_ASSETS = TypeAdapter(list[dict[str, JsonValue]])


class HubError(RuntimeError):
    """Only fixed error codes; never interpolate remote responses or credentials."""


class HubClient:
    def __init__(
        self, config: HubConfig | None = None, *, bridge: NodeAssetBridge | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.config = config or HubConfig()
        self.bridge = bridge or NodeAssetBridge()
        self._secret = self.config.node_secret
        # Own the client: no inherited proxy/auth/cookies/redirect behavior.
        self._http = httpx.Client(
            timeout=self.config.timeout_seconds, transport=transport,
            trust_env=False, follow_redirects=False,
        )

    @property
    def node_secret(self) -> SecretStr | None:
        """For an authorized caller's secure storage; never written by this adapter."""
        return self._secret

    def close(self) -> None:
        self._http.close()

    def _post(self, kind: str, payload: dict[str, JsonValue]) -> dict[str, JsonValue]:
        if self.config.base_url is None:
            raise HubError("hub_not_configured")
        headers = {}
        if self._secret is not None:
            headers["Authorization"] = "Bearer " + self._secret.get_secret_value()
        envelope = {
            "protocol": "gep-a2a", "protocol_version": "1.0.0", "message_type": kind,
            "message_id": f"msg_{int(datetime.now(timezone.utc).timestamp() * 1000)}_{uuid4().hex}",
            "sender_id": self.config.sender_id,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "payload": payload,
        }
        # One send only. Even connection errors are never automatically retried.
        try:
            response = self._http.post(
                self.config.base_url.rstrip("/") + "/a2a/" + kind,
                json=envelope, headers=headers,
            )
        except (httpx.ConnectError, httpx.ConnectTimeout):
            raise HubError("connection_failed") from None
        except httpx.HTTPError:
            raise HubError("transport_unknown") from None
        if not 200 <= response.status_code < 300:
            # 5xx and redirects do not establish whether a publish took effect.
            if 400 <= response.status_code < 500:
                raise HubError("http_rejected")
            raise HubError("http_unknown")
        try:
            body = _OBJECT.validate_json(response.content, strict=True)
            if body.get("error") or body.get("success") is False:
                raise HubError("hub_rejected")
            if "payload" in body:
                body = _OBJECT.validate_python(body["payload"], strict=True)
        except (ValidationError, ValueError):
            raise HubError("malformed_response") from None
        if (
            body.get("error") or body.get("success") is False
            or body.get("status") in ("rejected", "quarantined")
            or body.get("decision") in ("rejected", "reject", "quarantined")
        ):
            raise HubError("hub_rejected")
        return body

    def hello(self, *, env_fingerprint: dict[str, JsonValue]) -> HelloResult:
        if self.config.base_url is None:
            return HelloResult(state="pending", reason="hub_not_configured")
        try:
            body = self._post("hello", {"capabilities": {}, "env_fingerprint": env_fingerprint})
            if body.get("status") != "acknowledged" or body.get("your_node_id") != self.config.sender_id:
                raise HubError("invalid_hello_identity_or_status")
            secret = body.get("node_secret")
            if secret is not None and (not isinstance(secret, str) or not secret.strip()):
                raise HubError("invalid_hello_secret")
            # Absent/null secret means no rotation, not deletion.
            if isinstance(secret, str):
                self._secret = SecretStr(secret)
            return HelloResult(
                state="acknowledged", reason="local_stub_acknowledged",
                secret_updated=isinstance(secret, str),
                acceptance=Acceptance(provenance="mock", contract_local="passed"),
            )
        except HubError as exc:
            return HelloResult(state="failed", reason=str(exc))

    def prepare(
        self, gene: Gene, policy: GenePolicy, evidence: CapsuleEvidence, *, artifact_path: Path,
    ) -> PublicationRecord:
        assets = build_assets(gene, policy, evidence, self.bridge)
        record = PublicationRecord(
            payload_json=self.bridge.canonicalize({"assets": [asset for asset in assets]}),
            provenance=gene.provenance, original_run_uri=evidence.result.original_run_uri,
            acceptance=Acceptance(
                provenance=gene.provenance, original_run_uri=evidence.result.original_run_uri,
                contract_local="passed",
            ),
        )
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        # An existing publication must never be reset to pending by prepare().
        with artifact_path.open("x", encoding="utf-8") as stream:
            stream.write(record.model_dump_json(indent=2))
            stream.flush()
            os.fsync(stream.fileno())
        return record

    @staticmethod
    def read_publication(path: Path) -> PublicationRecord:
        return PublicationRecord.model_validate_json(path.read_bytes())

    @staticmethod
    def _save(path: Path, record: PublicationRecord, state: PublicationState, reason: str) -> PublicationRecord:
        data = record.model_dump()
        data.update(state=state, reason=reason)
        # Network evidence is always mock in this local-only version; source
        # provenance stays separately attached to the original publication.
        data["acceptance"] = Acceptance(provenance="mock", contract_local="passed").model_dump()
        result = PublicationRecord.model_validate(data)
        temporary = path.with_name(path.name + "." + uuid4().hex + ".tmp")
        try:
            with temporary.open("x", encoding="utf-8") as stream:
                stream.write(result.model_dump_json(indent=2))
                stream.flush()
                os.fsync(stream.fileno())
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
        return result

    def publish(self, artifact_path: Path, *, approval: PublishApproval | None = None) -> PublicationRecord:
        # An exclusive per-artifact lock prevents simultaneous local sends. A
        # crash leaves it in place for manual review, never automatic takeover.
        lock = artifact_path.with_name(artifact_path.name + ".publish.lock")
        try:
            with lock.open("x", encoding="utf-8"):
                pass
        except FileExistsError:
            raise HubError("publication_locked_manual_review_required") from None
        try:
            return self._publish_locked(artifact_path, approval)
        finally:
            lock.unlink()

    def _publish_locked(self, path: Path, approval: PublishApproval | None) -> PublicationRecord:
        record = self.read_publication(path)
        if record.state != "pending":
            return record  # Includes unknown: never silently re-send on restart.
        if self.config.base_url is None:
            return record
        if approval is None:
            return record
        if (
            approval.payload_json != record.payload_json
            or approval.provenance != record.provenance
            or approval.original_run_uri != record.original_run_uri
            or approval.sender_id != self.config.sender_id
            or approval.hub_url.rstrip("/") != self.config.base_url.rstrip("/")
        ):
            raise HubError("approval_does_not_match_publication")
        if self._secret is None or not self._secret.get_secret_value().strip():
            return record
        try:
            payload = _OBJECT.validate_json(record.payload_json, strict=True)
            if set(payload) != {"assets"}:
                raise AssetError("invalid_bundle_payload")
            assets = _ASSETS.validate_python(payload["assets"], strict=True)
            validate_bundle(assets, self.bridge)
        except (ValidationError, AssetError, BridgeError):
            raise HubError("publication_validation_failed") from None
        # Fail conservatively across a crash between send and receipt persistence.
        record = self._save(path, record, "unknown", "send_started_receipt_not_recorded")
        try:
            body = self._post("publish", payload)
        except HubError as exc:
            reason = str(exc)
            state: PublicationState = "unknown"
            if reason == "connection_failed":
                state = "pending"  # Caller may explicitly retry a known pre-connect failure.
            elif reason in {"http_rejected", "hub_rejected"}:
                state = "rejected"
            return self._save(path, record, state, reason)
        status = body.get("status")
        decision = body.get("decision")
        if status in ("rejected", "quarantined") or decision in ("rejected", "reject", "quarantined"):
            return self._save(path, record, "rejected", "hub_rejected")
        if status == "promoted":
            return self._save(path, record, "promoted", "local_stub_reports_promoted")
        if status == "candidate" or decision == "accepted":
            return self._save(path, record, "candidate", "local_stub_reports_candidate")
        if status in ("received", "accepted", "acknowledged"):
            return self._save(path, record, "received", "local_stub_reports_received")
        return self._save(path, record, "unknown", "unrecognized_publish_receipt")

    def fetch(self, *, signals: list[str], asset_ids: list[str] | None = None) -> FetchResult:
        if self.config.base_url is None:
            return FetchResult(state="pending", reason="hub_not_configured")
        if self._secret is None or not self._secret.get_secret_value().strip():
            return FetchResult(state="pending", reason="node_secret_required")
        payload: dict[str, JsonValue] = {"signals": list(signals)}
        if asset_ids is not None:
            payload["asset_ids"] = list(asset_ids)
        try:
            body = self._post("fetch", payload)
            raw = body.get("assets", body.get("results"))
            items = _ASSETS.validate_python(raw, strict=True)
            assets: list[dict[str, JsonValue]] = []
            for item in items:
                # Hub listings may wrap full official JSON in payload metadata.
                asset = _OBJECT.validate_python(item.get("payload", item), strict=True)
                if not self.bridge.validate_asset(asset).valid:
                    raise HubError("invalid_fetched_asset")
                if asset_ids is not None and asset.get("asset_id") not in asset_ids:
                    raise HubError("unexpected_fetched_asset")
                assets.append(asset)
            return FetchResult(
                state="discovered" if assets else "empty", reason="local_stub_fetch",
                assets=assets, acceptance=Acceptance(provenance="mock", contract_local="passed"),
            )
        except (ValidationError, BridgeError):
            return FetchResult(state="failed", reason="invalid_fetched_assets")
        except HubError as exc:
            return FetchResult(state="failed", reason=str(exc))
