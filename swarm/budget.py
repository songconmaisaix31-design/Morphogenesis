"""Atomic swarm-run admission estimates. Unknown execution never releases a hold."""

from __future__ import annotations

import math
import json
import sqlite3
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from pydantic import JsonValue

from orchestration.gateway import _usage
from swarm.models import BudgetPolicy, BudgetSnapshot, ExecutionBound, Reservation
from swarm.task_ledger import connection, enable_wal


class BudgetBlocked(RuntimeError):
    def __init__(self, reason: str, sleep_seconds: float = 60.0) -> None:
        super().__init__(reason)
        self.reason, self.sleep_seconds = reason, sleep_seconds


class BudgetLedger:
    def __init__(self, path: str | Path, swarm_id: str, policy: BudgetPolicy, *,
                 clock: Callable[[], float] = time.time) -> None:
        policy = BudgetPolicy.model_validate(policy.model_dump())
        if not swarm_id.strip():
            raise ValueError("swarm_id is required")
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.swarm_id, self.policy, self.clock = swarm_id, policy, clock
        enable_wal(self.path)
        with self._transaction() as db:
            if db.execute("SELECT 1 FROM sqlite_master WHERE name='accounts'").fetchone():
                raise ValueError("legacy account budget requires explicit migration; preserve its holds")
            db.execute("CREATE TABLE IF NOT EXISTS swarm_budgets (swarm_id TEXT PRIMARY KEY, "
                       "policy_json TEXT NOT NULL, breaker TEXT, started_at REAL NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS budget_reservations (reservation_id TEXT PRIMARY KEY, "
                       "swarm_id TEXT NOT NULL, worker_id TEXT NOT NULL, task_id TEXT NOT NULL, "
                       "body TEXT NOT NULL, status TEXT NOT NULL, created_at REAL NOT NULL, "
                       "settled_at REAL, tokens INTEGER, estimate_usd REAL, reserved_usd REAL NOT NULL, "
                       "request_id TEXT NOT NULL, usage_metering TEXT NOT NULL, request_bound TEXT NOT NULL, admission_control TEXT NOT NULL, cost TEXT NOT NULL, settlement TEXT, admitted_usd REAL, UNIQUE(swarm_id,request_id))")
            db.execute("CREATE INDEX IF NOT EXISTS budget_reservations_swarm ON "
                       "budget_reservations(swarm_id,worker_id,created_at)")
            row = db.execute("SELECT policy_json FROM swarm_budgets WHERE swarm_id=?", (swarm_id,)).fetchone()
            if row is None:
                db.execute("INSERT INTO swarm_budgets VALUES (?,?,NULL,?)", (swarm_id, policy.model_dump_json(), self._now()))
            elif BudgetPolicy.model_validate_json(row[0]) != policy:
                raise ValueError("swarm policy differs from durable policy; cannot reset budget")

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        with connection(self.path, write=True) as db:
            yield db

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
        swarm = db.execute("SELECT breaker FROM swarm_budgets WHERE swarm_id=?", (self.swarm_id,)).fetchone()
        rows = db.execute("SELECT status,tokens,estimate_usd,reserved_usd,request_bound,admitted_usd,usage_metering,cost FROM budget_reservations "
                          "WHERE swarm_id=?", (self.swarm_id,)).fetchall()
        uncertain = sum(row["status"] == "uncertain" for row in rows)
        pending = sum(row["status"] == "pending" for row in rows)
        holds = sum(float(row["reserved_usd"]) for row in rows if row["status"] != "settled")
        spent = sum(float(row["estimate_usd"]) for row in rows if row["estimate_usd"] is not None)
        tokens = sum(int(row["tokens"]) for row in rows if row["tokens"] is not None)
        usage_unknown = any(row["usage_metering"] == "unknown" for row in rows)
        cost_unknown = any(row["cost"] == "unknown" for row in rows) or self.policy.prices is None
        reason = swarm["breaker"]
        sleep = self.policy.burn_window_seconds if reason else 0.0
        if worker_id is not None and reason is None:
            recent = db.execute("SELECT body,status,tokens,created_at,settled_at FROM budget_reservations "
                                "WHERE swarm_id=? AND worker_id=? AND "
                                "(status NOT IN ('settled','unknown_cost_allowed') OR settled_at>?)",
                                (self.swarm_id, worker_id, now - self.policy.burn_window_seconds)).fetchall()
            burn = 0
            for row in recent:
                item = Reservation.model_validate_json(row["body"])
                burn += (int(row["tokens"]) if row["tokens"] is not None else
                         item.bound.input_tokens + item.bound.max_output_tokens)
            if burn >= self.policy.burn_rate_tokens:
                reason, sleep = "worker_burn_rate", self.policy.burn_window_seconds
        return BudgetSnapshot(swarm_id=self.swarm_id, sleeping=reason is not None,
                              reason=reason, sleep_seconds=sleep, tokens=None if usage_unknown else tokens,
                              estimated_cost_usd=None if cost_unknown else spent,
                              reserved_estimate_usd=holds, uncertain_reservations=uncertain,
                              pending_reservations=pending,
                              usage_metering="unknown" if usage_unknown else "verified",
                              request_bound="verified" if rows and all(r["request_bound"] == "verified" for r in rows) else "unbounded",
                              admission_control=self.policy.admission_control,
                              cost="unknown" if cost_unknown else "estimated",
                              admission_charged_usd=sum(float(r["admitted_usd"] or 0) for r in rows),
                              unreconciled_reservations=len(rows))

    def snapshot(self, worker_id: str | None = None) -> BudgetSnapshot:
        with connection(self.path) as db:
            return self._snapshot(db, worker_id, self._now())

    def pending(self, worker_id: str, *, limit: int = 100) -> list[Reservation]:
        """Read durable in-flight holds even when worker status was never written.

        Runtime decides whether the owner is recovering before marking uncertain;
        merely observing a live in-flight request must not change its state.
        """
        if not worker_id.strip() or not 1 <= limit <= 1000:
            raise ValueError("worker_id required; limit must be in [1,1000]")
        with connection(self.path) as db:
            return [Reservation.model_validate_json(row[0]) for row in db.execute(
                "SELECT body FROM budget_reservations WHERE swarm_id=? AND worker_id=? AND status='pending' "
                "ORDER BY created_at,reservation_id LIMIT ?", (self.swarm_id, worker_id, limit))]

    def reserve(self, worker_id: str, task_id: str, bound: ExecutionBound, *, request_id: str | None = None) -> Reservation:
        bound = ExecutionBound.model_validate(bound.model_dump())
        if not worker_id.strip() or not task_id.strip():
            raise ValueError("worker_id and task_id are required")
        prices = self.policy.prices
        allowance = self.policy.unbounded_reservation_usd
        if bound.request_bound == "unbounded" and (allowance is None or self.policy.admission_control != "enabled"):
            raise BudgetBlocked("explicit_unbounded_admission_required")
        if prices is not None and (prices.provider, prices.model) != (bound.provider, bound.model):
            raise BudgetBlocked("explicit_matching_model_prices_required")
        total_bound = bound.input_tokens + bound.max_output_tokens
        if total_bound > self.policy.max_tokens:
            raise BudgetBlocked("task_token_bound_exceeded")
        estimate = self._estimate(bound.input_tokens, bound.max_output_tokens) if prices is not None else None
        if bound.request_bound == "verified":
            assert bound.max_cost_usd is not None
            if estimate is None:
                raise BudgetBlocked("explicit_matching_model_prices_required")
            if bound.max_cost_usd < estimate:
                raise BudgetBlocked("request_cost_bound_below_estimate")
            reservation_amount = bound.max_cost_usd
        else:
            assert allowance is not None
            reservation_amount = max(allowance, estimate) if estimate is not None else allowance
        request_id = task_id if request_id is None else request_id
        if not request_id.strip():
            raise ValueError("request_id is required")
        now = self._now()
        with self._transaction() as db:
            start = float(db.execute("SELECT started_at FROM swarm_budgets WHERE swarm_id=?", (self.swarm_id,)).fetchone()[0])
            if now < start or now - start >= self.policy.limits.max_runtime_seconds:
                raise BudgetBlocked("run_runtime_limit")
            count = db.execute("SELECT COUNT(*),COUNT(DISTINCT task_id) FROM budget_reservations WHERE swarm_id=?", (self.swarm_id,)).fetchone()
            if count[0] >= self.policy.limits.max_attempts:
                raise BudgetBlocked("max_attempts")
            task_count = db.execute("SELECT COUNT(*) FROM budget_reservations WHERE swarm_id=? AND task_id=?", (self.swarm_id,task_id)).fetchone()[0]
            if task_count >= self.policy.limits.max_attempts_per_task:
                raise BudgetBlocked("max_attempts_per_task")
            if not task_count and count[1] >= self.policy.limits.max_tasks:
                raise BudgetBlocked("max_tasks")
            state = self._snapshot(db, worker_id, now)
            if state.sleeping:
                raise BudgetBlocked(state.reason or "swarm_sleeping", state.sleep_seconds)
            if db.execute("SELECT 1 FROM budget_reservations WHERE swarm_id=? AND (request_id=? OR (task_id=? AND status!='settled'))",
                          (self.swarm_id, request_id, task_id)).fetchone():
                raise BudgetBlocked("task_already_reserved_no_retry")
            recent = db.execute("SELECT body,tokens FROM budget_reservations WHERE swarm_id=? AND worker_id=? "
                                "AND (status NOT IN ('settled','unknown_cost_allowed') OR settled_at>?)",
                                (self.swarm_id, worker_id, now - self.policy.burn_window_seconds)).fetchall()
            burn = 0
            for row in recent:
                previous = Reservation.model_validate_json(row["body"])
                burn += (int(row["tokens"]) if row["tokens"] is not None else
                         previous.bound.input_tokens + previous.bound.max_output_tokens)
            if burn + total_bound > self.policy.burn_rate_tokens:
                raise BudgetBlocked("worker_burn_rate", self.policy.burn_window_seconds)
            spent = float(db.execute("SELECT COALESCE(SUM(admitted_usd),0) FROM budget_reservations "
                                     "WHERE swarm_id=?", (self.swarm_id,)).fetchone()[0])
            if self.policy.admission_control == "enabled" and spent + state.reserved_estimate_usd + reservation_amount > self.policy.max_cost_usd:
                raise BudgetBlocked("swarm_reservation_capacity", self.policy.burn_window_seconds)
            reservation = Reservation(reservation_id=uuid4().hex, swarm_id=self.swarm_id,
                                      worker_id=worker_id, task_id=task_id, bound=bound,
                                      reserved_estimate_usd=reservation_amount, created_at=now, request_id=request_id,
                                      request_bound=bound.request_bound, admission_control=self.policy.admission_control)
            db.execute("INSERT INTO budget_reservations VALUES (?,?,?,?,?,'pending',?,NULL,NULL,NULL,?,?,'unknown',?,?,'unknown',NULL,NULL)",
                       (reservation.reservation_id, self.swarm_id, worker_id, task_id,
                        reservation.model_dump_json(), now, reservation_amount, request_id, bound.request_bound,
                        self.policy.admission_control))
            return reservation

    def _stored(self, db: sqlite3.Connection, reservation: Reservation) -> sqlite3.Row:
        row = db.execute("SELECT * FROM budget_reservations WHERE reservation_id=? AND swarm_id=?",
                         (reservation.reservation_id, self.swarm_id)).fetchone()
        if not isinstance(row, sqlite3.Row) or Reservation.model_validate_json(row["body"]) != reservation:
            raise ValueError("reservation identity does not match durable hold")
        return row

    def mark_uncertain(self, reservation: Reservation) -> BudgetSnapshot:
        return self.settle(reservation, None)

    def _trip(self, db: sqlite3.Connection, reason: str) -> None:
        priorities = {"swarm_cost_estimate_exhausted": 1, "unknown_cost": 2,
                      "provider_bound_violated": 3, "request_token_limit_exceeded": 3, "unknown_usage": 4}
        previous = db.execute("SELECT breaker FROM swarm_budgets WHERE swarm_id=?", (self.swarm_id,)).fetchone()[0]
        if previous is None or priorities[reason] > priorities.get(previous, 4):
            db.execute("UPDATE swarm_budgets SET breaker=? WHERE swarm_id=?", (reason, self.swarm_id))

    def settle(self, reservation: Reservation, usage: JsonValue) -> BudgetSnapshot:
        reservation = Reservation.model_validate(reservation.model_dump())
        reported = _usage(usage)  # Same strict nonnegative integer + consistent-total gateway parser.
        if reported is not None and reported.total_tokens > 2**63 - 1:
            reported = None  # Cannot persist safely as a SQLite integer; retain uncertain hold.
        now = self._now()
        settlement = json.dumps([reported.prompt_tokens, reported.completion_tokens, reported.total_tokens]) if reported else None
        with self._transaction() as db:
            row = self._stored(db, reservation)
            if row["status"] != "pending":
                if row["settlement"] is not None and settlement is not None and row["settlement"] != settlement:
                    raise ValueError("conflicting usage settlement")
                # Idempotent replay does not overwrite unknown evidence or charge twice.
                return self._snapshot(db, reservation.worker_id, now)
            if now < reservation.created_at:
                raise ValueError("time cannot move backwards")
            try:
                estimate = (self._estimate(reported.prompt_tokens, reported.completion_tokens)
                            if reported is not None else None)
            except (BudgetBlocked, OverflowError):
                estimate = None  # Keep valid observed tokens even if monetary evidence is missing.
            if reported is None:
                db.execute("UPDATE budget_reservations SET status='uncertain',settled_at=? WHERE reservation_id=?",
                           (now, reservation.reservation_id))
                if not self.policy.allow_unknown_usage:
                    self._trip(db, "unknown_usage")
            else:
                if estimate is None:
                    # Operator admission allowance is not a model price. Preserve
                    # the full hold while recording the independently known usage.
                    status = "unknown_cost_allowed" if self.policy.allow_unknown_cost else "uncertain"
                    db.execute("UPDATE budget_reservations SET status=?,usage_metering='verified',cost='unknown',"
                               "settled_at=?,tokens=?,settlement=? WHERE reservation_id=?",
                               (status, now, reported.total_tokens, settlement, reservation.reservation_id))
                    if not self.policy.allow_unknown_cost:
                        self._trip(db, "unknown_cost")
                else:
                    # Usage plus local prices is not a bill. Never free committed
                    # allowance on a lower estimate, even for an unbounded request.
                    admitted = max(estimate, reservation.reserved_estimate_usd)
                    db.execute("UPDATE budget_reservations SET status='settled',usage_metering='verified',cost='estimated',settled_at=?,tokens=?,estimate_usd=?,settlement=?,admitted_usd=? "
                               "WHERE reservation_id=?", (now, reported.total_tokens, estimate, settlement, admitted,
                                                          reservation.reservation_id))
                spent = db.execute("SELECT COALESCE(SUM(estimate_usd),0) FROM budget_reservations WHERE swarm_id=?",
                                   (self.swarm_id,)).fetchone()[0]
                violated = (reported.prompt_tokens > reservation.bound.input_tokens or
                            reported.completion_tokens > reservation.bound.max_output_tokens or
                            reported.total_tokens > self.policy.max_tokens)
                violated = violated or (reservation.bound.request_bound == "verified" and estimate is not None
                                        and estimate > reservation.reserved_estimate_usd)
                if violated:
                    self._trip(db, "provider_bound_violated" if reservation.bound.provider_enforced
                               else "request_token_limit_exceeded")
                elif estimate is not None and spent >= self.policy.max_cost_usd:
                    self._trip(db, "swarm_cost_estimate_exhausted")
            return self._snapshot(db, reservation.worker_id, now)
