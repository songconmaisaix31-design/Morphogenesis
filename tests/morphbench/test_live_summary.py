"""Ensure missing/unknown evidence cannot silently become zero usage or success."""
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2] / "tools" / "morphbench"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_load("live_cases")
_load("live_plan")
_load("summarize")
summary = _load("live_summary")


def test_missing_cells_remain_not_run_and_have_no_observed_ci(tmp_path):
    report = summary.summarize(tmp_path)
    assert len(report["missing_cells"]) == 24
    assert all(c["status"] == "NOT_RUN" for c in report["cells"])
    assert all(c["observed_cell_completion_rate"]["n"] == 0 for c in report["groups"])
    assert all(c["ci95"] is None for c in report["paired_contrasts"])


def test_sent_intent_without_response_keeps_unknown_usage_and_bill(tmp_path):
    task = tmp_path / "gateway"
    task.mkdir()
    (task / "request.json").write_text(json.dumps({"request_id": "local-intent",
        "attempt": {"task_id": "a"}, "request": {"model": "fixed"}, "provenance": "live"}))
    (task / "http-trace.jsonl").write_text(json.dumps({"stage": "http_send_entered"}) + "\n")
    result = summary.accounting(tmp_path)
    assert result["local_request_intents"] == result["live_http_send_entries"] == 1
    assert result["rows"][0]["unknown_effect"] is True
    assert result["input_tokens"] is result["output_tokens"] is result["estimated_cost_cny"] is None
    assert result["actual_bill_cny"] is None


def test_known_usage_is_only_an_estimate_without_a_bill(tmp_path):
    (tmp_path / "request.json").write_text(json.dumps({"request_id": "known", "request": {}}))
    (tmp_path / "response.json").write_text(json.dumps({"request_id": "provider-1", "usage": {
        "prompt_tokens": 1000, "completion_tokens": 500, "total_tokens": 1500}, "cached_input_tokens": None}))
    result = summary.accounting(tmp_path)
    assert result["estimated_cost_cny"] == 0.0018
    assert result["rows"][0]["cached_input_tokens"] is None
    assert result["actual_bill_cny"] is None
