"""Real SQLite, process termination, fencing and scope aliases; no remote execution."""
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import pytest
from swarm.models import Lease, Locality, Signal
from swarm.lease import LeaseManager, LeaseLost
from swarm.task_ledger import TaskLedger, TaskConflict


def setup(tmp_path, now=None):
    now=now or [100.0]
    ledger=TaskLedger(tmp_path/'tasks.db','run',clock=lambda:now[0])
    for task,scope in [('a','src'),('b','src/child'),('c','other')]:
        ledger.enqueue(Signal(task_id=task,workspace=str(tmp_path),scope=scope,kind='opportunity'))
    return ledger,LeaseManager(ledger),Locality(workspace=str(tmp_path),authorized_scopes=('.',)),now


def test_expired_owner_successor_commit_then_stale_submit_release_rejected(tmp_path):
    ledger,leases,locality,now=setup(tmp_path)
    a=leases.acquire('a','A',ttl_seconds=10,locality=locality)
    assert a.token==1
    now[0]=111
    b=leases.acquire('a','B',ttl_seconds=30,locality=locality)
    assert b.token==2
    target=tmp_path/'result.txt'
    def publish(check):
        check()
        target.write_text('B',encoding='utf-8')
    done=leases.submit(b,'r2',{'accepted':True},apply=publish)
    assert done.effect_applied
    assert leases.submit(b,'r2',{'accepted':True},apply=lambda _:pytest.fail('duplicate effect')) == done
    with pytest.raises(LeaseLost):
        leases.submit(a,'r1',{},apply=lambda _:target.write_text('A'))
    assert not leases.release(a)
    assert not leases.release(b)  # Completed task never returns to available.
    assert target.read_text()=='B'
    assert ledger.get('a').result_id=='r2'
    with pytest.raises(TaskConflict):
        leases.submit(b,'r2',{'different':True})


def test_killed_real_owner_then_integer_token_two_completion(tmp_path):
    ledger,leases,locality,now=setup(tmp_path)
    script='''
import sys,time
from swarm.task_ledger import TaskLedger
from swarm.models import Locality
ledger=TaskLedger(sys.argv[1],'run',clock=lambda:100.)
lease=ledger.claim('a','child-A',ttl_seconds=10,locality=Locality(workspace=sys.argv[2],authorized_scopes=('.',)))
print(lease.model_dump_json(),flush=True)
time.sleep(120)
'''
    child=subprocess.Popen([sys.executable,'-c',script,str(ledger.path),str(tmp_path)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        old=Lease.model_validate_json(child.stdout.readline())
        child.kill()
        child.communicate(timeout=20)
        assert child.returncode != 0
    finally:
        if child.poll() is None:
            child.kill(); child.wait(timeout=20)
    now[0]=111
    new=leases.acquire('a','B',locality=locality)
    assert (old.token,new.token)==(1,2)
    leases.submit(new,'B',{})
    with pytest.raises(LeaseLost):
        leases.submit(old,'A',{})
    assert not leases.release(old)


def test_parent_child_siblings_aliases_and_empty_auth(tmp_path):
    ledger,leases,locality,now=setup(tmp_path)
    assert leases.acquire('a','w',locality=Locality(workspace=str(tmp_path))) is None
    a=leases.acquire('a','A',locality=locality)
    assert leases.acquire('b','B',locality=locality) is None
    assert leases.acquire('c','C',locality=locality)
    ledger.enqueue(Signal(task_id='alias',workspace=str(tmp_path),scope='src/../src',kind='opportunity'))
    assert leases.acquire('alias','alias',locality=locality) is None
    now[0]+=1
    renewed=leases.renew(a,ttl_seconds=40)
    assert renewed.token==a.token and renewed.expires_at>a.expires_at
    assert not leases.release(a)
    assert leases.release(renewed)
    b=leases.acquire('b','B',locality=locality)
    assert b and leases.acquire('a','A',locality=locality) is None


def test_junction_or_symlink_aliases_cannot_bypass_scope(tmp_path):
    ledger,leases,locality,_=setup(tmp_path)
    root=tmp_path/'src';root.mkdir()
    alias=tmp_path/'link'
    if os.name=='nt':
        result=subprocess.run(['cmd','/c','mklink','/J',str(alias),str(root)],capture_output=True,text=True)
        assert result.returncode==0,result.stderr
    else:
        alias.symlink_to(root,target_is_directory=True)
    ledger.enqueue(Signal(task_id='alias',workspace=str(tmp_path),scope='link',kind='opportunity'))
    lease=leases.acquire('a','A',locality=locality)
    assert lease and leases.acquire('alias','B',locality=locality) is None


def test_submit_failure_holds_intent_and_overlapping_scope_across_restart(tmp_path):
    ledger,leases,locality,now=setup(tmp_path)
    lease=leases.acquire('a','A',locality=locality)
    def partial(check):
        check()
        (tmp_path/'partial').write_text('part')
        raise RuntimeError('interrupted')
    with pytest.raises(RuntimeError,match='interrupted'):
        ledger.submit(lease,'partial',{'applied':True},apply=partial)
    assert ledger.get('a').status=='submitting'
    assert not ledger.get('a').effect_applied
    now[0]+=100
    restarted=TaskLedger(ledger.path,'run',clock=lambda:now[0])
    assert restarted.claim('a','B',locality=locality) is None
    assert restarted.claim('b','B',locality=locality) is None
    assert not restarted.release(lease)
    with pytest.raises(LeaseLost):
        restarted.submit(lease,'partial',{'applied':True},apply=lambda _:pytest.fail('replay'))


def test_submit_ttl_check_during_effect_keeps_unknown_intent(tmp_path):
    ledger,leases,locality,now=setup(tmp_path)
    lease=leases.acquire('a','A',ttl_seconds=1,locality=locality)
    def expires(check):
        now[0]+=2
        check()
        pytest.fail('expired effect')
    with pytest.raises(LeaseLost):
        ledger.submit(lease,'r',{},apply=expires)
    assert ledger.get('a').status=='submitting'


def test_atomic_claim_contention_many_processes(tmp_path):
    ledger,_,_,_=setup(tmp_path)
    script='''
import sys
from swarm.task_ledger import TaskLedger
from swarm.models import Locality
ledger=TaskLedger(sys.argv[1],'run',clock=lambda:100.)
lease=ledger.claim('a',sys.argv[3],locality=Locality(workspace=sys.argv[2],authorized_scopes=('.',)))
print(lease.token if lease else 'blocked')
'''
    children=[subprocess.Popen([sys.executable,'-c',script,str(ledger.path),str(tmp_path),str(i)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for i in range(5)]
    results=[p.communicate(timeout=40) for p in children]
    assert all(p.returncode==0 for p in children),results
    assert sum(out.strip()=='1' for out,_ in results)==1
    assert ledger.get('a').attempts==1


def test_sqlite_contention_is_bounded_and_reader_does_not_write(tmp_path):
    ledger,leases,locality,_=setup(tmp_path)
    contender=TaskLedger(ledger.path,'run',clock=lambda:100.,timeout_seconds=.02)
    with ledger.transaction():
        assert contender.get('a').status=='available'  # WAL reader allowed.
        with pytest.raises(sqlite3.OperationalError,match='locked'):
            contender.claim('a','B',locality=locality)
    assert leases.acquire('a','A',locality=locality).token==1


def test_fabricated_effect_boolean_has_no_authority(tmp_path):
    ledger,leases,locality,_=setup(tmp_path)
    lease=leases.acquire('a','A',locality=locality)
    record=ledger.submit(lease,'fake',{'applied':True})
    assert record.status=='completed' and not record.effect_applied
