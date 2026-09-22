"""Local cache state and adoption facts, not a GEP memory graph or scheduler."""

from pydantic import Field as ValidatedField
from sqlmodel import Field, SQLModel

from contracts.base import Contract
from contracts.identity import AttemptId
from contracts.provenance import Provenance
from contracts.resolution import GeneRef


class GeneState(SQLModel, table=True):
    __tablename__ = "metabolism_gene_state"
    gene_id: str = Field(primary_key=True)
    version: int = Field(primary_key=True)
    ref_json: str
    provenance: str
    original_run_uri: str | None = None
    source_attempt_json: str | None = None
    created_at: float
    anchor_at: float
    evaluated_at: float
    tau_seconds: float
    weight: float = 1.0
    use_count: int = 0
    archived_at: float | None = None


class InjectionBatch(SQLModel, table=True):
    __tablename__ = "metabolism_injections"
    run_id: str = Field(primary_key=True)
    task_id: str = Field(primary_key=True)
    role: str = Field(primary_key=True)
    instance: int = Field(primary_key=True)
    attempt: int = Field(primary_key=True)
    provenance: str
    budget: int
    signals_json: str
    refs_json: str
    injected_at: float


class Adoption(SQLModel, table=True):
    __tablename__ = "metabolism_adoptions"
    run_id: str = Field(primary_key=True)
    task_id: str = Field(primary_key=True)
    role: str = Field(primary_key=True)
    instance: int = Field(primary_key=True)
    attempt: int = Field(primary_key=True)
    gene_id: str = Field(primary_key=True)
    version: int
    used_at: float


class GeneView(Contract):
    ref: GeneRef
    provenance: Provenance
    original_run_uri: str | None
    source_attempt: AttemptId | None
    weight: float
    use_count: int
    injected_count: int
    created_at: float
    last_used_at: float | None
    evaluated_at: float
    tau_seconds: float
    archived_at: float | None
    remote_archive_status: str = "not_synchronized"


class UseRecord(Contract):
    run_id: str
    attempt: AttemptId
    ref: GeneRef
    used_at: float
    provenance: Provenance


class AttemptContext(Contract):
    attempt: AttemptId
    signals: list[str] = ValidatedField(default_factory=list)
