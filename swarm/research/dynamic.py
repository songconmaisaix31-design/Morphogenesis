"""Generated research tools over the original executor, ledger and asset chain.

This is a host adapter: it owns no scheduling, execution database or approval
algorithm. Candidate text is stored and statically checked, never imported or
executed on the host. Host settings are absent from the MCP tool schemas.
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import TYPE_CHECKING, Literal
from uuid import uuid4

from pydantic import Field, JsonValue, TypeAdapter, model_validator

from contracts.base import Contract
from contracts.identity import AttemptId
from local_assets.generated_validation import (
    approve_generated, generated_candidate, generated_result_payload, generated_validation, record_generated_observation,
)
from local_assets.models import AssetSafetyError, Candidate
from local_assets.paths import git, no_links
from local_assets.research_models import ResearchObservation
from local_assets.research import require_reproduced
from local_assets.snapshot import snapshot_revision
from local_assets.validate import blast_radius, inspect_candidate
from orchestration.experiments.generated import (
    ApprovedEnvironment, BackendProfile, GeneratedContext, GeneratedExperimentPlan, GeneratedResult,
)
from orchestration.experiments.generated_executor import GeneratedExperimentExecutor, read_generated_result
from orchestration.experiments.fixture import GeneratedFixtureBackend
from orchestration.experiments.sandbox_adapter import LocalCpuSandboxBackend
from orchestration.experiments.trusted import (
    IsolationProbeRecord, TrustedCriteriaRecord, TrustedCriteriaRegistry, TrustedProbeRegistry,
)

if TYPE_CHECKING:
    from swarm.research.service import Purpose, ResearchService

_OBJECT = TypeAdapter(dict[str, JsonValue])


class GeneratedHostSettings(Contract):
    """One explicitly selected host environment; mock grants no live authority."""

    mode: Literal["mock", "live"]
    environment: ApprovedEnvironment
    resources: BackendProfile = Field(default_factory=BackendProfile)
    criteria: tuple[TrustedCriteriaRecord, ...] = Field(min_length=1)
    probes: tuple[IsolationProbeRecord, ...] = ()
    data_files: dict[str, str] = Field(default_factory=dict)
    data_refs: tuple[str, ...] = ()
    domain: str = "127.0.0.1:8097"
    protocol: Literal["http", "https"] = "http"
    api_key_env: str | None = None
    instance_id: str | None = None
    runtime_profile: str | None = None
    server_process_limit: int | None = Field(default=None, gt=0, strict=True)
    fixture_workspace: str | None = None
    fixture_output: str | None = None
    fixture_outcome: Literal["succeeded", "failed", "timeout", "unknown"] = "succeeded"

    @model_validator(mode="after")
    def fixture_binding(self) -> GeneratedHostSettings:
        if self.mode == "mock":
            if not self.fixture_workspace or not Path(self.fixture_workspace).is_absolute() or not self.instance_id:
                raise ValueError("mock_requires_dedicated_host_fixture_workspace_and_identity")
        elif self.fixture_workspace is not None or self.fixture_output is not None or self.fixture_outcome != "succeeded":
            raise ValueError("fixture_settings_require_mock_mode")
        return self


class GeneratedResearch:
    def __init__(self, service: ResearchService, executor: GeneratedExperimentExecutor | None) -> None:
        self.service = service
        self.settings = GeneratedHostSettings.model_validate(service.config.generated_experiments)
        self.criteria = TrustedCriteriaRegistry(self.settings.criteria)
        self.probes = TrustedProbeRegistry(self.settings.probes)
        if executor is None:
            if self.settings.mode == "mock":
                fixture = GeneratedFixtureBackend(environment=self.settings.environment,
                    resources=self.settings.resources,
                    output=self.settings.fixture_output.encode("utf-8") if self.settings.fixture_output is not None else None,
                    instance_id=self.settings.instance_id or "", outcome=self.settings.fixture_outcome)
                self.probes = fixture.probe_registry
                executor = GeneratedExperimentExecutor(fixture)
            else:
                secret = os.environ.get(self.settings.api_key_env) if self.settings.api_key_env else None
                if self.settings.api_key_env and not secret:
                    raise AssetSafetyError("generated_backend_credential_missing")
                backend = LocalCpuSandboxBackend(
                    domain=self.settings.domain, protocol=self.settings.protocol, api_key=secret,
                    probe=self.settings.probes[0] if len(self.settings.probes) == 1 else None,
                    instance_id=self.settings.instance_id, runtime_profile=self.settings.runtime_profile,
                    server_process_limit=self.settings.server_process_limit)
                executor = GeneratedExperimentExecutor(backend)
        if executor.backend.provenance != self.settings.mode:
            raise AssetSafetyError("generated_backend_provenance_mismatch")
        # Registries come only from the frozen host configuration; never from
        # the candidate, tool call or supplied backend's own assertion.
        self.executor = GeneratedExperimentExecutor(executor.backend, probe_registry=self.probes,
                                                    criteria_registry=self.criteria)

    def _authorized(self, task_id: str) -> None:
        s = self.service
        s._research_action("experiment")
        s._authorize_project(s.config.project_id)
        s._task(task_id, require_capability=True)
        if s.config.research_envelope is None or s.budget is None:
            raise AssetSafetyError("generated_host_authorization_required")

    def _check_plan(self, task_id: str, plan: GeneratedExperimentPlan) -> None:
        self._authorized(task_id)
        s = self.service
        task = s._task(task_id)
        if (plan.task_id != task_id or plan.project_id != s.config.project_id
                or plan.authorization_ref != s.config.authorization_ref
                or plan.branch_id != task.signal.payload.get("branch_id")):
            raise PermissionError("generated_plan_outside_host_task_or_project")
        s._require_branch(plan.project_id, plan.branch_id)
        if plan.environment != self.settings.environment or plan.backend != self.settings.resources:
            raise PermissionError("generated_environment_outside_host_approval")
        if not set(plan.data_refs).issubset(self.settings.data_refs):
            raise PermissionError("generated_data_outside_host_approval")
        approval = self.criteria.approval(plan.evaluation)
        if approval is None or approval.approved_at > s.ledger.now():
            raise PermissionError("host_frozen_evaluation_required")

    def _data(self, plan: GeneratedExperimentPlan) -> dict[str, bytes]:
        data: dict[str, bytes] = {}
        for entry in plan.data:
            path_text = self.settings.data_files.get(entry.name)
            if path_text is None:
                raise PermissionError("generated_data_file_not_host_bound")
            path = Path(path_text)
            if not path.is_absolute():
                raise PermissionError("generated_data_requires_absolute_host_path")
            no_links(path)
            if path.stat().st_size != entry.size_bytes:
                raise AssetSafetyError("generated_data_size_changed")
            data[entry.name] = path.read_bytes()
        return data

    @staticmethod
    def _files(candidate: Candidate) -> dict[str, bytes]:
        prefix = "" if candidate.scope == "." else candidate.scope + "/"
        return {c.path.removeprefix(prefix): c.after.encode("utf-8")
                for c in candidate.changes if c.after is not None}

    def plan(self, task_id: str) -> GeneratedExperimentPlan:
        value = self.service._task(task_id).acceptance.get("generated_plan")
        if not isinstance(value, dict):
            raise AssetSafetyError("frozen_generated_plan_required")
        plan = GeneratedExperimentPlan.model_validate(value)
        self._check_plan(task_id, plan)
        return plan

    def _candidate_context(self, task_id: str, token: int, plan: GeneratedExperimentPlan,
                           purpose: Purpose, run_id: str) -> GeneratedContext:
        s = self.service
        task = s._task(task_id)
        candidate = s._asset(task_id, plan.candidate_asset_id)
        origin = s._task(candidate.attempt.task_id)
        author = origin.owner
        approval = self.criteria.approval(plan.evaluation)
        if author is None or approval is None or approval.approved_by == author:
            raise AssetSafetyError("independent_frozen_evaluator_required")
        if purpose == "original":
            if candidate.attempt != AttemptId(task_id=task_id, agent=s.config.agent, attempt=task.attempts):
                raise AssetSafetyError("generated_original_attempt_mismatch")
        elif (origin.status != "completed" or origin.signal.task_id not in task.dependencies
              or author == s.config.worker_id or candidate.attempt.task_id == task_id):
            raise AssetSafetyError("generated_independent_dependency_required")
        return GeneratedContext(run_id=run_id, task_id=task_id, worker_id=s.config.worker_id,
                                fencing_token=token, author=author, reviewer=approval.approved_by)

    def prepare(self, task_id: str, token: int, plan: GeneratedExperimentPlan,
                files: dict[str, str] | None, *, asset_id: str | None, purpose: Purpose) -> dict[str, JsonValue]:
        s = self.service
        lease = s._lease(task_id, token)
        s.ledger.assert_execution_confirmed(lease)
        self._check_plan(task_id, plan)
        task = s._task(task_id)
        previous = task.acceptance.get("generated_plan")
        if asset_id is None:
            if purpose != "original" or files is None:
                raise ValueError("new_generated_candidate_requires_original_code")
            bodies = {name: text.encode("utf-8") for name, text in files.items()}
            preparation = self.executor.prepare(plan, bodies, self._data(plan))
            if not preparation.static.passed:
                raise AssetSafetyError("static_security_failed")
            if previous is not None:
                saved = GeneratedExperimentPlan.model_validate(previous)
                candidate = s._asset(task_id, saved.candidate_asset_id)
                if (bodies != self._files(candidate)
                        or plan.candidate_revision not in {saved.candidate_revision, candidate.base_head}):
                    raise AssetSafetyError("generated_plan_already_frozen")
                plan = plan.model_copy(update={"candidate_revision": saved.candidate_revision})
                asset_id = saved.candidate_asset_id
            else:
                workspace = Path(s.config.workspace)
                if git(workspace, "rev-parse", "HEAD").decode().strip() != plan.candidate_revision:
                    raise AssetSafetyError("generated_candidate_base_revision_changed")
                # Reuse native scoped snapshots for edits after an earlier apply.
                # Host-derived preimages bind the diff; caller text supplies only
                # the proposed after-bytes. No worktree/index/ref is modified.
                revision, head = snapshot_revision(workspace, task.signal.scope, s.store.root / "snapshots")
                plan = plan.model_copy(update={"candidate_revision": revision})
                candidate = generated_candidate(plan, bodies,
                    attempt=AttemptId(task_id=task_id, agent=s.config.agent, attempt=task.attempts),
                    scope=task.signal.scope, summary=plan.claim)
                changes = tuple(change.model_copy(update={"before":
                    git(workspace, "show", revision + ":" + change.path).decode("utf-8")
                    if git(workspace, "ls-tree", revision, "--", change.path) else None})
                    for change in candidate.changes)
                candidate = candidate.model_copy(update={"base_head": head, "changes": changes})
                count, lines = blast_radius(candidate)
                candidate = candidate.model_copy(update={"declared_files": count, "declared_lines": lines})
                inspect_candidate(candidate)
                asset_id = s.store.publish(candidate)
                s._lease(task_id, token)
        else:
            if files is not None:
                raise ValueError("existing_generated_asset_does_not_accept_replacement_code")
            candidate = s._asset(task_id, asset_id)
            if plan.candidate_revision not in {candidate.base_revision, candidate.base_head}:
                raise AssetSafetyError("generated_candidate_base_revision_changed")
            plan = plan.model_copy(update={"candidate_revision": candidate.base_revision})
            bodies = self._files(candidate)
        frozen = plan.model_copy(update={"candidate_asset_id": asset_id})
        self._candidate_context(task_id, token, frozen, purpose, "preparation")
        if previous is not None:
            if previous != frozen.model_dump(mode="json") or task.acceptance.get("generated_purpose") != purpose:
                raise AssetSafetyError("generated_plan_already_frozen")
            report_id = task.acceptance.get("generated_report_id")
            if not isinstance(report_id, str):
                raise AssetSafetyError("generated_preparation_incomplete")
            report = s.store.generated_report(report_id)
        else:
            preparation = self.executor.prepare(frozen, bodies, self._data(frozen))
            # Static report/plan freeze happens before any execution. This lock
            # protects only local metadata, never a model or sandbox call.
            with s.ledger.transaction() as db:
                row = s.ledger._owned(db, s._lease(task_id, token))
                acceptance = _OBJECT.validate_json(row["acceptance"])
                if "generated_plan" in acceptance or db.execute(
                        "SELECT 1 FROM task_audit WHERE swarm_id=? AND task_id=? AND event='execution_unconfirmed'",
                        (s.config.swarm_id, task_id)).fetchone() is not None:
                    raise AssetSafetyError("generated_plan_cannot_change_after_execution")
                report = generated_validation(s.store, asset_id, frozen, bodies, preparation.isolation,
                                              probe_registry=self.probes, data=self._data(frozen))
                acceptance.update({"generated_plan": frozen.model_dump(mode="json"),
                                   "generated_report_id": report.report_id, "generated_purpose": purpose,
                                   "research_claim": candidate.research.model_dump(mode="json") if candidate.research else None})
                db.execute("UPDATE tasks SET acceptance=?,updated_at=? WHERE swarm_id=? AND task_id=?",
                           (_OBJECT.dump_json(acceptance).decode(), s.ledger.now(), s.config.swarm_id, task_id))
                approval = self.criteria.approval(frozen.evaluation)
                s.ledger._event(db, task_id, "generated_plan_frozen", {
                    "plan": frozen.model_dump(mode="json"), "asset_id": asset_id,
                    "criteria_approval": approval.model_dump(mode="json") if approval else None,
                    "worker_id": s.config.worker_id, "token": token})
                s.ledger._owned(db, lease)
        return {"asset_id": asset_id, "plan": frozen.model_dump(mode="json"),
                "report": report.model_dump(mode="json"), "admitted": report.passed,
                "execution_started": False, "provenance": self.settings.mode}

    def admit(self, task_id: str, token: int) -> dict[str, JsonValue]:
        s = self.service
        s._lease(task_id, token)
        plan = self.plan(task_id)
        candidate = s._asset(task_id, plan.candidate_asset_id)
        self.executor.admit(self.executor.prepare(plan, self._files(candidate), self._data(plan)))
        s._budget_ready(required=True)
        return {"admitted": True, "execution_started": False, "plan_id": plan.plan_id,
                "provenance": self.settings.mode, "budget_reservation": "on_execute"}

    def validate(self, task_id: str, token: int, asset_id: str) -> dict[str, JsonValue]:
        s = self.service
        lease = s._lease(task_id, token)
        plan, candidate = self.bound_candidate(task_id, token, asset_id)
        preparation = self.executor.prepare(plan, self._files(candidate), self._data(plan))
        with s.ledger.fenced(lease):
            report = generated_validation(s.store, asset_id, plan, preparation.files, preparation.isolation,
                                          probe_registry=self.probes, data=preparation.data)
        return _OBJECT.validate_json(report.model_dump_json())

    def bound_candidate(self, task_id: str, token: int, asset_id: str) -> tuple[GeneratedExperimentPlan, Candidate]:
        s = self.service
        plan = self.plan(task_id)
        candidate = s._asset(task_id, asset_id)
        if asset_id != plan.candidate_asset_id:
            consumption = s.store.source_consumption(asset_id)
            if (consumption is None or consumption.asset_id != plan.candidate_asset_id
                    or consumption.context.task_id != task_id or consumption.context.worker_id != s.config.worker_id
                    or consumption.context.fencing_token != token):
                raise AssetSafetyError("generated_child_consumption_binding_required")
            plan = plan.model_copy(update={"candidate_asset_id": asset_id, "candidate_revision": candidate.base_revision})
        return plan, candidate

    def approve(self, task_id: str, token: int, asset_id: str, report_id: str) -> dict[str, JsonValue]:
        s = self.service
        self._authorized(task_id)
        s._research_action("review")
        lease = s._lease(task_id, token)
        s.ledger.assert_execution_confirmed(lease)
        _, candidate = self.bound_candidate(task_id, token, asset_id)
        report = s.store.generated_report(report_id)
        if report.asset_id != asset_id:
            raise AssetSafetyError("generated_report_candidate_mismatch")
        source = s.store.source_consumption(asset_id)
        if source is None and candidate.attempt.agent == s.config.agent:
            raise PermissionError("independent_reviewer_required")
        require_reproduced(s.store, asset_id)
        with s.ledger.fenced(lease) as owned:
            approve_generated(s.store, report, owned, proof_ref=report_id)
        s._record_event("candidate_approved", s.config.project_id, task_id=task_id,
                       source_ref=asset_id, payload={"report_id": report_id, "provenance": self.settings.mode})
        return {"asset_id": asset_id, "report_id": report_id, "stage": "approved",
                "adopted": False, "provenance": self.settings.mode}

    def _purpose(self, task_id: str) -> Purpose:
        value = self.service._task(task_id).acceptance.get("generated_purpose")
        if value == "original":
            return "original"
        if value == "reproduction":
            return "reproduction"
        if value == "inheritance":
            return "inheritance"
        if value == "counterexample":
            return "counterexample"
        raise AssetSafetyError("generated_purpose_not_frozen")

    async def execute(self, task_id: str, token: int) -> dict[str, JsonValue]:
        s = self.service
        self.admit(task_id, token)
        plan = self.plan(task_id)
        candidate = s._asset(task_id, plan.candidate_asset_id)
        run_id = uuid4().hex
        context = self._candidate_context(task_id, token, plan, self._purpose(task_id), run_id)
        lease = s._lease(task_id, token)
        if s.budget is None or s.config.research_execution_bound is None:
            raise AssetSafetyError("generated_project_budget_required")
        reservation = s.budget.reserve(s.config.worker_id, task_id, s.config.research_execution_bound, request_id=run_id)
        try:
            s.ledger.begin_execution(lease, run_id, max_executions=s.config.max_experiments_per_task)
            await asyncio.to_thread(self.executor.execute, plan, context, self._files(candidate),
                                    Path(s.config.evidence_root), self._data(plan))
            s._lease(task_id, token)
            result = read_generated_result(s.config.evidence_root, run_id, expected_plan=plan, expected_context=context)
            payload = _OBJECT.validate_python(generated_result_payload(result, criteria_registry=self.criteria))
            s.ledger.record_event("research_execution", {"run_id": run_id, "worker_id": s.config.worker_id,
                                                        "token": token, "result": payload}, task_id=task_id)
            if result.remote_effect == "known":
                s.budget.settle(reservation, None)
                s.ledger.confirm_execution(s._lease(task_id, token), run_id)
            else:
                s.budget.mark_uncertain(reservation)
            return {"run_id": run_id, "result": payload}
        except BaseException:
            s.budget.mark_uncertain(reservation)
            raise

    def _read(self, task_id: str, run_id: str) -> GeneratedResult:
        s = self.service
        lineage = s._run(task_id, run_id)
        saved = lineage.get("result")
        if not isinstance(saved, dict):
            raise AssetSafetyError("generated_execution_lineage_required")
        original = GeneratedResult.model_validate(saved.get("experiment_result"))
        result = read_generated_result(s.config.evidence_root, run_id, expected_plan=self.plan(task_id),
                                       expected_context=original.context)
        if _OBJECT.validate_python(generated_result_payload(result, criteria_registry=self.criteria)) != saved:
            raise AssetSafetyError("generated_archive_disagrees_with_execution_audit")
        return result

    def read(self, task_id: str, run_id: str) -> dict[str, JsonValue]:
        return _OBJECT.validate_python(generated_result_payload(self._read(task_id, run_id), criteria_registry=self.criteria))

    def observe(self, task_id: str, token: int, asset_id: str, run_id: str, purpose: Purpose) -> ResearchObservation:
        s = self.service
        s._lease(task_id, token)
        result = self._read(task_id, run_id)
        if (result.plan.candidate_asset_id != asset_id or purpose != self._purpose(task_id)
                or result.context.worker_id != s.config.worker_id or result.context.fencing_token != token):
            raise AssetSafetyError("generated_observation_host_binding_mismatch")
        with s.ledger.fenced(s._lease(task_id, token)) as owned:
            return record_generated_observation(s.store, asset_id, archive_root=s.config.evidence_root,
                plan=result.plan, context=result.context, purpose=purpose, criteria_registry=self.criteria,
                assert_owned=owned, source_swarm_id=s.config.swarm_id,
                source_attempt=AttemptId(task_id=task_id, agent=s.config.agent, attempt=s._task(task_id).attempts),
                source_fencing_token=result.context.fencing_token)
