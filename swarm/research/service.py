"""Host-bound tools; task assignment remains a voluntary ledger claim."""
from __future__ import annotations

from pathlib import Path
from collections.abc import Callable
from typing import Literal, Protocol
from uuid import uuid4

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
from swarm.models import Lease, Signal, TaskRecord
from swarm.feedback import trusted_facts
from swarm.pheromone import PheromoneField
from swarm.router import Router
from swarm.research.knowledge import ResearchKnowledge
from swarm.research.models import HostConfig
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

_OBJECT = TypeAdapter(dict[str, JsonValue])
Purpose = Literal["original", "reproduction", "inheritance", "counterexample"]


class ExperimentBackend(Protocol):
    async def execute(self, plan: dict[str, JsonValue], run_id: str, lease: Lease) -> dict[str, JsonValue]: ...
    def read(self, run_id: str) -> dict[str, JsonValue]: ...
    def evaluate(self, run_id: str, plan: dict[str, JsonValue], lease: Lease) -> dict[str, JsonValue]: ...


class ResearchService:
    def __init__(self, config: HostConfig, *, ledger: TaskLedger | None = None,
                 store: LocalAssetStore | None = None, backend: ExperimentBackend | None = None) -> None:
        self.config = config
        for value in (config.ledger_path, config.workspace, config.assets_root, config.evidence_root):
            if not Path(value).is_absolute():
                raise ValueError("host_paths_must_be_absolute")
            no_links(Path(value))
        self.locality = config.locality()
        self.ledger = ledger or TaskLedger(config.ledger_path, config.swarm_id)
        if self.ledger.swarm_id != config.swarm_id or self.ledger.path != Path(config.ledger_path).resolve():
            raise ValueError("host_ledger_identity_mismatch")
        self.store = store or LocalAssetStore(config.assets_root)
        self.backend = backend
        self.field = PheromoneField(self.ledger.path.with_name("policy-field.sqlite3"), ledger=self.ledger,
                                    clock=self.ledger.clock)
        self.router = Router(self.field, strategy_version="v0.1")
        knowledge_path = config.knowledge_path()
        if not knowledge_path.is_absolute():
            raise ValueError("research_knowledge_path_must_be_absolute")
        no_links(knowledge_path)
        self.knowledge = ResearchKnowledge(knowledge_path, clock=self.ledger.clock)

    def discover(self, limit: int = 100) -> list[dict[str, JsonValue]]:
        self.field.synchronize(trusted_facts(self.ledger, self.store.root))
        recommendation = self.router.recommend(self.config.worker_id, self.locality,
                                                {key: 1.0 for key in self.config.capabilities}, limit=limit)
        responses: list[dict[str, JsonValue]] = []
        for task in self.ledger.candidates(self.locality, limit=limit, capabilities=self.config.capabilities):
            response = _OBJECT.validate_json(task.model_dump_json())
            response["policy_recommendation"] = (recommendation if not responses else {
                "routing_sequence": recommendation["routing_sequence"], "policy_version": recommendation["policy_version"],
                "selected": recommendation["selected"], "reference_only": True})
            response["research"] = self._task_research(task.signal.task_id)
            responses.append(response)
        return responses

    def _task(self, task_id: str, *, require_capability: bool = False) -> TaskRecord:
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
        return task

    def context(self, task_id: str) -> dict[str, JsonValue]:
        task = self._task(task_id)
        return {"task": _OBJECT.validate_json(task.model_dump_json()),
                "project_context": self.config.project_context,
                "dependency_results": [{"task_id": d, "status": self._task(d).status,
                                        "result": self._task(d).result} for d in task.dependencies],
                "worker_id": self.config.worker_id, "agent": _OBJECT.validate_json(self.config.agent.model_dump_json()),
                "research": self._task_research(task_id)}

    def claim(self, task_id: str, ttl_seconds: float = 60) -> dict[str, JsonValue] | None:
        self._task(task_id, require_capability=True)
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
        return {"plan": self._plan(task_id), "backend_configured": self.backend is not None,
                "allocation": "on_execute", "isolation_requested": "fresh_sandbox_per_execution",
                "execution_started": False}

    async def execute(self, task_id: str, token: int) -> dict[str, JsonValue]:
        lease = self._lease(task_id, token)
        plan = self._plan(task_id)
        if self.backend is None:
            raise AssetSafetyError("experiment_backend_not_configured")
        run_id = uuid4().hex
        self.ledger.begin_execution(lease, run_id, max_executions=self.config.max_experiments_per_task)
        # No SQLite transaction survives this boundary. Exceptions/crashes retain
        # unconfirmed_request_id and prohibit automatic replay after expiry.
        result = await self.backend.execute(plan, run_id, lease)
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
        if self.backend is None:
            raise AssetSafetyError("experiment_backend_not_configured")
        return self.backend.read(run_id)

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
        policy = ValidationPolicy.model_validate(self._task(task_id).acceptance.get("file_policy"))
        report = AssetValidator(self.store, self.config.workspace, policy=policy).validate(asset_id)
        self._lease(task_id, token)
        return _OBJECT.validate_json(report.model_dump_json())

    def _asset(self, task_id: str, asset_id: str) -> Candidate:
        task = self._task(task_id)
        candidate = self.store.fetch(asset_id)
        if candidate.scope != task.signal.scope:
            raise PermissionError("asset_scope_mismatch")
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
                                      "scientific_verdict": last.scientific_verdict,
                                      "execution_state": last.execution_state,
                                      "stage": "evidence_submitted", "approved": False,
                                      "provenance": last.provenance}
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
        if not 1 <= limit <= 100 or len(query) > 1000:
            raise ValueError("bounded_search_required")
        with self.store.connection() as db:
            ids = [str(row[0]) for row in db.execute("SELECT asset_id FROM assets WHERE instr(lower(body),lower(?))>0 LIMIT 1000",
                                                    (query,))]
        results: list[dict[str, JsonValue]] = []
        for asset_id in ids:
            candidate = self.store.fetch(asset_id)
            target = canonical_scope(Path(self.config.workspace) / candidate.scope)
            if not any(Path(target).is_relative_to(Path(canonical_scope(Path(self.config.workspace) / s)))
                       for s in self.config.authorized_scopes):
                continue
            if not set(candidate.required_capabilities).issubset(self.config.capabilities):
                continue
            results.append({"asset_id": asset_id, "candidate": _OBJECT.validate_json(candidate.model_dump_json()),
                            "state": self.store.state(asset_id),
                            "research_reports": [_OBJECT.validate_json(r.model_dump_json()) for r in self.store.research_reports(asset_id)],
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
        policy = ValidationPolicy.model_validate(self._task(task_id).acceptance.get("file_policy"))
        self.store.fetch_approved(asset_id)
        prepared = AssetApplicator(self.store, self.config.workspace, policy_version=policy.version,
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
        if self.config.project_id and project_id != self.config.project_id:
            raise PermissionError("project_outside_host_authorization")
        return self.knowledge.project(project_id)

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
                              provenance="live", event_kind=kind,
                              payload=payload or {}, correlation_ref=None)
        self.knowledge.record(event)
        self.ledger.record_event("research." + kind, event.model_dump(mode="json"), task_id=task_id)

    def create_project(self, project_id: str, goal: str, *,
                       allowed_domains: tuple[str, ...] = (),
                       data_bounds: dict[str, str] | None = None,
                       authorization_ref: str | None = None,
                       milestones: tuple[str, ...] = ()) -> dict[str, JsonValue]:
        """Idempotent project registration; authorization is host-supplied, never caller-granted."""
        if self.config.project_id and project_id != self.config.project_id:
            raise PermissionError("project_outside_host_authorization")
        if authorization_ref is not None and authorization_ref != self.config.authorization_ref:
            raise PermissionError("authorization_ref_is_host_bound")
        project = ResearchProject(project_id=project_id, goal=goal, allowed_domains=allowed_domains,
                                  data_bounds=data_bounds or {}, authorization_ref=self.config.authorization_ref,
                                  milestones=milestones, created_at=self.ledger.now())
        saved = self.knowledge.put_project(project)
        self._record_event("project_created", project_id)
        return _OBJECT.validate_json(saved.model_dump_json())

    def project(self, project_id: str | None = None) -> dict[str, JsonValue]:
        return _OBJECT.validate_json(self._authorize_project(self._project_id(project_id)).model_dump_json())

    def create_branch(self, project_id: str, branch_id: str, title: str, goal: str, *,
                      parent_branch_id: str | None = None) -> dict[str, JsonValue]:
        self._authorize_project(project_id)
        self._require_branch(project_id, parent_branch_id)
        branch = ResearchBranch(branch_id=branch_id, project_id=project_id, parent_branch_id=parent_branch_id,
                                title=title, goal=goal, status="proposed", created_at=self.ledger.now())
        saved = self.knowledge.put_branch(branch)
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
        self._authorize_project(project_id)
        self._require_branch(project_id, branch_id)
        self._require_hypothesis(project_id, hypothesis_id)
        if task_id is not None:
            self._task(task_id)
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
            self._task(dependency)
        if derived_from is not None:
            self._task(derived_from)
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

    def research_context(self, project_id: str | None = None, *, limit: int = 100) -> dict[str, JsonValue]:
        """Shared research memory for a (possibly new) member (FR-04/05/10).

        Notes are trimmed by the host's locality (a note attached to a task
        outside the host's authorized scope is hidden) and each collection is
        bounded to ``limit`` with an explicit ``*_truncated`` flag.
        """
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be in [1,1000]")
        bound = self._project_id(project_id)
        project = self._authorize_project(bound)
        notes = [n for n in self.knowledge.notes(bound) if self._note_in_scope(n)]
        unverified = [n for n in notes if n.review_state != "verified"]
        verified = [n for n in notes if n.review_state == "verified"]
        branches = self.knowledge.branches(bound)
        hypotheses = self.knowledge.hypotheses(bound)
        proposals = self.knowledge.proposals(bound)
        events = self.knowledge.events(bound, limit=min(limit + 1, 1000))
        return {"project": _OBJECT.validate_json(project.model_dump_json()), "limit": limit,
                "branches": [b.model_dump(mode="json") for b in branches[:limit]],
                "branches_truncated": len(branches) > limit,
                "hypotheses": [h.model_dump(mode="json") for h in hypotheses[:limit]],
                "hypotheses_truncated": len(hypotheses) > limit,
                "notes_unverified": [n.model_dump(mode="json") for n in unverified[:limit]],
                "notes_unverified_truncated": len(unverified) > limit,
                "notes_verified": [n.model_dump(mode="json") for n in verified[:limit]],
                "notes_verified_truncated": len(verified) > limit,
                "proposals": [p.model_dump(mode="json") for p in proposals[:limit]],
                "proposals_truncated": len(proposals) > limit,
                "events": [e.model_dump(mode="json") for e in events[:limit]],
                "events_truncated": len(events) > limit}

    def _task_research(self, task_id: str) -> dict[str, JsonValue]:
        notes = self.knowledge.notes(task_id=task_id)
        return {"notes": [n.model_dump(mode="json") for n in notes]}
