"""Derived preferences from existing immutable evidence; never execute recovery."""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import os
from pathlib import Path
import random
import sqlite3
import time
from typing import Literal, cast

from pydantic import Field, JsonValue, TypeAdapter

from contracts.base import Contract
from local_assets.models import AdoptionReceipt, Candidate, ConsumptionExecution, PromotionReceipt, ValidationReport
from local_assets.paths import no_links
from local_assets.research import known_effect, scientific_plan
from local_assets.research_models import ResearchObservation
from swarm.models import Locality, RunLimits, TaskRecord
from swarm.task_ledger import TaskLedger, connection

_OBJECT = TypeAdapter(dict[str, JsonValue])


class FeedbackFact(Contract):
    source_id: str = Field(min_length=1)  # Existing completed result ID, not a new proof.
    kind: Literal["validated_completion", "scientific_result", "scientific_adoption"]
    task_id: str
    worker_id: str
    pipe_key: str
    at: float = Field(ge=0, allow_inf_nan=False)
    report_id: str
    scientific_report_id: str | None = None
    adoption_id: str | None = None
    provenance: Literal["live", "replay", "mock", "contract_local"]


@contextmanager
def readonly(path: Path) -> Iterator[sqlite3.Connection]:
    no_links(path)
    # Opening a closed WAL-mode database in ordinary ro mode creates -wal/-shm.
    # Immutable mode is safe only for a checkpointed file, not an active WAL
    # (it ignores uncheckpointed pages). Never checkpoint or create sidecars
    # in somebody else's archive. An active archive explicitly needs review.
    sidecars = [path.with_name(path.name + suffix) for suffix in ("-wal", "-journal")]
    if any(p.exists() and p.stat().st_size for p in sidecars):
        raise ValueError("readonly_policy_source_requires_checkpointed_archive")
    before = path.stat()
    db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro&immutable=1",
                         uri=True, isolation_level=None)
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA query_only=ON")
        db.execute("BEGIN")
        yield db
        after = path.stat()
        if (any(p.exists() and p.stat().st_size for p in sidecars) or
                (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns)):
            raise ValueError("policy_source_changed_during_read")
    finally:
        db.close()


class ReadonlyLedger(TaskLedger):
    """Supported diagnostic view; uses the ledger's existing eligibility SQL."""
    def __init__(self, path: Path, swarm_id: str) -> None:
        self.path, self.swarm_id = path.resolve(), swarm_id
        self.clock, self.timeout_seconds = time.time, 10.0
        with readonly(self.path) as db:
            row = db.execute("SELECT limits FROM swarm_runs WHERE swarm_id=?", (swarm_id,)).fetchone()
            if row is None:
                raise ValueError("unknown_policy_swarm")
            self.limits = RunLimits.model_validate_json(row[0])

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        raise PermissionError("readonly_policy_view")
        yield  # pragma: no cover

    def get(self, task_id: str) -> TaskRecord:
        with readonly(self.path) as db:
            return self._record(db, self._row(db, task_id))

    def candidates(self, locality: Locality, *, limit: int = 100, include_blocked: bool = False,
                   capabilities: tuple[str, ...] | None = None) -> list[TaskRecord]:
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be in [1,1000]")
        query, args = self._local_filter(locality)
        parameters: list[str | float | int] = list(args)
        if not include_blocked:
            query += " AND " + self._eligible()
            parameters.extend([self.now(), self.limits.max_attempts_per_task, self.now(), os.sep, os.sep])
        if capabilities is not None:
            if len(capabilities) > 64:
                raise ValueError("too many capabilities")
            query += " AND t.capability IN (" + (",".join("?" for _ in capabilities) or "NULL") + ")"
            parameters.extend(capabilities)
        with readonly(self.path) as db:
            return [self._record(db, row) for row in db.execute(
                "SELECT t.* FROM tasks t WHERE " + query + " ORDER BY t.created_at,t.task_id LIMIT ?",
                [*parameters, limit])]


def trusted_facts(ledger: TaskLedger, assets_root: Path) -> list[FeedbackFact]:
    """Positive learning only from completed authority and its actual report chain.

    Report/result/adoption are not three rewards. One completed result earns one
    reward of its explicit kind; an adoption is required when consumption is claimed.
    Invalid/unknown/non-passing evidence earns no scientific reward.
    """
    database = assets_root / "assets.sqlite3"
    if not database.exists():
        return []
    facts: list[FeedbackFact] = []
    # A running service already owns its writable runtime and may share a WAL
    # with other Workers. Use the existing read transaction there. Operator
    # archive diagnostics always use the strict, no-sidecar ReadonlyLedger.
    read = readonly if isinstance(ledger, ReadonlyLedger) else connection
    no_links(ledger.path)
    no_links(database)
    with read(ledger.path) as db, read(database) as assets:
        rows = db.execute("SELECT * FROM tasks WHERE swarm_id=? AND status='completed' "
                          "AND result_id IS NOT NULL AND unconfirmed_request_id IS NULL", (ledger.swarm_id,))
        for row in rows:
            task = ledger._record(db, row)
            result = task.result or {}
            # Dynamic science has its own versioned, raw-archive-verified
            # projection. Never reinterpret it as legacy passed/failed reward.
            if "generated_plan" in task.acceptance:
                continue
            at = _completed_at(db, task)
            if at is None or not task.owner:
                continue
            report: ValidationReport | ResearchObservation | None = None
            kind: Literal["validated_completion", "scientific_result", "scientific_adoption"] = "validated_completion"
            provenance: Literal["live", "replay", "mock", "contract_local"] = "contract_local"
            scientific_report_id: str | None = None
            adoption_id = _adoption(assets, task, result)
            if result.get("consumed_asset_ids") and adoption_id is None:
                continue
            if result.get("stage") == "evidence_submitted":
                kind = "scientific_result"
                candidates = [ResearchObservation.model_validate_json(r[0]) for r in assets.execute(
                    "SELECT body FROM research_reports WHERE asset_id=?", (result.get("asset_id"),))]
                matches = [r for r in candidates if (r.task_id, r.worker_id, r.fencing_token, r.run_id) ==
                           (task.signal.task_id, task.owner, task.token, result.get("run_id"))]
                if not matches:
                    continue
                scientific = max(matches, key=lambda r: (r.created_at, r.report_id))
                if (not _trusted_science(db, task, scientific, result, at)
                        or not _candidate_matches(assets, scientific.asset_id, Candidate.model_validate_json(scientific.candidate_json))):
                    continue
                report, provenance = scientific, scientific.provenance
                scientific_report_id = scientific.report_id
            else:
                if not task.effect_applied or result.get("applied") is not True:
                    continue
                validation = _validation(assets, result)
                if validation is None:
                    continue
                candidate = Candidate.model_validate_json(validation.candidate_json)
                # Ordinary Worker persists its pre-claim, zero-based AttemptId;
                # research hosts use the post-claim count. Neither is the lease token.
                expected_attempt = task.attempts - 1 if "worker_id" in result else task.attempts
                # File reports use wall time; the ledger may use a controlled
                # clock. Completed effect authority already passed the original
                # applicator's expiry guard. Do not compare different domains or
                # revalidate a historical accepted result against today's clock.
                if (not validation.passed or validation.expires_at <= validation.created_at
                        or validation.asset_id != result.get("candidate_asset_id")
                        or validation.attempt != candidate.attempt or candidate.scope != task.signal.scope
                        or _OBJECT.validate_json(validation.policy_json) != task.acceptance.get("validation_policy", task.acceptance.get("file_policy"))):
                    continue
                if (result.get("worker_id", task.owner) != task.owner or result.get("fencing_token", task.token) != task.token
                        or not _candidate_matches(assets, validation.asset_id, candidate)):
                    continue
                if "worker_id" in result and task.owner != f"{candidate.attempt.agent.role}-{candidate.attempt.agent.instance}":
                    continue
                if candidate.research is not None:
                    sources = [validation.asset_id, *TypeAdapter(list[str]).validate_python(result.get("consumed_asset_ids", []))]
                    scientific_reports = [ResearchObservation.model_validate_json(r[0]) for source in sources for r in assets.execute(
                        "SELECT body FROM research_reports WHERE asset_id=?", (source,))]
                    verified = [r for r in scientific_reports if r.task_id == task.signal.task_id and r.worker_id == task.owner
                                and r.fencing_token == task.token and _trusted_science(db, task, r, {
                                    "scientific_verdict": r.scientific_verdict, "execution_state": r.execution_state,
                                    "provenance": r.provenance}, at)
                                and _candidate_matches(assets, r.asset_id, Candidate.model_validate_json(r.candidate_json))
                                and _application_source(db, assets, ledger, task, candidate, r, adoption_id)]
                    if not verified:
                        continue
                    scientific = max(verified, key=lambda r: (r.created_at, r.report_id))
                    scientific_report_id, provenance = scientific.report_id, scientific.provenance
                    kind = "scientific_adoption" if adoption_id is not None else "scientific_result"
                elif (candidate.attempt.task_id != task.signal.task_id or candidate.attempt.attempt != expected_attempt
                      or "report_id" not in result):
                    # Historical report lookup is only for the scientific host's
                    # approved apply chain, never an ordinary Worker shortcut.
                    continue
                # The completed authority supplies worker/token; the report is bound to
                # the identical candidate/result and validated policy, never a caller flag.
                report = validation
                reported_provenance = result.get("provenance")
                if candidate.research is None and reported_provenance in {"live", "replay", "mock", "contract_local"}:
                    provenance = cast(Literal["live", "replay", "mock", "contract_local"], reported_provenance)
            if task.result_id is not None and report is not None:
                facts.append(FeedbackFact(source_id=task.result_id, kind=kind, task_id=task.signal.task_id,
                                          worker_id=task.owner, pipe_key=task.signal.required_capability or task.signal.task_kind,
                                          at=at, report_id=report.report_id, scientific_report_id=scientific_report_id,
                                          adoption_id=adoption_id, provenance=provenance))
    return sorted(facts, key=lambda fact: (fact.at, fact.source_id, fact.kind))


def _completed_at(db: sqlite3.Connection, task: TaskRecord) -> float | None:
    if task.status != "completed" or task.result_id is None or not task.owner:
        return None
    confirmed = db.execute("SELECT unconfirmed_request_id FROM tasks WHERE swarm_id=? AND task_id=?",
                           (task.swarm_id, task.signal.task_id)).fetchone()
    if confirmed is None or confirmed[0] is not None:
        return None
    completed = db.execute("SELECT at,body FROM task_audit WHERE swarm_id=? AND task_id=? AND event='completed'",
                           (task.swarm_id, task.signal.task_id)).fetchall()
    anchors = [r[0] for r in completed if _OBJECT.validate_json(r[1]).get("result_id") == task.result_id
               and _OBJECT.validate_json(r[1]).get("token") == task.token]
    attempt = db.execute("SELECT worker_id,outcome FROM task_attempts WHERE swarm_id=? AND task_id=? AND token=?",
                         (task.swarm_id, task.signal.task_id, task.token)).fetchone()
    return float(anchors[0]) if len(anchors) == 1 and attempt is not None and tuple(attempt) == (task.owner, "completed") else None


def _validation(assets: sqlite3.Connection, result: dict[str, JsonValue]) -> ValidationReport | None:
    report_id = result.get("report_id")
    approval: PromotionReceipt | None = None
    if "report_id" not in result:
        # Original ResearchService.apply omitted report_id. The existing unique
        # approval supplies its precise report; do not choose a passing report.
        row = assets.execute("SELECT report_id,body FROM approvals WHERE asset_id=?",
                             (result.get("candidate_asset_id"),)).fetchone()
        if row is None:
            return None
        approval = PromotionReceipt.model_validate_json(row[1])
        report_id = row[0]
        if approval.report_id != report_id or approval.asset_id != result.get("candidate_asset_id"):
            return None
    row = assets.execute("SELECT body FROM reports WHERE report_id=?", (report_id,)).fetchone()
    if row is None:
        return None
    report = ValidationReport.model_validate_json(row[0])
    if (report.report_id != report_id or approval is not None and (
            approval.policy_version != report.policy_version
            or not report.created_at <= approval.promoted_at < report.expires_at)):
        return None
    return report


def _application_source(db: sqlite3.Connection, assets: sqlite3.Connection, ledger: TaskLedger,
                        task: TaskRecord, candidate: Candidate, report: ResearchObservation,
                        adoption_id: str | None) -> bool:
    source_candidate = Candidate.model_validate_json(report.candidate_json)
    if adoption_id is not None:
        execution_row = assets.execute("SELECT body FROM consumptions WHERE execution_id=?", (adoption_id,)).fetchone()
        if execution_row is None:
            return False
        execution = ConsumptionExecution.model_validate_json(execution_row[0])
        if (report.purpose != "inheritance" or report.asset_id != execution.asset_id
                or execution.candidate != candidate or source_candidate.research != candidate.research
                or candidate.attempt.task_id != task.signal.task_id or candidate.attempt.attempt != task.attempts):
            return False
    elif source_candidate != candidate or report.asset_id != (task.result or {}).get("candidate_asset_id"):
        return False
    elif report.purpose == "original":
        return candidate.attempt.task_id == task.signal.task_id
    elif report.purpose != "reproduction":
        return False
    # Reproduction observes the author's Candidate; inheritance observes that
    # same source while applying the recorded child. Bind it to the completed
    # author and its original run, not the consumer's Candidate AttemptId.
    source_id = source_candidate.attempt.task_id
    if source_id not in task.dependencies:
        return False
    row = db.execute("SELECT * FROM tasks WHERE swarm_id=? AND task_id=?", (task.swarm_id, source_id)).fetchone()
    if row is None:
        return False
    source = ledger._record(db, row)
    source_at = _completed_at(db, source)
    result = source.result or {}
    if source_at is None or result.get("stage") != "evidence_submitted" or result.get("asset_id") != report.asset_id:
        return False
    originals = [ResearchObservation.model_validate_json(r[0]) for r in assets.execute(
        "SELECT body FROM research_reports WHERE asset_id=?", (report.asset_id,))]
    return any(r.purpose == "original" and (r.task_id, r.worker_id, r.fencing_token, r.run_id) ==
               (source_id, source.owner, source.token, result.get("run_id"))
               and Candidate.model_validate_json(r.candidate_json) == source_candidate
               and scientific_plan(r.plan_json) == scientific_plan(report.plan_json)
               and r.provenance == report.provenance and _trusted_science(db, source, r, result, source_at) for r in originals)


def _trusted_science(db: sqlite3.Connection, task: TaskRecord, report: ResearchObservation,
                     result: dict[str, JsonValue], at: float) -> bool:
    candidate = Candidate.model_validate_json(report.candidate_json)
    claim = candidate.research
    evaluated = _OBJECT.validate_json(report.result_json)
    if (claim is None or candidate.scope != task.signal.scope or report.created_at > at
            or report.scientific_verdict != "passed" or report.execution_state != "succeeded" or not known_effect(report)
            or result.get("scientific_verdict") != report.scientific_verdict
            or result.get("execution_state") != report.execution_state or result.get("provenance") != report.provenance
            or any(evaluated.get(key) != getattr(report, key) for key in ("scientific_verdict", "execution_state", "provenance"))
            or _OBJECT.validate_json(claim.model_dump_json()) != task.acceptance.get("research_claim")
            or _OBJECT.validate_json(report.plan_json) != task.acceptance.get("experiment_plan")
            or (report.plan_id, report.criterion_version, report.conditions) != (claim.plan_id, claim.criterion_version, claim.conditions)):
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
                                          or report.source_attempt is not None and candidate.attempt != report.source_attempt):
        return False
    events = [_OBJECT.validate_json(r[0]) for r in db.execute(
        "SELECT body FROM task_audit WHERE swarm_id=? AND task_id=? AND event='research_execution'",
        (task.swarm_id, task.signal.task_id))]
    confirmations = [_OBJECT.validate_json(r[0]) for r in db.execute(
        "SELECT body FROM task_audit WHERE swarm_id=? AND task_id=? AND event='execution_confirmed'",
        (task.swarm_id, task.signal.task_id))]
    matching = [e for e in events if e.get("run_id") == report.run_id and e.get("worker_id") == task.owner and e.get("token") == source_token]
    results = [e.get("result") for e in matching]
    return any(isinstance(r, dict) and r.get("effect_state") in {"known", "confirmed"}
               and r.get("execution_state") == "succeeded" and r.get("scientific_verdict") == "passed"
               and r.get("provenance") == report.provenance for r in results) and any(
                   e.get("request_id") == report.run_id and e.get("token") == source_token for e in confirmations)


def _candidate_matches(db: sqlite3.Connection, asset_id: str, candidate: Candidate) -> bool:
    row = db.execute("SELECT body FROM assets WHERE asset_id=?", (asset_id,)).fetchone()
    if row is None:
        return False
    body = _OBJECT.validate_json(row[0])
    strategy = body.get("strategy")
    return (body.get("asset_id") == asset_id and isinstance(strategy, list) and len(strategy) == 2
            and isinstance(strategy[1], str) and strategy[1].startswith("local_candidate_json:")
            and Candidate.model_validate_json(strategy[1].removeprefix("local_candidate_json:")) == candidate)


def _adoption(db: sqlite3.Connection, task: TaskRecord, result: dict[str, JsonValue]) -> str | None:
    execution_id = result.get("execution_id")
    if not isinstance(execution_id, str) or not result.get("consumed_asset_ids"):
        return None
    row = db.execute("SELECT body FROM adoptions WHERE execution_id=?", (execution_id,)).fetchone()
    original = db.execute("SELECT body FROM consumptions WHERE execution_id=?", (execution_id,)).fetchone()
    if row is None or original is None:
        return None
    receipt = AdoptionReceipt.model_validate_json(row[0])
    execution = ConsumptionExecution.model_validate_json(original[0])
    context = receipt.context
    if (not task.effect_applied or receipt.result_id != task.result_id or receipt.context != execution.context
            or receipt.candidate_asset_id != execution.candidate_asset_id or receipt.asset_id != execution.asset_id
            or receipt.candidate_asset_id != result.get("candidate_asset_id")
            or receipt.asset_id not in TypeAdapter(list[str]).validate_python(result.get("consumed_asset_ids", []))
            or context.input_context != result.get("input_context")
            or context.execution_id != execution_id
            or not _candidate_matches(db, execution.candidate_asset_id, execution.candidate)
            or (context.swarm_id, context.task_id, context.worker_id, context.fencing_token, context.scope) !=
            (task.swarm_id, task.signal.task_id, task.owner, task.token, task.signal.scope)):
        return None
    return execution_id


def policy_diagnostics(config: object, *, rebuild_to: Path | None = None,
                       seed: int = 0, limit: int = 100) -> dict[str, JsonValue]:
    # Imported here to keep the evidence reader independent from the entrypoint.
    from swarm.pheromone import PheromoneField, PreviewField
    from swarm.research.models import HostConfig
    from swarm.router import Router
    host = HostConfig.model_validate(config)
    for value in (host.ledger_path, host.workspace, host.assets_root, host.evidence_root):
        if not Path(value).is_absolute():
            raise ValueError("host_paths_must_be_absolute")
        no_links(Path(value))
    ledger = ReadonlyLedger(Path(host.ledger_path), host.swarm_id)
    facts = trusted_facts(ledger, Path(host.assets_root))
    if rebuild_to is not None:
        if not rebuild_to.is_absolute():
            raise ValueError("rebuild_requires_absolute_derived_path")
        destination = rebuild_to.absolute()
        no_links(destination)
        if destination.exists() or any(destination.resolve().is_relative_to(Path(p).resolve()) for p in (
                host.workspace, host.assets_root, host.evidence_root, str(ledger.path.parent),
                str(Path(__file__).resolve().parents[1]))):
            raise ValueError("rebuild_requires_new_separate_derived_path")
        field = PheromoneField(destination, ledger=ledger)
        field.synchronize(facts)
    else:
        field = PreviewField(ledger, facts)
    decision = Router(field, strategy_version="v0.1", rng=random.Random(seed)).recommend(
        host.worker_id, host.locality(), {key: 1.0 for key in host.capabilities}, limit=limit, record_audit=False)
    decision.pop("recommendation", None)  # Never expose task payloads to operator diagnostics.
    return {"policy": decision, "feedback": [ _OBJECT.validate_json(f.model_dump_json()) for f in facts],
            "source": "existing_authoritative_facts", "rebuild": rebuild_to is not None,
            "evidence_class": "contract_local", "execution_invoked": False}
