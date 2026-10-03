"""Bounded, explainable research-route policy (research-v1); advisory only.

The three research axes — execution, hypothesis and contribution — are kept as
independent dimensions. A valid refutation earns a contribution while lowering
the future opportunity of the refuted branch under its declared conditions; a
crash, timeout, auth error or unknown effect earns no scientific reward.

This module is a pure advisory layer. Route opportunities are suggestions only:
a task is still claimed through the existing TaskLedger, which re-checks scope,
capabilities, dependencies, lease/fencing and budget. No scheduler, forced
central allocation or completion proof is introduced here.

``ResearchPolicy.accept`` is a pure computation used to *suggest* whether an
independently supplied result should be accepted. It is **not** a persistence
authorization: the durable acceptance entry in ``swarm.research.feedback``
re-derives every result from trusted persistent facts and never trusts a
caller-supplied ``ThreeAxisResult``.
"""
from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, JsonValue, TypeAdapter

from contracts.base import Contract
from orchestration.experiments.generated import (
    ContributionAxis,
    ExecutionAxis,
    HypothesisAxis,
)

_JSON: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)

# The three result axes are the single, shared three-axis result model (spec 5.2)
# owned by B's generated-experiment contracts; C reuses them verbatim so the
# policy projection never builds a parallel truth.
ExecutionState = ExecutionAxis
HypothesisState = HypothesisAxis
ContributionState = ContributionAxis
BranchStatus = Literal["proposed", "exploring", "testing", "supported", "disputed",
                       "dormant", "refuted", "archived"]
CorrectionKind = Literal["sleep", "downgrade", "reopen"]
Provenance = Literal["live", "replay", "mock", "contract_local"]


class ThreeAxisResult(Contract):
    result_id: str = Field(min_length=1)
    report_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    actor: str = Field(min_length=1)
    source_ref: str = Field(min_length=1)
    provenance: Provenance
    execution: ExecutionState
    hypothesis: HypothesisState
    contribution: ContributionState = "proposed"
    asset_id: str | None = None
    branch_id: str | None = None
    project_id: str | None = None
    experiment_schema: Literal["generated-experiment/v1"] | None = None
    run_id: str | None = None
    sandbox_id: str | None = None
    conditions: dict[str, str] = Field(default_factory=dict)
    purpose: Literal["original", "reproduction", "inheritance", "counterexample"] | None = None
    reviewer: str | None = None
    review_report_id: str | None = None
    at: float = Field(ge=0)
    reasons: tuple[str, ...] = ()


class Branch(Contract):
    branch_id: str = Field(min_length=1)
    status: BranchStatus
    conditions: dict[str, str] = Field(default_factory=dict)
    parent_id: str | None = None
    authorized: bool = True
    supported_by: tuple[str, ...] = ()
    refuted_by: tuple[str, ...] = ()
    # Bounded, explainable inputs (spec 7.2): applicability, goal relevance,
    # proven risk and estimated cost are explicit factors, never a hidden score.
    applicability: float = Field(default=1.0, ge=0, le=1)
    goal_relevance: float = Field(default=1.0, ge=0, le=1)
    risk: float = Field(default=0.0, ge=0, le=1)
    known_cost: float | None = Field(default=None, ge=0)


class RouteOpportunity(Contract):
    branch_id: str = Field(min_length=1)
    eligible: bool
    share: float = Field(ge=0, le=1)
    factors: dict[str, float] = Field(default_factory=dict)
    known_cost: float | None = Field(default=None, ge=0)
    # The accepted contribution result ids that actually drive this opportunity,
    # so a recommendation references real contributions rather than a bare score.
    supported_by: tuple[str, ...] = ()
    refuted_by: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()


class RouteOpportunityPlan(Contract):
    version: Literal["research-v1"] = "research-v1"
    exploration_fraction: float = Field(ge=0, le=1)
    total_share: float = 1.0
    opportunities: tuple[RouteOpportunity, ...]
    reasons: tuple[str, ...] = ()


class CorrectionEvent(Contract):
    event_id: str = Field(min_length=1)
    branch_id: str = Field(min_length=1)
    kind: CorrectionKind
    reason: str = Field(min_length=1)
    source_ref: str = Field(min_length=1)
    actor: str = Field(min_length=1)
    at: float = Field(ge=0)


class SupersessionEvent(Contract):
    event_id: str = Field(min_length=1)
    result_id: str = Field(min_length=1)
    superseded_by: str | None = None
    reason: str = Field(min_length=1)
    source_ref: str = Field(min_length=1)
    actor: str = Field(min_length=1)
    at: float = Field(ge=0)


class ContributionDecision(Contract):
    accepted: bool
    state: ContributionState
    reasons: tuple[str, ...] = ()


class ResearchPolicy:
    """research-v1 route policy: independent contribution acceptance and
    bounded, explainable branch opportunities."""

    version = "research-v1"

    _DOWNGRADE: dict[BranchStatus, BranchStatus] = {
        "supported": "disputed", "testing": "exploring", "exploring": "proposed",
        "disputed": "dormant", "proposed": "dormant",
    }

    def __init__(self, *, exploration_fraction: float = 0.20) -> None:
        if (isinstance(exploration_fraction, bool) or not math.isfinite(exploration_fraction)
                or not 0 <= exploration_fraction <= 1):
            raise ValueError("exploration_fraction must be finite and in [0,1]")
        self.exploration_fraction = exploration_fraction

    @staticmethod
    def dedup_keys(result: ThreeAxisResult) -> tuple[str, str]:
        """A contribution is identified by its completed result and its source.

        The same result and the same paper/origin copy are one contribution;
        agent brand is never part of the identity.
        """
        return ("result:" + result.result_id, "source:" + result.source_ref)

    def accept(self, result: ThreeAxisResult, *, reviewer: str,
               seen: set[str]) -> ContributionDecision:
        """Pure suggestion of whether a result may be accepted; no persistence."""
        if not reviewer.strip():
            raise ValueError("reviewer is required")
        if reviewer == result.actor:
            return ContributionDecision(accepted=False, state="rejected", reasons=("self_approval_rejected",))
        if result.execution != "succeeded":
            return ContributionDecision(accepted=False, state="rejected", reasons=("execution_not_succeeded",))
        if result.hypothesis not in ("supported", "refuted"):
            return ContributionDecision(accepted=False, state="rejected", reasons=("no_scientific_conclusion",))
        keys = self.dedup_keys(result)
        if any(key in seen for key in keys):
            return ContributionDecision(accepted=False, state="rejected", reasons=("duplicate_contribution",))
        seen.update(keys)
        return ContributionDecision(accepted=True, state="accepted", reasons=("independent_evidence_accepted",))

    @staticmethod
    def _evidence(branch: Branch) -> float:
        """research-v1 neutral prior: no evidence=.5, support raises the
        factor and refutation lowers it. These are bounded route preferences,
        not probabilities of scientific truth. The legacy v0/v0.1 is separate.
        """
        support = len(branch.supported_by)
        refute = len(branch.refuted_by)
        return (1.0 + support) / (2.0 + support + refute)

    @classmethod
    def _value(cls, branch: Branch) -> float:
        """Bounded, explainable composite: evidence * applicability *
        goal relevance * (1 - proven risk)."""
        return cls._evidence(branch) * branch.applicability * branch.goal_relevance * (1.0 - branch.risk)

    def opportunities(self, branches: list[Branch] | tuple[Branch, ...]) -> RouteOpportunityPlan:
        """Allocate a fixed opportunity pool across eligible branches.

        80% follows evidence (times applicability, goal relevance and inverse
        risk); the configurable exploration fraction is a floor shared by every
        legal branch so low-evidence branches are not starved. Dormant, refuted,
        archived, inapplicable and out-of-scope branches have no exploration quota and
        therefore no execution right from this suggestion. Unknown cost is never
        treated as zero; it is reported as an explicit ``unknown_cost`` reason.
        """
        if not branches:
            return RouteOpportunityPlan(exploration_fraction=self.exploration_fraction,
                                        opportunities=(), reasons=("no_branches",))
        opportunities: list[RouteOpportunity] = []
        eligible: list[Branch] = []
        reasons: list[str] = []
        for branch in branches:
            if not branch.authorized:
                opportunities.append(RouteOpportunity(
                    branch_id=branch.branch_id, eligible=False, share=0.0,
                    supported_by=branch.supported_by, refuted_by=branch.refuted_by,
                    reasons=("out_of_scope",)))
            elif branch.status == "refuted":
                opportunities.append(RouteOpportunity(
                    branch_id=branch.branch_id, eligible=False, share=0.0,
                    known_cost=branch.known_cost, supported_by=branch.supported_by,
                    refuted_by=branch.refuted_by, reasons=("refuted_under_conditions",)))
            elif branch.status == "archived":
                opportunities.append(RouteOpportunity(
                    branch_id=branch.branch_id, eligible=False, share=0.0,
                    known_cost=branch.known_cost, supported_by=branch.supported_by,
                    refuted_by=branch.refuted_by, reasons=("archived",)))
            elif branch.status == "dormant":
                opportunities.append(RouteOpportunity(
                    branch_id=branch.branch_id, eligible=False, share=0.0,
                    known_cost=branch.known_cost, supported_by=branch.supported_by,
                    refuted_by=branch.refuted_by, reasons=("dormant",)))
            elif branch.applicability == 0:
                opportunities.append(RouteOpportunity(
                    branch_id=branch.branch_id, eligible=False, share=0.0,
                    known_cost=branch.known_cost, supported_by=branch.supported_by,
                    refuted_by=branch.refuted_by, reasons=("inapplicable",)))
            else:
                eligible.append(branch)
        count = len(eligible)
        if count == 0:
            reasons.append("no_eligible_branch")
            return RouteOpportunityPlan(exploration_fraction=self.exploration_fraction,
                                        opportunities=tuple(opportunities),
                                        reasons=tuple(reasons))
        values = [self._value(branch) for branch in eligible]
        value_sum = sum(values)
        exploration_floor = 1.0 / count
        exploration = self.exploration_fraction
        eligible_index = 0
        for branch in branches:
            if (not branch.authorized or branch.status in ("refuted", "archived", "dormant")
                    or branch.applicability == 0):
                continue
            value = values[eligible_index]
            value_share = value / value_sum if value_sum > 0 else 0.0
            share = min(1.0, max(0.0, (1.0 - exploration) * value_share + exploration * exploration_floor))
            support = len(branch.supported_by)
            refute = len(branch.refuted_by)
            evidence = self._evidence(branch)
            branch_reasons = ["eligible"]
            if support == 0 and refute == 0:
                branch_reasons.append("insufficient_evidence")
            if branch.known_cost is None:
                branch_reasons.append("unknown_cost")
            opportunities.append(RouteOpportunity(
                branch_id=branch.branch_id, eligible=True, share=share,
                factors={"evidence": evidence, "insufficient_evidence": 1.0 - evidence,
                         "applicability": branch.applicability, "goal_relevance": branch.goal_relevance,
                         "risk": branch.risk, "support_count": float(support), "refute_count": float(refute),
                         "exploration_floor": exploration_floor},
                known_cost=branch.known_cost, supported_by=branch.supported_by,
                refuted_by=branch.refuted_by, reasons=tuple(branch_reasons)))
            eligible_index += 1
        by_id = {op.branch_id: op for op in opportunities}
        ordered = [by_id[branch.branch_id] for branch in branches]
        return RouteOpportunityPlan(exploration_fraction=self.exploration_fraction,
                                    opportunities=tuple(ordered), reasons=tuple(reasons))

    def apply_correction(self, branch: Branch, event: CorrectionEvent) -> Branch:
        """Sleep, downgrade or reopen a branch; history is preserved by callers."""
        if event.branch_id != branch.branch_id:
            raise ValueError("correction_branch_mismatch")
        if event.kind == "sleep":
            if branch.status in ("dormant", "refuted", "archived"):
                raise ValueError("branch_not_active")
            return branch.model_copy(update={"status": "dormant"})
        if event.kind == "downgrade":
            new_status = self._DOWNGRADE.get(branch.status)
            if new_status is None:
                raise ValueError("branch_not_downgradable")
            return branch.model_copy(update={"status": new_status})
        if event.kind == "reopen":
            if branch.status == "refuted":
                raise ValueError("refuted_requires_new_branch")
            if branch.status not in ("dormant", "archived"):
                raise ValueError("only_dormant_or_archived_reopen")
            return branch.model_copy(update={"status": "proposed"})
        raise ValueError("unknown_correction_kind")

    @staticmethod
    def new_condition_branch(branch: Branch, branch_id: str, conditions: dict[str, str]) -> Branch:
        """A refuted branch reopens as a new version under changed conditions."""
        return Branch(branch_id=branch_id, status="proposed", conditions=conditions,
                      parent_id=branch.branch_id, authorized=branch.authorized)

    def snapshot(self, results: list[ThreeAxisResult] | tuple[ThreeAxisResult, ...],
                 branches: list[Branch] | tuple[Branch, ...]) -> dict[str, JsonValue]:
        """Thin read interface for A/P: three-axis view, reasons and opportunities."""
        def axis_counts(axis: str) -> dict[str, int]:
            counts: dict[str, int] = {}
            for result in results:
                value = getattr(result, axis)
                counts[value] = counts.get(value, 0) + 1
            return counts

        plan = self.opportunities(branches)
        return {
            "policy_version": self.version,
            "advisory_only": True,
            "claim_requires_recheck": True,
            "exploration_fraction": self.exploration_fraction,
            "three_axis": {
                "execution": _JSON.validate_python(axis_counts("execution")),
                "hypothesis": _JSON.validate_python(axis_counts("hypothesis")),
                "contribution": _JSON.validate_python(axis_counts("contribution")),
            },
            "results": [_JSON.validate_python(result.model_dump(mode="json")) for result in results],
            "branches": [_JSON.validate_python(branch.model_dump(mode="json")) for branch in branches],
            "opportunities": _JSON.validate_python(plan.model_dump(mode="json")),
        }
