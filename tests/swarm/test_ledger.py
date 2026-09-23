import sqlite3
import pytest
from swarm.models import Signal,Locality,RunLimits
from swarm.task_ledger import TaskLedger,RunLimitReached,TaskConflict


def s(root,task,scope=None,**kw):
    return Signal(task_id=task,workspace=str(root),scope=scope or task,kind='opportunity',**kw)


def test_scope_module_dependency_queries_bounded_before_loading_bodies(tmp_path):
    ledger=TaskLedger(tmp_path/'ledger.db','run')
    ledger.enqueue(s(tmp_path,'a','src/a',module='core',x=1e6))
    ledger.enqueue(s(tmp_path,'b','src/b',module='core'),dependencies=('a',))
    ledger.enqueue(s(tmp_path,'c','src/c',module='other'))
    ledger.enqueue(s(tmp_path,'remote','remote'))
    with sqlite3.connect(ledger.path) as db:
        db.execute("UPDATE tasks SET signal='not json' WHERE task_id='remote'")
        plan=db.execute('EXPLAIN QUERY PLAN SELECT * FROM tasks WHERE swarm_id=? AND workspace=? AND scope=?',('run',ledger.get('a').signal.workspace,'src')).fetchall()
        assert 'tasks_locality' in str(plan)
    locality=Locality(workspace=str(tmp_path),authorized_scopes=('src',),modules=('core',),dependency_of=('a',))
    assert [r.signal.task_id for r in ledger.candidates(locality)]==['a']
    lease=ledger.claim('a','w',locality=locality)
    ledger.submit(lease,'done',{})
    assert [r.signal.task_id for r in ledger.candidates(locality)]==['b']
    assert len(ledger.candidates(locality,include_blocked=True,limit=1))==1
    assert ledger.candidates(Locality(workspace=str(tmp_path)))==[]
    with pytest.raises(ValueError):
        ledger.candidates(locality,limit=1001)


def test_failure_attempts_and_audit_survive_restart_and_export(tmp_path):
    path=tmp_path/'ledger.db'
    limits=RunLimits(max_attempts_per_task=2)
    ledger=TaskLedger(path,'run',limits=limits)
    ledger.enqueue(s(tmp_path,'a'),acceptance={'check':'fixed'})
    locality=Locality(workspace=str(tmp_path),authorized_scopes=('.',))
    one=ledger.claim('a','A',locality=locality)
    assert ledger.fail(one,{'error':'validation'}).status=='available'
    ledger=TaskLedger(path,'run',limits=limits)
    two=ledger.claim('a','B',locality=locality)
    assert two.token==2
    final=ledger.fail(two,{'error':'validation-again'})
    assert final.status=='failed' and final.attempts==2 and final.acceptance=={'check':'fixed'}
    assert ledger.claim('a','C',locality=locality) is None
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT COUNT(*) FROM task_attempts WHERE evidence IS NOT NULL').fetchone()[0]==2
        assert db.execute('PRAGMA journal_mode').fetchone()[0]=='wal'
    export=tmp_path/'audit.jsonl'
    ledger.export_jsonl(export)
    assert len(export.read_text().splitlines())==5
    export.write_text('corrupt export')
    assert len(ledger.audit())==5


def test_run_task_derived_attempt_and_runtime_limits(tmp_path):
    now=[100.]
    limits=RunLimits(max_tasks=3,max_derived_tasks=1,max_attempts=1,max_runtime_seconds=10)
    ledger=TaskLedger(tmp_path/'ledger.db','run',limits=limits,clock=lambda:now[0])
    ledger.enqueue(s(tmp_path,'a'))
    ledger.enqueue(s(tmp_path,'b'),derived_from='a')
    with pytest.raises(RunLimitReached,match='derived'):
        ledger.enqueue(s(tmp_path,'c'),derived_from='a')
    ledger.enqueue(s(tmp_path,'c'))
    with pytest.raises(RunLimitReached,match='max_tasks'):
        ledger.enqueue(s(tmp_path,'d'))
    loc=Locality(workspace=str(tmp_path),authorized_scopes=('.',))
    lease=ledger.claim('a','A',locality=loc)
    ledger.release(lease)
    with pytest.raises(RunLimitReached,match='max_attempts'):
        ledger.claim('b','B',locality=loc)
    now[0]=110
    with pytest.raises(RunLimitReached,match='runtime'):
        ledger.claim('b','B',locality=loc)
    assert ledger.get('a').attempts==1
    with pytest.raises(ValueError,match='limits'):
        TaskLedger(ledger.path,'run')


def test_immutable_tasks_missing_dependencies_cycles_and_run_isolation(tmp_path):
    ledger=TaskLedger(tmp_path/'ledger.db','one')
    task=s(tmp_path,'a')
    ledger.enqueue(task)
    with pytest.raises(TaskConflict):
        ledger.enqueue(task.model_copy(update={'payload':{'mutated':True}}))
    with pytest.raises(KeyError):
        ledger.enqueue(s(tmp_path,'b'),dependencies=('missing',))
    with pytest.raises(ValueError):
        ledger.enqueue(s(tmp_path,'b'),dependencies=('b',))
    other=TaskLedger(ledger.path,'two')
    assert other.snapshot()==[]
    other.enqueue(s(tmp_path,'a'))
    assert len(other.snapshot())==1
