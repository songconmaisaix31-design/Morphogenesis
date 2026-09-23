"""Task-specified discrete heuristic, not a continuum Physarum flow solver."""

from __future__ import annotations

from collections.abc import Mapping
import math
import random

from pydantic import JsonValue

from swarm.models import Locality, PipeHistory, Signal
from swarm.pheromone import PheromoneField


class Router:
    def __init__(self, field: PheromoneField, *, beta: float = 1.0,
                 rng: random.Random | None = None, exploration: float = 0.05,
                 aging_seconds: float = 86400) -> None:
        if not math.isfinite(beta) or not 0 <= beta <= 1e6:
            raise ValueError("beta must be finite and between zero and 1e6")
        self.field, self.beta = field, beta
        self.rng = rng or random.Random()
        if not math.isfinite(exploration) or not 0 <= exploration <= 1:
            raise ValueError("exploration must be in [0,1]")
        if not math.isfinite(aging_seconds) or aging_seconds <= 0:
            raise ValueError("aging_seconds must be finite and positive")
        self.exploration, self.aging_seconds = exploration, aging_seconds

    @staticmethod
    def pipe_key(signal: Signal) -> str:
        return signal.required_capability or signal.task_kind

    def choose(self, worker_id: str, locality: Locality,
               capabilities: Mapping[str, float]) -> Signal | None:
        if not worker_id.strip():
            raise ValueError("worker_id is required")
        if any(isinstance(value, bool) or not math.isfinite(value) or not 0 <= value <= 1
               for value in capabilities.values()):
            raise ValueError("capability match must be finite and between zero and one")
        choices: list[Signal] = []
        scores: list[float] = []
        own_history: dict[str, float] = {}
        ledger = self.field.ledger
        records = ledger.candidates(locality, capabilities=tuple(key for key, value in capabilities.items() if value > 0))
        inspected = ledger.candidates(locality, include_blocked=True)
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
            score = self.beta * own_history[key] * signal.concentration * match * urgency
            scores.append(score)
            age_weights.append(age)
            choices.append(signal)
            signals.append({"task_id": signal.task_id, "concentration": signal.concentration,
                            "capability_match": match, "w_history": own_history[key], "urgency": urgency,
                            "base_urgency": signal.urgency, "age_weight": age, "score": score})
        audit: dict[str, JsonValue] = {"worker_id": worker_id, "authorized_scopes": list(locality.authorized_scopes),
                                      "modules": list(locality.modules), "dependency_of": list(locality.dependency_of),
                                      "filtered": filtered, "signals": signals, "query_limit": 100,
                                      "beta": self.beta, "exploration": self.exploration,
                                      "constraints": ["authorized_scope", "module", "dependency_neighborhood",
                                                      "dependency_completed", "available_or_expired", "attempt_limit",
                                                      "no_overlapping_claim_or_uncertain_effect", "capability"]}
        if not choices:
            audit.update({"selected": None, "probabilities": []})
            ledger.record_event("routing", audit)
            return None
        maximum = max(scores)
        weights = [math.exp(score - maximum) for score in scores]
        softmax = [w / sum(weights) for w in weights]
        probabilities = [(1-self.exploration)*p + self.exploration*a/sum(age_weights)
                         for p, a in zip(softmax, age_weights, strict=True)]
        # Standard-library weighted sampling, not a maximum-score decision.
        selected = self.rng.choices(choices, weights=probabilities, k=1)[0]
        audit.update({"selected": selected.task_id, "softmax": list(softmax), "probabilities": list(probabilities)})
        ledger.record_event("routing", audit)
        return selected

    def reinforce(self, worker_id: str, signal: Signal, *, success: bool,
                  speedup: float = 0.0, token_saving: float = 0.0) -> PipeHistory:
        if any(not math.isfinite(value) or not 0 <= value <= 1 for value in (speedup, token_saving)):
            raise ValueError("speedup and token_saving must be normalized fractions in [0,1]")
        reward = (0.5 + 0.25 * speedup + 0.25 * token_saving) if success else 0.0
        return self.field.reinforce(worker_id, self.pipe_key(signal), reward)
