"""Offline transport fixtures only; no live provider or benchmark evidence."""

import asyncio
from dataclasses import replace
import json
import multiprocessing
import pickle

import httpx
import pytest

from swarm.benchmark_model import (
    MAX_REQUESTS,
    ModelRequest,
    STEPFUN_MODEL,
    STEPFUN_URL,
    SYSTEM_PROMPT,
    SharedRequestGate,
    StepFunBenchmarkExecutor,
    request_payload,
    validate_transport_configuration,
)

CANARY = "not-a-real-credential-fixture-0123"


def request(**changes):
    return replace(ModelRequest(run_id="run", framework="morphogenesis", block_id="block-1",
        seed=42, task_id="gsm8k-1", prompt="What is one plus one?", max_tokens=4096,
        temperature=0.0), **changes)


def gate(concurrency=2, max_requests=10):
    return SharedRequestGate.create(multiprocessing.get_context("spawn"), concurrency=concurrency,
                                    max_requests=max_requests)


def body(text="#### 2", usage=True):
    result = {"id": "request-id", "model": STEPFUN_MODEL,
              "choices": [{"message": {"role": "assistant", "content": text}, "finish_reason": "stop"}]}
    if usage:
        result["usage"] = {"prompt_tokens": 12, "completion_tokens": 3, "total_tokens": 15}
    return result


def executor(handler, shared=None, **kwargs):
    return StepFunBenchmarkExecutor(CANARY, shared or gate(), transport=httpx.MockTransport(handler),
                                   provenance="mock", **kwargs)


def _reserve_in_spawned_child(shared, started, release):
    shared.semaphore.acquire()
    try:
        with shared.lock:
            shared.reserved.value += 1
            shared.active.value += 1
            shared.peak.value = max(shared.peak.value, shared.active.value)
        started.send(True)
        release.recv()
    finally:
        with shared.lock:
            shared.active.value -= 1
        shared.semaphore.release()


def test_one_identical_payload_for_all_frameworks_and_no_gold_or_metadata():
    original = request_payload(request())
    for framework in ("autogen", "langgraph"):
        assert request_payload(request(framework=framework, block_id="other")) == original
    assert original["messages"][0] == {"role": "system", "content": SYSTEM_PROMPT}
    assert original["model"] == STEPFUN_MODEL and original["stream"] is False
    assert original["max_tokens"] == 4096
    assert "tools" not in original and "seed" not in original
    assert "framework" not in json.dumps(original) and "gold" not in json.dumps(original)


@pytest.mark.parametrize("changes", [{"attempt": 2}, {"max_tokens": 4097}, {"max_tokens": True},
    {"temperature": float("nan")}, {"seed": -1}, {"task_id": "with space"}, {"prompt": ""}])
def test_invalid_request_configuration_refused(changes):
    with pytest.raises(ValueError):
        request(**changes)


def test_gate_bounds_and_transport_provenance_fail_closed():
    for concurrency, limit in ((0, 1), (6, 1), (1, 0), (1, MAX_REQUESTS + 1)):
        with pytest.raises(ValueError):
            gate(concurrency, limit)
    with pytest.raises(ValueError, match="provenance"):
        StepFunBenchmarkExecutor(CANARY, gate(), transport=httpx.MockTransport(lambda _: None))
    with pytest.raises(ValueError, match="provenance"):
        StepFunBenchmarkExecutor(CANARY, gate(), provenance="mock")


def test_success_records_real_transport_boundary_and_unknown_usage_as_null():
    calls = []

    def handler(incoming):
        calls.append(incoming)
        assert str(incoming.url) == STEPFUN_URL
        assert incoming.headers["authorization"] == "Bearer " + CANARY
        return httpx.Response(200, json=body(usage=False))

    model = executor(handler)
    result = model.generate_sync(request())
    assert result.status == "completed" and result.text == "#### 2" and result.usage is None
    assert len(calls) == 1 and result.request_id == "request-id"
    evidence = result.evidence
    assert evidence["provenance"] == "mock" and evidence["retry_count"] == 0
    assert evidence["queued_at_ns"] <= evidence["permit_acquired_at_ns"] <= evidence["http_entered_at_ns"]
    assert evidence["http_entered_at_ns"] <= evidence["response_headers_at_ns"] <= evidence["http_returned_at_ns"] <= evidence["ended_at_ns"]
    assert evidence["first_stream_delta_at_ns"] is None and evidence["billing_cost"] is None
    assert "http_active_not_model_or_gpu" in evidence["interval_scope"]
    assert CANARY not in repr(model) + repr(result)
    with pytest.raises(TypeError, match="must_not_be_serialized"):
        pickle.dumps(model)


def test_account_gate_bounds_concurrent_fixture_requests_without_hidden_retries():
    async def scenario():
        shared = gate(3, 8)
        release = asyncio.Event()
        active, peak, total = 0, 0, 0

        async def handler(_):
            nonlocal active, peak, total
            active += 1
            total += 1
            peak = max(peak, active)
            if active == 3:
                release.set()
            await release.wait()
            active -= 1
            return httpx.Response(200, json=body())

        model = executor(handler, shared)
        results = await asyncio.gather(*(model.generate(request(task_id=f"task-{i}")) for i in range(8)))
        assert all(result.status == "completed" for result in results)
        assert total == 8 and peak == 3
        assert shared.snapshot()["peak_active_reservations"] == 3
        assert shared.snapshot()["active_reservations"] == 0
        assert shared.snapshot()["reserved_requests"] == 8

    asyncio.run(scenario())


def test_shared_gate_is_actual_spawn_process_state_not_per_worker_copies():
    context = multiprocessing.get_context("spawn")
    shared = gate(1, 2)
    started_read, started_write = context.Pipe(duplex=False)
    release_read, release_write = context.Pipe(duplex=False)
    child = context.Process(target=_reserve_in_spawned_child,
                            args=(shared, started_write, release_read))
    child.start()
    try:
        assert started_read.poll(10) and started_read.recv() is True
        assert shared.snapshot()["active_reservations"] == 1
        assert shared.snapshot()["reserved_requests"] == 1
        assert shared.semaphore.acquire(False) is False
        release_write.send(True)
        child.join(10)
        assert child.exitcode == 0
        assert shared.snapshot()["active_reservations"] == 0
        assert shared.semaphore.acquire(False) is True
        shared.semaphore.release()
    finally:
        if child.is_alive():
            child.terminate()
            child.join(10)
        for connection in (started_read, started_write, release_read, release_write):
            connection.close()


def test_global_request_budget_is_atomic_and_stops_future_calls():
    calls = []
    model = executor(lambda incoming: calls.append(incoming) or httpx.Response(200, json=body()), gate(1, 1))
    assert model.generate_sync(request()).status == "completed"
    blocked = model.generate_sync(request(task_id="second"))
    assert blocked.status == "fatal" and blocked.evidence["error_kind"] == "shared_request_budget_exhausted"
    assert model.generate_sync(request(task_id="third")).status == "fatal"
    assert len(calls) == 1 and model.gate.snapshot()["stopped"] is True


def test_rate_limit_records_retry_after_but_never_retries():
    calls = []
    model = executor(lambda incoming: calls.append(incoming) or httpx.Response(
        429, headers={"retry-after": "2"}, json={"error": {"message": "rate limited"}}))
    first = model.generate_sync(request())
    assert first.status == "fatal" and first.evidence["error_kind"] == "provider_rate_limit"
    assert first.evidence["retry_after_seconds"] == 2
    assert model.generate_sync(request(task_id="second")).status == "fatal"
    assert len(calls) == 1


@pytest.mark.parametrize("encoded", [False, True])
def test_secret_echo_is_blocked_before_return_or_persistence(encoded):
    value = json.dumps(body("reflected " + CANARY))
    if encoded:
        value = value.replace(CANARY, "".join(f"\\u{ord(char):04x}" for char in CANARY))
    model = executor(lambda _: httpx.Response(200, content=value))
    response = model.generate_sync(request())
    assert response.status == "fatal" and response.text is None
    assert response.evidence["error_kind"] == "credential_echo"
    assert CANARY not in repr(response)


def test_transport_error_text_is_never_returned_and_unknown_stops_gate():
    def handler(incoming):
        raise httpx.ReadTimeout("echo " + CANARY, request=incoming)

    model = executor(handler)
    response = model.generate_sync(request())
    assert response.status == "fatal" and response.evidence["unknown_remote_effect"]
    assert response.evidence["error_kind"] == "transport_unknown"
    assert CANARY not in repr(response)
    assert model.gate.snapshot()["active_reservations"] == 0


def test_async_deadline_and_cancel_close_active_slot_without_replay():
    async def scenario(cancel):
        started = asyncio.Event()

        async def handler(_):
            started.set()
            await asyncio.Event().wait()

        model = executor(handler, timeout_seconds=0.05)
        task = asyncio.create_task(model.generate(request()))
        if cancel:
            await started.wait()
            task.cancel()
        result = await task
        assert result.status == "fatal" and result.evidence["unknown_remote_effect"] is True
        assert result.evidence["error_kind"] == ("request_canceled" if cancel else "request_deadline_exceeded")
        assert model.gate.snapshot()["active_reservations"] == 0
        assert model.gate.snapshot()["reserved_requests"] == 1
        assert (await model.generate(request(task_id="next"))).status == "fatal"

    asyncio.run(scenario(False))
    asyncio.run(scenario(True))


def test_cancel_before_admission_never_sends_or_reserves():
    async def scenario():
        calls = []
        shared = gate(1)
        shared.semaphore.acquire()
        model = executor(lambda incoming: calls.append(incoming) or httpx.Response(200, json=body()), shared)
        task = asyncio.create_task(model.generate(request()))
        await asyncio.sleep(0)
        task.cancel()
        response = await task
        shared.semaphore.release()
        assert response.status == "canceled" and response.evidence["unknown_remote_effect"] is False
        assert shared.snapshot()["reserved_requests"] == 0 and calls == []

    asyncio.run(scenario())


def test_active_response_is_closed_before_canceled_permit_is_released():
    async def scenario():
        began = asyncio.Event()
        closed = asyncio.Event()
        shared = gate(1)

        class HeldResponse(httpx.AsyncByteStream):
            async def __aiter__(self):
                began.set()
                await asyncio.Event().wait()
                yield b"unreachable fixture"

            async def aclose(self):
                assert shared.snapshot()["active_reservations"] == 1
                assert shared.semaphore.acquire(False) is False
                closed.set()

        model = executor(lambda _: httpx.Response(200, stream=HeldResponse()), shared)
        task = asyncio.create_task(model.generate(request()))
        await began.wait()
        task.cancel()
        response = await task
        assert closed.is_set() and response.status == "fatal"
        assert shared.snapshot()["active_reservations"] == 0
        assert shared.semaphore.acquire(False) is True
        shared.semaphore.release()

    asyncio.run(scenario())


def test_closed_ephemeral_credential_refuses_network_before_reservation():
    calls = []
    model = executor(lambda incoming: calls.append(incoming) or httpx.Response(200, json=body()))
    model.close()
    response = model.generate_sync(request())
    assert response.status == "fatal" and response.evidence["error_kind"] == "ephemeral_credential_closed"
    assert calls == [] and model.gate.snapshot()["reserved_requests"] == 0


@pytest.mark.parametrize("reason,text", [("stop", "not an answer"), ("length", "unfinished reasoning"),
                                        ("content_filter", None)])
def test_known_terminal_model_outcomes_are_scored_without_retry_or_global_stop(reason, text):
    value = body(text)
    value["choices"][0]["finish_reason"] = reason
    model = executor(lambda _: httpx.Response(200, json=value))
    response = model.generate_sync(request())
    assert response.status == "completed" and response.text == text
    assert response.evidence["model_outcome"] == {"stop": "completed", "length": "truncated",
                                                 "content_filter": "filtered"}[reason]
    assert response.evidence["unknown_remote_effect"] is False
    assert model.gate.snapshot()["stopped"] is False
    assert model.gate.snapshot()["reserved_requests"] == 1


@pytest.mark.parametrize("invalid", ["choices", "finish", "content", "json"])
def test_unknown_completion_or_protocol_shape_stops_all_following_requests(invalid):
    value = body()
    if invalid == "choices":
        value["choices"] = []
    elif invalid == "finish":
        value["choices"][0]["finish_reason"] = "unexpected"
    elif invalid == "content":
        value["choices"][0]["message"]["content"] = None
    model = executor(lambda _: httpx.Response(200, content="{" if invalid == "json" else json.dumps(value)))
    response = model.generate_sync(request())
    assert response.status == "fatal" and response.evidence["unknown_remote_effect"] is True
    assert model.gate.snapshot()["stopped"] is True


@pytest.mark.parametrize("usage", [None, {}, {"prompt_tokens": 12},
    {"prompt_tokens": 12, "completion_tokens": 3, "total_tokens": 16},
    {"prompt_tokens": True, "completion_tokens": 3, "total_tokens": 4},
    {"prompt_tokens": -1, "completion_tokens": 3, "total_tokens": 2}])
def test_partial_invalid_or_inconsistent_usage_is_unknown_without_new_call_rights(usage):
    value = body()
    value["usage"] = usage
    model = executor(lambda _: httpx.Response(200, json=value))
    response = model.generate_sync(request())
    assert response.status == "completed" and response.usage is None
    assert response.evidence["usage_metering"] == "unknown"
    assert response.evidence["provider_usage_present"] is True
    assert response.evidence["billing_cost"] is None
    assert model.gate.snapshot()["reserved_requests"] == 1
    assert model.gate.snapshot()["stopped"] is False


def test_per_arm_cap_changes_without_resetting_lifetime_budget_clock_or_stop():
    context = multiprocessing.get_context("spawn")
    original = gate(2, 3)
    first = executor(lambda _: httpx.Response(200, json=body()), original)
    assert first.generate_sync(request()).status == "completed"
    second_gate = original.for_concurrency(context, 1)
    assert second_gate.clock_id == original.clock_id
    assert second_gate.reserved is original.reserved and second_gate.stopped is original.stopped
    assert second_gate.snapshot()["reserved_requests"] == 1
    assert second_gate.concurrency == 1
    assert second_gate.semaphore.acquire(False) is True
    assert second_gate.semaphore.acquire(False) is False
    second_gate.semaphore.release()
    second = executor(lambda _: httpx.Response(200, json=body()), second_gate)
    assert second.generate_sync(request(task_id="two")).status == "completed"
    assert second.generate_sync(request(task_id="three")).status == "completed"
    exhausted = second.generate_sync(request(task_id="four"))
    assert exhausted.status == "fatal"
    assert original.snapshot()["reserved_requests"] == second_gate.snapshot()["reserved_requests"] == 3
    assert original.snapshot()["stopped"] is True


def test_per_arm_cap_change_refuses_active_requests_and_old_generation():
    async def scenario():
        context = multiprocessing.get_context("spawn")
        original = gate(2)
        began, release = asyncio.Event(), asyncio.Event()

        async def handler(_):
            began.set()
            await release.wait()
            return httpx.Response(200, json=body())

        first = executor(handler, original)
        task = asyncio.create_task(first.generate(request()))
        await began.wait()
        with pytest.raises(ValueError, match="active_requests"):
            original.for_concurrency(context, 1)
        release.set()
        assert (await task).status == "completed"
        replacement = original.for_concurrency(context, 1)
        with pytest.raises(ValueError, match="generation_stale"):
            original.for_concurrency(context, 3)
        refused = await first.generate(request(task_id="stale"))
        assert refused.status == "fatal" and refused.evidence["error_kind"] == "stale_request_gate"
        assert replacement.snapshot()["reserved_requests"] == 1
        assert replacement.snapshot()["stopped"] is True

    asyncio.run(scenario())


def test_transport_constructor_import_failure_is_sanitized_before_http_entry(monkeypatch):
    calls = []

    def unavailable(**kwargs):
        calls.append(kwargs)
        raise ImportError("missing optional transport " + CANARY)

    monkeypatch.setattr(httpx, "AsyncClient", unavailable)
    model = executor(lambda _: pytest.fail("no request may be sent"))
    response = model.generate_sync(request())
    assert response.status == "fatal"
    assert response.evidence["error_kind"] == "transport_initialization_failure"
    assert response.evidence["unknown_remote_effect"] is False
    assert response.evidence["http_entered_at_ns"] is None
    assert response.evidence["http_returned_at_ns"] is None
    assert response.evidence["request_ordinal"] == 1
    assert model.gate.snapshot()["reserved_requests"] == 1
    assert model.gate.snapshot()["active_reservations"] == 0
    assert model.gate.snapshot()["stopped"] is True
    assert CANARY not in repr(response)
    assert len(calls) == 1 and calls[0]["trust_env"] is True


def test_keyless_transport_preflight_never_requests_and_sanitizes_failure(monkeypatch):
    observed = []

    class KeylessClient:
        def __init__(self, **kwargs):
            assert kwargs["trust_env"] is True and kwargs["follow_redirects"] is False
            observed.append("constructed")

        async def __aenter__(self):
            observed.append("entered")
            return self

        async def __aexit__(self, *args):
            observed.append("closed")

    monkeypatch.setattr(httpx, "AsyncClient", KeylessClient)
    validate_transport_configuration()
    assert observed == ["constructed", "entered", "closed"]

    def unavailable(**kwargs):
        raise ImportError("fixture proxy support missing " + CANARY)

    monkeypatch.setattr(httpx, "AsyncClient", unavailable)
    with pytest.raises(RuntimeError, match="^transport_initialization_failure$") as captured:
        validate_transport_configuration()
    assert CANARY not in str(captured.value)
    assert captured.value.__suppress_context__ is True


@pytest.mark.parametrize("cached", [13, -1, True, None])
def test_invalid_cached_detail_is_unknown_not_a_negative_cost_basis(cached):
    value = body()
    value["usage"]["prompt_tokens_details"] = {"cached_tokens": cached}
    response = executor(lambda _: httpx.Response(200, json=value)).generate_sync(request())
    assert response.status == "completed" and response.usage is None
    assert response.evidence["usage_metering"] == "unknown"
