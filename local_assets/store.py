"""Append-only SQLite PUBLISH/FETCH/REPORT, using official GEP addresses."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import sqlite3
from collections.abc import Iterator

from pydantic import JsonValue, TypeAdapter

from bridge_node.assets import NodeAssetBridge
from contracts.identity import AgentId
from contracts.provenance import Acceptance
from contracts.resolution import Gene, GeneRef
from contracts.results import TaskResult, Verification
from hub_client.assets import build_assets, validate_bundle
from hub_client.models import CapsuleEvidence, GenePolicy
from local_assets.models import AssetSafetyError, Candidate, PromotionReceipt, ValidationReport
from local_assets.paths import FROZEN_MAINLINE, no_links

_OBJECT = TypeAdapter(dict[str, JsonValue])


class LocalAssetStore:
    def __init__(self, root: Path | str, *, bridge: NodeAssetBridge | None = None) -> None:
        self.root = Path(root).absolute()
        no_links(self.root)
        if self.root.resolve().is_relative_to(FROZEN_MAINLINE.resolve()):
            raise AssetSafetyError("protected_target")
        self.root.mkdir(parents=True, exist_ok=True)
        self.database = self.root / "assets.sqlite3"
        no_links(self.database)
        self.bridge = bridge or NodeAssetBridge()
        with self.connection() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS assets (
                    asset_id TEXT PRIMARY KEY, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS reports (
                    report_id TEXT PRIMARY KEY, asset_id TEXT NOT NULL,
                    body TEXT NOT NULL, FOREIGN KEY(asset_id) REFERENCES assets(asset_id));
                CREATE TABLE IF NOT EXISTS promotions (
                    report_id TEXT PRIMARY KEY, asset_id TEXT NOT NULL,
                    body TEXT NOT NULL, FOREIGN KEY(report_id) REFERENCES reports(report_id));
            """)
            for table in ("assets", "reports", "promotions"):
                for operation in ("UPDATE", "DELETE"):
                    db.execute(f"CREATE TRIGGER IF NOT EXISTS {table}_{operation} "
                               f"BEFORE {operation} ON {table} BEGIN "
                               "SELECT RAISE(ABORT, 'immutable_local_evidence'); END")

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        no_links(self.database)
        db = sqlite3.connect(self.database, timeout=10)
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def publish(self, candidate: Candidate) -> str:
        candidate = Candidate.model_validate_json(candidate.model_dump_json())
        # Candidate is a Gene, not an invented successful Capsule. The official
        # schema forbids unknown properties: a strategy string carries the exact
        # local application payload without extending the SDK's wire schema.
        asset: dict[str, JsonValue] = {
            "type": "Gene", "schema_version": "1.14.0",
            "id": "local_" + candidate.attempt.task_id,
            "category": "repair", "signals_match": ["local_candidate"],
            "strategy": [candidate.summary, "local_candidate_json:" + candidate.model_dump_json()],
            "constraints": {"max_files": candidate.declared_files, "forbidden_paths": [".git/**"]},
            "validation": ["local_assets.AssetValidator"],
        }
        asset_id = self.bridge.compute_asset_id(asset)
        asset["asset_id"] = asset_id
        if not self.bridge.validate_asset(asset).valid:
            raise AssetSafetyError("official_asset_validation_failed")
        body = self.bridge.canonicalize(asset)
        with self.connection() as db:
            db.execute("INSERT OR IGNORE INTO assets VALUES (?, ?)", (asset_id, body))
            if db.execute("SELECT body FROM assets WHERE asset_id=?", (asset_id,)).fetchone()[0] != body:
                raise AssetSafetyError("asset_address_conflict")
        return asset_id

    def fetch_asset(self, asset_id: str) -> dict[str, JsonValue]:
        with self.connection() as db:
            row = db.execute("SELECT body FROM assets WHERE asset_id=?", (asset_id,)).fetchone()
        if row is None:
            raise AssetSafetyError("unknown_asset")
        asset = _OBJECT.validate_json(row[0])
        if asset.get("asset_id") != asset_id or not self.bridge.validate_asset(asset).valid:
            raise AssetSafetyError("tampered_asset")
        return asset

    def fetch(self, asset_id: str) -> Candidate:
        strategy = self.fetch_asset(asset_id).get("strategy")
        if (not isinstance(strategy, list) or len(strategy) != 2
                or not isinstance(strategy[1], str)
                or not strategy[1].startswith("local_candidate_json:")):
            raise AssetSafetyError("missing_candidate")
        return Candidate.model_validate_json(strategy[1].removeprefix("local_candidate_json:"))

    def report(self, report: ValidationReport) -> None:
        """Persist a failed observation; only AssetValidator issues passing reports."""
        if report.passed:
            raise AssetSafetyError("passing_report_requires_validator")
        self._record_validation(report)

    def _record_validation(self, report: ValidationReport) -> None:
        """Validator-only append. OS/database owners remain trusted."""
        candidate = self.fetch(report.asset_id)
        if (report.candidate_json != candidate.model_dump_json()
                or report.attempt != candidate.attempt
                or report.base_revision != candidate.base_revision):
            raise AssetSafetyError("report_candidate_mismatch")
        with self.connection() as db:
            db.execute("INSERT INTO reports VALUES (?, ?, ?)",
                       (report.report_id, report.asset_id, report.model_dump_json()))

    def get_report(self, report_id: str) -> ValidationReport:
        with self.connection() as db:
            row = db.execute("SELECT body FROM reports WHERE report_id=?", (report_id,)).fetchone()
        if row is None:
            raise AssetSafetyError("unknown_report")
        report = ValidationReport.model_validate_json(row[0])
        if report.report_id != report_id:
            raise AssetSafetyError("report_id_mismatch")
        return report

    def reports(self) -> list[ValidationReport]:
        with self.connection() as db:
            rows = db.execute("SELECT body FROM reports ORDER BY rowid").fetchall()
        return [ValidationReport.model_validate_json(row[0]) for row in rows]

    def state(self, asset_id: str) -> str:
        self.fetch(asset_id)
        with self.connection() as db:
            row = db.execute("SELECT 1 FROM promotions WHERE asset_id=?", (asset_id,)).fetchone()
        return "promoted" if row else "quarantined"

    def promotions(self, asset_id: str | None = None) -> list[PromotionReceipt]:
        with self.connection() as db:
            if asset_id:
                rows = db.execute("SELECT body FROM promotions WHERE asset_id=? ORDER BY rowid", (asset_id,)).fetchall()
            else:
                rows = db.execute("SELECT body FROM promotions ORDER BY rowid").fetchall()
        return [PromotionReceipt.model_validate_json(row[0]) for row in rows]

    def promoted_bundle(self, asset_id: str) -> list[dict[str, JsonValue]]:
        bundle = self.promoted_assets(asset_id)
        if not bundle:
            raise AssetSafetyError("asset_not_promoted")
        return bundle

    def promoted_assets(self, asset_id: str | None = None) -> list[dict[str, JsonValue]]:
        """Only validated and promoted bundles are eligible for optional mirroring."""
        assets: list[dict[str, JsonValue]] = []
        seen: set[str] = set()
        for receipt in self.promotions(asset_id):
            if receipt.asset_id in seen:
                continue
            seen.add(receipt.asset_id)
            candidate = self.fetch(receipt.asset_id)
            report = self.get_report(receipt.report_id)
            if not report.passed or report.candidate_json != candidate.model_dump_json():
                raise AssetSafetyError("invalid_promoted_report")
            internal_gene = Gene(
                ref=GeneRef(gene_id="local_" + candidate.attempt.task_id),
                signals_match=["local_candidate"], strategy=[candidate.summary],
                verification=["local_assets.AssetValidator"], provenance="mock",
            )
            result = TaskResult(
                run_id="local_assets", task_id=candidate.attempt.task_id,
                attempt=candidate.attempt, status="succeeded", provenance="mock",
                acceptance=Acceptance(provenance="mock"),
                artifact_uri="local-report:" + report.report_id,
                verdict=Verification(
                    passed=True,
                    reviewer=AgentId(role="reviewer", instance=candidate.attempt.agent.instance + 1),
                    evidence=["local-report:" + report.report_id], exit_code=0,
                    summary="Independent configured local validation commands",
                ),
            )
            bundle = build_assets(
                internal_gene,
                GenePolicy(category="repair", max_files=candidate.declared_files,
                           forbidden_paths=[".git/**"]),
                CapsuleEvidence(
                    capsule_id="validation_" + report.report_id, summary=candidate.summary,
                    confidence=1, files_changed=report.actual_files, lines_changed=report.actual_lines,
                    score=1, result=result,
                    env_fingerprint=_OBJECT.validate_json(report.env_fingerprint.model_dump_json()),
                    content={"candidate_asset_id": receipt.asset_id, "report_id": report.report_id,
                             "evidence_class": "contract_local"},
                ), self.bridge,
            )
            # Preserve the originally addressed Gene, including candidate bytes.
            bundle[0] = self.fetch_asset(receipt.asset_id)
            bundle[1]["gene"] = receipt.asset_id
            bundle[1]["asset_id"] = self.bridge.compute_asset_id(bundle[1])
            validate_bundle(bundle, self.bridge)
            assets.extend(bundle)
        return assets
