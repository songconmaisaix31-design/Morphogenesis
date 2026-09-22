from typing import Protocol

from pydantic import Field

from contracts.base import Contract
from contracts.identity import AgentId, AttemptId
from contracts.provenance import Provenance


class GeneRef(Contract):
    gene_id: str = Field(min_length=1)
    version: int = Field(default=1, ge=1)
    asset_id: str | None = None


class Gene(Contract):
    """Internal experience body; T1 maps it into the official GEP schema."""

    ref: GeneRef
    signals_match: list[str]
    strategy: list[str] = Field(min_length=1)
    avoid: list[str] = Field(default_factory=list)
    verification: list[str] = Field(default_factory=list)
    provenance: Provenance = "live"
    source_attempt: AttemptId | None = None


class Metabolism(Protocol):
    def ingest(self, gene: Gene) -> None: ...
    def resolve(self, ref: GeneRef) -> Gene: ...
    def inject(self, agent: AgentId, budget: int) -> list[Gene]: ...
    def mark_used(self, gene_id: str, attempt: AttemptId) -> None: ...
    def decay_weights(self, now: float) -> None: ...
    def merge_candidates(self) -> list[list[GeneRef]]: ...
    def archive(self) -> list[str]: ...
