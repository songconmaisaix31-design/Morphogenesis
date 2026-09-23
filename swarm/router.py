"""Task-specified discrete heuristic, not a continuum Physarum flow solver."""

from __future__ import annotations

from collections.abc import Mapping
import math
import random

from swarm.models import Locality, PipeHistory, Signal
from swarm.pheromone import PheromoneField


class Router:
    def __init__(self, field: PheromoneField, *, beta: float = 1.0,
                 rng: random.Random | None = None) -> None:
        if not math.isfinite(beta) or not 0 <= beta <= 1e6:
            raise ValueError("beta must be finite and between zero and 1e6")
        self.field, self.beta = field, beta
        self.rng = rng or random.Random()

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
        for signal in self.field.sense(locality):
            key = self.pipe_key(signal)
            match = capabilities.get(key, 0.0)
            if match <= 0 or signal.concentration <= 0 or signal.completed:
                continue
            if key not in own_history:
                own_history[key] = self.field.pipe_history(worker_id, key).weight
            # History modulates effective capability but never invents a capability.
            effective_match = match * (0.5 + 0.5 * own_history[key])
            scores.append(self.beta * signal.concentration * effective_match * signal.urgency)
            choices.append(signal)
        if not choices:
            return None
        maximum = max(scores)
        weights = [math.exp(score - maximum) for score in scores]
        # Standard-library weighted sampling, not a maximum-score decision.
        return self.rng.choices(choices, weights=weights, k=1)[0]

    def reinforce(self, worker_id: str, signal: Signal, *, success: bool,
                  speedup: float = 0.0, token_saving: float = 0.0) -> PipeHistory:
        if any(not math.isfinite(value) or not 0 <= value <= 1 for value in (speedup, token_saving)):
            raise ValueError("speedup and token_saving must be normalized fractions in [0,1]")
        reward = (0.5 + 0.25 * speedup + 0.25 * token_saving) if success else 0.0
        return self.field.reinforce(worker_id, self.pipe_key(signal), reward)
