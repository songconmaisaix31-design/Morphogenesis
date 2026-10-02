"""Trusted evaluator unit tests: diagnostic-only recompute, refute-vs-crash, self-score denial."""

import json
import math

import pytest
from pydantic import ValidationError

from orchestration.experiments.evaluation import evaluate
from orchestration.experiments.generated import EvaluationSpec
from tests.experiments.generated_helpers import make_poisson_plan, uniform_x


def _output(n_intervals: int, us=None):
    xs = uniform_x(n_intervals)
    if us is None:
        us = [math.sin(math.pi * x) for x in xs]
    return json.dumps({"x": xs, "u": us}).encode()


def test_poisson_reference_supported_is_diagnostic():
    plan = make_poisson_plan(n_intervals=50, approved=True)
    assessment = evaluate(plan, _output(50), reviewer_independent=True)
    assert assessment.hypothesis == "supported"
    assert assessment.trusted is False
    assert assessment.mode == "diagnostic"
    assert assessment.contribution == "proposed"
    assert assessment.metrics["max_absolute_error"] < 1e-6


def test_poisson_reference_refuted():
    plan = make_poisson_plan(n_intervals=50)
    assessment = evaluate(plan, _output(50, us=[0.5] * 51), reviewer_independent=True)
    assert assessment.hypothesis == "refuted"
    assert assessment.execution == "succeeded"
    assert assessment.contribution == "proposed"


def test_invalid_schema_is_inconclusive_not_refuted():
    plan = make_poisson_plan(n_intervals=50)
    assessment = evaluate(plan, b"{}", reviewer_independent=True)
    assert assessment.hypothesis == "inconclusive"
    assert "output_schema_mismatch" in assessment.reasons


def test_self_reported_score_never_trusted():
    plan = make_poisson_plan(n_intervals=50)
    body = json.loads(_output(50))
    body["score"] = 1.0
    body["passed"] = True
    assessment = evaluate(plan, json.dumps(body).encode(), reviewer_independent=True)
    assert assessment.hypothesis == "inconclusive"
    assert assessment.mode == "diagnostic"
    assert assessment.contribution != "accepted"


def test_caller_approved_boolean_cannot_grant_final():
    plan = make_poisson_plan(n_intervals=50, approved=True)
    assessment = evaluate(plan, _output(50), reviewer_independent=True)
    assert assessment.mode == "diagnostic"
    assert assessment.contribution != "accepted"


def test_generic_empty_properties_rejected_at_construction():
    with pytest.raises(ValidationError):
        EvaluationSpec(version="g", kind="generic_property_v1", properties=())


def test_generic_unknown_property_is_inconclusive():
    plan = make_poisson_plan(n_intervals=50)
    plan = plan.model_copy(update={"evaluation": plan.evaluation.model_copy(update={
        "version": "g-v1", "kind": "generic_property_v1", "properties": ("finite", "madeup"),
    })})
    assessment = evaluate(plan, _output(50), reviewer_independent=True)
    assert assessment.hypothesis == "inconclusive"
    assert any("unknown_property" in reason for reason in assessment.reasons)


def test_generic_property_template_supported_and_refuted():
    plan = make_poisson_plan(n_intervals=50)
    plan = plan.model_copy(update={"evaluation": plan.evaluation.model_copy(update={
        "version": "g-v1", "kind": "generic_property_v1", "properties": ("finite", "boundary", "symmetric"),
    })})
    supported = evaluate(plan, _output(50), reviewer_independent=True)
    assert supported.hypothesis == "supported"
    refuted = evaluate(plan, _output(50, us=[2.0] * 51), reviewer_independent=True)
    assert refuted.hypothesis == "refuted"
