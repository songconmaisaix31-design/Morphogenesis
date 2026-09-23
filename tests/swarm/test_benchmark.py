"""Local source/scoring tests. Fixtures are synthetic and not benchmark examples."""

import json
import subprocess

from tools.run_swarm_benchmark import (
    BBH_REVISION,
    GSM8K_REVISION,
    BenchmarkExample,
    public_manifest,
    score_response,
    summarize,
)


def example(dataset="gsm8k"):
    return BenchmarkExample("fixture:0", dataset, "fixture", "synthetic question", "42" if dataset == "gsm8k" else "True")


def test_gsm8k_numeric_normalization_and_strict_json_contract():
    correct = score_response(example(), '{"answer":"42.0","adopted_asset_ids":[]}')
    malformed = score_response(example(), '{"answer":42}')
    assert correct.status == "correct" and correct.strict_json and correct.normalized_correct
    assert malformed.status == "malformed" and not malformed.strict_json


def test_bbh_uses_exact_case_sensitive_target_after_whitespace_normalization():
    assert score_response(example("bbh"), '{"answer":" True ","adopted_asset_ids":[]}').status == "correct"
    assert score_response(example("bbh"), '{"answer":"true","adopted_asset_ids":[]}').status == "incorrect"


def test_missing_duplicate_and_malformed_are_in_requested_denominator():
    scores = [score_response(example(), None), score_response(example(), '{"answer":"42"}', duplicate=True),
              score_response(example(), "not json"), score_response(example(), '{"answer":"0","adopted_asset_ids":[]}')]
    assert summarize(scores) == {"requested": 4, "correct": 0, "incorrect": 1, "malformed": 1,
                                 "missing": 1, "duplicate": 1, "accuracy": 0.0, "strict_json_rate": 0.25}


def test_public_manifest_excludes_questions_and_targets():
    manifest = public_manifest([example()], seed=7)
    rendered = json.dumps(manifest)
    assert manifest["sources"]["gsm8k"]["revision"] == GSM8K_REVISION
    assert manifest["sources"]["bbh"]["revision"] == BBH_REVISION
    assert "synthetic question" not in rendered and "42" not in rendered


def test_revision_guard_rejects_nonmatching_checkout(tmp_path, monkeypatch):
    from tools import run_swarm_benchmark as benchmark
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, "wrong\n", ""))
    try:
        benchmark._require_revision(tmp_path, GSM8K_REVISION)
    except ValueError as error:
        assert str(error) == "dataset_revision_mismatch"
    else:
        raise AssertionError("revision mismatch accepted")


def test_nonfinite_numeric_answers_are_incorrect_not_equal():
    response = '{"answer":"NaN","adopted_asset_ids":[]}'
    assert score_response(example(), response).status == "incorrect"
