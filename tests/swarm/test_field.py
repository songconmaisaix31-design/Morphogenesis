from pathlib import Path
import math
import sqlite3
import pytest
from swarm.models import Locality, RunLimits, Signal
from swarm.task_ledger import TaskLedger, TaskConflict
from swarm.pheromone import PheromoneField


def setup(tmp_path, now=None, **field_options):
    now = now or [100.0]
    ledger = TaskLedger(tmp_path / 'tasks.db', 'run', clock=lambda: now[0],
                        limits=RunLimits(max_runtime_seconds=1e12))
    field = PheromoneField(tmp_path / 'field.db', ledger=ledger, clock=lambda: now[0], **field_options)
    return ledger, field, now


def signal(root, task='a', **kwargs):
    return Signal(task_id=task, workspace=str(root), scope=task, kind='error_pattern', **kwargs)


def test_default_tau_daily_decay_and_independent_alpha(tmp_path):
    ledger, field, now = setup(tmp_path, alpha=.2)
    s = field.deposit(signal(tmp_path, concentration=10.0))
    assert field.tau_seconds == 86400
    assert field.reinforce('w', 'repair', 1).weight == pytest.approx(.8*.25+.2)
    now[0] += 86400
    locality = Locality(workspace=str(tmp_path), authorized_scopes=('.',))
    assert field.sense(locality)[0].concentration == pytest.approx(10/math.e)
    assert field.sense(locality)[0].concentration == pytest.approx(10/math.e)  # No double decay.
    assert field.deposit(s, 2).concentration == pytest.approx(10/math.e+2)
    with pytest.raises(ValueError, match='tau/alpha'):
        PheromoneField(field.path, ledger=ledger, alpha=.5)


def test_no_forgetting_tasks_dependencies_attempts_results_audit(tmp_path):
    ledger, field, now = setup(tmp_path)
    first = field.deposit(signal(tmp_path))
    ledger.enqueue(signal(tmp_path, 'b'), dependencies=('a',), acceptance={'policy':'fixed-v1'})
    locality = Locality(workspace=str(tmp_path), authorized_scopes=('.',))
    lease = ledger.claim('a','w',locality=locality)
    ledger.submit(lease,'result',{'accepted':True})
    field.feedback(first.signal_id, success=False)
    now[0] += 1e9
    restarted = TaskLedger(ledger.path,'run',limits=ledger.limits,clock=lambda:now[0])
    field = PheromoneField(field.path,ledger=restarted,clock=lambda:now[0])
    assert restarted.get('a').status == 'completed'
    assert restarted.get('a').result == {'accepted':True}
    assert restarted.get('a').attempts == 1
    assert restarted.get('b').dependencies == ('a',)
    assert restarted.get('b').acceptance == {'policy':'fixed-v1'}
    assert [s.task_id for s in field.sense(locality)] == ['b']
    assert field.sense(locality)[0].concentration == 0
    assert any(e['event']=='completed' for e in restarted.audit())
    assert not hasattr(field,'complete')


def test_duplicate_error_does_not_inflate_field_or_create_task(tmp_path):
    ledger, field, _ = setup(tmp_path)
    first = field.deposit(signal(tmp_path,payload={'error':'same'}))
    duplicate = signal(tmp_path,payload={'error':'same'}).model_copy(update={'task_id':'duplicate'})
    assert field.deposit(duplicate, 50).signal_id == first.signal_id
    assert field.snapshot()[0].concentration == 1
    assert len(ledger.snapshot()) == 1
    with sqlite3.connect(ledger.path) as db:
        assert db.execute('SELECT occurrences FROM task_evidence').fetchone()[0] == 2


def test_failure_only_preferences_and_history_worker_scoped(tmp_path):
    ledger, field, now = setup(tmp_path)
    s = field.deposit(signal(tmp_path))
    failed = field.feedback(s.signal_id,success=False)
    assert failed.concentration == .5 and failed.decay_multiplier == 2
    now[0] += 86400
    assert field.snapshot()[0].concentration == pytest.approx(.5*math.exp(-2))
    assert ledger.get('a').status == 'available'
    for _ in range(20):
        field.reinforce('a','repair',1)
    assert field.pipe_history('a','repair').weight > .25
    assert field.pipe_history('b','repair').weight == .25
    other = TaskLedger(ledger.path,'other',clock=lambda:now[0])
    assert PheromoneField(field.path,ledger=other,clock=lambda:now[0]).pipe_history('a','repair').weight == .25


def test_scope_escape_identity_change_and_legacy_fail_closed(tmp_path):
    ledger, field, _ = setup(tmp_path)
    with pytest.raises(ValueError,match='escapes'):
        field.deposit(signal(tmp_path).model_copy(update={'scope':'../outside'}))
    s = field.deposit(signal(tmp_path))
    with pytest.raises(TaskConflict,match='identity'):
        field.deposit(s.model_copy(update={'payload':{'changed':True}}))
    with sqlite3.connect(tmp_path/'legacy.db') as db:
        db.execute('CREATE TABLE signals (body TEXT)')
    with pytest.raises(ValueError,match='legacy'):
        PheromoneField(tmp_path/'legacy.db',ledger=ledger)
