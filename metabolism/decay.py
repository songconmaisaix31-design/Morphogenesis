"""Shared exponential time-constant decay; tau is not a half-life."""

import math


def exponential_decay(elapsed_seconds: float, tau_seconds: float) -> float:
    if not math.isfinite(elapsed_seconds) or elapsed_seconds < 0:
        raise ValueError("elapsed_seconds must be finite and nonnegative")
    if not math.isfinite(tau_seconds) or tau_seconds <= 0:
        raise ValueError("tau_seconds must be finite and positive")
    return math.exp(-elapsed_seconds / tau_seconds)
