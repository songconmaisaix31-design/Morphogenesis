"""Trusted evaluator unit tests: recompute, refute-vs-crash, self-score denial."""

import json

from orchestration.experiments.evaluation import evaluate
from tests.experiments.generated_helpers import make_poisson_plan


def _output(n_intervals: int, us=None):
    h = 1.0 / n_intervals
    xs = [i * h for i in range(n_intervals + 1)]
    if us is None:
        import math
        us = [math.sin(math.pi * x) for x in xs]
    return json.dumps({"x": xs, "u": us}).encode()


def test_poisson_reference_supported():
    plan = make_poisson_plan(n_intervals=50, approved=True)
    assessment = evaluate(plan, _output(50), reviewer_independent=True)
    assert assessment.hypothesis == "supported"
    assert assessment.trusted is True
    assert assessment.mode == "final"
    assert assessment.metrics["max_absolute_error"] < 1e-6


def test_poisson_reference_refuted():
    plan = make_poisson_plan(n_intervals=50, approved=True)
    us = [0.5] * 51
    assessment = evaluate(plan, _output(50, us=us), reviewer_independent=True)
    assert assessment.hypothesis == "refuted"
    assert assessment.execution == "succeeded"
    assert assessment.contribution == "proposed"


def test_invalid_schema_is_inconclusive_not_refuted():
    plan = make_poisson_plan(n_intervals=50)
    assessment = evaluate(plan, b"{}", reviewer_independent=True)
    assert assessment.hypothesis == "inconclusive"
    assert "output_schema_mismatch" in assessment.reasons


def test_unapproved_evaluator_diagnostic():
    plan = make_poisson_plan(n_intervals=50, approved=False)
    assessment = evaluate(plan, _output(50), reviewer_independent=True)
    assert assessment.hypothesis == "supported"
    assert assessment.mode == "diagnostic"


def test_non_independent_reviewer_diagnostic():
    plan = make_poisson_plan(n_intervals=50, approved=True)
    assessment = evaluate(plan, _output(50), reviewer_independent=False)
    assert assessment.mode == "diagnostic"


def test_generic_property_template():
    plan = make_poisson_plan(n_intervals=50, approved=True)
    plan = plan.model_copy(update={"evaluation": plan.evaluation.model_copy(update={
        "kind": "generic_property_v1", "properties": ("finite", "boundary", "symmetric", "range"),
    })})
    assessment = evaluate(plan, _output(50), reviewer_independent=True)
    assert assessment.hypothesis == "supported"
    bad = plan.model_copy(update={"evaluation": plan.evaluation.model_copy(update={
        "properties": ("finite", "range"),
    })})
    assessment = evaluate(bad, _output(50, us=[2.0] * 51), reviewer_independent=True)
    assert assessment.hypothesis == "refuted"
