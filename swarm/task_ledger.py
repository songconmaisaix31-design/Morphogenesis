"""Durable SQLite task facts and short, fenced result publication transactions."""
from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
import json
import math
import os
from pathlib import Path
import sqlite3
import time

from pydantic import JsonValue, TypeAdapter

from swarm.models import Lease, Locality, RunLimits, Signal, TaskRecord

_OBJECT = TypeAdapter(dict[str, JsonValue])
Apply = Callable[[Callable[[], None]], None]


def canonical_scope(scope: str | Path) -> str:
    path = Path(scope)
    if not path.is_absolute():
        raise ValueError("scope must be absolute")
    return os.path.normcase(str(path.resolve()))


def scopes_collide(first: str, second: str) -> bool:
    a, b = Path(canonical_scope(first)), Path(canonical_scope(second))
    return a == b or a.is_relative_to(b) or b.is_relative_to(a)


def now_checked(clock: Callable[[], float]) -> float:
    now = clock()
    if not math.isfinite(now) or now < 0:
        raise ValueError("invalid clock")
    return now


@contextmanager
def connection(path: Path, *, write: bool = False, timeout: float = 10) -> Iterator[sqlite3.Connection]:
    db = sqlite3.connect(path, timeout=timeout, isolation_level=None)
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA synchronous=FULL")
        db.execute("BEGIN IMMEDIATE" if write else "BEGIN")
        yield db
        if write:
            db.commit()
    except BaseException:
        if write:
            db.rollback()
        raise
    finally:
        db.close()


def enable_wal(path: Path, timeout: float = 10) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=timeout, isolation_level=None)
    try:
        if str(db.execute("PRAGMA journal_mode=WAL").fetchone()[0]).lower() != "wal":
            raise RuntimeError("SQLite WAL required")
    finally:
        db.close()


class LeaseLost(RuntimeError):
    pass


class TaskConflict(RuntimeError):
    pass


class RunLimitReached(RuntimeError):
    pass


class TaskLedger:
    def __init__(self, path: str | Path, swarm_id: str, *, limits: RunLimits | None = None,
                 clock: Callable[[], float] = time.time, timeout_seconds: float = 10) -> None:
        if not swarm_id.strip():
            raise ValueError("swarm_id required")
        if not math.isfinite(timeout_seconds) or not 0 <= timeout_seconds <= 60:
            raise ValueError("timeout_seconds must be in [0,60]")
        self.path, self.swarm_id = Path(path).resolve(), swarm_id
        self.clock, self.timeout_seconds = clock, timeout_seconds
        self.limits = RunLimits.model_validate((limits or RunLimits()).model_dump())
        enable_wal(self.path, timeout_seconds)
        with self.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS swarm_runs (swarm_id TEXT PRIMARY KEY, limits TEXT NOT NULL, started_at REAL NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS tasks (swarm_id TEXT NOT NULL, task_id TEXT NOT NULL, "
                       "workspace TEXT NOT NULL, scope TEXT NOT NULL, module TEXT NOT NULL, capability TEXT NOT NULL, "
                       "signal TEXT NOT NULL, status TEXT NOT NULL, acceptance TEXT NOT NULL, attempts INTEGER NOT NULL, "
                       "token INTEGER NOT NULL, owner TEXT, expiry REAL, created_at REAL NOT NULL, updated_at REAL NOT NULL, "
                       "derived_from TEXT, result_id TEXT, result TEXT, effect_applied INTEGER NOT NULL DEFAULT 0, "
                       "condition_fail_count INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(swarm_id,task_id))")
            if "effect_applied" not in {r[1] for r in db.execute("PRAGMA table_info(tasks)")}:
                db.execute("ALTER TABLE tasks ADD COLUMN effect_applied INTEGER NOT NULL DEFAULT 0")
            if "condition_fail_count" not in {r[1] for r in db.execute("PRAGMA table_info(tasks)")}:
                db.execute("ALTER TABLE tasks ADD COLUMN condition_fail_count INTEGER NOT NULL DEFAULT 0")
            db.execute("CREATE INDEX IF NOT EXISTS tasks_locality ON tasks(swarm_id,workspace,scope,status,created_at)")
            db.execute("CREATE INDEX IF NOT EXISTS tasks_claims ON tasks(swarm_id,status,expiry,scope)")
            db.execute("CREATE TABLE IF NOT EXISTS dependencies (swarm_id TEXT NOT NULL, task_id TEXT NOT NULL, "
                       "dependency_id TEXT NOT NULL, PRIMARY KEY(swarm_id,task_id,dependency_id))")
            db.execute("CREATE INDEX IF NOT EXISTS dependencies_reverse ON dependencies(swarm_id,dependency_id,task_id)")
            db.execute("CREATE TABLE IF NOT EXISTS task_evidence (swarm_id TEXT NOT NULL, evidence_key TEXT NOT NULL, "
                       "task_id TEXT NOT NULL, body TEXT NOT NULL, occurrences INTEGER NOT NULL, PRIMARY KEY(swarm_id,evidence_key))")
            db.execute("CREATE TABLE IF NOT EXISTS task_attempts (swarm_id TEXT NOT NULL, task_id TEXT NOT NULL, "
                       "token INTEGER NOT NULL, worker_id TEXT NOT NULL, started_at REAL NOT NULL, finished_at REAL, "
                       "outcome TEXT, evidence TEXT, PRIMARY KEY(swarm_id,task_id,token))")
            db.execute("CREATE TABLE IF NOT EXISTS task_audit (sequence INTEGER PRIMARY KEY AUTOINCREMENT, "
                       "swarm_id TEXT NOT NULL, task_id TEXT, event TEXT NOT NULL, at REAL NOT NULL, body TEXT NOT NULL)")
            row = db.execute("SELECT limits FROM swarm_runs WHERE swarm_id=?", (swarm_id,)).fetchone()
            if row is None:
                db.execute("INSERT INTO swarm_runs VALUES (?,?,?)", (swarm_id, self.limits.model_dump_json(), self.now()))
            elif RunLimits.model_validate_json(row[0]) != self.limits:
                raise ValueError("persisted run limits cannot change")

    def now(self) -> float:
        return now_checked(self.clock)

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with connection(self.path, write=True, timeout=self.timeout_seconds) as db:
            yield db

    def _event(self, db: sqlite3.Connection, task_id: str | None, event: str, body: dict[str, JsonValue]) -> None:
        db.execute("INSERT INTO task_audit(swarm_id,task_id,event,at,body) VALUES (?,?,?,?,?)",
                   (self.swarm_id, task_id, event, self.now(), _OBJECT.dump_json(body).decode()))

    def record_event(self, event: str, body: dict[str, JsonValue], *, task_id: str | None = None) -> None:
        body = _OBJECT.validate_python(body)
        with self.transaction() as db:
            self._event(db, task_id, event, body)

    def _check_runtime(self, db: sqlite3.Connection) -> None:
        started = float(db.execute("SELECT started_at FROM swarm_runs WHERE swarm_id=?", (self.swarm_id,)).fetchone()[0])
        elapsed = self.now() - started
        if elapsed < 0 or elapsed >= self.limits.max_runtime_seconds:
            raise RunLimitReached("run_runtime_limit")

    def _row(self, db: sqlite3.Connection, task_id: str) -> sqlite3.Row:
        row = db.execute("SELECT * FROM tasks WHERE swarm_id=? AND task_id=?", (self.swarm_id, task_id)).fetchone()
        if not isinstance(row, sqlite3.Row):
            raise KeyError(task_id)
        return row

    def _record(self, db: sqlite3.Connection, row: sqlite3.Row) -> TaskRecord:
        deps = tuple(str(r[0]) for r in db.execute("SELECT dependency_id FROM dependencies WHERE swarm_id=? "
                                                "AND task_id=? ORDER BY dependency_id", (self.swarm_id, row["task_id"])))
        return TaskRecord(swarm_id=self.swarm_id, signal=Signal.model_validate_json(row["signal"]),
                          status=row["status"], dependencies=deps, acceptance=_OBJECT.validate_json(row["acceptance"]),
                          attempts=row["attempts"], condition_fail_count=int(row["condition_fail_count"]),
                          token=row["token"], owner=row["owner"], expires_at=row["expiry"],
                          created_at=row["created_at"], updated_at=row["updated_at"], derived_from=row["derived_from"],
                          result_id=row["result_id"], result=_OBJECT.validate_json(row["result"]) if row["result"] else None,
                          effect_applied=bool(row["effect_applied"]))

    def get(self, task_id: str) -> TaskRecord:
        with connection(self.path) as db:
            return self._record(db, self._row(db, task_id))

    @staticmethod
    def normalize(signal: Signal) -> Signal:
        signal = Signal.model_validate(signal.model_dump())
        root = Path(canonical_scope(Path(signal.workspace).resolve()))
        target = Path(canonical_scope(root / signal.scope))
        if not target.is_relative_to(root):
            raise ValueError("task scope escapes workspace")
        return signal.model_copy(update={"workspace": str(root), "scope": target.relative_to(root).as_posix()})

    def enqueue(self, signal: Signal, *, dependencies: tuple[str, ...] = (),
                acceptance: dict[str, JsonValue] | None = None, evidence_key: str | None = None,
                derived_from: str | None = None) -> TaskRecord:
        signal = self.normalize(signal)
        acceptance = _OBJECT.validate_python(acceptance or {})
        if len(dependencies) > 64 or signal.task_id in dependencies:
            raise ValueError("invalid or excessive dependencies")
        deps = tuple(sorted(set(dependencies)))
        scope = canonical_scope(Path(signal.workspace) / signal.scope)
        # Literal evidence identity; no custom hash or completion-proof convention.
        if evidence_key is None and signal.kind != "opportunity":
            evidence_key = json.dumps([signal.workspace, scope, signal.kind, signal.payload], sort_keys=True)
        now = self.now()
        with self.transaction() as db:
            existing = db.execute("SELECT * FROM tasks WHERE swarm_id=? AND task_id=?", (self.swarm_id, signal.task_id)).fetchone()
            if existing:
                record = self._record(db, existing)
                stable = ("task_id", "workspace", "scope", "kind", "payload", "module", "required_capability")
                if any(getattr(record.signal, key) != getattr(signal, key) for key in stable):
                    raise TaskConflict("task identity/content cannot change")
                if (deps and record.dependencies != deps) or (acceptance and record.acceptance != acceptance):
                    raise TaskConflict("task dependencies/acceptance cannot change")
                return record
            if evidence_key is not None:
                evidence = db.execute("SELECT task_id FROM task_evidence WHERE swarm_id=? AND evidence_key=?",
                                      (self.swarm_id, evidence_key)).fetchone()
                if evidence:
                    old = self._row(db, evidence[0])
                    if old["scope"] != scope:
                        raise TaskConflict("evidence key refers to different scope")
                    db.execute("UPDATE task_evidence SET occurrences=occurrences+1 WHERE swarm_id=? AND evidence_key=?",
                               (self.swarm_id, evidence_key))
                    self._event(db, old["task_id"], "evidence_duplicate", {"evidence_key": evidence_key})
                    return self._record(db, old)
            self._check_runtime(db)
            if db.execute("SELECT COUNT(*) FROM tasks WHERE swarm_id=?", (self.swarm_id,)).fetchone()[0] >= self.limits.max_tasks:
                raise RunLimitReached("max_tasks")
            if derived_from is not None:
                self._row(db, derived_from)
                derived = db.execute("SELECT COUNT(*) FROM tasks WHERE swarm_id=? AND derived_from IS NOT NULL", (self.swarm_id,)).fetchone()[0]
                if derived >= self.limits.max_derived_tasks:
                    raise RunLimitReached("max_derived_tasks")
            for dependency in deps:
                self._row(db, dependency)
            db.execute("INSERT INTO tasks VALUES (?,?,?,?,?,?,?,'available',?,0,0,NULL,NULL,?,?,?,NULL,NULL,0,0)",
                       (self.swarm_id, signal.task_id, signal.workspace, scope, signal.module,
                        signal.required_capability or signal.task_kind, signal.model_dump_json(),
                        _OBJECT.dump_json(acceptance).decode(), now, now, derived_from))
            db.executemany("INSERT INTO dependencies VALUES (?,?,?)", [(self.swarm_id, signal.task_id, d) for d in deps])
            if evidence_key is not None:
                db.execute("INSERT INTO task_evidence VALUES (?,?,?,?,1)",
                           (self.swarm_id, evidence_key, signal.task_id, json.dumps(signal.payload, sort_keys=True)))
            self._event(db, signal.task_id, "created", {"derived_from": derived_from})
            return self._record(db, self._row(db, signal.task_id))

    def _local_filter(self, locality: Locality) -> tuple[str, list[str]]:
        locality = Locality.model_validate(locality.model_dump())
        root = Path(canonical_scope(Path(locality.workspace).resolve()))
        args = [self.swarm_id, str(root)]
        scopes: list[str] = []
        for authorized in locality.authorized_scopes:
            path = Path(canonical_scope(root / authorized))
            if not path.is_relative_to(root):
                raise ValueError("authorized scope escapes workspace")
            scopes.append("(t.scope=? OR substr(t.scope,1,length(?))=?)")
            prefix = str(path).rstrip(os.sep) + os.sep
            args.extend([str(path), prefix, prefix])
        query = "t.swarm_id=? AND t.workspace=? AND (" + (" OR ".join(scopes) or "0") + ")"
        if locality.modules:
            query += " AND t.module IN (" + ",".join("?" for _ in locality.modules) + ")"
            args.extend(locality.modules)
        if locality.dependency_of:
            marks = ",".join("?" for _ in locality.dependency_of)
            query += (f" AND (t.task_id IN ({marks}) OR EXISTS (SELECT 1 FROM dependencies d WHERE "
                      f"d.swarm_id=t.swarm_id AND ((d.task_id=t.task_id AND d.dependency_id IN ({marks})) "
                      f"OR (d.dependency_id=t.task_id AND d.task_id IN ({marks})))))")
            args.extend(locality.dependency_of * 3)
        return query, args

    @staticmethod
    def _eligible() -> str:
        return ("(t.status IN ('available','partial','handoff') OR (t.status='claimed' AND t.expiry<=?)) AND t.attempts<? "
                "AND NOT EXISTS (SELECT 1 FROM dependencies d LEFT JOIN tasks p ON p.swarm_id=d.swarm_id "
                "AND p.task_id=d.dependency_id WHERE d.swarm_id=t.swarm_id AND d.task_id=t.task_id "
                "AND (p.status IS NULL OR p.status!='completed')) "
                "AND NOT EXISTS (SELECT 1 FROM tasks c WHERE c.swarm_id=t.swarm_id AND c.task_id!=t.task_id "
                "AND (c.status='submitting' OR (c.status='claimed' AND c.expiry>?)) AND "
                "(c.scope=t.scope OR substr(c.scope,1,length(t.scope)+1)=t.scope||? "
                "OR substr(t.scope,1,length(c.scope)+1)=c.scope||?))")

    def candidates(self, locality: Locality, *, limit: int = 100, include_blocked: bool = False,
                   capabilities: tuple[str, ...] | None = None) -> list[TaskRecord]:
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be in [1,1000]")
        query, args = self._local_filter(locality)
        parameters: list[str | float | int] = list(args)
        if not include_blocked:
            query += " AND " + self._eligible()
            parameters.extend([self.now(), self.limits.max_attempts_per_task, self.now(), os.sep, os.sep])
        if capabilities is not None:
            if len(capabilities) > 64:
                raise ValueError("too many capabilities")
            query += " AND t.capability IN (" + (",".join("?" for _ in capabilities) or "NULL") + ")"
            parameters.extend(capabilities)
        with connection(self.path) as db:
            rows = db.execute("SELECT t.* FROM tasks t WHERE " + query + " ORDER BY t.created_at,t.task_id LIMIT ?", [*parameters, limit]).fetchall()
            return [self._record(db, row) for row in rows]

    @staticmethod
    def _ttl(ttl: float) -> None:
        if not math.isfinite(ttl) or not 0 < ttl <= 86400:
            raise ValueError("TTL must be finite in (0,86400]")

    def claim(self, task_id: str, worker_id: str, *, ttl_seconds: float = 30, locality: Locality) -> Lease | None:
        self._ttl(ttl_seconds)
        if not worker_id.strip():
            raise ValueError("worker_id required")
        query, args = self._local_filter(locality)
        with self.transaction() as db:
            self._check_runtime(db)
            attempts = db.execute("SELECT COUNT(*) FROM task_attempts WHERE swarm_id=?", (self.swarm_id,)).fetchone()[0]
            if attempts >= self.limits.max_attempts:
                raise RunLimitReached("max_attempts")
            now = self.now()
            row = db.execute("SELECT t.* FROM tasks t WHERE " + query + " AND t.task_id=? AND " + self._eligible(),
                             [*args, task_id, now, self.limits.max_attempts_per_task, now, os.sep, os.sep]).fetchone()
            if row is None:
                return None
            if canonical_scope(row["scope"]) != row["scope"]:
                raise LeaseLost("canonical scope changed")
            if row["status"] == "claimed":
                db.execute("UPDATE task_attempts SET finished_at=?,outcome='expired' WHERE swarm_id=? AND task_id=? AND token=?",
                           (now, self.swarm_id, task_id, row["token"]))
            lease = Lease(task_id=task_id, swarm_id=self.swarm_id, scope=row["scope"], worker_id=worker_id,
                          token=row["token"] + 1, expires_at=now + ttl_seconds)
            db.execute("UPDATE tasks SET status='claimed',attempts=attempts+1,token=?,owner=?,expiry=?,updated_at=? "
                       "WHERE swarm_id=? AND task_id=?", (lease.token, worker_id, lease.expires_at, now, self.swarm_id, task_id))
            db.execute("INSERT INTO task_attempts VALUES (?,?,?,?,?,NULL,NULL,NULL)", (self.swarm_id, task_id, lease.token, worker_id, now))
            self._event(db, task_id, "claimed", {"worker_id": worker_id, "token": lease.token})
            return lease

    def _owned(self, db: sqlite3.Connection, lease: Lease, *, submitting: bool = False) -> sqlite3.Row:
        lease = Lease.model_validate(lease.model_dump())
        row = self._row(db, lease.task_id)
        statuses = ("claimed", "submitting") if submitting else ("claimed",)
        if (lease.swarm_id != self.swarm_id or row["owner"] != lease.worker_id or row["token"] != lease.token or
            row["scope"] != lease.scope or row["expiry"] != lease.expires_at or row["status"] not in statuses or
            lease.expires_at <= self.now() or canonical_scope(lease.scope) != lease.scope):
            raise LeaseLost("lease expired, changed or fenced by another owner")
        return row

    def renew(self, lease: Lease, *, ttl_seconds: float = 30) -> Lease | None:
        self._ttl(ttl_seconds)
        with self.transaction() as db:
            try:
                self._owned(db, lease)
            except (LeaseLost, KeyError):
                return None
            renewed = lease.model_copy(update={"expires_at": self.now() + ttl_seconds})
            db.execute("UPDATE tasks SET expiry=?,updated_at=? WHERE swarm_id=? AND task_id=?",
                       (renewed.expires_at, self.now(), self.swarm_id, lease.task_id))
            return renewed

    def is_valid(self, lease: Lease) -> bool:
        with connection(self.path) as db:
            try:
                self._owned(db, lease)
                return True
            except (LeaseLost, KeyError):
                return False

    def release(self, lease: Lease) -> bool:
        with self.transaction() as db:
            try:
                row = self._owned(db, lease)
            except (LeaseLost, KeyError):
                return False
            self._finish_attempt(db, lease, row, "released", {})
            return True

    def _finish_attempt(self, db: sqlite3.Connection, lease: Lease, row: sqlite3.Row,
                        outcome: str, evidence: dict[str, JsonValue]) -> None:
        status = "failed" if row["attempts"] >= self.limits.max_attempts_per_task else "available"
        db.execute("UPDATE tasks SET status=?,owner=NULL,expiry=NULL,updated_at=? WHERE swarm_id=? AND task_id=?",
                   (status, self.now(), self.swarm_id, lease.task_id))
        db.execute("UPDATE task_attempts SET finished_at=?,outcome=?,evidence=? WHERE swarm_id=? AND task_id=? AND token=?",
                   (self.now(), outcome, _OBJECT.dump_json(evidence).decode(), self.swarm_id, lease.task_id, lease.token))
        self._event(db, lease.task_id, outcome, {"token": lease.token, "evidence": evidence})

    def fail(self, lease: Lease, evidence: dict[str, JsonValue]) -> TaskRecord:
        evidence = _OBJECT.validate_python(evidence)
        with self.transaction() as db:
            row = self._owned(db, lease)
            self._finish_attempt(db, lease, row, "failed", evidence)
            return self._record(db, self._row(db, lease.task_id))

    def record_condition_failure(self, task_id: str) -> TaskRecord:
        """Count one unsatisfied precondition; block once it exhausts its budget.

        A task whose reuse dependency is never satisfied stays claimable, so the
        router would keep selecting it and burn polling. Each failed
        precondition check increments ``condition_fail_count``; at
        ``max_attempts_per_task`` the task is blocked and leaves the candidate set.
        """

        with self.transaction() as db:
            row = self._row(db, task_id)
            if row["status"] in ("completed", "failed", "blocked"):
                return self._record(db, row)
            count = int(row["condition_fail_count"]) + 1
            status = "blocked" if count >= self.limits.max_attempts_per_task else row["status"]
            db.execute("UPDATE tasks SET condition_fail_count=?,status=?,updated_at=? WHERE swarm_id=? AND task_id=?",
                       (count, status, self.now(), self.swarm_id, task_id))
            self._event(db, task_id, "blocked" if status == "blocked" else "condition_failed",
                        {"condition_fail_count": count})
            return self._record(db, self._row(db, task_id))

    def handoff(self, lease: Lease, next_worker_id: str, *, partial: dict[str, JsonValue] | None = None) -> TaskRecord:
        """Voluntarily yield a held task to another worker (the missing primitive).

        Only the current holder may hand off: ``_owned`` rejects any stale or
        fenced holder, so a resumed former holder can never extend, submit, or
        re-hand-off. The task becomes ``handoff`` (or ``partial`` when partial
        work is preserved in ``result``), its owner and expiry are cleared, and
        the next worker claims it through the normal candidate path.
        """

        if not next_worker_id.strip():
            raise ValueError("next_worker_id required")
        partial_body = _OBJECT.validate_python(partial) if partial is not None else None
        with self.transaction() as db:
            row = self._owned(db, lease)
            if row["owner"] == next_worker_id:
                raise TaskConflict("handoff target already owns the task")
            status = "partial" if partial_body is not None else "handoff"
            db.execute("UPDATE tasks SET status=?,owner=NULL,expiry=NULL,"
                       "result=COALESCE(?,result),updated_at=? WHERE swarm_id=? AND task_id=?",
                       (status, json.dumps(partial_body, sort_keys=True) if partial_body is not None else None,
                        self.now(), self.swarm_id, lease.task_id))
            db.execute("UPDATE task_attempts SET finished_at=?,outcome=? WHERE swarm_id=? AND task_id=? AND token=?",
                       (self.now(), status, self.swarm_id, lease.task_id, lease.token))
            self._event(db, lease.task_id, status,
                        {"from": lease.worker_id, "to": next_worker_id, "token": lease.token})
            return self._record(db, self._row(db, lease.task_id))

    def submit(self, lease: Lease, result_id: str, result: dict[str, JsonValue], *, apply: Apply | None = None) -> TaskRecord:
        lease = Lease.model_validate(lease.model_dump())
        if not result_id.strip():
            raise ValueError("result_id required")
        result = _OBJECT.validate_python(result)
        body = json.dumps(result, sort_keys=True, separators=(",", ":"))
        with self.transaction() as db:
            row = self._row(db, lease.task_id)
            same_owner = (lease.swarm_id == self.swarm_id and row["token"] == lease.token and
                          row["owner"] == lease.worker_id and row["scope"] == lease.scope and row["expiry"] == lease.expires_at)
            if row["status"] == "completed" and same_owner:
                if row["result_id"] == result_id and row["result"] == body:
                    return self._record(db, row)
                raise TaskConflict("conflicting result submission")
            self._owned(db, lease)
            if apply is None:
                return self._complete(db, lease, result_id, body)
            db.execute("UPDATE tasks SET status='submitting',result_id=?,result=?,updated_at=? WHERE swarm_id=? AND task_id=?",
                       (result_id, body, self.now(), self.swarm_id, lease.task_id))
            self._event(db, lease.task_id, "submitting", {"token": lease.token, "result_id": result_id})
        # Only prevalidated short publication. A crash leaves durable submitting.
        with self.transaction() as db:
            def assert_owned() -> None:
                self._owned(db, lease, submitting=True)
            assert_owned()
            apply(assert_owned)
            assert_owned()
            return self._complete(db, lease, result_id, body, effect_applied=True)

    def _complete(self, db: sqlite3.Connection, lease: Lease, result_id: str, body: str, *, effect_applied: bool = False) -> TaskRecord:
        db.execute("UPDATE tasks SET status='completed',result_id=?,result=?,updated_at=?,effect_applied=? WHERE swarm_id=? AND task_id=?",
                   (result_id, body, self.now(), int(effect_applied), self.swarm_id, lease.task_id))
        db.execute("UPDATE task_attempts SET finished_at=?,outcome='completed' WHERE swarm_id=? AND task_id=? AND token=?",
                   (self.now(), self.swarm_id, lease.task_id, lease.token))
        self._event(db, lease.task_id, "completed", {"token": lease.token, "result_id": result_id})
        return self._record(db, self._row(db, lease.task_id))

    def snapshot(self, *, limit: int = 100) -> list[TaskRecord]:
        if not 1 <= limit <= 10000:
            raise ValueError("invalid snapshot limit")
        with connection(self.path) as db:
            return [self._record(db, row) for row in db.execute(
                "SELECT * FROM tasks WHERE swarm_id=? ORDER BY created_at,task_id LIMIT ?", (self.swarm_id, limit))]

    def leases(self) -> list[Lease]:
        with connection(self.path) as db:
            return [Lease(task_id=r["task_id"], swarm_id=self.swarm_id, scope=r["scope"], worker_id=r["owner"],
                          token=r["token"], expires_at=r["expiry"]) for r in db.execute(
                              "SELECT * FROM tasks WHERE swarm_id=? AND status IN ('claimed','submitting') LIMIT 10000", (self.swarm_id,))]

    def audit(self, *, limit: int = 100) -> list[dict[str, JsonValue]]:
        if not 1 <= limit <= 10000:
            raise ValueError("invalid audit limit")
        with connection(self.path) as db:
            return [{"sequence": r["sequence"], "task_id": r["task_id"], "event": r["event"], "at": r["at"],
                     "body": _OBJECT.validate_json(r["body"])} for r in db.execute(
                         "SELECT * FROM task_audit WHERE swarm_id=? ORDER BY sequence DESC LIMIT ?", (self.swarm_id, limit))]

    def export_jsonl(self, path: str | Path) -> None:
        with connection(self.path) as db, Path(path).open("x", encoding="utf-8") as output:
            for row in db.execute("SELECT * FROM task_audit WHERE swarm_id=? ORDER BY sequence", (self.swarm_id,)):
                output.write(json.dumps(dict(row), ensure_ascii=False) + "\n")
