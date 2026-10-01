"""Task-specified discrete heuristic, not a continuum Physarum flow solver."""

from __future__ import annotations

from collections.abc import Mapping
import math
import random
from typing import Literal

from pydantic import JsonValue, TypeAdapter

from swarm.models import Locality, PipeHistory, Signal
from swarm.pheromone import PheromoneField

StrategyVersion = Literal["v0", "v0.1"]
_DECISION = TypeAdapter(dict[str, JsonValue])


class Router:
    def __init__(self, field: PheromoneField, *, beta: float = 1.0,
                 rng: random.Random | None = None, exploration: float = 0.05,
                 aging_seconds: float = 86400,
                 strategy_version: StrategyVersion = "v0") -> None:
        if not math.isfinite(beta) or not 0 <= beta <= 1e6:
            raise ValueError("beta must be finite and between zero and 1e6")
        self.field, self.beta = field, beta
        self.rng = rng or random.Random()
        if not math.isfinite(exploration) or not 0 <= exploration <= 1:
            raise ValueError("exploration must be in [0,1]")
        if not math.isfinite(aging_seconds) or aging_seconds <= 0:
            raise ValueError("aging_seconds must be finite and positive")
        if strategy_version not in ("v0", "v0.1"):
            raise ValueError("strategy_version must be v0 or v0.1")
        self.exploration, self.aging_seconds = exploration, aging_seconds
        self.strategy_version = strategy_version

    @staticmethod
    def pipe_key(signal: Signal) -> str:
        return signal.required_capability or signal.task_kind

    def _record_decision(self, audit: dict[str, JsonValue], *, record_audit: bool) -> dict[str, JsonValue]:
        audit = _DECISION.validate_python(audit)
        if not record_audit:
            return {**audit, "routing_sequence": None, "audited": False}
        # Reuse the authoritative audit row as the recommendation reference.
        # The same short transaction/connection prevents a concurrent writer's
        # row from being mistaken for this decision. No lease is acquired here.
        with self.field.ledger.transaction() as db:
            self.field.ledger._event(db, None, "routing", audit)
            sequence = int(db.execute("SELECT last_insert_rowid()").fetchone()[0])
        return {**audit, "routing_sequence": sequence, "audited": True}

    def choose(self, worker_id: str, locality: Locality,
               capabilities: Mapping[str, float]) -> Signal | None:
        """Compatibility sampler: a preference, never a lease or execution."""
        selected, _ = self._recommend(worker_id, locality, capabilities, limit=100, record_audit=True)
        return selected

    def recommend(self, worker_id: str, locality: Locality,
                  capabilities: Mapping[str, float], *, limit: int = 100,
                  record_audit: bool = True) -> dict[str, JsonValue]:
        """JSON decision shared by native discovery and choose, audited once.

        The caller records actual choice/override using its existing ledger audit.
        This snapshot does not authorize a later claim or reserve a candidate.
        record_audit=False is an operator-only read-only diagnostic, not a
        native tool parameter. Formal discovery always uses the default True.
        """
        _, decision = self._recommend(worker_id, locality, capabilities, limit=limit, record_audit=record_audit)
        return decision

    def _recommend(self, worker_id: str, locality: Locality,
                   capabilities: Mapping[str, float], *, limit: int,
                   record_audit: bool) -> tuple[Signal | None, dict[str, JsonValue]]:
        if not worker_id.strip():
            raise ValueError("worker_id is required")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("recommendation limit must be in [1,100]")
        if not isinstance(record_audit, bool):
            raise ValueError("record_audit must be a bool")
        if any(isinstance(value, bool) or not math.isfinite(value) or not 0 <= value <= 1
               for value in capabilities.values()):
            raise ValueError("capability match must be finite and between zero and one")
        choices: list[Signal] = []
        scores: list[float] = []
        own_history: dict[str, float] = {}
        ledger = self.field.ledger
        records = ledger.candidates(locality, limit=limit,
                                    capabilities=tuple(key for key, value in capabilities.items() if value > 0))
        inspected = ledger.candidates(locality, limit=limit, include_blocked=True)
        eligible_ids = {r.signal.task_id for r in records}
        filtered: list[JsonValue] = [{"task_id": r.signal.task_id, "status": r.status,
                                    "dependencies": list(r.dependencies), "attempts": r.attempts,
                                    "owner": r.owner, "expires_at": r.expires_at,
                                    "reason": "capability" if capabilities.get(self.pipe_key(r.signal), 0) <= 0
                                    else "status_dependency_scope_or_query_limit"}
                                   for r in inspected if r.signal.task_id not in eligible_ids]
        signals: list[JsonValue] = []
        age_weights: list[float] = []
        for record, signal in zip(records, self.field.for_records(records), strict=True):
            key = self.pipe_key(signal)
            match = capabilities.get(key, 0.0)
            if key not in own_history:
                own_history[key] = self.field.pipe_history(worker_id, key).weight
            age = 1 + min(10.0, max(0.0, ledger.now() - record.created_at) / self.aging_seconds)
            urgency = signal.urgency * age
            if self.strategy_version == "v0.1":
                # Fixed unit scales: at c=u=1 the product still equals one.
                # Separate bounded factors retain history influence at large c/u.
                concentration_factor = 2 * signal.concentration / (1 + signal.concentration)
                urgency_factor = 2 * signal.urgency / (1 + signal.urgency)
                score = self.beta * own_history[key] * concentration_factor * match * urgency_factor * age
            else:
                concentration_factor, urgency_factor = signal.concentration, signal.urgency
                score = self.beta * own_history[key] * signal.concentration * match * urgency
            scores.append(score)
            age_weights.append(age)
            choices.append(signal)
            signals.append({"task_id": signal.task_id, "concentration": signal.concentration,
                            "capability_match": match, "w_history": own_history[key], "urgency": urgency,
                            "base_urgency": signal.urgency, "age_weight": age, "score": score,
                            "concentration_factor": concentration_factor, "urgency_factor": urgency_factor,
                            "scope": signal.scope, "module": signal.module, "required_capability": key,
                            "dependencies": list(record.dependencies), "status": record.status,
                            "created_at": record.created_at})
        audit: dict[str, JsonValue] = {"worker_id": worker_id, "authorized_scopes": list(locality.authorized_scopes),
                                      "modules": list(locality.modules), "dependency_of": list(locality.dependency_of),
                                      "filtered": filtered, "signals": signals, "query_limit": limit,
                                      "strategy_version": self.strategy_version,
                                      "policy_version": self.strategy_version,
                                      "window_order": ["created_at", "task_id"],
                                      "reason": "bounded_local_weighted_sample",
                                      "aging_seconds": self.aging_seconds,
                                      "tau_seconds": self.field.tau_seconds, "alpha": self.field.alpha,
                                      "concentration_scale": 1.0, "urgency_scale": 1.0,
                                      "beta": self.beta, "exploration": self.exploration,
                                      "constraints": ["authorized_scope", "module", "dependency_neighborhood",
                                                      "dependency_completed", "available_or_expired", "attempt_limit",
                                                      "no_overlapping_claim_or_uncertain_effect", "capability"]}
        if not choices:
            audit.update({"selected": None, "recommendation": None, "softmax": [], "probabilities": []})
            return None, self._record_decision(audit, record_audit=record_audit)
        maximum = max(scores)
        weights = [math.exp(score - maximum) for score in scores]
        weight_total = sum(weights)
        age_total = sum(age_weights)
        softmax = [w / weight_total for w in weights]
        probabilities = [(1-self.exploration)*p + self.exploration*a/age_total
                         for p, a in zip(softmax, age_weights, strict=True)]
        # Standard-library weighted sampling, not a maximum-score decision.
        selected = self.rng.choices(choices, weights=probabilities, k=1)[0]
        audit.update({"selected": selected.task_id, "softmax": list(softmax), "probabilities": list(probabilities),
                      "recommendation": {"task_id": selected.task_id, "scope": selected.scope,
                                         "task_kind": selected.task_kind, "payload": selected.payload}})
        return selected, self._record_decision(audit, record_audit=record_audit)

    def reinforce(self, worker_id: str, signal: Signal, *, success: bool,
                  speedup: float = 0.0, token_saving: float = 0.0) -> PipeHistory:
        if any(not math.isfinite(value) or not 0 <= value <= 1 for value in (speedup, token_saving)):
            raise ValueError("speedup and token_saving must be normalized fractions in [0,1]")
        reward = (0.5 + 0.25 * speedup + 0.25 * token_saving) if success else 0.0
        return self.field.reinforce(worker_id, self.pipe_key(signal), reward)
