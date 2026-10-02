"""Trusted host recomputation of generated-candidate output.

The evaluator reads only the frozen ``EvaluationSpec`` from the plan and the
candidate's *raw output*, recomputing every metric from first principles. It
never trusts a candidate-reported score: the output schema is strict, and any
extra field (such as ``score`` or ``passed``) is rejected as a schema mismatch.
A valid-but-refuted output is a legitimate negative result; a crash or invalid
output is ``inconclusive``, never ``refuted``.
"""

from __future__ import annotations

import json
import math
from typing import Literal

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


def _reference(x: float) -> float:
    return math.sin(math.pi * x)


def evaluate_poisson(spec: EvaluationSpec, xs: list[float], us: list[float]) -> tuple[HypothesisAxis, dict[str, float], list[str]]:
    errors = [abs(u - _reference(x)) for x, u in zip(xs, us, strict=True)]
    max_abs_error = max(errors)
    boundary_error = max(abs(us[0]), abs(us[-1]))
    reasons: list[str] = []
    if max_abs_error > spec.max_abs_tolerance:
        reasons.append("max_abs_error_exceeds_tolerance")
    if boundary_error > spec.boundary_tolerance:
        reasons.append("boundary_error_exceeds_tolerance")
    hypothesis: HypothesisAxis = "refuted" if reasons else "supported"
    return hypothesis, {"max_absolute_error": max_abs_error, "boundary_error": boundary_error}, reasons


def _generic_checks(spec: EvaluationSpec, xs: list[float], us: list[float]) -> tuple[bool, list[str]]:
    # Generic property template: each named property is applied with the frozen
    # tolerances. A candidate cannot register a new property string as a trusted
    # criterion; only the approved template names are honored.
    reasons: list[str] = []
    ok = True
    for name in spec.properties:
        if name == "finite":
            if not all(math.isfinite(u) for u in us):
                ok = False
                reasons.append("nonfinite_output")
        elif name == "boundary":
            if max(abs(us[0]), abs(us[-1])) > spec.boundary_tolerance:
                ok = False
                reasons.append("boundary_property_failed")
        elif name == "symmetric":
            if max(abs(a - b) for a, b in zip(us, reversed(us))) > spec.max_abs_tolerance:
                ok = False
                reasons.append("symmetry_property_failed")
        elif name == "range":
            if any(not -spec.max_abs_tolerance <= u <= 1.0 + spec.max_abs_tolerance for u in us):
                ok = False
                reasons.append("range_property_failed")
        elif name == "concave":
            second = [us[i - 1] - 2 * us[i] + us[i + 1] for i in range(1, len(us) - 1)]
            if any(d > spec.max_abs_tolerance for d in second):
                ok = False
                reasons.append("concavity_property_failed")
        else:
            ok = False
            reasons.append("unknown_property:" + name)
    return ok, reasons


def evaluate_generic(spec: EvaluationSpec, xs: list[float], us: list[float]) -> tuple[HypothesisAxis, dict[str, float], list[str]]:
    ok, reasons = _generic_checks(spec, xs, us)
    hypothesis: HypothesisAxis = "supported" if ok else "refuted"
    return hypothesis, {"max_absolute_value": max(abs(u) for u in us)}, reasons


def evaluate(plan: GeneratedExperimentPlan, raw_output: bytes, *, reviewer_independent: bool) -> GeneratedAssessment:
    """Recompute the three-axis scientific assessment from raw output only."""
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
    mode: Literal["diagnostic", "final"] = "final" if spec.approved and reviewer_independent else "diagnostic"
    return GeneratedAssessment(
        execution="succeeded", hypothesis=hypothesis, contribution="proposed",
        mode=mode, trusted=True, evaluator_version=spec.version,
        reasons=tuple(reasons), metrics=metrics,
    )
