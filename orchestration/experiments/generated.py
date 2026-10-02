"""Versioned generated-candidate experiment contracts (generated-experiment/v1).

These models describe the *dynamic* computation mode added for Research Swarm
Alpha R1. They coexist with the frozen ``registered_case`` contracts in
``models.py`` and never change the byte-equality semantics of the original two
cases. A generated candidate is untrusted by definition: its plan, environment,
evaluation criteria, authorization and resources are all frozen before any
output is produced, and the candidate author is never granted trusted-criteria
write authority (the evaluation spec is host-owned and immutable once built).
"""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Literal

from pydantic import Field, JsonValue, field_validator, model_validator

from contracts.base import Contract
from orchestration.experiments.models import ExperimentArtifact

SchemaVersion = Literal["generated-experiment/v1"]
OutputSchema = Literal["generated-output/v1"]

ExecutionAxis = Literal["not_run", "running", "succeeded", "failed", "cancelled", "unknown"]
HypothesisAxis = Literal["not_evaluated", "supported", "refuted", "inconclusive", "disputed"]
ContributionAxis = Literal["proposed", "accepted", "rejected", "superseded"]


class GeneratedSource(Contract):
    """An attributed origin for a candidate: paper, discussion, hypothesis, prior result."""

    kind: Literal["paper", "discussion", "hypothesis", "prior_result"]
    ref: str = Field(min_length=1, max_length=2048)
    locator: str = Field(default="", max_length=512)
    title: str = Field(default="", max_length=512)


class GeneratedFile(Contract):
    """One immutable code-manifest entry with a standard-library digest."""

    name: str = Field(min_length=1, max_length=240)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=1, le=1048576, strict=True)
    source: str = Field(min_length=1, max_length=2048)

    @field_validator("name")
    @classmethod
    def relative_file(cls, value: str) -> str:
        path = PurePosixPath(value)
        if (path.is_absolute() or not value or "\\" in value or ":" in value
                or any(part in {"", ".", ".."} for part in value.split("/"))):
            raise ValueError("relative generated file required")
        return value


class ApprovedEnvironment(Contract):
    """Approved image, runtime and dependency-lock identity; never derived from the candidate."""

    image: str = Field(min_length=1, max_length=512)
    python_version: Literal["3.12"] = "3.12"
    sdk_version: Literal["1.1.0"] = "1.1.0"
    backend: Literal["opensandbox"] = "opensandbox"
    dependency_lock_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    dependencies: tuple[str, ...] = Field(default_factory=tuple, max_length=256)

    @field_validator("image")
    @classmethod
    def pinned_image(cls, value: str) -> str:
        if (not value or any(ch.isspace() for ch in value) or
                ("@sha256:" not in value and ":" not in value.rsplit("/", 1)[-1]) or
                value.endswith(":latest")):
            raise ValueError("explicit image version or digest required")
        return value


class NetworkPolicy(Contract):
    default: Literal["deny"] = "deny"


class BackendProfile(Contract):
    """Bounded CPU backend request: cpu/memory/process/time and a deny-by-default network."""

    backend: Literal["opensandbox"] = "opensandbox"
    cpu: int = Field(default=1, ge=1, le=2, strict=True)
    memory_mib: int = Field(default=512, ge=256, le=2048, strict=True)
    lifetime_seconds: int = Field(default=180, ge=30, le=900, strict=True)
    command_seconds: int = Field(default=30, ge=1, le=300, strict=True)
    artifact_bytes: int = Field(default=1048576, ge=1024, le=16777216, strict=True)
    process_limit: int = Field(default=16, ge=1, le=1024, strict=True)
    network: NetworkPolicy = Field(default_factory=NetworkPolicy)

    @model_validator(mode="after")
    def lifetime_bounds_command(self) -> BackendProfile:
        if self.command_seconds >= self.lifetime_seconds:
            raise ValueError("command duration must be below sandbox lifetime")
        return self


class EvaluationSpec(Contract):
    """Frozen, host-owned evaluation criteria. ``approved=False`` means diagnostic only.

    The candidate may *propose* standards but never holds write authority over a
    trusted criterion version. Until an independent review approves the version,
    any trusted recomputation is reported as ``diagnostic`` and cannot set a final
    hypothesis or contribution state.
    """

    version: str = Field(min_length=1, max_length=120)
    kind: Literal["poisson_reference_v1", "generic_property_v1"]
    max_abs_tolerance: float = Field(default=1e-6, ge=0.0, le=1.0)
    boundary_tolerance: float = Field(default=1e-8, ge=0.0, le=1.0)
    n_intervals: int = Field(default=100, ge=2, le=100000, strict=True)
    x_left: float = Field(default=0.0)
    x_right: float = Field(default=1.0)
    properties: tuple[str, ...] = Field(default_factory=tuple, max_length=64)
    approved: bool = False
    approved_by: str | None = Field(default=None, min_length=1, max_length=120)

    @model_validator(mode="after")
    def poisson_domain(self) -> EvaluationSpec:
        if self.kind == "poisson_reference_v1" and not self.x_left < self.x_right:
            raise ValueError("poisson reference requires x_left < x_right")
        return self


class GeneratedExperimentPlan(Contract):
    """Dynamic experiment plan (the R1 DynamicExperimentPlan). Immutable by construction."""

    schema_version: SchemaVersion = "generated-experiment/v1"
    plan_id: str = Field(min_length=1, max_length=120)
    project_id: str = Field(min_length=1, max_length=120)
    branch_id: str = Field(min_length=1, max_length=120)
    task_id: str = Field(min_length=1, max_length=120)
    candidate_asset_id: str = Field(min_length=1, max_length=120)
    candidate_revision: str = Field(pattern=r"^[a-f0-9]{40,64}$")
    authorization_ref: str = Field(min_length=1, max_length=120)
    files: tuple[GeneratedFile, ...] = Field(min_length=1, max_length=64)
    entrypoint: str = Field(min_length=1, max_length=240)
    data_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=64)
    environment: ApprovedEnvironment
    parameters: dict[str, JsonValue] = Field(default_factory=dict)
    seeds: tuple[int, ...] = Field(default_factory=tuple, max_length=64)
    evaluation: EvaluationSpec
    backend: BackendProfile = Field(default_factory=BackendProfile)
    sources: tuple[GeneratedSource, ...] = Field(min_length=1, max_length=64)
    claim: str = Field(min_length=1, max_length=2048)
    hypothesis: str = Field(min_length=1, max_length=2048)
    output_schema: OutputSchema = "generated-output/v1"

    @field_validator("entrypoint")
    @classmethod
    def python_entrypoint(cls, value: str) -> str:
        path = PurePosixPath(value)
        if path.is_absolute() or not value.endswith(".py") or "\\" in value or ":" in value:
            raise ValueError("relative python entrypoint required")
        return value

    @model_validator(mode="after")
    def entrypoint_in_manifest(self) -> GeneratedExperimentPlan:
        names = {file.name for file in self.files}
        if self.entrypoint not in names:
            raise ValueError("entrypoint_missing_from_code_manifest")
        return self


class GeneratedContext(Contract):
    """Run identity plus author/reviewer. The reviewer must be independent of the author."""

    run_id: str = Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,119}$")
    task_id: str = Field(min_length=1, max_length=120)
    worker_id: str = Field(min_length=1, max_length=120)
    fencing_token: int = Field(ge=1, strict=True)
    author: str = Field(min_length=1, max_length=120)
    reviewer: str = Field(min_length=1, max_length=120)

    @model_validator(mode="after")
    def independent_reviewer(self) -> GeneratedContext:
        if self.author == self.reviewer:
            raise ValueError("candidate_author_cannot_self_review")
        return self


class StaticSecurityReport(Contract):
    """Fail-closed static gate results; a single failure rejects execution."""

    scope: Literal["pass", "fail"] = "pass"
    syntax: Literal["pass", "fail", "not_applicable"] = "pass"
    dependency: Literal["pass", "fail", "not_applicable"] = "pass"
    danger: Literal["pass", "fail"] = "pass"
    resource: Literal["pass", "fail"] = "pass"
    reasons: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return (self.scope == "pass" and self.danger == "pass" and self.resource == "pass"
                and self.syntax in {"pass", "not_applicable"}
                and self.dependency in {"pass", "not_applicable"})


class IsolationCapability(Contract):
    """Declared isolation properties of a backend. ``complete`` is not ``verified``."""

    no_host_write: bool
    no_credentials: bool
    no_host_control: bool
    no_privilege: bool
    export_bounded: bool
    network_deny: bool
    cpu_limit: bool
    memory_limit: bool
    process_limit: bool
    time_limit: bool
    self_owned_cleanup: bool

    @property
    def complete(self) -> bool:
        return all((self.no_host_write, self.no_credentials, self.no_host_control, self.no_privilege,
                    self.export_bounded, self.network_deny, self.cpu_limit, self.memory_limit,
                    self.process_limit, self.time_limit, self.self_owned_cleanup))


class IsolationReport(Contract):
    """Isolation evidence. Declared capability is never treated as a real proof."""

    backend: str = Field(min_length=1, max_length=120)
    declared: IsolationCapability
    verified: bool = False
    probe: Literal["not_run", "passed", "failed"] = "not_run"
    reasons: tuple[str, ...] = ()

    @property
    def admitted(self) -> bool:
        return self.verified and self.probe == "passed" and self.declared.complete


class GeneratedAssessment(Contract):
    """Three-axis result. ``trusted`` means the host recomputed it from raw output."""

    execution: ExecutionAxis = "not_run"
    hypothesis: HypothesisAxis = "not_evaluated"
    contribution: ContributionAxis = "proposed"
    mode: Literal["diagnostic", "final"] = "diagnostic"
    trusted: bool = False
    evaluator_version: str = Field(default="", max_length=120)
    reasons: tuple[str, ...] = ()
    metrics: dict[str, float] = Field(default_factory=dict)
    candidate_self_score: float | None = None


class GeneratedResult(Contract):
    """Durable generated-run archive record; mirrors the registered result envelope."""

    plan: GeneratedExperimentPlan
    context: GeneratedContext
    archive_path: str
    provenance: Literal["live", "replay", "mock"]
    admission: StaticSecurityReport = Field(default_factory=StaticSecurityReport)
    isolation: IsolationReport
    execution_state: Literal[
        "succeeded", "failed", "timeout", "unknown", "unsupported", "missing_artifact",
    ] = "unknown"
    assessment: GeneratedAssessment = Field(default_factory=GeneratedAssessment)
    sandbox_id: str | None = None
    exit_code: int | None = None
    artifacts: tuple[ExperimentArtifact, ...] = ()
    reasons: tuple[str, ...] = ()
    remote_effect: Literal["known", "unknown"] = "unknown"
    cleanup_state: Literal["not_created", "destroyed", "unknown"] = "not_created"
    usage: None = None
    cost_usd: None = None
