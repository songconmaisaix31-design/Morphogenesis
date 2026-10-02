"""Host-owned trusted registries for criteria approval and isolation verification.

The evaluator and executor in this package are trusted *host* components, but
they must never grant a final verdict or execution admission from fields that a
candidate, a tool argument or a mock backend can write. Authoritative approval
therefore lives in host-owned registries constructed from service configuration:

- ``TrustedCriteriaRegistry`` records which evaluation criteria versions the host
  has independently approved (frozen template + approver + time). Two different
  templates for the same version are a construction error, never a silent
  overwrite.
- ``TrustedProbeRegistry`` records which isolation backends have a *real* harmless
  probe proving the declared capability set (AT-07). A probe is bound to its
  exact ``probe_id`` (the report's ``proof_ref``), backend and declared set — a
  missing or different reference can never consume the record.

These registries are immutable once constructed and are injected into the
executor/evaluator by the host; a candidate or tool cannot add records at run
time.
"""

from __future__ import annotations

from pydantic import Field

from contracts.base import Contract
from orchestration.experiments.generated import (
    EvaluationSpec, GeneratedAssessment, IsolationCapability, IsolationConfiguration, IsolationReport,
    effective_environment,
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
            existing = self._by_version.get(record.spec.version)
            if existing is not None and existing.template != record.template:
                raise ValueError("criteria_version_conflict")
            self._by_version[record.spec.version] = record

    def is_approved(self, spec: EvaluationSpec) -> bool:
        record = self._by_version.get(spec.version)
        if record is None:
            return False
        return record.template == spec.model_copy(update={"approved": False, "approved_by": None})

    def approver(self, version: str) -> str | None:
        record = self._by_version.get(version)
        return record.approved_by if record is not None else None

    def approval(self, spec: EvaluationSpec) -> TrustedCriteriaRecord | None:
        return self._by_version.get(spec.version) if self.is_approved(spec) else None


class IsolationProbeRecord(Contract):
    probe_id: str = Field(min_length=1, max_length=120)
    backend: str = Field(min_length=1, max_length=120)
    declared: IsolationCapability
    image_digest: str | None = Field(default=None, pattern=r"^sha256:[a-f0-9]{64}$")
    verified: bool
    passed: bool
    evidence_ref: str = Field(min_length=1, max_length=240)
    probed_at: float
    configuration: IsolationConfiguration | None = None


class TrustedProbeRegistry:
    def __init__(self, records: tuple[IsolationProbeRecord, ...] = ()) -> None:
        self._by_probe_id: dict[str, IsolationProbeRecord] = {}
        for record in records:
            record = IsolationProbeRecord.model_validate_json(record.model_dump_json())
            existing = self._by_probe_id.get(record.probe_id)
            if existing is not None and existing != record:
                raise ValueError("probe_id_conflict")
            self._by_probe_id[record.probe_id] = record

    def is_verified(self, isolation: IsolationReport) -> bool:
        if not isolation.proof_ref:
            return False
        record = self._by_probe_id.get(isolation.proof_ref)
        if record is None or record.configuration is None or isolation.configuration is None:
            return False
        try:
            environment = effective_environment(isolation.configuration.environment)
        except ValueError:
            return False
        return (record.verified and record.passed
                and record.backend == isolation.backend
                and record.declared == isolation.declared
                and record.configuration == isolation.configuration
                and record.image_digest == environment.image_digest
                and record.configuration.environment == environment)


def finalize_assessment(assessment: GeneratedAssessment, *, spec: EvaluationSpec,
                        registry: TrustedCriteriaRegistry | None,
                        execution_state: str, remote_effect: str) -> GeneratedAssessment:
    """Grant a final (still not accepted) scientific verdict only from host authority.

    ``mode="final"`` and ``trusted=True`` require a host-approved criteria
    version AND a known external effect AND successful execution. The diagnostic
    path clears ``trusted`` and resets ``contribution`` to ``proposed`` so a
    diagnostic can never retain final scientific authority. Accepting a
    contribution remains a separate, independently reviewed step (track C) that
    binds a ``proof_ref`` to an original ledger fact.
    """
    approved = registry is not None and registry.is_approved(spec)
    if execution_state == "succeeded" and remote_effect == "known" and approved:
        return assessment.model_copy(update={"mode": "final", "trusted": True, "contribution": "proposed"})
    return assessment.model_copy(update={"mode": "diagnostic", "trusted": False, "contribution": "proposed"})
