from typing import Protocol

from pydantic import Field

from contracts.base import Contract
from contracts.identity import AgentId, AttemptId
from contracts.messages import Envelope
from contracts.readiness import ProbeResult, ProbeSubject
from contracts.resolution import Gene, GeneRef
from contracts.results import TaskResult, Verification
from contracts.runtime import Provision, RunConfig


class PipeState(Contract):
    src: AgentId
    dst: AgentId
    weight: float = Field(default=0.0, ge=0)
    flow: float = Field(default=0.0, ge=0)
    success_rate: float = Field(default=0.5, ge=0, le=1)
    active: bool = True


class TopologyEngine(Protocol):
    def select(self, targets: list[AgentId]) -> AgentId | None: ...
    def record(self, attempt: AttemptId, success: bool) -> None: ...
    def snapshot(self) -> list[PipeState]: ...


class EventStore(Protocol):
    def append_event(self, event: Envelope) -> bool: ...
    def events(self, run_id: str) -> list[Envelope]: ...
    def mark_handled(self, run_id: str, msg_id: str) -> None: ...


class ResultStore(Protocol):
    def save_result(self, result: TaskResult) -> None: ...
    def get_result(self, run_id: str, attempt: AttemptId) -> TaskResult | None: ...


class GeneStore(Protocol):
    def save_gene(self, gene: Gene) -> None: ...
    def get_gene(self, ref: GeneRef) -> Gene | None: ...


class Executor(Protocol):
    def execute(self, attempt: AttemptId, config: RunConfig, genes: list[Gene]) -> TaskResult: ...


class Verifier(Protocol):
    def verify(self, workspace: str, reviewer: AgentId) -> Verification: ...


class Provisioner(Protocol):
    def provision(self, run_id: str, count: int) -> Provision: ...


class ReadinessProbe(Protocol):
    """One declared way to observe readiness.

    Intentionally transport-free: a probe may read the local machine, run an
    allowlisted public CLI, or speak MCP.  Those details belong to the adapter
    behind this boundary, and an empty probe set is a valid deployment state
    that must report ``not_run`` rather than a default verdict.
    """

    @property
    def probe_id(self) -> str: ...

    @property
    def subject(self) -> ProbeSubject: ...

    def probe(self) -> ProbeResult: ...
