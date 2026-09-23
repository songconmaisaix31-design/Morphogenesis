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

    def enqueue(self, asset_id: str, *, approval: PublishApproval | None = None,
                publication: PublicationRecord | None = None) -> bool:
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
                # SDK/store/transport errors can contain caller input. Preserve
                # the publication state and never log exception text or retry.
                pass
            finally:
                self._queue.task_done()

    def _publish(self, asset_id: str, approval: PublishApproval,
                 publication: PublicationRecord | None) -> None:
        client = self.client
        if client is None or self.store.state(asset_id) != "promoted":
            return
        if publication is None:
            bundle = self.store.promoted_bundle(asset_id)
            payload = client.bridge.canonicalize({"assets": list[JsonValue](bundle)})
            record = PublicationRecord(payload_json=payload, provenance="mock",
                                       source="local_stub", acceptance=Acceptance(provenance="mock"))
        else:
            record = PublicationRecord.model_validate_json(publication.model_dump_json())
            if record.state != "pending" or record.source != client.config.source:
                return
            payload_object = TypeAdapter(dict[str, JsonValue]).validate_json(record.payload_json)
            bundle = TypeAdapter(list[dict[str, JsonValue]]).validate_python(payload_object.get("assets"))
            validate_bundle(bundle, client.bridge, for_proxy=client.config.source == "evolver_proxy")
            # A supplied official bundle must preserve the exact locally promoted
            # Gene ID/bytes and the candidate AttemptId. Proxy-specific model
            # metadata is caller evidence, never fabricated by the mirror.
            if bundle[0] != self.store.fetch_asset(asset_id):
                return
            content = bundle[1].get("content")
            if not isinstance(content, dict):
                return
            if content.get("source_attempt") != self.store.fetch(asset_id).attempt.model_dump(mode="json"):
                return
            details = content.get("details")
            if not isinstance(details, dict) or details.get("candidate_asset_id") != asset_id:
                return
            report_id = details.get("report_id")
            if not isinstance(report_id, str):
                return
            report = self.store.get_report(report_id)
            if not report.passed or report.asset_id != asset_id:
                return
            if client.config.source == "evolver_proxy" and any(
                not isinstance(content.get(key), str) or not content[key]
                for key in ("model_name", "returned_model_name")
            ):
                return
        if approval.payload_json != record.payload_json or approval.provenance != record.provenance:
            return
        no_links(self.directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / (asset_id.removeprefix("sha256:") + ".json")
        no_links(path)
        try:
            with path.open("x", encoding="utf-8") as stream:
                stream.write(record.model_dump_json())
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError:
            # Includes pending failures and unknown send effects across restart.
            return
        client.publish(path, approval=approval)

    def close(self, *, wait_seconds: float = 0.0) -> None:
        if not 0 <= wait_seconds <= 1:
            raise ValueError("mirror_close_wait_must_be_bounded")
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=wait_seconds)
