"""Explicit MockTransport/IPC regressions; no paid model or live acceptance."""

from collections import Counter
import json
import multiprocessing
import os
from pathlib import Path
import socket
import subprocess
import time

import httpx
import pytest

from swarm.cli import EvoMapRun, evomap_worker_config, seed_evomap
from swarm.evomap_executor import EvoMapConfig, EvoMapExecutor, Reply, _proposal_content, _request
from swarm.worker_loop import Worker, WorkerConfig
from local_assets.models import AssetSafetyError

KEY = "fixture-only-not-a-real-key"


def configured(tmp_path, *, prices=True):
    key_file = tmp_path / "private-key.txt"
    key_file.write_text(KEY)
    budget = {"max_cost_usd": 1, "unbounded_reservation_usd": 0.02,
              "limits": {"max_tasks": 6, "max_attempts": 6, "max_attempts_per_task": 1,
                         "max_derived_tasks": 0, "max_runtime_seconds": 300}}
    if prices:
        budget["prices"] = {"provider": "evomap", "model": "evomap-gpt-5.6-sol",
                            "input_usd_per_million": 1, "output_usd_per_million": 1}
    config = EvoMapRun(directory=tmp_path / "data", api=EvoMapConfig(credential_file=key_file), budget=budget)
    seed_evomap(config)
    return config


def completion(request, *, wrong=False):
    payload = json.loads(request.content)
    assert payload["stream"] is False and payload["model"] == "evomap-gpt-5.6-sol"
    context = json.loads(payload["messages"][1]["content"])
    assert set(context) == {"task_id", "instruction", "input", "experience"}
    assert "validation_policy" not in request.content.decode()
    incoming, instruction = context["input"], context["instruction"]
    normalized = instruction.lower()
    if normalized.startswith("sort"):
        answer = sorted(incoming)
    elif normalized.startswith("remove repeated"):
        answer = list(dict.fromkeys(incoming))
    elif "three smallest" in normalized:
        answer = sorted(incoming)[:3]
    elif "sum" in normalized:
        answer = sum(incoming)
    else:
        answer = dict(Counter(incoming))
    experience = context["experience"]
    adopted = [experience[0]["asset_id"]] if experience else []
    return {"id": "fixture-request", "model": "fixture-returned-model",
            "choices": [{"finish_reason": "stop", "message": {"role": "assistant",
                "content": json.dumps({"answer": "wrong" if wrong else answer, "adopted_asset_ids": adopted})}}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 8, "total_tokens": 20}}


def audit(config):
    return [json.loads(path.read_bytes()) for path in (config.directory / "state/audit").rglob("*.json")]


def _model_worker(config_json, instance, start):
    def deny(*args, **kwargs):
        raise AssertionError("network is blocked")
    socket.socket.connect = deny
    socket.create_connection = deny
    socket.getaddrinfo = deny
    calls = []
    def handle(request):
        calls.append(json.loads(request.content))
        return httpx.Response(200, json=completion(request))
    config = EvoMapRun.model_validate_json(config_json)
    executor = EvoMapExecutor(config.api, transport=httpx.MockTransport(handle), provenance="mock")
    worker = Worker(WorkerConfig.model_validate_json(evomap_worker_config(config, instance)), executor)
    start.wait(60)
    result = worker.run()
    (config.directory / f"mock-http-{instance}.json").write_text(json.dumps({
        "pid": os.getpid(), "calls": len(calls), "state": result["state"], "provenance": "mock"}))


def test_three_process_data_requests_and_exact_cross_member_adoption(tmp_path):
    config = configured(tmp_path)
    context = multiprocessing.get_context("spawn")
    start = context.Barrier(3)
    processes = [context.Process(target=_model_worker, args=(config.model_dump_json(), i, start)) for i in range(3)]
    try:
        for process in processes:
            process.start()
        deadline = time.monotonic() + 180
        for process in processes:
            process.join(max(0, deadline-time.monotonic()))
        assert [process.exitcode for process in processes] == [0, 0, 0]
    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(5)
    rows = audit(config)
    assert len(rows) == 6 and all(row["outcome"] == "promoted" for row in rows), rows
    assert {row["worker_id"] for row in rows} == {"builder-0", "builder-1", "builder-2"}
    assert len({row["pid"] for row in rows}) == 3
    assert all(row["execution"]["requested_model"] == config.api.model for row in rows)
    assert all(row["execution"]["returned_model"] == "fixture-returned-model" for row in rows)
    assert all(row["execution"]["provider_request_id"] == "fixture-request" for row in rows)
    assert all(row["interface_live"] == row["task_live"] == "not_run" for row in rows)
    receipts = [json.loads(path.read_bytes()) for path in config.directory.glob("mock-http-*.json")]
    assert sum(row["calls"] for row in receipts) == 6
    assert all(row["calls"] > 0 for row in receipts)
    from local_assets.store import LocalAssetStore
    store = LocalAssetStore(config.directory / "state/assets")
    adoption, = store.adoptions()
    assert adoption.context.worker_id == "builder-2" and adoption.context.task_id == "data-5"
    source = next(row for row in rows if row["task_id"] == "data-0")
    target = next(row for row in rows if row["task_id"] == "data-5")
    assert source["worker_id"] != target["worker_id"]
    assert target["consumed_asset_ids"] == [source["asset_id"]]
    assert adoption.asset_id == source["asset_id"] and adoption.result_id == target["result_id"]
    assert all(KEY.encode() not in path.read_bytes() for path in config.directory.rglob("*.json"))


def test_no_price_known_usage_finishes_one_then_stops_new_requests(tmp_path):
    config = configured(tmp_path, prices=False)
    calls = []
    def handle(request):
        calls.append(request)
        return httpx.Response(200, json=completion(request))
    executor = EvoMapExecutor(config.api, transport=httpx.MockTransport(handle), provenance="mock")
    worker = Worker(WorkerConfig.model_validate_json(evomap_worker_config(config, 0)), executor)
    result = worker.run()
    assert result["state"] == "sleeping" and result["completed"] == 1
    assert len(calls) == 1 and audit(config)[0]["outcome"] == "promoted"
    snapshot = worker.budget.snapshot()
    assert snapshot.reason == "unknown_cost" and snapshot.tokens == 20
    assert snapshot.estimated_cost_usd is snapshot.actual_cost_usd is None
    assert snapshot.reserved_estimate_usd == 0.02
    assert Worker(worker.config, executor).run()["state"] == "sleeping" and len(calls) == 1


@pytest.mark.parametrize("fault", ["unknown", "timeout", "wrong", "false_adoption", "too_many_tokens"])
def test_gateway_failure_keeps_bounded_call_usage_and_no_false_adoption(tmp_path, fault):
    config = configured(tmp_path)
    calls = []
    def handle(request):
        calls.append(request)
        if fault == "timeout":
            raise httpx.ReadTimeout(KEY, request=request)
        body = completion(request, wrong=fault == "wrong")
        if fault == "unknown":
            body.pop("usage")
        if fault == "false_adoption":
            body["choices"][0]["message"]["content"] = json.dumps({"answer": [], "adopted_asset_ids": ["invented"]})
        if fault == "too_many_tokens":
            body["usage"] = {"prompt_tokens": 12, "completion_tokens": 10000, "total_tokens": 10012}
        return httpx.Response(200, json=body)
    executor = EvoMapExecutor(config.api, transport=httpx.MockTransport(handle), provenance="mock")
    worker = Worker(WorkerConfig.model_validate_json(evomap_worker_config(config, 0)), executor)
    result = worker.run()
    assert result["state"] in {"sleeping", "stopped"} and len(calls) == 1
    assert not worker.assets.promotions() and not worker.assets.adoptions()
    assert all(path.read_text() == "null\n" for path in worker.target.rglob("*.json"))
    if fault in {"timeout", "unknown"}:
        assert worker.budget.snapshot().reason == "unknown_usage"
        assert worker.budget.snapshot().tokens is None
    else:
        assert worker.budget.snapshot().tokens is not None
    assert all(KEY.encode() not in path.read_bytes() for path in config.directory.rglob("*.json"))


@pytest.mark.parametrize("location", ["target", "state", "repository", "frozen"])
def test_credential_path_rejected_before_any_credential_read(tmp_path, monkeypatch, location):
    from local_assets.paths import FROZEN_MAINLINE
    config = configured(tmp_path)
    worker_config = WorkerConfig.model_validate_json(evomap_worker_config(config, 0))
    root = {"target": worker_config.target, "state": worker_config.state,
            "repository": Path(__file__).resolve().parents[2], "frozen": FROZEN_MAINLINE}[location]
    credential = root / "must-not-read.secret"
    executor = EvoMapExecutor(config.api.model_copy(update={"credential_file": credential}),
                             transport=httpx.MockTransport(lambda _: pytest.fail("request reached")), provenance="mock")
    read = Path.read_text
    def guarded(path, *args, **kwargs):
        assert path != credential, "credential reached parent read"
        return read(path, *args, **kwargs)
    monkeypatch.setattr(Path, "read_text", guarded)
    with pytest.raises(AssetSafetyError, match="credential_path_overlaps"):
        Worker(worker_config, executor)


def test_no_fake_live_transport_or_inherited_secret(tmp_path, monkeypatch):
    config = EvoMapConfig(credential_file=tmp_path / "private")
    with pytest.raises(ValueError, match="provenance"):
        EvoMapExecutor(config, transport=httpx.MockTransport(lambda _: httpx.Response(200)))
    monkeypatch.setenv("MORPH_EVOMAP_API_KEY", KEY)
    with pytest.raises(ValueError, match="environment_must_be_cleared"):
        EvoMapExecutor(config)


def test_request_child_receives_path_only_and_parent_never_reads_secret(tmp_path, monkeypatch):
    config = configured(tmp_path)
    executor = EvoMapExecutor(config.api, transport=httpx.MockTransport(lambda _: pytest.fail("unexpected mock")), provenance="mock")
    monkeypatch.setattr(executor, "_transport", None)  # Exercise subprocess IPC with a simulated child below.
    worker_config = WorkerConfig.model_validate_json(evomap_worker_config(config, 0)).model_copy(update={"energy": 1})
    read = Path.read_text
    def no_parent_read(path, *args, **kwargs):
        assert path != config.api.credential_file
        return read(path, *args, **kwargs)
    monkeypatch.setattr(Path, "read_text", no_parent_read)
    run = subprocess.run
    calls = []
    def child(command, **kwargs):
        if command[-1] != "--request-child":
            return run(command, **kwargs)
        calls.append(command)
        assert KEY not in str(command) and KEY.encode() not in kwargs["input"]
        assert "MORPH_EVOMAP_API_KEY" not in kwargs["env"]
        envelope = json.loads(kwargs["input"])
        assert envelope["config"]["credential_file"] == str(config.api.credential_file)
        # Simulated IPC retains outer mock provenance and claims no live proof.
        return subprocess.CompletedProcess(command, 0, Reply(error_kind="simulated_child_failure", uncertain=True).model_dump_json().encode(), b"")
    monkeypatch.setattr(subprocess, "run", child)
    worker = Worker(worker_config, executor)
    assert worker.run()["state"] == "sleeping" and len(calls) == 1
    assert audit(config)[0]["interface_live"] != "passed"
    assert all(KEY.encode() not in path.read_bytes() for path in config.directory.rglob("*.json"))


def test_echoed_key_and_redirect_are_not_accepted_or_retried():
    calls = []
    def handle(request):
        calls.append(request)
        return httpx.Response(307, json={"id": KEY, "error": KEY}, headers={"Location": "https://invalid.example"})
    reply = _request({"model": "fixture"}, KEY, 1,
                     transport=httpx.MockTransport(handle), provenance="mock")
    assert len(calls) == 1 and reply.uncertain and reply.content is None
    assert reply.interface_live == "not_run" and KEY not in reply.model_dump_json()


@pytest.mark.parametrize("tag", ["json", "JSON", ""])
def test_complete_json_fence_is_unwrapped(tag):
    content = '{"answer":{"item":1},"adopted_asset_ids":[]}'
    assert _proposal_content(f"```{tag}\n{content}\n```") == content


@pytest.mark.parametrize("content", [
    'prefix\n```json\n{"answer":1,"adopted_asset_ids":[]}\n```',
    '```json\n{"answer":1,"adopted_asset_ids":[]}\n```\nsuffix',
    '```python\n{"answer":1,"adopted_asset_ids":[]}\n```',
])
def test_json_fence_unwrap_rejects_prose_and_other_languages(content):
    assert _proposal_content(content) == content


def test_aggregate_live_scene_requires_members_pids_and_authoritative_adoption():
    from swarm.cli import evomap_acceptance
    rows = [{"provenance": "live", "outcome": "promoted", "task_live": "passed", "interface_live": "passed",
             "worker_id": f"builder-{i // 2}", "pid": 100 + i // 2, "task_id": f"data-{i}",
             "asset_id": f"asset-{i}", "result_id": f"result-{i}",
             "consumed_asset_ids": ["asset-0"] if i == 5 else []} for i in range(6)]
    view = {"sections": {"validation": {"tables": {"adoptions": [{"body": {
        "asset_id": "asset-0", "result_id": "result-5", "context": {"task_id": "data-5", "worker_id": "builder-2"}}}]}}}}
    assert evomap_acceptance(rows, view)["task_live"] == "passed"
    assert evomap_acceptance(rows, {})["task_live"] == "blocked"
    assert evomap_acceptance([{**row, "pid": 100} for row in rows], view)["task_live"] == "blocked"
    assert evomap_acceptance([{**row, "worker_id": "builder-0"} for row in rows], view)["task_live"] == "blocked"
    assert evomap_acceptance([{**row, "provenance": "mock"} for row in rows], view)["task_live"] == "blocked"


def test_acceptance_does_not_report_pending_without_audit_as_zero_usage():
    from swarm.cli import evomap_acceptance
    view = {"sections": {"budget": {"tables": {"budget_reservations": [{
        "request_id": "task:lease", "status": "pending", "tokens": None,
        "usage_metering": "unknown", "cost": "unknown", "reserved_usd": 0.02}]}}}}
    summary = evomap_acceptance([], view)
    assert summary["tokens"] == {"audited_requests": 0, "known_requests": 0,
                                  "unknown_reservations": 1, "known_total": 0, "total": None}
