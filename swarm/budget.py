"""Atomic account-wide local estimates. Unknown execution never releases a hold."""

from __future__ import annotations

import math
import sqlite3
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from pydantic import JsonValue

from orchestration.gateway import _usage
from swarm.models import BudgetPolicy, BudgetSnapshot, ExecutionBound, Reservation


class BudgetBlocked(RuntimeError):
    def __init__(self, reason: str, sleep_seconds: float = 60.0) -> None:
        super().__init__(reason)
        self.reason, self.sleep_seconds = reason, sleep_seconds


class BudgetLedger:
    def __init__(self, path: str | Path, account_id: str, policy: BudgetPolicy, *,
                 clock: Callable[[], float] = time.time) -> None:
        policy = BudgetPolicy.model_validate(policy.model_dump())
        if not account_id.strip():
            raise ValueError("account_id is required")
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.account_id, self.policy, self.clock = account_id, policy, clock
        with self._transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS accounts (account_id TEXT PRIMARY KEY, "
                       "policy_json TEXT NOT NULL, breaker TEXT)")
            db.execute("CREATE TABLE IF NOT EXISTS reservations (reservation_id TEXT PRIMARY KEY, "
                       "account_id TEXT NOT NULL, worker_id TEXT NOT NULL, task_id TEXT NOT NULL, "
                       "body TEXT NOT NULL, status TEXT NOT NULL, created_at REAL NOT NULL, "
                       "settled_at REAL, tokens INTEGER, estimate_usd REAL, reserved_usd REAL NOT NULL, "
                       "UNIQUE(account_id,task_id))")
            db.execute("CREATE INDEX IF NOT EXISTS reservations_account ON "
                       "reservations(account_id,worker_id,created_at)")
            row = db.execute("SELECT policy_json FROM accounts WHERE account_id=?", (account_id,)).fetchone()
            if row is None:
                db.execute("INSERT INTO accounts VALUES (?,?,NULL)", (account_id, policy.model_dump_json()))
            elif BudgetPolicy.model_validate_json(row[0]) != policy:
                raise ValueError("account policy differs from durable policy; cannot reset budget")

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        db.row_factory = sqlite3.Row
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

    def _estimate(self, input_tokens: int, output_tokens: int) -> float:
        prices = self.policy.prices
        if prices is None:
            raise BudgetBlocked("explicit_model_prices_required")
        estimate = (input_tokens * prices.input_usd_per_million +
                    output_tokens * prices.output_usd_per_million) / 1_000_000
        if not math.isfinite(estimate):
            raise BudgetBlocked("nonfinite_estimate")
        return estimate

    def _snapshot(self, db: sqlite3.Connection, worker_id: str | None, now: float) -> BudgetSnapshot:
        account = db.execute("SELECT breaker FROM accounts WHERE account_id=?", (self.account_id,)).fetchone()
        rows = db.execute("SELECT status,tokens,estimate_usd,reserved_usd FROM reservations "
                          "WHERE account_id=?", (self.account_id,)).fetchall()
        uncertain = sum(row["status"] == "uncertain" for row in rows)
        pending = sum(row["status"] == "pending" for row in rows)
        holds = sum(float(row["reserved_usd"]) for row in rows if row["status"] != "settled")
        spent = sum(float(row["estimate_usd"]) for row in rows if row["estimate_usd"] is not None)
        tokens = sum(int(row["tokens"]) for row in rows if row["tokens"] is not None)
        reason = account["breaker"]
        sleep = self.policy.burn_window_seconds if reason else 0.0
        if worker_id is not None and reason is None:
            recent = db.execute("SELECT body,status,tokens,created_at,settled_at FROM reservations "
                                "WHERE account_id=? AND worker_id=? AND "
                                "(status!='settled' OR settled_at>?)",
                                (self.account_id, worker_id, now - self.policy.burn_window_seconds)).fetchall()
            burn = 0
            for row in recent:
                item = Reservation.model_validate_json(row["body"])
                burn += (int(row["tokens"]) if row["tokens"] is not None else
                         item.bound.input_tokens + item.bound.max_output_tokens)
            if burn >= self.policy.burn_rate_tokens:
                reason, sleep = "worker_burn_rate", self.policy.burn_window_seconds
        return BudgetSnapshot(account_id=self.account_id, sleeping=reason is not None,
                              reason=reason, sleep_seconds=sleep, tokens=None if uncertain or pending else tokens,
                              estimated_cost_usd=None if uncertain or pending else spent,
                              reserved_estimate_usd=holds, uncertain_reservations=uncertain,
                              pending_reservations=pending)

    def snapshot(self, worker_id: str | None = None) -> BudgetSnapshot:
        with self._transaction() as db:
            return self._snapshot(db, worker_id, self._now())

    def reserve(self, worker_id: str, task_id: str, bound: ExecutionBound) -> Reservation:
        bound = ExecutionBound.model_validate(bound.model_dump())
        if not worker_id.strip() or not task_id.strip():
            raise ValueError("worker_id and task_id are required")
        if not bound.provider_enforced:
            raise BudgetBlocked("provider_bound_not_enforced")
        prices = self.policy.prices
        if prices is None or (prices.provider, prices.model) != (bound.provider, bound.model):
            raise BudgetBlocked("explicit_matching_model_prices_required")
        total_bound = bound.input_tokens + bound.max_output_tokens
        if total_bound > self.policy.max_tokens:
            raise BudgetBlocked("task_token_bound_exceeded")
        estimate = self._estimate(bound.input_tokens, bound.max_output_tokens)
        now = self._now()
        with self._transaction() as db:
            state = self._snapshot(db, worker_id, now)
            if state.sleeping:
                raise BudgetBlocked(state.reason or "account_sleeping", state.sleep_seconds)
            if db.execute("SELECT 1 FROM reservations WHERE account_id=? AND task_id=?",
                          (self.account_id, task_id)).fetchone():
                raise BudgetBlocked("task_already_reserved_no_retry")
            recent = db.execute("SELECT body,tokens FROM reservations WHERE account_id=? AND worker_id=? "
                                "AND (status!='settled' OR settled_at>?)",
                                (self.account_id, worker_id, now - self.policy.burn_window_seconds)).fetchall()
            burn = 0
            for row in recent:
                previous = Reservation.model_validate_json(row["body"])
                burn += (int(row["tokens"]) if row["tokens"] is not None else
                         previous.bound.input_tokens + previous.bound.max_output_tokens)
            if burn + total_bound > self.policy.burn_rate_tokens:
                raise BudgetBlocked("worker_burn_rate", self.policy.burn_window_seconds)
            spent = float(db.execute("SELECT COALESCE(SUM(estimate_usd),0) FROM reservations "
                                     "WHERE account_id=?", (self.account_id,)).fetchone()[0])
            if spent + state.reserved_estimate_usd + estimate > self.policy.max_cost_usd:
                raise BudgetBlocked("account_reservation_capacity", self.policy.burn_window_seconds)
            reservation = Reservation(reservation_id=uuid4().hex, account_id=self.account_id,
                                      worker_id=worker_id, task_id=task_id, bound=bound,
                                      reserved_estimate_usd=estimate, created_at=now)
            db.execute("INSERT INTO reservations VALUES (?,?,?,?,?,'pending',?,NULL,NULL,NULL,?)",
                       (reservation.reservation_id, self.account_id, worker_id, task_id,
                        reservation.model_dump_json(), now, estimate))
            return reservation

    def _stored(self, db: sqlite3.Connection, reservation: Reservation) -> sqlite3.Row:
        row = db.execute("SELECT * FROM reservations WHERE reservation_id=? AND account_id=?",
                         (reservation.reservation_id, self.account_id)).fetchone()
        if not isinstance(row, sqlite3.Row) or Reservation.model_validate_json(row["body"]) != reservation:
            raise ValueError("reservation identity does not match durable hold")
        return row

    def mark_uncertain(self, reservation: Reservation) -> BudgetSnapshot:
        return self.settle(reservation, None)

    def settle(self, reservation: Reservation, usage: JsonValue) -> BudgetSnapshot:
        reservation = Reservation.model_validate(reservation.model_dump())
        reported = _usage(usage)  # Same strict nonnegative integer + consistent-total gateway parser.
        if reported is not None and reported.total_tokens > 2**63 - 1:
            reported = None  # Cannot persist safely as a SQLite integer; retain uncertain hold.
        now = self._now()
        with self._transaction() as db:
            row = self._stored(db, reservation)
            if row["status"] != "pending":
                # Idempotent replay does not overwrite unknown evidence or charge twice.
                return self._snapshot(db, reservation.worker_id, now)
            if now < reservation.created_at:
                raise ValueError("time cannot move backwards")
            try:
                estimate = (self._estimate(reported.prompt_tokens, reported.completion_tokens)
                            if reported is not None else None)
            except (BudgetBlocked, OverflowError):
                reported, estimate = None, None
            if reported is None:
                db.execute("UPDATE reservations SET status='uncertain',settled_at=? WHERE reservation_id=?",
                           (now, reservation.reservation_id))
                db.execute("UPDATE accounts SET breaker=COALESCE(breaker,'unknown_usage') WHERE account_id=?",
                           (self.account_id,))
            else:
                assert estimate is not None
                db.execute("UPDATE reservations SET status='settled',settled_at=?,tokens=?,estimate_usd=? "
                           "WHERE reservation_id=?", (now, reported.total_tokens, estimate,
                                                      reservation.reservation_id))
                spent = db.execute("SELECT COALESCE(SUM(estimate_usd),0) FROM reservations WHERE account_id=?",
                                   (self.account_id,)).fetchone()[0]
                violated = (reported.prompt_tokens > reservation.bound.input_tokens or
                            reported.completion_tokens > reservation.bound.max_output_tokens or
                            reported.total_tokens > self.policy.max_tokens)
                reason = "provider_bound_violated" if violated else None
                if spent >= self.policy.max_cost_usd:
                    reason = "account_cost_estimate_exhausted"
                if reason:
                    db.execute("UPDATE accounts SET breaker=COALESCE(breaker,?) WHERE account_id=?",
                               (reason, self.account_id))
            return self._snapshot(db, reservation.worker_id, now)
