"""Project-owned synthetic OLS case; exact host arithmetic, no candidate imports."""

import csv
from fractions import Fraction
import hashlib
import io
import json
import math

from orchestration.experiments.models import CaseId, ExperimentPlan, LinearRegressionCriteria, ScientificAssessment

DATA = b"x,y\n-3,-2.25\n-2,-1.25\n-1,0.5\n0,2\n1,3.5\n2,4.75\n3,6.75\n"
DATA_SHA256 = hashlib.sha256(DATA).hexdigest()


def observations(raw: bytes) -> list[tuple[Fraction, Fraction]]:
    rows = list(csv.reader(io.StringIO(raw.decode("ascii"))))
    if not rows or rows[0] != ["x", "y"] or len(rows) != 8 or any(len(row) != 2 for row in rows[1:]):
        raise ValueError("synthetic_input_schema_mismatch")
    points = [(Fraction(x), Fraction(y)) for x, y in rows[1:]]
    if [x for x, _ in points] != [Fraction(x) for x in range(-3, 4)]:
        raise ValueError("synthetic_input_conditions_mismatch")
    # Fixed raw input identity is independently checked as well as the row conditions.
    if hashlib.sha256(raw).hexdigest() != DATA_SHA256:
        raise ValueError("synthetic_input_digest_mismatch")
    return points


def assess(plan: ExperimentPlan, raw_input: bytes, raw_output: bytes) -> ScientificAssessment:
    version: CaseId = "synthetic-linear-regression-v1"
    try:
        if not isinstance(plan.criteria, LinearRegressionCriteria) or plan.parameters != ("original",):
            raise ValueError("synthetic_criteria_or_order_mismatch")
        points = observations(raw_input)
        count = len(points)
        mean_x = sum((x for x, _ in points), Fraction(0)) / count
        mean_y = sum((y for _, y in points), Fraction(0)) / count
        xx = sum(((x - mean_x) ** 2 for x, _ in points), Fraction(0))
        if not xx:
            raise ValueError("singular_input")
        slope = sum(((x - mean_x) * (y - mean_y) for x, y in points), Fraction(0)) / xx
        intercept = mean_y - slope * mean_x
        residuals = [y - (slope * x + intercept) for x, y in points]
        sse = sum((r * r for r in residuals), Fraction(0))
        if slope != Fraction(3, 2) or intercept != 2 or sse != Fraction(1, 4):
            raise ValueError("predeclared_ols_conditions_mismatch")
        output = json.loads(raw_output)
        if not isinstance(output, dict) or set(output) != {"count", "slope", "intercept", "residuals", "sse"}:
            raise ValueError("output_schema_mismatch")
        if type(output["count"]) is not int or output["count"] != count:
            raise ValueError("observation_count_mismatch")
        for name in ("slope", "intercept", "sse"):
            if type(output[name]) not in (int, float) or not math.isfinite(output[name]):
                raise ValueError("nonfinite_or_nonnumeric_metric")
        reported = output["residuals"]
        if not isinstance(reported, list) or len(reported) != count:
            raise ValueError("raw_residuals_missing")
        for value, expected in zip(reported, residuals, strict=True):
            if (type(value) not in (int, float) or not math.isfinite(value)
                    or abs(value - float(expected)) > plan.criteria.residual_absolute_tolerance):
                raise ValueError("raw_residual_mismatch")
        errors = {"slope_absolute_error": abs(output["slope"] - float(slope)),
                  "intercept_absolute_error": abs(output["intercept"] - float(intercept)),
                  "sse_absolute_error": abs(output["sse"] - float(sse))}
        reasons = tuple(name + "_failed" for name, error in errors.items()
                        if error > (plan.criteria.sse_absolute_tolerance if name == "sse_absolute_error"
                                    else plan.criteria.coefficient_absolute_tolerance))
        return ScientificAssessment(criteria_version=version, verdict="failed" if reasons else "passed",
                                    reasons=reasons, metrics={**errors, "sum_squared_error": output["sse"]})
    except (ValueError, TypeError, KeyError, UnicodeError, OverflowError) as error:
        return ScientificAssessment(criteria_version=version, verdict="failed", reasons=(str(error),))
