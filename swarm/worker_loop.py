"""Independent local forager. Environment signals are its only task source."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
import json
import os
from pathlib import Path
import random
import time
from typing import Literal, Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, JsonValue, TypeAdapter

from contracts.identity import AgentId, AttemptId
from contracts.provenance import Acceptance, Provenance
from local_assets.models import AssetSafetyError, Candidate, FileChange, ValidationReport
from local_assets.paths import FROZEN_MAINLINE, check_target, git, no_links, relative_path, safe_join
from local_assets.promote import AssetPromoter
from local_assets.store import LocalAssetStore
from local_assets.snapshot import snapshot_revision
from local_assets.validate import AssetValidator, blast_radius, inspect_candidate
from orchestration.gateway import _usage
from swarm.budget import BudgetBlocked, BudgetLedger
from swarm.hub_mirror import HubMirror
from swarm.lease import LeaseManager
from swarm.models import BudgetPolicy, ExecutionBound, Lease, Locality, Reservation, Signal
from swarm.pheromone import PheromoneField
from swarm.router import Router

_JSON: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)
_CHANGES = TypeAdapter(tuple[FileChange, ...])
_SOURCE = Path(__file__).resolve().parents[1]


class WorkerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)
    state: Path
    target: Path
    agent: AgentId
    locality: Locality
    budget: BudgetPolicy
    account_id: str = "local-fixture"
    capabilities: dict[str, float] = Field(default_factory=lambda: {"repair": 1.0})
    energy: int = Field(default=20, ge=1, le=10000)
    max_idle: int = Field(default=3, ge=1, le=100)
    idle_seconds: float = Field(default=0.05, gt=0, le=60)
    sleep_seconds: float = Field(default=0.05, gt=0, le=60)
    lease_seconds: float = Field(default=300, gt=0, le=3600)
    validation_seconds: float = Field(default=15, gt=0, le=300)
    commands: tuple[tuple[str, ...], ...] = Field(min_length=1, max_length=16)
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
    """Trusted bounded adapters only. CLI exposes only the offline fixture one."""

    provenance: Provenance
    usage_source: Literal["fixture_mock", "provider_reported", "replay"]
    original_run_uri: str | None

    def bound(self, signal: Signal) -> ExecutionBound: ...

    def execute(self, signal: Signal, attempt: AttemptId, repository: Path,
                directory: Path, *, base_revision: str, base_head: str) -> ExecutionResult: ...


class FixtureExecutor:
    """Apply supplied fixture changes in a real detached worktree; no model call.

    Token counts are explicitly synthetic test units. Enforced bounds concern
    this local fixture operation, never an upstream provider's billing contract.
    """

    provenance: Provenance = "mock"
    usage_source: Literal["fixture_mock", "provider_reported", "replay"] = "fixture_mock"
    original_run_uri: str | None = None

    def bound(self, signal: Signal) -> ExecutionBound:
        changes = _CHANGES.validate_python(signal.payload.get("changes"))
        if not 1 <= len(changes) <= 16 or len(json.dumps(signal.payload)) > 64 * 1024:
            raise ValueError("fixture_input_bound")
        return ExecutionBound(provider="local", model="fixture", input_tokens=1,
                              max_output_tokens=1, provider_enforced=True)

    def execute(self, signal: Signal, attempt: AttemptId, repository: Path,
                directory: Path, *, base_revision: str, base_head: str) -> ExecutionResult:
        self.bound(signal)
        changes = _CHANGES.validate_python(signal.payload.get("changes"))
        candidate = Candidate(attempt=attempt, base_revision=base_revision, base_head=base_head,
                              changes=changes, declared_files=len(changes), declared_lines=0,
                              scope=signal.scope)
        count, lines = blast_radius(candidate)
        candidate = candidate.model_copy(update={"declared_files": count, "declared_lines": lines})
        inspect_candidate(candidate)
        # Reject source-tree links before even checking them out.
        tree = git(repository, "ls-tree", "-rz", candidate.base_revision)
        if any(item.startswith((b"120000 ", b"160000 ")) for item in tree.split(b"\0")):
            raise AssetSafetyError("baseline_links_or_submodules")
        no_links(directory)
        directory.parent.mkdir(parents=True, exist_ok=True)
        git(repository, "worktree", "add", "--detach", str(directory), candidate.base_revision)
        for change in changes:
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
        return ExecutionResult(candidate, {"usage": {"prompt_tokens": 1,
                               "completion_tokens": 1, "total_tokens": 2}}, str(directory))


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
        self.field = PheromoneField(self.state / "field.sqlite3")
        self.router = Router(self.field, rng=random.Random(config.seed))
        self.leases = LeaseManager(self.state / "leases", lock_timeout_seconds=30)
        self.budget = BudgetLedger(self.state / "budget.sqlite3", config.account_id, config.budget)
        self.assets = LocalAssetStore(self.state / "assets")
        self.promoter = AssetPromoter(self.assets, self.target, protected_paths=(_SOURCE,))
        self.status_path = self.state / "workers" / (self.worker_id + ".json")
        self.remaining = config.energy
        self.completed = 0
        self._active: Reservation | None = None

    def _status(self, state: str, reason: str = "") -> dict[str, JsonValue]:
        result: dict[str, JsonValue] = {
            "worker_id": self.worker_id, "pid": os.getpid(), "state": state, "reason": reason,
            "remaining_energy": self.remaining, "completed": self.completed,
            "updated_at": time.time(), "provenance": self.executor.provenance,
            "evidence_class": "contract_local", "usage_source": self.executor.usage_source,
            "active_reservation": _JSON.validate_python(self._active.model_dump(mode="json"))
            if self._active is not None else None,
        }
        _write_json(self.status_path, result)
        return result

    def _resume(self) -> None:
        no_links(self.status_path)
        if not self.status_path.exists():
            return
        previous = _JSON.validate_json(self.status_path.read_bytes())
        if not isinstance(previous, dict) or previous.get("worker_id") != self.worker_id:
            raise ValueError("invalid_worker_state")
        remaining, completed = previous.get("remaining_energy"), previous.get("completed")
        if not isinstance(remaining, int) or not isinstance(completed, int):
            raise ValueError("invalid_worker_counters")
        self.remaining, self.completed = min(self.remaining, remaining), completed
        active = previous.get("active_reservation")
        if active is not None:
            self.budget.mark_uncertain(Reservation.model_validate(active))

    def _audit(self, signal: Signal, lease: Lease, attempt: AttemptId, outcome: str, *,
               report: ValidationReport | None = None, asset_id: str | None = None,
               workspace: str | None = None, usage: JsonValue = None) -> None:
        value: dict[str, JsonValue] = {
            "worker_id": self.worker_id, "pid": os.getpid(), "signal_id": signal.signal_id,
            "attempt": _JSON.validate_python(attempt.model_dump(mode="json")), "outcome": outcome,
            "lease": _JSON.validate_python(lease.model_dump(mode="json")),
            "asset_id": asset_id, "validation_report_id": report.report_id if report else None,
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
        _write_json(self.state / "audit" / self.worker_id / (uuid4().hex + ".json"), value)

    def _process(self, signal: Signal, lease: Lease) -> str:
        attempt = AttemptId(task_id=signal.task_id, agent=self.config.agent, attempt=0)
        report: ValidationReport | None = None
        result: ExecutionResult | None = None
        asset_id: str | None = None
        outcome = "execution_unknown"
        usage: JsonValue = None
        try:
            bound = self.executor.bound(signal)
            self._active = self.budget.reserve(self.worker_id, signal.task_id, bound)
            self._status("executing")
            try:
                with self.leases.guard(lease) as assert_owned:
                    assert_owned()
                    revision, head = snapshot_revision(self.target, signal.scope,
                                                       self.state / "snapshots")
                    assert_owned()
                result = self.executor.execute(signal, attempt, self.target,
                    self.state / "execution" / uuid4().hex, base_revision=revision, base_head=head)
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
            if settled.sleeping and settled.reason != "worker_burn_rate":
                outcome = "budget_stopped"
                return "sleeping"
            if result.candidate is None:
                outcome = "execution_failed"
                with self.leases.guard(lease) as assert_owned:
                    assert_owned()
                    self.field.feedback(signal.signal_id, success=False)
                    self.router.reinforce(self.worker_id, signal, success=False)
                    self.field.complete(signal.signal_id)
                return "failed"
            candidate = result.candidate
            if candidate.attempt != attempt or candidate.scope != signal.scope:
                raise AssetSafetyError("executor_identity_or_scope_mismatch")
            asset_id = self.assets.publish(candidate)
            commands = tuple(tuple(arg.replace("{scope}", signal.scope) for arg in command)
                             for command in self.config.commands)
            report = AssetValidator(self.assets, self.target, commands=commands,
                                    timeout_seconds=self.config.validation_seconds).validate(asset_id)
            with self.leases.guard(lease) as assert_owned:
                assert_owned()

                @contextmanager
                def guarded_scope(scope: str) -> Iterator[Callable[[], None]]:
                    if Path(scope).resolve() != Path(lease.scope).resolve():
                        raise AssetSafetyError("promotion_lease_scope_mismatch")
                    assert_owned()
                    yield assert_owned
                    assert_owned()

                if report.passed:
                    self.promoter.promote(asset_id, report.report_id, guarded_scope)
                    assert_owned()
                    outcome = "promoted"
                    self.completed += 1
                else:
                    outcome = "quarantined"
                assert_owned()
                self.field.feedback(signal.signal_id, success=report.passed)
                self.router.reinforce(self.worker_id, signal, success=report.passed)
                self.field.complete(signal.signal_id)
                assert_owned()
                self._audit(signal, lease, attempt, outcome, report=report, asset_id=asset_id,
                            workspace=result.workspace, usage=usage)
                if report.passed and self.mirror is not None:
                    try:
                        self.mirror.enqueue(asset_id)
                    except Exception:
                        pass  # Optional transport never changes a local result.
                return "completed" if report.passed else "failed"
        except BudgetBlocked as error:
            outcome = error.reason
            return "sleeping"
        except Exception:
            try:
                owned = self.leases.is_valid(lease)
            except TimeoutError:
                owned = False
            outcome = "stale_lease" if not owned else "execution_or_validation_failed"
            return "failed"
        finally:
            try:
                if self._active is not None:
                    self.budget.mark_uncertain(self._active)
                    self._active = None
                if outcome not in {"promoted", "quarantined"}:
                    self._audit(signal, lease, attempt, outcome, report=report, asset_id=asset_id,
                                workspace=result.workspace if result else None, usage=usage)
            finally:
                try:
                    self.leases.release(lease)
                except TimeoutError:
                    pass  # Fail closed: the durable lease remains fenced until TTL.

    def run(self) -> dict[str, JsonValue]:
        # One OS-held worker identity lock prevents two copies restoring one
        # energy counter. It is not a scheduler and never allocates work.
        try:
            identity = self.leases.acquire(str(self.state / "workers" / self.worker_id), self.worker_id,
                                           ttl_seconds=self.config.lease_seconds)
        except TimeoutError:
            time.sleep(self.config.sleep_seconds)
            # Identity was not obtained: do not overwrite another copy's status.
            return {"worker_id": self.worker_id, "state": "sleeping", "reason": "lease_metadata_busy"}
        if identity is None:
            return {"worker_id": self.worker_id, "state": "identity_busy"}
        try:
            self._resume()
            idle = 0
            while self.remaining > 0:
                renewed = self.leases.renew(identity, ttl_seconds=self.config.lease_seconds)
                if renewed is None:
                    return self._status("sleeping", "worker_identity_lease_expired")
                identity = renewed
                self.remaining -= 1
                state = self.budget.snapshot(self.worker_id)
                if state.sleeping:
                    result = self._status("sleeping", state.reason or "budget")
                    time.sleep(self.config.sleep_seconds)
                    return result
                signal = self.router.choose(self.worker_id, self.config.locality, self.config.capabilities)
                if signal is None:
                    idle += 1
                    result = self._status("idle", "no_local_signal")
                    time.sleep(self.config.idle_seconds)
                    if idle >= self.config.max_idle:
                        return result
                    continue
                scope = self.target if signal.scope == "." else safe_join(self.target, relative_path(signal.scope))
                lease = self.leases.acquire(str(scope), self.worker_id, ttl_seconds=self.config.lease_seconds)
                if lease is None:
                    self._status("contended")
                    time.sleep(self.config.idle_seconds)
                    continue
                try:
                    still_present = any(item.signal_id == signal.signal_id
                                        for item in self.field.sense(self.config.locality))
                except BaseException:
                    self.leases.release(lease)
                    raise
                if not still_present:
                    self.leases.release(lease)
                    self._status("contended", "signal_already_retired")
                    time.sleep(self.config.idle_seconds)
                    continue
                idle = 0
                outcome = self._process(signal, lease)
                if outcome == "sleeping":
                    result = self._status("sleeping", "budget_or_uncertain_execution")
                    time.sleep(self.config.sleep_seconds)
                    return result
                self._status("active")
                if outcome == "failed":
                    time.sleep(self.config.idle_seconds)
            return self._status("exhausted", "energy_limit")
        except TimeoutError:
            result = self._status("sleeping", "lease_metadata_busy")
            time.sleep(self.config.sleep_seconds)
            return result
        finally:
            try:
                self.leases.release(identity)
            except TimeoutError:
                pass
