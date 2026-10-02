"""Three-axis research feedback projection built only from approved facts.

The projection derives execution/hypothesis/contribution axes from the same
immutable ledger and asset facts that ``trusted_facts`` validates. A valid
refutation (succeeded execution + refuted hypothesis + known effect) is a
positive contribution; a crash, timeout, auth error or unknown effect produces
no scientific entry. Read failures are never swallowed, and a rebuild re-reads
the same source facts without re-running any science.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
import time
from typing import Literal
from collections.abc import Callable

from pydantic import JsonValue, TypeAdapter

from local_assets.models import Candidate
from local_assets.paths import no_links
from local_assets.research import known_effect
from local_assets.research_models import ResearchObservation
from swarm.feedback import (
    FeedbackFact,
    ReadonlyLedger,
    _candidate_matches,
    _completed_at,
    readonly,
    trusted_facts,
)
from swarm.models import TaskRecord
from swarm.research.policy import (
    ContributionDecision,
    CorrectionEvent,
    ResearchPolicy,
    ThreeAxisResult,
)
from swarm.task_ledger import TaskLedger, connection, enable_wal

_OBJECT = TypeAdapter(dict[str, JsonValue])
_JSON: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)


def _claim_sources(report: ResearchObservation) -> str:
    claim = Candidate.model_validate_json(report.candidate_json).research
    if claim is None or not claim.sources:
        return "report:" + report.report_id
    return ";".join(claim.sources)


def _source_ref(assets: sqlite3.Connection, fact: FeedbackFact) -> str:
    if fact.kind == "validated_completion":
        return "receipt:" + fact.report_id
    report_id = fact.scientific_report_id or fact.report_id
    row = assets.execute("SELECT body FROM research_reports WHERE report_id=?", (report_id,)).fetchone()
    if row is None:
        return "report:" + report_id
    return _claim_sources(ResearchObservation.model_validate_json(row[0]))


def _trusted_refutation(db: sqlite3.Connection, task: TaskRecord, report: ResearchObservation,
                        result: dict[str, JsonValue], at: float) -> bool:
    candidate = Candidate.model_validate_json(report.candidate_json)
    claim = candidate.research
    evaluated = _OBJECT.validate_json(report.result_json)
    if (claim is None or candidate.scope != task.signal.scope or report.created_at > at
            or report.scientific_verdict != "failed" or report.execution_state != "succeeded"
            or not known_effect(report)
            or result.get("scientific_verdict") != report.scientific_verdict
            or result.get("execution_state") != report.execution_state
            or result.get("provenance") != report.provenance
            or any(evaluated.get(key) != getattr(report, key)
                   for key in ("scientific_verdict", "execution_state", "provenance"))
            or _OBJECT.validate_json(claim.model_dump_json()) != task.acceptance.get("research_claim")
            or _OBJECT.validate_json(report.plan_json) != task.acceptance.get("experiment_plan")
            or (report.plan_id, report.criterion_version, report.conditions) !=
            (claim.plan_id, claim.criterion_version, claim.conditions)):
        return False
    source_token = report.source_fencing_token or report.fencing_token
    source = db.execute("SELECT worker_id FROM task_attempts WHERE swarm_id=? AND task_id=? AND token=?",
                        (task.swarm_id, task.signal.task_id, source_token)).fetchone()
    if source is None or source[0] != task.owner or source_token > task.token:
        return False
    if report.source_swarm_id not in {None, task.swarm_id}:
        return False
    count = db.execute("SELECT COUNT(*) FROM task_attempts WHERE swarm_id=? AND task_id=? AND token<=?",
                       (task.swarm_id, task.signal.task_id, source_token)).fetchone()[0]
    if report.source_attempt is not None and (report.source_attempt.task_id != task.signal.task_id
                                              or report.source_attempt.attempt != count):
        return False
    if report.purpose == "original" and (candidate.attempt.task_id != task.signal.task_id
                                         or candidate.attempt.attempt != count
                                         or report.source_attempt is not None
                                         and candidate.attempt != report.source_attempt):
        return False
    events = [_OBJECT.validate_json(r[0]) for r in db.execute(
        "SELECT body FROM task_audit WHERE swarm_id=? AND task_id=? AND event='research_execution'",
        (task.swarm_id, task.signal.task_id))]
    confirmations = [_OBJECT.validate_json(r[0]) for r in db.execute(
        "SELECT body FROM task_audit WHERE swarm_id=? AND task_id=? AND event='execution_confirmed'",
        (task.swarm_id, task.signal.task_id))]
    matching = [e for e in events if e.get("run_id") == report.run_id and e.get("worker_id") == task.owner
                and e.get("token") == source_token]
    results = [e.get("result") for e in matching]
    return any(isinstance(r, dict) and r.get("effect_state") in {"known", "confirmed"}
               and r.get("execution_state") == "succeeded" and r.get("scientific_verdict") == "failed"
               and r.get("provenance") == report.provenance for r in results) and any(
                   e.get("request_id") == report.run_id and e.get("token") == source_token for e in confirmations)


def trusted_refutations(ledger: TaskLedger, assets_root: Path) -> list[ThreeAxisResult]:
    """Approved-fact refutations only; a crash or unknown effect is never one."""
    database = assets_root / "assets.sqlite3"
    if not database.exists():
        return []
    read = readonly if isinstance(ledger, ReadonlyLedger) else connection
    no_links(ledger.path)
    no_links(database)
    results: list[ThreeAxisResult] = []
    with read(ledger.path) as db, read(database) as assets:
        rows = db.execute("SELECT * FROM tasks WHERE swarm_id=? AND status='completed' "
                          "AND result_id IS NOT NULL AND unconfirmed_request_id IS NULL", (ledger.swarm_id,))
        for row in rows:
            task = ledger._record(db, row)
            result = task.result or {}
            at = _completed_at(db, task)
            asset_id = result.get("asset_id")
            if at is None or not task.owner or result.get("stage") != "evidence_submitted" \
                    or not isinstance(asset_id, str):
                continue
            observations = [ResearchObservation.model_validate_json(r[0]) for r in assets.execute(
                "SELECT body FROM research_reports WHERE asset_id=?", (asset_id,))]
            for scientific in observations:
                if (scientific.scientific_verdict != "failed" or scientific.execution_state != "succeeded"
                        or (scientific.task_id, scientific.worker_id, scientific.fencing_token, scientific.run_id) !=
                        (task.signal.task_id, task.owner, task.token, result.get("run_id"))):
                    continue
                candidate = Candidate.model_validate_json(scientific.candidate_json)
                if (not _trusted_refutation(db, task, scientific, result, at)
                        or not _candidate_matches(assets, scientific.asset_id, candidate)
                        or task.result_id is None):
                    continue
                results.append(ThreeAxisResult(
                    result_id=task.result_id, report_id=scientific.report_id, task_id=task.signal.task_id,
                    actor=task.owner, source_ref=_claim_sources(scientific), provenance=scientific.provenance,
                    execution="succeeded", hypothesis="refuted", contribution="proposed", at=at))
    return results


def research_feedback(ledger: TaskLedger, assets_root: Path) -> list[ThreeAxisResult]:
    """Projection of the three axes from approved facts; deterministic and idempotent."""
    database = assets_root / "assets.sqlite3"
    if not database.exists():
        return []
    facts = trusted_facts(ledger, assets_root)
    read = readonly if isinstance(ledger, ReadonlyLedger) else connection
    no_links(ledger.path)
    no_links(database)
    results: list[ThreeAxisResult] = []
    with read(database) as assets:
        for fact in facts:
            hypothesis: Literal["supported", "not_evaluated"] = (
                "supported" if fact.kind in ("scientific_result", "scientific_adoption") else "not_evaluated")
            results.append(ThreeAxisResult(
                result_id=fact.source_id, report_id=fact.report_id, task_id=fact.task_id, actor=fact.worker_id,
                source_ref=_source_ref(assets, fact), provenance=fact.provenance, execution="succeeded",
                hypothesis=hypothesis, contribution="proposed", at=fact.at))
    results.extend(trusted_refutations(ledger, assets_root))
    return sorted(results, key=lambda result: (result.at, result.result_id, result.hypothesis))


class ResearchFeedbackStore:
    """Append-only, idempotent persistence of accepted contributions and corrections.

    Contributions are deduplicated by completed result and source reference;
    correction events are appended and never rewritten. The store only persists
    facts already decided by the policy; it never re-runs science or an executor.
    """

    def __init__(self, path: str | Path, ledger: TaskLedger, *, clock: Callable[[], float] = time.time) -> None:
        self.path = Path(path).resolve()
        self.ledger = ledger
        self.clock = clock
        self.policy = ResearchPolicy()
        enable_wal(self.path)
        with connection(self.path, write=True) as db:
            db.execute("CREATE TABLE IF NOT EXISTS contributions (swarm_id TEXT, result_id TEXT, body TEXT, "
                       "PRIMARY KEY(swarm_id, result_id))")
            db.execute("CREATE TABLE IF NOT EXISTS corrections (event_id TEXT PRIMARY KEY, swarm_id TEXT, "
                       "branch_id TEXT, kind TEXT, body TEXT)")

    def _seen_keys(self, db: sqlite3.Connection) -> set[str]:
        keys: set[str] = set()
        for row in db.execute("SELECT body FROM contributions WHERE swarm_id=?", (self.ledger.swarm_id,)):
            keys.update(ResearchPolicy.dedup_keys(ThreeAxisResult.model_validate_json(row[0])))
        return keys

    def accept(self, result: ThreeAxisResult, *, reviewer: str) -> ContributionDecision:
        with connection(self.path, write=True) as db:
            decision = self.policy.accept(result, reviewer=reviewer, seen=self._seen_keys(db))
            if decision.accepted:
                db.execute("INSERT OR IGNORE INTO contributions VALUES (?,?,?)",
                           (self.ledger.swarm_id, result.result_id,
                            result.model_copy(update={"contribution": "accepted"}).model_dump_json()))
        return decision

    def synchronize(self, results: list[ThreeAxisResult], *, replace: bool = False) -> None:
        """Idempotent import of already-accepted contributions; never double-counts."""
        with connection(self.path, write=True) as db:
            if replace:
                db.execute("DELETE FROM contributions WHERE swarm_id=?", (self.ledger.swarm_id,))
            for result in results:
                if result.contribution != "accepted":
                    continue
                db.execute("INSERT OR IGNORE INTO contributions VALUES (?,?,?)",
                           (self.ledger.swarm_id, result.result_id, result.model_dump_json()))

    def contributions(self) -> list[ThreeAxisResult]:
        with connection(self.path) as db:
            rows = db.execute("SELECT body FROM contributions WHERE swarm_id=? ORDER BY rowid",
                              (self.ledger.swarm_id,)).fetchall()
        return [ThreeAxisResult.model_validate_json(row[0]) for row in rows]

    def record_correction(self, event: CorrectionEvent) -> None:
        with connection(self.path, write=True) as db:
            existing = db.execute("SELECT 1 FROM corrections WHERE event_id=?", (event.event_id,)).fetchone()
            if existing is not None:
                raise ValueError("correction_event_already_recorded")
            db.execute("INSERT INTO corrections VALUES (?,?,?,?,?)",
                       (event.event_id, self.ledger.swarm_id, event.branch_id, event.kind,
                        event.model_dump_json()))

    def corrections(self, branch_id: str | None = None) -> list[CorrectionEvent]:
        with connection(self.path) as db:
            if branch_id is None:
                rows = db.execute("SELECT body FROM corrections WHERE swarm_id=? ORDER BY rowid",
                                  (self.ledger.swarm_id,)).fetchall()
            else:
                rows = db.execute("SELECT body FROM corrections WHERE swarm_id=? AND branch_id=? ORDER BY rowid",
                                  (self.ledger.swarm_id, branch_id)).fetchall()
        return [CorrectionEvent.model_validate_json(row[0]) for row in rows]

    def snapshot(self) -> dict[str, JsonValue]:
        contributions = self.contributions()
        corrections = self.corrections()

        def axis_counts(axis: str) -> dict[str, int]:
            counts: dict[str, int] = {}
            for result in contributions:
                value = getattr(result, axis)
                counts[value] = counts.get(value, 0) + 1
            return counts

        return {
            "policy_version": self.policy.version,
            "advisory_only": True,
            "claim_requires_recheck": True,
            "three_axis": {
                "execution": _JSON.validate_python(axis_counts("execution")),
                "hypothesis": _JSON.validate_python(axis_counts("hypothesis")),
                "contribution": _JSON.validate_python(axis_counts("contribution")),
            },
            "contributions": [_JSON.validate_python(c.model_dump(mode="json")) for c in contributions],
            "corrections": [_JSON.validate_python(c.model_dump(mode="json")) for c in corrections],
        }
