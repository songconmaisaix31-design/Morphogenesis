"""Decaying preferences, separate from durable task facts and acceptance."""
from __future__ import annotations

import math
from pathlib import Path
import sqlite3
import time
from collections.abc import Callable

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

    def _now(self) -> float:
        return now_checked(self.clock)

    def _materialize(self, db: sqlite3.Connection, record: TaskRecord, now: float) -> Signal:
        signal = record.signal
        row = db.execute("SELECT concentration,updated_at,multiplier FROM pheromones WHERE swarm_id=? AND task_id=?",
                         (self.ledger.swarm_id, signal.task_id)).fetchone()
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
            self._save(db,result)
            return result

    def snapshot(self, *, limit: int = 100) -> list[Signal]:
        return self.for_records(self.ledger.snapshot(limit=limit))

    def _history(self, db: sqlite3.Connection, worker_id: str, pipe_key: str, now: float) -> PipeHistory:
        row = db.execute("SELECT weight,samples,updated_at FROM pipe_history WHERE swarm_id=? AND worker_id=? AND pipe_key=?",
                         (self.ledger.swarm_id,worker_id,pipe_key)).fetchone()
        return PipeHistory(worker_id=worker_id,pipe_key=pipe_key,
                           weight=row[0]*exponential_decay(now-row[2],self.tau_seconds) if row else 0.25,
                           samples=row[1] if row else 0)

    def pipe_history(self, worker_id: str, pipe_key: str) -> PipeHistory:
        with connection(self.path) as db:
            return self._history(db,worker_id,pipe_key,self._now())

    def reinforce(self, worker_id: str, pipe_key: str, reward: float) -> PipeHistory:
        if not worker_id.strip() or not pipe_key.strip() or not math.isfinite(reward) or not 0 <= reward <= 1:
            raise ValueError("invalid worker, pipe or reward")
        with connection(self.path, write=True) as db:
            now = self._now()
            previous = self._history(db,worker_id,pipe_key,now)
            result = PipeHistory(worker_id=worker_id,pipe_key=pipe_key,
                                 weight=(1-self.alpha)*previous.weight+self.alpha*reward,samples=previous.samples+1)
            db.execute("INSERT INTO pipe_history VALUES (?,?,?,?,?,?) ON CONFLICT(swarm_id,worker_id,pipe_key) "
                       "DO UPDATE SET weight=excluded.weight,samples=excluded.samples,updated_at=excluded.updated_at",
                       (self.ledger.swarm_id,worker_id,pipe_key,result.weight,result.samples,now))
            return result
