"""Run-bound adoption over a shared SQLite cache; GEP algorithms stay in MCP."""

import json
import math
import time
from collections import Counter
from collections.abc import Callable, Iterator
from contextlib import contextmanager

from pydantic import TypeAdapter
from sqlmodel import Session, SQLModel, col, select

from contracts.identity import AgentId, AttemptId
from contracts.provenance import Provenance
from contracts.resolution import Gene, GeneRef
from metabolism.index import CosineIndex, Embedding, lexical_embedding
from metabolism.models import Adoption, AttemptContext, GeneState, GeneView, InjectionBatch, UseRecord
from persistence import SQLiteStore
from persistence.store import GeneRow

_REFS = TypeAdapter(list[GeneRef])


class LocalMetabolism:
    def __init__(
        self, store: SQLiteStore, run_id: str, *,
        provenance: Provenance = "live", tau_seconds: float = 86400.0,
        archive_threshold: float = 0.05, merge_similarity: float = 0.9,
        clock: Callable[[], float] = time.time, embedding: Embedding = lexical_embedding,
    ) -> None:
        if not run_id.strip():
            raise ValueError("run_id is required to scope AttemptId adoption")
        if provenance not in ("live", "mock", "replay"):
            raise ValueError("invalid provenance")
        if not math.isfinite(tau_seconds) or tau_seconds <= 0:
            raise ValueError("tau_seconds must be finite and positive")
        if not 0 <= archive_threshold < 1 or not 0 <= merge_similarity <= 1:
            raise ValueError("invalid archive threshold or merge similarity")
        self.store = store
        self.run_id = run_id
        self.provenance = provenance
        self.tau_seconds = tau_seconds
        self.archive_threshold = archive_threshold
        self.merge_similarity = merge_similarity
        self.clock = clock
        self.embedding = embedding
        self._contexts: dict[AgentId, AttemptContext] = {}
        SQLModel.metadata.create_all(store.engine)

    @contextmanager
    def _transaction(self) -> Iterator[Session]:
        # SQLite serializes these operations across instances/processes too. FAISS
        # is built and consumed inside this same snapshot, never persisted.
        with Session(self.store.engine) as session:
            session.connection().exec_driver_sql("BEGIN IMMEDIATE")
            try:
                yield session
                session.commit()
            except BaseException:
                session.rollback()
                raise

    def _now(self) -> float:
        now = self.clock()
        if not math.isfinite(now) or now < 0:
            raise ValueError("clock must return nonnegative Unix seconds")
        return now

    def _states(self, session: Session) -> list[GeneState]:
        return list(session.exec(select(GeneState).where(
            GeneState.provenance == self.provenance,
        ).order_by(col(GeneState.gene_id), col(GeneState.version))).all())

    @staticmethod
    def _evaluate(state: GeneState, now: float) -> None:
        if now < state.evaluated_at:
            raise ValueError("time cannot move backwards")
        state.weight = math.exp(-(now - state.anchor_at) / state.tau_seconds)
        state.evaluated_at = now

    @staticmethod
    def _body(session: Session, ref: GeneRef) -> Gene:
        row = session.get(GeneRow, (ref.gene_id, ref.version))
        if row is None:
            raise KeyError("Gene body is not cached")
        gene = Gene.model_validate_json(row.body)
        if ref.asset_id is not None and ref.asset_id != gene.ref.asset_id:
            raise ValueError("GeneRef asset_id does not match cached body")
        return gene

    def _resolve(self, session: Session, ref: GeneRef) -> Gene:
        state = session.get(GeneState, (ref.gene_id, ref.version))
        if state is None or state.archived_at is not None or state.provenance != self.provenance:
            raise KeyError("Gene is unknown, archived or outside this provenance")
        gene = self._body(session, ref)
        if gene.provenance != self.provenance:
            raise ValueError("cached body provenance disagrees with local state")
        return gene

    def ingest(self, gene: Gene, *, original_run_uri: str | None = None) -> None:
        """Cache an immutable body supplied by the bridge; no evolve/publish call."""
        gene = Gene.model_validate_json(gene.model_dump_json())
        if gene.provenance != self.provenance:
            raise ValueError("Gene provenance does not match this metabolism instance")
        if self.provenance == "replay" and not original_run_uri:
            raise ValueError("replay requires original_run_uri")
        with self._transaction() as session:
            key = (gene.ref.gene_id, gene.ref.version)
            state = session.get(GeneState, key)
            if state is not None:
                if state.archived_at is not None:
                    raise ValueError("archived Gene version cannot be reactivated")
                if self._resolve(session, gene.ref) != gene or state.original_run_uri != original_run_uri:
                    raise ValueError("Gene version already has different content or origin")
                return
            existing = session.get(GeneRow, key)
            if existing is not None and Gene.model_validate_json(existing.body) != gene:
                raise ValueError("Gene version already has different cached content")
            now = self._now()
            if existing is None:
                session.add(GeneRow(gene_id=gene.ref.gene_id, version=gene.ref.version,
                                    body=gene.model_dump_json()))
            session.add(GeneState(
                gene_id=gene.ref.gene_id, version=gene.ref.version,
                ref_json=gene.ref.model_dump_json(), provenance=gene.provenance,
                original_run_uri=original_run_uri,
                source_attempt_json=(gene.source_attempt.model_dump_json()
                                     if gene.source_attempt else None),
                created_at=now, anchor_at=now, evaluated_at=now, tau_seconds=self.tau_seconds,
            ))

    def resolve(self, ref: GeneRef) -> Gene:
        with self._transaction() as session:
            return self._resolve(session, ref)

    def bind_attempt(self, attempt: AttemptId, signals: list[str] | None = None) -> None:
        """Supply concrete task applicability and identity before inject(agent)."""
        attempt = AttemptId.model_validate_json(attempt.model_dump_json())
        normalized = sorted({s.strip().casefold() for s in (signals or []) if s.strip()})
        self._contexts[attempt.agent] = AttemptContext(attempt=attempt, signals=normalized)

    @staticmethod
    def _key(run_id: str, attempt: AttemptId) -> tuple[str, str, str, int, int]:
        return (run_id, attempt.task_id, attempt.agent.role, attempt.agent.instance, attempt.attempt)

    @staticmethod
    def _applicable(gene: Gene, context: AttemptContext) -> bool:
        signals = {s.strip().casefold() for s in gene.signals_match if s.strip()}
        roles = {s[5:] for s in signals if s.startswith("role:")}
        task_signals = {s for s in signals if not s.startswith("role:")}
        return (not roles or context.attempt.agent.role in roles) and (
            not task_signals or bool(task_signals.intersection(context.signals)))

    def _active(self, session: Session) -> list[tuple[GeneState, Gene]]:
        # Latest known version only, including tombstones in the comparison:
        # archiving v2 must not silently resurrect v1 in searches.
        latest = {state.gene_id: state for state in self._states(session)}
        return [(state, self._resolve(session, GeneRef.model_validate_json(state.ref_json)))
                for state in latest.values() if state.archived_at is None]

    @staticmethod
    def _text(gene: Gene) -> str:
        return "\n".join(gene.signals_match + gene.strategy + gene.avoid + gene.verification)

    def inject(self, agent: AgentId, budget: int) -> list[Gene]:
        """Budget counts whole Gene bodies, not tokens; never marks adoption."""
        if isinstance(budget, bool) or not isinstance(budget, int) or budget < 0:
            raise ValueError("budget must be a nonnegative integer Gene count")
        context = self._contexts.get(agent)
        if context is None:
            raise ValueError("bind_attempt(attempt, signals) is required before inject")
        with self._transaction() as session:
            attempt = context.attempt
            signals_json = json.dumps(context.signals)
            prior = session.get(InjectionBatch, self._key(self.run_id, attempt))
            if prior is not None:
                if prior.provenance != self.provenance:
                    raise ValueError("injection provenance does not match this run")
                if prior.budget != budget or prior.signals_json != signals_json:
                    raise ValueError("an injected AttemptId cannot change budget or signals")
                # Replays never return bodies archived since their first injection.
                result = []
                for ref in _REFS.validate_json(prior.refs_json):
                    try:
                        result.append(self._resolve(session, ref))
                    except KeyError:
                        continue
                return result
            now = self._now()
            choices = [(s, g) for s, g in self._active(session) if self._applicable(g, context)]
            for state, _ in choices:
                self._evaluate(state, now)
                session.add(state)
            chosen: list[Gene] = []
            if choices and budget:
                index = CosineIndex([self._text(g) for _, g in choices], self.embedding)
                query = " ".join(context.signals) or agent.role
                ranks = index.search(query)
                ranks.sort(key=lambda pair: (
                    -max(0.0, pair[1]) * choices[pair[0]][0].weight,
                    -choices[pair[0]][0].weight,
                    choices[pair[0]][1].ref.gene_id,
                ))
                chosen = [choices[i][1] for i, _ in ranks[:budget]]
            session.add(InjectionBatch(
                run_id=self.run_id, task_id=attempt.task_id, role=agent.role,
                instance=agent.instance, attempt=attempt.attempt, budget=budget,
                provenance=self.provenance,
                signals_json=signals_json,
                refs_json=_REFS.dump_json([g.ref for g in chosen]).decode(), injected_at=now,
            ))
            return chosen

    def mark_used(self, gene_id: str, attempt: AttemptId) -> None:
        """Call only after the executor consumed the injected body, not at search."""
        attempt = AttemptId.model_validate_json(attempt.model_dump_json())
        with self._transaction() as session:
            key = self._key(self.run_id, attempt)
            batch = session.get(InjectionBatch, key)
            if batch is None:
                raise ValueError("no injection exists for this run and exact AttemptId")
            if batch.provenance != self.provenance:
                raise ValueError("injection provenance does not match this run")
            if session.get(Adoption, (*key, gene_id)) is not None:
                return
            refs = [ref for ref in _REFS.validate_json(batch.refs_json) if ref.gene_id == gene_id]
            if len(refs) != 1:
                raise ValueError("Gene was not injected into this exact AttemptId")
            ref = refs[0]
            self._resolve(session, ref)
            state = session.get(GeneState, (ref.gene_id, ref.version))
            assert state is not None  # _resolve checked the same transaction.
            now = self._now()
            self._evaluate(state, now)
            state.anchor_at = now
            state.weight = 1.0
            state.use_count += 1
            session.add(state)
            session.add(Adoption(
                run_id=self.run_id, task_id=attempt.task_id, role=attempt.agent.role,
                instance=attempt.agent.instance, attempt=attempt.attempt,
                gene_id=ref.gene_id, version=ref.version, used_at=now,
            ))

    def decay_weights(self, now: float) -> None:
        """now is Unix seconds; w=exp(-(now-last_adoption_or_ingest)/tau_seconds)."""
        if not math.isfinite(now) or now < 0:
            raise ValueError("now must be nonnegative finite Unix seconds")
        with self._transaction() as session:
            for state in self._states(session):
                if state.archived_at is None:
                    self._evaluate(state, now)
                    session.add(state)

    def merge_candidates(self) -> list[list[GeneRef]]:
        """Suggest similar pairs with identical applicability, never merge/evolve."""
        with self._transaction() as session:
            choices = self._active(session)
            if len(choices) < 2:
                return []
            index = CosineIndex([self._text(g) for _, g in choices], self.embedding)
            pairs: list[list[GeneRef]] = []
            for i, (_, first) in enumerate(choices):
                for j, similarity in index.neighbors(i):
                    second = choices[j][1]
                    if (j > i and similarity >= self.merge_similarity
                            and set(first.signals_match) == set(second.signals_match)):
                        pairs.append([first.ref, second.ref])
            return sorted(pairs, key=lambda pair: (pair[0].gene_id, pair[1].gene_id))

    def archive(self) -> list[str]:
        """Atomically tombstone low-weight versions and remove cached bodies locally."""
        with self._transaction() as session:
            now = self._now()
            archived: set[str] = set()
            for state in self._states(session):
                if state.archived_at is not None:
                    continue
                self._evaluate(state, now)
                if state.weight < self.archive_threshold:
                    state.archived_at = now
                    cached = session.get(GeneRow, (state.gene_id, state.version))
                    if cached is not None:
                        session.delete(cached)
                    archived.add(state.gene_id)
                session.add(state)
            return sorted(archived)

    def snapshot(self) -> list[GeneView]:
        """Read-only version/source/usage view; archived rows have no cached body."""
        with self._transaction() as session:
            counts: Counter[tuple[str, int]] = Counter()
            for batch in session.exec(select(InjectionBatch)).all():
                counts.update((r.gene_id, r.version) for r in _REFS.validate_json(batch.refs_json))
            return [GeneView(
                ref=GeneRef.model_validate_json(s.ref_json), provenance=self.provenance,
                original_run_uri=s.original_run_uri,
                source_attempt=AttemptId.model_validate_json(s.source_attempt_json)
                if s.source_attempt_json else None,
                weight=s.weight, use_count=s.use_count,
                injected_count=counts[(s.gene_id, s.version)], created_at=s.created_at,
                last_used_at=s.anchor_at if s.use_count else None, evaluated_at=s.evaluated_at,
                tau_seconds=s.tau_seconds, archived_at=s.archived_at,
            ) for s in self._states(session)]

    def usage_records(self) -> list[UseRecord]:
        """Adoptions for this run only; preserves exact AttemptId and Gene version."""
        with self._transaction() as session:
            records: list[UseRecord] = []
            for row in session.exec(select(Adoption).where(Adoption.run_id == self.run_id)).all():
                state = session.get(GeneState, (row.gene_id, row.version))
                if state is not None and state.provenance == self.provenance:
                    records.append(UseRecord(
                        run_id=row.run_id, attempt=AttemptId.model_validate({
                            "task_id": row.task_id, "agent": {"role": row.role, "instance": row.instance},
                            "attempt": row.attempt,
                        }), ref=GeneRef.model_validate_json(state.ref_json),
                        used_at=row.used_at, provenance=self.provenance,
                    ))
            return sorted(records, key=lambda r: (r.used_at, r.attempt.task_id, r.ref.gene_id))
