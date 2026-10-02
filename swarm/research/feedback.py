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
from orchestration.experiments.trusted import TrustedCriteriaRegistry
from swarm.feedback import (
    FeedbackFact,
    ReadonlyLedger,
    _candidate_matches,
    _completed_at,
    readonly,
    trusted_facts,
)
from swarm.models import Locality, TaskRecord
from swarm.research.policy import (
    Branch,
    ContributionDecision,
    CorrectionEvent,
    Provenance,
    ResearchPolicy,
    SupersessionEvent,
    ThreeAxisResult,
)
from swarm.research.feedback_generated import trusted_generated_feedback
from swarm.task_ledger import TaskLedger, connection, enable_wal

_OBJECT = TypeAdapter(dict[str, JsonValue])
_JSON: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)


def _local_tasks(ledger: TaskLedger, locality: Locality | None) -> set[str] | None:
    if locality is None:
        return None
    query, args = ledger._local_filter(locality)
    read = readonly if isinstance(ledger, ReadonlyLedger) else connection
    with read(ledger.path) as db:
        return {row[0] for row in db.execute("SELECT t.task_id FROM tasks t WHERE " + query, args)}


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
            if "generated_plan" in task.acceptance:
                continue
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
                    asset_id=scientific.asset_id, conditions=scientific.conditions,
                    run_id=scientific.run_id, sandbox_id=scientific.sandbox_id, purpose=scientific.purpose))
    return results


def research_feedback(ledger: TaskLedger, assets_root: Path, *,
                      generated_criteria: TrustedCriteriaRegistry | None = None,
                      project_id: str | None = None, archive_root: Path | None = None,
                      locality: Locality | None = None) -> list[ThreeAxisResult]:
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
                asset_id=observation.asset_id if observation is not None else None,
                conditions=observation.conditions if observation is not None else {},
                run_id=observation.run_id if observation is not None else None,
                sandbox_id=observation.sandbox_id if observation is not None else None,
                purpose=observation.purpose if observation is not None else None))
    results.extend(trusted_refutations(ledger, assets_root))
    local_tasks = _local_tasks(ledger, locality)
    bound: list[ThreeAxisResult] = []
    for result in results:
        if local_tasks is not None and result.task_id not in local_tasks:
            continue
        payload = ledger.get(result.task_id).signal.payload
        project, branch = payload.get("project_id"), payload.get("branch_id")
        if project_id is not None and project != project_id:
            continue
        bound.append(result.model_copy(update={"project_id": project if isinstance(project, str) else None,
                                               "branch_id": branch if isinstance(branch, str) else None}))
    results = bound
    results.extend(trusted_generated_feedback(ledger, assets_root, criteria_registry=generated_criteria,
                                              project_id=project_id, archive_root=archive_root,
                                              task_ids=local_tasks))
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
                 reviewer: str, clock: Callable[[], float] = time.time,
                 generated_criteria: TrustedCriteriaRegistry | None = None,
                 project_id: str | None = None, archive_root: Path | None = None,
                 locality: Locality | None = None) -> None:
        self.path = Path(path).resolve()
        self.ledger = ledger
        self.assets_root = Path(assets_root).resolve()
        self.reviewer = reviewer
        self.clock = clock
        self.generated_criteria = generated_criteria
        self.project_id = project_id
        self.archive_root = archive_root
        self.locality = Locality.model_validate(locality.model_dump()) if locality is not None else None
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
        return research_feedback(self.ledger, self.assets_root, generated_criteria=self.generated_criteria,
                                 project_id=self.project_id, archive_root=self.archive_root,
                                 locality=self.locality)

    def _seen_keys(self, db: sqlite3.Connection) -> set[str]:
        keys: set[str] = set()
        for row in db.execute("SELECT body FROM contributions WHERE swarm_id=?", (self.ledger.swarm_id,)):
            keys.update(ResearchPolicy.dedup_keys(ThreeAxisResult.model_validate_json(row[0])))
        return keys

    def _review(self, fact: ThreeAxisResult, facts: list[ThreeAxisResult], *,
                reviewer: str | None = None) -> ThreeAxisResult | None:
        """The host's own bound reviewer must have an independently derived,
        trusted result on the same candidate (a distinct completed task that is
        a reproduction or counterexample of this fact). A forged observation
        that merely claims ``purpose=reproduction`` with no confirmed ledger
        execution never appears in the trusted projection, so it cannot
        authorize an acceptance."""
        if fact.asset_id is None:
            return None
        for other in facts:
            if (other.actor != (reviewer or self.reviewer) or other.actor == fact.actor
                    or other.asset_id != fact.asset_id or other.task_id == fact.task_id
                    or other.provenance == "replay" or other.provenance != fact.provenance
                    or other.execution != "succeeded" or other.hypothesis != fact.hypothesis
                    or other.hypothesis not in ("supported", "refuted")
                    or other.purpose not in ("reproduction", "counterexample")
                    or other.conditions != fact.conditions or other.project_id != fact.project_id
                    or other.experiment_schema != fact.experiment_schema):
                continue
            if fact.experiment_schema is not None and (
                    not fact.run_id or not other.run_id or fact.run_id == other.run_id
                    or not fact.sandbox_id or not other.sandbox_id or fact.sandbox_id == other.sandbox_id):
                continue
            return other
        return None

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
        review = self._review(fact, facts)
        if review is None:
            return ContributionDecision(accepted=False, state="rejected", reasons=("reviewer_not_admitted",))
        with connection(self.path, write=True) as db:
            decision = self.policy.accept(fact, reviewer=self.reviewer, seen=self._seen_keys(db))
            if decision.accepted:
                db.execute("INSERT OR IGNORE INTO contributions VALUES (?,?,?)",
                           (self.ledger.swarm_id, fact.result_id,
                            fact.model_copy(update={"contribution": "accepted", "reviewer": self.reviewer,
                                                    "review_report_id": review.report_id})
                            .model_dump_json()))
        return decision

    def contributions(self) -> list[ThreeAxisResult]:
        with connection(self.path) as db:
            rows = db.execute("SELECT body FROM contributions WHERE swarm_id=? ORDER BY rowid",
                              (self.ledger.swarm_id,)).fetchall()
        results = [ThreeAxisResult.model_validate_json(row[0]) for row in rows]
        local_tasks = _local_tasks(self.ledger, self.locality)
        return [result for result in results if (self.project_id is None or result.project_id == self.project_id)
                and (local_tasks is None or result.task_id in local_tasks)]

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
        facts = self.trusted()
        trusted = {fact.result_id: fact for fact in facts}
        accepted: dict[str, ThreeAxisResult] = {}
        for contribution in effective:
            fact = trusted.get(contribution.result_id)
            if (contribution.contribution != "accepted" or fact is None or not contribution.reviewer
                    or fact.provenance == "replay"
                    or contribution.model_copy(update={"contribution": "proposed", "reviewer": None,
                                                       "review_report_id": None}) != fact):
                continue
            review = self._review(fact, facts, reviewer=contribution.reviewer)
            if review is not None and review.report_id == contribution.review_report_id:
                accepted[fact.result_id] = contribution
        resolved: list[Branch] = []
        for branch in branches:
            def references(hypothesis: str) -> tuple[str, ...]:
                return tuple(fact.result_id for fact in accepted.values()
                    if fact.hypothesis == hypothesis and fact.branch_id == branch.branch_id
                    and (not branch.conditions or fact.conditions == branch.conditions)
                    and (self.project_id is None or fact.project_id == self.project_id))

            # Derive references from accepted source facts even when the caller
            # passes none. Caller refs cannot create, duplicate, relocate or
            # resurrect evidence, or omit a valid refutation from the next advice.
            resolved.append(branch.model_copy(update={
                "supported_by": references("supported"), "refuted_by": references("refuted")}))
        plan = self.policy.opportunities(resolved)
        return {
            "policy_version": self.policy.version,
            "advisory_only": True,
            "claim_requires_recheck": True,
            "contributions": [_JSON.validate_python(c.model_dump(mode="json")) for c in accepted.values()],
            "branches": [_JSON.validate_python(branch.model_dump(mode="json")) for branch in resolved],
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
            "results": [_JSON.validate_python(result.model_dump(mode="json")) for result in self.trusted()],
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
