"""Host-owned trusted registries for criteria approval and isolation verification.

The evaluator and executor in this package are trusted *host* components, but
they must never grant a final verdict or execution admission from fields that a
candidate, a tool argument or a mock backend can write. Authoritative approval
therefore lives in host-owned registries constructed from service configuration:

- ``TrustedCriteriaRegistry`` records which evaluation criteria versions the host
  has independently approved (frozen template + approver + time).
- ``TrustedProbeRegistry`` records which isolation backends have a *real* harmless
  probe proving the declared capability set (AT-07); a declared capability or a
  mock boolean is never a proof.

These registries are immutable once constructed and are injected into the
executor/evaluator by the host; a candidate or tool cannot add records at run
time.
"""

from __future__ import annotations

from pydantic import Field

from contracts.base import Contract
from orchestration.experiments.generated import (
    EvaluationSpec, GeneratedAssessment, IsolationCapability, IsolationReport,
)


class TrustedCriteriaRecord(Contract):
    spec: EvaluationSpec
    approved_by: str = Field(min_length=1, max_length=120)
    approved_at: float

    @property
    def template(self) -> EvaluationSpec:
        return self.spec.model_copy(update={"approved": False, "approved_by": None})


class TrustedCriteriaRegistry:
    def __init__(self, records: tuple[TrustedCriteriaRecord, ...] = ()) -> None:
        self._by_version: dict[str, TrustedCriteriaRecord] = {}
        for record in records:
            self._by_version[record.spec.version] = record

    def is_approved(self, spec: EvaluationSpec) -> bool:
        record = self._by_version.get(spec.version)
        if record is None:
            return False
        return record.template == spec.model_copy(update={"approved": False, "approved_by": None})

    def approver(self, version: str) -> str | None:
        record = self._by_version.get(version)
        return record.approved_by if record is not None else None


class IsolationProbeRecord(Contract):
    probe_id: str = Field(min_length=1, max_length=120)
    backend: str = Field(min_length=1, max_length=120)
    declared: IsolationCapability
    verified: bool
    passed: bool
    evidence_ref: str = Field(min_length=1, max_length=240)
    probed_at: float


class TrustedProbeRegistry:
    def __init__(self, records: tuple[IsolationProbeRecord, ...] = ()) -> None:
        self._by_backend: dict[str, IsolationProbeRecord] = {}
        for record in records:
            self._by_backend[record.backend] = record

    def is_verified(self, isolation: IsolationReport) -> bool:
        record = self._by_backend.get(isolation.backend)
        if record is None:
            return False
        return record.verified and record.passed and record.declared == isolation.declared


def finalize_assessment(assessment: GeneratedAssessment, *, spec: EvaluationSpec,
                        registry: TrustedCriteriaRegistry | None,
                        execution_state: str, remote_effect: str) -> GeneratedAssessment:
    """Grant a final (still not accepted) scientific verdict only from host authority.

    ``mode="final"`` requires a host-approved criteria version AND a known
    external effect AND successful execution. ``contribution`` is deliberately
    left untouched: accepting a contribution is a separate, independently
    reviewed step (track C) that binds a ``proof_ref`` to an original ledger fact.
    """
    approved = registry is not None and registry.is_approved(spec)
    if assessment.trusted and execution_state == "succeeded" and remote_effect == "known" and approved:
        return assessment.model_copy(update={"mode": "final"})
    return assessment.model_copy(update={"mode": "diagnostic"})
