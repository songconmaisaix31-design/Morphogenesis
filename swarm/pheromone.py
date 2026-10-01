"""Decaying preferences, separate from durable task facts and acceptance."""
from __future__ import annotations

import math
from pathlib import Path
import sqlite3
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swarm.feedback import FeedbackFact

_PAIR: ContextVar[tuple[object, set[str]] | None] = ContextVar("trusted_feedback_pair", default=None)

from metabolism.decay import exponential_decay
from swarm.models import Locality, PipeHistory, Signal, TaskRecord
from swarm.task_ledger import TaskLedger, connection, enable_wal, now_checked


class PheromoneField:
    def __init__(self, path: str | Path, *, ledger: TaskLedger, tau_seconds: float = 86400.0,
                 alpha: float = 0.05, clock: Callable[[], float] = time.time) -> None:
        if not math.isfinite(tau_seconds) or tau_seconds <= 0:
            raise ValueError("tau_seconds must be finite and positive")
        if not math.isfinite(alpha) or not 0 < alpha <= 1:
            raise ValueError("alpha must be in (0,1]")
        self.path, self.ledger, self.clock = Path(path).resolve(), ledger, clock
        self.tau_seconds, self.alpha = tau_seconds, alpha
        enable_wal(self.path)
        with connection(self.path, write=True) as db:
            if db.execute("SELECT 1 FROM sqlite_master WHERE name='signals'").fetchone():
                raise ValueError("legacy field requires explicit task migration; preserve its audit")
            db.execute("CREATE TABLE IF NOT EXISTS preference_config (swarm_id TEXT PRIMARY KEY,tau REAL,alpha REAL)")
            row = db.execute("SELECT tau,alpha FROM preference_config WHERE swarm_id=?", (ledger.swarm_id,)).fetchone()
            if row and (row[0], row[1]) != (tau_seconds, alpha):
                raise ValueError("persisted tau/alpha cannot change")
            db.execute("INSERT OR IGNORE INTO preference_config VALUES (?,?,?)", (ledger.swarm_id,tau_seconds,alpha))
            db.execute("CREATE TABLE IF NOT EXISTS pheromones (swarm_id TEXT,signal_id TEXT,task_id TEXT,concentration REAL,"
                       "updated_at REAL,multiplier REAL,PRIMARY KEY(swarm_id,signal_id),UNIQUE(swarm_id,task_id))")
            db.execute("CREATE TABLE IF NOT EXISTS pipe_history (swarm_id TEXT,worker_id TEXT,pipe_key TEXT,weight REAL,"
                       "samples INTEGER,updated_at REAL,PRIMARY KEY(swarm_id,worker_id,pipe_key))")
            db.execute("CREATE TABLE IF NOT EXISTS learning_facts (swarm_id TEXT,source_id TEXT,kind TEXT,body TEXT,"
                       "PRIMARY KEY(swarm_id,source_id,kind))")
            db.execute("CREATE TABLE IF NOT EXISTS learned_signals (swarm_id TEXT,task_id TEXT,concentration REAL,"
                       "updated_at REAL,PRIMARY KEY(swarm_id,task_id))")
            db.execute("CREATE TABLE IF NOT EXISTS learned_history (swarm_id TEXT,worker_id TEXT,pipe_key TEXT,weight REAL,"
                       "samples INTEGER,updated_at REAL,PRIMARY KEY(swarm_id,worker_id,pipe_key))")

    def _now(self) -> float:
        return now_checked(self.clock)

    def _materialize(self, db: sqlite3.Connection, record: TaskRecord, now: float) -> Signal:
        signal = record.signal
        row = db.execute("SELECT concentration,updated_at,multiplier FROM pheromones WHERE swarm_id=? AND task_id=?",
                         (self.ledger.swarm_id, signal.task_id)).fetchone()
        learned = db.execute("SELECT concentration,updated_at FROM learned_signals WHERE swarm_id=? AND task_id=?",
                             (self.ledger.swarm_id, signal.task_id)).fetchone()
        if learned is not None:
            row = (learned[0], learned[1], 1.0)
        concentration, anchor, multiplier = (row[0],row[1],row[2]) if row else (signal.concentration,record.created_at,1.0)
        concentration *= exponential_decay(now - anchor, self.tau_seconds / multiplier)
        return signal.model_copy(update={"concentration": concentration, "updated_at": now,
                                         "decay_multiplier": multiplier, "completed": record.status == "completed"})

    def _save(self, db: sqlite3.Connection, signal: Signal) -> None:
        db.execute("INSERT INTO pheromones VALUES (?,?,?,?,?,?) ON CONFLICT(swarm_id,signal_id) DO UPDATE SET "
                   "concentration=excluded.concentration,updated_at=excluded.updated_at,multiplier=excluded.multiplier",
                   (self.ledger.swarm_id,signal.signal_id,signal.task_id,signal.concentration,signal.updated_at,signal.decay_multiplier))

    def deposit(self, signal: Signal, delta: float = 0.0) -> Signal:
        if not math.isfinite(delta) or delta < 0:
            raise ValueError("delta must be finite and nonnegative")
        record = self.ledger.enqueue(signal)
        with connection(self.path, write=True) as db:
            current = self._materialize(db, record, self._now())
            # Duplicate error observation with a new identity cannot amplify routing.
            if record.signal.signal_id == signal.signal_id:
                current = Signal.model_validate(current.model_copy(update={"concentration": current.concentration + delta}).model_dump())
            self._save(db, current)
            return current

    def for_records(self, records: list[TaskRecord]) -> list[Signal]:
        with connection(self.path) as db:
            now = self._now()
            return [self._materialize(db, record, now) for record in records]

    def sense(self, locality: Locality, *, limit: int = 100) -> list[Signal]:
        return self.for_records(self.ledger.candidates(locality, limit=limit))

    def feedback(self, signal_id: str, *, success: bool, reward: float = 1.0) -> Signal:
        if not math.isfinite(reward) or not 0 <= reward <= 1:
            raise ValueError("reward must be in [0,1]")
        with connection(self.path) as db:
            row = db.execute("SELECT task_id FROM pheromones WHERE swarm_id=? AND signal_id=?",
                             (self.ledger.swarm_id,signal_id)).fetchone()
        if row is None:
            raise KeyError(signal_id)
        record = self.ledger.get(row[0])
        with connection(self.path, write=True) as db:
            signal = self._materialize(db,record,self._now())
            updates = ({"concentration": min(1e12, signal.concentration + reward)} if success else
                       {"concentration": signal.concentration * (1.0 - 0.5 * reward),
                        "decay_multiplier": min(1e6, signal.decay_multiplier * (1.0 + reward))})
            result = signal.model_copy(update=updates)
            pair = _PAIR.get()
            if pair is not None and pair[0] is self:
                pair[1].add("signal")
            else:
                self._save(db,result)
            return result

    def snapshot(self, *, limit: int = 100) -> list[Signal]:
        return self.for_records(self.ledger.snapshot(limit=limit))

    def _history(self, db: sqlite3.Connection, worker_id: str, pipe_key: str, now: float,
                 prior: float | None = None) -> PipeHistory:
        row = db.execute("SELECT weight,samples,updated_at FROM pipe_history WHERE swarm_id=? AND worker_id=? AND pipe_key=?",
                         (self.ledger.swarm_id,worker_id,pipe_key)).fetchone()
        learned = db.execute("SELECT weight,samples,updated_at FROM learned_history WHERE swarm_id=? AND worker_id=? AND pipe_key=?",
                             (self.ledger.swarm_id,worker_id,pipe_key)).fetchone()
        if learned is not None:
            row = learned
        baseline = 0.0 if prior is None else prior
        return PipeHistory(worker_id=worker_id,pipe_key=pipe_key,
                           weight=baseline+(row[0]-baseline)*exponential_decay(now-row[2],self.tau_seconds) if row else 0.25,
                           samples=row[1] if row else 0)

    @staticmethod
    def _check_prior(prior: float | None) -> None:
        if prior is not None and (isinstance(prior, bool) or not math.isfinite(prior) or not 0 <= prior <= 1):
            raise ValueError("prior must be a finite fraction")

    def pipe_history(self, worker_id: str, pipe_key: str, *, prior: float | None = None) -> PipeHistory:
        self._check_prior(prior)
        with connection(self.path) as db:
            return self._history(db,worker_id,pipe_key,self._now(),prior)

    def reinforce(self, worker_id: str, pipe_key: str, reward: float, *, prior: float | None = None) -> PipeHistory:
        self._check_prior(prior)
        if not worker_id.strip() or not pipe_key.strip() or not math.isfinite(reward) or not 0 <= reward <= 1:
            raise ValueError("invalid worker, pipe or reward")
        with connection(self.path, write=True) as db:
            now = self._now()
            previous = self._history(db,worker_id,pipe_key,now,prior)
            result = PipeHistory(worker_id=worker_id,pipe_key=pipe_key,
                                 weight=(1-self.alpha)*previous.weight+self.alpha*reward,samples=previous.samples+1)
            pair = _PAIR.get()
            if pair is not None and pair[0] is self:
                pair[1].add("history")
            else:
                db.execute("INSERT INTO pipe_history VALUES (?,?,?,?,?,?) ON CONFLICT(swarm_id,worker_id,pipe_key) "
                           "DO UPDATE SET weight=excluded.weight,samples=excluded.samples,updated_at=excluded.updated_at",
                           (self.ledger.swarm_id,worker_id,pipe_key,result.weight,result.samples,now))
            return result

    @contextmanager
    def trusted_pair(self, fact: FeedbackFact) -> Iterator[None]:
        """Keep the Worker feedback crash boundary; commit a successful pair once."""
        if _PAIR.get() is not None:
            raise RuntimeError("nested_trusted_feedback")
        calls: set[str] = set()
        token = _PAIR.set((self, calls))
        try:
            yield
            if calls != {"signal", "history"}:
                raise RuntimeError("incomplete_trusted_feedback_pair")
            self.synchronize([fact], replace=False)
        finally:
            _PAIR.reset(token)

    def synchronize(self, facts: list[FeedbackFact], *, replace: bool = True) -> None:
        """Atomic derived-index rebuild. Original fact times remain the anchors."""
        from swarm.feedback import FeedbackFact
        with connection(self.path, write=True) as db:
            if replace:
                db.execute("DELETE FROM learning_facts WHERE swarm_id=?", (self.ledger.swarm_id,))
            for fact in facts:
                body = fact.model_dump_json()
                kinds = db.execute("SELECT kind FROM learning_facts WHERE swarm_id=? AND source_id=?",
                                   (self.ledger.swarm_id, fact.source_id)).fetchall()
                if any(row[0] != fact.kind for row in kinds):
                    raise ValueError("completed_source_kind_changed")
                old = db.execute("SELECT body FROM learning_facts WHERE swarm_id=? AND source_id=? AND kind=?",
                                 (self.ledger.swarm_id, fact.source_id, fact.kind)).fetchone()
                if old is not None and old[0] != body:
                    raise ValueError("learning_source_identity_changed")
                db.execute("INSERT OR IGNORE INTO learning_facts VALUES (?,?,?,?)",
                           (self.ledger.swarm_id, fact.source_id, fact.kind, body))
            ordered = [FeedbackFact.model_validate_json(row[0]) for row in db.execute(
                "SELECT body FROM learning_facts WHERE swarm_id=?", (self.ledger.swarm_id,))]
            signals, history = project(self.ledger, ordered, self.tau_seconds, self.alpha)
            db.execute("DELETE FROM learned_signals WHERE swarm_id=?", (self.ledger.swarm_id,))
            db.execute("DELETE FROM learned_history WHERE swarm_id=?", (self.ledger.swarm_id,))
            db.executemany("INSERT INTO learned_signals VALUES (?,?,?,?)",
                           [(self.ledger.swarm_id, task, c, at) for task, (c, at) in signals.items()])
            db.executemany("INSERT INTO learned_history VALUES (?,?,?,?,?,?)",
                           [(self.ledger.swarm_id, worker, pipe, w, n, at) for (worker, pipe), (w, n, at) in history.items()])


def project(ledger: TaskLedger, facts: list[FeedbackFact], tau: float, alpha: float) -> tuple[
        dict[str, tuple[float, float]], dict[tuple[str, str], tuple[float, int, float]]]:
    signals: dict[str, tuple[float, float]] = {}
    history: dict[tuple[str, str], tuple[float, int, float]] = {}
    unique = {(fact.source_id, fact.kind): fact for fact in facts}
    for fact in sorted(unique.values(), key=lambda f: (f.at, f.source_id, f.kind)):
        task = ledger.get(fact.task_id)
        c, at = signals.get(fact.task_id, (task.signal.concentration, task.created_at))
        signals[fact.task_id] = (min(1e12, c * exponential_decay(fact.at-at, tau) + 1.0), fact.at)
        key = (fact.worker_id, fact.pipe_key)
        weight, samples, at = history.get(key, (0.25, 0, fact.at))
        weight = 0.25 + (weight - 0.25) * exponential_decay(fact.at-at, tau)
        history[key] = ((1-alpha)*weight + alpha*0.5, samples+1, fact.at)
    return signals, history


class PreviewField(PheromoneField):
    """In-memory derived view; no database initialization or credential access."""
    def __init__(self, ledger: TaskLedger, facts: list[FeedbackFact]) -> None:
        self.ledger, self.clock = ledger, ledger.clock
        self.tau_seconds, self.alpha = 86400.0, 0.05
        self.signals, self.histories = project(ledger, facts, self.tau_seconds, self.alpha)

    def for_records(self, records: list[TaskRecord]) -> list[Signal]:
        now = self._now()
        results = []
        for record in records:
            c, at = self.signals.get(record.signal.task_id, (record.signal.concentration, record.created_at))
            results.append(record.signal.model_copy(update={"concentration": c * exponential_decay(now-at, self.tau_seconds),
                                                             "updated_at": now, "completed": record.status == "completed"}))
        return results

    def pipe_history(self, worker_id: str, pipe_key: str, *, prior: float | None = None) -> PipeHistory:
        self._check_prior(prior)
        if (worker_id, pipe_key) not in self.histories:
            return PipeHistory(worker_id=worker_id, pipe_key=pipe_key, weight=0.25, samples=0)
        weight, samples, at = self.histories.get((worker_id, pipe_key), (0.25, 0, self._now()))
        baseline = 0.0 if prior is None else prior
        return PipeHistory(worker_id=worker_id, pipe_key=pipe_key,
                           weight=baseline+(weight-baseline)*exponential_decay(self._now()-at, self.tau_seconds), samples=samples)
