"""Three-axis research feedback projection built only from approved facts.

The projection derives execution/hypothesis/contribution axes from the same
immutable ledger and asset facts that ``trusted_facts`` validates. A valid
refutation (a trusted ``counterexample``: succeeded execution + failed verdict +
known effect, bound to the original claim/conditions) is a positive
contribution; a crash, timeout, auth error or unknown effect produces no
scientific entry. Read failures are never swallowed.

The durable acceptance entry (``ResearchFeedbackStore.accept``) re-derives every
result from trusted persistent facts and never trusts a caller-supplied result.
Contributions and corrections are append-only; supersession is recorded as an
appended event and never deletes the original record.
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
from orchestration.experiments.generated import GeneratedAssessment
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
    Branch,
    ContributionDecision,
    CorrectionEvent,
    Provenance,
    ResearchPolicy,
    SupersessionEvent,
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


def _observation(assets: sqlite3.Connection, fact: FeedbackFact) -> ResearchObservation | None:
    if fact.kind == "validated_completion":
        return None
    report_id = fact.scientific_report_id or fact.report_id
    row = assets.execute("SELECT body FROM research_reports WHERE report_id=?", (report_id,)).fetchone()
    return ResearchObservation.model_validate_json(row[0]) if row is not None else None


def _source_ref(assets: sqlite3.Connection, fact: FeedbackFact) -> str:
    if fact.kind == "validated_completion":
        return "receipt:" + fact.report_id
    observation = _observation(assets, fact)
    if observation is None:
        return "report:" + (fact.scientific_report_id or fact.report_id)
    return _claim_sources(observation)


def _trusted_refutation(db: sqlite3.Connection, task: TaskRecord, report: ResearchObservation,
                        result: dict[str, JsonValue], at: float) -> bool:
    candidate = Candidate.model_validate_json(report.candidate_json)
    claim = candidate.research
    evaluated = _OBJECT.validate_json(report.result_json)
    if (claim is None or candidate.scope != task.signal.scope or report.created_at > at
            or report.purpose != "counterexample"
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
    """Approved-fact counterexamples only; a legacy failure or unknown effect is never one."""
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
                if (scientific.purpose != "counterexample" or scientific.scientific_verdict != "failed"
                        or scientific.execution_state != "succeeded"
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
                    execution="succeeded", hypothesis="refuted", contribution="proposed", at=at,
                    asset_id=scientific.asset_id))
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
            observation = _observation(assets, fact)
            results.append(ThreeAxisResult(
                result_id=fact.source_id, report_id=fact.report_id, task_id=fact.task_id, actor=fact.worker_id,
                source_ref=_source_ref(assets, fact), provenance=fact.provenance, execution="succeeded",
                hypothesis=hypothesis, contribution="proposed", at=fact.at,
                asset_id=observation.asset_id if observation is not None else None))
    results.extend(trusted_refutations(ledger, assets_root))
    return sorted(results, key=lambda result: (result.at, result.result_id, result.hypothesis))


def from_generated_assessment(assessment: GeneratedAssessment, *, result_id: str, report_id: str,
                              task_id: str, actor: str, source_ref: str, provenance: Provenance,
                              asset_id: str | None = None, at: float = 0.0) -> ThreeAxisResult:
    """Thin conversion of B's three-axis ``GeneratedAssessment`` into C's policy
    ``ThreeAxisResult``.

    ``assessment.trusted`` and ``assessment.mode`` are deliberately ignored: C
    derives authority from the original TaskLedger execution, source/result and
    independent review, never from a backend-recomputed boolean or a "final"
    label. ``contribution`` stays ``proposed`` — accepting a contribution is a
    separate, independently reviewed step.
    """
    return ThreeAxisResult(
        result_id=result_id, report_id=report_id, task_id=task_id, actor=actor,
        source_ref=source_ref, provenance=provenance,
        execution=assessment.execution, hypothesis=assessment.hypothesis,
        contribution="proposed", asset_id=asset_id, at=at, reasons=assessment.reasons,
    )


class ResearchFeedbackStore:
    """Append-only, idempotent persistence of accepted contributions and corrections.

    ``accept`` is the only durable acceptance entry and re-derives the target
    result from the trusted ledger/asset facts bound to this store's swarm; a
    forged result id, a replay provenance, a self-approval or a result from
    another project/scope is rejected without persistence. Supersession is an
    appended event; it never deletes the original contribution record. A fresh
    rebuild writes to a new destination store and never mutates the source.
    """

    def __init__(self, path: str | Path, ledger: TaskLedger, assets_root: Path, *,
                 reviewer: str, clock: Callable[[], float] = time.time) -> None:
        self.path = Path(path).resolve()
        self.ledger = ledger
        self.assets_root = Path(assets_root).resolve()
        self.reviewer = reviewer
        self.clock = clock
        self.policy = ResearchPolicy()
        enable_wal(self.path)
        with connection(self.path, write=True) as db:
            db.execute("CREATE TABLE IF NOT EXISTS contributions (swarm_id TEXT, result_id TEXT, body TEXT, "
                       "PRIMARY KEY(swarm_id, result_id))")
            db.execute("CREATE TABLE IF NOT EXISTS corrections (event_id TEXT PRIMARY KEY, swarm_id TEXT, "
                       "branch_id TEXT, kind TEXT, body TEXT)")
            db.execute("CREATE TABLE IF NOT EXISTS supersessions (event_id TEXT PRIMARY KEY, swarm_id TEXT, "
                       "result_id TEXT, body TEXT)")

    def trusted(self) -> list[ThreeAxisResult]:
        """Derived three-axis facts; never caller-supplied assertions."""
        return research_feedback(self.ledger, self.assets_root)

    def _seen_keys(self, db: sqlite3.Connection) -> set[str]:
        keys: set[str] = set()
        for row in db.execute("SELECT body FROM contributions WHERE swarm_id=?", (self.ledger.swarm_id,)):
            keys.update(ResearchPolicy.dedup_keys(ThreeAxisResult.model_validate_json(row[0])))
        return keys

    def _reviewed(self, fact: ThreeAxisResult, facts: list[ThreeAxisResult]) -> bool:
        """The host's own bound reviewer must have an independently derived,
        trusted result on the same candidate (a distinct completed task that is
        a reproduction or counterexample of this fact). A forged observation
        that merely claims ``purpose=reproduction`` with no confirmed ledger
        execution never appears in the trusted projection, so it cannot
        authorize an acceptance."""
        if fact.asset_id is None:
            return False
        return any(other.actor == self.reviewer and other.asset_id == fact.asset_id
                   and other.task_id != fact.task_id and other.hypothesis in ("supported", "refuted")
                   for other in facts)

    def accept(self, result_id: str) -> ContributionDecision:
        """Independently accept one trusted result under the host's bound reviewer.

        The result is re-derived from this store's trusted ledger/asset facts and
        the reviewer is the host's own identity (fixed at construction, never a
        caller string). A caller-supplied result id, replay provenance, a reviewer
        that is the author, a reviewer with no trusted independent review of this
        candidate, or a result from another project/scope is rejected without
        persistence.
        """
        facts = self.trusted()
        matches = [fact for fact in facts if fact.result_id == result_id]
        if not matches:
            return ContributionDecision(accepted=False, state="rejected", reasons=("untrusted_result",))
        fact = matches[0]
        if fact.provenance == "replay":
            return ContributionDecision(accepted=False, state="rejected", reasons=("replay_not_acceptable",))
        if not self._reviewed(fact, facts):
            return ContributionDecision(accepted=False, state="rejected", reasons=("reviewer_not_admitted",))
        with connection(self.path, write=True) as db:
            decision = self.policy.accept(fact, reviewer=self.reviewer, seen=self._seen_keys(db))
            if decision.accepted:
                db.execute("INSERT OR IGNORE INTO contributions VALUES (?,?,?)",
                           (self.ledger.swarm_id, fact.result_id,
                            fact.model_copy(update={"contribution": "accepted", "reviewer": self.reviewer})
                            .model_dump_json()))
        return decision

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

    def record_supersession(self, event: SupersessionEvent) -> None:
        with connection(self.path, write=True) as db:
            existing = db.execute("SELECT 1 FROM supersessions WHERE event_id=?", (event.event_id,)).fetchone()
            if existing is not None:
                raise ValueError("supersession_event_already_recorded")
            db.execute("INSERT INTO supersessions VALUES (?,?,?,?)",
                       (event.event_id, self.ledger.swarm_id, event.result_id, event.model_dump_json()))

    def supersessions(self) -> list[SupersessionEvent]:
        with connection(self.path) as db:
            rows = db.execute("SELECT body FROM supersessions WHERE swarm_id=? ORDER BY rowid",
                              (self.ledger.swarm_id,)).fetchall()
        return [SupersessionEvent.model_validate_json(row[0]) for row in rows]

    def effective_contributions(self) -> list[ThreeAxisResult]:
        """Derived view: superseded contributions are marked, never deleted."""
        superseded = {event.result_id for event in self.supersessions()}
        return [contribution.model_copy(update={"contribution": "superseded"})
                if contribution.result_id in superseded else contribution
                for contribution in self.contributions()]

    def advisory(self, branches: list[Branch] | tuple[Branch, ...]) -> dict[str, JsonValue]:
        """Thin advisory projection for A/P: the accepted contributions plus the
        branch opportunities that reference them. Advisory only — a task is still
        claimed through the existing TaskLedger, which re-checks scope,
        capabilities, dependencies, lease/fencing and budget."""
        effective = self.effective_contributions()
        plan = self.policy.opportunities(branches)
        return {
            "policy_version": self.policy.version,
            "advisory_only": True,
            "claim_requires_recheck": True,
            "contributions": [_JSON.validate_python(c.model_dump(mode="json")) for c in effective],
            "opportunities": _JSON.validate_python(plan.model_dump(mode="json")),
        }

    def snapshot(self) -> dict[str, JsonValue]:
        contributions = self.contributions()
        effective = self.effective_contributions()
        corrections = self.corrections()
        supersessions = self.supersessions()

        def axis_counts(axis: str) -> dict[str, int]:
            counts: dict[str, int] = {}
            for result in effective:
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
            "effective_contributions": [_JSON.validate_python(c.model_dump(mode="json")) for c in effective],
            "corrections": [_JSON.validate_python(c.model_dump(mode="json")) for c in corrections],
            "supersessions": [_JSON.validate_python(c.model_dump(mode="json")) for c in supersessions],
        }
