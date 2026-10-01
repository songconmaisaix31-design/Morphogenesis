"""Trusted registered judges; legacy NIST imports remain available."""

from orchestration.experiments.case import get_case
from orchestration.experiments.models import ExperimentPlan, ScientificAssessment
from orchestration.experiments.nist import NIST_DATA_SHA256 as NIST_DATA_SHA256, observations as observations


def assess(plan: ExperimentPlan, raw_input: bytes, raw_output: bytes) -> ScientificAssessment:
    return get_case(plan.criteria.version).assess(plan, raw_input, raw_output)
