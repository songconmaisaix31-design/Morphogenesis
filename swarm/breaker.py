"""Shared four-state circuit breaker; routing eligibility only.

States: insufficient_evidence -> normal -> suspended -> probing_recovery.
Evidence is FC-B's (swarm/fault_observations.py), consumed structurally via
the protocols below so this track neither imports nor copies that module:
FaultAggregate windows the facts and read().issues exposes incomplete JSONL.
Durable state lives in its own SQLite file written through
swarm.task_ledger.connection short BEGIN IMMEDIATE transactions (the same
helper FC-B's sidecar lock uses), so every cooperating worker sees one shared
state and half-open probe slots are claimed atomically.

Red lines honored here:
- Breaker state only answers "may this (provider, reason) be routed to".
  Budgets, leases and attempt accounting are never read, written or bypassed;
  this module imports none of their owners.
- Only service-failure facts drive transitions. There is no event for answer
  correctness, and an unknown event name raises instead of passing silently.
- An unknown Retry-After stays unknown: the injected cooldown_seconds (> 0,
  never 0) decides the first probe time; a known hint is used verbatim as the
  absolute deadline.

cachetools.TTLCache (MIT) holds the sliding evidence window in-process with an
injectable timer; BreakerConfig enforces window_seconds >=
aggregation_period_seconds so samples cannot expire before the next
aggregation cycle. The cache is hysteresis only: absence of cached evidence
never unsuspends a breaker -- recovery happens exclusively through a won
probe, so a restart loses smoothing but never resurrects a probe slot before
its persisted deadline.
"""

from __future__ import annotations

import json
import math
import sqlite3
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Literal, Protocol, get_args

from cachetools import TTLCache
from pydantic import BaseModel, ConfigDict, Field, model_validator

from swarm.task_ledger import connection, enable_wal, now_checked

BreakerState = Literal["insufficient_evidence", "normal", "suspended", "probing_recovery"]
BreakerEvent = Literal["aggregate", "cooldown_expired", "probe_success", "probe_failure"]
BreakerAction = Literal[
    "persist_state", "claim_probe_slot", "release_probe_slot", "set_cooldown", "reset_window"
]

_STATES = frozenset(get_args(BreakerState))
_EVENTS = frozenset(get_args(BreakerEvent))


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True, allow_inf_nan=False)


class FaultAggregateLike(Protocol):
    """Structural mirror of FC-B's FaultAggregate (field names verbatim).

    Members are read-only properties so the real frozen pydantic model
    satisfies this protocol covariantly under strict mypy.
    """

    @property
    def provider(self) -> str: ...
    @property
    def normalized_reason(self) -> str: ...
    @property
    def sample_count(self) -> int: ...
    @property
    def confirmed_rejections(self) -> int: ...
    @property
    def first_occurred_at(self) -> float: ...
    @property
    def last_occurred_at(self) -> float: ...
    @property
    def retry_after_until(self) -> float | None: ...


class FaultIssueLike(Protocol):
    """Structural mirror of FC-B's FaultReadIssue."""

    @property
    def line_number(self) -> int: ...
    @property
    def reason(self) -> str: ...


class FaultReadLike(Protocol):
    """Structural mirror of FC-B's FaultReadResult (issues are surfaced, never swallowed)."""

    @property
    def issues(self) -> tuple[FaultIssueLike, ...]: ...


class FaultStoreLike(Protocol):
    """Structural mirror of the FC-B store methods this track consumes."""

    def read(self) -> FaultReadLike: ...

    def aggregate(
        self, *, now: float, window_seconds: float
    ) -> Mapping[tuple[str, str], FaultAggregateLike]: ...


class BreakerConfig(_Model):
    """Every knob injected; the breaker body contains zero magic numbers.

    direct_suspend_reasons lists FC-B normalized_reason values whose confirmed
    rejections (e.g. arrearage) suspend immediately, bypassing sample floors.
    The default covers both canonical spellings in circulation: FC-A emits
    "billing_arrearage" today, while "arrearage" appears in earlier contracts;
    callers can inject a narrower or wider vocabulary without editing this file.
    """

    window_seconds: float = Field(gt=0)
    aggregation_period_seconds: float = Field(gt=0)
    failure_threshold: int = Field(ge=1)
    min_samples: int = Field(default=5, ge=1)
    cooldown_seconds: float = Field(gt=0)
    probe_ttl_seconds: float = Field(gt=0)
    window_max_keys: int = Field(default=1024, ge=1)
    direct_suspend_reasons: frozenset[str] = frozenset({"arrearage", "billing_arrearage"})

    @model_validator(mode="after")
    def window_covers_aggregation(self) -> BreakerConfig:
        # TTLCache pitfall: a window shorter than the aggregation period would
        # drop samples before the next cycle can ever count them.
        if self.window_seconds < self.aggregation_period_seconds:
            raise ValueError("window_seconds must be >= aggregation_period_seconds")
        return self


class TransitionParams(_Model):
    """All facts and configuration the pure transition needs; nothing else."""

    now: float = Field(ge=0)
    reason: str = Field(min_length=1)
    config: BreakerConfig
    sample_count: int = Field(default=0, ge=0)
    confirmed_rejections: int = Field(default=0, ge=0)
    retry_after_until: float | None = Field(default=None, ge=0)
    cooldown_until: float | None = Field(default=None, ge=0)
    probe_expires_at: float | None = Field(default=None, ge=0)
    probe_owner: str | None = Field(default=None, min_length=1)
    worker_id: str | None = Field(default=None, min_length=1)


def _suspension_required(params: TransitionParams) -> bool:
    config = params.config
    if params.reason in config.direct_suspend_reasons and params.confirmed_rejections > 0:
        return True  # confirmed arrearage-class rejection bypasses sample floors
    return (
        params.sample_count >= config.failure_threshold
        and params.sample_count >= config.min_samples
    )


def _live_probe(params: TransitionParams) -> bool:
    return (
        params.worker_id is not None
        and params.worker_id == params.probe_owner
        and params.probe_expires_at is not None
        and params.probe_expires_at > params.now
    )


def cooldown_deadline(params: TransitionParams) -> float:
    """Known Retry-After hint verbatim; unknown stays unknown -> injected cooldown.

    Never fabricates 0: cooldown_seconds is validated > 0, and a hint that
    already lies in the past is the server's own statement, not a fabrication.
    """
    if params.retry_after_until is not None:
        return params.retry_after_until
    return params.now + params.config.cooldown_seconds


def transition(
    state: BreakerState, event: BreakerEvent, params: TransitionParams
) -> tuple[BreakerState, tuple[BreakerAction, ...]]:
    """Pure decision core: no I/O, no clock reads, no mutation.

    Returns the new state and the actions the durable store must apply. An
    unchanged state carries no actions. Only the four service-failure events
    exist; anything else (notably answer-correctness signals) is rejected.
    """
    # TODO-HUMAN-REVIEW: complete four-state transition table.
    if state not in _STATES:
        raise ValueError(f"unknown breaker state: {state!r}")
    if event not in _EVENTS:
        raise ValueError(
            f"unknown breaker event: {event!r}; only service-failure facts drive transitions"
        )

    if event == "aggregate":
        if state in ("suspended", "probing_recovery"):
            # Probe outcomes arrive via probe_* events; while suspended only a
            # strictly later server hint may extend the deadline (never shorten,
            # never re-trigger a fresh cooldown from stale in-window evidence).
            if (
                state == "suspended"
                and params.retry_after_until is not None
                and (params.cooldown_until is None or params.retry_after_until > params.cooldown_until)
            ):
                return "suspended", ("persist_state", "set_cooldown")
            return state, ()
        if _suspension_required(params):
            return "suspended", ("persist_state", "set_cooldown")
        if state == "insufficient_evidence" and params.sample_count >= params.config.min_samples:
            return "normal", ("persist_state",)
        return state, ()

    if event == "cooldown_expired":
        if state == "suspended":
            if params.cooldown_until is not None and params.cooldown_until <= params.now:
                return "probing_recovery", ("persist_state", "claim_probe_slot")
            return state, ()
        if state == "probing_recovery":
            # Owner died or restarted mid-probe: the slot is reclaimable once
            # its persisted TTL lapses, never before.
            if params.probe_expires_at is not None and params.probe_expires_at <= params.now:
                return "probing_recovery", ("persist_state", "claim_probe_slot")
            return state, ()
        return state, ()

    if event == "probe_success":
        if state == "probing_recovery" and _live_probe(params):
            return "normal", ("persist_state", "release_probe_slot", "reset_window")
        return state, ()

    # event == "probe_failure"
    if state == "probing_recovery" and _live_probe(params):
        return "suspended", ("persist_state", "release_probe_slot", "set_cooldown")
    return state, ()


class BreakerView(_Model):
    """Read-only snapshot of one (provider, reason) breaker."""

    provider: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    state: BreakerState = "insufficient_evidence"
    sample_count: int = Field(default=0, ge=0)
    confirmed_rejections: int = Field(default=0, ge=0)
    cooldown_until: float | None = None
    retry_after_until: float | None = None
    probe_owner: str | None = None
    probe_token: int = Field(default=0, ge=0)
    probe_expires_at: float | None = None
    updated_at: float | None = None


class BreakerChange(_Model):
    provider: str
    reason: str
    event: BreakerEvent
    from_state: BreakerState
    to_state: BreakerState


class ObservationReport(_Model):
    """What one observation cycle saw and changed.

    evidence_complete=False means FC-B reported invalid/duplicate/conflicting
    JSONL lines: decisions were made from the valid facts only, and callers
    must not read the absence of failures as health.
    """

    now: float
    evidence_complete: bool = True
    issues: tuple[tuple[int, str], ...] = ()
    changes: tuple[BreakerChange, ...] = ()


class SharedBreaker:
    """Durable cross-worker breaker over FC-B fault facts.

    Answers routing-eligibility questions only. It holds no budget, lease or
    attempt authority, and a True from eligible() never releases a caller from
    those owners' checks.
    """

    def __init__(
        self,
        path: str | Path,
        swarm_id: str,
        config: BreakerConfig,
        *,
        clock: Callable[[], float] = time.time,
        timeout_seconds: float = 10,
    ) -> None:
        if not swarm_id.strip():
            raise ValueError("swarm_id required")
        if not math.isfinite(timeout_seconds) or not 0 <= timeout_seconds <= 60:
            raise ValueError("timeout_seconds must be in [0,60]")
        self.path = Path(path).resolve()
        self.swarm_id = swarm_id
        self.config = config
        self.clock = clock
        self.timeout_seconds = timeout_seconds
        self._window: TTLCache[tuple[str, str], FaultAggregateLike] = TTLCache(
            maxsize=config.window_max_keys, ttl=config.window_seconds, timer=clock
        )
        enable_wal(self.path, timeout_seconds)
        with self._write() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS breaker_states ("
                "swarm_id TEXT NOT NULL, provider TEXT NOT NULL, reason TEXT NOT NULL, "
                "state TEXT NOT NULL, sample_count INTEGER NOT NULL, confirmed_rejections INTEGER NOT NULL, "
                "cooldown_until REAL, retry_after_until REAL, probe_owner TEXT, "
                "probe_token INTEGER NOT NULL DEFAULT 0, probe_expires_at REAL, "
                "updated_at REAL NOT NULL, PRIMARY KEY(swarm_id, provider, reason))"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS breaker_audit ("
                "sequence INTEGER PRIMARY KEY AUTOINCREMENT, swarm_id TEXT NOT NULL, "
                "provider TEXT NOT NULL, reason TEXT NOT NULL, event TEXT NOT NULL, "
                "from_state TEXT NOT NULL, to_state TEXT NOT NULL, at REAL NOT NULL, body TEXT NOT NULL)"
            )

    def _at(self, now: float | None) -> float:
        return now_checked(self.clock) if now is None else now_checked(lambda: now)

    @contextmanager
    def _write(self) -> Iterator[sqlite3.Connection]:
        with connection(self.path, write=True, timeout=self.timeout_seconds) as db:
            yield db

    def _row(self, db: sqlite3.Connection, provider: str, reason: str) -> sqlite3.Row | None:
        row = db.execute(
            "SELECT * FROM breaker_states WHERE swarm_id=? AND provider=? AND reason=?",
            (self.swarm_id, provider, reason),
        ).fetchone()
        return row if isinstance(row, sqlite3.Row) else None

    @staticmethod
    def _view(provider: str, reason: str, row: sqlite3.Row | None) -> BreakerView:
        if row is None:
            return BreakerView(provider=provider, reason=reason)
        state = str(row["state"])
        if state not in _STATES:
            raise RuntimeError(f"corrupt persisted breaker state: {state!r}")
        return BreakerView(
            provider=str(row["provider"]),
            reason=str(row["reason"]),
            state=state,  # type: ignore[arg-type]
            sample_count=int(row["sample_count"]),
            confirmed_rejections=int(row["confirmed_rejections"]),
            cooldown_until=row["cooldown_until"],
            retry_after_until=row["retry_after_until"],
            probe_owner=row["probe_owner"],
            probe_token=int(row["probe_token"]),
            probe_expires_at=row["probe_expires_at"],
            updated_at=row["updated_at"],
        )

    def _audit(
        self,
        db: sqlite3.Connection,
        provider: str,
        reason: str,
        event: str,
        change: BreakerChange,
        body: Mapping[str, object],
        at: float,
    ) -> None:
        db.execute(
            "INSERT INTO breaker_audit(swarm_id,provider,reason,event,from_state,to_state,at,body) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (
                self.swarm_id, provider, reason, event, change.from_state, change.to_state,
                at, json.dumps(dict(body), sort_keys=True),
            ),
        )

    def view(self, provider: str, reason: str) -> BreakerView:
        with connection(self.path, timeout=self.timeout_seconds) as db:
            return self._view(provider, reason, self._row(db, provider, reason))

    def views(self, *, limit: int = 1000) -> list[BreakerView]:
        if not 1 <= limit <= 10000:
            raise ValueError("invalid views limit")
        with connection(self.path, timeout=self.timeout_seconds) as db:
            rows = db.execute(
                "SELECT * FROM breaker_states WHERE swarm_id=? ORDER BY provider,reason LIMIT ?",
                (self.swarm_id, limit),
            ).fetchall()
            return [self._view(str(r["provider"]), str(r["reason"]), r) for r in rows]

    def eligible(self, provider: str, reason: str, *, worker_id: str | None = None,
                 now: float | None = None) -> bool:
        """Routing eligibility only; budgets and leases remain their owners' job."""
        at = self._at(now)
        snapshot = self.view(provider, reason)
        if snapshot.state in ("insufficient_evidence", "normal"):
            return True
        if snapshot.state == "suspended":
            return False
        return (
            worker_id is not None
            and worker_id == snapshot.probe_owner
            and snapshot.probe_expires_at is not None
            and snapshot.probe_expires_at > at
        )

    def windowed_evidence(self) -> dict[tuple[str, str], int]:
        """Live TTLCache window contents: (provider, reason) -> sample_count."""
        live: dict[tuple[str, str], int] = {}
        for key in list(self._window):
            cached = self._window.get(key)
            if cached is not None:
                live[key] = cached.sample_count
        return live

    def observe(self, store: FaultStoreLike, *, now: float | None = None) -> ObservationReport:
        """One observation cycle against an FC-B store (or its structural equal)."""
        at = self._at(now)
        snapshot = store.read()
        aggregates = store.aggregate(now=at, window_seconds=self.config.window_seconds)
        return self.apply_aggregates(aggregates, issues=snapshot.issues, now=at)

    def apply_aggregates(
        self,
        aggregates: Mapping[tuple[str, str], FaultAggregateLike],
        *,
        issues: Sequence[FaultIssueLike] = (),
        now: float | None = None,
    ) -> ObservationReport:
        at = self._at(now)
        effective: dict[tuple[str, str], FaultAggregateLike] = {}
        for key in list(self._window):
            cached = self._window.get(key)
            if cached is not None:
                effective[key] = cached
        for aggregate in aggregates.values():
            key = (aggregate.provider, aggregate.normalized_reason)
            self._window[key] = aggregate
            effective[key] = aggregate
        changes: list[BreakerChange] = []
        for key in sorted(effective):
            change = self._apply_aggregate(effective[key], now=at)
            if change is not None:
                changes.append(change)
        return ObservationReport(
            now=at,
            evidence_complete=not issues,
            issues=tuple((issue.line_number, issue.reason) for issue in issues),
            changes=tuple(changes),
        )

    def _apply_aggregate(
        self, aggregate: FaultAggregateLike, *, now: float
    ) -> BreakerChange | None:
        provider, reason = aggregate.provider, aggregate.normalized_reason
        with self._write() as db:
            current = self._view(provider, reason, self._row(db, provider, reason))
            params = TransitionParams(
                now=now, reason=reason, config=self.config,
                sample_count=aggregate.sample_count,
                confirmed_rejections=aggregate.confirmed_rejections,
                retry_after_until=aggregate.retry_after_until,
                cooldown_until=current.cooldown_until,
                probe_expires_at=current.probe_expires_at,
                probe_owner=current.probe_owner,
            )
            new_state, actions = transition(current.state, "aggregate", params)
            if not actions:
                return None
            values = self._next_values(current, new_state, actions, params)
            self._upsert(db, provider, reason, values, now)
            change = BreakerChange(
                provider=provider, reason=reason, event="aggregate",
                from_state=current.state, to_state=new_state,
            )
            self._audit(db, provider, reason, "aggregate", change, {
                "sample_count": aggregate.sample_count,
                "confirmed_rejections": aggregate.confirmed_rejections,
                "retry_after_until": aggregate.retry_after_until,
                "cooldown_until": values["cooldown_until"],
                "actions": list(actions),
            }, now)
            return change

    @staticmethod
    def _next_values(
        current: BreakerView,
        new_state: BreakerState,
        actions: tuple[BreakerAction, ...],
        params: TransitionParams,
    ) -> dict[str, object]:
        values: dict[str, object] = {
            "state": new_state,
            "sample_count": current.sample_count,
            "confirmed_rejections": current.confirmed_rejections,
            "cooldown_until": current.cooldown_until,
            "retry_after_until": current.retry_after_until,
            "probe_owner": current.probe_owner,
            "probe_expires_at": current.probe_expires_at,
        }
        if "set_cooldown" in actions:
            values["cooldown_until"] = cooldown_deadline(params)
            values["retry_after_until"] = params.retry_after_until
        if new_state == "suspended" and current.state != "suspended":
            values["sample_count"] = params.sample_count
            values["confirmed_rejections"] = params.confirmed_rejections
            values["probe_owner"] = None
            values["probe_expires_at"] = None
        if new_state == "normal" and current.state == "probing_recovery":
            values.update(sample_count=0, confirmed_rejections=0,
                          cooldown_until=None, retry_after_until=None)
        return values

    def _upsert(self, db: sqlite3.Connection, provider: str, reason: str,
                values: Mapping[str, object], now: float) -> None:
        db.execute(
            "INSERT INTO breaker_states VALUES (?,?,?,?,?,?,?,?,?,0,?,?) "
            "ON CONFLICT(swarm_id,provider,reason) DO UPDATE SET state=excluded.state, "
            "sample_count=excluded.sample_count, confirmed_rejections=excluded.confirmed_rejections, "
            "cooldown_until=excluded.cooldown_until, retry_after_until=excluded.retry_after_until, "
            "probe_owner=excluded.probe_owner, probe_expires_at=excluded.probe_expires_at, "
            "updated_at=excluded.updated_at",
            (
                self.swarm_id, provider, reason, values["state"], values["sample_count"],
                values["confirmed_rejections"], values["cooldown_until"],
                values["retry_after_until"], values["probe_owner"], values["probe_expires_at"],
                now,
            ),
        )

    def try_claim_probe(self, provider: str, reason: str, worker_id: str, *,
                        now: float | None = None) -> BreakerView | None:
        """Atomic half-open claim: at most one worker wins the single probe slot.

        Returns the fresh view for the winner and None for everyone else
        (cooldown not expired, slot already held, or lost the race).
        """
        if not worker_id.strip():
            raise ValueError("worker_id required")
        at = self._at(now)
        with self._write() as db:
            current = self._view(provider, reason, self._row(db, provider, reason))
            params = TransitionParams(
                now=at, reason=reason, config=self.config,
                cooldown_until=current.cooldown_until,
                probe_expires_at=current.probe_expires_at,
                probe_owner=current.probe_owner,
                worker_id=worker_id,
            )
            new_state, actions = transition(current.state, "cooldown_expired", params)
            if new_state != "probing_recovery" or "claim_probe_slot" not in actions:
                return None
            expires_at = at + self.config.probe_ttl_seconds
            # TODO-HUMAN-REVIEW: multi-worker half-open race — the guarded UPDATE
            # inside BEGIN IMMEDIATE plus token fencing admits exactly one winner.
            cursor = db.execute(
                "UPDATE breaker_states SET state='probing_recovery', probe_owner=?, "
                "probe_token=probe_token+1, probe_expires_at=?, updated_at=? "
                "WHERE swarm_id=? AND provider=? AND reason=? AND probe_token=? "
                "AND ((state='suspended' AND cooldown_until IS NOT NULL AND cooldown_until<=?) "
                "OR (state='probing_recovery' AND probe_expires_at IS NOT NULL AND probe_expires_at<=?))",
                (worker_id, expires_at, at, self.swarm_id, provider, reason,
                 current.probe_token, at, at),
            )
            if cursor.rowcount != 1:
                return None
            change = BreakerChange(
                provider=provider, reason=reason, event="cooldown_expired",
                from_state=current.state, to_state="probing_recovery",
            )
            self._audit(db, provider, reason, "probe_claimed", change, {
                "worker_id": worker_id,
                "probe_token": current.probe_token + 1,
                "probe_expires_at": expires_at,
            }, at)
            return self._view(provider, reason, self._row(db, provider, reason))

    def report_probe_success(self, provider: str, reason: str, worker_id: str, *,
                             probe_token: int, now: float | None = None) -> bool:
        return self._finish_probe(provider, reason, worker_id, "probe_success",
                                  probe_token=probe_token, retry_after_until=None, now=now)

    def report_probe_failure(self, provider: str, reason: str, worker_id: str, *,
                             probe_token: int,
                             retry_after_until: float | None = None,
                             now: float | None = None) -> bool:
        return self._finish_probe(provider, reason, worker_id, "probe_failure",
                                  probe_token=probe_token,
                                  retry_after_until=retry_after_until, now=now)

    def _finish_probe(self, provider: str, reason: str, worker_id: str, event: str, *,
                      probe_token: int, retry_after_until: float | None,
                      now: float | None) -> bool:
        """Fenced probe outcome: only the live slot owner's report is applied.

        The caller must pass the probe_token it won from try_claim_probe; the
        UPDATE fences on that exact token. A same-worker stale result (the
        worker reclaimed after its TTL lapsed, so the token advanced) can no
        longer mutate the live slot's state.
        """
        if event not in ("probe_success", "probe_failure"):
            raise ValueError(f"not a probe outcome event: {event!r}")
        if probe_token < 1:
            raise ValueError("probe_token must be the token claimed via try_claim_probe")
        at = self._at(now)
        with self._write() as db:
            current = self._view(provider, reason, self._row(db, provider, reason))
            params = TransitionParams(
                now=at, reason=reason, config=self.config,
                retry_after_until=retry_after_until,
                probe_owner=current.probe_owner,
                probe_expires_at=current.probe_expires_at,
                worker_id=worker_id,
            )
            typed_event: BreakerEvent = event  # type: ignore[assignment]
            new_state, actions = transition(current.state, typed_event, params)
            if not actions:
                return False
            if new_state == "normal":
                fields = ("state=?, probe_owner=NULL, probe_expires_at=NULL, sample_count=0, "
                          "confirmed_rejections=0, cooldown_until=NULL, retry_after_until=NULL, "
                          "updated_at=?")
                args: tuple[object, ...] = (new_state, at)
            else:
                deadline = cooldown_deadline(params)
                fields = ("state=?, probe_owner=NULL, probe_expires_at=NULL, cooldown_until=?, "
                          "retry_after_until=?, updated_at=?")
                args = (new_state, deadline, retry_after_until, at)
            # TODO-HUMAN-REVIEW: same-owner stale probe — the fenced token is the
            # caller-claimed one, not the row's current token, so a late outcome
            # from a reclaimed (superseded) probe can never overwrite the live slot.
            cursor = db.execute(
                f"UPDATE breaker_states SET {fields} WHERE swarm_id=? AND provider=? AND reason=? "
                "AND state='probing_recovery' AND probe_owner=? AND probe_token=? "
                "AND probe_expires_at IS NOT NULL AND probe_expires_at>?",
                (*args, self.swarm_id, provider, reason, worker_id, probe_token, at),
            )
            if cursor.rowcount != 1:
                return False
            if "reset_window" in actions:
                self._window.pop((provider, reason), None)
            change = BreakerChange(
                provider=provider, reason=reason, event=typed_event,
                from_state=current.state, to_state=new_state,
            )
            self._audit(db, provider, reason, event, change, {
                "worker_id": worker_id,
                "retry_after_until": retry_after_until,
                "probe_token": probe_token,
            }, at)
            return True

    def audit(self, *, limit: int = 100) -> list[dict[str, object]]:
        if not 1 <= limit <= 10000:
            raise ValueError("invalid audit limit")
        with connection(self.path, timeout=self.timeout_seconds) as db:
            return [
                {
                    "sequence": int(r["sequence"]), "provider": str(r["provider"]),
                    "reason": str(r["reason"]), "event": str(r["event"]),
                    "from_state": str(r["from_state"]), "to_state": str(r["to_state"]),
                    "at": float(r["at"]), "body": json.loads(str(r["body"])),
                }
                for r in db.execute(
                    "SELECT * FROM breaker_audit WHERE swarm_id=? ORDER BY sequence DESC LIMIT ?",
                    (self.swarm_id, limit),
                )
            ]
