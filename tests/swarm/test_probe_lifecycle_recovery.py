"""Real Worker routing, persistent evidence, and probe recovery regressions.

Only executor responses are mocked; local fixture usage is explicit test data.
No assertions live inside Worker exception handlers or executor callbacks.
"""
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from threading import Event
from pathlib import Path
import subprocess
import sys

import pytest
import time_machine

from swarm.breaker import BreakerConfig, SharedBreaker
from swarm.worker_loop import FixtureExecutor, Worker
from tests.swarm.test_failure_chain_runtime import (
    _assert_calls, _claim, _events, _executor, _facts, _failure, _reservations,
    _worker_config,
)


def config():
    return BreakerConfig(window_seconds=600.0, aggregation_period_seconds=1.0,
                         failure_threshold=2, min_samples=2, cooldown_seconds=2.0,
                         probe_ttl_seconds=3.0)


def worker(settings, executor, instance=0):
    settings = settings.model_copy(update={
        "agent": settings.agent.model_copy(update={"instance": instance}),
        "locality": settings.locality.model_copy(update={
            "authorized_scopes": ("module_0", "module_1", "module_2"),
            "modules": ("module_0", "module_1", "module_2"),
        }),
    })
    return Worker(settings, executor, breaker_config=config())


def process(subject, task_id):
    signal, lease = _claim(subject, task_id)
    return subject._process(signal, lease), signal, lease


def suspend(settings, *, reason="billing_arrearage"):
    executor = _executor("alpha", result=_failure(reason=reason))
    subject = worker(settings, executor)
    outcome, signal, lease = process(subject, "fixture-0")
    assert outcome == "rejected", _events(subject)
    _assert_calls(executor, signal, lease)
    subject.shared_breaker.observe(subject.fault_observation_store)
    return subject


@pytest.mark.parametrize("same_owner", [False, True])
def test_expired_probe_is_reclaimed_through_worker_guard(tmp_path, same_owner):
    with time_machine.travel(1800000000.0, tick=False) as clock:
        settings = _worker_config(tmp_path)
        old = suspend(settings)
        clock.shift(2)
        owner = old.worker_id if same_owner else "lost-worker"
        stale = old.shared_breaker.try_claim_probe("alpha", "billing_arrearage", owner)
        assert stale is not None
        clock.shift(3)  # Exact TTL boundary must admit a new fenced probe.
        captured = []
        fixture = FixtureExecutor()
        fresh = worker(settings, _executor("alpha"), instance=0 if same_owner else 1)

        def execute(*args, **kwargs):
            captured.append(fresh.shared_breaker.view("alpha", "billing_arrearage"))
            captured.append(old.shared_breaker.report_probe_success(
                "alpha", "billing_arrearage", owner, probe_token=stale.probe_token))
            captured.append(old.shared_breaker.report_probe_failure(
                "alpha", "billing_arrearage", owner, probe_token=stale.probe_token))
            captured.append(fresh.shared_breaker.view("alpha", "billing_arrearage"))
            return fixture.execute(*args, **kwargs)

        fresh.executor.execute.side_effect = execute
        outcome, signal, lease = process(fresh, "fixture-2")

    _assert_calls(fresh.executor, signal, lease)
    assert outcome == "completed", _events(fresh)
    before, stale_success, stale_failure, after = captured
    assert before == after
    assert before.probe_owner == fresh.worker_id and before.probe_token == stale.probe_token + 1
    assert stale_success is stale_failure is False
    assert fresh.shared_breaker.view("alpha", "billing_arrearage").state == "normal"


def test_expired_probe_race_admits_one_real_executor(tmp_path):
    with time_machine.travel(1800000000.0, tick=False) as clock:
        settings = _worker_config(tmp_path)
        old = suspend(settings)
        clock.shift(2)
        stale = old.shared_breaker.try_claim_probe("alpha", "billing_arrearage", "lost")
        assert stale is not None
        clock.shift(3)
        release = Event()
        entered = Event()
        seen = []
        subjects = [worker(settings, _executor("alpha"), i + 1) for i in range(2)]

        def execute(*args, **kwargs):
            seen.append(old.shared_breaker.view("alpha", "billing_arrearage"))
            entered.set()
            release.wait(30)
            return _failure(reason="rate_limited")

        for subject in subjects:
            subject.executor.execute.side_effect = execute
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(process, subject, f"fixture-{2 + i * 2}")
                       for i, subject in enumerate(subjects)]
            try:
                finished, _ = wait(futures, timeout=20, return_when=FIRST_COMPLETED)
                executor_entered = entered.wait(15)
                calls_while_held = [s.executor.execute.call_count for s in subjects]
            finally:
                release.set()
            outcomes = [future.result(timeout=30) for future in futures]

    assert len(finished) >= 1
    assert executor_entered
    assert sorted(calls_while_held) == [0, 1]
    assert sorted(s.executor.execute.call_count for s in subjects) == [0, 1]
    assert sorted(result[0] for result in outcomes) == ["rejected", "sleeping"]
    assert len(seen) == 1 and seen[0].probe_token == stale.probe_token + 1
    assert len(_reservations(subjects[0])) == 2  # Initial failure plus exactly one probe.


def test_worker_cannot_reclaim_live_probe_before_ttl(tmp_path):
    with time_machine.travel(1800000000.0, tick=False) as clock:
        settings = _worker_config(tmp_path)
        old = suspend(settings)
        clock.shift(2)
        held = old.shared_breaker.try_claim_probe("alpha", "billing_arrearage", "live-owner")
        clock.shift(2.999)
        contender = worker(settings, _executor("alpha"), instance=1)
        before = _reservations(contender)
        outcome, signal, lease = process(contender, "fixture-2")
        after = contender.shared_breaker.view("alpha", "billing_arrearage")
    _assert_calls(contender.executor, signal, lease, expected=0)
    assert outcome == "sleeping", _events(contender)
    assert _reservations(contender) == before and after == held


@pytest.mark.parametrize("observer", ["same_worker", "other_worker", "restart"])
def test_recovered_history_cannot_resuspend_but_new_failures_can(tmp_path, observer):
    with time_machine.travel(1800000000.0, tick=False) as clock:
        settings = _worker_config(tmp_path, prices=True, max_cost=4.0)
        settings = settings.model_copy(update={"budget": settings.budget.model_copy(update={
            "prices": settings.budget.prices.model_copy(update={"provider": "alpha"}),
        })})
        reject = _executor("alpha", result=_failure(reason="rate_limited"))
        initial = worker(settings, reject)
        for number in (0, 1):
            outcome, _, _ = process(initial, f"fixture-{number}")
            assert outcome == "rejected", _events(initial)
        assert reject.execute.call_count == 2
        initial.shared_breaker.observe(initial.fault_observation_store)
        assert initial.shared_breaker.view("alpha", "rate_limited").state == "suspended"
        old_bytes = initial.fault_observation_store.path.read_bytes()
        # Populate an independent process-like cache before the successful probe.
        peer = worker(settings, _executor("alpha"), instance=1)
        peer.shared_breaker.observe(peer.fault_observation_store)
        clock.shift(2)
        recovered = worker(settings, _executor("alpha"))
        outcome, signal, lease = process(recovered, "fixture-2")
        assert outcome == "completed", _events(recovered)
        _assert_calls(recovered.executor, signal, lease)
        if observer == "same_worker":
            reader = recovered
        elif observer == "other_worker":
            reader = peer
        else:
            # A new OS process reads the same persisted boundary and full JSONL.
            script = """
import sys
from swarm.breaker import BreakerConfig, SharedBreaker
from swarm.fault_observations import FaultObservationStore
breaker = SharedBreaker(sys.argv[1], 'local-fixture', BreakerConfig.model_validate_json(sys.argv[3]))
breaker.observe(FaultObservationStore(sys.argv[2], 'local-fixture'), now=1800000002.0)
print(breaker.view('alpha', 'rate_limited').state)
"""
            restarted = subprocess.run([
                sys.executable, "-c", script, str(recovered.shared_breaker.path),
                str(recovered.fault_observation_store.path), config().model_dump_json(),
            ], cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, timeout=30)
            assert restarted.returncode == 0, restarted.stderr
            assert restarted.stdout.strip() == "normal"
            reader = worker(settings, _executor("alpha"), instance=2)
        reader.shared_breaker.observe(reader.fault_observation_store)
        assert reader.fault_observation_store.path.read_bytes() == old_bytes
        assert len(_facts(reader)) == 2
        # Same timestamp as recovery: append order distinguishes new failures.
        fresh = _executor("alpha", result=_failure(reason="rate_limited"))
        reader.executor = fresh
        reader._candidates = (fresh,)
        for number in (3, 4):
            outcome, _, _ = process(reader, f"fixture-{number}")
            assert fresh.execute.call_count == number - 2
            assert outcome == "rejected", _events(reader)
            assert reader.shared_breaker.view("alpha", "rate_limited").state == "normal"
        assert fresh.execute.call_count == 2
        outcome, signal, lease = process(reader, "fixture-5")
        assert fresh.execute.call_count == 2
        assert outcome == "sleeping", _events(reader)
        assert reader.shared_breaker.view("alpha", "rate_limited").state == "suspended"
        assert len(_facts(reader)) == 4
        assert reader.fault_observation_store.path.read_bytes().startswith(old_bytes)
