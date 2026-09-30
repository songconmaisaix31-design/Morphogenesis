"""Trusted host calculation, independent of experiment code and claimed metrics."""

from __future__ import annotations

from fractions import Fraction
import json
import math

from orchestration.experiments.models import ExperimentPlan, ScientificAssessment


NIST_DATA_SHA256 = "ca310dc767f5130f980f8280bbe69e26ba414a4d85a89fc11b6c767b828e5fe4"


def observations(raw: bytes) -> list[Fraction]:
    text = raw.decode("ascii")
    values = [Fraction(line.strip()) for line in text.splitlines()[60:] if line.strip()]
    if len(values) != 1001 or set(values) != {Fraction("10000000.1"), Fraction("10000000.2"), Fraction("10000000.3")}:
        raise ValueError("nist_data_conditions_mismatch")
    return values


def assess(plan: ExperimentPlan, raw_input: bytes, raw_output: bytes) -> ScientificAssessment:
    """Recompute exact sample statistics and every residual from original input."""
    try:
        values = observations(raw_input)
        if plan.parameters == ("reverse",):
            values.reverse()
        mean = sum(values, Fraction(0)) / len(values)
        variance = sum(((value - mean) ** 2 for value in values), Fraction(0)) / (len(values) - 1)
        if variance != Fraction("0.01"):
            raise ValueError("certified_variance_mismatch")
        output = json.loads(raw_output)
        if not isinstance(output, dict) or set(output) != {"count", "mean", "sample_variance", "naive_variance", "residuals"}:
            raise ValueError("output_schema_mismatch")
        if type(output["count"]) is not int or output["count"] != len(values):
            raise ValueError("observation_count_mismatch")
        for key in ("mean", "sample_variance", "naive_variance"):
            if type(output[key]) not in (int, float) or not math.isfinite(output[key]):
                raise ValueError("nonfinite_or_nonnumeric_metric")
        residuals = output["residuals"]
        if not isinstance(residuals, list) or len(residuals) != len(values):
            raise ValueError("raw_residuals_missing")
        for value, residual in zip(values, residuals, strict=True):
            if (type(residual) not in (int, float) or not math.isfinite(residual) or
                    abs(residual - float(value - mean)) > plan.criteria.residual_absolute_tolerance):
                raise ValueError("raw_residual_mismatch")
        float_values = [float(value) for value in values]
        naive = (sum(value * value for value in float_values) - sum(float_values) ** 2 / len(values)) / (len(values) - 1)
        if output["naive_variance"] != naive:
            raise ValueError("naive_control_mismatch")
        mean_error = abs(output["mean"] - float(mean))
        variance_error = abs(output["sample_variance"] - float(variance))
        reasons = tuple(reason for failed, reason in (
            (mean_error > plan.criteria.mean_absolute_tolerance, "mean_accuracy_failed"),
            (variance_error > plan.criteria.variance_absolute_tolerance, "variance_accuracy_failed"),
        ) if failed)
        return ScientificAssessment(verdict="failed" if reasons else "passed", reasons=reasons,
            metrics={"mean_absolute_error": mean_error, "variance_absolute_error": variance_error,
                     "naive_variance_absolute_error": abs(naive - float(variance)),
                     "sample_variance": output["sample_variance"]})
    except (ValueError, TypeError, KeyError, UnicodeError, OverflowError) as error:
        return ScientificAssessment(verdict="failed", reasons=(str(error),))
