from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from swarm.models import Locality, Signal
from swarm.pheromone import PheromoneField


def signal(root: Path, **kwargs: object) -> Signal:
    return Signal.model_validate(dict(task_id="repair-1", workspace=str(root), scope="src",
                                     kind="error_pattern", **kwargs))


def test_restart_decay_time_scale_and_deposition(tmp_path: Path) -> None:
    now = [100.0]
    path = tmp_path / "field.db"
    field = PheromoneField(path, time_step_seconds=10, clock=lambda: now[0])
    s = field.deposit(signal(tmp_path, concentration=10.0))
    now[0] += 10
    restarted = PheromoneField(path, time_step_seconds=10, clock=lambda: now[0])
    sensed = restarted.sense(Locality(workspace=str(tmp_path)))[0]
    assert sensed.concentration == pytest.approx(9.5)
    updated = restarted.deposit(s, delta=2)
    assert updated.concentration == pytest.approx(11.5)
    now[0] += 20
    assert restarted.sense(Locality(workspace=str(tmp_path)))[0].concentration == pytest.approx(11.5 * .95**2)
    with pytest.raises(ValueError, match="time step"):
        PheromoneField(path, time_step_seconds=20)


def test_radius_query_uses_index_and_never_reads_remote_bodies(tmp_path: Path) -> None:
    field = PheromoneField(tmp_path / "field.db", clock=lambda: 100.0)
    near = field.deposit(signal(tmp_path, x=3.0, y=4.0))
    field.deposit(signal(tmp_path, x=4.0, y=4.0))  # Inside box, outside circle.
    remote = field.deposit(signal(tmp_path, x=1000.0))
    other = field.deposit(signal(tmp_path / "elsewhere"))
    with sqlite3.connect(field.path) as db:
        # Invalid remote bodies would explode if sense loaded globally then filtered.
        db.execute("UPDATE signals SET body='not json' WHERE signal_id IN (?,?)",
                   (remote.signal_id, other.signal_id))
        plan = db.execute("EXPLAIN QUERY PLAN SELECT body FROM signals INDEXED BY signals_locality "
                          "WHERE workspace=? AND x BETWEEN ? AND ? AND y BETWEEN ? AND ?",
                          (str(tmp_path), -5, 5, -5, 5)).fetchall()
    assert "SEARCH" in str(plan) and "signals_locality" in str(plan)
    assert [s.signal_id for s in field.sense(Locality(workspace=str(tmp_path), radius=5.0))] == [near.signal_id]


def test_failure_accelerates_decay_nonnegative_and_completion_persists(tmp_path: Path) -> None:
    now = [100.0]
    field = PheromoneField(tmp_path / "field.db", time_step_seconds=10, clock=lambda: now[0])
    s = field.deposit(signal(tmp_path))
    failed = field.feedback(s.signal_id, success=False)
    assert failed.concentration == .5 and failed.decay_multiplier == 2
    now[0] += 10
    assert field.sense(Locality(workspace=str(tmp_path)))[0].concentration == pytest.approx(.5 * .95**2)
    for _ in range(100):
        field.feedback(s.signal_id, success=False)
    assert field.sense(Locality(workspace=str(tmp_path)))[0].concentration >= 0
    field.complete(s.signal_id)
    restarted = PheromoneField(field.path, time_step_seconds=10, clock=lambda: now[0])
    assert restarted.sense(Locality(workspace=str(tmp_path))) == []
    assert restarted.snapshot()[0].completed


def test_own_history_exact_update_restart_and_process_visibility(tmp_path: Path) -> None:
    field = PheromoneField(tmp_path / "field.db")
    assert field.reinforce("a", "repair", 0).weight == .95 * .25
    assert field.reinforce("a", "repair", 1).weight == .95 * .95 * .25 + .05
    assert field.pipe_history("b", "repair").weight == .25
    script = "from swarm.pheromone import PheromoneField; import sys; print(PheromoneField(sys.argv[1]).pipe_history('a','repair').model_dump_json())"
    result = subprocess.run([sys.executable, "-c", script, str(field.path)], capture_output=True,
                            text=True, timeout=30, check=True)
    assert '"samples":2' in result.stdout


def test_scope_escape_and_signal_mutation_rejected(tmp_path: Path) -> None:
    field = PheromoneField(tmp_path / "field.db")
    with pytest.raises(ValueError, match="escapes"):
        field.deposit(signal(tmp_path).model_copy(update={"scope": "../outside"}))
    s = field.deposit(signal(tmp_path))
    with pytest.raises(ValueError, match="identity"):
        field.deposit(s.model_copy(update={"payload": {"command": "changed"}}))
