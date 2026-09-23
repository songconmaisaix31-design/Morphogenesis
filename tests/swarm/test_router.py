import math
from pathlib import Path
import random

import pytest

from swarm.models import Locality, Signal
from swarm.pheromone import PheromoneField
from swarm.router import Router


class CapturingRandom(random.Random):
    def choices(self, population, weights=None, *, cum_weights=None, k=1):
        self.weights = weights
        return super().choices(population, weights, cum_weights=cum_weights, k=k)


def setup(tmp_path: Path):
    field = PheromoneField(tmp_path / "field.db", clock=lambda: 100.0)
    first = field.deposit(Signal(task_id="a", workspace=str(tmp_path), scope="a",
                                 kind="error_pattern", concentration=1.0))
    second = field.deposit(Signal(task_id="b", workspace=str(tmp_path), scope="b",
                                  kind="opportunity", concentration=2.0))
    return field, first, second, Locality(workspace=str(tmp_path))


def test_stable_softmax_weighted_sampling_is_not_greedy(tmp_path: Path) -> None:
    field, first, second, locality = setup(tmp_path)
    rng = CapturingRandom(7)
    router = Router(field, rng=rng)
    counts = {first.task_id: 0, second.task_id: 0}
    for _ in range(500):
        chosen = router.choose("w", locality, {"repair": 1.0, "innovation": 1.0})
        counts[chosen.task_id] += 1
    assert 130 < counts["a"] < 215  # Expected 174; both candidates sampled.
    assert counts["b"] > counts["a"]
    assert sorted(rng.weights) == pytest.approx([math.exp(-.625), 1])


def test_capability_urgency_and_own_history_each_change_weights(tmp_path: Path) -> None:
    field, first, second, locality = setup(tmp_path)
    rng = CapturingRandom(1)
    router = Router(field, rng=rng)
    router.choose("w", locality, {"repair": 1.0, "innovation": .5})
    assert rng.weights == pytest.approx([1, 1])
    for _ in range(80):
        router.reinforce("w", first, success=False)
    router.choose("w", locality, {"repair": 1.0, "innovation": .5})
    assert sorted(rng.weights)[0] < .9
    router.choose("other", locality, {"repair": 1.0, "innovation": .5})
    assert rng.weights == pytest.approx([1, 1])  # Other workers' history never leaks.
    urgent = field.deposit(Signal(task_id="urgent", workspace=str(tmp_path), scope="c",
                                  kind="retry_flood", concentration=1.0, urgency=2.0))
    router.choose("other", locality, {"repair": 1.0, "optimize": 1.0})
    assert sorted(rng.weights) == pytest.approx([math.exp(-.625), 1])
    assert urgent.task_kind == "optimize"
    before = field.pipe_history("w", "repair").weight
    after = router.reinforce("w", first, success=True, speedup=.4, token_saving=.8)
    assert after.weight == pytest.approx(.95 * before + .05 * .8)


def test_overflow_empty_and_ineligible_capabilities(tmp_path: Path) -> None:
    field, first, second, locality = setup(tmp_path)
    router = Router(field, beta=1e6, rng=random.Random(4))
    assert router.choose("w", locality, {}) is None
    assert router.choose("w", locality, {"repair": 1.0}).task_id == first.task_id
    field.deposit(second, delta=1e12 - 2)
    assert router.choose("w", locality, {"repair": 1.0, "innovation": 1.0}).task_id == second.task_id
    assert router.choose("w", Locality(workspace=str(tmp_path / "remote")), {"repair": 1.0}) is None
    with pytest.raises(ValueError):
        router.choose("w", locality, {"repair": float("nan")})


def test_required_capability_and_success_components(tmp_path: Path) -> None:
    field = PheromoneField(tmp_path / "field.db")
    s = field.deposit(Signal(task_id="t", workspace=str(tmp_path), scope="a", kind="timeout_storm",
                            required_capability="python"))
    router = Router(field)
    assert router.choose("w", Locality(workspace=str(tmp_path)), {"optimize": 1.0}) is None
    assert router.choose("w", Locality(workspace=str(tmp_path)), {"python": .2}) is not None
    a = router.reinforce("a", s, success=True)
    b = router.reinforce("b", s, success=True, speedup=1, token_saving=1)
    c = router.reinforce("c", s, success=False, speedup=1, token_saving=1)
    assert c.weight < a.weight < b.weight


def test_first_success_strengthens_repeated_quality_history_and_failure_weakens(tmp_path: Path) -> None:
    field, first, _, _ = setup(tmp_path)
    router = Router(field)
    baseline = field.pipe_history("w", "repair").weight
    previous = baseline
    for _ in range(20):
        after = router.reinforce("w", first, success=True)
        assert previous < after.weight < .5
        previous = after.weight
    stronger = router.reinforce("w", first, success=True, speedup=1, token_saving=1)
    assert stronger.weight > previous
    failed = router.reinforce("w", first, success=False)
    assert failed.weight < stronger.weight
    assert router.reinforce("fresh", first, success=False).weight < baseline
