"""A deliberately local-only A2A adapter with durable, content-bound publication."""

from __future__ import annotations

import os
import time
import math
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import httpx
from pydantic import JsonValue, SecretStr, TypeAdapter, ValidationError

from bridge_node.assets import BridgeError, NodeAssetBridge
from contracts.provenance import Acceptance
from contracts.resolution import Gene
from contracts.results import TaskResult
from metabolism.models import UseRecord
from hub_client.assets import AssetError, build_assets, validate_bundle
from hub_client.models import (
    CapsuleEvidence, FetchResult, GenePolicy, HelloResult, HubConfig,
    PublicationRecord, PublicationState, PublishApproval, ReuseRecord,
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
        self._fetched: dict[str, tuple[dict[str, JsonValue], float]] = {}
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

    def _credential(self) -> SecretStr | None:
        return self.config.proxy_token if self.config.source == "evolver_proxy" else self._secret

    def _acceptance(self, *, confirmed: bool = False) -> Acceptance:
        provenance = self.config.transport_provenance
        return Acceptance(
            provenance=provenance, contract_local="passed",
            interface_live="passed" if confirmed and provenance == "live" else "not_run",
        )

    def _post(self, kind: str, payload: dict[str, JsonValue]) -> dict[str, JsonValue]:
        if self.config.base_url is None:
            raise HubError("hub_not_configured")
        headers = {}
        credential = self._credential()
        if credential is not None:
            headers["Authorization"] = "Bearer " + credential.get_secret_value()
        envelope: dict[str, JsonValue] = {
            "protocol": "gep-a2a", "protocol_version": "1.0.0", "message_type": kind,
            "message_id": f"msg_{int(datetime.now(timezone.utc).timestamp() * 1000)}_{uuid4().hex}",
            "sender_id": self.config.sender_id,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "payload": payload,
        }
        method = "POST"
        route = "/a2a/" + kind
        request_body: dict[str, JsonValue] = envelope
        if self.config.source == "evolver_proxy":
            headers["X-EvoMap-Expected-Hub-Mode"] = "public"
            routes = {"hello": "/proxy/status", "publish": "/asset/submit?mode=sync",
                      "fetch": "/asset/fetch", "report": "/asset/reuse-result"}
            route = routes[kind]
            request_body = dict(payload)
            if kind == "hello":
                method = "GET"
            elif kind == "publish":
                request_body["compose_recipe"] = False
            elif kind == "fetch":
                # This route is exact-ID lookup; it can return cached assets.
                if not payload.get("asset_ids"):
                    raise HubError("proxy_fetch_requires_asset_ids")
                request_body = {"asset_ids": payload["asset_ids"]}
        # One send only. Even connection errors are never automatically retried.
        try:
            response = self._http.request(
                method, self.config.base_url.rstrip("/") + route,
                json=request_body if method == "POST" else None, headers=headers,
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
            if "payload" in body and self.config.source == "local_stub":
                body = _OBJECT.validate_python(body["payload"], strict=True)
        except (ValidationError, ValueError):
            raise HubError("malformed_response") from None
        if (
            body.get("error") or body.get("success") is False or body.get("ok") is False
            or body.get("status") in ("rejected", "quarantined", "quarantine")
            or body.get("decision") in ("rejected", "reject", "quarantined", "quarantine")
        ):
            raise HubError("hub_rejected")
        return body

    def hello(self, *, env_fingerprint: dict[str, JsonValue]) -> HelloResult:
        if self.config.base_url is None:
            return HelloResult(state="pending", reason="hub_not_configured")
        try:
            body = self._post("hello", {"capabilities": {}, "env_fingerprint": env_fingerprint})
            if self.config.source == "evolver_proxy":
                if (body.get("running") is not True or body.get("node_id") != self.config.sender_id
                    or body.get("hub_mode") != "public" or body.get("hub_auth_status") != "ok"):
                    raise HubError("proxy_identity_or_auth_unconfirmed")
                return HelloResult(state="acknowledged", reason="evolver_proxy_authenticated_status",
                                   source="evolver_proxy", acceptance=self._acceptance())
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
            return HelloResult(state="failed", reason=str(exc), source=self.config.source)

    def prepare(
        self, gene: Gene, policy: GenePolicy, evidence: CapsuleEvidence, *, artifact_path: Path,
    ) -> PublicationRecord:
        assets = build_assets(gene, policy, evidence, self.bridge, for_proxy=self.config.source == "evolver_proxy")
        record = PublicationRecord(
            payload_json=self.bridge.canonicalize({"assets": [asset for asset in assets]}),
            provenance=gene.provenance, original_run_uri=evidence.result.original_run_uri,
            source=self.config.source,
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

    def _save(self, path: Path, record: PublicationRecord, state: PublicationState, reason: str,
              *, receipt_id: str | None = None) -> PublicationRecord:
        data = record.model_dump()
        data.update(state=state, reason=reason)
        data["acceptance"] = self._acceptance(confirmed=state in {"received", "candidate", "promoted"}).model_dump()
        data["receipt_id"] = receipt_id or record.receipt_id
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
        if record.source != self.config.source:
            raise HubError("publication_source_mismatch")
        if self.config.transport_provenance == "live" and record.provenance != "live":
            raise HubError("mock_or_replay_cannot_publish_as_live")
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
        credential = self._credential()
        if credential is None or not credential.get_secret_value().strip():
            return record
        try:
            payload = _OBJECT.validate_json(record.payload_json, strict=True)
            if set(payload) != {"assets"}:
                raise AssetError("invalid_bundle_payload")
            assets = _ASSETS.validate_python(payload["assets"], strict=True)
            validate_bundle(assets, self.bridge, for_proxy=self.config.source == "evolver_proxy")
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
        if self.config.source == "evolver_proxy":
            # Durable queued / timeout receipts are unknown even with HTTP 2xx.
            receipt = body.get("receiptId")
            asset_ids = body.get("assetIds")
            expected_ids = [a["asset_id"] for a in assets]
            if (body.get("publish_status") != "accepted" or body.get("queued") is not False
                or status != "accepted" or not isinstance(receipt, str) or not receipt.strip()
                or (asset_ids is not None and asset_ids != expected_ids)
                or (body.get("assetId") is not None and body.get("assetId") not in expected_ids)):
                return self._save(path, record, "unknown", "proxy_publish_receipt_unconfirmed")
            return self._save(path, record, "received", "evolver_proxy_hub_received", receipt_id=receipt)
        if status in ("rejected", "quarantined", "quarantine") or decision in ("rejected", "reject", "quarantined", "quarantine"):
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
        credential = self._credential()
        if credential is None or not credential.get_secret_value().strip():
            return FetchResult(state="pending", reason="node_secret_required")
        payload: dict[str, JsonValue] = {"signals": list(signals)}
        if asset_ids is not None:
            payload["asset_ids"] = list(asset_ids)
        try:
            body = self._post("fetch", payload)
            if body.get("degraded") is True or body.get("local_fallback") is True:
                raise HubError("proxy_fetch_degraded")
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
            for asset in assets:
                fetched_id = asset.get("asset_id")
                if isinstance(fetched_id, str):
                    self._fetched[fetched_id] = (_OBJECT.validate_json(self.bridge.canonicalize(asset)), time.time())
            return FetchResult(
                state="discovered" if assets else "empty", reason=self.config.source + "_fetch",
                assets=assets, source=self.config.source, acceptance=self._acceptance(),
            )
        except (ValidationError, BridgeError):
            return FetchResult(state="failed", reason="invalid_fetched_assets", source=self.config.source)
        except HubError as exc:
            return FetchResult(state="failed", reason=str(exc), source=self.config.source)

    def report_use(
        self, asset_id: str, result: TaskResult, *, artifact_path: Path, approved: bool = False,
        use: UseRecord | None = None,
    ) -> ReuseRecord:
        """One explicit report of an independently verified use; unknown never re-sends."""
        if self.config.source != "evolver_proxy":
            raise HubError("reuse_report_requires_evolver_proxy")
        result = TaskResult.model_validate(result.model_dump())
        if result.status != "succeeded" or result.verdict.passed is not True:
            raise HubError("reuse_requires_independent_observed_success")
        if self.config.transport_provenance == "live" and result.provenance != "live":
            raise HubError("mock_or_replay_cannot_report_live_use")
        fetched = self._fetched.get(asset_id)
        if use is None or fetched is None:
            raise HubError("reuse_requires_fetched_asset_and_adoption")
        use = UseRecord.model_validate(use.model_dump())
        asset, fetched_at = fetched
        target_gene = asset.get("gene") if asset.get("type") == "Capsule" else asset_id
        if (use.attempt != result.attempt or use.run_id != result.run_id or use.provenance != result.provenance
            or use.ref.asset_id != target_gene or not math.isfinite(use.used_at)
            or use.used_at < fetched_at or use.used_at > time.time()
            or (asset.get("type") == "Gene" and use.ref.gene_id != asset.get("id"))):
            raise HubError("reuse_adoption_mismatch")
        if artifact_path.exists():
            prior = ReuseRecord.model_validate_json(artifact_path.read_bytes())
            if prior.asset_id != asset_id or prior.task_id != result.task_id:
                raise HubError("reuse_report_identity_mismatch")
            return prior
        record = ReuseRecord(asset_id=asset_id, task_id=result.task_id, state="pending",
                             reason="approval_required", acceptance=self._acceptance())
        if not approved or self.config.base_url is None or self._credential() is None:
            return record
        record = record.model_copy(update={"state": "unknown", "reason": "send_started_receipt_not_recorded"})
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        with artifact_path.open("x", encoding="utf-8") as stream:
            stream.write(record.model_dump_json(indent=2))
            stream.flush()
            os.fsync(stream.fileno())
        try:
            body = self._post("report", {"asset_id": asset_id, "outcome": "success", "task_id": result.task_id,
                                         "reason": "independent_acceptance_passed"})
            receipt = body.get("id")
            # Official Proxy may turn an empty upstream body into recorded=true.
            # A bare boolean is therefore not an authenticated Hub receipt.
            if body.get("recorded") is True and isinstance(receipt, str) and receipt.strip():
                record = record.model_copy(update={"state": "recorded", "reason": "evolver_proxy_use_recorded",
                                                  "receipt_id": receipt,
                                                  "acceptance": self._acceptance(confirmed=True)})
        except HubError:
            pass
        temporary = artifact_path.with_name(artifact_path.name + "." + uuid4().hex + ".tmp")
        try:
            with temporary.open("x", encoding="utf-8") as stream:
                stream.write(record.model_dump_json(indent=2))
                stream.flush()
                os.fsync(stream.fileno())
            temporary.replace(artifact_path)
        finally:
            temporary.unlink(missing_ok=True)
        return record
