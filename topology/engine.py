"""A deliberately small in-memory implementation of the topology contract.

The update ``D = (1 - lambda) * D + alpha * Q * s`` is a routing heuristic,
not a convergence or optimality claim.  In particular, it only updates an
existing connection; it never creates a connection from feedback.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from pydantic import Field, model_validator

from contracts.base import Contract
from contracts.identity import AgentId, AttemptId
from contracts.messages import Envelope
from contracts.protocols import PipeState


class TopologyPolicy(Contract):
    """Validated tuning parameters for one in-memory topology."""

    decay_lambda: float = Field(default=0.1, ge=0, lt=1)
    reinforcement: float = Field(default=1.0, gt=0)
    quality: float = Field(default=1.0, gt=0)
    prune_threshold: float = Field(default=0.05, ge=0)
    low_activity_window: int = Field(default=3, ge=1)
    min_active_outgoing: int = Field(default=1, ge=0)
    candidate_weight: float = Field(default=0.1, ge=0)


class Connection(Contract):
    """An explicit directed connection between two *instances*."""

    src: AgentId
    dst: AgentId
    weight: float = Field(default=1.0, ge=0)
    required: bool = False

    @model_validator(mode="after")
    def distinct_instances(self) -> Connection:
        if self.src == self.dst:
            raise ValueError("a topology connection must link distinct AgentId instances")
        return self


@dataclass
class _Edge:
    spec: Connection
    weight: float
    feedback_count: int = 0
    success_count: int = 0
    idle_windows: int = 0
    active: bool = True

    def state(self) -> PipeState:
        success_rate = self.success_count / self.feedback_count if self.feedback_count else 0.5
        return PipeState(
            src=self.spec.src,
            dst=self.spec.dst,
            weight=self.weight,
            flow=float(self.feedback_count),
            success_rate=success_rate,
            active=self.active,
        )


class TopologyEngine:
    """Select targets for one source instance and apply idempotent feedback.

    ``record`` keeps the T0 protocol surface.  T2 should instead call
    :meth:`record_feedback` with its result/review ``Envelope`` whenever it
    has one, because that additionally deduplicates the envelope ``msg_id``.
    The explicit ``route_source`` and ``route_target`` are deliberately not
    inferred from the feedback sender/receiver: a reviewer can report on a
    builder's attempt without becoming either endpoint of the routed edge.
    """

    def __init__(
        self,
        source: AgentId,
        connections: Iterable[Connection],
        policy: TopologyPolicy | None = None,
    ) -> None:
        self.source = source
        self.policy = policy or TopologyPolicy()
        self._edges: dict[AgentId, _Edge] = {}
        for connection in connections:
            if connection.src != source:
                raise ValueError("every connection must originate at the engine source")
            if connection.dst in self._edges:
                raise ValueError("duplicate directed connection")
            self._edges[connection.dst] = _Edge(connection, connection.weight)
        self._seen_attempts: set[AttemptId] = set()
        self._seen_msg_ids: set[str] = set()

    def select(self, targets: list[AgentId]) -> AgentId | None:
        """Return the highest-weight available, active connected instance.

        A target absent from the configured directed connections is unavailable.
        Equal weights keep the caller's target-list order for deterministic,
        caller-visible tie breaking.
        """

        best: AgentId | None = None
        best_weight = -1.0
        for target in targets:
            edge = self._edges.get(target)
            if edge is not None and edge.active and edge.weight > best_weight:
                best = target
                best_weight = edge.weight
        return best

    def record(self, attempt: AttemptId, success: bool) -> None:
        """Apply one protocol-compatible feedback event, deduped by attempt."""

        self._record(attempt=attempt, success=success, target=attempt.agent)

    def record_feedback(
        self,
        feedback: Envelope,
        success: bool,
        *,
        route_source: AgentId,
        route_target: AgentId,
    ) -> bool:
        """Apply feedback once, returning whether it changed topology state.

        ``feedback.sender`` is the feedback reporter and may be different from
        ``route_source`` and ``route_target``.  The route target must equal the
        concrete executing instance in ``feedback.attempt``; roles are never
        accepted as a substitute for an ``AgentId``.
        """

        if route_source != self.source:
            raise ValueError("feedback route_source must match the engine source")
        if route_target != feedback.attempt.agent:
            raise ValueError("feedback route_target must match feedback.attempt.agent")
        if feedback.msg_id in self._seen_msg_ids or feedback.attempt in self._seen_attempts:
            return False
        changed = self._record(attempt=feedback.attempt, success=success, target=route_target)
        if changed:
            self._seen_msg_ids.add(feedback.msg_id)
        return changed

    def advance_idle_window(self) -> None:
        """Advance the explicit low-activity window; this does not prune."""

        for edge in self._edges.values():
            if edge.active:
                edge.idle_windows += 1

    def prune(self) -> list[Connection]:
        """Deactivate eligible links while retaining required/minimum links.

        Finite feedback or idle windows do not themselves make a link zero.
        Pruning needs all three explicit conditions: weight below threshold,
        low activity for the configured window, and preservation of the
        configured minimum active outgoing connections.  Required links are
        never removed merely because their weight is low.
        """

        pruned: list[Connection] = []
        active_count = sum(edge.active for edge in self._edges.values())
        for edge in self._edges.values():
            if (
                edge.active
                and not edge.spec.required
                and edge.weight < self.policy.prune_threshold
                and edge.idle_windows >= self.policy.low_activity_window
                and active_count > self.policy.min_active_outgoing
            ):
                edge.active = False
                active_count -= 1
                pruned.append(edge.spec)
        return pruned

    def candidate_connections(self, targets: list[AgentId]) -> list[Connection]:
        """Return, but do not install, explicit candidate directed connections.

        A candidate is a distinct, currently unconnected target in caller order.
        Adding it requires an explicit :meth:`add_connection` call; feedback on
        an existing connection never creates candidate or live connections.
        """

        return [
            Connection(src=self.source, dst=target, weight=self.policy.candidate_weight)
            for target in targets
            if target != self.source and target not in self._edges
        ]

    def add_connection(self, connection: Connection) -> None:
        """Explicitly install a candidate after the caller's policy decision."""

        if connection.src != self.source:
            raise ValueError("connection source must match the engine source")
        if connection.dst in self._edges:
            raise ValueError("connection already exists")
        self._edges[connection.dst] = _Edge(connection, connection.weight)

    def snapshot(self) -> list[PipeState]:
        """Expose stable state in connection insertion order for diagnostics."""

        return [edge.state() for edge in self._edges.values()]

    def _record(self, attempt: AttemptId, success: bool, target: AgentId) -> bool:
        if attempt in self._seen_attempts:
            return False
        edge = self._edges.get(target)
        if edge is None:
            raise ValueError("feedback target has no configured connection")
        if not edge.active:
            raise ValueError("feedback target connection is inactive")
        signal = 1.0 if success else -1.0
        edge.weight = max(
            0.0,
            (1.0 - self.policy.decay_lambda) * edge.weight
            + self.policy.reinforcement * self.policy.quality * signal,
        )
        edge.feedback_count += 1
        edge.success_count += int(success)
        edge.idle_windows = 0
        self._seen_attempts.add(attempt)
        return True
