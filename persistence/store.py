"""Small SQLModel metadata repository; LangGraph owns graph checkpoints."""

from pathlib import Path

from sqlalchemy.exc import IntegrityError
from sqlmodel import Field, Session, SQLModel, col, create_engine, select

from contracts.identity import AttemptId
from contracts.messages import Envelope
from contracts.resolution import Gene, GeneRef
from contracts.results import TaskResult
from contracts.runtime import Provision


class EventRow(SQLModel, table=True):
    __tablename__ = "events"
    run_id: str = Field(primary_key=True)
    msg_id: str = Field(primary_key=True)
    seq: int = Field(index=True)
    body: str
    handled: bool = False


class ResultRow(SQLModel, table=True):
    __tablename__ = "task_results"
    run_id: str = Field(primary_key=True)
    task_id: str = Field(primary_key=True)
    role: str = Field(primary_key=True)
    instance: int = Field(primary_key=True)
    attempt: int = Field(primary_key=True)
    body: str


class GeneRow(SQLModel, table=True):
    __tablename__ = "genes"
    gene_id: str = Field(primary_key=True)
    version: int = Field(primary_key=True)
    body: str


class ProvisionRow(SQLModel, table=True):
    __tablename__ = "provisions"
    run_id: str = Field(primary_key=True)
    provision_id: str = Field(primary_key=True)
    body: str


class SQLiteStore:
    def __init__(self, path: str | Path) -> None:
        db_path = Path(path).resolve()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(
            f"sqlite:///{db_path.as_posix()}", connect_args={"check_same_thread": False}
        )
        SQLModel.metadata.create_all(self.engine)

    def close(self) -> None:
        self.engine.dispose()

    def append_event(self, event: Envelope) -> bool:
        """Return False on an identical redelivery, reject conflicting IDs."""
        event = Envelope.model_validate_json(event.model_dump_json())
        with Session(self.engine) as session:
            session.add(EventRow(
                run_id=event.run_id, msg_id=event.msg_id, seq=event.seq,
                body=event.model_dump_json(), handled=event.handled,
            ))
            try:
                session.commit()
                return True
            except IntegrityError:
                session.rollback()
                existing = session.get(EventRow, (event.run_id, event.msg_id))
                if existing is None:
                    raise
                prior = Envelope.model_validate_json(existing.body)
                if prior.model_dump(exclude={"handled"}) != event.model_dump(exclude={"handled"}):
                    raise ValueError("msg_id reused with a different event") from None
                return False

    def events(self, run_id: str) -> list[Envelope]:
        with Session(self.engine) as session:
            rows = session.exec(
                select(EventRow).where(EventRow.run_id == run_id)
                .order_by(col(EventRow.seq), col(EventRow.msg_id))
            ).all()
            return [Envelope.model_validate_json(row.body).model_copy(
                update={"handled": row.handled}
            ) for row in rows]

    def mark_handled(self, run_id: str, msg_id: str) -> None:
        with Session(self.engine) as session:
            row = session.get(EventRow, (run_id, msg_id))
            if row is None:
                raise KeyError((run_id, msg_id))
            row.handled = True
            session.add(row)
            session.commit()

    def save_result(self, result: TaskResult) -> None:
        # Validate at persistence boundary too (model_copy can bypass validators).
        result = TaskResult.model_validate_json(result.model_dump_json())
        with Session(self.engine) as session:
            session.merge(ResultRow(
                run_id=result.run_id, task_id=result.task_id,
                role=result.attempt.agent.role, instance=result.attempt.agent.instance,
                attempt=result.attempt.attempt, body=result.model_dump_json(),
            ))
            session.commit()

    def get_result(self, run_id: str, attempt: AttemptId) -> TaskResult | None:
        with Session(self.engine) as session:
            row = session.get(ResultRow, (
                run_id, attempt.task_id, attempt.agent.role,
                attempt.agent.instance, attempt.attempt,
            ))
            return TaskResult.model_validate_json(row.body) if row else None

    def save_gene(self, gene: Gene) -> None:
        """A version identifies immutable content; revisions need a new version."""
        gene = Gene.model_validate_json(gene.model_dump_json())
        with Session(self.engine) as session:
            existing = session.get(GeneRow, (gene.ref.gene_id, gene.ref.version))
            if existing:
                if Gene.model_validate_json(existing.body) != gene:
                    raise ValueError("Gene version already exists with different content")
                return
            session.add(GeneRow(
                gene_id=gene.ref.gene_id, version=gene.ref.version,
                body=gene.model_dump_json(),
            ))
            session.commit()

    def get_gene(self, ref: GeneRef) -> Gene | None:
        with Session(self.engine) as session:
            row = session.get(GeneRow, (ref.gene_id, ref.version))
            if row is None:
                return None
            gene = Gene.model_validate_json(row.body)
            if ref.asset_id is not None and ref.asset_id != gene.ref.asset_id:
                raise ValueError("GeneRef asset_id does not match stored body")
            return gene

    def save_provision(self, provision: Provision) -> None:
        provision = Provision.model_validate_json(provision.model_dump_json())
        with Session(self.engine) as session:
            existing = session.get(ProvisionRow, (provision.run_id, provision.provision_id))
            if existing:
                if Provision.model_validate_json(existing.body) != provision:
                    raise ValueError("provision_id reused with different provision")
                return
            session.add(ProvisionRow(
                run_id=provision.run_id, provision_id=provision.provision_id,
                body=provision.model_dump_json(),
            ))
            session.commit()

    def get_provision(self, run_id: str, provision_id: str) -> Provision | None:
        with Session(self.engine) as session:
            row = session.get(ProvisionRow, (run_id, provision_id))
            return Provision.model_validate_json(row.body) if row else None
