"""Local publication inputs and receipts, not replacements for official schemas."""

from __future__ import annotations

from typing import Literal, Self

import httpx
from pydantic import BaseModel, ConfigDict, Field, JsonValue, SecretStr, model_validator

from contracts.provenance import Acceptance, Provenance
from contracts.results import TaskResult


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class HubConfig(Model):
    """Only literal loopback destinations are enabled until sandbox authorization exists."""

    base_url: str | None = None
    sender_id: str = Field(default="node_morphogenesis_local", pattern=r"^node_[A-Za-z0-9_-]+$")
    node_secret: SecretStr | None = Field(default=None, repr=False, exclude=True)
    timeout_seconds: float = Field(default=10, gt=0, allow_inf_nan=False)
    source: Literal["local_stub", "evolver_proxy"] = "local_stub"
    transport_provenance: Literal["mock", "live"] = "mock"
    proxy_token: SecretStr | None = Field(default=None, repr=False, exclude=True)

    @model_validator(mode="after")
    def local_only(self) -> Self:
        if self.base_url is not None:
            url = httpx.URL(self.base_url)
            if (
                url.scheme not in {"http", "https"}
                or url.host not in {"127.0.0.1", "::1"}
                or url.userinfo or url.query or url.fragment
                or url.path not in {"", "/"}
            ):
                raise ValueError("only literal loopback Hub origins are currently enabled")
        return self

    @model_validator(mode="after")
    def separate_credentials(self) -> Self:
        if self.source == "local_stub" and self.transport_provenance != "mock":
            raise ValueError("local_stub cannot establish live provenance")
        if self.source == "evolver_proxy" and self.node_secret is not None:
            raise ValueError("Proxy requires its IPC token, not the Hub node secret")
        return self


class GenePolicy(Model):
    category: Literal["repair", "optimize", "innovate", "explore"]
    max_files: int = Field(ge=1)
    forbidden_paths: list[str] = Field(min_length=1)
    validation_commands: list[str] | None = Field(default=None, min_length=1)


class CapsuleEvidence(Model):
    """Caller-owned observations; the adapter never guesses these measurements."""

    capsule_id: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1, allow_inf_nan=False)
    files_changed: int = Field(ge=0)
    lines_changed: int = Field(ge=0)
    score: float = Field(ge=0, le=1, allow_inf_nan=False)
    result: TaskResult
    env_fingerprint: dict[str, JsonValue]
    content: dict[str, JsonValue]
    model_name: str | None = Field(default=None, min_length=1)
    returned_model_name: str | None = Field(default=None, min_length=1)
    gateway_response_id: str | None = Field(default=None, min_length=1)
    event_id: str | None = Field(default=None, min_length=1)


PublicationState = Literal["pending", "unknown", "received", "candidate", "promoted", "rejected"]


class PublicationRecord(Model):
    payload_json: str
    provenance: Provenance
    original_run_uri: str | None = None
    state: PublicationState = "pending"
    reason: str = "awaiting_configuration_or_approval"
    acceptance: Acceptance
    source: Literal["local_stub", "evolver_proxy"] = "local_stub"
    receipt_id: str | None = None


class PublishApproval(Model):
    """An explicit caller approval of the exact stored content and destination.

    Creating this value belongs to the application's human/automatic approval gate.
    It is a data receipt, not authentication of the approver's identity.
    """

    approved_by: str = Field(min_length=1, pattern=r"\S")
    payload_json: str
    provenance: Provenance
    original_run_uri: str | None = None
    sender_id: str
    hub_url: str


class HelloResult(Model):
    state: Literal["pending", "acknowledged", "failed"]
    reason: str
    secret_updated: bool = False
    acceptance: Acceptance = Field(default_factory=lambda: Acceptance(provenance="mock"))
    source: Literal["local_stub", "evolver_proxy"] = "local_stub"


class FetchResult(Model):
    state: Literal["pending", "empty", "discovered", "failed"]
    reason: str
    assets: list[dict[str, JsonValue]] = Field(default_factory=list)
    acceptance: Acceptance = Field(default_factory=lambda: Acceptance(provenance="mock"))
    source: Literal["local_stub", "evolver_proxy"] = "local_stub"


class ReuseRecord(Model):
    asset_id: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    task_id: str
    state: Literal["pending", "unknown", "recorded"]
    reason: str
    source: Literal["evolver_proxy"] = "evolver_proxy"
    receipt_id: str | None = None
    acceptance: Acceptance
