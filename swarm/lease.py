"""Task-scoped SQLite lease facade; no JSON/file-lock authority."""
from pydantic import JsonValue
from swarm.models import Lease, Locality, TaskRecord
from swarm.task_ledger import Apply, LeaseLost, TaskLedger, canonical_scope, scopes_collide

__all__ = ["LeaseManager", "LeaseLost", "canonical_scope", "scopes_collide"]


class LeaseManager:
    def __init__(self, ledger: TaskLedger) -> None:
        self.ledger = ledger

    def acquire(self, task_id: str, worker_id: str, *, ttl_seconds: float = 30, locality: Locality) -> Lease | None:
        return self.ledger.claim(task_id, worker_id, ttl_seconds=ttl_seconds, locality=locality)

    def renew(self, lease: Lease, *, ttl_seconds: float = 30) -> Lease | None:
        return self.ledger.renew(lease, ttl_seconds=ttl_seconds)

    def release(self, lease: Lease) -> bool:
        return self.ledger.release(lease)

    def is_valid(self, lease: Lease) -> bool:
        return self.ledger.is_valid(lease)

    def submit(self, lease: Lease, result_id: str, result: dict[str, JsonValue], *, apply: Apply | None = None) -> TaskRecord:
        return self.ledger.submit(lease, result_id, result, apply=apply)

    def snapshot(self) -> list[Lease]:
        return self.ledger.leases()
