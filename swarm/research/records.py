"""Research-semantics domain objects (M1). Pydantic data identity only.

These contracts describe the *research plane*: sourced materials, notes,
hypotheses, branches, expert opinions, work proposals and research events.
They never describe execution state, cost settlement or fencing; those facts
remain authoritative in the existing TaskLedger / BudgetLedger / AssetStore.
Verified science lives only in the existing trusted observation chain; every
note submitted here starts in the exploration zone (``review_state`` unverified)
and an expert opinion can never be promoted to a verified fact by a member.
"""
from __future__ import annotations

from typing import Literal

from pydantic import Field, JsonValue, model_validator

from contracts.base import Contract
from contracts.identity import AgentId

SourceKind = Literal["markdown", "text", "pdf", "repository", "link", "notebook"]
RetrievalState = Literal["present", "abstract_only", "missing", "parse_failed", "formula_unreliable"]
NoteKind = Literal["observation", "hypothesis", "supporting_evidence", "opposing_evidence",
                   "dispute", "expert_opinion", "cross_domain_link"]
ReviewState = Literal["unverified", "verified", "disputed"]
BranchStatus = Literal["proposed", "exploring", "testing", "supported", "disputed",
                       "dormant", "refuted", "archived"]
HypothesisStatus = Literal["proposed", "supported", "disputed", "dormant", "refuted", "archived"]
ProposalKind = Literal["question", "subtask", "alternative_route", "counterexample_check",
                       "cross_domain_link", "experiment"]
ProposalStatus = Literal["proposed", "accepted", "rejected", "duplicate", "blocked"]


class SourceRef(Contract):
    """A precise, back-linkable location inside a material (FR-02)."""

    source_id: str = Field(min_length=1)
    kind: SourceKind
    identifier: str = Field(min_length=1)
    version: str | None = None
    license: str | None = None
    fetched_at: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    retrieval: RetrievalState = "present"
    location: str | None = None
    excerpt: str | None = None


class ResearchNote(Contract):
    """Sourced observation/opinion/dispute in the shared memory (FR-03/11).

    ``review_state`` separates the exploration zone from verified results.
    A member-written note is always ``unverified``; ``verified`` is reserved for
    the trusted evaluation chain. Expert opinions are never scientific facts.
    """

    note_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    branch_id: str | None = None
    hypothesis_id: str | None = None
    task_id: str | None = None
    kind: NoteKind
    actor: AgentId
    signer: str | None = None
    source_refs: tuple[SourceRef, ...] = ()
    text: str = Field(min_length=1)
    applicability: dict[str, str] = Field(default_factory=dict)
    review_state: ReviewState = "unverified"
    references: tuple[str, ...] = ()
    created_at: float = Field(ge=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def _evidence_and_opinion_bounds(self) -> "ResearchNote":
        if self.kind in {"observation", "supporting_evidence", "opposing_evidence"} and not self.source_refs:
            raise ValueError("evidence_note_requires_source_reference")
        if self.kind == "expert_opinion" and self.review_state != "unverified":
            raise ValueError("expert_opinion_is_never_verified_fact")
        if self.kind != "expert_opinion" and self.signer is not None:
            raise ValueError("signer_is_reserved_for_expert_opinion")
        return self


class Hypothesis(Contract):
    """A falsifiable claim with conditions and source back-links (FR-03/11)."""

    hypothesis_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    branch_id: str | None = None
    claim: str = Field(min_length=1)
    conditions: dict[str, str] = Field(default_factory=dict)
    status: HypothesisStatus = "proposed"
    supporting: tuple[str, ...] = ()
    opposing: tuple[str, ...] = ()
    source_refs: tuple[SourceRef, ...] = ()
    refuted_conditions: str | None = None
    created_at: float = Field(ge=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def _refutation_requires_conditions(self) -> "Hypothesis":
        if self.status == "refuted" and not self.refuted_conditions:
            raise ValueError("refuted_hypothesis_requires_conditions")
        return self


class ResearchBranch(Contract):
    """A non-pre-registered line of research; task state stays in TaskLedger."""

    branch_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    parent_branch_id: str | None = None
    title: str = Field(min_length=1)
    goal: str = Field(min_length=1)
    status: BranchStatus = "proposed"
    created_at: float = Field(ge=0, allow_inf_nan=False)


class ResearchProject(Contract):
    """Project-level goal and authorization references, persistent across branches/runs."""

    project_id: str = Field(min_length=1)
    goal: str = Field(min_length=1)
    allowed_domains: tuple[str, ...] = Field(default=(), max_length=64)
    data_bounds: dict[str, str] = Field(default_factory=dict)
    authorization_ref: str | None = None
    milestones: tuple[str, ...] = Field(default=(), max_length=64)
    created_at: float = Field(ge=0, allow_inf_nan=False)
    host_binding: dict[str, JsonValue] = Field(default_factory=dict)


class WorkProposal(Contract):
    """A member's proposed work; after host admission it becomes a ledger task (FR-06)."""

    proposal_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    branch_id: str | None = None
    kind: ProposalKind
    goal: str = Field(min_length=1)
    justification: str = Field(min_length=1)
    expected_contribution: str = Field(min_length=1)
    scope: str | None = None
    required_capability: str | None = None
    dependencies: tuple[str, ...] = Field(default=(), max_length=64)
    source_refs: tuple[SourceRef, ...] = ()
    actor: AgentId
    status: ProposalStatus = "proposed"
    task_id: str | None = None
    reason: str | None = None
    created_at: float = Field(ge=0, allow_inf_nan=False)


class ResearchEvent(Contract):
    """Minimal common research event field set (spec 9.3); correlation only."""

    event_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    branch_id: str | None = None
    task_id: str | None = None
    source_ref: str | None = None
    actor: AgentId
    at: float = Field(ge=0, allow_inf_nan=False)
    schema_version: str = Field(min_length=1)
    provenance: Literal["live", "mock", "contract_local"] = "live"
    event_kind: str = Field(min_length=1)
    payload: dict[str, JsonValue] = Field(default_factory=dict)
    correlation_ref: str | None = None
