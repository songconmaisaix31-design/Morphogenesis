"""Offline renewal boundaries with real SQLite authority; no science execution."""

from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from local_assets.models import AssetSafetyError
from swarm.lease import LeaseManager
from swarm.models import Locality, Signal
from swarm.task_ledger import LeaseLost, TaskLedger
from swarm.worker_loop import _Renewal
import swarm.worker_loop as worker_loop


@pytest.mark.parametrize("completion_delay", [1.5, 2.5])
def test_transaction_completion_delay_does_not_add_a_fresh_sleep(tmp_path, monkeypatch, completion_delay):
    """A committed expiry ages during transaction exit, before renew returns.

    Virtual time fixes the IO boundary without relying on OS load. The real
    SQLite ledger still owns all expiry, owner, token and submission decisions.
    A delay beyond TTL must fail closed; a live returned lease must keep renewing.
    """
    clock = [100.0]
    ledger = TaskLedger(tmp_path / "tasks.db", "renewal-boundary", clock=lambda: clock[0])
    ledger.enqueue(Signal(task_id="task", workspace=str(tmp_path), scope="src", kind="opportunity"))
    manager = LeaseManager(ledger)
    lease = manager.acquire("task", "owner", ttl_seconds=2,
                            locality=Locality(workspace=str(tmp_path), authorized_scopes=("src",)))
    assert lease is not None
    keeper = _Renewal(manager, lease, 2)
    transaction = ledger.transaction

    @contextmanager
    def delayed_completion():
        with transaction() as db:
            yield db
        # After durable commit/close, before returning the renewed Lease.
        clock[0] += completion_delay

    monkeypatch.setattr(ledger, "transaction", delayed_completion)
    monkeypatch.setattr(worker_loop, "time", SimpleNamespace(monotonic=lambda: clock[0], time=lambda: clock[0]))

    class ScheduledStop:
        waits = 0

        def set(self):
            pass

        def wait(self, seconds):
            self.waits += 1
            if self.waits > 3:
                return True
            clock[0] += seconds
            return False

    monkeypatch.setattr(keeper, "stop_event", ScheduledStop())
    keeper._run()
    audit = ledger.audit()
    renewals = [event for event in reversed(audit) if event["event"] == "renewed"]
    if completion_delay < 2:
        assert not keeper.failed, {"diagnostics": keeper.diagnostics(), "audit": audit}
        assert keeper.renewals == len(renewals) == 3
        assert manager.is_valid(keeper.current)
        assert ledger.get("task").token == lease.token
        assert ledger.get("task").owner == lease.worker_id
        expiries = [event["body"]["expires_at"] for event in renewals]
        assert all(after > before for before, after in zip(expiries, expiries[1:]))
    else:
        assert keeper.failed and keeper.last_failure == {"failure_reason": "renewal_rejected"}
        assert not manager.is_valid(keeper.current)
        with pytest.raises(AssetSafetyError, match="stale_lease"):
            keeper.handoff()
        with pytest.raises(LeaseLost):
            manager.submit(keeper.current, "late", {}, apply=lambda _: pytest.fail("expired effect"))
        assert not ledger.get("task").effect_applied


def test_renewal_io_error_stays_failed_and_handoff_does_not_retry(tmp_path, monkeypatch):
    ledger = TaskLedger(tmp_path / "tasks.db", "renewal-error")
    ledger.enqueue(Signal(task_id="task", workspace=str(tmp_path), scope="src", kind="opportunity"))
    manager = LeaseManager(ledger)
    lease = manager.acquire("task", "owner", ttl_seconds=2,
                            locality=Locality(workspace=str(tmp_path), authorized_scopes=("src",)))
    assert lease is not None
    keeper = _Renewal(manager, lease, 2)
    calls = []

    def failed_renew(*args, **kwargs):
        calls.append(1)
        raise OSError(5, "private diagnostic must not enter evidence")

    monkeypatch.setattr(manager, "renew", failed_renew)
    keeper._renew_locked()
    with pytest.raises(AssetSafetyError, match="stale_lease"):
        keeper.handoff()
    assert calls == [1] and keeper.failed
    assert keeper.last_failure == {"failure_kind": "OSError", "failure_reason": "os_error", "os_errno": 5}
    assert keeper.current == lease
    assert not ledger.get("task").effect_applied
