"""Explicit test boundaries. No fabricated execution or verification results."""

from collections.abc import Callable
import time
from typing import Literal

from contracts.identity import AgentId, AttemptId
from contracts.resolution import Gene, GeneRef
from contracts.results import TaskResult, Verification
from contracts.runtime import RunConfig
from metabolism import LocalMetabolism
from persistence import SQLiteStore


def gene_fixture(gene_id: str, strategy: list[str], *, signals: list[str] | None = None) -> Gene:
    """Only caller-supplied test content, always labeled mock."""
    return Gene(ref=GeneRef(gene_id=gene_id), strategy=strategy,
                signals_match=signals or [], provenance="mock")


class MockMetabolism(LocalMetabolism):
    """Real local mechanism on explicit mock bodies; cannot ingest live data."""

    def __init__(self, store: SQLiteStore, run_id: str, *,
                 clock: Callable[[], float] = time.time, tau_seconds: float = 86400.0) -> None:
        super().__init__(store, run_id, provenance="mock", clock=clock, tau_seconds=tau_seconds)


class UnimplementedExecutor:
    provenance: Literal["mock"] = "mock"

    def execute(self, attempt: AttemptId, config: RunConfig, genes: list[Gene]) -> TaskResult:
        raise NotImplementedError("mock executor has no execution result")


class UnimplementedVerifier:
    provenance: Literal["mock"] = "mock"

    def verify(self, workspace: str, reviewer: AgentId) -> Verification:
        raise NotImplementedError("mock verifier has no verification evidence")
