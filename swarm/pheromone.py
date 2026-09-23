"""Indexed radius-local field and own-worker pipe memory on durable SQLite."""

from __future__ import annotations

import math
import os
import sqlite3
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

from metabolism.decay import exponential_decay
from swarm.models import Locality, PipeHistory, Signal


def canonical_workspace(workspace: str) -> str:
    return os.path.normcase(str(Path(workspace).resolve()))


class PheromoneField:
    def __init__(self, path: str | Path, *, time_step_seconds: float = 60.0,
                 clock: Callable[[], float] = time.time) -> None:
        if not math.isfinite(time_step_seconds) or time_step_seconds <= 0:
            raise ValueError("time_step_seconds must be positive and finite")
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.clock = clock
        self.tau_seconds = -time_step_seconds / math.log1p(-0.05)
        with self._transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS field_config (id INTEGER PRIMARY KEY, time_step REAL NOT NULL)")
            existing = db.execute("SELECT time_step FROM field_config WHERE id=1").fetchone()
            if existing is not None and existing[0] != time_step_seconds:
                raise ValueError("persisted field time step cannot change on restart")
            db.execute("INSERT OR IGNORE INTO field_config VALUES (1,?)", (time_step_seconds,))
            db.execute("CREATE TABLE IF NOT EXISTS signals (signal_id TEXT PRIMARY KEY, workspace TEXT NOT NULL, "
                       "x REAL NOT NULL, y REAL NOT NULL, body TEXT NOT NULL)")
            db.execute("CREATE INDEX IF NOT EXISTS signals_locality ON signals(workspace,x,y)")
            db.execute("CREATE TABLE IF NOT EXISTS pipes (worker_id TEXT NOT NULL, pipe_key TEXT NOT NULL, "
                       "weight REAL NOT NULL, samples INTEGER NOT NULL, PRIMARY KEY(worker_id,pipe_key))")

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        try:
            db.execute("PRAGMA synchronous=FULL")
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def _now(self) -> float:
        now = self.clock()
        if not math.isfinite(now) or now < 0:
            raise ValueError("invalid clock")
        return now

    def _decay(self, signal: Signal, now: float) -> Signal:
        concentration = signal.concentration * exponential_decay(
            now - signal.updated_at, self.tau_seconds / signal.decay_multiplier)
        return signal.model_copy(update={"concentration": concentration, "updated_at": now})

    @staticmethod
    def _save(db: sqlite3.Connection, signal: Signal) -> None:
        db.execute("INSERT INTO signals VALUES (?,?,?,?,?) ON CONFLICT(signal_id) DO UPDATE SET body=excluded.body",
                   (signal.signal_id, signal.workspace, signal.x, signal.y, signal.model_dump_json()))

    def deposit(self, signal: Signal, delta: float = 0.0) -> Signal:
        if not math.isfinite(delta) or delta < 0:
            raise ValueError("deposit delta must be finite and nonnegative; use feedback for failure")
        signal = Signal.model_validate(signal.model_dump())
        workspace = canonical_workspace(signal.workspace)
        scope = Path(signal.scope)
        target = (Path(workspace) / scope).resolve()
        if not target.is_relative_to(Path(workspace)):
            raise ValueError("signal scope escapes workspace")
        signal = signal.model_copy(update={"workspace": workspace})
        with self._transaction() as db:
            now = self._now()
            row = db.execute("SELECT body FROM signals WHERE signal_id=?", (signal.signal_id,)).fetchone()
            if row:
                old = Signal.model_validate_json(row[0])
                stable = ("task_id", "workspace", "scope", "kind", "payload", "x", "y", "required_capability")
                if any(getattr(old, key) != getattr(signal, key) for key in stable):
                    raise ValueError("signal identity/payload cannot change")
                signal = self._decay(old, now)
            else:
                signal = signal.model_copy(update={"updated_at": now})
            signal = Signal.model_validate(signal.model_copy(update={
                "concentration": signal.concentration + delta}).model_dump())
            self._save(db, signal)
            return signal

    def sense(self, locality: Locality, *, limit: int = 100) -> list[Signal]:
        locality = Locality.model_validate(locality.model_dump())
        if not 1 <= limit <= 10000:
            raise ValueError("limit must be between 1 and 10000")
        x, y, r = locality.x, locality.y, locality.radius
        with self._transaction() as db:
            # The index restricts workspace/x first; exact Euclidean radius is filtered
            # in SQLite before any bodies are read into Python. No global snapshot.
            rows = db.execute("SELECT body FROM signals INDEXED BY signals_locality WHERE workspace=? "
                              "AND x BETWEEN ? AND ? AND y BETWEEN ? AND ? "
                              "AND ((x-?)*(x-?)+(y-?)*(y-?))<=? "
                              "AND json_extract(body,'$.completed')=0 ORDER BY x,y,signal_id LIMIT ?",
                              (canonical_workspace(locality.workspace), x-r, x+r, y-r, y+r,
                               x, x, y, y, r*r, limit)).fetchall()
            now = self._now()
            return [self._decay(Signal.model_validate_json(row[0]), now) for row in rows]

    def feedback(self, signal_id: str, *, success: bool, reward: float = 1.0) -> Signal:
        if not math.isfinite(reward) or not 0 <= reward <= 1:
            raise ValueError("reward must be between zero and one")
        with self._transaction() as db:
            row = db.execute("SELECT body FROM signals WHERE signal_id=?", (signal_id,)).fetchone()
            if row is None:
                raise KeyError(signal_id)
            signal = self._decay(Signal.model_validate_json(row[0]), self._now())
            updates = ({"concentration": min(1e12, signal.concentration + reward)} if success else
                       {"concentration": max(0.0, signal.concentration * (1.0 - 0.5 * reward)),
                        "decay_multiplier": min(1e6, signal.decay_multiplier * (1.0 + reward))})
            signal = signal.model_copy(update=updates)
            self._save(db, signal)
            return signal

    def complete(self, signal_id: str) -> None:
        with self._transaction() as db:
            row = db.execute("SELECT body FROM signals WHERE signal_id=?", (signal_id,)).fetchone()
            if row is None:
                raise KeyError(signal_id)
            signal = self._decay(Signal.model_validate_json(row[0]), self._now())
            self._save(db, signal.model_copy(update={"completed": True}))

    def snapshot(self) -> list[Signal]:
        """Observer-only global read; runtime sensing must use sense(locality)."""
        with self._transaction() as db:
            now = self._now()
            return [self._decay(Signal.model_validate_json(row[0]), now)
                    for row in db.execute("SELECT body FROM signals ORDER BY signal_id")]

    def pipe_history(self, worker_id: str, pipe_key: str) -> PipeHistory:
        with self._transaction() as db:
            row = db.execute("SELECT weight,samples FROM pipes WHERE worker_id=? AND pipe_key=?",
                             (worker_id, pipe_key)).fetchone()
            return PipeHistory(worker_id=worker_id, pipe_key=pipe_key,
                               weight=row[0] if row else 0.25, samples=row[1] if row else 0)

    def reinforce(self, worker_id: str, pipe_key: str, reward: float) -> PipeHistory:
        if not worker_id.strip() or not pipe_key.strip() or not math.isfinite(reward) or not 0 <= reward <= 1:
            raise ValueError("invalid worker, pipe or reward")
        with self._transaction() as db:
            row = db.execute("SELECT weight,samples FROM pipes WHERE worker_id=? AND pipe_key=?",
                             (worker_id, pipe_key)).fetchone()
            result = PipeHistory(worker_id=worker_id, pipe_key=pipe_key,
                                 weight=0.95 * (row[0] if row else 0.25) + 0.05 * reward,
                                 samples=(row[1] if row else 0) + 1)
            db.execute("INSERT INTO pipes VALUES (?,?,?,?) ON CONFLICT(worker_id,pipe_key) "
                       "DO UPDATE SET weight=excluded.weight,samples=excluded.samples",
                       (worker_id, pipe_key, result.weight, result.samples))
            return result
