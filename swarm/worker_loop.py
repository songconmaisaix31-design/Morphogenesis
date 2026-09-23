"""Independent bounded forager using only authorized local task observations."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import json
import os
from pathlib import Path
import random
from threading import Event, Lock, Thread
import time
from typing import Literal, Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, JsonValue, TypeAdapter

from contracts.identity import AgentId, AttemptId
from contracts.provenance import Acceptance, Provenance
from local_assets.apply import AssetApplicator
from local_assets.consume import AssetConsumer
from local_assets.models import (
    AssetSafetyError, Candidate, ConsumptionContext, ConsumptionExecution, FileChange,
    ValidationPolicy, ValidationReport,
)
from local_assets.paths import FROZEN_MAINLINE, check_target, git, no_links, safe_join
from local_assets.promote import AssetPromoter
from local_assets.snapshot import snapshot_revision
from local_assets.store import LocalAssetStore
from local_assets.validate import AssetValidator, blast_radius, inspect_candidate
from orchestration.gateway import _usage
from swarm.budget import BudgetBlocked, BudgetLedger
from swarm.hub_mirror import HubMirror
from swarm.lease import LeaseManager
from swarm.models import BudgetPolicy, ExecutionBound, Lease, Locality, Reservation, Signal
from swarm.pheromone import PheromoneField
from swarm.router import Router
from swarm.task_ledger import RunLimitReached, TaskLedger

_JSON: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)
_CHANGES = TypeAdapter(tuple[FileChange, ...])
_SOURCE = Path(__file__).resolve().parents[1]
_FIXTURE_USAGE: JsonValue = {"usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}


class WorkerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)
    state: Path
    target: Path
    agent: AgentId
    locality: Locality
    budget: BudgetPolicy
    swarm_id: str = Field(default="local-fixture", min_length=1, max_length=120)
    capabilities: dict[str, float] = Field(default_factory=lambda: {"repair": 1.0})
    energy: int = Field(default=20, ge=1, le=10000)
    max_idle: int = Field(default=3, ge=1, le=100)
    idle_seconds: float = Field(default=0.05, gt=0, le=60)
    sleep_seconds: float = Field(default=0.05, gt=0, le=60)
    lease_seconds: float = Field(default=300, gt=0, le=3600)
    validation_seconds: float = Field(default=15, gt=0, le=300)
    seed: int | None = None

    @property
    def worker_id(self) -> str:
        return f"{self.agent.role}-{self.agent.instance}"


@dataclass(frozen=True)
class ExecutionResult:
    candidate: Candidate | None
    usage: JsonValue
    workspace: str | None = None
    provenance: Provenance = "mock"
    usage_source: Literal["fixture_mock", "provider_reported", "replay"] = "fixture_mock"
    original_run_uri: str | None = None


class Executor(Protocol):
    """Trusted bounded adapters only; CLI exposes the literal-file fixture."""

    provenance: Provenance
    usage_source: Literal["fixture_mock", "provider_reported", "replay"]
    original_run_uri: str | None

    def bound(self, signal: Signal) -> ExecutionBound: ...

    def execute(self, signal: Signal, attempt: AttemptId, repository: Path,
                directory: Path, *, base_revision: str, base_head: str) -> ExecutionResult: ...


class FixtureExecutor:
    """Actual file transformation, never arbitrary candidate code execution.

    Synthetic usage/bounds describe only this fixture, never remote billing.
    """

    provenance: Provenance = "mock"
    usage_source: Literal["fixture_mock", "provider_reported", "replay"] = "fixture_mock"
    original_run_uri: str | None = None

    def bound(self, signal: Signal) -> ExecutionBound:
        if "reuse_task_id" not in signal.payload:
            changes = _CHANGES.validate_python(signal.payload.get("changes"))
            if not 1 <= len(changes) <= 16:
                raise ValueError("fixture_input_bound")
        if len(json.dumps(signal.payload)) > 64 * 1024:
            raise ValueError("fixture_input_bound")
        return ExecutionBound(provider="local", model="fixture", input_tokens=1,
                              max_output_tokens=1, provider_enforced=True,
                              request_bound="verified", max_cost_usd=0.000002,
                              bound_evidence="local fixture: two synthetic units; no paid calls")

    def execute(self, signal: Signal, attempt: AttemptId, repository: Path,
                directory: Path, *, base_revision: str, base_head: str) -> ExecutionResult:
        changes = _CHANGES.validate_python(signal.payload.get("changes"))
        candidate = Candidate(attempt=attempt, base_revision=base_revision, base_head=base_head,
                              changes=changes, declared_files=len(changes), declared_lines=0,
                              scope=signal.scope)
        count, lines = blast_radius(candidate)
        candidate = candidate.model_copy(update={"declared_files": count, "declared_lines": lines})
        self.materialize(candidate, repository, directory)
        return ExecutionResult(candidate, _FIXTURE_USAGE, str(directory))

    @staticmethod
    def materialize(candidate: Candidate, repository: Path, directory: Path) -> None:
        inspect_candidate(candidate)
        tree = git(repository, "ls-tree", "-rz", candidate.base_revision)
        if any(item.startswith((b"120000 ", b"160000 ")) for item in tree.split(b"\0")):
            raise AssetSafetyError("baseline_links_or_submodules")
        no_links(directory)
        directory.parent.mkdir(parents=True, exist_ok=True)
        git(repository, "worktree", "add", "--detach", str(directory), candidate.base_revision)
        for change in candidate.changes:
            path = safe_join(directory, change.path)
            current = path.read_bytes() if path.is_file() else None
            expected = change.before.encode("utf-8") if change.before is not None else None
            if current != expected:
                raise AssetSafetyError("execution_preimage_mismatch")
            if change.after is None:
                path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(change.after.encode("utf-8"))


def check_state_path(path: Path) -> Path:
    no_links(path)
    root = path.resolve()
    for protected in (FROZEN_MAINLINE.resolve(), _SOURCE):
        if root == protected or root.is_relative_to(protected):
            raise AssetSafetyError("protected_runtime_state")
    return root


def _write_json(path: Path, value: JsonValue) -> None:
    no_links(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid4().hex + ".tmp")
    try:
        with temporary.open("x", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


class _Renewal:
    """A bounded lease keeper, with no task selection or worker messaging."""

    def __init__(self, manager: LeaseManager, lease: Lease, ttl: float) -> None:
        self.manager, self.current, self.ttl = manager, lease, ttl
        self.stop_event, self.lock = Event(), Lock()
        self.failed = False
        self.thread = Thread(target=self._run, name="scope-lease-renewal", daemon=True)

    def _run(self) -> None:
        while not self.stop_event.wait(max(0.001, min(1.0, self.ttl / 3))):
            with self.lock:
                try:
                    renewed = self.manager.renew(self.current, ttl_seconds=self.ttl)
                    if renewed is None:
                        self.failed = True
                        return
                    self.current = renewed
                except Exception:
                    self.failed = True
                    return

    def start(self) -> None:
        self.check()
        self.thread.start()

    def check(self) -> None:
        with self.lock:
            if self.failed or not self.manager.is_valid(self.current):
                raise AssetSafetyError("stale_lease")

    def stop(self) -> Lease:
        self.stop_event.set()
        if self.thread.ident is not None:
            self.thread.join(timeout=11)
        if self.thread.is_alive():
            raise AssetSafetyError("lease_renewal_did_not_stop")
        return self.current


class Worker:
    def __init__(self, config: WorkerConfig, executor: Executor | None = None, *,
                 mirror: HubMirror | None = None) -> None:
        self.config = config
        self.target = check_target(config.target, (_SOURCE,))
        self.state = check_state_path(config.state)
        if self.state == self.target or self.state.is_relative_to(self.target):
            raise AssetSafetyError("state_must_be_outside_promotion_target")
        if Path(config.locality.workspace).resolve() != self.target:
            raise AssetSafetyError("locality_target_mismatch")
        self.worker_id = config.worker_id
        self.executor = executor or FixtureExecutor()
        self.mirror = mirror
        Acceptance(provenance=self.executor.provenance, original_run_uri=self.executor.original_run_uri)
        self.ledger = TaskLedger(self.state / "tasks.sqlite3", config.swarm_id, limits=config.budget.limits)
        self.field = PheromoneField(self.state / "field.sqlite3", ledger=self.ledger)
        self.rng = random.Random(config.seed)
        self.router = Router(self.field, rng=self.rng)
        self.leases = LeaseManager(self.ledger)
        self.budget = BudgetLedger(self.state / "budget.sqlite3", config.swarm_id, config.budget)
        self.assets = LocalAssetStore(self.state / "assets")
        self.consumer = AssetConsumer(self.assets)
        self.status_path = self.state / "workers" / (self.worker_id + ".json")
        self.remaining = config.energy
        self.completed = 0
        self._active: Reservation | None = None
        self._pending: dict[str, JsonValue] | None = None

    def _status(self, state: str, reason: str = "") -> dict[str, JsonValue]:
        result: dict[str, JsonValue] = {
            "worker_id": self.worker_id, "swarm_id": self.config.swarm_id,
            "pid": os.getpid(), "state": state, "reason": reason,
            "remaining_energy": self.remaining, "completed": self.completed,
            "updated_at": time.time(), "provenance": self.executor.provenance,
            "evidence_class": "contract_local", "usage_source": self.executor.usage_source,
            "active_reservation": _JSON.validate_python(self._active.model_dump(mode="json"))
            if self._active is not None else None,
            "pending_finalization": self._pending,
        }
        _write_json(self.status_path, result)
        return result

    def _resume(self) -> None:
        # One process owns this configured worker identity. Durable holds also
        # cover a crash after reserve commits but before status is written.
        for reservation in self.budget.pending(self.worker_id):
            self.budget.mark_uncertain(reservation)
        no_links(self.status_path)
        if not self.status_path.exists():
            return
        previous = _JSON.validate_json(self.status_path.read_bytes())
        if (not isinstance(previous, dict) or previous.get("worker_id") != self.worker_id
                or previous.get("swarm_id") != self.config.swarm_id):
            raise ValueError("invalid_worker_state")
        remaining, completed = previous.get("remaining_energy"), previous.get("completed")
        if not isinstance(remaining, int) or not isinstance(completed, int):
            raise ValueError("invalid_worker_counters")
        self.remaining, self.completed = min(self.remaining, remaining), completed
        active = previous.get("active_reservation")
        if active is not None:
            self.budget.mark_uncertain(Reservation.model_validate(active))
        pending = previous.get("pending_finalization")
        if pending is not None:
            self._pending = TypeAdapter(dict[str, JsonValue]).validate_python(pending)
            self._finalize()
            self._status("recovered")

    def _audit(self, signal: Signal, lease: Lease, attempt: AttemptId, outcome: str, *,
               report: ValidationReport | None = None, asset_id: str | None = None,
               workspace: str | None = None, usage: JsonValue = None,
               result_id: str | None = None, consumed: list[str] | None = None) -> None:
        value: dict[str, JsonValue] = {
            "worker_id": self.worker_id, "swarm_id": self.config.swarm_id, "pid": os.getpid(),
            "signal_id": signal.signal_id, "task_id": signal.task_id,
            "attempt": _JSON.validate_python(attempt.model_dump(mode="json")), "outcome": outcome,
            "lease": _JSON.validate_python(lease.model_dump(mode="json")), "result_id": result_id,
            "asset_id": asset_id, "consumed_asset_ids": list[JsonValue](consumed or []),
            "validation_report_id": report.report_id if report else None,
            "policy_version": report.policy_version if report else None,
            "env_fingerprint": _JSON.validate_python(report.env_fingerprint.model_dump(mode="json"))
            if report else None, "execution_workspace": workspace,
            "validation_workspace": report.worktree_path if report else None,
            "usage": _JSON.validate_python(parsed.model_dump(mode="json"))
            if (parsed := _usage(usage)) is not None else None,
            "usage_source": self.executor.usage_source, "actual_cost_usd": None,
            "provenance": self.executor.provenance, "original_run_uri": self.executor.original_run_uri,
            "evidence_class": "contract_local", "created_at": time.time(),
            "interface_live": "not_run", "task_live": "not_run",
        }
        if outcome == "promoted":
            value["feedback_state"] = ("complete" if self._pending and self._pending.get("feedback_complete")
                                       else "incomplete")
        audit_key = result_id if outcome == "promoted" and result_id is not None else uuid4().hex
        path = self.state / "audit" / self.worker_id / (audit_key + ".json")
        no_links(path)
        if path.exists():
            previous = _JSON.validate_json(path.read_bytes())
            if not isinstance(previous, dict) or previous.get("result_id") != result_id:
                raise AssetSafetyError("audit_identity_conflict")
            return
        _write_json(path, value)

    def _finalize(self) -> None:
        """Resume accepted evidence only; never resubmit or reapply a task."""
        pending = self._pending
        if pending is None:
            return
        lease = Lease.model_validate(pending["lease"])
        task = self.ledger.get(lease.task_id)
        result_id = pending.get("result_id")
        if (task.status != "completed" or task.owner != self.worker_id or task.token != lease.token
                or task.result_id != result_id or not isinstance(result_id, str) or task.result is None
                or not task.effect_applied):
            raise AssetSafetyError("finalization_requires_completed_effect")
        asset_id, report_id = pending.get("asset_id"), pending.get("report_id")
        if (not isinstance(asset_id, str) or not isinstance(report_id, str)
                or task.result.get("candidate_asset_id") != asset_id or task.result.get("report_id") != report_id):
            raise AssetSafetyError("finalization_identity_mismatch")
        report = self.assets.get_report(report_id)
        if self.assets.state(asset_id) != "approved":
            AssetPromoter(self.assets, policy_version=report.policy_version).promote(asset_id, report_id)
        consumed = TypeAdapter(list[str]).validate_python(task.result.get("consumed_asset_ids", []))
        if consumed:
            execution_id = task.result.get("execution_id")
            if not isinstance(execution_id, str):
                raise AssetSafetyError("finalization_execution_missing")
            self.consumer.record_adoption(execution_id, result_id, self.ledger)
        if not pending.get("feedback_started"):
            pending["feedback_started"] = True
            self._status("finalizing")
            self.field.feedback(task.signal.signal_id, success=True)
            self.router.reinforce(self.worker_id, task.signal, success=True)
            pending["feedback_complete"] = True
            self._status("finalizing")
        # An interrupted feedback pair is explicitly incomplete, never replayed.
        if not pending.get("feedback_complete"):
            raise AssetSafetyError("feedback_incomplete_requires_review")
        workspace = pending.get("workspace")
        self._audit(task.signal, lease, report.attempt, "promoted", report=report, asset_id=asset_id,
                    workspace=workspace if isinstance(workspace, str) else None,
                    usage=pending.get("usage"), result_id=result_id, consumed=consumed)
        count = pending.get("completion_count")
        if not isinstance(count, int):
            raise AssetSafetyError("finalization_counter_invalid")
        self.completed = max(self.completed, count)
        self._pending = None
        self._status("active")

    def _reuse_ready(self, signal: Signal) -> bool:
        source_task = signal.payload.get("reuse_task_id")
        if source_task is None:
            return True
        task = self.ledger.get(signal.task_id)
        if not isinstance(source_task, str) or source_task not in task.dependencies:
            raise AssetSafetyError("reuse_requires_declared_dependency")
        source = self.ledger.get(source_task)
        asset_id = source.result.get("candidate_asset_id") if source.result else None
        return source.status == "completed" and isinstance(asset_id, str) and self.assets.state(asset_id) == "approved"

    def _consume(self, signal: Signal, lease: Lease, attempt: AttemptId, revision: str,
                 head: str, execution_id: str) -> ConsumptionExecution | None:
        source_task = signal.payload.get("reuse_task_id")
        if source_task is None:
            return None
        task = self.ledger.get(signal.task_id)
        if not isinstance(source_task, str) or source_task not in task.dependencies:
            raise AssetSafetyError("reuse_requires_declared_dependency")
        source = self.ledger.get(source_task)
        asset_id = source.result.get("candidate_asset_id") if source.result else None
        if source.status != "completed" or not isinstance(asset_id, str):
            raise AssetSafetyError("reuse_source_not_completed")
        context = ConsumptionContext(
            swarm_id=lease.swarm_id, task_id=signal.task_id, worker_id=self.worker_id, fencing_token=lease.token,
            execution_id=execution_id, scope=signal.scope,
            capabilities=tuple(key for key, value in self.config.capabilities.items() if value > 0),
            completed_dependencies=task.dependencies,
            input_context=json.dumps({"task_id": signal.task_id, "payload": signal.payload,
                                      "baseline": revision}, sort_keys=True, ensure_ascii=False),
        )
        injected = self.consumer.inject(asset_id, context)
        path_map = TypeAdapter(dict[str, str]).validate_python(signal.payload.get("path_map"))
        preimages = self._preimages(path_map, signal.scope)
        return self.consumer.execute(injected, attempt=attempt, base_revision=revision,
                                     base_head=head, path_map=path_map, preimages=preimages)

    def _preimages(self, path_map: dict[str, str], scope: str) -> dict[str, str | None]:
        root = self.target if scope == "." else safe_join(self.target, scope)
        paths: dict[str, Path] = {}
        for value in path_map.values():
            path = safe_join(self.target, value)
            if path != root and not path.is_relative_to(root):
                raise AssetSafetyError("reuse_destination_outside_scope")
            if path.is_dir() or (path.exists() and path.stat().st_size > 256 * 1024):
                raise AssetSafetyError("reuse_preimage_limit")
            paths[value] = path
        return {name: path.read_bytes().decode("utf-8") if path.is_file() else None
                for name, path in paths.items()}

    def _process(self, signal: Signal, lease: Lease) -> str:
        attempt = AttemptId(task_id=signal.task_id, agent=self.config.agent, attempt=lease.token - 1)
        keeper = _Renewal(self.leases, lease, self.config.lease_seconds)
        report: ValidationReport | None = None
        result: ExecutionResult | None = None
        consumption: ConsumptionExecution | None = None
        asset_id: str | None = None
        result_id: str | None = None
        outcome = "execution_unknown"
        usage: JsonValue = None
        try:
            keeper.start()
            # Acceptance comes from immutable operator-seeded task facts.
            policy = ValidationPolicy.model_validate(self.ledger.get(signal.task_id).acceptance.get("validation_policy"))
            bound = self.executor.bound(signal)
            if not bound.provider_enforced:
                raise BudgetBlocked("provider_bound_not_enforced")
            keeper.check()
            self._active = self.budget.reserve(self.worker_id, signal.task_id, bound,
                                              request_id=f"{signal.task_id}:{lease.token}")
            self._status("executing")
            try:
                keeper.check()
                revision, head = snapshot_revision(self.target, signal.scope, self.state / "snapshots")
                keeper.check()
                execution_id = uuid4().hex
                directory = self.state / "execution" / execution_id
                consumption = self._consume(signal, keeper.current, attempt, revision, head, execution_id)
                if consumption is None:
                    result = self.executor.execute(signal, attempt, self.target, directory,
                                                   base_revision=revision, base_head=head)
                else:
                    if type(self.executor) is not FixtureExecutor:
                        raise AssetSafetyError("reuse_executor_not_supported")
                    self.executor.materialize(consumption.candidate, self.target, directory)
                    result = ExecutionResult(consumption.candidate, _FIXTURE_USAGE, str(directory))
            except BaseException:
                self.budget.mark_uncertain(self._active)
                self._active = None
                raise
            usage = result.usage
            settled = self.budget.settle(self._active, usage)
            self._active = None
            self._status("settled")
            if (result.provenance != self.executor.provenance
                    or result.usage_source != self.executor.usage_source
                    or result.original_run_uri != self.executor.original_run_uri):
                raise AssetSafetyError("execution_provenance_mismatch")
            if settled.uncertain_reservations:
                outcome = "unknown_usage"
                return "sleeping"
            if settled.sleeping and settled.reason not in {
                "worker_burn_rate", "swarm_cost_estimate_exhausted",
            }:
                outcome = "budget_stopped"
                return "sleeping"
            keeper.check()
            if result.candidate is None:
                outcome = "execution_failed"
            else:
                candidate = result.candidate
                if candidate.attempt != attempt or candidate.scope != signal.scope:
                    raise AssetSafetyError("executor_identity_or_scope_mismatch")
                asset_id = self.assets.publish(candidate)
                report = AssetValidator(self.assets, self.target, policy=policy,
                                        timeout_seconds=self.config.validation_seconds).validate(asset_id)
                outcome = "quarantined"
            if report is None or not report.passed:
                lease = keeper.stop()
                self.ledger.fail(lease, {"outcome": outcome, "asset_id": asset_id})
                self.field.feedback(signal.signal_id, success=False)
                self.router.reinforce(self.worker_id, signal, success=False)
                return "failed"
            if asset_id is None:
                raise AssetSafetyError("missing_validated_asset")
            prepared = AssetApplicator(self.assets, self.target, policy_version=policy.version,
                                       protected_paths=(_SOURCE,)).prepare(asset_id, report.report_id)
            if Path(prepared.scope).resolve() != Path(lease.scope).resolve():
                raise AssetSafetyError("application_scope_mismatch")
            lease = keeper.stop()
            keeper.check()
            result_id = uuid4().hex
            result_data: dict[str, JsonValue] = {
                "candidate_asset_id": asset_id, "report_id": report.report_id, "applied": True,
                "execution_id": execution_id,
                "consumed_asset_ids": [consumption.asset_id] if consumption else [],
                "input_context": consumption.context.input_context if consumption else None,
                "worker_id": self.worker_id, "fencing_token": lease.token,
                "provenance": self.executor.provenance, "evidence_class": "contract_local",
                "policy_version": policy.version,
            }

            def apply(assert_owned: Callable[[], None]) -> None:
                prepared.apply(assert_owned)

            parsed_usage = _usage(usage)
            self._pending = {
                "lease": _JSON.validate_python(lease.model_dump(mode="json")), "result_id": result_id,
                "asset_id": asset_id, "report_id": report.report_id, "workspace": result.workspace,
                "completion_count": self.completed + 1, "feedback_started": False, "feedback_complete": False,
                "usage": {"usage": _JSON.validate_python(parsed_usage.model_dump(mode="json"))}
                if parsed_usage else None,
            }
            self._status("submitting")
            self.leases.submit(lease, result_id, result_data, apply=apply)
            self._finalize()
            outcome = "promoted"
            if self.mirror is not None:
                try:
                    self.mirror.enqueue(asset_id)
                except Exception:
                    pass
            return "completed"
        except BudgetBlocked as error:
            outcome = error.reason
            return "sleeping"
        except Exception:
            try:
                owned = self.leases.is_valid(keeper.current)
            except Exception:
                owned = False
            outcome = ("finalization_incomplete" if self._pending else
                       "stale_lease" if not owned else "execution_or_validation_failed")
            return "failed"
        finally:
            try:
                lease = keeper.stop()
                if self._active is not None:
                    self.budget.mark_uncertain(self._active)
                    self._active = None
                if outcome != "promoted":
                    self._audit(signal, lease, attempt, outcome, report=report, asset_id=asset_id,
                                workspace=result.workspace if result else None, usage=usage,
                                result_id=result_id, consumed=[consumption.asset_id] if consumption else [])
            finally:
                self.leases.release(keeper.current)

    def _backoff(self, count: int) -> None:
        upper = min(5.0, self.config.idle_seconds * 2 ** min(count, 8))
        time.sleep(self.rng.uniform(upper / 2, upper))

    def run(self) -> dict[str, JsonValue]:
        try:
            self._resume()
        except AssetSafetyError:
            return self._status("needs_review", "incomplete_accepted_evidence")
        idle = 0
        started = time.monotonic()
        while self.remaining > 0:
            if time.monotonic() - started >= self.config.budget.limits.max_runtime_seconds:
                return self._status("exhausted", "runtime_limit")
            state = self.budget.snapshot(self.worker_id)
            if state.sleeping:
                result = self._status("sleeping", state.reason or "budget")
                time.sleep(self.config.sleep_seconds)
                return result
            self.remaining -= 1
            self._status("sensing")
            signal = self.router.choose(self.worker_id, self.config.locality, self.config.capabilities)
            if signal is None:
                idle += 1
                result = self._status("idle", "no_local_signal")
                self._backoff(idle)
                if idle >= self.config.max_idle:
                    return result
                continue
            if not self._reuse_ready(signal):
                idle += 1
                result = self._status("waiting", "dependency_asset_not_approved")
                self._backoff(idle)
                if idle >= self.config.max_idle:
                    return result
                continue
            try:
                lease = self.leases.acquire(signal.task_id, self.worker_id, ttl_seconds=self.config.lease_seconds,
                                            locality=self.config.locality)
            except RunLimitReached:
                return self._status("exhausted", "shared_run_limit")
            if lease is None:
                idle += 1
                self._status("contended")
                self._backoff(idle)
                continue
            idle = 0
            outcome = self._process(signal, lease)
            if outcome == "sleeping":
                result = self._status("sleeping", "budget_or_uncertain_execution")
                time.sleep(self.config.sleep_seconds)
                return result
            if outcome == "failed":
                return self._status("stopped", "execution_or_validation_failed")
            self._status("active")
        return self._status("exhausted", "energy_limit")
