"""Trusted host recomputation of generated-candidate output (diagnostic only).

The evaluator reads only the frozen ``EvaluationSpec`` from the plan and the
candidate's *raw output*, recomputing every metric from first principles. It
never trusts a candidate-reported score and never grants a final verdict: the
returned assessment is always ``mode="diagnostic"`` and ``contribution="proposed"``
until a host-owned ``TrustedCriteriaRegistry`` explicitly finalizes it (see
``trusted.finalize_assessment``). A valid-but-refuted output is a legitimate
negative result; a crash or invalid/unknown output is ``inconclusive``, never
``refuted``.
"""

from __future__ import annotations

import json
import math

from orchestration.experiments.generated import (
    EvaluationSpec, GeneratedAssessment, GeneratedExperimentPlan, HypothesisAxis,
)

_EPS = 1e-9


def _parse_grid(spec: EvaluationSpec, raw_output: bytes) -> tuple[list[float], list[float]]:
    output = json.loads(raw_output)
    if not isinstance(output, dict) or set(output) != {"x", "u"}:
        raise ValueError("output_schema_mismatch")
    xs = output["x"]
    us = output["u"]
    n = spec.n_intervals
    if (not isinstance(xs, list) or not isinstance(us, list)
            or len(xs) != n + 1 or len(us) != n + 1):
        raise ValueError("grid_arity_mismatch")
    width = (spec.x_right - spec.x_left) / n
    for index, (x, u) in enumerate(zip(xs, us, strict=True)):
        if (type(x) not in (int, float) or type(u) not in (int, float)
                or not math.isfinite(float(x)) or not math.isfinite(float(u))):
            raise ValueError("nonfinite_or_nonnumeric_output")
        expected = spec.x_left + index * width
        if not math.isclose(float(x), expected, rel_tol=_EPS, abs_tol=_EPS):
            raise ValueError("grid_point_off_spec")
    return [float(x) for x in xs], [float(u) for u in us]


def _reference(spec: EvaluationSpec, x: float) -> float:
    if spec.reference != "sin_pi_x":
        raise ValueError("unknown_reference:" + spec.reference)
    return math.sin(math.pi * x)


def evaluate_poisson(spec: EvaluationSpec, xs: list[float], us: list[float]) -> tuple[HypothesisAxis, dict[str, float], list[str]]:
    errors = [abs(u - _reference(spec, x)) for x, u in zip(xs, us, strict=True)]
    max_abs_error = max(errors)
    boundary_error = max(abs(us[0]), abs(us[-1]))
    reasons: list[str] = []
    if max_abs_error > spec.max_abs_tolerance:
        reasons.append("max_abs_error_exceeds_tolerance")
    if boundary_error > spec.boundary_tolerance:
        reasons.append("boundary_error_exceeds_tolerance")
    hypothesis: HypothesisAxis = "refuted" if reasons else "supported"
    return hypothesis, {"max_absolute_error": max_abs_error, "boundary_error": boundary_error}, reasons


def _property_ok(spec: EvaluationSpec, name: str, us: list[float]) -> bool:
    if name == "finite":
        return all(math.isfinite(u) for u in us)
    if name == "boundary":
        return max(abs(us[0]), abs(us[-1])) <= spec.boundary_tolerance
    if name == "symmetric":
        return max(abs(a - b) for a, b in zip(us, reversed(us))) <= spec.max_abs_tolerance
    if name == "range":
        return all(-spec.max_abs_tolerance <= u <= 1.0 + spec.max_abs_tolerance for u in us)
    if name == "concave":
        second = [us[i - 1] - 2 * us[i] + us[i + 1] for i in range(1, len(us) - 1)]
        return all(d <= spec.max_abs_tolerance for d in second)
    raise ValueError("unknown_property:" + name)


def evaluate_generic(spec: EvaluationSpec, xs: list[float], us: list[float]) -> tuple[HypothesisAxis, dict[str, float], list[str]]:
    # A generic template must be explicit: an empty property set is rejected by
    # the model, and an unknown property is invalid (inconclusive), never refuted.
    if not spec.properties:
        return "inconclusive", {}, ["empty_property_template"]
    reasons: list[str] = []
    try:
        for name in spec.properties:
            if not _property_ok(spec, name, us):
                reasons.append(name + "_property_failed")
    except ValueError as error:
        return "inconclusive", {}, [str(error)]
    hypothesis: HypothesisAxis = "refuted" if reasons else "supported"
    return hypothesis, {"max_absolute_value": max(abs(u) for u in us)}, reasons


def evaluate(plan: GeneratedExperimentPlan, raw_output: bytes, *,
             reviewer_independent: bool = False) -> GeneratedAssessment:
    """Recompute the three-axis scientific assessment from raw output only.

    ``reviewer_independent`` is accepted for interface compatibility but is
    deliberately ignored: independence and finality are host-owned facts, never
    a caller boolean. The result is always diagnostic and proposed.
    """
    spec = plan.evaluation
    try:
        xs, us = _parse_grid(spec, raw_output)
    except (ValueError, TypeError, KeyError, UnicodeError, OverflowError) as error:
        return GeneratedAssessment(
            execution="succeeded", hypothesis="inconclusive", contribution="proposed",
            mode="diagnostic", trusted=True, evaluator_version=spec.version,
            reasons=(str(error),),
        )
    if spec.kind == "poisson_reference_v1":
        hypothesis, metrics, reasons = evaluate_poisson(spec, xs, us)
    else:
        hypothesis, metrics, reasons = evaluate_generic(spec, xs, us)
    return GeneratedAssessment(
        execution="succeeded", hypothesis=hypothesis, contribution="proposed",
        mode="diagnostic", trusted=True, evaluator_version=spec.version,
        reasons=tuple(reasons), metrics=metrics,
    )
