"""Experiment data identities and predeclared policy; no scheduling machinery."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Literal

from pydantic import Field, field_validator, model_validator

from contracts.base import Contract


class ExperimentInput(Contract):
    local_path: str
    name: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source: str

    @field_validator("name")
    @classmethod
    def relative_file(cls, value: str) -> str:
        path = PurePosixPath(value)
        if (path.is_absolute() or not value or "\\" in value or ":" in value
                or any(part in {"", ".", ".."} for part in value.split("/"))):
            raise ValueError("relative experiment file required")
        return value


class ExperimentResources(Contract):
    cpu: int = Field(default=1, ge=1, le=2, strict=True)
    memory_mib: int = Field(default=512, ge=256, le=2048, strict=True)
    lifetime_seconds: int = Field(default=180, ge=30, le=900, strict=True)
    command_seconds: int = Field(default=30, ge=1, le=300, strict=True)
    artifact_bytes: int = Field(default=1048576, ge=1024, le=16777216, strict=True)

    @model_validator(mode="after")
    def lifetime_bounds_command(self) -> ExperimentResources:
        if self.command_seconds >= self.lifetime_seconds:
            raise ValueError("command duration must be below sandbox lifetime")
        return self


class ExperimentEnvironment(Contract):
    image: str
    python_version: Literal["3.12"] = "3.12"
    sdk_version: Literal["1.1.0"] = "1.1.0"
    backend: Literal["opensandbox"] = "opensandbox"

    @field_validator("image")
    @classmethod
    def pinned_image(cls, value: str) -> str:
        if (not value or any(ch.isspace() for ch in value) or
                ("@sha256:" not in value and ":" not in value.rsplit("/", 1)[-1]) or
                value.endswith(":latest")):
            raise ValueError("explicit image version or digest required")
        return value


class ExperimentCriteria(Contract):
    # A task cannot select a shell command as its scientific validator.
    version: Literal["nist-numacc4-v1"] = "nist-numacc4-v1"
    sample_variance: float = Field(default=0.01, ge=0.01, le=0.01)
    variance_absolute_tolerance: float = Field(default=1e-9, ge=1e-9, le=1e-9)
    mean_absolute_tolerance: float = Field(default=1e-8, ge=1e-8, le=1e-8)
    residual_absolute_tolerance: float = Field(default=1e-8, ge=1e-8, le=1e-8)
    observations: Literal[1001] = 1001


class ExperimentPlan(Contract):
    plan_id: str = Field(min_length=1, max_length=120)
    claim: str = Field(min_length=1, max_length=2048)
    role: Literal["author", "replication", "inheritance"]
    code: ExperimentInput
    data: ExperimentInput
    environment: ExperimentEnvironment
    criteria: ExperimentCriteria = Field(default_factory=ExperimentCriteria)
    resources: ExperimentResources = Field(default_factory=ExperimentResources)
    mode: Literal["script", "notebook", "codeinterpreter"] = "script"
    parameters: tuple[Literal["original", "reverse"], ...] = ("original",)
    seed: Literal[0] = 0
    output_name: Literal["metrics.json"] = "metrics.json"
    persistent_volume: str | None = Field(default=None, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,62}$")

    @model_validator(mode="after")
    def distinct_input_files(self) -> ExperimentPlan:
        if self.code.name == self.data.name or len(self.parameters) != 1:
            raise ValueError("distinct code/data and one fixed order required")
        if self.code.name in {"metrics.json", "runtime.json", "executed.ipynb", "notebook_runner.py"}:
            raise ValueError("reserved output name")
        if self.data.name in {"metrics.json", "runtime.json", "executed.ipynb", "notebook_runner.py"}:
            raise ValueError("reserved output name")
        return self


class ExperimentContext(Contract):
    run_id: str = Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,119}$")
    task_id: str = Field(min_length=1, max_length=120)
    worker_id: str = Field(min_length=1, max_length=120)
    fencing_token: int = Field(ge=1, strict=True)


class ExperimentArtifact(Contract):
    name: str
    archive_path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)


class ScientificAssessment(Contract):
    verdict: Literal["passed", "failed", "not_evaluated"] = "not_evaluated"
    reasons: tuple[str, ...] = ()
    metrics: dict[str, float] = Field(default_factory=dict)
    criteria_version: Literal["nist-numacc4-v1"] = "nist-numacc4-v1"


class ExperimentResult(Contract):
    plan: ExperimentPlan
    context: ExperimentContext
    archive_path: str
    provenance: Literal["live", "replay", "mock"]
    execution_state: Literal["succeeded", "failed", "timeout", "unknown", "unsupported", "missing_artifact"] = "unknown"
    scientific: ScientificAssessment = Field(default_factory=ScientificAssessment)
    sandbox_id: str | None = None
    kernel_id: str | None = None
    command_id: str | None = None
    exit_code: int | None = None
    artifacts: tuple[ExperimentArtifact, ...] = ()
    reasons: tuple[str, ...] = ()
    remote_effect: Literal["known", "unknown"] = "unknown"
    cleanup_state: Literal["not_created", "destroyed", "unknown"] = "not_created"
    resource_enforcement: Literal["unknown", "observed"] = "unknown"
    usage: None = None
    cost_usd: None = None
