"""Approved content reuse and adoption bound to a completed fenced task result."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Protocol

from contracts.identity import AttemptId
from local_assets.models import (
    AdoptionReceipt, AssetSafetyError, Candidate, ConsumptionContext,
    ConsumptionExecution, FileChange, InjectedAsset,
)
from local_assets.paths import check_target, relative_path, safe_join
from local_assets.store import LocalAssetStore
from local_assets.validate import blast_radius, inspect_candidate
from swarm.models import TaskRecord


class CompletedLedger(Protocol):
    def get(self, task_id: str) -> TaskRecord | None: ...


def _within(path: str, scope: str) -> bool:
    return scope == "." or path == scope or path.startswith(scope + "/")


class AssetConsumer:
    def __init__(self, store: LocalAssetStore) -> None:
        self.store = store

    def inject(self, asset_id: str, context: ConsumptionContext) -> InjectedAsset:
        candidate = self.store.fetch_approved(asset_id)
        relative_path(context.scope, allow_root=True)
        if not set(candidate.dependencies).issubset(context.completed_dependencies):
            raise AssetSafetyError("asset_dependencies_unsatisfied")
        if not set(candidate.required_capabilities).issubset(context.capabilities):
            raise AssetSafetyError("asset_capabilities_unsatisfied")
        if not _within(context.scope, candidate.scope):
            raise AssetSafetyError("asset_scope_inapplicable")
        # Injection deliberately has no adoption or execution database write.
        return InjectedAsset(asset_id=asset_id, candidate=candidate, context=context)

    def execute(self, injected: InjectedAsset, *, attempt: AttemptId, base_revision: str,
                path_map: dict[str, str], preimages: dict[str, str | None],
                base_head: str | None = None) -> ConsumptionExecution:
        verified = self.inject(injected.asset_id, injected.context)
        if injected != verified or attempt.task_id != injected.context.task_id:
            raise AssetSafetyError("injected_execution_identity_mismatch")
        if attempt.task_id == injected.candidate.attempt.task_id:
            raise AssetSafetyError("reuse_requires_new_task")
        source = {change.path: change for change in verified.candidate.changes}
        if (not path_map or not set(path_map).issubset(source)
                or len(set(path_map.values())) != len(path_map)
                or set(preimages) != set(path_map.values())):
            raise AssetSafetyError("invalid_reuse_mapping")
        changes: list[FileChange] = []
        for origin, destination in path_map.items():
            relative_path(destination)
            if not _within(destination, injected.context.scope):
                raise AssetSafetyError("reuse_destination_outside_scope")
            # Actual data use: only the addressed asset supplies after bytes.
            # There is no eval, import, template interpolation, command or network.
            changes.append(FileChange(path=destination, before=preimages[destination], after=source[origin].after))
        candidate = Candidate(
            attempt=attempt, base_revision=base_revision, base_head=base_head,
            scope=injected.context.scope, changes=tuple(changes),
            declared_files=len(changes), declared_lines=0,
            summary="Literal content reuse from " + injected.asset_id,
            required_capabilities=verified.candidate.required_capabilities,
            dependencies=verified.candidate.dependencies,
        )
        files, lines = blast_radius(candidate)
        candidate = candidate.model_copy(update={"declared_files": files, "declared_lines": lines})
        inspect_candidate(candidate)
        candidate_asset_id = self.store.publish(candidate)
        execution = ConsumptionExecution(
            asset_id=injected.asset_id, context=injected.context, candidate=candidate,
            candidate_asset_id=candidate_asset_id, created_at=time.time(),
        )
        with self.store.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT body FROM consumptions WHERE execution_id=?",
                             (injected.context.execution_id,)).fetchone()
            if row:
                old = ConsumptionExecution.model_validate_json(row[0])
                if old.model_copy(update={"created_at": execution.created_at}) != execution:
                    raise AssetSafetyError("execution_identity_conflict")
                return old
            db.execute("INSERT INTO consumptions VALUES (?, ?)",
                       (injected.context.execution_id, execution.model_dump_json()))
        return execution

    def record_adoption(self, execution_id: str, result_id: str,
                        ledger: CompletedLedger) -> AdoptionReceipt:
        execution = self.store.consumption(execution_id)
        context = execution.context
        self.store.fetch_approved(execution.asset_id)
        self.store.fetch_approved(execution.candidate_asset_id)
        task = ledger.get(context.task_id)
        if (task is None or task.status != "completed" or not task.effect_applied or task.result_id != result_id
                or task.swarm_id != context.swarm_id
                or task.token != context.fencing_token or task.owner != context.worker_id
                or task.signal.scope != context.scope or task.result is None):
            raise AssetSafetyError("adoption_requires_completed_fenced_execution")
        result = task.result
        consumed = result.get("consumed_asset_ids")
        if (result.get("execution_id") != execution_id or result.get("input_context") != context.input_context
                or result.get("candidate_asset_id") != execution.candidate_asset_id
                or result.get("applied") is not True or not isinstance(consumed, list)
                or consumed != [execution.asset_id]):
            raise AssetSafetyError("adoption_result_mismatch")
        if self.store.fetch(execution.candidate_asset_id) != execution.candidate:
            raise AssetSafetyError("consumed_candidate_mismatch")
        receipt = AdoptionReceipt(asset_id=execution.asset_id, candidate_asset_id=execution.candidate_asset_id,
                                  context=context, result_id=result_id, adopted_at=time.time())
        # An existing immutable adoption is a historical fact. Later legitimate
        # tasks may change target bytes; replay must not erase that prior effect.
        with self.store.connection() as db:
            row = db.execute("SELECT body FROM adoptions WHERE execution_id=?", (execution_id,)).fetchone()
        if row:
            old = AdoptionReceipt.model_validate_json(row[0])
            if old.model_copy(update={"adopted_at": receipt.adopted_at}) != receipt:
                raise AssetSafetyError("adoption_identity_conflict")
            return old
        target = check_target(Path(task.signal.workspace))
        for change in execution.candidate.changes:
            path = safe_join(target, change.path)
            expected = change.after.encode("utf-8") if change.after is not None else None
            if path.is_dir() or (path.read_bytes() if path.is_file() else None) != expected:
                raise AssetSafetyError("adoption_target_effect_missing")
        with self.store.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT body FROM adoptions WHERE execution_id=?", (execution_id,)).fetchone()
            if row:
                old = AdoptionReceipt.model_validate_json(row[0])
                if old.model_copy(update={"adopted_at": receipt.adopted_at}) != receipt:
                    raise AssetSafetyError("adoption_identity_conflict")
                return old
            db.execute("INSERT INTO adoptions VALUES (?, ?)", (execution_id, receipt.model_dump_json()))
        return receipt
