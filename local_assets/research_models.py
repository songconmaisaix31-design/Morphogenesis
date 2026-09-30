"""Scientific metadata on the existing asset and report chain, not a scheduler."""
from typing import Literal

from pydantic import Field

from contracts.base import Contract
from contracts.identity import AttemptId


class ResearchClaim(Contract):
    plan_id: str = Field(min_length=1)
    criterion_version: str = Field(min_length=1)
    conditions: dict[str, str] = Field(min_length=1)
    sources: tuple[str, ...] = Field(min_length=1)


class ResearchObservation(Contract):
    report_id: str
    asset_id: str
    task_id: str
    worker_id: str
    fencing_token: int = Field(gt=0)
    run_id: str
    sandbox_id: str | None
    plan_id: str
    criterion_version: str
    conditions: dict[str, str]
    plan_json: str
    candidate_json: str
    result_json: str
    provenance: Literal["live", "replay", "mock"]
    purpose: Literal["original", "reproduction", "inheritance", "counterexample"]
    execution_state: str
    scientific_verdict: Literal["passed", "failed", "not_evaluated"]
    reasons: tuple[str, ...] = ()
    created_at: float
    source_swarm_id: str | None = None
    source_fencing_token: int | None = Field(default=None, gt=0)
    source_attempt: AttemptId | None = None
