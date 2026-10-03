"""Host-bound tools; task assignment remains a voluntary ledger claim."""
from __future__ import annotations

from pathlib import Path
from collections.abc import Callable
from typing import TYPE_CHECKING, Literal, Protocol
from uuid import UUID, uuid4

from pydantic import JsonValue, TypeAdapter

from contracts.identity import AttemptId
from local_assets import AssetApplicator, AssetPromoter, AssetValidator, LocalAssetStore
from local_assets.consume import AssetConsumer
from local_assets.models import AssetSafetyError, Candidate, ConsumptionContext, ValidationPolicy
from local_assets.paths import no_links
from local_assets.research import known_effect, require_inheritance
from local_assets.research_models import ResearchObservation
from local_assets.snapshot import snapshot_revision
from local_assets.validate import inspect_candidate
from swarm.models import ExecutionBound, Lease, Reservation, Signal, TaskRecord
from swarm.budget import BudgetBlocked, BudgetLedger
from swarm.feedback import trusted_facts
from swarm.pheromone import PheromoneField
from swarm.router import Router
from swarm.research.feedback import ResearchFeedbackStore
from swarm.research.knowledge import ResearchKnowledge
from swarm.research.models import HostConfig, NativeInvocationBinding
from swarm.research.policy import Branch, CorrectionEvent, CorrectionKind, SupersessionEvent, ThreeAxisResult
from swarm.research.records import (
    Hypothesis,
    NoteKind,
    ProposalKind,
    ResearchBranch,
    ResearchEvent,
    ResearchNote,
    ResearchProject,
    SourceRef,
    WorkProposal,
)
from swarm.task_ledger import LeaseLost, TaskConflict, TaskLedger, canonical_scope, connection

if TYPE_CHECKING:
    from orchestration.experiments.generated_executor import GeneratedExperimentExecutor
    from swarm.research.dynamic import GeneratedResearch

_OBJECT = TypeAdapter(dict[str, JsonValue])
Purpose = Literal["original", "reproduction", "inheritance", "counterexample"]


class ExperimentBackend(Protocol):
    async def execute(self, plan: dict[str, JsonValue], run_id: str, lease: Lease) -> dict[str, JsonValue]: ...
    def read(self, run_id: str) -> dict[str, JsonValue]: ...
    def evaluate(self, run_id: str, plan: dict[str, JsonValue], lease: Lease) -> dict[str, JsonValue]: ...


class ResearchService:
    def __init__(self, config: HostConfig, *, ledger: TaskLedger | None = None,
                 store: LocalAssetStore | None = None, backend: ExperimentBackend | None = None,
                 generated_executor: GeneratedExperimentExecutor | None = None) -> None:
        # model_copy can bypass validators; reject a mismatched invocation before
        # opening any ledger/store under a different host identity.
        config = HostConfig.model_validate(config.model_dump())
        self.config = config
        for value in (config.ledger_path, config.workspace, config.assets_root, config.evidence_root):
            if not Path(value).is_absolute():
                raise ValueError("host_paths_must_be_absolute")
            no_links(Path(value))
        self.locality = config.locality()
        limits = config.research_envelope.limits if config.research_envelope else None
        self.ledger = ledger or TaskLedger(config.ledger_path, config.swarm_id, limits=limits)
        if self.ledger.swarm_id != config.swarm_id or self.ledger.path != Path(config.ledger_path).resolve():
            raise ValueError("host_ledger_identity_mismatch")
        if limits is not None and self.ledger.limits != limits:
            raise ValueError("host_ledger_limits_mismatch")
        if config.generated_experiments:
            from swarm.research.dynamic import GeneratedHostSettings
            from orchestration.experiments.trusted import TrustedCriteriaRegistry
            settings = GeneratedHostSettings.model_validate(config.generated_experiments)
            criteria = TrustedCriteriaRegistry(settings.criteria)
            if config.research_provenance != settings.mode:
                raise ValueError("generated_host_provenance_mismatch")
            self.store = store or LocalAssetStore(config.assets_root, research_provenance=settings.mode,
                                                  fixture_workspace=settings.fixture_workspace, generated_criteria=criteria)
            if (self.store.research_provenance != settings.mode
                    or self.store.fixture_workspace != (Path(settings.fixture_workspace).resolve()
                                                         if settings.fixture_workspace else None)):
                raise ValueError("host_asset_store_provenance_mismatch")
            if self.store.generated_criteria is None or any(
                    self.store.generated_criteria.approval(record.spec) != record for record in settings.criteria):
                raise ValueError("host_asset_store_evaluation_mismatch")
            self.store.check_fixture_target(Path(config.workspace))
        else:
            self.store = store or LocalAssetStore(config.assets_root)
        if self.store.root != Path(config.assets_root).resolve():
            raise ValueError("host_asset_store_identity_mismatch")
        self.backend = backend
        self.field = PheromoneField(self.ledger.path.with_name("policy-field.sqlite3"), ledger=self.ledger,
                                    clock=self.ledger.clock)
        self.router = Router(self.field, strategy_version="v0.1")
        knowledge_path = config.knowledge_path()
        if not knowledge_path.is_absolute():
            raise ValueError("research_knowledge_path_must_be_absolute")
        no_links(knowledge_path)
        self.knowledge = ResearchKnowledge(knowledge_path, clock=self.ledger.clock)
        self.budget: BudgetLedger | None = None
        if config.research_budget_path is not None and config.research_budget_policy is not None:
            no_links(Path(config.research_budget_path))
            self.budget = BudgetLedger(config.research_budget_path, config.project_id,
                                       config.research_budget_policy, clock=self.ledger.clock)
        self._native_reservation()
        self.generated: GeneratedResearch | None = None
        if config.generated_experiments:
            from swarm.research.dynamic import GeneratedResearch
            self.generated = GeneratedResearch(self, generated_executor)
        elif generated_executor is not None:
            raise AssetSafetyError("generated_executor_requires_host_configuration")
        feedback_path = self.ledger.path.with_name("research-feedback.sqlite3")
        no_links(feedback_path)
        self.feedback_store = ResearchFeedbackStore(feedback_path, ledger=self.ledger,
                                                   assets_root=Path(config.assets_root),
                                                   reviewer=config.worker_id,
                                                   generated_criteria=self.generated.criteria if self.generated else None,
                                                   project_id=config.project_id or None,
                                                   locality=self.locality,
                                                   archive_root=Path(config.evidence_root),
                                                   clock=self.ledger.clock)

    def discover(self, limit: int = 100) -> list[dict[str, JsonValue]]:
        if self.config.project_id:
            self._research_action("read")
            self._authorize_project(self.config.project_id)
        self.field.synchronize(trusted_facts(self.ledger, self.store.root))
        records = self.ledger.candidates(self.locality, limit=limit, capabilities=self.config.capabilities)
        visible = [task for task in records if self._task_visible(task.signal.task_id)]
        # Preserve the legacy policy unchanged. A mixed-project window cannot
        # be passed through that legacy schema as if it were project scoped.
        recommendation: dict[str, JsonValue]
        inspected = self.ledger.candidates(self.locality, limit=limit, include_blocked=True)
        if len(visible) == len(records) and all(self._task_visible(t.signal.task_id) for t in inspected):
            recommendation = self.router.recommend(self.config.worker_id, self.locality,
                                                    {key: 1.0 for key in self.config.capabilities}, limit=limit)
        else:
            recommendation = {"routing_sequence": None, "policy_version": "v0.1", "selected": None,
                              "reason": "legacy_window_not_project_scoped", "advisory_only": True}
        research_v1 = self._discover_research_v1()
        if research_v1 is not None:
            opportunities = self._opportunities(research_v1)
            visible = [task for task in visible if self._opportunity_allows(task, opportunities)]
            visible.sort(key=lambda task: -self._opportunity_share(task, opportunities))
        responses: list[dict[str, JsonValue]] = []
        for task in visible:
            response = _OBJECT.validate_json(task.model_dump_json())
            response["policy_recommendation"] = (recommendation if not responses else {
                "routing_sequence": recommendation["routing_sequence"], "policy_version": recommendation["policy_version"],
                "selected": recommendation["selected"], "reference_only": True})
            response["research"] = self._task_research(task.signal.task_id)
            if research_v1 is not None:
                response["research_v1"] = research_v1
                response["research_opportunity"] = self._task_opportunity(task, self._opportunities(research_v1))
            response["candidate_window"] = {"limit": limit, "truncated": len(records) == limit,
                                            "order": "research_opportunity_then_ledger" if research_v1 else "ledger"}
            responses.append(response)
        return responses

    def _task(self, task_id: str, *, require_capability: bool = False) -> TaskRecord:
        self._native_reservation()
        # Query uses authoritative locality and capability filters, including held tasks.
        query, args = self.ledger._local_filter(self.locality)
        with connection(self.ledger.path) as db:
            row = db.execute("SELECT t.* FROM tasks t WHERE " + query + " AND t.task_id=?",
                             [*args, task_id]).fetchone()
            if row is None:
                raise PermissionError("task_outside_host_scope")
            task = self.ledger._record(db, row)
        if require_capability and (task.signal.required_capability or task.signal.task_kind) not in self.config.capabilities:
            raise PermissionError("task_capability_required")
        if self.config.project_id and task.signal.payload.get("project_id") != self.config.project_id:
            raise PermissionError("task_outside_host_project")
        return task

    def _task_visible(self, task_id: str) -> bool:
        try:
            self._task(task_id)
        except (PermissionError, KeyError):
            return False
        return True

    def context(self, task_id: str, *, limit: int = 100) -> dict[str, JsonValue]:
        task = self._task(task_id)
        return {"task": _OBJECT.validate_json(task.model_dump_json()),
                "project_context": self.config.project_context,
                "dependency_results": [{"task_id": d, "status": self._task(d).status,
                                        "result": self._task(d).result} for d in task.dependencies],
                "worker_id": self.config.worker_id, "agent": _OBJECT.validate_json(self.config.agent.model_dump_json()),
                "research": self._task_research(task_id, limit=limit)}

    def claim(self, task_id: str, ttl_seconds: float = 60) -> dict[str, JsonValue] | None:
        task = self._task(task_id, require_capability=True)
        if self.config.project_id:
            self._research_action("claim")
            self._budget_ready()
            advisory = self.research_advisory()
            if not self._opportunity_allows(task, self._opportunities(advisory)):
                raise PermissionError("research_branch_not_active")
        lease = self.ledger.claim(task_id, self.config.worker_id, locality=self.locality, ttl_seconds=ttl_seconds)
        if lease is None:
            return None
        response = _OBJECT.validate_json(lease.model_dump_json())
        response["attempt_id"] = _OBJECT.validate_json(AttemptId(task_id=task_id, agent=self.config.agent,
                                                               attempt=self.ledger.get(task_id).attempts).model_dump_json())
        # Re-read the authoritative recommendation row, not an Agent-supplied ID.
        with connection(self.ledger.path) as db:
            routing = db.execute("SELECT sequence,body FROM task_audit WHERE swarm_id=? AND event='routing' "
                                 "ORDER BY sequence DESC", (self.config.swarm_id,)).fetchall()
            selections = db.execute("SELECT sequence,body FROM task_audit WHERE swarm_id=? AND event='policy_selection'",
                                    (self.config.swarm_id,)).fetchall()
        used = max((r[0] for r in selections if _OBJECT.validate_json(r[1]).get("worker_id") == self.config.worker_id), default=0)
        associated = next((r for r in routing if r[0] > used and self._recommendation_context(_OBJECT.validate_json(r[1]))), None)
        decision = _OBJECT.validate_json(associated[1]) if associated is not None else None
        selection: dict[str, JsonValue] = {"actual_task_id": task_id, "worker_id": self.config.worker_id,
                                           "token": lease.token, "routing_sequence": associated[0] if associated is not None else None,
                                           "policy_version": decision.get("policy_version") if decision else None,
                                           "recommended_task_id": decision.get("selected") if decision else None,
                                           "overridden": task_id != decision.get("selected") if decision else None,
                                           "recommendation_present": decision is not None,
                                           "conditions": decision.get("constraints") if decision else None,
                                           "candidate_conditions": decision.get("policy_candidates", decision.get("signals")) if decision else None,
                                           "feedback_source": "existing_authoritative_facts"}
        self.ledger.record_event("policy_selection", selection, task_id=task_id)
        response["policy_selection"] = selection
        if self.config.project_id:
            response["research_selection"] = self._record_research_selection(task, lease)
        return response

    def _recommendation_context(self, decision: dict[str, JsonValue]) -> bool:
        if (decision.get("worker_id") != self.config.worker_id
                or decision.get("authorized_scopes") != list(self.locality.authorized_scopes)
                or decision.get("modules") != list(self.locality.modules)
                or decision.get("dependency_of") != list(self.locality.dependency_of)
                or decision.get("policy_version") != self.router.strategy_version
                or not isinstance(decision.get("selected"), str)):
            return False
        candidates = decision.get("policy_candidates", decision.get("signals"))
        if not isinstance(candidates, list) or not candidates:
            return False
        for candidate in candidates:
            if not isinstance(candidate, dict) or not isinstance(candidate.get("task_id"), str):
                return False
            candidate_id = candidate.get("task_id")
            if not isinstance(candidate_id, str):
                return False
            try:
                task = self._task(candidate_id, require_capability=True)
            except (PermissionError, KeyError):
                return False
            if (candidate.get("scope") != task.signal.scope
                    or candidate.get("module") != task.signal.module
                    or candidate.get("required_capability") != (task.signal.required_capability or task.signal.task_kind)
                    or candidate.get("capability_match") != 1.0
                    or candidate.get("dependencies") != list(task.dependencies)):
                return False
        return True

    def _lease(self, task_id: str, token: int) -> Lease:
        if self.config.project_id:
            self._authorize_project(self.config.project_id)
        task = self._task(task_id, require_capability=True)
        if (task.owner != self.config.worker_id or task.token != token or task.expires_at is None
                or isinstance(token, bool)):
            raise LeaseLost("host_identity_or_fencing_token_mismatch")
        lease = Lease(task_id=task_id, swarm_id=self.config.swarm_id, worker_id=self.config.worker_id,
                      scope=canonical_scope(Path(task.signal.workspace) / task.signal.scope),
                      token=token, expires_at=task.expires_at)
        if not self.ledger.is_valid(lease):
            raise LeaseLost("lease_expired_or_not_claimed")
        return lease

    def renew(self, task_id: str, token: int, ttl_seconds: float = 60) -> dict[str, JsonValue]:
        renewed = self.ledger.renew(self._lease(task_id, token), ttl_seconds=ttl_seconds)
        if renewed is None:
            raise LeaseLost("renewal_lost")
        return _OBJECT.validate_json(renewed.model_dump_json())

    def release(self, task_id: str, token: int) -> bool:
        return self.ledger.release(self._lease(task_id, token))

    def handoff(self, task_id: str, token: int, next_worker_id: str,
                partial: dict[str, JsonValue] | None = None) -> dict[str, JsonValue]:
        return _OBJECT.validate_json(self.ledger.handoff(self._lease(task_id, token), next_worker_id,
                                                       partial=partial).model_dump_json())

    def _plan(self, task_id: str) -> dict[str, JsonValue]:
        plan = self._task(task_id).acceptance.get("experiment_plan")
        if not isinstance(plan, dict):
            raise AssetSafetyError("pre_registered_experiment_plan_required")
        return _OBJECT.validate_python(plan)

    def environment(self, task_id: str, token: int) -> dict[str, JsonValue]:
        self._lease(task_id, token)
        if self._task(task_id).acceptance.get("generated_plan") is not None:
            generated = self._generated_tools()
            return {"plan": generated.plan(task_id).model_dump(mode="json"), "backend_configured": True,
                    "allocation": "on_execute", "execution_started": False,
                    "provenance": generated.settings.mode}
        return {"plan": self._plan(task_id), "backend_configured": self.backend is not None,
                "allocation": "on_execute", "isolation_requested": "fresh_sandbox_per_execution",
                "execution_started": False}

    async def execute(self, task_id: str, token: int) -> dict[str, JsonValue]:
        lease = self._lease(task_id, token)
        if self._task(task_id).acceptance.get("generated_plan") is not None:
            return await self._generated_tools().execute(task_id, token)
        plan = self._plan(task_id)
        if self.backend is None:
            raise AssetSafetyError("experiment_backend_not_configured")
        if self.config.research_envelope is not None:
            self._research_action("experiment")
            self._authorize_project(self.config.project_id)
            self._budget_ready(required=True)
        run_id = uuid4().hex
        reservation = (self.budget.reserve(self.config.worker_id, task_id, self.config.research_execution_bound,
                                           request_id=run_id)
                       if self.budget is not None and self.config.research_execution_bound is not None else None)
        # No SQLite transaction survives this boundary. Exceptions/crashes retain
        # unconfirmed_request_id and prohibit automatic replay after expiry.
        try:
            self.ledger.begin_execution(lease, run_id, max_executions=self.config.max_experiments_per_task)
            result = await self.backend.execute(plan, run_id, lease)
        except BaseException:
            if reservation is not None and self.budget is not None:
                self.budget.mark_uncertain(reservation)
            raise
        if reservation is not None and self.budget is not None:
            if result.get("effect_state") in {"known", "confirmed"}:
                self.budget.settle(reservation, result.get("usage"))
            else:
                self.budget.mark_uncertain(reservation)
        self._lease(task_id, token)
        self.ledger.record_event("research_execution", {"run_id": run_id, "worker_id": lease.worker_id,
                                                       "token": token, "result": result}, task_id=task_id)
        if (result.get("execution_state") in {"succeeded", "failed", "timeout", "unsupported", "missing_artifact"}
                and result.get("effect_state") in {"known", "confirmed"}):
            self.ledger.confirm_execution(self._lease(task_id, token), run_id)
        return {"run_id": run_id, "result": result}

    def _run(self, task_id: str, run_id: str) -> dict[str, JsonValue]:
        self._task(task_id)
        # Durable authoritative lineage; an Agent cannot nominate arbitrary archives.
        with connection(self.ledger.path) as db:
            rows = db.execute("SELECT body FROM task_audit WHERE swarm_id=? AND task_id=? AND event='research_execution'",
                              (self.config.swarm_id, task_id)).fetchall()
        for row in rows:
            body = _OBJECT.validate_json(row[0])
            if body.get("run_id") == run_id:
                return body
        raise AssetSafetyError("unknown_task_run")

    def result(self, task_id: str, run_id: str) -> dict[str, JsonValue]:
        self._run(task_id, run_id)
        if self._task(task_id).acceptance.get("generated_plan") is not None:
            return self._generated_tools().read(task_id, run_id)
        if self.backend is None:
            raise AssetSafetyError("experiment_backend_not_configured")
        return self.backend.read(run_id)

    def artifact(self, task_id: str, run_id: str, artifact_path: str, *, max_bytes: int = 65536) -> dict[str, JsonValue]:
        """Read only a verified, size-bounded original generated output or log."""
        self._run(task_id, run_id)
        return self._generated_tools().artifact(task_id, run_id, artifact_path, max_bytes)

    def publish(self, task_id: str, token: int, candidate: Candidate) -> str:
        lease = self._lease(task_id, token)
        task = self._task(task_id)
        expected = AttemptId(task_id=task_id, agent=self.config.agent, attempt=task.attempts)
        if candidate.attempt != expected or candidate.scope != task.signal.scope:
            raise AssetSafetyError("candidate_host_identity_or_scope_mismatch")
        if candidate.research is None:
            raise AssetSafetyError("research_claim_required")
        claim_data = task.acceptance.get("research_claim")
        if claim_data != _OBJECT.validate_json(candidate.research.model_dump_json()):
            raise AssetSafetyError("claim_must_match_pre_registered_acceptance")
        inspect_candidate(candidate)
        # Official SDK calls outside the ledger lock; publication is quarantine only.
        asset_id = self.store.publish(candidate)
        if not self.ledger.is_valid(lease):
            raise LeaseLost("publication_quarantined_after_lease_loss")
        return asset_id

    def validate_files(self, task_id: str, token: int, asset_id: str) -> dict[str, JsonValue]:
        self._asset(task_id, asset_id)
        self._lease(task_id, token)
        if self._task(task_id).acceptance.get("generated_plan") is not None:
            return self._generated_tools().validate(task_id, token, asset_id)
        policy = ValidationPolicy.model_validate(self._task(task_id).acceptance.get("file_policy"))
        report = AssetValidator(self.store, self.config.workspace, policy=policy).validate(asset_id)
        self._lease(task_id, token)
        return _OBJECT.validate_json(report.model_dump_json())

    def _asset(self, task_id: str, asset_id: str) -> Candidate:
        task = self._task(task_id)
        candidate = self.store.fetch(asset_id)
        if candidate.scope != task.signal.scope:
            raise PermissionError("asset_scope_mismatch")
        if self.config.project_id:
            self._task(candidate.attempt.task_id)
        return candidate

    def _observation_source(self, lease: Lease, candidate: Candidate, lineage: dict[str, JsonValue],
                            run_id: str, purpose: Purpose) -> tuple[Lease, AttemptId, bool]:
        source_token = lineage.get("token")
        if (lineage.get("worker_id") != self.config.worker_id or not isinstance(source_token, int)
                or isinstance(source_token, bool) or not 0 < source_token <= lease.token):
            raise AssetSafetyError("run_host_identity_mismatch")
        with connection(self.ledger.path) as db:
            source = db.execute("SELECT worker_id FROM task_attempts WHERE swarm_id=? AND task_id=? AND token=?",
                                (lease.swarm_id, lease.task_id, source_token)).fetchone()
            attempt = db.execute("SELECT COUNT(*) FROM task_attempts WHERE swarm_id=? AND task_id=? AND token<=?",
                                 (lease.swarm_id, lease.task_id, source_token)).fetchone()[0]
            confirmations = db.execute("SELECT body FROM task_audit WHERE swarm_id=? AND task_id=? AND event='execution_confirmed'",
                                       (lease.swarm_id, lease.task_id)).fetchall()
        if source is None or source[0] != self.config.worker_id:
            raise AssetSafetyError("source_execution_attempt_missing_or_mismatched")
        source_attempt = AttemptId(task_id=lease.task_id, agent=self.config.agent, attempt=attempt)
        if purpose == "original" and candidate.attempt != source_attempt:
            raise AssetSafetyError("original_execution_attempt_mismatch")
        recovered = source_token != lease.token
        if recovered:
            result = lineage.get("result")
            if (purpose != "original" or not isinstance(result, dict)
                    or result.get("execution_state") not in {"succeeded", "failed", "timeout", "unsupported", "missing_artifact"}
                    or result.get("effect_state") not in {"known", "confirmed"}
                    or not any(_OBJECT.validate_json(r[0]).get("request_id") == run_id
                               and _OBJECT.validate_json(r[0]).get("token") == source_token for r in confirmations)):
                raise AssetSafetyError("confirmed_original_execution_required_for_recovery")
            self.ledger.assert_execution_confirmed(lease)
        # Data identity only. This token never authorizes a ledger/store write.
        return lease.model_copy(update={"token": source_token}), source_attempt, recovered

    def observe(self, task_id: str, token: int, asset_id: str, run_id: str, purpose: Purpose) -> dict[str, JsonValue]:
        lease = self._lease(task_id, token)
        if self._task(task_id).acceptance.get("generated_plan") is not None:
            return _OBJECT.validate_json(self._generated_tools().observe(task_id, token, asset_id, run_id, purpose).model_dump_json())
        candidate = self._asset(task_id, asset_id)
        if purpose == "original" and (candidate.attempt.task_id != task_id or candidate.attempt.agent != self.config.agent):
            raise AssetSafetyError("original_author_identity_mismatch")
        lineage = self._run(task_id, run_id)
        source_context, source_attempt, recovered = self._observation_source(lease, candidate, lineage, run_id, purpose)
        if self.backend is None or candidate.research is None:
            raise AssetSafetyError("research_backend_and_claim_required")
        plan = self._plan(task_id)
        claim = candidate.research
        criteria = plan.get("criteria")
        if (plan.get("plan_id") != claim.plan_id or not isinstance(criteria, dict)
                or criteria.get("version") != claim.criterion_version):
            raise AssetSafetyError("research_pre_registered_plan_claim_mismatch")
        try:
            evaluated = self.backend.evaluate(run_id, plan, source_context)
        except (ValueError, OSError) as error:
            if recovered:
                raise AssetSafetyError("recovered_execution_archive_rejected") from error
            original = lineage.get("result")
            if not isinstance(original, dict) or original.get("provenance") not in {"live", "replay", "mock"}:
                raise AssetSafetyError("durable_result_provenance_required") from error
            evaluated = {"execution_state": "missing_artifact", "scientific_verdict": "not_evaluated",
                         "provenance": original["provenance"], "sandbox_id": original.get("sandbox_id"),
                         "reasons": ["trusted_archive_rejected:" + type(error).__name__ + ":" + str(error)],
                         "code_text": None}
        claim = candidate.research
        if self._task(task_id).acceptance.get("research_claim") != _OBJECT.validate_json(claim.model_dump_json()):
            raise AssetSafetyError("research_condition_mismatch")
        if recovered:
            original_result = lineage.get("result")
            if (not isinstance(original_result, dict)
                    or evaluated.get("effect_state") not in {"known", "confirmed"}
                    or any(evaluated.get(field) != original_result.get(field) for field in (
                        "execution_state", "scientific_verdict", "provenance", "sandbox_id", "effect_state", "exit_code"))
                    or (isinstance(original_result.get("experiment_result"), dict)
                        and evaluated.get("experiment_result") != original_result["experiment_result"])):
                raise AssetSafetyError("recovered_execution_result_mismatch_or_unknown")
        # The executed code, not an unrelated passing reference program, must
        # supply every candidate after-byte. The current CPU case is one script.
        if (evaluated.get("execution_state") == "succeeded"
                and (len(candidate.changes) != 1 or candidate.changes[0].after != evaluated.get("code_text"))):
            raise AssetSafetyError("research_candidate_executed_code_mismatch")
        verdict = evaluated.get("scientific_verdict")
        if verdict not in {"passed", "failed", "not_evaluated"}:
            raise AssetSafetyError("invalid_trusted_verdict")
        report = ResearchObservation.model_validate({
            "report_id": uuid4().hex, "asset_id": asset_id, "task_id": task_id, "worker_id": self.config.worker_id,
            "fencing_token": token, "run_id": run_id,
            "sandbox_id": evaluated.get("sandbox_id"), "plan_id": claim.plan_id,
            "criterion_version": claim.criterion_version, "conditions": claim.conditions,
            "plan_json": _OBJECT.dump_json(plan).decode(), "result_json": _OBJECT.dump_json(evaluated).decode(),
            "candidate_json": candidate.model_dump_json(),
            "provenance": evaluated.get("provenance"), "purpose": purpose,
            "execution_state": evaluated.get("execution_state"), "scientific_verdict": verdict,
            "reasons": evaluated.get("reasons", []), "created_at": self.ledger.now(),
            "source_swarm_id": lease.swarm_id, "source_fencing_token": source_context.token,
            "source_attempt": source_attempt.model_dump(mode="json"),
        })
        with self.ledger.fenced(self._lease(task_id, token)):
            self.store._record_research(report)
        return _OBJECT.validate_json(report.model_dump_json())

    def complete_research(self, task_id: str, token: int, asset_id: str, run_id: str) -> dict[str, JsonValue]:
        """Finish evidence work while the candidate remains quarantined for replication."""
        lease = self._lease(task_id, token)
        self.ledger.assert_execution_confirmed(lease)
        self._asset(task_id, asset_id)
        reports = [r for r in self.store.research_reports(asset_id)
                   if r.task_id == task_id and r.worker_id == self.config.worker_id
                   and r.fencing_token == token and r.run_id == run_id]
        if not reports:
            raise AssetSafetyError("trusted_research_observation_required")
        last = reports[-1]
        if (last.source_fencing_token is not None and last.source_fencing_token != last.fencing_token
                and (last.scientific_verdict != "passed" or last.execution_state != "succeeded" or not known_effect(last))):
            raise AssetSafetyError("trusted_passed_observation_required_for_completion")
        result: dict[str, JsonValue] = {"asset_id": asset_id, "run_id": run_id,
                                      "report_id": last.report_id,
                                      "scientific_verdict": last.scientific_verdict,
                                      "execution_state": last.execution_state,
                                      "stage": "evidence_submitted", "approved": False,
                                      "provenance": last.provenance}
        if self._task(task_id).acceptance.get("generated_plan") is not None:
            verified = self._generated_tools().read(task_id, run_id)
            if _OBJECT.validate_json(last.result_json) != verified:
                raise AssetSafetyError("generated_observation_execution_mismatch")
            result["generated_assessment"] = verified.get("generated_assessment")
            result["effect_state"] = verified.get("effect_state")
        if last.source_attempt is not None:
            result.update({"source_swarm_id": last.source_swarm_id,
                           "source_fencing_token": last.source_fencing_token,
                           "source_attempt": _OBJECT.validate_json(last.source_attempt.model_dump_json()),
                           "observation_fencing_token": last.fencing_token})
        task = self.ledger.submit(lease, uuid4().hex, result)
        self.field.synchronize(trusted_facts(self.ledger, self.store.root))
        return _OBJECT.validate_json(task.model_dump_json())

    def approve(self, task_id: str, token: int, asset_id: str, report_id: str) -> dict[str, JsonValue]:
        self._asset(task_id, asset_id)
        if self._task(task_id).acceptance.get("generated_plan") is not None:
            return self._generated_tools().approve(task_id, token, asset_id, report_id)
        policy = ValidationPolicy.model_validate(self._task(task_id).acceptance.get("file_policy"))
        lease = self._lease(task_id, token)
        self.ledger.assert_execution_confirmed(lease)
        # Promotion still invokes the existing static report checks. No MCP tool
        # accepts passed/approved flags or a caller-supplied scientific metric.
        promoter = AssetPromoter(self.store, policy_version=policy.version)
        receipt = promoter.prepare(asset_id, report_id)
        with self.ledger.fenced(self._lease(task_id, token)) as owned:
            receipt = promoter._commit(receipt, owned)
        return _OBJECT.validate_json(receipt.model_dump_json())

    def search(self, query: str, limit: int = 20) -> list[dict[str, JsonValue]]:
        if self.config.project_id:
            self._research_action("read")
            self._authorize_project(self.config.project_id)
        if not 1 <= limit <= 100 or len(query) > 1000:
            raise ValueError("bounded_search_required")
        with self.store.connection() as db:
            ids = [str(row[0]) for row in db.execute("SELECT asset_id FROM assets WHERE instr(lower(body),lower(?))>0 LIMIT 1000",
                                                    (query,))]
        results: list[dict[str, JsonValue]] = []
        for asset_id in ids:
            candidate = self.store.fetch(asset_id)
            if self.config.project_id and not self._task_visible(candidate.attempt.task_id):
                continue
            target = canonical_scope(Path(self.config.workspace) / candidate.scope)
            if not any(Path(target).is_relative_to(Path(canonical_scope(Path(self.config.workspace) / s)))
                       for s in self.config.authorized_scopes):
                continue
            if not set(candidate.required_capabilities).issubset(self.config.capabilities):
                continue
            results.append({"asset_id": asset_id, "candidate": _OBJECT.validate_json(candidate.model_dump_json()),
                            "state": self.store.state(asset_id),
                            "research_reports": [_OBJECT.validate_json(r.model_dump_json()) for r in self.store.research_reports(asset_id)
                                                 if not self.config.project_id or self._task_visible(r.task_id)],
                            "stage": "retrieved", "adopted": False})
            if len(results) >= limit:
                break
        return results

    def inherit(self, task_id: str, token: int, asset_id: str, path_map: dict[str, str],
                preimages: dict[str, str | None], base_revision: str, base_head: str | None = None) -> dict[str, JsonValue]:
        lease = self._lease(task_id, token)
        self.ledger.assert_execution_confirmed(lease)
        task = self._task(task_id)
        candidate = self._asset(task_id, asset_id)
        if task.acceptance.get("generated_plan") is not None:
            self._generated_tools().bound_candidate(task_id, token, asset_id)
        claim = candidate.research
        if claim is None or task.acceptance.get("research_claim") != _OBJECT.validate_json(claim.model_dump_json()):
            raise AssetSafetyError("research_condition_mismatch")
        require_inheritance(self.store, asset_id, task_id, self.config.worker_id, token, claim.conditions)
        context = ConsumptionContext(swarm_id=self.config.swarm_id, task_id=task_id,
                                     worker_id=self.config.worker_id, fencing_token=token,
                                     execution_id=uuid4().hex, scope=task.signal.scope,
                                     capabilities=self.config.capabilities,
                                     completed_dependencies=tuple(d for d in task.dependencies if self.ledger.get(d).status == "completed"),
                                     input_context=self.config.project_context or task.signal.task_id)
        consumer = AssetConsumer(self.store)
        injected = consumer.inject(asset_id, context)
        # Reuse the existing scoped Git snapshot after prior candidate application.
        # The Agent supplies only the target HEAD anchor; it cannot select stale bytes.
        snapshot, head = snapshot_revision(self.config.workspace, task.signal.scope, self.store.root / "snapshots")
        if (base_head or base_revision) != head:
            raise AssetSafetyError("inheritance_target_head_changed")
        execution = consumer.execute(injected, attempt=AttemptId(task_id=task_id, agent=self.config.agent, attempt=task.attempts),
                                     base_revision=snapshot, base_head=head, path_map=path_map, preimages=preimages)
        self._lease(task_id, token)
        return _OBJECT.validate_json(execution.model_dump_json())

    def apply(self, task_id: str, token: int, asset_id: str, report_id: str,
              execution_id: str | None = None) -> dict[str, JsonValue]:
        lease = self._lease(task_id, token)
        self.ledger.assert_execution_confirmed(lease)
        candidate = self._asset(task_id, asset_id)
        generated = self._task(task_id).acceptance.get("generated_plan") is not None
        if generated:
            self._research_action("apply")
            self._authorize_project(self.config.project_id)
            self._generated_tools().bound_candidate(task_id, token, asset_id)
            policy_version = "generated-isolation-v1"
        else:
            policy_version = ValidationPolicy.model_validate(self._task(task_id).acceptance.get("file_policy")).version
        self.store.fetch_approved(asset_id)
        prepared = AssetApplicator(self.store, self.config.workspace, policy_version=policy_version,
                                   protected_paths=(self.store.root, Path(self.config.evidence_root), self.ledger.path)).prepare(asset_id, report_id)
        if canonical_scope(prepared.scope) != lease.scope:
            raise AssetSafetyError("application_lease_scope_mismatch")
        result_id = uuid4().hex
        result: dict[str, JsonValue] = {"candidate_asset_id": asset_id, "report_id": report_id, "applied": True}
        if execution_id is not None:
            execution = self.store.consumption(execution_id)
            if (execution.candidate_asset_id != asset_id or execution.context.task_id != task_id
                    or execution.context.worker_id != self.config.worker_id or execution.context.fencing_token != token):
                raise AssetSafetyError("adoption_execution_mismatch")
            claim = candidate.research
            if claim is None:
                raise AssetSafetyError("research_claim_required")
            require_inheritance(self.store, execution.asset_id, task_id, self.config.worker_id, token, claim.conditions)
            result.update({"execution_id": execution_id, "consumed_asset_ids": [execution.asset_id],
                           "input_context": execution.context.input_context})
        def apply_bytes(owned: Callable[[], None]) -> None:
            prepared.apply(owned)
        self.ledger.submit(self._lease(task_id, token), result_id, result, apply=apply_bytes)
        response: dict[str, JsonValue] = {"result_id": result_id, "stage": "applied", "adopted": False}
        if execution_id is not None:
            receipt = AssetConsumer(self.store).record_adoption(execution_id, result_id, self.ledger)
            response.update({"stage": "adopted", "adopted": True, "adoption": _OBJECT.validate_json(receipt.model_dump_json())})
        self.field.synchronize(trusted_facts(self.ledger, self.store.root))
        return response

    # -- research plane (M1): projects, notes, branches, proposals ---------

    def _project_id(self, project_id: str | None = None) -> str:
        bound = project_id or self.config.project_id
        if not bound:
            raise ValueError("research_project_required")
        return bound

    def _authorize_project(self, project_id: str) -> ResearchProject:
        """Enforce the host's project binding and existence (FR-05/10.2)."""
        self._native_reservation()
        if self.config.project_id and project_id != self.config.project_id:
            raise PermissionError("project_outside_host_authorization")
        project = self.knowledge.project(project_id)
        if self.config.research_envelope is not None and project.host_binding != self._host_binding():
            raise PermissionError("project_host_envelope_changed")
        if project.host_binding and project.host_binding != self._host_binding():
            raise PermissionError("project_host_envelope_changed")
        return project

    def _host_binding(self) -> dict[str, JsonValue]:
        envelope = self.config.research_envelope
        if envelope is None:
            return {}
        return {"envelope": _OBJECT.validate_json(envelope.model_dump_json()),
                "authorization_ref": self.config.authorization_ref, "swarm_id": self.config.swarm_id,
                "ledger_path": canonical_scope(self.ledger.path), "workspace": canonical_scope(self.config.workspace),
                "assets_root": canonical_scope(self.store.root),
                "budget_path": canonical_scope(self.config.research_budget_path) if self.config.research_budget_path else None,
                "budget_policy": self.config.research_budget_policy.model_dump(mode="json") if self.config.research_budget_policy else None,
                "execution_bound": self.config.research_execution_bound.model_dump(mode="json") if self.config.research_execution_bound else None,
                "generated_experiments": self.config.generated_experiments,
                "max_experiments_per_task": self.config.max_experiments_per_task}

    def _research_action(self, action: str) -> None:
        self._native_reservation()
        envelope = self.config.research_envelope
        if envelope is not None and action not in envelope.actions:
            raise PermissionError("action_outside_research_envelope")

    def admit_native_invocation(self, invocation_id: str, bound: ExecutionBound, *,
                                ttl_seconds: float) -> NativeInvocationBinding:
        """Host-only admission; the MCP tool surface cannot issue its own exception.

        The protected product launcher installs the returned binding in only this
        invocation's HostConfig and settles/marks uncertain the same reservation
        on exit. Original BudgetLedger limits and cumulative holds remain intact.
        """
        if self.config.native_invocation is not None:
            raise PermissionError("native_invocation_cannot_admit_another_invocation")
        invocation = UUID(invocation_id)
        self.ledger._ttl(ttl_seconds)
        self._research_action("read")
        self._authorize_project(self._project_id())
        if bound != self.config.research_execution_bound:
            raise PermissionError("native_execution_bound_outside_host_approval")
        self._budget_ready(required=True)
        assert self.budget is not None
        if self.budget.snapshot().uncertain_reservations:
            raise BudgetBlocked("project_unknown_usage_requires_reconciliation")
        with connection(self.ledger.path) as db:
            self.ledger._check_runtime(db)
            ledger_started = float(db.execute("SELECT started_at FROM swarm_runs WHERE swarm_id=?",
                                              (self.config.swarm_id,)).fetchone()[0])
        with connection(self.budget.path) as db:
            started = float(db.execute("SELECT started_at FROM swarm_budgets WHERE swarm_id=?",
                                      (self.config.project_id,)).fetchone()[0])
        deadline = min(started + self.budget.policy.limits.max_runtime_seconds,
                       ledger_started + self.ledger.limits.max_runtime_seconds)
        expires = min(self.ledger.now() + ttl_seconds, deadline)
        if expires <= self.ledger.now():
            raise BudgetBlocked("native_invocation_expired")
        reservation = self.budget.reserve(self.config.worker_id, "native-member:" + self.config.worker_id,
                                          bound, request_id="native:" + str(invocation))
        return NativeInvocationBinding(invocation_id=invocation, reservation=reservation, expires_at=expires)

    def _native_reservation(self) -> Reservation | None:
        binding = self.config.native_invocation
        if binding is None:
            return None
        binding = NativeInvocationBinding.model_validate(binding.model_dump())
        reservation = binding.reservation
        if (self.budget is None or reservation.swarm_id != self.config.project_id or
                reservation.worker_id != self.config.worker_id or
                reservation.task_id != "native-member:" + self.config.worker_id or
                reservation.request_id != "native:" + str(binding.invocation_id) or
                reservation.bound != self.config.research_execution_bound):
            raise PermissionError("native_invocation_host_binding_mismatch")
        now = self.ledger.now()
        with connection(self.budget.path) as db:
            started = float(db.execute("SELECT started_at FROM swarm_budgets WHERE swarm_id=?",
                                      (self.config.project_id,)).fetchone()[0])
        with connection(self.ledger.path) as db:
            ledger_started = float(db.execute("SELECT started_at FROM swarm_runs WHERE swarm_id=?",
                                              (self.config.swarm_id,)).fetchone()[0])
        deadline = min(started + self.budget.policy.limits.max_runtime_seconds,
                       ledger_started + self.ledger.limits.max_runtime_seconds)
        if not reservation.created_at <= now < binding.expires_at <= deadline:
            raise BudgetBlocked("native_invocation_expired")
        if reservation not in self.budget.pending(self.config.worker_id):
            raise BudgetBlocked("native_invocation_not_active")
        return reservation

    def _budget_ready(self, *, required: bool = False) -> None:
        if self.budget is None:
            if required:
                raise BudgetBlocked("host_project_budget_required")
            return
        snapshot = self.budget.snapshot(self.config.worker_id)
        if snapshot.sleeping:
            raise BudgetBlocked(snapshot.reason or "project_budget_blocked")
        own = self._native_reservation()
        if own is not None and snapshot.uncertain_reservations:
            raise BudgetBlocked("project_unknown_usage_requires_reconciliation")
        if snapshot.pending_reservations > int(own is not None):
            # A process may have stopped between the two original database
            # writes. A hold without an execution anchor is not permission to
            # open another branch or replay a request.
            raise BudgetBlocked("project_pending_request_requires_reconciliation")
        with connection(self.ledger.path) as db:
            unknown = db.execute("SELECT 1 FROM tasks WHERE swarm_id=? AND unconfirmed_request_id IS NOT NULL LIMIT 1",
                                 (self.config.swarm_id,)).fetchone()
        if unknown is not None:
            raise BudgetBlocked("project_unknown_effect_requires_reconciliation")
        if snapshot.admission_charged_usd + snapshot.reserved_estimate_usd >= self.budget.policy.max_cost_usd:
            raise BudgetBlocked("project_admission_capacity_exhausted")

    def _require_branch(self, project_id: str, branch_id: str | None) -> None:
        if branch_id is None:
            return
        if self.knowledge.branch(branch_id).project_id != project_id:
            raise ValueError("branch_does_not_belong_to_project")

    def _require_hypothesis(self, project_id: str, hypothesis_id: str | None) -> None:
        if hypothesis_id is None:
            return
        if self.knowledge.hypothesis(hypothesis_id).project_id != project_id:
            raise ValueError("hypothesis_does_not_belong_to_project")

    def _note_in_scope(self, note: ResearchNote) -> bool:
        if note.task_id is None:
            return True
        try:
            self._task(note.task_id)
            return True
        except PermissionError:
            return False

    def _record_event(self, kind: str, project_id: str, *, branch_id: str | None = None,
                      task_id: str | None = None, source_ref: str | None = None,
                      payload: dict[str, JsonValue] | None = None) -> None:
        event = ResearchEvent(event_id=uuid4().hex, project_id=project_id, branch_id=branch_id,
                              task_id=task_id, source_ref=source_ref, actor=self.config.agent,
                              at=self.ledger.now(), schema_version="research-v1",
                              provenance=self.config.research_provenance, event_kind=kind,
                              payload=payload or {}, correlation_ref=None)
        self.knowledge.record(event)
        self.ledger.record_event("research." + kind, event.model_dump(mode="json"), task_id=task_id)

    def create_project(self, project_id: str, goal: str, *,
                       allowed_domains: tuple[str, ...] = (),
                       data_bounds: dict[str, str] | None = None,
                       authorization_ref: str | None = None,
                       milestones: tuple[str, ...] = ()) -> dict[str, JsonValue]:
        """Idempotent project registration; authorization is host-supplied, never caller-granted."""
        self._native_reservation()
        if self.config.project_id and project_id != self.config.project_id:
            raise PermissionError("project_outside_host_authorization")
        if authorization_ref is not None and authorization_ref != self.config.authorization_ref:
            raise PermissionError("authorization_ref_is_host_bound")
        envelope = self.config.research_envelope
        if envelope is not None:
            if (goal != envelope.goal or (allowed_domains and allowed_domains != envelope.allowed_domains)
                    or (data_bounds and data_bounds != envelope.data_bounds)):
                raise PermissionError("project_outside_host_envelope")
            allowed_domains, data_bounds = envelope.allowed_domains, envelope.data_bounds
        try:
            existing = self.knowledge.project(project_id)
        except KeyError:
            existing = None
        project = ResearchProject(project_id=project_id, goal=goal, allowed_domains=allowed_domains,
                                  data_bounds=data_bounds or {}, authorization_ref=self.config.authorization_ref,
                                  milestones=milestones, created_at=existing.created_at if existing else self.ledger.now(),
                                  host_binding=self._host_binding())
        saved = self.knowledge.put_project(project)
        if existing is None:
            self._record_event("project_created", project_id)
        return _OBJECT.validate_json(saved.model_dump_json())

    def project(self, project_id: str | None = None) -> dict[str, JsonValue]:
        return _OBJECT.validate_json(self._authorize_project(self._project_id(project_id)).model_dump_json())

    def create_branch(self, project_id: str, branch_id: str, title: str, goal: str, *,
                      parent_branch_id: str | None = None) -> dict[str, JsonValue]:
        self._research_action("branch")
        self._authorize_project(project_id)
        self._require_branch(project_id, parent_branch_id)
        try:
            existing = self.knowledge.branch(branch_id)
        except KeyError:
            existing = None
        branch = ResearchBranch(branch_id=branch_id, project_id=project_id, parent_branch_id=parent_branch_id,
                                title=title, goal=goal, status="proposed",
                                created_at=existing.created_at if existing else self.ledger.now())
        saved = self.knowledge.put_branch(branch)
        if existing is None:
            self._record_event("branch_created", project_id, branch_id=branch_id)
        return _OBJECT.validate_json(saved.model_dump_json())

    def submit_note(self, project_id: str, kind: NoteKind, text: str, *,
                    source_refs: tuple[SourceRef, ...] = (),
                    branch_id: str | None = None, hypothesis_id: str | None = None,
                    task_id: str | None = None, signer: str | None = None,
                    applicability: dict[str, str] | None = None,
                    references: tuple[str, ...] = ()) -> dict[str, JsonValue]:
        """Share a sourced observation/opinion in the exploration zone (never verified).

        The note is bound to the host identity; review_state is always
        ``unverified`` here — members cannot promote their own claim, and an
        expert opinion can never become a verified scientific fact. Repeated
        requests for the same note return the original, never a duplicate.
        """
        self._research_action("note")
        self._authorize_project(project_id)
        self._require_branch(project_id, branch_id)
        self._require_hypothesis(project_id, hypothesis_id)
        if task_id is not None:
            task = self._task(task_id)
            if task.signal.payload.get("project_id", project_id) != project_id:
                raise PermissionError("note_task_outside_project")
        note = ResearchNote(note_id=uuid4().hex, project_id=project_id, branch_id=branch_id,
                            hypothesis_id=hypothesis_id, task_id=task_id, kind=kind,
                            actor=self.config.agent, signer=signer, source_refs=source_refs,
                            text=text, applicability=applicability or {}, review_state="unverified",
                            references=references, created_at=self.ledger.now())
        saved = self.knowledge.put_note(note)
        created = saved.note_id == note.note_id
        if created:
            if kind == "hypothesis":
                self.knowledge.put_hypothesis(Hypothesis(
                    hypothesis_id=saved.note_id, project_id=project_id, branch_id=branch_id,
                    claim=saved.text, status="proposed", source_refs=source_refs,
                    created_at=self.ledger.now()))
            self._record_event("note_submitted", project_id, branch_id=branch_id, task_id=task_id,
                               source_ref=source_refs[0].source_id if source_refs else None,
                               payload={"note_id": saved.note_id, "kind": saved.kind})
        return _OBJECT.validate_json(saved.model_dump_json())

    def propose_work(self, project_id: str, kind: ProposalKind, goal: str, justification: str,
                     expected_contribution: str, *, scope: str | None = None,
                     required_capability: str | None = None, dependencies: tuple[str, ...] = (),
                     source_refs: tuple[SourceRef, ...] = (), branch_id: str | None = None,
                     derived_from: str | None = None) -> dict[str, JsonValue]:
        """Host-admit a proposal into the single TaskLedger (FR-06/07).

        Authorization is host-bound: ``scope`` must fall inside the host's
        ``authorized_scopes`` and ``required_capability`` inside the host's
        ``capabilities``; neither is granted by the caller. Every dependency and
        ``derived_from`` parent must exist *and* be inside the host's locality
        (a missing ``derived_from`` never bypasses the derived quota or parent
        locality). A duplicate proposal returns its existing admission without
        enqueuing a second task.
        """
        self._research_action("propose")
        self._authorize_project(project_id)
        self._require_branch(project_id, branch_id)
        if len(dependencies) > 64 or project_id in dependencies:
            raise ValueError("invalid or excessive dependencies")
        scope = scope or self.config.authorized_scopes[0]
        if scope not in self.config.authorized_scopes:
            raise PermissionError("proposal_scope_outside_host_authorization")
        capability = required_capability or self.config.capabilities[0]
        if capability not in self.config.capabilities:
            raise PermissionError("proposal_capability_outside_host")
        for dependency in dependencies:
            if self._task(dependency).signal.payload.get("project_id", project_id) != project_id:
                raise PermissionError("dependency_outside_project")
        if derived_from is not None:
            if self._task(derived_from).signal.payload.get("project_id", project_id) != project_id:
                raise PermissionError("parent_task_outside_project")
        proposal = WorkProposal(proposal_id=uuid4().hex, project_id=project_id, branch_id=branch_id,
                                kind=kind, goal=goal, justification=justification,
                                expected_contribution=expected_contribution, scope=scope,
                                required_capability=capability, dependencies=dependencies,
                                source_refs=source_refs, actor=self.config.agent, status="proposed",
                                created_at=self.ledger.now())
        existing = self.knowledge.put_proposal(proposal)
        if existing.status == "accepted" and existing.task_id is not None:
            # Idempotent re-proposal: the same work was already admitted once.
            return _OBJECT.validate_json(existing.model_dump_json())
        # Fresh proposal, or recovery from an interrupted admission: reuse the
        # persisted proposal identity everywhere (payload, acceptance, dedup) so
        # a crash between the knowledge write, the ledger enqueue and the bind
        # cannot create a duplicate task or drift the persisted proposal id.
        task_id = existing.proposal_id
        payload: dict[str, JsonValue] = {"proposal_id": task_id, "kind": existing.kind,
                                         "goal": existing.goal, "justification": existing.justification,
                                         "expected_contribution": existing.expected_contribution,
                                         "project_id": existing.project_id, "branch_id": existing.branch_id}
        acceptance: dict[str, JsonValue] = {"research_proposal_id": task_id,
                                            "research_proposal": existing.model_dump(mode="json")}
        try:
            self.ledger.enqueue(Signal(task_id=task_id, workspace=self.config.workspace, scope=scope,
                                       kind="opportunity", required_capability=capability, module="research",
                                       payload=payload),
                                dependencies=dependencies, derived_from=derived_from,
                                evidence_key=self.knowledge.proposal_dedup_key(
                                    existing.project_id, existing.kind, existing.goal, existing.justification,
                                    existing.expected_contribution, existing.scope, existing.required_capability,
                                    existing.dependencies, existing.source_refs),
                                acceptance=acceptance)
        except TaskConflict as error:
            bound = self.knowledge.bind_proposal(task_id, task_id, "blocked", str(error))
            self._record_event("proposal_blocked", project_id, branch_id=branch_id, task_id=task_id)
            return _OBJECT.validate_json(bound.model_dump_json())
        self.knowledge.bind_proposal(task_id, task_id, "accepted")
        self._record_event("proposal_accepted", project_id, branch_id=branch_id, task_id=task_id,
                           payload={"proposal_id": task_id})
        return _OBJECT.validate_json(self.knowledge.proposal(task_id).model_dump_json())

    def research_context(self, project_id: str | None = None, *, limit: int = 100,
                         task_id: str | None = None, branch_id: str | None = None,
                         overview: bool = False) -> dict[str, JsonValue]:
        """Read a local context, or an explicit bounded project overview.

        Permission precedes relevance and truncation. Selection follows existing
        branch, dependency and citation relations; it never claims or schedules.
        Cross-branch citations include the referenced record, not its neighbours.
        """
        self._research_action("read")
        if isinstance(limit, bool) or not 1 <= limit <= 1000:
            raise ValueError("limit must be in [1,1000]")
        bound = self._project_id(project_id)
        project = self._authorize_project(bound)
        self._require_branch(bound, branch_id)
        query, args = self.ledger._local_filter(self.locality)
        with connection(self.ledger.path) as db:
            tasks = {t.signal.task_id: t for t in (self.ledger._record(db, row) for row in db.execute(
                "SELECT t.* FROM tasks t WHERE " + query +
                " AND json_extract(t.signal,'$.payload.project_id')=? ORDER BY t.created_at,t.task_id",
                [*args, bound]))}
        capable = {key for key, t in tasks.items()
                   if (t.signal.required_capability or t.signal.task_kind) in self.config.capabilities}
        reason = "explicit_branch" if branch_id is not None else "shared_background"
        candidate_window_truncated = False
        if task_id is not None:
            if task_id not in tasks:
                raise PermissionError("context_task_outside_host_project_or_scope")
            reason = "explicit_task"
        elif branch_id is None and not overview:
            held = next((key for key, t in tasks.items() if key in capable and
                         t.owner == self.config.worker_id and t.status == "claimed" and
                         t.expires_at is not None and t.expires_at > self.ledger.now()), None)
            opportunities = self._opportunities(self.research_advisory(bound))
            candidates = self.ledger.candidates(self.locality, limit=1000, capabilities=self.config.capabilities)
            candidate_window_truncated = len(candidates) == 1000
            eligible = next((t.signal.task_id for t in candidates
                if t.signal.task_id in tasks and self._opportunity_allows(t, opportunities)), None)
            task_id = held or eligible
            reason = "held_task" if held else "eligible_task" if eligible else reason
        if task_id is not None:
            task_branch = tasks[task_id].signal.payload.get("branch_id")
            if branch_id is not None and task_branch != branch_id:
                raise ValueError("context_task_branch_mismatch")
            branch_id = task_branch if isinstance(task_branch, str) else None

        # Index only authorized records, so a hidden citation cannot act as a
        # bridge to another branch. Hypothesis notes share their original id.
        all_notes = self.knowledge.notes(bound)
        notes = [n for n in all_notes if n.task_id is None or n.task_id in tasks]
        note_tasks = {n.note_id: n.task_id for n in notes}
        visible_note_ids = set(note_tasks)
        hidden_hypotheses = {n.note_id for n in all_notes if n.task_id is not None and n.task_id not in tasks}
        hypotheses = [h for h in self.knowledge.hypotheses(bound) if h.hypothesis_id not in hidden_hypotheses]
        branches = self.knowledge.branches(bound)
        proposals = [p for p in self.knowledge.proposals(bound)
                     if (p.task_id is None or p.task_id in tasks) and
                     (p.task_id is not None or p.scope is None or p.scope in self.config.authorized_scopes)]
        snapshot = self.research_snapshot(bound)
        entries: dict[tuple[str, str], dict[str, JsonValue]] = {}
        links: dict[tuple[str, str], tuple[str, ...]] = {}
        references: dict[str, list[tuple[str, str]]] = {}
        selected: dict[tuple[str, str], str] = {}

        def register(kind: str, identifier: str, body: dict[str, JsonValue], *,
                     refs: tuple[str, ...] = (), aliases: tuple[str, ...] = ()) -> None:
            key = (kind, identifier)
            entries[key], links[key] = body, refs
            for ref in (identifier, *aliases):
                references.setdefault(ref, []).append(key)

        for n in notes:
            register("notes", n.note_id, n.model_dump(mode="json"),
                     refs=(*n.references, *((n.task_id,) if n.task_id else ()),
                           *((n.hypothesis_id,) if n.hypothesis_id else ())),
                     aliases=tuple(s.source_id for s in n.source_refs))
        for h in hypotheses:
            register("hypotheses", h.hypothesis_id, h.model_dump(mode="json"),
                     refs=(*h.supporting, *h.opposing), aliases=tuple(s.source_id for s in h.source_refs))
        for p in proposals:
            register("proposals", p.proposal_id, p.model_dump(mode="json"),
                     refs=(*p.dependencies, *((p.task_id,) if p.task_id else ())),
                     aliases=tuple(s.source_id for s in p.source_refs))
        for task_key, task_record in tasks.items():
            register("tasks", task_key, {"task_id": task_key, "branch_id": task_record.signal.payload.get("branch_id"),
                     "status": task_record.status, "result_id": task_record.result_id, "result": task_record.result,
                     "dependencies": list(task_record.dependencies), "required_capability": task_record.signal.required_capability,
                     "acceptance": task_record.acceptance}, refs=(*task_record.dependencies,
                         *((task_record.derived_from,) if task_record.derived_from else ())),
                     aliases=(task_record.result_id,) if task_record.result_id else ())
        for key, body in entries.items():
            b, linked_task = body.get("branch_id"), body.get("task_id")
            if key[0] == "hypotheses":
                linked_task = note_tasks.get(key[1])
            shared = b is None and linked_task is None
            same_branch = branch_id is not None and b == branch_id
            readable_role = linked_task is None or linked_task in capable
            if key[0] == "proposals" and body.get("required_capability") is not None:
                readable_role = readable_role and body["required_capability"] in self.config.capabilities
            if overview or key == ("tasks", task_id) or ((shared or same_branch) and readable_role):
                selected[key] = "overview" if overview else "task" if key == ("tasks", task_id) else (
                    "branch" if same_branch else "shared_background")
        # A task's proposal sources remain reachable even when the task has no
        # branch. Explicit dependencies/references may be read across roles.
        unresolved = False
        queue = list(selected)
        for key in queue:
            outgoing = links[key]
            if key[0] == "tasks":
                outgoing += tuple(p.proposal_id for p in proposals if p.task_id == key[1])
                outgoing += tuple(n.note_id for n in notes if n.task_id == key[1])
            for ref in outgoing:
                targets = references.get(ref, [])
                unresolved = unresolved or not targets
                for target in targets:
                    if target not in selected:
                        selected[target] = "dependency" if key[0] == "tasks" and ref in links[key] else "reference"
                        queue.append(target)
        selected_tasks = {key[1] for key in selected if key[0] == "tasks"}
        selected_notes = {key[1] for key in selected if key[0] == "notes"}
        selected_branches = {str(entries[key]["branch_id"]) for key in selected
                             if isinstance(entries[key].get("branch_id"), str)}
        if branch_id is not None:
            selected_branches.add(branch_id)
        background = task_id is None and branch_id is None
        if overview or background:
            selected_branches.update(b.branch_id for b in branches)

        def event_visible(event: ResearchEvent) -> bool:
            if event.task_id is not None and event.task_id not in tasks:
                return False
            note_id = event.payload.get("note_id")
            if isinstance(note_id, str) and note_id not in visible_note_ids:
                return False
            if overview:
                return True
            if isinstance(note_id, str):
                return note_id in selected_notes
            return (event.task_id in selected_tasks or
                    (event.task_id is None and event.branch_id == branch_id) or
                    (event.task_id is None and event.branch_id is None))

        events = self.knowledge.events(bound, limit=limit, predicate=event_visible, include_overflow=True)
        collections: dict[str, list[dict[str, JsonValue]]] = {
            kind: [entries[key] for key in selected if key[0] == kind]
            for kind in ("notes", "hypotheses", "proposals", "tasks")}
        collections["notes_unverified"] = [n for n in collections["notes"] if n["review_state"] != "verified"]
        collections["notes_verified"] = [n for n in collections["notes"] if n["review_state"] == "verified"]
        collections["branches"] = [b.model_dump(mode="json") for b in branches if b.branch_id in selected_branches]
        collections["events"] = [e.model_dump(mode="json") for e in events]
        response: dict[str, JsonValue] = {"project": project.model_dump(mode="json"), "limit": limit,
            "selection": {"mode": "overview" if overview else "local", "reason": "overview" if overview else reason,
                "task_id": task_id, "branch_id": branch_id, "read_only": True, "claim_requires_recheck": True,
                "candidate_window_truncated": candidate_window_truncated,
                "unresolved_references": unresolved,
                "reasons": [{"kind": key[0], "id": key[1], "via": why} for key, why in list(selected.items())[:limit]],
                "reasons_truncated": len(selected) > limit},
            "constraints": {"authorized_scopes": list(self.config.authorized_scopes),
                "capabilities": list(self.config.capabilities), "data_bounds": dict(project.data_bounds),
                "actions": list(self.config.research_envelope.actions) if self.config.research_envelope else None,
                "context_grants_execution": False}}
        for kind, values in collections.items():
            response[kind] = list(values[:limit])
            response[kind + "_truncated"] = len(values) > limit
        response["research_v1"] = snapshot if overview else self._local_snapshot(
            snapshot, selected_tasks, selected_branches, limit)
        return response

    @staticmethod
    def _local_snapshot(snapshot: dict[str, JsonValue], tasks: set[str], branches: set[str],
                        limit: int) -> dict[str, JsonValue]:
        """Project the existing policy facts; never rescore or renormalize shares."""
        result: dict[str, JsonValue] = {"policy_version": snapshot["policy_version"], "advisory_only": True,
                                       "claim_requires_recheck": True, "context_subset": True}
        ids: set[str] = set()
        for name in ("results", "contributions", "effective_contributions", "trusted_results"):
            raw = snapshot.get(name)
            values = [r for r in raw if isinstance(r, dict) and r.get("task_id") in tasks] if isinstance(raw, list) else []
            ids.update(str(r["result_id"]) for r in values)
            result[name], result[name + "_truncated"] = list(values[:limit]), len(values) > limit
        for name, field, allowed in (("branches", "branch_id", branches), ("corrections", "branch_id", branches),
                                     ("supersessions", "result_id", ids)):
            raw = snapshot.get(name)
            values = [r for r in raw if isinstance(r, dict) and r.get(field) in allowed] if isinstance(raw, list) else []
            result[name], result[name + "_truncated"] = list(values[:limit]), len(values) > limit
        plan = snapshot.get("opportunities")
        if isinstance(plan, dict):
            raw = plan.get("opportunities")
            values = [r for r in raw if isinstance(r, dict) and r.get("branch_id") in branches] if isinstance(raw, list) else []
            result["opportunities"] = {**plan, "opportunities": list(values[:limit]), "context_subset": True,
                                       "opportunities_truncated": len(values) > limit}
        raw_results = result["results"]
        axes: dict[str, JsonValue] = {}
        for axis in ("execution", "hypothesis", "contribution"):
            counts: dict[str, JsonValue] = {}
            if isinstance(raw_results, list):
                for item in raw_results:
                    state = item.get(axis) if isinstance(item, dict) else None
                    if isinstance(state, str):
                        previous = counts.get(state, 0)
                        counts[state] = (previous if isinstance(previous, int) else 0) + 1
            axes[axis] = counts
        result["three_axis"] = axes
        return result

    def research_package(self, project_id: str | None = None, *, limit: int = 100) -> dict[str, JsonValue]:
        """Read original scoped records for an export; creates no execution or adoption.

        Stored observations and audit results retain their provenance. Every
        returned run separately reports whether the archive was reread. An
        incomplete bounded package is explicit and never a completion receipt.
        """
        self._research_action("read")
        if isinstance(limit, bool) or not 1 <= limit <= 1000:
            raise ValueError("package_limit_must_be_in_1_1000")
        bound = self._project_id(project_id)
        context = self.research_context(bound, limit=limit, overview=True)
        query, args = self.ledger._local_filter(self.locality)
        with connection(self.ledger.path) as db:
            rows = db.execute("SELECT t.* FROM tasks t WHERE " + query +
                " AND json_extract(t.signal,'$.payload.project_id')=? ORDER BY t.created_at,t.task_id LIMIT ?",
                [*args, bound, limit + 1]).fetchall()
            tasks = [self.ledger._record(db, row) for row in rows[:limit]]
        task_ids = {t.signal.task_id for t in tasks}
        assets: dict[str, JsonValue] = {}
        observations: list[JsonValue] = []
        validation_reports: dict[str, JsonValue] = {}
        executions: list[JsonValue] = []
        audit: list[JsonValue] = []
        audit_truncated = False
        for task in tasks:
            with connection(self.ledger.path) as db:
                events = db.execute("SELECT sequence,event,at,body FROM task_audit WHERE swarm_id=? AND task_id=? "
                    "ORDER BY sequence LIMIT ?", (self.config.swarm_id, task.signal.task_id, limit + 1)).fetchall()
            audit_truncated = audit_truncated or len(events) > limit
            for event in events[:limit]:
                body = _OBJECT.validate_json(event["body"])
                record: dict[str, JsonValue] = {"sequence": event["sequence"], "task_id": task.signal.task_id,
                    "event": event["event"], "at": event["at"], "body": body}
                audit.append(record)
                run_id = body.get("run_id")
                if event["event"] == "research_execution" and isinstance(run_id, str):
                    execution: dict[str, JsonValue] = {"task_id": task.signal.task_id, "run_id": run_id,
                        "audit_sequence": event["sequence"], "recorded_result": body.get("result")}
                    try:
                        execution["verified_result"] = self.result(task.signal.task_id, run_id)
                        execution["archive_status"] = "verified"
                    except (ValueError, OSError, KeyError) as error:
                        execution.update({"archive_status": "refused", "refusal": type(error).__name__})
                    executions.append(execution)
            asset_ids: set[str] = set()
            plan = task.acceptance.get("generated_plan")
            if isinstance(plan, dict) and isinstance(plan.get("candidate_asset_id"), str):
                asset_ids.add(str(plan["candidate_asset_id"]))
                report_id = task.acceptance.get("generated_report_id")
                if isinstance(report_id, str):
                    validation_reports[report_id] = self.store.generated_report(report_id).model_dump(mode="json")
                applied_report = (task.result or {}).get("report_id")
                if (task.result or {}).get("applied") is True and isinstance(applied_report, str):
                    validation_reports[applied_report] = self.store.generated_report(applied_report).model_dump(mode="json")
            for key in ("asset_id", "candidate_asset_id"):
                value = (task.result or {}).get(key)
                if isinstance(value, str):
                    asset_ids.add(value)
            for asset_id in asset_ids:
                if asset_id in assets:
                    continue
                candidate = self._asset(task.signal.task_id, asset_id)
                assets[asset_id] = {"asset_id": asset_id, "candidate": candidate.model_dump(mode="json"),
                                    "stored_state": self.store.state(asset_id)}
                observations.extend(r.model_dump(mode="json") for r in self.store.research_reports(asset_id)
                                    if r.task_id in task_ids and self._task_visible(r.task_id))
        receipts: list[JsonValue] = [_OBJECT.validate_json(r.model_dump_json()) for r in self.store.adoptions()
                                    if r.context.task_id in task_ids and r.context.swarm_id == self.config.swarm_id]
        return {"schema_version": "research-package/v1", "project_id": bound, "context": context,
                "tasks": [t.model_dump(mode="json") for t in tasks], "tasks_truncated": len(rows) > limit,
                "limit": limit, "assets": list(assets.values()), "persisted_observations": observations,
                "generated_validation_reports": list(validation_reports.values()),
                "executions": executions, "task_audit": audit, "audit_truncated": audit_truncated,
                "adoption_receipts": receipts, "export_performed_external_io": False,
                "evidence_boundary": "per_record_provenance", "completion_claim": False}

    def _task_research(self, task_id: str, *, limit: int = 100) -> dict[str, JsonValue]:
        task = self._task(task_id)
        project_id = task.signal.payload.get("project_id")
        if isinstance(project_id, str):
            return self.research_context(project_id, task_id=task_id, limit=limit)
        notes = [n for n in self.knowledge.notes(task_id=task_id)
                 if not isinstance(project_id, str) or n.project_id == project_id]
        return {"notes": [n.model_dump(mode="json") for n in notes]}

    # -- research-v1: three-axis, advisory, acceptance, lifecycle ----------

    def _contribution_branch(self, task_id: str, project_id: str) -> str | None:
        try:
            task = self._task(task_id)
        except (KeyError, PermissionError):
            return None
        payload = task.signal.payload
        if payload.get("project_id") != project_id:
            return None
        branch_id = payload.get("branch_id")
        return branch_id if isinstance(branch_id, str) else None

    def _project_result(self, result: ThreeAxisResult, project_id: str) -> bool:
        try:
            task = self._task(result.task_id)
        except (KeyError, PermissionError):
            return False
        return task.signal.payload.get("project_id") == project_id

    def _research_branches(self, project_id: str) -> tuple[Branch, ...]:
        """Append lifecycle transitions; the feedback store alone derives references."""
        branches: list[Branch] = []
        for branch in self.knowledge.branches(project_id):
            projected = Branch.model_validate({
                "branch_id": branch.branch_id, "status": branch.status,
                "parent_id": branch.parent_branch_id, "authorized": True})
            for event in self.feedback_store.corrections(branch.branch_id):
                projected = self.feedback_store.policy.apply_correction(projected, event)
            branches.append(projected)
        return tuple(branches)

    def accept_result(self, result_id: str) -> dict[str, JsonValue]:
        """Independently accept one trusted result under the host's bound reviewer.

        The reviewer is the host identity (``HostConfig.worker_id``), never a
        caller string; the store re-derives the result from trusted ledger/asset
        facts and rejects replays, self-approval, forged ids and foreign scopes.
        """
        self._research_action("review")
        bound = self._project_id()
        self._authorize_project(bound)
        fact = next((r for r in self.feedback_store.trusted() if r.result_id == result_id), None)
        if fact is not None and not self._project_result(fact, bound):
            raise PermissionError("result_outside_host_project_or_scope")
        decision = self.feedback_store.accept(result_id)
        if decision.accepted and fact is not None:
            self._record_event("contribution_accepted", bound, task_id=fact.task_id,
                               branch_id=self._contribution_branch(fact.task_id, bound), source_ref=result_id,
                               payload={"result_id": result_id, "provenance": fact.provenance})
        return _OBJECT.validate_json(decision.model_dump_json())

    def research_advisory(self, project_id: str | None = None) -> dict[str, JsonValue]:
        """research-v1 advisory: accepted contributions + branch opportunities.

        Advisory only — claiming still goes through the existing TaskLedger which
        re-checks scope, capabilities, dependencies, lease/fencing and budget.
        """
        bound = self._project_id(project_id)
        self._authorize_project(bound)
        result = self.feedback_store.advisory(self._research_branches(bound))
        result["project_id"] = bound
        return _OBJECT.validate_python(result)

    def research_snapshot(self, project_id: str | None = None) -> dict[str, JsonValue]:
        """Three-axis/context/project snapshot (research-v1), separate from legacy v0.1."""
        bound = self._project_id(project_id)
        self._authorize_project(bound)
        advice = self.research_advisory(bound)
        raw = advice["contributions"]
        results = [ThreeAxisResult.model_validate(c) for c in raw] if isinstance(raw, list) else []
        raw_branches = advice["branches"]
        branches = tuple(Branch.model_validate(b) for b in raw_branches) if isinstance(raw_branches, list) else ()
        feedback = self.feedback_store.policy.snapshot(results, branches)
        snapshot: dict[str, JsonValue] = dict(feedback)
        snapshot["project_id"] = bound
        snapshot["contributions"] = [c.model_dump(mode="json") for c in self.feedback_store.contributions()
                                     if self._project_result(c, bound)]
        snapshot["effective_contributions"] = [c.model_dump(mode="json") for c in results]
        branch_ids = {b.branch_id for b in branches}
        result_ids = {c.result_id for c in self.feedback_store.contributions() if self._project_result(c, bound)}
        snapshot["corrections"] = [c.model_dump(mode="json") for c in self.feedback_store.corrections()
                                   if c.branch_id in branch_ids]
        snapshot["supersessions"] = [c.model_dump(mode="json") for c in self.feedback_store.supersessions()
                                     if c.result_id in result_ids]
        snapshot["trusted_results"] = [c.model_dump(mode="json") for c in self.feedback_store.trusted()
                                       if self._project_result(c, bound)]
        snapshot["branches"] = [b.model_dump(mode="json") for b in branches]
        snapshot["opportunities"] = advice["opportunities"]
        return _OBJECT.validate_python(snapshot)

    def record_correction(self, branch_id: str, kind: CorrectionKind, reason: str,
                          source_ref: str) -> dict[str, JsonValue]:
        """Append a branch lifecycle correction (sleep/downgrade/reopen); never deletes history."""
        self._research_action("review")
        bound = self._project_id()
        self._authorize_project(bound)
        self._require_branch(bound, branch_id)
        self._require_research_source(bound, source_ref)
        for previous in self.feedback_store.corrections(branch_id):
            if (previous.kind, previous.reason, previous.source_ref, previous.actor) == (
                    kind, reason, source_ref, self.config.worker_id):
                return _OBJECT.validate_json(previous.model_dump_json())
        event = CorrectionEvent(event_id=uuid4().hex, branch_id=branch_id, kind=kind, reason=reason,
                                source_ref=source_ref, actor=self.config.worker_id, at=self.ledger.now())
        branch = next(b for b in self._research_branches(bound) if b.branch_id == branch_id)
        self.feedback_store.policy.apply_correction(branch, event)
        self.feedback_store.record_correction(event)
        self._record_event("branch_" + kind, bound, branch_id=branch_id, source_ref=source_ref,
                           payload={"correction_id": event.event_id, "reason": reason})
        return _OBJECT.validate_json(event.model_dump_json())

    def record_supersession(self, result_id: str, reason: str, source_ref: str, *,
                            superseded_by: str | None = None) -> dict[str, JsonValue]:
        """Append a contribution supersession; the original contribution is retained."""
        self._research_action("review")
        bound = self._project_id()
        self._authorize_project(bound)
        self._require_research_source(bound, source_ref)
        contributions = {c.result_id: c for c in self.feedback_store.contributions()
                         if self._project_result(c, bound)}
        if result_id not in contributions or (superseded_by is not None and superseded_by not in contributions):
            raise PermissionError("contribution_outside_host_project_or_scope")
        if contributions[result_id].actor == self.config.worker_id:
            raise PermissionError("independent_reviewer_required")
        for previous in self.feedback_store.supersessions():
            if (previous.result_id, previous.superseded_by, previous.reason, previous.source_ref) == (
                    result_id, superseded_by, reason, source_ref):
                return _OBJECT.validate_json(previous.model_dump_json())
        event = SupersessionEvent(event_id=uuid4().hex, result_id=result_id, superseded_by=superseded_by,
                                  reason=reason, source_ref=source_ref, actor=self.config.worker_id,
                                  at=self.ledger.now())
        self.feedback_store.record_supersession(event)
        self._record_event("contribution_superseded", bound, source_ref=source_ref,
                           task_id=contributions[result_id].task_id, payload={"result_id": result_id, "reason": reason})
        return _OBJECT.validate_json(event.model_dump_json())

    def _discover_research_v1(self) -> dict[str, JsonValue] | None:
        if not self.config.project_id:
            return None
        return self.research_advisory(self.config.project_id)

    def _require_research_source(self, project_id: str, source_ref: str) -> None:
        notes = [n for n in self.knowledge.notes(project_id) if self._note_in_scope(n)]
        if any(source_ref == n.note_id or source_ref in {s.source_id for s in n.source_refs} for n in notes):
            return
        if any(c.result_id == source_ref and self._project_result(c, project_id)
               for c in self.feedback_store.contributions()):
            return
        raise PermissionError("research_source_not_in_project_context")

    @staticmethod
    def _opportunities(advisory: dict[str, JsonValue]) -> dict[str, dict[str, JsonValue]]:
        plan = advisory.get("opportunities")
        values = plan.get("opportunities") if isinstance(plan, dict) else None
        if not isinstance(values, list):
            raise ValueError("invalid_research_opportunities")
        return {str(v["branch_id"]): _OBJECT.validate_python(v) for v in values if isinstance(v, dict)}

    @staticmethod
    def _task_opportunity(task: TaskRecord, opportunities: dict[str, dict[str, JsonValue]]) -> dict[str, JsonValue]:
        branch_id = task.signal.payload.get("branch_id")
        if branch_id is None:
            return {"branch_id": None, "eligible": True, "share": 1.0, "supported_by": [], "refuted_by": [],
                    "reasons": ["project_work_without_branch"]}
        return opportunities.get(str(branch_id), {"branch_id": branch_id, "eligible": False, "share": 0.0})

    def _opportunity_allows(self, task: TaskRecord, opportunities: dict[str, dict[str, JsonValue]]) -> bool:
        return self._task_opportunity(task, opportunities).get("eligible") is True

    def _opportunity_share(self, task: TaskRecord, opportunities: dict[str, dict[str, JsonValue]]) -> float:
        value = self._task_opportunity(task, opportunities).get("share")
        return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else 0.0

    def choose(self, task_id: str | None = None, *, reason: str = "", limit: int = 100) -> dict[str, JsonValue]:
        """A member selects an opportunity; the later claim remains authoritative."""
        self._research_action("choose")
        bound = self._project_id()
        self._authorize_project(bound)
        candidates = self.discover(limit)
        tasks: list[TaskRecord] = []
        for candidate in candidates:
            signal = candidate.get("signal")
            if isinstance(signal, dict) and isinstance(signal.get("task_id"), str):
                tasks.append(self._task(str(signal["task_id"])))
        opportunities = self._opportunities(self.research_advisory(bound))
        counts: dict[str, int] = {}
        for task in tasks:
            branch = str(task.signal.payload.get("branch_id"))
            counts[branch] = counts.get(branch, 0) + 1
        weights = [self._opportunity_share(task, opportunities) / counts[str(task.signal.payload.get("branch_id"))]
                   for task in tasks]
        recommended = self.router.rng.choices(tasks, weights=weights, k=1)[0].signal.task_id if tasks and sum(weights) > 0 else None
        selected = task_id if task_id is not None else recommended
        if selected is not None and selected not in {t.signal.task_id for t in tasks}:
            raise PermissionError("choice_not_current_legal_opportunity")
        selected_task = next((t for t in tasks if t.signal.task_id == selected), None)
        opportunity = self._task_opportunity(selected_task, opportunities) if selected_task is not None else None
        decision: dict[str, JsonValue] = {
            "policy_version": "research-v1", "project_id": bound, "worker_id": self.config.worker_id,
            "selected": selected, "recommended_task_id": recommended, "overridden": selected != recommended,
            "reason": reason or "member_accepted_research_opportunity", "advisory_only": True,
            "claim_requires_recheck": True, "opportunity": opportunity,
            "candidate_task_ids": [t.signal.task_id for t in tasks], "query_limit": limit,
            "candidate_window_truncated": len(candidates) == limit}
        self.ledger.record_event("research_choice", decision, task_id=selected)
        return decision

    def _record_research_selection(self, task: TaskRecord, lease: Lease) -> dict[str, JsonValue]:
        with connection(self.ledger.path) as db:
            rows = db.execute("SELECT body FROM task_audit WHERE swarm_id=? AND task_id=? AND event='research_choice' "
                              "ORDER BY sequence DESC", (self.config.swarm_id, task.signal.task_id)).fetchall()
        choice = next((_OBJECT.validate_json(row[0]) for row in rows
                       if _OBJECT.validate_json(row[0]).get("worker_id") == self.config.worker_id), None)
        current = self._task_opportunity(task, self._opportunities(self.research_advisory()))
        references: list[JsonValue] = []
        for name in ("supported_by", "refuted_by"):
            values = current.get(name)
            if isinstance(values, list):
                references.extend(values)
        selection: dict[str, JsonValue] = {
            "policy_version": "research-v1", "project_id": self.config.project_id,
            "worker_id": self.config.worker_id, "actual_task_id": task.signal.task_id, "token": lease.token,
            "choice": choice, "opportunity": current, "reason": choice.get("reason") if choice else "direct_member_choice",
            "result_references": references,
            "claim_authority": "TaskLedger"}
        self.ledger.record_event("research_selection", selection, task_id=task.signal.task_id)
        return selection

    def _generated_tools(self) -> GeneratedResearch:
        if self.generated is None:
            raise AssetSafetyError("generated_experiment_backend_not_configured")
        return self.generated

    def prepare_candidate_experiment(self, task_id: str, token: int, plan: dict[str, JsonValue],
                                     files: dict[str, str] | None = None, *, asset_id: str | None = None,
                                     purpose: Purpose = "original") -> dict[str, JsonValue]:
        from orchestration.experiments.generated import GeneratedExperimentPlan
        return self._generated_tools().prepare(task_id, token, GeneratedExperimentPlan.model_validate(plan),
                                               files, asset_id=asset_id, purpose=purpose)

    def admit_candidate_experiment(self, task_id: str, token: int) -> dict[str, JsonValue]:
        return self._generated_tools().admit(task_id, token)


def build_service(config: HostConfig) -> ResearchService:
    """Shared production factory used by stdio and the product's official adapter."""
    backend: ExperimentBackend | None = None
    if config.experiment_backend:
        from swarm.research.experiments import OfficialExperiments
        backend = OfficialExperiments(config)
    return ResearchService(config, backend=backend)
