import json

import pytest

from contracts.identity import AgentId, AttemptId
from local_assets.models import AssetSafetyError, BenchmarkOutputValidationPolicy, Candidate, FileChange
from local_assets.validate import blast_radius, inspect_benchmark_output
from swarm.benchmark_model import ANSWER_FORMAT_INSTRUCTION, ModelRequest, SYSTEM_PROMPT, request_payload
from tools.benchmark_protocol import Example, extract_answer, model_tasks, ordered_arms, score_records, summarize_http


def candidate(content, path="task_000/result.json"):
    result = Candidate(attempt=AttemptId(task_id="fixture:0", agent=AgentId(role="builder", instance=0), attempt=1),
        scope="task_000", base_revision="a" * 40, base_head="a" * 40,
        changes=(FileChange(path=path, before="null\n", after=content),), declared_files=1, declared_lines=2)
    files, lines = blast_radius(result)
    return result.model_copy(update={"declared_files": files, "declared_lines": lines})


def test_official_first_marker_exact_string_scoring():
    assert extract_answer("reason\n#### 1,234") == "1234"
    example = Example("fixture:0", 0, "synthetic fixture", "42")
    assert score_records([example], [{"task_id": example.sample_id, "text": "#### 42.0"}])["correct"] == 0
    assert score_records([example], [{"task_id": example.sample_id, "text": "#### 42\n#### 7"}])["correct"] == 1
    assert score_records([example], [{"task_id": example.sample_id, "text": "#### 42\n#### 7"}])["single_marker_rate"] == 0


def test_missing_duplicates_and_malformed_stay_in_denominator():
    examples = [Example(f"fixture:{i}", i, "synthetic fixture", "42") for i in range(4)]
    result = score_records(examples, [{"task_id": "fixture:0", "text": "#### 42"},
        {"task_id": "fixture:1", "text": "#### 42"}, {"task_id": "fixture:1", "text": "#### 42"},
        {"task_id": "fixture:2", "text": "no final answer"}])
    assert result["accuracy"] == 0.25
    assert (result["correct"], result["duplicate"], result["malformed"], result["missing"]) == (1, 1, 1, 1)


def test_truncated_filtered_outputs_fail_even_with_correct_marker():
    for outcome in ("truncated", "filtered"):
        result = score_records([Example("fixture:0", 0, "fixture", "42")],
            [{"task_id": "fixture:0", "status": "completed", "text": "#### 42", "evidence": {"model_outcome": outcome}}])
        assert result["correct"] == 0
        assert result["incorrect"] == 1


def test_http_attempts_use_client_ordinals_not_optional_provider_ids():
    rows = [{"request_id": None, "usage": {"total_tokens": 3}, "evidence": {
        "clock": {"id": "same-host", "kind": "host-monotonic"}, "request_ordinal": 1,
        "http_entered_at_ns": 10, "http_returned_at_ns": 30}},
        {"request_id": None, "usage": None, "evidence": {
        "clock": {"id": "same-host", "kind": "host-monotonic"}, "request_ordinal": 2,
        "http_entered_at_ns": 20, "http_returned_at_ns": 40}}]
    summary = summarize_http(rows + rows[:1])
    assert summary["deduplicated_requests"] == 2
    assert summary["peak_client_http_active"] == 2
    assert summary["unknown_usage_requests"] == 1 and summary["tokens_total"] is None
    for row in rows:
        row["request_id"] = "same-provider-id"
    assert summarize_http(rows)["deduplicated_requests"] == 2


def test_gold_never_enters_model_tasks_and_all_fifteen_arms_are_fixed():
    example = Example("fixture:0", 0, "synthetic question", "hidden-gold-canary")
    assert "hidden-gold-canary" not in json.dumps(model_tasks([example]))
    arms = ordered_arms(123)
    assert arms == ordered_arms(123)
    assert len({(arm["framework"], arm["concurrency"]) for arm in arms}) == 15
    assert {arm["concurrency"] for arm in arms} == {1, 2, 3, 4, 5}


def test_explicit_numeric_format_is_identical_for_every_framework_without_gold():
    example = Example("fixture:0", 0, "synthetic question", "hidden-gold-canary")
    task = model_tasks([example])[0]
    payloads = [request_payload(ModelRequest(run_id="fixture", framework=framework,
        block_id="fixture", seed=7, task_id=task["id"], prompt=task["prompt"],
        max_tokens=4096, temperature=0.0)) for framework in ("morphogenesis", "autogen-core", "langgraph")]
    assert payloads[0] == payloads[1] == payloads[2]
    assert ANSWER_FORMAT_INSTRUCTION in SYSTEM_PROMPT
    assert ANSWER_FORMAT_INSTRUCTION in task["prompt"]
    assert "#### 42" in task["prompt"] and "#### answer" not in task["prompt"]
    assert "hidden-gold-canary" not in json.dumps(payloads)


def test_incorrect_mathematics_is_valid_storage_but_independently_incorrect():
    raw = "A deliberately wrong synthetic response.\n#### 999"
    inspect_benchmark_output(candidate(json.dumps({"response": raw})), BenchmarkOutputValidationPolicy(path="task_000/result.json"))
    score = score_records([Example("fixture:0", 0, "fixture", "42")], [{"task_id": "fixture:0", "text": raw}])
    assert score["incorrect"] == 1


@pytest.mark.parametrize("content", [json.dumps({"response": 42}), json.dumps({"response": "ok", "extra": True}),
                                      json.dumps({"response": "x" * 65537}), "not json", "null"],
                         ids=["nonstring", "extra-field", "oversize", "invalid-json", "null"])
def test_benchmark_output_rejects_bad_shapes_and_limits(content):
    with pytest.raises(AssetSafetyError):
        inspect_benchmark_output(candidate(content), BenchmarkOutputValidationPolicy(path="task_000/result.json"))


def test_benchmark_output_rejects_escape_wrong_path_and_extra_changes():
    content = json.dumps({"response": "#### 999"})
    for path in ("../outside.json", "task_001/result.json", "task_000/result.py"):
        with pytest.raises(AssetSafetyError):
            inspect_benchmark_output(candidate(content, path), BenchmarkOutputValidationPolicy(path="task_000/result.json"))
    value = candidate(content)
    with pytest.raises(AssetSafetyError):
        inspect_benchmark_output(value.model_copy(update={"changes": value.changes * 2}), BenchmarkOutputValidationPolicy(path="task_000/result.json"))
