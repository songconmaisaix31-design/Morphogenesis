"""Renewal timing boundaries with real SQLite fencing and no remote execution."""

from contextlib import contextmanager
from threading import Event
import time
from types import SimpleNamespace

import pytest

from local_assets.models import AssetSafetyError
from swarm.lease import LeaseManager
from swarm.models import Locality, Signal
from swarm.task_ledger import LeaseLost, TaskLedger
from swarm.worker_loop import _Renewal
import swarm.worker_loop as worker_loop


def claimed(tmp_path, **kwargs):
    ledger = TaskLedger(tmp_path / "tasks.db", "renewal-boundary", **kwargs)
    ledger.enqueue(Signal(task_id="task", workspace=str(tmp_path), scope="src", kind="opportunity"))
    manager = LeaseManager(ledger)
    lease = manager.acquire("task", "owner", ttl_seconds=2,
                            locality=Locality(workspace=str(tmp_path), authorized_scopes=("src",)))
    assert lease is not None
    return ledger, manager, lease


@pytest.mark.parametrize("completion_delay", [0.1, 1.5, 2.5])
def test_transaction_completion_delay_preserves_live_renewal_only(tmp_path, monkeypatch, completion_delay):
    """A committed expiry ages before renew returns; TTL and fencing still apply.

    Controlled time isolates transaction completion from OS scheduling. SQLite
    remains the authority for renewal, expiry, owner, token and publication.
    """
    clock = [100.0]
    ledger, manager, lease = claimed(tmp_path, clock=lambda: clock[0])
    keeper = _Renewal(manager, lease, 2)
    transaction = ledger.transaction

    @contextmanager
    def delayed_completion():
        with transaction() as db:
            yield db
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
    monkeypatch.setattr(ledger, "transaction", transaction)
    if completion_delay < 2:
        assert not keeper.failed, keeper.diagnostics()
        assert keeper.renewals == 3
        assert manager.is_valid(keeper.current)
        assert ledger.get("task").token == lease.token
        assert ledger.get("task").owner == lease.worker_id
        final = keeper.handoff()
        writes = []

        def apply(check):
            check()
            writes.append("owned")

        assert manager.submit(final, "result", {}, apply=apply).effect_applied
        assert writes == ["owned"]
    else:
        assert keeper.failed and keeper.last_failure == {"failure_reason": "renewal_rejected"}
        assert not manager.is_valid(keeper.current)
        with pytest.raises(AssetSafetyError, match="stale_lease"):
            keeper.handoff()
        with pytest.raises(LeaseLost):
            manager.submit(keeper.current, "late", {}, apply=lambda _: pytest.fail("expired effect"))
        assert not ledger.get("task").effect_applied


def test_wall_clock_slow_renewal_returns_before_expiry_and_keeps_ownership(tmp_path, monkeypatch):
    ledger, manager, lease = claimed(tmp_path)
    keeper = _Renewal(manager, lease, 2)
    original = manager.renew
    renewed = []
    second_renewal = Event()

    def delayed(lease, **kwargs):
        result = original(lease, **kwargs)
        if result is not None:
            renewed.append(result)
            if len(renewed) == 1:
                time.sleep(1.5)  # Durable expiry ages before the caller resumes.
            else:
                second_renewal.set()
        return result

    monkeypatch.setattr(manager, "renew", delayed)
    keeper.start()
    try:
        observed = second_renewal.wait(6)
    finally:
        keeper.stop()
    assert observed and not keeper.failed, keeper.diagnostics()
    assert len(renewed) >= 2
    assert all(item.token == lease.token for item in renewed)
    assert all(after.expires_at > before.expires_at for before, after in zip(renewed, renewed[1:]))
    final = keeper.handoff()
    assert manager.submit(final, "result", {}).status == "completed"
    assert not ledger.get("task").effect_applied


def test_renewal_io_error_stays_failed_and_handoff_does_not_retry(tmp_path, monkeypatch):
    ledger, manager, lease = claimed(tmp_path)
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
