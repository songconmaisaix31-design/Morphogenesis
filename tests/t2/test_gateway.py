"""MockTransport only: real adapter/validation, never paid gateway acceptance."""

import json
from pathlib import Path
import time
from typing import Any

import httpx
import pytest

from bootstrap.sample import prepare_workspace
from bootstrap.verify import SampleVerifier
from contracts.identity import AgentId, AttemptId
from contracts.resolution import Gene, GeneRef
from contracts.runtime import RunConfig
from orchestration.gateway import EVOMAP_BASE_URL, EVOMAP_MODEL, GatewayExecutor
from orchestration.rehearsal import Rehearsal, RehearsalOptions, read_rehearsal
from tests.t2.test_codex import FIXED

KEY = "fixture-only-not-a-real-gateway-key"
ENDPOINT = EVOMAP_BASE_URL + "/chat/completions"


def completion(*, adopted: list[str] | None = None) -> dict[str, Any]:
    return {
        "model": "fixture-provider-model", "choices": [{
            "index": 0, "finish_reason": "stop", "message": {
                "role": "assistant", "content": json.dumps({
                    "path": "sample.py", "content": FIXED, "summary": "fixture verified strategy",
                    "adopted_gene_ids": adopted or [],
                }),
            },
        }],
        "usage": {"prompt_tokens": 12, "completion_tokens": 8, "total_tokens": 20},
    }


def prepared(tmp_path: Path, **changes: object) -> tuple[RunConfig, AttemptId]:
    workspace = prepare_workspace(tmp_path / "task")
    return (RunConfig.model_validate({
        "run_id": "gateway-fixture", "workspace": str(workspace), "writable_paths": ["sample.py"], **changes,
    }), AttemptId(task_id="repair-gateway", agent=AgentId(role="builder", instance=0), attempt=0))


def assert_no_secret(evidence: Path, result_json: str) -> None:
    assert KEY not in result_json
    for path in evidence.rglob("*"):
        if path.is_file():
            assert KEY.encode() not in path.read_bytes()


def test_one_post_applies_proposal_and_preserves_real_http_evidence(tmp_path: Path) -> None:
    config, attempt = prepared(tmp_path)
    requests: list[httpx.Request] = []
    gene = Gene(ref=GeneRef(gene_id="injected-repair"), signals_match=["python", "repair"],
                strategy=["preserve first occurrence order"], provenance="mock")

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert str(request.url) == ENDPOINT and request.method == "POST"
        assert request.headers["Authorization"] == f"Bearer {KEY}"
        payload = json.loads(request.content)
        assert set(payload) == {"model", "messages", "max_tokens", "stream"}
        assert payload["model"] == EVOMAP_MODEL
        assert payload["max_tokens"] == 4096 <= config.max_tokens
        assert payload["stream"] is False
        assert KEY not in request.content.decode()
        context = json.loads(payload["messages"][1]["content"])
        assert context["experience"][0]["strategy"] == gene.strategy
        assert all(0 < value <= config.timeout_seconds for value in request.extensions["timeout"].values())
        return httpx.Response(200, json=completion(adopted=[gene.ref.gene_id]))

    evidence = tmp_path / "gateway"
    executor = GatewayExecutor(evidence, api_key=KEY, provenance="mock", transport=httpx.MockTransport(handle))
    result = executor.execute(attempt, config, [gene])
    assert result.status == "pending_review"
    assert result.acceptance.interface_live == result.acceptance.task_live == "not_run"
    assert result.usage.tokens == 20 and result.usage.cost_usd is None
    assert (Path(config.workspace) / "sample.py").read_text() == FIXED
    assert SampleVerifier(tmp_path / "review").verify(config.workspace, AgentId(role="reviewer", instance=0)).passed
    assert sorted(path.name for path in evidence.iterdir()) == ["proposal.json", "request.json", "response.json"]
    saved = json.loads((evidence / "response.json").read_text())
    assert saved["http_status"] == 200 and saved["elapsed_seconds"] >= 0
    assert saved["body"]["model"] == "fixture-provider-model"
    assert saved["body"]["usage"]["total_tokens"] == 20
    assert json.loads((evidence / "proposal.json").read_text())["adopted_gene_ids"] == [gene.ref.gene_id]
    assert_no_secret(evidence, result.model_dump_json())
    with pytest.raises(FileExistsError):
        executor.execute(attempt, config, [gene])
    assert len(requests) == 1


def test_environment_credential_and_missing_credential_fail_before_request(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config, attempt = prepared(tmp_path)
    requests: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.headers["Authorization"] == f"Bearer {KEY}"
        return httpx.Response(200, json=completion())

    monkeypatch.delenv("MORPH_EVOMAP_API_KEY", raising=False)
    executor = GatewayExecutor(tmp_path / "gateway", provenance="mock", transport=httpx.MockTransport(handle))
    with pytest.raises(ValueError, match="missing or invalid"):
        executor.execute(attempt, config, [])
    assert not requests and not (tmp_path / "gateway").exists()
    monkeypatch.setenv("MORPH_EVOMAP_API_KEY", KEY)
    assert executor.execute(attempt, config, []).status == "pending_review"
    assert len(requests) == 1


@pytest.mark.parametrize("base_url", ["http://api.evomap.ai/v1", "https://other.invalid/v1",
                                      "https://api.evomap.ai/v1/chat/completions", "https://api.evomap.ai:444/v1"])
def test_unapproved_destination_is_rejected_before_effects(tmp_path: Path, base_url: str) -> None:
    with pytest.raises(ValueError, match="confirmed"):
        GatewayExecutor(tmp_path / "gateway", base_url=base_url)
    assert not (tmp_path / "gateway").exists()


def test_custom_transport_cannot_claim_live_or_replay(tmp_path: Path) -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json=completion()))
    with pytest.raises(ValueError, match="mock provenance"):
        GatewayExecutor(tmp_path / "gateway", transport=transport)
    with pytest.raises(ValueError, match="explicit MockTransport"):
        GatewayExecutor(tmp_path / "gateway", provenance="mock")
    with pytest.raises(ValueError, match="replay"):
        GatewayExecutor(tmp_path / "gateway", provenance="replay")


@pytest.mark.parametrize("status", [401, 429, 500, 307])
def test_http_failure_or_redirect_has_one_request_and_redacted_evidence(tmp_path: Path, status: int) -> None:
    config, attempt = prepared(tmp_path)
    original = (Path(config.workspace) / "sample.py").read_bytes()
    requests: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(status, json={"error": {"message": f"fixture echoes {KEY}"}},
                              headers={"Location": "https://unapproved.invalid/steal"})

    evidence = tmp_path / "gateway"
    result = GatewayExecutor(evidence, api_key=KEY, provenance="mock", transport=httpx.MockTransport(handle)).execute(
        attempt, config, [])
    assert result.status == "insufficient_evidence" and len(requests) == 1
    assert result.usage.tokens is None and result.usage.cost_usd is None
    assert (Path(config.workspace) / "sample.py").read_bytes() == original
    assert json.loads((evidence / "response.json").read_text())["http_status"] == status
    assert_no_secret(evidence, result.model_dump_json())


def test_timeout_has_no_retry_or_exception_secret(tmp_path: Path) -> None:
    config, attempt = prepared(tmp_path)
    calls = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout(f"do not log {KEY}", request=request)

    evidence = tmp_path / "gateway"
    result = GatewayExecutor(evidence, api_key=KEY, provenance="mock", transport=httpx.MockTransport(handle)).execute(
        attempt, config, [])
    assert result.status == "insufficient_evidence" and calls == 1
    assert "ReadTimeout" in result.verdict.summary
    assert result.usage.tokens is None
    assert not (evidence / "proposal.json").exists()
    assert_no_secret(evidence, result.model_dump_json())


@pytest.mark.parametrize("fault", [
    "missing_usage", "negative_usage", "bool_usage", "inconsistent_usage", "not_json",
    "length", "refusal", "tool_calls", "bad_path", "unsafe_python", "false_adoption", "credential_echo",
])
def test_invalid_response_is_not_applied_or_retried(tmp_path: Path, fault: str) -> None:
    config, attempt = prepared(tmp_path)
    original = (Path(config.workspace) / "sample.py").read_bytes()
    body = completion()
    message = body["choices"][0]["message"]
    proposal = json.loads(message["content"])
    if fault == "missing_usage":
        del body["usage"]
    elif fault == "negative_usage":
        body["usage"]["prompt_tokens"] = -1
    elif fault == "bool_usage":
        body["usage"]["prompt_tokens"] = True
    elif fault == "inconsistent_usage":
        body["usage"]["total_tokens"] = 21
    elif fault == "not_json":
        message["content"] = "not a proposal"
    elif fault == "length":
        body["choices"][0]["finish_reason"] = "length"
    elif fault == "refusal":
        message["refusal"] = "fixture refusal"
    elif fault == "tool_calls":
        message["tool_calls"] = [{"id": "forbidden-tool"}]
    elif fault == "bad_path":
        proposal["path"] = "../outside.py"
    elif fault == "unsafe_python":
        proposal["content"] = "import os\n" + FIXED
    elif fault == "false_adoption":
        proposal["adopted_gene_ids"] = ["never-injected"]
    elif fault == "credential_echo":
        proposal["summary"] = KEY
    if fault in {"bad_path", "unsafe_python", "false_adoption", "credential_echo"}:
        message["content"] = json.dumps(proposal)
    calls = 0

    def handle(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json=body)

    evidence = tmp_path / "gateway"
    result = GatewayExecutor(evidence, api_key=KEY, provenance="mock", transport=httpx.MockTransport(handle)).execute(
        attempt, config, [])
    assert result.status == "insufficient_evidence" and calls == 1
    assert (Path(config.workspace) / "sample.py").read_bytes() == original
    assert not (evidence / "proposal.json").exists()
    assert_no_secret(evidence, result.model_dump_json())


@pytest.mark.parametrize("fault", ["stop_before", "stop_during", "changed_path", "token_budget", "elapsed_budget"])
def test_path_stop_and_budget_guards_at_effect_boundary(tmp_path: Path, fault: str) -> None:
    config, attempt = prepared(tmp_path, max_tokens=10 if fault == "token_budget" else 20000,
                               timeout_seconds=0.01 if fault == "elapsed_budget" else 120)
    source = Path(config.workspace) / "sample.py"
    original = source.read_bytes()
    stopped = fault == "stop_before"
    calls = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal stopped, calls
        calls += 1
        assert json.loads(request.content)["max_tokens"] == min(config.max_tokens, 4096)
        if fault == "stop_during":
            stopped = True
        if fault == "changed_path":
            (Path(config.workspace) / "extra-file").write_text("path changed in flight")
        if fault == "elapsed_budget":
            time.sleep(0.03)  # MockTransport ignores phase timeout; the application check still rejects.
        return httpx.Response(200, json=completion())

    result = GatewayExecutor(tmp_path / "gateway", api_key=KEY, provenance="mock", transport=httpx.MockTransport(handle),
                             stop_requested=lambda: stopped).execute(attempt, config, [])
    assert result.status == "insufficient_evidence"
    assert calls == (0 if fault == "stop_before" else 1)
    assert source.read_bytes() == original


def test_key_in_task_context_and_invalid_input_paths_fail_before_request(tmp_path: Path) -> None:
    config, attempt = prepared(tmp_path)
    calls = 0

    def handle(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json=completion())

    executor = GatewayExecutor(tmp_path / "gateway", api_key=KEY, provenance="mock", transport=httpx.MockTransport(handle))
    task = Path(config.workspace) / "TASK.md"
    task.write_text(KEY)
    with pytest.raises(ValueError, match="credential found"):
        executor.execute(attempt, config, [])
    task.write_text("safe fixture")
    outside = RunConfig.model_validate({**config.model_dump(), "writable_paths": ["other.py"]})
    with pytest.raises(ValueError, match="only sample.py"):
        executor.execute(attempt, outside, [])
    assert calls == 0 and not (tmp_path / "gateway").exists()


@pytest.mark.parametrize("outcome", ["success", "missing_usage", "timeout"])
def test_gateway_rehearsal_reuses_review_adoption_and_stops_unknowns(tmp_path: Path, outcome: str) -> None:
    calls: list[dict[str, Any]] = []

    def handle(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        calls.append(payload)
        if outcome == "timeout":
            raise httpx.ReadTimeout("fixture timeout", request=request)
        context = json.loads(payload["messages"][1]["content"])
        body = completion(adopted=[gene["ref"]["gene_id"] for gene in context["experience"]])
        if outcome == "missing_usage":
            del body["usage"]
        return httpx.Response(200, json=body)

    options = RehearsalOptions(root=tmp_path / "run", executor="evomap", tau_seconds=0.1,
                               stage_delay=0, tick_seconds=0.025)
    assert options.model == EVOMAP_MODEL
    assert RehearsalOptions(root=tmp_path / "unused").model == "gpt-5.6-luna"
    app = Rehearsal(options, provenance="mock", executor_factory=lambda evidence, cfg: GatewayExecutor(
        evidence, model=cfg.model, api_key=KEY, provenance="mock", transport=httpx.MockTransport(handle)))
    document = app.run()
    assert read_rehearsal(app.root / "rehearsal.json") == document
    assert all(snapshot.executor == "evomap" and snapshot.model == EVOMAP_MODEL for snapshot in document.history)
    assert not list(app.root.rglob("codex.jsonl")) and not list(app.root.rglob("command.json"))
    assert not (app.root / "repair/cli").exists()
    if outcome == "success":
        assert document.current.stage == "completed", document.current.failure
        assert len(calls) == document.current.model_calls_started == 2
        assert document.current.adoptions[0].attempt == document.current.results[1].attempt
        assert document.current.results[0].attempt.agent != document.current.results[1].attempt.agent
        assert len(document.current.genes) == 2 and not document.current.retrievable_gene_ids
        assert (app.root / "recovery/gateway/proposal.json").exists()
    else:
        assert document.current.stage == "failed"
        assert len(calls) == document.current.model_calls_started == 1
        assert not (app.root / "recovery").exists()
    assert_no_secret(app.root, document.model_dump_json())
