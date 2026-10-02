"""Read generated science from the original task, asset, report and archive.

This module owns no persistence and grants no execution permission. B's reader
recomputes science from archived bytes; this projection verifies its original
ledger authority before exposing a proposed contribution.
"""
from __future__ import annotations

from pathlib import Path
import sqlite3

from pydantic import JsonValue, TypeAdapter

from local_assets.generated_validation import read_generated_observation
from local_assets.models import Candidate
from local_assets.paths import no_links
from local_assets.research_models import ResearchObservation
from orchestration.experiments.generated import GeneratedExperimentPlan, GeneratedResult
from orchestration.experiments.generated_executor import GENERATED_OUTPUT
from orchestration.experiments.trusted import TrustedCriteriaRecord, TrustedCriteriaRegistry
from swarm.feedback import ReadonlyLedger, _candidate_matches, _completed_at, readonly
from swarm.models import TaskRecord
from swarm.research.policy import ThreeAxisResult
from swarm.task_ledger import TaskLedger, connection

_OBJECT = TypeAdapter(dict[str, JsonValue])


def _audit(db: sqlite3.Connection, task: TaskRecord, event: str) -> list[tuple[int, float, dict[str, JsonValue]]]:
    return [(row[0], row[1], _OBJECT.validate_json(row[2])) for row in db.execute(
        "SELECT sequence,at,body FROM task_audit WHERE swarm_id=? AND task_id=? AND event=?",
        (task.swarm_id, task.signal.task_id, event))]


def _execution_anchor(db: sqlite3.Connection, task: TaskRecord, report: ResearchObservation,
                      envelope: dict[str, JsonValue], completed_at: float) -> float | None:
    token = report.source_fencing_token
    if token is None or token != task.token or report.source_swarm_id != task.swarm_id:
        return None
    attempt = report.source_attempt
    count = db.execute("SELECT COUNT(*) FROM task_attempts WHERE swarm_id=? AND task_id=? AND token<=?",
                       (task.swarm_id, task.signal.task_id, token)).fetchone()[0]
    if attempt is None or (attempt.task_id, attempt.attempt) != (task.signal.task_id, count):
        return None
    starts = [event for event in _audit(db, task, "execution_unconfirmed")
              if event[2].get("request_id") == report.run_id and event[2].get("token") == token]
    confirms = [event for event in _audit(db, task, "execution_confirmed")
                if event[2].get("request_id") == report.run_id and event[2].get("token") == token]
    executions = [event for event in _audit(db, task, "research_execution")
                  if event[2].get("run_id") == report.run_id]
    completions = [event for event in _audit(db, task, "completed")
                   if event[2].get("result_id") == task.result_id and event[2].get("token") == token]
    if not (len(starts) == len(confirms) == len(executions) == len(completions) == 1):
        return None
    start, confirmed, execution, completed = starts[0], confirms[0], executions[0], completions[0]
    if (execution[2].get("worker_id") != task.owner or execution[2].get("token") != token
            or execution[2].get("result") != envelope
            or not start[0] < execution[0] < completed[0]
            or not start[0] < confirmed[0] < completed[0]
            or not start[1] <= report.created_at <= completed_at):
        return None
    return start[1]


def _bound_result(db: sqlite3.Connection, assets: sqlite3.Connection, ledger: TaskLedger,
                  task: TaskRecord, report: ResearchObservation, plan: GeneratedExperimentPlan,
                  registry: TrustedCriteriaRegistry, at: float,
                  archive_root: Path | None) -> GeneratedResult | None:
    submitted = task.result or {}
    if (report.report_id != submitted.get("report_id")
            or report.asset_id != plan.candidate_asset_id
            or (report.task_id, report.worker_id, report.fencing_token, report.run_id) !=
            (task.signal.task_id, task.owner, task.token, submitted.get("run_id"))
            or report.plan_json != plan.model_dump_json()
            or plan.task_id != task.signal.task_id
            or task.signal.payload.get("project_id") != plan.project_id
            or task.signal.payload.get("branch_id") != plan.branch_id
            or task.acceptance.get("generated_plan") != plan.model_dump(mode="json")
            or report.execution_state != "succeeded"):
        return None
    envelope = _OBJECT.validate_json(report.result_json)
    if (envelope.get("schema_version") != "generated-experiment/v1"
            or envelope.get("effect_state") != "known"
            or any(envelope.get(key) != getattr(report, key)
                   or submitted.get(key) != getattr(report, key)
                   for key in ("execution_state", "scientific_verdict", "provenance"))):
        return None
    started_at = _execution_anchor(db, task, report, envelope, at)
    if started_at is None:
        return None
    frozen_approval = envelope.get("criteria_approval")
    if not isinstance(frozen_approval, dict):
        return None
    approval = TrustedCriteriaRecord.model_validate(frozen_approval)
    if registry.approval(plan.evaluation) != approval or approval.approved_at > started_at:
        return None
    candidate = Candidate.model_validate_json(report.candidate_json)
    if candidate.scope != task.signal.scope or not _candidate_matches(assets, report.asset_id, candidate):
        return None
    author_row = db.execute("SELECT * FROM tasks WHERE swarm_id=? AND task_id=?",
                            (ledger.swarm_id, candidate.attempt.task_id)).fetchone()
    if author_row is None:
        return None
    author_task = ledger._record(db, author_row)
    author_at = _completed_at(db, author_task)
    if (author_at is None or author_at > at or not author_task.owner
            or author_task.signal.scope != task.signal.scope
            or author_task.signal.payload.get("project_id") != plan.project_id
            or (author_task.result or {}).get("asset_id") != report.asset_id
            or candidate.attempt.attempt != author_task.attempts
            or approval.approved_by == author_task.owner):
        return None
    # Check the archive location before B opens it; never follow caller links.
    persisted = GeneratedResult.model_validate(envelope.get("experiment_result"))
    path = Path(persisted.archive_path)
    no_links(path)
    if archive_root is not None and not path.resolve().is_relative_to(archive_root.resolve()):
        return None
    if (persisted.context.author != author_task.owner or persisted.context.reviewer != approval.approved_by
            or persisted.context.worker_id != task.owner
            or persisted.remote_effect != "known" or persisted.cleanup_state != "destroyed"
            or not persisted.sandbox_id or persisted.exit_code != 0):
        return None
    # B validates frozen conditions, code, evaluator, approval and every raw
    # artifact digest, then re-evaluates. Its cached trusted/mode flags grant no authority.
    return read_generated_observation(report, criteria_registry=registry)


def trusted_generated_feedback(ledger: TaskLedger, assets_root: Path, *,
                               criteria_registry: TrustedCriteriaRegistry | None,
                               project_id: str | None = None,
                               archive_root: Path | None = None) -> list[ThreeAxisResult]:
    if criteria_registry is None or not (assets_root / "assets.sqlite3").exists():
        return []
    read = readonly if isinstance(ledger, ReadonlyLedger) else connection
    no_links(ledger.path)
    no_links(assets_root / "assets.sqlite3")
    results: list[ThreeAxisResult] = []
    with read(ledger.path) as db, read(assets_root / "assets.sqlite3") as assets:
        rows = db.execute("SELECT * FROM tasks WHERE swarm_id=? AND status='completed' "
                          "AND result_id IS NOT NULL AND unconfirmed_request_id IS NULL", (ledger.swarm_id,))
        for row in rows:
            task = ledger._record(db, row)
            submitted = task.result or {}
            frozen = task.acceptance.get("generated_plan")
            if not isinstance(frozen, dict) or submitted.get("stage") != "evidence_submitted":
                continue
            plan = GeneratedExperimentPlan.model_validate(frozen)
            if project_id is not None and plan.project_id != project_id:
                continue
            at = _completed_at(db, task)
            if at is None or task.result_id is None or task.owner is None:
                continue
            records = assets.execute("SELECT body FROM research_reports WHERE report_id=? AND asset_id=?",
                                     (submitted.get("report_id"), submitted.get("asset_id"))).fetchall()
            if len(records) != 1:
                continue
            report = ResearchObservation.model_validate_json(records[0][0])
            result = _bound_result(db, assets, ledger, task, report, plan, criteria_registry, at, archive_root)
            if result is None:
                continue
            outputs = [artifact for artifact in result.artifacts
                       if artifact.archive_path == f"outputs/{GENERATED_OUTPUT}"]
            if len(outputs) != 1:
                continue
            results.append(ThreeAxisResult(
                result_id=task.result_id, report_id=report.report_id, task_id=task.signal.task_id,
                actor=task.owner, source_ref="generated-output:sha256:" + outputs[0].sha256,
                provenance=report.provenance, execution=result.assessment.execution,
                hypothesis=result.assessment.hypothesis, contribution="proposed", at=at,
                asset_id=report.asset_id, branch_id=plan.branch_id, project_id=plan.project_id,
                experiment_schema=plan.schema_version, run_id=report.run_id, sandbox_id=report.sandbox_id,
                conditions=report.conditions, purpose=report.purpose, reasons=result.assessment.reasons))
    return results
