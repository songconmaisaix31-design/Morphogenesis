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
from swarm.models import Lease, TaskRecord
from swarm.research.models import HostConfig
from swarm.task_ledger import LeaseLost, TaskLedger, canonical_scope, connection

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

    def discover(self, limit: int = 100) -> list[dict[str, JsonValue]]:
        return [_OBJECT.validate_json(t.model_dump_json()) for t in self.ledger.candidates(
            self.locality, limit=limit, capabilities=self.config.capabilities)]

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
                "worker_id": self.config.worker_id, "agent": _OBJECT.validate_json(self.config.agent.model_dump_json())}

    def claim(self, task_id: str, ttl_seconds: float = 60) -> dict[str, JsonValue] | None:
        self._task(task_id, require_capability=True)
        lease = self.ledger.claim(task_id, self.config.worker_id, locality=self.locality, ttl_seconds=ttl_seconds)
        if lease is None:
            return None
        response = _OBJECT.validate_json(lease.model_dump_json())
        response["attempt_id"] = _OBJECT.validate_json(AttemptId(task_id=task_id, agent=self.config.agent,
                                                               attempt=self.ledger.get(task_id).attempts).model_dump_json())
        return response

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
        result: dict[str, JsonValue] = {"candidate_asset_id": asset_id, "applied": True}
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
        return response
