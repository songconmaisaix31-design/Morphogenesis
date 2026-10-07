"""Protect the measurement boundaries, including unfavorable and missing pairs."""
import importlib.util
from pathlib import Path

import pytest


def load(name):
    path = Path(__file__).resolve().parents[2] / "tools" / "morphbench" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


stats = load("summarize")
runner = load("run_local")


def test_paired_bootstrap_preserves_negative_gain_and_pairs_by_seed():
    result = stats.paired({0: 0.1, 1: 0.2, 9: 100.0}, {0: 0.3, 1: 0.4, 8: -100.0})
    assert result["seeds"] == [0, 1]
    assert result["mean"] == pytest.approx(-0.2)
    assert result["ci95"] == pytest.approx([-0.2, -0.2])
    assert result["sign_flip_p"] == 0.5


def test_missing_pairs_do_not_become_zero_or_five_samples():
    result = stats.paired({0: 2}, {1: 3})
    assert result["n"] == 0
    assert result["mean"] is None
    assert result["ci95"] is None
    assert stats.estimate([1])["se"] is None


def test_exact_five_pair_test_cannot_claim_small_two_sided_p_value():
    result = stats.paired(dict.fromkeys(range(5), 1.0), dict.fromkeys(range(5), 0.0))
    assert result["sign_flip_p"] == 2 / 32
    assert result["ci95"] == [1.0, 1.0]


def test_fdr_restores_original_order_and_monotonicity():
    assert stats.bh_adjust([0.2, 0.01, 0.03]) == pytest.approx([0.2, 0.03, 0.045])


def test_worker_energy_is_global_total_and_rejects_empty_workers():
    assert runner.split_energy(8, 3) == [3, 3, 2]
    assert sum(runner.split_energy(8, 3)) == 8
    with pytest.raises(ValueError):
        runner.split_energy(2, 3)


def test_partial_trial_not_silently_included_in_matched_budget(tmp_path):
    import json
    for system, status, score in [("MorphSwarm", "INCOMPLETE_budget_not_completed", 99.0), ("SingleAgent", "PASS_local_trial", 0.3)]:
        directory = tmp_path / f"BM-01-s0-{system}"
        directory.mkdir()
        data = dict(task="BM-01", seed=0, system=system, status=status, test_score=score,
                    search_wall_seconds=1, evaluations_finished=1, duplicate_evaluations=0,
                    setup_evaluations=0, test_evaluations=1)
        (directory / "result.json").write_text(json.dumps(data))
    report = stats.summarize(tmp_path)
    morph = next(g for g in report["groups"] if g["system"] == "MorphSwarm")
    assert morph["complete_trials"] == 0
    assert morph["observed_test_score_including_partial"]["mean"] == 99.0
    assert all(row["n"] == 0 for row in report["paired_contrasts"])
    allowance = report["fixed_allowance_paired_contrasts"][0]
    assert allowance["n"] == 1
    assert allowance["mean"] == pytest.approx(98.7)


def test_expected_coverage_distinguishes_first_exception_and_not_run(tmp_path):
    import json
    (tmp_path / "arguments.json").write_text(json.dumps({"tasks": ["BM-01"], "seeds": [0],
        "systems": ["SingleAgent", "MorphSwarm"]}))
    failed = tmp_path / "BM-01-s0-SingleAgent"
    failed.mkdir()
    (failed / "failure.json").write_text('{"exception":"first failure"}')
    report = stats.summarize(tmp_path)
    coverage = report["coverage"]
    assert (coverage["expected"], coverage["observed"], coverage["missing_count"]) == (2, 0, 2)
    assert [r["status"] for r in coverage["missing"]] == ["FAIL_no_result", "NOT_RUN"]
    assert "no independent test set" in stats.markdown(report)
