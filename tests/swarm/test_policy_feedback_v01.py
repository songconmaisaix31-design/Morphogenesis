import math
import sqlite3

import pytest

from swarm.pheromone import PheromoneField
from swarm.task_ledger import TaskLedger


def test_explicit_history_prior_keeps_old_default_and_original_anchor(tmp_path):
    clock = [1000.0]
    ledger = TaskLedger(tmp_path / "ledger.sqlite3", "policy", clock=lambda: clock[0])
    field = PheromoneField(tmp_path / "field.sqlite3", ledger=ledger,
                           tau_seconds=100, alpha=0.5, clock=lambda: clock[0])
    first = field.reinforce("worker", "pipe", 1.0, prior=0.25)
    assert first.weight == 0.625
    clock[0] += 100
    assert field.pipe_history("worker", "pipe").weight == pytest.approx(0.625 / math.e)
    assert field.pipe_history("worker", "pipe", prior=0.25).weight == pytest.approx(0.25 + 0.375 / math.e)
    with sqlite3.connect(field.path) as db:
        assert db.execute("SELECT updated_at,samples FROM pipe_history").fetchone() == (1000.0, 1)
    second = field.reinforce("worker", "pipe", 0, prior=0.25)
    assert second.weight == pytest.approx((0.25 + 0.375 / math.e) / 2)
    assert second.samples == 2
    with pytest.raises(ValueError, match="prior"):
        field.pipe_history("worker", "pipe", prior=float("nan"))
