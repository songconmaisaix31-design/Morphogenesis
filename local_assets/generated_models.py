"""Admission models for generated candidates (generated-isolation-v1).

Distinct from the literal-files ``ValidationReport`` chain: a generated
candidate is admitted by static security gates plus a *verified* isolation
report, never by byte-equality to a template. The frozen plan is carried as a
JSON string so it remains immutable and independently re-readable.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from contracts.base import Contract
from orchestration.experiments.generated import IsolationReport, StaticSecurityReport


class GeneratedValidationPolicy(Contract):
    schema_version: Literal["generated-experiment/v1"] = "generated-experiment/v1"
    version: str = Field(min_length=1, max_length=120)
    plan_json: str = Field(min_length=1)


class GeneratedValidationReport(Contract):
    report_id: str = Field(min_length=1, max_length=120)
    asset_id: str = Field(min_length=1, max_length=120)
    plan_json: str = Field(min_length=1)
    passed: bool
    reasons: tuple[str, ...] = ()
    static: StaticSecurityReport
    isolation: IsolationReport
    created_at: float
    expires_at: float
    policy_version: str = "generated-isolation-v1"


class GeneratedApproval(Contract):
    asset_id: str = Field(min_length=1, max_length=120)
    report_id: str = Field(min_length=1, max_length=120)
    policy_version: str = "generated-isolation-v1"
    proof_ref: str | None = Field(default=None, min_length=1, max_length=240)
