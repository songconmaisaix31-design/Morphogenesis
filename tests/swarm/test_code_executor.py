"""Mock HTTP contract and real fixed local validation, never paid requests."""

import json
import inspect
import os
from pathlib import Path
import subprocess
import sys

import httpx
import pytest

from contracts.identity import AgentId
from local_assets.models import SampleValidationPolicy
from local_assets.paths import git
from swarm.code_executor import DashScopeCodeConfig, DashScopeCodeExecutor
from swarm.models import BudgetPolicy, Locality, ModelPrices, RunLimits, Signal
from swarm.worker_loop import Worker, WorkerConfig
from tests.local_assets.test_fixed_sample import BAD, GOOD


def configured(tmp_path, monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    target, state = tmp_path / "target", tmp_path / "state"
    target.mkdir()
    for directory in ("a", "b"):
        (target / directory).mkdir()
        (target / directory / "sample.py").write_bytes(BAD.encode())
    git(target, "init", "-b", "code-task")
    git(target, "add", ".")
    git(target, "-c", "user.name=Test", "-c", "user.email=test@localhost", "commit", "-m", "seed")
    config = WorkerConfig(state=state, target=target, agent=AgentId(role="builder", instance=0),
        locality=Locality(workspace=str(target), authorized_scopes=(".",), modules=("code",)),
        budget=BudgetPolicy(max_cost_usd=1, max_tokens=100000, burn_rate_tokens=100000,
            unbounded_reservation_usd=0.1, limits=RunLimits(max_tasks=2, max_attempts=2, max_attempts_per_task=1),
            prices=ModelPrices(provider="dashscope", model="qwen-plus-2025-12-01",
                input_usd_per_million=0.1, output_usd_per_million=0.3)),
        energy=1, energy_policy="claim", max_senses=10, max_idle=1)
    return config


def handler(request, *, wrong=False, unknown=False):
    payload = json.loads(request.content)
    assert payload["enable_thinking"] is False
    assert payload["model"] == "qwen-plus-2025-12-01"
    assert payload["temperature"] == 0.2 and payload["seed"] == 1234
    assert "acceptance_runner" not in request.content.decode()
    assert "expectations" not in request.content.decode()
    context = json.loads(payload["messages"][1]["content"])
    experience = context["experience"]
    # A transformed but still correct repair must not require source equality.
    after = GOOD.replace('"empty"', '"no values"') if experience else GOOD
    if wrong:
        after = after.replace("sum(values) / len(values)", "0")
    proposal = {"changes": [{"path": context["path"], "before": context["source"], "after": after}],
        "adopted_asset_ids": [experience[0]["asset_id"]] if experience else []}
    body = {"id": "mock-code-request", "model": payload["model"], "choices": [{
        "finish_reason": "stop", "message": {"role": "assistant", "content": json.dumps(proposal)}}]}
    if not unknown:
        body["usage"] = {"prompt_tokens": 30, "completion_tokens": 40, "total_tokens": 70,
                         "prompt_tokens_details": {"cached_tokens": 10}}
    return httpx.Response(200, json=body)


def enqueue(worker, name, path, *, reuse=False):
    payload = {"instruction": "Repair clamp, mean and unique per their public specification.",
               "output_path": path, "phase": "1"}
    if reuse:
        payload.update({"reuse_task_id": "first", "path_map": {"a/sample.py": path}})
    signal = Signal(task_id=name, signal_id=name, workspace=str(worker.target), scope=".",
        module="code", kind="error_pattern", required_capability="repair", payload=payload)
    policy = SampleValidationPolicy(version="sample-tests-v1", path=path)
    worker.ledger.enqueue(signal, dependencies=("first",) if reuse else (),
        acceptance={"validation_policy": policy.model_dump(mode="json")})
    worker.field.deposit(signal)


def test_transformed_experience_validates_then_adopts(tmp_path, monkeypatch):
    config = configured(tmp_path, monkeypatch)
    executor = DashScopeCodeExecutor(DashScopeCodeConfig(phase_profiles={"1": "Check order."}),
                                    transport=httpx.MockTransport(handler), provenance="mock")
    first = Worker(config, executor)
    enqueue(first, "first", "a/sample.py")
    assert first.run()["completed"] == 1
    # Fresh Git workspace and actual fresh process share authoritative state;
    # the previous target and original candidate bytes are never copied.
    target = tmp_path / "fresh-target"
    (target / "b").mkdir(parents=True)
    (target / "b/sample.py").write_bytes(BAD.encode())
    git(target, "init", "-b", "fresh-session")
    git(target, "add", ".")
    git(target, "-c", "user.name=Test", "-c", "user.email=test@localhost", "commit", "-m", "seed")
    fresh = config.model_copy(update={"agent": AgentId(role="builder", instance=1), "target": target,
        "locality": config.locality.model_copy(update={"workspace": str(target)})})
    successor = Worker(fresh, executor)
    enqueue(successor, "second", "b/sample.py", reuse=True)
    program = ("import json, os, httpx\nfrom swarm.code_executor import DashScopeCodeConfig, DashScopeCodeExecutor\n"
        "from swarm.worker_loop import Worker, WorkerConfig\nGOOD=" + repr(GOOD) + "\n" + inspect.getsource(handler)
        + "\nconfig=WorkerConfig.model_validate_json(" + repr(fresh.model_dump_json()) + ")\n"
        "executor=DashScopeCodeExecutor(DashScopeCodeConfig(),transport=httpx.MockTransport(handler),provenance='mock')\n"
        "print(json.dumps({'pid':os.getpid(),'status':Worker(config,executor).run()}))\n")
    child = subprocess.run([sys.executable, "-c", program], capture_output=True, timeout=180, check=False)
    assert child.returncode == 0, child.stderr.decode(errors="replace")
    observation = json.loads(child.stdout)
    assert observation["pid"] != os.getpid()
    status = observation["status"]
    assert status["completed"] == 1, status
    result = successor.ledger.get("second").result
    execution = successor.assets.consumption(result["execution_id"])
    assert "model_declared_derivation" in execution.context.input_context
    assert successor.assets.fetch(execution.asset_id).changes[0].after != execution.candidate.changes[0].after
    assert Path(successor.ledger.get("second").signal.workspace) != first.target
    with successor.assets.connection() as db:
        assert db.execute("SELECT COUNT(*) FROM adoptions").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM consumptions").fetchone()[0] == 2


@pytest.mark.parametrize("unknown", [False, True])
def test_wrong_or_unknown_stops_without_adoption(tmp_path, monkeypatch, unknown):
    config = configured(tmp_path, monkeypatch)
    calls = []
    def respond(request):
        calls.append(request)
        return handler(request, wrong=True, unknown=unknown)
    executor = DashScopeCodeExecutor(DashScopeCodeConfig(), transport=httpx.MockTransport(respond), provenance="mock")
    worker = Worker(config, executor)
    enqueue(worker, "first", "a/sample.py")
    result = worker.run()
    assert result["completed"] == 0
    assert (worker.target / "a/sample.py").read_bytes() == BAD.encode()
    with worker.assets.connection() as db:
        assert db.execute("SELECT COUNT(*) FROM adoptions").fetchone()[0] == 0
    assert len(calls) == 1
    if unknown:
        assert result["state"] == "sleeping"
        assert Worker(config, executor).run()["state"] == "sleeping"
        assert len(calls) == 1


def test_executor_rejects_parent_credential(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "not-real")
    with pytest.raises(ValueError, match="credential_environment_must_be_cleared"):
        DashScopeCodeExecutor(DashScopeCodeConfig())


def test_transport_trace_marks_entry_headers_and_return_without_payload():
    from orchestration.gateway_transport import single_request
    phases = []
    def response(request):
        assert phases == ["http_send_entered"]
        return httpx.Response(200, json={"ok": True})
    result = single_request({"model": "fixture"}, key="not-real", phase_timeout=5,
                            transport=httpx.MockTransport(response), observe=phases.append)
    assert result.status == 200
    assert phases == ["http_send_entered", "http_response_headers", "http_transport_returned"]
