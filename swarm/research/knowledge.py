"""Research knowledge namespace: durable shared memory for the research plane.

Stored next to the existing ledger (same directory, own SQLite + WAL), mirroring
``PheromoneField``. This is a *science relationship* store, not a second task
ledger: it never records execution state, cost, fencing tokens or completion.

The store is **project-scoped, not run-scoped**: records are keyed by
``project_id`` and their own UUID identity, never by a ledger ``swarm_id``, so
project knowledge persists across bounded run fragments (FR-05). Every write is
idempotent: the same content returns the original record, while the same id
with different content is rejected rather than silently overwritten.
"""
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from collections.abc import Callable

from pydantic import JsonValue, TypeAdapter

from contracts.identity import AgentId
from swarm.research.records import (
    Hypothesis,
    ResearchBranch,
    ResearchEvent,
    ResearchNote,
    ResearchProject,
    SourceRef,
    WorkProposal,
)
from swarm.task_ledger import connection, enable_wal, now_checked

_OBJECT = TypeAdapter(dict[str, JsonValue])


def _dumps(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


class ResearchKnowledge:
    def __init__(self, path: str | Path, *, clock: Callable[[], float]) -> None:
        self.path = Path(path).resolve()
        self.clock = clock
        enable_wal(self.path)
        with connection(self.path, write=True) as db:
            db.execute("CREATE TABLE IF NOT EXISTS research_projects ("
                       "project_id TEXT PRIMARY KEY, goal TEXT NOT NULL, "
                       "allowed_domains TEXT NOT NULL, data_bounds TEXT NOT NULL, authorization_ref TEXT, "
                       "milestones TEXT NOT NULL, created_at REAL NOT NULL)")
            if "host_binding" not in {r[1] for r in db.execute("PRAGMA table_info(research_projects)")}:
                db.execute("ALTER TABLE research_projects ADD COLUMN host_binding TEXT NOT NULL DEFAULT '{}'")
            db.execute("CREATE TABLE IF NOT EXISTS research_branches ("
                       "branch_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, "
                       "parent_branch_id TEXT, title TEXT NOT NULL, goal TEXT NOT NULL, status TEXT NOT NULL, "
                       "created_at REAL NOT NULL)")
            db.execute("CREATE INDEX IF NOT EXISTS research_branches_project "
                       "ON research_branches(project_id)")
            db.execute("CREATE TABLE IF NOT EXISTS research_hypotheses ("
                       "hypothesis_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, "
                       "branch_id TEXT, claim TEXT NOT NULL, conditions TEXT NOT NULL, status TEXT NOT NULL, "
                       "supporting TEXT NOT NULL, opposing TEXT NOT NULL, source_refs TEXT NOT NULL, "
                       "refuted_conditions TEXT, created_at REAL NOT NULL)")
            db.execute("CREATE INDEX IF NOT EXISTS research_hypotheses_project "
                       "ON research_hypotheses(project_id)")
            db.execute("CREATE TABLE IF NOT EXISTS research_notes ("
                       "note_id TEXT PRIMARY KEY, dedup_key TEXT UNIQUE, project_id TEXT NOT NULL, "
                       "branch_id TEXT, hypothesis_id TEXT, task_id TEXT, kind TEXT NOT NULL, actor TEXT NOT NULL, "
                       "signer TEXT, source_refs TEXT NOT NULL, text TEXT NOT NULL, applicability TEXT NOT NULL, "
                       "review_state TEXT NOT NULL, refs TEXT NOT NULL, created_at REAL NOT NULL)")
            db.execute("CREATE INDEX IF NOT EXISTS research_notes_scope "
                       "ON research_notes(project_id, branch_id, hypothesis_id, task_id)")
            db.execute("CREATE TABLE IF NOT EXISTS research_proposals ("
                       "proposal_id TEXT PRIMARY KEY, dedup_key TEXT UNIQUE, project_id TEXT NOT NULL, "
                       "branch_id TEXT, kind TEXT NOT NULL, goal TEXT NOT NULL, justification TEXT NOT NULL, "
                       "expected_contribution TEXT NOT NULL, scope TEXT, required_capability TEXT, "
                       "dependencies TEXT NOT NULL, source_refs TEXT NOT NULL, actor TEXT NOT NULL, status TEXT NOT NULL, "
                       "task_id TEXT, reason TEXT, created_at REAL NOT NULL)")
            db.execute("CREATE INDEX IF NOT EXISTS research_proposals_project "
                       "ON research_proposals(project_id)")
            db.execute("CREATE TABLE IF NOT EXISTS research_events ("
                       "event_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, branch_id TEXT, "
                       "task_id TEXT, source_ref TEXT, actor TEXT NOT NULL, at REAL NOT NULL, schema_version TEXT NOT NULL, "
                       "provenance TEXT NOT NULL, event_kind TEXT NOT NULL, payload TEXT NOT NULL, correlation_ref TEXT)")
            db.execute("CREATE INDEX IF NOT EXISTS research_events_project "
                       "ON research_events(project_id, at)")

    def _now(self) -> float:
        return now_checked(self.clock)

    @staticmethod
    def _sources_dump(sources: tuple[SourceRef, ...]) -> str:
        return _dumps([s.model_dump(mode="json") for s in sources])

    # --- project -----------------------------------------------------------

    def put_project(self, project: ResearchProject) -> ResearchProject:
        with connection(self.path, write=True) as db:
            row = db.execute("SELECT * FROM research_projects WHERE project_id=?",
                             (project.project_id,)).fetchone()
            if row is not None:
                existing = self._project(row)
                if existing != project:
                    raise ValueError("project_identity_cannot_change")
                return existing
            db.execute("INSERT INTO research_projects VALUES (?,?,?,?,?,?,?,?)",
                       (project.project_id, project.goal, _dumps(list(project.allowed_domains)),
                        _dumps(project.data_bounds), project.authorization_ref,
                        _dumps(list(project.milestones)), project.created_at, _dumps(project.host_binding)))
            return project

    @staticmethod
    def _project(row: sqlite3.Row) -> ResearchProject:
        return ResearchProject.model_validate({
            "project_id": row["project_id"], "goal": row["goal"],
            "allowed_domains": json.loads(row["allowed_domains"]),
            "data_bounds": json.loads(row["data_bounds"]),
            "authorization_ref": row["authorization_ref"],
            "milestones": json.loads(row["milestones"]), "created_at": row["created_at"],
            "host_binding": json.loads(row["host_binding"])})

    def project(self, project_id: str) -> ResearchProject:
        with connection(self.path) as db:
            row = db.execute("SELECT * FROM research_projects WHERE project_id=?",
                             (project_id,)).fetchone()
            if row is None:
                raise KeyError(project_id)
            return self._project(row)

    # --- branch / hypothesis ----------------------------------------------

    def put_branch(self, branch: ResearchBranch) -> ResearchBranch:
        with connection(self.path, write=True) as db:
            row = db.execute("SELECT * FROM research_branches WHERE branch_id=?",
                             (branch.branch_id,)).fetchone()
            if row is not None:
                existing = self._branch(row)
                if existing != branch:
                    raise ValueError("branch_identity_cannot_change")
                return existing
            db.execute("INSERT INTO research_branches VALUES (?,?,?,?,?,?,?)",
                       (branch.branch_id, branch.project_id, branch.parent_branch_id,
                        branch.title, branch.goal, branch.status, branch.created_at))
            return branch

    @staticmethod
    def _branch(row: sqlite3.Row) -> ResearchBranch:
        return ResearchBranch.model_validate({
            "branch_id": row["branch_id"], "project_id": row["project_id"],
            "parent_branch_id": row["parent_branch_id"], "title": row["title"],
            "goal": row["goal"], "status": row["status"], "created_at": row["created_at"]})

    def branch(self, branch_id: str) -> ResearchBranch:
        with connection(self.path) as db:
            row = db.execute("SELECT * FROM research_branches WHERE branch_id=?",
                             (branch_id,)).fetchone()
            if row is None:
                raise KeyError(branch_id)
            return self._branch(row)

    def branches(self, project_id: str) -> list[ResearchBranch]:
        with connection(self.path) as db:
            return [self._branch(r) for r in db.execute(
                "SELECT * FROM research_branches WHERE project_id=? ORDER BY created_at, branch_id",
                (project_id,))]

    def put_hypothesis(self, hypothesis: Hypothesis) -> Hypothesis:
        with connection(self.path, write=True) as db:
            row = db.execute("SELECT * FROM research_hypotheses WHERE hypothesis_id=?",
                             (hypothesis.hypothesis_id,)).fetchone()
            if row is not None:
                existing = self._hypothesis(row)
                if existing != hypothesis:
                    raise ValueError("hypothesis_identity_cannot_change")
                return existing
            db.execute("INSERT INTO research_hypotheses VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                       (hypothesis.hypothesis_id, hypothesis.project_id, hypothesis.branch_id,
                        hypothesis.claim, _dumps(hypothesis.conditions), hypothesis.status,
                        _dumps(list(hypothesis.supporting)), _dumps(list(hypothesis.opposing)),
                        self._sources_dump(hypothesis.source_refs), hypothesis.refuted_conditions,
                        hypothesis.created_at))
            return hypothesis

    @staticmethod
    def _hypothesis(row: sqlite3.Row) -> Hypothesis:
        return Hypothesis.model_validate({
            "hypothesis_id": row["hypothesis_id"], "project_id": row["project_id"],
            "branch_id": row["branch_id"], "claim": row["claim"],
            "conditions": json.loads(row["conditions"]), "status": row["status"],
            "supporting": tuple(json.loads(row["supporting"])), "opposing": tuple(json.loads(row["opposing"])),
            "source_refs": [SourceRef.model_validate(s) for s in json.loads(row["source_refs"])],
            "refuted_conditions": row["refuted_conditions"], "created_at": row["created_at"]})

    def hypothesis(self, hypothesis_id: str) -> Hypothesis:
        with connection(self.path) as db:
            row = db.execute("SELECT * FROM research_hypotheses WHERE hypothesis_id=?",
                             (hypothesis_id,)).fetchone()
            if row is None:
                raise KeyError(hypothesis_id)
            return self._hypothesis(row)

    def hypotheses(self, project_id: str) -> list[Hypothesis]:
        with connection(self.path) as db:
            return [self._hypothesis(r) for r in db.execute(
                "SELECT * FROM research_hypotheses WHERE project_id=? ORDER BY created_at, hypothesis_id",
                (project_id,))]

    # --- notes -------------------------------------------------------------

    def note_dedup_key(self, project_id: str, kind: str, actor: AgentId, text: str,
                       source_refs: tuple[SourceRef, ...]) -> str:
        return _dumps([project_id, kind, actor.model_dump(mode="json"), text,
                       [s.model_dump(mode="json") for s in source_refs]])

    def put_note(self, note: ResearchNote) -> ResearchNote:
        dedup_key = self.note_dedup_key(note.project_id, note.kind, note.actor, note.text, note.source_refs)
        with connection(self.path, write=True) as db:
            row = db.execute("SELECT * FROM research_notes WHERE dedup_key=?", (dedup_key,)).fetchone()
            if row is not None:
                return self._note(row)
            db.execute("INSERT INTO research_notes VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                       (note.note_id, dedup_key, note.project_id, note.branch_id, note.hypothesis_id,
                        note.task_id, note.kind, note.actor.model_dump_json(), note.signer,
                        self._sources_dump(note.source_refs), note.text, _dumps(note.applicability),
                        note.review_state, _dumps(list(note.references)), note.created_at))
            return note

    @staticmethod
    def _note(row: sqlite3.Row) -> ResearchNote:
        return ResearchNote.model_validate({
            "note_id": row["note_id"], "project_id": row["project_id"], "branch_id": row["branch_id"],
            "hypothesis_id": row["hypothesis_id"], "task_id": row["task_id"], "kind": row["kind"],
            "actor": AgentId.model_validate_json(row["actor"]), "signer": row["signer"],
            "source_refs": [SourceRef.model_validate(s) for s in json.loads(row["source_refs"])],
            "text": row["text"], "applicability": json.loads(row["applicability"]),
            "review_state": row["review_state"], "references": tuple(json.loads(row["refs"])),
            "created_at": row["created_at"]})

    def note(self, note_id: str) -> ResearchNote:
        with connection(self.path) as db:
            row = db.execute("SELECT * FROM research_notes WHERE note_id=?", (note_id,)).fetchone()
            if row is None:
                raise KeyError(note_id)
            return self._note(row)

    def notes(self, project_id: str | None = None, branch_id: str | None = None,
              hypothesis_id: str | None = None, task_id: str | None = None,
              *, verified: bool | None = None) -> list[ResearchNote]:
        query = "SELECT * FROM research_notes WHERE 1=1"
        args: list[object] = []
        for column, value in (("project_id", project_id), ("branch_id", branch_id),
                              ("hypothesis_id", hypothesis_id), ("task_id", task_id)):
            if value is not None:
                query += f" AND {column}=?"
                args.append(value)
        if verified is True:
            query += " AND review_state='verified'"
        elif verified is False:
            query += " AND review_state!='verified'"
        with connection(self.path) as db:
            return [self._note(r) for r in db.execute(query + " ORDER BY created_at, note_id", args)]

    # --- proposals ---------------------------------------------------------

    def proposal_dedup_key(self, project_id: str, kind: str, goal: str, justification: str,
                           expected_contribution: str, scope: str | None,
                           required_capability: str | None, dependencies: tuple[str, ...],
                           source_refs: tuple[SourceRef, ...]) -> str:
        return _dumps([project_id, kind, goal, justification, expected_contribution, scope,
                       required_capability, list(dependencies),
                       [s.model_dump(mode="json") for s in source_refs]])

    def put_proposal(self, proposal: WorkProposal) -> WorkProposal:
        dedup_key = self.proposal_dedup_key(
            proposal.project_id, proposal.kind, proposal.goal, proposal.justification,
            proposal.expected_contribution, proposal.scope, proposal.required_capability,
            proposal.dependencies, proposal.source_refs)
        with connection(self.path, write=True) as db:
            row = db.execute("SELECT * FROM research_proposals WHERE dedup_key=?", (dedup_key,)).fetchone()
            if row is not None:
                return self._proposal(row)
            db.execute("INSERT INTO research_proposals VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                       (proposal.proposal_id, dedup_key, proposal.project_id, proposal.branch_id,
                        proposal.kind, proposal.goal, proposal.justification, proposal.expected_contribution,
                        proposal.scope, proposal.required_capability,
                        _dumps(list(proposal.dependencies)), self._sources_dump(proposal.source_refs),
                        proposal.actor.model_dump_json(), proposal.status, proposal.task_id,
                        proposal.reason, proposal.created_at))
            return proposal

    def bind_proposal(self, proposal_id: str, task_id: str, status: str, reason: str | None = None) -> WorkProposal:
        with connection(self.path, write=True) as db:
            row = db.execute("SELECT * FROM research_proposals WHERE proposal_id=?",
                             (proposal_id,)).fetchone()
            if row is None:
                raise KeyError(proposal_id)
            db.execute("UPDATE research_proposals SET status=?,task_id=?,reason=? WHERE proposal_id=?",
                       (status, task_id, reason, proposal_id))
            return self._proposal(db.execute(
                "SELECT * FROM research_proposals WHERE proposal_id=?", (proposal_id,)).fetchone())

    @staticmethod
    def _proposal(row: sqlite3.Row) -> WorkProposal:
        return WorkProposal.model_validate({
            "proposal_id": row["proposal_id"], "project_id": row["project_id"], "branch_id": row["branch_id"],
            "kind": row["kind"], "goal": row["goal"], "justification": row["justification"],
            "expected_contribution": row["expected_contribution"], "scope": row["scope"],
            "required_capability": row["required_capability"],
            "dependencies": tuple(json.loads(row["dependencies"])),
            "source_refs": [SourceRef.model_validate(s) for s in json.loads(row["source_refs"])],
            "actor": AgentId.model_validate_json(row["actor"]), "status": row["status"],
            "task_id": row["task_id"], "reason": row["reason"], "created_at": row["created_at"]})

    def proposal(self, proposal_id: str) -> WorkProposal:
        with connection(self.path) as db:
            row = db.execute("SELECT * FROM research_proposals WHERE proposal_id=?",
                             (proposal_id,)).fetchone()
            if row is None:
                raise KeyError(proposal_id)
            return self._proposal(row)

    def proposals(self, project_id: str | None = None, branch_id: str | None = None) -> list[WorkProposal]:
        query = "SELECT * FROM research_proposals WHERE 1=1"
        args: list[object] = []
        for column, value in (("project_id", project_id), ("branch_id", branch_id)):
            if value is not None:
                query += f" AND {column}=?"
                args.append(value)
        with connection(self.path) as db:
            return [self._proposal(r) for r in db.execute(query + " ORDER BY created_at, proposal_id", args)]

    # --- events ------------------------------------------------------------

    def record(self, event: ResearchEvent) -> ResearchEvent:
        with connection(self.path, write=True) as db:
            row = db.execute("SELECT * FROM research_events WHERE event_id=?",
                             (event.event_id,)).fetchone()
            if row is not None:
                existing = self._event(row)
                if existing != event:
                    raise ValueError("event_identity_cannot_change")
                return existing
            db.execute("INSERT INTO research_events VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                       (event.event_id, event.project_id, event.branch_id, event.task_id, event.source_ref,
                        event.actor.model_dump_json(), event.at, event.schema_version, event.provenance,
                        event.event_kind, _OBJECT.dump_json(event.payload).decode(), event.correlation_ref))
            return event

    @staticmethod
    def _event(row: sqlite3.Row) -> ResearchEvent:
        return ResearchEvent.model_validate({
            "event_id": row["event_id"], "project_id": row["project_id"], "branch_id": row["branch_id"],
            "task_id": row["task_id"], "source_ref": row["source_ref"],
            "actor": AgentId.model_validate_json(row["actor"]), "at": row["at"],
            "schema_version": row["schema_version"], "provenance": row["provenance"],
            "event_kind": row["event_kind"], "payload": _OBJECT.validate_json(row["payload"]),
            "correlation_ref": row["correlation_ref"]})

    def events(self, project_id: str, *, limit: int = 100,
               predicate: Callable[[ResearchEvent], bool] | None = None,
               include_overflow: bool = False) -> list[ResearchEvent]:
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be in [1,1000]")
        with connection(self.path) as db:
            rows = db.execute("SELECT * FROM research_events WHERE project_id=? "
                              "ORDER BY at DESC, event_id", (project_id,))
            result = []
            for row in rows:
                event = self._event(row)
                if predicate is None or predicate(event):
                    result.append(event)
                    if len(result) >= limit + int(include_overflow):
                        break
        return result
