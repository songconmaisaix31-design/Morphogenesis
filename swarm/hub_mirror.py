"""Optional bounded asynchronous publication through the existing direct adapter."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from queue import Empty, Full, Queue
import re
from threading import Event, Lock, Thread

from pydantic import JsonValue, TypeAdapter

from contracts.provenance import Acceptance
from hub_client.client import HubClient
from hub_client.assets import validate_bundle
from hub_client.models import PublicationRecord, PublishApproval
from local_assets.paths import FROZEN_MAINLINE, no_links
from local_assets.store import LocalAssetStore


class HubMirror:
    """No polling, retries, credentials in artifacts, or effect on local outcomes.

    The caller owns the client and the exact payload-bound approval. Only the
    official Evolver direct adapter is supported with caller-prepared lineage;
    missing metadata is deferred. A daemon thread cannot hold process exit.
    """

    def __init__(self, store: LocalAssetStore, directory: Path, *, enabled: bool = False,
                 client: HubClient | None = None, max_pending: int = 8,
                 approvals: Mapping[str, PublishApproval] | None = None,
                 publications: Mapping[str, PublicationRecord] | None = None) -> None:
        if not 1 <= max_pending <= 64:
            raise ValueError("mirror_queue_limit")
        if enabled and (client is None or client.config.timeout_seconds > 10):
            raise ValueError("bounded_direct_mirror_required")
        no_links(directory)
        if enabled and any(directory.resolve().is_relative_to(protected.resolve())
                           for protected in (FROZEN_MAINLINE, Path(__file__).resolve().parents[1])):
            raise ValueError("protected_mirror_state")
        self.store, self.directory, self.enabled, self.client = store, directory, enabled, client
        self.approvals, self.publications = dict(approvals or {}), dict(publications or {})
        self._queue: Queue[tuple[str, PublishApproval, PublicationRecord | None]] = Queue(maxsize=max_pending)
        self._stop = Event()
        self._lock = Lock()
        self._thread: Thread | None = None
        # One bounded, sanitized diagnostic when storage itself is unavailable.
        # It is process-local, not a durable delivery receipt.
        self.last_error: str | None = None

    def enqueue(self, asset_id: str, *, approval: PublishApproval | None = None,
                publication: PublicationRecord | None = None) -> bool:
        """True means queued in memory, not sent or durably accepted by the Hub.

        False means disabled/closed, invalid ID, missing approval/official
        lineage, or queue capacity; these unaccepted offers create no record.
        """
        # No IO, validation, SDK work or network wait on the local worker path.
        approval = approval or self.approvals.get(asset_id)
        publication = publication or self.publications.get(asset_id)
        if (not self.enabled or self._stop.is_set() or approval is None
                or re.fullmatch(r"sha256:[a-f0-9]{64}", asset_id) is None):
            return False
        if self.client is not None and self.client.config.source == "evolver_proxy" and publication is None:
            return False  # Never synthesize missing model/event lineage.
        with self._lock:
            try:
                self._queue.put_nowait((asset_id, approval, publication))
            except Full:
                return False
            if self._thread is None:
                self._thread = Thread(target=self._run, name="optional-hub-mirror", daemon=True)
                self._thread.start()
        return True

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                item = self._queue.get(timeout=0.1)
            except Empty:
                continue
            try:
                self._publish(*item)
            except Exception:
                # If even record IO fails, retain existing evidence and expose
                # only this bounded diagnostic, never exception text or retries.
                self.last_error = "mirror_record_unavailable"
            finally:
                self._queue.task_done()

    def _publish(self, asset_id: str, approval: PublishApproval,
                 publication: PublicationRecord | None) -> None:
        client = self.client
        if client is None:
            return
        no_links(self.directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / (asset_id.removeprefix("sha256:") + ".json")
        no_links(path)
        # Reuse the adapter record before *any* store/SDK work. An empty payload
        # is deliberately unsendable; preparation is not Hub acknowledgement.
        marker = PublicationRecord(payload_json="{}", provenance=client.config.transport_provenance,
                                   source=client.config.source, reason="mirror_preparation_pending",
                                   acceptance=Acceptance(provenance=client.config.transport_provenance))
        try:
            with path.open("x", encoding="utf-8") as stream:
                stream.write(marker.model_dump_json())
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError:
            # Pending, unknown, confirmed and rejected are all terminal for
            # automatic mirror dispatch, including after process restart.
            return
        try:
            prepared = self._prepare(asset_id, approval, publication, client)
        except Exception:
            self._save_preparation(client, path, marker, marker.model_copy(update={
                "state": "unknown", "reason": "mirror_preparation_failed"}))
            return
        if isinstance(prepared, str):
            self._save_preparation(client, path, marker, marker.model_copy(update={
                "state": "rejected", "reason": prepared}))
            return
        if not self._save_preparation(client, path, marker, prepared):
            return
        try:
            client.publish(path, approval=approval)
        except Exception:
            # The adapter may already have recorded an outcome before raising.
            # Keep it; an unclassified failure with only pending evidence is
            # unknown and must not be automatically repeated.
            current = client.read_publication(path)
            if current.state == "pending":
                client._save(path, current, "unknown", "mirror_adapter_failed")

    @staticmethod
    def _save_preparation(client: HubClient, path: Path, marker: PublicationRecord,
                          record: PublicationRecord) -> bool:
        no_links(path)
        if client.read_publication(path) != marker:
            return False  # Never replace another persisted outcome with pending.
        # Existing adapter's atomic fsync/replace, not another delivery store.
        client._save(path, record, record.state, record.reason)
        return True

    def _prepare(self, asset_id: str, approval: PublishApproval,
                 publication: PublicationRecord | None, client: HubClient) -> PublicationRecord | str:
        if self.store.state(asset_id) != "approved":
            return "mirror_local_asset_not_approved"
        if publication is None:
            bundle = self.store.promoted_bundle(asset_id)
            payload = client.bridge.canonicalize({"assets": list[JsonValue](bundle)})
            record = PublicationRecord(payload_json=payload, provenance="mock",
                                       source="local_stub", acceptance=Acceptance(provenance="mock"))
        else:
            record = PublicationRecord.model_validate_json(publication.model_dump_json())
            if record.state != "pending" or record.source != client.config.source:
                return "mirror_publication_state_or_source_mismatch"
            payload_object = TypeAdapter(dict[str, JsonValue]).validate_json(record.payload_json)
            bundle = TypeAdapter(list[dict[str, JsonValue]]).validate_python(payload_object.get("assets"))
            validate_bundle(bundle, client.bridge, for_proxy=client.config.source == "evolver_proxy")
            # A supplied official bundle must preserve the exact locally promoted
            # Gene ID/bytes and the candidate AttemptId. Proxy-specific model
            # metadata is caller evidence, never fabricated by the mirror.
            if bundle[0] != self.store.fetch_asset(asset_id):
                return "mirror_local_gene_mismatch"
            content = bundle[1].get("content")
            if not isinstance(content, dict):
                return "mirror_lineage_mismatch"
            if content.get("source_attempt") != self.store.fetch(asset_id).attempt.model_dump(mode="json"):
                return "mirror_lineage_mismatch"
            details = content.get("details")
            if not isinstance(details, dict) or details.get("candidate_asset_id") != asset_id:
                return "mirror_lineage_mismatch"
            report_id = details.get("report_id")
            if not isinstance(report_id, str):
                return "mirror_validation_mismatch"
            report = self.store.get_report(report_id)
            if not report.passed or report.asset_id != asset_id:
                return "mirror_validation_mismatch"
            if client.config.source == "evolver_proxy" and any(
                not isinstance(content.get(key), str) or not content[key]
                for key in ("model_name", "returned_model_name")
            ):
                return "mirror_lineage_mismatch"
        if (approval.payload_json != record.payload_json or approval.provenance != record.provenance
                or approval.original_run_uri != record.original_run_uri
                or approval.sender_id != client.config.sender_id
                or (client.config.base_url is not None
                    and approval.hub_url.rstrip("/") != client.config.base_url.rstrip("/"))):
            return "mirror_approval_mismatch"
        if client.config.transport_provenance == "live" and record.provenance != "live":
            return "mirror_provenance_mismatch"
        return record.model_copy(update={"reason": "mirror_prepared"})

    def close(self, *, wait_seconds: float = 0.0) -> None:
        if not 0 <= wait_seconds <= 1:
            raise ValueError("mirror_close_wait_must_be_bounded")
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=wait_seconds)
